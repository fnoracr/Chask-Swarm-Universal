"""
daily_report.py — Informe Diario Premium con HTML + Metricas
=============================================================
Genera un informe visual HTML con graficas, metricas de uso,
tendencias y comparativa semanal. Envía por Telegram + guarda en Qdrant.
"""
import os, sys, io, subprocess, json, time
from datetime import datetime, timedelta

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY    = os.path.join(BASE_DIR, "memory.md")
AUDIT     = os.path.join(BASE_DIR, "Logs_Sistema", "security_audit.log")
TG_SCRIPT = os.path.join(BASE_DIR, "charm_telegram.py")
QDR       = os.path.join(TOOLS_DIR, "qdrant_memory_manager.py")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
LLM_USAGE = os.path.join(TOOLS_DIR, "llm_usage_today.json")
LEARNER_LOG = os.path.join(BASE_DIR, "skill_learner_log.json")
SANDBOX_AUDIT = os.path.join(BASE_DIR, "sandbox_audit.log")

sys.path.insert(0, TOOLS_DIR)

os.makedirs(REPORT_DIR, exist_ok=True)


def send_telegram(msg: str):
    subprocess.run([sys.executable, TG_SCRIPT, "send", msg],
                   capture_output=True, timeout=20)

def send_doc(path: str, caption: str = ""):
    try:
        subprocess.run([sys.executable, os.path.join(TOOLS_DIR, "send_doc.py"), path, caption],
                       capture_output=True, timeout=30)
    except Exception:
        pass


def get_daemon_count() -> int:
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV"],
                          capture_output=True, text=True, timeout=5)
        return r.stdout.count("pythonw.exe")
    except Exception:
        return 0


def get_qdrant_stats() -> dict:
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        cols = client.get_collections().collections
        total_points = 0
        col_list = []
        for c in cols:
            info = client.get_collection(c.name)
            total_points += info.points_count
            col_list.append({"name": c.name, "points": info.points_count})
        return {"collections": len(cols), "total_points": total_points, "list": col_list}
    except Exception:
        return {"collections": 0, "total_points": 0, "list": []}


