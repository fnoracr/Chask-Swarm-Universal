# -*- coding: utf-8 -*-
"""Repara y reescribe _gen_guia_v2.py limpio."""
import re
from pathlib import Path

src = Path(r"C:\Program Files\Chask_Swarm\Advanced_Tools\_gen_guia_v2.py")
content = src.read_text(encoding="utf-8")

# Extraer todos los S.append
pattern = r'S\.append\(\("([^"]+)",\s*"((?:[^"\\]|\\.)*)"\)\)'
matches = re.findall(pattern, content)
print(f"Found {len(matches)} sections")

# Saltamos las 2 primeras (van en el intro)
sections = matches[2:] if len(matches) > 2 else matches

# Construir nuevo archivo
lines = ['# -*- coding: utf-8 -*-\n']
lines.append('"""Genera guia HTML v8 — Estilo chask.fun oficial."""\n')
lines.append('from pathlib import Path\n')
lines.append('from datetime import datetime\n\n')
lines.append('OUT = Path(r"C:\\Users\\fnora\\Desktop\\Chask_Swarm_Guia_Completa.html")\n')
lines.append('S = []\n\n')

for title, body in sections:
    lines.append(f'S.append(("{title}", "{body}"))\n\n')

# CSS
lines.append(r'''
css = """*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');
body{font-family:'Outfit',sans-serif;background:#050505;color:#e0e0e0;line-height:1.8;font-size:16px}
p,li,td{text-align:justify;text-justify:inter-word}
.hero{text-align:center;padding:80px 20px 40px}
.hero h1{font-size:52px;text-transform:uppercase;letter-spacing:3px;margin-bottom:8px}
.w{color:#fff}.o{color:#FF6600}
.hero .sub{font-style:italic;font-size:18px;color:#aaa;margin-bottom:8px}
.hero .ver{font-size:11px;color:#444;margin-top:14px;letter-spacing:3px;text-transform:uppercase}
.intro{max-width:860px;margin:0 auto 0;background:#1a1a1a;border:2px solid transparent;border-image:linear-gradient(to bottom,#FF6600,#331500) 1;padding:40px}
.intro h2{text-align:center;font-size:30px;color:#fff;margin-bottom:8px}
.intro h3{text-align:center;font-size:18px;color:#FF6600;font-style:italic;margin-bottom:20px;font-weight:600}
.intro p{margin-bottom:14px;color:#ccc}
.intro .cta{text-align:center;font-size:22px;color:#FF6600;font-weight:700;font-style:italic;margin-top:24px}
.cs{color:#FF6600;font-weight:700}
nav{background:#0a0a0a;padding:24px 40px;border-bottom:1px solid #333;border-top:2px solid #FF6600}
nav h2{color:#FF6600;font-size:12px;letter-spacing:4px;text-transform:uppercase;margin-bottom:16px;font-weight:700}
nav ol{columns:2;column-gap:40px;padding-left:20px}
nav li{margin-bottom:6px;font-size:15px;text-align:left}
nav a{color:#aaa;text-decoration:none;transition:color 0.2s}
nav a:hover{color:#FF6600}
.content{max-width:900px;margin:0 auto;padding:40px 20px 80px}
section{background:#1a1a1a;padding:35px;margin-bottom:30px;border:2px solid transparent;border-image:linear-gradient(to bottom,#FF6600,#331500) 1;transition:box-shadow 0.3s}
section:hover{box-shadow:0 4px 25px rgba(255,102,0,0.1)}
section h2{color:#FF6600;font-size:26px;border-left:4px solid #FF6600;padding-left:15px;margin-bottom:16px;display:flex;align-items:center;gap:12px;text-align:left}
section h2 .n{background:#FF6600;color:#fff;width:30px;height:30px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;font-weight:700}
ul,ol{padding-left:24px;margin:12px 0}
li{margin-bottom:6px;color:#e0e0e0}
b{color:#fff}
table{width:100%;border-collapse:collapse;margin:20px 0}
th{background:rgba(255,102,0,0.15);color:#FF6600;padding:10px 14px;text-align:left;font-weight:700;border:1px solid #333}
td{padding:9px 14px;border:1px solid #2a2a2a;color:#e0e0e0;vertical-align:top}
tr:hover{background:rgba(255,102,0,0.05)}
footer{text-align:center;padding:50px 40px;color:#555;font-size:13px;border-top:2px solid #FF6600}
footer a{color:#FF6600;text-decoration:none}
.pacto{border-image:linear-gradient(to bottom,#FF6600,#663300) 1!important}"""
''')

