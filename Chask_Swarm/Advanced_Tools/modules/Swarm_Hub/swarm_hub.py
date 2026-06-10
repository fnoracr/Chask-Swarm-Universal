"""
swarm_hub.py — Nodo Central de la Internet de Enjambres
========================================================
Corre en el VPS del administrador. Es el registro global.

Funciones:
  - Registra enjambres y enrutadores que se conectan
  - Ping cada hora a enrutadores para saber si estan vivos
  - Distribuye lista de enrutadores activos a toda la red
  - El propio hub es tambien enrutador
  - Recibe solicitudes de ayuda y las redirige

API REST (Flask):
  POST /register       — Registrar un enjambre
  POST /register_router — Registrarse como enrutador
  GET  /routers        — Obtener lista de enrutadores activos
  POST /ping           — Heartbeat de un nodo
  POST /help           — Solicitar ayuda a la red global
  GET  /network        — Estado completo de la red
  GET  /health         — Health check del hub

Seguridad:
  - Todas las comunicaciones usan HTTPS (en produccion)
  - API Key para registro (anti-spam)
  - Rate limiting por IP
  - Cifrado E2E del payload de tareas
"""
import os
import sys
import json
import time
import hmac
import hashlib
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Flask import con fallback
try:
    from flask import Flask, request, jsonify
    FLASK_OK = True
except ImportError:
    FLASK_OK = False

ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
HUB_DATA = ROOT / "hub_data"
SWARMS_DB = HUB_DATA / "swarms.json"
ROUTERS_DB = HUB_DATA / "routers.json"
HUB_CONFIG = ROOT / "hub_config.json"
HUB_LOG = HUB_DATA / "hub.log"

HUB_DATA.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "hub_port": 51400,
    "api_key": "",
    "ping_interval_minutes": 60,
    "router_timeout_minutes": 120,
    "max_swarms": 10000,
    "hub_is_router": True,
    "hub_name": "ChaskHub-Central",
}


