"""
email_monitor.py — Monitor de email via IMAP
Vigila la bandeja de entrada y reenvía correos importantes por Telegram.
Config en: Advanced_Tools/email_config.json
"""
import os, sys, json, imaplib, email, time, schedule, subprocess
from email.header import decode_header
from datetime import datetime

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "Advanced_Tools", "email_config.json")
TG_SCRIPT   = os.path.join(BASE_DIR, "antigravity_telegram.py")
SEEN_FILE   = os.path.join(BASE_DIR, "Advanced_Tools", "email_seen.json")

DEFAULT_CONFIG = {
    "email": "tu@gmail.com",
    "password": "tu_contrasena_de_aplicacion",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "check_interval_minutes": 15,
    "keywords": ["urgente", "factura", "pago", "reunión"],
    "active": False,
    "note": "Usa una contrasena de aplicacion de Google, no tu contrasena principal"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        print(f"[Email] Config creada en {CONFIG_FILE}. Configura tus credenciales.")
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)

def decode_str(s):
    if not s: return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)

def send_telegram(msg: str):
    subprocess.run([sys.executable, TG_SCRIPT, "send", msg],
                   capture_output=True, timeout=20)

def check_email():
    config = load_config()
    if not config.get("active"):
        return
    seen = load_seen()
    keywords = [k.lower() for k in config.get("keywords", [])]
    try:
        mail = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])
        mail.login(config["email"], config["password"])
        mail.select("inbox")
        _, data = mail.search(None, "UNSEEN")
        ids = data[0].split()
        for uid in ids[-20:]:  # Últimos 20 no leídos
            uid_str = uid.decode()
            if uid_str in seen:
                continue
            _, msg_data = mail.fetch(uid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_str(msg["Subject"])
            sender  = decode_str(msg["From"])
            # Obtener cuerpo
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")[:300]
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")[:300]

            # Comprobar keywords
            full_text = (subject + " " + body).lower()
            matched = [k for k in keywords if k in full_text]
            if matched or not keywords:
                alert = (
                    f"📧 CORREO NUEVO\n"
                    f"De: {sender}\n"
                    f"Asunto: {subject}\n"
                    f"Keywords: {', '.join(matched)}\n"
                    f"Vista previa: {body[:150]}..."
                )
                send_telegram(alert)
            seen.add(uid_str)
        mail.logout()
        save_seen(seen)
        print(f"[Email] {datetime.now().strftime('%H:%M')} — {len(ids)} no leídos revisados")
    except Exception as e:
        print(f"[Email] Error: {e}")

def run_daemon():
    config = load_config()
    if not config.get("active"):
        print("[Email] Monitor desactivado. Configura email_config.json para activarlo.")
        return
    interval = config.get("check_interval_minutes", 15)
    print(f"[Email] Monitor activo. Revisando cada {interval} minutos.")
    schedule.every(interval).minutes.do(check_email)
    check_email()
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_email()
    else:
        run_daemon()