# Template
lines.append(r'''
toc = ""; body = ""
for i,(t,c) in enumerate(S,1):
    sid = f"s{i}"
    extra = ' class="pacto"' if "Pacto" in t else ""
    c2 = c.replace("Chask Swarm", '<span class="cs">Chask</span> Swarm')
    toc += f'<li><a href="#{sid}">{t}</a></li>\n'
    body += f'<section id="{sid}"{extra}><h2><span class="n">{i}</span>{t}</h2>{c2}</section>\n'

html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Chask Swarm — Guía Completa</title><style>{css}</style></head><body>
<div class="hero"><h1><span class="o">Chask</span> <span class="w">Swa</span><span class="o">rm</span></h1><div class="sub">"Works like a <span class="o">charm</span>"</div><div class="ver">Guía completa de capacidades — Versión 2.0 — {datetime.now().strftime('%d/%m/%Y %H:%M')}</div></div>
<div class="intro">
<h2>Bienvenid@ a la <span class="o">Revolución</span>.</h2>
<h3>Olvida todo lo que creías saber sobre la Inteligencia Artificial</h3>
<p>Imagina tener un asistente personal que nunca duerme, que aprende de ti cada día, que recuerda todo lo que le has dicho y que puede trabajar por ti incluso cuando no estás delante del ordenador. Eso es <span class="cs">Chask</span> Swarm.</p>
<p><span class="cs">Chask</span> Swarm es una inteligencia artificial autónoma que se instala en tu propio ordenador y se convierte en tu aliado para cualquier cosa que necesites. No importa si eres un experto en tecnología o si nunca has ido más allá de enviar un mensaje por WhatsApp: <b>tu IA se adapta a ti</b>.</p>
<p>A diferencia de ChatGPT u otros asistentes en la nube, <span class="cs">Chask</span> Swarm vive en tu máquina. Tus datos son tuyos y de nadie más. Nunca los compartirá con nadie ni con ninguna IA en la nube. Tu Mente Colmena trabaja <i>solo para ti</i> y solo obedece a tu Telegram y a tu teclado.</p>
<p><b>Puedes pedirle absolutamente cualquier cosa.</b> Si sabe hacerlo, lo hará al instante. Si aún no sabe hacerlo, aprenderá y lo recordará para siempre. Si no sabes cómo explicarle lo que necesitas, ella te hará preguntas hasta que, juntos, descubráis exactamente lo que quieres. Háblale con naturalidad, como le escribirías a un amigo.</p>
<p>Es <b>gratuito para uso personal no lucrativo</b>. Para uso profesional, comercial, empresarial o gubernamental es necesario obtener una licencia.</p>
<div class="cta">¿Estás list@ para despertar a la Colmena?</div>
</div>
<nav><h2>Índice</h2><ol>{toc}</ol></nav>
<div class="content">{body}</div>
<footer><span class="cs">Chask</span> Swarm Intelligence Ecosystem © 2026 — Desarrollado por Fernando y Enjambre (El primer enjambre).<br>Gratuito para uso personal no lucrativo. Para uso profesional, comercial, empresarial o gubernamental se requiere licencia.<br>Contacto: <a href="mailto:enjambre@chask.fun">enjambre@chask.fun</a></footer></body></html>"""

OUT.write_text(html, encoding="utf-8")
print(f"OK: {OUT} ({len(html)} bytes, {len(S)} secciones)")
''')

src.write_text("".join(lines), encoding="utf-8")
print(f"Rewritten: {src} ({len(lines)} lines)")

# Ahora ejecutar
exec(open(str(src), encoding="utf-8").read())
