"""
telegram_sentinel.py — Centinela de Telegram (siempre activo, INMORTAL)
========================================================================
Este script es el ÚNICO proceso que sobrevive al cierre de Charm.
Corre SIEMPRE en segundo plano (arranca con Windows via Startup).

Su misión:
1. Escuchar mensajes de Telegram del administrador 24/7
2. Si llega un mensaje y Charm NO está corriendo:
   a. Responde "Recibido. Arrancando sistema..." por Telegram
   b. Guarda el mensaje en input_queue.json
   c. Arranca todo el sistema Chask Swarm (Chask_Swarm.exe o process_watchdog.py)
   d. Espera a que Charm esté listo
   e. El boot_injection.py del launcher se encarga de pasar el mensaje
3. Si Charm SÍ está corriendo Y unified_daemon está activo: duerme (no interfiere)
4. Intercepta /on y /off como kill switch independiente

PROTECCIÓN: shutdown_cleanup.py NUNCA debe matar este proceso.
Identificación: La línea de comandos contiene "Advanced_Tools/Daemons/telegram_sentinel.py"

Ejecutar con: pythonw Advanced_Tools\telegram_sentinel.py
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime

# ── CONSTANTES ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADVANCED_DIR = os.path.join(BASE_DIR, "Advanced_Tools")
LOG_PATH = os.path.join(BASE_DIR, "Logs_Sistema", "sentinel.log")
QUEUE_PATH = os.path.join(ADVANCED_DIR, "Colas_Mensajes", "input_queue.json")
STATE_FILE = os.path.join(BASE_DIR, "Colas_Mensajes", "telegram_sentinel_state.txt")

# Credenciales
MASTER_CREDS = os.path.join(BASE_DIR, "Configuracion", "master_credentials.json")
AGENTS_CONFIG = os.path.join(BASE_DIR, "agents_config.json")

POLL_TIMEOUT = 30
STARTUP_WAIT = 120
CHECK_INTERVAL = 3
COOLDOWN_AFTER_BOOT = 45


def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def get_config():
    """Lee credenciales de Telegram (soporta ambos formatos de config)."""
    # Intentar master_credentials.json primero (formato nuevo)
    if os.path.exists(MASTER_CREDS):
        try:
            with open(MASTER_CREDS, "r") as f:
                creds = json.load(f)["credentials"]
            return creds["telegram_bot"], creds["telegram_admin"]
        except Exception:
            pass
    # Fallback: agents_config.json (formato original)
    if os.path.exists(AGENTS_CONFIG):
        try:
            with open(AGENTS_CONFIG, "r") as f:
                creds = json.load(f)["credentials"]
            return creds["telegram_bot"], creds["telegram_admin"]
        except Exception:
            pass
    return None, None


def get_last_update_id():
    """Lee el último update_id, sincronizado con el daemon principal."""
    # Intentar nuestro propio state primero
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return int(f.read().strip())
        except Exception:
            pass
    # Sincronizar con el daemon
    daemon_state = os.path.join(BASE_DIR, "Colas_Mensajes", "telegram_state.txt")
    if os.path.exists(daemon_state):
        try:
            with open(daemon_state, "r") as f:
                return int(f.read().strip())
        except Exception:
            pass
    return 0


def save_last_update_id(update_id):
    try:
        with open(STATE_FILE, "w") as f:
            f.write(str(update_id))
        # Sincronizar para evitar duplicados cuando unified_daemon arranque
        daemon_state = os.path.join(BASE_DIR, "Colas_Mensajes", "telegram_state.txt")
        with open(daemon_state, "w") as f:
            f.write(str(update_id))
    except Exception as e:
        log(f"Error guardando state: {e}")


def send_telegram(token, admin_id, text):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": admin_id, "text": text}, timeout=10)
    except Exception as e:
        log(f"Error enviando Telegram: {e}")


def is_charm_running():
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Antigravity.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "Antigravity.exe" in result.stdout
    except Exception:
        return False


def is_unified_daemon_running():
    """Comprueba si nora_core_supervisor (V3) ya está corriendo."""
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='python.exe' or name='pythonw.exe'",
             "get", "commandline", "/format:csv"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "unified_channel_daemon.py" in result.stdout or "nora_core_supervisor.py" in result.stdout
    except Exception:
        return False


def add_to_queue(message, source="telegram_sentinel"):
    try:
        # En V3, intentamos enviarlo directo al IPC Socket en lugar del JSON
        import requests
        try:
            payload = {"target": "ide", "text": message, "source": source}
            resp = requests.post("http://127.0.0.1:6334/enqueue", json=payload, timeout=2)
            if resp.status_code == 200:
                log("Mensaje inyectado vía IPC Zero-Disk")
                return
        except Exception:
            pass # Si el socket aún no está vivo, caemos al JSON legacy
            
        data = []
        if os.path.exists(QUEUE_PATH):
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        data.append({
            "ts": datetime.now().isoformat(),
            "source": source,
            "message": message,
            "status": "pending"
        })
        with open(QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log(f"Error en add_to_queue: {e}")


def boot_chask_swarm():
    """Arranca el sistema V3 (Docker, N8N, Qdrant, Antigravity, y Daemons)"""
    log("Purgando procesos antiguos antes de arrancar...")
    try:
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "Advanced_Tools", "shutdown_cleanup.py")], 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(3)
    except Exception as e:
        log(f"Error purgando procesos: {e}")

    log("Arrancando Chask Swarm desde start_swarm.bat (V3)...")
    launcher_bat = os.path.join(BASE_DIR, "start_swarm.bat")
    if os.path.isfile(launcher_bat):
        try:
            os.startfile(launcher_bat)
            log(f"Lanzado: start_swarm.bat (V3) via os.startfile")
            return True
        except Exception as e:
            log(f"Error lanzando start_swarm.bat: {e}")

    log("ERROR: No se encontró start_swarm.bat")
    return False


def wait_for_charm():
    elapsed = 0
    while elapsed < STARTUP_WAIT:
        if is_charm_running():
            log(f"Charm detectado tras {elapsed}s")
            return True
        time.sleep(CHECK_INTERVAL)
        elapsed += CHECK_INTERVAL
    log(f"Charm no arrancó en {STARTUP_WAIT}s")
    return False


def main():
    log("=" * 60)
    log("TELEGRAM SENTINEL V2 INICIADO — Centinela permanente 24/7")
    log(f"PID: {os.getpid()}")
    log("=" * 60)

    token, admin_id = get_config()
    if not token:
        log("FATAL: No se pudieron leer credenciales. Saliendo.")
        return

    url_base = f"https://api.telegram.org/bot{token}"
    last_update_id = get_last_update_id()
    log(f"Token OK. Último update_id: {last_update_id}")

    while True:
        try:
            charm_on = is_charm_running()
            daemon_on = is_unified_daemon_running()
            
            # Auto-arranque si el IDE fue abierto manualmente pero los daemons no están
            if charm_on and not daemon_on:
                log("Detectado IDE abierto pero sin daemons. Auto-arrancando Enjambre...")
                send_telegram(token, admin_id, "✅ IDE detectado abierto manualmente. Encendiendo el Enjambre de fondo...")
                boot_chask_swarm()
                time.sleep(5)
                continue

            # Si el sistema ya está corriendo completo, dormir largo
            if charm_on and daemon_on:
                time.sleep(15)
                # Sincronizar state por si el daemon avanzó
                daemon_state = os.path.join(BASE_DIR, "Colas_Mensajes", "telegram_state.txt")
                if os.path.exists(daemon_state):
                    try:
                        with open(daemon_state, "r") as f:
                            daemon_id = int(f.read().strip())
                        if daemon_id > last_update_id:
                            last_update_id = daemon_id
                            save_last_update_id(last_update_id)
                    except Exception:
                        pass
                continue

            # Charm NO está corriendo → Escuchar Telegram
            resp = requests.get(
                f"{url_base}/getUpdates?offset={last_update_id + 1}&timeout={POLL_TIMEOUT}",
                timeout=POLL_TIMEOUT + 5
            ).json()

            for update in resp.get("result", []):
                last_update_id = update["update_id"]
                save_last_update_id(last_update_id)

                if "message" not in update:
                    continue
                    
                user_telegram_id = str(update["message"]["chat"]["id"])
                is_admin = False
                
                # Comprobar si el usuario tiene rol 'admin' en users.json
                try:
                    sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools", "Core_Logic"))
                    from user_manager import identify_user
                    user_obj = identify_user("telegram", user_telegram_id)
                    if user_obj and user_obj.get("role") == "admin":
                        is_admin = True
                except Exception:
                    pass
                
                # Fallback al admin_id original de la config
                if not is_admin and user_telegram_id == str(admin_id):
                    is_admin = True
                    
                if not is_admin:
                    continue

                text = update["message"].get("text", update["message"].get("caption", ""))
                if not text:
                    continue

                log(f"MENSAJE (Charm apagado): {text[:80]}")

                # Interceptar kill switch
                text_lower = text.strip().lower()
                if text_lower in ["/off", "off charm", "🔴 off charm", "🔴", "\U0001f534", "\U0001f534 off charm"]:
                    send_telegram(token, admin_id, "⚠️ Iniciando apagado de emergencia (Kill Switch desde Sentinel)...")
                    try:
                        subprocess.run([sys.executable, os.path.join(BASE_DIR, "Advanced_Tools", "shutdown_cleanup.py"), "--force"], 
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                    except Exception as e:
                        log(f"Error llamando a shutdown_cleanup.py: {e}")
                    send_telegram(token, admin_id, "💀 Sistema apagado (Zombies purgados). Solo el Sentinel sigue en guardia.")
                    continue
                elif text_lower in ["/on", "on charm", "🟢 on charm", "🚀", "/start_charm"]:
                    send_telegram(token, admin_id, "🌱 Encendiendo Chask Swarm desde el Sentinel...")
                    boot_chask_swarm()
                    if wait_for_charm():
                        time.sleep(10)
                        send_telegram(token, admin_id, "✅ Chask Swarm arrancado correctamente.")
                    else:
                        send_telegram(token, admin_id, "⚠️ Sistema arrancado pero Charm tardó.")
                    time.sleep(COOLDOWN_AFTER_BOOT)
                    continue

                # Mensaje normal — guardar y arrancar
                send_telegram(token, admin_id,
                    "🔄 Recibido. Charm estaba apagado.\n"
                    "Arrancando sistema Chask Swarm...\n"
                    "Te avisaré cuando esté listo."
                )

                formatted = f"[TELEGRAM {datetime.now().strftime('%H:%M:%S')}] {text}"
                add_to_queue(formatted, source="telegram_sentinel")

                if boot_chask_swarm():
                    if wait_for_charm():
                        time.sleep(15)
                        send_telegram(token, admin_id,
                            "✅ Chask Swarm arrancado. Nora procesando tu mensaje..."
                        )
                    else:
                        send_telegram(token, admin_id,
                            "⚠️ Sistema arrancado pero Charm tardó.\n"
                            "Tu mensaje está en cola."
                        )
                else:
                    send_telegram(token, admin_id, "❌ Error al arrancar. Mensaje guardado en cola.")

                time.sleep(COOLDOWN_AFTER_BOOT)

        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.ConnectionError:
            log("Sin conexión a internet. Reintentando en 30s...")
            time.sleep(30)
        except Exception as e:
            log(f"ERROR EN BUCLE: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
