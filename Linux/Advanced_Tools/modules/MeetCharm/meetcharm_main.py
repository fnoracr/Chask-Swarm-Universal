import os, json, sqlite3, hashlib, secrets, threading, datetime
from pathlib import Path
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import asyncio

app = FastAPI(title="Meet [Nombre_IA] API", version="2.0.0")
app.mount("/static", StaticFiles(directory="/opt/Meet[Nombre_IA]/static"), name="static")

# ── Base de datos ──────────────────────────────────────────────────
DB_PATH = Path("/opt/chask/meetcharm_users.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            full_name   TEXT    NOT NULL,
            node_id     TEXT    DEFAULT '',
            swarm_ok    INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now')),
            active      INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token       TEXT    PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            username    TEXT    NOT NULL,
            full_name   TEXT    NOT NULL,
            expires_at  TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    # Insertar Administrador como primer usuario
    pw = hashlib.sha256(("N0r4Z0e?*12" + "chaskswarm").encode()).hexdigest()
    c.execute("""
        INSERT OR IGNORE INTO users (username, email, password, full_name, node_id, swarm_ok)
        VALUES (?, ?, ?, ?, ?, 1)
    """, ("fnoracr", "fnoracr@gmail.com", pw, "Administrador Enjambre", "terminus"))
    conn.commit()
    conn.close()
    print("[DB] Base de datos Meet [Nombre_IA] inicializada")

init_db()

# ── Auth helpers ───────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256((password + "chaskswarm").encode()).hexdigest()

def create_session(user_id: int, username: str, full_name: str) -> str:
    token = secrets.token_hex(32)
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=72)).isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (token, user_id, username, full_name, expires_at) VALUES (?,?,?,?,?)",
        (token, user_id, username, full_name, expires)
    )
    conn.commit(); conn.close()
    return token

def validate_session(token: str) -> dict | None:
    if not token:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM sessions WHERE token=? AND expires_at > datetime('now')", (token,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_session_from_request(request: Request) -> dict | None:
    token = request.cookies.get("mc_session") or request.headers.get("X-Session-Token")
    return validate_session(token)

# ── CORS middleware ────────────────────────────────────────────────
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
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

# ── Rutas estáticas ────────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse("/opt/Meet[Nombre_IA]/static/index.html")

# ══════════════════════════════════════════════════════════════════
#  AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@app.post("/api/auth/register")
async def register(request: Request):
    data = await request.json()
    username  = (data.get("username") or "").strip().lower()
    email     = (data.get("email") or "").strip().lower()
    password  = (data.get("password") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    node_id   = (data.get("node_id") or "").strip()

    # Validaciones básicas
    if not all([username, email, password, full_name]):
        raise HTTPException(400, "Todos los campos son obligatorios")
    if len(password) < 8:
        raise HTTPException(400, "La contraseña debe tener al menos 8 caracteres")
    if "@" not in email:
        raise HTTPException(400, "Email no válido")

    # Verificar ChaskSwarm: node_id debe existir
    if not node_id:
        raise HTTPException(400, "Se requiere el ID de enjambre (ChaskSwarm). Cópialo de tu panel local en Configuración → Red Mundial.")

    pw_hash = hash_password(password)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password, full_name, node_id, swarm_ok) VALUES (?,?,?,?,?,1)",
            (username, email, pw_hash, full_name, node_id)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        token = create_session(row["id"], row["username"], row["full_name"])
        conn.close()
        resp = JSONResponse({"success": True, "username": username, "full_name": full_name})
        resp.set_cookie("mc_session", token, max_age=259200, samesite="lax")
        return resp
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            raise HTTPException(409, "El nombre de usuario ya está en uso")
        if "email" in str(e):
            raise HTTPException(409, "El email ya está registrado")
        raise HTTPException(409, "Error de registro")

@app.post("/api/auth/login")
async def login(request: Request):
    data = await request.json()
    username = (data.get("username") or "").strip().lower()
    password = (data.get("password") or "").strip()
    if not username or not password:
        raise HTTPException(400, "Usuario y contraseña requeridos")

    pw_hash = hash_password(password)
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND active=1",
        (username, pw_hash)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(401, "Usuario o contraseña incorrectos")

    token = create_session(row["id"], row["username"], row["full_name"])
    resp = JSONResponse({
        "success": True,
        "username": row["username"],
        "full_name": row["full_name"]
    })
    resp.set_cookie("mc_session", token, max_age=259200, samesite="lax")
    return resp

@app.get("/api/auth/me")
async def me(request: Request):
    session = get_session_from_request(request)
    if not session:
        raise HTTPException(401, "No autenticado")
    return {"username": session["username"], "full_name": session["full_name"]}

@app.post("/api/auth/logout")
async def logout(request: Request):
    token = request.cookies.get("mc_session")
    if token:
        conn = get_db()
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit(); conn.close()
    resp = JSONResponse({"success": True})
    resp.delete_cookie("mc_session")
    return resp

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
    """
    Crear o unirse a una sala. Un solo endpoint.
    Si la sala existe: unirse. Si no: crearla.
    Requiere autenticación.
    """
    session = get_session_from_request(request)
    if not session:
        raise HTTPException(401, "Debes iniciar sesión para usar Meet [Nombre_IA]")

    data = await request.json()
    room_id = (data.get("room_id") or "").strip()
    if not room_id or len(room_id) < 4:
        import secrets as sec
        room_id = sec.token_hex(4)

    is_new = room_id not in rooms
    if is_new:
        rooms[room_id] = Room(room_id, session["username"])
        # Lanzar bot+bridge solo para salas nuevas
        try:
            import urllib.request
            req = urllib.request.Request(f"http://172.17.0.1:8099/launch/{room_id}", method="POST")
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            print(f"[Room] Warning: Could not launch bot+bridge: {e}")

    return {"room_id": room_id, "is_new": is_new, "display_name": session["full_name"]}

