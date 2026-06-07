#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
youtube_academic_indexer.py — Motor de Ingesta Académica de YouTube (Checkpointed & Lazy Load)
========================================================================================
Extrae la lista de vídeos de YouTube de forma plana, comprueba localmente un registro
de exclusión (checkpoint) para omitir vídeos ya procesados, descarga de forma perezosa (lazy) 
el audio de UN SOLO VÍDEO a la vez para conservar almacenamiento, lo transcribe con Whisper,
lo depura y corrige con Ollama local (qwen2-math), y lo indexa de inmediato en Qdrant.

Diseñado por Enjambre para el ecosistema Chask Swarm.
"""

import os
import sys
import json
import time

# Forzar codificación UTF-8 en flujos estándar para evitar errores de codificación en Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
import shutil
import argparse
import tempfile
import requests
from datetime import datetime

# Importar dependencias críticas
try:
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')  # Configurar backend headless para evitar errores en hilos y segundo plano
    import matplotlib.pyplot as plt
except ImportError:
    print("[Error] Las librerías 'numpy' o 'matplotlib' no están instaladas. Ejecuta: pip install numpy matplotlib")
    sys.exit(1)

try:
    import yt_dlp
except ImportError:
    print("[Error] La librería 'yt-dlp' no está instalada. Ejecuta: pip install yt-dlp")
    sys.exit(1)

try:
    import whisper
except ImportError:
    print("[Error] La librería 'openai-whisper' no está instalada. Ejecuta: pip install openai-whisper")
    sys.exit(1)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except ImportError:
    print("[Error] La librería 'qdrant-client' no está instalada. Ejecuta: pip install qdrant-client")
    sys.exit(1)

# Configuraciones por defecto
BASE_DIR = r"C:\Program Files\Chask_Swarm"
FFMPEG_PATH = os.path.join(BASE_DIR, "Binarios", "ffmpeg.exe")
OLLAMA_URL = "http://localhost:11434"
CHECKPOINT_FILE = os.path.join(r"C:\Users\fnora\Desktop\Enjambre Datos", "youtube_indexer_checkpoint.json")

def log(msg: str, level: str = "INFO"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

def test_ollama_model(model_name: str) -> bool:
    """Verifica si el modelo de Ollama está disponible localmente."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            for m in models:
                if model_name in m or m in model_name:
                    return True
        return False
    except Exception:
        return False

def load_checkpoint() -> dict:
    """Carga el historial de videos ya procesados para no repetir descargas."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"indexed_video_ids": []}

def save_checkpoint(checkpoint: dict):
    """Guarda el historial de videos procesados en disco."""
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error guardando checkpoint: {e}", "WARNING")

def get_ollama_embedding(text: str) -> list[float] | None:
    """Genera embeddings vectoriales usando nomic-embed-text en local."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text:latest", "prompt": text},
            timeout=15
        )
        if r.status_code == 200:
            return r.json().get("embedding")
    except Exception as e:
        log(f"Error generando embedding: {e}", "ERROR")
    return None

def restore_latex_backslashes(text: str) -> str:
    """Restaura comandos LaTeX que fueron corrompidos por secuencias de escape de control JSON o tokenización de Qwen."""
    if not isinstance(text, str) or not text:
        return text
    # 1. Restaurar escapes comunes de control JSON
    text = text.replace('\x08', '\\b')  # \b -> \begin, \beta, \bigg, \boxed
    text = text.replace('\x09', '\\t')  # \t -> \times, \theta, \text
    text = text.replace('\x0b', '\\v')  # \v -> \vec, \var
    text = text.replace('\x0d', '\\r')  # \r -> \right, \rho
    text = text.replace('\x0c', '\\f')  # \f -> \frac, \phi
    text = text.replace('\x07', '\\a')  # \a -> \alpha

    # 2. Corregir aberraciones de tokenización de Qwen (Vectores y raíces cuadradas)
    # Vectores s y t corrompidos en caracteres turcos/rumanos
    text = text.replace('ș', '\\vec{s}')
    text = text.replace('ş', '\\vec{s}')
    text = text.replace('Ț', '\\vec{t}')
    text = text.replace('ț', '\\vec{t}')
    text = text.replace('ţ', '\\vec{t}')
    
    # Raíces cuadradas (\sqrt{ ... }) corrompidas en símbolos fonéticos
    text = text.replace('ʇ', '\\sqrt{')
    text = text.replace('ʈ', '}')
    return text

