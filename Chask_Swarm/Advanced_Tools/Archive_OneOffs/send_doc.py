import requests
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(BASE_DIR, "Configuracion", "master_credentials.json")
file_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "..", "Charm_ES", "Leeme_Swarm_v3.html")

with open(config_path, "r") as f:
    config = json.load(f)

token = config["telegram_bot"]
admin_id = config["telegram_admin"]

with open(file_path, "rb") as doc:
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    r = requests.post(url, data={"chat_id": admin_id, "caption": "Aquí tienes la versión definitiva de la documentación v3.0 🐝"}, files={"document": doc})
    if r.status_code == 200:
        print("Documento enviado con éxito.")
    else:
        print(f"Error al enviar: {r.text}")
