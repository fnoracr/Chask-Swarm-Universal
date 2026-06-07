"""Diagnóstico completo de la cadena de comunicación Telegram -> Nora"""
import psutil
import json
import os
from datetime import datetime

print("=" * 70)
print("DIAGNÓSTICO COMPLETO DE COMUNICACIONES NORA")
print(f"Hora: {datetime.now().isoformat()}")
print("=" * 70)

# 1. Procesos Python activos
print("\n[1] PROCESOS PYTHON ACTIVOS:")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if p.info['cmdline'] and 'python' in p.info['name'].lower():
            cmd = " ".join(p.info['cmdline'])
            print(f"  PID={p.info['pid']}  {cmd[:120]}")
    except Exception:
        pass

# 2. Cola principal (Colas_Mensajes)
q1 = r"C:\Program Files\Chask_Swarm\Advanced_Tools\Colas_Mensajes\input_queue.json"
print(f"\n[2] COLA PRINCIPAL: {q1}")
print(f"  Existe: {os.path.exists(q1)}")
if os.path.exists(q1):
    with open(q1, "r", encoding="utf-8") as f:
        data = json.load(f)
    pending = [x for x in data if x.get("status") == "pending"]
    delivered = [x for x in data if x.get("status") == "delivered"]
    processed = [x for x in data if x.get("status") == "processed"]
    print(f"  Total: {len(data)} | Pending: {len(pending)} | Delivered: {len(delivered)} | Processed: {len(processed)}")
    if pending:
        print(f"  ÚLTIMO PENDING: ts={pending[-1]['ts']}")
        print(f"    msg={pending[-1]['message'][:100]}...")
    if data:
        print(f"  ÚLTIMO ENTRY:   ts={data[-1]['ts']} status={data[-1]['status']}")

# 3. Cola vieja (raíz Advanced_Tools)
q2 = r"C:\Program Files\Chask_Swarm\Advanced_Tools\input_queue.json"
print(f"\n[3] COLA VIEJA: {q2}")
print(f"  Existe: {os.path.exists(q2)}")
if os.path.exists(q2):
    with open(q2, "r", encoding="utf-8") as f:
        data2 = json.load(f)
    print(f"  Total: {len(data2)}")

# 4. unified_channel_daemon.py - log
log1 = r"C:\Program Files\Chask_Swarm\Advanced_Tools\unified_channel.log"
print(f"\n[4] LOG UNIFIED CHANNEL: {log1}")
print(f"  Existe: {os.path.exists(log1)}")
if os.path.exists(log1):
    with open(log1, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"  Total líneas: {len(lines)}")
    print(f"  Últimas 5 líneas:")
    for l in lines[-5:]:
        print(f"    {l.strip()}")

# 5. Verificar qué función deliver() se está usando realmente
print(f"\n[5] VERIFICACIÓN DE RUTAS EN unified_channel_daemon.py:")
daemon_path = r"C:\Program Files\Chask_Swarm\Advanced_Tools\Daemons\unified_channel_daemon.py"
if os.path.exists(daemon_path):
    with open(daemon_path, "r", encoding="utf-8") as f:
        src = f.read()
    # Buscar todas las definiciones de QUEUE_FILE
    for i, line in enumerate(src.split("\n"), 1):
        if "QUEUE_FILE" in line and "=" in line and "#" not in line.split("QUEUE_FILE")[0]:
            print(f"  Línea {i}: {line.strip()}")
    # Buscar todas las definiciones de deliver
    for i, line in enumerate(src.split("\n"), 1):
        if "def deliver" in line:
            print(f"  Línea {i}: {line.strip()}")

# 6. Verificar el queue_monitor_bg.py
monitor_path = r"C:\Program Files\Chask_Swarm\Advanced_Tools\queue_monitor_bg.py"
print(f"\n[6] QUEUE_MONITOR_BG.PY:")
print(f"  Existe: {os.path.exists(monitor_path)}")
if os.path.exists(monitor_path):
    with open(monitor_path, "r", encoding="utf-8") as f:
        print(f"  Contenido completo:")
        print(f.read())

# 7. Verificar si hay mensajes recientes de hoy (7:58 y 8:01)
print(f"\n[7] MENSAJES DE HOY EN LA COLA:")
if os.path.exists(q1):
    with open(q1, "r", encoding="utf-8") as f:
        data = json.load(f)
    today = datetime.now().strftime("%Y-%m-%05")
    for item in data:
        if "2026-06-05" in item.get("ts", ""):
            print(f"  ts={item['ts']} status={item['status']}")
            print(f"    msg={item['message'][:120]}...")

print("\n" + "=" * 70)
print("FIN DEL DIAGNÓSTICO")