def process_chunk_with_ollama(chunk_text: str, video_title: str, model_name: str) -> dict:
    """
    Envía un fragmento de la transcripción a qwen2-math para:
    1. Corregir cualquier desliz, error de cálculo o notación matemática/física.
    2. Eliminar saludos, comentarios informales o divagaciones no académicas.
    3. Clasificar por Asignatura, Tema y Nivel Educativo sugerido.
    """
    prompt = f"""Actúa como un profesor universitario experto de Matemáticas, Física y Economía.
Tu objetivo es transformar el siguiente fragmento de transcripción de clase titulado "{video_title}" en un contenido académico excepcional, riguroso, y sumamente detallado.

La transcripción proviene de reconocimiento por voz (ASR), por lo que puede contener deslices verbales, faltas de ortografía o ligeros errores aritméticos.

Sigue estrictamente estas pautas para generar el JSON:

1. **FIDELIDAD DE ESTILO PEDAGÓGICO**:
   * Sé extremadamente fiel a la forma de explicar y de estructurar la resolución del profesor en la transcripción. 
   * Explica los conceptos con un tono cálido, didáctico y profesional.
   
2. **PASOS INTERMEDIOS AL MÁXIMO DETALLE**:
   * Explica al máximo nivel de detalle cada uno de los pasos algebraicos, analíticos o lógicos necesarios para resolver los problemas planteados.
   * Si el profesor en el vídeo omitió algún paso de cálculo intermedio (reducción de términos, despeje, aplicación de una propiedad o identidad), tú DEBES expandir ese paso, escribirlo completo y explicar detalladamente qué propiedad, fórmula o teorema matemático se está aplicando en ese punto exacto. No dejes saltos lógicos inexplicados.

3. **DIVISIÓN EN PÁRRAFOS LÓGICOS**:
   * Divide y estructura el contenido descriptivo en párrafos lógicos, cortos y claros separados por doble salto de línea (`\\n\\n`). Evita a toda costa bloques de texto masivos e ilegibles.

4. **REGLA DE EXPRESIONES MATEMÁTICAS LARGAS**:
   * Las expresiones matemáticas complejas, ejemplos de cálculo, deducciones, matrices, sistemas de ecuaciones o demostraciones de varios pasos **NO deben ir incrustadas en medio de un párrafo de texto**.
   * En su lugar, **debes colocarlas siempre en su propia línea, completamente separadas del texto y centradas usando delimitadores de bloque de ecuación de doble dólar `$$...$$`**. El párrafo anterior debe finalizar con un punto o dos puntos, y luego el bloque matemático debe ir solo en su propia línea.

5. **LaTeX Y MATHJAX DE CALIDAD EDITORIAL**:
   * Cada una de las ecuaciones, fórmulas, variables aisladas, matrices o identidades DEBE estar formateada de manera impecable en LaTeX.
   * Usa `$...$` únicamente para variables o fórmulas muy cortas incrustadas en línea (por ejemplo: $x = 3$ o $f(x)$).
   * Usa `$$...$$` en líneas separadas para cualquier otra cosa.
   * Asegúrate de que todos los corchetes, llaves y delimitadores LaTeX estén perfectamente cerrados para que el motor MathJax de la web los renderice con absoluta perfección tipográfica sin roturas de código.

6. **CORRECCIÓN CIENTÍFICA**:
   * Identifica y enmienda cualquier desliz matemático, de cálculo o de notación física/química cometido en la transcripción. Si la transcripción dice una suma o producto erróneo, corrígelo, explícalo y guárdalo en la lista "errores_corregidos".

7. **ESTRUCTURA DE SALIDA**:
   * Si el fragmento no contiene sustancia académica o es puramente publicitario/divagación, escribe "N/A" en la clave "contenido_limpio".

Formatea tu respuesta estrictamente en JSON con la siguiente estructura:
{{
  "asignatura": "Asignatura (Matemáticas, Física, Química o Economía)",
  "tema": "Tema o título de la lección",
  "nivel": "Nivel escolar estimado (ej. Bachillerato, Universidad, ESO)",
  "contenido_limpio": "El contenido de la explicación depurado y redactado con el máximo nivel de detalle de pasos intermedios, párrafos estructurados con \\n\\n, explicaciones conceptuales paso a paso y fórmulas impecables de bloque con $$...$$.",
  "errores_corregidos": ["Lista corta de deslices o errores corregidos en este bloque. Si no hay ninguno, pon una lista vacía []"],
  "grafico_config": {{
    "tipo": "funcion" o "lineas",
    "titulo": "Título corto y claro del gráfico",
    "expresion": "fórmula_en_python (ej. x**2 - 4 o sin(x)). Rellenar solo si tipo es 'funcion'",
    "lineas": [
      {{"formula": "fórmula_en_python_1", "label": "etiqueta_1"}},
      {{"formula": "fórmula_en_python_2", "label": "etiqueta_2"}}
    ],
    "rango": [min_x, max_x],
    "etiqueta_x": "x",
    "etiqueta_y": "y"
  }}
}}
*Nota: La clave "grafico_config" es opcional. Inclúyela ÚNICAMENTE si el fragmento contiene explicaciones gráficas concretas, curvas, funciones matemáticas o problemas de optimización (como programación lineal) donde un gráfico sea altamente beneficioso.*

FRAGMENTO DE TRANSCRIPCIÓN A PROCESAR:
\"\"\"
{chunk_text}
\"\"\"

Responde ÚNICAMENTE con el bloque JSON válido, sin preámbulos, comentarios, etiquetas de código ni rodeos en markdown.
"""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=120
        )
        if r.status_code == 200:
            result = json.loads(r.json().get("response", "{}"))
            if "contenido_limpio" in result:
                result["contenido_limpio"] = restore_latex_backslashes(result["contenido_limpio"])
            return result
    except Exception as e:
        log(f"Error procesando fragmento con Ollama: {e}", "WARNING")
    
    return {
        "asignatura": "Sin clasificar",
        "tema": "Transcripción Cruda",
        "nivel": "Desconocido",
        "contenido_limpio": chunk_text,
        "errores_corregidos": []
    }

