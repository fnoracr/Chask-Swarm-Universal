"""
style_extractor.py — Skill de extracción de estilos visuales.
Permite generar temas estéticos personalizados para doc_renderer.py a partir de:
  1. Una página web (URL), analizando sus hojas de estilo y colores.
  2. Una imagen (ruta local), extrayendo su paleta dominante con Pillow y calibrándola con IA.

Registra el nuevo tema de forma persistente llamando a skills.doc_renderer.save_theme.
"""
NAME = "Style Extractor"
DESCRIPTION = "Genera nuevos temas visuales para doc_renderer a partir de una página web (URL) o una imagen."
KEYWORDS = [
    "crea estilo de", "crear estilo de", "extrae estilo de", "extraer estilo de",
    "tema de imagen", "tema de web", "tema de url", "estilo de imagen", "estilo de web",
    "extract style", "create style from", "theme from image", "theme from web",
]

import os
import re
import json
import requests
from PIL import Image
from urllib.parse import urlparse

# Importar save_theme dinámicamente para registrar el tema
try:
    from skills.doc_renderer import save_theme, get_all_themes
except ImportError:
    # Fallback si se ejecuta en un path alternativo
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from skills.doc_renderer import save_theme, get_all_themes


def rgb_to_hex(r, g, b) -> str:
    """Convierte tupla RGB a color hexadecimal."""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_str: str) -> tuple:
    """Convierte hexadecimal a tupla RGB."""
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def calculate_luminance(hex_str: str) -> float:
    """Calcula la luminancia relativa de un color hex (0.0 a 1.0)."""
    try:
        r, g, b = hex_to_rgb(hex_str)
        # Coeficientes estándar de luminancia
        return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    except Exception:
        return 0.5


def extract_palette_from_image(image_path: str, num_colors: int = 12) -> list:
    """
    Carga una imagen local y extrae los colores dominantes utilizando cuantización.
    Devuelve una lista de colores hexadecimales.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"No se encontró la imagen en la ruta: {image_path}")

    # Abrir la imagen y downsamplear para velocidad
    img = Image.open(image_path)
    img = img.convert("RGB")
    img.thumbnail((150, 150))

    # Obtener los colores y sus frecuencias
    colors = img.getcolors(maxcolors=150 * 150)
    if not colors:
        raise ValueError("No se pudieron extraer los colores de la imagen.")

    # Ordenar por frecuencia descendente
    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)

    # Filtrar colores muy similares para tener variedad
    hex_palette = []
    seen_rgb = []
    
    for count, rgb in sorted_colors:
        # Evitar duplicar tonos casi idénticos
        is_similar = False
        for sr, sg, sb in seen_rgb:
            # Distancia euclídea simple de color
            dist = ((rgb[0]-sr)**2 + (rgb[1]-sg)**2 + (rgb[2]-sb)**2)**0.5
            if dist < 35:  # Umbral de similitud
                is_similar = True
                break
        
        if not is_similar:
            hex_palette.append(rgb_to_hex(*rgb))
            seen_rgb.append(rgb)
            if len(hex_palette) >= num_colors:
                break

    return hex_palette


def extract_palette_from_web(url: str) -> dict:
    """
    Hace una petición HTTP a la URL y extrae colores potenciales del HTML y hojas de estilo inline.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChaskSwarm/NoraAgent"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        html_content = r.text
    except Exception as e:
        raise ConnectionError(f"Error al conectar con la URL {url}: {e}")

    # Buscar colores hexadecimales de 3 y 6 dígitos
    hex_patterns = re.findall(r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})\b', html_content)
    
    # Buscar colores rgb/rgba
    rgba_patterns = re.findall(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d\.]+\s*)?\)', html_content)

    colors_found = []
    for h in hex_patterns:
        full_hex = h
        if len(h) == 3:
            full_hex = "".join(char*2 for char in h)
        colors_found.append(f"#{full_hex.lower()}")

    for rgb in rgba_patterns:
        try:
            r_val, g_val, b_val = map(int, rgb)
            colors_found.append(rgb_to_hex(r_val, g_val, b_val))
        except ValueError:
            pass

    # Contar frecuencias de colores
    color_counts = {}
    for c in colors_found:
        color_counts[c] = color_counts.get(c, 0) + 1

    # Ordenar por frecuencia
    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Filtrar similares
    filtered_palette = []
    seen_rgb = []
    for c, count in sorted_colors:
        try:
            rgb = hex_to_rgb(c)
            is_similar = False
            for sr, sg, sb in seen_rgb:
                dist = ((rgb[0]-sr)**2 + (rgb[1]-sg)**2 + (rgb[2]-sb)**2)**0.5
                if dist < 25:
                    is_similar = True
                    break
            if not is_similar:
                filtered_palette.append(c)
                seen_rgb.append(rgb)
                if len(filtered_palette) >= 12:
                    break
        except Exception:
            pass

    # Obtener metadatos básicos del HTML
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
    site_title = title_match.group(1).strip() if title_match else urlparse(url).netloc

    return {
        "title": site_title,
        "palette": filtered_palette,
        "html_snippet": html_content[:4000]  # Mandar los primeros 4KB al LLM para contexto de fuentes/estructura
    }


