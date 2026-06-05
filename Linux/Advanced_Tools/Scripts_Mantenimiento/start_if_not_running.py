import psutil
import sys
import subprocess
import os

def is_running(script_name):
    for p in psutil.process_iter(['cmdline']):
        try:
            cmdline = p.info.get('cmdline')
            if cmdline:
                cmd_str = " ".join(cmdline).lower()
                if script_name.lower() in cmd_str and "python" in cmd_str and "start_if_not_running" not in cmd_str:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    script_to_check = sys.argv[1]
    command_to_run = sys.argv[2:]
    
    if not is_running(script_to_check):
        # Desacople total mediante WMI
        args_str = " ".join(f'"{arg}"' for arg in command_to_run[1:])
        cmd_str = f'"{command_to_run[0]}" {args_str}'
        wmic_cmd = ["wmic", "process", "call", "create", cmd_str]
        
        audit_log = r"C:\Program Files\Chask_Swarm\System_Logs\swarm_power_audit.log"
        from datetime import datetime
        import time
        
        def audit(msg):
            try:
                with open(audit_log, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
            except:
                pass
                
        audit(f"[INFO] Lanzando {script_to_check} vía WMI...")
        subprocess.Popen(wmic_cmd, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Validación de supervivencia
        time.sleep(2)
        if is_running(script_to_check):
            audit(f"[ÉXITO] El daemon {script_to_check} sobrevivió al arranque WMI.")
        else:
            audit(f"[ERROR FATAL] El daemon {script_to_check} crasheó o desapareció inmediatamente después de usar WMI.")
