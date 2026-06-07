"""
mode_router.py — Motor de selección de modos de agente
=======================================================
Detecta automáticamente el modo más adecuado para cada prompt
y aplica el system prompt, modelo y restricciones correspondientes.

Uso:
  python mode_router.py detect "diseña la arquitectura del sistema"
  python mode_router.py list
  python mode_router.py info viper
"""
import os
import sys
import json
import unicodedata
import io

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODES_FILE = os.path.join(BASE_DIR, "Advanced_Tools", "agent_modes.json")


def _norm(text: str) -> str:
    """Normaliza texto para matching robusto."""
    return unicodedata.normalize('NFD', text.lower()).encode('ascii', 'ignore').decode()


def load_markdown_agents() -> list[dict]:
    import glob, re
    agents = []
    subagentes_dir = os.path.join(BASE_DIR, "Advanced_Tools", "Subagentes")
    if not os.path.exists(subagentes_dir): return agents
    
    for file_path in glob.glob(os.path.join(subagentes_dir, "*.md")):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        name_match = re.search(r"^#\s*Agent:\s*(.+)", content, re.M)
        desc_match = re.search(r"##\s*Description\n(.*?)(?=\n##|\Z)", content, re.S)
        model_match = re.search(r"##\s*Preferred Model\n(.*?)(?=\n##|\Z)", content, re.S)
        trigger_match = re.search(r"##\s*Trigger Keywords\n(.*?)(?=\n##|\Z)", content, re.S)
        system_match = re.search(r"##\s*System Prompt\n(.*?)(?=\n##|\Z)", content, re.S)
        
        if name_match:
            name = name_match.group(1).strip()
            mode_id = name.lower().replace(" ", "_")
            triggers = [k.strip() for k in trigger_match.group(1).split(",")] if trigger_match else []
            
            agent = {
                "id": mode_id,
                "name": name,
                "description": desc_match.group(1).strip() if desc_match else "Markdown agent",
                "icon": "🤖",
                "active": True,
                "custom": True,
                "system_prompt": system_match.group(1).strip() if system_match else "",
                "trigger_keywords": triggers,
                "model_preference": model_match.group(1).strip() if model_match else "qwen3:8b",
                "cloud_model": model_match.group(1).strip() if model_match else "qwen3:8b",
                "allowed_tools": ["*"],
                "restricted_tools": []
            }
            agents.append(agent)
    return agents

