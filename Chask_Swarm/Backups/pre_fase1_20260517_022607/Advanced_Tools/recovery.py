"""
recovery.py — Recuperación automática del sistema desde backup
Uso: python recovery.py              → recupera el último backup
     python recovery.py list         → lista backups disponibles
     python recovery.py backup_XXXX  → recupera un backup específico
"""
import os
import shutil
import json
import sys

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(BASE_DIR, "Chask_Backups")

def list_backups():
    if not os.path.exists(BACKUP_DIR):
        print("No se encontró la carpeta de backups.")
        return []
    backups = sorted([d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")])
    if not backups:
        print("No hay backups disponibles.")
        return []
    print(f"\n{'='*50}")
    print("  BACKUPS DISPONIBLES")
    print(f"{'='*50}")
    for i, b in enumerate(backups):
        mp = os.path.join(BACKUP_DIR, b, "manifest.json")
        if os.path.exists(mp):
            with open(mp, encoding="utf-8") as f:
                m = json.load(f)
            print(f"  [{i}] {b}  —  {m['total']} archivos")
        else:
            print(f"  [{i}] {b}")
    print(f"{'='*50}\n")
    return backups

def recover(backup_name: str):
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        print(f"[ERROR] Backup no encontrado: {backup_path}")
        return False

    manifest_path = os.path.join(backup_path, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        files = manifest.get("files", [])
    else:
        files = [f for f in os.listdir(backup_path) if f != "manifest.json"]

    print(f"\n[Recovery] Restaurando desde: {backup_name}")
    print(f"[Recovery] Archivos a restaurar: {len(files)}")

    restored = []
    errors = []

    for item in files:
        item_clean = item.rstrip("/")
        src = os.path.join(backup_path, os.path.basename(item_clean))
        dst = os.path.join(BASE_DIR, item_clean)

        try:
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            elif os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            restored.append(item_clean)
        except Exception as e:
            errors.append(f"{item_clean}: {e}")

    print(f"\n[Recovery] ✅ Restaurados: {len(restored)}")
    for r in restored:
        print(f"    ✓ {r}")

    if errors:
        print(f"\n[Recovery] ⚠️  Errores: {len(errors)}")
        for e in errors:
            print(f"    ✗ {e}")

    print(f"\n[Recovery] Sistema restaurado desde {backup_name}")
    return len(errors) == 0

def recover_latest():
    backups = list_backups()
    if not backups:
        return False
    latest = backups[-1]
    print(f"[Recovery] Recuperando el backup más reciente: {latest}")
    return recover(latest)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "list":
            list_backups()
        elif arg.startswith("backup_"):
            recover(arg)
        else:
            print("Uso: python recovery.py [list | backup_YYYYMMDD_HHMMSS]")
    else:
        # Sin argumentos → recuperar el más reciente
        confirm = input("¿Recuperar el backup más reciente? (s/N): ").strip().lower()
        if confirm == "s":
            recover_latest()
        else:
            print("Operación cancelada.")
            backups = list_backups()
            if backups:
                choice = input("Introduce el nombre del backup a recuperar (o Enter para salir): ").strip()
                if choice:
                    recover(choice)
