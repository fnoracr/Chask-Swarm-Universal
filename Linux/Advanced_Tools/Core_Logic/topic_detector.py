"""
topic_detector.py — Detector de Temas Recurrentes en Conversación
==================================================================
Monitoriza el historial de preguntas del usuario y detecta cuando
un tema aparece con suficiente frecuencia para ofrecer crear una
base de conocimiento profundo sobre él.

Uso desde llm_router o telegram_daemon:
    from topic_detector import TopicDetector
    detector = TopicDetector()
    result = detector.analyze(user_query)
    if result.should_offer:
        # Ofrecer crear base de conocimiento
        offer_knowledge_base(result.topic, result.suggested_sources)
"""

import re
import json
import os
import time
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime, timedelta

log = logging.getLogger("topic_detector")

# ─── Configuración ────────────────────────────────────────────
STATE_FILE       = r"C:\Program Files\Chask_Swarn\Advanced_Tools\topic_state.json"
TRIGGER_COUNT    = 3       # Número de preguntas sobre el mismo tema para activar oferta
WINDOW_HOURS     = 48      # Ventana de tiempo en horas para considerar recurrencia
MIN_TOPIC_WORDS  = 2       # Mínimo de palabras en un tema para considerarlo válido

# Fuentes conocidas por categoría de tema
KNOWN_SOURCES = {
    "power automate":  ["https://learn.microsoft.com/es-es/power-automate/"],
    "python":          ["https://docs.python.org/3/", "https://realpython.com/"],
    "javascript":      ["https://developer.mozilla.org/es/docs/Web/JavaScript"],
    "react":           ["https://react.dev/", "https://es.react.dev/"],
    "docker":          ["https://docs.docker.com/"],
    "kubernetes":      ["https://kubernetes.io/es/docs/"],
    "sql":             ["https://www.postgresql.org/docs/", "https://dev.mysql.com/doc/"],
    "azure":           ["https://learn.microsoft.com/es-es/azure/"],
    "sharepoint":      ["https://learn.microsoft.com/es-es/sharepoint/"],
    "excel":           ["https://support.microsoft.com/es-es/excel"],
    "flutter":         ["https://docs.flutter.dev/", "https://dart.dev/guides"],
    "fastapi":         ["https://fastapi.tiangolo.com/"],
    "qdrant":          ["https://qdrant.tech/documentation/"],
    "ollama":          ["https://ollama.com/blog/", "https://github.com/ollama/ollama"],
    "n8n":             ["https://docs.n8n.io/"],
    "make":            ["https://www.make.com/en/help/"],
    "zapier":          ["https://zapier.com/help/"],
    "telegram bot":    ["https://core.telegram.org/bots/api"],
    "selenium":        ["https://selenium-python.readthedocs.io/"],
    "playwright":      ["https://playwright.dev/python/docs/intro"],
    "openai":          ["https://platform.openai.com/docs/"],
    "langchain":       ["https://python.langchain.com/docs/"],
    "rag":             ["https://python.langchain.com/docs/", "https://qdrant.tech/documentation/"],
    "machine learning":["https://scikit-learn.org/stable/", "https://pytorch.org/docs/"],
    "rpa":             ["https://learn.microsoft.com/es-es/power-automate/desktop-flows/"],
    "power bi":        ["https://learn.microsoft.com/es-es/power-bi/"],
    "dynamics 365":    ["https://learn.microsoft.com/es-es/dynamics365/"],
}

# Stopwords para extracción de temas
TOPIC_STOPWORDS = {
    "qué", "cómo", "cuál", "cuándo", "dónde", "por", "para", "con", "sin", "sobre", "entre", "hasta", "desde",
    "que", "como", "cual", "cuando", "donde", "hacer", "es", "son", "del", "las", "los", "una", "uno", "unos", "unas",
    "está", "están", "tiene", "tienen", "puedo", "puede", "quiero", "este", "esta", "esto", "estos", "estas", "aquí", "alli",
    "necesito", "ayuda", "explicar", "explicame", "dime", "muéstrame", "mostrame", "explicar", "entender", "saber", "ver",
    "funciona", "funcione", "problema", "error", "fallo", "issue", "usar", "uso", "hago", "hace", "hacerlo", "pon", "poner",
    "what", "how", "when", "where", "which", "can", "could", "would", "todo", "todos", "toda", "todas", "cada", "algun",
    "should", "help", "please", "show", "tell", "explain", "use", "using", "used", "this", "that", "these", "those",
    "there", "here", "hola", "charlar", "hablar", "conversar", "responder", "pregunta", "preguntas", "duda", "dudas",
    "creo", "crear", "crea", "tengo", "alguna", "algunos", "algunas", "otro", "otra", "otros", "otras", "pero", "mas", "más",
    "muy", "bien", "así", "sino", "tanto", "también", "tampoco", "siempre", "nunca", "jamas", "jamás", "algo", "nada", "alguien",
    "nadie", "quien", "quién", "quienes", "quiénes", "cuyo", "cuya", "cuyos", "cuyas", "hacia", "para", "por", "según", "segun"
}


@dataclass
class TopicResult:
    """Resultado del análisis de temas recurrentes."""
    topic: str = ""
    count: int = 0
    should_offer: bool = False
    collection_name: str = ""
    suggested_sources: list[str] = field(default_factory=list)
    suggested_query: str = ""    # La pregunta del usuario que activó la oferta
    already_indexed: bool = False


