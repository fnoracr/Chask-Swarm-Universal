"""
auto_updater.py — Auto-actualización desde GitHub
Comprueba si hay versión nueva y actualiza el sistema con permiso del usuario.
"""
import os, sys, json, subprocess, requests, hashlib
from datetime import datetime

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TG_SCRIPT   = os.path.join(BASE_DIR, "charm_telegram.py")
VERSION_FILE = os.path.join(BASE_DIR, "version.json")

# Repositorio GitHub (actualizar con el repo real cuando esté disponible)
GITHUB_REPO    = "fnora/chask-swarm"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def get_current_version() -> str:
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, encoding="utf-8") as f:
            return json.load(f).get("version", "0.0.0")
    return "0.0.0"

def check_for_updates() -> dict | None:
    """Consulta GitHub API para ver si hay versión nueva."""
    try:
        r = requests.get(GITHUB_API_URL, timeout=10,
                         headers={"Accept": "application/vnd.github.v3+json"})
        if r.status_code == 200:
            data = r.json()
            latest = data.get("tag_name", "").lstrip("v")
            current = get_current_version()
            if latest and latest != current:
                return {
                    "version": latest,
                    "current": current,
                    "notes": data.get("body", "")[:300],
                    "url": data.get("html_url", "")
                }
    except Exception as e:
        print(f"[Updater] Error comprobando actualizaciones: {e}")
    return None

def send_telegram(msg: str):
    subprocess.run([sys.executable, TG_SCRIPT, "send", msg],
                   capture_output=True, timeout=20)

def notify_update(update_info: dict):
    msg = (
        f"🔄 ACTUALIZACIÓN DISPONIBLE\n"
        f"Versión actual: {update_info['current']}\n"
        f"Nueva versión: {update_info['version']}\n\n"
        f"Novedades: {update_info['notes']}\n\n"
        f"Dime 'actualiza Chask' para instalar, o ignora este mensaje."
    )
    send_telegram(msg)
    print(f"[Updater] Nueva versión disponible: {update_info['version']}")

def do_update():
    """Realiza la actualización via git pull."""
    git_dir = os.path.join(BASE_DIR, ".git")
    if not os.path.exists(git_dir):
        print("[Updater] No es un repositorio git. Actualización manual requerida.")
        return False
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"[Updater] Actualizado correctamente:\n{result.stdout}")
            # Reinstalar dependencias
            subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                            os.path.join(BASE_DIR, "requirements.txt"), "-q"],
                           capture_output=True, timeout=120)
            send_telegram("✅ Chask Swarm actualizado correctamente. Reiniciando...")
            return True
        else:
            print(f"[Updater] Error en git pull: {result.stderr}")
            return False
    except Exception as e:
        print(f"[Updater] Error actualizando: {e}")
        return False

def run_check():
    print(f"[Updater] Comprobando actualizaciones — {datetime.now().strftime('%H:%M')}")
    update = check_for_updates()
    if update:
        notify_update(update)
    else:
        print("[Updater] Sistema actualizado.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        do_update()
    else:
        run_check()
