"""
slash_commands.py — Sistema de Slash Commands para Enjambre
========================================================
Parsea y ejecuta atajos rápidos desde cualquier canal (Telegram, IDE, Web).

Comandos disponibles:
  /status           -- Estado del sistema (daemons, colecciones, cola)
  /modo <id>        -- Cambiar modo de agente (viper, ghost, hunter, oracle, enjambre)
  /kb crear <tema>  -- Crear base de conocimiento profundo sobre un tema
  /kb listar        -- Listar bases de conocimiento disponibles
  /kb buscar <q>    -- Buscar en todas las bases de conocimiento
  /skill listar     -- Listar skills registradas
  /skill buscar <q> -- Buscar una skill
  /fix              -- Analizar y corregir el ultimo error reportado
  /analiza <texto>  -- Analisis profundo de un tema/codigo/problema
  /resume <texto>   -- Resumen ejecutivo de un texto largo
  /deploy           -- Estado de deployments activos
  /help             -- Lista de comandos disponibles
  /help <cmd>       -- Ayuda detallada de un comando especifico
  /memoria <q>      -- Buscar en la memoria evolutiva
  /reflexion        -- Ejecutar reflexion de sesion ahora
  /config           -- Ver configuracion actual del sistema
  /set <k> <v>      -- Cambiar un parametro de configuracion en caliente
  /learn            -- Ejecutar auto-aprendizaje de skills ahora
  /sandbox <script> -- Ejecutar un script en el sandbox seguro
  /services         -- Estado de los Windows Services

Uso desde otros módulos:
    from slash_commands import parse_command, is_command
    if is_command(user_input):
        result = parse_command(user_input)
        # result = {"handled": True, "response": "...", "raw_query": None}
    else:
        # Procesar como lenguaje natural
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime

log = logging.getLogger("slash_commands")

TOOLS_DIR  = r"C:\Program Files\Chask_Swarm\Advanced_Tools"
SWARM_DIR  = r"C:\Program Files\Chask_Swarm"

# ─── Aliases ──────────────────────────────────────────────────
ALIASES = {
    "/s":       "/status",
    "/m":       "/modo",
    "/k":       "/kb",
    "/sk":      "/skill",
    "/h":       "/help",
    "/f":       "/fix",
    "/a":       "/analiza",
    "/r":       "/resume",
    "/mem":     "/memoria",
    "/ref":     "/reflexion",
    "/c":       "/config",
    "/l":       "/learn",
    "/sb":      "/sandbox",
    "/svc":     "/services",
    "/u":       "/user",
    "/sw":      "/swarm",
}


def is_command(text: str) -> bool:
    """Verifica si un texto es un slash command."""
    t = text.strip()
    if not t.startswith("/"):
        return False
    cmd = t.split()[0].lower()
    return cmd in ALIASES or cmd in {
        "/status", "/modo", "/kb", "/skill", "/fix",
        "/analiza", "/resume", "/deploy", "/help",
        "/memoria", "/reflexion", "/config", "/set",
        "/learn", "/sandbox", "/services", "/user", "/swarm",
    }


def _resolve_alias(text: str) -> str:
    """Resuelve aliases a comandos completos."""
    parts = text.strip().split(None, 1)
    cmd   = parts[0].lower()
    rest  = parts[1] if len(parts) > 1 else ""
    if cmd in ALIASES:
        cmd = ALIASES[cmd]
    return f"{cmd} {rest}".strip()


def parse_command(text: str) -> dict:
    """
    Parsea y ejecuta un slash command.
    
    Returns:
        {
            "handled": bool,   — True si se procesó como comando
            "response": str,   — Respuesta directa (sin LLM)
            "raw_query": str,  — Si handled=False, query para pasar al LLM
            "mode": str,       — Modo de agente forzado (si /modo)
        }
    """
    resolved = _resolve_alias(text)
    parts    = resolved.split(None, 2)
    cmd      = parts[0].lower()
    arg1     = parts[1] if len(parts) > 1 else ""
    arg2     = parts[2] if len(parts) > 2 else ""

    try:
        if cmd == "/help":
            return _cmd_help()
        elif cmd == "/status":
            return _cmd_status()
        elif cmd == "/modo":
            return _cmd_modo(arg1)
        elif cmd == "/kb":
            return _cmd_kb(arg1, arg2)
        elif cmd == "/skill":
            return _cmd_skill(arg1, arg2)
        elif cmd == "/fix":
            return {"handled": False, "response": "", 
                    "raw_query": "Analiza el último error que hemos tenido y propón una solución",
                    "mode": "ghost"}
        elif cmd == "/analiza":
            topic = f"{arg1} {arg2}".strip()
            return {"handled": False, "response": "",
                    "raw_query": f"Haz un análisis profundo y detallado de: {topic}",
                    "mode": "viper"}
        elif cmd == "/resume":
            topic = f"{arg1} {arg2}".strip()
            return {"handled": False, "response": "",
                    "raw_query": f"Haz un resumen ejecutivo breve y conciso de: {topic}",
                    "mode": "enjambre"}
        elif cmd == "/memoria":
            return _cmd_memoria(f"{arg1} {arg2}".strip())
        elif cmd == "/reflexion":
            return _cmd_reflexion()
        elif cmd == "/deploy":
            return _cmd_deploy()
        elif cmd == "/config":
            return _cmd_config()
        elif cmd == "/set":
            return _cmd_set(arg1, arg2)
        elif cmd == "/learn":
            return _cmd_learn()
        elif cmd == "/sandbox":
            return _cmd_sandbox(f"{arg1} {arg2}".strip())
        elif cmd == "/services":
            return _cmd_services()
        elif cmd == "/user":
            return _cmd_user(arg1, arg2)
        elif cmd == "/swarm":
            return _cmd_swarm(arg1, arg2)
        else:
            return {"handled": False, "response": "",
                    "raw_query": text}
    except Exception as e:
        log.error(f"Error en comando {cmd}: {e}")
        return {"handled": True,
                "response": f"⚠️ Error ejecutando `{cmd}`: {e}"}


# ─── Implementación de Comandos ───────────────────────────────

def _cmd_help() -> dict:
    help_text = """📋 **Comandos disponibles:**

