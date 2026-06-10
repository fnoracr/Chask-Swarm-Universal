"""
evolutionary_memory.py — Pilar 3: Memoria Evolutiva con Mem0
=============================================================
Capa de memoria inteligente que:
- Extrae hechos automáticamente de las conversaciones
- Actualiza/elimina hechos obsoletos
- Usa Qdrant local como backend (ya existente)
- Funciona con el pool de IAs gratuitas (OpenRouter)
- Decadencia temporal: hechos pierden confianza si no se confirman

Uso:
  python evolutionary_memory.py add "Fernando prefiere Python sobre PowerShell"
  python evolutionary_memory.py search "preferencias de Fernando"
  python evolutionary_memory.py list
  python evolutionary_memory.py decay      (aplicar decadencia temporal)
  python evolutionary_memory.py confirm 5  (confirmar memoria #5)
"""
import os
import sys
import json
import math
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "agents_config.json")
MEMORY_STORE = os.path.join(BASE_DIR, "Configuracion", "evolutionary_memory.json")

# Intentar usar Mem0 con Qdrant
MEM0_AVAILABLE = False
mem0_instance = None

def _get_openrouter_key():
    """Obtiene la API key de OpenRouter del config."""
    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        return cfg.get("credentials", {}).get("openrouter_api_key", "")
    except:
        return ""

def init_mem0():
    """Inicializa Mem0 con Qdrant local y OpenRouter."""
    global MEM0_AVAILABLE, mem0_instance
    if mem0_instance is not None:
        return MEM0_AVAILABLE
    
    try:
        from mem0 import Memory
        
        api_key = _get_openrouter_key()
        
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "localhost",
                    "port": 6333,
                    "collection_name": "chask_evo_memory_768",
                    "embedding_model_dims": 768
                }
            },
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": "phi4-mini",
                    "ollama_base_url": "http://localhost:11434"
                }
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": "nomic-embed-text",
                    "ollama_base_url": "http://localhost:11434"
                }
            }
        }
        
        mem0_instance = Memory.from_config(config)
        MEM0_AVAILABLE = True
        print("[EvoMemory] Mem0 inicializado con Qdrant local")
        
    except Exception as e:
        MEM0_AVAILABLE = False
        print(f"[EvoMemory] Mem0 no disponible ({e}). Usando fallback JSON.")
    
    return MEM0_AVAILABLE


