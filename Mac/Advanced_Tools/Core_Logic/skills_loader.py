"""
skills_loader.py — Sistema de Skills/Plugins dinamico con Hot-Reload
====================================================================
Descubre y carga automaticamente scripts de /skills/ y /skills/learned/
Incluye hot-reload: detecta nuevos skills sin reiniciar.
Incluye busqueda semantica via Qdrant cuando keyword match falla.
"""
import os, sys, importlib.util, threading, time, json, hashlib
from pathlib import Path

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
LEARNED_DIR = os.path.join(SKILLS_DIR, "learned")

sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools"))

REGISTRY = {}  # {nombre: {func, description, keywords, ...}}
MD_SKILLS = {}  # {nombre: {description, trigger, steps, path}}
_FILE_HASHES = {}  # {path: hash} for hot-reload detection
_WATCHER_RUNNING = False

try:
    from qdrant_memory_manager import search_memory
    QDRANT_OK = True
except ImportError:
    QDRANT_OK = False


def _file_hash(path: str) -> str:
    """Quick hash of file for change detection."""
    try:
        return hashlib.md5(Path(path).read_bytes()).hexdigest()[:12]
    except Exception:
        return ""


def discover_skills(silent: bool = False):
    """Escanea /skills/ y /skills/learned/ y registra todo."""
    global _FILE_HASHES
    if not os.path.exists(SKILLS_DIR):
        os.makedirs(SKILLS_DIR)
        _create_example_skills()

    REGISTRY.clear()
    MD_SKILLS.clear()
    _FILE_HASHES.clear()
    
    # 1. Load Python skills
    for dirpath in [SKILLS_DIR, LEARNED_DIR]:
        if not os.path.exists(dirpath):
            continue
        for fname in os.listdir(dirpath):
            if fname.endswith(".py") and not fname.startswith("_"):
                _load_py_skill(os.path.join(dirpath, fname), silent)
            elif fname.endswith(".md") and not fname.startswith("_"):
                _load_md_skill(os.path.join(dirpath, fname), silent)
    
    if not silent:
        print(f"[Skills] {len(REGISTRY)} Python + {len(MD_SKILLS)} Markdown skills cargadas.")
    return REGISTRY


def _load_py_skill(path: str, silent: bool = False):
    """Load a single Python skill file."""
    fname = os.path.basename(path)
    skill_name = fname[:-3]
    try:
        spec = importlib.util.spec_from_file_location(skill_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "run"):
            REGISTRY[skill_name] = {
                "func":        mod.run,
                "name":        getattr(mod, "NAME", skill_name),
                "description": getattr(mod, "DESCRIPTION", ""),
                "keywords":    getattr(mod, "KEYWORDS", []),
                "path":        path
            }
            _FILE_HASHES[path] = _file_hash(path)
            if not silent:
                print(f"  [Skills] [OK] {skill_name} cargada")
    except Exception as e:
        if not silent:
            print(f"  [Skills] [!!] Error en {fname}: {e}")


def _load_md_skill(path: str, silent: bool = False):
    """Load a SKILL.md file (learned skill)."""
    try:
        content = Path(path).read_text(encoding="utf-8")
        name = Path(path).stem
        
        # Parse key fields
        desc = ""
        trigger = ""
        steps = []
        
        current_section = ""
        for line in content.split("\n"):
            if line.startswith("## Descripcion"):
                current_section = "desc"
            elif line.startswith("## Trigger"):
                current_section = "trigger"
            elif line.startswith("## Pasos"):
                current_section = "steps"
            elif line.startswith("## "):
                current_section = ""
            elif current_section == "desc" and line.strip():
                desc += line.strip() + " "
            elif current_section == "trigger" and line.strip():
                trigger += line.strip() + " "
            elif current_section == "steps" and line.strip().startswith("- "):
                steps.append(line.strip()[2:])
        
        MD_SKILLS[name] = {
            "description": desc.strip(),
            "trigger": trigger.strip(),
            "steps": steps,
            "path": path
        }
        _FILE_HASHES[path] = _file_hash(path)
        if not silent:
            print(f"  [Skills] [OK] {name}.md cargada (learned)")
    except Exception as e:
        if not silent:
            print(f"  [Skills] [!!] Error en {Path(path).name}: {e}")


