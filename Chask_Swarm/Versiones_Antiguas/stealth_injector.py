import ctypes
import time
import sys
from ctypes import wintypes

# --- Estructuras y Constantes ---
class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT)
    ]

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_L = 0x4C
VK_ESCAPE = 0x1B
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

def find_antigravity_hwnd():
    found = []
    def callback(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if "Antigravity" in buff.value or "antigravity" in buff.value:
                    found.append(hwnd)
        return True
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return found[0] if found else None

def inject_v8(text):
    print("Enjambre: Iniciando Protocolo V8 (Quirurgical Focus Injection)...")
    main_hwnd = find_antigravity_hwnd()
    if not main_hwnd: return False
    
    my_tid = kernel32.GetCurrentThreadId()
    target_tid = user32.GetWindowThreadProcessId(main_hwnd, None)
    
    # 1. Attach threads
    user32.AttachThreadInput(my_tid, target_tid, True)
    
    try:
        # 2. Abrir Chat (Ctrl+L) usando keybd_event mientras estamos attached
        # Al estar attached, keybd_event afecta a la cola de entrada del hilo destino
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.1)
        user32.keybd_event(VK_L, 0, 0, 0)
        time.sleep(0.1)
        user32.keybd_event(VK_L, KEYEVENTF_KEYUP, 0, 0)
        user32.keybd_event(VK_CONTROL, KEYEVENTF_KEYUP, 0, 0)
        
        time.sleep(0.6) # Tiempo para que Electron mueva el foco al chat

        # 3. Identificar el control que tiene el foco REAL ahora
        gui = GUITHREADINFO()
        gui.cbSize = ctypes.sizeof(GUITHREADINFO)
        user32.GetGUIThreadInfo(target_tid, ctypes.byref(gui))
        
        target = gui.hwndFocus
        if not target:
            target = gui.hwndActive
        if not target:
            target = main_hwnd
            
        print(f"Target detectado para inyección: HWND {target}")

        # 4. Inyectar texto
        for char in text:
            user32.PostMessageW(target, WM_CHAR, ord(char), 0)
            time.sleep(0.005)

        # 5. Enter
        time.sleep(0.1)
        user32.PostMessageW(target, WM_KEYDOWN, VK_RETURN, 0)
        user32.PostMessageW(target, WM_KEYUP, VK_RETURN, 0)
        
    finally:
        user32.AttachThreadInput(my_tid, target_tid, False)
    
    print("Enjambre: Protocolo V8 finalizado.")
    return True

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Enjambre: [TEST V8] Inyección quirúrgica. Foco detectado por UIA/ThreadInfo."
    inject_v8(msg)
