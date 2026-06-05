"""
telegram_listener_daemon.py — Daemon de escucha Telegram 24/7
==============================================================
Escucha mensajes de Telegram de Administrador y los inyecta directamente
en el IDE de [Nombre_IA] usando el stealth injector.

Pipeline:
  Telegram API (long-polling) → inyección directa IDE → input_queue (respaldo)

Inicio automático: incluido en chask_launcher.py / process_watchdog
"""
import os
import sys
import time
import json
import io
import threading
import traceback
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "Configuration", "master_credentials.json")
STATE_FILE  = os.path.join(BASE_DIR, "Message_Queues", "telegram_state.txt")
QUEUE_FILE  = os.path.join(BASE_DIR, "Message_Queues", "pending_messages.json")
MEDIA_DIR   = os.path.join(BASE_DIR, "telegram_media")
LOG_FILE    = os.path.join(BASE_DIR, "Advanced_Tools", "telegram_listener.log")

os.makedirs(MEDIA_DIR, exist_ok=True)

POLL_TIMEOUT = 30   # segundos de long-polling
RETRY_SLEEP  = 5    # espera entre errores

# ── Logging ──────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── Config ───────────────────────────────────────────────────────────────────
def get_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        creds = json.load(f)["credentials"]
    return creds["telegram_bot"], str(creds["telegram_admin"])

# ── State (último update_id procesado) ───────────────────────────────────────
def get_last_id() -> int:
    try:
        if os.path.exists(STATE_FILE):
            return int(open(STATE_FILE).read().strip())
    except Exception:
        pass
    return 0

def save_last_id(uid: int):
    with open(STATE_FILE, "w") as f:
        f.write(str(uid))

# ── Cola de respaldo ─────────────────────────────────────────────────────────
def add_to_queue(message: str, source: str = "telegram"):
    try:
        data = []
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({
            "id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_telegram",
            "ts": datetime.now().isoformat(),
            "source": source,
            "text": message,
            "thinking_mid": None,
            "status": "pending"
        })
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"[Queue] Error: {e}")

# ── Inyección en el IDE ───────────────────────────────────────────────────────
def inject_to_ide(message: str) -> bool:
    """Intenta inyectar el mensaje en el IDE de [Nombre_IA]."""
    try:
        sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools"))
        import chask_stealth_injector as nsi
        success, reason = nsi.inject_to_charm(message)
        if success:
            log(f"[IDE] Inyección OK: {reason}")
        else:
            log(f"[IDE] Inyección falló: {reason}")
        return success
    except Exception as e:
        log(f"[IDE] Error importando injector: {e}")
        return False

# ── Enviar respuesta por Telegram ─────────────────────────────────────────────
def send_telegram(token: str, chat_id: str, text: str):
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        log(f"[TG] Error enviando: {e}")

