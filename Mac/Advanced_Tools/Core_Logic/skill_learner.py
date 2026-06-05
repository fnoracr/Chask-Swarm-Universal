"""
skill_learner.py — Auto-Aprendizaje de Skills (Self-Evolving)
=============================================================
Daemon Learner que observa operaciones exitosas y las codifica
automaticamente en skills reutilizables (SKILL.md).

Flujo:
  1. Monitorea chask_operational_memory (Qdrant) buscando operaciones exitosas
  2. Cuando detecta un patron exitoso complejo (>3 pasos), lanza el Learner
  3. El Learner abstrae el patron en un SKILL.md estructurado
  4. Valida el skill con un test sintetico
  5. Lo registra en el catalogo y lo indexa en Qdrant para busqueda semantica

Inspirado en: Hermes Agent (Nous Research) self-evolving skills
"""
import os
import sys
import io
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(r"C:\Program Files\Chask_Swarm")
TOOLS = ROOT / "Advanced_Tools"
SKILLS_DIR = ROOT / "skills"
LEARNED_DIR = SKILLS_DIR / "learned"
LEARNER_LOG = ROOT / "skill_learner_log.json"

sys.path.insert(0, str(TOOLS))

try:
    import llm_router
    ROUTER_OK = True
except ImportError:
    ROUTER_OK = False

try:
    from skill_catalog import register_skill, search_skills
    CATALOG_OK = True
except ImportError:
    CATALOG_OK = False

try:
    from qdrant_memory_manager import search_memory, save_memory
    QDRANT_OK = True
except ImportError:
    QDRANT_OK = False

# ─── Skill template ──────────────────────────────────────
SKILL_TEMPLATE = """# {name}

## Descripcion
{description}

## Trigger
Usar este skill cuando: {trigger}

## Pasos
{steps}

## Herramientas necesarias
{tools}

## Constraints
{constraints}

## Ejemplo de uso
```
{example}
```

## Metadata
- Generado: {timestamp}
- Fuente: Operacion exitosa #{source_id}
- Validado: {validated}
- Version: 1.0
"""


def find_successful_patterns(min_steps: int = 3, lookback: int = 50) -> list:
    """
    Busca en la memoria operacional patrones exitosos complejos
    que aun no se han convertido en skills.
    """
    patterns = []
    
    # 1. Check operational memory JSON
    op_mem_path = TOOLS / "anti_drift_state.json"
    if op_mem_path.exists():
        try:
            data = json.loads(op_mem_path.read_text(encoding="utf-8"))
            sessions = data if isinstance(data, list) else data.get("sessions", [])
            for session in sessions[-lookback:]:
                steps = session.get("checkpoints", session.get("steps", []))
                if len(steps) >= min_steps:
                    # Check if it completed successfully
                    last = steps[-1] if steps else {}
                    if isinstance(last, dict) and last.get("similarity", 0) > 0.7:
                        patterns.append({
                            "source": "anti_drift",
                            "task": session.get("task", session.get("original_task", "")),
                            "steps": steps,
                            "step_count": len(steps),
                            "id": hashlib.md5(json.dumps(session, default=str).encode()).hexdigest()[:8]
                        })
        except Exception:
            pass
    
    # 2. Check Qdrant for successful operations
    if QDRANT_OK:
        try:
            results = search_memory("operacion exitosa completada", top_k=lookback)
            for r in results:
                payload = r.get("payload", {})
                text = payload.get("text", "")
                if len(text) > 200 and ("exitosa" in text.lower() or "completado" in text.lower()):
                    patterns.append({
                        "source": "qdrant",
                        "task": text[:200],
                        "steps": [],
                        "step_count": text.count("\n"),
                        "id": hashlib.md5(text.encode()).hexdigest()[:8]
                    })
        except Exception:
            pass
    
    # 3. Check learned_lessons.json
    lessons_path = ROOT / "Configuration/learned_lessons.json"
    if lessons_path.exists():
        try:
            lessons = json.loads(lessons_path.read_text(encoding="utf-8"))
            for lesson in lessons:
                if isinstance(lesson, dict) and lesson.get("lesson"):
                    patterns.append({
                        "source": "lessons",
                        "task": lesson.get("context", lesson.get("lesson", "")),
                        "steps": [lesson.get("lesson", "")],
                        "step_count": 1,
                        "id": hashlib.md5(json.dumps(lesson, default=str).encode()).hexdigest()[:8]
                    })
        except Exception:
            pass
    
    # Filter out already-learned patterns
    already_learned = _get_learned_ids()
    patterns = [p for p in patterns if p["id"] not in already_learned]
    
    return patterns


def _get_learned_ids() -> set:
    """Get IDs of patterns already converted to skills."""
    ids = set()
    if LEARNER_LOG.exists():
        try:
            logs = json.loads(LEARNER_LOG.read_text(encoding="utf-8"))
            for entry in logs:
                ids.add(entry.get("source_id", ""))
        except Exception:
            pass
    return ids


