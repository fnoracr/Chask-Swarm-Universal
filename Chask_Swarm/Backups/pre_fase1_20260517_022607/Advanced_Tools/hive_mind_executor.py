"""
hive_mind_executor.py — Delegación Multi-Modelo en Paralelo
============================================================
Divide tareas complejas en subtareas y las ejecuta en paralelo
usando distintos agentes del pool LLM.

Flujo:
  1. Alpha: Analiza la tarea y genera plan con subtareas
  2. Beta:  Ejecuta cada subtarea en paralelo (cada una con un agente distinto)
  3. Gamma: Agrega los resultados en una respuesta unificada
  4. Delta: Auto-evalúa la calidad del resultado

Uso:
  python hive_mind_executor.py "Diseña un sistema de notificaciones para la app Chask"
  python hive_mind_executor.py --file tarea.txt
"""
import asyncio
import json
import os
import sys
import time
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVANCED_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ADVANCED_DIR)

try:
    import llm_router
    ROUTER_OK = True
except ImportError:
    ROUTER_OK = False

LOG_FILE = os.path.join(BASE_DIR, "hive_mind_log.json")


# ── Fase Alpha: Planificación ──────────────────────────────────────
def alpha_plan(task: str, max_subtasks: int = 4) -> list[dict]:
    """
    Analiza la tarea y genera un plan de subtareas paralelas.
    Returns: [{"id": 1, "subtask": "...", "agent": "viper|ghost|hunter|oracle"}]
    """
    if not ROUTER_OK:
        return [{"id": 1, "subtask": task, "agent": "ghost"}]

    prompt = f"""Eres un planificador de tareas. Divide esta tarea en {max_subtasks} subtareas
que puedan ejecutarse EN PARALELO por distintos agentes.

TAREA: {task}

AGENTES DISPONIBLES:
- viper: Arquitecto (diseño, diagramas, decisiones técnicas)
- ghost: Developer (código, implementación, debugging)
- hunter: Growth & Sales (marketing, ventas, copy, estrategia comercial)
- oracle: Compliance & Data (datos, análisis, regulación, documentación)

Responde SOLO con JSON válido, sin markdown ni explicación:
[
  {{"id": 1, "subtask": "descripción concreta", "agent": "nombre_agente"}},
  {{"id": 2, "subtask": "descripción concreta", "agent": "nombre_agente"}}
]

Reglas:
- Cada subtarea debe ser autocontenida (no depender de otra)
- Asigna el agente más adecuado para cada una
- Máximo {max_subtasks} subtareas
- Si la tarea es simple, devuelve solo 1 subtarea"""

    try:
        result = llm_router.route(prompt, force_free=True)
        response = result.get("response", "")
        # Extraer JSON del response
        start = response.find("[")
        end = response.rfind("]") + 1
        if start >= 0 and end > start:
            subtasks = json.loads(response[start:end])
            return subtasks
    except Exception as e:
        print(f"  [Alpha] Error planificando: {e}")

    # Fallback: tarea única
    return [{"id": 1, "subtask": task, "agent": "ghost"}]


# ── Fase Beta: Ejecución Paralela ──────────────────────────────────
def _execute_subtask(subtask: dict, original_task: str) -> dict:
    """Ejecuta una subtarea individual con el agente asignado."""
    agent = subtask.get("agent", "ghost")
    sub = subtask.get("subtask", "")
    sid = subtask.get("id", 0)

    prompt = f"""Eres parte de un equipo Hive Mind resolviendo una tarea mayor.

TAREA PRINCIPAL: {original_task}
TU SUBTAREA (#{sid}): {sub}

Resuelve TU subtarea de forma completa y concisa. Tu respuesta será combinada
con las de otros agentes para formar la respuesta final.
Enfócate solo en tu parte. Sé concreto y directo."""

    start = time.time()
    try:
        result = llm_router.route(prompt, agent=agent, force_free=True)
        elapsed = round(time.time() - start, 1)
        return {
            "id": sid,
            "agent": agent,
            "subtask": sub,
            "response": result.get("response", ""),
            "model": result.get("model_used", "unknown"),
            "time_s": elapsed,
            "status": "ok"
        }
    except Exception as e:
        return {
            "id": sid,
            "agent": agent,
            "subtask": sub,
            "response": f"[ERROR] {e}",
            "model": "error",
            "time_s": round(time.time() - start, 1),
            "status": "error"
        }


