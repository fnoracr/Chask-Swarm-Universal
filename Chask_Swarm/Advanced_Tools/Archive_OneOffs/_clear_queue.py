import json
import os

path = r"C:\Program Files\Chask_Swarm\Advanced_Tools\input_queue.json"
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for msg in data:
        if msg.get("status") == "pending":
            msg["status"] = "processed"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f"Error: {e}")