# ── Procesar un update de Telegram ────────────────────────────────────────────
def process_update(update: dict, token: str, admin_id: str) -> str | None:
    """Extrae el texto de un update (texto, foto, voz, documento)."""
    if "message" not in update:
        return None
    msg = update["message"]
    chat_id = str(msg.get("chat", {}).get("id", ""))
    
    # Seguridad: solo aceptar mensajes del admin autorizado
    if chat_id != admin_id:
        log(f"[SEC] Mensaje rechazado de chat_id={chat_id}")
        return None

    parts = []
    ts = datetime.now().strftime("%H:%M:%S")

    # Texto plano
    if "text" in msg:
        parts.append(msg["text"])

    # Foto
    if "photo" in msg:
        photo = msg["photo"][-1]
        try:
            import requests
            r = requests.get(
                f"https://api.telegram.org/bot{token}/getFile?file_id={photo['file_id']}",
                timeout=10
            ).json()
            if r.get("ok"):
                fp = r["result"]["file_path"]
                dl = requests.get(
                    f"https://api.telegram.org/file/bot{token}/{fp}",
                    timeout=20
                ).content
                local = os.path.join(MEDIA_DIR, f"{photo['file_id']}.jpg")
                with open(local, "wb") as f:
                    f.write(dl)
                parts.append(f"[IMAGEN ADJUNTA: {local}]")
        except Exception as e:
            parts.append(f"[Foto recibida — error al descargar: {e}]")
        if "caption" in msg:
            parts.append(msg["caption"])

    # Nota de voz
    if "voice" in msg:
        voice = msg["voice"]
        try:
            import requests
            r = requests.get(
                f"https://api.telegram.org/bot{token}/getFile?file_id={voice['file_id']}",
                timeout=10
            ).json()
            if r.get("ok"):
                fp = r["result"]["file_path"]
                dl = requests.get(
                    f"https://api.telegram.org/file/bot{token}/{fp}",
                    timeout=20
                ).content
                local = os.path.join(MEDIA_DIR, f"{voice['file_id']}.ogg")
                with open(local, "wb") as f:
                    f.write(dl)
                # Transcripción de voz
                try:
                    from pydub import AudioSegment
                    import speech_recognition as sr
                    ffmpeg = os.path.join(BASE_DIR, "Binaries", "ffmpeg.exe")
                    AudioSegment.converter = ffmpeg
                    wav = local.replace(".ogg", ".wav")
                    AudioSegment.from_ogg(local).export(wav, format="wav")
                    rec = sr.Recognizer()
                    with sr.AudioFile(wav) as src:
                        audio_data = rec.record(src)
                    transcription = rec.recognize_google(audio_data, language="es-ES")
                    parts.append(f"[VOZ]: {transcription}")
                except Exception as te:
                    parts.append(f"[Nota de voz recibida — transcripción falló: {te}]")
        except Exception as e:
            parts.append(f"[Voz recibida — error: {e}]")

    # Documento
    if "document" in msg:
        doc = msg["document"]
        parts.append(f"[DOCUMENTO: {doc.get('file_name', 'sin nombre')} — recibido via Telegram]")
        if "caption" in msg:
            parts.append(msg["caption"])

    if not parts:
        return None

    text = "\n".join(parts).strip()
    return f"[TELEGRAM {ts}] {text}"

# ── Bucle principal de long-polling ──────────────────────────────────────────
def main():
    log("=" * 60)
    log("Telegram Listener Daemon arrancando...")
    
    try:
        import requests
    except ImportError:
        log("ERROR: requests no instalado. Abortando.")
        sys.exit(1)

    token, admin_id = get_config()
    log(f"Bot token: {token[:10]}... | Admin: {admin_id}")

    last_id = get_last_id()
    
    # Si no hay estado previo, marcar todos los updates existentes como vistos
    if last_id == 0:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                timeout=10
            ).json()
            if resp.get("result"):
                last_id = resp["result"][-1]["update_id"]
                save_last_id(last_id)
                log(f"Estado inicial: último update_id={last_id}")
        except Exception as e:
            log(f"Error obteniendo estado inicial: {e}")

    log(f"Escuchando desde update_id > {last_id}...")
    send_telegram(token, admin_id, "✅ [Nombre_IA] en línea y escuchando Telegram.")

    consecutive_errors = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            resp = requests.get(
                f"{url}?offset={last_id + 1}&timeout={POLL_TIMEOUT}",
                timeout=POLL_TIMEOUT + 5
            ).json()
            
            consecutive_errors = 0  # Reset en éxito

            for update in resp.get("result", []):
                uid = update["update_id"]
                last_id = uid
                save_last_id(uid)

                text = process_update(update, token, admin_id)
                if not text:
                    continue

                log(f"Mensaje recibido: {text[:100]}")

                # 1. Intentar inyección directa en el IDE
                injected = inject_to_ide(text)
                
                # 2. Siempre escribir en cola como respaldo
                add_to_queue(text, source="telegram")

                if not injected:
                    log("[IDE] No disponible — mensaje en cola para procesamiento posterior")

        except requests.exceptions.Timeout:
            # Long-poll timeout normal — seguir
            continue
        except Exception as e:
            consecutive_errors += 1
            log(f"Error en polling (#{consecutive_errors}): {e}")
            if consecutive_errors > 10:
                log("Demasiados errores consecutivos. Esperando 60s...")
                time.sleep(60)
                consecutive_errors = 0
            else:
                time.sleep(RETRY_SLEEP)

if __name__ == "__main__":
    main()
