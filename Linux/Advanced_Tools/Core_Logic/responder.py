import sys, os, requests, json
from datetime import datetime

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "Configuration", "master_credentials.json")
CHANNELS_PATH = os.path.join(BASE_DIR, "Configuration", "channels_config.json")
QUEUE_PATH = os.path.join(BASE_DIR, "", "Advanced_Tools", "Message_Queues", "input_queue.json")
WEB_URL = "http://localhost:7860/web_send"

def load_channel_config(channel_name):
    try:
        with open(CHANNELS_PATH, "r") as f:
            cfg = json.load(f)
        return cfg.get("channels", {}).get(channel_name, {})
    except:
        return {}

def send_to_web(msg):
    try:
        requests.post(WEB_URL, json={"message": msg}, timeout=5)
        print("[Responder] Enviado a WEB")
    except:
        print("[Responder] Error enviando a WEB")

def send_to_telegram(msg, thinking_mid=None):
    try:
        if not os.path.exists(CONFIG_PATH): 
            return
        with open(CONFIG_PATH, "r") as f: 
            cfg = json.load(f)["credentials"]
        token, admin_id = cfg["telegram_bot"], cfg["telegram_admin"]
        
        if thinking_mid:
            try:
                requests.post(f"https://api.telegram.org/bot{token}/deleteMessage", 
                              json={"chat_id": admin_id, "message_id": thinking_mid}, timeout=5)
            except: pass

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": admin_id, "text": msg}, timeout=10)
        print(f"[Responder] Telegram Status: {r.status_code}")
    except Exception as e:
        print(f"[Responder] Error Telegram: {e}")

def send_to_discord(msg):
    cfg = load_channel_config("discord")
    webhook_url = cfg.get("webhook_url")
    if webhook_url:
        try:
            requests.post(webhook_url, json={"content": msg}, timeout=5)
            print("[Responder] Enviado a Discord")
        except Exception as e:
            print(f"[Responder] Error Discord: {e}")

import re

def strip_html(text):
    # Eliminar etiquetas div de justificación y otras etiquetas HTML básicas
    return re.sub(r'<[^>]+>', '', text).strip()

def send_to_slack(msg):
    cfg = load_channel_config("slack")
    webhook_url = cfg.get("webhook_url")
    if webhook_url:
        try:
            clean_msg = strip_html(msg)
            requests.post(webhook_url, json={"text": clean_msg}, timeout=5)
            print("[Responder] Enviado a Slack")
        except Exception as e:
            print(f"[Responder] Error Slack: {e}")
    else:
        print(f"[Responder MOCK SLACK] No hay webhook_url. Simulando envío:\n>>> {msg}")

def send_to_teams(msg):
    cfg = load_channel_config("teams")
    webhook_url = cfg.get("webhook_url")
    if webhook_url:
        try:
            requests.post(webhook_url, json={"text": msg}, timeout=5)
            print("[Responder] Enviado a Teams")
        except Exception as e:
            print(f"[Responder] Error Teams: {e}")

def send_to_meet_charm(msg):
    # Endpoint simulado asumiendo que el VPS lo expone en un puerto estándar
    # En producción esto apuntaría a https://api.chask.fun/meet_charm/webhook
    webhook_url = "http://46.202.172.31:8080/webhook/meet_charm_receive"
    try:
        requests.post(webhook_url, json={"message": msg, "bot_sender": "Chask_Swarm_[Nombre_IA]"}, timeout=5)
        print("[Responder] Enviado a Meet [Nombre_IA] VPS")
    except Exception as e:
        print(f"[Responder] Error Meet [Nombre_IA]: {e}")

def get_and_mark_source():
    """Busca el ultimo mensaje sin responder y lo marca."""
    try:
        if not os.path.exists(QUEUE_PATH): return "both", None
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for i in range(len(data)-1, -1, -1):
            if data[i].get("status") != "responded":
                source = data[i].get("source", "both")
                thinking_mid = data[i].get("thinking_mid")
                data[i]["status"] = "responded"
                with open(QUEUE_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return source, thinking_mid
    except: pass
    return "both", None

def smart_respond(mensaje, thinking_mid=None, force_target=None):
    """Detecta el origen automáticamente y responde al canal adecuado."""
    if force_target:
        target = force_target
        t_mid = None
    else:
        target, t_mid = get_and_mark_source()
        
    final_mid = thinking_mid if thinking_mid else t_mid
    
    if target in ["web", "both"]: send_to_web(mensaje)
    if target in ["telegram", "both"]: send_to_telegram(mensaje, final_mid)
    if target == "discord": send_to_discord(mensaje)
    if target == "slack": send_to_slack(mensaje)
    if target == "teams": send_to_teams(mensaje)
    if target == "meet_charm": send_to_meet_charm(mensaje)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    args = sys.argv[1:]
    target = "auto"
    thinking_mid = None
    
    if args[0].startswith("--"):
        target = args[0].replace("--", "")
        mensaje = " ".join(args[1:])
    else:
        target, thinking_mid = get_and_mark_source()
        mensaje = " ".join(args)
    
    smart_respond(mensaje, thinking_mid, force_target=target if target != "auto" else None)
