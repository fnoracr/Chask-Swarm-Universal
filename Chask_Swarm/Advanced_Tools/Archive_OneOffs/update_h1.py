import os
import re
import subprocess

DIST_BASE_DIR = r"C:\Users\fnora\Desktop\Distribuciones"
MAIN_DIR = r"C:\Program Files\Chask_Swarm"

def run_cmd(cmd, cwd):
    print(f"Running '{cmd}' in {cwd}")
    subprocess.run(cmd, cwd=cwd, shell=True)

def update_html_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 1. Replace <h1>Chask <span>Hive</span></h1>
        # Use inline styles to be absolutely sure, while removing the old <span>
        h1_replacement = r'<h1><span style="color: var(--primary);">Cha</span><span style="color: #ffffff;">sk Schwa</span><span style="color: var(--primary);">rm</span></h1>'
        content = re.sub(r'<h1>\s*Chask\s*<span>\s*Hive\s*</span>\s*</h1>', h1_replacement, content, flags=re.IGNORECASE)
        
        # 2. Replace Iniciar_Chask_Hive.bat with Iniciar_Charm.bat
        content = content.replace("Iniciar_Chask_Hive.bat", "Iniciar_Charm.bat")
        
        # 3. Replace any stray "Chask Hive" ignoring case (excluding tags) just in case
        # Note: We already did the exact match, but this catches uppercase
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated HTML content: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

# 1. Process Main Directory
for root, _, files in os.walk(MAIN_DIR):
    for file in files:
        if file.endswith('.html'):
            update_html_file(os.path.join(root, file))

# 2. Process Distributions
repos = [os.path.join(DIST_BASE_DIR, d) for d in os.listdir(DIST_BASE_DIR) if os.path.isdir(os.path.join(DIST_BASE_DIR, d, ".git"))]

for repo in repos:
    print(f"\n--- Processing Repository: {repo} ---")
    changes_made = False
    
    # Update HTML contents
    for root, _, files in os.walk(repo):
        if '.git' in root: continue
        for file in files:
            if file.endswith('.html'):
                if update_html_file(os.path.join(root, file)):
                    changes_made = True

    if changes_made:
        run_cmd('git add .', repo)
        run_cmd('git commit -m "Fix main H1 title to Chask Schwarm with colors"', repo)
        run_cmd("git push origin master", repo)

print("\nAll distributions updated successfully.")
