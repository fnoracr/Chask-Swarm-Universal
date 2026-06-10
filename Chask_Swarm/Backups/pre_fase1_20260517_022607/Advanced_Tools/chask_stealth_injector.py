"""
chask_stealth_injector.py — Motor de Inyeccion Stealth V8.0
============================================================
Inyecta texto en el chat de Antigravity IDE usando UIA ValuePattern
cuando es posible (sin clipboard, sin pyautogui). Fallback a clipboard
si ValuePattern no esta disponible.

Mejoras V8.0 vs V7.5:
- Intenta ValuePattern primero (no toca clipboard del usuario)
- Fallback a clipboard + Ctrl+V si ValuePattern falla
- Hotkey Ctrl+L via SendMessage (no pyautogui) para abrir chat
- Logging de metodo usado para diagnostico
"""
import uiautomation as auto
import time
import ctypes
from ctypes import wintypes

# Constantes Win32
SW_RESTORE = 9
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_L = 0x4C

user32 = ctypes.windll.user32


def _send_enter_via_uia(control):
    """Envia Enter al control usando SendMessage (no necesita pyautogui)."""
    hwnd = control.NativeWindowHandle
    if hwnd:
        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RETURN, 0)
        time.sleep(0.05)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_RETURN, 0)
        return True
    return False


def _open_chat_panel(window):
    """Abre el panel de chat con Ctrl+L via la ventana."""
    hwnd = window.NativeWindowHandle
    if hwnd:
        # Ctrl+L via PostMessage
        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_CONTROL, 0)
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_L, 0)
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_L, 0)
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_CONTROL, 0)
        time.sleep(1.2)
        return True
    # Fallback a pyautogui
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(1.2)
        return True
    except:
        return False


def inject_to_antigravity(text):
    """
    Motor de Inyeccion Stealth V8.0
    Prioriza ValuePattern (sin clipboard). Fallback a clipboard si falla.
    Retorna (success: bool, message: str)
    """
    method_used = "none"
    try:
        # 1. Localizar ventana por subcadena
        window = auto.WindowControl(searchDepth=1, SubName='Antigravity')
        if not window.Exists(2):
            window = auto.WindowControl(
                searchDepth=1, ClassName='Chrome_WidgetWin_1', SubName='Antigravity'
            )

        if not window.Exists(0):
            return False, "Ventana Antigravity no encontrada"

        main_hwnd = window.NativeWindowHandle

        # 2. Guardar ventana activa para restaurar despues
        prev_hwnd = user32.GetForegroundWindow()

        # 3. Restaurar si minimizada y traer al frente
        user32.ShowWindow(main_hwnd, SW_RESTORE)
        time.sleep(0.15)
        user32.SetForegroundWindow(main_hwnd)
        time.sleep(0.5)

        # 4. Buscar chat input
        chat_input = window.EditControl(searchDepth=100, Name='Message input')

        if not chat_input.Exists(2):
            _open_chat_panel(window)
            chat_input = window.EditControl(searchDepth=100, Name='Message input')

        if not chat_input.Exists(0):
            return False, "No se localizo la caja de chat 'Message input'"

        # 5. INTENTAR ValuePattern (metodo preferido: sin clipboard)
        value_ok = False
        try:
            vp = chat_input.GetValuePattern()
            vp.SetValue(text)
            value_ok = True
            method_used = "ValuePattern"
        except Exception:
            pass

        if not value_ok:
            # 6. FALLBACK: clipboard + Ctrl+V
            try:
                import pyperclip
                import pyautogui

                rect = chat_input.BoundingRectangle
                center_x = (rect.left + rect.right) // 2
                center_y = (rect.top + rect.bottom) // 2

                pyautogui.click(center_x, center_y)
                time.sleep(0.2)

                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')
                method_used = "Clipboard+CtrlV"
            except Exception as e:
                return False, f"Fallback clipboard fallo: {e}"

        # 7. Enviar Enter
        time.sleep(0.2)
        enter_sent = _send_enter_via_uia(chat_input)
        if not enter_sent:
            try:
                import pyautogui
                pyautogui.press('enter')
            except:
                return False, "No se pudo enviar Enter"

        # 8. Restaurar ventana anterior
        time.sleep(0.3)
        if prev_hwnd and prev_hwnd != main_hwnd:
            user32.SetForegroundWindow(prev_hwnd)

        return True, f"Inyeccion exitosa (metodo: {method_used})"

    except Exception as e:
        return False, f"Error en motor de inyeccion: {str(e)}"


if __name__ == "__main__":
    success, msg = inject_to_antigravity("Enjambre: Test de motor Stealth V8.0")
    print(f"{msg} (Exito: {success})")
