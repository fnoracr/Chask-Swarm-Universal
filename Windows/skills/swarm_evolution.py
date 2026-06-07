"""
swarm_evolution.py   Protocolo Elektra para Chask Swarm
Motor evolutivo multi-agente: m ltiples IAs resuelven el mismo problema
desde  ngulos distintos, evolucionan sus prompts y se sintetiza la mejor soluci n.

Uso desde Alpha (Charm):
    from skills.swarm_evolution import evolve_solution, should_activate
    if should_activate(task_description):
        result = evolve_solution(problem, task_type="code")

Uso desde prompt:
    "Elektra, resuelve esto con m xima calidad"
    "usa el protocolo evolutivo para este c digo"
"""
NAME = "Swarm Evolution (Protocolo Elektra)"
DESCRIPTION = "Motor evolutivo multi-agente para tareas cr ticas que requieren perfecci n"
KEYWORDS = [
    "elektra", "evoluci n", "evolutivo", "m xima calidad", "perfecto",
    "protocolo evolutivo", "multi-agente", "swarm evolution",
    "maximum quality", "perfect", "evolutionary",
]

import os, sys, json, random, copy, time
from dataclasses import dataclass, field
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools"))

#    Configuraci n                                                           
GENERATIONS = 2          # Generaciones evolutivas (2 = equilibrio calidad/coste)
MUTATION_RATE = 0.4      # Probabilidad de mutaci n vs crossover
ELITE_FRACTION = 0.5     # Fracci n de agentes que sobreviven sin cambios

#    Ranking de IAs por capacidad (Charm premium + Pool gratuito)      
# Tier 1: Modelos premium de Charm (los m s capaces)
# Tier 2: Pool gratuito (buenos, pero menos capaces que los premium)
# agentic: True si el modelo tiene capacidad ag ntica (razonamiento complejo,
#          evaluaci n cr tica, s ntesis, orquestaci n)
AI_TIERS = {
    #    Tier 1: Charm Premium (si est n disponibles)   
    "gemini_pro_high": {
        "tier": 1, "label": "Gemini 3.1 Pro (High)",
        "best_for": ["code", "analysis", "reasoning", "math"],
        "engine": "charm", "agentic": True,
    },
    "claude_opus": {
        "tier": 1, "label": "Claude Opus 4.6 (Thinking)",
        "best_for": ["code", "security", "analysis", "text"],
        "engine": "charm", "agentic": True,
    },
    "claude_sonnet": {
        "tier": 1, "label": "Claude Sonnet 4.6 (Thinking)",
        "best_for": ["code", "text", "analysis"],
        "engine": "charm", "agentic": True,
    },
    "gemini_flash": {
        "tier": 1, "label": "Gemini 3 Flash",
        "best_for": ["general", "fast", "text"],
        "engine": "charm", "agentic": False,  # R pido pero no ag ntico
    },
    "gpt_oss": {
        "tier": 1, "label": "GPT-OSS 120B (Medium)",
        "best_for": ["code", "general"],
        "engine": "charm", "agentic": True,
    },
    #    Tier 2: Pool Gratuito   
    "deepseek": {
        "tier": 2, "label": "DeepSeek Chat",
        "best_for": ["code", "reasoning", "math"],
        "engine": "pool", "agentic": True,   # DeepSeek V3 = razonamiento fuerte
    },
    "groq": {
        "tier": 2, "label": "Groq Llama 3.3 70B",
        "best_for": ["general", "fast", "translation"],
        "engine": "pool", "agentic": True,   # 70B = capacidad decente
    },
    "cohere": {
        "tier": 2, "label": "Cohere Command-R",
        "best_for": ["summary", "classification", "text"],
        "engine": "pool", "agentic": False,  # Bueno en texto, no en orquestaci n
    },
    "cerebras": {
        "tier": 2, "label": "Cerebras Llama 8B",
        "best_for": ["general", "fast"],
        "engine": "pool", "agentic": False,  # 8B = demasiado peque o para orquestar
    },
    "openrouter": {
        "tier": 2, "label": "OpenRouter Multi-modelo",
        "best_for": ["general", "fallback"],
        "engine": "pool", "agentic": True,   # Depende del modelo ruteado
    },
    "ollama_cloud": {
        "tier": 2, "label": "Ollama Cloud (8+ modelos)",
        "best_for": ["general", "fallback"],
        "engine": "pool", "agentic": False,  # Modelos peque os
    },
}

