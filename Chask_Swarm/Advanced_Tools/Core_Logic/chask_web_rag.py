"""
chask_web_rag.py — Pipeline Web → RAG (Crawl4AI + Qdrant)
=========================================================
Ingesta cualquier URL, extrae contenido limpio, lo fragmenta,
genera embeddings y lo almacena en Qdrant para consulta semantica.
"""
import os
import sys
import json
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

COLLECTION = "chask_web_knowledge"


class WebRAG:
    def __init__(self):
        self.client = None
        self._init_qdrant()

    def _init_qdrant(self):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import VectorParams, Distance
            self.client = QdrantClient(host="localhost", port=6333, timeout=10)
            collections = [c.name for c in self.client.get_collections().collections]
            if COLLECTION not in collections:
                self.client.create_collection(
                    collection_name=COLLECTION,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                print(f"[WebRAG] Coleccion '{COLLECTION}' creada")
        except Exception as e:
            print(f"[WebRAG] Error Qdrant: {e}")

    def _get_embedding(self, text):
        """Genera embedding via Ollama (nomic-embed-text)."""
        import urllib.request
        data = json.dumps({"model": "nomic-embed-text", "prompt": text[:2000]}).encode()
        req = urllib.request.Request("http://localhost:11434/api/embeddings",
                                     data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())["embedding"]

    def _chunk_text(self, text, chunk_size=500, overlap=50):
        """Divide texto en fragmentos con overlap."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:
                chunks.append(chunk)
        return chunks

    def ingest(self, url, title=None):
        """Ingesta una URL: extrae, fragmenta, almacena en Qdrant."""
        # Extraer contenido con crawl4ai o fallback a urllib
        text = self._extract(url)
        if not text or len(text.strip()) < 100:
            return {"ok": False, "error": "No se pudo extraer contenido suficiente"}

        chunks = self._chunk_text(text)
        stored = 0

        for i, chunk in enumerate(chunks):
            try:
                embedding = self._get_embedding(chunk)
                point_id = int(hashlib.md5(f"{url}_{i}".encode()).hexdigest()[:12], 16)
                self.client.upsert(
                    collection_name=COLLECTION,
                    points=[{
                        "id": point_id,
                        "vector": embedding,
                        "payload": {
                            "url": url,
                            "title": title or url,
                            "chunk_index": i,
                            "text": chunk[:1000],
                            "ingested_at": datetime.now().isoformat(),
                            "word_count": len(chunk.split())
                        }
                    }]
                )
                stored += 1
            except Exception as e:
                print(f"[WebRAG] Error chunk {i}: {e}")

        return {"ok": True, "url": url, "chunks_total": len(chunks), "chunks_stored": stored}

    def _extract(self, url):
        """Extrae texto de una URL."""
        try:
            # Intento con crawl4ai
            from crawl4ai import CrawlerStrategy, Crawler
            crawler = Crawler()
            result = crawler.run(url)
            if result and hasattr(result, 'markdown') and result.markdown:
                return result.markdown
        except Exception:
            pass

        # Fallback: urllib + html simple
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            html = resp.read().decode("utf-8", errors="replace")
            # Extraer texto básico quitando tags
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception as e:
            print(f"[WebRAG] Error extraccion: {e}")
            return ""

    def query(self, question, limit=5):
        """Busca en el conocimiento web ingestado."""
        try:
            embedding = self._get_embedding(question)
            results = self.client.search(
                collection_name=COLLECTION,
                query_vector=embedding,
                limit=limit
            )
            return [{
                "score": round(r.score, 3),
                "url": r.payload.get("url", ""),
                "title": r.payload.get("title", ""),
                "text": r.payload.get("text", "")[:300]
            } for r in results]
        except Exception as e:
            print(f"[WebRAG] Error query: {e}")
            return []

    def stats(self):
        """Estadísticas de la colección."""
        try:
            info = self.client.get_collection(COLLECTION)
            return {"points": info.points_count, "status": str(info.status)}
        except:
            return {"points": 0, "status": "offline"}


if __name__ == "__main__":
    rag = WebRAG()
    if len(sys.argv) > 2 and sys.argv[1] == "ingest":
        result = rag.ingest(sys.argv[2])
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "query":
        results = rag.query(sys.argv[2])
        for r in results:
            print(f"  [{r['score']}] {r['title']}: {r['text'][:100]}...")
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(rag.stats(), indent=2))
    else:
        print("Uso: python chask_web_rag.py ingest <url> | query <pregunta> | stats")
