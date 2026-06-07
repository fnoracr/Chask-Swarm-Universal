"""
html_fusion.py — Skill de fusión inteligente de ficheros HTML
Analiza múltiples HTMLs, calcula el tamaño óptimo del resultado y los fusiona
en un único documento unificado, limpio y sin redundancias.
"""
NAME = "Fusión HTML Inteligente"
DESCRIPTION = "Fusiona múltiples ficheros HTML en uno solo, eliminando duplicados y optimizando el tamaño"
KEYWORDS = [
    "fusiona html", "fusionar html", "merge html", "unir html", "combinar html",
    "ficheros html", "archivos html", "html único", "html unico",
    "fusiona los html", "une los html", "junta los html",
]

import os, re, hashlib
from html.parser import HTMLParser
from datetime import datetime


# ─── Configuración de tamaños óptimos ──────────────────────────────────────
MAX_OPTIMAL_KB = 120      # Máximo recomendado para un HTML legible (KB)
WARN_KB = 80              # Aviso si supera este umbral
TARGET_SECTIONS = 25      # Nº ideal de secciones principales
MAX_SECTION_CHARS = 3000  # Máximo de texto por sección antes de recomendar recorte


class HTMLTextExtractor(HTMLParser):
    """Extrae texto plano y estructura de un HTML."""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.sections = []       # [(tag, id, title_text)]
        self.current_tag = None
        self.in_style = False
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == "style": self.in_style = True
        if tag == "script": self.in_script = True
        attrs_dict = dict(attrs)
        if tag in ("h1", "h2", "h3") and "id" in attrs_dict:
            self.sections.append({"tag": tag, "id": attrs_dict["id"], "title": ""})

    def handle_endtag(self, tag):
        if tag == "style": self.in_style = False
        if tag == "script": self.in_script = False
        self.current_tag = None

    def handle_data(self, data):
        if self.in_style or self.in_script:
            return
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)
            if self.sections and self.current_tag in ("h1", "h2", "h3"):
                self.sections[-1]["title"] = stripped

    def get_text(self):
        return " ".join(self.text_parts)


