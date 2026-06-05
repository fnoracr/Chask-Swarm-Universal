"""
TELEGRAM WATCHER — Vigila pending_messages.json cada N segundos.
Imprime a stdout cuando encuentra mensajes con status "pending".
Enjambre lanza esto como comando de fondo y consulta su output entre tareas.
"""
import json
import os
import sys
import time

PENDING_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Message_Queues", "pending_messages.json")
CHECK_INTERVAL = 3  # segundos

def watch():
    print(f"[WATCHER] Vigilando {PENDING_FILE} cada {CHECK_INTERVAL}s", flush=True)
    seen_ids = set()
    
    # Load already-processed IDs to avoid re-alerting
    try:
        if os.path.exists(PENDING_FILE):
            with open(PENDING_FILE, "r", encoding="utf-8") as f:
                for msg in json.load(f):
                    seen_ids.add(msg.get("id", ""))
    except:
        pass
    
    while True:
        try:
            if os.path.exists(PENDING_FILE):
                with open(PENDING_FILE, "r", encoding="utf-8") as f:
                    messages = json.load(f)
                
                for msg in messages:
                    msg_id = msg.get("id", "")
                    if msg.get("status") == "pending" and msg_id not in seen_ids:
                        seen_ids.add(msg_id)
                        ts = msg.get("ts", "?")[:19]
                        text = msg.get("text", "")
                        print(f"\n[TELEGRAM {ts}] {text}", flush=True)
        except Exception as e:
            pass  # Silencioso si hay error de lectura concurrente
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    watch()
