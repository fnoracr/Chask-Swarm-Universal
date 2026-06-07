import sys
import json
import os
import subprocess
import requests

BASE_DIR = r"C:\Program Files\Chask_Swarm"
CONFIG_FILE = os.path.join(BASE_DIR, "Configuracion", "channels_config.json")
TELEGRAM_SCRIPT = os.path.join(BASE_DIR, "antigravity_telegram.py")

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("channels", {})
    except Exception:
        return {}

def send_telegram(message):
    subprocess.run([sys.executable, TELEGRAM_SCRIPT, "send", message])

def send_webhook(url, message, platform):
    if not url:
        print(f"Error: No webhook URL for {platform}")
        return
    
    payload = {}
    if platform == "discord":
        payload = {
            "content": message,
            "username": "Nora (Chask Swarm)",
            "avatar_url": "https://files.catbox.moe/r054at.JPG"
        }
    elif platform == "slack":
        payload = {"text": message}
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending to {platform} webhook: {e}")

def main():
    if len(sys.argv) < 3:
        print("Uso: universal_sender.py <source> <mensaje>")
        return

    source = sys.argv[1].upper()
    message = sys.argv[2]
    cfg = load_config()

    if "TELEGRAM" in source:
        send_telegram(message)
    elif "DISCORD" in source:
        url = cfg.get("discord", {}).get("webhook_url", "")
        send_webhook(url, message, "discord")
    elif "SLACK" in source:
        url = cfg.get("slack", {}).get("webhook_url", "")
        send_webhook(url, message, "slack")
    else:
        # Default o fallback a Telegram si no se reconoce
        send_telegram(f"[Aviso: canal {source} no soportado para salida] " + message)

if __name__ == "__main__":
    main()
