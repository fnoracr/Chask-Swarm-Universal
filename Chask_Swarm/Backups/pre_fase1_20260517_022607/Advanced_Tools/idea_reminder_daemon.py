import os
import time
import json
import subprocess
from datetime import datetime

IDEAS_FILE = r"C:\Program Files\Chask_Swarm\pending_ideas.md"
TELEGRAM_SCRIPT = r"C:\Program Files\Chask_Swarm\antigravity_telegram.py"
STATE_FILE = r"C:\Program Files\Chask_Swarm\Advanced_Tools\reminder_state.json"

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def already_sent_today():
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            return state.get("last_reminder_date") == get_today()
    except:
        return False

def update_state():
    with open(STATE_FILE, "w") as f:
        json.dump({"last_reminder_date": get_today()}, f)

def send_reminder():
    if not os.path.exists(IDEAS_FILE):
        return
    
    with open(IDEAS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Message header
    header = "🔔 **RECORDATORIO DIARIO: Visión 10.000M€ (Chask Swarm)**\n"
    header += "⚠️ *Incluye análisis crítico y objeciones de seguridad.*\n\n"
    message = header + content
    
    # Send via Telegram script
    try:
        subprocess.run(["python", TELEGRAM_SCRIPT, "send", message], check=True)
        update_state()
    except Exception as e:
        print(f"Error sending reminder: {e}")

if __name__ == "__main__":
    # Wait 5 minutes (300 seconds)
    time.sleep(300)
    
    # Send if not already sent today
    if not already_sent_today():
        send_reminder()
