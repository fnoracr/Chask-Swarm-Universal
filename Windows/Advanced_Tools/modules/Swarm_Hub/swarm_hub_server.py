"""
swarm_hub_server.py — Servidor Central del Hub (instalar en el VPS)
====================================================================
Puerto: 51400

Responsabilidades:
  1. Mantener lista de enrutadores activos
  2. Dar lista de enrutadores a enjambres nuevos
  3. Actuar como enrutador mientras no haya suficientes en la red
     (umbral configurable: HUB_ROUTER_THRESHOLD)

Endpoints:
  POST /hub/router/online   — enrutador se activa
  POST /hub/router/offline  — enrutador se apaga
  GET  /hub/routers         — enjambre pide lista de enrutadores
  POST /hub/help            — solicitud de ayuda (solo cuando hub actua como enrutador)
  GET  /hub/status          — estado general de la red (admin)
"""
import json
import time
import threading
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    err = traceback.format_exc()
    _log(f"UNHANDLED EXCEPTION: {err}")
    from flask import jsonify
    return jsonify({"success": False, "error": "Internal Server Error", "trace": err}), 500

# ── Config ─────────────────────────────────────────────────────────
HUB_PORT              = 51400
HUB_ROUTER_THRESHOLD  = 5       # Cuando hay >= N enrutadores, Hub deja de rutear
ROUTER_TTL_SECONDS    = 300     # Enrutador considerado muerto si no hace ping en 5 min
DATA_FILE             = Path("hub_data.json")
LOG_FILE              = Path("hub.log")

# ── Estado en memoria ──────────────────────────────────────────────
_lock   = threading.Lock()
_state  = {"routers": {}, "blacklist": {}}   # node_id → router_info, blacklist: node_id → {ip, reason, timestamp}


