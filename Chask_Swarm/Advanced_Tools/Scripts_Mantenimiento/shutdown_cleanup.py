"""
shutdown_cleanup.py — Limpieza Automática al Cerrar Charm
================================================================
Este script corre como daemon (pythonw) y vigila el proceso Charm.exe.
Cuando detecta que Charm se cierra:
1. Espera 5 segundos de gracia (por si es un reinicio rápido del IDE)
2. Si sigue cerrado, mata TODOS los procesos pythonw (daemons del enjambre)
3. Se excluye a sí mismo hasta el final
4. NO toca a telegram_sentinel.py (corre como proceso aparte)
5. Se auto-termina

Ejecutar con: pythonw Advanced_Tools\shutdown_cleanup.py
"""

import os
import sys
import time
import ctypes
import subprocess
from datetime import datetime

# ── CONSTANTES ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_PATH = os.path.join(BASE_DIR, "cleanup.log")
SENTINEL_SCRIPT = "Advanced_Tools/Daemons/telegram_sentinel.py"
POLL_INTERVAL = 5        # Segundos entre comprobaciones
GRACE_PERIOD = 10        # Segundos de espera antes de limpiar (evita false positives en reinicios)
MY_PID = os.getpid()


def log(msg):
    """Log silencioso a archivo."""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def is_charm_running():
    """Comprueba si hay algún proceso Antigravity.exe corriendo."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Antigravity.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        # Si hay proceso, la salida contiene "Antigravity.exe"
        return "Antigravity.exe" in result.stdout
    except Exception as e:
        log(f"Error comprobando Antigravity: {e}")
        return True  # En caso de duda, asumimos que sigue vivo


def get_pythonw_pids():
    """Obtiene todos los PIDs de pythonw.exe excepto el mío."""
    pids = []
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line or "pythonw.exe" not in line:
                continue
            # Formato CSV: "pythonw.exe","PID","Console","1","MEM"
            parts = line.replace('"', '').split(",")
            if len(parts) >= 2:
                try:
                    pid = int(parts[1].strip())
                    if pid != MY_PID:
                        pids.append(pid)
                except ValueError:
                    continue
    except Exception as e:
        log(f"Error listando pythonw PIDs: {e}")
    return pids


def get_sentinel_pids():
    """Obtiene PIDs del telegram_sentinel (para NO matarlo).
    Usa múltiples métodos de detección para máxima robustez."""
    sentinel_pids = set()
    PROTECTED_SCRIPTS = ["Advanced_Tools/Daemons/telegram_sentinel.py"]

    try:
        # Método 1: wmic con formato list (más fiable que CSV)
        result = subprocess.run(
            'wmic process where "name=\'pythonw.exe\'" get ProcessId,CommandLine /FORMAT:LIST',
            shell=True, capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        current_cmdline = ""
        current_pid = None
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("CommandLine="):
                current_cmdline = line[12:]
            elif line.startswith("ProcessId="):
                try:
                    current_pid = int(line[10:])
                except ValueError:
                    current_pid = None
            elif not line and current_cmdline and current_pid:
                for script in PROTECTED_SCRIPTS:
                    if script.lower() in current_cmdline.lower():
                        sentinel_pids.add(current_pid)
                        log(f"  PROTEGIDO: PID {current_pid} ({script})")
                current_cmdline = ""
                current_pid = None
    except Exception as e:
        log(f"Error buscando sentinel PIDs (método 1): {e}")

    if not sentinel_pids:
        # Método 2: Fallback con powershell
        try:
            result = subprocess.run(
                'powershell -Command "Get-CimInstance Win32_Process | Where-Object {$_.Name -eq \'pythonw.exe\' -and $_.CommandLine -match \'sentinel\'} | Select-Object -ExpandProperty ProcessId"',
                shell=True, capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.isdigit():
                    sentinel_pids.add(int(line))
                    log(f"  PROTEGIDO (fallback): PID {line}")
        except Exception as e:
            log(f"Error buscando sentinel PIDs (método 2): {e}")

    return sentinel_pids


def kill_pid(pid):
    """Mata un proceso por PID."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True
    except Exception:
        return False


