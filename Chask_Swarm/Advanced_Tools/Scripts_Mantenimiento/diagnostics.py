import os
import sys
import requests
import socket

# ==============================================================================
# ASISTENTE DE DIAGNÓSTICO PARA CHARM
# Verifica la salud del ecosistema antes de arrancar
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def check_python_deps():
    print("[1/4] Comprobando librerías Python...")
    try:
        import pydub
        import speech_recognition
        import pygetwindow
        import pyautogui
        import qdrant_client
        import gtts
        import plyer
        print("  [OK] Todas las dependencias están instaladas.")
        return True
    except ImportError as e:
        print(f"  [FALLO] Falta librería: {e}")
        print("  Ejecuta 'Instalar_Dependencias.bat'.")
        return False

def check_ffmpeg():
    print("[2/4] Comprobando binario de FFmpeg...")
    ffmpeg_path = os.path.join(BASE_DIR, "Binarios", "ffmpeg.exe")
    if os.path.exists(ffmpeg_path):
        print("  [OK] FFmpeg local detectado.")
        return True
    else:
        print("  [FALLO] No se encuentra ffmpeg.exe en el directorio raíz.")
        return False

def check_telegram():
    print("[3/4] Comprobando conexión a Telegram...")
    config_path = os.path.join(BASE_DIR, "Configuracion", "master_credentials.json")
    if not os.path.exists(config_path):
        print("  [FALLO] master_credentials.json no existe.")
        return False
        
    try:
        import json
        with open(config_path, 'r') as f:
            creds = json.load(f)
        token = creds.get('telegram_bot')
        if not token or token == "AQUÍ_VA_EL_TOKEN_DE_TU_BOT":
            print("  [FALLO] El Token del bot no se ha configurado.")
            return False
            
        url = f"https://api.telegram.org/bot{token}/getMe"
        resp = requests.get(url, timeout=5).json()
        if resp.get('ok'):
            print(f"  [OK] Conectado exitosamente como @{resp['result']['username']}")
            return True
        else:
            print(f"  [FALLO] El token no parece válido: {resp}")
            return False
    except Exception as e:
        print(f"  [FALLO] Error de conexión: {e}")
        return False

def check_qdrant():
    print("[4/4] Comprobando Base de Datos Qdrant (Docker)...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('127.0.0.1', 6333))
    sock.close()
    if result == 0:
        print("  [OK] Qdrant está ejecutándose en el puerto 6333.")
        return True
    else:
        print("  [AVISO] Qdrant no está respondiendo. Si no usas memoria a largo plazo, puedes ignorar esto. Para usarlo, asegúrate de que Docker está corriendo: 'docker run -p 6333:6333 qdrant/qdrant'")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ASISTENTE DE DIAGNÓSTICO DE CHARM")
    print("="*50 + "\n")
    
    r1 = check_python_deps()
    r2 = check_ffmpeg()
    r3 = check_telegram()
    r4 = check_qdrant()
    
    print("\n" + "="*50)
    if r1 and r2 and r3:
        print("  SISTEMA SALUDABLE. ¡Listo para iniciar telegram_daemon.py!")
    else:
        print("  SISTEMA INCOMPLETO. Por favor, resuelve los fallos antes de iniciar.")
    print("="*50 + "\n")
