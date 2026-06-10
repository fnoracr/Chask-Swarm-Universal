"""
skill_catalog.py — Pilar 4: Catálogo de Skills Reutilizables
=============================================================
Detecta cuando Enjambre repite una tarea y la cataloga como skill.
Los skills son scripts reutilizables con metadata para búsqueda.

Uso:
  python skill_catalog.py register "nombre" "descripción" "ruta_script"
  python skill_catalog.py search "qué necesito"
  python skill_catalog.py list
  python skill_catalog.py track "acción realizada"  (cuenta frecuencia)
"""
import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG_FILE = os.path.join(BASE_DIR, "Configuracion", "skill_catalog.json")
ACTIONS_LOG = os.path.join(BASE_DIR, "action_frequency.json")
SKILLS_DIR = os.path.join(BASE_DIR, "skills")

REPETITION_THRESHOLD = 3  # Crear skill tras 3 repeticiones


def load_catalog():
    if os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"skills": [], "version": 1}


def save_catalog(data):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_actions():
    if os.path.exists(ACTIONS_LOG):
        with open(ACTIONS_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_actions(data):
    with open(ACTIONS_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def register_skill(name, description, script_path, tags=None):
    """Registra un nuevo skill en el catálogo."""
    catalog = load_catalog()
    
    # Verificar duplicados
    for skill in catalog["skills"]:
        if skill["name"].lower() == name.lower():
            print(f"[Skills] Skill '{name}' ya existe.")
            return False
    
    skill = {
        "id": len(catalog["skills"]) + 1,
        "name": name,
        "description": description,
        "script_path": script_path,
        "tags": tags or [],
        "created": datetime.now().isoformat(),
        "usage_count": 0,
        "last_used": None
    }
    
    catalog["skills"].append(skill)
    save_catalog(catalog)
    print(f"[Skills] Skill registrado: {name}")
    return True


def search_skills(query):
    """Busca skills por nombre, descripción o tags."""
    catalog = load_catalog()
    results = []
    query_lower = query.lower()
    
    for skill in catalog["skills"]:
        score = 0
        if query_lower in skill["name"].lower(): score += 3
        if query_lower in skill["description"].lower(): score += 2
        if any(query_lower in t.lower() for t in skill.get("tags", [])): score += 1
        if score > 0:
            results.append((score, skill))
    
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results]


def track_action(action_key):
    """
    Registra una acción y detecta si se repite.
    Si supera el umbral, sugiere crear un skill.
    """
    actions = load_actions()
    key = action_key.lower().strip()
    
    if key not in actions:
        actions[key] = {"count": 0, "first_seen": datetime.now().isoformat(), "skill_suggested": False}
    
    actions[key]["count"] += 1
    actions[key]["last_seen"] = datetime.now().isoformat()
    
    save_actions(actions)
    
    # Detectar repetición
    if actions[key]["count"] >= REPETITION_THRESHOLD and not actions[key]["skill_suggested"]:
        actions[key]["skill_suggested"] = True
        save_actions(actions)
        print(f"[Skills] PATRON DETECTADO: '{action_key}' se ha repetido {actions[key]['count']} veces.")
        print(f"[Skills] Considera crear un skill reutilizable para esta tarea.")
        return True  # Sugiere crear skill
    
    return False


def use_skill(skill_name):
    """Marca un skill como usado (incrementa contador)."""
    catalog = load_catalog()
    for skill in catalog["skills"]:
        if skill["name"].lower() == skill_name.lower():
            skill["usage_count"] += 1
            skill["last_used"] = datetime.now().isoformat()
            save_catalog(catalog)
            return skill
    return None


def list_skills():
    """Lista todos los skills."""
    catalog = load_catalog()
    if not catalog["skills"]:
        print("[Skills] No hay skills registrados.")
        return
    
    print(f"\nCATALOGO DE SKILLS ({len(catalog['skills'])} total):\n")
    for s in catalog["skills"]:
        used = f"(usado {s['usage_count']}x)" if s['usage_count'] > 0 else "(sin usar)"
        print(f"  [{s['id']}] {s['name']} {used}")
        print(f"      {s['description']}")
        print(f"      Script: {s['script_path']}")
        print()


# ── Registro inicial de skills existentes ──
def bootstrap_existing_skills():
    """Registra los scripts existentes que ya actúan como skills."""
    existing = [
        ("telegram_send", "Enviar mensaje por Telegram", 
         os.path.join(BASE_DIR, "charm_telegram.py"), ["telegram", "comunicacion"]),
        ("llm_router", "Enrutar consultas al pool de IAs gratuitas",
         os.path.join(BASE_DIR, "Advanced_Tools", "llm_router.py"), ["ia", "llm", "pool"]),
        ("audit_log", "Registrar accion critica en log de auditoria",
         os.path.join(BASE_DIR, "Advanced_Tools", "audit_logger.py"), ["seguridad", "audit"]),
        ("backup", "Sistema de backups automaticos",
         os.path.join(BASE_DIR, "Advanced_Tools", "backup_system.py"), ["backup", "seguridad"]),
        ("reflection", "Motor de auto-evolucion y lecciones aprendidas",
         os.path.join(BASE_DIR, "Advanced_Tools", "reflection_engine.py"), ["aprendizaje", "reflexion"]),
        ("evo_memory", "Memoria evolutiva con hechos temporales",
         os.path.join(BASE_DIR, "Advanced_Tools", "evolutionary_memory.py"), ["memoria", "hechos"]),
        ("qdrant_memory", "Memoria vectorial a largo plazo",
         os.path.join(BASE_DIR, "Advanced_Tools", "qdrant_memory_manager.py"), ["memoria", "vectorial"]),
        ("privacy_engine", "Anonimizacion de datos sensibles",
         os.path.join(BASE_DIR, "Advanced_Tools", "privacy_engine.py"), ["seguridad", "privacidad"]),
    ]
    
    count = 0
    for name, desc, path, tags in existing:
        if os.path.exists(path):
            if register_skill(name, desc, path, tags):
                count += 1
    
    if count > 0:
        print(f"[Skills] Bootstrap: {count} skills existentes registrados.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python skill_catalog.py [register|search|list|track|bootstrap] [args...]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "register" and len(sys.argv) >= 5:
        register_skill(sys.argv[2], sys.argv[3], sys.argv[4], 
                       sys.argv[5].split(",") if len(sys.argv) > 5 else [])
    elif cmd == "search" and len(sys.argv) >= 3:
        results = search_skills(" ".join(sys.argv[2:]))
        for s in results:
            print(f"  [{s['id']}] {s['name']}: {s['description']}")
        if not results:
            print("  Sin resultados.")
    elif cmd == "list":
        list_skills()
    elif cmd == "track" and len(sys.argv) >= 3:
        track_action(" ".join(sys.argv[2:]))
    elif cmd == "bootstrap":
        bootstrap_existing_skills()
    else:
        print(f"Comando desconocido: {cmd}")