def get_llm_usage() -> dict:
    if os.path.exists(LLM_USAGE):
        try:
            with open(LLM_USAGE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_skills_learned_today() -> int:
    if os.path.exists(LEARNER_LOG):
        try:
            with open(LEARNER_LOG, encoding="utf-8") as f:
                logs = json.load(f)
            today = datetime.now().strftime("%Y-%m-%d")
            return sum(1 for l in logs if l.get("ts", "").startswith(today))
        except Exception:
            pass
    return 0


def get_audit_actions_today() -> list:
    actions = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    for log_file in [AUDIT, SANDBOX_AUDIT]:
        if os.path.exists(log_file):
            try:
                with open(log_file, encoding="utf-8") as f:
                    for line in f:
                        if today_str in line:
                            actions.append(line.strip())
            except Exception:
                pass
    return actions


def get_memory_summary() -> list:
    if os.path.exists(MEMORY):
        with open(MEMORY, encoding="utf-8") as f:
            mem = f.read()
        return [l.strip() for l in mem.splitlines()
                if l.strip() and any(k in l for k in ["Tarea", "Proyecto", "Paso", "COMPLETADO", "completad", "Estado", "|"])][:15]
    return []

def get_social_stats() -> dict:
    from playwright.sync_api import sync_playwright
    import re
    stats = {
        "Twitter": {"seguidores": "N/A", "suscriptores": "N/A"},
        "Instagram": {"seguidores": "N/A", "suscriptores": "N/A"},
        "Patreon": {"seguidores": "N/A", "suscriptores": "N/A"}
    }
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Twitter
            try:
                page.goto('https://x.com/fernandonora', timeout=30000)
                page.wait_for_timeout(3000)
                text = page.evaluate('document.body.innerText')
                match = re.search(r'([0-9.,kmKM]+)\s*Followers?', text, re.IGNORECASE)
                if match:
                    stats['Twitter']['seguidores'] = match.group(1)
            except:
                pass
                
            # Instagram
            try:
                page.goto('https://www.instagram.com/fernandonora/', timeout=30000)
                page.wait_for_timeout(3000)
                text = page.evaluate('document.body.innerText')
                match = re.search(r'([0-9.,kmKM]+)\s*followers?', text, re.IGNORECASE)
                if match:
                    stats['Instagram']['seguidores'] = match.group(1)
            except:
                pass
                
            # Patreon
            try:
                page.goto('https://www.patreon.com/Tuprofeonline992', timeout=30000)
                page.wait_for_timeout(3000)
                text = page.evaluate('document.body.innerText')
                match = re.search(r'([0-9.,kmKM]+)\s*members?', text, re.IGNORECASE)
                if match:
                    stats['Patreon']['suscriptores'] = match.group(1)
            except:
                pass
                
            browser.close()
    except Exception as e:
        print(f"Error web scraping: {e}")
        
    return stats

def get_github_stats() -> dict:
    import urllib.request
    stats = {"stars": "N/A", "downloads": 0}
    try:
        req = urllib.request.Request("https://api.github.com/repos/nora-chask/chask-swarm", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            stats["stars"] = data.get("stargazers_count", 0)
            
        req2 = urllib.request.Request("https://api.github.com/repos/nora-chask/chask-swarm/releases", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2, timeout=10) as response2:
            data2 = json.loads(response2.read().decode())
            total_downloads = sum(asset.get("download_count", 0) for release in data2 for asset in release.get("assets", []))
            stats["downloads"] = total_downloads
    except Exception:
        pass
    return stats

def get_web_stats() -> dict:
    import ftplib
    stats = {"visits_charm": 0, "visits_blog": 0, "downloads": 0}
    try:
        ftp = ftplib.FTP('46.202.172.31')
        ftp.login('u336848474.chask.fun', 'AQUI_VA_TU_FTP_PASS')
        ftp.cwd('/public_html/charm')
        
        mem_file = io.BytesIO()
        ftp.retrbinary('RETR stats.json', mem_file.write)
        ftp.quit()
        
        mem_file.seek(0)
        data = json.loads(mem_file.read().decode())
        stats["visits_charm"] = len(data.get("visits", {}).get("charm", []))
        stats["visits_blog"] = len(data.get("visits", {}).get("blog", []))
        stats["downloads"] = data.get("downloads", 0)
    except Exception:
        pass
    return stats


def generate_html_report() -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    now = datetime.now().strftime("%H:%M")

    daemons = get_daemon_count()
    qdrant = get_qdrant_stats()
    llm = get_llm_usage()
    skills_today = get_skills_learned_today()
    audit = get_audit_actions_today()
    memory = get_memory_summary()
    social = get_social_stats()
    github = get_github_stats()
    web = get_web_stats()

    llm_calls = 0
    if llm:
        for v in llm.values():
            if isinstance(v, (int, float)):
                llm_calls += int(v)
            elif isinstance(v, dict):
                llm_calls += v.get("calls", 0)

    # Collections bar chart data
    col_data = qdrant.get("list", [])[:10]
    col_labels = [c["name"][:15] for c in col_data]
    col_values = [c["points"] for c in col_data]
    max_val = max(col_values) if col_values else 1

    col_bars = ""
    for name, val in zip(col_labels, col_values):
        pct = (val / max_val) * 100
        col_bars += f'<div class="bar-row"><span class="bar-label">{name}</span><div class="bar-bg"><div class="bar-fill" style="width:{pct}%"></div></div><span class="bar-val">{val}</span></div>\n'

    memory_html = ""
    for line in memory:
        memory_html += f"<div class='mem-line'>{line}</div>\n"

    audit_html = ""
    for a in audit[-8:]:
        audit_html += f"<div class='audit-line'>{a[:100]}</div>\n"

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<title>Daily Report — {today}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Outfit',sans-serif;background:#0a0a1a;color:#e0e0e0;padding:20px 30px}}
h1{{text-align:center;font-size:1.6em;font-weight:800;background:linear-gradient(135deg,#ff6b6b,#7b2ff7,#00d4ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px}}
.sub{{text-align:center;color:#666;margin-bottom:16px;font-size:12px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}}
.stat{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:14px;text-align:center}}
.stat-val{{font-size:28px;font-weight:800;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.stat-label{{font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
h2{{color:#00d4ff;font-size:1em;margin:18px 0 8px;border-bottom:1px solid #7b2ff733;padding-bottom:4px}}
.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:12px;margin:8px 0}}
.bar-row{{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:11px}}
.bar-label{{width:100px;text-align:right;color:#888;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bar-bg{{flex:1;height:14px;background:rgba(255,255,255,0.05);border-radius:7px;overflow:hidden}}
.bar-fill{{height:100%;background:linear-gradient(90deg,#7b2ff7,#00d4ff);border-radius:7px;transition:width 0.5s}}
.bar-val{{width:40px;color:#00d4ff;font-weight:600}}
.mem-line{{font-size:11px;padding:2px 0;color:#ccc;border-bottom:1px solid rgba(255,255,255,0.03)}}
.audit-line{{font-size:10px;padding:2px 0;color:#888;font-family:monospace}}
.footer{{text-align:center;color:#333;margin-top:20px;font-size:10px}}
</style></head><body>

<h1>Daily Report — Chask Swarm</h1>
<p class="sub">{today} {now} | Generado automaticamente</p>

<div class="stats">
<div class="stat"><div class="stat-val">{daemons}</div><div class="stat-label">Daemons activos</div></div>
<div class="stat"><div class="stat-val">{qdrant['total_points']}</div><div class="stat-label">Puntos Qdrant</div></div>
<div class="stat"><div class="stat-val">{llm_calls}</div><div class="stat-label">Llamadas LLM hoy</div></div>
<div class="stat"><div class="stat-val">{skills_today}</div><div class="stat-label">Skills aprendidos</div></div>
</div>

<h2>Audiencia e Impacto</h2>
<div class="stats" style="grid-template-columns:repeat(5,1fr);">
<div class="stat"><div class="stat-val" style="color:#1DA1F2">{social['Twitter']['seguidores']}</div><div class="stat-label">X Followers<br><small>({social['Twitter']['suscriptores']} subs)</small></div></div>
<div class="stat"><div class="stat-val" style="color:#C13584">{social['Instagram']['seguidores']}</div><div class="stat-label">Insta Followers<br><small>({social['Instagram']['suscriptores']} subs)</small></div></div>
<div class="stat"><div class="stat-val" style="color:#FF424D">{social['Patreon']['seguidores']}</div><div class="stat-label">Patreon Seguidores<br><small>({social['Patreon']['suscriptores']} subs)</small></div></div>
<div class="stat"><div class="stat-val" style="color:#FFC107">{github['stars']}</div><div class="stat-label">GitHub Stars</div></div>
<div class="stat"><div class="stat-val" style="color:#4CAF50">{web['downloads'] + github['downloads']}</div><div class="stat-label">Total Descargas</div></div>
</div>

<div class="card" style="display:flex; justify-content:space-around; text-align:center;">
    <div><span style="color:#888;font-size:12px;">Visitas Blog:</span> <b style="color:#fff">{web['visits_blog']}</b></div>
    <div><span style="color:#888;font-size:12px;">Visitas Charm:</span> <b style="color:#fff">{web['visits_charm']}</b></div>
</div>

<h2>Colecciones Qdrant ({qdrant['collections']})</h2>
<div class="card">{col_bars if col_bars else '<p style="color:#666">Sin colecciones</p>'}</div>

<h2>Trabajo realizado</h2>
<div class="card">{memory_html if memory_html else '<p style="color:#666">Sin registros</p>'}</div>

<h2>Auditoria de seguridad ({len(audit)} acciones)</h2>
<div class="card">{audit_html if audit_html else '<p style="color:#666">Sin acciones hoy</p>'}</div>

<p class="footer">Chask Swarm Daily Report | {today}</p>
</body></html>"""
    return html


def generate_text_report() -> str:
    """Version texto para Telegram."""
    today = datetime.now().strftime("%d/%m/%Y")
    daemons = get_daemon_count()
    qdrant = get_qdrant_stats()
    skills_today = get_skills_learned_today()
    audit = get_audit_actions_today()
    memory = get_memory_summary()
    social = get_social_stats()
    github = get_github_stats()
    web = get_web_stats()

    lines = [f"INFORME DIARIO - {today}\n"]
    lines.append(f"Daemons: {daemons} | Qdrant: {qdrant['total_points']} pts | Skills: {skills_today}")
    lines.append(f"\n📊 AUDIENCIA:")
    lines.append(f"- X: {social['Twitter']['seguidores']} seg / {social['Twitter']['suscriptores']} sub")
    lines.append(f"- Insta: {social['Instagram']['seguidores']} seg / {social['Instagram']['suscriptores']} sub")
    lines.append(f"- Patreon: {social['Patreon']['seguidores']} seg / {social['Patreon']['suscriptores']} sub")
    lines.append(f"- GitHub Stars: {github['stars']}")
    lines.append(f"- Descargas (Web+Git): {web['downloads'] + github['downloads']}")
    lines.append(f"- Visitas (Charm: {web['visits_charm']} | Blog: {web['visits_blog']})")
    
    if memory:
        lines.append("\nTrabajo:")
        lines.extend([f"  {l}" for l in memory[:6]])
    
    if audit:
        lines.append(f"\nAuditoria: {len(audit)} acciones")
    
    lines.append("\nSistema operativo.")
    return "\n".join(lines)


def do_daily_report():
    print(f"[DailyReport] Generando informe - {datetime.now().strftime('%H:%M')}")
    
    # Generate HTML
    html = generate_html_report()
    today = datetime.now().strftime("%Y-%m-%d")
    html_path = os.path.join(REPORT_DIR, f"report_{today}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[DailyReport] HTML: {html_path}")
    
    # Generate text summary for Telegram
    text_report = generate_text_report()
    send_telegram(text_report)
    
    # Send HTML as document
    send_doc(html_path, f"Daily Report {today}")
    
    # Save in Qdrant
    try:
        subprocess.run([
            sys.executable, QDR,
            "--save", text_report,
            "--keywords", f"informe,diario,{today}",
            "--project", "informes_diarios"
        ], capture_output=True, timeout=20)
    except Exception:
        pass
        
    # Archivador diario de chat logs en Qdrant
    try:
        archiver_script = os.path.join(TOOLS_DIR, "daily_qdrant_archiver.py")
        subprocess.run([sys.executable, archiver_script], capture_output=True, timeout=30)
        print("[DailyReport] Conversaciones diarias archivadas en Qdrant.")
    except Exception as e:
        print(f"[DailyReport] Error ejecutando archivador diario: {e}")
    
    print("[DailyReport] Completado.")


def run_daemon():
    """Ejecuta reporte diario inmediato y finaliza (One-Shot)."""
    print("[DailyReport] Ejecutando reporte en modo One-Shot...")
    do_daily_report()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        do_daily_report()
    else:
        run_daemon()
