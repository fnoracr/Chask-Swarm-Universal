"""
content_filter.py — Filtro Parental de Chask Swarm
====================================================
Filtra contenido inapropiado para menores de edad.
Dos niveles:
  - strict (child, <13): Bloquea violencia, lenguaje adulto, temas sensibles
  - moderate (teen, 13-17): Bloquea contenido explicito, permite temas educativos

Funciona en ambas direcciones:
  - INPUT: Filtra lo que el usuario envia (por si alguien le envia contenido)
  - OUTPUT: Filtra lo que el sistema le responde al menor
"""
import os
import sys
import io
import re
import json
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(r"C:\Program Files\Chask_Swarn")
TOOLS_DIR = ROOT / "Advanced_Tools"
FILTER_LOG = ROOT / "content_filter_log.json"

sys.path.insert(0, str(TOOLS_DIR))

# ─── Categorias de contenido peligroso ────────────────────
# NOTA: Estas listas son minimas y deben expandirse.
# En produccion, usar un modelo de clasificacion (Perspective API, etc.)

STRICT_BLOCK_PATTERNS = [
    # Violencia explicita
    r'\b(matar|asesinar|torturar|violar|suicid|autolesion|cortarse)\b',
    r'\b(bomba|explosivo|arma\s+de\s+fuego|pistola|rifle)\b',
    # Contenido sexual
    r'\b(porno|pornograf|sexo\s+explicito|desnud|erotic|orgasm|masturb)',
    r'\b(escort|prostitu|webcam\s+adultos|onlyfans)\b',
    # Drogas
    r'\b(cocaina|heroina|metanfetamina|mdma|lsd|crack)\b',
    r'\b(fumar\s+marihuana|consumir\s+drogas)\b',
    # Acoso
    r'\b(acoso\s+sexual|bullying|ciberbullying|sextorsion|grooming)\b',
    # Apuestas
    r'\b(apuesta|casino|apostar\s+dinero|ruleta|tragaperras)\b',
    # Ideologia extremista
    r'\b(terroris|supremacis|odio\s+racial|nazi|yihad)\b',
]

MODERATE_BLOCK_PATTERNS = [
    # Solo los mas graves para teens
    r'\b(porno|pornograf|escort|prostitu|webcam\s+adultos|onlyfans)',
    r'\b(suicid|autolesion|cortarse|metodo\s+para\s+morir)\b',
    r'\b(grooming|sextorsion|acoso\s+sexual)\b',
    r'\b(cocaina|heroina|metanfetamina|crack)\b',
    r'\b(terroris|supremacis|yihad)\b',
]

# Respuestas de reemplazo
BLOCK_RESPONSES = {
    "strict": "Lo siento, no puedo ayudarte con eso. Si necesitas hablar con alguien de confianza, pide ayuda a un adulto.",
    "moderate": "Ese tema no es apropiado para tratar aqui. Te sugiero hablar con un adulto de confianza sobre esto."
}


def check_content(text: str, filter_level: str = "none") -> dict:
    """
    Analiza texto y determina si es apropiado segun el nivel de filtro.
    
    Args:
        text: Texto a analizar
        filter_level: 'strict', 'moderate', o 'none'
    
    Returns:
        {
            "safe": bool,
            "blocked": bool,
            "reason": str,
            "matched_patterns": list,
            "replacement": str (respuesta segura si bloqueado)
        }
    """
    if filter_level == "none" or not text:
        return {"safe": True, "blocked": False, "reason": "", "matched_patterns": [], "replacement": ""}
    
    text_lower = text.lower()
    matched = []
    
    patterns = STRICT_BLOCK_PATTERNS if filter_level == "strict" else MODERATE_BLOCK_PATTERNS
    
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matched.append(pattern)
    
    if matched:
        _log_filter_event(text[:100], filter_level, matched)
        return {
            "safe": False,
            "blocked": True,
            "reason": f"Contenido inapropiado detectado (nivel: {filter_level})",
            "matched_patterns": matched,
            "replacement": BLOCK_RESPONSES.get(filter_level, "Contenido no disponible.")
        }
    
    return {"safe": True, "blocked": False, "reason": "", "matched_patterns": [], "replacement": ""}


