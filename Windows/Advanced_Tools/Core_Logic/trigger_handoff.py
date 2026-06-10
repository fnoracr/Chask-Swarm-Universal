import os
import sys
import json
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HANDOFF_FILE = os.path.join(BASE_DIR, "..", "handoff_context.json")
ORCHESTRATOR_PATH = os.path.join(BASE_DIR, "local_orchestrator.py")

def trigger_handoff(reason="Traspaso manual solicitado por Charm."):
    print(f"Iniciando Protocolo de Traspaso (Handoff)...")
    
    # 1. Crear el contexto de handoff
    ctx = {
        "timestamp": datetime.now().isoformat(),
        "message": reason,
        "source": "charm_manual"
    }
    
    try:
        with open(HANDOFF_FILE, "w", encoding="utf-8") as f:
            json.dump(ctx, f, indent=2)
        print(f"Contexto guardado en {HANDOFF_FILE}")
    except Exception as e:
        print(f"Error escribiendo contexto: {e}")
        return False
        
    # 2. Levantar orquestador local
    try:
        subprocess.Popen(
            [sys.executable, ORCHESTRATOR_PATH],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )
        print("Orquestador local lanzado con éxito.")
    except Exception as e:
        print(f"Error levantando orquestador: {e}")
        return False
        
    return True

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Handoff de emergencia activado."
    if trigger_handoff(msg):
        print("Traspaso completado. Charm cede el mando.")
        sys.exit(0)
    else:
        sys.exit(1)
