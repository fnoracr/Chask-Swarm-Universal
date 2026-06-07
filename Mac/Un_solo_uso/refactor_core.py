import os
import shutil
import re

ROOT = r"C:\Program Files\Chask_Swarm"

MAPPINGS = {
    # Logs
    "Logs_Sistema/watchdog.log": "Logs_Sistema",
    "Logs_Sistema/guardian.log": "Logs_Sistema",
    "Logs_Sistema/launcher.log": "Logs_Sistema",
    "Logs_Sistema/nora_core.log": "Logs_Sistema",
    "Logs_Sistema/security_audit.log": "Logs_Sistema",
    "Logs_Sistema/sentinel.log": "Logs_Sistema",
    "Logs_Sistema/swarm_internet.log": "Logs_Sistema",
    "Logs_Sistema/swarm_network.log": "Logs_Sistema",
    "Logs_Sistema/swarm_power_audit.log": "Logs_Sistema",
    
    # Documentacion
    "Documentacion/Manual_Oficial_Charm.html": "Documentacion",
    "Documentacion/Manual_de_Uso_Charm.md": "Documentacion",
    "Documentacion/arquitectura_enjambre.html": "Documentacion",
    "Documentacion/README.md": "Documentacion",
    "Documentacion/LICENSE.md": "Documentacion",
    
    # Configuracion
    "Configuracion/master_credentials.json": "Configuracion",
    "Configuracion/authorized_users.json": "Configuracion",
    "Configuracion/channels_config.json": "Configuracion",
    "Configuracion/mcp_config.json": "Configuracion",
    "Configuracion/passport.json": "Configuracion",
    "Configuracion/skill_catalog.json": "Configuracion",
    "Configuracion/skills-lock.json": "Configuracion",
    "Configuracion/swarm_internet_config.json": "Configuracion",
    "Configuracion/swarm_network_config.json": "Configuracion",
    "Configuracion/users.json": "Configuracion",
    "Configuracion/workflows_active.json": "Configuracion",
    "Configuracion/workflows_backup.json": "Configuracion",
    "Configuracion/workflows_modified.json": "Configuracion",
    "Configuracion/guardian_state.json": "Configuracion",
    "Configuracion/meetcharm_users.db": "Configuracion",
    "Configuracion/evolutionary_memory.json": "Configuracion",
    "Configuracion/learned_lessons.json": "Configuracion",
    "Configuracion/canvas_descriptions.json": "Configuracion",

    # Colas y Estados
    "Colas_Mensajes/channel_messages.json": "Colas_Mensajes",
    "Colas_Mensajes/input_queue.json": "Colas_Mensajes",
    "Colas_Mensajes/out_pending.json": "Colas_Mensajes",
    "Colas_Mensajes/pending_messages.json": "Colas_Mensajes",
    "Colas_Mensajes/telegram_daemon_state.txt": "Colas_Mensajes",
    "Colas_Mensajes/telegram_sentinel_state.txt": "Colas_Mensajes",
    "Colas_Mensajes/telegram_state.txt": "Colas_Mensajes",
    "Colas_Mensajes/telegram_hashes.txt": "Colas_Mensajes",

    # Daemons
    "Advanced_Tools/Daemons/process_watchdog.py": "Advanced_Tools",
    "Advanced_Tools/Daemons/telegram_sentinel.py": "Advanced_Tools",
    "Advanced_Tools/Scripts_Mantenimiento/shutdown_cleanup.py": "Advanced_Tools",
    "Advanced_Tools/Scripts_Mantenimiento/generate_dist_canvas.py": "Advanced_Tools",
    "Advanced_Tools/Daemons/kill_switch_daemon.bat": "Advanced_Tools",

    # Binarios
    "Binarios/ffmpeg.exe": "Binarios",
    "Binarios/chask_logo.ico": "Binarios"
}

def create_folders():
    folders = set(MAPPINGS.values())
    for f in folders:
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Creada carpeta {path}")

