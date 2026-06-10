"""
unified_daemon.py — Daemon Unificado de Comunicaciones Chask Swarm (V2.1)
=========================================================================
Un SOLO proceso que gestiona Telegram + Discord + Web Queue.
Arquitectura: Cola de inyección centralizada con hilo dedicado COM-safe.

Ejecutar con: python.exe unified_daemon.py
Lanzar con:   start "ChaskDaemon" /MIN python.exe unified_daemon.py
"""
import os
import sys
import json
import time
import asyncio
import ctypes
import ctypes.wintypes
import atexit
import threading
import queue as queue_module
from datetime import datetime

# ── Dependencias opcionales ──
try:
    from filelock import FileLock
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

import requests as http_requests

# Importar motor de inyección Enjambre V7.5
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Advanced_Tools"))
    import chask_stealth_injector as nsi
except ImportError:
    nsi = None

# Importar Dependencias de Discord
try:
    import discord
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False

# Importar Memoria Operativa Enjambre V2.0
try:
    from chask_operational_memory import OperationalMemory
    HAS_CHASK_MEMORY = True
except ImportError:
    HAS_CHASK_MEMORY = False

# ── CONFIGURACIÓN ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "unified_daemon.log")
LOCK_FILE = os.path.join(BASE_DIR, "unified_daemon.lock")
INPUT_QUEUE_FILE = os.path.join(BASE_DIR, "Advanced_Tools", "Colas_Mensajes", "input_queue.json")
QUEUE_LOCK_FILE = INPUT_QUEUE_FILE + ".lock"
PENDING_FILE = os.path.join(BASE_DIR, "Colas_Mensajes", "pending_messages.json")
CHANNELS_CONFIG = os.path.join(BASE_DIR, "Configuracion", "channels_config.json")
AGENTS_CONFIG = os.path.join(BASE_DIR, "agents_config.json")
AUTH_USERS_FILE = os.path.join(BASE_DIR, "Configuracion", "authorized_users.json")
STATE_FILE = os.path.join(BASE_DIR, "Colas_Mensajes", "telegram_daemon_state.txt")

# ── MEMORIA OPERATIVA ──
chask_memory = None
injection_queue = queue_module.Queue()

# ══════════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════════
def log(message):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    print(line)

# ══════════════════════════════════════════════════════════════════
#  MUTEX (una sola instancia)
# ══════════════════════════════════════════════════════════════════
def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, old_pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                log(f"Matando instancia anterior (PID {old_pid})")
                os.system(f"taskkill /PID {old_pid} /F >nul 2>&1")
                time.sleep(1)
        except:
            pass
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    log(f"Lock adquirido (PID {os.getpid()})")

def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

atexit.register(release_lock)

# ══════════════════════════════════════════════════════════════════
#  MASTER INJECTOR (Hilo dedicado con COM inicializado)
# ══════════════════════════════════════════════════════════════════
def master_injector_worker():
    """Bucle que procesa la cola de inyección de forma secuencial y COM-safe."""
    try:
        ctypes.windll.ole32.CoInitialize(None)
    except:
        pass
    log("[MASTER] Inyector Maestro iniciado (COM Init OK).")
    while True:
        try:
            formatted_text = injection_queue.get(timeout=30)
            if formatted_text is None:
                break
            log(f"[MASTER] Procesando: {formatted_text[:50]}...")
            if nsi:
                success, msg = nsi.inject_to_antigravity(formatted_text)
                
                # Registro en memoria evolutiva
                if chask_memory:
                    res_str = "success" if success else "failure"
                    chask_memory.log_operation(
                        description=f"Inyección de mensaje: {formatted_text[:100]}",
                        approach="nsi.inject_to_antigravity (Win32/UIA)",
                        result=res_str,
                        error_msg=msg if not success else "",
                        project="comunicaciones",
                        keywords=["inyeccion", "antigravity", "daemon"]
                    )

                if success:
                    log(f"[MASTER] Éxito: {msg}")
                else:
                    log(f"[MASTER] FALLO: {msg}")
            else:
                log("[MASTER] Motor chask_stealth_injector no disponible")
            injection_queue.task_done()
        except queue_module.Empty:
            pass  # Normal timeout, seguir esperando
        except Exception as e:
            log(f"[MASTER] Error: {e}")
            if chask_memory:
                chask_memory.log_operation(
                    description="Fallo crítico en Master Injector",
                    result="failure",
                    error_msg=str(e),
                    project="daemon",
                    keywords=["crash", "master_injector"]
                )
            time.sleep(1)

