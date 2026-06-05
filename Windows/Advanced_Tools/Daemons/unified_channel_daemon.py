"""
unified_channel_daemon.py — Daemon Unificado de Canales [Nombre_IA] v2.0
==================================================================
Canales:
  · HILO 1 — TELEGRAM : Long-polling Telegram Bot API 24/7
  · HILO 2 — WEB      : Polling input_queue.json cada 2s
  · PROCESO — DISCORD : Subproceso independiente (discord.py usa asyncio
                        y puede matar el proceso principal si falla)

Cada hilo tiene su propio bucle de reinicio interno.
El watchdog principal verifica cada 30s que todos los hilos sigan vivos.
"""
import os
import sys
import io
import time
import json
import threading
import subprocess
import traceback
import requests
from datetime import datetime

os.chdir(r"C:\Program Files\Chask_Swarn")

if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR        = r"C:\Program Files\Chask_Swarn"
TOOLS_DIR       = os.path.join(BASE_DIR, "Advanced_Tools")
CONFIG_PATH     = os.path.join(BASE_DIR, "Configuration", "master_credentials.json")
CHANNELS_CONFIG = os.path.join(BASE_DIR, "Configuration", "channels_config.json")
QUEUE_FILE      = os.path.join(TOOLS_DIR, "Message_Queues", "input_queue.json")
STATE_FILE      = os.path.join(BASE_DIR, "Message_Queues", "telegram_state.txt")
MEDIA_DIR       = os.path.join(BASE_DIR, "telegram_media")
LOG_FILE        = os.path.join(TOOLS_DIR, "unified_channel.log")
DISCORD_SCRIPT  = os.path.join(TOOLS_DIR, "Daemons", "discord_worker.py")
SLACK_SCRIPT    = os.path.join(TOOLS_DIR, "Daemons", "slack_worker.py")

# ── Python ejecutable (ruta absoluta para garantizar que se encuentre desde daemons) ──
_py311 = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Python", "Python311", "python.exe")
PYTHONW_EXE = _py311.replace("python.exe", "pythonw.exe") if os.path.isfile(_py311) else (os.path.join(os.path.dirname(sys.executable), "pythonw.exe"))
IDE_EXE = r"C:\Users\fnora\AppData\Local\Programs\Antigravity\Antigravity.exe"

os.makedirs(MEDIA_DIR, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
_log_lock = threading.Lock()

def log(channel: str, msg: str):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{channel}] {msg}"
    try:
        if sys.stdout is not None:
            print(line, flush=True)
    except Exception:
        pass
    with _log_lock:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

# ── Config ────────────────────────────────────────────────────────────────────
def get_config() -> dict:
    cfg = {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f).get("credentials", {}))
    except Exception as e:
        log("CONFIG", f"Error agents_config: {e}")
    try:
        if os.path.exists(CHANNELS_CONFIG):
            with open(CHANNELS_CONFIG, "r", encoding="utf-8") as f:
                ch = json.load(f).get("channels", {})
            dc = ch.get("discord", {})
            if dc.get("enabled") and dc.get("bot_token"):
                cfg["discord_bot"]     = dc["bot_token"]
                cfg["discord_webhook"] = dc.get("webhook_url", "")
                cfg["discord_channel"] = dc.get("channel_id", "")
    except Exception as e:
        log("CONFIG", f"Error channels_config: {e}")
    return cfg

# ── Cola de respaldo ──────────────────────────────────────────────────────────
_queue_lock = threading.Lock()

def add_to_queue(message: str, source: str):
    with _queue_lock:
        try:
            data = []
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data.append({
                "ts":      datetime.now().isoformat(),
                "source":  source,
                "message": message,
                "status":  "pending"
            })
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log("QUEUE", f"Error: {e}")

def deliver(message: str, source: str):
    """Entrega: Solo cola de respaldo + PING silencioso."""
    add_to_queue(message, source=source)
    try:
        sys.__stdout__.write("[WAKEUP_PING] Nuevo mensaje en input_queue.json\n")
        sys.__stdout__.flush()
    except Exception as e:
        log("PING", f"Error enviando WAKEUP_PING: {e}")

# ════════════════════════════════════════════════════════════════════════════
# HILO 1 — TELEGRAM (long-polling, reinicio automático interno)
# ════════════════════════════════════════════════════════════════════════════
def _tg_get_last_id() -> int:
    try:
        if os.path.exists(STATE_FILE):
            return int(open(STATE_FILE).read().strip())
    except Exception:
        pass
    return 0

