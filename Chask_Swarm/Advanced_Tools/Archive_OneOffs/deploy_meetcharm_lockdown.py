import paramiko, sys, io, json, secrets as sec
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PASSWORD = 'N0r4Z0e?12@3'
HOST = '31.97.152.240'
SWARM_API_KEY = '5b1d20a71ca8104db92c26443f03a74317463ad04e189111d81cee6ca95ace6a'

# Nuevo main.py del VPS con bloqueo completo de acceso directo
NEW_MAIN_PY = '''import os, json, sqlite3, secrets, datetime
from pathlib import Path
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Meet Charm API", version="2.0.0")
app.mount("/static", StaticFiles(directory="/opt/MeetCharm/static"), name="static")

# ── Sesiones DB (token → username, expiry) ─────────────────────────
SESSIONS_DB = "/opt/chask/mc_sessions.db"
Path("/opt/chask").mkdir(parents=True, exist_ok=True)

def _db():
    conn = sqlite3.connect(SESSIONS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS mc_sessions (
        token      TEXT PRIMARY KEY,
        username   TEXT NOT NULL,
        disp_name  TEXT NOT NULL,
        room_id    TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )""")
    conn.commit()
    return conn

def _valid_session(token: str) -> dict | None:
    if not token: return None
    conn = _db()
    row = conn.execute(
        "SELECT * FROM mc_sessions WHERE token=? AND expires_at > datetime(\\'now\\')",
        (token,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

# ── Clave API del enjambre (autenticación swarm → VPS) ─────────────
SWARM_API_KEY = os.environ.get("SWARM_API_KEY", "''' + SWARM_API_KEY + '''")

def _check_swarm_key(request: Request):
    key = request.headers.get("X-Swarm-Key", "")
    if key != SWARM_API_KEY:
        raise HTTPException(403, "Clave de enjambre no válida")

# ── Página de acceso denegado ───────────────────────────────────────
ACCESS_DENIED_HTML = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Meet Charm — Acceso restringido</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0d0d14;font-family:system-ui,sans-serif;color:#fff}
.card{text-align:center;padding:48px;background:rgba(123,47,247,0.06);border:1px solid rgba(123,47,247,0.25);border-radius:20px;max-width:420px;width:90%}
.icon{font-size:56px;margin-bottom:20px}h1{font-size:22px;font-weight:800;margin-bottom:12px}
p{color:rgba(255,255,255,0.5);font-size:13px;line-height:1.6}</style></head>
<body><div class="card"><div class="icon">🔐</div>
<h1>Meet Charm</h1><h2 style="color:#7b2ff7;margin-bottom:16px">Acceso restringido</h2>
<p>Solo puedes acceder a Meet Charm desde el panel web de tu enjambre Chask Swarm.<br><br>
Si formas parte de un enjambre, abre el panel en <strong>localhost:7860</strong> y accede desde la pestaña <strong>Meet Charm</strong>.</p>
</div></body></html>"""

# ── CORS ────────────────────────────────────────────────────────────
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        r = Response()
        r.headers["Access-Control-Allow-Origin"]  = "*"
        r.headers["Access-Control-Allow-Methods"] = "*"
        r.headers["Access-Control-Allow-Headers"] = "*"
        return r
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# ── Raíz — solo con token válido ────────────────────────────────────
@app.get("/")
async def root(request: Request):
    token = request.query_params.get("token", "")
    session = _valid_session(token)
    if not session:
        return HTMLResponse(ACCESS_DENIED_HTML, status_code=403)
    return FileResponse("/opt/MeetCharm/static/index.html")

# ── Registro de sesión desde el enjambre ───────────────────────────
@app.post("/api/session/register")
async def register_session(request: Request):
    _check_swarm_key(request)
    data      = await request.json()
    token     = data.get("token", "")
    username  = data.get("username", "")
    disp_name = data.get("disp_name", username)
    room_id   = data.get("room_id", "")
    expires   = data.get("expires_at", "")
    if not all([token, username, room_id, expires]):
        raise HTTPException(400, "Datos incompletos")
    conn = _db()
    conn.execute(
        "INSERT OR REPLACE INTO mc_sessions (token, username, disp_name, room_id, expires_at) VALUES (?,?,?,?,?)",
        (token, username, disp_name, room_id, expires)
    )
    conn.commit(); conn.close()
    return JSONResponse({"success": True})

# ── Validar token (para uso del WebSocket) ─────────────────────────
@app.get("/api/session/validate")
async def validate_session(request: Request):
    token = request.query_params.get("token", "")
    session = _valid_session(token)
    if not session:
        raise HTTPException(401, "Token inválido o expirado")
    return JSONResponse({"valid": True, "username": session["username"], "disp_name": session["disp_name"]})

# ══════════════════════════════════════════════════════════════════
#  ROOM MANAGEMENT
# ══════════════════════════════════════════════════════════════════
class Room:
    def __init__(self, room_id, created_by):
        self.room_id = room_id
        self.created_by = created_by
        self.created_at = datetime.datetime.utcnow().isoformat()
        self.connections: Dict[str, WebSocket] = {}
        self.participants: set = set()
        self.current_presenter: str = None

rooms: Dict[str, Room] = {}

@app.post("/api/rooms/enter")
async def enter_room(request: Request):
    token = request.headers.get("X-Session-Token") or request.query_params.get("token", "")
    session = _valid_session(token)
    if not session:
        raise HTTPException(403, "Acceso denegado: sesión no válida")
    room_id = session["room_id"]
    is_new  = room_id not in rooms
    if is_new:
        rooms[room_id] = Room(room_id, session["username"])
        try:
            import urllib.request
            req = urllib.request.Request(f"http://172.17.0.1:8099/launch/{room_id}", method="POST")
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            print(f"[Room] Warning: {e}")
    return {"room_id": room_id, "is_new": is_new, "display_name": session["disp_name"]}

# ══════════════════════════════════════════════════════════════════
#  WEBSOCKET — token obligatorio
# ══════════════════════════════════════════════════════════════════
@app.websocket("/ws/{room_id}/{display_name}")
async def websocket_endpoint(ws: WebSocket, room_id: str, display_name: str):
    token   = ws.query_params.get("token", "")
    session = _valid_session(token)
    if not session:
        await ws.close(code=4403)
        return

    authenticated_name = session["disp_name"]
    if room_id not in rooms:
        rooms[room_id] = Room(room_id, authenticated_name)
    room = rooms[room_id]
    await ws.accept()
    room.connections[authenticated_name] = ws
    room.participants.add(authenticated_name)

    try:
        await ws.send_text(json.dumps({
            "type": "connected", "room_id": room_id,
            "user_id": authenticated_name,
            "participants": list(room.participants),
            "authenticated": True
        }))
        for uid, conn in list(room.connections.items()):
            if uid != authenticated_name:
                try:
                    await conn.send_text(json.dumps({"type": "user_joined", "user_id": authenticated_name}))
                except: pass

        inbox = Path(f"/tmp/MeetCharm-inbox-{room_id}.jsonl")
        try:
            with open(inbox, "a") as f:
                f.write(json.dumps({"ts": datetime.datetime.utcnow().isoformat(), "type": "joined",
                                    "user_id": authenticated_name}) + "\\n")
        except: pass

        while True:
            raw  = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "chat":
                try:
                    with open(inbox, "a") as f:
                        f.write(json.dumps({"ts": datetime.datetime.utcnow().isoformat(),
                                            "type": "chat", "user_id": authenticated_name,
                                            "text": data.get("text", ""),
                                            "authenticated": True}) + "\\n")
                except: pass
                for uid, conn in list(room.connections.items()):
                    if uid != authenticated_name:
                        try:
                            await conn.send_text(json.dumps({"type": "chat", "user_id": authenticated_name,
                                                             "text": data.get("text", ""), "file": data.get("file")}))
                        except: pass

            elif msg_type in ("offer", "answer", "ice"):
                target = data.get("target")
                if target and target in room.connections:
                    try:
                        await room.connections[target].send_text(json.dumps({**data, "from": authenticated_name}))
                    except: pass

            elif msg_type == "presenter_start":
                room.current_presenter = authenticated_name
                for uid, conn in list(room.connections.items()):
                    if uid != authenticated_name:
                        try: await conn.send_text(json.dumps({"type": "presenter_start", "user_id": authenticated_name}))
                        except: pass

            elif msg_type == "presenter_stop":
                if room.current_presenter == authenticated_name: room.current_presenter = None
                for uid, conn in list(room.connections.items()):
                    if uid != authenticated_name:
                        try: await conn.send_text(json.dumps({"type": "presenter_stop", "user_id": authenticated_name}))
                        except: pass

    except WebSocketDisconnect:
        room.connections.pop(authenticated_name, None)
        room.participants.discard(authenticated_name)
        for uid, conn in list(room.connections.items()):
            try: await conn.send_text(json.dumps({"type": "user_left", "user_id": authenticated_name}))
            except: pass
        try:
            with open(inbox, "a") as f:
                f.write(json.dumps({"ts": datetime.datetime.utcnow().isoformat(),
                                    "type": "left", "user_id": authenticated_name}) + "\\n")
        except: pass

# ══════════════════════════════════════════════════════════════════
#  TRANSCRIPCIÓN
# ══════════════════════════════════════════════════════════════════
try:
    from transcription_module import handle_transcription_ws
    from realtime_transcription import handle_realtime_transcription_ws

    @app.websocket("/ws/transcription/{room_id}")
    async def transcription_ws(ws: WebSocket, room_id: str):
        await handle_transcription_ws(ws, room_id)

    @app.websocket("/ws/realtime_transcription/{room_id}")
    async def realtime_transcription_ws(ws: WebSocket, room_id: str):
        await handle_realtime_transcription_ws(ws, room_id)
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════════
#  SCREENSHOTS
# ══════════════════════════════════════════════════════════════════
import base64 as _b64
SCREENSHOTS_DIR = "/opt/MeetCharm/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

@app.post("/api/screenshot/{room_id}")
async def save_screenshot(room_id: str, request: Request):
    data      = await request.json()
    image_b64 = data.get("image", "")
    source    = data.get("source", "unknown")
    if "," in image_b64: image_b64 = image_b64.split(",", 1)[1]
    ts       = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{room_id}_{source}_{ts}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(_b64.b64decode(image_b64))
    return {"success": True, "filename": filename}
'''