#    Roles por tipo de tarea con asignaci n inteligente de IAs               
# Cada agente tiene una lista priorizada de IAs: usa la mejor disponible.
TASK_ROLES = {
    "code": {
        "agents": [
            {"id": "coder", "role": "Desarrollador Senior",
             "prompt": "Eres un desarrollador senior experto. Escribes c digo limpio, "
                       "eficiente, bien documentado y con manejo robusto de errores. "
                       "Siempre incluyes validaciones de entrada y sigues las mejores pr cticas.",
             "preferred_ais": ["claude_opus", "gemini_pro_high", "deepseek", "groq"]},
            {"id": "security", "role": "Auditor de Seguridad",
             "prompt": "Eres un auditor de seguridad inform tica. Revisas c digo buscando "
                       "vulnerabilidades: inyecci n SQL, XSS, buffer overflows, credenciales "
                       "hardcoded, permisos excesivos y fugas de datos. Propones correcciones concretas.",
             "preferred_ais": ["claude_sonnet", "gemini_pro_high", "deepseek", "groq"]},
            {"id": "architect", "role": "Arquitecto de Software",
             "prompt": "Eres un arquitecto de software. Eval as la estructura del c digo, "
                       "patrones de dise o, escalabilidad, mantenibilidad y acoplamiento. "
                       "Propones mejoras arquitect nicas sin sobreingenier a.",
             "preferred_ais": ["gemini_pro_high", "claude_opus", "deepseek", "cerebras"]},
        ],
    },
    "text": {
        "agents": [
            {"id": "writer", "role": "Redactor Profesional",
             "prompt": "Eres un redactor profesional. Escribes con claridad, precisi n y "
                       "estilo atractivo. Cuidas la estructura, los p rrafos y el flujo narrativo.",
             "preferred_ais": ["claude_opus", "claude_sonnet", "groq", "cohere"]},
            {"id": "editor", "role": "Editor y Corrector",
             "prompt": "Eres un editor experto. Revisas textos buscando errores gramaticales, "
                       "inconsistencias, redundancias y falta de claridad. Mejoras sin cambiar el tono.",
             "preferred_ais": ["gemini_pro_high", "claude_sonnet", "cohere", "groq"]},
            {"id": "factcheck", "role": "Verificador de Hechos",
             "prompt": "Eres un verificador de hechos riguroso. Compruebas que las afirmaciones "
                       "sean correctas, las fuentes fiables y no haya sesgos ni exageraciones.",
             "preferred_ais": ["gemini_pro_high", "claude_opus", "deepseek", "groq"]},
        ],
    },
    "analysis": {
        "agents": [
            {"id": "analyst", "role": "Analista Sist mico",
             "prompt": "Eres un analista sist mico. Descompones problemas en subsistemas, "
                       "identificas relaciones causales y puntos de palanca.",
             "preferred_ais": ["claude_opus", "gemini_pro_high", "deepseek", "groq"]},
            {"id": "lateral", "role": "Pensador Lateral",
             "prompt": "Eres un pensador lateral. Buscas analog as de otros campos, inviertes "
                       "supuestos y propones soluciones que nadie ha considerado.",
             "preferred_ais": ["claude_sonnet", "gemini_flash", "groq", "openrouter"]},
            {"id": "critic", "role": "Cr tico Constructivo",
             "prompt": "Eres un cr tico constructivo. Identificas fallos, riesgos ocultos y "
                       "sesgos. Siempre propones c mo mitigar lo que se alas.",
             "preferred_ais": ["gemini_pro_high", "claude_opus", "deepseek", "cohere"]},
        ],
    },
}


