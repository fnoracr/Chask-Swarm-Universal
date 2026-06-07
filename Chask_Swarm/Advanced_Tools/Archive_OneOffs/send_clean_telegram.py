# -*- coding: utf-8 -*-
import json
import requests
import sys

CONFIG_PATH = r"C:\Program Files\Chask_Swarm\Configuracion\master_credentials.json"

def send_message(text):
    with open(CONFIG_PATH, 'r') as f:
        cfg = json.load(f)
    token = cfg['credentials']['telegram_bot']
    admin_id = cfg['credentials']['telegram_admin']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": admin_id, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read entire content of a file if passed, or join arguments
        msg_text = sys.argv[1]
        send_message(msg_text)