def handler(title, instructions, fields): return [PASSWORD]*len(fields)
t = paramiko.Transport((HOST, 22))
t.connect(); t.auth_interactive('root', handler)
ssh = paramiko.SSHClient(); ssh._transport = t

# 1. Subir el nuevo main.py
print("=== [1/4] Subiendo nuevo main.py al VPS ===")
stdin, stdout, stderr = ssh.exec_command("tee /root/proyecto_norameet/backend/main.py")
stdin.write(NEW_MAIN_PY)
stdin.channel.shutdown_write()
stdout.read()
print("main.py subido")

# 2. Actualizar norameet_config.json con la swarm_api_key
print("\n=== [2/4] Actualizando swarm_api_key en VPS ===")
new_cfg_cmd = f"""python3 -c "
import json
from pathlib import Path
p = Path('/opt/chask/norameet_config.json')
cfg = json.loads(p.read_text()) if p.exists() else {{}}
cfg['swarm_api_key'] = '{SWARM_API_KEY}'
p.write_text(json.dumps(cfg, indent=2))
print('OK')
" """
stdin, stdout, stderr = ssh.exec_command(new_cfg_cmd)
print(stdout.read().decode(errors='replace').strip())

# 3. Verificar sintaxis
print("\n=== [3/4] Verificando sintaxis ===")
stdin, stdout, stderr = ssh.exec_command("python3 -m py_compile /root/proyecto_norameet/backend/main.py && echo 'SINTAXIS OK'")
print(stdout.read().decode(errors='replace').strip())

# 4. Reiniciar el container Docker de MeetCharm
print("\n=== [4/4] Reiniciando container MeetCharm ===")
stdin, stdout, stderr = ssh.exec_command("cd /root/proyecto_norameet && docker-compose restart MeetCharm 2>&1 | tail -5")
print(stdout.read().decode(errors='replace').strip())

t.close()
print("\n=== VPS ACTUALIZADO ===")
