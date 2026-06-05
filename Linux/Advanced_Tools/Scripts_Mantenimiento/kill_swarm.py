import os
import sys
import time
import subprocess
from datetime import datetime
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_LOG = os.path.join(BASE_DIR, "System_Logs", "swarm_power_audit.log")

def audit(msg):
    try:
        os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def kill_swarm():
    try:
        audit("==================================================")
        audit("[INICIO] Apagado completo del enjambre ejecutado por [Nombre_IA]")
        
        lock_file = os.path.join(BASE_DIR, "kill_switch.lock")
        with open(lock_file, "w") as f:
            f.write(datetime.now().isoformat())
        if os.path.exists(lock_file):
            audit("[ÉXITO] Paso 1: kill_switch.lock creado correctamente.")
            
        subprocess.run('powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match \'process_watchdog.py\' } | Stop-Process -Force"', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 2: process_watchdog.py aniquilado.")

        subprocess.run('powershell -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match \'python\' -and $_.CommandLine -match \'Chask_Swarm\' -and $_.CommandLine -notmatch \'telegram_sentinel.py\' -and $_.ProcessId -ne $PID }; foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force }"', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 3: Todos los daemons Python secundarios aniquilados (excepto Sentinel y este script).")

        subprocess.run('powershell -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match \'node.exe\' -and $_.CommandLine -match \'n8n\' }; foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force }"', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 4: Proceso n8n (node.exe) aniquilado.")

        subprocess.run('docker stop qdrant n8n', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 5: Contenedores Qdrant y N8N detenidos.")

        def _close_ide_delayed():
            time.sleep(2)
            subprocess.run('taskkill /IM Antigravity.exe /F', shell=True, capture_output=True)
            audit("[ÉXITO] Paso 6: IDE Antigravity cerrado.")
            audit("[FIN] Proceso de apagado concluido.")
            audit("==================================================")
            os._exit(0)
            
        threading.Thread(target=_close_ide_delayed, daemon=True).start()
        
        # Esperar a que el thread cierre todo
        time.sleep(5)
    except Exception as e:
        audit(f"[CRITICAL ERROR] Fallo durante kill_swarm: {e}")

if __name__ == "__main__":
    kill_swarm()
