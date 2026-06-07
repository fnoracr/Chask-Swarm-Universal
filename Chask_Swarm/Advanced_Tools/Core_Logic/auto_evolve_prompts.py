"""
auto_evolve_prompts.py — Pilar 2: Auto-Evolución de System Prompts
===================================================================
Detecta cuando Fernando corrige a Enjambre y extrae automáticamente
una lección aprendida para añadirla a directives.md.

Flujo:
  1. Detecta correcciones (frases: "no", "para", "así no", "te dije")
  2. Analiza la corrección con modelo local barato (phi4-mini)
  3. Genera una regla candidata
  4. Valida contra reglas existentes (no duplicar)
  5. Escribe en directives.md sección 12
  6. Persiste en memoria vectorial

Uso desde llm_router o telegram_daemon:
    from auto_evolve_prompts import check_for_correction
    lesson = check_for_correction(user_message, chask_previous_response)
    if lesson:
        # Enjambre aprendió algo nuevo
"""

import re
import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path

import requests

log = logging.getLogger("auto_evolve")

# ─── Configuración ────────────────────────────────────────────
DIRECTIVES_FILE  = r"C:\Users\fnora\Desktop\Enjambre Datos\directives.md"
DIRECTIVES_CORE  = r"C:\Program Files\Chask_Swarm\directives.md"
LESSONS_FILE     = r"C:\Program Files\Chask_Swarm\Advanced_Tools\learned_lessons.json"
OLLAMA_URL       = "http://localhost:11434"
LOCAL_MODEL      = "phi4-mini:latest"
TOOLS_DIR        = r"C:\Program Files\Chask_Swarm\Advanced_Tools"

# ─── Patrones de corrección ───────────────────────────────────
CORRECTION_PATTERNS = [
    # Español
    r"(?i)\b(no,?\s+(?:eso|así|esa|ese)\s+no)",
    r"(?i)\b(para[, ]+no\s+(?:hagas|hag|quiero))",
    r"(?i)\b(te\s+(?:dije|digo|he\s+dicho)\s+que)",
    r"(?i)\b(eso\s+(?:no\s+es|está\s+mal|es\s+incorrecto))",
    r"(?i)\b(no\s+(?:hagas|implementes|pongas|uses|metas))",
    r"(?i)\b(quita(?:lo|la|los|las)?|elimina(?:lo|la)?|borra(?:lo|la)?)",
    r"(?i)\b((?:eso|así)\s+no\s+(?:es|era|funciona|va))",
    r"(?i)\b(mal[., ])",
    r"(?i)\b(detenlo|para(?:lo)?[.,!])",
    r"(?i)\b(no\s+funciona\s+bien)",
    r"(?i)\b(arregla(?:lo)?|corrígelo|corrige(?:lo)?)",
    r"(?i)\b(prefiero\s+(?:que|sin|con|no))",
    r"(?i)\b(mejor\s+(?:hazlo|haz|usa|pon|sin))",
    r"(?i)\b(nunca\s+(?:hagas|uses|pongas|implementes))",
    r"(?i)\b(siempre\s+(?:hazlo|haz|usa|pon))",
    # Inglés (por si acaso)
    r"(?i)\b(don'?t\s+(?:do|use|add|implement))",
    r"(?i)\b(stop|wrong|incorrect|bad)",
    r"(?i)\b(I\s+(?:told|said|asked)\s+you)",
]

# ─── Score mínimo para considerar corrección real ─────────────
MIN_CORRECTION_SCORE = 2  # Al menos 2 patrones deben matchear


def detect_correction(user_message: str) -> tuple[bool, int, list[str]]:
    """
    Detecta si el mensaje del usuario contiene una corrección a Enjambre.
    
    Returns:
        (is_correction, score, matched_patterns)
    """
    score   = 0
    matched = []

    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, user_message):
            score += 1
            matched.append(pattern[:40])

    # Heurísticas adicionales
    msg_lower = user_message.lower()

    # Mensajes cortos negativos son correcciones fuertes
    if len(user_message.split()) <= 5:
        if any(w in msg_lower for w in ["no", "para", "mal", "stop", "quita"]):
            score += 1

    # Signos de exclamación + negación
    if "!" in user_message and any(w in msg_lower for w in ["no", "para", "mal"]):
        score += 1

    return score >= MIN_CORRECTION_SCORE, score, matched


def extract_lesson(user_message: str, chask_response: str = "") -> str | None:
    """
    Usa modelo local para extraer la lección de la corrección.
    
    Returns:
        La lección como string, o None si no se pudo extraer.
    """
    prompt = f"""Analiza esta interacción donde el usuario corrige a la IA:

RESPUESTA PREVIA DE LA IA: {chask_response[:500] if chask_response else '(no disponible)'}

CORRECCIÓN DEL USUARIO: {user_message}

Extrae UNA regla clara y concisa que la IA debería seguir en el futuro para evitar esta corrección.
La regla debe ser específica y accionable, no genérica.

Formato de respuesta (SOLO la regla, nada más):
No [hacer X] cuando/sin [condición]. [Alternativa preferida].

Regla:"""

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": LOCAL_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 100}
            },
            timeout=30
        )
        if resp.status_code == 200:
            lesson = resp.json().get("response", "").strip()
            # Limpiar
            lesson = lesson.split("\n")[0].strip()  # Solo primera línea
            lesson = re.sub(r'^(regla:|regla\s*\d*:?)\s*', '', lesson, flags=re.I)
            if len(lesson) > 20 and len(lesson) < 300:
                return lesson
    except Exception as e:
        log.warning(f"Error extrayendo lección con {LOCAL_MODEL}: {e}")

    # Fallback: extraer directamente del mensaje del usuario
    if "prefiero" in user_message.lower():
        return user_message.strip()
    if "nunca" in user_message.lower() or "siempre" in user_message.lower():
        return user_message.strip()

    return None


