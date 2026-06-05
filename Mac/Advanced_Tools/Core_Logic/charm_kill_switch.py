"""
charm_kill_switch.py — Interruptor Maestro de Chask Swarm
===========================================================
Se conecta a Telegram y permite apagar o encender el sistema
entero desde el teléfono del administrador.
Soporte para teclados No-Latinos mediante ReplyKeyboards y Comandos.
"""
import os
import sys
import json
import time
import subprocess
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHASK_DIR = os.path.dirname(BASE_DIR)
CREDENTIALS_FILE = os.path.join(CHASK_DIR, "Configuration", "master_credentials.json")

# Python executable (use the main pythonw.exe or python.exe depending on needs)
PYTHONW_EXE = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Python", "Python311", "pythonw.exe")

def get_credentials():
    with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["messaging"]["telegram"]["bot_token"], str(data["messaging"]["telegram"]["admin_id"])

BOT_TOKEN, ADMIN_ID = get_credentials()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def send_message(chat_id, text, use_keyboard=True):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if use_keyboard:
        # Añadimos el teclado visual permanente (ReplyKeyboardMarkup)
        payload["reply_markup"] = {
            "keyboard": [
                [{"text": "🔴 Off [Nombre_IA]"}, {"text": "🟢 On [Nombre_IA]"}]
            ],
            "resize_keyboard": True,
            "persistent": True
        }
    
    requests.post(API_URL + "sendMessage", json=payload)

def kill_system():
    # 0. Crear candado para que el watchdog no levante nada
    lock_file = os.path.join(CHASK_DIR, "kill_switch.lock")
    with open(lock_file, "w") as f:
        f.write("KILLED")

    # 1. Guardar memoria a corto plazo en Qdrant (largo plazo) antes de apagar
    try:
        adv_tools = os.path.join(CHASK_DIR, "Advanced_Tools")
        if adv_tools not in sys.path:
            sys.path.append(adv_tools)
        from qdrant_memory_manager import index_memory
        
        mem_path = os.path.join(CHASK_DIR, "memory.md")
        if os.path.exists(mem_path):
            with open(mem_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                index_memory(content, keywords=["shutdown", "memory_dump", "estado_final"])
                print("Memoria guardada en Qdrant exitosamente.")
    except Exception as e:
        print(f"Error guardando memoria en Qdrant: {e}")

    # 2. Matar todos los daemons de Python en CHASK_DIR excepto nosotros
    subprocess.run('wmic process where "name=\'python.exe\' and commandline like \'%Chask_Swarn%\' and not commandline like \'%charm_kill_switch.py%\'" call terminate', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run('wmic process where "name=\'pythonw.exe\' and commandline like \'%Chask_Swarn%\' and not commandline like \'%charm_kill_switch.py%\'" call terminate', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Cerrar visualmente el IDE (matando todo su árbol de procesos)
    subprocess.run('taskkill /F /IM Antigravity.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 4. Detener contenedores Docker
    subprocess.run('docker stop n8n qdrant', shell=True)

def start_system():
    # 1. Quitar el candado de seguridad
    lock_file = os.path.join(CHASK_DIR, "kill_switch.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except:
            pass

    # 2. Matar todos los daemons activos (limpieza profunda y fiable con wmic)
    subprocess.run('wmic process where "name=\'python.exe\' and commandline like \'%Chask_Swarn%\' and not commandline like \'%charm_kill_switch.py%\'" call terminate', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run('wmic process where "name=\'pythonw.exe\' and commandline like \'%Chask_Swarn%\' and not commandline like \'%charm_kill_switch.py%\'" call terminate', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Lanzar el acceso directo del escritorio garantizando la visibilidad.
    shortcut_path = os.path.join(os.path.expanduser("~"), "Desktop", "Boot Chask Swarm.lnk")
    
    try:
        # os.startfile invoca la API ShellExecute nativa de Windows.
        # Es literalmente la misma llamada a nivel de SO que hace el ratón al hacer doble clic.
        os.startfile(shortcut_path)
    except Exception as e:
        print(f"Error con os.startfile: {e}")
        # Fallback por si acaso
        subprocess.Popen(f'explorer.exe "{shortcut_path}"', shell=True)

def main():
    offset = None
    print("Kill Switch Daemon Iniciado. Esperando órdenes...")
    # Enviar mensaje de inicio con el teclado
    send_message(ADMIN_ID, "🛡️ *Kill Switch Armado*.\n\nUsa los botones abajo, o los comandos /on y /off para controlar el Enjambre Chask Swarm.")
    
    while True:
        try:
            req_url = API_URL + "getUpdates?timeout=30"
            if offset:
                req_url += f"&offset={offset}"
            
            resp = requests.get(req_url, timeout=40).json()
            if not resp.get("ok"):
                time.sleep(5)
                continue
            
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                
                if not message:
                    continue
                
                chat_id = str(message.get("chat", {}).get("id"))
                
                # REGLA DE HIERRO: Solo el Admin puede interactuar.
                if chat_id != ADMIN_ID:
                    continue
                
                text = message.get("text", "").strip().lower()
                
                if text in ["off charm", "/off", "🔴 off charm", "🛑"]:
                    send_message(chat_id, "⚠️ Iniciando apagado de emergencia (Kill Switch)...")
                    kill_system()
                    send_message(chat_id, "💀 Chask Swarm ha sido apagado. Daemons muertos, contenedores detenidos. Solo el Kill Switch sigue despierto.")
                
                elif text in ["on charm", "/on", "🟢 on charm", "🚀", "/start_charm"]:
                    send_message(chat_id, "🌱 Encendiendo el Ouroboros (Watchdog)...")
                    start_system()
                    send_message(chat_id, "✅ Watchdog activado. El Enjambre se está auto-ensamblando de fondo. Todo debería estar online en ~60 segundos.")
                    
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    main()
