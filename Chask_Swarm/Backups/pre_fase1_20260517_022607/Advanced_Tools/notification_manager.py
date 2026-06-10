"""
notification_manager.py — Notificaciones Inteligentes Agrupadas
================================================================
Sistema de notificaciones que:
- Agrupa mensajes similares para no saturar al usuario
- Prioriza por urgencia (critical > warning > info)
- Respeta horarios de "no molestar"
- Soporta múltiples canales vía ChannelRouter

Uso:
  python notification_manager.py send info "Build completado"
  python notification_manager.py send critical "Daemon caído"
  python notification_manager.py flush   (envía todo lo pendiente)
  python notification_manager.py stats
"""
import os
import sys
import json
import io
from datetime import datetime, timedelta
from collections import defaultdict

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVANCED_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(BASE_DIR, "notification_queue.json")
NOTIF_LOG = os.path.join(BASE_DIR, "notification_log.json")
NOTIF_CONFIG = os.path.join(BASE_DIR, "notification_config.json")

sys.path.insert(0, ADVANCED_DIR)

# Prioridades
PRIORITY = {"critical": 0, "warning": 1, "info": 2, "debug": 3}
PRIORITY_ICONS = {"critical": "🔴", "warning": "⚠️", "info": "ℹ️", "debug": "🔵"}

# Config por defecto
DEFAULT_CONFIG = {
    "do_not_disturb": {
        "enabled": False,
        "start_hour": 23,
        "end_hour": 8
    },
    "grouping": {
        "enabled": True,
        "window_minutes": 5,
        "max_group_size": 10
    },
    "channels": {
        "critical": ["telegram"],
        "warning": ["telegram"],
        "info": ["telegram"],
        "debug": []
    },
    "throttle": {
        "max_per_hour": 20,
        "cooldown_seconds": 30
    }
}


