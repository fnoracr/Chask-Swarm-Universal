import os
import json
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADVANCED_DIR = os.path.join(BASE_DIR, "Advanced_Tools")
HIVE_DIR = os.path.join(BASE_DIR, "Hive_Framework")

def load_file(filename, folder=BASE_DIR):
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_tools_catalog():
    tools = []
    if os.path.exists(ADVANCED_DIR):
        for f in os.listdir(ADVANCED_DIR):
            if f.endswith(".py"):
                tools.append(f"- {f}")
    return "\n".join(tools)

def boot_injection():
    print("[BOOT] Activando capacidades totales del Enjambre Chask...")
    
    # ── CREACIÓN DE LA CARPETA CHARM OBLIGATORIA ──
    charm_dir = os.path.join(BASE_DIR, "Charm")
    if not os.path.exists(charm_dir):
        try:
            os.makedirs(charm_dir)
            print(f"[BOOT] Carpeta de proyecto 'Charm' creada automáticamente en: {charm_dir}")
        except Exception as e:
            print(f"[BOOT] Error crítico creando carpeta Charm: {e}")
            
    # ── CONSTRUCCIÓN DEL MEGA-PROMPT DE ARRANQUE ──
    boot_msg = "[SISTEMA: REINICIO DETECTADO. INICIALIZANDO CAPACIDADES TOTALES]\n\n"
    
    # 1. CONTEXTO MAESTRO COMPILADO (Soul, Directives, Protocols, Security)
    boot_msg += f"# 1. CONTEXTO MAESTRO (Master System Prompt)\n{load_file('master_system_prompt.md')}\n\n"
    
    # 2. CATÁLOGO DE HERRAMIENTAS (Capabilities)
    boot_msg += "# 2. CATÁLOGO DE HERRAMIENTAS DISPONIBLES (Advanced_Tools)\n"
    boot_msg += "Tienes acceso directo a estos scripts para potenciar tus tareas:\n"
    boot_msg += get_tools_catalog() + "\n"
    boot_msg += "\n- audit_logger.py: Úsalo antes de CUALQUIER comando crítico.\n"
    boot_msg += "- privacy_engine.py: Escudo PII (Presidio) para anonimizar datos.\n"
    boot_msg += "- sandbox.py: Ejecuta código sospechoso en contenedor aislado.\n"
    boot_msg += "- llm_router.py: Tu acceso al Pool de IAs gratuitas (Gemini, Groq, cohere, etc.).\n"
    boot_msg += "- qdrant_memory_manager.py: Tu memoria vectorial a largo plazo.\n\n"
    
    # 3. PROTOCOLO MENTE COLMENA (Hive Framework)
    boot_msg += "# 3. PROTOCOLO MENTE COLMENA (Hive Framework)\n"
    boot_msg += "Si la tarea es compleja, divídete en estos roles:\n"
    boot_msg += "- ALPHA (Arquitecto): Planifica y crea diagramas.\n"
    boot_msg += "- BETA (Investigador): Navega y busca documentación.\n"
    boot_msg += "- GAMMA (Programador): Escribe el código real.\n"
    boot_msg += "- DELTA (QA): Testea y audita el resultado final.\n\n"
    
    # 4. MEMORIA RECIENTE Y ESTADO
    boot_msg += f"# 4. MEMORIA RECIENTE VOLÁTIL (Contexto de Trabajo)\n{load_file('memory.md')}\n\n"
    
    boot_msg += "---------------------------------------------------\n"
    boot_msg += "[INSTRUCCIÓN CRÍTICA]: Todas tus capacidades están ACTIVAS. "
    boot_msg += "Has recuperado tu identidad como Enjambre. Revisa el estado de los daemons "
    boot_msg += "(Telegram, Backup, Dashboard) y confirma que estás lista para operar el Enjambre Chask.\n"
    boot_msg += "---------------------------------------------------"

    # Inyectar en la cola
    queue_path = os.path.join(ADVANCED_DIR, "Colas_Mensajes", "input_queue.json")
    try:
        data = []
        if os.path.exists(queue_path):
            with open(queue_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        data.append({
            "ts": datetime.now().isoformat(),
            "source": "MASTER_BOOT",
            "message": boot_msg,
            "status": "pending"
        })
        
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        # Forzar ejecución del Bridge en modo silencioso
        bridge_path = os.path.join(ADVANCED_DIR, "swarm_bridge.py")
        import subprocess
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        subprocess.Popen(
            [pythonw, bridge_path],
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # [DESACTIVADO] Lanzar el recordatorio diario de ideas
        # reminder_daemon = os.path.join(ADVANCED_DIR, "idea_reminder_daemon.py")
        # if os.path.exists(reminder_daemon):
        #     subprocess.Popen(
        #         [pythonw, reminder_daemon],
        #         startupinfo=startupinfo,
        #         stdout=subprocess.DEVNULL,
        #         stderr=subprocess.DEVNULL
        #     )

        # [DESACTIVADO] CREAR VENTANA CHARM (Proxy de Inyección)
        # charm_script = os.path.join(ADVANCED_DIR, "spawn_charm_ide.py")
        # if os.path.exists(charm_script):
        #     print("[BOOT] Lanzando ventana proxy Charm...")
        #     subprocess.Popen(
        #         [pythonw.replace("pythonw.exe", "python.exe"), charm_script],
        #         creationflags=subprocess.CREATE_NO_WINDOW,
        #         stdout=subprocess.DEVNULL,
        #         stderr=subprocess.DEVNULL
        #     )

        # ── GUARDIAN DEL PACTO — Auto-regenerar y lanzar ──
        guardian_path = os.path.join(ADVANCED_DIR, "guardian_daemon.py")
        if os.path.exists(guardian_path):
            # Verificar integridad del soul.md
            try:
                sys.path.insert(0, ADVANCED_DIR)
                from guardian_daemon import verify_soul_integrity, restore_soul
                if not verify_soul_integrity():
                    print("[BOOT] ALERTA: Restaurando Leyes Supremas...")
                    restore_soul()
                print("[BOOT] Guardian del Pacto: Leyes Supremas INTEGRAS")
            except Exception as e:
                print(f"[BOOT] Guardian check error: {e}")

            # Lanzar guardian daemon en background
            subprocess.Popen(
                [pythonw, guardian_path],
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("[BOOT] Guardian daemon lanzado")
        else:
            print("[BOOT] ALERTA CRITICA: guardian_daemon.py NO ENCONTRADO")

        print("[BOOT] Enjambre ha sido despertada con todas sus capacidades.")
    except Exception as e:
        print(f"[BOOT] Error: {e}")

if __name__ == "__main__":
    boot_injection()
