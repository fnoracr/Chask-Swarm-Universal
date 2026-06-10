"""
reflection_engine.py — Motor de Auto-Evolución de Prompts
=========================================================
Cuando Fernando corrige a Enjambre, este motor analiza la corrección,
extrae una lección aprendida, y la persiste en:
1. directives.md (como regla aprendida)
2. Qdrant (memoria vectorial a largo plazo)

Uso:
  python reflection_engine.py learn "No implementar debounce sin que Fernando lo pida"
  python reflection_engine.py reflect  (reflexión de fin de sesión)
  python reflection_engine.py lessons   (listar lecciones aprendidas)
"""
import os
import sys
import json
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVANCED_DIR = os.path.dirname(os.path.abspath(__file__))
DIRECTIVES_CORE = os.path.join(BASE_DIR, "directives.md")
DIRECTIVES_USER = os.path.join(os.path.expanduser("~"), "Desktop", "Enjambre Datos", "directives.md")
LESSONS_FILE = os.path.join(BASE_DIR, "Configuracion", "learned_lessons.json")
SOUL_FILE = os.path.join(BASE_DIR, "soul.md")

# Router LLM para análisis barato
sys.path.insert(0, ADVANCED_DIR)
try:
    import llm_router
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False

# Qdrant memory manager
try:
    from qdrant_memory_manager import save_memory, search_memory
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


def load_lessons():
    """Carga las lecciones aprendidas del archivo JSON."""
    if os.path.exists(LESSONS_FILE):
        with open(LESSONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_lessons(lessons):
    """Guarda las lecciones al archivo JSON."""
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, indent=2, ensure_ascii=False)


def learn(correction: str, context: str = ""):
    """
    Registra una corrección de Fernando como lección aprendida.
    
    Args:
        correction: La corrección o preferencia expresada por Fernando
        context: Contexto opcional de la tarea donde ocurrió
    """
    lessons = load_lessons()
    
    # Verificar duplicados (búsqueda simple por similitud textual)
    for existing in lessons:
        if correction.lower().strip() in existing.get("lesson", "").lower():
            print(f"[Reflection] Lección ya registrada: {correction[:50]}...")
            return False
    
    lesson_entry = {
        "id": len(lessons) + 1,
        "ts": datetime.now().isoformat(),
        "lesson": correction,
        "context": context,
        "source": "user_correction",
        "applied": False
    }
    
    lessons.append(lesson_entry)
    save_lessons(lessons)
    
    # Persistir en Qdrant si disponible
    if QDRANT_AVAILABLE:
        try:
            save_memory(
                text=f"LECCIÓN APRENDIDA: {correction}",
                collection="chask_lessons",
                metadata={"type": "lesson", "context": context}
            )
        except Exception as e:
            print(f"[Reflection] Error guardando en Qdrant: {e}")
    
    # Añadir al archivo de directivas del usuario
    _append_to_directives(lesson_entry)
    
    print(f"[Reflection] OK Leccion #{lesson_entry['id']} registrada: {correction[:60]}...")
    return True


def _append_to_directives(lesson):
    """Añade una lección aprendida a directives.md."""
    target = DIRECTIVES_USER if os.path.exists(DIRECTIVES_USER) else DIRECTIVES_CORE
    
    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Buscar sección de lecciones aprendidas
        header = "## 12. Lecciones Aprendidas (Auto-Evolución)"
        if header not in content:
            content += f"\n\n{header}\n\n"
            content += "Las siguientes reglas fueron aprendidas automáticamente a partir de correcciones de Fernando:\n\n"
        
        # Añadir la lección
        lesson_line = f"- **L{lesson['id']}** ({lesson['ts'][:10]}): {lesson['lesson']}\n"
        
        if lesson['lesson'] not in content:
            content += lesson_line
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[Reflection] Directiva actualizada: {target}")
    except Exception as e:
        print(f"[Reflection] Error actualizando directivas: {e}")


def analyze_correction(user_message: str, chask_response: str):
    """
    Analiza una corrección del usuario y extrae la lección.
    Usa el pool de IAs gratuitas para el análisis.
    
    Args:
        user_message: Lo que Fernando dijo para corregir
        chask_response: Lo que Enjambre había hecho/dicho antes
    """
    if not ROUTER_AVAILABLE:
        # Sin router, registrar la corrección directa
        return learn(user_message)
    
    prompt = f"""Analiza esta interacción donde el usuario corrige a la IA.

LO QUE LA IA HIZO/DIJO:
{chask_response[:500]}

LA CORRECCIÓN DEL USUARIO:
{user_message}

Extrae UNA regla concisa que la IA debe seguir en el futuro para no repetir este error.
La regla debe ser específica y accionable. Máximo 1 línea.
Responde SOLO con la regla, sin explicación adicional."""

    try:
        result = llm_router.route(prompt, force_free=True)
        rule = result.get("response", "").strip()
        if rule and len(rule) > 10:
            return learn(rule, context=user_message)
    except Exception as e:
        print(f"[Reflection] Error en análisis LLM: {e}")
    
    # Fallback: registrar la corrección directa
    return learn(user_message)


