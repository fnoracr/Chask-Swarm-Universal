"""
process_watchdog.py — Centinela del Enjambre Chask Swarm
=========================================================
Vigila cada 30s que todos los daemons críticos estén vivos.
- Si un daemon cae: INYECTA aviso directamente en el IDE (no via cola).
- Si el IDE/Enjambre está caída: la REINICIA automáticamente.
- Es el PRIMER daemon en cerrarse cuando el usuario cierra Antigravity.

Ejecutar con: python.exe Advanced_Tools\process_watchdog.py  (necesita UI para inyectar)
Lanzar con:   start "ChaskWatchdog" /MIN python.exe Advanced_Tools\process_watchdog.py
"""
import os
import sys
import json
import time
import ctypes
import subprocess
import shutil
from datetime import datetime

# ── CONFIGURACIÓN ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "Logs_Sistema", "watchdog.log")
CHECK_INTERVAL = 30  # segundos
COOLDOWN = 300  # 5 minutos entre alertas del mismo daemon
SHUTDOWN_FLAG = os.path.join(BASE_DIR, "watchdog_shutdown.flag")

# Importar motor de inyección Enjambre V7.4
try:
    sys.path.append(os.path.join(BASE_DIR, "Advanced_Tools"))
    import chask_stealth_injector as nsi
except ImportError:
    nsi = None

# Python ejecutable (priorizar Python 3.11 con deps instaladas)
PY311 = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Local", "Programs", "Python", "Python311", "python.exe"
)
PYTHON_EXE = PY311 if os.path.isfile(PY311) else (shutil.which("python") or sys.executable)
PYTHONW_EXE = PYTHON_EXE.replace("python.exe", "pythonw.exe")

# ── PROCESOS A VIGILAR ──
WATCHED_PROCESSES = [
    {
        "name": "Unified Daemon (Telegram+Discord+Web)",
        "match": "unified_daemon.py",
        "critical": True,
        "restart": [PYTHON_EXE, os.path.join(BASE_DIR, "unified_daemon.py")],
        "use_start": True,  # Lanzar con start /MIN para que tenga ventana propia
    },
    {
        "name": "Backup System",
        "match": "backup_system.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "backup_system.py")],
    },
    {
        "name": "Daily Report",
        "match": "daily_report.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "daily_report.py")],
    },
    {
        "name": "Web Monitor",
        "match": "web_monitor.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "web_monitor.py")],
    },
]


def log(message):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


def get_running_commands():
    """Obtiene todas las líneas de comandos de procesos Python activos."""
    try:
        out = subprocess.check_output(
            'wmic process where "name=\'python.exe\' or name=\'pythonw.exe\'" get CommandLine /FORMAT:LIST',
            shell=True, text=True, stderr=subprocess.DEVNULL
        )
        return out.lower()
    except:
        return ""


def is_antigravity_running():
    """Comprueba si el IDE Antigravity está corriendo (API Win32, sin consola)."""
    try:
        TH32CS_SNAPPROCESS = 0x00000002
        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                        ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_void_p),
                        ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                        ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                        ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_char * 260)]
        kernel32 = ctypes.windll.kernel32
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == -1:
            return False
        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        found = False
        if kernel32.Process32First(snapshot, ctypes.byref(entry)):
            while True:
                if b"antigravity" in entry.szExeFile.lower():
                    found = True
                    break
                if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                    break
        kernel32.CloseHandle(snapshot)
        return found
    except:
        return False