def _load_lessons() -> list[dict]:
    """Carga las lecciones aprendidas del fichero JSON."""
    if os.path.exists(LESSONS_FILE):
        try:
            with open(LESSONS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_lessons(lessons: list[dict]):
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)


def _is_duplicate(lesson_text: str, existing: list[dict]) -> bool:
    """Verifica si una lección ya existe (por hash o similitud textual)."""
    h = hashlib.md5(lesson_text.lower().encode()).hexdigest()
    for les in existing:
        if les.get("hash") == h:
            return True
        # Similitud básica por palabras compartidas
        existing_words = set(les.get("text", "").lower().split())
        new_words      = set(lesson_text.lower().split())
        if existing_words and new_words:
            overlap = len(existing_words & new_words) / max(len(existing_words), len(new_words))
            if overlap > 0.7:
                return True
    return False


def persist_lesson(lesson_text: str) -> bool:
    """
    Persiste una lección aprendida:
    1. En lessons.json (para consulta rápida)
    2. En directives.md sección 12 (para el system prompt)
    3. En memoria vectorial (para búsqueda semántica)
    """
    lessons = _load_lessons()

    if _is_duplicate(lesson_text, lessons):
        log.info(f"Lección duplicada ignorada: {lesson_text[:50]}")
        return False

    # 1. Guardar en JSON
    lesson_num = len(lessons) + 1
    entry = {
        "id": f"L{lesson_num}",
        "text": lesson_text,
        "hash": hashlib.md5(lesson_text.lower().encode()).hexdigest(),
        "date": datetime.now().isoformat(),
        "source": "auto_evolve",
    }
    lessons.append(entry)
    _save_lessons(lessons)

    # 2. Añadir a directives.md
    date_str = datetime.now().strftime("%Y-%m-%d")
    directive_line = f"- **L{lesson_num}** ({date_str}): {lesson_text}\n"

    for directives_path in [DIRECTIVES_FILE, DIRECTIVES_CORE]:
        try:
            if os.path.exists(directives_path):
                content = Path(directives_path).read_text(encoding="utf-8")
                # Buscar la sección 12 de lecciones aprendidas
                marker = "## 12. Lecciones Aprendidas"
                if marker in content:
                    # Insertar antes de la siguiente sección o al final
                    next_section = re.search(r'\n## \d+\.', content[content.index(marker) + len(marker):])
                    if next_section:
                        insert_pos = content.index(marker) + len(marker) + next_section.start()
                    else:
                        insert_pos = len(content)
                    
                    # Insertar la nueva lección
                    content = content[:insert_pos] + directive_line + content[insert_pos:]
                    Path(directives_path).write_text(content, encoding="utf-8")
                    log.info(f"Lección L{lesson_num} añadida a {directives_path}")
        except Exception as e:
            log.warning(f"Error escribiendo en {directives_path}: {e}")

    # 3. Guardar en memoria vectorial
    try:
        sys.path.insert(0, TOOLS_DIR)
        from evolutionary_memory import add_memory
        add_memory(f"[LECCIÓN APRENDIDA] {lesson_text}", "fernando")
    except Exception as e:
        log.warning(f"Error guardando en memoria evolutiva: {e}")

    log.info(f"Nueva lección aprendida L{lesson_num}: {lesson_text[:60]}")
    return True


def check_for_correction(user_message: str,
                          chask_previous_response: str = "") -> str | None:
    """
    API principal: verifica si el mensaje es una corrección y aprende.
    
    Returns:
        El texto de la lección aprendida, o None si no hubo corrección.
    """
    is_correction, score, patterns = detect_correction(user_message)

    if not is_correction:
        return None

    log.info(f"Corrección detectada (score={score}): {user_message[:60]}")

    # Extraer la lección
    lesson = extract_lesson(user_message, chask_previous_response)
    if not lesson:
        log.info("No se pudo extraer una lección clara de la corrección")
        return None

    # Persistir
    if persist_lesson(lesson):
        return lesson

    return None


def get_all_lessons() -> list[dict]:
    """Devuelve todas las lecciones aprendidas."""
    return _load_lessons()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Test con correcciones de ejemplo
            tests = [
                "no, eso no es lo que te pedí",
                "para, no funciona bien",
                "te dije que no uses debounce",
                "prefiero que lo hagas sin optimizaciones innecesarias",
                "quítalo, está mal",
                "hola, como estás",  # No es corrección
                "muéstrame el archivo",  # No es corrección
            ]
            for t in tests:
                is_c, score, _ = detect_correction(t)
                print(f"{'✅' if is_c else '  '} score={score} | {t}")

        elif sys.argv[1] == "list":
            lessons = get_all_lessons()
            for l in lessons:
                print(f"  [{l['id']}] ({l['date'][:10]}) {l['text']}")
            if not lessons:
                print("  Sin lecciones registradas.")

        elif sys.argv[1] == "check":
            msg = " ".join(sys.argv[2:])
            result = check_for_correction(msg)
            if result:
                print(f"✅ Lección aprendida: {result}")
            else:
                print("No se detectó corrección.")
    else:
        print("Uso: python auto_evolve_prompts.py [test|list|check <mensaje>]")
