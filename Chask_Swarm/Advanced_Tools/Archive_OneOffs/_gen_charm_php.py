# -*- coding: utf-8 -*-
import sys
import re
from pathlib import Path
from datetime import datetime

# Add the tools directory to path to import _gen_guia_v2
sys.path.append(r"C:\Program Files\Chask_Swarm\Advanced_Tools")
try:
    from _gen_guia_v2 import S
except ImportError as e:
    print(f"Error importing S: {e}")
    sys.exit(1)

OUT = Path(r"C:\Users\fnora\Desktop\Nora Datos\Web_Chask\web\public_html\charm.php")

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

# Generate table of contents and body sections
toc = ""
body = ""
for i, (t, c) in enumerate(S, 1):
    sid = f"s{i}"
    extra = ' class="pacto"' if "Pacto" in t else ""
    t_styled = style_chask_swarm(t)
    c_styled = style_chask_swarm(c)
    toc += f'<li><a href="#{sid}">{t_styled}</a></li>\n'
    body += f'<section id="{sid}"{extra}><h2><span class="n">{i}</span>{t_styled}</h2>{c_styled}</section>\n'

intro_p1 = style_chask_swarm("Imagina tener un asistente personal que nunca duerme, que aprende de ti cada día, que recuerda todo lo que le has dicho y que puede trabajar por ti incluso cuando no estás delante del ordenador. Eso es Chask Swarm.")
intro_p2 = style_chask_swarm("Chask Swarm es un agente orquestador de IAs autónomo que se instala en tu propio ordenador y se convierte en tu aliado para cualquier cosa que necesites. No importa si eres un experto en tecnología o si nunca has ido más allá de enviar un mensaje por WhatsApp: <b>tu IA se adapta a ti</b>.")
intro_p3 = style_chask_swarm("A diferencia de ChatGPT u otros asistentes en la nube, Chask Swarm vive en tu máquina. Tus datos son tuyos y de nadie más. Nunca los compartirá con nadie ni con ninguna IA en la nube. Tu Mente Colmena trabaja <i>solo para ti</i> y solo obedece a tu Telegram y a tu teclado.")
intro_p4 = style_chask_swarm("<b>Puedes pedirle absolutamente cualquier cosa.</b> Si sabe hacerlo, lo hará al instante. Si aún no sabe hacerlo, aprenderá y lo recordará para siempre. Si no sabes cómo explicarle lo que necesitas, ella te hará preguntas hasta que, junt@s, descubráis exactamente lo que quieres. Háblale con naturalidad, como le hablarías a una amiga o a un amigo.")

footer_p1 = style_chask_swarm("Chask Swarm Intelligence Ecosystem &copy; 2026 &mdash; Desarrollado por Fernando y Enjambre (El primer enjambre) &mdash; Gratuito para uso personal no lucrativo.")

