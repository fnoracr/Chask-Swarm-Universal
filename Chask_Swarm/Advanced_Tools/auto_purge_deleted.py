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
                    print(f"Failed to purge {file_path}: {e}")

if __name__ == "__main__":
    # Base directory of Chask Swarm
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Starting auto purge daemon...")
    while True:
        purge_deleted_folder(base_dir)
        # Sleep for 1 hour
        time.sleep(3600)
