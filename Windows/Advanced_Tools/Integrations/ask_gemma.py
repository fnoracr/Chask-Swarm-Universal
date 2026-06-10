import sys
import json
import requests
import argparse

def ask_ollama(prompt, model="gemma4:e4b", system="Eres un desarrollador experto (Codex/Gemma). Responde s\u00f3lo con el c\u00f3digo y una breve explicaci\u00f3n."):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False
    }
    try:
        response = requests.post(url, json=data, timeout=300)
        response.raise_for_status()
        result = response.json()
        print(f"--- [RESPUESTA DE {model}] ---")
        print(result.get("response", ""))
        print("---------------------------------")
    except Exception as e:
        print(f"Error conectando a Ollama: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delega una tarea a Gemma4 local")
    parser.add_argument("prompt", type=str, help="El prompt o tarea de c\u00f3digo")
    parser.add_argument("--model", type=str, default="gemma4:e4b", help="Modelo a utilizar")
    parser.add_argument("--system", type=str, default="Eres un experto desarrollador. Resuelve la tarea de programaci\u00f3n paso a paso.", help="Prompt del sistema")
    
    args = parser.parse_args()
    ask_ollama(args.prompt, model=args.model, system=args.system)
