"""
slack_worker.py — Worker Slack via Socket Mode para [Nombre_IA]
Ejecutado como subproceso por unified_channel_daemon para aislar la conexión.
Requiere: pip install slack-sdk
"""
import os, sys, io, json, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR        = r"C:\Program Files\Chask_Swarm"
CHANNELS_CONFIG = os.path.join(BASE_DIR, "Configuration", "channels_config.json")
QUEUE_FILE      = os.path.join(BASE_DIR, "Advanced_Tools", "Message_Queues", "input_queue.json")
LOG_FILE        = os.path.join(BASE_DIR, "Advanced_Tools", "unified_channel.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [SLACK] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def add_to_queue(message, source):
    try:
        data = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({"ts": datetime.now().isoformat(), "source": source,
                     "message": message, "status": "pending"})
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Queue error: {e}")

def main():
    with open(CHANNELS_CONFIG, "r", encoding="utf-8") as f:
        ch = json.load(f).get("channels", {})
    sl = ch.get("slack", {})
    if not sl.get("enabled", False):
        log("Slack desactivado en channels_config.json — saliendo")
        return
    app_token = sl.get("app_token", "")
    bot_token = sl.get("bot_token", "")
    if not app_token or not bot_token:
        log("Sin tokens de Slack — saliendo")
        return

    try:
        from slack_sdk.socket_mode import SocketModeClient
        from slack_sdk.socket_mode.request import SocketModeRequest
        from slack_sdk.socket_mode.response import SocketModeResponse
        from slack_sdk import WebClient
    except ImportError:
        log("slack-sdk no instalado. Ejecuta: pip install slack-sdk")
        return

    web_client = WebClient(token=bot_token)
    client = SocketModeClient(app_token=app_token, web_client=web_client)

    def process_event(client, req):
        if req.type == "events_api":
            client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
            event = req.payload.get("event", {})
            if event.get("type") == "message" and not event.get("bot_id"):
                ts = datetime.now().strftime("%H:%M:%S")
                user = event.get("user", "unknown")
                text = event.get("text", "")
                channel = event.get("channel", "")
                if text.strip():
                    formatted = f"[SLACK {ts}] [USER: {user}] {text}"
                    log(f"MSG: {formatted[:80]}")
                    add_to_queue(formatted, f"slack_{channel}")

    client.socket_mode_request_listeners.append(process_event)
    log(f"Conectado a Slack via Socket Mode con app_token={app_token[:20]}...")
    client.connect()

    # Mantener vivo
    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