def beta_execute(subtasks: list[dict], original_task: str, max_workers: int = 4) -> list[dict]:
    """Ejecuta todas las subtareas en paralelo."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_execute_subtask, st, original_task): st
            for st in subtasks
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r["id"])
    return results


# ── Fase Gamma: Agregación ─────────────────────────────────────────
def gamma_aggregate(results: list[dict], original_task: str) -> str:
    """Agrega los resultados parciales en una respuesta unificada."""
    if not ROUTER_OK:
        return "\n\n".join(r["response"] for r in results)

    parts = "\n\n".join(
        f"=== Subtarea #{r['id']} ({r['agent']}) ===\n{r['response']}"
        for r in results
    )

    prompt = f"""Eres un integrador. Combina estas respuestas parciales de distintos agentes
en UNA respuesta unificada, coherente y completa.

TAREA ORIGINAL: {original_task}

RESPUESTAS PARCIALES:
{parts}

Genera la respuesta final integrando lo mejor de cada agente.
Elimina redundancias. Mantén la estructura lógica.
NO menciones que son respuestas de distintos agentes."""

    try:
        result = llm_router.route(prompt, force_free=True)
        return result.get("response", parts)
    except Exception:
        return parts


# ── Fase Delta: Auto-Evaluación ────────────────────────────────────
def delta_evaluate(task: str, final_response: str) -> dict:
    """Auto-evalúa la calidad del resultado."""
    if not ROUTER_OK:
        return {"score": 0, "feedback": "Router no disponible"}

    prompt = f"""Evalúa esta respuesta del 1 al 10 y da feedback breve.

TAREA: {task}

RESPUESTA:
{final_response[:2000]}

Responde SOLO con JSON:
{{"score": N, "feedback": "una línea de feedback"}}"""

    try:
        result = llm_router.route(prompt, force_free=True)
        resp = result.get("response", "")
        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(resp[start:end])
    except Exception:
        pass
    return {"score": 0, "feedback": "auto-eval no disponible"}


# ── Orquestador Principal ─────────────────────────────────────────
def execute_hive_mind(task: str, max_subtasks: int = 4, evaluate: bool = True) -> dict:
    """
    Ejecuta el ciclo completo Hive Mind.
    Returns: {
        "task": str,
        "plan": list,
        "results": list,
        "final": str,
        "evaluation": dict,
        "total_time_s": float
    }
    """
    start = time.time()
    print(f"\n{'='*60}")
    print(f"  HIVE MIND — Ejecutando tarea compleja")
    print(f"{'='*60}")
    print(f"  Tarea: {task[:80]}...")

    # Alpha
    print(f"\n  [Alpha] Planificando...")
    subtasks = alpha_plan(task, max_subtasks)
    print(f"  [Alpha] Plan: {len(subtasks)} subtareas")
    for st in subtasks:
        print(f"    #{st['id']} [{st['agent']}] {st['subtask'][:60]}")

    # Beta
    print(f"\n  [Beta] Ejecutando {len(subtasks)} subtareas en paralelo...")
    results = beta_execute(subtasks, task)
    for r in results:
        status = "OK" if r["status"] == "ok" else "ERR"
        print(f"    #{r['id']} [{r['agent']}] {status} ({r['time_s']}s, {r['model']})")

    # Gamma
    print(f"\n  [Gamma] Agregando resultados...")
    final = gamma_aggregate(results, task)
    print(f"  [Gamma] Respuesta final: {len(final)} chars")

    # Delta
    evaluation = {}
    if evaluate:
        print(f"\n  [Delta] Auto-evaluando...")
        evaluation = delta_evaluate(task, final)
        print(f"  [Delta] Score: {evaluation.get('score', '?')}/10 — {evaluation.get('feedback', '')}")

    total = round(time.time() - start, 1)
    print(f"\n  Total: {total}s")
    print(f"{'='*60}\n")

    # Log
    log_entry = {
        "ts": datetime.now().isoformat(),
        "task": task,
        "subtasks": len(subtasks),
        "agents": [r["agent"] for r in results],
        "models": [r["model"] for r in results],
        "score": evaluation.get("score", 0),
        "total_time_s": total
    }
    _save_log(log_entry)

    return {
        "task": task,
        "plan": subtasks,
        "results": results,
        "final": final,
        "evaluation": evaluation,
        "total_time_s": total
    }


def _save_log(entry: dict):
    """Guarda log de ejecución."""
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append(entry)
    logs = logs[-50:]  # Mantener últimas 50
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


# ── CLI ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python hive_mind_executor.py \"tarea compleja\"")
        print("     python hive_mind_executor.py --file tarea.txt")
        sys.exit(1)

    if sys.argv[1] == "--file":
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            task = f.read().strip()
    else:
        task = " ".join(sys.argv[1:])

    result = execute_hive_mind(task)
    print("\n=== RESPUESTA FINAL ===\n")
    print(result["final"])