def _tg_save_last_id(uid: int):
    try:
        with open(STATE_FILE, "w") as f:
            f.write(str(uid))
    except Exception:
        pass

def _tg_send(token: str, chat_id: str, text: str, use_keyboard=True):
    try:
        import requests
        payload = {"chat_id": chat_id, "text": text}
        if use_keyboard:
            payload["reply_markup"] = {
                "keyboard": [[{"text": "\U0001f534 Off [Nombre_IA]"}, {"text": "\U0001f7e2 On [Nombre_IA]"}]],
                "resize_keyboard": True,
                "persistent": True
            }
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
            timeout=10
        )
    except Exception:
        pass

def _kill_swarm():
    audit_log = r"C:\Program Files\Chask_Swarn\System_Logs\swarm_power_audit.log"
    def audit(msg):
        with open(audit_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    try:
        audit("==================================================")
        audit("[INICIO] Apagado completo del enjambre solicitado por Telegram")
        
        lock_file = os.path.join(BASE_DIR, "kill_switch.lock")
        with open(lock_file, "w") as f:
            f.write(datetime.now().isoformat())
        if os.path.exists(lock_file):
            audit("[ÉXITO] Paso 1: kill_switch.lock creado correctamente.")
            
        subprocess.run('powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match \'process_watchdog.py\' } | Stop-Process -Force"', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 2: process_watchdog.py aniquilado.")

        subprocess.run('powershell -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match \'python\' -and $_.CommandLine -match \'Chask_Swarn\' -and $_.CommandLine -notmatch \'telegram_sentinel.py\' -and $_.CommandLine -notmatch \'unified_channel_daemon.py\' }; foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force }"', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 3: Todos los daemons Python secundarios aniquilados (excepto Sentinel y Unified).")

        subprocess.run('powershell -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match \'node.exe\' -and $_.CommandLine -match \'n8n\' }; foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force }"', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 4: Proceso n8n (node.exe) aniquilado.")

        subprocess.run('docker stop qdrant n8n', shell=True, capture_output=True)
        audit("[ÉXITO] Paso 5: Contenedores Qdrant y N8N detenidos.")

        def _close_ide_delayed():
            time.sleep(3)
            subprocess.run('taskkill /IM Antigravity.exe /F', shell=True, capture_output=True)
            audit("[ÉXITO] Paso 6: IDE Antigravity cerrado.")
            audit("[FIN] Proceso de apagado concluido.")
            audit("==================================================")
            # Suicidio final para dejar el control al Sentinel
            os._exit(0)
            
        threading.Thread(target=_close_ide_delayed, daemon=True).start()
    except Exception as e:
        audit(f"[CRITICAL ERROR] Fallo durante _kill_swarm: {e}")

def _start_swarm():
    audit_log = r"C:\Program Files\Chask_Swarn\System_Logs\swarm_power_audit.log"
    def audit(msg):
        with open(audit_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    try:
        audit("==================================================")
        audit("[INICIO] Encendido completo del enjambre solicitado por Telegram")

        lock_file = os.path.join(BASE_DIR, "kill_switch.lock")
        if os.path.exists(lock_file):
            os.remove(lock_file)
            if not os.path.exists(lock_file):
                audit("[ÉXITO] Paso 1: kill_switch.lock eliminado correctamente.")
            else:
                audit("[ERROR] Paso 1: No se pudo eliminar kill_switch.lock.")
        else:
            audit("[INFO] Paso 1: kill_switch.lock no existía.")

        bat_path = os.path.join(BASE_DIR, "start_swarm.bat")
        proc = subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
        if proc.pid:
            audit(f"[ÉXITO] Paso 2: start_swarm.bat lanzado con PID {proc.pid}.")
        else:
            audit("[ERROR] Paso 2: Falló el lanzamiento de start_swarm.bat.")
        
        audit("[FIN] Proceso de encendido delegado a start_swarm.bat.")
        audit("==================================================")
    except Exception as e:
        audit(f"[CRITICAL ERROR] Fallo durante _start_swarm: {e}")

def _tg_process_update(update: dict, token: str, admin_id: str):
    if "message" not in update:
        return None
    msg = update["message"]
    chat_id = str(msg.get("chat", {}).get("id", ""))
    
    parts = []
    ts    = datetime.now().strftime("%H:%M:%S")

    if "text" in msg:
        text_lower = msg["text"].strip().lower()
        if text_lower in ["off charm", "/off", "\U0001f534 off charm", "\U0001f534"]:
            log("TG", f"Detected OFF command from chat_id {chat_id}, admin_id is {admin_id}")
            if chat_id != admin_id: return None
            _tg_send(token, admin_id, "💤 Entendido. Solicitando a [Nombre_IA] que guarde su memoria y desconecte el enjambre...")
            deliver("[TELEGRAM] [Nombre_IA], por favor guarda tu progreso en memory.md, asegúrate de que el estado en Qdrant quede guardado y procede a apagar el sistema por completo ejecutando el script kill_swarm.py.", source="telegram")
            return None
        
        elif text_lower in ["on charm", "/on", "\U0001f7e2 on charm", "\U0001f7e2", "/start_charm"]:
            if chat_id != admin_id: return None
            _tg_send(token, admin_id, "🌱 Encendiendo el Ouroboros (Watchdog)...")
            _start_swarm()
            _tg_send(token, admin_id, "✅ Watchdog activado. El Enjambre se está auto-ensamblando de fondo.")
            return None
            
        parts.append(msg["text"])

    if "photo" in msg:
        try:
            import requests
            r = requests.get(
                f"https://api.telegram.org/bot{token}/getFile?file_id={msg['photo'][-1]['file_id']}",
                timeout=10
            ).json()
            if r.get("ok"):
                fp   = r["result"]["file_path"]
                data = requests.get(f"https://api.telegram.org/file/bot{token}/{fp}", timeout=30).content
                local = os.path.join(MEDIA_DIR, f"{msg['photo'][-1]['file_id']}.jpg")
                with open(local, "wb") as fh:
                    fh.write(data)
                parts.append(f"[IMAGEN ADJUNTA: {local}]")
        except Exception as e:
            parts.append(f"[Foto — error descarga: {e}]")
        if "caption" in msg:
            parts.append(msg["caption"])

    if "voice" in msg:
        try:
            import requests
            r = requests.get(
                f"https://api.telegram.org/bot{token}/getFile?file_id={msg['voice']['file_id']}",
                timeout=10
            ).json()
            if r.get("ok"):
                fp   = r["result"]["file_path"]
                data = requests.get(f"https://api.telegram.org/file/bot{token}/{fp}", timeout=30).content
                local = os.path.join(MEDIA_DIR, f"{msg['voice']['file_id']}.ogg")
                with open(local, "wb") as fh:
                    fh.write(data)
                try:
                    from pydub import AudioSegment
                    import speech_recognition as sr
                    AudioSegment.converter = os.path.join(BASE_DIR, "Binaries", "ffmpeg.exe")
                    wav = local.replace(".ogg", ".wav")
                    AudioSegment.from_ogg(local).export(wav, format="wav")
                    rec  = sr.Recognizer()
                    with sr.AudioFile(wav) as src:
                        audio = rec.record(src)
                    parts.append(f"[VOZ]: {rec.recognize_google(audio, language='es-ES')}")
                except Exception as te:
                    parts.append(f"[Nota de voz — transcripción falló: {te}]")
        except Exception as e:
            parts.append(f"[Voz — error: {e}]")

    if "document" in msg:
        parts.append(f"[DOCUMENTO: {msg['document'].get('file_name', 'archivo')}]")
        if "caption" in msg:
            parts.append(msg["caption"])

    if parts:
        raw_text = "\n".join(parts)
        try:
            sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools", "Core_Logic"))
            from auth_middleware import process_request
            auth_res = process_request("telegram", chat_id, raw_text)
            if not auth_res["authorized"]:
                _tg_send(token, chat_id, auth_res.get("error", "No autorizado."))
                return None
            user_name = auth_res["user"]["username"]
            prompt_extra = auth_res.get("system_prompt_extra", "")
            final_text = auth_res.get("text", raw_text)
            formatted_msg = f"{prompt_extra}\n\n[TELEGRAM {ts}] [USER: {user_name}] {final_text}"
            return formatted_msg.strip()
        except Exception as e:
            log("TG", f"Auth Middleware error: {e}")
            return f"[TELEGRAM {ts}] {raw_text}"

    return None

def telegram_thread():
    """Bucle de Telegram con reinicio automático ante cualquier fallo."""
    while True:   # <-- reinicio externo infinito
        try:
            import requests
            cfg      = get_config()
            token    = cfg.get("telegram_bot", "")
            admin_id = str(cfg.get("telegram_admin", ""))

            if not token or not admin_id:
                log("TG", "Sin credenciales — reintentando en 60s")
                time.sleep(60)
                continue

            log("TG", f"Token: {token[:10]}... | Admin: {admin_id}")

            last_id = _tg_get_last_id()
            if last_id == 0:
                try:
                    resp = requests.get(
                        f"https://api.telegram.org/bot{token}/getUpdates", timeout=10
                    ).json()
                    if resp.get("result"):
                        last_id = resp["result"][-1]["update_id"]
                        _tg_save_last_id(last_id)
                except Exception:
                    pass

            log("TG", f"Escuchando desde update_id > {last_id}")
            
            # Registrar slash commands universales en Telegram
            try:
                requests.post(
                    f"https://api.telegram.org/bot{token}/setMyCommands",
                    json={"commands": [
                        {"command": "on", "description": "Encender Chask Swarm"},
                        {"command": "off", "description": "Apagar Chask Swarm"}
                    ]},
                    timeout=10
                )
            except Exception:
                pass
                
            _tg_send(token, admin_id, "[Nombre_IA] online — Telegram activo. 🛡️ Kill Switch integrado.")

            errors = 0
            while True:
                try:
                    resp = requests.get(
                        f"https://api.telegram.org/bot{token}/getUpdates"
                        f"?offset={last_id + 1}&timeout=30",
                        timeout=35
                    ).json()
                    errors = 0
                    for update in resp.get("result", []):
                        last_id = update["update_id"]
                        _tg_save_last_id(last_id)
                        text = _tg_process_update(update, token, admin_id)
                        if text:
                            log("TG", f"MSG: {text[:80]}")
                            deliver(text, source="telegram")
                except requests.exceptions.Timeout:
                    continue
                except Exception as e:
                    errors += 1
                    log("TG", f"Error #{errors}: {e}")
                    time.sleep(min(5 * errors, 60))
                    if errors > 20:
                        log("TG", "Demasiados errores — reiniciando sesion")
                        break  # sale al bucle externo para reconectar

        except Exception as e:
            log("TG", f"Fallo critico: {e} — reiniciando en 10s")
            time.sleep(10)


# ════════════════════════════════════════════════════════════════════════════
# HILO 2 — WEB (polling input_queue.json)
# ════════════════════════════════════════════════════════════════════════════
def web_thread():
    log("WEB", "Hilo Web activo — vigilando cola input_queue.json (Inyector GUI nativo)")
    while True:
        try:
            pending_msgs = []
            with _queue_lock:
                if os.path.exists(QUEUE_FILE):
                    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except Exception:
                            data = []
                    
                    modified = False
                    for item in data:
                        if item.get("status") == "pending":
                            pending_msgs.append(item)
                            item["status"] = "processed"
                            modified = True
                            
                    if modified:
                        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                            
            # Inyectar físicamente en la GUI
            if pending_msgs:
                try:
                    sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools", "Integrations"))
                    import stealth_uiautomation
                    for msg in pending_msgs:
                        text = msg.get("message", "")
                        src = msg.get("source", "unknown")
                        success, reason = stealth_uiautomation.inject_to_charm(text, src)
                        if success:
                            log("INJECT", f"[{src}] GUI Inyección exitosa: {reason}")
                        else:
                            log("INJECT", f"[{src}] GUI Inyección fallida: {reason}")
                except Exception as e:
                    log("INJECT", f"Fallo al importar/inyectar stealth_uiautomation: {e}")
        except Exception as e:
            log("WEB", f"Error en web_thread: {e}")
        time.sleep(2)


# ════════════════════════════════════════════════════════════════════════════
# PROCESO — DISCORD (subproceso independiente, se autoreinicia)
# ════════════════════════════════════════════════════════════════════════════
def _write_discord_worker():
    """Genera discord_worker.py si no existe o está desactualizado."""
    code = '''"""
discord_worker.py — Worker Discord independiente para [Nombre_IA]
Ejecutado como subproceso por unified_channel_daemon para aislar asyncio.
"""
import os, sys, io, json, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR        = r"C:\\Program Files\\Chask_Swarn"
CHANNELS_CONFIG = os.path.join(BASE_DIR, "Configuration", "channels_config.json")
QUEUE_FILE      = os.path.join(BASE_DIR, "Advanced_Tools", "Message_Queues", "input_queue.json")
LOG_FILE        = os.path.join(BASE_DIR, "Advanced_Tools", "unified_channel.log")

def log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [DISCORD] {msg}"
    try:
        if sys.stdout is not None:
            print(line, flush=True)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\\n")
    except Exception:
        pass

def add_queue(message, source):
    try:
        data = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({"ts": datetime.now().isoformat(), "source": source,
                     "message": message, "status": "pending"})
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Queue error: {e}")

def deliver(message, source):
    # Intentar Universal Injector (IPC Zero-Disk)
    try:
        import requests
        payload = {"target": "ide", "text": message, "source": source}
        resp = requests.post("http://127.0.0.1:6334/enqueue", json=payload, timeout=2)
        if resp.status_code == 200:
            log("[IPC] Mensaje inyectado vía Universal Injector")
            return
    except Exception as e:
        log(f"[IPC] Fallo inyector universal, usando cola legacy: {e}")
        
    add_queue(message, source)
    
    # Intento de ping stdout (puede fallar en pythonw)
    try:
        if sys.__stdout__ is not None:
            sys.__stdout__.write("[WAKEUP_PING] Nuevo mensaje en input_queue.json\\n")
            sys.__stdout__.flush()
    except Exception as e:
        log(f"[PING] Ping error: {e}")

def main():
    with open(CHANNELS_CONFIG, "r", encoding="utf-8") as f:
        ch = json.load(f).get("channels", {})
    dc = ch.get("discord", {})
    token      = dc.get("bot_token", "")
    channel_id = str(dc.get("channel_id", ""))
    if not token:
        log("Sin token Discord — saliendo")
        return

    import discord
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        log(f"Bot conectado como {client.user}")

    @client.event
    async def on_message(message):
        if message.author == client.user or message.author.bot:
            return
        if channel_id and str(message.channel.id) != channel_id:
            return
        ts     = datetime.now().strftime("%H:%M:%S")
        author = message.author.display_name
        parts  = []
        if message.content.strip():
            parts.append(message.content.strip())
        for att in message.attachments:
            parts.append(f"[ADJUNTO: {att.filename}]")
        if parts:
            text = f"[DISCORD {ts} - {author}] " + "\\n".join(parts)
            log(f"MSG: {text[:80]}")
            deliver(text, f"discord_{author}")

    log(f"Conectando con token {token[:10]}...")
    client.run(token, log_handler=None)

if __name__ == "__main__":
    main()
'''
    with open(DISCORD_SCRIPT, "w", encoding="utf-8") as f:
        f.write(code)

def discord_thread():
    """Mantiene el subproceso discord_worker.py vivo indefinidamente."""
    _write_discord_worker()

    cfg = get_config()
    if not cfg.get("discord_bot"):
        log("DISCORD", "Sin token — hilo desactivado")
        return

    log("DISCORD", "Iniciando subproceso discord_worker.py")
    python = sys.executable

    while True:
        try:
            proc = subprocess.Popen(
                [python, DISCORD_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            log("DISCORD", f"Subproceso PID {proc.pid}")
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    log("DISCORD", line)
            proc.wait()
            log("DISCORD", f"Subproceso terminó (código {proc.returncode}) — reiniciando en 10s")
        except Exception as e:
            log("DISCORD", f"Error lanzando subproceso: {e}")
        time.sleep(10)


def _write_slack_worker():
    """Genera slack_worker.py usando Slack Socket Mode (tiempo real, sin webhooks)."""
    code = '''"""
slack_worker.py — Worker Slack via Socket Mode para [Nombre_IA]
Ejecutado como subproceso por unified_channel_daemon para aislar la conexión.
Requiere: pip install slack-sdk
"""
import os, sys, io, json, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR        = r"C:\\Program Files\\Chask_Swarn"
CHANNELS_CONFIG = os.path.join(BASE_DIR, "Configuration", "channels_config.json")
QUEUE_FILE      = os.path.join(BASE_DIR, "Advanced_Tools", "Message_Queues", "input_queue.json")
LOG_FILE        = os.path.join(BASE_DIR, "Advanced_Tools", "unified_channel.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [SLACK] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\\n")
    except Exception:
        pass

def add_to_queue(message, source):
    try:
        data = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({"ts": datetime.now().isoformat(), "source": source,
                     "message": message, "status": "pending"})
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Queue error: {e}")

def main():
    with open(CHANNELS_CONFIG, "r", encoding="utf-8") as f:
        ch = json.load(f).get("channels", {})
    sl = ch.get("slack", {})
    if not sl.get("enabled", False):
        log("Slack desactivado en channels_config.json — saliendo")
        return
    app_token = sl.get("app_token", "")
    bot_token = sl.get("bot_token", "")
    if not app_token or not bot_token:
        log("Sin tokens de Slack — saliendo")
        return

    try:
        from slack_sdk.socket_mode import SocketModeClient
        from slack_sdk.socket_mode.request import SocketModeRequest
        from slack_sdk.socket_mode.response import SocketModeResponse
        from slack_sdk import WebClient
    except ImportError:
        log("slack-sdk no instalado. Ejecuta: pip install slack-sdk")
        return

    web_client = WebClient(token=bot_token)
    client = SocketModeClient(app_token=app_token, web_client=web_client)

    def process_event(client, req):
        if req.type == "events_api":
            client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
            event = req.payload.get("event", {})
            if event.get("type") == "message" and not event.get("bot_id"):
                ts = datetime.now().strftime("%H:%M:%S")
                user = event.get("user", "unknown")
                text = event.get("text", "")
                channel = event.get("channel", "")
                if text.strip():
                    formatted = f"[SLACK {ts}] [USER: {user}] {text}"
                    log(f"MSG: {formatted[:80]}")
                    add_to_queue(formatted, f"slack_{channel}")

    client.socket_mode_request_listeners.append(process_event)
    log(f"Conectado a Slack via Socket Mode con app_token={app_token[:20]}...")
    client.connect()

    # Mantener vivo
    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
'''
    with open(SLACK_SCRIPT, "w", encoding="utf-8") as f:
        f.write(code)


def slack_thread():
    """Mantiene el subproceso slack_worker.py vivo indefinidamente."""
    _write_slack_worker()

    # Verificar si Slack está habilitado antes de lanzar
    try:
        with open(CHANNELS_CONFIG, "r", encoding="utf-8") as f:
            sl = json.load(f).get("channels", {}).get("slack", {})
        if not sl.get("enabled") or not sl.get("app_token"):
            log("SLACK", "Sin token o desactivado — hilo desactivado")
            return
    except Exception:
        log("SLACK", "No se pudo leer channels_config — hilo desactivado")
        return

    log("SLACK", "Iniciando subproceso slack_worker.py")
    python = sys.executable

    while True:
        try:
            proc = subprocess.Popen(
                [python, SLACK_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            log("SLACK", f"Subproceso PID {proc.pid}")
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    log("SLACK", line)
            proc.wait()
            log("SLACK", f"Subproceso terminó (código {proc.returncode}) — reiniciando en 10s")
        except Exception as e:
            log("SLACK", f"Error lanzando subproceso: {e}")
        time.sleep(10)


# ════════════════════════════════════════════════════════════════════════════
# MAIN — Watchdog que reinicia hilos muertos cada 30s
# ════════════════════════════════════════════════════════════════════════════
THREAD_DEFS = [
    ("TELEGRAM", telegram_thread),
    ("DISCORD",  discord_thread),
    ("SLACK",    slack_thread),
]

def main():
    log("MAIN", "=" * 60)
    log("MAIN", "Unified Channel Daemon v2.0 — [Nombre_IA]")
    log("MAIN", "Canales: Telegram + Web + Discord")
    log("MAIN", "=" * 60)

    live_threads = {}
    for name, target in THREAD_DEFS:
        t = threading.Thread(target=target, name=name, daemon=True)
        t.start()
        live_threads[name] = (t, target)
        log("MAIN", f"Hilo {name} iniciado.")

    # Watchdog
    while True:
        time.sleep(30)
        for name, (t, target) in list(live_threads.items()):
            if not t.is_alive():
                log("MAIN", f"Hilo {name} muerto — reiniciando...")
                nt = threading.Thread(target=target, name=name, daemon=True)
                nt.start()
                live_threads[name] = (nt, target)

if __name__ == "__main__":
    main()
