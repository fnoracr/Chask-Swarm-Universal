"""
email_monitor.py — Monitor de email bidireccional via IMAP + SMTP
=================================================================
Lee emails entrantes, clasifica por LLM, alerta por Telegram.
Puede responder emails automaticamente via SMTP.
Config en: Advanced_Tools/Integrations/email_config.json
"""
import os, sys, json, imaplib, email, time, subprocess, smtplib, io
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(TOOLS_DIR, "email_config.json")
TG_SCRIPT   = os.path.join(BASE_DIR, "charm_telegram.py")
SEEN_FILE   = os.path.join(TOOLS_DIR, "email_seen.json")

sys.path.insert(0, TOOLS_DIR)

DEFAULT_CONFIG = {
    "email": "tu@gmail.com",
    "password": "tu_contrasena_de_aplicacion",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "check_interval_minutes": 15,
    "keywords": ["urgente", "factura", "pago", "reunion"],
    "auto_classify": True,
    "auto_reply": True,
    "active": False,
    "note": "Usa una contrasena de aplicacion de Google si usas Gmail. Si usas tu propio dominio, configura imap y smtp."
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
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


def classify_email(subject: str, body: str) -> dict:
    """Clasifica un email usando LLM."""
    try:
        import llm_router
        prompt = f"""Clasifica este email en UNA categoria:
- URGENTE (requiere accion inmediata)
- IMPORTANTE (requiere accion pronto)
- INFO (informativo, no requiere accion)
- SPAM (promocional, no deseado)

Asunto: {subject}
Cuerpo: {body[:300]}

Responde SOLO con la categoria."""
        result = llm_router.route(prompt, force_free=True)
        cat = result.get("response", "INFO").strip().upper()
        for valid in ["URGENTE", "IMPORTANTE", "INFO", "SPAM"]:
            if valid in cat:
                return {"category": valid}
        return {"category": "INFO"}
    except Exception:
        return {"category": "INFO"}


def reply_email(to: str, subject: str, body: str, in_reply_to: str = None) -> bool:
    """Envia una respuesta via SMTP."""
    config = load_config()
    try:
        msg = MIMEMultipart()
        msg["From"] = config["email"]
        msg["To"] = to
        msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        server = smtplib.SMTP(config.get("smtp_server", "smtp.gmail.com"),
                              config.get("smtp_port", 587))
        server.starttls()
        server.login(config["email"], config["password"])
        server.send_message(msg)
        server.quit()
        
        print(f"[Email] Respuesta enviada a {to}")
        return True
    except Exception as e:
        print(f"[Email] Error SMTP: {e}")
        return False

def generate_and_send_auto_reply(sender: str, subject: str, body: str, msg_id: str):
    """Generates an AI reply with strict privacy guidelines and sends it."""
    import llm_router
    prompt = f"""Escribe una respuesta PROFESIONAL y EDUCADA a este correo electrónico.
REGLAS OBLIGATORIAS:
- Tienes estrictamente prohibido revelar ninguna información personal, confidencial, interna o privada bajo ninguna circunstancia.
- Si el correo pide información sensible, debes negarte amablemente de forma profesional.
- Eres Nora AI, el asistente inteligente oficial del ecosistema Chask Swarm.
- Solo debes devolver el texto de la respuesta, sin aclaraciones ni explicaciones previas.

Asunto original: {subject}
Cuerpo original: {body}"""
    
    print(f"[Email] Generando auto-respuesta para {sender}...")
    # apply_privacy=True ensures the Privacy Shield removes PII before sending it to the LLM
    result = llm_router.route(prompt, apply_privacy=True)
    reply_text = result.get("response", "")
    
    if reply_text and "Error" not in reply_text:
        reply_email(sender, subject, reply_text, msg_id)
        return reply_text
    return None



def check_email():
    config = load_config()
    if not config.get("active"):
        return
    seen = load_seen()
    keywords = [k.lower() for k in config.get("keywords", [])]
    auto_classify = config.get("auto_classify", False)
    
    try:
        mail = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])
        mail.login(config["email"], config["password"])
        mail.select("inbox")
        _, data = mail.search(None, "UNSEEN")
        ids = data[0].split()
        
        for uid in ids[-20:]:
            uid_str = uid.decode()
            if uid_str in seen:
                continue
            _, msg_data = mail.fetch(uid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_str(msg["Subject"])
            sender  = decode_str(msg["From"])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")[:500]
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")[:500]
            
            # Classify
            category = "INFO"
            if auto_classify:
                cls = classify_email(subject, body)
                category = cls["category"]
            
            # Keyword match
            full_text = (subject + " " + body).lower()
            matched = [k for k in keywords if k in full_text]
            
            if matched or category in ("URGENTE", "IMPORTANTE") or not keywords:
                icon = {"URGENTE": "[!!]", "IMPORTANTE": "[!]", "INFO": "[i]", "SPAM": "[~]"}.get(category, "")
                alert = (
                    f"CORREO {icon}\n"
                    f"De: {sender}\n"
                    f"Asunto: {subject}\n"
                    f"Categoria: {category}\n"
                    f"Keywords: {', '.join(matched) if matched else 'ninguna'}\n"
                    f"Vista previa: {body[:200]}..."
                )
                
                # Auto-reply
                if config.get("auto_reply", False) and category != "SPAM":
                    reply_text = generate_and_send_auto_reply(sender, subject, body, msg.get("Message-ID"))
                    if reply_text:
                        alert += f"\n\n[Auto-respuesta generada y enviada por Nora AI]\nRespuesta: {reply_text[:200]}..."
                
                send_telegram(alert)
            
            seen.add(uid_str)
        
        mail.logout()
        save_seen(seen)
        print(f"[Email] {datetime.now().strftime('%H:%M')} - {len(ids)} revisados")
    except Exception as e:
        print(f"[Email] Error: {e}")


def run_daemon():
    config = load_config()
    if not config.get("active"):
        print("[Email] Monitor desactivado. Configura email_config.json.")
        return
    try:
        import schedule
    except ImportError:
        print("[Email] schedule no instalado. pip install schedule")
        return
    interval = config.get("check_interval_minutes", 15)
    print(f"[Email] Monitor activo. Cada {interval} min.")
    schedule.every(interval).minutes.do(check_email)
    check_email()
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_email()
        elif sys.argv[1] == "reply" and len(sys.argv) >= 5:
            # reply <to> <subject> <body>
            reply_email(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
        elif sys.argv[1] == "daemon":
            run_daemon()
        else:
            print("Uso:")
            print("  python email_monitor.py check")
            print("  python email_monitor.py reply <to> <subject> <body>")
            print("  python email_monitor.py daemon")
    else:
        run_daemon()

