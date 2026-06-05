import os
import sys
import argparse
import uuid
import json
import uuid
import urllib.request
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# Configure paths
BASE_DIR = r"C:\Program Files\Chask_Swarn\Advanced_Tools"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import llm_router

def extract_text_from_file(file_path):
    text = ""
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".pdf":
            import fitz
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        elif ext in [".docx", ".doc"]:
            import docx2txt
            text = docx2txt.process(file_path)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            text = f"[Archivo no soportado para lectura directa: {file_path}]"
    except Exception as e:
        text = f"[Error extrayendo {file_path}: {e}]"
        
    return text

def notify_telegram(message):
    try:
        script = os.path.join(r"C:\Program Files\Chask_Swarn\Advanced_Tools\charm_telegram.py")
        os.system(f'python "{script}" send "{message}"')
    except:
        pass

def generate_topic(name, urls, files_str, agent):
    print(f"[{agent}] Iniciando generacion para el tema: {name}")
    
    # 1. Extracción pura sin IA
    content_corpus = ""
    if files_str:
        file_paths = files_str.split(',')
        for fp in file_paths:
            print(f"Extrayendo: {fp}")
            content_corpus += f"\n\n--- DOCUMENTO: {os.path.basename(fp)} ---\n"
            content_corpus += extract_text_from_file(fp)
            
    if urls:
        content_corpus += f"\n\n--- URLs DE REFERENCIA ---\n{urls}"
        
    if not content_corpus.strip():
        content_corpus = "Utiliza tu conocimiento interno avanzado para desarrollar este tema."

    # 2. Orquestación (Elektra u Orestes)
    system_prompt = ""
    if agent == "Elektra":
        system_prompt = (
            "Eres el Protocolo Elektra (Enjambre Evolutivo de Máxima Precisión). "
            "Tu misión es estructurar y sintetizar información educativa en formato JSON estricto. "
            "Genera un currículo académico profundo basado en el corpus proporcionado."
        )
    else:
        system_prompt = (
            "Eres el Protocolo Orestes (Fusión Colmena - Síntesis Estructurada). "
            "Crea un curso educativo detallado en formato JSON estricto basado en la información recibida."
        )
        
    prompt = (
        f"Tema: {name}\n\n"
        f"Corpus Base:\n{content_corpus[:30000]}\n\n" # Limitar a 30k chars para no saturar contextos standard
        "Devuelve EXCLUSIVAMENTE un JSON con esta estructura (sin bloques markdown ```json):\n"
        "{\n"
        '  "title": "Nombre del tema",\n'
        '  "lessons": [\n'
        '    {"title": "Titulo Leccion 1", "content": "Contenido extenso en Markdown / LaTeX..."},\n'
        '    {"title": "Titulo Leccion 2", "content": "..."}\n'
        "  ]\n"
        "}"
    )
    
    print("Invocando al enrutador de LLMs...")
    # Prefer free routers to not waste credits unless necessary
    res = llm_router.route(prompt, system_prompt, force_free=True)
    json_text = res.get("response", "")
    
    # Limpiar posibles delimitadores
    json_text = json_text.strip()
    if json_text.startswith("```json"): json_text = json_text[7:]
    elif json_text.startswith("```"): json_text = json_text[3:]
    if json_text.endswith("```"): json_text = json_text[:-3]
    json_text = json_text.strip()
    
    try:
        topic_data = json.loads(json_text)
    except Exception as e:
        print(f"Error parseando JSON devuelto por {res.get('engine')}: {e}")
        notify_telegram(f"❌ Fallo al generar el tema '{name}'. La IA devolvió un formato inválido.")
        return
        
    # 3. Almacenamiento Local (Qdrant)
    # Convert name to a valid Qdrant collection name
    collection_name = "edu_" + "".join([c if c.isalnum() else "_" for c in name.lower()])
    
    try:
        client = QdrantClient("localhost", port=6333)
        # Create collection if not exists
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
        # Add points
        points = []
        for i, lesson in enumerate(topic_data.get("lessons", [])):
            points.append(PointStruct(
                id=i+1,
                vector=[0.0]*384, # Pseudo-vector as we are using it for storage
                payload={
                    "title": lesson.get("title", f"Leccion {i+1}"),
                    "content": lesson.get("content", ""),
                    "topic_name": name,
                    "lesson_id": str(uuid.uuid4())
                }
            ))
            
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Guardadas {len(points)} lecciones en la coleccion {collection_name}")
        notify_telegram(f"✅ Tema '{name}' forjado y guardado exitosamente en Qdrant con {len(points)} lecciones.")
        
    except Exception as e:
        print(f"Error guardando en Qdrant: {e}")
        notify_telegram(f"❌ Fallo al guardar el tema '{name}' en la base de datos local Qdrant.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--urls", default="")
    parser.add_argument("--files", default="")
    parser.add_argument("--agent", required=True)
    
    args = parser.parse_args()
    
    try:
        generate_topic(args.name, args.urls, args.files, args.agent)
    except Exception as e:
        notify_telegram(f"❌ Error crítico en el generador de temas para '{args.name}': {e}")
