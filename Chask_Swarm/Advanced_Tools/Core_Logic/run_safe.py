import sys
import subprocess
import os

# ====================================================================
# AUTO-HEALING WRAPPER
# Uso: python run_safe.py mi_script.py [argumentos...]
# Si el script falla, atrapa el error y se lo manda a la IA por Telegram
# ====================================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TELEGRAM_SCRIPT = os.path.join(BASE_DIR, "charm_telegram.py")

def main():
    if len(sys.argv) < 2:
        print("Uso: python run_safe.py mi_script.py")
        sys.exit(1)
        
    script_to_run = sys.argv[1]
    args = sys.argv[2:]
    
    print(f"[RunSafe] Ejecutando: {script_to_run}")
    
    try:
        # Ejecutar el script y capturar su salida (stderr)
        result = subprocess.run(
            [sys.executable, script_to_run] + args,
            capture_output=True,
            text=True
        )
        
        # Imprimir la salida normal al usuario
        if result.stdout:
            print(result.stdout)
            
        if result.returncode != 0:
            print("[RunSafe] ¡Se ha detectado un error! Enviando a Charm...")
            error_text = result.stderr.strip()
            print(f"Error:\n{error_text}")
            
            # Mandar el error por Telegram
            msg = f"¡ALERTA DE AUTO-HEALING!\nHe intentado ejecutar `{script_to_run}` pero ha crasheado. Este es el Traceback:\n\n```python\n{error_text}\n```\n\nPor favor, dime cómo solucionarlo."
            
            subprocess.run([sys.executable, TELEGRAM_SCRIPT, "send", msg])
            print("[RunSafe] Error reportado con éxito. Revisa tu Telegram.")
        else:
            print("[RunSafe] Ejecución completada sin errores.")
            
    except Exception as e:
        print(f"[RunSafe] Fallo catastrófico al intentar ejecutar {script_to_run}: {e}")

if __name__ == "__main__":
    main()
