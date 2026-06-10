"""
Limpia entradas de test_battery_* de la coleccion chask_operations en Qdrant.
Busca todos los puntos cuya descripcion empiece por "test_battery_" y los elimina.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText

client = QdrantClient(host="localhost", port=6333, timeout=30)
collection = "chask_operations"

# Scroll all points and filter test_battery ones
deleted = 0
offset = None
while True:
    results = client.scroll(collection_name=collection, limit=100, offset=offset, with_payload=True)
    points, next_offset = results
    if not points:
        break
    ids_to_delete = []
    for p in points:
        desc = p.payload.get("description", "")
        if desc.startswith("test_battery_"):
            ids_to_delete.append(p.id)
    if ids_to_delete:
        client.delete(collection_name=collection, points_selector=ids_to_delete)
        deleted += len(ids_to_delete)
        print(f"Eliminados {len(ids_to_delete)} puntos (total: {deleted})")
    if next_offset is None:
        break
    offset = next_offset

print(f"\nLimpieza completada: {deleted} entradas test_battery eliminadas")
