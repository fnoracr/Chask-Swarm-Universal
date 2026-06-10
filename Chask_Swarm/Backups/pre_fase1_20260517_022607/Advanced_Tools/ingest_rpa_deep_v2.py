"""
ingest_rpa_deep_v2.py — Ingesta Agéntica de Conocimiento RPA
=============================================================
Utiliza el agentic_chunker para una fragmentación semántica inteligente.
"""
import re
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Importar el chunker inteligente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import agentic_chunker

# Configuración
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "power_automate_deep"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
MARKDOWN_FILE = "C:\\Users\\fnora\\Desktop\\Conocimiento RPA\\Conocimiento_Profundo_RPA.md"
STATE_FILE = "C:\\Users\\fnora\\Desktop\\Conocimiento RPA\\indexed_urls_v2.json"

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s", 
    handlers=[logging.FileHandler("C:\\Users\\fnora\\Desktop\\Conocimiento RPA\\ingest_deep_v2.log", encoding="utf-8"), logging.StreamHandler()]
)
log = logging.getLogger("ingest_v2")

@dataclass
class Article:
    index: int
    title: str
    url: str
    content: str

@dataclass
class Chunk:
    article_index: int
    article_title: str
    article_url: str
    chunk_index: int
    total_chunks: int
    content: str

def parse_markdown_articles(filepath: str) -> list[Article]:
    if not os.path.exists(filepath):
        log.warning(f"El archivo {filepath} no existe.")
        return []
        
    text = Path(filepath).read_text(encoding="utf-8")
    parts = re.split(r"^## Origen:\s*(https?://[^\s]+)", text, flags=re.MULTILINE)
    
    articles = []
    for i in range(1, len(parts), 2):
        url = parts[i].strip()
        body = parts[i+1]
        
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Sin título"
        
        # Limpieza básica de ruido de MS Learn
        body_lines = body.split("\n")
        clean_lines = []
        skip_words = ["Tabla de contenido", "Salir del modo de editor", "Preguntar a Learn", "Modo de lectura"]
        for line in body_lines:
            if not any(sw in line for sw in skip_words):
                clean_lines.append(line)
        
        content = "\n".join(clean_lines).strip()
        if len(content) > 100:
            articles.append(Article(index=i//2 + 1, title=title, url=url, content=content))
    return articles

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Limitar numero de articulos (0 para todos)")
    args = parser.parse_args()

    log.info("🚀 Iniciando Ingesta Agéntica V2...")
    
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    model = SentenceTransformer(EMBEDDING_MODEL)

    if args.reset:
        log.info(f"🗑️ Reseteando colección {COLLECTION_NAME}...")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        if os.path.exists(STATE_FILE): os.remove(STATE_FILE)

    articles = parse_markdown_articles(MARKDOWN_FILE)
    if args.limit > 0:
        articles = articles[:args.limit]
    
    log.info(f"📚 Procesando {len(articles)} artículos con IA Local...")
    
    point_id = 0
    indexed_urls = []

    for i, article in enumerate(articles):
        log.info(f"[{i+1}/{len(articles)}] Fragmentando semánticamente: {article.title}")
        
        # AQUÍ OCURRE LA MAGIA: Fragmentación con IA
        semantic_texts = agentic_chunker.split_semantically(article.content, article.title)
        
        log.info(f"   -> Generados {len(semantic_texts)} fragmentos inteligentes.")
        
        chunks = []
        for idx, text in enumerate(semantic_texts):
            enriched = f"Artículo: {article.title}\nURL: {article.url}\n\n{text}"
            chunks.append(Chunk(
                article_index=article.index,
                article_title=article.title,
                article_url=article.url,
                chunk_index=idx,
                total_chunks=len(semantic_texts),
                content=enriched
            ))

        # Vectorizar e insertar
        if chunks:
            texts = [c.content for c in chunks]
            embeddings = model.encode(texts, normalize_embeddings=True)
            
            points = []
            for j, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                points.append(PointStruct(
                    id=point_id,
                    vector=emb.tolist(),
                    payload={
                        "article_title": chunk.article_title,
                        "article_url": chunk.article_url,
                        "content": chunk.content,
                        "agentic": True
                    }
                ))
                point_id += 1
            
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            indexed_urls.append(article.url)
            
            # Guardar progreso parcial
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(indexed_urls, f)

    log.info(f"✅ ¡Ingesta completada! Total puntos: {point_id}")

if __name__ == "__main__":
    main()
