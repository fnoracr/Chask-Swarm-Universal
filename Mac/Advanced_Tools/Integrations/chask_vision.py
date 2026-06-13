"""
chask_vision.py — Computer Vision para Enjambre
============================================
Captura pantalla, OCR local, y descripcion semantica via LLM.
Doble motor: easyocr (local, rapido) + LLM vision (inteligente).
"""
import os
import sys
import json
import base64
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

_ocr_reader = None


def screenshot(region=None, save_path=None):
    """Captura pantalla completa o region. Retorna path del fichero."""
    import mss
    with mss.mss() as sct:
        if region:
            monitor = {"left": region[0], "top": region[1],
                       "width": region[2], "height": region[3]}
        else:
            monitor = sct.monitors[0]  # Pantalla completa

        img = sct.grab(monitor)
        path = save_path or os.path.join(
            SCREENSHOTS_DIR, f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        # Guardar como PNG
        from mss.tools import to_png
        to_png(img.rgb, img.size, output=path)
        return path


def ocr(image_path):
    """Extrae texto de una imagen usando easyocr (local, sin API)."""
    global _ocr_reader
    try:
        import easyocr
        if _ocr_reader is None:
            _ocr_reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
        results = _ocr_reader.readtext(image_path)
        texts = [{"text": r[1], "confidence": round(r[2], 3),
                  "bbox": [int(c) for p in r[0] for c in p]} for r in results]
        full_text = " ".join(r[1] for r in results)
        return {"texts": texts, "full_text": full_text, "count": len(texts)}
    except ImportError:
        # Fallback sin easyocr
        return {"texts": [], "full_text": "", "count": 0, "error": "easyocr no instalado"}
    except Exception as e:
        return {"texts": [], "full_text": "", "count": 0, "error": str(e)}


def describe(image_path, prompt="Describe lo que ves en esta pantalla en espanol."):
    """
    Envia screenshot a LLM con vision para descripcion semantica.
    Cadena de fallback: Cloud Vision (GPT-4V/Gemini) -> Ollama (llava) -> OCR
    """
    img_b64 = None
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
    except Exception as e:
        return {"description": "", "model": "error", "error": str(e)}
    
    # 1. Try cloud vision via LLM Router (GPT-4V, Gemini Vision)
    try:
        providers_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data", "llm_providers_config.json")
        if os.path.exists(providers_path):
            with open(providers_path, "r") as f:
                providers = json.load(f)
            
            # Try OpenAI GPT-4V
            for name, cfg in providers.items():
                api_key = cfg.get("api_key", "")
                if not api_key or api_key.startswith("FREE"):
                    continue
                base_url = cfg.get("base_url", "")
                
                # OpenAI-compatible vision
                if "openai" in name.lower() or "gpt" in name.lower():
                    import urllib.request
                    data = json.dumps({
                        "model": cfg.get("model", "gpt-4o"),
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                        ]}],
                        "max_tokens": 500
                    }).encode()
                    url = (base_url or "https://api.openai.com/v1") + "/chat/completions"
                    req = urllib.request.Request(url, data=data, headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    })
                    resp = urllib.request.urlopen(req, timeout=30)
                    result = json.loads(resp.read())
                    desc = result["choices"][0]["message"]["content"]
                    return {"description": desc, "model": f"cloud-{name}"}
                
                # Google Gemini Vision
                if "gemini" in name.lower() or "google" in name.lower():
                    import urllib.request
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
                    data = json.dumps({
                        "contents": [{"parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                        ]}]
                    }).encode()
                    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                    resp = urllib.request.urlopen(req, timeout=30)
                    result = json.loads(resp.read())
                    desc = result["candidates"][0]["content"]["parts"][0]["text"]
                    return {"description": desc, "model": f"cloud-{name}"}
    except Exception:
        pass  # Fall through to Ollama
    
    # 2. Try Ollama local (llava)
    try:
        import urllib.request
        data = json.dumps({
            "model": "llava",
            "prompt": prompt,
            "images": [img_b64],
            "stream": False
        }).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        return {"description": result.get("response", ""), "model": "llava-local"}
    except Exception:
        pass  # Fall through to OCR
    
    # 3. Fallback: solo OCR
    ocr_result = ocr(image_path)
    return {
        "description": f"(Vision LLM no disponible. OCR: {ocr_result['full_text'][:500]})",
        "model": "ocr-fallback"
    }


def find_element(description_text):
    """Captura pantalla y busca un elemento por descripcion textual via OCR."""
    path = screenshot()
    ocr_result = ocr(path)
    matches = []
    desc_lower = description_text.lower()
    for t in ocr_result["texts"]:
        if desc_lower in t["text"].lower():
            bbox = t["bbox"]
            cx = (bbox[0] + bbox[4]) // 2
            cy = (bbox[1] + bbox[5]) // 2
            matches.append({"text": t["text"], "center": (cx, cy), "confidence": t["confidence"]})
    return {"matches": matches, "screenshot": path, "total_texts": ocr_result["count"]}


def screen_read():
    """Captura y lee toda la pantalla. Retorna texto completo."""
    path = screenshot()
    result = ocr(path)
    return {"text": result["full_text"], "screenshot": path, "elements": result["count"]}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "screenshot":
            path = screenshot()
            print(f"Screenshot: {path}")
        elif sys.argv[1] == "ocr" and len(sys.argv) > 2:
            result = ocr(sys.argv[2])
            print(f"Texto: {result['full_text'][:500]}")
            print(f"Elementos: {result['count']}")
        elif sys.argv[1] == "describe" and len(sys.argv) > 2:
            result = describe(sys.argv[2])
            print(f"Descripcion: {result['description'][:500]}")
        elif sys.argv[1] == "find" and len(sys.argv) > 2:
            result = find_element(sys.argv[2])
            print(f"Matches: {len(result['matches'])}")
            for m in result["matches"]:
                print(f"  '{m['text']}' en {m['center']}")
        elif sys.argv[1] == "read":
            result = screen_read()
            print(f"Pantalla ({result['elements']} elementos):")
            print(result["text"][:1000])
    else:
        print("Uso: python chask_vision.py screenshot|ocr <img>|describe <img>|find <texto>|read")
