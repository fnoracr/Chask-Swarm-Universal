"""
user_manager.py — Sistema Multiusuario de Chask Swarm
======================================================
CRUD completo de usuarios con roles, permisos, canales vinculados,
categorias de edad, y sesiones aisladas.

Roles predefinidos:
  - admin:  Control total del sistema
  - power:  Acceso a todas las capacidades excepto gestion de usuarios
  - user:   Acceso a skills, LLM, memoria personal
  - child:  Usuario menor con filtro parental activo
  - teen:   Adolescente con filtro parental moderado
  - guest:  Solo consultas basicas, sin persistencia

Capacidades granulares:
  - llm_chat, llm_vision, skill_run, skill_create, skill_learn,
  - memory_read, memory_write, kb_create, kb_search,
  - sandbox_run, deploy, system_status, scheduler_manage,
  - services_manage, user_manage, config_write, audit_read
"""
import os
import sys
import io
import json
import hashlib
import uuid
import secrets
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(r"C:\Program Files\Chask_Swarm")
USERS_FILE = ROOT / "Configuracion/users.json"
SESSIONS_DIR = ROOT / "user_sessions"

# ─── Roles y sus capacidades por defecto ──────────────────
ROLE_CAPABILITIES = {
    "admin": [
        "llm_chat", "llm_vision", "skill_run", "skill_create", "skill_learn",
        "memory_read", "memory_write", "kb_create", "kb_search",
        "sandbox_run", "deploy", "system_status", "scheduler_manage",
        "services_manage", "user_manage", "config_write", "audit_read",
        "file_access", "telegram_send", "discord_send", "email_send"
    ],
    "power": [
        "llm_chat", "llm_vision", "skill_run", "skill_create", "skill_learn",
        "memory_read", "memory_write", "kb_create", "kb_search",
        "sandbox_run", "deploy", "system_status", "audit_read",
        "file_access", "telegram_send", "discord_send", "email_send"
    ],
    "user": [
        "llm_chat", "llm_vision", "skill_run",
        "memory_read", "memory_write", "kb_search",
        "system_status", "telegram_send", "discord_send"
    ],
    "teen": [
        "llm_chat", "skill_run",
        "memory_read", "memory_write", "kb_search",
        "system_status"
    ],
    "child": [
        "llm_chat", "skill_run",
        "memory_read", "kb_search"
    ],
    "guest": [
        "llm_chat", "system_status"
    ]
}

ALL_CAPABILITIES = sorted(set(cap for caps in ROLE_CAPABILITIES.values() for cap in caps))

# ─── Age categories ──────────────────────────────────────
AGE_CATEGORIES = {
    "child": {"min_age": 0, "max_age": 12, "content_filter": "strict", "role": "child"},
    "teen":  {"min_age": 13, "max_age": 17, "content_filter": "moderate", "role": "teen"},
    "adult": {"min_age": 18, "max_age": 999, "content_filter": "none", "role": "user"},
}


def _hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed.hex(), salt


def load_users() -> dict:
    """Load users database."""
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"users": {}, "meta": {"created": datetime.now().isoformat(), "version": "1.0"}}


