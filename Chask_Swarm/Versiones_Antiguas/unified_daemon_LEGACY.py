"""
unified_daemon.py — Daemon Unificado de Comunicaciones Chask Swarm
===================================================================
Un SOLO proceso que gestiona Telegram + Discord + Web Queue.
Reemplaza: telegram_daemon.py, discord_daemon.py, inject_to_antigravity.py

Ejecutar con: python.exe unified_daemon.py  (NO pythonw)
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
from datetime import datetime

# ── Dependencias opcionales ──
try:
    import pyautogui
    import pyperclip
    HAS_UI = True
except ImportError:
    HAS_UI = False

try:
    import discord
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False

try:
    from filelock import FileLock
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

import requests as http_requests

# ── CONFIGURACIÓN ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "unified_daemon.log")
LOCK_FILE = os.path.join(BASE_DIR, "unified_daemon.lock")
INPUT_QUEUE_FILE = os.path.join(BASE_DIR, "Advanced_Tools", "input_queue.json")
QUEUE_LOCK_FILE = INPUT_QUEUE_FILE + ".lock"
PENDING_FILE = os.path.join(BASE_DIR, "pending_messages.json")
CHANNELS_CONFIG = os.path.join(BASE_DIR, "channels_config.json")
AGENTS_CONFIG = os.path.join(BASE_DIR, "agents_config.json")
AUTH_USERS_FILE = os.path.join(BASE_DIR, "authorized_users.json")
STATE_FILE = os.path.join(BASE_DIR, "telegram_daemon_state.txt")

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
#  COLA DE MENSAJES (con filelock)
# ══════════════════════════════════════════════════════════════════
def write_to_queue(text, source, user_id="admin"):
    """Escribe un mensaje a input_queue.json con file locking."""
    lock = FileLock(QUEUE_LOCK_FILE, timeout=5) if HAS_FILELOCK else None
    try:
        if lock:
            lock.acquire()
        # input_queue.json
        queue = []
        if os.path.exists(INPUT_QUEUE_FILE):
            with open(INPUT_QUEUE_FILE, "r", encoding="utf-8-sig") as f:
                queue = json.load(f)
        queue.append({
            "ts": datetime.now().isoformat(),
            "source": source,
            "message": text,
            "status": "pending",
            "user_id": str(user_id)
        })
        with open(INPUT_QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)

        # pending_messages.json (historial para el dashboard)
        p_data = []
        if os.path.exists(PENDING_FILE):
            try:
                with open(PENDING_FILE, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
            except:
                pass
        p_data.append({
            "id": f"{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "ts": datetime.now().isoformat(),
            "source": source,
            "text": text,
            "status": "pending",
            "user_id": str(user_id)
        })
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(p_data, f, indent=2, ensure_ascii=False)

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
#  INYECCIÓN EN IDE (pyautogui — requiere python.exe, NO pythonw)
# ══════════════════════════════════════════════════════════════════
def _find_antigravity_hwnd():
    """Busca la ventana de Antigravity por título."""
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    found = [None]
    def callback(hwnd, lParam):
        length = GetWindowTextLength(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            if "Antigravity" in buff.value or "antigravity" in buff.value:
                found[0] = hwnd
                return False
        return True
    EnumWindows(EnumWindowsProc(callback), 0)
    return found[0]

def inject_to_ide(text):
    """Inyecta un mensaje en el IDE de Antigravity.
    Minimiza la ventana al tamaño mínimo, inyecta y la envía detrás."""
    if not HAS_UI:
        log("[INJECT] pyautogui/pyperclip no disponible")
        return False
    try:
        hwnd = _find_antigravity_hwnd()
        if not hwnd:
            log("[INJECT] Ventana Antigravity no encontrada")
            return False

        prev_hwnd = ctypes.windll.user32.GetForegroundWindow()

        # Guardar posición/tamaño original de Antigravity
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        orig_x, orig_y = rect.left, rect.top
        orig_w, orig_h = rect.right - rect.left, rect.bottom - rect.top
        was_maximized = ctypes.windll.user32.IsZoomed(hwnd)
        was_minimized = ctypes.windll.user32.IsIconic(hwnd)

        # Des-minimizar si está minimizada
        if was_minimized:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            time.sleep(0.3)

        # Des-maximizar si está maximizada
        if was_maximized:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            time.sleep(0.3)

        # Encoger al tamaño mínimo en esquina inferior derecha
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        ctypes.windll.user32.MoveWindow(hwnd, sw - 410, sh - 250, 400, 200, True)
        time.sleep(0.3)

        # Obtener foco (3 reintentos)
        success = False
        for i in range(3):
            pyautogui.press('alt')
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            if ctypes.windll.user32.GetForegroundWindow() == hwnd:
                success = True
                break
            log(f"[INJECT] Reintento de foco {i+1}/3...")
            time.sleep(0.5)

        if not success:
            log("[INJECT] ABORTADA: No se pudo obtener el foco tras 3 reintentos")
            return False

        # Estabilizar
        time.sleep(1.0)

        # Asegurar que el panel de chat está abierto:
        # Escape cierra el panel si estuviera abierto (reset estado)
        # Ctrl+L siempre lo abre desde estado cerrado
        pyautogui.press('escape')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(1.0)

        # Pegar y enviar
        pyperclip.copy(text)
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(1.0)

        # Restaurar tamaño/posición original
        if was_maximized:
            ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
        else:
            ctypes.windll.user32.MoveWindow(hwnd, orig_x, orig_y, orig_w, orig_h, True)

        # Enviar Antigravity detrás de todas las ventanas
        ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0,
            0x0001 | 0x0002 | 0x0010)  # HWND_BOTTOM, SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE
        time.sleep(0.2)

        # Devolver foco al usuario
        if prev_hwnd and prev_hwnd != hwnd:
            try:
                ctypes.windll.user32.SetForegroundWindow(prev_hwnd)
            except:
                pass

        log("[INJECT] Exitosa")
        return True
    except Exception as e:
        log(f"[INJECT] Error: {e}")
        return False

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
#  TELEGRAM (polling en un asyncio Task)
# ══════════════════════════════════════════════════════════════════
async def telegram_loop():
    """Bucle de Telegram con long polling."""
    token, admin_id = get_telegram_config()
    url = f"https://api.telegram.org/bot{token}"

    last_update_id = 0
    if os.path.exists(STATE_FILE):
        try:
            last_update_id = int(open(STATE_FILE).read().strip())
        except:
            pass

    log("[TELEGRAM] Iniciado")

    while True:
        try:
            resp = http_requests.get(
                f"{url}/getUpdates?offset={last_update_id + 1}&timeout=30",
                timeout=35
            ).json()

            for update in resp.get("result", []):
                last_update_id = update["update_id"]
                with open(STATE_FILE, "w") as f:
                    f.write(str(last_update_id))

                # ── Callback queries (HITL) ──
                if "callback_query" in update:
                    cb = update["callback_query"]
                    if str(cb.get("from", {}).get("id", "")) != admin_id:
                        continue
                    cb_data = cb.get("data", "")
                    cb_id = cb.get("id", "")
                    if ":" in cb_data:
                        approval_id, action = cb_data.rsplit(":", 1)
                        approval_path = os.path.join(BASE_DIR, "approvals", f"{approval_id}.json")
                        if os.path.exists(approval_path):
                            try:
                                with open(approval_path, "r", encoding="utf-8") as af:
                                    astate = json.load(af)
                                astate["response_time"] = time.time() - astate.get("created_at", 0)
                                astate["status"] = {"approve": "approved", "deny": "denied", "modify": "modified"}.get(action, action)
                                with open(approval_path, "w", encoding="utf-8") as af:
                                    json.dump(astate, af, ensure_ascii=False, indent=2)
                                log(f"[HITL] {approval_id} -> {action}")
                                status_map = {"approve": "✅ Aprobado", "deny": "❌ Denegado", "modify": "📝 Modificar"}
                                http_requests.post(f"{url}/answerCallbackQuery", json={
                                    "callback_query_id": cb_id, "text": status_map.get(action, action)
                                }, timeout=5)
                                msg_id = astate.get("message_id")
                                if msg_id:
                                    icon = {"approve": "✅", "deny": "❌", "modify": "📝"}.get(action, "❓")
                                    http_requests.post(f"{url}/editMessageText", json={
                                        "chat_id": admin_id, "message_id": msg_id,
                                        "text": f"{icon} **{action.upper()}**\n🕐 {astate.get('response_time', 0):.1f}s",
                                        "parse_mode": "Markdown"
                                    }, timeout=5)
                            except Exception as e:
                                log(f"[HITL] Error: {e}")
                    continue

                # ── Mensajes normales ──
                if "message" not in update:
                    continue
                if str(update["message"]["chat"]["id"]) != admin_id:
                    continue

                text = update["message"].get("text", update["message"].get("caption", ""))
                if not text:
                    continue

                log(f"[TELEGRAM] MSG: {text[:80]}")

                # Confirmación de procesamiento
                try:
                    http_requests.post(f"{url}/sendChatAction", json={"chat_id": admin_id, "action": "typing"}, timeout=5)
                    think_resp = http_requests.post(f"{url}/sendMessage", json={
                        "chat_id": admin_id, "text": "⏳ Recibido. Inyectando en Antigravity..."
                    }, timeout=5).json()
                    thinking_mid = think_resp.get("result", {}).get("message_id")
                except:
                    thinking_mid = None

                # Escribir a cola + inyectar
                formatted = f"[TELEGRAM {datetime.now().strftime('%H:%M:%S')}] {text}"
                write_to_queue(formatted, "telegram", admin_id)
                injected = inject_to_ide(formatted)

                # Confirmar resultado
                try:
                    if thinking_mid:
                        status = "✅ Inyectado en Antigravity" if injected else "📥 En cola (IDE sin foco)"
                        http_requests.post(f"{url}/editMessageText", json={
                            "chat_id": admin_id, "message_id": thinking_mid, "text": status
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

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.author.bot or message.webhook_id:
            return
        if message.content.startswith("[DISCORD"):
            return
        if not is_authorized("discord", message.author.id):
            log(f"[DISCORD] No autorizado: {message.author.id} ({message.author.name})")
            return

        text = message.content
        if not text:
            return

        log(f"[DISCORD] MSG de {message.author.id}: {text[:80]}")

        # Reacción de confirmación
        try:
            await message.add_reaction("✅")
        except:
            pass

        # Escribir a cola + inyectar (en thread para no bloquear el bot)
        formatted = f"[DISCORD {datetime.now().strftime('%H:%M:%S')}] {text}"
        write_to_queue(formatted, "discord", str(message.author.id))
        threading.Thread(target=inject_to_ide, args=(formatted,), daemon=True).start()

# ══════════════════════════════════════════════════════════════════
#  WEB QUEUE WATCHER
# ══════════════════════════════════════════════════════════════════
async def web_queue_watcher():
    """Vigila input_queue.json para mensajes pendientes (web, watchdog, etc.)."""
    log("[WATCHER] Queue Watcher iniciado")
    # Sources handled inline by their own loops (don't re-inject)
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
                                # No re-formatear si ya tiene prefijo
                                if text.startswith("["):
                                    formatted = text
                                else:
                                    formatted = f"[{src.upper()} {datetime.now().strftime('%H:%M:%S')}] {text}"
                                inject_to_ide(formatted)
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
#  MAIN — Orquestador async
# ══════════════════════════════════════════════════════════════════
async def main():
    log("=" * 60)
    log("UNIFIED DAEMON INICIADO")
    log(f"PID: {os.getpid()}")
    log("=" * 60)

    acquire_lock()

    tasks = []

    # 1. Telegram (siempre)
    tasks.append(asyncio.create_task(telegram_loop()))
    log("[MAIN] Telegram polling: ACTIVO")

    # 2. Web Queue Watcher (siempre)
    tasks.append(asyncio.create_task(web_queue_watcher()))
    log("[MAIN] Web Queue Watcher: ACTIVO")

    # 3. Discord (si hay token)
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

        tasks.append(asyncio.create_task(run_discord()))
        log("[MAIN] Discord bot: ACTIVO")
    else:
        log("[MAIN] Discord bot: DESACTIVADO (sin token o sin discord.py)")

    log("[MAIN] Todos los servicios iniciados. Esperando mensajes...")

    # Mantener vivo
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Daemon detenido por el usuario (Ctrl+C)")
    except Exception as e:
        log(f"ERROR FATAL: {e}")
        raise
