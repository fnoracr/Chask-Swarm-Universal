import os
import sys
import time
import json
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(BASE_DIR, "Message_Queues", "input_queue.json")

print("Monitor de cola de Telegram iniciado. Escuchando mensajes de input_queue.json...", flush=True)

while True:
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8", errors="replace") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
            
            changed = False
            for item in data:
                if item.get("status") == "pending":
                    # Imprimir para despertar a Antigravity (el daemon captura el stdout)
                    print(f"\nNUEVO MENSAJE DE TELEGRAM:\n{item.get('message', '')}\n", flush=True)
                    item["status"] = "processed"
                    changed = True
            
            if changed:
                with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                    
    except Exception as e:
        pass
        
    time.sleep(2)
