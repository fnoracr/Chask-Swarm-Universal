"""
inject_to_antigravity.py — Inyector compartido para Chask Swarm
================================================================
Escribe un mensaje a pending_messages.json y lo inyecta en Antigravity.
Des-maximiza si necesario, pone ventana pequeña, escribe, envía detrás.

Uso: python inject_to_antigravity.py "mensaje" [source]
"""
import sys
import os
import json
import time
import ctypes
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_FILE = os.path.join(BASE_DIR, "Colas_Mensajes", "pending_messages.json")

try:
    import pyperclip
    import pyautogui
    HAS_UI = True
except ImportError:
    HAS_UI = False


def write_to_pending(text, source="web"):
    try:
        data = []
        if os.path.exists(PENDING_FILE):
            with open(PENDING_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({
            "id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source}",
            "ts": datetime.now().isoformat(),
            "source": source,
            "text": text,
            "thinking_mid": None,
            "status": "pending"
        })
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False


def _find_hwnd():
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    found = [None]
    def cb(hwnd, lp):
        length = GetWindowTextLength(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buf, length + 1)
            if "Antigravity" in buf.value or "antigravity" in buf.value:
                found[0] = hwnd
                return False
        return True
    EnumWindows(EnumWindowsProc(cb), 0)
    return found[0]


def _make_small(hwnd):
    """Des-maximiza y redimensiona Antigravity a 500x350 en esquina inferior derecha."""
    # Des-maximizar si está maximizada
    if ctypes.windll.user32.IsZoomed(hwnd):
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.3)
    # Des-minimizar si está minimizada
    if ctypes.windll.user32.IsIconic(hwnd):
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.3)
    # Mover y redimensionar
    sw = ctypes.windll.user32.GetSystemMetrics(0)
    sh = ctypes.windll.user32.GetSystemMetrics(1)
    ctypes.windll.user32.MoveWindow(hwnd, sw - 510, sh - 400, 500, 350, True)


def _send_behind(hwnd):
    """Envía la ventana detrás de todas las demás."""
    ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0,
        0x0001 | 0x0002 | 0x0010)


def hide_antigravity():
    """Solo oculta Antigravity (sin inyectar). Para uso del panel web al cargar."""
    hwnd = _find_hwnd()
    if not hwnd:
        return False
    _make_small(hwnd)
    _send_behind(hwnd)
    return True


def inject(text, source="web"):
    """Inyecta mensaje en Antigravity."""
    if not HAS_UI:
        return False
    try:
        hwnd = _find_hwnd()
        if not hwnd:
            return False

        prev_hwnd = ctypes.windll.user32.GetForegroundWindow()
        _make_small(hwnd)

        ctypes.windll.user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)

        # Asegurar que el panel de chat está abierto (Escape reset + Ctrl+L abre)
        pyautogui.press('escape')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.5)

        tag = "WEB" if source == "web" else source.upper()
        formatted = f"[{tag} {datetime.now().strftime('%H:%M:%S')}] {text}"
        pyperclip.copy(formatted)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        pyautogui.press('enter')
        time.sleep(0.3)

        _send_behind(hwnd)
        time.sleep(0.1)
        if prev_hwnd:
            ctypes.windll.user32.SetForegroundWindow(prev_hwnd)
        return True
    except:
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--hide":
            hide_antigravity()
        else:
            text = sys.argv[1]
            source = sys.argv[2] if len(sys.argv) > 2 else "cli"
            write_to_pending(text, source)
            inject(text, source)