def reflect_on_session(session_summary: str = ""):
    """
    Reflexión de fin de sesión. Analiza el trabajo realizado
    y extrae lecciones generales.
    """
    if not session_summary:
        # Leer memory.md como resumen de sesión
        mem_path = os.path.join(BASE_DIR, "memory.md")
        if os.path.exists(mem_path):
            with open(mem_path, "r", encoding="utf-8") as f:
                session_summary = f.read()
    
    if not session_summary:
        print("[Reflection] No hay resumen de sesión disponible.")
        return
    
    if not ROUTER_AVAILABLE:
        print("[Reflection] Router LLM no disponible para reflexión.")
        return
    
    prompt = f"""Eres Enjambre, una IA autónoma. Analiza tu sesión de trabajo y extrae lecciones:

RESUMEN DE SESIÓN:
{session_summary[:2000]}

LECCIONES PREVIAS:
{json.dumps([l['lesson'] for l in load_lessons()[-10:]], ensure_ascii=False)}

Identifica:
1. ¿Qué errores cometiste que el usuario tuvo que corregir?
2. ¿Qué patrones de preferencia del usuario detectas?
3. ¿Qué podrías hacer mejor la próxima vez?

Devuelve SOLO las lecciones nuevas (que no estén ya en las previas), una por línea.
Si no hay lecciones nuevas, responde "SIN_LECCIONES"."""

    try:
        result = llm_router.route(prompt, force_free=True)
        response = result.get("response", "").strip()
        
        if "SIN_LECCIONES" in response:
            print("[Reflection] Sesión sin lecciones nuevas.")
            return
        
        for line in response.split("\n"):
            line = line.strip().lstrip("0123456789.-) ")
            if line and len(line) > 15:
                learn(line, context="reflexión_de_sesión")
    except Exception as e:
        print(f"[Reflection] Error en reflexión: {e}")


def list_lessons():
    """Lista todas las lecciones aprendidas."""
    lessons = load_lessons()
    if not lessons:
        print("[Reflection] No hay lecciones aprendidas aún.")
        return
    
    print(f"\nLECCIONES APRENDIDAS ({len(lessons)} total):\n")
    for l in lessons:
        status = "[OK]" if l.get("applied") else "[  ]"
        print(f"  {status} L{l['id']} [{l['ts'][:10]}] {l['lesson']}")
    print()


def get_learned_lessons() -> list[dict]:
    """Devuelve las lecciones aprendidas (para MCP/API)."""
    return load_lessons()


def auto_reflect():
    """
    Reflexión automática. Diseñada para ejecutarse vía daemon
    cuando se detecta inactividad (sin mensajes nuevos por N minutos).
    
    Lee:
    1. memory.md para contexto de sesión
    2. input_queue.json para mensajes recientes de Telegram
    3. learned_lessons.json para evitar duplicados
    
    Ejecuta reflexión y guarda lecciones nuevas.
    """
    print(f"[AutoReflect] {datetime.now().strftime('%H:%M:%S')} Iniciando reflexión automática...")
    
    # Recopilar contexto de múltiples fuentes
    context_parts = []
    
    # 1. Memory.md
    for mem_path in [
        os.path.join(os.path.expanduser("~"), "Desktop", "Enjambre Datos", "memory.md"),
        os.path.join(BASE_DIR, "memory.md")
    ]:
        if os.path.exists(mem_path):
            try:
                with open(mem_path, "r", encoding="utf-8") as f:
                    context_parts.append(f"=== MEMORIA ({mem_path}) ===\n{f.read()[:1500]}")
            except Exception:
                pass
    
    # 2. Mensajes recientes de Telegram (input_queue.json)
    queue_path = os.path.join(ADVANCED_DIR, "Colas_Mensajes", "input_queue.json")
    if os.path.exists(queue_path):
        try:
            with open(queue_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
            # Últimos 10 mensajes
            recent = queue[-10:] if isinstance(queue, list) else []
            if recent:
                msgs = "\n".join(
                    f"- [{m.get('timestamp', '?')}] {m.get('text', m.get('message', ''))[:100]}"
                    for m in recent if isinstance(m, dict)
                )
                context_parts.append(f"=== MENSAJES RECIENTES ===\n{msgs}")
        except Exception:
            pass
    
    # 3. Lecciones existentes
    existing = load_lessons()
    existing_texts = [l["lesson"] for l in existing[-15:]]
    
    if not context_parts:
        print("[AutoReflect] No hay contexto disponible para reflexión.")
        return
    
    full_context = "\n\n".join(context_parts)
    
    if not ROUTER_AVAILABLE:
        print("[AutoReflect] Router LLM no disponible.")
        return
    
    prompt = f"""Eres Enjambre, una IA autónoma. Analiza tu actividad reciente y extrae lecciones:

{full_context}

LECCIONES YA REGISTRADAS (no repetir):
{json.dumps(existing_texts, ensure_ascii=False)}

Analiza:
1. ¿Hubo correcciones o quejas del usuario?
2. ¿Qué patrones de comportamiento del usuario detectas?
3. ¿Qué podrías hacer diferente la próxima vez?

Devuelve SOLO las lecciones nuevas (que no estén ya registradas), una por línea.
Cada lección debe ser concreta y accionable (ej: "Siempre preguntar antes de borrar archivos").
Si no hay lecciones nuevas, responde exactamente "SIN_LECCIONES"."""

    try:
        result = llm_router.route(prompt, force_free=True)
        response = result.get("response", "").strip()
        
        if "SIN_LECCIONES" in response:
            print("[AutoReflect] Sin lecciones nuevas.")
            return
        
        count = 0
        for line in response.split("\n"):
            line = line.strip().lstrip("0123456789.-) •*")
            if line and len(line) > 15 and "SIN_LECCIONES" not in line:
                if learn(line, context="auto_reflect"):
                    count += 1
        
        print(f"[AutoReflect] {count} lecciones nuevas registradas.")
        
    except Exception as e:
        print(f"[AutoReflect] Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python reflection_engine.py [learn|reflect|lessons|auto] [args...]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "learn" and len(sys.argv) >= 3:
        learn(" ".join(sys.argv[2:]))
    elif cmd == "reflect":
        summary = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        reflect_on_session(summary)
    elif cmd == "lessons":
        list_lessons()
    elif cmd == "auto":
        auto_reflect()
    else:
        print(f"Comando desconocido: {cmd}")

