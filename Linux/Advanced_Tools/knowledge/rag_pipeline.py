"""
rag_pipeline.py — Pipeline RAG automático
Vectoriza conversaciones automáticamente en Qdrant para memoria persistente.
"""
import os, sys, json, hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "Advanced_Tools"))

CONV_LOG = os.path.join(BASE_DIR, "conversation_log.jsonl")

def vectorize_conversation(user_msg: str, ai_response: str, context: str = ""):
    """Guarda un turno de conversación en Qdrant vía qdrant_memory_manager."""
    combined = f"[Usuario]: {user_msg}\n[Chask]: {ai_response}"
    uid = hashlib.md5(combined.encode()).hexdigest()[:12]

    # Guardar en log local (JSONL)
    entry = {
        "id": uid,
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "ai": ai_response,
        "context": context
    }
    with open(CONV_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Vectorizar en Qdrant
    keywords = extract_keywords(user_msg + " " + ai_response)
    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "Advanced_Tools", "qdrant_memory_manager.py"),
        "--save", combined,
        "--keywords", keywords,
        "--project", "conversaciones"
    ]
    import subprocess
    subprocess.run(cmd, capture_output=True, timeout=15)
    print(f"[RAG] Conversación {uid} vectorizada.")

def extract_keywords(text: str, max_kw: int = 6) -> str:
    """Extrae keywords simples por frecuencia."""
    import re
    stopwords = {"que", "con", "por", "para", "una", "del", "los", "las",
                 "the", "and", "for", "this", "that", "with", "from", "have"}
    words = re.findall(r'\b[a-záéíóúüñA-Z]{4,}\b', text.lower())
    freq = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    top = sorted(freq, key=freq.get, reverse=True)[:max_kw]
    return ",".join(top) if top else "conversacion"

def search_relevant_context(query: str, top_k: int = 3) -> str:
    """Busca en Qdrant el contexto más relevante para una query."""
    import subprocess
    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "Advanced_Tools", "qdrant_memory_manager.py"),
        "--search", query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return result.stdout.strip()[:1500] if result.stdout else ""

if __name__ == "__main__":
    # Test
    vectorize_conversation(
        "¿Qué tiempo hace en Sevilla?",
        "No tengo acceso en tiempo real al tiempo, pero puedo buscarlo por ti.",
        context="test"
    )