#    Estructuras de datos                                                   
@dataclass
class EvAgent:
    id: str
    role: str
    system_prompt: str
    provider: str = ""
    fitness_history: list = field(default_factory=list)
    generation: int = 0
    mutations: int = 0

    @property
    def fitness(self) -> float:
        if not self.fitness_history:
            return 0.0
        return sum(self.fitness_history[-5:]) / len(self.fitness_history[-5:])

    def to_dict(self):
        return {
            "id": self.id, "role": self.role, "provider": self.provider,
            "fitness": round(self.fitness, 3), "generation": self.generation,
            "mutations": self.mutations,
        }


#    Asignar IAs  NICAS a cada agente                                       
def _assign_unique_providers(agents_config: list) -> dict:
    """
    Asigna una IA diferente a cada agente. NUNCA dos agentes con la misma IA.
    Devuelve {agent_id: provider_name}
    """
    assigned = {}  # {agent_id: pool_provider_name}
    used_providers = set()

    # Cargar pool disponible
    try:
        import llm_router
        cfg = llm_router.load_config()
        usage = llm_router.load_usage()
        pool_available = []
        for pv in cfg["providers"]:
            if not pv.get("active"):
                continue
            used = usage["counts"].get(pv["name"], 0)
            if used < pv.get("daily_limit", 500):
                pool_available.append(pv["name"])
    except Exception:
        pool_available = ["deepseek", "groq", "cohere", "cerebras"]

    for agent_cfg in agents_config:
        agent_id = agent_cfg["id"]
        preferred = agent_cfg.get("preferred_ais", [])

        # Filtrar solo pool providers (Tier 2) que no est n ya asignados
        pool_prefs = [ai for ai in preferred
                      if AI_TIERS.get(ai, {}).get("engine") == "pool"
                      and ai not in used_providers
                      and ai in pool_available]

        if pool_prefs:
            chosen = pool_prefs[0]
        else:
            # Fallback: cualquier pool provider no usado
            remaining = [p for p in pool_available if p not in used_providers]
            chosen = remaining[0] if remaining else pool_available[0] if pool_available else "groq"

        assigned[agent_id] = chosen
        used_providers.add(chosen)

    return assigned


def _call_specific_provider(system_prompt: str, user_prompt: str,
                            provider_name: str) -> tuple:
    """
    Llama a un proveedor ESPEC FICO del pool. Para forzar que cada agente
    use su IA asignada (no la primera disponible).
    Devuelve (respuesta, label).
    """
    try:
        import llm_router
        cfg = llm_router.load_config()
        usage = llm_router.load_usage()

        pv = next((p for p in cfg["providers"]
                   if p["name"] == provider_name and p.get("active")), None)
        if pv:
            used = usage["counts"].get(pv["name"], 0)
            if used < pv.get("daily_limit", 500):
                result = llm_router.call_provider(pv, user_prompt, system_prompt)
                if result:
                    usage["counts"][pv["name"]] = used + 1
                    llm_router.save_usage(usage)
                    label = AI_TIERS.get(provider_name, {}).get("label", provider_name)
                    return result, label

        # Si el proveedor espec fico falla, intentar cualquier otro
        pv = llm_router.pick_provider(user_prompt, cfg, usage)
        if pv:
            result = llm_router.call_provider(pv, user_prompt, system_prompt)
            if result:
                usage["counts"][pv["name"]] = usage["counts"].get(pv["name"], 0) + 1
                llm_router.save_usage(usage)
                return result, pv.get("label", pv["name"])

    except Exception as e:
        print(f"[Elektra] Error llamando a {provider_name}: {e}")

    return "[Error: No se pudo contactar con ninguna IA]", "error"