# ── FALLBACK: Memoria JSON simple ──
def _load_json_memory():
    if os.path.exists(MEMORY_STORE):
        with open(MEMORY_STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save_json_memory(data):
    with open(MEMORY_STORE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_memory(text, user_id="fernando"):
    """Almacena un hecho/preferencia."""
    if init_mem0() and MEM0_AVAILABLE:
        try:
            result = mem0_instance.add(text, user_id=user_id)
            print(f"[EvoMemory] Mem0: {result}")
            return True
        except Exception as e:
            print(f"[EvoMemory] Error Mem0: {e}")
    
    # Fallback JSON
    data = _load_json_memory()
    # Comprobar duplicados
    for entry in data:
        if text.lower().strip() == entry.get("text", "").lower().strip():
            print(f"[EvoMemory] Duplicado detectado, ignorando.")
            return False
    
    data.append({
        "id": len(data) + 1,
        "ts": datetime.now().isoformat(),
        "text": text,
        "user_id": user_id,
        "active": True,
        "confidence": 1.0,
        "access_count": 0,
        "last_accessed": datetime.now().isoformat(),
        "confirmed_count": 0
    })
    _save_json_memory(data)
    print(f"[EvoMemory] Memoria guardada (JSON fallback): {text[:60]}...")
    return True


def search_memory(query, user_id="fernando", limit=5):
    """Busca hechos relevantes."""
    if init_mem0() and MEM0_AVAILABLE:
        try:
            results = mem0_instance.search(query, filters={"user_id": user_id}, limit=limit)
            return [r.get("memory", r.get("text", "")) for r in results.get("results", [])]
        except Exception as e:
            print(f"[EvoMemory] Error buscando en Mem0: {e}")
    
    # Fallback: búsqueda con peso por confianza y frescura
    data = _load_json_memory()
    scored = []
    query_lower = query.lower()
    now = datetime.now()
    for entry in data:
        if not entry.get("active", True):
            continue
        if query_lower in entry.get("text", "").lower():
            conf = entry.get("confidence", 1.0)
            # Bonus por accesos recientes
            try:
                last = datetime.fromisoformat(entry.get("last_accessed", entry["ts"]))
                days_ago = (now - last).days
                freshness = max(0.1, 1.0 - (days_ago * 0.02))  # -2% por día
            except Exception:
                freshness = 0.5
            score = conf * freshness
            # Registrar acceso
            entry["access_count"] = entry.get("access_count", 0) + 1
            entry["last_accessed"] = now.isoformat()
            scored.append((score, entry["text"]))
    _save_json_memory(data)  # Guardar accesos actualizados
    scored.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored[:limit]]


def update_memory(old_fact, new_fact, user_id="fernando"):
    """Actualiza un hecho (marca el viejo como inactivo, añade el nuevo)."""
    data = _load_json_memory()
    for entry in data:
        if old_fact.lower() in entry.get("text", "").lower():
            entry["active"] = False
            entry["superseded_by"] = new_fact
            entry["superseded_at"] = datetime.now().isoformat()
    _save_json_memory(data)
    add_memory(new_fact, user_id)
    print(f"[EvoMemory] Hecho actualizado: '{old_fact[:30]}...' -> '{new_fact[:30]}...'")


def list_memories(user_id="fernando", active_only=True):
    """Lista todas las memorias."""
    data = _load_json_memory()
    results = []
    for entry in data:
        if entry.get("user_id") == user_id:
            if active_only and not entry.get("active", True):
                continue
            results.append(entry)
    return results


def apply_decay(half_life_days: int = 30):
    """
    Aplica decadencia temporal a todas las memorias.
    La confianza decae exponencialmente: conf *= 2^(-days/half_life)
    Memorias con confianza < 0.1 se desactivan.
    
    Args:
        half_life_days: Días para que la confianza se reduzca a la mitad
    """
    data = _load_json_memory()
    now = datetime.now()
    decayed = 0
    pruned = 0
    
    for entry in data:
        if not entry.get("active", True):
            continue
        
        # Calcular días desde último acceso
        try:
            last = datetime.fromisoformat(entry.get("last_accessed", entry["ts"]))
            days = (now - last).days
        except Exception:
            days = 30
        
        if days <= 0:
            continue
        
        # Decadencia exponencial
        old_conf = entry.get("confidence", 1.0)
        decay_factor = math.pow(2, -days / half_life_days)
        new_conf = round(old_conf * decay_factor, 4)
        
        # Bonus por confirmaciones (cada confirmación suma 0.1)
        confirmations = entry.get("confirmed_count", 0)
        new_conf = min(1.0, new_conf + (confirmations * 0.1))
        
        entry["confidence"] = new_conf
        
        if new_conf < 0.1:
            entry["active"] = False
            entry["pruned_at"] = now.isoformat()
            entry["prune_reason"] = "decay_below_threshold"
            pruned += 1
        elif new_conf < old_conf:
            decayed += 1
    
    _save_json_memory(data)
    print(f"[EvoMemory] Decay aplicado: {decayed} memorias decayeron, {pruned} desactivadas.")
    return {"decayed": decayed, "pruned": pruned}


def confirm_memory(memory_id: int):
    """
    Confirma una memoria (refuerza su confianza).
    Usar cuando Fernando menciona o valida un hecho existente.
    """
    data = _load_json_memory()
    for entry in data:
        if entry.get("id") == memory_id:
            entry["confidence"] = min(1.0, entry.get("confidence", 0.5) + 0.2)
            entry["confirmed_count"] = entry.get("confirmed_count", 0) + 1
            entry["last_accessed"] = datetime.now().isoformat()
            _save_json_memory(data)
            print(f"[EvoMemory] Memoria #{memory_id} confirmada (conf={entry['confidence']})")
            return True
    print(f"[EvoMemory] Memoria #{memory_id} no encontrada.")
    return False


def get_stats() -> dict:
    """Devuelve estadísticas del sistema de memoria."""
    data = _load_json_memory()
    active = [e for e in data if e.get("active", True)]
    inactive = [e for e in data if not e.get("active", True)]
    avg_conf = sum(e.get("confidence", 1.0) for e in active) / max(len(active), 1)
    return {
        "total": len(data),
        "active": len(active),
        "inactive": len(inactive),
        "avg_confidence": round(avg_conf, 3),
        "high_confidence": len([e for e in active if e.get("confidence", 1.0) >= 0.7]),
        "low_confidence": len([e for e in active if e.get("confidence", 1.0) < 0.3])
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python evolutionary_memory.py [add|search|list|update|decay|confirm|stats] [args...]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "add" and len(sys.argv) >= 3:
        add_memory(" ".join(sys.argv[2:]))
    elif cmd == "search" and len(sys.argv) >= 3:
        results = search_memory(" ".join(sys.argv[2:]))
        for r in results:
            print(f"  -> {r}")
        if not results:
            print("  Sin resultados.")
    elif cmd == "list":
        memories = list_memories()
        print(f"\nMEMORIAS ACTIVAS ({len(memories)} total):\n")
        for m in memories:
            conf = m.get('confidence', 1.0)
            bar = '#' * int(conf * 10)
            print(f"  #{m['id']} [{m['ts'][:10]}] (conf={conf:.2f}) {bar:10s} {m['text']}")
    elif cmd == "update" and len(sys.argv) >= 4:
        update_memory(sys.argv[2], sys.argv[3])
    elif cmd == "decay":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        apply_decay(days)
    elif cmd == "confirm" and len(sys.argv) >= 3:
        confirm_memory(int(sys.argv[2]))
    elif cmd == "stats":
        stats = get_stats()
        print(f"\nESTADISTICAS DE MEMORIA:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print(f"Comando desconocido: {cmd}")
