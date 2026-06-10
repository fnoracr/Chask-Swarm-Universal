import sys, os, requests, json
from datetime import datetime

# Rutas
# Script en: Advanced_Tools/responder.py
# Root en: . (Chask_Swarm)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "agents_config.json")
QUEUE_PATH = os.path.join(BASE_DIR, "", "Advanced_Tools", "Colas_Mensajes", "input_queue.json")
WEB_URL = "http://localhost:7860/web_send"

def send_to_web(msg):
    try:
        requests.post(WEB_URL, json={"message": msg}, timeout=5)
        print("[Responder] Enviado a WEB")
    except:
        print("[Responder] Error enviando a WEB")

def send_to_telegram(msg, thinking_mid=None):
    try:
        if not os.path.exists(CONFIG_PATH): 
            print(f"[Responder] Config no encontrada: {CONFIG_PATH}")
            return
        with open(CONFIG_PATH, "r") as f: 
            cfg = json.load(f)["credentials"]
        token, admin_id = cfg["telegram_bot"], cfg["telegram_admin"]
        
        # [STORM PROTOCOL SUGGESTION]: Borrar el indicador de carga
        if thinking_mid:
            try:
                requests.post(f"https://api.telegram.org/bot{token}/deleteMessage", 
                              json={"chat_id": admin_id, "message_id": thinking_mid}, timeout=5)
                print(f"[Responder] Indicador {thinking_mid} borrado.")
            except: pass

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": admin_id, "text": msg}, timeout=10)
        print(f"[Responder] Telegram Status: {r.status_code}")
    except Exception as e:
        print(f"[Responder] Error Telegram: {e}")

def get_and_mark_source():
    """Busca el ultimo mensaje sin responder y lo marca."""
    try:
        if not os.path.exists(QUEUE_PATH): return "both", None
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Buscar el ultimo que no este marcado como 'responded'
        for i in range(len(data)-1, -1, -1):
            if data[i].get("status") != "responded":
                source = data[i].get("source", "both")
                thinking_mid = data[i].get("thinking_mid")
                # Marcar como respondido
                data[i]["status"] = "responded"
                with open(QUEUE_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return source, thinking_mid
    except: pass
    return "both", None

def smart_respond(mensaje, thinking_mid=None):
    """Detecta el origen automáticamente y responde."""
    target, t_mid = get_and_mark_source()
    # Si t_mid es None pero pasamos uno por argumento, lo usamos
    final_mid = thinking_mid if thinking_mid else t_mid
    
    if target in ["web", "both"]:
        send_to_web(mensaje)
    if target in ["telegram", "both"]:
        send_to_telegram(mensaje, final_mid)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    args = sys.argv[1:]
    target = "auto"
    thinking_mid = None
    
    if args[0] == "--web":
        target = "web"
        mensaje = " ".join(args[1:])
    elif args[0] == "--telegram":
        target = "telegram"
        mensaje = " ".join(args[1:])
    else:
        # Modo Auto: Detecta y marca como consumido
        target, thinking_mid = get_and_mark_source()
        mensaje = " ".join(args)
    
    if target in ["web", "both"]:
        send_to_web(mensaje)
    if target in ["telegram", "both"]:
        send_to_telegram(mensaje, thinking_mid)