def save_users(data: dict):
    """Save users database."""
    data["meta"]["last_modified"] = datetime.now().isoformat()
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def create_user(username: str, password: str, role: str = "user",
                display_name: str = "", age: int = None,
                telegram_id: str = "", discord_id: str = "",
                email: str = "", created_by: str = "admin") -> dict:
    """
    Crear un nuevo usuario.
    
    Args:
        username: ID unico del usuario
        password: Contrasena (se hashea)
        role: Rol (admin/power/user/teen/child/guest)
        display_name: Nombre visible
        age: Edad (determina categoria si role no es explicito)
        telegram_id: ID de Telegram vinculado
        discord_id: ID de Discord vinculado
        email: Email vinculado
        created_by: Quien lo creo (audit)
    """
    data = load_users()
    
    if username in data["users"]:
        return {"success": False, "error": f"Usuario '{username}' ya existe"}
    
    if role not in ROLE_CAPABILITIES:
        return {"success": False, "error": f"Rol '{role}' no existe. Validos: {', '.join(ROLE_CAPABILITIES.keys())}"}
    
    # Auto-detect role from age if child/teen
    if age is not None:
        for cat_name, cat in AGE_CATEGORIES.items():
            if cat["min_age"] <= age <= cat["max_age"]:
                if cat_name in ("child", "teen") and role not in ("child", "teen"):
                    role = cat["role"]
                break
    
    pwd_hash, salt = _hash_password(password)
    
    user = {
        "id": str(uuid.uuid4())[:8],
        "username": username,
        "display_name": display_name or username,
        "role": role,
        "capabilities": list(ROLE_CAPABILITIES.get(role, [])),
        "custom_capabilities": [],  # Additional caps beyond role
        "blocked_capabilities": [], # Caps removed from role defaults
        "age": age,
        "age_category": _get_age_category(age) if age else ("child" if role == "child" else "adult"),
        "content_filter": _get_content_filter(age, role),
        "channels": {
            "telegram_id": str(telegram_id) if telegram_id else "",
            "discord_id": str(discord_id) if discord_id else "",
            "email": email,
            "web_token": secrets.token_urlsafe(32),
        },
        "password_hash": pwd_hash,
        "password_salt": salt,
        "active": True,
        "created_at": datetime.now().isoformat(),
        "created_by": created_by,
        "last_login": None,
        "login_count": 0,
        "session_count": 0
    }
    
    data["users"][username] = user
    save_users(data)
    
    # Create user session directory
    user_dir = SESSIONS_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "memory.md").write_text(f"# Memoria de {display_name or username}\n", encoding="utf-8")
    (user_dir / "preferences.json").write_text("{}", encoding="utf-8")
    
    return {"success": True, "user": username, "role": role, "id": user["id"]}


def _get_age_category(age: int) -> str:
    if age is None:
        return "adult"
    for cat_name, cat in AGE_CATEGORIES.items():
        if cat["min_age"] <= age <= cat["max_age"]:
            return cat_name
    return "adult"


def _get_content_filter(age: int, role: str) -> str:
    if role == "child":
        return "strict"
    elif role == "teen":
        return "moderate"
    elif age is not None:
        cat = _get_age_category(age)
        return AGE_CATEGORIES.get(cat, {}).get("content_filter", "none")
    return "none"


def delete_user(username: str) -> dict:
    """Eliminar un usuario (soft delete)."""
    if username == "admin":
        return {"success": False, "error": "No se puede eliminar al administrador maestro."}
        
    data = load_users()
    if username not in data["users"]:
        return {"success": False, "error": "Usuario no encontrado"}
    data["users"][username]["active"] = False
    data["users"][username]["deleted_at"] = datetime.now().isoformat()
    save_users(data)
    return {"success": True, "user": username}


def update_user(username: str, **kwargs) -> dict:
    """Actualizar campos de un usuario."""
    if username == "admin":
        if kwargs.get("role") and kwargs.get("role") != "admin":
            return {"success": False, "error": "No se puede cambiar el rol del administrador maestro."}
        if kwargs.get("new_username") and kwargs.get("new_username") != "admin":
            return {"success": False, "error": "No se puede cambiar el ID de usuario del administrador maestro."}
            
    data = load_users()
    if username not in data["users"]:
        return {"success": False, "error": "Usuario no encontrado"}
        
    new_username = kwargs.get("new_username")
    if new_username and new_username != username:
        if new_username in data["users"]:
            return {"success": False, "error": "El nuevo ID de usuario ya está registrado."}
    
    user = data["users"][username]
    
    # Aplicar cambios a los canales y campos normales
    for key, value in kwargs.items():
        if key == "password":
            pwd_hash, salt = _hash_password(value)
            user["password_hash"] = pwd_hash
            user["password_salt"] = salt
        elif key == "role":
            if value in ROLE_CAPABILITIES:
                user["role"] = value
                user["capabilities"] = list(ROLE_CAPABILITIES[value])
        elif key in ("display_name", "age", "active", "email"):
            user[key] = value
            if key == "age" and value is not None:
                user["age_category"] = _get_age_category(value)
                user["content_filter"] = _get_content_filter(value, user["role"])
        elif key == "telegram_id":
            user["channels"]["telegram_id"] = str(value)
        elif key == "discord_id":
            user["channels"]["discord_id"] = str(value)
    
    if new_username and new_username != username:
        user["username"] = new_username
        data["users"][new_username] = user
        del data["users"][username]
        
        # Renombrar directorio de sesión para no perder su memoria y soul
        old_dir = SESSIONS_DIR / username
        new_dir = SESSIONS_DIR / new_username
        if old_dir.exists():
            try:
                old_dir.rename(new_dir)
            except Exception as e:
                print(f"[UserManager] Error al renombrar dir de sesión: {e}")
                
        save_users(data)
        return {"success": True, "user": new_username}
    else:
        data["users"][username] = user
        save_users(data)
        return {"success": True, "user": username}


