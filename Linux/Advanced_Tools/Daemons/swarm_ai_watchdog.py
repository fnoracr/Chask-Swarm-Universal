import os
import sys
import time
import json
import subprocess
from datetime import datetime

# Añadir rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import llm_router
import responder
import charm_sdk_client

def check_providers():
    print(f"[{datetime.now()}] Iniciando chequeo de salud y créditos del Pool de IAs...")
    config = llm_router.load_config()
    usage = llm_router.load_usage()
    
    failed = []
    credits_exhausted = []
    active_cloud_providers = 0
    
    for provider in config.get("providers", []):
        if not provider.get("active"):
            continue
            
        name = provider.get("name")
        limit = provider.get("daily_limit", 500)
        used = usage.get("counts", {}).get(name, 0)
        
        # Ignorar Ollama local para los conteos de nube
        if "ollama" not in name.lower() or name == "ollama_cloud":
            active_cloud_providers += 1
            if used >= limit:
                credits_exhausted.append(name)
                continue
                
        print(f"  > Testeando {name}...", end=" ", flush=True)
        
        try:
            # Petición minimalista de test
            test_prompt = "Responde solo con la palabra 'OK'"
            response = llm_router.call_provider(provider, test_prompt, "Test de salud.")
            
            if response and "OK" in response.upper():
                print("✅")
            else:
                print("⚠️ (Respuesta inesperada)")
                failed.append(name)
        except Exception as e:
            print("❌")
            failed.append(name)

    # 1. Lógica de Traspaso (SDK Model Swapping - [Nombre_IA] 2.0)
    # Si TODOS los proveedores de la nube activos están agotados o fallando:
    total_unavailable = len(set(failed + credits_exhausted))
    if active_cloud_providers > 0 and total_unavailable >= active_cloud_providers:
        print("[Watchdog] ¡ALERTA CRÍTICA! Todos los proveedores de la nube están caídos o sin créditos.")
        print("[Watchdog] Iniciando reconfiguración dinámica vía [Nombre_IA] SDK...")
        # Cambiamos la IA de [Nombre_IA] al vuelo a un modelo local usando el SDK
        charm_sdk_client.set_agent_model("chask_swarm_main", "ollama/qwen2.5-coder:7b")
        responder.smart_respond("⚠️ **SWARM ALERT**: He reconfigurado [Nombre_IA] 2.0 para usar inferencia local debido al agotamiento de recursos en la nube.")
        return

    if failed or credits_exhausted:
        report = "⚠️ **INFORME DE CAÍDA/CRÉDITOS DE NODOS**\n\n"
        if failed:
            report += "Nodos caídos:\n" + "\n".join([f"- {f}" for f in failed]) + "\n\n"
        if credits_exhausted:
            report += "Nodos sin créditos:\n" + "\n".join([f"- {c}" for c in credits_exhausted]) + "\n\n"
        
        report += "Usando nodos de respaldo."
        
        print(f"Enviando reporte de fallo/créditos.")
        responder.smart_respond(report)
    else:
        print("Todos los sistemas operativos y con créditos.")

if __name__ == "__main__":
    # Ciclo de 30 minutos
    while True:
        try:
            check_providers()
        except Exception as e:
            print(f"Error en watchdog: {e}")
        
        print("Próximo chequeo en 30 minutos...")
        time.sleep(1800)
