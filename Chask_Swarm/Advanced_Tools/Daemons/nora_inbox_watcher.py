"""
nora_inbox_watcher.py — Vigía de la cola de mensajes + Inyección en conversación activa
=========================================================================================
1. Monitorea input_queue.json cada 2 segundos.
2. Cuando detecta un mensaje con status=pending:
   a. Intenta inyectarlo en el campo de texto de la ventana Antigravity activa
      (cualquier conversación que esté abierta en ese momento, no solo Charm).
   b. Emite [WAKEUP_PING] en stdout para notificar al runtime de Antigravity.
"""
import os
import sys
import json
import time
import io
from datetime import datetime

# Forzar stdout en UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

QUEUE_FILE = r"C:\Program Files\Chask_Swarm\Advanced_Tools\Colas_Mensajes\input_queue.json"
LOG_FILE   = r"C:\Program Files\Chask_Swarm\Advanced_Tools\unified_channel.log"

# Clase de ventana de Antigravity (Qt)
ANTIGRAVITY_CLASS = "Qt51518QWindowIcon"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [INBOX_WATCHER] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def inject_into_active_window(text: str) -> tuple:
    """Inyecta el texto en la conversación activa de Antigravity (sin robar foco)."""
    try:
        from pywinauto import findwindows
        from pywinauto.application import Application

        # Buscar por clase exacta para evitar ambigüedades
        handles = findwindows.find_windows(class_name=ANTIGRAVITY_CLASS)
        if not handles:
            return False, "Ventana Antigravity no encontrada"

        # Usar la primera ventana visible
        app = Application(backend="uia").connect(handle=handles[0])
        dlg = app.top_window()

        # Buscar el campo de escritura de mensajes (Edit con placeholder "Write a message...")
        edits = dlg.descendants(control_type="Edit")
        chat_box = None
        for edit in edits:
            try:
                ph = edit.legacy_properties().get('Value', '') or ''
                name = edit.element_info.name or ''
                # El cajón de chat tiene el texto "Write a message..." como placeholder
                if 'message' in name.lower() or 'write' in name.lower() or 'mensaje' in name.lower():
                    chat_box = edit
                    break
            except Exception:
                pass

        # Si no encontramos por nombre, usamos el primero (suele ser el de chat)
        if chat_box is None and edits:
            chat_box = edits[0]

        if chat_box is None:
            return False, "No se encontró cuadro de chat en la ventana activa"

        # Escribir sin robar foco
        chat_box.type_keys(text + "{ENTER}", set_foreground=False, pause=0.05)
        return True, "Inyectado en conversación activa"

    except Exception as e:
        return False, f"Error inyectando: {e}"

print("[INBOX_WATCHER] Iniciado — vigilando cola y conversación activa...", flush=True)
log("Iniciado.")

while True:
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []

            pending = [item for item in data if item.get("status") == "pending"]

            if pending:
                # Marcar como procesados antes de actuar (evitar duplicados)
                for item in data:
                    if item.get("status") == "pending":
                        item["status"] = "processed"

                with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                for item in pending:
                    source  = item.get("source", "unknown")
                    message = item.get("message", "")

                    # 1. Intentar inyectar directamente en la ventana activa
                    ok, reason = inject_into_active_window(message)
                    log(f"Inyección en ventana activa: {reason}")

                    if not ok:
                        # 2. Si falla la inyección, al menos notificar con WAKEUP_PING
                        # para que Antigravity me despierte y yo lea la cola
                        log(f"Enviando WAKEUP_PING como fallback")

                    # Siempre emitir el WAKEUP_PING (funciona en la conversación donde
                    # está corriendo esta tarea de fondo)
                    print(f"[WAKEUP_PING] [{source.upper()}] {message}", flush=True)

    except Exception as e:
        log(f"Error en bucle principal: {e}")

    time.sleep(2)
