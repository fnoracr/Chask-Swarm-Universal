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
        
        # 1. Replace in <title> without spans
        content = re.sub(r'<title>(.*?)Chask Hive(.*?)</title>', r'<title>\1Chask Schwarm\2</title>', content)
        
        # 2. Replace remaining "Chask Hive" with spans
        replacement = r'<span style="color: var(--primary);">Cha</span><span style="color: #ffffff;">sk Schwa</span><span style="color: var(--primary);">rm</span>'
        content = content.replace("Chask Hive", replacement)
        
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
print("--- Processing Main Directory ---")
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

    # Find files to rename (containing Charm)
    for root, _, files in os.walk(repo):
        if '.git' in root: continue
        for file in files:
            if 'Charm' in file and (file.endswith('.html') or file.endswith('.md')):
                old_path = os.path.join(root, file)
                new_file = file.replace('Charm', 'Charm')
                new_path = os.path.join(root, new_file)
                # Git mv
                rel_old = os.path.relpath(old_path, repo)
                rel_new = os.path.relpath(new_path, repo)
                run_cmd(f'git mv "{rel_old}" "{rel_new}"', repo)
                changes_made = True
                print(f"Git renamed: {rel_old} -> {rel_new}")

    if changes_made:
        run_cmd('git add .', repo)
        run_cmd('git commit -m "Update Chask Hive to Chask Schwarm and rename leftover Charm files"', repo)
        run_cmd("git push origin master", repo)

print("\nAll distributions updated successfully.")
