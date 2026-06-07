import os
import sys
import time
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

def spawn_and_rename():
    try:
        import pyautogui
    except ImportError:
        print("[Charm] pyautogui no instalado.")
        return False
        
    found_hwnd = None
    def callback(hwnd, extra):
        nonlocal found_hwnd
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.lower()
            if "resolving system communication loop" in title:
                found_hwnd = hwnd
                return False
        return True
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    
    if not found_hwnd:
        print("[Charm] No se encontró ventana principal para duplicar.")
        return False
        
    print(f"[Charm] Ventana principal encontrada HWND: {found_hwnd}. Duplicando...")
    user32.ShowWindow(found_hwnd, 9)
    time.sleep(0.2)
    user32.SetForegroundWindow(found_hwnd)
    time.sleep(0.5)
    
    # Abrir nueva ventana (Ctrl+Shift+N)
    pyautogui.hotkey('ctrl', 'shift', 'n')
    print("[Charm] Esperando a que cargue la nueva ventana...")
    time.sleep(6)
    
    # La nueva ventana debería ser la activa ahora
    new_hwnd = user32.GetForegroundWindow()
    if new_hwnd == found_hwnd:
        print("[Charm] Falló la creación de nueva ventana.")
        return False
        
    # Abrir chat (Ctrl+L)
    print("[Charm] Preparando chat (Ctrl+L)...")
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(1)
    
    # Renombrar ventana a "Charm - Charm Proxy"
    new_title = "Charm - Charm Proxy"
    user32.SetWindowTextW(new_hwnd, new_title)
    
    # Minimizar
    time.sleep(0.5)
    user32.ShowWindow(new_hwnd, 2) # SW_SHOWMINIMIZED
    
    # Devolver foco a la principal
    user32.ShowWindow(found_hwnd, 9)
    user32.SetForegroundWindow(found_hwnd)
    
    # GUARDAR HWND PARA LA INYECCION
    hwnd_path = os.path.join(os.path.dirname(__file__), "charm_hwnd.txt")
    with open(hwnd_path, "w") as f:
        f.write(str(new_hwnd))
    
    print(f"[Charm] Ventana configurada y minimizada correctamente: {new_title} (HWND: {new_hwnd})")
    return True

if __name__ == "__main__":
    spawn_and_rename()