class TopicDetector:
    """
    Rastrea los temas que el usuario pregunta y detecta recurrencia.
    """

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"queries": [], "offered_topics": [], "indexed_collections": []}

    def _save_state(self):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def _extract_topics(self, text: str) -> list[str]:
        """Extrae posibles temas de una query del usuario."""
        text_lower = text.lower()
        topics = []

        # 1. Buscar temas conocidos directamente
        for known_topic in KNOWN_SOURCES:
            if known_topic in text_lower:
                topics.append(known_topic)

        # 2. Extraer bigramas y trigramas de palabras clave
        words = re.findall(r'\b[a-záéíóúüñA-Za-z]{3,}\b', text_lower)
        keywords = [w for w in words if w not in TOPIC_STOPWORDS]

        # Bigramas
        for i in range(len(keywords) - 1):
            bigram = f"{keywords[i]} {keywords[i+1]}"
            if len(bigram) > 5:
                topics.append(bigram)

        # Palabras simples técnicas (ej: "Qdrant", "Docker", "Selenium")
        for w in keywords:
            if len(w) >= 5 and w[0].isupper() or w in {
                "python", "docker", "azure", "react", "fastapi", "qdrant",
                "ollama", "selenium", "playwright", "flutter", "dart",
            }:
                topics.append(w)

        return list(set(topics))

    def _normalize_topic(self, topic: str) -> str:
        """Normaliza un tema para comparación."""
        return re.sub(r'\s+', ' ', topic.lower().strip())

    def _topic_to_collection(self, topic: str) -> str:
        """Convierte un nombre de tema a nombre de colección Qdrant válido."""
        clean = re.sub(r'[^a-z0-9_]', '_', topic.lower())
        clean = re.sub(r'_+', '_', clean).strip('_')
        return f"kb_{clean}"

    def _is_in_window(self, timestamp: float) -> bool:
        """Verifica si un timestamp está dentro de la ventana de tiempo."""
        cutoff = time.time() - (WINDOW_HOURS * 3600)
        return timestamp > cutoff

    def _get_sources_for_topic(self, topic: str) -> list[str]:
        """Obtiene URLs de fuentes para un tema."""
        topic_lower = topic.lower()
        for known, sources in KNOWN_SOURCES.items():
            if known in topic_lower or topic_lower in known:
                return sources
        # Fallback: búsqueda web (se usará en el scraper)
        return [f"https://www.google.com/search?q={topic.replace(' ', '+')}+documentation+tutorial"]

    def analyze(self, user_query: str) -> TopicResult:
        """
        Analiza una query del usuario y detecta si hay un tema recurrente.
        Registra la query y devuelve un TopicResult.
        """
        # Limpiar queries antiguas fuera de ventana
        self.state["queries"] = [
            q for q in self.state["queries"]
            if self._is_in_window(q["ts"])
        ]

        # Registrar la query actual
        topics = self._extract_topics(user_query)
        entry = {
            "text": user_query[:200],
            "topics": topics,
            "ts": time.time()
        }
        self.state["queries"].append(entry)
        self._save_state()

        # Contar frecuencia de temas en ventana
        topic_counts = Counter()
        for q in self.state["queries"]:
            for t in q.get("topics", []):
                norm = self._normalize_topic(t)
                if len(norm.split()) >= 1 and len(norm) >= 4:
                    topic_counts[norm] += 1

        # Buscar temas que superen el umbral y no se hayan ofrecido ya
        offered = set(self.state.get("offered_topics", []))
        indexed = set(self.state.get("indexed_collections", []))

        for topic, count in topic_counts.most_common(5):
            if count >= TRIGGER_COUNT and topic not in offered:
                collection = self._topic_to_collection(topic)
                sources    = self._get_sources_for_topic(topic)
                already    = collection in indexed

                # Marcar como ofrecido
                self.state.setdefault("offered_topics", []).append(topic)
                self._save_state()

                log.info(f"TopicDetector: tema recurrente detectado → '{topic}' ({count} veces)")

                return TopicResult(
                    topic=topic,
                    count=count,
                    should_offer=True,
                    collection_name=collection,
                    suggested_sources=sources,
                    suggested_query=user_query,
                    already_indexed=already
                )

        return TopicResult()  # Sin oferta

    def mark_as_indexed(self, collection_name: str):
        """Registra que una colección ya ha sido indexada."""
        indexed = self.state.setdefault("indexed_collections", [])
        if collection_name not in indexed:
            indexed.append(collection_name)
        self._save_state()

    def get_stats(self) -> dict:
        """Devuelve estadísticas de los temas detectados."""
        topic_counts = Counter()
        for q in self.state["queries"]:
            for t in q.get("topics", []):
                topic_counts[self._normalize_topic(t)] += 1
        return {
            "total_queries": len(self.state["queries"]),
            "top_topics": topic_counts.most_common(10),
            "indexed_collections": self.state.get("indexed_collections", []),
            "offered_topics": self.state.get("offered_topics", []),
        }

    def reset_topic(self, topic: str):
        """Resetea la oferta para un tema (permite volver a ofrecerlo)."""
        norm = self._normalize_topic(topic)
        offered = self.state.get("offered_topics", [])
        self.state["offered_topics"] = [t for t in offered if t != norm]
        self._save_state()


if __name__ == "__main__":
    # Test rápido
    logging.basicConfig(level=logging.INFO)
    d = TopicDetector()

    test_queries = [
        "cómo crear un flujo en Power Automate",
        "qué conectores tiene Power Automate",
        "cómo usar Copilot en Power Automate",
        "cuál es la diferencia entre flujo nube y escritorio Power Automate",
    ]

    for q in test_queries:
        result = d.analyze(q)
        if result.should_offer:
            print(f"\n✅ OFERTA ACTIVADA:")
            print(f"   Tema: '{result.topic}' ({result.count} veces)")
            print(f"   Colección: {result.collection_name}")
            print(f"   Fuentes: {result.suggested_sources}")
        else:
            print(f"   Query analizada: '{q[:50]}' — sin oferta aún")

    print(f"\nEstadísticas: {d.get_stats()}")
