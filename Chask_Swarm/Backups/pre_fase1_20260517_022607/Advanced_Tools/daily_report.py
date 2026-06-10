"""
daily_report.py — Informe diario automático
Cada día a las 22:00 resume el trabajo, lo guarda en Qdrant y lo manda por Telegram.
"""
import os, sys, subprocess, schedule, time
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY    = os.path.join(BASE_DIR, "memory.md")
AUDIT     = os.path.join(BASE_DIR, "Logs_Sistema", "security_audit.log")
TG_SCRIPT = os.path.join(BASE_DIR, "antigravity_telegram.py")
QDR       = os.path.join(BASE_DIR, "Advanced_Tools", "qdrant_memory_manager.py")

def send_telegram(msg: str):
    subprocess.run([sys.executable, TG_SCRIPT, "send", msg],
                   capture_output=True, timeout=20)

def generate_report() -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    lines = [f"📊 INFORME DIARIO — {today}\n"]

    # Resumen de memory.md
    if os.path.exists(MEMORY):
        with open(MEMORY, encoding="utf-8") as f:
            mem = f.read()
        # Extraer líneas relevantes
        relevant = [l.strip() for l in mem.splitlines()
                    if any(k in l for k in ["Tarea", "Proyecto", "Paso", "✅", "completad"])]
        if relevant:
            lines.append("🧠 Trabajo realizado:")
            lines.extend([f"  {l}" for l in relevant[:8]])
        else:
            lines.append("🧠 Sin tareas registradas hoy.")

    # Resumen de auditoría
    if os.path.exists(AUDIT):
        with open(AUDIT, encoding="utf-8") as f:
            audit_lines = f.readlines()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_actions = [l.strip() for l in audit_lines if today_str in l]
        if today_actions:
            lines.append(f"\n🔒 Acciones auditadas hoy: {len(today_actions)}")
            lines.extend([f"  {a}" for a in today_actions[-3:]])

    lines.append("\n✅ Sistema operativo. Hasta mañana.")
    return "\n".join(lines)

def do_daily_report():
    print(f"[DailyReport] Generando informe — {datetime.now().strftime('%H:%M')}")
    report = generate_report()
    print(report)

    # Enviar por Telegram
    send_telegram(report)

    # Guardar en Qdrant
    today = datetime.now().strftime("%Y-%m-%d")
    subprocess.run([
        sys.executable, QDR,
        "--save", report,
        "--keywords", f"informe,diario,{today}",
        "--project", "informes_diarios"
    ], capture_output=True, timeout=20)
    print("[DailyReport] Informe guardado en Qdrant.")

def run_daemon():
    report_time = "22:00"
    print(f"[DailyReport] Programado para las {report_time} cada día.")
    schedule.every().day.at(report_time).do(do_daily_report)
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        do_daily_report()
    else:
        run_daemon()
