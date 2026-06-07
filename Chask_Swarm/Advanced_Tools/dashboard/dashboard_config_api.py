"""
dashboard_config_api.py — API REST para configuracion desde el Panel de Control
=================================================================================
Endpoints para gestionar TODA la configuracion de Chask Swarm desde la web.
Se registra como Blueprint de Flask en web_dashboard.py.

Secciones:
  /api/users/*        — Gestion de usuarios (CRUD, roles, capacidades)
  /api/network/*      — Red LAN de enjambres
  /api/internet/*     — Internet de Enjambres (hub, enrutadores, opt-in/out)
  /api/filter/*       — Filtro parental
  /api/config/*       — Configuracion general del sistema
  /api/services/*     — Windows Services
  /api/llm/*          — Configuracion de LLM providers
"""
import os
import sys
import json
from pathlib import Path
from flask import Blueprint, request, jsonify, session

ROOT = Path(r"C:\Program Files\Chask_Swarm")
TOOLS = ROOT / "Advanced_Tools"
sys.path.insert(0, str(TOOLS))

config_api = Blueprint('config_api', __name__)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


# ═══════════════════════════════════════════════════════════
# USUARIOS
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/users", methods=["GET"])
def api_users_list():
    current_username = session.get("username")
    role = session.get("role", "guest")
    
    if not current_username:
        return jsonify({"success": False, "error": "Acceso denegado: Inicie sesión."})
        
    if role in ["child", "guest"]:
        return jsonify([])
        
    from user_manager import list_users
    user_list = []
    
    # 1. Cargar usuarios reales de la base de datos (user_manager)
    try:
        real_users = list_users(include_inactive=False)
        for ru in real_users:
            # Si no es admin y no es su propio usuario, ignorarlo
            if role != "admin" and ru["username"] != current_username:
                continue
            channels = []
            if ru["channels"].get("telegram"): channels.append("Telegram")
            if ru["channels"].get("discord"): channels.append("Discord")
            if ru["channels"].get("email"): channels.append("Email")
            
            user_list.append({
                "username": ru["username"],
                "display_name": ru["display_name"],
                "role": ru["role"],
                "telegram_id": ru["channels"].get("telegram_id", ""),
                "discord_id": ru["channels"].get("discord_id", ""),
                "type": "human",
                "channels": channels,
                "status": "Online" if ru["login_count"] > 0 or ru["username"] == "admin" else "Idle",
                "last_active": "Recientemente" if ru["last_login"] else "Nunca",
                "task": "Administración del sistema" if ru["username"] == "admin" else None
            })
    except Exception as e:
        print(f"[Dashboard] Error leyendo user_manager: {e}")
        
    # Fernando por defecto si no se pudo cargar y es admin
    if role == "admin":
        if not any(u["username"] == "admin" for u in user_list):
            user_list.append({
                "username": "admin",
                "display_name": "Fernando",
                "role": "admin",
                "type": "human",
                "channels": ["Telegram"],
                "status": "Online",
                "last_active": "Hace 1 min",
                "task": "Administración del sistema"
            })
            
        # 2. Agregar agentes especializados del ecosistema
        agents = [
            {"username": "enjambre", "display_name": "Enjambre Chask", "role": "Orchestrator Core", "channels": ["Telegram", "Web", "IDE"], "status": "Online", "last_active": "En ejecución", "task": "Supervisión de daemons y cola"},
            {"username": "viper", "display_name": "Viper", "role": "Arquitecto de Software", "channels": ["Local Daemon"], "status": "Online", "last_active": "Activo", "task": "Diseño de microservicios"},
            {"username": "ghost", "display_name": "Ghost", "role": "Desarrollador Core", "channels": ["Local Daemon"], "status": "Online", "last_active": "Activo", "task": "Compilación y despliegue"},
            {"username": "hunter", "display_name": "Hunter", "role": "Growth & Sales", "channels": ["External Sync"], "status": "Idle", "last_active": "Hace 2 horas", "task": "Monitoreo del mercado"},
            {"username": "oracle", "display_name": "Oracle", "role": "Compliance & Data", "channels": ["Memory Vectorial"], "status": "Online", "last_active": "En espera", "task": "Indexación y auditoría de seguridad"},
            {"username": "elektra", "display_name": "Elektra", "role": "Asistente Técnica", "channels": ["Telegram"], "status": "Online", "last_active": "En espera", "task": "Auditoría de maquetas corporativas"},
            {"username": "orestes", "display_name": "Orestes", "role": "Despliegue y Localización", "channels": ["FTP Adapter"], "status": "Online", "last_active": "En ejecución", "task": "Sincronización a chask.fun (40 idiomas)"}
        ]
        
        for ag in agents:
            user_list.append({
                "username": ag["username"],
                "display_name": ag["display_name"],
                "role": ag["role"],
                "type": "agent",
                "channels": ag["channels"],
                "status": ag["status"],
                "last_active": ag["last_active"],
                "task": ag["task"]
            })
        
    return jsonify(user_list)

