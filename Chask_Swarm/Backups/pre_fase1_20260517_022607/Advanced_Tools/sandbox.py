import sys
import subprocess
import os

# ==============================================================================
# DOCKER SANDBOX RUNNER
# Uso: python sandbox.py mi_codigo_sospechoso.py
# ==============================================================================

def run_in_sandbox(script_path):
    if not os.path.exists(script_path):
        print(f"Error: No se encuentra {script_path}")
        return

    script_name = os.path.basename(script_path)
    script_dir = os.path.dirname(os.path.abspath(script_path))

    print(f"[Sandbox] Levantando contenedor Docker aislado para ejecutar {script_name}...")
    
    # Run the script inside an ephemeral python docker container
    # -rm removes container after run
    # -v mounts the directory read-only (ro) except if we want the script to write output
    # --network none disables internet access to prevent malware from dialing home
    
    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "-v", f"{script_dir}:/usr/src/app:ro",
        "-w", "/usr/src/app",
        "python:3.10-alpine",
        "python", script_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("\n--- SALIDA DEL SANDBOX ---")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("\n[ERRORES O ADVERTENCIAS]:")
            print(result.stderr)
        print("--- FIN DEL SANDBOX ---")
    except Exception as e:
        print(f"[Sandbox Error] No se pudo ejecutar Docker: {e}")
        print("Asegúrate de tener Docker instalado y encendido.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_in_sandbox(sys.argv[1])
    else:
        print("Uso: python sandbox.py mi_script.py")
