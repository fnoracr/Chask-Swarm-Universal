"""
auth_middleware.py — Middleware de Autenticacion y Permisos
============================================================
Se interpone entre los canales de comunicacion y el motor de Enjambre.
En cada mensaje:
  1. Identifica al usuario por canal + ID
  2. Verifica que la accion solicitada esta en sus capacidades
  3. Aplica filtro parental si es menor
  4. Rutea al contexto de sesion del usuario
  5. Filtra la respuesta de salida si es menor

Uso desde otros modulos:
    from auth_middleware import process_request
    result = process_request(
        channel="telegram",
        channel_id="123456789",
        text="Hola Enjambre, genera un script"
    )
"""
import os
import sys
import io
import json
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(r"C:\Program Files\Chask_Swarm")
TOOLS_DIR = ROOT / "Advanced_Tools"

sys.path.insert(0, str(TOOLS_DIR))


def process_request(channel: str, channel_id: str, text: str,
                    action: str = None) -> dict:
    """
    Punto de entrada principal. Procesa cualquier request de cualquier canal.
    
    Args:
        channel: 'telegram', 'discord', 'web', 'email'
        channel_id: ID del usuario en ese canal
        text: Mensaje del usuario
        action: Capacidad requerida (auto-detectada si None)
    
    Returns:
        {
            "authorized": bool,
            "user": dict or None,
            "text": str (filtrado si es menor),
            "system_prompt_extra": str,
            "error": str,
            "content_blocked": bool
        }
    """
    from user_manager import identify_user, has_capability
    from content_filter import filter_input, filter_output, get_safe_system_prompt
    
    # 1. Identificar usuario
    user = identify_user(channel, channel_id)
    
    if not user:
        return {
            "authorized": False,
            "user": None,
            "text": text,
            "system_prompt_extra": "",
            "error": "Usuario no registrado. Contacta al administrador.",
            "content_blocked": False
        }
    
    # 2. Detectar accion requerida
    if not action:
        action = _detect_action(text)
    
    # 3. Verificar permisos
    if action and not has_capability(user["username"], action):
        return {
            "authorized": False,
            "user": user,
            "text": text,
            "system_prompt_extra": "",
            "error": f"No tienes permiso para: {action}. Tu rol: {user['role']}",
            "content_blocked": False
        }
    
    # 4. Filtrar input (para menores)
    filter_level = user.get("content_filter", "none")
    input_check = filter_input(text, user["username"], filter_level)
    
    if input_check["blocked"]:
        return {
            "authorized": True,
            "user": user,
            "text": input_check["replacement"],
            "system_prompt_extra": get_safe_system_prompt(filter_level),
            "error": "",
            "content_blocked": True,
            "block_reason": input_check["reason"]
        }
    
    # 5. Todo OK — preparar contexto
    system_prompt_extra = get_safe_system_prompt(filter_level)
    
    # Build user context
    uctx = get_user_context(user["username"])
    ctx_block = f"\n[CONTEXTO DE USUARIO]\nIdentidad: {uctx['display_name']} (Rol: {uctx['role']})\n"
    if uctx.get('soul'):
        ctx_block += f"=== INSTRUCCIONES ESPECÍFICAS PARA ESTE USUARIO (soul.md) ===\n{uctx['soul']}\n============================================================\n"
    if uctx.get('memory'):
        ctx_block += f"Recuerdos sobre este usuario: {uctx['memory']}\n"
    if uctx.get('preferences'):
        ctx_block += f"Preferencias: {json.dumps(uctx['preferences'], ensure_ascii=False)}\n"
        
    system_prompt_extra += ctx_block

    return {
        "authorized": True,
        "user": user,
        "text": text,
        "system_prompt_extra": system_prompt_extra.strip(),
        "error": "",
        "content_blocked": False,
        "session_dir": user.get("session_dir", ""),
        "filter_level": filter_level
    }


def filter_response(text: str, username: str) -> str:
    """
    Filtra la respuesta del sistema antes de enviarla al usuario.
    Solo aplica para usuarios con filtro parental.
    """
    from content_filter import filter_output
    
    result = filter_output(text, username)
    return result.get("filtered_text", text)