def analyze_html(filepath: str) -> dict:
    """Analiza un fichero HTML y devuelve métricas."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parser = HTMLTextExtractor()
    parser.feed(content)

    text = parser.get_text()
    size_kb = len(content) / 1024
    word_count = len(text.split())

    return {
        "path": filepath,
        "name": os.path.basename(filepath),
        "size_kb": round(size_kb, 1),
        "size_bytes": len(content),
        "word_count": word_count,
        "sections": parser.sections,
        "section_count": len(parser.sections),
        "content": content,
        "text": text,
        "text_hash": hashlib.md5(text.encode()).hexdigest(),
    }


def find_duplicate_sections(analyses: list) -> list:
    """Encuentra secciones duplicadas entre múltiples HTMLs."""
    seen_ids = {}
    duplicates = []
    for a in analyses:
        for sec in a["sections"]:
            key = sec["id"]
            if key in seen_ids:
                duplicates.append({
                    "id": key,
                    "title": sec["title"],
                    "in_files": [seen_ids[key], a["name"]],
                })
            else:
                seen_ids[key] = a["name"]
    return duplicates


def extract_css(html: str) -> str:
    """Extrae todos los bloques <style> de un HTML."""
    styles = re.findall(r"<style[^>]*>(.*?)</style>", html, re.DOTALL)
    return "\n".join(styles)


def extract_body(html: str) -> str:
    """Extrae el contenido dentro de <body>."""
    match = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
    return match.group(1).strip() if match else html


def extract_sections_from_body(body: str) -> list:
    """Divide el body en secciones basándose en divs con class='card'."""
    parts = re.split(r'(?=<div\s+class="card")', body)
    return [p.strip() for p in parts if p.strip()]


def compute_optimal_size(analyses: list) -> dict:
    """Calcula el tamaño óptimo del documento fusionado."""
    total_kb = sum(a["size_kb"] for a in analyses)
    total_words = sum(a["word_count"] for a in analyses)
    total_sections = sum(a["section_count"] for a in analyses)
    duplicates = find_duplicate_sections(analyses)
    unique_sections = total_sections - len(duplicates)

    # Estimar reducción por duplicados (media de 2KB por sección duplicada)
    estimated_savings_kb = len(duplicates) * 2.0
    estimated_final_kb = total_kb - estimated_savings_kb

    # Determinar si necesita recorte
    needs_trimming = estimated_final_kb > MAX_OPTIMAL_KB
    recommended_kb = min(estimated_final_kb, MAX_OPTIMAL_KB)

    return {
        "input_files": len(analyses),
        "total_input_kb": round(total_kb, 1),
        "total_words": total_words,
        "total_sections": total_sections,
        "duplicate_sections": len(duplicates),
        "duplicates_detail": duplicates,
        "unique_sections": unique_sections,
        "estimated_savings_kb": round(estimated_savings_kb, 1),
        "estimated_final_kb": round(estimated_final_kb, 1),
        "recommended_max_kb": MAX_OPTIMAL_KB,
        "needs_trimming": needs_trimming,
        "optimal_sections": min(unique_sections, TARGET_SECTIONS),
        "status": "⚠️ GRANDE" if estimated_final_kb > WARN_KB else "✅ ÓPTIMO",
    }


def merge_htmls(analyses: list, output_path: str) -> dict:
    """Fusiona múltiples HTMLs en uno solo, eliminando duplicados."""
    if not analyses:
        return {"error": "No hay ficheros para fusionar"}

    # Usar el fichero más reciente/grande como base para CSS y estructura
    base = max(analyses, key=lambda a: a["size_bytes"])
    base_css = extract_css(base["content"])

    # Recopilar todas las secciones únicas de todos los ficheros
    all_sections = {}  # id -> (html_content, source_file, word_count)

    for a in analyses:
        body = extract_body(a["content"])
        raw_sections = extract_sections_from_body(body)

        for sec_html in raw_sections:
            # Extraer el ID de la sección
            id_match = re.search(r'id="([^"]+)"', sec_html)
            if not id_match:
                continue
            sec_id = id_match.group(1)

            # Ignorar IDs de navegación/índice
            if sec_id in ("indice", "toc"):
                if sec_id not in all_sections:
                    all_sections[sec_id] = {
                        "html": sec_html, "source": a["name"],
                        "words": len(sec_html.split())
                    }
                continue

            # Si ya existe, quedarnos con la versión más larga (más completa)
            existing = all_sections.get(sec_id)
            new_words = len(sec_html.split())
            if not existing or new_words > existing["words"]:
                all_sections[sec_id] = {
                    "html": sec_html, "source": a["name"],
                    "words": new_words
                }

    # Ordenar secciones: header/TOC primero, luego por orden numérico, licencia al final
    def section_sort_key(item):
        sid, data = item
        if sid in ("indice", "toc"):
            return (0, sid)
        if "license" in sid or "licencia" in sid:
            return (998, sid)
        if "privacy" in sid:
            return (997, sid)
        # Extraer número de sección si existe
        num_match = re.search(r'(\d+)', sid)
        if num_match:
            return (1, int(num_match.group(1)))
        return (500, sid)

    sorted_sections = sorted(all_sections.items(), key=section_sort_key)

    # Extraer header (todo antes del primer card)
    base_body = extract_body(base["content"])
    header_match = re.match(r'(.*?)(?=<div\s+class="card")', base_body, re.DOTALL)
    header_html = header_match.group(1).strip() if header_match else ""

    # Construir el HTML final
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    version = f"v4.0 — Generado automáticamente el {timestamp}"

    final_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Guía Definitiva de Chask Swarm - Manual completo del ecosistema de IA autónoma">
    <title>Chask Swarm - Guía Definitiva</title>
    <style>
{base_css}
        @media print {{
            body {{ background: #fff; color: #000; }}
            .card {{ background: #fff; box-shadow: none; border: 1px solid #ddd; }}
            h1, h3, .agent .role {{ color: #000; }}
            .header {{ border-bottom: 2px solid #000; }}
            code {{ background: #eee; color: #000; }}
            pre {{ background: #eee; border: 1px solid #ccc; color: #000; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <button class="button no-print" onclick="window.print()" style="position:fixed;top:20px;right:20px;">Guardar como PDF</button>

    {header_html}

"""
    # Añadir secciones
    for sec_id, data in sorted_sections:
        final_html += f"    {data['html']}\n\n"

    # Footer
    final_html += f"""
    <div style="text-align: center; margin-top: 50px; color: #666; padding-bottom: 50px;">
        <p>Chask Swarm Ecosystem &copy; 2026 &mdash; Desarrollado por Fernando Enjambre</p>
        <p style="margin-top:6px;font-size:13px;">{version}</p>
    </div>
</div>
</body>
</html>
"""

    # Eliminar la "regla del cursor" obsoleta
    final_html = final_html.replace(
        "debe quedarse abierto, y debes dejar el cursor del ratón parpadeando",
        "debe quedarse abierto. El sistema gestiona automáticamente las peticiones mediante cola JSON"
    )

    # Escribir fichero
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    final_kb = len(final_html) / 1024
    return {
        "output_path": output_path,
        "final_size_kb": round(final_kb, 1),
        "sections_merged": len(sorted_sections),
        "status": "⚠️ GRANDE" if final_kb > WARN_KB else "✅ ÓPTIMO",
    }