def hot_reload():
    """Check for new or modified skill files and reload them."""
    changed = 0
    for dirpath in [SKILLS_DIR, LEARNED_DIR]:
        if not os.path.exists(dirpath):
            continue
        for fname in os.listdir(dirpath):
            path = os.path.join(dirpath, fname)
            if fname.endswith(".py") and not fname.startswith("_"):
                current_hash = _file_hash(path)
                if path not in _FILE_HASHES or _FILE_HASHES[path] != current_hash:
                    _load_py_skill(path, silent=True)
                    changed += 1
            elif fname.endswith(".md") and not fname.startswith("_"):
                current_hash = _file_hash(path)
                if path not in _FILE_HASHES or _FILE_HASHES[path] != current_hash:
                    _load_md_skill(path, silent=True)
                    changed += 1
    return changed


def start_watcher(interval: int = 10):
    """Start background thread that watches for new skills."""
    global _WATCHER_RUNNING
    if _WATCHER_RUNNING:
        return
    _WATCHER_RUNNING = True
    
    def _watch():
        while _WATCHER_RUNNING:
            try:
                n = hot_reload()
                if n > 0:
                    print(f"[Skills] Hot-reload: {n} skills actualizadas")
            except Exception:
                pass
            time.sleep(interval)
    
    t = threading.Thread(target=_watch, daemon=True, name="SkillWatcher")
    t.start()


def stop_watcher():
    global _WATCHER_RUNNING
    _WATCHER_RUNNING = False


def match_skill(prompt: str) -> str | None:
    """Match por keywords primero, luego busqueda semantica en Qdrant."""
    p = prompt.lower()
    
    # 1. Keyword match (fast)
    for name, skill in REGISTRY.items():
        for kw in skill.get("keywords", []):
            if kw.lower() in p:
                return name
    
    # 2. Semantic match via Qdrant (if keywords fail)
    if QDRANT_OK:
        try:
            results = search_memory(prompt, top_k=3)
            for r in results:
                payload = r.get("payload", {})
                if payload.get("type") == "learned_skill":
                    name = payload.get("name", "")
                    if name in MD_SKILLS:
                        return f"md:{name}"
        except Exception:
            pass
    
    return None


def run_skill(skill_name: str, prompt: str) -> str:
    """Ejecuta una skill Python o devuelve pasos de un SKILL.md."""
    # Python skill
    if skill_name in REGISTRY:
        try:
            return REGISTRY[skill_name]["func"](prompt)
        except Exception as e:
            return f"Error ejecutando {skill_name}: {e}"
    
    # Learned SKILL.md
    md_name = skill_name.replace("md:", "")
    if md_name in MD_SKILLS:
        skill = MD_SKILLS[md_name]
        steps_text = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(skill["steps"])])
        return f"Skill aprendido: {skill['description']}\nPasos:\n{steps_text}"
    
    return f"Skill '{skill_name}' no encontrada."


def list_skills() -> str:
    """Lista todas las skills disponibles (Python + Markdown)."""
    lines = []
    if REGISTRY:
        lines.append("Skills Python:")
        for name, s in REGISTRY.items():
            lines.append(f"  - {s['name']}: {s['description']}")
    if MD_SKILLS:
        lines.append("Skills Aprendidas (SKILL.md):")
        for name, s in MD_SKILLS.items():
            lines.append(f"  - {name}: {s['description']}")
    if not lines:
        return "No hay skills instaladas."
    return "\n".join(lines)


def _create_example_skills():
    """Crea skills de ejemplo."""
    clima = '''NAME = "Consulta Clima"
DESCRIPTION = "Consulta el tiempo actual en una ciudad"
KEYWORDS = ["tiempo", "clima", "temperatura", "llueve", "weather"]

def run(prompt: str) -> str:
    import re, requests
    city = re.search(r"en ([\\w\\s]+)", prompt)
    city = city.group(1).strip() if city else "Madrid"
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=8)
        return r.text.strip()
    except:
        return f"No pude obtener el tiempo para {city}."
'''
    hora = '''NAME = "Hora Actual"
DESCRIPTION = "Dice la hora y fecha actuales"
KEYWORDS = ["hora", "fecha", "hoy", "dia", "what time", "what day"]

def run(prompt: str) -> str:
    from datetime import datetime
    now = datetime.now()
    return f"Son las {now.strftime('%H:%M')} del {now.strftime('%A %d de %B de %Y')}."
'''
    with open(os.path.join(SKILLS_DIR, "clima.py"), "w", encoding="utf-8") as f:
        f.write(clima)
    with open(os.path.join(SKILLS_DIR, "hora_actual.py"), "w", encoding="utf-8") as f:
        f.write(hora)
    with open(os.path.join(SKILLS_DIR, "__init__.py"), "w") as f:
        f.write("")


if __name__ == "__main__":
    discover_skills()
    print(list_skills())
    name = match_skill("Que tiempo hace en Sevilla?")
    if name:
        print(run_skill(name, "Que tiempo hace en Sevilla?"))