@config_api.route("/api/users", methods=["POST"])
def api_users_create():
    current_username = session.get("username")
    role = session.get("role", "guest")
    
    if not current_username or role != "admin":
        return jsonify({"success": False, "error": "Acceso denegado: Solo el Administrador puede registrar usuarios."})
        
    data = request.json or {}
    from user_manager import create_user
    r = create_user(
        username=data.get("username", ""),
        password=data.get("password", ""),
        role=data.get("role", "user"),
        display_name=data.get("display_name", ""),
        age=data.get("age"),
        telegram_id=data.get("telegram_id", ""),
        discord_id=data.get("discord_id", ""),
        email=data.get("email", "")
    )
    return jsonify(r)

@config_api.route("/api/users/<username>", methods=["PUT"])
def api_users_update(username):
    current_username = session.get("username")
    role = session.get("role", "guest")
    
    if not current_username:
        return jsonify({"success": False, "error": "Acceso denegado: Inicie sesión."})
        
    if username == "admin":
        # Bloquear degradación de rol del admin principal
        data = request.json or {}
        if data.get("role") and data.get("role") != "admin":
            return jsonify({"success": False, "error": "No se permite cambiar el rol del administrador principal."})
            
    # Si no es administrador, aplicar restricciones de auto-gestión
    if role != "admin":
        if username != current_username:
            return jsonify({"success": False, "error": "Acceso denegado: Solo puedes modificar tu propio usuario."})
        data = request.json or {}
        if "role" in data and data["role"] != role:
            return jsonify({"success": False, "error": "Acceso denegado: No puedes alterar tu propio rol de usuario."})
            
    data = request.json or {}
    new_username = data.pop("username", None) # Capturar el nuevo username enviado en el formulario
    
    if username == "admin":
        if new_username and new_username != "admin":
            return jsonify({"success": False, "error": "No se permite renombrar al administrador principal."})
            
    if new_username and new_username != username:
        data["new_username"] = new_username
        
    # El usuario normal no puede modificar su propio rol
    if role != "admin" and "role" in data:
        data.pop("role")
        
    from user_manager import update_user
    return jsonify(update_user(username, **data))

@config_api.route("/api/users/<username>", methods=["DELETE"])
def api_users_delete(username):
    current_username = session.get("username")
    role = session.get("role", "guest")
    
    if not current_username or role != "admin":
        return jsonify({"success": False, "error": "Acceso denegado: Solo el Administrador puede eliminar usuarios."})
        
    if username == "admin":
        return jsonify({"success": False, "error": "No se puede eliminar al administrador principal."})
    from user_manager import delete_user
    return jsonify(delete_user(username))

@config_api.route("/api/users/<username>/caps", methods=["GET"])
def api_users_caps(username):
    from user_manager import get_effective_capabilities
    return jsonify({"capabilities": get_effective_capabilities(username)})

