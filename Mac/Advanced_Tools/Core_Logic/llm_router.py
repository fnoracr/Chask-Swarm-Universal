"""
llm_router.py — Pool de IAs gratuitas con rotación automática
Alpha orquesta: elige el proveedor con créditos disponibles.
Fallback final: Ollama local.
"""
import os
import sys
import json
import requests
import re
import subprocess
from typing import Dict, Tuple, List
from datetime import datetime, date
# ── Privacy Engine (Microsoft Presidio) ───────────────────────────────────
PRIVACY_SHIELD_ACTIVE = False
privacy_engine = None

def init_privacy():
    global PRIVACY_SHIELD_ACTIVE, privacy_engine
    if privacy_engine is not None: return
    try:
        # Intentar importación relativa al directorio del script
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from privacy_engine import PrivacyEngine
        privacy_engine = PrivacyEngine(country_code="ES") 
        PRIVACY_SHIELD_ACTIVE = True
        print("[Router] Privacy Shield (Microsoft Presidio) Activo.")
    except Exception as e:
        PRIVACY_SHIELD_ACTIVE = False
        print(f"[Router] Privacy Shield no disponible: {e}")

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "Advanced_Tools", "llm_providers_config.json")
USAGE_PATH  = os.path.join(BASE_DIR, "Advanced_Tools", "llm_usage_today.json")

# ── Detección Dinámica de Nombre de la IA ─────────────────────────────────
def get_ai_name() -> str:
    """Extrae el nombre de la IA del archivo soul.md o el prompt."""
    default_name = "[Nombre_IA]"
    try:
        soul_path = os.path.join(BASE_DIR, "soul.md")
        if os.path.exists(soul_path):
            with open(soul_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Buscar patrones comunes como "Tu nombre es X" o "Eres X"
                match = re.search(r"(?i)nombre\s+(?:es|sea)\s+([\w\s]+)", content)
                if match: return match.group(1).strip()
    except: pass
    return default_name

# ── Cargar configuración ──────────────────────────────────────────────────
def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)