def add_capability(username: str, capability: str) -> dict:
    """Anadir una capacidad extra a un usuario."""
    data = load_users()
    if username not in data["users"]:
        return {"success": False, "error": "Usuario no encontrado"}
    if capability not in ALL_CAPABILITIES:
        return {"success": False, "error": f"Capacidad '{capability}' no existe"}
    
    user = data["users"][username]
    if capability not in user["custom_capabilities"]:
        user["custom_capabilities"].append(capability)
    if capability in user["blocked_capabilities"]:
        user["blocked_capabilities"].remove(capability)
    save_users(data)
    return {"success": True}


def remove_capability(username: str, capability: str) -> dict:
    """Quitar una capacidad a un usuario."""
    data = load_users()
    if username not in data["users"]:
        return {"success": False, "error": "Usuario no encontrado"}
    
    user = data["users"][username]
    if capability not in user["blocked_capabilities"]:
        user["blocked_capabilities"].append(capability)
    if capability in user["custom_capabilities"]:
        user["custom_capabilities"].remove(capability)
    save_users(data)
    return {"success": True}


def get_effective_capabilities(username: str) -> list:
    """Obtener la lista efectiva de capacidades de un usuario."""
    data = load_users()
    if username not in data["users"]:
        return []
    user = data["users"][username]
    caps = set(user.get("capabilities", []))
    caps |= set(user.get("custom_capabilities", []))
    caps -= set(user.get("blocked_capabilities", []))
    return sorted(caps)


def has_capability(username: str, capability: str) -> bool:
    """Comprobar si un usuario tiene una capacidad."""
    return capability in get_effective_capabilities(username)


def authenticate(username: str, password: str) -> dict:
    """Autenticar un usuario."""
    data = load_users()
    if username not in data["users"]:
        return {"success": False, "error": "Credenciales incorrectas"}
    
    user = data["users"][username]
    if not user.get("active", True):
        return {"success": False, "error": "Cuenta desactivada"}
    
    pwd_hash, _ = _hash_password(password, user["password_salt"])
    if pwd_hash != user["password_hash"]:
        return {"success": False, "error": "Credenciales incorrectas"}
    
    # Update login stats
    user["last_login"] = datetime.now().isoformat()
    user["login_count"] = user.get("login_count", 0) + 1
    save_users(data)
    
    return {
        "success": True,
        "username": username,
        "role": user["role"],
        "display_name": user["display_name"],
        "capabilities": get_effective_capabilities(username),
        "content_filter": user.get("content_filter", "none"),
        "web_token": user["channels"]["web_token"]
    }


def identify_user(channel: str, channel_id: str) -> dict:
    """
    Identificar un usuario por su canal y ID de canal.
    Usado por todos los adaptadores (Telegram, Discord, Web).
    
    Args:
        channel: 'telegram', 'discord', 'web', 'email'
        channel_id: ID del usuario en ese canal
    
    Returns:
        dict con info del usuario o None si no encontrado
    """
    data = load_users()
    channel_key = f"{channel}_id" if channel != "web" else "web_token"
    
    for username, user in data["users"].items():
        if not user.get("active", True):
            continue
        channels = user.get("channels", {})
        if channels.get(channel_key) == str(channel_id):
            return {
                "username": username,
                "display_name": user["display_name"],
                "role": user["role"],
                "capabilities": get_effective_capabilities(username),
                "content_filter": user.get("content_filter", "none"),
                "age_category": user.get("age_category", "adult"),
                "session_dir": str(SESSIONS_DIR / username)
            }
    
    return None