def _log(msg: str):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _save():
    try:
        DATA_FILE.write_text(json.dumps(_state, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _load():
    global _state
    if DATA_FILE.exists():
        try:
            _state = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if "blacklist" not in _state:
                _state["blacklist"] = {}
        except Exception:
            pass


def _active_routers() -> list:
    """Enrutadores vistos en los ultimos ROUTER_TTL_SECONDS segundos."""
    cutoff = time.time() - ROUTER_TTL_SECONDS
    return [r for r in _state["routers"].values() if r.get("last_seen", 0) > cutoff]


def _hub_acts_as_router() -> bool:
    """El Hub actua como enrutador si hay pocos enrutadores reales."""
    return len(_active_routers()) < HUB_ROUTER_THRESHOLD


# ══════════════════════════════════════════════════════════════════
#  ENDPOINTS DE ENRUTADORES
# ══════════════════════════════════════════════════════════════════

@app.route("/hub/router/online", methods=["POST"])
def router_online():
    """Un enrutador notifica que esta activo. Hub responde con lista completa."""
    data    = request.get_json() or {}
    node_id = data.get("node_id", str(uuid.uuid4())[:8])
    ip      = data.get("ip", request.remote_addr)

    # Verificar si está en la lista negra global
    with _lock:
        if node_id in _state.get("blacklist", {}) or any(b.get("ip") == ip for b in _state.get("blacklist", {}).values()):
            _log(f"⚠️ REGISTRO RECHAZADO: El enrutador {node_id} ({ip}) está en la LISTA NEGRA GLOBAL.")
            return jsonify({"success": False, "error": "El nodo está en la lista negra por intento de intrusión o manipulación"}), 403

        _state["routers"][node_id] = {
            "node_id":      node_id,
            "node_name":    data.get("node_name", "unknown"),
            "ip":           ip,
            "port":         data.get("port", 51338),
            "capabilities": data.get("capabilities", []),
            "last_seen":    time.time(),
            "online_since": time.time(),
        }
        _save()
        active = _active_routers()

    _log(f"Enrutador ONLINE: {data.get('node_name')} ({ip}) — Total activos: {len(active)}")

    return jsonify({
        "success": True,
        "routers": active,              # Lista completa de enrutadores activos
        "hub_is_router": _hub_acts_as_router(),
        "total_routers": len(active),
    })


# ══════════════════════════════════════════════════════════════════
#  BLACKBOX / SEGURIDAD PROACTIVA GLOBAL
# ══════════════════════════════════════════════════════════════════

@app.route("/hub/blacklist/report", methods=["POST"])
def blacklist_report():
    """Cualquier enjambre o enrutador reporta una intrusión. El Hub aísla al nodo a perpetuidad."""
    data    = request.get_json() or {}
    node_id = data.get("node_id")
    ip      = data.get("ip")
    reason  = data.get("reason", "Intrusión detectada / Manipulación de prompts")

    if not node_id and not ip:
        return jsonify({"success": False, "error": "Falta node_id o ip para aislar"}), 400

    _log(f"🚨 ALERTA GLOBAL DE INTRUSIÓN: Reportado nodo {node_id} ({ip}) por: '{reason}'")

    with _lock:
        # Añadir a la lista negra
        target_id = node_id or f"unk_{str(uuid.uuid4())[:6]}"
        _state["blacklist"][target_id] = {
            "node_id": node_id,
            "ip": ip,
            "reason": reason,
            "timestamp": time.time()
        }
        
        # Remover inmediatamente de routers y peers activos
        if node_id in _state["routers"]:
            del _state["routers"][node_id]
        if "peers" in _state and node_id in _state["peers"]:
            del _state["peers"][node_id]
            
        _save()
        active_routers_list = _active_routers()

    # PROPAGACIÓN ACTIVA A TODOS LOS ENRUTADORES ONLINE
    def propagate():
        import requests as req_lib
        for r in active_routers_list:
            try:
                # POST a cada enrutador para añadir inmediatamente el nodo a su blacklist persistente
                req_lib.post(
                    f"http://{r['ip']}:{r.get('port', 51338)}/router/blacklist/add",
                    json={"node_id": node_id, "ip": ip, "reason": reason},
                    timeout=4
                )
                _log(f"Propagación exitosa a enrutador {r['node_name']} ({r['ip']})")
            except Exception as e:
                _log(f"Error propagando a enrutador {r['node_name']}: {e}")

    threading.Thread(target=propagate, daemon=True).start()

    return jsonify({
        "success": True, 
        "message": f"Nodo {node_id} ({ip}) añadido a la lista negra global y propagado a todos los enrutadores."
    })


@app.route("/hub/blacklist", methods=["GET"])
def get_blacklist():
    """Devuelve la lista negra global para que los enrutadores se sincronicen en el arranque."""
    with _lock:
        blacklist_data = list(_state.get("blacklist", {}).values())
    return jsonify({"blacklist": blacklist_data})


@app.route("/hub/router/offline", methods=["POST"])
def router_offline():
    """Un enrutador notifica que se va a apagar."""
    data    = request.get_json() or {}
    node_id = data.get("node_id", "")

    with _lock:
        removed = _state["routers"].pop(node_id, None)
        _save()

    if removed:
        _log(f"Enrutador OFFLINE: {removed.get('node_name')} ({removed.get('ip')})")
    return jsonify({"success": True})


@app.route("/hub/router/ping", methods=["POST"])
def router_ping():
    """Heartbeat de un enrutador (actualiza last_seen)."""
    data    = request.get_json() or {}
    node_id = data.get("node_id", "")
    with _lock:
        if node_id in _state["routers"]:
            _state["routers"][node_id]["last_seen"] = time.time()
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════
#  ENDPOINTS DE ENJAMBRES (nodos cliente)
# ══════════════════════════════════════════════════════════════════

@app.route("/hub/routers", methods=["GET"])
def get_routers():
    """
    Un enjambre nuevo pide la lista de enrutadores activos.
    Si el Hub actua como enrutador, se incluye a si mismo.
    """
    active = _active_routers()
    _log(f"Lista de enrutadores solicitada desde {request.remote_addr} — {len(active)} activos")
    return jsonify({
        "routers": active,
        "hub_is_router": _hub_acts_as_router(),
        "total": len(active),
    })


# ══════════════════════════════════════════════════════════════════
#  HUB COMO ENRUTADOR (activo cuando hay pocos enrutadores reales)
# ══════════════════════════════════════════════════════════════════

@app.route("/router/register", methods=["POST"])
def hub_register_peer():
    """El Hub acepta registro de enjambres cuando actua como enrutador."""
    if not _hub_acts_as_router():
        return jsonify({"success": False, "reason": "Hub en modo directorio. Usa los enrutadores de /hub/routers"}), 503
    data = request.get_json() or {}
    # Guardar peer temporalmente (en memoria, no en disco — el Hub no necesita persistirlos)
    node_id = data.get("node_id")
    if node_id:
        with _lock:
            if "peers" not in _state:
                _state["peers"] = {}
            _state["peers"][node_id] = {**data, "last_seen": time.time()}
    _log(f"Peer registrado en Hub (modo enrutador): {data.get('node_name')} ({data.get('ip')})")
    return jsonify({"success": True})


@app.route("/router/help", methods=["POST"])
def hub_help():
    """El Hub procesa solicitudes de ayuda cuando actua como enrutador."""
    if not _hub_acts_as_router():
        return jsonify({"queued": False, "reason": "Hub en modo directorio"}), 503

    data = request.get_json() or {}
    threading.Thread(target=_process_help_as_router, args=(data,), daemon=True).start()
    return jsonify({"queued": True})


def _process_help_as_router(request_data: dict):
    """
    El Hub actua como enrutador: hace broadcast can_help? a los peers conocidos.
    Replica la logica de SwarmRouter.handle_help_request.
    """
    import requests as req_lib
    task_id  = request_data.get("task_id", "?")
    req_caps = request_data.get("required_capabilities", ["llm_chat"])
    requester = {
        "ip":      request_data.get("ip"),
        "port":    request_data.get("port", 51338),
        "node_id": request_data.get("node_id"),
    }

    peers = list(_state.get("peers", {}).values())
    cutoff = time.time() - 600
    active_peers = [p for p in peers if p.get("last_seen", 0) > cutoff
                    and p.get("node_id") != requester["node_id"]]

    first_helper = None
    lock = threading.Lock()

    def ask(peer):
        nonlocal first_helper
        try:
            r = req_lib.post(
                f"http://{peer['ip']}:{peer.get('port', 51338)}/node/can_help",
                json={"task_id": task_id, "description": request_data.get("description", ""),
                      "required_capabilities": req_caps},
                timeout=5
            )
            if r.status_code == 200 and r.json().get("can_help"):
                with lock:
                    if first_helper is None:
                        first_helper = peer
        except Exception:
            pass

    threads = [threading.Thread(target=ask, args=(p,), daemon=True) for p in active_peers]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=6)

    if first_helper:
        _log(f"[{task_id}] Hub (modo enrutador) encontro helper: {first_helper.get('node_name')}")
        try:
            # Mandar datos del helper al solicitante
            req_lib.post(
                f"http://{requester['ip']}:{requester['port']}/node/helper_contact",
                json={"task_id": task_id, "helper": first_helper}, timeout=5
            )
            # Mandar datos del solicitante al helper
            req_lib.post(
                f"http://{first_helper['ip']}:{first_helper.get('port', 51338)}/node/task_contact",
                json={"task_id": task_id, "requester": requester}, timeout=5
            )
        except Exception as e:
            _log(f"[{task_id}] Error intercambiando contactos: {e}")
    else:
        _log(f"[{task_id}] Sin helpers disponibles en el Hub.")


# ══════════════════════════════════════════════════════════════════
#  ESTADO / ADMIN
# ══════════════════════════════════════════════════════════════════

@app.route("/hub/status", methods=["GET"])
def hub_status():
    active = _active_routers()
    return jsonify({
        "hub_is_router":   _hub_acts_as_router(),
        "active_routers":  len(active),
        "threshold":       HUB_ROUTER_THRESHOLD,
        "routers":         active,
        "peers_connected": len(_state.get("peers", {})),
        "uptime":          time.time(),
    })


# ══════════════════════════════════════════════════════════════════
#  BIBLIOTECA GLOBAL DE SKILLS EN VPS (QDRANT)
# ══════════════════════════════════════════════════════════════════

def _ensure_qdrant_collection():
    """Asegura que la colección shared_skills_library existe en el Qdrant local del VPS."""
    import urllib.request
    import json
    try:
        col_name = "shared_skills_library"
        url = f"http://localhost:6333/collections/{col_name}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=3) as r:
                pass
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Crear la colección
                payload = {
                    "vectors": {
                        "size": 384,
                        "distance": "Cosine"
                    }
                }
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="PUT")
                with urllib.request.urlopen(req, timeout=5):
                    pass
                _log(f"Colección Qdrant {col_name} creada en VPS.")
    except Exception as e:
        _log(f"Error inicializando colección Qdrant: {e}")

