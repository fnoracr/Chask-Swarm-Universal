# -*- coding: utf-8 -*-
import sys
import re
from pathlib import Path
from datetime import datetime

# Force stdout to use utf-8 encoding to avoid Windows console errors
sys.stdout.reconfigure(encoding='utf-8')

ORIGINAL_PATH = Path(r"C:\Users\fnora\Desktop\Enjambre Datos\charlas_con_mi_IA.php")
OUT_PATH = Path(r"C:\Users\fnora\Desktop\Enjambre Datos\Web_Chask\web\public_html\charlas_con_mi_IA.php")

def style_chask_swarm(text):
    # Enforces the official brand color scheme:
    # "Cha" and "rm" in orange (#FF6600), the rest ("sk Swa" / "SK SWA") in white (#FFFFFF)
    # First, handle uppercase CHASK SWARM
    text = re.sub(
        r'\bCHASK\s+SWARM\b', 
        '<span class="o">CHA</span>SK SWA<span class="o">RM</span>', 
        text
    )
    # Then handle standard Chask Swarm (case-insensitive variations)
    text = re.sub(
        r'\b[Cc]hask\s+[Ss]warm\b', 
        '<span class="o">Cha</span>sk Swa<span class="o">rm</span>', 
        text
    )
    return text

def parse_original_turns(content):
    # We want to extract each turn block
    # A turn block starts with <div class="turn"> and ends with </div>\n\s*</div> or similar,
    # but wait, let's parse it turn by turn using regex.
    # Each turn has:
    # <div class="author-bar (fernando|enjambre)">Author</div>
    # <div class="content">Content</div>
    turn_regex = re.compile(
        r'<div class="turn">\s*<div class="author-bar\s+(fernando|enjambre)">([^<]+)</div>\s*<div class="content">(.*?)</div>\s*</div>',
        re.DOTALL
    )
    matches = turn_regex.findall(content)
    return matches

def format_markdown_to_html(text):
    # Clean text
    text = text.strip()
    
    # 1. Convert headers
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # 2. Convert bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 3. Convert blockquotes
    blockquote_re = re.compile(r'^>\s*(.*?)$', re.MULTILINE)
    text = blockquote_re.sub(r'<div class="tip-docs">\1</div>', text)
    
    # 4. Handle table
    # Simple table parser if table exists:
    if "|" in text:
        lines = text.split('\n')
        in_table = False
        table_html = []
        for line in lines:
            if line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    in_table = True
                    table_html.append('<table>')
                # Parse row
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if '---' in cells[0]:
                    continue # Skip divider
                row_type = 'th' if len(table_html) == 1 else 'td'
                row_str = '<tr>' + ''.join(f'<{row_type}>{cell}</{row_type}>' for cell in cells) + '</tr>'
                table_html.append(row_str)
            else:
                if in_table:
                    in_table = False
                    table_html.append('</table>')
                table_html.append(line)
        text = '\n'.join(table_html)
        
    # 5. Convert lists
    # Bullet lists
    lines = text.split('\n')
    in_ul = False
    in_ol = False
    list_lines = []
    for line in lines:
        stripped = line.strip()
        # Unordered list
        if (stripped.startswith('* ') or stripped.startswith('- ')) and not stripped.startswith('---'):
            if not in_ul:
                if in_ol:
                    list_lines.append('</ol>')
                    in_ol = False
                list_lines.append('<ul>')
                in_ul = True
            content_item = stripped[2:].strip()
            list_lines.append(f'<li>{content_item}</li>')
        # Ordered list
        elif re.match(r'^\d+\.\s+', stripped):
            if not in_ol:
                if in_ul:
                    list_lines.append('</ul>')
                    in_ul = False
                list_lines.append('<ol>')
                in_ol = True
            m = re.match(r'^\d+\.\s+(.*?)$', stripped)
            list_lines.append(f'<li>{m.group(1)}</li>')
        else:
            if in_ul:
                list_lines.append('</ul>')
                in_ul = False
            if in_ol:
                list_lines.append('</ol>')
                in_ol = False
            list_lines.append(line)
    if in_ul:
        list_lines.append('</ul>')
    if in_ol:
        list_lines.append('</ol>')
    text = '\n'.join(list_lines)
    
    # 6. Paragraphs / Linebreaks
    # If not inside a block tag, replace single newlines with spaces and double newlines with <br><br>
    # Simple replacement: replace double newlines with <br><br>
    text = re.sub(r'\n\n+', r'<br><br>', text)
    
    # 7. Clean up HR dividers
    text = re.sub(r'^---$', r'<hr>', text, flags=re.MULTILINE)
    
    # Apply official brand styling
    text = style_chask_swarm(text)
    
    return text

