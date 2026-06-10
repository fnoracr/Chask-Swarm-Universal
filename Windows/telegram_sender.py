import os
import sys
import requests
import json

def get_telegram_config():
    import json, os
    master_creds = r"C:\Program Files\Chask_Swarm\Configuracion\master_credentials.json"
    if os.path.exists(master_creds):
        with open(master_creds, "r", encoding="utf-8") as f:
            creds = json.load(f).get("credentials", {})
            return creds.get("telegram_bot"), str(creds.get("telegram_admin"))
            
    agents_config = r"C:\Program Files\Chask_Swarm\agents_config.json"
    if os.path.exists(agents_config):
        with open(agents_config, "r", encoding="utf-8") as f:
            creds = json.load(f).get("credentials", {})
            return creds.get("telegram_bot"), str(creds.get("telegram_admin"))
            
    return None, None

def send_message(text):
    token, admin_id = get_telegram_config()
    
    if not token or not admin_id:
        print("Error: Credenciales de Telegram no configuradas.")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": admin_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Mensaje enviado correctamente.")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "send":
        message = " ".join(sys.argv[2:])
        send_message(message)
    else:
        print("Uso: python telegram_sender.py send <mensaje>")
