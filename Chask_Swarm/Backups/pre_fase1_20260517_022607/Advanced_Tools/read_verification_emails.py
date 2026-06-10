"""
read_verification_emails.py — Lee emails de verificación de enjambre@chask.fun
"""
import imaplib, email, re, json, os
from email.header import decode_header
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "telegram_config.json")

def get_email_config():
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
    return cfg.get("email_user", ""), cfg.get("email_pass", ""), cfg.get("email_imap", "imap.hostinger.com")

CODES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "verification_codes.json")

def decode_str(s):
    if not s: return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct in ("text/plain", "text/html"):
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
                except: pass
    else:
        try:
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except: pass
    return ""

def extract_code(text):
    # Buscar código de 6 dígitos
    m = re.search(r'\b(\d{6})\b', text)
    if m: return m.group(1)
    return None

def read_latest_codes():
    email_user, email_pass, email_server = get_email_config()
    if not email_user or not email_pass:
        print("[IMAP] Error: Credenciales de email no configuradas en telegram_config.json")
        return {}
    m = imaplib.IMAP4_SSL(email_server, 993)
    m.login(email_user, email_pass)
    m.select("INBOX")
    _, data = m.search(None, "ALL")
    ids = data[0].split()
    
    codes = {}
    print(f"\n[IMAP] {len(ids)} emails en inbox\n")
    
    for uid in ids[-10:]:  # Últimos 10
        _, msg_data = m.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        sender  = decode_str(msg["From"])
        subject = decode_str(msg["Subject"])
        body    = get_body(msg)
        code    = extract_code(body)
        
        print(f"  De: {sender}")
        print(f"  Asunto: {subject}")
        if code:
            print(f"  CODIGO: {code}")
            # Identificar plataforma
            for platform in ["deepseek","groq","gemini","mistral","openrouter","cohere"]:
                if platform in sender.lower() or platform in subject.lower():
                    codes[platform] = code
                    break
            else:
                codes[f"unknown_{uid.decode()}"] = code
        print()
    
    m.logout()
    
    # Guardar códigos encontrados
    os.makedirs(os.path.dirname(CODES_FILE), exist_ok=True)
    with open(CODES_FILE, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "codes": codes}, f, indent=2)
    
    print(f"\n[IMAP] Códigos encontrados: {codes}")
    return codes

if __name__ == "__main__":
    read_latest_codes()
