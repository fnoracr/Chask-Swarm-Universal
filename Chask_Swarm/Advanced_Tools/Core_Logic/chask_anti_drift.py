"""
chask_anti_drift.py — Sistema Anti-Desviacion
=============================================
Evita que Enjambre se desvie del objetivo original en tareas largas.
Usa comparacion de embeddings para detectar drift.
"""
import os
import sys
import json
import math
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anti_drift_state.json")
YELLOW_THRESHOLD = 0.4  # Distancia coseno para alerta amarilla
RED_THRESHOLD = 0.6     # Distancia coseno para alerta roja


def _get_embedding(text):
    """Embedding via Ollama."""
    import urllib.request
    data = json.dumps({"model": "nomic-embed-text", "prompt": text[:2000]}).encode()
    req = urllib.request.Request("http://localhost:11434/api/embeddings",
                                 data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())["embedding"]


def _cosine_distance(a, b):
    """Distancia coseno entre dos vectores (0 = identicos, 1 = opuestos)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    similarity = dot / (norm_a * norm_b)
    return 1.0 - similarity


class AntiDrift:
    def __init__(self):
        self.state = self._load()

    def _load(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"objective": None, "objective_embedding": None, "checkpoints": [], "alerts": []}

    def _save(self):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def set_objective(self, text):
        """Registra el objetivo original de la tarea."""
        embedding = _get_embedding(text)
        self.state = {
            "objective": text,
            "objective_embedding": embedding,
            "set_at": datetime.now().isoformat(),
            "checkpoints": [],
            "alerts": []
        }
        self._save()
        return {"ok": True, "objective": text[:100]}

    def check_alignment(self, current_action):
        """Verifica si la accion actual esta alineada con el objetivo."""
        if not self.state.get("objective_embedding"):
            return {"status": "no_objective", "distance": 0}

        current_embedding = _get_embedding(current_action)
        distance = _cosine_distance(self.state["objective_embedding"], current_embedding)

        result = {
            "distance": round(distance, 4),
            "objective": self.state["objective"][:80],
            "current": current_action[:80],
            "timestamp": datetime.now().isoformat()
        }

        if distance >= RED_THRESHOLD:
            result["status"] = "RED"
            result["message"] = f"ALERTA ROJA: Desviacion critica ({distance:.2f}). Reencauzar."
            self.state["alerts"].append(result)
        elif distance >= YELLOW_THRESHOLD:
            result["status"] = "YELLOW"
            result["message"] = f"Alerta amarilla: Posible desviacion ({distance:.2f})."
            self.state["alerts"].append(result)
        else:
            result["status"] = "GREEN"
            result["message"] = f"Alineado ({distance:.2f})."

        self._save()
        return result

    def checkpoint(self, step_number, summary):
        """Registra un checkpoint y verifica alineacion."""
        check = self.check_alignment(summary)
        check["step"] = step_number
        self.state["checkpoints"].append(check)
        self._save()
        return check

    def get_status(self):
        """Estado actual del anti-drift."""
        return {
            "objective": (self.state.get("objective") or "")[:100],
            "checkpoints": len(self.state.get("checkpoints", [])),
            "alerts": len(self.state.get("alerts", [])),
            "last_check": self.state["checkpoints"][-1] if self.state.get("checkpoints") else None
        }

    def clear(self):
        """Limpia el estado (nueva tarea)."""
        self.state = {"objective": None, "objective_embedding": None, "checkpoints": [], "alerts": []}
        self._save()


if __name__ == "__main__":
    ad = AntiDrift()
    if len(sys.argv) > 2 and sys.argv[1] == "set":
        print(json.dumps(ad.set_objective(sys.argv[2]), indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "check":
        print(json.dumps(ad.check_alignment(sys.argv[2]), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(ad.get_status(), indent=2))
    else:
        print("Uso: python chask_anti_drift.py set <objetivo> | check <accion> | status")