def get_user_context(username: str) -> dict:
    """
    Obtener el contexto completo de un usuario para inyectar en el LLM.
    Incluye: memoria personal, preferencias, historial reciente.
    """
    from user_manager import get_user_memory, get_effective_capabilities, load_users
    
    data = load_users()
    user = data.get("users", {}).get(username, {})
    
    memory = get_user_memory(username)
    caps = get_effective_capabilities(username)
    
    # Load preferences
    prefs = {}
    prefs_path = ROOT / "user_sessions" / username / "preferences.json"
    if prefs_path.exists():
        try:
            prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    # Load soul.md
    soul = ""
    soul_path = ROOT / "user_sessions" / username / "soul.md"
    if soul_path.exists():
        try:
            soul = soul_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    
    return {
        "username": username,
        "display_name": user.get("display_name", username),
        "role": user.get("role", "guest"),
        "memory": memory,
        "capabilities": caps,
        "preferences": prefs,
        "soul": soul,
        "content_filter": user.get("content_filter", "none")
    }


def _detect_action(text: str) -> str:
    """Auto-detectar la accion/capacidad requerida por el texto."""
    t = text.lower()
    
    # Slash commands
    if t.startswith("/"):
        parts = t.split()
        cmd = parts[0]
        cmd_map = {
            "/status": "system_status",
            "/config": "config_write",
            "/set": "config_write",
            "/services": "services_manage",
            "/deploy": "deploy",
            "/sandbox": "sandbox_run",
            "/learn": "skill_learn",
            "/skill": "skill_run",
            "/kb": "kb_search",
            "/memoria": "memory_read",
        }
        if cmd in cmd_map:
            return cmd_map[cmd]
        if cmd in ("/kb",) and len(parts) > 1 and parts[1] == "crear":
            return "kb_create"
    
    # Natural language detection
    if any(w in t for w in ["genera", "crea", "programa", "codigo"]):
        return "skill_create"
    if any(w in t for w in ["sandbox", "ejecuta en sandbox"]):
        return "sandbox_run"
    if any(w in t for w in ["usuario", "crear usuario", "borrar usuario"]):
        return "user_manage"
    if any(w in t for w in ["screenshot", "captura", "pantalla", "vision"]):
        return "llm_vision"
    
    # Default: chat
    return "llm_chat"


# ─── Admin-only functions ─────────────────────────────────

def admin_create_user(admin_channel: str, admin_channel_id: str,
                      username: str, password: str, role: str = "user",
                      **kwargs) -> dict:
    """Crear usuario (solo admin)."""
    from user_manager import identify_user, create_user, has_capability
    
    admin = identify_user(admin_channel, admin_channel_id)
    if not admin or not has_capability(admin["username"], "user_manage"):
        return {"success": False, "error": "No tienes permisos de administrador"}
    
    return create_user(username, password, role, created_by=admin["username"], **kwargs)


def admin_list_users(admin_channel: str, admin_channel_id: str) -> dict:
    """Listar usuarios (solo admin)."""
    from user_manager import identify_user, list_users, has_capability
    
    admin = identify_user(admin_channel, admin_channel_id)
    if not admin or not has_capability(admin["username"], "user_manage"):
        return {"success": False, "error": "No tienes permisos"}
    
    return {"success": True, "users": list_users()}


if __name__ == "__main__":
    print("=== Auth Middleware Test ===")
    
    # Init admin first
    from user_manager import init_admin
    init_admin()
    
    # Test: admin via Telegram
    result = process_request("telegram", "5034994867", "/status")
    user_obj = result.get('user') or {}
    print(f"\nAdmin /status: authorized={result['authorized']}, user={user_obj.get('username', 'N/A')}")
    
    # Test: unknown user
    result = process_request("telegram", "999999999", "Hola")
    print(f"Unknown user: authorized={result['authorized']}, error={result.get('error', '')}")
    
    print("\nMiddleware operativo.")
