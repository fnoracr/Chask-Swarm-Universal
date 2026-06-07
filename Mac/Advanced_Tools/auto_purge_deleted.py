import os
import time

def purge_deleted_folder(base_dir):
    """Purges files in the 'Borrados' (or 'Deleted') folder older than 48 hours."""
    # Look for either the Spanish or English name depending on the distribution
    folder_paths = [
        os.path.join(base_dir, "Borrados"),
        os.path.join(base_dir, "Deleted")
    ]
    
    current_time = time.time()
    # 48 hours in seconds
    age_limit_seconds = 48 * 3600

    for folder_path in folder_paths:
        if not os.path.exists(folder_path):
            continue

        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    file_mod_time = os.path.getmtime(file_path)
                    if current_time - file_mod_time > age_limit_seconds:
                        os.remove(file_path)
                        print(f"Purged: {file_path}")
                except Exception as e:
                    print(f"Failed to purge file {file_path}: {e}")

    # Nuevo bloque para Logs y Backups (límite de 24 horas = 24 * 3600)
    system_folders = [
        os.path.join(base_dir, "Logs_Sistema"),
        os.path.join(base_dir, "Chask_Backups")
    ]
    age_limit_24h = 24 * 3600

    for folder_path in system_folders:
        if not os.path.exists(folder_path):
            continue
            
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    file_mod_time = os.path.getmtime(file_path)
                    if current_time - file_mod_time > age_limit_24h:
                        os.remove(file_path)
                        print(f"Purged (24h limit): {file_path}")
                except Exception as e:
                    pass
            # Intentar borrar directorios vacíos (como las subcarpetas de backups)
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        print(f"Purged empty directory: {dir_path}")
                except Exception:
                    pass

if __name__ == "__main__":
    # Base directory of Chask Swarm
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Starting auto purge daemon...")
    while True:
        purge_deleted_folder(base_dir)
        # Sleep for 1 hour
        time.sleep(3600)