def generate_academic_plot(config: dict, output_path: str) -> bool:
    """Genera un gráfico científico altamente estético con temática oscura a partir de una configuración JSON."""
    try:
        # Configurar estilos premium de temática oscura
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        
        # Paleta de colores premium (Naranja, Cyan, Violeta de Chask Swarm)
        colors = ['#FF6600', '#00D4FF', '#7B2FF7', '#00F5D4', '#FF007F']
        
        tipo = config.get("tipo", "funcion")
        titulo = config.get("titulo", "Representación Gráfica")
        rango = config.get("rango", [-10, 10])
        etiqueta_x = config.get("etiqueta_x", "x")
        etiqueta_y = config.get("etiqueta_y", "y")
        
        # Asegurarse de que el rango sea válido
        if not isinstance(rango, list) or len(rango) < 2:
            rango = [-10, 10]
            
        x = np.linspace(rango[0], rango[1], 400)
        
        # Restringir variables globales para un eval() seguro
        safe_dict = {
            "x": x,
            "np": np,
            "sin": np.sin, "cos": np.cos, "tan": np.tan,
            "exp": np.exp, "log": np.log, "sqrt": np.sqrt,
            "pi": np.pi, "e": np.e
        }
        
        plot_done = False
        
        if tipo == "funcion" and "expresion" in config:
            expr = str(config["expresion"]).replace("^", "**") # Corregir sintaxis LaTeX/humana a python
            y = eval(expr, {"__builtins__": None}, safe_dict)
            ax.plot(x, y, label=f"$y = {config.get('expresion')}$", color=colors[0], linewidth=2)
            plot_done = True
            
        elif tipo == "lineas" and "lineas" in config:
            lines = config["lineas"]
            if isinstance(lines, list):
                for i, line in enumerate(lines):
                    if not isinstance(line, dict): continue
                    formula = line.get("formula", "").replace("^", "**")
                    label = line.get("label", f"L{i+1}")
                    if formula:
                        y = eval(formula, {"__builtins__": None}, safe_dict)
                        color = colors[i % len(colors)]
                        ax.plot(x, y, label=f"${label}$", color=color, linewidth=2)
                plot_done = True
            
        if not plot_done:
            plt.close()
            return False
            
        # Embellecer el gráfico estilo premium
        ax.set_title(titulo, fontsize=12, fontweight='bold', color='#ffffff', pad=15)
        ax.set_xlabel(etiqueta_x, fontsize=10, color='#a0a0c0')
        ax.set_ylabel(etiqueta_y, fontsize=10, color='#a0a0c0')
        
        # Cuadrícula sutil
        ax.grid(True, linestyle='--', alpha=0.15, color='#ffffff')
        
        # Ejes x e y marcados en el origen
        ax.axhline(0, color='#a0a0c0', linewidth=1, alpha=0.5)
        ax.axvline(0, color='#a0a0c0', linewidth=1, alpha=0.5)
        
        # Leyenda premium
        ax.legend(frameon=True, facecolor='#101026', edgecolor='rgba(255,255,255,0.05)', fontsize=9)
        
        # Ajustar márgenes y bordes
        for spine in ax.spines.values():
            spine.set_color('rgba(255,255,255,0.08)')
            
        plt.tight_layout()
        
        # Guardar en disco
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, bbox_inches='tight', transparent=True)
        plt.close()
        return True
    except Exception as e:
        log(f"Error generando gráfico: {e}", "WARNING")
        try: plt.close()
        except Exception: pass
        return False

