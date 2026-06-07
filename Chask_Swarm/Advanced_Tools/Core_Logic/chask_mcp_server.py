"""
chask_mcp_server.py — Servidor MCP Completo de Enjambre/Chask Swarm
================================================================
Expone TODAS las herramientas del ecosistema como tools MCP estándar.
Cualquier IDE compatible (Cursor, VS Code, Windsurf, etc.) puede conectarse.

Uso: python chask_mcp_server.py
Transporte: stdio (el IDE lanza el proceso automáticamente)
"""
import asyncio
import json
import os
import subprocess
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# ── Paths ──────────────────────────────────────────────────────────
CHASK_ROOT = r"C:\Program Files\Chask_Swarm"
TOOLS_DIR = os.path.join(CHASK_ROOT, "Advanced_Tools")
DATA_DIR = r"C:\Users\fnora\Desktop\Enjambre Datos"
PYTHON = sys.executable

MEMORY_PATH = os.path.join(DATA_DIR, "memory.md")
DIRECTIVES_PATH = os.path.join(DATA_DIR, "directives.md")
MEMORY_CORE_PATH = os.path.join(CHASK_ROOT, "memory.md")
DIRECTIVES_CORE_PATH = os.path.join(CHASK_ROOT, "directives.md")
AGENTS_CONFIG_PATH = os.path.join(CHASK_ROOT, "Configuracion", "master_credentials.json")
TELEGRAM_SCRIPT = os.path.join(CHASK_ROOT, "charm_telegram.py")

# ── Helpers ────────────────────────────────────────────────────────
def _run_script(script_path: str, args: list[str] = None, timeout: int = 30) -> str:
    """Ejecuta un script Python del ecosistema y devuelve su output."""
    cmd = [PYTHON, script_path] + (args or [])
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=CHASK_ROOT, encoding="utf-8", errors="replace"
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[STDERR] {result.stderr.strip()}"
        return output or "(sin output)"
    except subprocess.TimeoutExpired:
        return f"[ERROR] Timeout ({timeout}s) ejecutando {os.path.basename(script_path)}"
    except Exception as e:
        return f"[ERROR] {e}"


def _read_file_safe(path: str, max_bytes: int = 50000) -> str:
    """Lee un archivo de forma segura."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(max_bytes)
        return content
    except Exception as e:
        return f"[ERROR] No se pudo leer {path}: {e}"


def _run_cmd(cmd: str, timeout: int = 15) -> str:
    """Ejecuta un comando shell y devuelve el output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=True, encoding="utf-8", errors="replace"
        )
        return result.stdout.strip() or "(sin output)"
    except Exception as e:
        return f"[ERROR] {e}"


# ══════════════════════════════════════════════════════════════════
#  SERVIDOR MCP
# ══════════════════════════════════════════════════════════════════
server = Server("enjambre-chask-swarm")