def cleanup_all_daemons():
    """Mata todos los pythonw excepto el sentinel y a mí mismo.
    PASO 1: Señala al watchdog que pare (es el PRIMERO en cerrarse).
    PASO 2: Espera a que el watchdog termine.
    PASO 3: Mata el resto de daemons.
    """
    log("=" * 50)
    log("INICIO DE LIMPIEZA — Charm cerrado detectado")
    log("=" * 50)

    # PASO 1: Señalar al watchdog que se cierre
    watchdog_flag = os.path.join(BASE_DIR, "watchdog_shutdown.flag")
    try:
        with open(watchdog_flag, "w") as f:
            f.write(datetime.now().isoformat())
        log("Señal de cierre enviada a process_watchdog")
    except:
        pass
    time.sleep(3)  # Dar tiempo al watchdog para cerrarse

    # PASO 2: Matar pythonw.exe o python.exe que corra unified_channel_daemon.py
    try:
        result = subprocess.run(
            'wmic process where "name=\'python.exe\' or name=\'pythonw.exe\'" get ProcessId,CommandLine /FORMAT:CSV',
            shell=True, capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in result.stdout.strip().split("\n"):
            if "unified_channel_daemon.py" in line.lower():
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if parts:
                    try:
                        pid = int(parts[-1])
                        kill_pid(pid)
                        log(f"  KILL unified_channel_daemon PID {pid}")
                    except ValueError:
                        pass
    except:
        pass

    # PASO 3: Matar todos los pythonw excepto sentinel y yo
    sentinel_pids = get_sentinel_pids()
    all_pids = get_pythonw_pids()
    targets = [pid for pid in all_pids if pid not in sentinel_pids and pid != MY_PID]

    log(f"PIDs pythonw totales: {len(all_pids)}")
    log(f"PIDs sentinel (protegidos): {sentinel_pids}")
    log(f"PIDs a eliminar: {len(targets)}")

    killed = 0
    for pid in targets:
        if kill_pid(pid):
            killed += 1
            log(f"  KILL PID {pid} — OK")
        else:
            log(f"  KILL PID {pid} — FAIL")

    log(f"Limpieza completada: {killed}/{len(targets)} procesos eliminados")
    log("Shutdown cleanup finalizando.")
    log("=" * 50)


def main():
    log("=" * 50)
    log(f"SHUTDOWN CLEANUP INICIADO (PID: {MY_PID})")
    if "--force" in sys.argv:
        log("MODO FORCE ACTIVADO. Purgando el enjambre de emergencia...")
        # Crear lock
        lock_file = os.path.join(BASE_DIR, "kill_switch.lock")
        try:
            with open(lock_file, "w") as f:
                f.write(datetime.now().isoformat())
            log("kill_switch.lock creado.")
        except Exception as e:
            log(f"Error creando lock: {e}")
            
        # Matar Antigravity
        subprocess.run(["taskkill", "/F", "/IM", "Antigravity.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        log("Antigravity.exe forzado a cerrar (si existía).")
        
        cleanup_all_daemons()
        return

    log("Vigilando cierre de Charm.exe...")
    log("=" * 50)

    # Esperar a que Charm arranque primero
    # (este script se lanza junto con los daemons, antes de que el IDE arranque)
    startup_wait = 0
    while not is_charm_running() and startup_wait < 120:
        time.sleep(2)
        startup_wait += 2

    if not is_charm_running():
        log("Charm no arrancó en 120s. Saliendo sin limpiar.")
        return

    log("Charm detectado. Comenzando vigilancia.")

    # Bucle principal: vigilar que Charm siga vivo
    while True:
        time.sleep(POLL_INTERVAL)

        if not is_charm_running():
            log(f"Charm NO detectado. Esperando {GRACE_PERIOD}s de gracia...")

            # Periodo de gracia (por si es un reinicio rápido)
            time.sleep(GRACE_PERIOD)

            if not is_charm_running():
                # Confirmado: Charm cerrado definitivamente
                cleanup_all_daemons()
                break
            else:
                log("Charm volvió durante el periodo de gracia. Falsa alarma.")

    log("Shutdown cleanup terminado. Auto-terminando.")


if __name__ == "__main__":
    main()