def _load_config() -> dict:
    if os.path.exists(NOTIF_CONFIG):
        try:
            with open(NOTIF_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG


def _load_queue() -> list:
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_queue(queue: list):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def _is_dnd() -> bool:
    """Verifica si estamos en horario de no molestar."""
    config = _load_config()
    dnd = config.get("do_not_disturb", {})
    if not dnd.get("enabled", False):
        return False
    now = datetime.now().hour
    start = dnd.get("start_hour", 23)
    end = dnd.get("end_hour", 8)
    if start > end:
        return now >= start or now < end
    return start <= now < end


def _get_recent_count() -> int:
    """Cuenta notificaciones de la última hora."""
    logs = []
    if os.path.exists(NOTIF_LOG):
        try:
            with open(NOTIF_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
    return len([l for l in logs if l.get("ts", "") > cutoff])


def _log_notification(message: str, priority: str, channel: str, grouped: int = 1):
    """Log de notificación enviada."""
    logs = []
    if os.path.exists(NOTIF_LOG):
        try:
            with open(NOTIF_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append({
        "ts": datetime.now().isoformat(),
        "priority": priority,
        "channel": channel,
        "message": message[:200],
        "grouped": grouped
    })
    logs = logs[-200:]
    with open(NOTIF_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def notify(message: str, priority: str = "info", immediate: bool = False) -> dict:
    """
    Envía o encola una notificación.
    
    Args:
        message: Texto de la notificación
        priority: critical|warning|info|debug
        immediate: Si True, envía inmediatamente sin agrupar
    
    Returns:
        {"sent": bool, "queued": bool, "reason": str}
    """
    config = _load_config()
    priority = priority.lower()
    if priority not in PRIORITY:
        priority = "info"

    # Critical siempre se envía inmediatamente
    if priority == "critical":
        immediate = True

    # DND: solo critical pasa
    if _is_dnd() and priority != "critical":
        _enqueue(message, priority)
        return {"sent": False, "queued": True, "reason": "do_not_disturb"}

    # Throttle
    throttle = config.get("throttle", {})
    max_per_hour = throttle.get("max_per_hour", 20)
    if _get_recent_count() >= max_per_hour and priority != "critical":
        _enqueue(message, priority)
        return {"sent": False, "queued": True, "reason": "throttle_limit"}

    # Grouping
    if not immediate and config.get("grouping", {}).get("enabled", True):
        _enqueue(message, priority)
        queue = _load_queue()
        window = config.get("grouping", {}).get("window_minutes", 5)
        cutoff = (datetime.now() - timedelta(minutes=window)).isoformat()
        pending = [q for q in queue if q.get("ts", "") > cutoff]
        
        if len(pending) < 2:
            return {"sent": False, "queued": True, "reason": "grouping_window"}
        # Hay suficientes, flush
        return flush()

    # Enviar directamente
    return _send_now(message, priority)


def _enqueue(message: str, priority: str):
    """Añade a la cola."""
    queue = _load_queue()
    queue.append({
        "ts": datetime.now().isoformat(),
        "message": message,
        "priority": priority
    })
    _save_queue(queue)


def _send_now(message: str, priority: str, grouped_count: int = 1) -> dict:
    """Envía la notificación por los canales configurados."""
    config = _load_config()
    channels = config.get("channels", {}).get(priority, ["telegram"])
    icon = PRIORITY_ICONS.get(priority, "")
    formatted = f"{icon} [{priority.upper()}] {message}"

    sent = False
    try:
        from channel_adapter import ChannelRouter
        router = ChannelRouter()
        for ch in channels:
            if router.send(ch, formatted):
                sent = True
                _log_notification(message, priority, ch, grouped_count)
    except ImportError:
        # Fallback directo a Telegram
        import subprocess
        try:
            subprocess.run(
                [sys.executable, os.path.join(BASE_DIR, "antigravity_telegram.py"), "send", formatted],
                capture_output=True, timeout=15
            )
            sent = True
            _log_notification(message, priority, "telegram", grouped_count)
        except Exception:
            pass

    return {"sent": sent, "queued": False, "reason": "sent" if sent else "send_failed"}


def flush() -> dict:
    """Envía todas las notificaciones pendientes (agrupadas por prioridad)."""
    queue = _load_queue()
    if not queue:
        return {"sent": True, "queued": False, "reason": "queue_empty"}

    # Agrupar por prioridad
    groups = defaultdict(list)
    for item in queue:
        groups[item.get("priority", "info")].append(item["message"])

    total_sent = 0
    # Enviar cada grupo
    for prio in sorted(groups.keys(), key=lambda p: PRIORITY.get(p, 9)):
        msgs = groups[prio]
        if len(msgs) == 1:
            combined = msgs[0]
        else:
            combined = f"({len(msgs)} notificaciones agrupadas):\n" + "\n".join(f"• {m}" for m in msgs[:10])
            if len(msgs) > 10:
                combined += f"\n... y {len(msgs) - 10} más"

        result = _send_now(combined, prio, len(msgs))
        if result["sent"]:
            total_sent += len(msgs)

    # Limpiar cola
    _save_queue([])
    return {"sent": True, "queued": False, "reason": f"flushed_{total_sent}"}


def get_stats() -> dict:
    """Estadísticas del sistema de notificaciones."""
    queue = _load_queue()
    logs = []
    if os.path.exists(NOTIF_LOG):
        try:
            with open(NOTIF_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass

    last_hour = (datetime.now() - timedelta(hours=1)).isoformat()
    last_day = (datetime.now() - timedelta(days=1)).isoformat()

    return {
        "pending_in_queue": len(queue),
        "sent_last_hour": len([l for l in logs if l.get("ts", "") > last_hour]),
        "sent_last_24h": len([l for l in logs if l.get("ts", "") > last_day]),
        "total_logged": len(logs),
        "dnd_active": _is_dnd()
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python notification_manager.py send [critical|warning|info] \"mensaje\"")
        print("  python notification_manager.py flush")
        print("  python notification_manager.py stats")
        print("  python notification_manager.py init-config")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "send" and len(sys.argv) >= 4:
        prio = sys.argv[2]
        msg = " ".join(sys.argv[3:])
        result = notify(msg, prio)
        print(f"  Resultado: {result}")

    elif cmd == "flush":
        result = flush()
        print(f"  Resultado: {result}")

    elif cmd == "stats":
        stats = get_stats()
        print("\nNOTIFICACIONES:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif cmd == "init-config":
        with open(NOTIF_CONFIG, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"Config creada: {NOTIF_CONFIG}")

    else:
        print(f"Comando desconocido: {cmd}")
