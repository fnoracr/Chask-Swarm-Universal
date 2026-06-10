#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
update_youtube_privacy.py — Sincroniza la privacidad de los vídeos de Qdrant con YouTube Público
==========================================================================================
Accede al canal @aquituprofe como usuario normal (anónimo) sin cookies, obtiene la lista de
vídeos públicos, y actualiza la colección 'youtube_academic_knowledge' en Qdrant para marcar
qué vídeos son realmente públicos y cuáles son privados/ocultos.
"""

import os
import sys
import re
import unicodedata
from qdrant_client import QdrantClient
import yt_dlp

# Forzar codificación UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

def normalize_title(title: str) -> str:
    if not title:
        return ""
    # Manejar posibles problemas de decodificación
    if isinstance(title, bytes):
        try:
            title = title.decode('utf-8', errors='ignore')
        except Exception:
            pass
    # Reemplazar caracteres rotos comunes del volcado de Qdrant/Windows
    title = title.replace("", "e") # Caracteres con tilde rotos comunes en español
    title = title.lower()
    # Eliminar acentos
    title = "".join(c for c in unicodedata.normalize('NFD', title) if unicodedata.category(c) != 'Mn')
    # Dejar solo letras y números
    title = re.sub(r'[^a-z0-9]', '', title)
    return title

def main():
    print("=== INICIANDO SINCRO DE PRIVACIDAD DE YOUTUBE ===")
    
    # 1. Scrapear vídeos públicos sin cookies (usuario normal)
    url = "https://www.youtube.com/@aquituprofe/videos"
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'playlistend': 1000
    }
    
    print(f"Scrapeando vídeos públicos desde canal: {url}...")
    public_videos = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            entries = info.get('entries', [])
            print(f"Encontrados {len(entries)} vídeos públicos en YouTube.")
            for entry in entries:
                if not entry:
                    continue
                v_title = entry.get("title", "")
                v_id = entry.get("id", "")
                if v_title and v_id:
                    norm = normalize_title(v_title)
                    public_videos[norm] = {
                        "id": v_id,
                        "title": v_title,
                        "url": f"https://youtube.com/watch?v={v_id}"
                    }
        except Exception as e:
            print(f"Error scrapeando canal: {e}")
            sys.exit(1)
            
    print(f"Normalizados {len(public_videos)} títulos únicos públicos para comparación.")
    
    # 2. Conectar a Qdrant
    client = QdrantClient(host="localhost", port=6333)
    collection_name = "youtube_academic_knowledge"
    
    print(f"Conectando a colección Qdrant '{collection_name}'...")
    try:
        offset = None
        points_to_update = []
        matched_count = 0
        private_count = 0
        total_processed = 0
        
        while True:
            records, next_offset = client.scroll(
                collection_name=collection_name,
                limit=100,
                with_payload=True,
                with_vectors=True, # Recuperar vectores para poder hacer el upsert completo
                offset=offset
            )
            
            for r in records:
                total_processed += 1
                payload = r.payload or {}
                v_title = payload.get("video_title", "")
                
                # Normalizar el título guardado en Qdrant
                norm_qdrant = normalize_title(v_title)
                
                # Buscar en la lista de vídeos públicos
                # 1. Coincidencia exacta de títulos normalizados
                match = public_videos.get(norm_qdrant)
                
                # 2. Coincidencia parcial si no hay exacta (por si la IA cortó o alteró levemente el título)
                if not match:
                    for norm_pub, info in public_videos.items():
                        if norm_qdrant in norm_pub or norm_pub in norm_qdrant:
                            match = info
                            break
                            
                if match:
                    # El vídeo es público
                    matched_count += 1
                    payload["is_public"] = True
                    payload["video_id"] = match["id"]
                    payload["video_url"] = match["url"]
                else:
                    # El vídeo es privado u oculto
                    private_count += 1
                    payload["is_public"] = False
                    payload["video_id"] = ""
                    payload["video_url"] = ""
                    
                points_to_update.append({
                    "id": r.id,
                    "vector": r.vector,
                    "payload": payload
                })
                
            if not next_offset:
                break
            offset = next_offset
            
        print(f"Procesados {total_processed} puntos de Qdrant.")
        print(f"-> Públicos (Coincidentes): {matched_count}")
        print(f"-> Privados/Ocultos: {private_count}")
        
        # 3. Subir las actualizaciones en lotes a Qdrant
        if points_to_update:
            print("Subiendo actualizaciones a Qdrant...")
            from qdrant_client.models import PointStruct
            
            # Enviar por lotes de 100
            for i in range(0, len(points_to_update), 100):
                batch = points_to_update[i:i+100]
                points = [
                    PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                    for p in batch
                ]
                client.upsert(
                    collection_name=collection_name,
                    points=points
                )
            print("=== SINCRO DE PRIVACIDAD COMPLETADA CON ÉXITO ===")
            
    except Exception as e:
        print(f"Error procesando actualización en Qdrant: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
