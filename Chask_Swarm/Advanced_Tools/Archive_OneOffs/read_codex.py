import uiautomation as auto
import time
import pyautogui
import pyperclip

def read_codex_chat():
    codex = auto.WindowControl(searchDepth=1, Name='Codex')
    if not codex.Exists(1):
        return "Error: No se encontró la ventana de Codex."
    
    # Hacer backup del portapapeles actual
    old_clipboard = pyperclip.paste()
    
    codex.SetFocus()
    time.sleep(0.5)
    
    # Seleccionar todo y copiar
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.2)
    
    # Quitar la selección haciendo clic en un área segura o pulsando escape/flecha
    pyautogui.press('right')
    time.sleep(0.1)
    
    content = pyperclip.paste()
    
    # Restaurar portapapeles si se quiere (opcional)
    # pyperclip.copy(old_clipboard)
    
    return content

if __name__ == "__main__":
    print(read_codex_chat())
