import os
import time
import shutil
from datetime import datetime, timedelta

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHASK_DATOS_DIR = r"C:\Users\fnora\Desktop\Enjambre Datos"

BORRADOS_PATHS = [
    os.path.join(BASE_DIR, "Borrados"),
    os.path.join(CHASK_DATOS_DIR, "Borrados")
]

LOG_FILE = os.path.join(BASE_DIR, "borrados_cleanup.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def clean_borrados():
    """Borra permanentemente archivos con más de 48 horas de antigüedad."""
    log("Iniciando limpieza de carpetas 'Borrados'...")
    now = time.time()
    retention_seconds = 48 * 3600  # 48 horas
    
    count = 0
    errors = 0
    
    for path in BORRADOS_PATHS:
        if not os.path.exists(path):
            continue
            
        log(f"Escaneando: {path}")
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                # Comprobar fecha de modificación
                mtime = os.path.getmtime(item_path)
                if (now - mtime) > retention_seconds:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    log(f"  [BORRADO] {item} (Antigüedad superada)")
                    count += 1
            except Exception as e:
                log(f"  [ERROR] No se pudo borrar {item}: {e}")
                errors += 1
                
    log(f"Limpieza completada: {count} elementos eliminados, {errors} errores.")

def main():
    # 1. Ejecución inicial (arranque)
    clean_borrados()
    
    log("Daemon de limpieza en espera (Próxima ejecución diaria a las 08:00 AM)")
    
    # 2. Bucle de daemon para ejecución diaria a las 08:00
    last_run_day = datetime.now().strftime("%Y-%m-%d")
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%Y-%m-%d")
        
        # Si son las 08:00 y no se ha ejecutado hoy
        if current_time == "08:00" and last_run_day != current_day:
            log("Disparando limpieza programada (08:00 AM)...")
            clean_borrados()
            last_run_day = current_day
            
        time.sleep(60) # Comprobar cada minuto

if __name__ == "__main__":
    main()
