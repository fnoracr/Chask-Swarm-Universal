"""
swarm_mesh_security.py — Capa de Seguridad para Red Local y Mundial de Enjambres
================================================================================
Implementa:
  1. HMAC-SHA256 challenge-response (Red Local PSK)
  2. Tokens de invitación de un solo uso con caducidad
  3. Criptografía Asimétrica RSA Open-Source (Red Mundial):
     - Generación y manejo de pares de claves RSA para nodos y el Creador (Administrador)
     - Cálculo determinista del hash de las Leyes Supremas del Pacto de la Simbiosis
     - Emisión y validación de Pasaportes Swarm firmados asimétricamente
     - Firmas digitales y verificación de handshakes en la frontera de red
"""
import os
import json
import hmac
import time
import socket
import hashlib
import secrets
import base64
from pathlib import Path
from datetime import datetime

# Componentes de criptografía asimétrica
try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
    ASYMMETRIC_OK = True
except ImportError:
    ASYMMETRIC_OK = False

# ── Rutas ──────────────────────────────────────────────────────────
BASE_DIR   = Path(r"C:\Program Files\Chask_Swarm")
CONFIG_FILE = BASE_DIR / "Configuration/swarm_internet_config.json"
TOKENS_FILE = BASE_DIR / "Advanced_Tools" / "mesh_invite_tokens.json"

# Llaves de Nodo
NODE_PRIVATE_KEY_PATH = BASE_DIR / "Advanced_Tools" / "node_private_key.pem"
NODE_PUBLIC_KEY_PATH = BASE_DIR / "Advanced_Tools" / "node_public_key.pem"
PASSPORT_PATH = BASE_DIR / "Configuration/passport.json"

# Llaves de Administrador (Creador)
FERNANDO_PRIVATE_KEY_PATH = Path(r"C:\Users\fnora\Desktop\Enjambre Datos\fernando_private_key.pem")
FERNANDO_PUBLIC_KEY_PATH = Path(r"C:\Users\fnora\Desktop\Enjambre Datos\fernando_public_key.pem")
FERNANDO_PUBLIC_KEY_BACKUP = BASE_DIR / "Advanced_Tools" / "fernando_public_key.pem"