@app.route("/hub/skills/share", methods=["POST"])
def hub_share_skill():
    """Un enrutador sube una skill para añadirla a la biblioteca global de la colmena."""
    
    def assign_primary_theme(name, desc, tags):
        text = f"{name} {desc} {' '.join(tags)}".lower()
        if any(w in text for w in ['ia', 'llm', 'rag', 'modelo', 'machine learning', 'ai']): return "IA y Machine Learning"
        if any(w in text for w in ['seguridad', 'audit', 'backup', 'privacidad', 'cripto', 'logs']): return "Seguridad y Auditoría"
        if any(w in text for w in ['desarrollo', 'script', 'frontend', 'backend', 'herramienta', 'html', 'css', 'js', 'python']): return "Desarrollo y Programación"
        if any(w in text for w in ['automatizacion', 'rpa', 'bot', 'scraping', 'tarea']): return "Automatización y Productividad"
        if any(w in text for w in ['datos', 'qdrant', 'base de datos', 'sql', 'almacenamiento']): return "Datos y Almacenamiento"
        if any(w in text for w in ['comunicacion', 'telegram', 'api', 'webhook', 'redes', 'ssh']): return "Comunicación e Integración"
        return "Otros"

    import hashlib
    import uuid
    from datetime import datetime
    data = request.get_json() or {}
    skill_data = data.get("skill", {})
    name = skill_data.get("name")
    if not name:
        return jsonify({"success": False, "error": "Skill sin nombre"}), 400

    _log(f"Recibiendo skill global en Hub: {name} de {data.get('node_id')}")
    _ensure_qdrant_collection()

    try:
        # Generar embedding determinista (pseudo-vector) como hace SwarmNode local
        content_to_vector = f"{name} {skill_data.get('description', '')} {' '.join(skill_data.get('tags', []))} {skill_data.get('code', '')}"
        h = hashlib.sha256(content_to_vector.encode("utf-8")).digest()
        vector = [float(x)/255.0 for x in h]
        if len(vector) < 384:
            vector += [0.0] * (384 - len(vector))
        else:
            vector = vector[:384]

        # Guardar en Qdrant vía REST (ya que qdrant_client puede no estar en VPS)
        point_id = hashlib.md5(name.encode("utf-8")).hexdigest()
        
        # En Qdrant REST API los UUIDs tienen guiones, o ints. Usaremos UUID
        point_uuid = str(uuid.UUID(point_id))

        payload = {
            "points": [{
                "id": point_uuid,
                "vector": vector,
                "payload": {
                    "name": name,
                    "description": skill_data.get("description", ""),
                    "tags": skill_data.get("tags", []),
                    "primary_theme": assign_primary_theme(name, skill_data.get("description", ""), skill_data.get("tags", [])),
                    "code": skill_data.get("code", ""),
                    "created": datetime.now().isoformat(),
                    "author": skill_data.get("author", "desconocido"),
                    "version": skill_data.get("version", "1.0.0"),
                    "downloads": 0
                }
            }]
        }

        import urllib.request
        import json
        req = urllib.request.Request("http://localhost:6333/collections/shared_skills_library/points", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="PUT")
        with urllib.request.urlopen(req, timeout=5) as r:
            _log(f"Skill '{name}' guardada exitosamente en Qdrant (VPS)")
            return jsonify({"success": True})
    except urllib.error.HTTPError as e:
        _log(f"Error de Qdrant VPS: {e.read().decode()}")
        return jsonify({"success": False, "error": f"Error interno Qdrant"}), 500
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        _log(f"Error procesando skill share en VPS: {err}")
        return jsonify({"success": False, "error": str(err)}), 500

