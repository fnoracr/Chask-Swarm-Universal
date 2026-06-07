import os
import shutil
import re

BASE_DIR = r"C:\Program Files\Chask_Swarm"
ADV_DIR = os.path.join(BASE_DIR, "Advanced_Tools")
AUTO_DIR = os.path.join(BASE_DIR, "Automatizaciones")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Map file keywords to subfolders for Advanced_Tools
ADV_MAP = {
    "Daemons": ["daemon", "watchdog", "sentinel", "svc", "worker", "monitor", "listener", "kill_switch.bat"],
    "Core_Logic": ["memory", "engine", "logger", "core", "orchestrator", "skill", "security", "injection", "responder", "slash", "auth", "filter", "anti_drift", "router", "topic", "protocolo", "sandbox", "mcp"],
    "Integrations": ["browser", "gemma", "sdk", "youtube", "internet", "network", "email", "discord", "telegram", "teams", "slack", "dashboard", "vision", "automation", "mcp_client", "computer_use"],
    "Scripts_Mantenimiento": ["build", "updater", "diagnostics", "generate", "report", "test", "cleanup", "telemetry", "backup", "setup", "install", "start", "recovery", "resurrection", "janitor"],
    "Data": [".json"]
}

# Map for Automatizaciones
AUTO_MAP = {
    "Twitter": ["twitter", "tweet"],
    "Instagram": ["insta"],
    "Patreon": ["patreon"],
    "YouTube": ["youtube", "video"],
    "FTP_Distribucion": ["ftp"]
}

def classify_file(filename, mapping_dict):
    f_lower = filename.lower()
    for cat, keywords in mapping_dict.items():
        for kw in keywords:
            if kw in f_lower:
                return cat
    if f_lower.endswith(".json"):
        return "Data"
    return "Core_Logic" # default for unclassified

def refactor():
    file_moves = {} # original_path -> new_path
    rel_moves = {} # original_filename -> "NewFolder/filename"
    
    # 1. Advanced Tools
    if os.path.exists(ADV_DIR):
        for f in os.listdir(ADV_DIR):
            fpath = os.path.join(ADV_DIR, f)
            if os.path.isfile(fpath):
                cat = classify_file(f, ADV_MAP)
                new_dir = os.path.join(ADV_DIR, cat)
                ensure_dir(new_dir)
                new_fpath = os.path.join(new_dir, f)
                file_moves[fpath] = new_fpath
                rel_moves[f] = f"Advanced_Tools/{cat}/{f}"
                
    # 2. Automatizaciones
    if os.path.exists(AUTO_DIR):
        for f in os.listdir(AUTO_DIR):
            fpath = os.path.join(AUTO_DIR, f)
            if os.path.isfile(fpath):
                cat = classify_file(f, AUTO_MAP)
                new_dir = os.path.join(AUTO_DIR, cat)
                ensure_dir(new_dir)
                new_fpath = os.path.join(new_dir, f)
                file_moves[fpath] = new_fpath
                rel_moves[f] = f"Automatizaciones/{cat}/{f}"

    # Move files
    print("Moviendo archivos...")
    for old_p, new_p in file_moves.items():
        try:
            shutil.move(old_p, new_p)
            print(f"Movido: {os.path.basename(old_p)} -> {os.path.basename(os.path.dirname(new_p))}")
        except Exception as e:
            print(f"Error moviendo {old_p}: {e}")

    # Now rewrite files in BASE_DIR recursively
    target_exts = {".py", ".bat", ".sh", ".json", ".md"}
    
    # Pre-compute replacements
    replacements = []
    for f_name, new_rel in rel_moves.items():
        # new_rel is like "Advanced_Tools/Daemons/file.py"
        # we want to replace "Advanced_Tools/file.py" with "Advanced_Tools/Daemons/file.py"
        old_rel = f"Advanced_Tools/{f_name}" if "Advanced_Tools" in new_rel else f"Automatizaciones/{f_name}"
        old_rel_win = old_rel.replace("/", "\\\\")
        new_rel_win = new_rel.replace("/", "\\\\")
        
        replacements.append((f'"{old_rel}"', f'"{new_rel}"'))
        replacements.append((f"'{old_rel}'", f"'{new_rel}'"))
        replacements.append((f'"{old_rel_win}"', f'"{new_rel_win}"'))
        replacements.append((f"'{old_rel_win}'", f"'{new_rel_win}'"))
        
        # also if just "file.py" is referenced and it was in Advanced_Tools
        if "Advanced_Tools" in new_rel:
            subfolder = new_rel.split("/")[1]
            replacements.append((f'Advanced_Tools\\\\{f_name}', f'Advanced_Tools\\\\{subfolder}\\\\{f_name}'))
            replacements.append((f'Advanced_Tools/{f_name}', f'Advanced_Tools/{subfolder}/{f_name}'))

    print("Actualizando rutas en codigo...")
    for root, dirs, files in os.walk(BASE_DIR):
        if "Borrados" in root or "Chask_Backups" in root or "Backups" in root:
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in target_exts:
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file_obj:
                        content = file_obj.read()
                    
                    orig_content = content
                    for old_str, new_str in replacements:
                        content = content.replace(old_str, new_str)
                        
                    if content != orig_content:
                        with open(filepath, "w", encoding="utf-8") as file_obj:
                            file_obj.write(content)
                        print(f"Actualizado: {filepath}")
                except Exception as e:
                    pass
    print("Refactor profundo finalizado!")

if __name__ == "__main__":
    refactor()
