"""
live_dashboard.py — Dashboard en Vivo con WebSocket
=====================================================
Servidor web local que expone un dashboard moderno con datos
en tiempo real del ecosistema Chask Swarm.

Características:
- WebSocket para actualizaciones en tiempo real
- Estado de daemons, memoria, notificaciones, skills
- Métricas del MCP Server
- Log de actividad en vivo

Uso:
  python live_dashboard.py              (arranca en localhost:7860)
  python live_dashboard.py --port 8080  (puerto custom)
"""
import asyncio
import json
import os
import sys
import io
import subprocess
import threading
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADVANCED_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 7860

sys.path.insert(0, ADVANCED_DIR)


def _collect_metrics() -> dict:
    """Recopila todas las métricas del ecosistema."""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "memory": {},
        "daemons": {},
        "notifications": {},
        "mcp": {},
        "modes": {},
        "skills": {}
    }

    # Daemons
    try:
        result = subprocess.run(
            'tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV',
            capture_output=True, text=True, shell=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        lines = [l for l in result.stdout.strip().split('\n') if 'pythonw' in l.lower()]
        metrics["daemons"]["pythonw_count"] = len(lines)
        metrics["daemons"]["processes"] = lines[:5]
    except Exception:
        metrics["daemons"]["pythonw_count"] = 0

    # Docker
    try:
        result = subprocess.run(
            'docker ps --format "{{.Names}}: {{.Status}}"',
            capture_output=True, text=True, shell=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        metrics["daemons"]["docker"] = result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception:
        metrics["daemons"]["docker"] = []

    # Memoria evolutiva
    try:
        import evolutionary_memory
        metrics["memory"] = evolutionary_memory.get_stats()
    except Exception:
        metrics["memory"] = {"error": "no disponible"}

    # Notificaciones
    try:
        import notification_manager
        metrics["notifications"] = notification_manager.get_stats()
    except Exception:
        metrics["notifications"] = {"error": "no disponible"}

    # Skills
    try:
        import skill_catalog
        catalog = skill_catalog.load_catalog()
        metrics["skills"]["total"] = len(catalog.get("skills", []))
    except Exception:
        metrics["skills"]["total"] = 0

    # Modos
    try:
        import mode_router
        config = mode_router.load_modes()
        modes = config.get("modes", [])
        metrics["modes"]["total"] = len(modes)
        metrics["modes"]["active"] = len([m for m in modes if m.get("active", True)])
        metrics["modes"]["custom"] = len([m for m in modes if m.get("custom", False)])
    except Exception:
        pass

    # Memory.md
    try:
        mem_path = os.path.join(os.path.expanduser("~"), "Desktop", "Enjambre Datos", "memory.md")
        if os.path.exists(mem_path):
            with open(mem_path, "r", encoding="utf-8") as f:
                content = f.read(500)
            metrics["system"]["memory_md"] = content
    except Exception:
        pass

    return metrics


# ── HTML del Dashboard ─────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Enjambre Live Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#0a0a1a;color:#e0e0e0;line-height:1.6}
.top-bar{background:linear-gradient(135deg,#12122a,#1a1a3e);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #2a2a4e}
.top-bar h1{font-size:1.4rem;font-weight:900;background:linear-gradient(135deg,#00f5d4,#7b61ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.status{display:flex;align-items:center;gap:8px;font-size:.85rem}
.dot{width:10px;height:10px;border-radius:50%;animation:pulse 2s infinite}
.dot.on{background:#00f5d4}
.dot.off{background:#f72585}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.container{max-width:1400px;margin:0 auto;padding:24px}
.grid{display:grid;gap:20px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.card{background:linear-gradient(135deg,#12122a,#1a1a3e);border:1px solid #2a2a4e;border-radius:16px;padding:20px;transition:transform .2s}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(0,245,212,.06)}
.card h3{font-size:.95rem;color:#00f5d4;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px;font-weight:700}
.metric{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #1a1a3e}
.metric:last-child{border:none}
.metric .label{color:#888;font-size:.85rem}
.metric .value{font-size:1.1rem;font-weight:700;color:#fff}
.metric .value.green{color:#00f5d4}
.metric .value.yellow{color:#ffd60a}
.metric .value.red{color:#f72585}
.log-box{background:#0a0a1a;border:1px solid #1a1a3e;border-radius:8px;padding:12px;height:200px;overflow-y:auto;font-family:monospace;font-size:.8rem;color:#888}
.log-entry{padding:2px 0;border-bottom:1px solid #0f0f2a}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:600}
.badge.on{background:#00f5d420;color:#00f5d4}
.badge.off{background:#f7258520;color:#f72585}
.progress-bar{width:100%;height:6px;background:#1a1a3e;border-radius:3px;overflow:hidden;margin-top:4px}
.progress-fill{height:100%;border-radius:3px;transition:width 1s ease}
.wide{grid-column:span 2}
@media(max-width:768px){.wide{grid-column:span 1}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="top-bar">
  <h1>🧠 ENJAMBRE — Live Dashboard</h1>
  <div class="status">
    <div class="dot on" id="ws-dot"></div>
    <span id="ws-status">Conectando...</span>
    <span style="margin-left:16px;color:#444" id="last-update"></span>
  </div>
</div>
<div class="container">
<div class="grid" id="dashboard">

  <div class="card">
    <h3>🔧 Daemons</h3>
    <div class="metric"><span class="label">pythonw procesos</span><span class="value" id="m-pythonw">-</span></div>
    <div class="metric"><span class="label">Docker containers</span><span class="value" id="m-docker">-</span></div>
  </div>

  <div class="card">
    <h3>🧠 Memoria Evolutiva</h3>
    <div class="metric"><span class="label">Total memorias</span><span class="value" id="m-mem-total">-</span></div>
    <div class="metric"><span class="label">Activas</span><span class="value green" id="m-mem-active">-</span></div>
    <div class="metric"><span class="label">Confianza promedio</span><span class="value" id="m-mem-conf">-</span></div>
    <div class="metric"><span class="label">Alta confianza</span><span class="value green" id="m-mem-high">-</span></div>
    <div class="metric"><span class="label">Baja confianza</span><span class="value yellow" id="m-mem-low">-</span></div>
  </div>

  <div class="card">
    <h3>🔔 Notificaciones</h3>
    <div class="metric"><span class="label">En cola</span><span class="value" id="m-notif-queue">-</span></div>
    <div class="metric"><span class="label">Última hora</span><span class="value" id="m-notif-hour">-</span></div>
    <div class="metric"><span class="label">Últimas 24h</span><span class="value" id="m-notif-day">-</span></div>
    <div class="metric"><span class="label">DND activo</span><span class="value" id="m-notif-dnd">-</span></div>
  </div>

  <div class="card">
    <h3>🎭 Modos de Agente</h3>
    <div class="metric"><span class="label">Total</span><span class="value" id="m-modes-total">-</span></div>
    <div class="metric"><span class="label">Activos</span><span class="value green" id="m-modes-active">-</span></div>
    <div class="metric"><span class="label">Custom</span><span class="value" id="m-modes-custom">-</span></div>
  </div>

  <div class="card">
    <h3>🛠️ MCP Server</h3>
    <div class="metric"><span class="label">Tools</span><span class="value green" id="m-mcp-tools">24</span></div>
    <div class="metric"><span class="label">Resources</span><span class="value" id="m-mcp-res">5</span></div>
    <div class="metric"><span class="label">Prompts</span><span class="value" id="m-mcp-prompts">3</span></div>
    <div class="metric"><span class="label">Skills generados</span><span class="value" id="m-skills">-</span></div>
  </div>

  <div class="card wide">
    <h3>📋 Contexto Actual (memory.md)</h3>
    <div class="log-box" id="memory-md" style="height:150px;white-space:pre-wrap">Cargando...</div>
  </div>

</div>
</div>

<script>
let ws;
function connect() {
  ws = new WebSocket('ws://localhost:WSPORT');
  ws.onopen = () => {
    document.getElementById('ws-dot').className = 'dot on';
    document.getElementById('ws-status').textContent = 'En vivo';
  };
  ws.onclose = () => {
    document.getElementById('ws-dot').className = 'dot off';
    document.getElementById('ws-status').textContent = 'Desconectado';
    setTimeout(connect, 3000);
  };
  ws.onmessage = (e) => {
    const d = JSON.parse(e.data);
    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
    // Daemons
    document.getElementById('m-pythonw').textContent = d.daemons?.pythonw_count ?? '-';
    document.getElementById('m-docker').textContent = (d.daemons?.docker?.length ?? 0);
    // Memory
    document.getElementById('m-mem-total').textContent = d.memory?.total ?? '-';
    document.getElementById('m-mem-active').textContent = d.memory?.active ?? '-';
    document.getElementById('m-mem-conf').textContent = d.memory?.avg_confidence ?? '-';
    document.getElementById('m-mem-high').textContent = d.memory?.high_confidence ?? '-';
    document.getElementById('m-mem-low').textContent = d.memory?.low_confidence ?? '-';
    // Notifications
    document.getElementById('m-notif-queue').textContent = d.notifications?.pending_in_queue ?? '-';
    document.getElementById('m-notif-hour').textContent = d.notifications?.sent_last_hour ?? '-';
    document.getElementById('m-notif-day').textContent = d.notifications?.sent_last_24h ?? '-';
    document.getElementById('m-notif-dnd').textContent = d.notifications?.dnd_active ? 'Sí' : 'No';
    // Modes
    document.getElementById('m-modes-total').textContent = d.modes?.total ?? '-';
    document.getElementById('m-modes-active').textContent = d.modes?.active ?? '-';
    document.getElementById('m-modes-custom').textContent = d.modes?.custom ?? '-';
    // Skills
    document.getElementById('m-skills').textContent = d.skills?.total ?? '-';
    // Memory.md
    if (d.system?.memory_md) document.getElementById('memory-md').textContent = d.system.memory_md;
  };
}
connect();
</script>
</body>
</html>"""


class DashboardHandler(SimpleHTTPRequestHandler):
    """Sirve el dashboard HTML."""
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html = DASHBOARD_HTML.replace('WSPORT', str(PORT + 1))
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/api/metrics':
            metrics = _collect_metrics()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(metrics, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP


async def ws_server(port: int):
    """WebSocket server que envía métricas cada 5 segundos."""
    try:
        import websockets
    except ImportError:
        print("[Dashboard] Instalando websockets...")
        subprocess.run([sys.executable, "-m", "pip", "install", "websockets"], capture_output=True)
        import websockets

    connected = set()

    async def handler(websocket):
        connected.add(websocket)
        try:
            async for _ in websocket:
                pass
        finally:
            connected.discard(websocket)

    async def broadcaster():
        while True:
            if connected:
                metrics = _collect_metrics()
                data = json.dumps(metrics, ensure_ascii=False)
                await asyncio.gather(
                    *[ws.send(data) for ws in connected],
                    return_exceptions=True
                )
            await asyncio.sleep(5)

    async with websockets.serve(handler, "localhost", port):
        print(f"[Dashboard] WebSocket en ws://localhost:{port}")
        await broadcaster()


def run_http(port: int):
    """Arranca el servidor HTTP en un thread."""
    server = HTTPServer(("localhost", port), DashboardHandler)
    print(f"[Dashboard] HTTP en http://localhost:{port}")
    server.serve_forever()


def main():
    port = PORT
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    # HTTP en thread
    http_thread = threading.Thread(target=run_http, args=(port,), daemon=True)
    http_thread.start()

    # WebSocket en asyncio
    print(f"\n  Dashboard: http://localhost:{port}")
    print(f"  WebSocket: ws://localhost:{port + 1}")
    print(f"  Ctrl+C para detener\n")

    asyncio.run(ws_server(port + 1))


if __name__ == "__main__":
    main()