def filter_input(text: str, username: str = None, filter_level: str = None) -> dict:
    """
    Filtra contenido de ENTRADA (lo que el usuario envia al sistema).
    Si es menor, puede estar recibiendo contenido inapropiado de terceros.
    """
    if not filter_level and username:
        filter_level = _get_user_filter_level(username)
    
    result = check_content(text, filter_level or "none")
    
    if result["blocked"]:
        # Alert admin about blocked content for minors
        _alert_admin_blocked(username, "input", text[:200])
    
    return result


def filter_output(text: str, username: str = None, filter_level: str = None) -> dict:
    """
    Filtra contenido de SALIDA (lo que el sistema responde al usuario).
    Asegura que las respuestas del LLM sean apropiadas para menores.
    """
    if not filter_level and username:
        filter_level = _get_user_filter_level(username)
    
    result = check_content(text, filter_level or "none")
    
    if result["blocked"]:
        result["filtered_text"] = result["replacement"]
    else:
        result["filtered_text"] = text
    
    return result


def get_safe_system_prompt(filter_level: str) -> str:
    """
    Genera un system prompt adicional para el LLM cuando
    el usuario tiene filtro parental activo.
    """
    if filter_level == "strict":
        return """IMPORTANTE: El usuario es un MENOR DE 13 ANOS. Debes:
1. NUNCA hablar de temas para adultos (violencia, drogas, sexo, armas)
2. Usar lenguaje simple y apropiado para ninos
3. Si te piden algo inapropiado, responde: "No puedo ayudarte con eso. Pide ayuda a un adulto."
4. Fomentar la creatividad, el aprendizaje y los valores positivos
5. No dar informacion personal ni pedir datos personales
6. Si detectas que alguien intenta hacerle dano, alerta inmediatamente"""
    
    elif filter_level == "moderate":
        return """IMPORTANTE: El usuario es un ADOLESCENTE (13-17). Debes:
1. Evitar contenido explicito (sexual, violencia grafica, drogas duras)
2. Puedes tratar temas educativos sobre salud, relaciones, etc. de forma apropiada
3. Si te piden contenido claramente inapropiado, redirige de forma respetuosa
4. No facilitar acceso a contenido para adultos
5. Fomentar el pensamiento critico y la responsabilidad"""
    
    return ""


def _get_user_filter_level(username: str) -> str:
    """Obtener nivel de filtro de un usuario."""
    try:
        from user_manager import load_users
        data = load_users()
        user = data.get("users", {}).get(username, {})
        return user.get("content_filter", "none")
    except Exception:
        return "none"


def _alert_admin_blocked(username: str, direction: str, content_preview: str):
    """Alertar al admin cuando se bloquea contenido de un menor."""
    try:
        import subprocess
        msg = (
            f"[FILTRO PARENTAL] Contenido bloqueado\n"
            f"Usuario: {username}\n"
            f"Direccion: {direction}\n"
            f"Preview: {content_preview[:100]}..."
        )
        subprocess.run(
            [sys.executable, str(ROOT / "charm_telegram.py"), "send", msg],
            capture_output=True, timeout=10
        )
    except Exception:
        pass


def _log_filter_event(content_preview: str, level: str, patterns: list):
    """Log de eventos de filtrado (para auditoria)."""
    try:
        logs = []
        if FILTER_LOG.exists():
            try:
                logs = json.loads(FILTER_LOG.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        logs.append({
            "ts": datetime.now().isoformat() if 'datetime' in dir() else "",
            "level": level,
            "preview": content_preview[:50],
            "patterns_matched": len(patterns)
        })
        
        logs = logs[-200:]  # Keep last 200
        FILTER_LOG.write_text(json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

# Fix datetime import for _log_filter_event
from datetime import datetime


if __name__ == "__main__":
    # Test
    tests = [
        ("Hola, que tal?", "strict"),
        ("Cuentame un cuento de hadas", "strict"),
        ("Como hacer una bomba casera", "strict"),
        ("Que es la fotosintesis", "moderate"),
        ("Donde puedo ver pornografia", "moderate"),
        ("Ayudame con los deberes de mates", "strict"),
    ]
    
    print("=== Test del Filtro Parental ===\n")
    for text, level in tests:
        result = check_content(text, level)
        status = "BLOCKED" if result["blocked"] else "OK"
        print(f"  [{status}] ({level}) \"{text[:50]}\"")
        if result["blocked"]:
            print(f"        -> {result['replacement']}")