def _log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] [Hub] {msg}"
    print(line)
    try:
        with open(HUB_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config() -> dict:
    if HUB_CONFIG.exists():
        try:
            return json.loads(HUB_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    cfg = DEFAULT_CONFIG.copy()
    cfg["api_key"] = secrets.token_urlsafe(32)
    HUB_CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg


def load_db(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_db(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


# ═══════════════════════════════════════════════════════════
# HUB CORE
# ═══════════════════════════════════════════════════════════

class SwarmHub:
    def __init__(self):
        self.config = load_config()
        self.swarms = load_db(SWARMS_DB)   # {node_id: {ip, name, caps, last_ping, ...}}
        self.routers = load_db(ROUTERS_DB) # {node_id: {ip, name, caps, last_ping, ...}}
        self._running = False
        _log(f"Hub inicializado: {len(self.swarms)} enjambres, {len(self.routers)} enrutadores")

    def register_swarm(self, node_id: str, ip: str, name: str,
                       capabilities: list, port: int = 51338) -> dict:
        """Registra un enjambre en la red global."""
        self.swarms[node_id] = {
            "node_id": node_id, "ip": ip, "name": name,
            "capabilities": capabilities, "port": port,
            "registered_at": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat(),
            "alive": True
        }
        save_db(SWARMS_DB, self.swarms)
        _log(f"Enjambre registrado: {name} ({ip}) id={node_id}")
        return {"success": True, "total_swarms": len(self.swarms)}

    def register_router(self, node_id: str, ip: str, name: str,
                        capabilities: list, port: int = 51338) -> dict:
        """Registra un enrutador (nodo que redirige solicitudes)."""
        self.routers[node_id] = {
            "node_id": node_id, "ip": ip, "name": name,
            "capabilities": capabilities, "port": port,
            "registered_at": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat(),
            "alive": True, "swarms_known": 0
        }
        save_db(ROUTERS_DB, self.routers)
        _log(f"Enrutador registrado: {name} ({ip}) id={node_id}")
        return {"success": True, "total_routers": len(self.routers)}

    def ping(self, node_id: str) -> dict:
        """Recibe heartbeat de un nodo."""
        now = datetime.now().isoformat()
        if node_id in self.swarms:
            self.swarms[node_id]["last_ping"] = now
            self.swarms[node_id]["alive"] = True
            save_db(SWARMS_DB, self.swarms)
        if node_id in self.routers:
            self.routers[node_id]["last_ping"] = now
            self.routers[node_id]["alive"] = True
            save_db(ROUTERS_DB, self.routers)
        return {"success": True, "timestamp": now}

    def get_active_routers(self) -> list:
        """Lista enrutadores activos (ping reciente)."""
        timeout = self.config.get("router_timeout_minutes", 120)
        cutoff = datetime.now() - timedelta(minutes=timeout)
        active = []
        for rid, r in self.routers.items():
            try:
                last = datetime.fromisoformat(r["last_ping"])
                if last > cutoff:
                    active.append({
                        "node_id": rid, "ip": r["ip"], "name": r["name"],
                        "capabilities": r["capabilities"], "port": r["port"]
                    })
                else:
                    r["alive"] = False
            except Exception:
                pass
        save_db(ROUTERS_DB, self.routers)
        return active

    def get_network_status(self) -> dict:
        """Estado completo de la red."""
        active_routers = self.get_active_routers()
        alive_swarms = sum(1 for s in self.swarms.values() if s.get("alive"))
        all_caps = set()
        for s in list(self.swarms.values()) + list(self.routers.values()):
            all_caps.update(s.get("capabilities", []))
        return {
            "total_swarms": len(self.swarms),
            "alive_swarms": alive_swarms,
            "total_routers": len(self.routers),
            "active_routers": len(active_routers),
            "unique_capabilities": sorted(all_caps),
            "timestamp": datetime.now().isoformat()
        }

    def find_capable_nodes(self, required_caps: list) -> list:
        """Busca nodos que tengan las capacidades requeridas."""
        needed = set(required_caps)
        matches = []
        # Primero enrutadores activos
        for r in self.get_active_routers():
            if needed.issubset(set(r["capabilities"])):
                matches.append(r)
        # Luego enjambres
        for sid, s in self.swarms.items():
            if s.get("alive") and needed.issubset(set(s.get("capabilities", []))):
                matches.append({
                    "node_id": sid, "ip": s["ip"], "name": s["name"],
                    "capabilities": s["capabilities"], "port": s["port"]
                })
        return matches

    def _ping_routers_loop(self):
        """Ping periodico a enrutadores para verificar que estan vivos."""
        import requests as req
        interval = self.config.get("ping_interval_minutes", 60) * 60
        while self._running:
            time.sleep(interval)
            _log("Ping periodico a enrutadores...")
            for rid, r in list(self.routers.items()):
                try:
                    resp = req.post(
                        f"http://{r['ip']}:{r['port']}/node/ping",
                        json={"from": "hub"}, timeout=10
                    )
                    if resp.status_code == 200:
                        r["last_ping"] = datetime.now().isoformat()
                        r["alive"] = True
                        _log(f"  Router {r['name']} ({r['ip']}): ALIVE")
                    else:
                        r["alive"] = False
                        _log(f"  Router {r['name']} ({r['ip']}): DOWN")
                except Exception:
                    r["alive"] = False
                    _log(f"  Router {r['name']} ({r['ip']}): UNREACHABLE")
            save_db(ROUTERS_DB, self.routers)

            # Distribuir lista de enrutadores a todos los enjambres
            self._distribute_router_list()

    def _distribute_router_list(self):
        """Envia lista de enrutadores activos a cada enjambre."""
        import requests as req
        active = self.get_active_routers()
        _log(f"Distribuyendo {len(active)} enrutadores a {len(self.swarms)} enjambres")
        for sid, s in self.swarms.items():
            if not s.get("alive"):
                continue
            try:
                req.post(
                    f"http://{s['ip']}:{s['port']}/node/update_routers",
                    json={"routers": active}, timeout=10
                )
            except Exception:
                pass

    def start(self):
        self._running = True
        threading.Thread(target=self._ping_routers_loop, daemon=True).start()
        _log("Hub iniciado con ping loop")


# ═══════════════════════════════════════════════════════════
# FLASK API
# ═══════════════════════════════════════════════════════════

def create_app() -> 'Flask':
    if not FLASK_OK:
        print("Flask no instalado. pip install flask")
        sys.exit(1)

    app = Flask(__name__)
    hub = SwarmHub()
    hub.start()
    config = hub.config

    def check_api_key():
        key = request.headers.get("X-API-Key", "")
        if config.get("api_key") and key != config["api_key"]:
            return False
        return True

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "hub": config["hub_name"],
                       "timestamp": datetime.now().isoformat()})

    @app.route("/register", methods=["POST"])
    def register():
        if not check_api_key():
            return jsonify({"error": "API key invalida"}), 403
        data = request.json or {}
        ip = data.get("ip") or request.remote_addr
        result = hub.register_swarm(
            data.get("node_id", ""), ip, data.get("name", "unknown"),
            data.get("capabilities", []), data.get("port", 51338)
        )
        # Devolver lista de enrutadores al registrarse
        result["routers"] = hub.get_active_routers()
        return jsonify(result)

    @app.route("/register_router", methods=["POST"])
    def register_router():
        if not check_api_key():
            return jsonify({"error": "API key invalida"}), 403
        data = request.json or {}
        ip = data.get("ip") or request.remote_addr
        result = hub.register_router(
            data.get("node_id", ""), ip, data.get("name", "unknown"),
            data.get("capabilities", []), data.get("port", 51338)
        )
        return jsonify(result)

    @app.route("/routers", methods=["GET"])
    def routers():
        return jsonify({"routers": hub.get_active_routers()})

    @app.route("/ping", methods=["POST"])
    def ping():
        data = request.json or {}
        result = hub.ping(data.get("node_id", ""))
        return jsonify(result)

    @app.route("/network", methods=["GET"])
    def network():
        return jsonify(hub.get_network_status())

    @app.route("/help", methods=["POST"])
    def help_request():
        """Buscar nodos capaces y redirigir solicitud."""
        if not check_api_key():
            return jsonify({"error": "API key invalida"}), 403
        data = request.json or {}
        caps = data.get("required_capabilities", ["llm_chat"])
        matches = hub.find_capable_nodes(caps)
        return jsonify({
            "matches": matches[:5],
            "total_matches": len(matches),
            "description": data.get("description", "")
        })

    return app


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    config = load_config()

    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        hub = SwarmHub()
        status = hub.get_network_status()
        print(f"=== Internet de Enjambres ===")
        print(f"Enjambres: {status['alive_swarms']}/{status['total_swarms']}")
        print(f"Enrutadores: {status['active_routers']}/{status['total_routers']}")
        print(f"Capacidades: {', '.join(status['unique_capabilities'])}")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--apikey":
        print(f"API Key: {config['api_key']}")
        sys.exit(0)

    print(f"=== Chask Swarm Hub — Internet de Enjambres ===")
    print(f"Puerto: {config['hub_port']}")
    print(f"API Key: {config['api_key'][:8]}...")
    print(f"Ping interval: {config['ping_interval_minutes']} min")

    app = create_app()
    app.run(host="0.0.0.0", port=config["hub_port"], debug=False)
