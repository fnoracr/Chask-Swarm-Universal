import os
import sys
import json
import time
import shutil
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

BASE_DIR = r"C:\Program Files\Chask_Swarm"
CHASK_DATOS_DIR = r"C:\Users\fnora\Desktop\Enjambre Datos"
LOG_FILE = os.path.join(BASE_DIR, "janitor.log")

BORRADOS_PATHS = [
    os.path.join(BASE_DIR, "Deleted"),
    os.path.join(CHASK_DATOS_DIR, "Deleted")
]

# Qdrant configs
COLLECTION_NAME = "charm_memory"
VECTOR_SIZE = 384

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def clean_borrados(days_old=7):
    """Elimina archivos en Deleted que sean más antiguos que `days_old` días."""
    log(f"Iniciando limpieza de papelera (archivos con >{days_old} días)")
    cutoff = time.time() - (days_old * 86400)
    count = 0
    for folder in BORRADOS_PATHS:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime < cutoff:
                        os.remove(filepath)
                        count += 1
                except Exception as e:
                    log(f"Error borrando {filepath}: {e}")
    log(f"Limpieza finalizada. {count} archivos viejos eliminados.")

def archive_daily_logs():
    """Toma el unified_daemon.log y lo consolida en Qdrant (placeholder)."""
    log("Iniciando archivado de logs diarios en Qdrant.")
    log_path = os.path.join(BASE_DIR, "unified_daemon.log")
    if not os.path.exists(log_path):
        log("No hay log diario para archivar hoy.")
        return
    
    # Aquí iría la lógica de vectorización (omitida para mantener ligereza si no hay servidor local)
    # Lo ideal es que esto se integre con evolutionary_memory.py que ya maneja embeddings.
    # Por ahora simplemente rotamos el log para que no crezca infinitamente.
    size = os.path.getsize(log_path)
    if size > 10 * 1024 * 1024:  # > 10MB
        archive_path = log_path + "." + datetime.now().strftime("%Y%m%d")
        shutil.move(log_path, archive_path)
        log(f"Log rotado a {archive_path}")

def run_janitor():
    log("=== JANITOR DAEMON INICIADO ===")
    clean_borrados(7)
    archive_daily_logs()
    log("=== JANITOR DAEMON FINALIZADO ===")

if __name__ == "__main__":
    run_janitor()