@config_api.route("/api/users/<username>/caps", methods=["POST"])
def api_users_add_cap(username):
    data = request.json or {}
    from user_manager import add_capability
    return jsonify(add_capability(username, data.get("capability", "")))

@config_api.route("/api/users/<username>/caps", methods=["DELETE"])
def api_users_remove_cap(username):
    data = request.json or {}
    from user_manager import remove_capability
    return jsonify(remove_capability(username, data.get("capability", "")))

@config_api.route("/api/roles", methods=["GET"])
def api_roles():
    from user_manager import ROLE_CAPABILITIES, ALL_CAPABILITIES
    return jsonify({"roles": ROLE_CAPABILITIES, "all_capabilities": ALL_CAPABILITIES})


# ═══════════════════════════════════════════════════════════
# RED LAN (swarm_network)
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/network/lan", methods=["GET"])
def api_network_lan():
    cfg = _load_json(ROOT / "Configuracion/swarm_network_config.json")
    key = cfg.get("cluster_key", "")
    return jsonify({
        "cluster_key_preview": f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "(no generada)",
        "discovery_port": 51337,
        "comm_port": 51338,
    })

@config_api.route("/api/network/lan/genkey", methods=["POST"])
def api_network_genkey():
    from swarm_network import generate_cluster_key
    key = generate_cluster_key()
    return jsonify({"success": True, "cluster_key": key})


# ═══════════════════════════════════════════════════════════
# INTERNET DE ENJAMBRES (swarm_internet)
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/network/internet", methods=["GET"])
def api_network_internet():
    cfg = _load_json(ROOT / "Configuracion/swarm_internet_config.json")
    return jsonify(cfg)

@config_api.route("/api/network/internet", methods=["PUT"])
def api_network_internet_update():
    data = request.json or {}
    cfg = _load_json(ROOT / "Configuracion/swarm_internet_config.json")
    allowed_keys = ["hub_url", "api_key", "is_router", "heartbeat_minutes",
                    "max_hops", "inter_swarm_free_only", "global_network_enabled"]
    for k in allowed_keys:
        if k in data:
            cfg[k] = data[k]
    _save_json(ROOT / "Configuracion/swarm_internet_config.json", cfg)
    return jsonify({"success": True, "config": cfg})


# ═══════════════════════════════════════════════════════════
# FILTRO PARENTAL
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/filter/test", methods=["POST"])
def api_filter_test():
    data = request.json or {}
    from content_filter import check_content
    result = check_content(data.get("text", ""), data.get("level", "strict"))
    return jsonify(result)

@config_api.route("/api/filter/log", methods=["GET"])
def api_filter_log():
    log_path = ROOT / "content_filter_log.json"
    logs = _load_json(log_path) if log_path.exists() else []
    if isinstance(logs, dict):
        logs = []
    return jsonify({"logs": logs[-50:]})


# ═══════════════════════════════════════════════════════════
# CONFIGURACION GENERAL
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/config/telegram", methods=["GET"])
def api_config_telegram():
    cfg = _load_json(ROOT / "Configuracion/master_credentials.json")
    creds = cfg.get("credentials", {})
    return jsonify({
        "telegram_bot": creds.get("telegram_bot", ""),
        "telegram_admin": creds.get("telegram_admin", "")
    })

@config_api.route("/api/config/telegram", methods=["PUT"])
def api_config_telegram_update():
    data = request.json or {}
    cfg = _load_json(ROOT / "Configuracion/master_credentials.json")
    if "credentials" not in cfg:
        cfg["credentials"] = {}
    
    if "telegram_bot" in data:
        cfg["credentials"]["telegram_bot"] = data["telegram_bot"]
    if "telegram_admin" in data:
        cfg["credentials"]["telegram_admin"] = data["telegram_admin"]
        
    _save_json(ROOT / "Configuracion/master_credentials.json", cfg)
    return jsonify({"success": True})
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/config/llm", methods=["GET"])
def api_config_llm():
    cfg = _load_json(TOOLS / "llm_providers_config.json")
    return jsonify(cfg)