def calibrate_palette_with_llm(palette: list, source_name: str, is_web: bool = False, html_snippet: str = "") -> dict:
    """
    Usa el llm_router para calibrar y mapear la paleta de colores cruda en un tema de diseño robusto
    y legible (contrastes correctos) para doc_renderer.
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Advanced_Tools"))
    from llm_router import route

    prompt = f"""
Has recibido una paleta de colores hexadecimales crudos extraídos de {'una página web' if is_web else 'una imagen'} llamada '{source_name}':
Paleta cruda: {', '.join(palette)}

Tu tarea es actuar como Diseñador de UI/UX Experto y calibrar estos colores para crear un tema de diseño premium, altamente legible y armonioso para un renderizador de documentos HTML.

Debes elegir o generar los siguientes campos de color obligatorios basándote en la paleta:
1. `bg`: Fondo general de la página (Debe ser muy oscuro si el tema es Dark, o muy claro/blanco si el tema es Light. No uses grises medianos para fondos de texto).
2. `card`: Fondo de las tarjetas/contenedores (ligeramente más claro que bg en temas oscuros, o ligeramente más oscuro/blanco en temas claros).
3. `text`: Color del texto principal (debe tener un contraste muy alto con `bg`, ej: blanco/crema para oscuros, negro/gris carbón para claros).
4. `primary`: El color de acento más vibrante de la paleta. Se usará para títulos H2, botones e íconos.
5. `heading`: Color para títulos H1 y H3 (un tono neutro de alto contraste, a veces igual a text o un derivado directo).
6. `link`: Color para los enlaces (usualmente igual a `primary` o un azul/cyan complementario vibrante).
7. `border`: Color para líneas divisorias y bordes (un tono muy sutil, ej: gris muy tenue o un tono de bg con opacidad).
8. `muted`: Color para textos secundarios o pies de página.

Además, debes seleccionar:
- `is_dark`: Indica si el tema resultante es oscuro (true/false).
- `font`: Una familia tipográfica CSS premium ideal para el estilo (ej: "'Outfit', sans-serif" si es moderno/tecnológico, o "'Playfair Display', serif" si es clásico/elegante).
- `font_import`: La URL de Google Fonts necesaria para importar la tipografía elegida (deja vacío si son fuentes estándar del sistema).

INFORMACIÓN DE DISEÑO ADICIONAL (Web Snippet):
{html_snippet[:1500] if html_snippet else 'No aplica.'}