def save_usage(usage: dict):
    with open(USAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(usage, f, indent=2)

def load_usage() -> dict:
    today = str(date.today())
    if os.path.exists(USAGE_PATH):
        with open(USAGE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") == today:
            return data
    # Nuevo día → reset
    return {"date": today, "counts": {}}

# ── Cargar contexto del usuario para enriquecer prompts ─────────────────────
def load_context() -> str:
    """
    Construye un system prompt rico con el contexto maestro compilado.
    Se inyecta en TODAS las llamadas a IAs gratuitas para que tengan contexto.
    """
    sections = []
    
    # 1. Cargar el Master System Prompt (Reglas, Identidad, Seguridad unificados)
    master_path = os.path.join(BASE_DIR, "master_system_prompt.md")
    if os.path.exists(master_path):
        try:
            with open(master_path, encoding="utf-8", errors="ignore") as f:
                sections.append(f.read().strip())
        except: pass

    # 2. Archivos de memoria temporal/volátil (opcional, si los daemons no los inyectaron ya)
    files_volatiles = [
        ("memory.md", "## Memoria de Trabajo Actual (Global)"),
        ("projects_memory.md", "## Proyectos en Curso")
    ]
    for fname, header in files_volatiles:
        fpath = os.path.join(BASE_DIR, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    text = f.read().strip()
                if text:
                    sections.append(f"{header}\n{text[:1500]}")
            except: pass

    context_body = "\n\n---\n\n".join(sections) if sections else ""

    # Instrucciones de comportamiento + protocolo de escalado
    header = (
        "Eres [Nombre_IA], asistente IA del ecosistema Chask Swarm de Administrador Enjambre.\n"
        "Responde SIEMPRE en el mismo idioma que el usuario.\n\n"
        "PROTOCOLO DE ESCALADO (OBLIGATORIO):\n"
        "Si el usuario pide una ACCION que requiere herramientas del sistema "
        "(ejecutar scripts, abrir ventanas, navegar web, crear/editar archivos, "
        "interactuar con el PC, hacer pruebas en el ordenador, controlar aplicaciones, "
        "enviar mensajes, etc.), NO expliques que no puedes hacerlo.\n"
        "En su lugar responde EXCLUSIVAMENTE con este JSON y nada mas:\n"
        '{"__escalate__": true, "reason": "descripcion breve en una frase"}\n\n'
        "Para preguntas de conocimiento, memoria o conversacion, responde normalmente.\n\n"
    )
    return header + ("\n".join(["CONTEXTO DEL SISTEMA:", context_body]) if context_body else "")


# ── Normalizar texto (quitar acentos para matching robusto) ──────────────────
import unicodedata
def _norm(text: str) -> str:
    return unicodedata.normalize('NFD', text.lower()).encode('ascii', 'ignore').decode()


# ── Clasificador de complejidad por puntuación ────────────────────────────────
def complexity_score(prompt: str, cfg: dict) -> tuple[int, str]:
    """
    Devuelve (puntuación 0-100, razón).
    >= 60 → [Nombre_IA]. < 60 → Pool gratuito.
    """
    p = _norm(prompt)
    score = 0
    reasons = []

    # ── 0. Mención Directa del Nombre (Escalado Inmediato) ──────────────────
    # Si el mensaje EMPIEZA por un nombre de la IA -> [Nombre_IA] siempre
    ai_name = _norm(get_ai_name())
    direct_names = {ai_name, "enjambre", "chask", "charm", "swarm"}
    first_token = p.split()[0].rstrip(",.;:!?" + chr(161) + chr(191)) if p.split() else ""
    if first_token in direct_names:
        return 100, f"nombre-directo-inicio('{first_token}')"
    # También si el nombre aparece en cualquier parte del texto
    if ai_name in p:
        return 100, f"mencion-directa-nombre('{ai_name}')"

    # ── 1. Acciones que requieren herramientas del sistema (siempre [Nombre_IA])
    ACTION_KEYWORDS = [
        "crea ", "crear ", "crea un", "genera ", "escribe un script", "escribe el codigo",
        "programa ", "implementa ", "desarrolla ", "despliega ",
        "abre el navegador", "navega a", "accede a", "descarga ", "sube ",
        "ejecuta ", "instala ", "mueve ", "borra ", "elimina ",
        "actualiza el archivo", "modifica el archivo", "guarda en",
        "envia un telegram", "manda un telegram", "mandame",
        "sube al servidor", "deploy", "ftp", "git ",
        "create ", "generate ", "write a script", "implement ", "deploy ",
        "open the browser", "navigate to", "download ", "upload ",
        "execute ", "install ", "delete ", "send a telegram",
    ]
    for kw in ACTION_KEYWORDS:
        if _norm(kw.strip()) in p:
            score += 45
            reasons.append(f"accion-sistema('{kw.strip()}')")
            break  # uno basta para ser [Nombre_IA]

    # ── 2. Análisis/síntesis profunda — ACUMULA todos los matches (sin break)
    DEEP_ANALYSIS = [
        "explica en detalle", "analisis profundo", "analiza en profundidad",
        "ensayo sobre", "ensayo acerca", "informe sobre", "comparativa entre", "diferencias entre",
        "ventajas e inconvenientes", "pros y contras", "tesis sobre", "tesis acerca",
        "algoritmo", "arquitectura de", "diseno de sistema", "patron de diseno",
        "machine learning", "deep learning", "inteligencia artificial",
        "redes neuronales", "neural network", "transformer", "genetico", "genetic",
        "criptografia", "cryptography", "seguridad informatica",
        "matematicas avanzadas", "calculo diferencial", "algebra lineal",
        "explica como funciona", "cual es la diferencia entre", "como funciona",
        "explica el concepto", "que es un", "que son los",
        "explain in detail", "deep analysis", "essay about", "report on",
        "compare and contrast", "advantages and disadvantages",
        "system architecture", "design pattern", "how does",
    ]
    deep_hits = [kw for kw in DEEP_ANALYSIS if _norm(kw) in p]
    if deep_hits:
        score += min(35 * len(deep_hits), 50)  # cap en 50 para no saturar
        reasons.append(f"analisis-profundo({len(deep_hits)} matches: {', '.join(deep_hits[:2])})")

    # ── 3. Requiere memoria de proyectos pasados
    MEMORY_REFS = [
        "que hicimos", "que estabamos haciendo", "lo que me dijiste",
        "el proyecto de", "el proyecto chask", "proyecto de chask", "chask swarm", "chask hive",
        "recuerdas cuando", "nuestra conversacion",
        "lo que hablamos", "lo que acordamos",
        "what we did", "what we were doing", "you told me", "the project",
        "do you remember", "our conversation", "what we agreed",
    ]
    for kw in MEMORY_REFS:
        if _norm(kw) in p:
            score += 15 # Reducido de 25
            reasons.append(f"referencia-memoria('{kw}')")
            break

    # ── 4. Triggers explícitos del config
    settings = cfg.get("settings", {})
    for trigger in settings.get("complex_task_triggers", []):
        if _norm(trigger) in p:
            score += 30
            reasons.append(f"trigger-config('{trigger}')")
            break

    # ── 5. Longitud del prompt (solo suma puntos menores, NO es determinante solo)
    if len(prompt) > 500:
        score += 10
        reasons.append("prompt-largo")
    elif len(prompt) > 200:
        score += 5

    # ── 6. Signos de tarea simple (descuentan puntos)
    SIMPLE_KEYWORDS = [
        "que hora", "cual es la capital", "como se dice", "traduce ",
        "cuantos", "quien es", "cuando nacio", "definicion de",
        "receta de", "ingredientes de", "como se hace el",
        "what time", "what is the capital", "how do you say", "translate ",
        "how many", "who is", "when was", "definition of",
        "recipe for", "ingredients for",
    ]
    for kw in SIMPLE_KEYWORDS:
        if _norm(kw) in p:
            score -= 25
            reasons.append(f"tarea-simple('{kw}')")
            break

    score = max(0, min(100, score))
    reason = ", ".join(reasons) if reasons else "sin-triggers"
    return score, reason


def is_complex(prompt: str, cfg: dict) -> bool:
    score, reason = complexity_score(prompt, cfg)
    verdict = score >= 60  # Umbral de Enjambre: 60 = Solo tareas de sistema reales o mención directa de Enjambre
    print(f"[Router] Complejidad: {score}/100 ({reason}) -> {'[Nombre_IA]' if verdict else 'Pool gratuito'}")
    return verdict

# ── Elegir el mejor proveedor por CAPACIDAD para la tarea ─────────────────
# Mapa de capacidades: qué proveedores son BUENOS y MALOS para cada tipo
TASK_SKILLS = {
    "código": {"best": ["deepseek", "groq"], "exclude": []},
    "code": {"best": ["deepseek", "groq"], "exclude": []},
    "programa": {"best": ["deepseek", "groq"], "exclude": []},
    "script": {"best": ["deepseek", "groq"], "exclude": []},
    "razonamiento": {"best": ["deepseek", "groq"], "exclude": []},
    "reasoning": {"best": ["deepseek", "groq"], "exclude": []},
    "resumen": {"best": ["cohere", "groq"], "exclude": []},
    "resume": {"best": ["cohere", "groq"], "exclude": []},
    "summarize": {"best": ["cohere", "groq"], "exclude": []},
    "traduce": {"best": ["groq", "deepseek"], "exclude": []},
    "translate": {"best": ["groq", "deepseek"], "exclude": []},
    "traducción": {"best": ["groq", "deepseek"], "exclude": []},
    "clasificación": {"best": ["cohere", "cerebras"], "exclude": []},
    "classify": {"best": ["cohere", "cerebras"], "exclude": []},
    "receta": {"best": ["groq", "cerebras", "openrouter"], "exclude": []},
    "recipe": {"best": ["groq", "cerebras", "openrouter"], "exclude": []},
    "explica": {"best": ["deepseek", "groq"], "exclude": []},
    "explain": {"best": ["deepseek", "groq"], "exclude": []},
    "analiza": {"best": ["deepseek", "groq"], "exclude": ["cerebras"]},
    "analyze": {"best": ["deepseek", "groq"], "exclude": ["cerebras"]},
    "matemáticas": {"best": ["deepseek", "groq"], "exclude": ["cohere", "cerebras"]},
    "math": {"best": ["deepseek", "groq"], "exclude": ["cohere", "cerebras"]},
}

def pick_provider(prompt: str, cfg: dict, usage: dict) -> dict | None:
    """Selecciona el proveedor más capaz para la tarea, con créditos disponibles."""
    p = _norm(prompt)

    # 1. Detectar tipo de tarea y proveedores ideales/excluidos
    best_names = []
    excluded_names = set()
    for keyword, skills in TASK_SKILLS.items():
        if _norm(keyword) in p:
            best_names.extend(skills["best"])
            excluded_names.update(skills["exclude"])

    # 2. Construir lista de proveedores activos con créditos
    active = []
    for pv in cfg["providers"]:
        if not pv.get("active"):
            continue
        used = usage["counts"].get(pv["name"], 0)
        limit = pv.get("daily_limit", 500)
        if used >= limit:
            print(f"[Router] {pv['name']}: límite diario alcanzado ({used}/{limit})")
            continue
        if pv["name"] in excluded_names:
            print(f"[Router] {pv['name']}: excluido para este tipo de tarea")
            continue
        active.append(pv)

    if not active:
        # Fallback: Ollama Cloud
        return next((pv for pv in cfg["providers"] if pv["name"] == "ollama_cloud"), None)

    # 3. Puntuar: proveedores "best" para la tarea van primero
    def score(pv):
        s = 0
        if pv["name"] in best_names:
            # Más puntos cuanto más arriba en la lista best_names
            try:
                s = 100 - best_names.index(pv["name"]) * 10
            except ValueError:
                s = 0
        # Desempate por prioridad original
        s -= pv.get("priority", 99) * 0.1
        return s

    active.sort(key=score, reverse=True)
    chosen = active[0]
    print(f"[Router] Mejor IA para esta tarea: {chosen['name']} ({chosen.get('label', '')})")
    return chosen

# -- Llamar a un proveedor -------------------------------------------------
def call_provider(provider: dict, prompt: str, system_prompt: str = "") -> str | None:
    name = provider["name"]
    compatible = provider.get("compatible", "openai")
    api_key = provider.get("api_key", "")
    model = provider.get("model", "")

    try:
        # ── OpenAI-compatible (DeepSeek, Groq, OpenRouter, Mistral) ──────
        if compatible == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key,
                            base_url=provider.get("base_url", "https://api.openai.com/v1"))
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Soporte para rotación de modelos si existe fallback_models
            models_to_try = [model]
            if "fallback_models" in provider:
                models_to_try.extend([m for m in provider["fallback_models"] if m != model])

            # ¡NUEVO!: Aleatorizar si la config lo indica (ej: OpenRouter Pool)
            if provider.get("use_pool_randomly") and "fallback_models" in provider:
                import random
                unique_models = list(set([model] + provider["fallback_models"]))
                random.shuffle(unique_models)
                models_to_try = unique_models

            for try_model in models_to_try:
                try:
                    resp = client.chat.completions.create(
                        model=try_model, messages=messages, max_tokens=2048, timeout=30
                    )
                    content = resp.choices[0].message.content.strip()
                    if content:
                        if try_model != model:
                            print(f"[Router] {name}: modelo {model} falló, usando {try_model}")
                        return content
                except Exception as model_err:
                    print(f"[Router] {name} modelo {try_model} falló: {model_err}")
                    continue
            return None

        # ── Google Gemini ─────────────────────────────────────────────────
        elif compatible == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(model)
            full = (system_prompt + "\n\n" + prompt) if system_prompt else prompt
            resp = m.generate_content(full)
            return resp.text.strip()

        # ── Cohere ───────────────────────────────────────────────────────
        elif compatible == "cohere":
            import cohere
            co = cohere.Client(api_key)
            resp = co.chat(model=model, message=prompt,
                           preamble=system_prompt or None)
            return resp.text.strip()

        # ── Ollama Cloud (ollama Python lib + Bearer auth + model rotation) ──
        elif compatible == "ollama_cloud":
            from ollama import Client
            client = Client(
                host=provider.get("base_url", "https://ollama.com"),
                headers={"Authorization": f"Bearer {api_key}"}
            )
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            # Intentar modelo principal + fallbacks
            models_to_try = [model] + [m for m in provider.get("fallback_models", []) if m != model]
            for try_model in models_to_try:
                try:
                    resp = client.chat(model=try_model, messages=messages, stream=False)
                    content = resp["message"]["content"].strip()
                    if content:
                        if try_model != model:
                            print(f"[Router] Ollama Cloud: modelo {model} no disponible, usando {try_model}")
                        return content
                except Exception as model_err:
                    print(f"[Router] Ollama Cloud modelo {try_model} falló: {model_err}")
                    continue
            return None  # Todos los modelos fallaron

        # ── Ollama local (último recurso sin internet) ────────────────────
        elif compatible == "ollama":
            try:
                # Usar llamada limpia HTTP a la API de Ollama para evitar códigos ANSI interactivas de terminal
                url = f"{provider.get('base_url', 'http://localhost:11434')}/api/generate"
                r = requests.post(url, json={
                    "model": model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                }, timeout=180)
                if r.status_code == 200:
                    return r.json().get("response", "").strip()
            except Exception as err:
                print(f"[Router] Error llamando a Ollama local via HTTP: {err}")
            
            # Fallback seguro con subprocess si falla el puerto HTTP
            full = (system_prompt + "\n\n" + prompt) if system_prompt else prompt
            result = subprocess.run(
                ["ollama", "run", model, full],
                capture_output=True, timeout=300
            )
            # Decodificar explícitamente en UTF-8 con ignore para evitar codificación de Windows cp1252 rota
            stdout_str = result.stdout.decode("utf-8", errors="ignore")
            # Limpiar secuencias de escape ANSI por si acaso
            clean_txt = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b[78]|\x1b\[[0-9;?]*[mK]|\x08', '', stdout_str)
            return clean_txt.strip() or None

    except Exception as e:
        print(f"[Router] Error en {name}: {e}")
        return None

# -- Funcion principal: route() --------------------------------------------
def route(prompt: str, system_prompt: str = "", source: str = "", force_free: bool = False, forced_mode: str = "", apply_privacy: bool = True) -> dict:
    """
    Enruta la tarea al mejor proveedor disponible.
    Devuelve: {"engine": nombre, "response": texto, "reason": explicación}
    apply_privacy=False → deshabilita el Privacy Shield para este prompt (chat interactivo).
    apply_privacy=True  → aplica Presidio antes de enviar (documentos, procesamiento batch).
    """
    # -- PRIVACIDAD AUTOMATICA (Microsoft Presidio) --
    # Movido como middleware obligatorio justo antes de enviar al proveedor externo.

    # -- SLASH COMMANDS (Atajos rápidos) ─────────────────────────────────
    try:
        from slash_commands import is_command, parse_command
        if is_command(prompt):
            cmd_result = parse_command(prompt)
            if cmd_result.get("handled"):
                return {
                    "engine": "slash_command",
                    "response": cmd_result["response"],
                    "reason": "Slash command ejecutado directamente"
                }
            elif cmd_result.get("raw_query"):
                prompt = cmd_result["raw_query"]
                if cmd_result.get("mode"):
                    print(f"[Router] Slash command → modo forzado: {cmd_result['mode']}")
    except Exception:
        pass

    # -- AUTO-EVOLUCIÓN: Detectar correcciones ─────────────────────────
    try:
        from auto_evolve_prompts import check_for_correction
        lesson = check_for_correction(prompt)
        if lesson:
            print(f"[Router] Lección aprendida automáticamente: {lesson[:60]}")
    except Exception:
        pass

    cfg   = load_config()
    usage = load_usage()

    # -- PRIMERA BARRERA: Nombres directos -> [Nombre_IA] SIEMPRE --
    p_lower = _norm(prompt)
    direct_names = {_norm(get_ai_name()), "enjambre", "chask", "charm", "swarm"}
    first_token = p_lower.split()[0].rstrip(",.;:!?" + chr(161) + chr(191)) if p_lower.split() else ""
    if first_token in direct_names:
        return {
            "engine": "charm",
            "response": None,
            "reason": f"Nombre directo '{first_token}' -> [Nombre_IA]"
        }

    # Tareas complejas → [Nombre_IA]
    if not force_free and is_complex(prompt, cfg):
        score, reason = complexity_score(prompt, cfg)
        return {
            "engine": "charm",
            "response": None,
            "reason": f"Tarea compleja ({score}/100: {reason}) -> [Nombre_IA]"
        }

    # Elegir proveedor gratuito
    provider = pick_provider(prompt, cfg, usage)
    if not provider:
        return {
            "engine": "charm",
            "response": None,
            "reason": "Sin proveedores disponibles -> [Nombre_IA]"
        }

    # -- Enriquecer el system prompt con contexto real y REGLA DEL ESPEJO --
    context = load_context()
    mirror_rule = ""
    if source == "telegram":
        mirror_rule = "\nIMPORTANTE: El usuario te escribe por TELEGRAM. Mantén una respuesta concisa y profesional."
    elif source == "web":
        mirror_rule = "\nIMPORTANTE: El usuario te escribe por la INTERFAZ WEB."

    # -- DETECCIÓN DE MODO DE AGENTE --
    mode_prompt = ""
    mode_preferred_model = None
    mode_result = None
    is_forced_teacher = False  # True SOLO si Administrador eligió modo Profesor explícitamente
    try:
        from mode_router import detect_mode, get_mode_by_id
        if forced_mode:
            mode = get_mode_by_id(forced_mode)
            if mode:
                mode_result = {"mode": mode, "score": 100, "reason": "forced"}
                # Marcar si el modo forzado ES el de Profesor
                if forced_mode == "teacher":
                    is_forced_teacher = True
        
        if not mode_result:
            mode_result = detect_mode(prompt)
            
        if mode_result and mode_result.get("score", 0) > 0:
            mode = mode_result["mode"]
            mode_prompt = mode.get("system_prompt", "")
            mode_preferred_model = mode.get("model_preference")
            print(f"[Router] Modo detectado: {mode['name']} (score={mode_result['score']}, {mode_result['reason']})")
    except Exception as e:
        print(f"[Router] Error en detect_mode: {e}")

    # -- INTEGRACIÓN EXCLUSIVA DE TEMARIOS ESCOLARES (Modo Profesor + Qdrant) --
    # IMPORTANTE: El curriculum SOLO se activa si el usuario eligió explícitamente
    # el modo Profesor. La auto-detección semántica NO debe disparar preguntas de
    # curso/país/asignatura. Si el modo no está forzado, la IA responde con normalidad.
    curriculum_context = ""
    if is_forced_teacher:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from curriculum_manager import get_or_research_curriculum
            curriculum_context = get_or_research_curriculum(prompt)
            if curriculum_context:
                print("[Router] Temario escolar recuperado/investigado con éxito desde Qdrant.")
        except Exception as e:
            print(f"[Router] Error cargando temarios del modo profesor: {e}")

    effective_system = context + mirror_rule
    if curriculum_context:
        effective_system = curriculum_context + "\n\n" + effective_system
    # El system prompt del modo Profesor solo se aplica si fue FORZADO por el usuario.
    # Si fue auto-detectado, se ignora para que la IA responda normalmente sin modo socrático.
    apply_mode_prompt = mode_prompt
    if mode_result and mode_result.get("mode", {}).get("id") == "teacher" and not is_forced_teacher:
        apply_mode_prompt = ""  # Ignorar system prompt socrático en auto-detección
    if apply_mode_prompt:
        effective_system = apply_mode_prompt + "\n\n" + effective_system
    if system_prompt:
        effective_system = system_prompt + ("\n\n" + effective_system)

    # -- ENRIQUECIMIENTO CON CONOCIMIENTO INDEXADO (RAG Universal) --
    knowledge_offer = ""
    try:
        from knowledge_orchestrator import enrich_prompt
        effective_system, knowledge_offer = enrich_prompt(prompt, effective_system)
    except Exception as e:
        pass  # No disponible, continuar sin RAG

    pname = provider["name"]
    # Sobreescribir modelo local si el modo especifica uno preferido
    if mode_preferred_model and pname in ["ollama_local", "ollama"]:
        provider["model"] = mode_preferred_model
        print(f"[Router] Sobreescribiendo modelo local a {mode_preferred_model} por modo de agente.")

    print(f"[Router] Enrutando a {pname} (source={source})...")

    # -- [MIDDLEWARE: ESCUDO PII OBLIGATORIO] --
    # Se aplica siempre y sin excepciones para cualquier proveedor que no sea local.
    is_local = (provider.get("compatible") == "ollama" or pname in ["ollama_local", "ollama"])
    if not is_local:
        init_privacy()
        if PRIVACY_SHIELD_ACTIVE and privacy_engine:
            original_prompt = prompt
            prompt = privacy_engine.anonymize(prompt)
            effective_system = privacy_engine.anonymize(effective_system)
            if prompt != original_prompt:
                print(f"[Router] Escudo PII interceptó payload hacia {pname}. Datos sensibles anonimizados.")

    response = call_provider(provider, prompt, effective_system)

    if response:
        # Limpiar cadena de pensamiento (Thinking Process) residual de IAs gratuitas/razonamiento
        original_len = len(response)
        # 0. Remover caracteres de control y secuencias de escape ANSI por completo para que los límites de palabras (\b) coincidan perfectamente
        response = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b[78]|\x1b\[[0-9;?]*[mK]|\x08', '', response)
        # 1. Remover etiquetas <think>...</think>
        response = re.sub(r'(?is)<think>.*?</think>\s*', '', response)
        # 2. Remover bloques "Thinking... ...done thinking."
        response = re.sub(r'(?is)\bThinking\b.*?\bdone thinking\b\.?\s*', '', response)
        # 3. Remover bloques "Thinking Process:" iniciales
        response = re.sub(r'(?is)^Thinking Process:.*?(?=\n\n|\n[A-Z\u00c0-\u00ff]|\Z)', '', response)
        response = response.strip()
        if len(response) != original_len:
            print(f"[Router] Cadena de pensamiento de {pname} eliminada con éxito.")

    # Añadir oferta de base de conocimiento al final de la respuesta
    if response and knowledge_offer:
        response = response + f"\n\n---\n{knowledge_offer}"

    if response:
        usage["counts"][pname] = usage["counts"].get(pname, 0) + 1
        save_usage(usage)
        
        # ── Autogestión de respuesta (Mirroring) ──────────────────────
        # Si viene de Telegram y NO escaló, lo mandamos nosotros mismos
        if source == "telegram" and "__escalate__" not in response:
            try:
                # Llamar al responder de forma no bloqueante para el flujo principal
                responder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responder.py")
                subprocess.Popen([sys.executable, responder_path, "--telegram", response])
            except: pass

        return {
            "engine": pname,
            "response": response,
            "reason": f"Pool gratuito → {pname} (con contexto)"
        }

    # Falló este proveedor → marcar y reintentar
    usage["counts"][pname] = provider.get("daily_limit", 500)
    save_usage(usage)
    return route(prompt, system_prompt, source, force_free=True)

def get_status() -> str:
    """Devuelve un resumen del estado de créditos de todos los proveedores."""
    cfg   = load_config()
    usage = load_usage()
    lines = [f"Status del Pool de IAs - {usage['date']}"]
    for pv in cfg["providers"]:
        if not pv.get("active"): continue
        used  = usage["counts"].get(pv["name"], 0)
        limit = pv.get("daily_limit", 0)
        pct   = int((used / limit) * 100) if limit else 0
        bar   = "#" * (pct // 10) + "-" * (10 - pct // 10)
        lines.append(f"  {pv['name']:<12} [{bar}] {used}/{limit}")
    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(get_status())
    else:
        prompt = " ".join(sys.argv[1:]) or "¿Cuál es la capital de Francia?"
        result = route(prompt)
        print(f"\n[{result['engine'].upper()}] {result['reason']}")
        if result["response"]:
            print(result["response"])
        else:
            print("-> Redirigir a [Nombre_IA]")