#    ORQUESTADOR: Yo (Charm) o el mejor modelo ag ntico disponible    
# Prioridad: Charm > DeepSeek (razonamiento) > Groq (70B) > OpenRouter
# NUNCA un modelo sin capacidad ag ntica (Cerebras 8B, Ollama peque os)
ORCHESTRATOR_PRIORITY = [
    "deepseek",     # DeepSeek V3 671B   razonamiento excepcional
    "groq",         # Llama 3.3 70B   buena capacidad ag ntica
    "openrouter",   # Multi-modelo   depende del modelo ruteado
]

_orchestrator_cache = {"provider": None, "label": None, "checked_at": None}


def _select_orchestrator() -> tuple:
    """
    Selecciona el orquestador: yo (Charm) si tengo cr ditos,
    si no, el mejor modelo AG NTICO del pool.
    Devuelve (provider_name, label, engine_type).
    """
    global _orchestrator_cache
    now = datetime.now()

    # Cache de 5 minutos para no comprobar cr ditos cada llamada
    if (_orchestrator_cache["provider"]
            and _orchestrator_cache["checked_at"]
            and (now - _orchestrator_cache["checked_at"]).seconds < 300):
        return (_orchestrator_cache["provider"],
                _orchestrator_cache["label"],
                _orchestrator_cache.get("engine", "pool"))

    #    Opci n 1: Charm (yo)   
    # Cuando este c digo se ejecuta desde Charm, YO soy el orquestador.
    # Detecto si estoy disponible comprobando la cola de entrada.
    charm_available = False
    try:
        import charm_telegram
        # Si el m dulo existe, Charm est  activo
        charm_available = True
    except ImportError:
        pass

    # Tambi n compruebo si hay un indicador de que estoy ejecutando
    ag_indicator = os.path.join(BASE_DIR, ".charm_active")
    if os.path.exists(ag_indicator):
        charm_available = True

    if charm_available:
        _orchestrator_cache = {
            "provider": "charm",
            "label": "Enjambre (Charm)",
            "engine": "charm",
            "checked_at": now
        }
        return "charm", "Enjambre (Charm)", "charm"

    #    Opci n 2: Mejor modelo AG NTICO del pool con cr ditos   
    try:
        import llm_router
        cfg = llm_router.load_config()
        usage = llm_router.load_usage()

        for name in ORCHESTRATOR_PRIORITY:
            info = AI_TIERS.get(name, {})
            if not info.get("agentic"):
                continue  # Solo modelos con capacidad ag ntica

            pv = next((p for p in cfg["providers"]
                       if p["name"] == name and p.get("active")), None)
            if not pv:
                continue

            used = usage["counts"].get(name, 0)
            limit = pv.get("daily_limit", 500)
            remaining = limit - used

            # Necesitamos al menos 10 cr ditos para orquestar una sesi n
            if remaining >= 10:
                label = info.get("label", name)
                _orchestrator_cache = {
                    "provider": name, "label": label,
                    "engine": "pool", "checked_at": now
                }
                print(f"[Elektra] Orquestador: {label} ({remaining} cr ditos restantes)")
                return name, label, "pool"
            else:
                print(f"[Elektra] {name}: solo {remaining} cr ditos, insuficiente para orquestar")

    except Exception as e:
        print(f"[Elektra] Error detectando orquestador: {e}")

    # Fallback final: NING N modelo ag ntico tiene cr ditos
    _orchestrator_cache = {
        "provider": None, "label": "SIN CR DITOS AG NTICOS",
        "engine": "none", "checked_at": now
    }
    # Notificar al usuario
    _notify_no_credits()
    return None, "SIN CR DITOS AG NTICOS", "none"