Devuelve EXCLUSIVAMENTE un objeto JSON estructurado con la siguiente forma, sin rodeos ni formato de markdown Markdown de bloque de código, solo el texto JSON plano:
{{
    "name": "Nombre descriptivo y premium del tema (ej: 'Bosque Esmeralda', 'Neon Cyberpunk')",
    "bg": "#hex",
    "card": "#hex",
    "text": "#hex",
    "primary": "#hex",
    "heading": "#hex",
    "link": "#hex",
    "border": "#hex",
    "muted": "#hex",
    "font": "familia_css",
    "font_import": "url_google_fonts"
}}
"""
    # Llamar al router de IAs gratuitas de forma robusta
    res = route(prompt, system_prompt="Eres un diseñador UX/UI experto que genera configuraciones JSON de temas CSS.", force_free=True)
    response_text = res.get("response", "")

    # Limpiar posibles bloques de código de markdown
    clean_json = response_text.replace("```json", "").replace("```", "").strip()
    
    try:
        theme_data = json.loads(clean_json)
        return theme_data
    except Exception as e:
        # Fallback de emergencia si el LLM falla
        # Determinar si la mayoría de colores son oscuros
        is_dark_bg = calculate_luminance(palette[0]) < 0.5 if palette else True
        
        bg = "#121212" if is_dark_bg else "#f8f9fa"
        card = "#1e1e1e" if is_dark_bg else "#ffffff"
        text = "#e0e0e0" if is_dark_bg else "#2d3748"
        primary = palette[1] if len(palette) > 1 else "#FF6600"
        
        return {
            "name": f"Estilo {source_name[:15].title()}",
            "bg": bg,
            "card": card,
            "text": text,
            "primary": primary,
            "heading": "#ffffff" if is_dark_bg else "#1a202c",
            "link": primary,
            "border": "#333333" if is_dark_bg else "#e2e8f0",
            "muted": "#888888" if is_dark_bg else "#718096",
            "font": "'Inter', system-ui, sans-serif",
            "font_import": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap"
        }


def run(prompt: str) -> str:
    """
    Punto de entrada de la skill.
    Identifica si es una URL o ruta de imagen y extrae el tema correspondiente.
    """
    # 1. Identificar URL en el prompt
    url_match = re.search(r'https?://[^\s"\'<>]+', prompt)
    
    # 2. Identificar ruta de archivo de imagen
    image_match = re.search(r'(?:imagen|img|file|archivo|ruta)\s+["\']?([^\s"\'<>]+?\.(?:png|jpe?g|webp|gif|bmp))["\']?', prompt, re.IGNORECASE)
    
    if not url_match and not image_match:
        # Intentar buscar cualquier palabra que termine en extensión de imagen
        img_words = [w.strip("\"'") for w in prompt.split() if w.strip("\"'").lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]
        if img_words:
            image_path = img_words[0]
        else:
            return ("🎨 **Style Extractor** listo.\n\n"
                    "Para extraer y generar un tema visual nuevo, indícame:\n"
                    "  • **Una URL:** *'extrae el estilo de la web https://ejemplo.com'* o *'crear estilo de https://marca.es'*\n"
                    "  • **Una Imagen:** *'crea un estilo a partir de la imagen C:\\fotos\\paleta.png'* o *'extraer estilo de logo.webp'*")

    theme_key = ""
    theme_data = {}
    report = ""

    if url_match:
        url = url_match.group(0)
        domain = urlparse(url).netloc
        theme_key = domain.replace(".", "_").replace("-", "_").lower()
        
        report += f"🌐 **Analizando página web:** `{url}`\n"
        
        try:
            web_data = extract_palette_from_web(url)
            report += f"  • Título del sitio: *{web_data['title']}*\n"
            report += f"  • Colores base encontrados: {len(web_data['palette'])}\n"
            
            if not web_data['palette']:
                web_data['palette'] = ["#121212", "#FF6600", "#3b82f6", "#ffffff"]
                report += "  • ⚠️ No se detectaron colores explícitos en el HTML, usando paleta neutra base.\n"
                
            theme_data = calibrate_palette_with_llm(
                palette=web_data['palette'],
                source_name=web_data['title'],
                is_web=True,
                html_snippet=web_data['html_snippet']
            )
        except Exception as e:
            return f"❌ Error analizando la página web: {e}"

    elif image_match or img_words:
        image_path = image_match.group(1) if image_match else img_words[0]
        
        # Intentar ruta absoluta si es relativa al workspace de Enjambre Datos
        if not os.path.isabs(image_path):
            candidate1 = os.path.join(r"C:\Users\fnora\Desktop\Enjambre Datos", image_path)
            candidate2 = os.path.join(r"C:\Program Files\Chask_Swarm", image_path)
            if os.path.exists(candidate1):
                image_path = candidate1
            elif os.path.exists(candidate2):
                image_path = candidate2

        filename = os.path.basename(image_path)
        theme_key = os.path.splitext(filename)[0].replace("-", "_").replace(" ", "_").lower()
        
        report += f"🖼️ **Analizando imagen local:** `{image_path}`\n"
        
        try:
            palette = extract_palette_from_image(image_path)
            report += f"  • Colores dominantes extraídos: {', '.join(palette)}\n"
            
            theme_data = calibrate_palette_with_llm(
                palette=palette,
                source_name=filename,
                is_web=False
            )
        except Exception as e:
            return f"❌ Error analizando la imagen: {e}"

    # Registrar el tema de forma persistente llamando a save_theme de doc_renderer
    try:
        registered = save_theme(
            key=theme_key,
            name=theme_data.get("name", "Tema Extraído"),
            bg=theme_data.get("bg", "#121212"),
            card=theme_data.get("card", ""),
            text=theme_data.get("text", "#e0e0e0"),
            primary=theme_data.get("primary", "#FF6600"),
            heading=theme_data.get("heading", "#ffffff"),
            link=theme_data.get("link", ""),
            code_bg=theme_data.get("code_bg", ""),
            code_text=theme_data.get("code_text", ""),
            border=theme_data.get("border", "#333333"),
            muted=theme_data.get("muted", "#888888"),
            font=theme_data.get("font", "'Inter', sans-serif"),
            font_import=theme_data.get("font_import", "")
        )
        
        report += f"\n🎨 **¡Tema diseñado y guardado con éxito!**\n"
        report += f"  • **Clave del tema:** `{theme_key}`\n"
        report += f"  • **Nombre:** *{registered['name']}*\n"
        report += f"  • **Fondo (bg):** `{registered['bg']}`\n"
        report += f"  • **Acento (primary):** `{registered['primary']}`\n"
        report += f"  • **Texto (text):** `{registered['text']}`\n"
        report += f"  • **Tipografía:** {registered['font']}\n\n"
        report += f"🚀 **¡Ya está disponible!** Puedes usarlo inmediatamente para renderizar informes con:\n"
        report += f"  `render(markdown, file, theme=\"{theme_key}\")`"
    except Exception as save_err:
        report += f"\n❌ Error registrando el tema: {save_err}"

    return report