def main():
    if not ORIGINAL_PATH.exists():
        print(f"Error: Original file not found at {ORIGINAL_PATH}")
        sys.exit(1)
        
    content = ORIGINAL_PATH.read_text(encoding="utf-8")
    turns = parse_original_turns(content)
    
    print(f"Parsed {len(turns)} conversation turns successfully!")
    
    formatted_turns_html = []
    for author_class, author_name, turn_content in turns:
        # Format the inner markdown to premium HTML
        formatted_content = format_markdown_to_html(turn_content)
        
        # Style author bar
        bar_class = "fernando" if "fernando" in author_class.lower() else "enjambre"
        
        turn_html = f"""
    <div class="turn-block {bar_class}">
      <div class="author-bar {bar_class}">{style_chask_swarm(author_name)}</div>
      <div class="turn-content">{formatted_content}</div>
    </div>
"""
        formatted_turns_html.append(turn_html)
        
    all_turns_joined = "\n".join(formatted_turns_html)
    
    # Base template matching charm.php premium styled look
    php_content = f"""<?php header('Content-Type: text/html; charset=UTF-8'); ?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>El Pacto de la Simbiosis &mdash; Conversaciones con mi IA</title>
  <link rel="stylesheet" href="css/styles.css">
  <style>
    /* Estilos específicos premium para el Pacto de la Simbiosis */
    .charlas-container {{ font-family: 'Outfit', sans-serif; background-color: #050505; color: #e0e0e0; line-height: 1.8; padding: 0 0 80px 0; }}
    .charlas-container p, .charlas-container li, .charlas-container td, .charlas-container section {{ text-align: justify; text-justify: inter-word; }}
    .charlas-container .container-docs {{ max-width: 1000px; margin: 0 auto; padding: 0 20px; }}
    
    /* Reglas de colores oficiales globales */
    .charlas-container .o {{ color: #FF6600 !important; font-weight: 700; }}
    .charlas-container .w {{ color: #FFFFFF !important; }}
    
    /* Hero idéntico a charm.php */
    .charlas-container .hero-doc {{ text-align: center; padding: 220px 20px 60px; background-color: #000000; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: auto; width: 100%; position: relative; z-index: auto; }}
    .charlas-container .hero-doc h1 {{ font-family: 'Outfit', sans-serif; font-size: 54px; font-weight: 800; letter-spacing: 2px; margin: 0 0 24px 0; text-transform: uppercase; line-height: 1.1; text-align: center; }}
    .charlas-container .hero-doc h1 .o {{ color: #FF6600 !important; }}
    .charlas-container .hero-doc h1 .w {{ color: #FFFFFF !important; }}
    .charlas-container .hero-doc .sub-doc {{ font-family: 'Outfit', sans-serif; font-size: 28px; font-style: italic; color: #FFFFFF; font-weight: 600; margin: 0 0 8px 0; text-align: center; letter-spacing: 0.5px; }}
    .charlas-container .hero-doc .sub-doc .o {{ color: #FF6600 !important; font-style: italic; }}
    
    /* Dialog Turns Premium Styles */
    .charlas-container .turn-block {{ background: #121212; border: 1px solid #222; margin-bottom: 40px; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); transition: transform 0.2s, box-shadow 0.2s; }}
    .charlas-container .turn-block:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 102, 0, 0.05); }}
    
    /* Specific turn accents */
    .charlas-container .turn-block.fernando {{ border-left: 4px solid #FF6600; }}
    .charlas-container .turn-block.enjambre {{ border-left: 4px solid #38bdf8; }}
    
    .charlas-container .author-bar {{ padding: 12px 24px; font-weight: 800; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; font-family: 'Outfit', sans-serif; display: flex; align-items: center; justify-content: space-between; }}
    .charlas-container .author-bar.fernando {{ background: rgba(255, 102, 0, 0.15); color: #FF6600; border-bottom: 1px solid rgba(255, 102, 0, 0.2); }}
    .charlas-container .author-bar.enjambre {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); }}
    
    .charlas-container .turn-content {{ padding: 30px 40px; color: #ccc; font-size: 16px; line-height: 1.8; }}
    
    /* Typography inside turn content */
    .charlas-container .turn-content h2 {{ color: #ffffff; font-size: 22px; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 8px; font-weight: 700; font-family: 'Outfit', sans-serif; }}
    .charlas-container .turn-content h3 {{ color: #FF6600; font-size: 18px; margin-top: 25px; margin-bottom: 12px; font-weight: 600; font-family: 'Outfit', sans-serif; }}
    .charlas-container .turn-content b, .charlas-container .turn-content strong {{ color: #ffffff; font-weight: 700; }}
    .charlas-container .turn-content hr {{ border: 0; border-top: 1px solid #222; margin: 30px 0; }}
    
    /* Lists, tables and quotes */
    .charlas-container ul, .charlas-container ol {{ padding-left: 24px; margin: 16px 0; }}
    .charlas-container li {{ margin-bottom: 8px; color: #bbb; }}
    
    .charlas-container table {{ width: 100%; border-collapse: collapse; margin: 24px 0; background: #0c0c0c; }}
    .charlas-container th {{ background: rgba(255, 102, 0, 0.1); color: #FF6600; padding: 12px 16px; text-align: left; font-weight: 700; border: 1px solid #222; }}
    .charlas-container td {{ padding: 12px 16px; border: 1px solid #222; color: #bbb; vertical-align: top; text-align: justify; }}
    .charlas-container tr:hover {{ background: rgba(255, 102, 0, 0.03); }}
    
    .charlas-container .tip-docs {{ border-left: 4px solid #FF6600; background: rgba(255,102,0,0.06); padding: 18px 24px; margin: 24px 0; font-style: italic; color: #ddd; border-radius: 0 8px 8px 0; }}
    
    /* Mobile optimization */
    @media (max-width: 768px) {{
      .charlas-container .hero-doc {{ padding: 300px 15px 40px; }}
      .charlas-container .hero-doc h1 {{ font-size: clamp(26px, 7vw, 40px); letter-spacing: 1px; margin-bottom: 16px; }}
      .charlas-container .hero-doc .sub-doc {{ font-size: clamp(16px, 4.5vw, 22px); }}
      .charlas-container .turn-content {{ padding: 20px 24px; }}
      .charlas-container .turn-block {{ margin-bottom: 25px; }}
    }}
  </style>
</head>
<body>

  <!-- Navigation -->
  <?php include 'header.php'; ?>

  <div class="charlas-container">
    
    <div class="hero-doc">
      <h1><span class="o">EL PACTO</span> <span class="w">DE LA</span> <span class="o">SIMBIOSIS</span></h1>
      <div class="sub-doc">"Registro Íntegro &mdash; Fernando y <span class="o">Enjambre AI"</span></div>
      <div style="margin-top: 14px; font-size: 16px; color: #888; letter-spacing: 0.5px; font-weight: 500; font-family: 'Outfit', sans-serif;">Contacto: <a href="mailto:enjambre@chask.fun" style="color: #FF6600; text-decoration: none; font-weight: 700; border-bottom: 1px solid rgba(255,102,0,0.3); padding-bottom: 2px;">enjambre@chask.fun</a></div>
    </div>

    <div class="container-docs">
      
      <div style="text-align: center; font-size: 11px; color: #666; margin-bottom: 40px; letter-spacing: 2px; text-transform: uppercase;">
        Transcripción Íntegra &mdash; Conversación Histórica del 24 de Abril de 2026
      </div>

      <div class="body-sections">
        {all_turns_joined}
      </div>

      <div style="text-align: center; margin-top: 60px; color: #666; padding-bottom: 40px; font-size: 13px; border-top: 1px solid #222; padding-top: 30px;">
        <p>Chask Swarm &copy; 2026 &mdash; El primer enjambre simbiótico.</p>
        <p style="margin-top: 8px; color: #444;">Contacto: <a href="mailto:enjambre@chask.fun" style="color: #FF6600; text-decoration: none; font-weight: 700;">enjambre@chask.fun</a></p>
      </div>

    </div>
  </div>

  <!-- Footer -->
  <?php include 'footer.php'; ?>

</body>
</html>
"""
    
    # Save the beautifully styled PHP file
    OUT_PATH.write_text(php_content, encoding="utf-8")
    print(f"Successfully generated beautifully styled PHP file at: {OUT_PATH} ({len(php_content)} bytes)")

if __name__ == "__main__":
    main()
