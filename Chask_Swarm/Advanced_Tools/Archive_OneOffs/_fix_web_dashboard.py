import os
import sys
import re

path = r'C:\Program Files\Chask_Swarm\Advanced_Tools\web_dashboard_pro.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

new_code = '''def add_to_queue(message: str, source: str = "web_dashboard"):
    """El panel web SOLO escribe en el JSON. El unified_daemon (COM-safe) inyecta."""
    from datetime import datetime
    import json, os
    try:
        data = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        data.append({"ts": datetime.now().isoformat(), "source": source, "message": message, "status": "pending"})
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Queue] Error: {e}"); return False'''

# Buscar la funcion y reemplazarla (hasta el return False)
text = re.sub(r'def add_to_queue\(message: str, source: str = .*?\):.*?return False', new_code, text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Sustitución completada")
