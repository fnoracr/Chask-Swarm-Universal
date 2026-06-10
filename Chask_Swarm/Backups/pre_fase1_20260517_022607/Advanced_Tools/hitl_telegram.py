"""
hitl_telegram.py — Human-in-the-Loop con Botones Inline de Telegram
=====================================================================
Sistema de aprobaciones con un click para operaciones críticas.

En vez de pedir confirmación por texto, envía botones:
  [✅ APROBAR]  [❌ DENEGAR]  [📝 MODIFICAR]

Uso:
    from hitl_telegram import request_approval, ApprovalResult

    # Síncrono (espera respuesta)
    result = request_approval(
        action="Borrar colección power_automate_v4 (5262 puntos)",
        timeout_seconds=300
    )
    if result.approved:
        # Proceder con la acción
    elif result.denied:
        # Abortar
    elif result.timed_out:
        # Denegar por timeout (seguridad)

    # Asíncrono (no bloquea)
    callback_id = send_approval_request("Instalar paquete X")
    # ... más tarde:
    status = check_approval(callback_id)
"""

import os
import sys
import json
import time
import uuid
import logging
import requests
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger("hitl_telegram")

# ─── Configuración ────────────────────────────────────────────
CONFIG_PATH   = r"C:\Program Files\Chask_Swarm\telegram_config.json"
APPROVALS_DIR = r"C:\Program Files\Chask_Swarm\approvals"

# Cargar config
def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)

_config = None
def _get_config():
    global _config
    if not _config:
        _config = _load_config()
    return _config


# ─── Dataclasses ──────────────────────────────────────────────
@dataclass
class ApprovalResult:
    callback_id: str
    approved: bool = False
    denied: bool = False
    modified: bool = False
    timed_out: bool = False
    user_note: str = ""
    response_time: float = 0.0


# ─── API de Telegram ──────────────────────────────────────────
def _telegram_api(method: str, data: dict) -> dict:
    """Llama a la API de Telegram Bot."""
    config = _get_config()
    token  = config["telegram_bot"]
    url    = f"https://api.telegram.org/bot{token}/{method}"
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json()
    except Exception as e:
        log.error(f"Telegram API error ({method}): {e}")
        return {"ok": False, "error": str(e)}