def find_antigravity_exe():
    """Busca el ejecutable de Antigravity."""
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Antigravity", "Antigravity.exe"),
    ]
    gemini_dir = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity")
    if os.path.isdir(gemini_dir):
        for f in os.listdir(gemini_dir):
            if f.lower().endswith(".exe"):
                candidates.append(os.path.join(gemini_dir, f))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def restart_antigravity():
    """Reinicia el IDE Antigravity."""
    ide_path = find_antigravity_exe()
    if not ide_path:
        log("[RESTART] Antigravity.exe no encontrado")
        return False
    try:
        subprocess.Popen(
            [ide_path],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )
        log(f"[RESTART] Antigravity reiniciado: {ide_path}")
        time.sleep(8)  # Esperar a que arranque
        # Re-inyectar contexto
        boot_script = os.path.join(BASE_DIR, "Advanced_Tools", "boot_injection.py")
        if os.path.isfile(boot_script):
            subprocess.Popen(
                [PYTHON_EXE, boot_script],
                cwd=BASE_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            log("[RESTART] boot_injection.py ejecutado")
        return True
    except Exception as e:
        log(f"[RESTART] Error: {e}")
        return False


def inject_alert_to_ide(message):
    """Inyecta un aviso directamente en el IDE usando el motor Stealth V7.4."""
    if not nsi:
        log("[INJECT] Motor chask_stealth_injector no disponible")
        return False
    
    log(f"[INJECT] Enviando alerta stealth: {message[:40]}...")
    success, info = nsi.inject_to_antigravity(message)
    if success:
        log(f"[INJECT] Alerta exitosa: {info}")
    else:
        log(f"[INJECT] Fallo en alerta: {info}")
    return success


def check_qdrant():
    """Comprueba si Qdrant responde en localhost:6333."""
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:6333/collections", timeout=5)
        return req.status == 200
    except Exception:
        return False


def restart_daemon(proc):
    """Reinicia un daemon caído."""
    restart_cmd = proc.get("restart")
    if not restart_cmd:
        return False
    try:
        if proc.get("use_start"):
            # Usar cmd /c start para que tenga ventana propia minimizada
            cmd_str = f'start "{proc["name"]}" /MIN "{restart_cmd[0]}" "{restart_cmd[1]}"'
            subprocess.Popen(cmd_str, shell=True, cwd=BASE_DIR)
        else:
            subprocess.Popen(
                restart_cmd, cwd=BASE_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
            )
        log(f"[RESTART] {proc['name']} reiniciado")
        return True
    except Exception as e:
        log(f"[RESTART] Error reiniciando {proc['name']}: {e}")
        return False


def check_processes():
    """Verifica qué procesos deben estar vivos y cuáles han caído."""
    running = get_running_commands()
    dead = []
    alive = []
    for proc in WATCHED_PROCESSES:
        if proc["match"].lower() in running:
            alive.append(proc)
        else:
            dead.append(proc)
    return alive, dead


def should_shutdown():
    """Comprueba si shutdown_cleanup ha puesto la señal de cierre."""
    if os.path.exists(SHUTDOWN_FLAG):
        try:
            os.remove(SHUTDOWN_FLAG)
        except:
            pass
        return True
    return False


def main():
    log("=" * 50)
    log("PROCESS WATCHDOG v2 — CENTINELA INICIADO")
    log(f"Vigilando {len(WATCHED_PROCESSES)} procesos cada {CHECK_INTERVAL}s")
    log(f"Python: {PYTHON_EXE}")
    log("=" * 50)

    last_alert = {}
    last_ide_check = 0
    last_qdrant_check = 0
    qdrant_fail_count = 0
    IDE_CHECK_INTERVAL = 60  # Comprobar IDE cada 60s
    QDRANT_CHECK_INTERVAL = 60  # Comprobar Qdrant cada 60s

    while True:
        # ── Señal de cierre (primer proceso en parar) ──
        if should_shutdown():
            log("Señal de cierre recibida. Watchdog terminando.")
            break

        try:
            alive, dead = check_processes()

            if dead:
                now = time.time()
                for d in dead:
                    last = last_alert.get(d["match"], 0)
                    if now - last > COOLDOWN:
                        last_alert[d["match"]] = now
                        log(f"CAIDO: {d['name']}")

                        # 1. Intentar reiniciar automáticamente
                        restarted = restart_daemon(d)

                        # 2. Notificar a Enjambre directamente en el IDE
                        status = "reiniciado" if restarted else "NO pudo reiniciarse"
                        alert_msg = (
                            f"[ENJAMBRE: WATCHDOG] [WATCHDOG {datetime.now().strftime('%H:%M:%S')}] "
                            f"ALERTA: {d['name']} ha caido. Estado: {status}."
                        )
                        inject_alert_to_ide(alert_msg)

            # ── Comprobar si Qdrant está vivo (cada 60s) ──
            now = time.time()
            if now - last_qdrant_check > QDRANT_CHECK_INTERVAL:
                last_qdrant_check = now
                if not check_qdrant():
                    qdrant_fail_count += 1
                    if qdrant_fail_count <= 2:
                        log("[QDRANT] Caido. Intentando reiniciar...")
                        try:
                            subprocess.run(
                                ["docker", "start", "qdrant"],
                                capture_output=True, timeout=15
                            )
                            time.sleep(3)
                            if check_qdrant():
                                log("[QDRANT] Reiniciado con exito")
                                inject_alert_to_ide(
                                    "[ENJAMBRE: WATCHDOG] Qdrant habia caido. "
                                    "Lo he reiniciado automaticamente. No requiere accion."
                                )
                                qdrant_fail_count = 0
                            else:
                                log("[QDRANT] Reinicio fallido")
                                inject_alert_to_ide(
                                    "[ENJAMBRE: WATCHDOG] ALERTA CRITICA: Qdrant ha caido "
                                    "y no responde tras reinicio. Memoria vectorial offline. "
                                    "Diagnostica con: docker logs qdrant"
                                )
                        except Exception as e:
                            log(f"[QDRANT] Error reiniciando: {e}")
                            inject_alert_to_ide(
                                f"[ENJAMBRE: WATCHDOG] Error reiniciando Qdrant: {str(e)[:100]}"
                            )
                    # Si ya falló 2+ veces, solo loguear sin spamear
                else:
                    if qdrant_fail_count > 0:
                        log("[QDRANT] Recuperado")
                    qdrant_fail_count = 0

            # ── Comprobar si el IDE está vivo (cada 60s) ──
            now = time.time()
            if now - last_ide_check > IDE_CHECK_INTERVAL:
                last_ide_check = now
                if not is_antigravity_running():
                    log("IDE Antigravity NO detectado. Reiniciando...")
                    restart_antigravity()

            # Log periódico
            if hasattr(main, '_cycle_count'):
                main._cycle_count += 1
            else:
                main._cycle_count = 1
            if main._cycle_count % 10 == 0:
                log(f"Estado: {len(alive)} vivos, {len(dead)} caidos")

        except Exception as e:
            log(f"Error en ciclo: {e}")

        time.sleep(CHECK_INTERVAL)

    log("WATCHDOG TERMINADO")


if __name__ == "__main__":
    main()
