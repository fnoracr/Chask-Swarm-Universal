import uiautomation as auto
import pyperclip
import pyautogui
import time
import ctypes
from ctypes import wintypes

# Constantes Win32
SW_MINIMIZE = 6
SW_SHOWNORMAL = 1
SW_SHOWNOACTIVATE = 4

class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.UINT),
        ("ptMinPosition", wintypes.POINT),
        ("ptMaxPosition", wintypes.POINT),
        ("rcNormalPosition", wintypes.RECT),
    ]

user32 = ctypes.windll.user32

def inject_to_antigravity(text):
    """
    Motor de Inyección Stealth V7.5 (Standard Enjambre)
    Busca la ventana del IDE por subcadena, abre el chat con Ctrl+L,
    pega el texto y envía. NO minimiza al final.
    """
    try:
        # 1. Localizar ventana por subcadena (el título cambia dinámicamente)
        window = auto.WindowControl(searchDepth=1, SubName='Antigravity')
        if not window.Exists(2):
            # Fallback: buscar por clase Electron
            window = auto.WindowControl(searchDepth=1, ClassName='Chrome_WidgetWin_1', SubName='Antigravity')

        if not window.Exists(0):
            return False, "Ventana Antigravity no encontrada"

        main_hwnd = window.NativeWindowHandle

        # 2. Guardar ventana activa actual para restaurar al final
        prev_hwnd = user32.GetForegroundWindow()

        # 3. Restaurar si está minimizada y traer al frente
        user32.ShowWindow(main_hwnd, 9)  # SW_RESTORE
        time.sleep(0.15)
        user32.SetForegroundWindow(main_hwnd)
        time.sleep(0.5)

        # 4. Localizar chat input
        chat_input = window.EditControl(searchDepth=100, Name='Message input')

        if not chat_input.Exists(2):
            # Abrir chat con Ctrl+L
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(1.2)
            chat_input = window.EditControl(searchDepth=100, Name='Message input')

        if chat_input.Exists(0):
            rect = chat_input.BoundingRectangle
            center_x = (rect.left + rect.right) // 2
            center_y = (rect.top + rect.bottom) // 2

            # Click y pegado
            pyautogui.click(center_x, center_y)
            time.sleep(0.2)

            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            pyautogui.press('enter')

            # Restaurar ventana anterior (NO minimizar Antigravity)
            time.sleep(0.3)
            if prev_hwnd and prev_hwnd != main_hwnd:
                user32.SetForegroundWindow(prev_hwnd)

            return True, "Inyección exitosa"
        else:
            return False, "No se localizó la caja de chat 'Message input'"

    except Exception as e:
        return False, f"Error en el motor de inyección: {str(e)}"

if __name__ == "__main__":
    success, msg = inject_to_antigravity("Enjambre: Test de motor Stealth V7.5")
    print(f"{msg} (Exito: {success})")