def load_modes() -> dict:
    config = {"auto_detect": True, "default_mode": "enjambre", "modes": []}
    if os.path.exists(MODES_FILE):
        try:
            with open(MODES_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass
    md_agents = load_markdown_agents()
    if md_agents:
        config["modes"].extend(md_agents)
    return config


def _get_embedding(text: str) -> list[float] | None:
    """Genera embedding usando Ollama nomic-embed (si disponible)."""
    try:
        import requests
        resp = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception:
        pass
    return None


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Similitud coseno entre dos vectores."""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def detect_mode(prompt: str) -> dict:
    """
    Analiza el prompt y devuelve el modo más adecuado.
    Usa routing semántico (embeddings) con fallback a keywords.
    Returns: {"mode": {...}, "reason": str, "score": float}
    """
    config = load_modes()
    if not config.get("auto_detect", True):
        default_id = config.get("default_mode", "enjambre")
        mode = next((m for m in config["modes"] if m["id"] == default_id), config["modes"][-1])
        return {"mode": mode, "reason": "auto_detect desactivado", "score": 0}

    active_modes = [m for m in config["modes"] if m.get("active", True)]

    # ── Intento 1: Routing Semántico ──
    prompt_emb = _get_embedding(prompt)
    if prompt_emb:
        best_mode = None
        best_sim = -1.0

        for mode in active_modes:
            # Usar descripción + keywords como texto de referencia
            ref_text = f"{mode['name']}: {mode['description']}. Keywords: {', '.join(mode.get('trigger_keywords', []))}"
            mode_emb = _get_embedding(ref_text)
            if mode_emb:
                sim = _cosine_sim(prompt_emb, mode_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_mode = mode

        if best_mode and best_sim > 0.3:  # Umbral mínimo de similitud
            return {
                "mode": best_mode,
                "reason": f"semantic (sim={best_sim:.3f})",
                "score": round(best_sim * 100, 1)
            }

    # ── Intento 2: Fallback a Keywords ──
    p = _norm(prompt)
    best_mode = None
    best_score = 0
    best_reason = ""

    for mode in active_modes:
        if not mode.get("trigger_keywords"):
            continue

        score = 0
        matched = []
        for kw in mode["trigger_keywords"]:
            if _norm(kw) in p:
                score += 10
                matched.append(kw)

        if score > best_score:
            best_score = score
            best_mode = mode
            best_reason = f"keywords: {', '.join(matched)}"

    # Si ningún modo especializado alcanza score > 0, usar default
    if best_mode is None or best_score == 0:
        default_id = config.get("default_mode", "enjambre")
        best_mode = next((m for m in config["modes"] if m["id"] == default_id), config["modes"][-1])
        best_reason = "default (sin match)"

    return {"mode": best_mode, "reason": best_reason, "score": best_score}



def get_mode_by_id(mode_id: str) -> dict | None:
    """Obtiene un modo por su ID."""
    config = load_modes()
    for mode in config["modes"]:
        if mode["id"] == mode_id:
            return mode
    return None


def get_system_prompt(mode: dict) -> str:
    """Construye el system prompt completo para un modo."""
    return mode.get("system_prompt", "")


def get_preferred_model(mode: dict, use_cloud: bool = False) -> str:
    """Devuelve el modelo preferido para este modo."""
    if use_cloud:
        return mode.get("cloud_model", "qwen3:8b")
    return mode.get("model_preference", "qwen3:8b")


def is_tool_allowed(mode: dict, tool_name: str) -> bool:
    """Verifica si una herramienta está permitida en este modo."""
    allowed = mode.get("allowed_tools", ["*"])
    restricted = mode.get("restricted_tools", [])

    if tool_name in restricted:
        return False
    if "*" in allowed:
        return True
    return tool_name in allowed


def list_modes():
    """Lista todos los modos disponibles."""
    config = load_modes()
    print(f"\nMODOS DE AGENTE ({len(config['modes'])} total):\n")
    for m in config["modes"]:
        status = "ACTIVO" if m.get("active", True) else "INACTIVO"
        default = " [DEFAULT]" if m["id"] == config.get("default_mode") else ""
        custom = " [CUSTOM]" if m.get("custom", False) else ""
        print(f"  {m.get('icon', '')} {m['name']} ({status}{default}{custom})")
        print(f"     {m['description']}")
        print(f"     Modelo local: {m.get('model_preference', 'N/A')}")
        print(f"     Modelo cloud: {m.get('cloud_model', 'N/A')}")
        print(f"     Keywords: {', '.join(m.get('trigger_keywords', []))}")
        print()


def create_mode(
    mode_id: str,
    name: str,
    description: str,
    system_prompt: str = "",
    trigger_keywords: list[str] = None,
    model_preference: str = "qwen3:8b",
    cloud_model: str = "qwen3:8b",
    icon: str = "🔧",
    allowed_tools: list[str] = None,
    restricted_tools: list[str] = None
) -> dict:
    """
    Crea un nuevo modo de agente dinámicamente.
    Se persiste en agent_modes.json.
    
    Returns:
        El modo creado
    """
    config = load_modes()
    
    # Verificar que no exista
    for m in config["modes"]:
        if m["id"] == mode_id:
            print(f"[ModeRouter] Modo '{mode_id}' ya existe.")
            return m
    
    mode = {
        "id": mode_id,
        "name": name,
        "description": description,
        "icon": icon,
        "active": True,
        "custom": True,
        "created": __import__('datetime').datetime.now().isoformat(),
        "system_prompt": system_prompt,
        "trigger_keywords": trigger_keywords or [],
        "model_preference": model_preference,
        "cloud_model": cloud_model,
        "allowed_tools": allowed_tools or ["*"],
        "restricted_tools": restricted_tools or []
    }
    
    config["modes"].append(mode)
    
    with open(MODES_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"[ModeRouter] Modo '{name}' creado ({mode_id})")
    return mode


def delete_mode(mode_id: str) -> bool:
    """
    Elimina un modo custom. No permite eliminar modos built-in.
    """
    config = load_modes()
    
    for i, m in enumerate(config["modes"]):
        if m["id"] == mode_id:
            if not m.get("custom", False):
                print(f"[ModeRouter] No se puede eliminar modo built-in '{mode_id}'.")
                return False
            config["modes"].pop(i)
            with open(MODES_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"[ModeRouter] Modo '{mode_id}' eliminado.")
            return True
    
    print(f"[ModeRouter] Modo '{mode_id}' no encontrado.")
    return False


def toggle_mode(mode_id: str) -> bool:
    """Activa/desactiva un modo."""
    config = load_modes()
    for m in config["modes"]:
        if m["id"] == mode_id:
            m["active"] = not m.get("active", True)
            with open(MODES_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            status = "activado" if m["active"] else "desactivado"
            print(f"[ModeRouter] Modo '{mode_id}' {status}.")
            return True
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python mode_router.py [detect|list|info|create|delete|toggle] [args...]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "detect" and len(sys.argv) >= 3:
        prompt = " ".join(sys.argv[2:])
        result = detect_mode(prompt)
        mode = result["mode"]
        print(f"  Modo: {mode.get('icon', '')} {mode['name']}")
        print(f"  Razon: {result['reason']}")
        print(f"  Score: {result['score']}")
        print(f"  Modelo: {mode.get('model_preference', 'N/A')}")

    elif cmd == "list":
        list_modes()

    elif cmd == "info" and len(sys.argv) >= 3:
        mode = get_mode_by_id(sys.argv[2])
        if mode:
            print(json.dumps(mode, indent=2, ensure_ascii=False))
        else:
            print(f"Modo '{sys.argv[2]}' no encontrado.")

    elif cmd == "create" and len(sys.argv) >= 5:
        # create id name description [keywords...]
        mode_id = sys.argv[2]
        name = sys.argv[3]
        desc = sys.argv[4]
        keywords = sys.argv[5:] if len(sys.argv) > 5 else []
        create_mode(mode_id, name, desc, trigger_keywords=keywords)

    elif cmd == "delete" and len(sys.argv) >= 3:
        delete_mode(sys.argv[2])

    elif cmd == "toggle" and len(sys.argv) >= 3:
        toggle_mode(sys.argv[2])

    else:
        print(f"Comando desconocido: {cmd}")