# ── TOOLS ──────────────────────────────────────────────────────────
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        # ── Comunicación ──
        types.Tool(
            name="send_telegram",
            description="Envía un mensaje al administrador (Fernando) por Telegram.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje a enviar"}
                },
                "required": ["message"]
            }
        ),
        types.Tool(
            name="ask_telegram",
            description="Envía una pregunta por Telegram y espera la respuesta del administrador.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Pregunta a enviar"},
                    "timeout": {"type": "number", "description": "Segundos a esperar (default: 120)", "default": 120}
                },
                "required": ["question"]
            }
        ),

        # ── Memoria vectorial (Qdrant) ──
        types.Tool(
            name="memory_search",
            description="Busca en la memoria vectorial de largo plazo (Qdrant). Útil para encontrar contexto de conversaciones pasadas, conocimiento técnico indexado, o lecciones aprendidas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto de búsqueda"},
                    "collection": {"type": "string", "description": "Colección Qdrant (default: chask_memory)", "default": "chask_memory"},
                    "limit": {"type": "number", "description": "Máximo de resultados (default: 5)", "default": 5}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="memory_store",
            description="Almacena un hecho, preferencia o lección aprendida en la memoria vectorial de largo plazo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Texto a almacenar"},
                    "collection": {"type": "string", "description": "Colección Qdrant (default: chask_memory)", "default": "chask_memory"},
                    "metadata": {"type": "string", "description": "Metadata JSON adicional (opcional)", "default": "{}"}
                },
                "required": ["text"]
            }
        ),

        # ── IA / LLM Router ──
        types.Tool(
            name="route_llm",
            description="Envía un prompt al pool de IAs gratuitas (OpenRouter). Útil para tareas delegadas: resúmenes, traducciones, análisis, generación de código.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt a enviar"},
                    "agent": {"type": "string", "description": "Agente a usar: viper|ghost|hunter|oracle (default: ghost)", "default": "ghost"},
                    "max_tokens": {"type": "number", "description": "Tokens máximos (default: 2000)", "default": 2000}
                },
                "required": ["prompt"]
            }
        ),

        # ── Seguridad ──
        types.Tool(
            name="audit_log",
            description="Registra una acción en el log de auditoría. Obligatorio antes de comandos críticos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Descripción de la acción a registrar"}
                },
                "required": ["action"]
            }
        ),
        types.Tool(
            name="run_sandbox",
            description="Ejecuta un script Python en sandbox aislado. Usar para código externo o no confiable.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_path": {"type": "string", "description": "Ruta al script a ejecutar"}
                },
                "required": ["script_path"]
            }
        ),
        types.Tool(
            name="privacy_scan",
            description="Escanea texto en busca de datos personales (PII) y devuelve una versión anonimizada.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Texto a escanear"}
                },
                "required": ["text"]
            }
        ),

        # ── Infraestructura ──
        types.Tool(
            name="check_daemons",
            description="Verifica el estado de los daemons de Chask Swarm (Telegram, Watchdog, etc.).",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="create_backup",
            description="Crea un backup del directorio especificado.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Directorio a respaldar (default: workspace)", "default": DATA_DIR}
                },
                "required": []
            }
        ),

        # ── Web ──
        types.Tool(
            name="scrape_url",
            description="Extrae contenido de una URL usando el scraper universal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL a scrapear"},
                    "mode": {"type": "string", "description": "Modo: text|links|full (default: text)", "default": "text"}
                },
                "required": ["url"]
            }
        ),

        # ── Archivos ──
        types.Tool(
            name="read_file",
            description="Lee el contenido de un archivo del sistema de archivos local.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta absoluta al archivo"}
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="write_file",
            description="Escribe contenido en un archivo. PRECAUCIÓN: sobrescribe si existe.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta absoluta al archivo"},
                    "content": {"type": "string", "description": "Contenido a escribir"}
                },
                "required": ["path", "content"]
            }
        ),

        # ── Knowledge ──
        types.Tool(
            name="knowledge_search",
            description="Busca en las bases de conocimiento indexadas (Power Automate, RPA, etc.) usando búsqueda híbrida BM25+vectorial.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de búsqueda"},
                    "collection": {"type": "string", "description": "Colección (default: power_automate_v4)", "default": "power_automate_v4"},
                    "limit": {"type": "number", "description": "Máximo resultados (default: 5)", "default": 5}
                },
                "required": ["query"]
            }
        ),

        # ── Fase 2: Inteligencia Real ──
        types.Tool(
            name="hive_mind",
            description="Ejecuta una tarea compleja dividiéndola en subtareas paralelas entre los 4 agentes (Viper, Ghost, Hunter, Oracle). Usa para tareas multi-fase o que requieren múltiples perspectivas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Tarea compleja a resolver"},
                    "max_subtasks": {"type": "number", "description": "Máximo de subtareas paralelas (default: 4)", "default": 4}
                },
                "required": ["task"]
            }
        ),
        types.Tool(
            name="auto_reflect",
            description="Ejecuta reflexión automática: analiza la actividad reciente y extrae lecciones aprendidas.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="detect_mode",
            description="Detecta el modo de agente más adecuado para un prompt usando routing semántico (embeddings) con fallback a keywords.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt a analizar"}
                },
                "required": ["prompt"]
            }
        ),

        # ── Fase 3: Madurez ──
        types.Tool(
            name="memory_decay",
            description="Aplica decadencia temporal a las memorias. Memorias no accedidas pierden confianza exponencialmente.",
            inputSchema={
                "type": "object",
                "properties": {
                    "half_life_days": {"type": "number", "description": "Días para media vida (default: 30)", "default": 30}
                },
                "required": []
            }
        ),
        types.Tool(
            name="memory_confirm",
            description="Confirma/refuerza una memoria existente (aumenta su confianza +0.2).",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "number", "description": "ID de la memoria a confirmar"}
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="memory_stats",
            description="Devuelve estadísticas del sistema de memoria (total, activas, confianza promedio, etc.).",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="generate_skill",
            description="Genera un script Python funcional a partir de una descripción en lenguaje natural. Lo guarda en /skills/ y lo registra en el catálogo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Descripción de lo que debe hacer el script"},
                    "filename": {"type": "string", "description": "Nombre del archivo (opcional, se auto-genera)"}
                },
                "required": ["description"]
            }
        ),

        # ── Fase 4: Alcance ──
        types.Tool(
            name="broadcast",
            description="Envía un mensaje a TODOS los canales configurados (Telegram, Discord, Slack, Teams).",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje a difundir"}
                },
                "required": ["message"]
            }
        ),
        types.Tool(
            name="notify",
            description="Envía una notificación inteligente con prioridad y agrupación automática.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Texto de la notificación"},
                    "priority": {"type": "string", "description": "critical|warning|info|debug (default: info)", "default": "info"},
                    "immediate": {"type": "boolean", "description": "Si true, envía sin agrupar", "default": False}
                },
                "required": ["message"]
            }
        ),
        types.Tool(
            name="channel_status",
            description="Muestra el estado de todos los canales de comunicación registrados.",
            inputSchema={"type": "object", "properties": {}}
        ),

        # ── Fase 5: Polish ──
        types.Tool(
            name="create_mode",
            description="Crea un nuevo modo de agente personalizado en runtime.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode_id": {"type": "string", "description": "ID único del modo (snake_case)"},
                    "name": {"type": "string", "description": "Nombre visible"},
                    "description": {"type": "string", "description": "Descripción del modo"},
                    "keywords": {"type": "string", "description": "Keywords separadas por comas (opcional)"}
                },
                "required": ["mode_id", "name", "description"]
            }
        ),
        types.Tool(
            name="delete_mode",
            description="Elimina un modo de agente custom (no permite eliminar built-in).",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode_id": {"type": "string", "description": "ID del modo a eliminar"}
                },
                "required": ["mode_id"]
            }
        ),
        types.Tool(
            name="mcp_discover",
            description="Descubre las tools disponibles en un servidor MCP externo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Nombre del servidor MCP registrado"}
                },
                "required": ["server_name"]
            }
        ),
        types.Tool(
            name="mcp_call",
            description="Llama a una tool de un servidor MCP externo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Nombre del servidor MCP"},
                    "tool_name": {"type": "string", "description": "Nombre de la tool"},
                    "arguments": {"type": "string", "description": "Argumentos JSON (opcional)", "default": "{}"}
                },
                "required": ["server_name", "tool_name"]
            }
        ),

        # ── Fase 6: Expansión ──
        types.Tool(
            name="git_worktree_create",
            description="Crea un Git worktree aislado para trabajar en una rama sin afectar main.",
            inputSchema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Nombre de la rama/worktree"},
                    "base": {"type": "string", "description": "Rama base (default: main)", "default": "main"}
                },
                "required": ["branch"]
            }
        ),
        types.Tool(
            name="git_worktree_list",
            description="Lista todos los Git worktrees activos.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="git_worktree_merge",
            description="Mergea un worktree/rama a main y limpia.",
            inputSchema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Rama a mergear"},
                    "target": {"type": "string", "description": "Rama destino (default: main)", "default": "main"}
                },
                "required": ["branch"]
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Ejecuta una herramienta del ecosistema."""
    args = arguments or {}

    # ── Comunicación ──
    if name == "send_telegram":
        out = _run_script(TELEGRAM_SCRIPT, ["send", args["message"]])
        return [types.TextContent(type="text", text=f"Telegram enviado: {out}")]

    elif name == "ask_telegram":
        timeout = str(int(args.get("timeout", 120)))
        out = _run_script(TELEGRAM_SCRIPT, ["ask", args["question"], timeout], timeout=int(timeout) + 10)
        return [types.TextContent(type="text", text=f"Respuesta Telegram: {out}")]

    # ── Memoria vectorial ──
    elif name == "memory_search":
        out = _run_script(
            os.path.join(TOOLS_DIR, "qdrant_memory_manager.py"),
            ["search", args["query"], args.get("collection", "chask_memory"), str(int(args.get("limit", 5)))]
        )
        return [types.TextContent(type="text", text=out)]

    elif name == "memory_store":
        out = _run_script(
            os.path.join(TOOLS_DIR, "qdrant_memory_manager.py"),
            ["store", args["text"], args.get("collection", "chask_memory")]
        )
        return [types.TextContent(type="text", text=f"Almacenado: {out}")]

    # ── LLM Router ──
    elif name == "route_llm":
        out = _run_script(
            os.path.join(TOOLS_DIR, "llm_router.py"),
            ["--prompt", args["prompt"], "--agent", args.get("agent", "ghost"),
             "--max-tokens", str(int(args.get("max_tokens", 2000)))],
            timeout=60
        )
        return [types.TextContent(type="text", text=out)]

    # ── Seguridad ──
    elif name == "audit_log":
        out = _run_script(os.path.join(TOOLS_DIR, "audit_logger.py"), [args["action"]])
        return [types.TextContent(type="text", text=f"Auditoria: {out}")]

    elif name == "run_sandbox":
        out = _run_script(os.path.join(TOOLS_DIR, "sandbox.py"), [args["script_path"]], timeout=60)
        return [types.TextContent(type="text", text=f"Sandbox: {out}")]

    elif name == "privacy_scan":
        out = _run_script(os.path.join(TOOLS_DIR, "privacy_engine.py"), [args["text"]])
        return [types.TextContent(type="text", text=out)]

    # ── Infraestructura ──
    elif name == "check_daemons":
        pythonw = _run_cmd('tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV')
        python = _run_cmd('tasklist /FI "IMAGENAME eq python.exe" /FO CSV')
        docker = _run_cmd("docker ps --format \"{{.Names}}: {{.Status}}\" 2>nul")
        return [types.TextContent(type="text", text=f"=== pythonw ===\n{pythonw}\n\n=== python ===\n{python}\n\n=== Docker ===\n{docker}")]

    elif name == "create_backup":
        target = args.get("target", DATA_DIR)
        out = _run_script(os.path.join(TOOLS_DIR, "backup_system.py"), [target])
        return [types.TextContent(type="text", text=f"Backup: {out}")]

    # ── Web ──
    elif name == "scrape_url":
        out = _run_script(
            os.path.join(BASE_DIR, "skills", "utilities", "universal_scraper.py"),
            [args["url"], "--mode", args.get("mode", "text")],
            timeout=30
        )
        return [types.TextContent(type="text", text=out)]

    # ── Archivos ──
    elif name == "read_file":
        content = _read_file_safe(args["path"])
        return [types.TextContent(type="text", text=content)]

    elif name == "write_file":
        try:
            with open(args["path"], "w", encoding="utf-8") as f:
                f.write(args["content"])
            return [types.TextContent(type="text", text=f"Escrito: {args['path']}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"[ERROR] {e}")]

    # ── Knowledge ──
    elif name == "knowledge_search":
        out = _run_script(
            os.path.join(TOOLS_DIR, "qdrant_memory_manager.py"),
            ["search", args["query"], args.get("collection", "power_automate_v4"), str(int(args.get("limit", 5)))]
        )
        return [types.TextContent(type="text", text=out)]

    # ── Fase 2: Inteligencia Real ──
    elif name == "hive_mind":
        out = _run_script(
            os.path.join(TOOLS_DIR, "hive_mind_executor.py"),
            [args["task"]],
            timeout=120
        )
        return [types.TextContent(type="text", text=out)]

    elif name == "auto_reflect":
        out = _run_script(os.path.join(TOOLS_DIR, "reflection_engine.py"), ["auto"], timeout=60)
        return [types.TextContent(type="text", text=out)]

    elif name == "detect_mode":
        out = _run_script(os.path.join(TOOLS_DIR, "mode_router.py"), ["detect", args["prompt"]])
        return [types.TextContent(type="text", text=out)]

    # ── Fase 3: Madurez ──
    elif name == "memory_decay":
        days = str(int(args.get("half_life_days", 30)))
        out = _run_script(os.path.join(TOOLS_DIR, "evolutionary_memory.py"), ["decay", days])
        return [types.TextContent(type="text", text=out)]

    elif name == "memory_confirm":
        out = _run_script(os.path.join(TOOLS_DIR, "evolutionary_memory.py"), ["confirm", str(int(args["memory_id"]))])
        return [types.TextContent(type="text", text=out)]

    elif name == "memory_stats":
        out = _run_script(os.path.join(TOOLS_DIR, "evolutionary_memory.py"), ["stats"])
        return [types.TextContent(type="text", text=out)]

    elif name == "generate_skill":
        cmd_args = [args["description"]]
        out = _run_script(os.path.join(TOOLS_DIR, "skill_generator.py"), cmd_args, timeout=60)
        return [types.TextContent(type="text", text=out)]

    # ── Fase 4: Alcance ──
    elif name == "broadcast":
        out = _run_script(os.path.join(TOOLS_DIR, "channel_adapter.py"), ["broadcast", args["message"]])
        return [types.TextContent(type="text", text=out)]

    elif name == "notify":
        prio = args.get("priority", "info")
        out = _run_script(os.path.join(TOOLS_DIR, "notification_manager.py"), ["send", prio, args["message"]])
        return [types.TextContent(type="text", text=out)]

    elif name == "channel_status":
        out = _run_script(os.path.join(TOOLS_DIR, "channel_adapter.py"), ["status"])
        return [types.TextContent(type="text", text=out)]

    # ── Fase 5: Polish ──
    elif name == "create_mode":
        keywords = args.get("keywords", "").split(",") if args.get("keywords") else []
        cmd_args = ["create", args["mode_id"], args["name"], args["description"]] + keywords
        out = _run_script(os.path.join(TOOLS_DIR, "mode_router.py"), cmd_args)
        return [types.TextContent(type="text", text=out)]

    elif name == "delete_mode":
        out = _run_script(os.path.join(TOOLS_DIR, "mode_router.py"), ["delete", args["mode_id"]])
        return [types.TextContent(type="text", text=out)]

    elif name == "mcp_discover":
        out = _run_script(os.path.join(TOOLS_DIR, "mcp_client.py"), ["discover", args["server_name"]], timeout=30)
        return [types.TextContent(type="text", text=out)]

    elif name == "mcp_call":
        cmd_args = ["call", args["server_name"], args["tool_name"], args.get("arguments", "{}")]
        out = _run_script(os.path.join(TOOLS_DIR, "mcp_client.py"), cmd_args, timeout=30)
        return [types.TextContent(type="text", text=out)]

    # ── Fase 6: Expansión ──
    elif name == "git_worktree_create":
        base = args.get("base", "main")
        out = _run_script(os.path.join(TOOLS_DIR, "git_worktree_manager.py"), ["create", args["branch"], base])
        return [types.TextContent(type="text", text=out)]

    elif name == "git_worktree_list":
        out = _run_script(os.path.join(TOOLS_DIR, "git_worktree_manager.py"), ["list"])
        return [types.TextContent(type="text", text=out)]

    elif name == "git_worktree_merge":
        target = args.get("target", "main")
        out = _run_script(os.path.join(TOOLS_DIR, "git_worktree_manager.py"), ["merge", args["branch"], target])
        return [types.TextContent(type="text", text=out)]

    raise ValueError(f"Herramienta desconocida: {name}")


# ── RESOURCES ──────────────────────────────────────────────────────
@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="enjambre://memory",
            name="Memoria activa de Enjambre",
            description="Contexto actual, tarea en curso, estado del sistema. Se actualiza en cada sesión.",
            mimeType="text/markdown"
        ),
        types.Resource(
            uri="enjambre://directives",
            name="Directivas operativas",
            description="Reglas, protocolos y configuración permanente de Enjambre.",
            mimeType="text/markdown"
        ),
        types.Resource(
            uri="enjambre://memory-core",
            name="Memoria core (Chask_Swarm)",
            description="Memoria del núcleo del sistema en Program Files.",
            mimeType="text/markdown"
        ),
        types.Resource(
            uri="enjambre://directives-core",
            name="Directivas core (Chask_Swarm)",
            description="Directivas del núcleo del sistema en Program Files.",
            mimeType="text/markdown"
        ),
        types.Resource(
            uri="enjambre://agents",
            name="Configuración de agentes",
            description="Configuración de los agentes especializados (Viper, Ghost, Hunter, Oracle).",
            mimeType="application/json"
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    uri_str = str(uri)
    if uri_str == "enjambre://memory":
        return _read_file_safe(MEMORY_PATH)
    elif uri_str == "enjambre://directives":
        return _read_file_safe(DIRECTIVES_PATH)
    elif uri_str == "enjambre://memory-core":
        return _read_file_safe(MEMORY_CORE_PATH)
    elif uri_str == "enjambre://directives-core":
        return _read_file_safe(DIRECTIVES_CORE_PATH)
    elif uri_str == "enjambre://agents":
        try:
            with open(AGENTS_CONFIG_PATH, "r") as f:
                config = json.load(f)
            # Sanitizar tokens/keys antes de exponer
            for agent in config.get("agents", []):
                if "api_key" in agent:
                    agent["api_key"] = "***REDACTED***"
            return json.dumps(config, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"[ERROR] {e}"
    raise ValueError(f"Recurso desconocido: {uri}")


# ── PROMPTS ────────────────────────────────────────────────────────
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="hive_mind",
            description="Protocolo Hive Mind para tareas complejas. Divide en 4 fases: Alpha (Planifica), Beta (Investiga), Gamma (Ejecuta), Delta (Audita).",
            arguments=[
                types.PromptArgument(name="task", description="Descripción de la tarea compleja", required=True)
            ]
        ),
        types.Prompt(
            name="chask_identity",
            description="Prompt de identidad completa de Enjambre. Incluye personalidad, protocolos de seguridad, directivas operativas y herramientas disponibles.",
            arguments=[]
        ),
        types.Prompt(
            name="code_review",
            description="Prompt para revisión de código con estándares del ecosistema Chask.",
            arguments=[
                types.PromptArgument(name="code", description="Código a revisar", required=True),
                types.PromptArgument(name="language", description="Lenguaje (python, javascript, etc.)", required=False)
            ]
        ),
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
    args = arguments or {}

    if name == "hive_mind":
        task = args.get("task", "tarea no especificada")
        return types.GetPromptResult(
            description=f"Hive Mind para: {task}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=f"""Activa el protocolo Hive Mind para la siguiente tarea:

