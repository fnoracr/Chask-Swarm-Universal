import sys
import time
import json
import os
from datetime import datetime

try:
    from filelock import FileLock
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_QUEUE_FILE = os.path.join(BASE_DIR, "Advanced_Tools", "Colas_Mensajes", "input_queue.json")
QUEUE_LOCK_FILE = INPUT_QUEUE_FILE + ".lock"
BOT_SCRIPT = os.path.join(BASE_DIR, "antigravity_telegram.py")

def load_schedule():
    schedule_path = os.path.join(os.path.dirname(__file__), "schedule_template.json")
    if not os.path.exists(schedule_path):
        return []
    with open(schedule_path, "r", encoding="utf-8") as f:
        return json.load(f).get("tasks", [])

def add_to_queue(message, source="scheduled_task"):
    """Escribe directamente a input_queue.json (sin depender de telegram_daemon)."""
    lock = FileLock(QUEUE_LOCK_FILE, timeout=5) if HAS_FILELOCK else None
    try:
        if lock:
            lock.acquire()
        queue = []
        if os.path.exists(INPUT_QUEUE_FILE):
            with open(INPUT_QUEUE_FILE, "r", encoding="utf-8-sig") as f:
                queue = json.load(f)
        queue.append({
            "ts": datetime.now().isoformat(),
            "source": source,
            "message": message,
            "status": "pending"
        })
        with open(INPUT_QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WAKEUP] Error escribiendo cola: {e}")
    finally:
        if lock:
            try:
                lock.release()
            except:
                pass

def trigger_ai(task_prompt):
    """
    Despierta a la IA inyectando una tarea programada en la cola.
    """
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] WAKEUP: {task_prompt}")
    message = f"[TAREA PROGRAMADA — {ts}] {task_prompt}"
    add_to_queue(message, source="scheduled_task")
    
def main():
    print("Starting Wakeup Daemon...")
    last_triggered = {}
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        tasks = load_schedule()
        for task in tasks:
            task_time = task.get("time")
            task_prompt = task.get("prompt")
            task_id = task.get("id")
            
            # Si coincide la hora y no se ha disparado hoy
            if current_time == task_time:
                today_str = now.strftime("%Y-%m-%d")
                if last_triggered.get(task_id) != today_str:
                    trigger_ai(task_prompt)
                    last_triggered[task_id] = today_str
                    
        time.sleep(30) # Comprueba cada 30 segundos

if __name__ == "__main__":
    main()
