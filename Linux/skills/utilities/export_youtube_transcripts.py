#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_youtube_transcripts.py — Exportador de Transcripciones Académicas de Qdrant a Markdown
========================================================================================
Conecta a la colección 'youtube_academic_knowledge' de Qdrant local, descarga todos los
vectores/payloads, los agrupa por vídeo y genera un archivo Markdown (.md) ultra-premium
para cada clase en 'C:\\Users\\fnora\\Desktop\\Enjambre Datos\\Transcripciones_YouTube\\'.

Diseñado por Enjambre para el ecosistema Chask Swarm.
"""

import os
import sys
import re
import json
from datetime import datetime
from qdrant_client import QdrantClient

# Forzar codificación UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

EXPORT_DIR = r"C:\Users\fnora\Desktop\Enjambre Datos\Transcripciones_YouTube"

def clean_filename(title: str) -> str:
    """Elimina caracteres no válidos para nombres de archivos en Windows."""
    clean = re.sub(r'[\\/*?:"<>|]', "", title)
    # Limitar longitud para evitar problemas de rutas largas
    return clean[:120].strip()

def main():
    print("=== INICIANDO EXPORTACIÓN DE TRANSCRIPCIONES ACADÉMICAS ===")
    
    # 1. Crear directorio de exportación si no existe
    os.makedirs(EXPORT_DIR, exist_ok=True)
    print(f"Directorio de destino: '{EXPORT_DIR}'")
    
    # 2. Conectar a Qdrant
    client = QdrantClient(host="localhost", port=6333)
    collection_name = "youtube_academic_knowledge"
    
    if not client.collection_exists(collection_name):
        print(f"[Error] La colección '{collection_name}' no existe en Qdrant.")
        sys.exit(1)
        
    print(f"Recuperando todos los puntos de la colección '{collection_name}'...")
    
    all_chunks = []
    offset = None
    
    try:
        while True:
            records, next_offset = client.scroll(
                collection_name=collection_name,
                limit=150,
                with_payload=True,
                offset=offset
            )
            
            for r in records:
                if r.payload:
                    payload = r.payload
                    payload["_id"] = r.id
                    all_chunks.append(payload)
                    
            if not next_offset:
                break
            offset = next_offset
            
        print(f"Recuperados con éxito {len(all_chunks)} fragmentos didácticos.")
        
    except Exception as e:
        print(f"[Error] Fallo al leer de Qdrant: {e}")
        sys.exit(1)
        
    # 3. Agrupar fragmentos por vídeo
    videos_dict = {}
    for chunk in all_chunks:
        title = chunk.get("video_title", "Video sin Título").strip()
        if not title:
            title = "Video sin Título"
            
        if title not in videos_dict:
            videos_dict[title] = {
                "title": title,
                "url": chunk.get("video_url", ""),
                "id": chunk.get("video_id", ""),
                "chunks": []
            }
        videos_dict[title]["chunks"].append(chunk)
        
    print(f"Agrupados en {len(videos_dict)} clases académicas únicas.")
    
    # 4. Generar archivos Markdown para cada vídeo
    exported_count = 0
    
    for title, vdata in videos_dict.items():
        # Ordenar fragmentos por start_time para que la lección sea cronológica
        vdata["chunks"].sort(key=lambda x: x.get("start_time", 0.0))
        
        filename = clean_filename(title) + ".md"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        # Obtener asignaturas y temas únicos de esta lección
        subjects = list(set([c.get("asignatura") for c in vdata["chunks"] if c.get("asignatura")]))
        topics = list(set([c.get("tema") for c in vdata["chunks"] if c.get("tema")]))
        levels = list(set([c.get("nivel") for c in vdata["chunks"] if c.get("nivel")]))
        
        subject_str = ", ".join(subjects) if subjects else "No especificada"
        topic_str = ", ".join(topics) if topics else "General"
        level_str = ", ".join(levels) if levels else "General"
        
        with open(filepath, "w", encoding="utf-8") as f:
            # Cabecera de alta gama con justificación tipográfica Scoped
            f.write(f"# Clases de YouTube — Transcripción y Depuración Académica\n")
            f.write(f"## {title}\n\n")
            
            f.write(f"> **Asignatura:** {subject_str}  \n")
            f.write(f"> **Tema principal:** {topic_str}  \n")
            f.write(f"> **Nivel académico sugerido:** {level_str}  \n")
            
            if vdata["url"]:
                f.write(f"> **Vídeo original:** [Ver en YouTube]({vdata['url']})  \n")
            else:
                f.write(f"> **Vídeo original:** 🔒 Vídeo Privado o No Listado  \n")
                
            f.write(f"> **Fecha de ingesta:** {datetime.now().strftime('%Y-%m-%d')}  \n\n")
            
            f.write("---\n\n")
            f.write("### 📖 Índice de Contenidos Didácticos\n\n")
            for idx, c in enumerate(vdata["chunks"], 1):
                t_tag = c.get("timestamp_tag", "00:00")
                sec_title = f"Sección {idx}: Fragmento desde el minuto {t_tag}"
                f.write(f"- [{sec_title}](#sección-{idx}-fragmento-desde-el-minuto-{t_tag.replace(':', '')})\n")
                
            f.write("\n---\n\n")
            
            # Escribir las secciones individuales
            for idx, c in enumerate(vdata["chunks"], 1):
                t_tag = c.get("timestamp_tag", "00:00")
                original_text = c.get("contenido_original", "").strip()
                cleaned_text = c.get("contenido_depurado", "").strip()
                graph_path = c.get("graph_image_path", "")
                
                # Encapsular cada fragmento con estilo justificado
                f.write(f"### Sección {idx}: Fragmento desde el minuto {t_tag}\n\n")
                
                # Explicación pedagógica depurada
                f.write("#### 🎓 Explicación Científica Purificada con IA:\n")
                f.write('<div style="text-align: justify; text-justify: inter-word; line-height: 1.6;">\n\n')
                f.write(cleaned_text)
                f.write('\n\n</div>\n\n')
                
                # Insertar gráfico si existe
                if graph_path:
                    # Dado que la ruta es local y relativa a Chask_Swarn\Advanced_Tools\uploads\graphs
                    # la mapeamos a la ruta completa del disco para que el lector markdown local la cargue.
                    abs_graph_path = os.path.join(r"C:\Program Files\Chask_Swarn\Advanced_Tools", graph_path.lstrip("/"))
                    abs_graph_path = abs_graph_path.replace("/", "\\")
                    f.write(f"#### 📈 Gráfico Científico Asociado:\n")
                    f.write(f"![Gráfico Científico de la Sección {idx}](file:///{abs_graph_path.replace(' ', '%20')})\n\n")
                
                # Transcripción cruda como colapsable de soporte
                f.write("<details>\n")
                f.write("<summary>🔍 Ver Transcripción Cruda de Referencia (Whisper)</summary>\n\n")
                f.write(f"```text\n{original_text}\n```\n\n")
                f.write("</details>\n\n")
                
                f.write("---\n\n")
                
        exported_count += 1
        
    print(f"=== EXPORTACIÓN FINALIZADA CON ÉXITO ===")
    print(f"Se han exportado {exported_count} clases académicas a formato Markdown en:")
    print(f"'{EXPORT_DIR}'")

if __name__ == "__main__":
    main()
