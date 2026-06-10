"""
agentic_chunker.py — Motor de Fragmentación Semántica
=====================================================
Usa una IA local (Ollama) para dividir textos técnicos en bloques 
conceptualmente independientes y coherentes.
"""
import os
import json
import requests
import logging

OLLAMA_URL = "http://localhost:11434/api/generate"
CHUNK_MODEL = "phi4-mini" # Rápido y preciso para extracción

log = logging.getLogger("agentic_chunker")

def split_semantically(text: str, title: str = "") -> list[str]:
    """
    Usa la IA para dividir un texto en fragmentos lógicos.
    """
    prompt = f"""
Actúa como un experto en documentación técnica de Power Automate.
Tu tarea es dividir el siguiente artículo titulado "{title}" en fragmentos (chunks) lógicamente independientes.

REGLAS:
1. Cada fragmento debe ser un concepto completo (ej: una acción de flujo, un requisito, un error común).
2. Mantén el formato original del texto (Markdown).
3. Cada fragmento debe tener entre 100 y 300 palabras aproximadamente.
4. Si el texto es corto y es un solo concepto, no lo dividas.
5. Separa CADA fragmento con la cadena exacta: ===CHUNKSPLIT===

TEXTO A PROCESAR:
{text}

RESPUESTA (Solo los fragmentos separados por ===CHUNKSPLIT===):
"""
    
    payload = {
        "model": CHUNK_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json().get("response", "")
            chunks = [c.strip() for c in result.split("===CHUNKSPLIT===") if len(c.strip()) > 50]
            if not chunks:
                return [text] # Fallback si la IA no separa bien
            return chunks
        else:
            return [text]
    except Exception as e:
        log.error(f"Error en Agentic Chunker: {e}")
        return [text]

if __name__ == "__main__":
    # Test rápido
    sample = "Power Automate permite crear flujos de nube. Un flujo de nube es... \n\n Por otro lado, los flujos de escritorio (RPA) sirven para..."
    print(f"Dividiendo {len(sample)} caracteres...")
    res = split_semantically(sample, "Test Power Automate")
    for i, c in enumerate(res):
        print(f"--- Chunk {i+1} ---\n{c}\n")
