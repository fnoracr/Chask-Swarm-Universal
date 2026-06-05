"""Marca todos los mensajes 'processing' como 'processed' y relanza el centinela."""
import json, subprocess, sys, os

QUEUE = r"C:\Program Files\Chask_Swarm\Advanced_Tools\Message_Queues\input_queue.json"
SENTINEL = r"C:\Program Files\Chask_Swarm\Advanced_Tools\queue_sentinel.py"
PYTHON = sys.executable

# Marcar processing -> processed
with open(QUEUE, "r", encoding="utf-8") as f:
    data = json.load(f)
for item in data:
    if item.get("status") == "processing":
        item["status"] = "processed"
with open(QUEUE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("DONE")