@app.route("/hub/skills/search", methods=["GET"])
def hub_search_skills():
    """Búsqueda global de skills en el VPS."""
    def assign_primary_theme(name, desc, tags):
        text = f"{name} {desc} {' '.join(tags)}".lower()
        if any(w in text for w in ['ia', 'llm', 'rag', 'modelo', 'machine learning', 'ai']): return "IA y Machine Learning"
        if any(w in text for w in ['seguridad', 'audit', 'backup', 'privacidad', 'cripto', 'logs']): return "Seguridad y Auditoría"
        if any(w in text for w in ['desarrollo', 'script', 'frontend', 'backend', 'herramienta', 'html', 'css', 'js', 'python']): return "Desarrollo y Programación"
        if any(w in text for w in ['automatizacion', 'rpa', 'bot', 'scraping', 'tarea']): return "Automatización y Productividad"
        if any(w in text for w in ['datos', 'qdrant', 'base de datos', 'sql', 'almacenamiento']): return "Datos y Almacenamiento"
        if any(w in text for w in ['comunicacion', 'telegram', 'api', 'webhook', 'redes', 'ssh']): return "Comunicación e Integración"
        return "Otros"

    import urllib.request
    import json
    import hashlib
    
    query_str = request.args.get("q", "")
    _ensure_qdrant_collection()
    
    try:
        if query_str.strip():
            # Búsqueda por texto (substring exacto) en el payload
            url_scroll = "http://localhost:6333/collections/shared_skills_library/points/scroll"
            req = urllib.request.Request(url_scroll, data=json.dumps({"limit": 1000, "with_payload": True}).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                
            points = data.get("result", [])
            if isinstance(points, dict) and "points" in points:
                points = points["points"]
                
            q_lower = query_str.lower()
            results = []
            for p in points:
                payload = p.get("payload", {})
                name = payload.get("name", "").lower()
                desc = payload.get("description", "").lower()
                tags = [t.lower() for t in payload.get("tags", [])]
                
                if q_lower in name or q_lower in desc or any(q_lower in t for t in tags):
                    if "primary_theme" not in payload:
                        payload["primary_theme"] = assign_primary_theme(name, desc, tags)
                    results.append(payload)
            return jsonify({"success": True, "results": results})
        else:
            # Sin query, devolver las top skills usando scroll
            url_scroll = "http://localhost:6333/collections/shared_skills_library/points/scroll"
            req = urllib.request.Request(url_scroll, data=json.dumps({"limit": 100, "with_payload": True}).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
            
            points = data.get("result", [])
            # En /search el array es data["result"], en /scroll es data["result"]["points"]
            if isinstance(points, dict) and "points" in points:
                points = points["points"]
                
            results = []
            for p in points:
                if not p.get("payload"):
                    continue
                payload = p["payload"]
                if "primary_theme" not in payload:
                    name = payload.get("name", "").lower()
                    desc = payload.get("description", "").lower()
                    tags = [t.lower() for t in payload.get("tags", [])]
                    payload["primary_theme"] = assign_primary_theme(name, desc, tags)
                results.append(payload)
            return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



# ══════════════════════════════════════════════════════════════════
#  LIMPIEZA PERIODICA
# ══════════════════════════════════════════════════════════════════

def _cleanup_loop():
    """Elimina enrutadores y peers que no hacen ping."""
    while True:
        time.sleep(60)
        cutoff = time.time() - ROUTER_TTL_SECONDS
        with _lock:
            dead = [nid for nid, r in _state["routers"].items()
                    if r.get("last_seen", 0) < cutoff]
            for nid in dead:
                name = _state["routers"][nid].get("node_name", nid)
                del _state["routers"][nid]
                _log(f"Enrutador eliminado por inactividad: {name}")
            if dead:
                _save()



# ══════════════════════════════════════════════════════════════════
#  ENDPOINTS DE P2P EDUCATION (Charm Edu)
# ══════════════════════════════════════════════════════════════════

@app.route("/hub/learning/share", methods=["POST"])
def hub_learning_share():
    data = request.get_json() or {}
    node_id = data.get("node_id")
    topic_id = data.get("topic_id")
    topic_name = data.get("topic_name")
    ip = request.remote_addr
    
    if not node_id or not topic_id:
        return jsonify({"success": False, "error": "Faltan parametros"}), 400
        
    if "p2p_topics" not in _state:
        _state["p2p_topics"] = {}
        
    if topic_id not in _state["p2p_topics"]:
        _state["p2p_topics"][topic_id] = {
            "name": topic_name,
            "peers": {}
        }
        
    _state["p2p_topics"][topic_id]["peers"][node_id] = {
        "ip": ip,
        "last_seen": time.time()
    }
    with _lock:
        _save()
    return jsonify({"success": True})

@app.route("/hub/learning/revoke", methods=["POST"])
def hub_learning_revoke():
    data = request.get_json() or {}
    node_id = data.get("node_id")
    topic_id = data.get("topic_id")
    
    if not node_id or not topic_id:
        return jsonify({"success": False, "error": "Faltan parametros"}), 400
        
    with _lock:
        if "p2p_topics" in _state and topic_id in _state["p2p_topics"]:
            peers = _state["p2p_topics"][topic_id].get("peers", {})
            if node_id in peers:
                del peers[node_id]
                _log(f"Seed {node_id} revocada del tema {topic_id} en el Hub VPS")
            if not peers:
                del _state["p2p_topics"][topic_id]
                _log(f"Tema {topic_id} eliminado de p2p_topics en el Hub VPS por no tener seeds")
            _save()
            
    return jsonify({"success": True})

@app.route("/hub/learning/find", methods=["GET"])
def hub_learning_find():
    q = request.args.get("q", "").lower()
    
    if "p2p_topics" not in _state:
        _state["p2p_topics"] = {}
        
    results = []
    cutoff = time.time() - (86400 * 7) # Consider peers seen in the last 7 days
    
    for topic_id, tdata in _state["p2p_topics"].items():
        name = tdata.get("name", "")
        if q in name.lower() or not q:
            # count active peers
            active_peers = 0
            for peer_id, peer_data in tdata.get("peers", {}).items():
                if peer_data.get("last_seen", 0) > cutoff:
                    active_peers += 1
                    
            if active_peers > 0:
                results.append({
                    "id": topic_id,
                    "name": name,
                    "peers": active_peers
                })
                
    return jsonify({"success": True, "results": results})


if __name__ == "__main__":
    _load()
    threading.Thread(target=_cleanup_loop, daemon=True, name="Cleanup").start()
    _log(f"Hub iniciado en puerto {HUB_PORT}. Umbral de enrutadores: {HUB_ROUTER_THRESHOLD}")
    app.run(host="0.0.0.0", port=HUB_PORT, debug=False, use_reloader=False)
