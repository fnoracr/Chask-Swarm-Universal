import os
import sys
import time
import json
from datetime import datetime

# Añadir rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

import llm_router
import responder

def check_providers():
    print(f"[{datetime.now()}] Iniciando chequeo de salud del Pool de IAs...")
    config = llm_router.load_config()
    failed = []
    
    for provider in config.get("providers", []):
        if not provider.get("active"):
            continue
            
        name = provider.get("name")
        print(f"  > Testeando {name}...", end=" ", flush=True)
        
        try:
            # Petición minimalista de test
            test_prompt = "Responde solo con la palabra 'OK'"
            # Timeout corto para no bloquear el watchdog
            response = llm_router.call_provider(provider, test_prompt, "Test de salud.")
            
            if "OK" in response.upper():
                print("✅")
            else:
                print("⚠️ (Respuesta inesperada)")
                failed.append(f"{name} (Respuesta no válida)")
        except Exception as e:
            print("❌")
            failed.append(f"{name} (Error: {str(e)[:50]})")

    if failed:
        report = "⚠️ **INFORME DE CAÍDA DE NODOS**\n\n"
        report += "He detectado que los siguientes nodos del pool no responden:\n"
        for f in failed:
            report += f"- {f}\n"
        report += "\nIntentaré usar los nodos de respaldo (fallback) para tus peticiones."
        
        print(f"Enviando reporte de fallo: {len(failed)} nodos caídos.")
        responder.smart_respond(report)
    else:
        print("Todos los sistemas operativos.")

if __name__ == "__main__":
    # Ciclo infinito de 1 hora
    while True:
        try:
            check_providers()
        except Exception as e:
            print(f"Error en watchdog: {e}")
        
        print("Próximo chequeo en 60 minutos...")
        time.sleep(3600)
