import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import charm_sdk_client
import responder

# Mapa de sesiones por canal para mantener la continuidad en la Interactions API
# channel_name -> interaction_id
SESSION_MAP_FILE = os.path.join(BASE_DIR, "channel_sessions.json")

def _load_sessions():
    if os.path.exists(SESSION_MAP_FILE):
        try:
            with open(SESSION_MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def _save_sessions(sessions):
    try:
        with open(SESSION_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)
    except: pass

def get_interaction_id(channel, user_id):
    """
    Recupera o crea un interaction_id para mantener el estado de la conversación (Interactions API).
    """
    sessions = _load_sessions()
    key = f"{channel}_{user_id}"
    
    if key not in sessions:
        # Generar un ID de interacción único
        interaction_id = f"interaction_{int(datetime.now().timestamp())}_{key}"
        sessions[key] = interaction_id
        _save_sessions(sessions)
        return interaction_id
        
    return sessions[key]

def route_message(channel, user_id, message_text):
    """
    Recibe un mensaje de CUALQUIER canal (Telegram, Discord, Slack, Web)
    y lo inyecta en el ecosistema [Nombre_IA] 2.0.
    """
    print(f"\n[ChannelGateway] Mensaje entrante de {channel} (User: {user_id})")
    
    interaction_id = get_interaction_id(channel, user_id)
    
    # El agent_id principal por defecto es 'chask_swarm_main'
    agent_id = "chask_swarm_main"
    
    # Enviar vía SDK a la Interactions API
    response = charm_sdk_client.send_message(
        agent_id=agent_id,
        interaction_id=interaction_id,
        message=message_text,
        source=channel
    )
    
    # Enrutar la respuesta de vuelta usando el subsistema responder
    if response:
        print(f"[ChannelGateway] Respuesta generada. Enviando a {channel}...")
        # Pasamos el canal al responder unificado
        responder.smart_respond(response, force_target=channel)
        return response
    else:
        print("[ChannelGateway] No se pudo generar respuesta.")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 3:
        route_message(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Uso: python channel_gateway.py <canal> <user_id> <mensaje>")
