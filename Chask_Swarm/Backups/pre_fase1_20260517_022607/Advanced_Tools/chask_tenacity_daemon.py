"""
chask_tenacity_daemon.py — Daemon Autonomo de Resolucion de Tareas
==================================================================
Bucle autonomo que recibe una tarea, la divide en pasos usando una IA gratuita,
ejecuta cada paso, verifica el resultado, reintenta si falla (con variacion de
enfoque), y avisa por Telegram cuando termina.

Uso:
  python chask_tenacity_daemon.py "Scrapea las 50 primeras URLs de este archivo"
  python chask_tenacity_daemon.py --file tarea.txt
  python chask_tenacity_daemon.py --resume  (retoma desde el ultimo checkpoint)
"""
import os
import sys
import io
import json
import time
import subprocess
import argparse
import traceback
from datetime import datetime

# Fix encoding
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

# Constantes
MAX_RETRIES_PER_STEP = 5
MAX_STEPS = 50
CHECKPOINT_FILE = os.path.join(TOOLS_DIR, "tenacity_checkpoint.json")
LOG_FILE = os.path.join(BASE_DIR, "tenacity_daemon.log")
PYTHON_EXE = sys.executable

# Importar dependencias del enjambre
try:
    import llm_router
    HAS_ROUTER = True
except ImportError:
    HAS_ROUTER = False

try:
    from chask_operational_memory import OperationalMemory
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    print(line)


def notify_telegram(message):
    """Envia notificacion por Telegram."""
    try:
        telegram_script = os.path.join(BASE_DIR, "antigravity_telegram.py")
        if os.path.exists(telegram_script):
            subprocess.run(
                [PYTHON_EXE, telegram_script, "send", message],
                capture_output=True, timeout=15
            )
    except:
        pass