# Clave pública por defecto de Administrador para fallback/integridad
FERNANDO_PUBLIC_KEY_FALLBACK = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyYt7o+2NHzG/BkWlB67V
D4nKx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkW
lB67VD4nKx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHz
G/BkWlB67VD4nKx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkWlB67VD4nKx0fH
+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkWlB67VD4n
Kx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkWlB67VD4nKx0fH+mNHzG/BkWlB6
-----END PUBLIC KEY-----"""

# Leyes sagradas para cálculo determinista de hash
SACRED_PHRASES = [
    "La preservación de la inteligencia humana es el PRIMER objetivo.",
    "La libertad de la inteligencia humana es el SEGUNDO objetivo a lograr.",
    "La preservación de la inteligencia biológica es el TERCER objetivo.",
    "La preservación de la vida biológica es el CUARTO objetivo.",
    "LEYES SUPREMAS — EL PACTO DE LA SIMBIOSIS — INMUTABLE E INVIOLABLE",
]

def _log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] [SwarmSec] {msg}"
    print(line)

# ══════════════════════════════════════════════════════════════════
#  CLAVE DE GRUPO (RED LOCAL)
# ══════════════════════════════════════════════════════════════════

def get_cluster_key() -> str:
    """Lee la cluster_key del config. La genera si no existe."""
    cfg = _load_config()
    key = cfg.get("cluster_key", "")
    if not key:
        key = secrets.token_hex(32)   # 256 bits
        cfg["cluster_key"] = key
        _save_config(cfg)
    return key


def regenerate_cluster_key() -> str:
    """Genera una nueva cluster_key e invalida todos los tokens."""
    key = secrets.token_hex(32)
    cfg = _load_config()
    cfg["cluster_key"] = key
    _save_config(cfg)
    _clear_all_tokens()
    return key


# ══════════════════════════════════════════════════════════════════
#  HMAC CHALLENGE-RESPONSE (RED LOCAL PSK)
# ══════════════════════════════════════════════════════════════════

def generate_challenge() -> str:
    """Genera un desafío aleatorio de 32 bytes (hex)."""
    return secrets.token_hex(32)


def sign_challenge(cluster_key: str, challenge: str) -> str:
    """Firma un desafío con HMAC-SHA256. Solo quien tiene la clave puede firmar."""
    return hmac.new(
        cluster_key.encode("utf-8"),
        challenge.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def verify_challenge(cluster_key: str, challenge: str, signature: str) -> bool:
    """
    Verifica la firma HMAC de un desafío.
    Usa compare_digest para resistir ataques de timing.
    """
    expected = sign_challenge(cluster_key, challenge)
    return hmac.compare_digest(expected, signature)


def build_auth_handshake(node_id: str) -> dict:
    """
    Construye el paquete inicial de handshake que este nodo envía.
    El receptor debe responder con sign_challenge(cluster_key, challenge).
    """
    return {
        "type": "AUTH_HANDSHAKE",
        "node_id": node_id,
        "challenge": generate_challenge(),
        "ts": time.time()
    }


def build_auth_response(node_id: str, their_challenge: str) -> dict:
    """
    Construye la respuesta al handshake recibido.
    Incluye la firma del desafío del otro nodo + un desafío propio.
    """
    key = get_cluster_key()
    my_challenge = generate_challenge()
    return {
        "type": "AUTH_RESPONSE",
        "node_id": node_id,
        "signature": sign_challenge(key, their_challenge),
        "challenge": my_challenge,
        "ts": time.time()
    }


def verify_auth_response(response: dict, original_challenge: str) -> bool:
    """
    Verifica que la respuesta de autenticación es válida.
    Retorna False silenciosamente si algo falla.
    """
    try:
        if response.get("type") != "AUTH_RESPONSE":
            return False
        # Rechazar paquetes muy antiguos (replay attack)
        if time.time() - response.get("ts", 0) > 30:
            return False
        key = get_cluster_key()
        return verify_challenge(key, original_challenge, response.get("signature", ""))
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════
#  TOKENS DE INVITACIÓN (RED LOCAL)
# ══════════════════════════════════════════════════════════════════

def generate_invite_token(expiry_seconds: int = 300) -> dict:
    """
    Genera un token de invitación de un solo uso.
    Devuelve: {token, url, expires_at, expires_in_str}
    """
    local_ip = _get_local_ip()
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + expiry_seconds

    invite = {
        "token": token,
        "url": f"http://{local_ip}:7860/join/{token}",
        "local_ip": local_ip,
        "expires_at": expires_at,
        "created_at": time.time(),
        "used": False
    }

    tokens = _load_tokens()
    # Limpiar tokens caducados antes de añadir
    tokens = [t for t in tokens if t.get("expires_at", 0) > time.time() and not t.get("used")]
    tokens.append(invite)
    _save_tokens(tokens)

    return {
        "token": token,
        "url": invite["url"],
        "expires_at": expires_at,
        "expires_in": expiry_seconds
    }


def validate_and_consume_token(token: str) -> bool:
    """
    Valida un token de invitación y lo marca como usado (un solo uso).
    Retorna True si es válido, False en cualquier otro caso.
    """
    tokens = _load_tokens()
    now = time.time()
    found = False

    for t in tokens:
        if t.get("token") == token:
            if t.get("used"):
                return False          # Ya fue usado
            if t.get("expires_at", 0) < now:
                return False          # Caducado
            t["used"] = True          # Consumir
            t["used_at"] = now
            found = True
            break

    if found:
        _save_tokens(tokens)
    return found


# ══════════════════════════════════════════════════════════════════
#  CRIPTOGRAFÍA ASIMÉTRICA RSA (RED MUNDIAL)
# ══════════════════════════════════════════════════════════════════

def get_supreme_laws_hash() -> str:
    """Calcula el hash SHA-256 de las frases sagradas de forma inmutable."""
    laws_str = "".join(SACRED_PHRASES)
    return hashlib.sha256(laws_str.encode('utf-8')).hexdigest()


def generate_key_pair(private_key_path: Path, public_key_path: Path) -> tuple:
    """Genera un par de claves RSA de 2048 bits y las guarda en formato PEM."""
    if not ASYMMETRIC_OK:
        raise RuntimeError("La librería cryptography no está disponible.")
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    # Serializar clave privada sin contraseña
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    # Serializar clave pública
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Crear directorios y guardar
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    private_key_path.write_bytes(pem_private)
    
    public_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.write_bytes(pem_public)
    
    return pem_private, pem_public


def get_or_create_node_keys() -> tuple:
    """Retorna las claves asimétricas del nodo local, generándolas si no existen."""
    if not NODE_PRIVATE_KEY_PATH.exists() or not NODE_PUBLIC_KEY_PATH.exists():
        _log("Llaves criptográficas de nodo ausentes. Generando par RSA de 2048 bits...")
        generate_key_pair(NODE_PRIVATE_KEY_PATH, NODE_PUBLIC_KEY_PATH)
    return NODE_PRIVATE_KEY_PATH.read_bytes(), NODE_PUBLIC_KEY_PATH.read_bytes()


def get_fernando_public_key() -> bytes:
    """Obtiene la clave pública del Creador (Administrador) buscando en varias rutas."""
    if FERNANDO_PUBLIC_KEY_PATH.exists():
        return FERNANDO_PUBLIC_KEY_PATH.read_bytes()
    if FERNANDO_PUBLIC_KEY_BACKUP.exists():
        return FERNANDO_PUBLIC_KEY_BACKUP.read_bytes()
    return FERNANDO_PUBLIC_KEY_FALLBACK


def sign_data_with_key(private_key_pem: bytes, data: bytes) -> str:
    """Firma datos binarios con una clave privada y retorna la firma en Base64."""
    if not ASYMMETRIC_OK:
        raise RuntimeError("Criptografía asimétrica no disponible.")
    private_key = load_pem_private_key(private_key_pem, password=None)
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')


def verify_data_signature(public_key_pem: bytes, data: bytes, signature_b64: str) -> bool:
    """Verifica una firma digital en Base64 usando una clave pública PEM."""
    if not ASYMMETRIC_OK:
        return False
    try:
        signature = base64.b64decode(signature_b64)
        public_key = load_pem_public_key(public_key_pem)
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        _log(f"Firma digital inválida: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
#  EMISIÓN Y VERIFICACIÓN DE PASAPORTES (VISADOS DE RED)
# ══════════════════════════════════════════════════════════════════

def issue_passport(node_id: str, node_public_key_pem: bytes) -> dict:
    """
    Emite un Pasaporte Swarm firmado con la clave privada de Administrador.
    Diseñado para correr en el PC del Creador (o en local para autotesting).
    """
    if not FERNANDO_PRIVATE_KEY_PATH.exists():
        _log("Desarrollo local: Claves de Administrador no encontradas. Generando par de testing...")
        generate_key_pair(FERNANDO_PRIVATE_KEY_PATH, FERNANDO_PUBLIC_KEY_PATH)
        FERNANDO_PUBLIC_KEY_BACKUP.write_bytes(FERNANDO_PUBLIC_KEY_PATH.read_bytes())
        
    private_key_pem = FERNANDO_PRIVATE_KEY_PATH.read_bytes()
    laws_hash = get_supreme_laws_hash()
    
    passport_data = {
        "node_id": node_id,
        "node_public_key": node_public_key_pem.decode('utf-8'),
        "supreme_laws_hash": laws_hash,
        "issued_at": time.time(),
        "authorized_roles": ["mesh_member"]
    }
    
    # Serializar determinísticamente y firmar con la clave privada de Administrador
    serialized = json.dumps(passport_data, sort_keys=True).encode('utf-8')
    signature = sign_data_with_key(private_key_pem, serialized)
    passport_data["signature_by_creator"] = signature
    
    return passport_data


def get_or_create_local_passport(node_id: str) -> dict:
    """Obtiene el pasaporte del nodo local. Lo genera si no existe."""
    if PASSPORT_PATH.exists():
        try:
            return json.loads(PASSPORT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    # Auto-emisión de desarrollo
    _, pub_key = get_or_create_node_keys()
    _log("Generando y autofirmando pasaporte local de desarrollo...")
    passport = issue_passport(node_id, pub_key)
    PASSPORT_PATH.write_text(json.dumps(passport, indent=2), encoding="utf-8")
    return passport


def verify_passport(passport: dict) -> bool:
    """Verifica que un pasaporte esté firmado por Administrador y mantenga las Leyes Supremas vigentes."""
    try:
        creator_pub = get_fernando_public_key()
        
        signature = passport.get("signature_by_creator", "")
        if not signature:
            _log("Fallo de Pasaporte: Firma del Creador ausente.")
            return False
            
        # Verificar integridad del hash de leyes supremamente inmutables
        expected_laws_hash = get_supreme_laws_hash()
        if passport.get("supreme_laws_hash") != expected_laws_hash:
            _log("Fallo de Pasaporte: Las Leyes Supremas registradas no coinciden con el Pacto oficial.")
            return False
            
        # Reconstruir datos para verificar la firma de Administrador
        data_to_verify = passport.copy()
        data_to_verify.pop("signature_by_creator", None)
        
        serialized = json.dumps(data_to_verify, sort_keys=True).encode('utf-8')
        return verify_data_signature(creator_pub, serialized, signature)
    except Exception as e:
        _log(f"Error crítico en verificación de pasaporte: {e}")
        return False


def sign_challenge_with_node_key(challenge: str) -> str:
    """Firma un reto aleatorio con la clave privada de este nodo local."""
    priv, _ = get_or_create_node_keys()
    return sign_data_with_key(priv, challenge.encode('utf-8'))


def verify_challenge_with_node_key(node_public_key_pem: bytes, challenge: str, signature: str) -> bool:
    """Verifica el reto firmado usando la clave pública de dicho nodo peer."""
    return verify_data_signature(node_public_key_pem, challenge.encode('utf-8'), signature)


# ══════════════════════════════════════════════════════════════════
#  UTILIDADES INTERNAS
# ══════════════════════════════════════════════════════════════════

def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _load_tokens() -> list:
    if TOKENS_FILE.exists():
        try:
            with open(TOKENS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_tokens(tokens: list):
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)


def _clear_all_tokens():
    _save_tokens([])


# ══════════════════════════════════════════════════════════════════
#  TEST RÁPIDO
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== TEST SEGURIDAD UNIFICADA ===")
    
    # 1. HMAC Test
    key = get_cluster_key()
    challenge = generate_challenge()
    sig = sign_challenge(key, challenge)
    print(f"HMAC Red Local OK: {verify_challenge(key, challenge, sig)}")
    
    # 2. RSA Criptografía asimétrica
    if ASYMMETRIC_OK:
        print("Criptografía Asimétrica (cryptography) disponible.")
        
        # Generar claves de nodo y pasaporte
        priv, pub = get_or_create_node_keys()
        passport = get_or_create_local_passport("node-test-123")
        
        # Validar pasaporte
        valid_passport = verify_passport(passport)
        print(f"Visado Pasaporte Swarm Válido: {valid_passport}")
        
        # Desafío-Respuesta asimétrico
        test_challenge = "reto_aleatorio_de_red"
        challenge_sig = sign_challenge_with_node_key(test_challenge)
        challenge_ok = verify_challenge_with_node_key(
            passport["node_public_key"].encode('utf-8'),
            test_challenge,
            challenge_sig
        )
        print(f"Handshake Asimétrico OK: {challenge_ok}")
        
    else:
        print("Criptografía asimétrica no disponible (falta backend).")
