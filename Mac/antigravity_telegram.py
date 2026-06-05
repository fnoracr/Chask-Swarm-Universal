import sys
import requests
import json
import os

CONFIG_PATH = r"C:\Program Files\Chask_Swarn\Configuration\master_credentials.json"

def get_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)['credentials']

def send_message(text):
    try:
        creds = get_config()
        token = creds.get('telegram_bot')
        admin_id = creds.get('telegram_admin')
        if not token or not admin_id:
            print("No token/admin_id found.")
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": admin_id, "text": text}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "send":
            text = " ".join(sys.argv[2:])
            send_message(text)
        elif command == "listen":
            import time
            QUEUE_FILE = r"C:\Program Files\Chask_Swarn\Advanced_Tools\Message_Queues\input_queue.json"
            print("Listening for Telegram messages in the background...", flush=True)
            while True:
                try:
                    if os.path.exists(QUEUE_FILE):
                        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        modified = False
                        for item in data:
                            if item.get("status") == "pending":
                                msg_text = item.get("message", "")
                                print(f"\n[MENSAJE ENTRANTE]: {msg_text}\n", flush=True)
                                item["status"] = "processed"
                                modified = True
                        
                        if modified:
                            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    pass
                time.sleep(2)
