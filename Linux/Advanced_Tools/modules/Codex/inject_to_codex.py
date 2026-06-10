import os
import sys
import time
import ctypes
from ctypes import wintypes
import logging

LOG_FILE = os.path.join(os.path.dirname(__file__), "inject_codex.log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("stealth_codex")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

def find_codex_hwnd():
    import psutil
    found = []
    
    def callback(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                try:
                    p = psutil.Process(pid.value)
                    proc_name = p.name().lower()
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    
                    if "codex" in proc_name or "codex" in title:
                        found.append(hwnd)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        return True
        
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    
    if found:
        return found[0] # Return the first matching window
    return None

def inject_to_codex(text):
    hwnd = find_codex_hwnd()
    if not hwnd:
        log.error("Codex window not found for injection.")
        return False
        
    try:
        import pyautogui
        import pyperclip
    except ImportError:
        log.error("pyautogui/pyperclip not installed.")
        return False

    prev_fg = user32.GetForegroundWindow()

    # Hack to force foreground (bypass Windows restriction)
    fg_hwnd = user32.GetForegroundWindow()
    if fg_hwnd != hwnd:
        user32.keybd_event(0x12, 0, 0, 0) # ALT down
        user32.keybd_event(0x12, 0, 2, 0) # ALT up
        
        fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
        my_thread = kernel32.GetCurrentThreadId()
        if fg_thread and fg_thread != my_thread:
            user32.AttachThreadInput(my_thread, fg_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            user32.AttachThreadInput(my_thread, fg_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)
            
    time.sleep(0.2)
    
    if user32.GetForegroundWindow() != hwnd:
        log.error("Fallo de seguridad: La ventana no obtuvo el foco. Abortando inyección física.")
        return False

    try:
        # Inject text
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        # Usamos el atajo de teclado nativo de Codex para "Nuevo Chat" (Ctrl+N)
        # Esto automáticamente limpia la pantalla y pone el foco en el cuadro de texto.
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(0.5)
        
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.2)
        
        log.info(f"Stealth GUI injection successful for msg: {text[:40]}")
    except Exception as e:
        log.error(f"Error during pyautogui injection: {e}")
        return False
    finally:
        # Restore state
        if prev_fg and prev_fg != hwnd:
            user32.SetForegroundWindow(prev_fg)
            
    return True

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Escribe un post de prueba sobre IA"
    if inject_to_codex(msg):
        print("OK Inyectado en Codex")
    else:
        print("ERROR al inyectar en Codex")
