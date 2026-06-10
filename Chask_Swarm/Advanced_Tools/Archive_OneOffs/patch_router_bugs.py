import os

directories_to_scan = [
    r"C:\Program Files\Chask_Swarm",
    r"C:\Users\fnora\Desktop"
]

files_to_patch = []

for base_dir in directories_to_scan:
    for root, dirs, files in os.walk(base_dir):
        if 'node_modules' in dirs: dirs.remove('node_modules')
        if '.git' in dirs: dirs.remove('.git')
        
        for file in files:
            if file.startswith("web_dashboard") and file.endswith(".py"):
                files_to_patch.append(os.path.join(root, file))

print(f"Found {len(files_to_patch)} dashboard scripts.")

old_regex = r"addressed_to_nora = bool(re.match(r'^nor[^a-záéíóúüñA-ZÁÉÍÓÚÜÑ]', full_message, re.IGNORECASE))"
new_regex = r"addressed_to_nora = bool(re.match(r'^nora?\b', full_message, re.IGNORECASE))"

old_escalate_1 = 'if resp and "__escalate__" not in resp:'
new_escalate_1 = 'if resp and "__escalate__" not in resp and "__escalade__" not in resp:'

for f_path in files_to_patch:
    try:
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        patched = False
        
        if old_regex in content:
            content = content.replace(old_regex, new_regex)
            patched = True
            
        if old_escalate_1 in content:
            content = content.replace(old_escalate_1, new_escalate_1)
            patched = True
            
        if patched:
            with open(f_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Patched successfully: {f_path}")
    except Exception as e:
        print(f"Failed {f_path}: {e}")
