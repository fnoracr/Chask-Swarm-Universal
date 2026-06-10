"""
stealth_uiautomation.py — Inyección de Interfaz de Usuario (Modo Silencioso)
=========================================================================================
"""

import time
import ctypes
import os

try:
    from pywinauto.application import Application
except ImportError:
    pass # Pywinauto not installed, fallback to disabled

def inject_to_charm(text: str, source: str = "web") -> tuple[bool, str]:
    # Escribir en el historial silenciosamente (chat_history.md en Charm)
    charm_dir = r"C:\Program Files\Chask_Swarm\Charm"
    if not os.path.exists(charm_dir):
        try:
            os.makedirs(charm_dir, exist_ok=True)
        except Exception:
            pass
            
    history_path = os.path.join(charm_dir, "chat_history.md")
    try:
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(f"\n**[{source.upper()}]** {time.strftime('%Y-%m-%d %H:%M:%S')}\\n{text}\\n")
    except Exception:
        pass

    try:
        import pyautogui
        import pygetwindow as gw
        
        # Find the Antigravity IDE window
        windows = [w for w in gw.getWindowsWithTitle('') if 'Antigravity' in w.title or 'Nora' in w.title or 'Charm' in w.title]
        if not windows:
            return False, "No se encontró la ventana del IDE"
            
        win = windows[0]
        
        # Bring to front and restore if minimized
        if win.isMinimized:
            win.restore()
        win.activate()
        time.sleep(0.5)
        
        # Type the message directly (assumes chat box gets focus or is already focused)
        # To be safe, we just send keys
        pyautogui.write(text, interval=0.01)
        pyautogui.press('enter')
        
        return True, "Inyectado usando pyautogui"
    except Exception as e:
        return False, f"Excepción en inyección silenciosa: {e}"

if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "Test de inyeccion silenciosa"
    print(inject_to_charm(msg))