def list_users(include_inactive: bool = False) -> list:
    """Listar todos los usuarios."""
    data = load_users()
    users = []
    for username, user in data["users"].items():
        if not include_inactive and not user.get("active", True):
            continue
        users.append({
            "username": username,
            "display_name": user["display_name"],
            "role": user["role"],
            "age_category": user.get("age_category", "adult"),
            "content_filter": user.get("content_filter", "none"),
            "active": user.get("active", True),
            "last_login": user.get("last_login"),
            "login_count": user.get("login_count", 0),
            "channels": {
                "telegram": bool(user.get("channels", {}).get("telegram_id")),
                "telegram_id": user.get("channels", {}).get("telegram_id", ""),
                "discord": bool(user.get("channels", {}).get("discord_id")),
                "discord_id": user.get("channels", {}).get("discord_id", ""),
                "email": bool(user.get("channels", {}).get("email")),
            }
        })
    return users


def get_user_session_dir(username: str) -> str:
    """Obtener el directorio de sesion de un usuario."""
    path = SESSIONS_DIR / username
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_user_memory(username: str) -> str:
    """Obtener la memoria personal de un usuario."""
    mem_path = SESSIONS_DIR / username / "memory.md"
    if mem_path.exists():
        return mem_path.read_text(encoding="utf-8")
    return ""


def save_user_memory(username: str, content: str):
    """Guardar la memoria personal de un usuario."""
    mem_path = SESSIONS_DIR / username / "memory.md"
    mem_path.parent.mkdir(parents=True, exist_ok=True)
    mem_path.write_text(content, encoding="utf-8")


def init_admin():
    """Inicializar el usuario admin (Fernando) si no existe."""
    data = load_users()
    if "admin" not in data["users"]:
        create_user(
            username="admin",
            password="N0r4Z0e?*12",
            role="admin",
            display_name="Fernando",
            telegram_id="5034994867",
            created_by="system"
        )
        print("[UserManager] Admin creado (Fernando)")
    return True


def get_user_session_dir(username: str) -> Path:
    """Retorna el directorio de sesion privado de un usuario, creándolo y poblándolo si es necesario."""
    dir_path = SESSIONS_DIR / username
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # Crear memory.md por defecto si no existe
    mem_file = dir_path / "memory.md"
    if not mem_file.exists():
        mem_file.write_text(f"# Memoria de @{username}\n\nEste archivo guarda tus interacciones, experiencias y preferencias específicas de forma confidencial.\n", encoding="utf-8")
        
    # Crear soul.md por defecto si no existe
    soul_file = dir_path / "soul.md"
    if not soul_file.exists():
        soul_file.write_text(f"# Alma y Personalidad de @{username}\n\nDefine cómo Enjambre debe interactuar contigo (tono, estilo y nivel de formalidad).\n", encoding="utf-8")
        
    return dir_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python user_manager.py --init              (crear admin)")
        print("  python user_manager.py --list              (listar usuarios)")
        print("  python user_manager.py --create <user> <pass> <role>")
        print("  python user_manager.py --identify <canal> <id>")
        print("  python user_manager.py --caps <user>       (ver capacidades)")
        print("  python user_manager.py --roles             (ver roles disponibles)")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "--init":
        init_admin()
        print("Admin inicializado.")
    
    elif cmd == "--list":
        users = list_users(include_inactive=True)
        print(f"=== Usuarios ({len(users)}) ===")
        for u in users:
            status = "ACTIVE" if u["active"] else "INACTIVE"
            channels = [k for k, v in u["channels"].items() if v]
            print(f"  {u['username']} ({u['role']}) [{status}] filter={u['content_filter']} channels={','.join(channels)}")
    
    elif cmd == "--create" and len(sys.argv) >= 5:
        r = create_user(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"Creado: {r}")
    
    elif cmd == "--identify" and len(sys.argv) >= 4:
        user = identify_user(sys.argv[2], sys.argv[3])
        if user:
            print(f"Usuario identificado: {user['username']} ({user['role']}) filter={user['content_filter']}")
        else:
            print("Usuario no encontrado")
    
    elif cmd == "--caps" and len(sys.argv) >= 3:
        caps = get_effective_capabilities(sys.argv[2])
        print(f"Capacidades de {sys.argv[2]}:")
        for c in caps:
            print(f"  - {c}")
    
    elif cmd == "--roles":
        print("=== Roles disponibles ===")
        for role, caps in ROLE_CAPABILITIES.items():
            print(f"\n  {role.upper()} ({len(caps)} caps):")
            for c in caps:
                print(f"    - {c}")
