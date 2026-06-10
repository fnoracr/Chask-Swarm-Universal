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
QUEUE_FILE  = os.path.join(BASE_DIR, "Advanced_Tools", "Colas_Mensajes", "input_queue.json")

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

# ── HTML de la interfaz ─────────
HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Chask Swarm — Panel Local</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
  :root{--bg:#121212;--card:#1e1e1e;--primary:#FF6600;--text:#e0e0e0;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;}
  header{background:var(--card);padding:14px 24px;border-bottom:2px solid var(--primary);display:flex;align-items:center;gap:14px;}
  header h1{font-size:22px;color:#fff;} header h1 span{color:var(--primary);}
  .status{font-size:12px;color:#aaa;} .dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e;margin-right:6px;animation:pulse 2s infinite;}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
  .main{display:flex;flex:1;overflow:hidden;}
  .sidebar{width:260px;background:var(--card);border-right:1px solid #333;padding:16px;overflow-y:auto;display:flex;flex-direction:column;gap:12px;}
  .sidebar h3{color:var(--primary);font-size:13px;letter-spacing:1px;text-transform:uppercase;border-bottom:1px solid #333;padding-bottom:6px;}
  .memory-box{background:#111;border-radius:8px;padding:10px;font-size:12px;color:#aaa;white-space:pre-wrap;max-height:200px;overflow-y:auto;}
  .chat{flex:1;display:flex;flex-direction:column;padding:20px;gap:12px;overflow-y:auto;} 
  .msg{max-width:75%;padding:12px 16px;border-radius:12px;line-height:1.6;font-size:15px;}
  .msg.user{background:var(--primary);color:#fff;align-self:flex-end;border-bottom-right-radius:2px;}
  .msg.ai{background:var(--card);color:var(--text);align-self:flex-start;border-bottom-left-radius:2px;border:1px solid #333;}
  .msg.system{background:#1a1a2e;color:#8888ff;font-size:12px;font-style:italic;align-self:center;}
  .input-area{background:var(--card);border-top:1px solid #333;padding:16px 20px;display:flex;gap:10px;}
  textarea{flex:1;background:#111;border:1px solid #444;border-radius:8px;padding:10px 14px;color:var(--text);font-family:'Outfit',sans-serif;font-size:15px;resize:none;height:48px;outline:none;}
  textarea:focus{border-color:var(--primary);}
  button{background:var(--primary);color:#fff;border:none;border-radius:8px;padding:0 20px;font-weight:700;cursor:pointer;font-size:15px;}
  button:hover{background:#e65c00;}
</style>
</head>
<body>
<header><h1>Chask Swarm <span>Dashboard</span></h1><div class="status"><span class="dot"></span>Online</div></header>
<div class="main">
  <div class="sidebar">
    <h3>Cerebro Swarm</h3><div id="status-box" class="memory-box">Cargando...</div>
    <h3>Memoria Viva</h3><div id="mem-box" class="memory-box">...</div>
  </div>
  <div class="chat" id="chat">
    <div class="msg ai">{{GREETING}}</div>
  </div>
</div>
<div class="input-area">
  <textarea id="inp" placeholder="Escribe un mensaje o comando técnico..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
  <button onclick="send()">ENVIAR</button>
</div>
<script>
const chat = document.getElementById('chat');
function addMsg(txt, type){
  const div = document.createElement('div');
  div.className = 'msg ' + type;
  div.textContent = txt;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
async function send(){
  const inp = document.getElementById('inp');
  const text = inp.value.trim();
  if(!text) return;
  inp.value = '';
  addMsg(text, 'user');
  addMsg('Procesando...', 'system');
  const r = await fetch('/send', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: text})});
  const data = await r.json();
  if(data.engine === 'antigravity'){
    chat.lastChild.textContent = 'Chask Swarm está trabajando en ello...';
  } else {
    chat.lastChild.remove();
    if(data.response) addMsg(data.response, 'ai');
  }
}
const evtSource = new EventSource('/stream');
evtSource.onmessage = e => {
  const data = JSON.parse(e.data);
  if(data.response) {
    if(chat.lastChild && chat.lastChild.classList.contains('system')) chat.lastChild.remove();
    addMsg(data.response, 'ai');
  }
};
async function loadMemory(){
  try {
    const r = await fetch('/memory');
    const data = await r.json();
    document.getElementById('mem-box').textContent = data.content;
    document.getElementById('status-box').textContent = data.status;
  } catch(e) {}
}
loadMemory(); setInterval(loadMemory, 10000);
document.getElementById('inp').focus();
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
    queue_path = os.path.join(BASE_DIR, "Colas_Mensajes", "pending_messages.json")
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
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, encoding="utf-8") as f: content = f.read()
    else: content = ""
    return jsonify({"content": content[:800], "status": "Online"})

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
