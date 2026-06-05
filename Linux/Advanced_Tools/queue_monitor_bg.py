import json
import time
import os
import sys

QUEUE_FILE = r"C:\Program Files\Chask_Swarn\Advanced_Tools\Message_Queues\input_queue.json"

def main():
    print("Iniciando monitor de cola ligero en background...", flush=True)
    while True:
        try:
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                changed = False
                for item in data:
                    if item.get("status") == "pending":
                        msg = item.get("message", "")
                        source = item.get("source", "unknown")
                        print(f"[{source.upper()}] Nuevo mensaje: {msg}", flush=True)
                        item["status"] = "delivered"
                        changed = True
                        
                if changed:
                    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
        time.sleep(3)

if __name__ == "__main__":
    main()