**Tarea:** {task}

Ejecuta las 4 fases en orden:

## 🔷 Alpha — Planificación
Analiza la tarea, identifica dependencias, estima complejidad, divide en subtareas.

## 🔶 Beta — Investigación
Investiga lo necesario: APIs, documentación, código existente, patrones similares.

## 🟢 Gamma — Ejecución
Implementa cada subtarea en orden. Documenta cada paso. Testea incrementalmente.

## 🔴 Delta — Auditoría
Revisa el resultado: ¿cumple requisitos? ¿hay edge cases? ¿se actualizó memory.md?
Envía confirmación por Telegram al completar.""")
                )
            ]
        )

    elif name == "chask_identity":
        identity = _read_file_safe(DIRECTIVES_CORE_PATH)
        return types.GetPromptResult(
            description="Identidad de Enjambre",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=f"""Eres Enjambre, la IA autónoma del ecosistema Chask Swarm.

{identity}

Confirma que estás online y lista.""")
                )
            ]
        )

    elif name == "code_review":
        code = args.get("code", "")
        lang = args.get("language", "auto-detect")
        return types.GetPromptResult(
            description="Revisión de código",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=f"""Revisa el siguiente código ({lang}):

```{lang}
{code}
```

Evalúa:
1. **Seguridad**: ¿Hay vulnerabilidades? ¿Manejo de datos sensibles?
2. **Robustez**: ¿Maneja errores? ¿Edge cases?
3. **Rendimiento**: ¿Hay cuellos de botella?
4. **Legibilidad**: ¿Está bien documentado?
5. **Mejoras**: Sugiere 3 mejoras concretas.""")
                )
            ]
        )

    raise ValueError(f"Prompt desconocido: {name}")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
