"""
start_if_not_running.py — Launcher anti-duplicados para Chask Swarm
====================================================================
Uso desde bat:
  pythonw.exe start_if_not_running.py "nombre_clave" "ruta_python" "ruta_script"

Comprueba si ya hay un proceso pythonw corriendo cuya línea de comandos
contiene "nombre_clave". Si no existe, lo lanza como proceso detached.
"""
import sys
import os
import subprocess
import ctypes

def get_running_pyw_cmdlines():
    """Devuelve lista de líneas de comando de procesos pythonw activos."""
    try:
        import psutil
        import os
        my_pid = os.getpid()
        result = []
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if p.info['pid'] != my_pid and p.info['name'] and 'python' in p.info['name'].lower():
                    cmdline = ' '.join(p.info['cmdline'] or [])
                    if 'start_if_not_running.py' not in cmdline:
                        result.append(cmdline)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return result
    except ImportError:
        # Fallback sin psutil: usar wmic
        try:
            out = subprocess.check_output(
                'wmic process where "name like \'%python%\'" get commandline',
                shell=True, stderr=subprocess.DEVNULL, timeout=10
            ).decode('utf-8', errors='replace')
            return [line.strip() for line in out.splitlines() if line.strip() and 'start_if_not_running.py' not in line]
        except Exception:
            return []

def main():
    if len(sys.argv) < 4:
        print("Uso: start_if_not_running.py <clave> <python_exe> <script>")
        sys.exit(1)

    key        = sys.argv[1]   # p.ej. "unified_channel_daemon.py"
    python_exe = sys.argv[2]   # ruta a pythonw.exe
    script     = sys.argv[3]   # ruta al script .py

    log_file = r"C:\Program Files\Chask_Swarm\Logs_Sistema\swarm_power_audit.log"

    def audit(msg):
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [LAUNCHER] {msg}\n")
        except Exception:
            pass

    # Verificar si ya está corriendo
    running = get_running_pyw_cmdlines()
    for cmdline in running:
        if key in cmdline:
            audit(f"Ya en ejecución (skip): {key}")
            sys.exit(0)

    # No está corriendo — lanzar como proceso detached
    if not os.path.exists(script):
        audit(f"Script no encontrado: {script}")
        sys.exit(1)

    try:
        DETACHED = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        proc = subprocess.Popen(
            [python_exe, script],
            creationflags=DETACHED | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
            cwd=os.path.dirname(script)
        )
        audit(f"Lanzado PID {proc.pid}: {key}")
    except Exception as e:
        audit(f"Error lanzando {key}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
