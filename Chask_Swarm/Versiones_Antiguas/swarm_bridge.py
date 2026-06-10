"""
swarm_bridge.py — Puente de Inyección (Protocolo Storm).
Restaura el parpadeo único necesario para inyectar mensajes.
"""
import os, json, sys, time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_PATH = os.path.join(BASE_DIR, "Advanced_Tools", "input_queue.json")
INBOX_DIR = os.path.join(BASE_DIR, "Advanced_Tools", "inbox")

if not os.path.exists(INBOX_DIR):
    os.makedirs(INBOX_DIR)

def log_bridge(text):
    log_path = os.path.join(BASE_DIR, "Advanced_Tools", "bridge_debug.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {text}\n")

def inject_to_ide(full_text: str) -> bool:
    """Inyecta un mensaje en el IDE de Antigravity (Parpadeo Único)."""
    try:
        import pygetwindow as gw
        import pyautogui
        import pyperclip

        # 1. Localizar ventana (Búsqueda difusa con reintentos)
        target = None
        for i in range(30): # Esperar hasta 30 segundos
            all_wins = gw.getAllWindows()
            target = next((w for w in all_wins if "Antigravity" in w.title or "antigravity" in w.title), None)
            if target:
                break
            time.sleep(1)
        
        if not target:
            log_bridge("Error: IDE Antigravity no encontrado tras 30 segundos de espera.")
            return False

        win = target
        was_minimized = win.isMinimized

        # 2. Restaurar y Posicionar
        if was_minimized:
            win.restore()
            time.sleep(0.5)
        
        screen_w, screen_h = pyautogui.size()
        win_w, win_h = 400, 300
        win.resizeTo(win_w, win_h)
        win.moveTo(screen_w - win_w - 20, screen_h - win_h - 20)
        
        # 3. Activar e Inyectar
        win.activate()
        time.sleep(0.7)
        
        # Verificación de foco
        active = gw.getActiveWindow()
        if active and ("Antigravity" in active.title or "antigravity" in active.title):
            pyperclip.copy(full_text)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            pyautogui.press('enter')
            log_bridge(f"Éxito: Mensaje inyectado en: {active.title}")
        else:
            log_bridge(f"Foco fallido: {active.title if active else 'None'}")
            return False

        # 4. Minimizar de nuevo si estaba minimizada
        if was_minimized:
            time.sleep(0.8)
            win.minimize()

        return True
    except Exception as e:
        log_bridge(f"Excepción en inject_to_ide: {e}")
        return False

def process_queue():
    if not os.path.exists(QUEUE_PATH): return

    try:
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            queue = json.load(f)

        # Procesar tanto los nuevos (pending) como los que fallaron (inbox_ready)
        pending = [m for m in queue if m.get("status") in ["pending", "inbox_ready"]]
        if not pending: return

        for msg in pending:
            ts = datetime.now().strftime('%H%M%S_%f')
            filename = f"INBOX_{ts}_{msg['source']}.txt"
            filepath = os.path.join(INBOX_DIR, filename)
            full_text = f"[ENJAMBRE: {msg['source'].upper()}] {msg['message']}"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_text)

            # Inyectar (esto causará el parpadeo único)
            injected = inject_to_ide(full_text)
            msg["status"] = "injected" if injected else "inbox_ready"

        with open(QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"[Bridge] Error: {e}")

if __name__ == "__main__":
    process_queue()
