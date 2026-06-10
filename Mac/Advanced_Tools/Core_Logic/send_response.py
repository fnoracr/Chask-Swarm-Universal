import sys
import os
import json
from datetime import datetime

QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_queue.json")

def send_response(tag: str, msg: str):
    data = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
            
    # Solo agregar si no esta ya pendiente (anti-duplicados simple)
    for entry in data:
        if entry.get("status") == "pending" and entry.get("tag") == tag and entry.get("message") == msg:
            print("[SendResponse] El mensaje ya esta en la cola pendiente.")
            return

    new_entry = {
        "ts": datetime.now().isoformat(),
        "tag": tag,
        "message": msg,
        "status": "pending"
    }
    
    data.append(new_entry)
    
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    print(f"[SendResponse] Mensaje encolado exitosamente para la etiqueta {tag}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Uso: python send_response.py "[ETIQUETA]" "mensaje"')
        sys.exit(1)
        
    tag = sys.argv[1]
    msg = sys.argv[2]
    
    # Manejar caso de sys.argv multiples si no se usan comillas bien
    if len(sys.argv) > 3:
        msg = " ".join(sys.argv[2:])
        
    send_response(tag, msg)
