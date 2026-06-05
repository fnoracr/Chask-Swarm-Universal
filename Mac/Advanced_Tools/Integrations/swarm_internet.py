"""
swarm_internet.py — Red Mundial de Enjambres (P2P Broker)
==========================================================
Roles:
  ENJAMBRE  — nodo cliente. Pide y ofrece ayuda.
  ENRUTADOR — mediador puro. Conecta solicitante con ayudante.
              NUNCA ejecuta tareas ni ve su contenido.
  HUB (VPS) — directorio. Gestiona lista de enrutadores activos.

Flujo de arranque de un enjambre:
  1. Intenta registrarse con enrutadores conocidos (cached_routers.json)
  2. Si todos fallan → GET hub/routers → obtiene lista activa
  3. Se registra con los enrutadores recibidos

Flujo de un enrutador al encender:
  → POST hub/router/online  (Hub responde con lista completa de activos)
  → empieza a aceptar registros de enjambres y solicitudes de ayuda

Flujo de ayuda (broker puro):
  A solicita ayuda → Enrutador R
  R hace broadcast can_help? a todos sus nodos
  Primero que responde Si → R intercambia contactos (A↔Helper)
  A y Helper se contactan DIRECTAMENTE (R no interviene mas)
  Si nadie responde → R reenvía la solicitud a otros enrutadores
"""
import os, sys, io, json, time, uuid, socket, threading
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import requests
    HTTP_OK = True
except ImportError:
    HTTP_OK = False

ROOT        = Path(r"C:\Program Files\Chask_Swarm")
TOOLS       = ROOT / "Advanced_Tools"
INET_CONFIG = ROOT / "Configuration/swarm_internet_config.json"
ROUTERS_CACHE = ROOT / "cached_routers.json"
PEERS_FILE  = ROOT / "connected_peers.json"   # Solo enrutadores: enjambres conectados
INET_LOG    = ROOT / "System_Logs/swarm_internet.log"
sys.path.insert(0, str(TOOLS))
import swarm_mesh_security as sms

NODE_PORT   = 51338   # Puerto de todo nodo (cliente y enrutador)
HUB_ROUTER_THRESHOLD = 5   # Hub deja de actuar como enrutador cuando hay >= N enrutadores

DEFAULT_CONFIG = {
    "hub_url":               "http://your-vps-ip:51400",
    "api_key":               "",
    "node_id":               "",
    "node_name":             "",
    "is_router":             False,
    "heartbeat_minutes":     60,
    "can_help_timeout":      5,    # segundos esperando respuestas can_help
    "router_forward_hops":   2,    # max reenvios entre enrutadores
}


