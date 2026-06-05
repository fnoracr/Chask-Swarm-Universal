import os
import sys
import json
import time
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import llm_router
import responder

# Orquestador Local: Toma el mando si [Nombre_IA] cede el control o cae.
ORCHESTRATOR_MODEL = "qwen2.5-coder:7b"
HANDOFF_FILE = os.path.join(BASE_DIR, "..", "handoff_context.json")

def read_handoff_context():
    if os.path.exists(HANDOFF_FILE):
        try:
            with open(HANDOFF_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[LocalOrchestrator] Error leyendo handoff context: {e}")
    return None

def clear_handoff_context():
    if os.path.exists(HANDOFF_FILE):
        try:
            os.remove(HANDOFF_FILE)
        except:
            pass

def process_task(task_text, source="telegram"):
    print(f"\n[LocalOrchestrator] Nueva tarea recibida: {task_text[:50]}...")
    
    # 1. Evaluar complejidad usando el orquestador local
    sys_prompt = (
        "Eres Chask Swarm (Orquestador Local). Tu deber es analizar la siguiente petición y decidir si "
        "necesitas ayuda externa de IAs en la nube, o si puedes responderla tú mismo directamente. "
        "Si puedes tú solo, responde con el texto final. Si necesitas una IA especialista en código "
        "o análisis profundo, responde EXACTAMENTE con: [DELEGATE: <instrucción específica para el especialista>]"
    )
    
    try:
        import requests
        url = "http://localhost:11434/api/generate"
        r = requests.post(url, json={
            "model": ORCHESTRATOR_MODEL,
            "prompt": task_text,
            "system": sys_prompt,
            "stream": False
        }, timeout=120)
        
        if r.status_code == 200:
            decision = r.json().get("response", "").strip()
            
            if "[DELEGATE:" in decision:
                print("[LocalOrchestrator] Decisión: DELEGAR al Pool de IAs.")
                # Extraer la instrucción delegada
                start = decision.find("[DELEGATE:") + 10
                end = decision.find("]", start)
                if end != -1:
                    delegated_task = decision[start:end].strip()
                else:
                    delegated_task = decision[start:].strip()
                
                # Enviar a llm_router para que elija la mejor IA con créditos
                print(f"[LocalOrchestrator] Tarea delegada: {delegated_task}")
                result = llm_router.route(delegated_task, system_prompt="Eres un especialista subcontratado por el Orquestador Chask Swarm.", source=source)
                
                final_response = f"*(Delegado a {result.get('engine', 'N/A')})*\n\n{result.get('response', 'Fallo en la delegación')}"
            else:
                print("[LocalOrchestrator] Decisión: RESPONDER LOCALMENTE.")
                final_response = f"*(Chask Swarm Local)*\n\n{decision}"
                
            # Enviar respuesta
            if source == "telegram":
                responder.smart_respond(final_response)
            else:
                print(f"Respuesta:\n{final_response}")
                
        else:
            print(f"[LocalOrchestrator] Error de Ollama local: {r.status_code}")
            
    except Exception as e:
        print(f"[LocalOrchestrator] Excepción en ejecución local: {e}")


def run_orchestrator_loop():
    print(f"[{datetime.now()}] Local Orchestrator Iniciado. Modelo: {ORCHESTRATOR_MODEL}")
    
    # Comprobar si hay contexto de handoff inicial
    ctx = read_handoff_context()
    if ctx:
        print("[LocalOrchestrator] Contexto Handoff detectado. Asumiendo el mando del enjambre.")
        msg = ctx.get("message", "He tomado el control local por agotamiento de recursos.")
        responder.smart_respond(f"⚡ [MODO LOCAL ACTIVADO]\n{msg}")
        clear_handoff_context()
        
    print("[LocalOrchestrator] Esperando tareas en modo degradado/offline...")
    
    # Aquí podríamos engancharnos a pending_messages o telegram
    # Por ahora, un bucle simple de escucha pasiva en pending_messages.json
    pending_file = os.path.join(BASE_DIR, "..", "Message_Queues", "pending_messages.json")
    
    while True:
        try:
            if os.path.exists(pending_file):
                with open(pending_file, "r", encoding="utf-8") as f:
                    messages = json.load(f)
                
                unhandled = [m for m in messages if m.get("status") == "pending" and m.get("target") == "orchestrator"]
                for msg in unhandled:
                    msg["status"] = "processing"
                    with open(pending_file, "w", encoding="utf-8") as f:
                        json.dump(messages, f, indent=2, ensure_ascii=False)
                    
                    process_task(msg.get("text", ""), source=msg.get("source", "system"))
                    
                    msg["status"] = "done"
                    with open(pending_file, "w", encoding="utf-8") as f:
                        json.dump(messages, f, indent=2, ensure_ascii=False)
                        
        except Exception as e:
            print(f"[LocalOrchestrator] Error en bucle de escucha: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    run_orchestrator_loop()