def get_playlist_videos(url: str, cookies_path: str = None, max_videos: int = None) -> list[dict]:
    """Extrae la lista de vídeos de un canal o lista de reproducción sin descargarlos."""
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True
    }
    if cookies_path and os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    if max_videos:
        ydl_opts['playlistend'] = max_videos

    videos = []
    log(f"Analizando canal/lista de reproducción: {url}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                entries = info['entries']
                for entry in entries:
                    if not entry: continue
                    availability = entry.get("availability") or entry.get("privacy") or "public"
                    is_public = (availability == "public")
                    videos.append({
                        "id": entry["id"],
                        "title": entry.get("title", "Video sin título"),
                        "url": f"https://youtube.com/watch?v={entry['id']}",
                        "is_public": is_public
                    })
            else:
                availability = info.get("availability") or info.get("privacy") or "public"
                is_public = (availability == "public")
                videos.append({
                    "id": info["id"],
                    "title": info.get("title", "Video sin título"),
                    "url": f"https://youtube.com/watch?v={info['id']}",
                    "is_public": is_public
                })
        except Exception as e:
            log(f"Error al analizar el canal: {e}", "ERROR")
    return videos

def download_single_audio(video_id: str, cookies_path: str = None) -> tuple[str, str] | None:
    """Descarga el audio de un único vídeo en formato WAV y devuelve (ruta_archivo, directorio_temp)."""
    temp_dir = tempfile.mkdtemp()
    url = f"https://youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True
    }
    
    if cookies_path and os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            file_path = os.path.join(temp_dir, f"{video_id}.wav")
            if os.path.exists(file_path):
                return file_path, temp_dir
        except Exception as e:
            log(f"Error descargando el video {video_id}: {e}", "ERROR")
            try:
                shutil.rmtree(temp_dir)
            except Exception: pass
    return None

