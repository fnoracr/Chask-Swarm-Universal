"""
nora_queue_watcher.py — Vigía de cola universal SIN LLM, cero tokens
======================================================================
- Monitoriza input_queue.json cada 2 segundos.
- Completamente agnóstico al canal: funciona con Telegram, Discord,
  Slack, Web y cualquier canal futuro que escriba en la cola.
- Cuando detecta un mensaje "pending":
    1. Envía acuse inmediato al canal de origen.
    2. Cambia estado a "delivered".
    3. Imprime [WAKEUP_PING] con el mensaje y TERMINA.
    4. Se relanza a sí mismo para seguir vigilando.
- La terminación notifica a [Nombre_IA] automáticamente (sin tokens).
- Si pasan MAX_WAIT segundos sin mensaje, termina para forzar reinicio.

Para añadir un canal nuevo, solo hay que:
  1. Crear su daemon que escriba en input_queue.json
  2. Añadir su función de ack en send_ack_to_channel()
"""
import os
import sys
import io
import re
import json
import time
import subprocess
from datetime import datetime

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

QUEUE_FILE    = r"C:\Program Files\Chask_Swarn\Advanced_Tools\Message_Queues\input_queue.json"
LOG_FILE      = r"C:\Program Files\Chask_Swarn\Advanced_Tools\unified_channel.log"
PYTHON_EXE    = r"C:\Users\fnora\AppData\Local\Programs\Python\Python311\python.exe"
BASE_DIR      = r"C:\Program Files\Chask_Swarn"
POLL_INTERVAL = 2    # segundos entre comprobaciones

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [QUEUE_WATCHER] {msg}\n")
    except Exception:
        pass

def extract_user_text(message: str) -> str:
    """Extrae solo el texto del usuario del mensaje formateado (canal-agnóstico)."""
    # Busca patrón genérico: [CANAL HH:MM:SS] [USER: xxx] texto
    match = re.search(
        r'\[(TELEGRAM|DISCORD|SLACK|WEB|PANEL)\s+\d+:\d+:\d+.*?\]\s+\[USER:\s*\w+\]\s+(.+)',
        message, re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(2).strip()
    return message[-120:]  # fallback

# ── Funciones de ack por canal ────────────────────────────────────────────────
# Para añadir un canal nuevo: añade un elif aquí y crea su función de ack.

def _ack_telegram(user_text: str):
    short = user_text[:80].replace('"', "'")
    subprocess.run(
        [PYTHON_EXE, os.path.join(BASE_DIR, "antigravity_telegram.py"),
         "send", f"⚡ Recibido: \"{short}\""],
        timeout=8, capture_output=True
    )

def _ack_discord(user_text: str):
    """Ack por Discord vía webhook (si está configurado)."""
    try:
        config_path = os.path.join(BASE_DIR, "Configuration", "master_credentials.json")
        with open(config_path, encoding="utf-8") as f:
            creds = json.load(f).get("credentials", {})
        webhook = creds.get("discord_webhook", "")
        if webhook:
            import urllib.request
            short = user_text[:80]
            payload = json.dumps({"content": f"⚡ Recibido: \"{short}\""}).encode()
            req = urllib.request.Request(webhook, data=payload,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        log(f"Error ack Discord: {e}")

def _ack_web(user_text: str):
    """Ack al panel web: escribe en una cola de respuestas."""
    try:
        resp_file = os.path.join(BASE_DIR, "Advanced_Tools", "Message_Queues", "web_responses.json")
        data = []
        if os.path.exists(resp_file):
            with open(resp_file, encoding="utf-8") as f:
                data = json.load(f)
        data.append({
            "ts": datetime.now().isoformat(),
            "type": "ack",
            "text": f"⚡ Recibido: \"{user_text[:80]}\""
        })
        with open(resp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error ack Web: {e}")

def _ack_slack(user_text: str):
    """Ack por Slack vía webhook (si está configurado en el futuro)."""
    try:
        config_path = os.path.join(BASE_DIR, "Configuration", "master_credentials.json")
        with open(config_path, encoding="utf-8") as f:
            creds = json.load(f).get("credentials", {})
        webhook = creds.get("slack_webhook", "")
        if webhook:
            import urllib.request
            short = user_text[:80]
            payload = json.dumps({"text": f"⚡ Recibido: \"{short}\""}).encode()
            req = urllib.request.Request(webhook, data=payload,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        log(f"Error ack Slack: {e}")

def send_ack_to_channel(source: str, user_text: str):
    """
    Enruta el acuse de recibo al canal correcto según el campo 'source'.
    Para añadir un canal nuevo: añade un elif con su función de ack.
    """
    src = source.lower()
    try:
        if "telegram" in src:
            _ack_telegram(user_text)
        elif "discord" in src:
            _ack_discord(user_text)
        elif "web" in src or "panel" in src:
            _ack_web(user_text)
        elif "slack" in src:
            _ack_slack(user_text)
        else:
            # Canal desconocido: ack por Telegram al admin como fallback
            _ack_telegram(f"[{source}] {user_text}")
        log(f"Ack enviado a canal '{source}': {user_text[:60]}")
    except Exception as e:
        log(f"Error enviando ack a canal '{source}': {e}")

def inject_into_active_window(text: str) -> tuple:
    """Inyecta el texto en la conversación activa de Antigravity (sin robar foco)."""
    try:
        import pyautogui
        import pygetwindow as gw
        import time

        windows = [w for w in gw.getWindowsWithTitle('') if 'Antigravity' in w.title or '[Nombre_IA]' in w.title or '[Nombre_IA]' in w.title]
        if not windows:
            return False, "Ventana Antigravity no encontrada"

        win = windows[0]
        if win.isMinimized:
            win.restore()
        win.activate()
        time.sleep(0.5)

        # Click at the bottom center of the window to focus the chat box
        click_x = win.left + (win.width // 2)
        click_y = win.bottom - 60
        pyautogui.click(click_x, click_y)
        time.sleep(0.2)

        pyautogui.write(text, interval=0.01)
        pyautogui.press('enter')

        return True, "Inyectado en conversación activa usando pyautogui"
    except Exception as e:
        return False, f"Error inyectando: {e}"

# ── Bucle principal ───────────────────────────────────────────────────────────

log("Iniciado — vigilando cola universal (modo daemon infinito)")

while True:
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            pending = [i for i in data if i.get("status") == "pending"]

            if pending:
                # Marcar todos como delivered antes de actuar (evita duplicados)
                for item in data:
                    if item.get("status") == "pending":
                        item["status"] = "delivered"
                with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                for item in pending:
                    source    = item.get("source", "unknown")
                    message   = item.get("message", "")
                    user_text = extract_user_text(message)

                    # 1. Acuse inmediato al canal correcto (sin LLM)
                    send_ack_to_channel(source, user_text)

                    # 2. Intentar inyectar directamente en la ventana activa
                    ok, reason = inject_into_active_window(message)
                    log(f"Inyección en ventana activa: {reason}")

                    if not ok:
                        # 3. WAKEUP_PING para notificar a [Nombre_IA] (si la inyección falla y [Nombre_IA] la está ejecutando localmente)
                        log("Enviando WAKEUP_PING como fallback")

                    print(f"[WAKEUP_PING] [{source.upper()}] {message}", flush=True)

    except json.JSONDecodeError:
        pass
    except Exception as e:
        log(f"Error: {e}")

    time.sleep(POLL_INTERVAL)
