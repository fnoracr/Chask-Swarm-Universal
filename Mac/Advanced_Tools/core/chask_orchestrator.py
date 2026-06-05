"""
chask_orchestrator.py — Orquestacion Multi-Agente con Grafos de Estado
======================================================================
Descompone tareas en sub-tareas, las despacha a multiples IAs
en paralelo via llm_router, consolida resultados y verifica.

Protocolo Hive Mind: Alpha->Beta(paralelo)->Gamma->Delta
Con grafos de estado, checkpointing, map-reduce y supervisor-worker.
"""
import os
import sys
import json
import time
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAX_AGENTS = 3  # Agentes paralelos por defecto


class Orchestrator:
    def __init__(self, max_agents=MAX_AGENTS):
        self.max_agents = max_agents
        self.results = []
        self.log_lines = []

    def _log(self, msg):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        self.log_lines.append(line)
        print(line)

    # ═══════════════════════════════════════════════════════
    # ALPHA: Descomponer tarea en sub-tareas
    # ═══════════════════════════════════════════════════════
    def decompose(self, task, n_subtasks=None):
        """Usa LLM para dividir una tarea en sub-tareas independientes."""
        from llm_router import route

        n = n_subtasks or self.max_agents
        prompt = (
            f"Descompone la siguiente tarea en exactamente {n} sub-tareas independientes "
            f"que puedan ejecutarse en paralelo. Cada sub-tarea debe ser autocontenida.\n\n"
            f"Tarea: {task}\n\n"
            f"Responde SOLO con un JSON array de strings, sin explicacion:\n"
            f'["subtarea 1", "subtarea 2", "subtarea 3"]'
        )

        result = route(prompt, force_free=True)
        if result.get("response"):
            try:
                # Extraer JSON del response
                text = result["response"]
                start = text.find("[")
                end = text.rfind("]") + 1
                if start >= 0 and end > start:
                    subtasks = json.loads(text[start:end])
                    self._log(f"[ALPHA] Tarea descompuesta en {len(subtasks)} sub-tareas")
                    return subtasks
            except json.JSONDecodeError:
                pass

        # Fallback: dividir manualmente
        self._log("[ALPHA] Fallback: division manual de la tarea")
        return [task]

    # ═══════════════════════════════════════════════════════
    # BETA: Despachar sub-tareas en paralelo
    # ═══════════════════════════════════════════════════════
    def _execute_subtask(self, subtask, agent_id):
        """Ejecuta una sub-tarea en un hilo con el LLM router."""
        from llm_router import route

        self._log(f"[BETA-{agent_id}] Iniciando: {subtask[:60]}...")
        t0 = time.time()

        try:
            result = route(subtask, force_free=True)
            elapsed = time.time() - t0
            response = result.get("response", "")
            engine = result.get("engine", "unknown")

            self._log(f"[BETA-{agent_id}] Completado en {elapsed:.1f}s via {engine}")
            return {
                "agent_id": agent_id,
                "subtask": subtask,
                "response": response or "(sin respuesta)",
                "engine": engine,
                "elapsed_s": round(elapsed, 2),
                "success": bool(response)
            }
        except Exception as e:
            self._log(f"[BETA-{agent_id}] ERROR: {e}")
            return {
                "agent_id": agent_id,
                "subtask": subtask,
                "response": f"Error: {str(e)}",
                "engine": "error",
                "elapsed_s": round(time.time() - t0, 2),
                "success": False
            }

    def dispatch(self, subtasks):
        """Ejecuta sub-tareas en paralelo con ThreadPoolExecutor."""
        self._log(f"[BETA] Despachando {len(subtasks)} sub-tareas a {self.max_agents} agentes...")

        with ThreadPoolExecutor(max_workers=self.max_agents) as executor:
            futures = []
            for i, subtask in enumerate(subtasks):
                future = executor.submit(self._execute_subtask, subtask, i + 1)
                futures.append(future)

            self.results = [f.result() for f in futures]

        ok = sum(1 for r in self.results if r["success"])
        self._log(f"[BETA] Completado: {ok}/{len(subtasks)} exitosos")
        return self.results

    # ═══════════════════════════════════════════════════════
    # GAMMA: Consolidar resultados
    # ═══════════════════════════════════════════════════════
    def consolidate(self, original_task):
        """Reune todos los resultados y genera sintesis."""
        from llm_router import route

        if not self.results:
            return "Sin resultados para consolidar."

        parts = []
        for r in self.results:
            if r["success"]:
                parts.append(f"## Sub-tarea: {r['subtask']}\n{r['response'][:500]}")

        all_parts = "\n\n---\n\n".join(parts)
        prompt = (
            f"Tarea original: {original_task}\n\n"
            f"Los siguientes son resultados parciales de multiples agentes:\n\n"
            f"{all_parts}\n\n"
            f"Sintetiza todos los resultados en una respuesta unificada y coherente."
        )

        result = route(prompt, force_free=True)
        synthesis = result.get("response", "(consolidacion fallida)")
        self._log(f"[GAMMA] Sintesis generada ({len(synthesis)} chars) via {result.get('engine', '?')}")
        return synthesis

    # ═══════════════════════════════════════════════════════
    # DELTA: Verificar resultado (anti-drift)
    # ═══════════════════════════════════════════════════════
    def verify(self, original_task, synthesis):
        """Verifica que la sintesis responde al objetivo original."""
        try:
            from chask_anti_drift import AntiDrift
            ad = AntiDrift()
            ad.set_objective(original_task)
            check = ad.check_alignment(synthesis[:500])
            self._log(f"[DELTA] Verificacion: {check['status']} (distancia: {check['distance']})")
            return check
        except Exception as e:
            self._log(f"[DELTA] Error en verificacion: {e}")
            return {"status": "SKIP", "distance": 0, "message": str(e)}

    # ═══════════════════════════════════════════════════════
    # EJECUTAR PIPELINE COMPLETO
    # ═══════════════════════════════════════════════════════
    def run(self, task, n_subtasks=None):
        """Pipeline completo: Alpha→Beta→Gamma→Delta."""
        self._log("=" * 60)
        self._log(f"[HIVE MIND] Tarea: {task[:80]}...")
        t0 = time.time()

        # Alpha: Descomponer
        subtasks = self.decompose(task, n_subtasks)

        # Beta: Ejecutar en paralelo
        results = self.dispatch(subtasks)

        # Gamma: Consolidar
        synthesis = self.consolidate(task)

        # Delta: Verificar
        verification = self.verify(task, synthesis)

        elapsed = time.time() - t0
        self._log(f"[HIVE MIND] Pipeline completado en {elapsed:.1f}s")

        # Registrar en Qdrant
        try:
            from chask_operational_memory import OperationalMemory
            mem = OperationalMemory()
            mem.log_operation(
                description=f"Hive Mind: {task[:100]}",
                approach=f"{len(subtasks)} sub-tareas paralelas",
                result="success" if verification.get("status") != "RED" else "drift_detected",
                keywords=["hive_mind", "multi_agent", "orchestrator"],
                project="orchestrator"
            )
        except:
            pass

        return {
            "task": task,
            "subtasks": subtasks,
            "results": results,
            "synthesis": synthesis,
            "verification": verification,
            "elapsed_s": round(elapsed, 2),
            "log": self.log_lines
        }

    def get_report(self, run_result):
        """Genera un resumen legible del resultado."""
        r = run_result
        lines = [
            f"HIVE MIND REPORT",
            f"Tarea: {r['task'][:100]}",
            f"Sub-tareas: {len(r['subtasks'])}",
            f"Tiempo total: {r['elapsed_s']}s",
            f"Verificacion: {r['verification'].get('status', '?')}",
            f"",
            f"SINTESIS:",
            r['synthesis'][:1000]
        ]
        return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════
