"""
skill_generator.py — Auto-Generación de Skills con LLM
========================================================
Genera scripts Python funcionales a partir de descripciones
en lenguaje natural usando el pool de IAs gratuitas.

Flujo:
  1. El usuario describe lo que necesita
  2. El LLM genera el código Python
  3. El script se guarda en /skills/
  4. Se registra automáticamente en el skill_catalog

Uso:
  python skill_generator.py "Script que convierta CSV a JSON"
  python skill_generator.py --describe "Qué hace convert_csv.py" convert_csv.py
"""
import os
import sys
import json
import io
import re
from datetime import datetime

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVANCED_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
GEN_LOG = os.path.join(BASE_DIR, "skill_gen_log.json")

sys.path.insert(0, ADVANCED_DIR)

try:
    import llm_router
    ROUTER_OK = True
except ImportError:
    ROUTER_OK = False

try:
    from skill_catalog import register_skill
    CATALOG_OK = True
except ImportError:
    CATALOG_OK = False


def _sanitize_filename(name: str) -> str:
    """Convierte una descripción en un nombre de archivo válido."""
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9_\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:40]


def generate_skill(description: str, filename: str = None) -> dict:
    """
    Genera un skill (script Python) a partir de una descripción.
    
    Args:
        description: Descripción en lenguaje natural de lo que debe hacer
        filename: Nombre del archivo (opcional, se auto-genera)
    
    Returns:
        {"path": str, "name": str, "success": bool, "error": str?}
    """
    if not ROUTER_OK:
        return {"success": False, "error": "LLM Router no disponible"}
    
    # Generar nombre si no se proporciona
    if not filename:
        # Pedir al LLM un nombre corto
        name_prompt = f'Genera UN nombre de archivo Python (snake_case, máx 3 palabras, sin .py) para: "{description}". Responde SOLO el nombre, nada más.'
        try:
            r = llm_router.route(name_prompt, force_free=True)
            raw_name = r.get("response", "").strip().strip('"').strip("'")
            filename = _sanitize_filename(raw_name)
        except Exception:
            filename = _sanitize_filename(description)
    
    if not filename.endswith('.py'):
        filename += '.py'
    
    # Generar el código
    code_prompt = f"""Genera un script Python completo y funcional para la siguiente tarea:

TAREA: {description}

REGLAS OBLIGATORIAS:
1. Script autocontenido (no depender de módulos personalizados)
2. Incluir docstring con descripción y uso
3. Incluir if __name__ == "__main__" con ejemplo funcional
4. Usar solo librerías estándar de Python cuando sea posible
5. Si necesita libs externas, incluir try/except con instrucciones de instalación
6. Manejar errores con try/except
7. Encoding UTF-8 en archivos
8. Compatible con Windows (paths con raw strings si es necesario)

Responde SOLO con el código Python. Sin markdown, sin ``` ni explicaciones."""

    try:
        result = llm_router.route(code_prompt, agent="ghost", force_free=True)
        code = result.get("response", "")
    except Exception as e:
        return {"success": False, "error": f"Error generando código: {e}"}
    
    # Limpiar el código (quitar markdown si el LLM lo incluyó)
    code = code.strip()
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()
    
    if not code or len(code) < 20:
        return {"success": False, "error": "Código generado vacío o demasiado corto"}
    
    # Verificar que es Python válido (sintaxis)
    try:
        compile(code, filename, "exec")
    except SyntaxError as e:
        return {"success": False, "error": f"Sintaxis inválida: {e}"}
    
    # Guardar
    os.makedirs(SKILLS_DIR, exist_ok=True)
    filepath = os.path.join(SKILLS_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"[SkillGen] Generado: {filepath} ({len(code)} bytes)")
    
    # Registrar en el catálogo
    skill_name = filename.replace('.py', '')
    if CATALOG_OK:
        try:
            register_skill(
                name=skill_name,
                description=description,
                script_path=filepath,
                tags="auto-generated"
            )
            print(f"[SkillGen] Registrado en catálogo: {skill_name}")
        except Exception as e:
            print(f"[SkillGen] Error registrando en catálogo: {e}")
    
    # Log
    _save_gen_log({
        "ts": datetime.now().isoformat(),
        "description": description,
        "filename": filename,
        "path": filepath,
        "bytes": len(code),
        "model": result.get("model_used", "unknown")
    })
    
    return {
        "success": True,
        "path": filepath,
        "name": skill_name,
        "bytes": len(code)
    }


def describe_skill(script_path: str) -> str:
    """
    Analiza un script existente y genera una descripción.
    Útil para documentar skills no catalogados.
    """
    if not ROUTER_OK:
        return "[ERROR] LLM Router no disponible"
    
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read(5000)
    except Exception as e:
        return f"[ERROR] No se pudo leer {script_path}: {e}"
    
    prompt = f"""Analiza este script Python y genera:
1. Una descripción de una línea de lo que hace
2. Cómo usarlo (ejemplo de CLI)
3. Qué dependencias necesita

Código:
{code}

Responde en formato conciso."""

    try:
        result = llm_router.route(prompt, force_free=True)
        return result.get("response", "Sin descripción")
    except Exception as e:
        return f"[ERROR] {e}"


def _save_gen_log(entry: dict):
    """Guarda log de generación."""
    logs = []
    if os.path.exists(GEN_LOG):
        try:
            with open(GEN_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append(entry)
    logs = logs[-30:]
    with open(GEN_LOG, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python skill_generator.py \"Descripción del script a generar\"")
        print("  python skill_generator.py --describe script.py")
        sys.exit(1)
    
    if sys.argv[1] == "--describe" and len(sys.argv) >= 3:
        desc = describe_skill(sys.argv[2])
        print(desc)
    else:
        description = " ".join(sys.argv[1:])
        print(f"\n[SkillGen] Generando skill: {description}\n")
        result = generate_skill(description)
        if result["success"]:
            print(f"\n✅ Skill generado: {result['path']} ({result['bytes']} bytes)")
        else:
            print(f"\n❌ Error: {result['error']}")
