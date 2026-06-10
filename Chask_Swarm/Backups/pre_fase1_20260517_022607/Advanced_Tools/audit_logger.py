import sys
import os
from datetime import datetime

# ==============================================================================
# AUDIT LOGGER (CAJA NEGRA)
# Uso: python audit_logger.py "Comando o acción realizada por la IA"
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_FILE = os.path.join(BASE_DIR, "Logs_Sistema", "security_audit.log")

def log_action(action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [ANTIGRAVITY_ACTION] -> {action}\n")
    print(f"[Audit Log] Acción registrada correctamente.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action_text = " ".join(sys.argv[1:])
        log_action(action_text)
    else:
        print("Uso: python audit_logger.py 'Texto de la acción a registrar'")
