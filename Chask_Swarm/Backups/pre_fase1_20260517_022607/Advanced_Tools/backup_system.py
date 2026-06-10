"""
backup_system.py — Backup automático horario + recuperación
Guarda toda la configuración del sistema en una carpeta con timestamp
"""
import os
import shutil
import schedule
import time
import json
from datetime import datetime

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(BASE_DIR, "Chask_Backups")

# Archivos y carpetas críticos a respaldar
BACKUP_TARGETS = [
    "telegram_config.json",
    "memory.md",
    "projects_memory.md",
    "directives.md",
    "security.md",
    "soul.md",
    "Cuestionario_Soul.md",
    "Prompt_Telegram_Antigravity.md",
    "Instrucciones_Instalacion.md",
    "Chask_Hive_Credenciales_y_Config",
    "Advanced_Tools/schedule_template.json",
    "skills",
]

def do_backup():
    """Realiza un backup completo con timestamp."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"backup_{ts}")
    os.makedirs(dest, exist_ok=True)

    backed = []
    for target in BACKUP_TARGETS:
        src = os.path.join(BASE_DIR, target)
        if os.path.isfile(src):
            shutil.copy2(src, dest)
            backed.append(target)
        elif os.path.isdir(src):
            shutil.copytree(src, os.path.join(dest, os.path.basename(src)),
                            dirs_exist_ok=True)
            backed.append(target + "/")

    # Guardar manifiesto
    manifest = {
        "timestamp": ts,
        "base_dir": BASE_DIR,
        "files": backed,
        "total": len(backed)
    }
    with open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Mantener los últimos 24 backups (se borra el más antiguo cuando hay 25)
    backups = sorted([
        d for d in os.listdir(BACKUP_DIR)
        if d.startswith("backup_")
    ])
    while len(backups) > 24:
        oldest = backups.pop(0)
        shutil.rmtree(os.path.join(BACKUP_DIR, oldest))
        print(f"[Backup] Borrado histórico antiguo: {oldest}")

    print(f"[Backup] {ts} — {len(backed)} elementos guardados en {dest}")
    return dest

def list_backups():
    """Lista todos los backups disponibles."""
    if not os.path.exists(BACKUP_DIR):
        print("No hay backups disponibles.")
        return []
    backups = sorted([
        d for d in os.listdir(BACKUP_DIR)
        if d.startswith("backup_")
    ])
    for b in backups:
        manifest_path = os.path.join(BACKUP_DIR, b, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as f:
                m = json.load(f)
            print(f"  {b}  —  {m['total']} archivos")
        else:
            print(f"  {b}")
    return backups

def run_daemon():
    """Ejecuta backup inmediato y luego cada hora."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print("[Backup] Daemon iniciado. Backup inicial en progreso...")
    do_backup()
    schedule.every(1).hours.do(do_backup)
    print("[Backup] Programado backup automático cada hora.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_backups()
    elif len(sys.argv) > 1 and sys.argv[1] == "now":
        os.makedirs(BACKUP_DIR, exist_ok=True)
        do_backup()
    else:
        run_daemon()