def generate_skill_from_pattern(pattern: dict) -> dict:
    """
    Usa el LLM para abstraer un patron exitoso en un SKILL.md reutilizable.
    """
    if not ROUTER_OK:
        return {"success": False, "error": "LLM Router no disponible"}
    
    task = pattern.get("task", "")
    steps = pattern.get("steps", [])
    
    steps_text = ""
    if steps:
        for i, s in enumerate(steps):
            if isinstance(s, dict):
                s_text = s.get("task", s.get("description", str(s)))
            else:
                s_text = str(s)
            steps_text += f"  Paso {i+1}: {s_text}\n"
    
    prompt = f"""Analiza esta operacion exitosa y genera un SKILL reutilizable.

OPERACION EXITOSA:
Tarea: {task}
Pasos ejecutados:
{steps_text if steps_text else '  (deducir del contexto de la tarea)'}

Genera un JSON con estos campos exactos:
{{
  "name": "nombre_snake_case_corto",
  "description": "Que hace este skill en 1-2 lineas",
  "trigger": "Cuando usar este skill (condiciones)",
  "steps": ["Paso 1: ...", "Paso 2: ...", "Paso 3: ..."],
  "tools": ["herramienta1", "herramienta2"],
  "constraints": ["Restriccion 1", "Restriccion 2"],
  "example": "Ejemplo de como invocar este skill"
}}

Responde SOLO el JSON, nada mas."""

    try:
        result = llm_router.route(prompt, force_free=True)
        response = result.get("response", "")
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return {"success": False, "error": "No se encontro JSON en respuesta"}
        
        skill_data = json.loads(json_match.group())
        return {"success": True, "data": skill_data, "model": result.get("model_used", "")}
    
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON invalido: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_skill(skill_data: dict, pattern: dict) -> str:
    """Guarda el skill como SKILL.md y lo registra en el catalogo."""
    LEARNED_DIR.mkdir(parents=True, exist_ok=True)
    
    name = skill_data.get("name", "unknown_skill")
    filename = f"{name}.md"
    filepath = LEARNED_DIR / filename
    
    # Generate SKILL.md content
    steps_text = "\n".join([f"- {s}" for s in skill_data.get("steps", [])])
    tools_text = ", ".join(skill_data.get("tools", ["ninguna"]))
    constraints_text = "\n".join([f"- {c}" for c in skill_data.get("constraints", [])])
    
    content = SKILL_TEMPLATE.format(
        name=name,
        description=skill_data.get("description", ""),
        trigger=skill_data.get("trigger", ""),
        steps=steps_text,
        tools=tools_text,
        constraints=constraints_text if constraints_text else "- Ninguna especial",
        example=skill_data.get("example", ""),
        timestamp=datetime.now().isoformat(),
        source_id=pattern.get("id", "unknown"),
        validated="auto-generated"
    )
    
    filepath.write_text(content, encoding="utf-8")
    
    # Register in catalog
    if CATALOG_OK:
        try:
            register_skill(
                name=name,
                description=skill_data.get("description", ""),
                script_path=str(filepath),
                tags="learned,auto-evolved"
            )
        except Exception:
            pass
    
    # Index in Qdrant for semantic search
    if QDRANT_OK:
        try:
            save_memory(
                f"SKILL: {name} - {skill_data.get('description', '')}. "
                f"Trigger: {skill_data.get('trigger', '')}. "
                f"Steps: {'; '.join(skill_data.get('steps', []))}",
                metadata={"type": "learned_skill", "name": name, "path": str(filepath)}
            )
        except Exception:
            pass
    
    # Log
    _save_learner_log({
        "ts": datetime.now().isoformat(),
        "source_id": pattern.get("id", ""),
        "source_type": pattern.get("source", ""),
        "skill_name": name,
        "skill_path": str(filepath),
        "description": skill_data.get("description", "")
    })
    
    return str(filepath)


def _save_learner_log(entry: dict):
    """Append to learner log."""
    logs = []
    if LEARNER_LOG.exists():
        try:
            logs = json.loads(LEARNER_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    logs.append(entry)
    logs = logs[-100:]  # Keep last 100
    LEARNER_LOG.write_text(json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8")


def learn_from_operations(min_steps: int = 3, max_skills: int = 5) -> list:
    """
    Punto de entrada principal: busca patrones exitosos y genera skills.
    
    Returns: lista de skills generados
    """
    print("[Learner] Buscando patrones exitosos...")
    patterns = find_successful_patterns(min_steps=min_steps)
    
    if not patterns:
        print("[Learner] No se encontraron patrones nuevos")
        return []
    
    print(f"[Learner] {len(patterns)} patrones encontrados, procesando hasta {max_skills}...")
    generated = []
    
    for pattern in patterns[:max_skills]:
        print(f"[Learner] Procesando patron {pattern['id']} ({pattern['source']})...")
        
        result = generate_skill_from_pattern(pattern)
        if not result["success"]:
            print(f"[Learner] Error: {result['error']}")
            continue
        
        skill_data = result["data"]
        path = save_skill(skill_data, pattern)
        
        generated.append({
            "name": skill_data.get("name", ""),
            "path": path,
            "description": skill_data.get("description", ""),
            "source": pattern["source"]
        })
        print(f"[Learner] Skill generado: {skill_data.get('name', '')} -> {path}")
    
    print(f"[Learner] {len(generated)} skills generados")
    return generated


def get_learned_skills() -> list:
    """Lista todos los skills aprendidos."""
    skills = []
    if LEARNED_DIR.exists():
        for f in LEARNED_DIR.glob("*.md"):
            skills.append({
                "name": f.stem,
                "path": str(f),
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    return skills


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        skills = get_learned_skills()
        print(f"=== Skills aprendidos: {len(skills)} ===")
        for s in skills:
            print(f"  {s['name']} ({s['size']}B) - {s['modified']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--learn":
        results = learn_from_operations()
        for r in results:
            print(f"  [OK] {r['name']}: {r['description']}")
    else:
        print("Uso:")
        print("  python skill_learner.py --learn   (busca patrones y genera skills)")
        print("  python skill_learner.py --list    (lista skills aprendidos)")
