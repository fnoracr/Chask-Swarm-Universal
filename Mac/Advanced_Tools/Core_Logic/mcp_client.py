"""
mcp_client.py — Cliente MCP para Consumir Tools Externas
=========================================================
Permite a Enjambre conectarse a servidores MCP externos y usar sus tools,
ampliando sus capacidades sin modificar el código base.

Uso:
  python mcp_client.py list-servers
  python mcp_client.py connect "server_name"
  python mcp_client.py call "server_name" "tool_name" '{"arg": "val"}'
  python mcp_client.py discover "server_name"  (lista tools del servidor)
"""
import asyncio
import json
import os
import sys
import io
import subprocess
from datetime import datetime

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVERS_CONFIG = os.path.join(BASE_DIR, "mcp_servers.json")
CALL_LOG = os.path.join(BASE_DIR, "mcp_client_log.json")

DEFAULT_SERVERS = {
    "servers": {
        "enjambre": {
            "command": "python",
            "args": [os.path.join(BASE_DIR, "Advanced_Tools", "chask_mcp_server.py")],
            "description": "Servidor MCP propio de Enjambre",
            "enabled": True
        }
    }
}


def load_servers() -> dict:
    if os.path.exists(SERVERS_CONFIG):
        try:
            with open(SERVERS_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_SERVERS


def save_servers(config: dict):
    with open(SERVERS_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def add_server(name: str, command: str, args: list, description: str = ""):
    """Registra un servidor MCP externo."""
    config = load_servers()
    config["servers"][name] = {
        "command": command,
        "args": args,
        "description": description,
        "enabled": True,
        "added": datetime.now().isoformat()
    }
    save_servers(config)
    print(f"[MCPClient] Servidor '{name}' registrado.")


def remove_server(name: str):
    """Elimina un servidor MCP."""
    config = load_servers()
    if name in config.get("servers", {}):
        del config["servers"][name]
        save_servers(config)
        print(f"[MCPClient] Servidor '{name}' eliminado.")
    else:
        print(f"[MCPClient] Servidor '{name}' no encontrado.")


def list_servers() -> dict:
    """Lista todos los servidores MCP configurados."""
    config = load_servers()
    return config.get("servers", {})


async def discover_tools(server_name: str) -> list[dict]:
    """
    Conecta a un servidor MCP y lista sus tools disponibles.
    Usa el protocolo stdio para comunicarse.
    """
    config = load_servers()
    server = config.get("servers", {}).get(server_name)
    if not server:
        print(f"[MCPClient] Servidor '{server_name}' no encontrado.")
        return []

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=server["command"],
            args=server.get("args", []),
            env=server.get("env")
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                tools = []
                for tool in tools_result.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description or "",
                        "schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                    })
                return tools

    except ImportError:
        print("[MCPClient] SDK MCP no disponible. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "mcp"], capture_output=True)
        print("[MCPClient] Reintenta tras instalar.")
        return []
    except Exception as e:
        print(f"[MCPClient] Error descubriendo tools: {e}")
        return []


async def call_tool(server_name: str, tool_name: str, arguments: dict = None) -> str:
    """
    Llama a una tool de un servidor MCP externo.
    
    Args:
        server_name: Nombre del servidor registrado
        tool_name: Nombre de la tool a ejecutar
        arguments: Argumentos para la tool
    
    Returns:
        Resultado de la tool como string
    """
    config = load_servers()
    server = config.get("servers", {}).get(server_name)
    if not server:
        return f"[ERROR] Servidor '{server_name}' no encontrado"

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=server["command"],
            args=server.get("args", []),
            env=server.get("env")
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments or {})
                
                # Extraer texto del resultado
                output = ""
                for content in result.content:
                    if hasattr(content, 'text'):
                        output += content.text
                
                # Log
                _log_call(server_name, tool_name, arguments, output[:500])
                return output

    except Exception as e:
        return f"[ERROR] {e}"


def _log_call(server: str, tool: str, args: dict, result: str):
    """Log de llamadas MCP."""
    logs = []
    if os.path.exists(CALL_LOG):
        try:
            with open(CALL_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append({
        "ts": datetime.now().isoformat(),
        "server": server,
        "tool": tool,
        "args": str(args)[:200],
        "result": result[:200]
    })
    logs = logs[-50:]
    with open(CALL_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


# ── CLI ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python mcp_client.py list-servers")
        print("  python mcp_client.py add-server name command [args...]")
        print("  python mcp_client.py discover server_name")
        print("  python mcp_client.py call server_name tool_name '{\"args\": {}}'")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list-servers":
        servers = list_servers()
        print(f"\nSERVIDORES MCP ({len(servers)}):\n")
        for name, info in servers.items():
            status = "ON" if info.get("enabled") else "OFF"
            print(f"  [{status}] {name}: {info.get('description', '')}")
            print(f"        cmd: {info.get('command')} {' '.join(info.get('args', []))}")

    elif cmd == "add-server" and len(sys.argv) >= 4:
        name = sys.argv[2]
        command = sys.argv[3]
        args = sys.argv[4:] if len(sys.argv) > 4 else []
        add_server(name, command, args)

    elif cmd == "discover" and len(sys.argv) >= 3:
        tools = asyncio.run(discover_tools(sys.argv[2]))
        print(f"\nTOOLS de '{sys.argv[2]}' ({len(tools)}):\n")
        for t in tools:
            print(f"  - {t['name']}: {t['description'][:60]}")

    elif cmd == "call" and len(sys.argv) >= 4:
        server = sys.argv[2]
        tool = sys.argv[3]
        args = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        result = asyncio.run(call_tool(server, tool, args))
        print(result)

    else:
        print(f"Comando desconocido: {cmd}")