def chunk_transcript(segments: list, chunk_duration_sec: int = 180) -> list[dict]:
    """Agrupa segmentos de Whisper en fragmentos de aproximadamente N segundos con solapamiento."""
    chunks = []
    current_chunk_text = []
    current_start = 0.0
    current_duration = 0.0
    
    for seg in segments:
        text = seg.get("text", "").strip()
        start = seg.get("start", 0.0)
        end = seg.get("end", 0.0)
        duration = end - start
        
        if not text: continue
        
        current_chunk_text.append(text)
        current_duration += duration
        
        if current_duration >= chunk_duration_sec:
            chunks.append({
                "text": " ".join(current_chunk_text),
                "start": current_start,
                "end": end
            })
            current_chunk_text = [text]
            current_start = start
            current_duration = duration
            
    if current_chunk_text:
        chunks.append({
            "text": " ".join(current_chunk_text),
            "start": current_start,
            "end": current_start + current_duration
        })
        
    return chunks

def index_to_qdrant(qdrant_host: str, qdrant_port: int, collection_name: str, points: list):
    """Inserta los puntos indexados en Qdrant."""
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        log(f"Creando nueva colección vectorial '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        
    client.upsert(
        collection_name=collection_name,
        points=points
    )

def main():
    parser = argparse.ArgumentParser(description="Motor de Ingesta Checkpointed & Lazy de YouTube")
    parser.add_argument("--url", required=True, help="URL de video, playlist o canal de YouTube")
    parser.add_argument("--cookies", help="Ruta al archivo cookies.txt para videos ocultos o privados")
    parser.add_argument("--whisper-model", default="base", help="Tamaño del modelo de Whisper (tiny, base, small, medium, large)")
    parser.add_argument("--ollama-model", default="qwen2-math", help="Nombre del modelo Ollama local para la depuración")
    parser.add_argument("--collection", default="youtube_academic_knowledge", help="Colección de Qdrant donde guardar los vectores")
    parser.add_argument("--qdrant-host", default="localhost", help="Host del servicio de Qdrant")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Puerto de Qdrant")
    parser.add_argument("--chunk-size", type=int, default=180, help="Tamaño de fragmento en segundos para analizar con IA")
    parser.add_argument("--max-videos", type=int, help="Número máximo de vídeos a descargar e indexar (comenzando por el más reciente)")
    parser.add_argument("--private", action="store_true", help="Fuerza a omitir y eliminar enlaces o identificadores de vídeos ocultos/privados para proteger la privacidad de los alumnos.")
    args = parser.parse_args()

    log("=== INICIANDO PIPELINE DE APRENDIZAJE Y TRANSCRIPCIÓN LOCAL CHECKPOINTED ===")
    
    # 1. Validar Ollama y modelos
    log("Verificando conectividad local con Ollama...")
    if not test_ollama_model("nomic-embed-text"):
        log("[Error] El modelo 'nomic-embed-text' no está en Ollama. Ejecuta: ollama pull nomic-embed-text", "ERROR")
        sys.exit(1)
        
    log(f"Verificando modelo matemático '{args.ollama_model}'...")
    if not test_ollama_model(args.ollama_model):
        log(f"Modelo '{args.ollama_model}' no encontrado. Buscando fallbacks locales...", "WARNING")
        fallbacks = ["qwen2-math", "mathstral", "phi4", "deepseek-r1:8b", "qwen3:8b", "llama3.1:8b"]
        found_fallback = False
        for f in fallbacks:
            if test_ollama_model(f):
                args.ollama_model = f
                log(f"Aplicando modelo local disponible como fallback: {f}")
                found_fallback = True
                break
        if not found_fallback:
            log("[Error] No se ha encontrado ningún modelo local apto para procesamiento de texto. Ejecuta: ollama pull qwen2-math", "ERROR")
            sys.exit(1)

    # 2. Cargar historial de checkpoints
    checkpoint = load_checkpoint()
    indexed_video_ids = set(checkpoint.get("indexed_video_ids", []))
    log(f"Cargado historial de exclusión: {len(indexed_video_ids)} videos ya indexados.")

    # 3. Obtener lista de videos plana (lazy extraction)
    log("Extrayendo lista de videos de YouTube (sin descargar)...")
    videos = get_playlist_videos(args.url, args.cookies, args.max_videos)
    if not videos:
        log("No se pudo obtener la lista de videos. Verifica la URL de tu canal/playlist.", "ERROR")
        sys.exit(1)
        
    log(f"Encontrados un total de {len(videos)} videos en la lista.")

    def is_academic_title(title: str) -> bool:
        t = title.lower()
        blacklisted = [
            "anuncio", "promo", "publicidad", "patrocinado", "patrocinio",
            "comercial", "trailer", "tráiler", "teaser", "sorteo",
            "presentación del canal", "presentacion del canal", "aquí tu profe", "aquituprofe"
        ]
        return not any(kw in t for kw in blacklisted)

    # Filtrar videos que ya han sido procesados o que son anuncios/promociones
    videos_to_process = []
    for v in videos:
        if v["id"] in indexed_video_ids:
            continue
        if not is_academic_title(v["title"]):
            log(f"[OMITIDO] Omitiendo vídeo no académico/anuncio por título: '{v['title']}'", "INFO")
            indexed_video_ids.add(v["id"])
            checkpoint["indexed_video_ids"] = list(indexed_video_ids)
            save_checkpoint(checkpoint)
            continue
        videos_to_process.append(v)
        
    log(f"Vídeos pendientes de procesamiento tras aplicar exclusiones y filtros: {len(videos_to_process)}")
    
    if not videos_to_process:
        log("¡Felicidades! Todo el contenido académico de este canal ya ha sido procesado e indexado en Qdrant.")
        sys.exit(0)

    # 4. Cargar Whisper local
    log(f"Cargando modelo local de Whisper '{args.whisper_model}'...")
    try:
        model = whisper.load_model(args.whisper_model)
        log("Whisper inicializado de forma exitosa.")
    except Exception as e:
        log(f"Error cargando Whisper: {e}", "ERROR")
        sys.exit(1)

    point_id_counter = int(time.time())

    # 5. Loop de procesamiento perezoso (Lazy Processing)
    for idx, video in enumerate(videos_to_process, 1):
        log(f"==================================================")
        log(f"PROCESANDO VIDEO ({idx}/{len(videos_to_process)}): '{video['title']}'...")
        log(f"URL: {video['url']}")
        log(f"==================================================")
        
        # A. Descarga acústica perezosa (Single Download)
        log("Descargando pista acústica WAV...")
        dl_res = download_single_audio(video["id"], args.cookies)
        if not dl_res:
            log(f"No se pudo descargar el audio para '{video['title']}'. Saltando al siguiente.", "ERROR")
            continue
            
        wav_path, temp_dir = dl_res
        
        # B. Transcribir con Whisper
        log("Transcribiendo pista de audio con Whisper local...")
        try:
            result = model.transcribe(wav_path, verbose=False, language="es")
            segments = result.get("segments", [])
            log(f"Transcripción finalizada. Generados {len(segments)} segmentos acústicos.")
        except Exception as e:
            log(f"Error transcribiendo '{video['title']}': {e}", "ERROR")
            # Limpiar temporales
            try:
                shutil.rmtree(temp_dir)
            except Exception: pass
            continue
            
        # C. Segmentar
        chunks = chunk_transcript(segments, chunk_duration_sec=args.chunk_size)
        log(f"Dividida transcripción en {len(chunks)} fragmentos académicos.")
        
        video_points = []
        
        # D. Procesar cada fragmento
        for c_idx, chunk in enumerate(chunks, 1):
            log(f"  -> Procesando y depurando bloque {c_idx}/{len(chunks)} con {args.ollama_model}...")
            
            # Depuración de cháchara y corrección de deslices con qwen2-math
            academic_data = process_chunk_with_ollama(chunk["text"], video["title"], args.ollama_model)
            
            cleaned_text = academic_data.get("contenido_limpio", "").strip()
            
            # Filtro estricto de contenido no académico o vacío
            lower_clean = cleaned_text.lower()
            if not cleaned_text or lower_clean in ["n/a", "no aplicable", "no académico", "no academico", "ninguno", "no se puede determinar"] or len(cleaned_text) < 15:
                log(f"     🚫 Fragmento clasificado como No Académico o N/A. Omitiendo del índice vectorial.", "INFO")
                continue
                
            subject = academic_data.get("asignatura", "Matemáticas/Física")
            topic = academic_data.get("tema", "Lección sin título")
            level = academic_data.get("nivel", "Universidad/Secundaria")
            corrections = academic_data.get("errores_corregidos", [])
            
            if corrections:
                log(f"     ✅ ¡Errores corregidos por IA!: {', '.join(corrections)}")
                
            # Embeddings vectoriales
            embed_text = f"Asignatura: {subject}. Tema: {topic}. Nivel: {level}. Explicación: {cleaned_text}"
            vector = get_ollama_embedding(embed_text)
            
            if not vector:
                log("     ⚠️ Fallo de embedding en fragmento. Omitiendo punto.", "WARNING")
                continue
                
            point_id_counter += 1
            timestamp_str = f"{int(chunk['start'] // 60):02d}:{int(chunk['start'] % 60):02d}"
            
            # Proteger privacidad de los alumnos para vídeos ocultos o si se activa --private
            is_unlisted_or_private = (not video.get("is_public", True)) or args.private
            v_url = "" if is_unlisted_or_private else video["url"]
            v_id = "" if is_unlisted_or_private else video["id"]
            
            if is_unlisted_or_private and c_idx == 1:
                log("     🔒 Vídeo Privado/Oculto detectado. Eliminando enlaces e IDs para proteger la privacidad de los alumnos.", "INFO")
            
            # Generar gráfico si viene en la respuesta de la IA
            graph_image_path = ""
            grafico_config = academic_data.get("grafico_config")
            if grafico_config and isinstance(grafico_config, dict):
                graph_dir = r"C:\Program Files\Chask_Swarm\Advanced_Tools\uploads\graphs"
                graph_filename = f"graph_{point_id_counter}.png"
                graph_filepath = os.path.join(graph_dir, graph_filename)
                
                log(f"     📈 Generando gráfico científico: '{grafico_config.get('titulo', 'Representación')}'...")
                if generate_academic_plot(grafico_config, graph_filepath):
                    graph_image_path = f"/uploads/graphs/{graph_filename}"
                    log("     ✅ ¡Gráfico científico guardado en disco y enlazado con éxito!")
            
            payload = {
                "video_title": video["title"],
                "video_url": v_url,
                "video_id": v_id,
                "start_time": chunk["start"],
                "end_time": chunk["end"],
                "timestamp_tag": timestamp_str,
                "asignatura": subject,
                "tema": topic,
                "nivel": level,
                "contenido_original": chunk["text"],
                "contenido_depurado": cleaned_text,
                "correcciones_realizadas": corrections,
                "graph_image_path": graph_image_path,
                "ingested_at": datetime.now().isoformat()
            }
            
            point = PointStruct(
                id=point_id_counter,
                vector=vector,
                payload=payload
            )
            video_points.append(point)
            
        # E. Cargar puntos del video en Qdrant
        if video_points:
            log(f"Subiendo {len(video_points)} vectores del vídeo a Qdrant...")
            try:
                index_to_qdrant(
                    args.qdrant_host,
                    args.qdrant_port,
                    args.collection,
                    video_points
                )
                log(f"✅ ¡Video '{video['title']}' indexado correctamente en Qdrant!")
                
                # F. Registrar en Checkpoint
                checkpoint["indexed_video_ids"].append(video["id"])
                save_checkpoint(checkpoint)
                
            except Exception as e:
                log(f"Fallo al indexar puntos de '{video['title']}' en Qdrant: {e}", "ERROR")
        else:
            log(f"Omitiendo registro de checkpoint. No se generaron vectores válidos para '{video['title']}'.")

        # G. Limpiar archivos temporales de este vídeo
        try:
            shutil.rmtree(temp_dir)
            log("Limpieza de temporales completada.")
        except Exception:
            pass

    log("=== EJECUCIÓN DEL PIPELINE FINALIZADA CON ÉXITO ===")

if __name__ == "__main__":
    main()
