import os
import sys
import json
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Simulamos el endpoint local de la Interactions API del [Nombre_IA] Desktop App
CHARM_LOCAL_PORT = 11435
CHARM_API_BASE = f"http://localhost:{CHARM_LOCAL_PORT}/api/v1"

# Archivo de estado para simular persistencia de Managed Agents si el puerto real no responde
SDK_STATE_FILE = os.path.join(BASE_DIR, "charm_sdk_state.json")

def _load_state():
    if os.path.exists(SDK_STATE_FILE):
        try:
            with open(SDK_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"current_model": "gemini-2.5-pro", "active_agents": {}}

def _save_state(state):
    try:
        with open(SDK_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except: pass

def set_agent_model(agent_id, new_model):
    """
    Cambia dinámicamente el modelo subyacente de un Managed Agent o de la aplicación de escritorio,
    sin perder el contexto (gracias a Interactions API).
    """
    print(f"[[Nombre_IA]SDK] Intentando cambiar el modelo de '{agent_id}' a '{new_model}'...")
    
    # 1. Intento por HTTP (API Real de [Nombre_IA] 2.0)
    try:
        response = requests.patch(
            f"{CHARM_API_BASE}/agents/{agent_id}/model",
            json={"model": new_model},
            timeout=2
        )
        if response.status_code == 200:
            print(f"[[Nombre_IA]SDK] Modelo cambiado con éxito vía Interactions API.")
            return True
    except requests.exceptions.RequestException:
        print("[[Nombre_IA]SDK] API local no disponible. Operando en modo simulación SDK...")

    # 2. Simulación de Estado
    state = _load_state()
    state["current_model"] = new_model
    _save_state(state)
    print(f"[[Nombre_IA]SDK] [Mock] Modelo de '{agent_id}' actualizado a '{new_model}' en state file.")
    return True

def send_message(agent_id, interaction_id, message, source="unknown"):
    """
    Envía un mensaje a la Interactions API, manteniendo el historial asociado al interaction_id.
    """
    print(f"[[Nombre_IA]SDK] Enviando mensaje a {agent_id} (ID: {interaction_id}) desde {source}...")
    
    # 1. Intento por HTTP
    try:
        response = requests.post(
            f"{CHARM_API_BASE}/interactions",
            json={
                "agent_id": agent_id,
                "interaction_id": interaction_id,
                "messages": [{"role": "user", "content": message}],
                "metadata": {"source": source}
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("reply", "")
    except requests.exceptions.RequestException:
        print("[[Nombre_IA]SDK] API local no disponible. Cayendo al router por defecto (legacy)...")

    # 2. Fallback: Si la API nativa no contesta, usamos el router antiguo pero 
    # respetando el modelo que el SDK tenga configurado en state.
    state = _load_state()
    forced_model = state.get("current_model")
    
    import llm_router
    # Modificamos temporalmente el config de memoria para forzar este modelo
    cfg = llm_router.load_config()
    target_provider = None
    
    # Buscar el proveedor que tenga ese modelo o uno similar
    for pv in cfg.get("providers", []):
        if forced_model in pv.get("model", "") or forced_model in pv.get("fallback_models", []):
            target_provider = pv
            break
            
    if target_provider:
        print(f"[[Nombre_IA]SDK] Enrutando vía fallback legacy hacia {target_provider['name']} ({forced_model})")
        res = llm_router.call_provider(target_provider, message, "Eres el agente principal. Continúa la conversación.")
        return res
    else:
        # Enrutado normal
        result = llm_router.route(message, source=source)
        return result.get("response", "")

if __name__ == "__main__":
    # Prueba CLI rápida
    if len(sys.argv) > 1:
        if sys.argv[1] == "set_model" and len(sys.argv) > 3:
            set_agent_model(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "send" and len(sys.argv) > 4:
            reply = send_message(sys.argv[2], sys.argv[3], sys.argv[4])
            print(f"Respuesta: {reply}")
