import os
import time
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuración
FOLDER_TO_WATCH = r"C:\Users\fnora\Desktop\Nora Datos"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "nora_memory"

class VectorIndexerHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        try:
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            # Create collection if not exists
            collections = [c.name for c in self.client.get_collections().collections]
            if COLLECTION_NAME not in collections:
                # We'll use a dummy vector size of 1536 (typical for OpenAI text-embedding-ada-002)
                # Note: In a real environment, we'd embed the text first.
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
                )
            print(f"[VectorIndexer] Conectado a Qdrant. Colección '{COLLECTION_NAME}' lista.")
        except Exception as e:
            print(f"[VectorIndexer] Error al conectar con Qdrant: {e}")
            self.client = None

    def process_file(self, file_path):
        if not self.client: return
        if not file_path.endswith(('.md', '.txt', '.json')): return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Dummy embedding (zeros) since we lack the specific embedder config in this scope.
            # A full implementation would call `embed(content)` here.
            dummy_vector = [0.0] * 1536
            
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, file_path))
            
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=dummy_vector,
                        payload={
                            "source_file": file_path,
                            "content": content,
                            "updated_at": time.time()
                        }
                    )
                ]
            )
            print(f"[VectorIndexer] Archivo indexado: {file_path}")
        except Exception as e:
            print(f"[VectorIndexer] Error leyendo {file_path}: {e}")

    def on_modified(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)
            
    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

def start_indexer():
    print(f"Iniciando indexador vectorial en {FOLDER_TO_WATCH}...")
    event_handler = VectorIndexerHandler()
    observer = Observer()
    observer.schedule(event_handler, FOLDER_TO_WATCH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_indexer()
