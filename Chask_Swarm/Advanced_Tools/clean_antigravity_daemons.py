import psutil
import os
import sys

def kill_daemons():
    print("Buscando procesos zombis de Antigravity (queue_sentinel.py y antigravity_telegram.py)...")
    target_scripts = ["queue_sentinel.py", "antigravity_telegram.py"]
    killed_count = 0

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] in ('python.exe', 'pythonw.exe'):
                cmdline = proc.info.get('cmdline') or []
                cmd_str = " ".join(cmdline).lower()
                
                if any(script in cmd_str for script in target_scripts):
                    print(f"Matando proceso {proc.info['pid']}: {cmd_str}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    print(f"Limpieza completada. {killed_count} procesos eliminados.")

if __name__ == "__main__":
    kill_daemons()
