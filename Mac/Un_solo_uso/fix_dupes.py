import os

ROOT = r"C:\Program Files\Chask_Swarm"

folders = [
    "Logs_Sistema", "Documentacion", "Configuracion", "Colas_Mensajes", "Advanced_Tools", "Binarios"
]

target_exts = {".py", ".bat", ".sh", ".json", ".md"}

def clean_dupes():
    for root_dir, dirs, files in os.walk(ROOT):
        if "Borrados" in root_dir or "Deprecado" in root_dir or "Versiones_Antiguas" in root_dir or "Chask_Backups" in root_dir:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in target_exts:
                filepath = os.path.join(root_dir, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file_obj:
                        content = file_obj.read()
                    
                    original_content = content
                    
                    # Fix triple/double join inserts
                    for folder in folders:
                        # Fix: , "Folder", "Folder", "Folder/file.ext" -> , "Folder", "file.ext"
                        # We'll just replace ', "Folder", ' recursively until only one is left
                        # But wait, Python replace is easy.
                        content = content.replace(f', "{folder}", "{folder}", "{folder}/', f', "{folder}", "')
                        content = content.replace(f", '{folder}', '{folder}', '{folder}/", f", '{folder}', '")
                        content = content.replace(f', "{folder}", "{folder}/', f', "{folder}", "')
                        content = content.replace(f", '{folder}', '{folder}/", f", '{folder}', '")
                        content = content.replace(f', "{folder}", "{folder}", ', f', "{folder}", ')
                        content = content.replace(f", '{folder}', '{folder}', ", f", '{folder}', ")
                        
                        # Fix Windows paths: \Folder\Folder\ -> \Folder\
                        content = content.replace(f"\\{folder}\\{folder}\\", f"\\{folder}\\")
                        # Fix linux paths: /Folder/Folder/ -> /Folder/
                        content = content.replace(f"/{folder}/{folder}/", f"/{folder}/")

                        # If it became: os.path.join(..., "Logs_Sistema", "watchdog.log")
                        content = content.replace(f', "{folder}", "{folder}/', f', "{folder}", "')
                        
                        # Sometimes it might be os.path.join(..., "Configuracion", "master_credentials.json")
                        content = content.replace(f', "{folder}", "{folder}\\', f', "{folder}", "')

                    if content != original_content:
                        with open(filepath, "w", encoding="utf-8") as file_obj:
                            file_obj.write(content)
                        print(f"Reparado: {filepath}")
                except Exception as e:
                    print(f"Error {filepath}: {e}")

if __name__ == "__main__":
    clean_dupes()
