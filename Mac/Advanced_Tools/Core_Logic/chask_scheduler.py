"""
chask_scheduler.py — Scheduling Inteligente
===========================================
Daemon que ejecuta tareas programadas con cron expressions.
Usa APScheduler. Reporta por Telegram y registra en Qdrant.
"""
import os
import sys
import json
import subprocess
import signal
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduled_tasks.json")
LOG = os.path.join(BASE, "scheduler.log")
PYTHON = sys.executable


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    print(line)


def send_telegram(msg):
    try:
        subprocess.run([PYTHON, os.path.join(BASE, "charm_telegram.py"), "send", msg],
                       capture_output=True, timeout=15)
    except:
        pass


def run_action(task_name, action):
    """Ejecuta una accion programada."""
    log(f"Ejecutando tarea: {task_name} -> {action}")
    try:
        if action == "system_health":
            # Health check rapido
            import urllib.request
            checks = {}
            try:
                urllib.request.urlopen("http://localhost:6333/collections", timeout=3)
                checks["qdrant"] = "OK"
            except:
                checks["qdrant"] = "FAIL"
            try:
                urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
                checks["ollama"] = "OK"
            except:
                checks["ollama"] = "FAIL"
            msg = f"[SCHEDULER] Health Check:\n" + "\n".join(f"  {k}: {v}" for k, v in checks.items())
            log(msg)

        elif action == "daily_report":
            subprocess.run([PYTHON, os.path.join(BASE, "Advanced_Tools", "daily_report.py")],
                           capture_output=True, timeout=60)
            log(f"Daily report ejecutado")

        elif action == "git_status_all":
            # Git status de repos conocidos
            repos_dir = r"C:\Users\fnora\Desktop\Enjambre Datos"
            if os.path.exists(repos_dir):
                result = subprocess.run(["git", "status", "--short"], capture_output=True,
                                        text=True, cwd=repos_dir, timeout=10)
                log(f"Git status: {result.stdout[:200]}")

        elif action.endswith(".py"):
            # Ejecutar script arbitrario
            script = os.path.join(BASE, "Advanced_Tools", action)
            if os.path.exists(script):
                subprocess.run([PYTHON, script], capture_output=True, timeout=120)
                log(f"Script {action} ejecutado")

        else:
            log(f"Accion desconocida: {action}")

        # Registrar en Qdrant
        try:
            from chask_operational_memory import OperationalMemory
            mem = OperationalMemory()
            mem.log_operation(f"Scheduled: {task_name}", approach=action,
                              result="success", keywords=["scheduler", task_name],
                              project="scheduler")
        except:
            pass

    except Exception as e:
        log(f"ERROR en tarea {task_name}: {e}")
        send_telegram(f"[SCHEDULER] Error en '{task_name}': {str(e)[:100]}")


def main():
    log("=" * 50)
    log("Enjambre Scheduler arrancando...")

    # Cargar tareas
    if not os.path.exists(TASKS_FILE):
        # Crear tareas por defecto
        default_tasks = [
            {"cron": "*/30 * * * *", "name": "Health Check", "action": "system_health"},
            {"cron": "0 22 * * *", "name": "Daily Report", "action": "daily_report"}
        ]
        with open(TASKS_FILE, "w") as f:
            json.dump(default_tasks, f, indent=2)
        log(f"Fichero de tareas creado con {len(default_tasks)} tareas por defecto")

    with open(TASKS_FILE, "r") as f:
        tasks = json.load(f)

    scheduler = BlockingScheduler()

    for task in tasks:
        parts = task["cron"].split()
        if len(parts) == 5:
            trigger = CronTrigger(minute=parts[0], hour=parts[1], day=parts[2],
                                   month=parts[3], day_of_week=parts[4])
            scheduler.add_job(run_action, trigger, args=[task["name"], task["action"]],
                              id=task["name"], replace_existing=True)
            log(f"  Tarea registrada: '{task['name']}' -> {task['cron']}")

    log(f"{len(tasks)} tareas programadas. Scheduler activo.")
    send_telegram(f"[SCHEDULER] Activo con {len(tasks)} tareas programadas.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log("Scheduler detenido.")


if __name__ == "__main__":
    main()
