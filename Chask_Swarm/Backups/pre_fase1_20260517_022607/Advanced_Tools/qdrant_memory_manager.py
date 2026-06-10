import os
import json
import argparse
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# Este script asume que Qdrant está corriendo localmente en Docker:
# docker run -d -p 6333:6333 qdrant/qdrant

# Usa memoria en memoria o conexión local
try:
    client = QdrantClient("localhost", port=6333)
except Exception:
    print("WARNING: No se pudo conectar a Qdrant en localhost:6333. Asegúrate de que Docker está corriendo el contenedor.")
    client = None

COLLECTION_NAME = "antigravity_memory"
VECTOR_SIZE = 384 # Asumimos un modelo de embedding pequeño o pseudo-vector si no usamos modelo real.

def init_db():
    if client is None: return
    try:
        collections = client.get_collections().collections
        if not any(c.name == COLLECTION_NAME for c in collections):
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            print("Colección Qdrant inicializada.")
    except Exception as e:
        print(f"Error inicializando BD: {e}")

def hash_text_to_vector(text):
    # Dummy vector generator for the sake of script completeness
    # In a real environment, use sentence-transformers.
    # We will just hash the string to a pseudo-vector for keyword matching via payload.
    import hashlib
    h = hashlib.sha256(text.encode()).digest()
    vec = [float(x)/255.0 for x in h]
    # Pad or truncate to VECTOR_SIZE
    if len(vec) < VECTOR_SIZE:
        vec += [0.0] * (VECTOR_SIZE - len(vec))
    else:
        vec = vec[:VECTOR_SIZE]
    return vec

def index_memory(text, keywords, project_name="general"):
    if client is None: return
    point_id = int(datetime.now().timestamp() * 1000) % (2**63 - 1)
    
    date_str = datetime.now().isoformat()
    
    vector = hash_text_to_vector(text + " " + " ".join(keywords))
    
    payload = {
        "text": text,
        "keywords": keywords,
        "project": project_name,
        "timestamp": date_str
    }
    
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)]
    )
    print(f"[{date_str}] Memoria guardada en Qdrant (ID: {point_id})")

def search_memory(query, older_first=False):
    if client is None: return
    print(f"Buscando en Qdrant: '{query}'...")
    
    vector = hash_text_to_vector(query)
    
    try:
        # qdrant-client v1.x uses query_points instead of search
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=10
        ).points
    except AttributeError:
        # fallback for older versions
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=10
        )
    
    if not results:
        print("No se encontraron recuerdos relevantes.")
        return
        
    sorted_results = sorted(results, key=lambda x: x.payload.get('timestamp', ''), reverse=not older_first)
    
    for r in sorted_results:
        date_str = r.payload.get('timestamp', 'N/A')
        project = r.payload.get('project', 'general')
        print(f"\n--- Memoria de {date_str} (Proyecto: {project}) ---")
        print(r.payload.get('text', ''))
        print("Keywords:", ", ".join(r.payload.get('keywords', [])))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", type=str, help="Texto a recordar")
    parser.add_argument("--keywords", type=str, help="Palabras clave separadas por comas")
    parser.add_argument("--project", type=str, default="general", help="Nombre del proyecto")
    parser.add_argument("--search", type=str, help="Buscar en memoria")
    parser.add_argument("--old", action="store_true", help="Priorizar recuerdos antiguos")
    args = parser.parse_args()
    
    init_db()
    
    if args.save:
        kw = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
        index_memory(args.save, kw, args.project)
    elif args.search:
        search_memory(args.search, args.old)
    else:
        parser.print_help()