def generate_replacements(filename, new_folder):
    replacements = [
        # Absolute paths
        (rf"C:\Program Files\Chask_Swarm\{filename}", rf"C:\Program Files\Chask_Swarm\{new_folder}\{filename}"),
        (rf"C:\\Program Files\\Chask_Swarm\\{filename}", rf"C:\\Program Files\\Chask_Swarm\\{new_folder}\\{filename}"),
        # os.path.join patterns
        (f', "{filename}"', f', "{new_folder}", "{filename}"'),
        (f", '{filename}'", f", '{new_folder}', '{filename}'"),
        (f', "{filename}")', f', "{new_folder}", "{filename}")'),
        (f", '{filename}')", f", '{new_folder}', '{filename}')"),
        # Batch and shell paths
        (rf"%CHASK_DIR%\{filename}", rf"%CHASK_DIR%\{new_folder}\{filename}"),
        (rf"%~dp0{filename}", rf"%~dp0{new_folder}\{filename}"),
        (rf"$(dirname ""$0"")/{filename}", rf"$(dirname ""$0"")/{new_folder}/{filename}"),
        (rf"./{filename}", rf"./{new_folder}/{filename}"),
        (rf".\{filename}", rf".\{new_folder}\{filename}"),
        # Python execution
        (f"python {filename}", f"python {new_folder}\\{filename}"),
        (f"pythonw {filename}", f"pythonw {new_folder}\\{filename}"),
        (f"pythonw.exe {filename}", f"pythonw.exe {new_folder}\\{filename}"),
        (f"python.exe {filename}", f"python.exe {new_folder}\\{filename}"),
        (f"start pythonw {filename}", f"start pythonw {new_folder}\\{filename}"),
        (f"start python {filename}", f"start python {new_folder}\\{filename}"),
        # Quotes (only after trying to match join/exec commands, to avoid double-replacing)
        # Note: applying this last in the list means it will match anything not caught above.
        # But we must be careful not to replace something already replaced. So we use a temporary placeholder?
        # Actually, python string replace is sequential. If we replace ', "file"' it won't be '"file"' anymore.
        (f'"{filename}"', f'"{new_folder}/{filename}"'),
        (f"'{filename}'", f"'{new_folder}/{filename}'"),
    ]
    return replacements

def rewrite_codebase():
    target_exts = {".py", ".bat", ".sh", ".json", ".md"}
    
    # We gather all replacements in a list of (old, new)
    all_replacements = []
    for file, folder in MAPPINGS.items():
        all_replacements.extend(generate_replacements(file, folder))
    
    # Scan all files
    for root_dir, dirs, files in os.walk(ROOT):
        if "Borrados" in root_dir or "Deprecado" in root_dir or "Versiones_Antiguas" in root_dir:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in target_exts:
                filepath = os.path.join(root_dir, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file_obj:
                        content = file_obj.read()
                    
                    original_content = content
                    for old, new in all_replacements:
                        # Prevent replacing already replaced things if there's a substring overlap. 
                        # But folder names don't overlap with filenames here.
                        content = content.replace(old, new)
                        
                    if content != original_content:
                        with open(filepath, "w", encoding="utf-8") as file_obj:
                            file_obj.write(content)
                        print(f"Modificado: {filepath}")
                except Exception as e:
                    print(f"Error leyendo {filepath}: {e}")

def move_files():
    for filename, folder in MAPPINGS.items():
        src = os.path.join(ROOT, filename)
        dst = os.path.join(ROOT, folder, filename)
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"Movido: {filename} -> {folder}/")
            except Exception as e:
                print(f"Error moviendo {filename}: {e}")

if __name__ == "__main__":
    print("Creando estructura de carpetas...")
    create_folders()
    print("Reescribiendo referencias en el código...")
    rewrite_codebase()
    print("Moviendo archivos físicos...")
    move_files()
    print("¡Refactorización Completada!")