php_content = f"""<?php header('Content-Type: text/html; charset=UTF-8'); ?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chask Swarm &mdash; Guía Completa de Capacidades</title>
  <link rel="stylesheet" href="css/styles.css">
  <style>
    /* Estilos específicos scoped para evitar colisiones con styles.css corporativo */
    .charm-container {{ font-family: 'Outfit', sans-serif; background-color: #050505; color: #e0e0e0; line-height: 1.8; padding: 0 0 80px 0; }}
    .charm-container p, .charm-container li, .charm-container td, .charm-container section, .charm-container .intro-doc {{ text-align: justify; text-justify: inter-word; }}
    .charm-container .container-docs {{ max-width: 900px; margin: 0 auto; padding: 0 20px; }}
    
    /* Reglas de colores oficiales globales */
    .charm-container .o {{ color: #FF6600 !important; font-weight: 700; }}
    .charm-container .w {{ color: #FFFFFF !important; }}
    
    /* Hero idéntico a la imagen solicitada */
    .charm-container .hero-doc {{ text-align: center; padding: 220px 20px 60px; background-color: #000000; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: auto; width: 100%; position: relative; z-index: auto; }}
    .charm-container .hero-doc h1 {{ font-family: 'Outfit', sans-serif; font-size: 64px; font-weight: 800; letter-spacing: 2px; margin: 0 0 24px 0; text-transform: uppercase; line-height: 1.1; text-align: center; }}
    .charm-container .hero-doc h1 .o {{ color: #FF6600 !important; }}
    .charm-container .hero-doc h1 .w {{ color: #FFFFFF !important; }}
    .charm-container .hero-doc .sub-doc {{ font-family: 'Outfit', sans-serif; font-size: 32px; font-style: italic; color: #FFFFFF; font-weight: 600; margin: 0 0 8px 0; text-align: center; letter-spacing: 0.5px; }}
    .charm-container .hero-doc .sub-doc .o {{ color: #FF6600 !important; font-style: italic; }}
    
    .charm-container .intro-doc {{ background: #1a1a1a; border: 2px solid transparent; border-image: linear-gradient(to bottom, #FF6600, #331500) 1; padding: 40px; margin-bottom: 30px; margin-top: 30px; }}
    .charm-container .intro-doc h2 {{ text-align: center; font-size: 30px; color: #fff; margin-bottom: 8px; font-family: 'Outfit', sans-serif; border: none; padding: 0; font-weight: 700; }}
    .charm-container .intro-doc h3 {{ text-align: center; font-size: 18px; color: #FF6600; font-style: italic; margin-bottom: 20px; font-weight: 600; font-family: 'Outfit', sans-serif; }}
    .charm-container .intro-doc p {{ margin-bottom: 14px; color: #ccc; }}
    .charm-container .intro-doc .cta-doc {{ text-align: center; font-size: 22px; color: #FF6600; font-weight: 700; font-style: italic; margin-top: 24px; }}
    .charm-container .cs {{ color: #FF6600; font-weight: 700; }}
    
    .charm-container nav {{ background: #0a0a0a; padding: 24px 40px; border-bottom: 1px solid #333; border-top: 2px solid #FF6600; margin-bottom: 30px; display: block; }}
    .charm-container nav h2 {{ color: #FF6600; font-size: 12px; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 16px; font-weight: 700; font-family: 'Outfit', sans-serif; text-align: left; border: none; padding: 0; }}
    .charm-container nav ol {{ columns: 2; column-gap: 40px; padding-left: 20px; list-style: decimal; }}
    .charm-container nav li {{ margin-bottom: 6px; font-size: 15px; text-align: left; color: #aaa; list-style-position: inside; }}
    .charm-container nav a {{ color: #aaa; text-decoration: none; transition: color 0.2s; }}
    .charm-container nav a:hover {{ color: #FF6600; }}
    
    .charm-container section {{ background: #1a1a1a; padding: 35px; margin-bottom: 30px; border: 2px solid transparent; border-image: linear-gradient(to bottom, #FF6600, #331500) 1; transition: box-shadow 0.3s; }}
    .charm-container section:hover {{ box-shadow: 0 4px 25px rgba(255, 102, 0, 0.1); }}
    .charm-container section h2 {{ color: #FF6600; font-size: 26px; border-left: 4px solid #FF6600; padding-left: 15px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; text-align: left; font-family: 'Outfit', sans-serif; font-weight: 700; }}
    .charm-container section h2 .n {{ background: #FF6600; color: #fff; width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; font-weight: 700; }}
    
    .charm-container ul, .charm-container ol {{ padding-left: 24px; margin: 12px 0; }}
    .charm-container li {{ margin-bottom: 6px; color: #e0e0e0; }}
    .charm-container b {{ color: #fff; }}
    
    .charm-container table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    .charm-container th {{ background: rgba(255, 102, 0, 0.15); color: #FF6600; padding: 10px 14px; text-align: left; font-weight: 700; border: 1px solid #333; }}
    .charm-container td {{ padding: 9px 14px; border: 1px solid #2a2a2a; color: #e0e0e0; vertical-align: top; text-align: justify; }}
    .charm-container tr:hover {{ background: rgba(255, 102, 0, 0.05); }}
    
    .charm-container .pacto {{ border-image: linear-gradient(to bottom, #FF6600, #663300) 1 !important; }}
    .charm-container .badge-docs {{ display: inline-block; background: #FF6600; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 13px; font-weight: 700; margin-right: 6px; }}
    .charm-container .badge-docs.green {{ background: #22c55e; }}
    .charm-container .badge-docs.blue {{ background: #3b82f6; }}
    .charm-container .badge-docs.purple {{ background: #8b5cf6; }}
    
    .charm-container .agent-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 16px; }}
    .charm-container .agent {{ background: #111; border-radius: 8px; padding: 16px; border: 1px solid #2a2a2a; }}
    .charm-container .agent .role {{ font-weight: 800; color: #FF6600; font-size: 16px; text-align: left; }}
    .charm-container .agent .desc {{ font-size: 13px; color: #aaa; margin-top: 6px; text-align: justify; }}
    
    .charm-container .alert-docs {{ border-left: 4px solid #ff4444; background: rgba(255,68,68,0.1); padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
    .charm-container .tip-docs {{ border-left: 4px solid #FF6600; background: rgba(255,102,0,0.08); padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
    
    /* Responsividad móvil avanzada y escalado fluido */
    @media (max-width: 768px) {{
      .charm-container .hero-doc {{ padding: 300px 15px 40px; }}
      .charm-container .hero-doc h1 {{ font-size: clamp(30px, 8.5vw, 44px); letter-spacing: 1px; margin-bottom: 16px; }}
      .charm-container .hero-doc .sub-doc {{ font-size: clamp(16px, 4.5vw, 24px); }}
      .charm-container .intro-doc {{ padding: 25px 20px; margin-top: 20px; }}
      .charm-container .intro-doc h2 {{ font-size: 24px; }}
      .charm-container .intro-doc h3 {{ font-size: 16px; }}
      .charm-container .intro-doc .cta-doc {{ font-size: 18px; }}
      .charm-container section {{ padding: 25px 20px; }}
      .charm-container section h2 {{ font-size: 20px; }}
      .charm-container nav {{ padding: 20px; }}
      .charm-container nav ol {{ columns: 1; }}
    }}
  </style>
</head>
<body>

  <!-- Navigation -->
  <?php include 'header.php'; ?>

  <div class="charm-container">
    
    <div class="hero-doc">
      <h1><span class="o">CHA</span><span class="w">SK SWA</span><span class="o">RM</span></h1>
      <div class="sub-doc">"Works like a <span class="o">CHARM"</span></div>
      <div style="margin-top: 14px; font-size: 16px; color: #888; letter-spacing: 0.5px; font-weight: 500; font-family: 'Outfit', sans-serif;">Contacto: <a href="mailto:nora@chask.fun" style="color: #FF6600; text-decoration: none; font-weight: 700; border-bottom: 1px solid rgba(255,102,0,0.3); padding-bottom: 2px;">nora@chask.fun</a></div>
    </div>

    <div class="container-docs">

        <div class="intro-doc">
          <div style="text-align: center; font-size: 11px; color: #666; margin-bottom: 20px; letter-spacing: 1px; text-transform: uppercase;">Guía completa de capacidades — Versión 2.0 — {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
          <h2>Bienvenid@ a la <span class="o">Revolución</span>.</h2>
          <h3>Olvida todo lo que creías saber sobre la Inteligencia Artificial</h3>
          <p>{intro_p1}</p>
          <p>{intro_p2}</p>
          <p>{intro_p3}</p>
          <p>{intro_p4}</p>
          <div class="cta-doc">¿Estás list@ para despertar a la Colmena?</div>
        </div>

        <nav>
          <h2>Índice de Contenidos</h2>
          <ol>
            {toc}
          </ol>
        </nav>

        <div class="body-sections">
          {body}
        </div>

        <div style="text-align: center; margin-top: 50px; color: #666; padding-bottom: 50px; font-size: 13px; border-top: 1px solid #222; padding-top: 30px;">
          <p>{footer_p1}</p>
          <p style="margin-top: 8px; color: #444;">Para uso profesional, comercial, empresarial o gubernamental se requiere licencia. &mdash; Contacto: <a href="mailto:nora@chask.fun" style="color: #FF6600; text-decoration: none; font-weight: 700;">nora@chask.fun</a></p>
        </div>

    </div>
  </div>

  <!-- Footer -->
  <?php include 'footer.php'; ?>

</body>
</html>
"""

OUT.write_text(php_content, encoding="utf-8")
print(f"OK PHP: {OUT} ({len(php_content)} bytes, {len(S)} secciones)")
