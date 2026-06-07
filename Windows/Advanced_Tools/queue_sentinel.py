"""
Centinela de cola de mensajes para Nora v2.
Poll cada 3s. Al detectar pending:
  1. Extrae el mensaje real del usuario
  2. Marca como "processing"  
  3. Imprime el mensaje extraído
  4. SALE → despierta a Antigravity
"""
import json, time, os, re

# === BLINDAJE DE INSTANCIA ÚNICA ===
try:
    import win32event, win32api, winerror, sys
    mutex = win32event.CreateMutex(None, 1, "Global\\ChaskSwarmQueueSentinel")
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        # Ya hay un centinela activo. Salimos silenciosamente.
        sys.exit(0)
except ImportError:
    pass

QUEUE = r"C:\Program Files\Chask_Swarm\Advanced_Tools\Colas_Mensajes\input_queue.json"

def extract_user_message(raw):
    """Extrae solo el texto del usuario del wrapper de contexto."""
    # Buscar patrón [TELEGRAM HH:MM:SS] [USER: xxx] mensaje
    m = re.search(r'\[TELEGRAM \d{2}:\d{2}:\d{2}\] \[USER: \w+\] (.+)', raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Buscar patrón de comando del sistema [TELEGRAM] Nora, ...
    m = re.search(r'\[TELEGRAM\] (.+)', raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    return raw.strip()

while True:
    try:
        if os.path.exists(QUEUE):
            with open(QUEUE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            pending = [x for x in data if x.get("status") == "pending"]
            if pending:
                messages = []
                for item in pending:
                    item["status"] = "processing"
                    msg = extract_user_message(item.get("message", ""))
                    source = item.get("source", "unknown")
                    messages.append(f"[{source.upper()}] {msg}")
                
                # Guardar estado "processing"
                with open(QUEUE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Imprimir mensajes extraídos y salir
                for msg in messages:
                    print(msg)
                break
    except Exception:
        pass
    time.sleep(3)
