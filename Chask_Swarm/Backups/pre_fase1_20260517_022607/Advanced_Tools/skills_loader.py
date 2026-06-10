"""
skills_loader.py — Sistema de Skills/Plugins dinámico
Descubre y carga automáticamente scripts de la carpeta /skills/
"""
import os, sys, importlib.util, inspect

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")

REGISTRY = {}  # {nombre: {func, description, keywords}}

def discover_skills():
    """Escanea /skills/ y registra todas las skills disponibles."""
    if not os.path.exists(SKILLS_DIR):
        os.makedirs(SKILLS_DIR)
        _create_example_skills()

    REGISTRY.clear()
    for fname in os.listdir(SKILLS_DIR):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        skill_name = fname[:-3]
        path = os.path.join(SKILLS_DIR, fname)
        try:
            spec = importlib.util.spec_from_file_location(skill_name, path)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # Requiere función run() y variables NAME, DESCRIPTION, KEYWORDS
            if hasattr(mod, "run"):
                REGISTRY[skill_name] = {
                    "func":        mod.run,
                    "name":        getattr(mod, "NAME", skill_name),
                    "description": getattr(mod, "DESCRIPTION", ""),
                    "keywords":    getattr(mod, "KEYWORDS", []),
                    "path":        path
                }
                print(f"  [Skills] ✓ {skill_name} cargada")
        except Exception as e:
            print(f"  [Skills] ✗ Error en {fname}: {e}")
    print(f"[Skills] {len(REGISTRY)} skills cargadas.")
    return REGISTRY

def match_skill(prompt: str) -> str | None:
    """Devuelve el nombre de la skill que mejor coincide con el prompt."""
    p = prompt.lower()
    for name, skill in REGISTRY.items():
        for kw in skill.get("keywords", []):
            if kw.lower() in p:
                return name
    return None

def run_skill(skill_name: str, prompt: str) -> str:
    """Ejecuta una skill y devuelve el resultado."""
    if skill_name not in REGISTRY:
        return f"Skill '{skill_name}' no encontrada."
    try:
        return REGISTRY[skill_name]["func"](prompt)
    except Exception as e:
        return f"Error ejecutando {skill_name}: {e}"

def list_skills() -> str:
    """Devuelve una descripción de todas las skills disponibles."""
    if not REGISTRY:
        return "No hay skills instaladas."
    lines = ["Skills disponibles:"]
    for name, s in REGISTRY.items():
        lines.append(f"  • {s['name']}: {s['description']}")
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
        return f"🌤 {r.text.strip()}"
    except:
        return f"No pude obtener el tiempo para {city}."
'''
    hora = '''NAME = "Hora Actual"
DESCRIPTION = "Dice la hora y fecha actuales"
KEYWORDS = ["hora", "fecha", "hoy", "qué día", "what time", "what day"]

def run(prompt: str) -> str:
    from datetime import datetime
    now = datetime.now()
    return f"🕐 Son las {now.strftime('%H:%M')} del {now.strftime('%A %d de %B de %Y')}."
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
    # Test
    name = match_skill("¿Qué tiempo hace en Sevilla?")
    if name:
        print(run_skill(name, "¿Qué tiempo hace en Sevilla?"))