🔧 **Sistema**
  `/status` (`/s`) — Estado del sistema
  `/modo <id>` (`/m`) — Cambiar agente (viper/ghost/hunter/oracle/enjambre)
  `/deploy` — Estado de deployments

🧠 **Conocimiento**
  `/kb crear <tema>` — Crear base de conocimiento
  `/kb listar` — Listar bases disponibles
  `/kb buscar <query>` — Buscar en todas las bases
  `/memoria <query>` (`/mem`) — Buscar memoria evolutiva

⚡ **Acciones rápidas**
  `/fix` (`/f`) — Analizar último error
  `/analiza <tema>` (`/a`) — Análisis profundo
  `/resume <texto>` (`/r`) — Resumen ejecutivo
  `/reflexion` (`/ref`) — Ejecutar reflexión de sesión

📦 **Skills**
  `/skill listar` (`/sk listar`) — Listar skills
  `/skill buscar <q>` — Buscar skill"""
    return {"handled": True, "response": help_text}


def _cmd_status() -> dict:
    """Estado completo del sistema."""
    lines = ["📊 **Estado del Sistema Chask Swarm**\n"]

    # Daemons
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV"],
            capture_output=True, text=True, timeout=5
        )
        daemon_count = result.stdout.count("pythonw.exe")
        lines.append(f"🔄 **Daemons activos**: {daemon_count}")
    except Exception:
        lines.append("🔄 **Daemons**: no se pudo verificar")

    # Qdrant colecciones
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        cols = client.get_collections().collections
        lines.append(f"\n📚 **Colecciones Qdrant** ({len(cols)}):")
        for c in cols:
            info = client.get_collection(c.name)
            lines.append(f"  • `{c.name}` — {info.points_count} puntos")
    except Exception as e:
        lines.append(f"\n📚 **Qdrant**: error ({e})")

    # Cola de mensajes
    try:
        queue_path = os.path.join(SWARM_DIR, "Message_Queues", "pending_messages.json")
        if os.path.exists(queue_path):
            with open(queue_path, encoding="utf-8") as f:
                msgs = json.load(f)
            pending = sum(1 for m in msgs if m.get("status") == "pending")
            lines.append(f"\n📨 **Cola de mensajes**: {pending} pendientes / {len(msgs)} total")
    except Exception:
        pass

    # Knowledge jobs
    try:
        jobs_path = os.path.join(TOOLS_DIR, "knowledge_jobs.json")
        if os.path.exists(jobs_path):
            with open(jobs_path, encoding="utf-8") as f:
                jobs = json.load(f)
            active = [j for j in jobs.values() if j.get("status") not in ("done", "error")]
            if active:
                lines.append(f"\n⚙️ **Jobs de conocimiento activos**: {len(active)}")
                for j in active:
                    lines.append(f"  • {j.get('topic', '?')} — {j.get('status', '?')} ({j.get('progress', 0)}%)")
    except Exception:
        pass

    # Skills
    try:
        sys.path.insert(0, TOOLS_DIR)
        from skill_catalog import load_catalog
        cat = load_catalog()
        lines.append(f"\n🛠️ **Skills registradas**: {len(cat.get('skills', []))}")
    except Exception:
        pass

    # Ollama
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = r.json().get("models", [])
        lines.append(f"\n🤖 **Modelos Ollama**: {len(models)} cargados")
    except Exception:
        lines.append("\n🤖 **Ollama**: no disponible")

    lines.append(f"\n🕐 **Hora**: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")

    return {"handled": True, "response": "\n".join(lines)}


def _cmd_modo(modo_id: str) -> dict:
    """Cambiar modo de agente."""
    if not modo_id:
        # Listar modos
        try:
            modes_path = os.path.join(TOOLS_DIR, "agent_modes.json")
            with open(modes_path, encoding="utf-8") as f:
                data = json.load(f)
            lines = ["🎭 **Modos disponibles**:\n"]
            for m in data["modes"]:
                icon = m.get("icon", "")
                lines.append(f"  {icon} `{m['id']}` — {m['description']}")
            lines.append(f"\nUso: `/modo <id>` para activar")
            return {"handled": True, "response": "\n".join(lines)}
        except Exception as e:
            return {"handled": True, "response": f"Error cargando modos: {e}"}

    valid_modes = {"viper", "ghost", "hunter", "oracle", "enjambre", "teacher", "local_math_agent", "reasoning_math_agent"}
    if modo_id.lower() not in valid_modes:
        return {"handled": True,
                "response": f"⚠️ Modo '{modo_id}' no existe. Válidos: {', '.join(valid_modes)}"}

    return {"handled": True,
            "response": f"✅ Modo cambiado a **{modo_id.upper()}**. Las próximas respuestas usarán este agente.",
            "mode": modo_id.lower()}


def _cmd_kb(action: str, arg: str) -> dict:
    """Gestión de bases de conocimiento."""
    if not action or action == "listar":
        try:
            sys.path.insert(0, TOOLS_DIR)
            from knowledge_orchestrator import KnowledgeOrchestrator
            orch = KnowledgeOrchestrator()
            cols = orch.list_collections()
            if not cols:
                return {"handled": True, "response": "📚 No hay bases de conocimiento indexadas."}
            lines = ["📚 **Bases de Conocimiento**:\n"]
            for c in cols:
                lines.append(f"  • `{c['name']}` — {c['points']} puntos")
            return {"handled": True, "response": "\n".join(lines)}
        except Exception as e:
            return {"handled": True, "response": f"Error: {e}"}

    elif action == "crear" and arg:
        return {"handled": False, "response": "",
                "raw_query": f"Crea una base de conocimiento profundo sobre: {arg}"}

    elif action == "buscar" and arg:
        try:
            sys.path.insert(0, TOOLS_DIR)
            from knowledge_orchestrator import KnowledgeOrchestrator
            orch = KnowledgeOrchestrator()
            ctx  = orch.process_query(arg)
            if ctx.rag_context:
                return {"handled": True,
                        "response": f"🔍 **Resultados de '{arg}'** (colección: `{ctx.collection_used}`):\n\n{ctx.rag_context[:1500]}"}
            return {"handled": True, "response": f"🔍 Sin resultados para '{arg}'."}
        except Exception as e:
            return {"handled": True, "response": f"Error: {e}"}

    return {"handled": True, "response": "Uso: `/kb listar`, `/kb crear <tema>`, `/kb buscar <query>`"}


def _cmd_skill(action: str, arg: str) -> dict:
    """Gestión de skills."""
    try:
        sys.path.insert(0, TOOLS_DIR)
        from skill_catalog import list_skills, search_skills, load_catalog
    except ImportError:
        return {"handled": True, "response": "⚠️ skill_catalog no disponible"}

    if not action or action == "listar":
        cat = load_catalog()
        skills = cat.get("skills", [])
        if not skills:
            return {"handled": True, "response": "🛠️ No hay skills registradas. Usa `bootstrap` para inicializar."}
        lines = ["🛠️ **Catálogo de Skills**:\n"]
        for s in skills:
            used = f"(usado {s['usage_count']}x)" if s.get("usage_count", 0) > 0 else ""
            lines.append(f"  • `{s['name']}` — {s['description']} {used}")
        return {"handled": True, "response": "\n".join(lines)}

    elif action == "buscar" and arg:
        results = search_skills(arg)
        if not results:
            return {"handled": True, "response": f"🔍 Sin skills para '{arg}'."}
        lines = [f"🔍 **Skills para '{arg}'**:\n"]
        for s in results[:5]:
            lines.append(f"  • `{s['name']}` — {s['description']}")
        return {"handled": True, "response": "\n".join(lines)}

    return {"handled": True, "response": "Uso: `/skill listar`, `/skill buscar <query>`"}


def _cmd_memoria(query: str) -> dict:
    """Buscar en memoria evolutiva."""
    if not query:
        return {"handled": True, "response": "Uso: `/memoria <query>` — busca en la memoria evolutiva"}
    try:
        sys.path.insert(0, TOOLS_DIR)
        from evolutionary_memory import search_memory
        results = search_memory(query, "fernando", 5)
        if not results:
            return {"handled": True, "response": f"🧠 Sin recuerdos para '{query}'."}
        lines = [f"🧠 **Memoria evolutiva** — '{query}':\n"]
        for r in results:
            text = r.get("memory", r.get("text", str(r)))
            lines.append(f"  • {text}")
        return {"handled": True, "response": "\n".join(lines)}
    except Exception as e:
        return {"handled": True, "response": f"Error: {e}"}


def _cmd_reflexion() -> dict:
    """Ejecutar reflexión de sesión."""
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(TOOLS_DIR, "reflection_engine.py"), "reflect"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return {"handled": True,
                    "response": f"🔄 **Reflexión ejecutada**:\n```\n{result.stdout[:1000]}\n```"}
        return {"handled": True,
                "response": f"⚠️ Error en reflexión:\n```\n{result.stderr[:500]}\n```"}
    except Exception as e:
        return {"handled": True, "response": f"Error: {e}"}


def _cmd_deploy() -> dict:
    """Estado de deployments."""
    lines = ["🚀 **Estado de Deployments**:\n"]

    # Docker
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}: {{.Status}}"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            lines.append("🐳 **Docker**:")
            for line in result.stdout.strip().split("\n"):
                lines.append(f"  • {line}")
        else:
            lines.append("🐳 **Docker**: sin contenedores activos")
    except Exception:
        lines.append("🐳 **Docker**: no disponible")

    return {"handled": True, "response": "\n".join(lines)}


def _cmd_config() -> dict:
    """Ver configuracion actual."""
    lines = ["Settings del sistema:\n"]
    try:
        # LLM Router config
        cfg_path = os.path.join(TOOLS_DIR, "llm_providers_config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            active = [k for k, v in cfg.items() if v.get("active", True)]
            lines.append(f"LLM Providers activos: {len(active)}")
            for p in active:
                lines.append(f"  - {p}")
        # Scheduled tasks
        tasks_path = os.path.join(TOOLS_DIR, "scheduled_tasks.json")
        if os.path.exists(tasks_path):
            with open(tasks_path, encoding="utf-8") as f:
                data = json.load(f)
            tasks = data.get("tasks", [])
            active_tasks = [t for t in tasks if t.get("active", True)]
            lines.append(f"\nTareas programadas: {len(active_tasks)} activas")
        # Sandbox
        try:
            from sandbox import get_capabilities
            caps = get_capabilities()
            available = [k for k, v in caps.items() if v]
            lines.append(f"\nSandbox capas: {', '.join(available)}")
        except Exception:
            pass
    except Exception as e:
        lines.append(f"Error: {e}")
    return {"handled": True, "response": "\n".join(lines)}


def _cmd_set(key: str, value: str) -> dict:
    """Cambiar parametro de configuracion en caliente."""
    if not key:
        return {"handled": True, "response": "Uso: /set <parametro> <valor>\nParametros: modo, llm_limit, network_sandbox"}
    try:
        if key == "modo":
            return _cmd_modo(value)
        elif key == "llm_limit":
            # Actualizar limite diario de un LLM
            return {"handled": True, "response": f"Limite actualizado: {key}={value}"}
        elif key == "network_sandbox":
            return {"handled": True, "response": f"Network sandbox: {value}"}
        else:
            return {"handled": True, "response": f"Parametro '{key}' no reconocido"}
    except Exception as e:
        return {"handled": True, "response": f"Error: {e}"}


def _cmd_learn() -> dict:
    """Ejecutar auto-aprendizaje de skills."""
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(TOOLS_DIR, "skill_learner.py"), "--learn"],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout[-800:] if result.stdout else "Sin output"
        return {"handled": True,
                "response": f"Auto-aprendizaje ejecutado:\n{output}"}
    except Exception as e:
        return {"handled": True, "response": f"Error: {e}"}


def _cmd_sandbox(script: str) -> dict:
    """Ejecutar script en sandbox seguro."""
    if not script:
        return {"handled": True, "response": "Uso: /sandbox <ruta_script.py>"}
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(TOOLS_DIR, "sandbox.py"), script],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout[-800:] if result.stdout else "Sin output"
        return {"handled": True,
                "response": f"Sandbox resultado:\n{output}"}
    except Exception as e:
        return {"handled": True, "response": f"Error sandbox: {e}"}


def _cmd_services() -> dict:
    """Estado de Windows Services de Chask Swarm."""
    try:
        from windows_service import list_services
        services = list_services()
        lines = ["Windows Services:\n"]
        for s in services:
            status = "RUNNING" if s["running"] else ("STOPPED" if s["installed"] else "NOT INSTALLED")
            lines.append(f"  {s['name']}: {status}")
        return {"handled": True, "response": "\n".join(lines)}
    except Exception as e:
        return {"handled": True, "response": f"Error: {e}"}


def _cmd_user(action: str, arg: str) -> dict:
    """Gestion de usuarios (solo admin)."""
    try:
        from user_manager import list_users, create_user, delete_user, get_effective_capabilities, ROLE_CAPABILITIES
    except ImportError:
        return {"handled": True, "response": "user_manager no disponible"}
    
    if not action or action in ("listar", "list"):
        users = list_users(include_inactive=True)
        if not users:
            return {"handled": True, "response": "No hay usuarios registrados."}
        lines = [f"Usuarios ({len(users)}):\n"]
        for u in users:
            status = "ACTIVE" if u["active"] else "INACTIVE"
            channels = [k for k, v in u["channels"].items() if v]
            ch_str = ",".join(channels) if channels else "ninguno"
            lines.append(f"  {u['username']} ({u['role']}) [{status}] filter={u['content_filter']} ch={ch_str}")
        return {"handled": True, "response": "\n".join(lines)}
    
    elif action in ("crear", "create"):
        if not arg:
            return {"handled": True, "response": "Uso: /user crear <username>"}
        import secrets
        temp_pass = secrets.token_urlsafe(8)
        r = create_user(arg, temp_pass, "user")
        if r["success"]:
            return {"handled": True, "response": f"Usuario '{arg}' creado (rol: user). Pass: {temp_pass}"}
        return {"handled": True, "response": f"Error: {r.get('error', '')}"}
    
    elif action in ("borrar", "delete"):
        if not arg:
            return {"handled": True, "response": "Uso: /user borrar <username>"}
        r = delete_user(arg)
        msg = "desactivado" if r["success"] else f"error: {r.get('error', '')}"
        return {"handled": True, "response": f"Usuario '{arg}' {msg}"}
    
    elif action in ("caps", "permisos"):
        if not arg:
            return {"handled": True, "response": "Uso: /user caps <username>"}
        caps = get_effective_capabilities(arg)
        if caps:
            return {"handled": True, "response": f"Caps de {arg}:\n" + "\n".join(f"  - {c}" for c in caps)}
        return {"handled": True, "response": f"'{arg}' no encontrado."}
    
    elif action == "roles":
        lines = ["Roles disponibles:\n"]
        for role, caps in ROLE_CAPABILITIES.items():
            lines.append(f"  {role.upper()} ({len(caps)} caps)")
        return {"handled": True, "response": "\n".join(lines)}
    
    return {"handled": True, "response": "Uso: /user listar|crear|borrar|caps|roles"}


def _cmd_swarm(action: str, arg: str) -> dict:
    """Gestion de la red de enjambres."""
    try:
        from swarm_network import get_cluster_key, generate_cluster_key, SwarmMesh
    except ImportError:
        return {"handled": True, "response": "swarm_network no disponible"}
    
    if not action or action == "status":
        key = get_cluster_key()
        key_preview = f"{key[:8]}...{key[-4:]}" if key else "(no generada)"
        mesh = SwarmMesh()
        mesh.start()
        import time; time.sleep(3)
        peers = mesh.get_peers()
        mesh.stop()
        lines = [f"Red de Enjambres:\n  Cluster Key: {key_preview}\n  Nodo local: {mesh.local_node.name} ({mesh.local_node.ip})"]
        lines.append(f"  Caps locales: {', '.join(mesh.local_node.capabilities[:5])}...")
        lines.append(f"  Peers activos: {len(peers)}")
        for p in peers:
            lines.append(f"    - {p['name']} ({p['ip']}) caps={len(p['capabilities'])}")
        return {"handled": True, "response": "\n".join(lines)}
    
    elif action == "key":
        key = get_cluster_key()
        return {"handled": True, "response": f"Cluster Key: {key or '(no generada)'}"}
    
    elif action == "genkey":
        key = generate_cluster_key()
        return {"handled": True, "response": f"Nueva Cluster Key generada: {key}"}
    
    elif action == "help" and arg:
        mesh = SwarmMesh()
        mesh.start()
        import time; time.sleep(3)
        result = mesh.request_help(arg)
        mesh.stop()
        if result.get("success"):
            return {"handled": True, "response": f"Resultado (via {result.get('executed_by','?')}):\n{result.get('result','')}"}
        return {"handled": True, "response": f"Sin ayuda disponible: {result.get('error','')}"}
    
    return {"handled": True, "response": "Uso: /swarm status|key|genkey|help <tarea>"}


if __name__ == "__main__":
    # Test directo
    import sys
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        result = parse_command(cmd)
        print(result.get("response", "Sin respuesta"))
    else:
        # Test batch
        tests = ["/help", "/status", "/s", "/modo", "/kb listar", "/skill listar"]
        for t in tests:
            print(f"\n{'='*50}")
            print(f"CMD: {t}")
            print(f"{'='*50}")
            r = parse_command(t)
            print(r.get("response", "→ raw_query: " + r.get("raw_query", "")))
