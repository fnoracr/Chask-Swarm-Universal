"""
discord_worker.py — Worker Discord independiente para [Nombre_IA]
Ejecutado como subproceso por unified_channel_daemon para aislar asyncio.
"""
import os, sys, io, json, time
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR        = r"C:\Program Files\Chask_Swarn"
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
            sys.__stdout__.write("[WAKEUP_PING] Nuevo mensaje en input_queue.json\n")
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
            text = f"[DISCORD {ts} - {author}] " + "\n".join(parts)
            log(f"MSG: {text[:80]}")
            deliver(text, f"discord_{author}")

    log(f"Conectando con token {token[:10]}...")
    client.run(token, log_handler=None)

if __name__ == "__main__":
    main()
