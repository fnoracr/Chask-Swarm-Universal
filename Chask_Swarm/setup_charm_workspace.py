import os
import sys

def setup_workspace():
    base_dir = r"C:\Program Files\Chask_Swarm"
    charm_dir = os.path.join(base_dir, "Charm")
    
    print(f"Configurando Workspace de Charm en: {charm_dir}")
    
    if not os.path.exists(charm_dir):
        os.makedirs(charm_dir, exist_ok=True)
        print("Directorio Charm creado.")
    else:
        print("Directorio Charm ya existe.")
        
    history_path = os.path.join(charm_dir, "chat_history.md")
    if not os.path.exists(history_path):
        with open(history_path, "w", encoding="utf-8") as f:
            f.write("# Historial de Conversaciones de Charm\n\n")
            f.write("Este archivo guarda el registro de los mensajes inyectados silenciosamente desde Telegram u otros canales.\n\n")
        print("Archivo chat_history.md creado.")
        
    readme_path = os.path.join(charm_dir, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# Proyecto Charm\n\n")
            f.write("Abre esta carpeta en Antigravity para iniciar el entorno de Charm.\n")
            f.write("Por diseño de seguridad de Antigravity, debes crear el primer chat manualmente y llamarlo 'Charm'.\n")
            f.write("A partir de ese momento, el Inyector Silencioso funcionará en segundo plano usando esta carpeta.\n")
        print("Archivo README.md creado.")

    flag_path = os.path.join(charm_dir, ".charm_initialized")
    if not os.path.exists(flag_path):
        print("Iniciando inyeccion de UI para crear conversacion inicial...")
        with open(flag_path, "w") as f:
            f.write("initialized")
        
        # Opcional: inyeccion de atajos de teclado
        # Descomentar e instalar pyautogui si se requiere inyeccion visual
        try:
            import pyautogui
            import time
            print("Esperando 10s a que Antigravity cargue la UI...")
            time.sleep(10)
            
            # Nuevo chat
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(1)
            
            # Enviar mensaje para inicializar el chat y forzar que el nombre sea "Charm"
            pyautogui.write("Charm")
            time.sleep(0.5)
            pyautogui.press('enter')
            print("Inyeccion completada.")
        except ImportError:
            print("pyautogui no instalado, saltando inyeccion UI.")

if __name__ == "__main__":
    setup_workspace()