# ══════════════════════════════════════════════════════════════════
#  COLA DE MENSAJES (con filelock)
# ══════════════════════════════════════════════════════════════════
def write_to_queue_and_inject(text, source, user_id="admin"):
    """Escribe a input_queue.json Y encola para inyección en IDE."""
    # 1. Encolar para inyección inmediata
    injection_queue.put(text)

    # 2. Persistir en archivo
    lock = FileLock(QUEUE_LOCK_FILE, timeout=5) if HAS_FILELOCK else None
    try:
        if lock:
            lock.acquire()
        file_queue = []
        if os.path.exists(INPUT_QUEUE_FILE):
            with open(INPUT_QUEUE_FILE, "r", encoding="utf-8-sig") as f:
                file_queue = json.load(f)
        file_queue.append({
            "ts": datetime.now().isoformat(),
            "source": source,
            "message": text,
            "status": "injected",
            "user_id": str(user_id)
        })
        with open(INPUT_QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(file_queue, f, indent=2, ensure_ascii=False)
        log(f"[{source.upper()}] Encolado: {text[:60]}...")
    except Exception as e:
        log(f"[QUEUE] Error: {e}")
    finally:
        if lock:
            try:
                lock.release()
            except:
                pass

# ══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════
def get_telegram_config():
    with open(AGENTS_CONFIG, "r") as f:
        creds = json.load(f)["credentials"]
    return creds["telegram_bot"], creds["telegram_admin"]

def get_discord_token():
    try:
        with open(CHANNELS_CONFIG, "r") as f:
            return json.load(f)["channels"]["discord"]["bot_token"]
    except:
        return None

def is_authorized(platform, user_id):
    try:
        with open(AUTH_USERS_FILE, "r") as f:
            users = json.load(f)["authorized_users"]
        for u in users:
            if u["platform"] == platform and str(u["user_id"]) == str(user_id):
                return u["role"] in ["Master", "Admin"]
    except:
        pass
    return False

# ══════════════════════════════════════════════════════════════════
#  TELEGRAM (polling asíncrono)
# ══════════════════════════════════════════════════════════════════
def get_last_update_id():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return 0

def save_last_update_id(update_id):
    with open(STATE_FILE, 'w') as f:
        f.write(str(update_id))

async def telegram_loop():
    """Bucle de Telegram con long polling."""
    token, admin_id = get_telegram_config()
    url = f"https://api.telegram.org/bot{token}"
    last_update_id = get_last_update_id()
    log("[TELEGRAM] Iniciado")

    # Sincronizar offset si es la primera vez
    if last_update_id == 0:
        try:
            resp = http_requests.get(f"{url}/getUpdates", timeout=5).json()
            if resp.get("result"):
                last_update_id = resp["result"][-1]["update_id"]
                save_last_update_id(last_update_id)
        except:
            pass

    while True:
        try:
            resp = http_requests.get(
                f"{url}/getUpdates?offset={last_update_id + 1}&timeout=20",
                timeout=25
            ).json()

            for update in resp.get("result", []):
                last_update_id = update["update_id"]
                save_last_update_id(last_update_id)
                msg = update.get("message")
                if msg and str(msg["chat"]["id"]) == admin_id:
                    text = msg.get("text", "")
                    if text:
                        log(f"[TELEGRAM] MSG: {text[:80]}")
                        formatted = f"[TELEGRAM {datetime.now().strftime('%H:%M:%S')}] {text}"
                        write_to_queue_and_inject(formatted, "telegram", admin_id)

                        # Confirmar lectura
                        try:
                            http_requests.post(f"{url}/sendMessage", json={
                                "chat_id": admin_id,
                                "text": f"✅ Recibido y entregado a Enjambre."
                            }, timeout=5)
                        except:
                            pass

        except http_requests.exceptions.ReadTimeout:
            pass
        except Exception as e:
            log(f"[TELEGRAM] Error: {e}")
            await asyncio.sleep(5)

        await asyncio.sleep(0.1)

# ══════════════════════════════════════════════════════════════════
#  DISCORD (discord.py async nativo)
# ══════════════════════════════════════════════════════════════════
class NoraDiscordBot(discord.Client):
    async def on_ready(self):
        log(f"[DISCORD] Conectado como {self.user}")
        log(f"[DISCORD] Guilds: {[g.name for g in self.guilds]}")

    async def on_message(self, message):
        # Filtros de seguridad
        if message.author == self.user:
            return
        if message.author.bot or (hasattr(message, 'webhook_id') and message.webhook_id):
            return
        if message.content.startswith("[DISCORD"):
            return
        if not is_authorized("discord", message.author.id):
            log(f"[DISCORD] No autorizado: {message.author.id} ({message.author.name})")
            return

        text = message.content
        if not text:
            return

        log(f"[DISCORD] MSG de {message.author.name}: {text[:80]}")

        # Reacción de confirmación
        try:
            await message.add_reaction("✅")
        except:
            pass

        # Encolar para inyección (NO ejecutar en este hilo)
        formatted = f"[DISCORD {datetime.now().strftime('%H:%M:%S')}] {text}"
        write_to_queue_and_inject(formatted, "discord", str(message.author.id))

    async def on_error(self, event, *args, **kwargs):
        import traceback
        log(f"[DISCORD] Error en evento '{event}': {traceback.format_exc()}")

# ══════════════════════════════════════════════════════════════════
#  WEB QUEUE WATCHER
# ══════════════════════════════════════════════════════════════════
async def web_queue_watcher():
    """Vigila input_queue.json para mensajes de fuentes externas."""
    log("[WATCHER] Queue Watcher iniciado")
    INLINE_SOURCES = {"telegram", "discord"}
    while True:
        try:
            if os.path.exists(INPUT_QUEUE_FILE):
                lock = FileLock(QUEUE_LOCK_FILE, timeout=3) if HAS_FILELOCK else None
                try:
                    if lock:
                        lock.acquire()
                    with open(INPUT_QUEUE_FILE, "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                    modified = False
                    for msg in data:
                        src = msg.get("source", "")
                        if src not in INLINE_SOURCES and msg.get("status") == "pending":
                            text = msg.get("message", "")
                            if text:
                                log(f"[WATCHER] Mensaje de '{src}': {text[:60]}")
                                if text.startswith("["):
                                    formatted = text
                                else:
                                    formatted = f"[{src.upper()} {datetime.now().strftime('%H:%M:%S')}] {text}"
                                injection_queue.put(formatted)
                                msg["status"] = "injected"
                                modified = True
                    if modified:
                        with open(INPUT_QUEUE_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                finally:
                    if lock:
                        try:
                            lock.release()
                        except:
                            pass
        except Exception as e:
            log(f"[WEB] Error: {e}")
        await asyncio.sleep(3)

# ══════════════════════════════════════════════════════════════════
#  TELEGRAM LOOP (hilo dedicado — usa requests síncronas)
# ══════════════════════════════════════════════════════════════════
def telegram_worker():
    """Telegram polling en hilo dedicado (requests son bloqueantes)."""
    token, admin_id = get_telegram_config()
    url = f"https://api.telegram.org/bot{token}"
    last_update_id = get_last_update_id()
    log("[TELEGRAM] Iniciado (hilo dedicado)")

    if last_update_id == 0:
        try:
            resp = http_requests.get(f"{url}/getUpdates", timeout=5).json()
            if resp.get("result"):
                last_update_id = resp["result"][-1]["update_id"]
                save_last_update_id(last_update_id)
        except:
            pass

    while True:
        try:
            resp = http_requests.get(
                f"{url}/getUpdates?offset={last_update_id + 1}&timeout=20",
                timeout=25
            ).json()

            for update in resp.get("result", []):
                last_update_id = update["update_id"]
                save_last_update_id(last_update_id)
                msg = update.get("message")
                if msg and str(msg["chat"]["id"]) == admin_id:
                    text = msg.get("text", "")
                    if text:
                        log(f"[TELEGRAM] MSG: {text[:80]}")
                        formatted = f"[TELEGRAM {datetime.now().strftime('%H:%M:%S')}] {text}"
                        write_to_queue_and_inject(formatted, "telegram", admin_id)

                        try:
                            http_requests.post(f"{url}/sendMessage", json={
                                "chat_id": admin_id,
                                "text": "✅ Recibido y entregado a Enjambre."
                            }, timeout=5)
                        except:
                            pass

        except http_requests.exceptions.ReadTimeout:
            pass
        except Exception as e:
            log(f"[TELEGRAM] Error: {e}")
            time.sleep(5)

        time.sleep(0.1)

# ══════════════════════════════════════════════════════════════════
#  MAIN — Orquestador
# ══════════════════════════════════════════════════════════════════
async def main():
    log("=" * 60)
    log("UNIFIED DAEMON V2.1 INICIADO")
    log(f"PID: {os.getpid()}")
    log("=" * 60)

    acquire_lock()

    # Inicializar Memoria Operativa
    global chask_memory
    if HAS_CHASK_MEMORY:
        try:
            chask_memory = OperationalMemory()
            log("[MAIN] Memoria Operativa V2.0: CONECTADA")
            # Snapshot inicial del sistema
            chask_memory.snapshot_all(note="Daemon Startup Auto-snapshot")
        except Exception as e:
            log(f"[MAIN] Error inicializando memoria: {e}")
    else:
        log("[MAIN] Memoria Operativa V2.0: NO DISPONIBLE (Falta chask_operational_memory.py)")

    # Hilo 1: Inyector Maestro (COM-safe)
    threading.Thread(target=master_injector_worker, daemon=True).start()

    # Hilo 2: Telegram polling (requests síncronas — necesita su propio hilo)
    threading.Thread(target=telegram_worker, daemon=True).start()
    log("[MAIN] Telegram polling: ACTIVO (hilo dedicado)")

    # Asyncio tasks (comparten el event loop principal con Discord)
    tasks = []

    # Web Queue Watcher
    tasks.append(asyncio.create_task(web_queue_watcher()))
    log("[MAIN] Web Queue Watcher: ACTIVO")

    # Discord (se queda con el event loop principal)
    discord_token = get_discord_token()
    if discord_token and HAS_DISCORD:
        intents = discord.Intents.default()
        intents.message_content = True
        bot = NoraDiscordBot(intents=intents)

        async def run_discord():
            try:
                await bot.start(discord_token)
            except Exception as e:
                log(f"[DISCORD] Error fatal: {e}")
                import traceback
                log(traceback.format_exc())

        tasks.append(asyncio.create_task(run_discord()))
        log("[MAIN] Discord bot: ACTIVO")
    else:
        log("[MAIN] Discord bot: DESACTIVADO (sin token o sin discord.py)")

    log("[MAIN] Todos los servicios iniciados. Esperando mensajes...")

    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Daemon detenido por el usuario (Ctrl+C)")
    except Exception as e:
        log(f"ERROR FATAL: {e}")
        import traceback
        log(traceback.format_exc())
        raise