def _notify_no_credits():
    """Notifica al usuario que no hay cr ditos para orquestar."""
    try:
        tg_cfg_path = os.path.join(BASE_DIR, "Configuracion", "master_credentials.json")
        if os.path.exists(tg_cfg_path):
            import requests
            tg_cfg = json.load(open(tg_cfg_path))
            token = tg_cfg.get("telegram_bot", "")
            admin = tg_cfg.get("telegram_admin", "")
            if token and admin:
                msg = (
                    "   PROTOCOLO ELEKTRA: Sin cr ditos\n\n"
                    "Todos los modelos ag nticos han agotado sus cr ditos diarios "
                    "(DeepSeek, Groq, OpenRouter).\n\n"
                    "Opciones:\n"
                    "1. Recargar cr ditos en los proveedores\n"
                    "2. Esperar al reset diario (medianoche UTC)\n"
                    "3. A partir de ahora solo se usar n IAs en la nube "
                    "con capacidad limitada para orquestar"
                )
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": admin, "text": msg}, timeout=5)
    except Exception:
        pass


def _call_orchestrator(system_prompt: str, user_prompt: str) -> tuple:
    """
    Llama al ORQUESTADOR con fallback autom tico:
    Si el modelo actual falla o se queda sin cr ditos a mitad de tarea,
    invalida el cache y prueba el siguiente modelo ag ntico.
    """
    global _orchestrator_cache

    orch_name, orch_label, engine = _select_orchestrator()

    if engine == "none":
        # Sin cr ditos ag nticos   usar cualquier IA disponible como  ltimo recurso
        for fallback in ["groq", "deepseek", "openrouter", "cohere", "cerebras"]:
            result, label = _call_specific_provider(system_prompt, user_prompt, fallback)
            if "Error" not in result:
                return result, f"{label} (sin orquestador   cr ditos agotados)"
        return "[Error: Sin cr ditos en ninguna IA]", "error"

    if engine == "charm":
        # Cuando soy yo (Charm), delego al mejor del pool como proxy
        for name in ORCHESTRATOR_PRIORITY:
            result, label = _call_specific_provider(system_prompt, user_prompt, name)
            if "Error" not in result:
                return result, f"{label} (delegado por Enjambre)"
        # Si todos fallan, invalidar cache e intentar cualquiera
        _orchestrator_cache = {"provider": None, "label": None, "checked_at": None}
        return _call_orchestrator(system_prompt, user_prompt)

    # Pool directo   intentar el orquestador seleccionado
    result, label = _call_specific_provider(system_prompt, user_prompt, orch_name)
    if "Error" not in result:
        return result, label

    # Fall    invalidar cache para que el siguiente intento elija otro modelo
    print(f"[Elektra] Orquestador {orch_label} fall . Rotando...")
    _orchestrator_cache = {"provider": None, "label": None, "checked_at": None}

    # Intentar el siguiente en la prioridad (excluyendo el que fall )
    for name in ORCHESTRATOR_PRIORITY:
        if name == orch_name:
            continue
        result, label = _call_specific_provider(system_prompt, user_prompt, name)
        if "Error" not in result:
            return result, f"{label} (rotaci n por cr ditos)"

    # Todo fall    notificar y usar cualquier IA
    _notify_no_credits()
    for fallback in ["cohere", "cerebras", "ollama_cloud"]:
        result, label = _call_specific_provider(system_prompt, user_prompt, fallback)
        if "Error" not in result:
            return result, f"{label} (emergencia   sin orquestador)"

    return "[Error: Sin cr ditos en ninguna IA]", "error"


def _call_ai(system_prompt: str, user_prompt: str,
             preferred_ais: list = None) -> tuple:
    """
    Llama a la mejor IA disponible (para tareas no-orquestador).
    Devuelve (respuesta, nombre_ia).
    """
    if not preferred_ais:
        preferred_ais = ["deepseek", "groq"]

    pool_prefs = [ai for ai in preferred_ais
                  if AI_TIERS.get(ai, {}).get("engine") == "pool"]

    for ai_name in pool_prefs:
        result, label = _call_specific_provider(system_prompt, user_prompt, ai_name)
        if "Error" not in result:
            return result, label

    return _call_specific_provider(system_prompt, user_prompt, "groq")