def send_approval_request(action_description: str,
                           urgency: str = "normal") -> str:
    """
    Envía un mensaje con botones inline a Telegram para aprobación.
    
    Args:
        action_description: Qué acción necesita aprobación
        urgency: "normal", "high", "critical"
    
    Returns:
        callback_id para seguimiento
    """
    config      = _get_config()
    chat_id     = config["telegram_admin"]
    callback_id = f"approval_{uuid.uuid4().hex[:12]}"

    # Iconos de urgencia
    icons = {"normal": "🔵", "high": "🟡", "critical": "🔴"}
    icon  = icons.get(urgency, "🔵")

    text = (
        f"{icon} **Aprobación requerida**\n\n"
        f"📋 {action_description}\n\n"
        f"🕐 Timeout: 5 minutos (denegación automática por seguridad)"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ APROBAR", "callback_data": f"{callback_id}:approve"},
                {"text": "❌ DENEGAR", "callback_data": f"{callback_id}:deny"},
            ],
            [
                {"text": "📝 MODIFICAR", "callback_data": f"{callback_id}:modify"},
            ]
        ]
    }

    result = _telegram_api("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })

    # Guardar estado de la aprobación
    os.makedirs(APPROVALS_DIR, exist_ok=True)
    approval_state = {
        "callback_id": callback_id,
        "action": action_description,
        "urgency": urgency,
        "status": "pending",
        "created_at": time.time(),
        "message_id": result.get("result", {}).get("message_id"),
    }
    _save_approval(callback_id, approval_state)

    log.info(f"Aprobación enviada: {callback_id} — {action_description[:50]}")
    return callback_id


def check_approval(callback_id: str) -> ApprovalResult:
    """
    Verifica el estado de una aprobación pendiente.
    Non-blocking: devuelve inmediatamente.
    """
    state = _load_approval(callback_id)
    if not state:
        return ApprovalResult(callback_id=callback_id, timed_out=True)

    if state["status"] == "approved":
        return ApprovalResult(callback_id=callback_id, approved=True,
                              response_time=state.get("response_time", 0))
    elif state["status"] == "denied":
        return ApprovalResult(callback_id=callback_id, denied=True,
                              response_time=state.get("response_time", 0))
    elif state["status"] == "modified":
        return ApprovalResult(callback_id=callback_id, modified=True,
                              user_note=state.get("user_note", ""),
                              response_time=state.get("response_time", 0))

    # Verificar timeout (5 minutos)
    elapsed = time.time() - state.get("created_at", 0)
    if elapsed > 300:
        state["status"] = "timeout"
        _save_approval(callback_id, state)
        return ApprovalResult(callback_id=callback_id, timed_out=True)

    # Aún pendiente — revisar updates de Telegram
    _poll_updates(callback_id)
    state = _load_approval(callback_id)
    if state["status"] != "pending":
        return check_approval(callback_id)  # Recursión segura (ya cambió)

    return ApprovalResult(callback_id=callback_id)  # Aún pendiente


def request_approval(action_description: str,
                      timeout_seconds: int = 300,
                      urgency: str = "normal") -> ApprovalResult:
    """
    Envía aprobación y ESPERA la respuesta (blocking).
    
    Args:
        action_description: Descripción de la acción
        timeout_seconds: Tiempo máximo de espera
        urgency: "normal", "high", "critical"
    
    Returns:
        ApprovalResult con la decisión del usuario
    """
    callback_id = send_approval_request(action_description, urgency)
    start_time  = time.time()

    while time.time() - start_time < timeout_seconds:
        result = check_approval(callback_id)
        if result.approved or result.denied or result.modified or result.timed_out:
            # Actualizar mensaje de Telegram
            _update_approval_message(callback_id, result)
            return result
        time.sleep(2)  # Poll cada 2 segundos

    # Timeout
    result = ApprovalResult(callback_id=callback_id, timed_out=True)
    _update_approval_message(callback_id, result)
    return result


# ─── Polling de Updates ───────────────────────────────────────
_last_update_id = 0

def _poll_updates(target_callback_id: str):
    """
    Revisa updates de Telegram buscando callback_query para nuestro ID.
    """
    global _last_update_id
    result = _telegram_api("getUpdates", {
        "offset": _last_update_id + 1,
        "timeout": 1,
        "allowed_updates": ["callback_query"]
    })

    if not result.get("ok"):
        return

    for update in result.get("result", []):
        _last_update_id = update["update_id"]

        callback_query = update.get("callback_query")
        if not callback_query:
            continue

        data = callback_query.get("data", "")
        if ":" not in data:
            continue

        cb_id, action = data.rsplit(":", 1)

        # Verificar que es del admin autorizado
        from_id = str(callback_query.get("from", {}).get("id", ""))
        config  = _get_config()
        if from_id != config["telegram_admin"]:
            log.warning(f"Callback de usuario no autorizado: {from_id}")
            continue

        # Procesar la respuesta
        state = _load_approval(cb_id)
        if not state:
            continue

        state["response_time"] = time.time() - state.get("created_at", 0)

        if action == "approve":
            state["status"] = "approved"
        elif action == "deny":
            state["status"] = "denied"
        elif action == "modify":
            state["status"] = "modified"
            state["user_note"] = "Modificación solicitada"

        _save_approval(cb_id, state)

        # Responder al callback (quitar el relojito de carga)
        _telegram_api("answerCallbackQuery", {
            "callback_query_id": callback_query["id"],
            "text": f"{'✅ Aprobado' if action == 'approve' else '❌ Denegado' if action == 'deny' else '📝 Modificar'}"
        })

        log.info(f"Aprobación {cb_id}: {action}")


def _update_approval_message(callback_id: str, result: ApprovalResult):
    """Actualiza el mensaje original con el resultado."""
    state = _load_approval(callback_id)
    if not state or not state.get("message_id"):
        return

    config  = _get_config()
    chat_id = config["telegram_admin"]
    msg_id  = state["message_id"]

    if result.approved:
        status_text = "✅ **APROBADO**"
    elif result.denied:
        status_text = "❌ **DENEGADO**"
    elif result.modified:
        status_text = "📝 **MODIFICAR**"
    elif result.timed_out:
        status_text = "⏰ **TIMEOUT** (denegado automáticamente)"
    else:
        return

    elapsed = result.response_time
    text = (
        f"{status_text}\n\n"
        f"📋 {state.get('action', '')}\n"
        f"🕐 Respondido en {elapsed:.1f}s" if elapsed else f"{status_text}\n\n📋 {state.get('action', '')}"
    )

    _telegram_api("editMessageText", {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": text,
        "parse_mode": "Markdown"
    })


# ─── Persistencia ─────────────────────────────────────────────
def _approval_path(callback_id: str) -> str:
    return os.path.join(APPROVALS_DIR, f"{callback_id}.json")

def _save_approval(callback_id: str, state: dict):
    os.makedirs(APPROVALS_DIR, exist_ok=True)
    with open(_approval_path(callback_id), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def _load_approval(callback_id: str) -> dict | None:
    path = _approval_path(callback_id)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


# ─── Funciones de conveniencia ────────────────────────────────
def quick_confirm(action: str) -> bool:
    """Atajo: pide aprobación y devuelve True/False."""
    result = request_approval(action, timeout_seconds=300, urgency="normal")
    return result.approved


def critical_confirm(action: str) -> bool:
    """Atajo para acciones críticas (urgencia alta)."""
    result = request_approval(action, timeout_seconds=120, urgency="critical")
    return result.approved


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        action = " ".join(sys.argv[1:])
        print(f"Enviando aprobación: {action}")
        result = request_approval(action, timeout_seconds=60)
        print(f"Resultado: approved={result.approved} denied={result.denied} "
              f"timed_out={result.timed_out} time={result.response_time:.1f}s")
    else:
        # Test rápido — solo enviar sin esperar
        cb = send_approval_request("Test de botones HITL desde consola", "normal")
        print(f"Aprobación enviada: {cb}")
        print("Comprueba Telegram y pulsa un botón.")