@config_api.route("/api/config/llm", methods=["PUT"])
def api_config_llm_update():
    data = request.json or {}
    _save_json(TOOLS / "llm_providers_config.json", data)
    return jsonify({"success": True})

@config_api.route("/api/config/channels", methods=["GET"])
def api_config_channels():
    cfg = _load_json(ROOT / "Configuracion/channels_config.json")
    return jsonify(cfg)

@config_api.route("/api/config/channels", methods=["PUT"])
def api_config_channels_update():
    data = request.json or {}
    _save_json(ROOT / "Configuracion/channels_config.json", data)
    return jsonify({"success": True})

@config_api.route("/api/config/scheduler", methods=["GET"])
def api_config_scheduler():
    cfg = _load_json(TOOLS / "scheduled_tasks.json")
    return jsonify(cfg)

@config_api.route("/api/config/scheduler", methods=["PUT"])
def api_config_scheduler_update():
    data = request.json or {}
    _save_json(TOOLS / "scheduled_tasks.json", data)
    return jsonify({"success": True})

@config_api.route("/api/config/email", methods=["GET"])
def api_config_email():
    cfg = _load_json(TOOLS / "email_config.json")
    # Ocultar password
    if "password" in cfg:
        cfg["password"] = "********"
    return jsonify(cfg)

@config_api.route("/api/config/email", methods=["PUT"])
def api_config_email_update():
    data = request.json or {}
    current = _load_json(TOOLS / "email_config.json")
    for k, v in data.items():
        if k == "password" and v == "********":
            continue  # No sobreescribir con placeholder
        current[k] = v
    _save_json(TOOLS / "email_config.json", current)
    return jsonify({"success": True})


# ═══════════════════════════════════════════════════════════
# SERVICES
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/services", methods=["GET"])
def api_services():
    try:
        from windows_service import list_services
        return jsonify({"services": list_services()})
    except Exception as e:
        return jsonify({"error": str(e)})

@config_api.route("/api/services/<name>/start", methods=["POST"])
def api_services_start(name):
    try:
        from windows_service import start_service
        return jsonify(start_service(name))
    except Exception as e:
        return jsonify({"error": str(e)})

@config_api.route("/api/services/<name>/stop", methods=["POST"])
def api_services_stop(name):
    try:
        from windows_service import stop_service
        return jsonify(stop_service(name))
    except Exception as e:
        return jsonify({"error": str(e)})


# ═══════════════════════════════════════════════════════════
# OVERVIEW — Estado completo para el dashboard
# ═══════════════════════════════════════════════════════════

@config_api.route("/api/overview", methods=["GET"])
def api_overview():
    """Resumen completo del sistema para el panel principal."""
    import subprocess

    # Daemons
    daemons = 0
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV"],
                          capture_output=True, text=True, timeout=5)
        daemons = r.stdout.count("pythonw.exe")
    except Exception:
        pass

    # Users
    users = 0
    try:
        from user_manager import list_users
        users = len(list_users())
    except Exception:
        pass

    # Qdrant
    qdrant = 0
    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(host="localhost", port=6333, timeout=3)
        for col in qc.get_collections().collections:
            qdrant += qc.get_collection(col.name).points_count
    except Exception:
        pass

    # Internet
    inet = _load_json(ROOT / "Configuracion/swarm_internet_config.json")
    routers = _load_json(ROOT / "cached_routers.json")
    if not isinstance(routers, list):
        routers = []

    return jsonify({
        "daemons": daemons,
        "users": users,
        "qdrant_points": qdrant,
        "global_network": inet.get("global_network_enabled", True),
        "cached_routers": len(routers),
        "free_only": inet.get("inter_swarm_free_only", True),
        "timestamp": __import__("datetime").datetime.now().isoformat()
    })
