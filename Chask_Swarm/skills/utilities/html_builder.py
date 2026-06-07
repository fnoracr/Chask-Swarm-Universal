"""
html_builder.py — Skill para generar HTMLs largos sin exceder tokens
=====================================================================
Genera archivos HTML grandes mediante plantillas Python, evitando que
Charm exceda el límite de tokens al escribir HTML inline.

Uso:
  from html_builder import HTMLBuilder
  b = HTMLBuilder("Mi Página", theme="dark")
  b.add_css(css_string)
  b.add_section("titulo", html_content)
  b.save("output.html")
  
  # O directamente:
  python html_builder.py --template dashboard --output archivo.html
"""
import os, sys, json

class HTMLBuilder:
    def __init__(self, title="", theme="dark", lang="es"):
        self.title = title
        self.theme = theme
        self.lang = lang
        self.css_blocks = []
        self.sections = []
        self.scripts = []
        self.meta = []
        self.fonts = ['https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap']

    def add_font(self, url):
        self.fonts.append(url)
        return self

    def add_meta(self, name, content):
        self.meta.append(f'<meta name="{name}" content="{content}">')
        return self

    def add_css(self, css):
        self.css_blocks.append(css)
        return self

    def add_section(self, html):
        self.sections.append(html)
        return self

    def add_script(self, js):
        self.scripts.append(js)
        return self

    def build(self):
        fonts = "\n".join(f'<link rel="preconnect" href="https://fonts.googleapis.com"><link href="{f}" rel="stylesheet">' for f in self.fonts)
        meta = "\n".join(self.meta)
        css = "\n".join(f"<style>{c}</style>" for c in self.css_blocks)
        body = "\n".join(self.sections)
        scripts = "\n".join(f"<script>{s}</script>" for s in self.scripts)
        return f"""<!DOCTYPE html>
<html lang="{self.lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{self.title}</title>
{meta}
{fonts}
{css}
</head>
<body>
{body}
{scripts}
</body>
</html>"""

    def save(self, path):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.build())
        print(f"HTML guardado: {path} ({os.path.getsize(path)} bytes)")
        return path


# ─── Componentes reutilizables ────────────────────────────────

def card(title, content, icon="", cls=""):
    return f'<div class="card {cls}"><h3>{icon} {title}</h3><div class="card-body">{content}</div></div>'

def progress_bar(label, value, max_val=100, color="#00f5d4"):
    pct = min(100, int(value / max_val * 100))
    return f'<div class="progress-item"><span class="prog-label">{label}</span><div class="prog-bar"><div class="prog-fill" style="width:{pct}%;background:{color}"></div></div><span class="prog-val">{value}/{max_val}</span></div>'

def badge(text, color="#00f5d4"):
    return f'<span class="badge" style="background:{color}20;color:{color};border:1px solid {color}40">{text}</span>'

def table(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = ""
    for row in rows:
        tds = "".join(f"<td>{c}</td>" for c in row)
        trs += f"<tr>{tds}</tr>"
    return f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'

def score_ring(label, score, color="#00f5d4"):
    pct = score * 3.6
    return f'''<div class="score-ring">
<svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="54" fill="none" stroke="#1a1a2e" stroke-width="8"/>
<circle cx="60" cy="60" r="54" fill="none" stroke="{color}" stroke-width="8" stroke-dasharray="{score*3.39} 999" stroke-linecap="round" transform="rotate(-90 60 60)" class="ring-anim"/></svg>
<div class="score-num">{score}</div><div class="score-label">{label}</div></div>'''


# ─── CSS Base Premium ─────────────────────────────────────────

DARK_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#0a0a1a;color:#e0e0e0;line-height:1.6;overflow-x:hidden}
.container{max-width:1200px;margin:0 auto;padding:0 24px}
h1{font-size:2.8rem;font-weight:900;background:linear-gradient(135deg,#00f5d4,#7b61ff,#f72585);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:8px}
h2{font-size:1.6rem;font-weight:700;color:#fff;margin:48px 0 24px;padding-bottom:12px;border-bottom:2px solid #1a1a3e}
h3{font-size:1.1rem;font-weight:600;color:#fff;margin-bottom:12px}
.subtitle{text-align:center;color:#888;font-size:1rem;margin-bottom:40px}
.hero{padding:60px 0 30px;text-align:center}
.grid{display:grid;gap:20px}
.grid-2{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.grid-3{grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.grid-4{grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.card{background:linear-gradient(135deg,#12122a,#1a1a3e);border:1px solid #2a2a4e;border-radius:16px;padding:24px;transition:transform .2s,box-shadow .2s}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,245,212,.08)}
.card.glow-green{border-color:#00f5d440}
.card.glow-purple{border-color:#7b61ff40}
.card.glow-pink{border-color:#f7258540}
.card.glow-yellow{border-color:#ffd60a40}
table{width:100%;border-collapse:collapse;margin:16px 0}
th{background:#1a1a3e;color:#00f5d4;padding:12px 16px;text-align:left;font-weight:600;font-size:.85rem;text-transform:uppercase;letter-spacing:.5px}
td{padding:10px 16px;border-bottom:1px solid #1a1a3e;font-size:.9rem}
tr:hover{background:#12122a}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:600;margin:2px}
.progress-item{display:flex;align-items:center;gap:12px;margin:8px 0}
.prog-label{min-width:140px;font-size:.85rem;color:#aaa}
.prog-bar{flex:1;height:8px;background:#1a1a3e;border-radius:4px;overflow:hidden}
.prog-fill{height:100%;border-radius:4px;transition:width 1.5s ease}
.prog-val{font-size:.8rem;color:#666;min-width:60px;text-align:right}
.score-ring{text-align:center;position:relative;width:130px;margin:0 auto}
.score-ring svg{width:120px;height:120px}
.score-num{position:absolute;top:38px;left:50%;transform:translateX(-50%);font-size:2rem;font-weight:900;color:#fff}
.score-label{font-size:.85rem;color:#aaa;margin-top:8px}
.ring-anim{animation:ring 1.5s ease forwards}
@keyframes ring{from{stroke-dasharray:0 999}}
.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.dot-green{background:#00f5d4}
.dot-yellow{background:#ffd60a}
.dot-red{background:#f72585}
.phase-tag{display:inline-block;padding:4px 12px;border-radius:8px;font-size:.75rem;font-weight:700;margin-right:8px}
.tag-done{background:#00f5d420;color:#00f5d4}
.tag-active{background:#7b61ff20;color:#7b61ff}
.tag-pending{background:#66666620;color:#999}
footer{text-align:center;padding:40px 0;color:#444;font-size:.8rem;border-top:1px solid #1a1a3e;margin-top:60px}
@media(max-width:768px){h1{font-size:2rem}.grid-4{grid-template-columns:1fr 1fr}}
"""

if __name__ == "__main__":
    print("html_builder.py — Skill para HTMLs largos")
    print("Uso: from html_builder import HTMLBuilder, card, table, score_ring, DARK_CSS")