# GRAFO DE ESTADO — Orquestacion avanzada con checkpointing
# ═══════════════════════════════════════════════════════════════

CHECKPOINTS_DIR = Path(BASE) / "orchestrator_checkpoints"


class StateGraph:
    """
    Grafo dirigido de estado para orquestacion avanzada.
    Cada nodo es una funcion que transforma el estado.
    Soporta: checkpointing, bifurcaciones, map-reduce, supervisor.
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.nodes = {}       # {name: callable}
        self.edges = {}       # {from_node: [to_node, ...]}
        self.state = {}       # Estado global del grafo
        self.history = []     # Historial de ejecucion
        self.checkpoint_id = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:8]
    
    def add_node(self, name: str, func: callable):
        """Registra un nodo (funcion) en el grafo."""
        self.nodes[name] = func
        if name not in self.edges:
            self.edges[name] = []
    
    def add_edge(self, from_node: str, to_node: str):
        """Conecta dos nodos con una transicion."""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
    
    def set_state(self, key: str, value):
        """Actualiza el estado global (delta merge)."""
        self.state[key] = value
    
    def checkpoint(self):
        """Guarda el estado actual a disco para recuperacion."""
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        cp = {
            "name": self.name,
            "state": self.state,
            "history": self.history,
            "timestamp": datetime.now().isoformat()
        }
        path = CHECKPOINTS_DIR / f"cp_{self.checkpoint_id}.json"
        path.write_text(json.dumps(cp, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return str(path)
    
    @classmethod
    def restore(cls, checkpoint_path: str) -> 'StateGraph':
        """Restaura un grafo desde un checkpoint."""
        data = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
        graph = cls(data["name"])
        graph.state = data["state"]
        graph.history = data["history"]
        return graph
    
    def run(self, start_node: str, initial_state: dict = None):
        """Ejecuta el grafo desde un nodo inicial."""
        if initial_state:
            self.state.update(initial_state)
        
        current = start_node
        visited = set()
        max_iterations = 50  # Safety limit
        
        while current and max_iterations > 0:
            if current not in self.nodes:
                break
            
            max_iterations -= 1
            print(f"[Graph] Ejecutando nodo: {current}")
            
            # Execute node
            try:
                result = self.nodes[current](self.state)
                if isinstance(result, dict):
                    self.state.update(result)
                
                self.history.append({
                    "node": current,
                    "timestamp": datetime.now().isoformat(),
                    "state_keys": list(self.state.keys())
                })
                
                # Checkpoint after each node
                self.checkpoint()
                
            except Exception as e:
                self.history.append({
                    "node": current,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                self.checkpoint()
                print(f"[Graph] Error en nodo {current}: {e}")
                break
            
            # Get next node(s)
            next_nodes = self.edges.get(current, [])
            
            if not next_nodes:
                break
            
            # If multiple edges, check for conditional routing
            if len(next_nodes) == 1:
                current = next_nodes[0]
            else:
                # Use state to determine next node (conditional edge)
                route_key = f"_route_{current}"
                chosen = self.state.get(route_key, next_nodes[0])
                current = chosen if chosen in next_nodes else next_nodes[0]
            
            # Cycle detection
            visit_key = f"{current}_{max_iterations}"
            if visit_key in visited:
                break
            visited.add(visit_key)
        
        return self.state


def map_reduce(task: str, mapper_count: int = 3) -> dict:
    """
    Map-Reduce pattern: divide task, process in parallel, aggregate.
    """
    orch = Orchestrator(max_agents=mapper_count)
    
    # MAP: divide and dispatch
    subtasks = orch.decompose(task, mapper_count)
    results = orch.dispatch(subtasks)
    
    # REDUCE: consolidate
    synthesis = orch.consolidate(task)
    
    return {
        "task": task,
        "mapped": len(subtasks),
        "successful": sum(1 for r in results if r["success"]),
        "synthesis": synthesis
    }


def supervisor_worker(task: str, workers: int = 3) -> dict:
    """
    Supervisor-Worker pattern: supervisor decomposes and manages workers,
    reviews results, and re-dispatches failed tasks.
    """
    from llm_router import route
    
    orch = Orchestrator(max_agents=workers)
    
    # Supervisor: decompose
    subtasks = orch.decompose(task, workers)
    
    # Workers: execute
    results = orch.dispatch(subtasks)
    
    # Supervisor: review failures and retry
    failed = [r for r in results if not r["success"]]
    if failed:
        orch._log(f"[SUPERVISOR] {len(failed)} tareas fallaron, reintentando...")
        retry_tasks = [r["subtask"] for r in failed]
        retry_results = orch.dispatch(retry_tasks)
        
        # Merge results
        for r in retry_results:
            for i, orig in enumerate(results):
                if orig["subtask"] == r["subtask"]:
                    results[i] = r
                    break
    
    # Supervisor: final synthesis
    synthesis = orch.consolidate(task)
    verification = orch.verify(task, synthesis)
    
    return {
        "task": task,
        "workers": workers,
        "retries": len(failed),
        "synthesis": synthesis,
        "verification": verification,
        "results": results
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1] if sys.argv[1].startswith("--") else None
        task = " ".join(sys.argv[2:] if mode else sys.argv[1:])
        
        if mode == "--map-reduce":
            print("[MAP-REDUCE]")
            result = map_reduce(task)
            print(f"\nMapped: {result['mapped']}, Successful: {result['successful']}")
            print(f"\nSYNTHESIS:\n{result['synthesis'][:1000]}")
        
        elif mode == "--supervisor":
            print("[SUPERVISOR-WORKER]")
            result = supervisor_worker(task)
            print(f"\nWorkers: {result['workers']}, Retries: {result['retries']}")
            print(f"Verification: {result['verification'].get('status', '?')}")
            print(f"\nSYNTHESIS:\n{result['synthesis'][:1000]}")
        
        else:
            orch = Orchestrator()
            result = orch.run(task)
            print("\n" + orch.get_report(result))
    else:
        print("Uso:")
        print("  python chask_orchestrator.py <tarea>              (Hive Mind pipeline)")
        print("  python chask_orchestrator.py --map-reduce <tarea> (Map-Reduce pattern)")
        print("  python chask_orchestrator.py --supervisor <tarea> (Supervisor-Worker)")