def call_llm(prompt, max_retries=3):
    """Llama al router de IAs con fallback automatico."""
    if not HAS_ROUTER:
        log("[LLM] Router no disponible")
        return None

    for attempt in range(max_retries):
        try:
            result = llm_router.route(prompt, force_free=True)
            response = result.get("response", "")
            if response:
                return response
        except Exception as e:
            log(f"[LLM] Intento {attempt+1}/{max_retries} fallo: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    return None


def plan_task(task_description):
    """Usa LLM para dividir la tarea en pasos ejecutables."""
    prompt = f"""Eres un planificador de tareas autonomo. Divide esta tarea en pasos
EJECUTABLES desde una terminal Python/PowerShell en Windows.

TAREA: {task_description}

Responde SOLO con JSON valido (sin markdown, sin explicacion):
[
  {{"step": 1, "description": "descripcion concreta", "command": "comando a ejecutar", "verify": "como verificar que funciono"}},
  {{"step": 2, "description": "...", "command": "...", "verify": "..."}}
]

Reglas:
- Cada paso debe ser un comando ejecutable (python, powershell, pip, etc.)
- Maximo 10 pasos
- Si necesitas Python, escribe scripts inline con python -c "..."
- Incluye como verificar que cada paso funciono"""

    response = call_llm(prompt)
    if not response:
        return None

    try:
        start = response.find("[")
        end = response.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except json.JSONDecodeError as e:
        log(f"[PLAN] Error parseando plan: {e}")

    return None


def execute_step(step):
    """Ejecuta un paso del plan."""
    cmd = step.get("command", "")
    if not cmd:
        return {"success": False, "output": "Sin comando", "error": "Comando vacio"}

    log(f"[EXEC] Paso {step.get('step', '?')}: {step.get('description', '')[:60]}")
    log(f"[EXEC] Comando: {cmd[:100]}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=120, cwd=BASE_DIR,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0

        if success:
            log(f"[EXEC] OK (exit 0)")
        else:
            log(f"[EXEC] FALLO (exit {result.returncode}): {output[:200]}")

        return {
            "success": success,
            "output": output[:2000],
            "exit_code": result.returncode,
            "error": "" if success else output[:500]
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timeout (120s)"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}


def retry_step(step, error, attempt):
    """Pide al LLM que sugiera un enfoque alternativo."""
    prompt = f"""Un paso de mi tarea autonoma ha fallado. Necesito un comando alternativo.

PASO ORIGINAL: {step.get('description', '')}
COMANDO QUE FALLO: {step.get('command', '')}
ERROR: {error}
INTENTO: {attempt}/{MAX_RETRIES_PER_STEP}

Dame SOLO el nuevo comando corregido (una sola linea, sin explicacion, sin markdown).
Si el error es de dependencia, incluye la instalacion.
Si el error es de permisos, intenta un enfoque diferente."""

    new_cmd = call_llm(prompt)
    if new_cmd:
        # Limpiar el comando
        new_cmd = new_cmd.strip().strip("`").strip()
        if new_cmd.startswith("```"):
            new_cmd = new_cmd.split("\n")[1] if "\n" in new_cmd else new_cmd
        return new_cmd
    return None


def save_checkpoint(state):
    """Guarda el estado actual para poder retomar."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_checkpoint():
    """Carga el ultimo checkpoint."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def run_task(task_description, resume=False):
    """Bucle principal del daemon autonomo."""
    start_time = time.time()
    log("=" * 60)
    log("TENACITY DAEMON — INICIADO")
    log(f"Tarea: {task_description[:100]}")
    log("=" * 60)

    notify_telegram(f"[Tenacity] Iniciando tarea autonoma: {task_description[:80]}...")

    # Cargar o crear estado
    state = None
    if resume:
        state = load_checkpoint()
        if state:
            log(f"[RESUME] Retomando desde paso {state.get('current_step', 1)}")
        else:
            log("[RESUME] Sin checkpoint, empezando desde cero")

    if not state:
        # Planificar
        log("[PLAN] Dividiendo tarea en pasos...")
        steps = plan_task(task_description)
        if not steps:
            log("[PLAN] No se pudo generar plan. Abortando.")
            notify_telegram("[Tenacity] FALLO: No se pudo planificar la tarea.")
            return False

        log(f"[PLAN] Plan generado: {len(steps)} pasos")
        for s in steps:
            log(f"  #{s.get('step', '?')}: {s.get('description', '')[:60]}")

        state = {
            "task": task_description,
            "steps": steps,
            "current_step": 0,
            "results": [],
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        save_checkpoint(state)

    steps = state["steps"]
    current = state.get("current_step", 0)
    results = state.get("results", [])

    # Bucle de ejecucion
    for i in range(current, len(steps)):
        step = steps[i]
        state["current_step"] = i

        # Ejecutar con reintentos
        success = False
        for attempt in range(1, MAX_RETRIES_PER_STEP + 1):
            result = execute_step(step)

            if result["success"]:
                success = True
                results.append({
                    "step": step.get("step", i+1),
                    "description": step.get("description", ""),
                    "status": "ok",
                    "attempts": attempt,
                    "output": result["output"][:500]
                })
                break
            else:
                log(f"[RETRY] Paso {i+1} fallo (intento {attempt}/{MAX_RETRIES_PER_STEP})")
                if attempt < MAX_RETRIES_PER_STEP:
                    new_cmd = retry_step(step, result["error"], attempt)
                    if new_cmd:
                        log(f"[RETRY] Nuevo enfoque: {new_cmd[:100]}")
                        step["command"] = new_cmd
                    else:
                        log("[RETRY] LLM no pudo sugerir alternativa")
                        time.sleep(2)

        if not success:
            results.append({
                "step": step.get("step", i+1),
                "description": step.get("description", ""),
                "status": "failed",
                "attempts": MAX_RETRIES_PER_STEP,
                "error": result.get("error", "")[:500]
            })
            log(f"[ABORT] Paso {i+1} fallo tras {MAX_RETRIES_PER_STEP} intentos")

        state["results"] = results
        save_checkpoint(state)

    # Finalizar
    elapsed = round(time.time() - start_time, 1)
    total_ok = sum(1 for r in results if r["status"] == "ok")
    total_fail = sum(1 for r in results if r["status"] == "failed")

    state["status"] = "completed" if total_fail == 0 else "partial"
    state["finished_at"] = datetime.now().isoformat()
    state["elapsed_s"] = elapsed
    save_checkpoint(state)

    # Resumen
    log("=" * 60)
    log(f"TENACITY DAEMON — FINALIZADO")
    log(f"Resultado: {total_ok}/{len(steps)} pasos exitosos, {total_fail} fallidos")
    log(f"Tiempo: {elapsed}s")
    log("=" * 60)

    # Notificar por Telegram
    status_emoji = "[OK]" if total_fail == 0 else "[PARCIAL]"
    notify_telegram(
        f"[Tenacity] {status_emoji} Tarea completada: {task_description[:60]}\n"
        f"Resultado: {total_ok}/{len(steps)} pasos OK | {elapsed}s"
    )

    # Guardar en memoria Qdrant
    if HAS_MEMORY:
        try:
            mem = OperationalMemory()
            mem.log_operation(
                description=f"Tarea autonoma: {task_description[:100]}",
                approach=f"{len(steps)} pasos planificados, {total_ok} exitosos",
                result="success" if total_fail == 0 else "partial",
                keywords=["tenacity", "daemon", "autonomo"],
                project="tenacity"
            )
        except:
            pass

    return total_fail == 0


# ── CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enjambre Tenacity Daemon — Resolucion Autonoma")
    parser.add_argument("task", nargs="?", help="Descripcion de la tarea")
    parser.add_argument("--file", help="Leer tarea desde archivo")
    parser.add_argument("--resume", action="store_true", help="Retomar desde checkpoint")
    args = parser.parse_args()

    if args.resume:
        cp = load_checkpoint()
        if cp:
            run_task(cp["task"], resume=True)
        else:
            print("Sin checkpoint para retomar.")
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            run_task(f.read().strip())
    elif args.task:
        run_task(args.task)
    else:
        parser.print_help()
