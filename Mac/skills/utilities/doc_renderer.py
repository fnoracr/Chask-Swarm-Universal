"""
doc_renderer.py — Skill universal de renderizado de documentos.
Convierte Markdown a HTML/PDF con temas profesionales.
La IA escribe markdown y esta skill genera el documento final.

Uso desde la IA:
    from skills.doc_renderer import render
    render("# Mi Doc\nContenido...", "output.html", theme="dark")

Crear tema personalizado:
    from skills.doc_renderer import save_theme
    save_theme("mi_tema", name="Mi Tema", bg="#1a1a2e", primary="#e94560", ...)

Uso desde prompt:
    "genera un documento HTML con tema oscuro sobre X"
    "crea un tema rojo y negro llamado cyberpunk"
    "lista los temas disponibles"
"""
NAME = "Document Renderer"
DESCRIPTION = "Genera documentos HTML/PDF profesionales desde Markdown con múltiples temas (personalizables)"
KEYWORDS = [
    "genera documento", "genera html", "genera pdf", "renderiza", "render",
    "crea documento", "documento html", "documento pdf", "genera un informe",
    "create document", "generate html", "generate pdf", "generate report",
    "crea tema", "crear tema", "nuevo tema", "create theme", "new theme",
]

import os, re, json, html as html_module
from datetime import datetime

# Ruta del fichero de temas personalizados (junto a la skill)
CUSTOM_THEMES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_themes.json")

# ─── TEMAS DISPONIBLES ─────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "name": "Dark Premium",
        "bg": "#121212", "card": "#1e1e1e", "text": "#e0e0e0",
        "primary": "#FF6600", "heading": "#ffffff", "link": "#FF6600",
        "code_bg": "#000000", "code_text": "#FF6600",
        "border": "#333333", "muted": "#888888",
        "font": "'Outfit', 'Inter', system-ui, sans-serif",
        "font_import": "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap",
    },
    "light": {
        "name": "Light Clean",
        "bg": "#f8f9fa", "card": "#ffffff", "text": "#2d3748",
        "primary": "#2563eb", "heading": "#1a202c", "link": "#2563eb",
        "code_bg": "#f1f5f9", "code_text": "#e11d48",
        "border": "#e2e8f0", "muted": "#718096",
        "font": "'Inter', system-ui, sans-serif",
        "font_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap",
    },
    "corporate": {
        "name": "Corporate Blue",
        "bg": "#ffffff", "card": "#f8fafc", "text": "#334155",
        "primary": "#0f4c81", "heading": "#0f172a", "link": "#0f4c81",
        "code_bg": "#f1f5f9", "code_text": "#7c3aed",
        "border": "#cbd5e1", "muted": "#64748b",
        "font": "'Roboto', 'Segoe UI', system-ui, sans-serif",
        "font_import": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
    },
    "elegant": {
        "name": "Elegant Serif",
        "bg": "#fefdfb", "card": "#fffffe", "text": "#3d3d3d",
        "primary": "#8b5e3c", "heading": "#2c2c2c", "link": "#8b5e3c",
        "code_bg": "#f5f0eb", "code_text": "#c0392b",
        "border": "#e8e0d8", "muted": "#8a8a8a",
        "font": "'Playfair Display', 'Georgia', serif",
        "font_import": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&display=swap",
    },
    "midnight": {
        "name": "Midnight Purple",
        "bg": "#0f0a1a", "card": "#1a1230", "text": "#c8c3d4",
        "primary": "#a78bfa", "heading": "#e8e0f0", "link": "#c4b5fd",
        "code_bg": "#120e20", "code_text": "#34d399",
        "border": "#2d2545", "muted": "#7c7394",
        "font": "'Outfit', system-ui, sans-serif",
        "font_import": "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap",
    },
    "minimal": {
        "name": "Minimal",
        "bg": "#ffffff", "card": "#ffffff", "text": "#111111",
        "primary": "#111111", "heading": "#000000", "link": "#0000ee",
        "code_bg": "#f5f5f5", "code_text": "#d63384",
        "border": "#dddddd", "muted": "#666666",
        "font": "'Helvetica Neue', Arial, sans-serif",
        "font_import": "",
    },
    "nature": {
        "name": "Nature Green",
        "bg": "#f0f7f4", "card": "#ffffff", "text": "#2d4a3e",
        "primary": "#16a34a", "heading": "#14532d", "link": "#15803d",
        "code_bg": "#ecfdf5", "code_text": "#9333ea",
        "border": "#bbf7d0", "muted": "#4ade80",
        "font": "'Inter', system-ui, sans-serif",
        "font_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap",
    },
}