#    Motor evolutivo                                                        
def _evaluate_fitness(problem: str, response: str, role: str) -> float:
    """Eval a la calidad de una respuesta (0.0 - 1.0)."""
    eval_prompt = (
        f"Eval a esta respuesta al problema dado.\n\n"
        f"Problema: {problem[:500]}\n"
        f"Rol del agente: {role}\n"
        f"Respuesta: {response[:1500]}\n\n"
        f"Punt a del 0 al 10 seg n:\n"
        f"- Relevancia y precisi n (3 pts)\n"
        f"- Profundidad de an lisis (3 pts)\n"
        f"- Originalidad del enfoque (2 pts)\n"
        f"- Claridad y utilidad pr ctica (2 pts)\n\n"
        f'Responde SOLO con JSON: {{"score": N, "reason": "..."}}'
    )
    try:
        result, orch_label = _call_orchestrator(
            "Eres un evaluador experto. Responde solo con JSON v lido.", eval_prompt)
        clean = result.strip().strip("`")
        if clean.lower().startswith("json"):
            clean = clean[4:].strip()
        data = json.loads(clean)
        return float(data.get("score", 5)) / 10.0
    except Exception:
        return 0.5


def _mutate_prompt(agent: EvAgent, problem_context: str) -> str:
    """Muta el prompt de un agente d bil."""
    strength = "radical" if agent.fitness < 0.5 else "sutil"
    prompt = (
        f"Mejora este system prompt con una mutaci n {strength}.\n\n"
        f"Rol: {agent.role}\nFitness: {agent.fitness:.2f}/1.0\n"
        f"Prompt actual:\n{agent.system_prompt}\n\n"
        f"Contexto: {problem_context[:300]}\n\n"
        f"Reglas: conserva el rol, {'cambia enfoque significativamente' if strength == 'radical' else 'refina sin cambiar la esencia'}. "
        f"Responde SOLO con el nuevo prompt."
    )
    result, _ = _call_orchestrator("Eres un experto en ingenier a de prompts evolutivos.", prompt)
    return result if len(result) > 20 else agent.system_prompt


def _crossover(agent_a: EvAgent, agent_b: EvAgent) -> str:
    """Cruza los prompts de dos agentes."""
    prompt = (
        f"Combina los mejores elementos de estos prompts:\n\n"
        f"A (fitness {agent_a.fitness:.2f}): {agent_a.system_prompt}\n\n"
        f"B (fitness {agent_b.fitness:.2f}): {agent_b.system_prompt}\n\n"
        f"Crea un prompt h brido con las fortalezas de ambos. Responde SOLO con el nuevo prompt."
    )
    result, _ = _call_orchestrator(
        "Eres un experto en s ntesis de instrucciones para sistemas de IA.", prompt)
    return result if len(result) > 20 else agent_a.system_prompt


#    Funci n de detecci n                                                   
def should_activate(task: str) -> bool:
    """Determina si Alpha deber a activar el Protocolo Elektra."""
    t = task.lower()

    # Activaci n expl cita
    explicit = ["elektra", "m xima calidad", "maximum quality", "perfecto",
                "protocolo evolutivo", "multi-agente", "swarm evolution"]
    if any(kw in t for kw in explicit):
        return True

    # Activaci n por contexto de seguridad/criticidad
    security = ["cifrado", "encrypt", "aes", "rsa", "password", "credential",
                "auth", "token", "ssl", "tls", "certificado", "firewall"]
    critical = ["producci n", "production", "deployment", "despliegue",
                "base de datos", "database", "migraci n", "migration",
                "financiero", "payment", "pago", "factura"]

    security_hits = sum(1 for kw in security if kw in t)
    critical_hits = sum(1 for kw in critical if kw in t)

    return security_hits >= 2 or critical_hits >= 2 or (security_hits >= 1 and critical_hits >= 1)


