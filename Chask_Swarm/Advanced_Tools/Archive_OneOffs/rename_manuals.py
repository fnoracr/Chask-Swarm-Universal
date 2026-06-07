import os
import subprocess

DIST_BASE_DIR = r"C:\Users\fnora\Desktop\Distribuciones"

# Map old names to new names
renames = {
    "Documentacion/Manual_Oficial_Charm.html": "Documentacion/Manual_Oficial_Charm.html",
    "Documentacion/Manual_de_Uso_Charm.md": "Documentacion/Manual_de_Uso_Charm.md",
    "Prompt_Telegram_Charm.md": "Prompt_Telegram_Charm.md",
}

def run_git(cmd, cwd):
    print(f"Running '{cmd}' in {cwd}")
    subprocess.run(cmd, cwd=cwd, shell=True)

# 1. Rename in C:\Program Files\Chask_Swarm
src_dir = r"C:\Program Files\Chask_Swarm"
for old_name, new_name in renames.items():
    old_path = os.path.join(src_dir, old_name)
    new_path = os.path.join(src_dir, new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f"Renamed in {src_dir}: {old_name} -> {new_name}")

# 2. Rename in Github repos
repos = [os.path.join(DIST_BASE_DIR, d) for d in os.listdir(DIST_BASE_DIR) if os.path.isdir(os.path.join(DIST_BASE_DIR, d, ".git"))]

for repo in repos:
    print(f"\n--- Processing Repository: {repo} ---")
    changes_made = False
    
    for old_name, new_name in renames.items():
        old_path = os.path.join(repo, old_name)
        new_path = os.path.join(repo, new_name)
        if os.path.exists(old_path):
            # Using git mv to rename
            run_git(f'git mv "{old_name}" "{new_name}"', repo)
            changes_made = True
            print(f"Git renamed: {old_name} -> {new_name}")

    if changes_made:
        run_git('git commit -m "Rename Charm manuals to Charm"', repo)
        run_git("git push origin master", repo)

print("\nManuals renamed successfully.")
