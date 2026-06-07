"""
Skill: email_charm — Acceso IMAP a nora@charm.fun
Permite leer emails, buscar códigos de verificación y enviar notificaciones.

Uso:
  "lee el email de enjambre"
  "hay algún código de verificación en el email?"
  "últimos emails de enjambre"
"""
import imaplib
import email
import re
import json
import os
from email.header import decode_header
from datetime import datetime

NAME        = "Email Enjambre IMAP"
DESCRIPTION = "Lee emails de nora@charm.fun via IMAP. Encuentra códigos de verificación y muestra los últimos correos recibidos."
KEYWORDS    = [
    "email", "correo", "mail", "bandeja", "inbox",
    "código verificación", "verification code", "código email",
    "lee el mail", "revisa el correo", "mensajes enjambre",
    "deepseek", "groq", "mistral", "openrouter", "cohere"
]

# ── Configuración IMAP ───────────────────────────────────────────────────
IMAP_HOST = "imap.hostinger.com"
IMAP_PORT = 993
EMAIL_ADDR = "nora@charm.fun"
EMAIL_PASS = "N0r4Z0e?*12"


def _decode_str(s):
    if not s:
        return ""
    parts = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct in ("text/plain", "text/html"):
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception:
            pass
    return ""


def _connect():
    m = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    m.login(EMAIL_ADDR, EMAIL_PASS)
    m.select("INBOX")
    return m


def get_latest_emails(n: int = 5) -> list[dict]:
    """Devuelve los últimos N emails como lista de dicts."""
    m = _connect()
    _, data = m.search(None, "ALL")
    ids = data[0].split()
    results = []
    for uid in ids[-n:]:
        _, msg_data = m.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        body = _get_body(msg)
        code = re.search(r'\b(\d{6})\b', body)
        results.append({
            "uid":     uid.decode(),
            "from":    _decode_str(msg["From"]),
            "subject": _decode_str(msg["Subject"]),
            "date":    msg["Date"],
            "code":    code.group(1) if code else None,
            "body_preview": body[:300].strip()
        })
    m.logout()
    return results


def find_verification_code(sender_keyword: str = "") -> str | None:
    """Busca el código de verificación más reciente, opcionalmente filtrando por remitente."""
    emails = get_latest_emails(10)
    for e in reversed(emails):
        if sender_keyword and sender_keyword.lower() not in e["from"].lower():
            continue
        if e["code"]:
            return e["code"]
    return None


def run(prompt: str) -> str:
    prompt_lower = prompt.lower()

    # Buscar código específico de una plataforma
    platforms = {
        "deepseek": "deepseek",
        "groq":     "groq",
        "mistral":  "mistral",
        "openrouter": "openrouter",
        "cohere":   "cohere",
        "linkedin": "linkedin",
    }
    for platform, keyword in platforms.items():
        if platform in prompt_lower:
            code = find_verification_code(keyword)
            if code:
                return f"🔑 Código de verificación de {platform.capitalize()}: **{code}**"
            else:
                # Mostrar todos los emails por si el remitente varía
                emails = get_latest_emails(5)
                lines = [f"No encontré código de {platform}. Últimos 5 emails:"]
                for e in reversed(emails):
                    lines.append(f"  De: {e['from']}")
                    lines.append(f"  Asunto: {e['subject']}")
                    lines.append(f"  Código: {e['code'] or 'ninguno'}")
                    lines.append("")
                return "\n".join(lines)

    # Mostrar últimos emails
    if any(w in prompt_lower for w in ["últimos", "últimos", "recientes", "lee", "revisa", "muestra", "latest", "show"]):
        emails = get_latest_emails(5)
        lines = [f"📧 Últimos {len(emails)} emails de {EMAIL_ADDR}:\n"]
        for e in reversed(emails):
            lines.append(f"  📌 De: {e['from']}")
            lines.append(f"     Asunto: {e['subject']}")
            lines.append(f"     Fecha: {e['date']}")
            if e["code"]:
                lines.append(f"     🔑 CÓDIGO: {e['code']}")
            lines.append(f"     Vista previa: {e['body_preview'][:100]}...")
            lines.append("")
        return "\n".join(lines)

    # Buscar cualquier código de verificación reciente
    emails = get_latest_emails(5)
    codes_found = [(e["from"], e["code"]) for e in emails if e["code"]]
    if codes_found:
        lines = ["🔑 Códigos de verificación encontrados:"]
        for sender, code in reversed(codes_found):
            lines.append(f"  {code}  ←  {sender}")
        return "\n".join(lines)

    return f"📧 No hay códigos de verificación recientes en {EMAIL_ADDR}."


if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "últimos emails"
    print(run(prompt))
