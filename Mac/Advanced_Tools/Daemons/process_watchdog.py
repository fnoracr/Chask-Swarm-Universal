"""
process_watchdog.py — Centinela del Enjambre Chask Swarm
=========================================================
Vigila cada 30s que todos los daemons críticos estén vivos.
- Si un daemon cae: INYECTA aviso directamente en el IDE (no via cola).
- Si el IDE/Enjambre está caída: la REINICIA automáticamente.
- Es el PRIMER daemon en cerrarse cuando el usuario cierra [Nombre_IA].

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

# Obligar a trabajar siempre en el directorio del enjambre
os.chdir(r"C:\Program Files\Chask_Swarm")

# ── CONFIGURACIÓN ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_FILE = os.path.join(BASE_DIR, "System_Logs", "watchdog.log")
CHECK_INTERVAL = 30  # segundos
COOLDOWN = 300  # 5 minutos entre alertas del mismo daemon
SHUTDOWN_FLAG = os.path.join(BASE_DIR, "watchdog_shutdown.flag")
KILL_SWITCH_LOCK = os.path.join(BASE_DIR, "kill_switch.lock")  # creado por Off [Nombre_IA], borrado por On [Nombre_IA]

# Importar motor de inyección V8 (detección dinámica por proceso)
HAS_INJECTOR = False

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
        "name": "Unified Channel Daemon (Telegram+Discord+Web)",
        "match": "unified_channel_daemon.py",
        "critical": True,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "Daemons", "unified_channel_daemon.py")],
    },
    {
        "name": "Web Monitor",
        "match": "web_monitor.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "web_monitor.py")],
    },
    {
        "name": "[Nombre_IA] Panel (Web UI :7860)",
        "match": "web_dashboard_pro.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "dashboard", "web_dashboard_pro.py")],
    },
    {
        "name": "Swarm AI Watchdog (Pool de IAs)",
        "match": "swarm_ai_watchdog.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "swarm_ai_watchdog.py")],
    },
    {
        "name": "[Nombre_IA] Edu P2P Daemon",
        "match": "learning_p2p_daemon.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "learning_p2p_daemon.py")],
    },
    {
        "name": "N8N Bridge Daemon (Docker Proxy)",
        "match": "n8n_bridge_daemon.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "modules", "N8N_Integration", "n8n_bridge_daemon.py")],
    },
    {
        "name": "Guardian Daemon (Seguridad Suprema)",
        "match": "guardian_daemon.py",
        "critical": True,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "guardian_daemon.py")],
    },
    {
        "name": "Auto Purge Deleted Daemon",
        "match": "auto_purge_deleted.py",
        "critical": False,
        "restart": [PYTHONW_EXE, os.path.join(BASE_DIR, "Advanced_Tools", "auto_purge_deleted.py")],
    },
]



def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    try:
        print(msg)
    except:
        pass


def get_running_commands():
    """Obtiene todas las líneas de comandos de procesos Python activos."""
    try:
        out = subprocess.check_output(
            'wmic process where "name=\'python.exe\' or name=\'pythonw.exe\'" get CommandLine /FORMAT:LIST',
            shell=True, text=True, stderr=subprocess.DEVNULL, timeout=8, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return out.lower().replace('"', '')
    except subprocess.TimeoutExpired:
        log("[WARNING] La consulta WMIC superó el tiempo límite (timeout de 8s). Evitando bloqueo del vigilante.")
        return ""
    except:
        return ""



def is_charm_running():
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


def find_charm_exe():
    """Busca el ejecutable de Antigravity (IDE)."""
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Antigravity", "Antigravity.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def restart_charm():
    """Reinicia el IDE directamente como se hacía en V3 para evadir problemas de herencia oculta."""
    ide_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Antigravity", "Antigravity.exe")
    if not os.path.exists(ide_path):
        log(f"[ERROR] No se pudo encontrar Antigravity en {ide_path}")
        return False
        
    try:
        log("[RESTART] Lanzando instancia de Antigravity ([Nombre_IA] Workspace)...")
        # Instancia Normal
        subprocess.Popen(
            [ide_path, "--user-data-dir=C:\\Users\\fnora\\Desktop\\[Nombre_IA]_Workspace\\.antigravity_data", "C:\\Users\\fnora\\Desktop\\[Nombre_IA]_Workspace"],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )
        log("[RESTART] Instancia de Antigravity lanzada exitosamente.")
    except Exception as e:
        log(f"[ERROR] No se pudo reiniciar [Nombre_IA]: {e}")
        
        time.sleep(8)  # Esperar a que arranque
        # Re-inyectar contexto
        boot_script = os.path.join(BASE_DIR, "Advanced_Tools", "boot_injection.py")
        if os.path.isfile(boot_script):
            try:
                subprocess.Popen(
                    [PYTHON_EXE, boot_script],
                    cwd=BASE_DIR,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                log("[RESTART] boot_injection.py ejecutado")
            except Exception as e:
                pass
        return True
    return False


def inject_alert_to_ide(message):
    """Encola una alerta de forma pasiva y notifica al Admin por Telegram sin robar foco."""
    log(f"[WATCHDOG_ALERT] {message}")
    
    # 1. Encolar de forma puramente pasiva en pending_messages.json
    pending_file = os.path.join(BASE_DIR, "Message_Queues", "pending_messages.json")
    try:
        messages = []
        if os.path.exists(pending_file):
            try:
                with open(pending_file, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            except:
                messages = []
        
        # Evitar duplicados de la misma alerta pendiente
        if not any(m.get("text") == message and m.get("status") == "pending" for m in messages):
            messages.append({
                "ts": datetime.now().isoformat(),
                "source": "watchdog",
                "text": message,
                "status": "pending"
            })
            with open(pending_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            log("[WATCHDOG_ALERT] Encolado pasivamente en pending_messages.json")
    except Exception as e:
        log(f"[WATCHDOG_ALERT] Error al encolar: {e}")

    # 2. Enviar por Telegram desactivado a petición del usuario para no saturar
    # try:
    #     telegram_script = os.path.join(BASE_DIR, "charm_telegram.py")
    #     if os.path.isfile(telegram_script):
    #         subprocess.Popen(
    #             [PYTHON_EXE, telegram_script, "send", message],
    #             cwd=BASE_DIR,
    #             creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    #             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
    #         )
    #         log("[WATCHDOG_ALERT] Notificación enviada asíncronamente por Telegram")
    # except Exception as e:
    #     log(f"[WATCHDOG_ALERT] Error enviando Telegram: {e}")
        
    return True


def check_qdrant():
    """Comprueba si Qdrant responde en localhost:6333."""
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:6333/collections", timeout=5)
        return req.status == 200
    except Exception:
        return False

def check_n8n_docker():
    """Comprueba si el contenedor n8n está en ejecución."""
    try:
        out = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Running}}", "n8n"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return out.strip().lower() == "true"
    except Exception:
        return False


def restart_daemon(proc):
    """Reinicia un daemon caído."""
    restart_cmd = proc.get("restart")
    if not restart_cmd:
        return False
    try:
        if proc.get("use_start"):
            # Usar PowerShell Start-Process con ventana minimizada para que sea 100% inmune a errores de escape de CMD
            args_list = [f"'{arg}'" for arg in restart_cmd[1:]]
            args_str = ", ".join(args_list)
            ps_command = f"Start-Process -FilePath '{restart_cmd[0]}' -ArgumentList {args_str} -WindowStyle Minimized"
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_command],
                cwd=BASE_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
            )
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
    last_n8n_check = 0
    qdrant_fail_count = 0
    IDE_CHECK_INTERVAL = 60  # Comprobar IDE cada 60s
    QDRANT_CHECK_INTERVAL = 60  # Comprobar Qdrant cada 60s
    N8N_CHECK_INTERVAL = 60

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

                        # Si el Kill Switch está activo, NO reiniciar daemons
                        if os.path.exists(KILL_SWITCH_LOCK) and "Unified" not in d['name']:
                            log(f"[KILL SWITCH] Lock activo — NO se reinicia {d['name']}.")
                            continue

                        # 1. Intentar reiniciar automáticamente
                        restarted = restart_daemon(d)

                        # 2. Notificar a Enjambre directamente en el IDE
                        status = "reiniciado" if restarted else "NO pudo reiniciarse"
                        alert_msg = (
                            f"[ENJAMBRE: WATCHDOG] [WATCHDOG {datetime.now().strftime('%H:%M:%S')}] "
                            f"ALERTA: {d['name']} ha caido. Estado: {status}."
                        )
                        inject_alert_to_ide(alert_msg)

            # 📡 Comprobar si N8N Docker está vivo (cada 60s) 📡
            now = time.time()
            if now - last_n8n_check > N8N_CHECK_INTERVAL:
                last_n8n_check = now
                if not check_n8n_docker():
                    if os.path.exists(KILL_SWITCH_LOCK):
                        log("[N8N] Kill Switch activo - NO se alerta ni reinicia.")
                    else:
                        log("[N8N DOCKER] Contenedor caído. Intentando iniciar...")
                        try:
                            subprocess.run(["docker", "start", "n8n"], capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
                        except:
                            pass

            # ── Comprobar si Qdrant está vivo (cada 60s) ──
            now = time.time()
            if now - last_qdrant_check > QDRANT_CHECK_INTERVAL:
                last_qdrant_check = now
                if not check_qdrant():
                    if os.path.exists(KILL_SWITCH_LOCK):
                        log("[QDRANT] Kill Switch activo - NO se alerta ni reinicia.")
                    else:
                        qdrant_fail_count += 1
                        if qdrant_fail_count <= 2:
                            log("[QDRANT] Caido. Intentando reiniciar...")
                            try:
                                # 1. Intentar arranque estándar
                                res = subprocess.run(
                                    ["docker", "start", "qdrant"],
                                    capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                # 2. Si no responde el daemon de Docker, intentar arrancar Docker Desktop
                                if res.returncode != 0 and ("failed" in res.stderr.lower() or "error" in res.stderr.lower() or "not running" in res.stderr.lower() or "npipe" in res.stderr.lower()):
                                    log("[DOCKER] Docker Desktop no parece estar activo. Intentando levantarlo...")
                                    docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
                                    if os.path.isfile(docker_path):
                                        subprocess.Popen(
                                            [docker_path],
                                            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
                                        )
                                        log("[DOCKER] Iniciado ejecutable. Esperando 30s para inicializacion del daemon...")
                                        time.sleep(30)
                                        # Intentar start del contenedor de nuevo
                                        res = subprocess.run(
                                            ["docker", "start", "qdrant"],
                                            capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
                                        )
                                
                                time.sleep(3)
                                if check_qdrant():
                                    log("[QDRANT] Reiniciado con exito")
                                    inject_alert_to_ide(
                                        "[ENJAMBRE: WATCHDOG] Qdrant ha sido levantado automáticamente "
                                        "(incluyendo inicio de Docker Desktop). Memoria vectorial online."
                                    )
                                    qdrant_fail_count = 0
                                else:
                                    log("[QDRANT] Reinicio fallido")
                                    inject_alert_to_ide(
                                        "[ENJAMBRE: WATCHDOG] ALERTA CRITICA: Qdrant ha caido "
                                        "y no responde tras reinicio automático de Docker. "
                                        "Por favor, revisa docker logs o inicia Docker Desktop manualmente."
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
                if os.path.exists(KILL_SWITCH_LOCK):
                    log("[IDE] Kill Switch activo — NO se reinicia el IDE.")
                elif not is_charm_running():
                    log("IDE [Nombre_IA] NO detectado. Reiniciando...")
                    restart_charm()

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
    try:
        main()
    except Exception as e:
        import traceback
        log(f"CRITICAL WATCHDOG CRASH: {e}")
        log(traceback.format_exc())