def _load_custom_themes() -> dict:
    """Carga temas personalizados del fichero JSON."""
    if os.path.exists(CUSTOM_THEMES_PATH):
        try:
            with open(CUSTOM_THEMES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_custom_themes(themes: dict):
    """Guarda temas personalizados en el fichero JSON."""
    with open(CUSTOM_THEMES_PATH, "w", encoding="utf-8") as f:
        json.dump(themes, f, indent=4, ensure_ascii=False)


def get_all_themes() -> dict:
    """Devuelve todos los temas (built-in + personalizados)."""
    all_t = dict(THEMES)
    all_t.update(_load_custom_themes())
    return all_t


def save_theme(key: str, name: str = "", bg: str = "#121212", card: str = "",
               text: str = "#e0e0e0", primary: str = "#FF6600",
               heading: str = "#ffffff", link: str = "",
               code_bg: str = "", code_text: str = "",
               border: str = "#333333", muted: str = "#888888",
               font: str = "'Inter', system-ui, sans-serif",
               font_import: str = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap") -> dict:
    """
    Crea o actualiza un tema personalizado.

    Args:
        key: Identificador corto del tema (ej: 'cyberpunk', 'mi_empresa')
        name: Nombre descriptivo
        bg: Color de fondo
        card: Color de tarjetas (si vacío, se auto-calcula)
        text: Color de texto principal
        primary: Color de acento principal
        heading: Color de títulos
        link: Color de enlaces (si vacío, usa primary)
        code_bg: Fondo de bloques de código
        code_text: Color del texto en código
        border: Color de bordes
        muted: Color de texto secundario
        font: Familia tipográfica CSS
        font_import: URL de Google Fonts (vacío para fuentes del sistema)

    Returns:
        dict con el tema creado
    """
    theme = {
        "name": name or key.replace('_', ' ').title(),
        "bg": bg,
        "card": card or ("#1e1e1e" if _is_dark(bg) else "#ffffff"),
        "text": text,
        "primary": primary,
        "heading": heading,
        "link": link or primary,
        "code_bg": code_bg or ("#000000" if _is_dark(bg) else "#f5f5f5"),
        "code_text": code_text or primary,
        "border": border,
        "muted": muted,
        "font": font,
        "font_import": font_import,
        "custom": True,
    }
    customs = _load_custom_themes()
    customs[key] = theme
    _save_custom_themes(customs)
    return theme


def delete_theme(key: str) -> bool:
    """Elimina un tema personalizado. No se pueden eliminar los built-in."""
    if key in THEMES:
        return False  # No borrar built-in
    customs = _load_custom_themes()
    if key in customs:
        del customs[key]
        _save_custom_themes(customs)
        return True
    return False


def _is_dark(hex_color: str) -> bool:
    """Determina si un color hex es oscuro."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r * 299 + g * 587 + b * 114) / 1000 < 128
    except Exception:
        return True


# ─── PARSER MARKDOWN → HTML ────────────────────────────────────────────────

def _md_to_html(md: str) -> tuple:
    """Convierte markdown a HTML. Devuelve (html_body, toc_entries)."""
    lines = md.split("\n")
    html_parts = []
    toc = []
    in_code = False
    in_list = False
    in_olist = False
    in_table = False
    table_headers = []
    code_lang = ""

    def close_lists():
        nonlocal in_list, in_olist
        parts = []
        if in_list:
            parts.append("</ul>")
            in_list = False
        if in_olist:
            parts.append("</ol>")
            in_olist = False
        return parts

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Code blocks
        if stripped.startswith("```"):
            if in_code:
                html_parts.append("</code></pre>")
                in_code = False
            else:
                html_parts.extend(close_lists())
                code_lang = stripped[3:].strip()
                cls = f' class="lang-{code_lang}"' if code_lang else ''
                html_parts.append(f"<pre><code{cls}>")
                in_code = True
            continue

        if in_code:
            html_parts.append(html_module.escape(line))
            continue

        # Empty line
        if not stripped:
            html_parts.extend(close_lists())
            if in_table:
                html_parts.append("</table>")
                in_table = False
            continue

        # Tables
        if "|" in stripped and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue  # separator row
            if not in_table:
                html_parts.extend(close_lists())
                html_parts.append("<table>")
                in_table = True
                html_parts.append("<tr>" + "".join(f"<th>{_inline(c)}</th>" for c in cells) + "</tr>")
                table_headers = cells
            else:
                html_parts.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
            continue
        elif in_table:
            html_parts.append("</table>")
            in_table = False

        # Headings
        hm = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if hm:
            html_parts.extend(close_lists())
            level = len(hm.group(1))
            text = hm.group(2).strip()
            slug = re.sub(r'[^\w\s-]', '', text.lower()).replace(' ', '-')[:40]
            toc.append({"level": level, "text": text, "id": slug})
            html_parts.append(f'<h{level} id="{slug}">{_inline(text)}</h{level}>')
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}$', stripped):
            html_parts.extend(close_lists())
            html_parts.append("<hr>")
            continue

        # Blockquotes / alerts
        if stripped.startswith(">"):
            html_parts.extend(close_lists())
            content = stripped.lstrip("> ").strip()
            # Detect alert types
            alert_match = re.match(r'\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]', content)
            if alert_match:
                atype = alert_match.group(1).lower()
                content = content[len(alert_match.group(0)):].strip()
                cls = {"note": "info", "tip": "tip", "important": "important",
                       "warning": "warning", "caution": "danger"}.get(atype, "info")
                html_parts.append(f'<div class="alert alert-{cls}"><strong>{atype.upper()}:</strong> {_inline(content)}</div>')
            else:
                html_parts.append(f'<blockquote>{_inline(content)}</blockquote>')
            continue

        # Unordered lists
        if re.match(r'^[\-\*\•]\s+', stripped):
            if not in_list:
                html_parts.extend(close_lists())
                html_parts.append("<ul>")
                in_list = True
            content = re.sub(r'^[\-\*\•]\s+', '', stripped)
            html_parts.append(f"<li>{_inline(content)}</li>")
            continue

        # Ordered lists
        om = re.match(r'^(\d+)[\.\)]\s+(.+)$', stripped)
        if om:
            if not in_olist:
                html_parts.extend(close_lists())
                html_parts.append("<ol>")
                in_olist = True
            html_parts.append(f"<li>{_inline(om.group(2))}</li>")
            continue

        # Paragraph
        html_parts.extend(close_lists())
        html_parts.append(f"<p>{_inline(stripped)}</p>")

    # Close any open elements
    html_parts.extend(close_lists())
    if in_code:
        html_parts.append("</code></pre>")
    if in_table:
        html_parts.append("</table>")

    return "\n".join(html_parts), toc


def _inline(text: str) -> str:
    """Procesa formato inline: bold, italic, code, links, images."""
    # Images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%;border-radius:8px;margin:10px 0;">', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic *text* or _text_
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Inline code `text`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Strikethrough ~~text~~
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    # Emoji shortcuts
    text = text.replace(":check:", "✅").replace(":cross:", "❌").replace(":warn:", "⚠️")
    return text


# ─── GENERADOR DE CSS POR TEMA ─────────────────────────────────────────────

def _build_css(theme: dict) -> str:
    t = theme
    imp = f"@import url('{t['font_import']}');\n" if t.get("font_import") else ""
    return f"""{imp}
:root {{
    --bg: {t['bg']}; --card: {t['card']}; --text: {t['text']};
    --primary: {t['primary']}; --heading: {t['heading']}; --link: {t['link']};
    --code-bg: {t['code_bg']}; --code-text: {t['code_text']};
    --border: {t['border']}; --muted: {t['muted']};
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: {t['font']}; background: var(--bg); color: var(--text); line-height: 1.8; }}
.container {{ max-width: 900px; margin: 0 auto; padding: 40px 30px; }}
h1 {{ font-size: 2.6em; color: var(--heading); margin: 30px 0 16px; letter-spacing: -0.5px; }}
h2 {{ font-size: 1.8em; color: var(--primary); margin: 28px 0 12px; padding-bottom: 6px; border-bottom: 2px solid var(--border); }}
h3 {{ font-size: 1.35em; color: var(--heading); margin: 22px 0 8px; }}
h4,h5,h6 {{ color: var(--heading); margin: 16px 0 6px; }}
p {{ margin: 10px 0; text-align: justify; }}
a {{ color: var(--link); text-decoration: none; border-bottom: 1px solid transparent; transition: border 0.2s; }}
a:hover {{ border-bottom-color: var(--link); }}
ul, ol {{ padding-left: 24px; margin: 10px 0; }}
li {{ margin-bottom: 6px; }}
code {{ background: var(--code-bg); color: var(--code-text); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; font-weight: 600; }}
pre {{ background: var(--code-bg); padding: 18px; border-radius: 8px; overflow-x: auto; border: 1px solid var(--border); margin: 16px 0; }}
pre code {{ background: none; padding: 0; color: var(--text); font-weight: 400; }}
blockquote {{ border-left: 4px solid var(--primary); padding: 12px 18px; margin: 16px 0; background: color-mix(in srgb, var(--primary) 6%, var(--card)); border-radius: 0 8px 8px 0; font-style: italic; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
th {{ background: color-mix(in srgb, var(--primary) 12%, var(--card)); color: var(--primary); padding: 10px 14px; text-align: left; font-weight: 700; border: 1px solid var(--border); }}
td {{ padding: 9px 14px; border: 1px solid var(--border); }}
tr:hover td {{ background: color-mix(in srgb, var(--primary) 4%, var(--card)); }}
hr {{ border: none; border-top: 1px solid var(--border); margin: 30px 0; }}
img {{ max-width: 100%; height: auto; border-radius: 8px; }}
.alert {{ padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 16px 0; }}
.alert-info {{ border-left: 4px solid #3b82f6; background: rgba(59,130,246,0.08); }}
.alert-tip {{ border-left: 4px solid #22c55e; background: rgba(34,197,94,0.08); }}
.alert-important {{ border-left: 4px solid var(--primary); background: color-mix(in srgb, var(--primary) 8%, var(--card)); }}
.alert-warning {{ border-left: 4px solid #f59e0b; background: rgba(245,158,11,0.08); }}
.alert-danger {{ border-left: 4px solid #ef4444; background: rgba(239,68,68,0.08); }}
.toc {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 24px 30px; margin: 20px 0 30px; }}
.toc h2 {{ border: none; margin-top: 0; font-size: 1.3em; }}
.toc ul {{ list-style: none; padding-left: 0; columns: 2; column-gap: 30px; }}
.toc li {{ margin-bottom: 4px; }}
.toc a {{ color: var(--primary); font-size: 0.95em; line-height: 2; }}
.toc .indent {{ padding-left: 20px; }}
.footer {{ text-align: center; color: var(--muted); padding: 40px 0; font-size: 0.85em; border-top: 1px solid var(--border); margin-top: 50px; }}
.btn-print {{ position: fixed; top: 16px; right: 16px; background: var(--primary); color: #fff; border: none; padding: 8px 18px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; z-index: 999; }}
.btn-print:hover {{ opacity: 0.85; }}
@media print {{
    body {{ background: #fff !important; color: #000 !important; }}
    .container {{ max-width: 100%; }}
    h1,h2,h3,h4 {{ color: #000 !important; }}
    .btn-print, .no-print {{ display: none !important; }}
    a {{ color: #000 !important; }}
    pre, code {{ background: #f5f5f5 !important; color: #000 !important; border-color: #ccc !important; }}
}}
@media (max-width: 700px) {{
    .container {{ padding: 20px 16px; }}
    h1 {{ font-size: 1.8em; }}
    .toc ul {{ columns: 1; }}
}}"""


# ─── FUNCIÓN PRINCIPAL DE RENDERIZADO ───────────────────────────────────────

def render(markdown: str, output_path: str, theme: str = "dark",
           title: str = "", author: str = "", toc: bool = True,
           print_btn: bool = True, footer: str = "") -> dict:
    """
    Renderiza markdown a un documento HTML profesional.

    Args:
        markdown: Contenido en formato Markdown
        output_path: Ruta del fichero HTML de salida
        theme: Nombre del tema (dark, light, corporate, elegant, midnight, minimal, nature)
        title: Título del documento (si vacío, usa el primer H1)
        author: Autor del documento
        toc: Generar tabla de contenidos automática
        print_btn: Incluir botón de imprimir/PDF
        footer: Texto personalizado del footer

    Returns:
        dict con path, size_kb, sections, theme
    """
    all_themes = get_all_themes()
    t = all_themes.get(theme, all_themes.get("dark", THEMES["dark"]))
    css = _build_css(t)
    body_html, toc_entries = _md_to_html(markdown)

    # Auto-detectar título del primer H1
    if not title and toc_entries:
        for entry in toc_entries:
            if entry["level"] == 1:
                title = entry["text"]
                break
    if not title:
        title = "Documento"

    # Generar TOC HTML (solo H2 para evitar índices gigantes)
    toc_html = ""
    if toc and toc_entries:
        toc_items = []
        h2_entries = [e for e in toc_entries if e["level"] <= 2]
        for e in h2_entries:
            toc_items.append(f'<li><a href="#{e["id"]}">{e["text"]}</a></li>')
        # 1 columna si hay más de 16 items, 2 columnas si menos
        col_style = "" if len(h2_entries) > 16 else ' style="columns:2;column-gap:30px;"'
        toc_html = f"""
    <nav class="toc">
        <h2>📋 Contenidos</h2>
        <ul{col_style}>{"".join(toc_items)}</ul>
    </nav>"""

    # Footer
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    author_line = f" &mdash; {html_module.escape(author)}" if author else ""
    footer_text = footer if footer else f"Generado el {ts}{author_line}"

    # Print button
    btn = '<button class="btn-print no-print" onclick="window.print()">📄 PDF</button>' if print_btn else ""

    # Ensamblar
    doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{html_module.escape(title)}">
    <title>{html_module.escape(title)}</title>
    <style>{css}</style>
</head>
<body>
<div class="container">
    {btn}
    {toc_html}
    {body_html}
    <div class="footer">{footer_text}</div>
</div>
</body>
</html>"""

    # Escribir
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc)

    return {
        "path": os.path.abspath(output_path),
        "size_kb": round(len(doc) / 1024, 1),
        "sections": len(toc_entries),
        "theme": t["name"],
        "title": title,
    }


def list_themes() -> str:
    """Devuelve los temas disponibles (built-in + personalizados)."""
    all_t = get_all_themes()
    lines = ["📎 Temas disponibles:"]
    lines.append("  Built-in:")
    for key, t in THEMES.items():
        lines.append(f"    • {key}: {t['name']} (fondo: {t['bg']}, acento: {t['primary']})")
    customs = _load_custom_themes()
    if customs:
        lines.append("  Personalizados:")
        for key, t in customs.items():
            lines.append(f"    ★ {key}: {t['name']} (fondo: {t['bg']}, acento: {t['primary']})")
    lines.append(f"\n  Total: {len(all_t)} temas ({len(THEMES)} built-in + {len(customs)} custom)")
    return "\n".join(lines)


# ─── PUNTO DE ENTRADA COMO SKILL ───────────────────────────────────────────

def run(prompt: str) -> str:
    """Punto de entrada cuando se invoca como skill desde el router."""
    p = prompt.lower()

    # Listar temas
    if any(w in p for w in ["temas", "themes", "estilos", "lista"]):
        return list_themes()

    # Crear tema (ejemplo: "crea un tema rojo y negro llamado cyberpunk")
    if any(w in p for w in ["crea tema", "crear tema", "nuevo tema", "create theme", "new theme"]):
        return ("🎨 Para crear un tema personalizado, usa:\n\n"
                "  from skills.doc_renderer import save_theme\n"
                '  save_theme("mi_tema",\n'
                '      name="Mi Tema Custom",\n'
                '      bg="#1a1a2e",       # Fondo\n'
                '      primary="#e94560",   # Color de acento\n'
                '      text="#eaeaea",      # Texto principal\n'
                '      heading="#ffffff",   # Títulos\n'
                '      border="#333333",    # Bordes\n'
                '  )\n\n'
                "Los campos card, link, code_bg y code_text se auto-calculan si no los especificas.\n"
                "El tema se guarda en custom_themes.json y estará disponible para siempre.")

    # Eliminar tema
    if any(w in p for w in ["borra tema", "elimina tema", "delete theme"]):
        return ("Para eliminar un tema personalizado:\n"
                "  from skills.doc_renderer import delete_theme\n"
                '  delete_theme("nombre_del_tema")\n\n'
                "Nota: Los 7 temas built-in no se pueden eliminar.")

    return ("📄 Document Renderer listo.\n\n"
            "Uso:\n"
            "  from skills.doc_renderer import render\n"
            '  render("# Titulo\\nContenido...", "salida.html", theme="dark")\n\n'
            "Temas personalizados:\n"
            "  from skills.doc_renderer import save_theme\n"
            '  save_theme("mi_tema", bg="#1a1a2e", primary="#e94560")\n\n'
            f"{list_themes()}\n\n"
            "Opciones: theme, title, author, toc (True/False), footer")