#    Funci n principal                                                      
def evolve_solution(problem: str, task_type: str = "code",
                    generations: int = GENERATIONS) -> dict:
    """
    Ejecuta el Protocolo Elektra: evoluci n multi-agente.

    Args:
        problem: Descripci n del problema a resolver
        task_type: "code", "text" o "analysis"
        generations: N mero de generaciones evolutivas

    Returns:
        dict con synthesis, agents, evolution_log, stats
    """
    config = TASK_ROLES.get(task_type, TASK_ROLES["code"])
    ts = datetime.now().strftime("%H:%M:%S")

    #    Seleccionar ORQUESTADOR (yo o el mejor ag ntico)   
    orch_name, orch_label, orch_engine = _select_orchestrator()

    #    Asignar IAs  NICAS a cada agente (excluyendo el orquestador)   
    provider_map = _assign_unique_providers(config["agents"])

    print(f"\n{'='*60}")
    print(f"--- PROTOCOLO ELEKTRA ACTIVADO [{ts}] ---")
    print(f"   Tipo: {task_type} | Generaciones: {generations}")
    print(f"   Agentes: {len(config['agents'])} (cada uno con IA diferente)")
    print(f"     Orquestador: {orch_label}")
    print(f"{'='*60}")

    # Inicializar agentes   cada uno con su IA  NICA asignada
    agents = []
    for cfg in config["agents"]:
        assigned_provider = provider_map[cfg["id"]]
        label = AI_TIERS.get(assigned_provider, {}).get("label", assigned_provider)
        agents.append(EvAgent(
            id=cfg["id"], role=cfg["role"],
            system_prompt=cfg["prompt"], provider=assigned_provider))
        print(f"   * {cfg['id']:12s} -> {label} (EXCLUSIVO)")
    print()

    evolution_log = []
    best_responses = {}

    for gen in range(1, generations + 1):
        print(f"--- GENERACION {gen}/{generations} ---")
        gen_log = [f"   Generaci n {gen}   "]

        # Cada agente responde USANDO SU IA EXCLUSIVA
        responses = {}
        for agent in agents:
            label = AI_TIERS.get(agent.provider, {}).get("label", agent.provider)
            print(f"   [RUN] {agent.id} [{label}]...", end=" ", flush=True)
            response, used_label = _call_specific_provider(
                agent.system_prompt, problem, agent.provider)
            responses[agent.id] = response
            print(f"  ({used_label})")

        best_responses = responses

        # Evaluar fitness
        for agent in agents:
            score = _evaluate_fitness(problem, responses.get(agent.id, ""), agent.role)
            agent.fitness_history.append(score)
            log_entry = f"    {agent.id}: fitness={score:.2f} (provider={agent.provider})"
            gen_log.append(log_entry)
            print(f"   [FIT] {agent.id}: fitness = {score:.2f}")

        # Evolucionar (salvo  ltima generaci n)
        if gen < generations:
            agents_sorted = sorted(agents, key=lambda a: a.fitness, reverse=True)
            elite_count = max(1, int(len(agents) * ELITE_FRACTION))

            new_agents = []
            #  lite: sobrevive sin cambios
            for agent in agents_sorted[:elite_count]:
                agent.generation += 1
                new_agents.append(agent)
                gen_log.append(f"    {agent.id}:  lite (fitness={agent.fitness:.2f})")

            # Resto: mutan o cruzan
            for agent in agents_sorted[elite_count:]:
                new_agent = copy.deepcopy(agent)
                new_agent.generation += 1

                if random.random() < MUTATION_RATE:
                    best = agents_sorted[0]
                    new_agent.system_prompt = _crossover(new_agent, best)
                    gen_log.append(f"  [CROSS] {agent.id}: crossover con {best.id}")
                    print(f"   [CROSS] {agent.id} -> crossover con {best.id}")
                else:
                    new_agent.system_prompt = _mutate_prompt(new_agent, problem)
                    label = "agresiva" if agent.fitness < 0.5 else "sutil"
                    gen_log.append(f"  [MUT] {agent.id}: mutaci n {label}")
                    print(f"   [MUT] {agent.id} -> mutaci n {label}")

                new_agent.mutations += 1
                new_agents.append(new_agent)

            agents = new_agents

        evolution_log.extend(gen_log)

    # S ntesis final
    print(f"\n--- SINTESIS FINAL [{orch_label}] ---")
    responses_text = "\n\n".join(
        f"--- {aid} ({next((a.role for a in agents if a.id == aid), '?')}) ---\n{resp[:1500]}"
        for aid, resp in best_responses.items()
    )
    synth_prompt = (
        f"Has coordinado {len(agents)} agentes especializados.\n\n"
        f"PROBLEMA: {problem}\n\n"
        f"RESPUESTAS DE LOS AGENTES:\n{responses_text}\n\n"
        f"Sintetiza una respuesta final que:\n"
        f"- Combine las mejores ideas de cada agente\n"
        f"- Resuelva contradicciones entre perspectivas\n"
        f"- Sea superior a cualquier respuesta individual\n"
        f"- Sea clara, estructurada y accionable"
    )
    synthesis, synth_provider = _call_orchestrator(
        "Eres un orquestador de inteligencia colectiva. Sintetizas m ltiples perspectivas "
        "en soluciones superiores.", synth_prompt)

    # Estad sticas
    avg_fitness = sum(a.fitness for a in agents) / len(agents) if agents else 0
    stats = {
        "generations": generations,
        "agents": len(agents),
        "avg_fitness": round(avg_fitness, 3),
        "best_agent": max(agents, key=lambda a: a.fitness).id if agents else "?",
        "total_calls": len(agents) * generations + generations + 1,
        "orchestrator": orch_label,
        "synth_provider": synth_provider,
    }

    print(f"\n{'='*60}")
    print(f"  PROTOCOLO ELEKTRA COMPLETADO")
    print(f"   Orquestador: {orch_label}")
    print(f"   Fitness promedio: {avg_fitness:.2f}")
    print(f"   Mejor agente: {stats['best_agent']}")
    print(f"   Llamadas totales: {stats['total_calls']}")
    print(f"{'='*60}\n")

    return {
        "synthesis": synthesis,
        "agents": [a.to_dict() for a in agents],
        "individual_responses": [
            {"agent": aid, "response": resp} for aid, resp in best_responses.items()
        ],
        "evolution_log": evolution_log,
        "stats": stats,
    }


#    Punto de entrada como skill                                            
def run(prompt: str) -> str:
    """Punto de entrada cuando se invoca como skill desde el router."""
    p = prompt.lower()

    if any(w in p for w in ["estado", "status", "info"]):
        return (
            "  Protocolo Elektra (Swarm Evolution)\n\n"
            "Motor evolutivo multi-agente para tareas cr ticas.\n"
            "3 agentes especializados evolucionan sus prompts en 2 generaciones.\n\n"
            "Tipos de tarea: code, text, analysis\n"
            "Se activa autom ticamente para seguridad, cifrado, producci n.\n"
            "O manualmente diciendo 'Elektra' o 'm xima calidad'."
        )

    # Determinar tipo
    task_type = "code"
    if any(w in p for w in ["texto", "text", "redact", "escrib", "document"]):
        task_type = "text"
    elif any(w in p for w in ["anali", "estudi", "investig", "compar"]):
        task_type = "analysis"

    result = evolve_solution(prompt, task_type=task_type)
    return result["synthesis"]