# Mantener /api/rooms/create por compatibilidad
@app.post("/api/rooms/create")
async def create_room_legacy(request: Request):
    return await enter_room(request)

# ══════════════════════════════════════════════════════════════════
#  WEBSOCKET (con validación de sesión)
# ══════════════════════════════════════════════════════════════════

@app.websocket("/ws/{room_id}/{display_name}")
async def websocket_endpoint(ws: WebSocket, room_id: str, display_name: str):
    # Extraer token de query params
    token = ws.query_params.get("token", "")
    session = validate_session(token)

    # Si no hay sesión válida, usar display_name como fallback temporal
    # (para compatibilidad con clientes existentes)
    authenticated_name = session["full_name"] if session else display_name

    if room_id not in rooms:
        rooms[room_id] = Room(room_id, authenticated_name)

    room = rooms[room_id]
    await ws.accept()
    room.connections[authenticated_name] = ws
    room.participants.add(authenticated_name)

    try:
        await ws.send_text(json.dumps({
            "type": "connected",
            "room_id": room_id,
            "user_id": authenticated_name,
            "participants": list(room.participants),
            "authenticated": bool(session)
        }))

        # Notificar a los demás
        for uid, conn in list(room.connections.items()):
            if uid != authenticated_name:
                try:
                    await conn.send_text(json.dumps({
                        "type": "user_joined",
                        "user_id": authenticated_name
                    }))
                except Exception:
                    pass

        # Escribir al inbox del bot
        inbox_path = Path(f"/tmp/Meet[Nombre_IA]-inbox-{room_id}.jsonl")
        try:
            with open(inbox_path, "a") as f:
                f.write(json.dumps({
                    "ts": datetime.datetime.utcnow().isoformat(),
                    "type": "joined",
                    "user_id": authenticated_name
                }) + "\n")
        except Exception:
            pass

        # Loop de mensajes
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "chat":
                # Escribir al inbox del bot (con info de autenticación)
                try:
                    with open(inbox_path, "a") as f:
                        f.write(json.dumps({
                            "ts": datetime.datetime.utcnow().isoformat(),
                            "type": "chat",
                            "user_id": authenticated_name,
                            "text": data.get("text", ""),
                            "authenticated": bool(session),
                            "session_username": session["username"] if session else None
                        }) + "\n")
                except Exception:
                    pass
                # Reenviar a todos
                for uid, conn in list(room.connections.items()):
                    if uid != authenticated_name:
                        try:
                            await conn.send_text(json.dumps({
                                "type": "chat",
                                "user_id": authenticated_name,
                                "text": data.get("text", ""),
                                "file": data.get("file")
                            }))
                        except Exception:
                            pass

            elif msg_type in ("offer", "answer", "ice"):
                target = data.get("target")
                if target and target in room.connections:
                    try:
                        await room.connections[target].send_text(json.dumps({
                            **data, "from": authenticated_name
                        }))
                    except Exception:
                        pass

            elif msg_type == "presenter_start":
                room.current_presenter = authenticated_name
                for uid, conn in list(room.connections.items()):
                    if uid != authenticated_name:
                        try:
                            await conn.send_text(json.dumps({
                                "type": "presenter_start",
                                "user_id": authenticated_name
                            }))
                        except Exception:
                            pass

            elif msg_type == "presenter_stop":
                if room.current_presenter == authenticated_name:
                    room.current_presenter = None
                for uid, conn in list(room.connections.items()):
                    if uid != authenticated_name:
                        try:
                            await conn.send_text(json.dumps({
                                "type": "presenter_stop",
                                "user_id": authenticated_name
                            }))
                        except Exception:
                            pass

    except WebSocketDisconnect:
        room.connections.pop(authenticated_name, None)
        room.participants.discard(authenticated_name)
        # Notificar salida
        for uid, conn in list(room.connections.items()):
            try:
                await conn.send_text(json.dumps({
                    "type": "user_left", "user_id": authenticated_name
                }))
            except Exception:
                pass
        # Inbox: salida
        try:
            with open(Path(f"/tmp/Meet[Nombre_IA]-inbox-{room_id}.jsonl"), "a") as f:
                f.write(json.dumps({
                    "ts": datetime.datetime.utcnow().isoformat(),
                    "type": "left",
                    "user_id": authenticated_name
                }) + "\n")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════
#  TRANSCRIPCIÓN (conservado del original)
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
SCREENSHOTS_DIR = "/opt/Meet[Nombre_IA]/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

@app.post("/api/screenshot/{room_id}")
async def save_screenshot(room_id: str, request: Request):
    data = await request.json()
    image_b64 = data.get("image", "")
    source = data.get("source", "unknown")
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{room_id}_{source}_{ts}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(_b64.b64decode(image_b64))
    return {"success": True, "filename": filename}