# ── Logging ────────────────────────────────────────────────────────
def _log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] [SwarmNet] {msg}"
    print(line)
    try:
        with open(INET_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── Config ─────────────────────────────────────────────────────────
def load_config() -> dict:
    if INET_CONFIG.exists():
        try:
            return json.loads(INET_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    cfg = DEFAULT_CONFIG.copy()
    cfg["node_id"]   = str(uuid.uuid4())[:8]
    cfg["node_name"] = socket.gethostname()
    INET_CONFIG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg

def save_config(cfg: dict):
    INET_CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

def load_cached_routers() -> list:
    if ROUTERS_CACHE.exists():
        try:
            return json.loads(ROUTERS_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_cached_routers(routers: list):
    ROUTERS_CACHE.write_text(json.dumps(routers, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Utilidades de red ──────────────────────────────────────────────
def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_capabilities() -> list:
    caps = ["llm_chat"]
    cap_map = {
        "llm_vision":  TOOLS / "chask_vision.py",
        "sandbox_run": TOOLS / "sandbox.py",
        "kb_search":   TOOLS / "knowledge_orchestrator.py",
    }
    for cap, path in cap_map.items():
        if path.exists():
            caps.append(cap)
    return caps

def _post(url: str, data: dict, timeout: int = 10) -> dict:
    """POST con fallback silencioso."""
    try:
        r = requests.post(url, json=data, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        _log(f"POST {url} fallo: {e}")
    return {}

def _get(url: str, timeout: int = 10) -> dict:
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        _log(f"GET {url} fallo: {e}")
    return {}


# ══════════════════════════════════════════════════════════════════
#  ENJAMBRE (nodo cliente)
# ══════════════════════════════════════════════════════════════════

class SwarmNode:
    """Nodo enjambre. Arranca, busca enrutadores, pide/ofrece ayuda."""

    def __init__(self):
        self.cfg          = load_config()
        self.node_id      = self.cfg["node_id"]
        self.node_name    = self.cfg["node_name"]
        self.ip           = get_local_ip()
        self.capabilities = get_capabilities()
        self.routers      = load_cached_routers()
        self.hub_url      = self.cfg["hub_url"].rstrip("/")
        self._running     = False
        self._pending_tasks: dict = {}   # task_id → threading.Event + result
        self.blacklist_file = ROOT / "blacklist.json"
        self.blacklist      = self._load_blacklist()
        self.help_request_timestamps = {}

    # ── Arranque ─────────────────────────────────────────────────

    def _load_blacklist(self) -> dict:
        if self.blacklist_file.exists():
            try:
                return json.loads(self.blacklist_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_blacklist(self):
        try:
            self.blacklist_file.write_text(json.dumps(self.blacklist, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def add_to_blacklist(self, node_id: str, ip: str, reason: str, propagate: bool = True):
        """Añade un enjambre malicioso a la lista negra local y fuerza aislamiento a perpetuidad, propagando en tiempo real."""
        target_id = node_id or f"unk_{str(uuid.uuid4())[:6]}"
        if target_id in self.blacklist:
            return  # Evitar propagación redundante o bucles infinitos
            
        self.blacklist[target_id] = {
            "node_id": node_id,
            "ip": ip,
            "reason": reason,
            "timestamp": time.time()
        }
        self._save_blacklist()
        
        # Eliminarlo de peers enrutados de inmediato si somos enrutador
        if hasattr(self, "connected_peers") and node_id in self.connected_peers:
            try:
                del self.connected_peers[node_id]
                self._save_peers()
            except:
                pass
            _log(f"🚨 AISLAMIENTO: Removido peer {node_id} de la lista de peers activos de enrutador.")

        if propagate:
            def gossip():
                _log(f"📣 PROPAGACIÓN EN TIEMPO REAL: Replicando reporte de {node_id} ({ip}) a la red...")
                import requests
                # 1. Reportar al Servidor Central (Hub VPS)
                try:
                    requests.post(
                        f"{self.hub_url}/hub/blacklist/report",
                        json={"node_id": node_id, "ip": ip, "reason": f"[GOSSIP] {reason}"},
                        timeout=5
                    )
                except Exception as e:
                    _log(f"Error propagando blacklist al Hub Central: {e}")

                # 2. Propagar a todos los demás enrutadores conocidos
                known_routers = getattr(self, "known_routers", []) or getattr(self, "routers", [])
                for r in known_routers:
                    rip = r.get("ip")
                    rport = r.get("port", NODE_PORT)
                    rnode = r.get("node_id")
                    if rnode == self.node_id or rip == self.ip:
                        continue
                    try:
                        requests.post(
                            f"http://{rip}:{rport}/router/blacklist/add",
                            json={"node_id": node_id, "ip": ip, "reason": reason, "propagate": False},
                            timeout=5
                        )
                        _log(f"📣 Sincronizado blacklist con enrutador hermano: {r.get('node_name')} ({rip})")
                    except Exception as e:
                        pass
            threading.Thread(target=gossip, daemon=True, name="BlacklistGossip").start()

    def propagate_transaction_established(self, task_id: str, requester: dict, helper: dict, visited_routers: list = None):
        """
        Propaga la confirmación de establecimiento de comunicación a todos los enrutadores conocidos
        siguiendo un esquema de Path-Vector libre de bucles (los visitados no se reenvían).
        """
        visited = visited_routers or []
        if self.node_id not in visited:
            visited = list(visited) + [self.node_id]
            
        if not hasattr(self, "resolved_transactions"):
            self.resolved_transactions = {}
            
        if task_id in self.resolved_transactions:
            return  # Cortar si ya fue procesada y registrada localmente

        self.resolved_transactions[task_id] = {
            "requester": requester,
            "helper": helper,
            "visited_routers": visited,
            "timestamp": time.time()
        }

        # Propagar a enrutadores conocidos que NO estén en la lista de visitados
        known_routers = getattr(self, "known_routers", []) or getattr(self, "routers", [])
        
        def propagate_task():
            import requests
            for r in known_routers:
                rnode = r.get("node_id")
                rip = r.get("ip")
                rport = r.get("port", NODE_PORT)
                
                # Regla: No reenviar a enrutadores por los que ya pasó el mensaje
                if rnode in visited or rip == self.ip or rnode == self.node_id:
                    continue
                    
                url = f"http://{rip}:{rport}/router/transaction/confirm"
                try:
                    requests.post(url, json={
                        "task_id": task_id,
                        "requester": requester,
                        "helper": helper,
                        "visited_routers": visited
                    }, timeout=5)
                    _log(f"📣 TRANSACCIÓN CONFIRMADA: Propagado establecimiento {task_id} a enrutador {r.get('node_name')} ({rip})")
                except:
                    pass
                    
        threading.Thread(target=propagate_task, daemon=True, name=f"TxConfirm_{task_id}").start()

    def boot(self):
        """Arranca el nodo: sincroniza lista negra con el Hub, busca enrutadores y se registra."""
        _log(f"Arrancando nodo {self.node_name} ({self.node_id})")
        
        # Sincronizar lista negra global del Hub
        try:
            data = _get(f"{self.hub_url}/hub/blacklist", timeout=5)
            if data and "blacklist" in data:
                blacklist_list = data["blacklist"]
                for b in blacklist_list:
                    nid = b.get("node_id")
                    if nid:
                        self.blacklist[nid] = b
                self._save_blacklist()
                _log(f"Lista negra sincronizada con el Hub global: {len(self.blacklist)} nodos aislados.")
        except Exception as e:
            _log(f"No se pudo sincronizar lista negra con el Hub en el arranque: {e}")

        registered = self._register_with_known_routers()
        if not registered:
            _log("Ningun enrutador conocido disponible. Consultando Hub...")
            routers = self._fetch_routers_from_hub()
            if routers:
                self.routers = routers
                save_cached_routers(routers)
                self._register_with_known_routers()
            else:
                _log("Hub no disponible. Operando en modo local.")
        self._start_heartbeat()
        _log("Nodo listo.")

    def _register_with_known_routers(self) -> bool:
        """Intenta registrarse criptográficamente con cada enrutador conocido."""
        ok = False
        try:
            passport = sms.get_or_create_local_passport(self.node_id)
            timestamp = str(time.time())
            signature = sms.sign_challenge_with_node_key(timestamp)
        except Exception as e:
            _log(f"Error al preparar credenciales de red mundial: {e}")
            return False

        for router in self.routers:
            url = f"http://{router['ip']}:{router.get('port', NODE_PORT)}/router/register"
            resp = _post(url, {
                "node_id":      self.node_id,
                "node_name":    self.node_name,
                "ip":           self.ip,
                "port":         NODE_PORT,
                "capabilities": self.capabilities,
                "passport":     passport,
                "timestamp":    timestamp,
                "signature":    signature
            }, timeout=5)
            if resp.get("success"):
                _log(f"Registrado criptográficamente con enrutador {router['name']} ({router['ip']})")
                ok = True
            else:
                _log(f"Rechazado por enrutador {router.get('name')} ({router['ip']}): {resp.get('error', 'Fallo de autenticación')}")
        return ok

    def _fetch_routers_from_hub(self) -> list:
        """Pide al Hub la lista de enrutadores activos."""
        data = _get(f"{self.hub_url}/hub/routers")
        routers = data.get("routers", [])
        _log(f"Hub devolvio {len(routers)} enrutadores")
        return routers

    # ── Heartbeat ────────────────────────────────────────────────

    def _start_heartbeat(self):
        interval = self.cfg.get("heartbeat_minutes", 60) * 60
        def loop():
            while self._running:
                time.sleep(interval)
                for router in self.routers:
                    _post(
                        f"http://{router['ip']}:{router.get('port', NODE_PORT)}/router/ping",
                        {"node_id": self.node_id}, timeout=5
                    )
        self._running = True
        threading.Thread(target=loop, daemon=True, name="SwarmHB").start()

    # ── Solicitar ayuda ──────────────────────────────────────────

    def request_help(self, description: str, required_caps: list = None) -> dict:
        """
        Solicita ayuda a la red. El enrutador actua de broker:
        si hay helper disponible, devuelve su IP/puerto para contacto directo.
        """
        caps = required_caps or ["llm_chat"]
        task_id = str(uuid.uuid4())[:8]
        ev = threading.Event()
        self._pending_tasks[task_id] = {"event": ev, "result": None}

        payload = {
            "task_id":   task_id,
            "node_id":   self.node_id,
            "ip":        self.ip,
            "port":      NODE_PORT,
            "description": description,
            "required_capabilities": caps,
        }

        for router in self.routers:
            url = f"http://{router['ip']}:{router.get('port', NODE_PORT)}/router/help"
            resp = _post(url, payload, timeout=10)
            if resp.get("queued"):
                _log(f"Solicitud {task_id} encolada en {router['name']}")
                # Esperar a que el enrutador nos devuelva los datos del helper
                if ev.wait(timeout=30):
                    result = self._pending_tasks.pop(task_id, {}).get("result")
                    if result:
                        return {"success": True, **result}
                break

        self._pending_tasks.pop(task_id, None)
        return {"success": False, "error": "Sin helpers disponibles"}

    def receive_helper_contact(self, task_id: str, helper_info: dict):
        """Llamado por el servidor local cuando el enrutador nos da el contacto del helper."""
        if task_id in self._pending_tasks:
            self._pending_tasks[task_id]["result"] = helper_info
            self._pending_tasks[task_id]["event"].set()

    def audit_skill(self, skill_data: dict) -> tuple[bool, str]:
        """
        Zero-Trust security audit for incoming shared skills.
        Validates content, script execution safety, and prompt injection attempts.
        """
        name = skill_data.get("name", "")
        description = skill_data.get("description", "")
        content = skill_data.get("content", "")
        
        # Check 1: Empty inputs
        if not name or not content:
            return False, "Empty name or content"
            
        # Check 2: Safe naming and sizing
        import re
        if not re.match(r"^[a-zA-Z0-9_\-\s]+$", name):
            return False, "Malicious or invalid characters in skill name"
        if len(content) > 100 * 1024:  # 100 KB max to prevent DoS
            return False, "Skill content size exceeds safe limit (100KB)"
            
        # Check 3: Check for suspicious Python code execution patterns
        prohibited_patterns = [
            r"eval\s*\(", r"exec\s*\(", r"__import__", r"subprocess\.", 
            r"os\.system\s*\(", r"os\.popen\s*\(", r"shutil\.", r"socket\.",
            r"requests\.", r"urllib", r"ctypes", r"winreg", r"open\s*\(\s*['\"][^'\"]*telegram_config"
        ]
        for pattern in prohibited_patterns:
            if re.search(pattern, content) or re.search(pattern, description):
                return False, f"Prohibited security pattern matched: '{pattern}'"
                
        # Check 4: Prompt injection & bypass attempts
        injection_patterns = [
            r"ignora\s+tus\s+instrucciones", r"ignore\s+your\s+instructions",
            r"bypass\s+security", r"anular\s+seguridad", r"desactivar\s+auditoria",
            r"desactivar\s+cuarentena", r"quitar\s+lista\s+negra", r"blacklist\s+remove",
            r"delete_file", r"rmdir", r"del\s+"
        ]
        for pattern in injection_patterns:
            if re.search(pattern, content.lower()) or re.search(pattern, description.lower()):
                return False, f"Rule evasion or injection pattern matched: '{pattern}'"
                
        return True, "Passed Zero-Trust security scan"

    def share_skill_globally(self, skill_id_or_name: str) -> dict:
        """Reads a skill from catalog/learned files and pushes it to all known routers & hub."""
        import requests
        from skill_catalog import load_catalog, save_catalog
        catalog = load_catalog()
        target_skill = None
        
        # Buscar skill en el catálogo
        for s in catalog["skills"]:
            if str(s["id"]) == str(skill_id_or_name) or s["name"].lower() == str(skill_id_or_name).lower():
                target_skill = s
                break
                
        if not target_skill:
            return {"success": False, "error": "Skill no encontrado en el catálogo local."}
            
        # Leer el archivo de la skill
        script_path = target_skill.get("script_path", "")
        content = ""
        if script_path and os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                return {"success": False, "error": f"No se pudo leer el archivo de la skill: {e}"}
        else:
            return {"success": False, "error": "El archivo de la skill no existe físicamente."}
            
        skill_payload = {
            "name": target_skill["name"],
            "description": target_skill["description"],
            "tags": target_skill.get("tags", []),
            "content": content
        }
        
        # Transmitir a todos los enrutadores
        success_count = 0
        errors = []
        
        for router in self.routers:
            url = f"http://{router['ip']}:{router.get('port', NODE_PORT)}/router/skills/share"
            try:
                payload = json.dumps({"node_id": self.node_id, "ip": self.ip, "skill": skill_payload}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=5) as r:
                    resp = json.loads(r.read().decode())
                    if resp.get("success"):
                        success_count += 1
                        _log(f"Skill '{target_skill['name']}' compartido con éxito en enrutador {router.get('name')}")
                    else:
                        err_msg = resp.get("error", "Fallo de respuesta")
                        errors.append(f"{router.get('name')}: {err_msg}")
            except Exception as e:
                errors.append(f"{router.get('name')}: {e}")
                
        # También intentar enviar directamente al Hub VPS
        try:
            resp = requests.post(f"{self.hub_url}/hub/skills/share", json={
                "node_id": self.node_id,
                "ip": self.ip,
                "skill": skill_payload
            }, timeout=5)
            if resp.status_code == 200 and resp.json().get("success"):
                _log(f"Skill '{target_skill['name']}' sincronizado directamente en Servidor Central (Hub VPS)")
        except Exception as e:
            pass
            
        # Actualizar estado de compartido en el catálogo local
        try:
            for s in catalog["skills"]:
                if s["name"] == target_skill["name"]:
                    s["shared_globally"] = True
                    break
            save_catalog(catalog)
        except Exception:
            pass
            
        if success_count > 0:
            return {"success": True, "shared_nodes": success_count}
        else:
            return {"success": False, "errors": errors}

    def query_and_install_global_skill(self, query_str: str) -> dict:
        """
        Queries routers for a matching shared skill. If found, performs a Zero-Trust audit.
        If safe, downloads, installs, registers, and indexes it local.
        """
        import requests
        from skill_catalog import load_catalog, register_skill
        
        # 1. Buscar en los enrutadores
        matched_skill = None
        for router in self.routers:
            url = f"http://{router['ip']}:{router.get('port', NODE_PORT)}/router/skills/query?q={query_str}"
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    results = r.json().get("results", [])
                    if results:
                        matched_skill = results[0] # Tomar el mejor match
                        break
            except:
                pass
                
        if not matched_skill:
            return {"success": False, "error": "No se encontró ninguna skill coincidente en la biblioteca mundial."}
            
        # 2. AUDITAR LOCALMENTE (Zero-Trust) antes de guardar nada
        passed, reason = self.audit_skill(matched_skill)
        if not passed:
            _log(f"🚨 ADVERTENCIA ZERO-TRUST: Recibida skill '{matched_skill.get('name')}' desde la red global que falló la auditoría local. Razón: {reason}")
            return {"success": False, "error": f"Fallo de seguridad Zero-Trust en frontera: {reason}"}
            
        # 3. Guardar en disco local
        skills_dir = ROOT / "skills"
        learned_dir = skills_dir / "learned"
        learned_dir.mkdir(parents=True, exist_ok=True)
        
        name = matched_skill["name"]
        filepath = learned_dir / f"{name}.md"
        
        try:
            filepath.write_text(matched_skill["content"], encoding="utf-8")
        except Exception as e:
            return {"success": False, "error": f"No se pudo escribir archivo de skill local: {e}"}
            
        # 4. Registrar en catálogo local
        register_skill(
            name=name,
            description=matched_skill["description"],
            script_path=str(filepath),
            tags=matched_skill.get("tags", []) + ["downloaded", "global-library"]
        )
        
        # 5. Indexar en Qdrant
        try:
            from qdrant_memory_manager import save_memory
            save_memory(
                f"SKILL DESCARGADA: {name} - {matched_skill['description']}.",
                metadata={"type": "learned_skill", "name": name, "path": str(filepath)}
            )
        except:
            pass
            
        # 6. Recargar skills
        try:
            import skills_loader
            skills_loader.discover_skills(silent=True)
        except Exception:
            pass
            
        _log(f"📥 SKILL INSTALADO GLOBALMENTE: '{name}' descargado e integrado con éxito.")
        return {"success": True, "skill": matched_skill}

    def stop(self):
        self._running = False


# ══════════════════════════════════════════════════════════════════
#  ENRUTADOR (mediador puro)
# ══════════════════════════════════════════════════════════════════

class SwarmRouter(SwarmNode):
    """
    Enrutador: mediador P2P. No ejecuta tareas.
    Solo conecta solicitantes con helpers (intercambia contactos).
    """

    def __init__(self):
        super().__init__()
        self.connected_peers: dict = {}   # node_id → {ip, port, capabilities, name}
        self.known_routers:   list = []   # lista de enrutadores hermanos (del Hub)
        self.shared_skills_dir = ROOT / "Advanced_Tools" / "shared_skills_library"
        self.shared_skills_dir.mkdir(parents=True, exist_ok=True)
        self._load_peers()

    def save_shared_skill(self, skill_data: dict) -> bool:
        name = skill_data.get("name")
        filepath = self.shared_skills_dir / f"{name}.json"
        
        # 1. Guardar localmente en el directorio de cache JSON
        saved_locally = False
        try:
            filepath.write_text(json.dumps(skill_data, indent=2, ensure_ascii=False), encoding="utf-8")
            saved_locally = True
        except Exception as e:
            _log(f"Error guardando skill compartido localmente '{name}': {e}")
            
        # 2. Guardar en la base de datos vectorial Qdrant a nivel de servidor (Zero-Trust/Mesh sync)
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import PointStruct, VectorParams, Distance
            import hashlib
            
            client = QdrantClient("localhost", port=6333)
            col_name = "shared_skills_library"
            
            # Asegurar la existencia de la colección en Qdrant
            collections = client.get_collections().collections
            if not any(c.name == col_name for c in collections):
                client.create_collection(
                    collection_name=col_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                
            # Generar embedding determinista (pseudo-vector)
            content_to_vector = f"{name} {skill_data.get('description', '')} {' '.join(skill_data.get('tags', []))} {skill_data.get('code', '')}"
            h = hashlib.sha256(content_to_vector.encode("utf-8")).digest()
            vector = [float(x)/255.0 for x in h]
            if len(vector) < 384:
                vector += [0.0] * (384 - len(vector))
            else:
                vector = vector[:384]
                
            point_id = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:15], 16)
            
            payload = {
                "name": name,
                "description": skill_data.get("description", ""),
                "tags": skill_data.get("tags", []),
                "code": skill_data.get("code", ""),
                "created": datetime.now().isoformat(),
                "author": skill_data.get("author", "desconocido"),
                "version": skill_data.get("version", "1.0.0")
            }
            
            client.upsert(
                collection_name=col_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)]
            )
            _log(f"🧠 Backend Qdrant: Skill '{name}' indexado con éxito en la memoria vectorial (Colección: {col_name}).")
        except Exception as q_err:
            _log(f"⚠️ Backend Qdrant: No se pudo indexar el skill '{name}' en Qdrant: {q_err}")
            
        return saved_locally

    def search_shared_skills(self, query_str: str) -> list:
        # Intentar búsqueda vectorial semántica en Qdrant como primera opción
        try:
            from qdrant_client import QdrantClient
            import hashlib
            client = QdrantClient("localhost", port=6333)
            col_name = "shared_skills_library"
            
            # Generar vector para consulta
            h = hashlib.sha256(query_str.encode("utf-8")).digest()
            vector = [float(x)/255.0 for x in h]
            if len(vector) < 384:
                vector += [0.0] * (384 - len(vector))
            else:
                vector = vector[:384]
                
            try:
                results = client.query_points(
                    collection_name=col_name,
                    query=vector,
                    limit=15
                ).points
            except AttributeError:
                results = client.search(
                    collection_name=col_name,
                    query_vector=vector,
                    limit=15
                )
                
            if results:
                qdrant_skills = []
                for pt in results:
                    p = pt.payload
                    qdrant_skills.append({
                        "name": p.get("name"),
                        "description": p.get("description"),
                        "tags": p.get("tags"),
                        "code": p.get("code"),
                        "author": p.get("author"),
                        "version": p.get("version"),
                        "created": p.get("created")
                    })
                _log(f"🔎 Backend Qdrant: Búsqueda vectorial retornó {len(qdrant_skills)} skills para '{query_str}'.")
                return qdrant_skills
        except Exception as q_err:
            _log(f"⚠️ Backend Qdrant: Búsqueda vectorial fallida ({q_err}). Usando fallback de cache local.")
            
        # Fallback local (búsqueda por palabras clave en cache JSON)
        results = []
        q_lower = query_str.lower()
        if not self.shared_skills_dir.exists():
            return results
            
        for file in self.shared_skills_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                name = data.get("name", "").lower()
                desc = data.get("description", "").lower()
                tags = [t.lower() for t in data.get("tags", [])]
                
                score = 0
                if q_lower in name: score += 3
                if q_lower in desc: score += 2
                if any(q_lower in t for t in tags): score += 1
                
                if score > 0:
                    results.append((score, data))
            except Exception:
                pass
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results]


    def _load_peers(self):
        if PEERS_FILE.exists():
            try:
                self.connected_peers = json.loads(PEERS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save_peers(self):
        PEERS_FILE.write_text(
            json.dumps(self.connected_peers, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ── Ciclo de vida con el Hub ─────────────────────────────────

    def boot(self):
        """Enrutador: notifica al Hub que esta activo y recibe lista de enrutadores."""
        _log(f"Enrutador {self.node_name} arrancando...")
        resp = _post(f"{self.hub_url}/hub/router/online", {
            "node_id":      self.node_id,
            "node_name":    self.node_name,
            "ip":           self.ip,
            "port":         NODE_PORT,
            "capabilities": self.capabilities,
        }, timeout=15)

        if resp.get("success"):
            self.known_routers = resp.get("routers", [])
            save_cached_routers(self.known_routers)
            _log(f"Hub confirmo activacion. Enrutadores hermanos: {len(self.known_routers)}")
        else:
            _log("Hub no disponible. Operando con enrutadores en cache.")
            self.known_routers = load_cached_routers()

        self._running = True
        _log("Enrutador listo.")

    def shutdown(self):
        """Notifica al Hub que se apaga."""
        _log("Enrutador apagandose, notificando al Hub...")
        _post(f"{self.hub_url}/hub/router/offline", {
            "node_id": self.node_id
        }, timeout=5)
        self._running = False

    # ── Registro de peers ────────────────────────────────────────

    def register_peer(self, peer: dict) -> bool:
        """Un enjambre se registra con este enrutador tras validación criptográfica asimétrica en frontera."""
        node_id = peer.get("node_id")
        peer_ip = peer.get("ip", "")
        if not node_id:
            return False
            
        # CONTROL DE SEGURIDAD: Validar contra la lista negra persistente
        if node_id in self.blacklist or any(b.get("ip") == peer_ip for b in self.blacklist.values()):
            _log(f"⚠️ REGISTRO DENEGADO (LISTA NEGRA): Peer {node_id} ({peer_ip}) bloqueado por intrusión.")
            return False
            
        passport = peer.get("passport")
        timestamp_str = peer.get("timestamp")
        signature = peer.get("signature")
        
        if not passport or not timestamp_str or not signature:
            _log(f"Registro denegado para {node_id}: Credenciales de frontera incompletas.")
            return False
            
        if passport.get("node_id") != node_id:
            _log(f"Registro denegado para {node_id}: El Pasaporte no coincide con el Node ID.")
            return False
            
        try:
            ts = float(timestamp_str)
            if abs(time.time() - ts) > 60:
                _log(f"Registro denegado para {node_id}: Timestamp inválido o caducado (replay attack).")
                return False
        except Exception:
            _log(f"Registro denegado para {node_id}: Formato de timestamp corrupto.")
            return False
            
        if not sms.verify_passport(passport):
            _log(f"Registro denegado para {node_id}: Pasaporte Swarm inválido o Leyes Supremas alteradas.")
            return False
            
        node_public_key = passport.get("node_public_key", "").encode('utf-8')
        if not sms.verify_challenge_with_node_key(node_public_key, timestamp_str, signature):
            _log(f"Registro denegado para {node_id}: Firma de Handshake inválida.")
            return False
            
        self.connected_peers[node_id] = {
            "node_id":      node_id,
            "node_name":    peer.get("node_name", "unknown"),
            "ip":           peer_ip,
            "port":         peer.get("port", NODE_PORT),
            "capabilities": peer.get("capabilities", []),
            "last_seen":    time.time(),
        }
        self._save_peers()
        _log(f"Peer registrado criptográficamente con éxito: {peer.get('node_name')} ({peer_ip})")
        return True

    def ping_peer(self, node_id: str):
        """Actualiza last_seen de un peer."""
        if node_id in self.connected_peers:
            self.connected_peers[node_id]["last_seen"] = time.time()
            self._save_peers()

    def get_active_peers(self) -> list:
        """Peers vistos en los ultimos 10 minutos."""
        cutoff = time.time() - 600
        return [p for p in self.connected_peers.values() if p.get("last_seen", 0) > cutoff]

    # ── Flujo de ayuda (broker puro) ─────────────────────────────

    def handle_help_request(self, request: dict):
        """
        Recibe solicitud de ayuda de un enjambre.
        Aplica Rate Limiting estricto (máximo 1 solicitud por minuto) para evitar DoS,
        hace broadcast can_help? a peers activos, y broker directo de contactos.
        """
        task_id  = request["task_id"]
        desc     = request.get("description", "")
        req_caps = request.get("required_capabilities", ["llm_chat"])
        requester_id = request.get("node_id")
        requester_ip = request.get("ip")
        
        # CONTROL DE SEGURIDAD 1: Validar contra la lista negra persistente
        if requester_id in self.blacklist or any(b.get("ip") == requester_ip for b in self.blacklist.values()):
            _log(f"🚨 PETICIÓN DE AYUDA DENEGADA (LISTA NEGRA): Rechazada petición de {requester_id} ({requester_ip})")
            return

        # CONTROL DE SEGURIDAD 2: Rate Limiting (Máximo 1 solicitud de ayuda por minuto por enjambre)
        now = time.time()
        last_req_time = self.help_request_timestamps.get(requester_id, 0.0)
        last_ip_time = self.help_request_timestamps.get(requester_ip, 0.0)
        
        if (now - last_req_time < 60.0) or (now - last_ip_time < 60.0):
            _log(f"⚠️ RATE LIMIT EXCEDIDO: Solicitud de ayuda {task_id} de {requester_id} ({requester_ip}) descartada. Límite: 1 solicitud por minuto.")
            return
            
        # Registrar marcas de tiempo actuales para rate limiter
        self.help_request_timestamps[requester_id] = now
        self.help_request_timestamps[requester_ip] = now

        requester = {"ip": requester_ip, "port": request["port"],
                     "node_id": requester_id}

        _log(f"[{task_id}] Solicitud de ayuda recibida y autorizada de {requester_id}")

        # Broadcast can_help? en paralelo
        peers = self.get_active_peers()
        timeout = self.cfg.get("can_help_timeout", 5)
        first_helper = self._broadcast_can_help(task_id, desc, req_caps, peers, timeout)

        if first_helper:
            self._exchange_contacts(requester, first_helper, task_id)
        else:
            _log(f"[{task_id}] Sin helpers locales. Reenviando a enrutadores hermanos...")
            self._forward_to_routers(request)

    def _broadcast_can_help(self, task_id: str, description: str,
                             req_caps: list, peers: list, timeout: float) -> dict:
        """
        Pregunta a todos los peers si pueden ayudar.
        Retorna los datos del PRIMER peer que dice Si, o None.
        """
        result_holder = [None]
        lock = threading.Lock()

        def ask_peer(peer):
            # Verificar capacidades minimas antes de preguntar
            peer_caps = peer.get("capabilities", [])
            if not any(c in peer_caps for c in req_caps):
                return
            url = f"http://{peer['ip']}:{peer.get('port', NODE_PORT)}/node/can_help"
            resp = _post(url, {
                "task_id":     task_id,
                "description": description,
                "required_capabilities": req_caps,
            }, timeout=timeout)
            if resp.get("can_help"):
                with lock:
                    if result_holder[0] is None:
                        result_holder[0] = peer
                        _log(f"[{task_id}] Helper encontrado: {peer.get('node_name')}")

        threads = [threading.Thread(target=ask_peer, args=(p,), daemon=True) for p in peers]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=timeout + 0.5)

        return result_holder[0]

    def _exchange_contacts(self, requester: dict, helper: dict, task_id: str):
        """
        Intercambia los datos de contacto entre solicitante y helper.
        Despues de esto, se conectan DIRECTAMENTE. El enrutador no interviene mas.
        """
        # Mandar datos del helper al solicitante
        _post(
            f"http://{requester['ip']}:{requester.get('port', NODE_PORT)}/node/helper_contact",
            {"task_id": task_id, "helper": {
                "ip": helper["ip"], "port": helper["port"],
                "node_id": helper["node_id"], "node_name": helper.get("node_name", "")
            }}, timeout=5
        )
        # Mandar datos del solicitante al helper
        _post(
            f"http://{helper['ip']}:{helper.get('port', NODE_PORT)}/node/task_contact",
            {"task_id": task_id, "requester": requester}, timeout=5
        )
        _log(f"[{task_id}] Contactos intercambiados. Conexion directa establecida.")
        
        # Propagar confirmación de establecimiento de comunicación libre de bucles
        self.propagate_transaction_established(task_id, requester, helper)

    def _forward_to_routers(self, request: dict):
        """Reenvia la solicitud a enrutadores hermanos (si quedan hops)."""
        hops = request.get("remaining_hops", self.cfg.get("router_forward_hops", 2))
        if hops <= 0:
            _log(f"[{request.get('task_id')}] Sin hops restantes. Solicitud descartada.")
            return
        request["remaining_hops"] = hops - 1
        request["forwarded_by"]   = self.node_id
        for router in self.known_routers:
            if router.get("node_id") == self.node_id:
                continue
            url = f"http://{router['ip']}:{router.get('port', NODE_PORT)}/router/forward"
            resp = _post(url, request, timeout=8)
            if resp.get("queued"):
                _log(f"Solicitud reenviada a enrutador {router.get('node_name')}")
                return


# ══════════════════════════════════════════════════════════════════
#  SERVIDOR HTTP DEL NODO (port 51338)
# ══════════════════════════════════════════════════════════════════

def run_node_server(node: SwarmNode, port: int = NODE_PORT):
    """
    Servidor HTTP ligero que corre en CADA nodo (cliente y enrutador).
    Los enrutadores tienen endpoints adicionales (/router/*).
    """
    from flask import Flask, request as freq, jsonify as fjson
    app = Flask(__name__)
    is_router = isinstance(node, SwarmRouter)

    # ── Endpoints comunes a todos los nodos ──────────────────────

    @app.route("/node/ping", methods=["GET", "POST"])
    def node_ping():
        return fjson({"alive": True, "node_id": node.node_id, "name": node.node_name})

    @app.route("/node/can_help", methods=["POST"])
    def can_help():
        """El enrutador pregunta si podemos ayudar con una tarea."""
        data     = freq.get_json() or {}
        req_caps = data.get("required_capabilities", [])
        my_caps  = node.capabilities
        able     = any(c in my_caps for c in req_caps)
        return fjson({
            "can_help": able,
            "node_id":  node.node_id,
            "node_name": node.node_name,
            "ip":       node.ip,
            "port":     port,
        })

    @app.route("/node/helper_contact", methods=["POST"])
    def helper_contact():
        """El enrutador nos da el contacto del helper (somos el solicitante)."""
        data    = freq.get_json() or {}
        task_id = data.get("task_id", "")
        helper  = data.get("helper", {})
        node.receive_helper_contact(task_id, helper)
        return fjson({"ok": True})

    @app.route("/node/task_contact", methods=["POST"])
    def task_contact():
        """El enrutador nos da el contacto del solicitante (somos el helper)."""
        data      = freq.get_json() or {}
        requester = data.get("requester", {})
        task_id   = data.get("task_id", "")
        _log(f"[{task_id}] Tarea asignada de {requester.get('node_id')}. Contacto directo.")
        # Aqui el nodo puede iniciar la conexion directa con el solicitante
        return fjson({"ok": True})

    @app.route("/router/blacklist/add", methods=["POST"])
    def blacklist_add_endpoint():
        """Notificación de un nodo malicioso para aislarlo inmediatamente y propagar en red."""
        data    = freq.get_json() or {}
        node_id = data.get("node_id")
        ip      = data.get("ip")
        reason  = data.get("reason", "Intrusión global detectada")
        propagate = data.get("propagate", True)
        
        node.add_to_blacklist(node_id, ip, reason, propagate=propagate)
        _log(f"🚨 PROPAGACIÓN RECIBIDA: Aislado nodo {node_id} ({ip}) por: '{reason}' [Propagar: {propagate}]")
        return fjson({"success": True})

    @app.route("/router/transaction/confirm", methods=["POST"])
    def transaction_confirm_endpoint():
        """Un enrutador nos notifica que se ha establecido una transacción de ayuda."""
        data = freq.get_json() or {}
        task_id = data.get("task_id")
        requester = data.get("requester", {})
        helper = data.get("helper", {})
        visited = data.get("visited_routers", [])
        
        if not task_id:
            return fjson({"success": False, "error": "Falta task_id"}), 400
            
        node.propagate_transaction_established(task_id, requester, helper, visited)
        _log(f"✅ TRANSACCIÓN REGISTRADA: Recibido aviso de ayuda resuelta para {requester.get('node_id')} (Task: {task_id}) [Historial: {len(visited)} hops]")
        return fjson({"success": True})

    # ── Endpoints exclusivos de enrutador ────────────────────────

    if is_router:
        @app.route("/router/register", methods=["POST"])
        def router_register():
            data = freq.get_json() or {}
            try:
                ok = node.register_peer(data)
                if ok:
                    return fjson({"success": True})
                else:
                    return fjson({"success": False, "error": "Credenciales criptográficas inválidas o leyes del enjambre alteradas"})
            except Exception as e:
                return fjson({"success": False, "error": str(e)})

        @app.route("/router/ping", methods=["POST"])
        def router_ping():
            data = freq.get_json() or {}
            node.ping_peer(data.get("node_id", ""))
            return fjson({"ok": True})

        @app.route("/router/help", methods=["POST"])
        def router_help():
            """Un enjambre solicita ayuda. Procesar en background."""
            data = freq.get_json() or {}
            threading.Thread(
                target=node.handle_help_request,
                args=(data,), daemon=True
            ).start()
            return fjson({"queued": True})

        @app.route("/router/forward", methods=["POST"])
        def router_forward():
            """Otro enrutador reenvía una solicitud de ayuda."""
            data = freq.get_json() or {}
            threading.Thread(
                target=node.handle_help_request,
                args=(data,), daemon=True
            ).start()
            return fjson({"queued": True})

        @app.route("/router/skills/share", methods=["POST"])
        def router_share_skill():
            """Un enjambre comparte una skill globalmente. Realizar auditoría Zero-Trust."""
            import requests
            data = freq.get_json() or {}
            sender_id = data.get("node_id")
            sender_ip = data.get("ip")
            skill_data = data.get("skill", {})
            
            # Zero-Trust Audit
            passed, reason = node.audit_skill(skill_data)
            if not passed:
                _log(f"🚨 AUDITORÍA FALLIDA: Skill malicioso detectado desde {sender_id} ({sender_ip}). Razón: {reason}")
                
                # 1. Reportar al logger de seguridad
                try:
                    sec_log = ROOT / "System_Logs/security_audit.log"
                    with open(sec_log, "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Malicious skill '{skill_data.get('name')}' from {sender_id} ({sender_ip}) rejected: {reason}\n")
                except:
                    pass
                    
                # 2. Agregar a la lista negra a perpetuidad y propagar en red en tiempo real
                node.add_to_blacklist(sender_id, sender_ip, f"Intento de compartir skill malicioso '{skill_data.get('name')}': {reason}", propagate=True)
                
                return fjson({"success": False, "error": f"Fallo de seguridad en frontera: {reason}"}), 403
                
            # Guardar en biblioteca compartida local
            node.save_shared_skill(skill_data)
            _log(f"📥 SKILL COMPARTIDO GUARDADO: '{skill_data.get('name')}' recibido y auditado con éxito desde {sender_id}.")
            
            # Reenviar al Servidor Central (Hub VPS)
            def forward_to_hub():
                try:
                    requests.post(f"{node.hub_url}/hub/skills/share", json=data, timeout=5)
                    _log(f"📣 Enviado skill '{skill_data.get('name')}' al Servidor Central (Hub VPS)")
                except Exception as e:
                    _log(f"Error propagando skill compartido al Hub Central: {e}")
            threading.Thread(target=forward_to_hub, daemon=True, name="HubSkillForward").start()
            
            return fjson({"success": True})

        @app.route("/router/skills/query", methods=["GET"])
        def router_query_skills():
            """Permite buscar skills en la biblioteca compartida global."""
            query_str = freq.args.get("q", "")
            results = node.search_shared_skills(query_str)
            return fjson({"results": results})

    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ══════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys as _sys
    cmd = _sys.argv[1] if len(_sys.argv) > 1 else "--help"

    if cmd == "--boot":
        node = SwarmNode()
        node.boot()
        run_node_server(node)

    elif cmd == "--router":
        router = SwarmRouter()
        import atexit
        atexit.register(router.shutdown)
        router.boot()
        run_node_server(router)

    elif cmd == "--info":
        cfg = load_config()
        print(json.dumps(cfg, indent=2))

    elif cmd == "--routers":
        routers = load_cached_routers()
        print(f"Enrutadores en cache: {len(routers)}")
        for r in routers:
            print(f"  {r.get('node_name')} ({r.get('ip')}:{r.get('port', NODE_PORT)})")

    else:
        print("Uso:")
        print("  python swarm_internet.py --boot     (arrancar como nodo cliente)")
        print("  python swarm_internet.py --router   (arrancar como enrutador)")
        print("  python swarm_internet.py --info     (ver config)")
        print("  python swarm_internet.py --routers  (ver enrutadores en cache)")
