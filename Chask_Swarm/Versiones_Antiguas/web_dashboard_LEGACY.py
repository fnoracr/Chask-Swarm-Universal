"""
web_dashboard.py — Interfaz web local de Chask Swarm
Accesible en http://localhost:7860
"""
import os, json, threading, time, webbrowser, sys, subprocess
from datetime import datetime
from flask import Flask, request, jsonify, Response

# Nota: El contexto (soul, memory, etc) se inyecta ahora via boot_injection.py 
# para mantener este codigo limpio y funcional.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "telegram_config.json")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.md")
QUEUE_FILE  = os.path.join(BASE_DIR, "Advanced_Tools", "input_queue.json")

# Router de IAs gratuitas
sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools"))
try:
    import llm_router
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False

def get_user_name():
    """Extrae el nombre del administrador desde soul.md de forma dinámica."""
    try:
        soul_path = os.path.join(BASE_DIR, "soul.md")
        if os.path.exists(soul_path):
            with open(soul_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "Administrador:" in line or "ADMINISTRADOR:" in line:
                        # Limpiar etiquetas y asteriscos
                        name = line.split(":")[-1].strip().replace("*", "").replace(".", "")
                        if name:
                            return name.split()[0] # Tomar solo el nombre de pila
    except: pass
    return ""

app = Flask(__name__)

# Registrar API de configuracion
try:
    from dashboard_config_api import config_api
    app.register_blueprint(config_api)
except Exception as e:
    print(f"[Dashboard] Config API no disponible: {e}")

# ── HTML de la interfaz ─────────
HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chask Swarm — Enjambre Command Center</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
  :root{--bg:#0a0a1a;--card:rgba(255,255,255,0.04);--card-border:rgba(255,255,255,0.08);--primary:#7b2ff7;--accent:#00d4ff;--orange:#FF6600;--text:#e0e0e0;--green:#00ff88;--yellow:#ffaa00;--red:#ff4444;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden;}

  header{background:rgba(20,20,40,0.95);backdrop-filter:blur(12px);padding:12px 24px;border-bottom:1px solid var(--card-border);display:flex;align-items:center;gap:14px;}
  header h1{font-size:20px;color:#fff;font-weight:600;} header h1 span{background:linear-gradient(135deg,var(--accent),var(--primary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .hdr-right{margin-left:auto;display:flex;align-items:center;gap:16px;}
  .status{font-size:12px;color:#aaa;display:flex;align-items:center;gap:6px;}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
  .version{font-size:11px;color:#555;letter-spacing:1px;}

  .main{display:flex;flex:1;overflow:hidden;}

  .sidebar{width:300px;background:rgba(15,15,30,0.95);border-right:1px solid var(--card-border);overflow-y:auto;display:flex;flex-direction:column;padding:0;}
  .sb-section{padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.05);}
  .sb-title{color:var(--accent);font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:600;margin-bottom:10px;}

  .cap-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;}
  .cap{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:8px;font-size:11px;display:flex;flex-direction:column;gap:3px;transition:all .2s;}
  .cap:hover{border-color:var(--accent);background:rgba(0,212,255,0.05);transform:translateY(-1px);}
  .cap-name{font-weight:600;color:#fff;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .cap-status{display:flex;align-items:center;gap:4px;font-size:10px;}
  .cap-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;}
  .cap-dot.on{background:var(--green);}
  .cap-dot.off{background:var(--red);}
  .cap-dot.new{background:var(--accent);box-shadow:0 0 6px var(--accent);}
  .cap-tag{font-size:9px;padding:1px 5px;border-radius:3px;font-weight:600;}
  .tag-core{background:rgba(123,47,247,0.2);color:#bb88ff;border:1px solid rgba(123,47,247,0.3);}
  .tag-new{background:rgba(0,212,255,0.15);color:var(--accent);border:1px solid rgba(0,212,255,0.3);}
  .tag-unique{background:rgba(255,215,0,0.15);color:#ffd700;border:1px solid rgba(255,215,0,0.3);}

  .mem-box{background:rgba(0,0,0,0.3);border-radius:8px;padding:10px;font-size:11px;color:#888;white-space:pre-wrap;max-height:140px;overflow-y:auto;font-family:'Courier New',monospace;line-height:1.5;}

  .stats-row{display:flex;gap:8px;flex-wrap:wrap;}
  .stat{flex:1;min-width:80px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:8px;text-align:center;}
  .stat-val{font-size:18px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--primary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .stat-label{font-size:9px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-top:2px;}

  .chat{flex:1;display:flex;flex-direction:column;padding:20px;gap:12px;overflow-y:auto;background:radial-gradient(ellipse at center,rgba(123,47,247,0.03) 0%,transparent 70%);}
  .msg{max-width:70%;padding:12px 16px;border-radius:14px;line-height:1.6;font-size:14px;animation:fadeIn .3s;}
  @keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
  .msg.user{background:linear-gradient(135deg,var(--primary),#5a1fd0);color:#fff;align-self:flex-end;border-bottom-right-radius:4px;}
  .msg.ai{background:rgba(255,255,255,0.05);color:var(--text);align-self:flex-start;border-bottom-left-radius:4px;border:1px solid var(--card-border);}
  .msg.system{background:rgba(0,212,255,0.08);color:var(--accent);font-size:12px;font-style:italic;align-self:center;border:1px solid rgba(0,212,255,0.15);}

  .input-area{background:rgba(15,15,30,0.95);backdrop-filter:blur(12px);border-top:1px solid var(--card-border);padding:14px 20px;display:flex;gap:10px;}
  textarea{flex:1;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:12px 16px;color:var(--text);font-family:'Outfit',sans-serif;font-size:14px;resize:none;height:48px;outline:none;transition:border-color .2s;}
  textarea:focus{border-color:var(--accent);box-shadow:0 0 0 2px rgba(0,212,255,0.1);}
  button{background:linear-gradient(135deg,var(--primary),#5a1fd0);color:#fff;border:none;border-radius:10px;padding:0 24px;font-weight:700;cursor:pointer;font-size:14px;transition:all .2s;}
  button:hover{transform:translateY(-1px);box-shadow:0 4px 15px rgba(123,47,247,0.4);}
</style>
</head>
<body>
<header>
  <h1>Chask <span>Swarm</span></h1>
  <div class="hdr-right">
    <div class="version">ENJAMBRE v2.0</div>
    <div class="status"><span class="dot"></span>Online</div>
  </div>
</header>
<div class="main">
  <div class="sidebar">
    <div class="sb-section">
      <div class="sb-title">Capacidades del Sistema</div>
      <div class="cap-grid">
        <div class="cap"><div class="cap-name">Terminal</div><div class="cap-status"><span class="cap-dot on"></span>Activo <span class="cap-tag tag-core">CORE</span></div></div>
        <div class="cap"><div class="cap-name">Filesystem</div><div class="cap-status"><span class="cap-dot on"></span>Activo <span class="cap-tag tag-core">CORE</span></div></div>
        <div class="cap"><div class="cap-name">Qdrant Memory</div><div class="cap-status"><span class="cap-dot on"></span>Activo <span class="cap-tag tag-unique">UNICA</span></div></div>
        <div class="cap"><div class="cap-name">LLM Router</div><div class="cap-status"><span class="cap-dot on"></span>Pool IA <span class="cap-tag tag-unique">UNICA</span></div></div>
        <div class="cap"><div class="cap-name">Telegram</div><div class="cap-status"><span class="cap-dot on"></span>24/7 <span class="cap-tag tag-unique">UNICA</span></div></div>
        <div class="cap"><div class="cap-name">Watchdog</div><div class="cap-status"><span class="cap-dot on"></span>Auto-heal <span class="cap-tag tag-unique">UNICA</span></div></div>
        <div class="cap"><div class="cap-name">Stealth Inject</div><div class="cap-status"><span class="cap-dot on"></span>V8.0 <span class="cap-tag tag-unique">UNICA</span></div></div>
        <div class="cap"><div class="cap-name">Browser Pool</div><div class="cap-status"><span class="cap-dot new"></span>51ms <span class="cap-tag tag-new">NUEVO</span></div></div>
        <div class="cap"><div class="cap-name">Web RAG</div><div class="cap-status"><span class="cap-dot new"></span>Crawl4AI <span class="cap-tag tag-new">NUEVO</span></div></div>
        <div class="cap"><div class="cap-name">Scheduler</div><div class="cap-status"><span class="cap-dot new"></span>Cron IA <span class="cap-tag tag-new">NUEVO</span></div></div>
        <div class="cap"><div class="cap-name">Graph Memory</div><div class="cap-status"><span class="cap-dot new"></span>NetworkX <span class="cap-tag tag-new">NUEVO</span></div></div>
        <div class="cap"><div class="cap-name">Anti-Drift</div><div class="cap-status"><span class="cap-dot new"></span>Embeddings <span class="cap-tag tag-new">NUEVO</span></div></div>
        <div class="cap"><div class="cap-name">Vision</div><div class="cap-status"><span class="cap-dot new"></span>OCR+LLM <span class="cap-tag tag-new">NUEVO</span></div></div>
        <div class="cap"><div class="cap-name">Orchestrator</div><div class="cap-status"><span class="cap-dot new"></span>Multi-IA <span class="cap-tag tag-new">NUEVO</span></div></div>
      </div>
    </div>
    <div class="sb-section">
      <div class="sb-title">Estadisticas</div>
      <div class="stats-row">
        <div class="stat"><div class="stat-val">14</div><div class="stat-label">Capacidades</div></div>
        <div class="stat"><div class="stat-val" id="st-nodes">-</div><div class="stat-label">Nodos Grafo</div></div>
        <div class="stat"><div class="stat-val" id="st-qdrant">-</div><div class="stat-label">Vectores</div></div>
      </div>
    </div>
    <div class="sb-section">
      <div class="sb-title">Memoria Viva</div>
      <div id="mem-box" class="mem-box">Cargando...</div>
    </div>
  </div>
  <div class="chat" id="chat">
    <div class="msg ai">{{GREETING}}</div>
  </div>
</div>
<div class="input-area">
  <textarea id="inp" placeholder="Escribe un mensaje o comando..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
  <button onclick="send()">ENVIAR</button>
</div>
<script>
const chat=document.getElementById('chat');
function addMsg(t,c){const d=document.createElement('div');d.className='msg '+c;d.textContent=t;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
async function send(){const i=document.getElementById('inp'),t=i.value.trim();if(!t)return;i.value='';addMsg(t,'user');addMsg('Procesando...','system');const r=await fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t})});const d=await r.json();if(d.engine==='antigravity'){chat.lastChild.textContent='Enjambre esta trabajando en ello...';}else{chat.lastChild.remove();if(d.response)addMsg(d.response,'ai');}}
const es=new EventSource('/stream');es.onmessage=e=>{const d=JSON.parse(e.data);if(d.response){if(chat.lastChild&&chat.lastChild.classList.contains('system'))chat.lastChild.remove();addMsg(d.response,'ai');}};
async function loadStatus(){try{const r=await fetch('/memory');const d=await r.json();document.getElementById('mem-box').textContent=d.content||'Sin datos';if(d.graph_nodes!==undefined)document.getElementById('st-nodes').textContent=d.graph_nodes;if(d.qdrant_points!==undefined)document.getElementById('st-qdrant').textContent=d.qdrant_points;}catch(e){}}
loadStatus();setInterval(loadStatus,10000);document.getElementById('inp').focus();
</script>
</body>
</html>"""

@app.route("/")
def index():
    user_name = get_user_name()
    greeting = f"Hola {user_name}" if user_name else "Hola"
    dynamic_html = HTML.replace("{{GREETING}}", f"{greeting} ¿En qué puedo ayudarte?")
    return dynamic_html

try:
    import chask_stealth_injector as nsi
except ImportError:
    nsi = None

def inject_to_ide(message: str, source: str = "web"):
    """Inyecta en el IDE usando el motor Stealth V7.5."""
    if not nsi:
        return False
    formatted = f"[ENJAMBRE: {source.upper()}] {message}"
    success, _ = nsi.inject_to_antigravity(formatted)
    return success


def add_to_queue(message: str, source: str = "web"):
    queue_path = os.path.join(BASE_DIR, "pending_messages.json")
    try:
        data = []
        if os.path.exists(queue_path):
            with open(queue_path, "r", encoding="utf-8") as f: data = json.load(f)
        
        if inject_to_ide(message, source):
            status = "injected"
        else:
            status = "pending"
            
        formatted_text = f"[WEB {time.strftime('%H:%M:%S')}] {message}"
        data.append({"id": f"{time.strftime('%Y%m%d_%H%M%S')}_{source}", "ts": time.strftime('%Y-%m-%dT%H:%M:%S'), "source": source, "text": formatted_text, "thinking_mid": None, "status": status})
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Queue] Error: {e}"); return False

@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json(); message = data.get("message", "").strip()
    if not message: return jsonify({"error": "Mensaje vacío"}), 400
    
    if ROUTER_AVAILABLE:
        try:
            # 1. Comprobar complejidad con la config real
            cfg = llm_router.load_config()
            score, reason = llm_router.complexity_score(message, cfg)
            if score >= 60:
                if add_to_queue(message):
                    return jsonify({"response": "", "engine": "antigravity"})

            # 2. Si es sencillo, pool gratuito
            result = llm_router.route(message, force_free=True)
            resp = result.get("response", "")
            if resp and "__escalate__" not in resp and "__escalade__" not in resp:
                return jsonify({"response": resp, "engine": result.get("engine")})
        except Exception as e:
            print(f"[Dashboard] Error en router: {e}")
        
    if add_to_queue(message): return jsonify({"response": "", "engine": "antigravity"})
    return jsonify({"error": "Error en colas"}), 500

@app.route("/memory")
def get_memory():
    content = ""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, encoding="utf-8") as f: content = f.read()

    # Stats del grafo
    graph_nodes = 0
    try:
        from chask_graph_memory import GraphMemory
        gm = GraphMemory()
        graph_nodes = gm.stats()["nodes"]
    except: pass

    # Stats de Qdrant
    qdrant_points = 0
    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(host="localhost", port=6333, timeout=3)
        for col in qc.get_collections().collections:
            info = qc.get_collection(col.name)
            qdrant_points += info.points_count
    except: pass

    return jsonify({
        "content": content[:800],
        "status": "Enjambre v2.0 Online",
        "graph_nodes": graph_nodes,
        "qdrant_points": qdrant_points
    })

response_queue = []
@app.route("/stream")
def stream():
    def event_gen():
        last = 0
        while True:
            if len(response_queue) > last:
                for item in response_queue[last:]:
                    yield f"data: {json.dumps({'response': item})}\n\n"
                last = len(response_queue)
            time.sleep(1)
    return Response(event_gen(), mimetype="text/event-stream")

@app.route("/web_send", methods=["POST"])
def web_send_response():
    data = request.get_json(); msg = data.get("message", "")
    if msg: response_queue.append(msg)
    return jsonify({"ok": True})

if __name__ == "__main__":
    # Abrir el dashboard automáticamente en el navegador
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:7860")).start()
    app.run(host="127.0.0.1", port=7860, debug=False, threaded=True)