def run(prompt: str) -> str:
    """Punto de entrada de la skill. Busca HTMLs y los fusiona."""
    import glob

    # Intentar extraer directorio del prompt
    dir_match = re.search(r'(?:en|de|from|carpeta|directorio|folder)\s+["\']?([^\'"]+)["\']?', prompt)

    # Buscar HTMLs en ubicaciones conocidas del proyecto
    search_dirs = []
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if dir_match:
        candidate = dir_match.group(1).strip()
        if os.path.isdir(candidate):
            search_dirs.append(candidate)
        # Intentar relativo al proyecto
        rel_path = os.path.join(base, candidate)
        if os.path.isdir(rel_path):
            search_dirs.append(rel_path)

    # Directorio por defecto: Charm_ES
    search_dirs.append(os.path.join(base, "Charm_ES"))
    search_dirs.append(base)

    # Buscar HTMLs
    html_files = []
    seen = set()
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for f in glob.glob(os.path.join(d, "*.html")):
            real = os.path.realpath(f)
            if real not in seen and "Guia_Definitiva" not in f:
                seen.add(real)
                html_files.append(f)

    if not html_files:
        return "❌ No encontré ficheros HTML para fusionar. Indica el directorio."

    if len(html_files) < 2:
        return f"⚠️ Solo encontré 1 HTML ({os.path.basename(html_files[0])}). Necesito al menos 2 para fusionar."

    # Analizar
    analyses = [analyze_html(f) for f in html_files]
    optimal = compute_optimal_size(analyses)

    # Fusionar
    output_dir = os.path.dirname(html_files[0])
    output_path = os.path.join(output_dir, "Guia_Definitiva_Chask_Swarm_v4.html")
    result = merge_htmls(analyses, output_path)

    # Construir informe
    report = "📄 **INFORME DE FUSIÓN HTML**\n\n"
    report += "**Ficheros de entrada:**\n"
    for a in analyses:
        report += f"  • {a['name']} — {a['size_kb']}KB, {a['section_count']} secciones, {a['word_count']} palabras\n"

    report += f"\n**Análisis de tamaño óptimo:**\n"
    report += f"  • Total entrada: {optimal['total_input_kb']}KB\n"
    report += f"  • Secciones duplicadas: {optimal['duplicate_sections']}\n"
    report += f"  • Ahorro estimado: {optimal['estimated_savings_kb']}KB\n"
    report += f"  • Tamaño estimado: {optimal['estimated_final_kb']}KB {optimal['status']}\n"
    report += f"  • Máximo recomendado: {MAX_OPTIMAL_KB}KB\n"

    if optimal["duplicates_detail"]:
        report += f"\n**Secciones duplicadas (resueltas):**\n"
        for d in optimal["duplicates_detail"][:5]:
            report += f"  • #{d['id']} ({d['title']}) — se usó versión más completa\n"

    report += f"\n**Resultado:**\n"
    report += f"  • Fichero: {os.path.basename(result['output_path'])}\n"
    report += f"  • Tamaño final: {result['final_size_kb']}KB {result['status']}\n"
    report += f"  • Secciones: {result['sections_merged']}\n"
    report += f"  • 📍 {result['output_path']}\n"

    return report
