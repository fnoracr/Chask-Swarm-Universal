"""
discord_worker.py — Worker Discord independiente para Nora
Ejecutado como subproceso por unified_channel_daemon para aislar asyncio.
"""
import os, sys, io, json, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHANNELS_CONFIG = os.path.join(BASE_DIR, "Configuracion", "channels_config.json")
QUEUE_FILE      = os.path.join(BASE_DIR, "Advanced_Tools", "Colas_Mensajes", "input_queue.json")
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
            f.write(line + "\n")
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

def inject(message):
    try:
        sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools"))
        import chask_stealth_injector as nsi
        ok, reason = nsi.inject_to_charm(message)
        log(f"{'OK' if ok else 'FALLO'}: {reason}")
        return ok
    except Exception as e:
        log(f"Injector error: {e}")
        return False

def deliver(message, source):
    inject(message)
    add_queue(message, source)

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
        if message.author == client.user:
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
            text = f"[DISCORD {ts} - {author}] " + "\n".join(parts)
            log(f"MSG: {text[:80]}")
            deliver(text, f"discord_{author}")

    log(f"Conectando con token {token[:10]}...")
    client.run(token, log_handler=None)

if __name__ == "__main__":
    main()
