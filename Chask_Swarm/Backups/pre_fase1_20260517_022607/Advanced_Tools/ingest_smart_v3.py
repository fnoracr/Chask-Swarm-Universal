"""
ingest_smart_v3.py — Sistema de Ingesta Inteligente para Conocimiento RPA
==========================================================================
Versión 3 - Diseño robusto con:
  1. Filtro de páginas de error / sin contenido real
  2. Chunking por secciones Markdown (H2/H3) con respaldo por párrafos
  3. Extracción de palabras clave por TF-IDF local (sin IA)
  4. Enriquecimiento semántico del payload para mejor recuperación
  5. Deduplicación por hash de contenido
  6. Log detallado de qué se descarta y por qué

Uso:
  python ingest_smart_v3.py --reset            # Borra e indexa todo
  python ingest_smart_v3.py --limit 100        # Solo primeros 100 artículos
  python ingest_smart_v3.py                    # Continúa donde dejó
"""

import re
import os
import sys
import json
import time
import hashlib
import logging
import argparse
import unicodedata
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from sentence_transformers import SentenceTransformer

# ─── Configuración ────────────────────────────────────────────
BASE_RPA  = r"C:\Users\fnora\Desktop\Conocimiento RPA"
QDRANT_HOST     = "localhost"
QDRANT_PORT     = 6333
COLLECTION_NAME = "power_automate_deep"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM   = 384
MARKDOWN_FILE   = os.path.join(BASE_RPA, "Conocimiento_Profundo_RPA.md")
STATE_FILE      = os.path.join(BASE_RPA, "indexed_v3.json")
LOG_FILE        = os.path.join(BASE_RPA, "ingest_v3.log")
BATCH_SIZE      = 32

# Longitud mínima de contenido útil para indexar un chunk (en chars)
MIN_CHUNK_CHARS = 150
# Longitud mínima del artículo completo para considerarlo válido
MIN_ARTICLE_CHARS = 300

# ─── Stopwords para TF-IDF ────────────────────────────────────
STOPWORDS = {
    "de","la","el","en","y","a","que","los","las","un","una","es",
    "por","con","para","del","al","se","su","sus","más","si","no",
    "como","o","este","esta","estos","estas","puede","puede","cuando",
    "the","and","for","this","that","with","from","have","are","was",
    "will","you","your","not","can","its","also","http","www","es",
    "Ã","Â","acceso","página","requiere","autorización","intentar",
    "iniciar","sesión","cambiar","directorios","nota","siguiente"
}

# Patrones que identifican páginas SIN contenido real (páginas de error)
ERROR_PATTERNS = [
    r"El acceso a esta p[aá]gina requiere autorizaci[oó]n",
    r"This page requires authorization",
    r"Access to this page requires authentication",
    r"404\s*[-–]\s*Not Found",
    r"Page not found",
    r"Página no encontrada",
    r"403\s*Forbidden",
]

# Ruido de MS Learn a eliminar línea a línea
NOISE_LINES = {
    "Tabla de contenido", "Salir del modo de editor",
    "Preguntar a Learn", "Modo de lectura", "Leer en inglés",
    "Leer en ingl", "Agregar", "Agregar al plan", "Copiar Markdown",
    "Imprimir", "Comentarios", "¿Le ha resultado", "Sí No",
    "¿Necesita ayuda", "¿Sugerir una corrección",
    "Recursos adicionales", "Last updated on", "Siguiente",
    "Anterior", "Volver al inicio", "En este artículo",
    "Mostrar más", "Mostrar menos",
}

# ─── Logging ──────────────────────────────────────────────────
import io
_stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(_stdout_utf8),
    ]
)
log = logging.getLogger("ingest_v3")


# ─── Dataclasses ──────────────────────────────────────────────
@dataclass
class Article:
    index: int
    title: str
    url: str
    content: str           # Contenido limpio
    discard_reason: str = ""  # Vacío si es válido


@dataclass
class Chunk:
    article_index: int
    article_title: str
    article_url: str
    section: str
    content: str
    keywords: list[str] = field(default_factory=list)
    content_hash: str = ""


# ─── Utilidades ───────────────────────────────────────────────
def normalize(text: str) -> str:
    """Normaliza encoding y caracteres raros de scraping web."""
    # Intentar reparar el texto mal codificado (latin1 mal interpretado como utf-8)
    try:
        fixed = text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        fixed = text
    # Normalizar a NFC
    return unicodedata.normalize('NFC', fixed)


def hash_content(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def is_error_page(content: str) -> tuple[bool, str]:
    """Detecta páginas de error o sin contenido real."""
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True, f"Página de error detectada: '{pattern}'"
    return False, ""


def clean_content(raw: str) -> str:
    """Limpia el contenido de ruido de MS Learn."""
    lines = raw.split("\n")
    clean = []
    for line in lines:
        stripped = line.strip()
        # Saltar separadores solos
        if stripped == "---":
            continue
        # Saltar líneas de ruido exactas o que empiecen con ellas
        if any(stripped == noise or stripped.startswith(noise) for noise in NOISE_LINES):
            continue
        # Saltar links internos tipo [Leer en inglés](#)
        if re.match(r'^\[.{1,30}\]\(#\)$', stripped):
            continue
        # Saltar líneas que solo tienen un enlace markdown sin texto real
        if re.match(r'^\[.*?\]\(https?://.*?\)$', stripped) and len(stripped) < 80:
            continue
        clean.append(line)

    # Colapsar múltiples líneas vacías consecutivas en máximo 2
    result = re.sub(r'\n{3,}', '\n\n', "\n".join(clean))
    return result.strip()


def extract_keywords(text: str, top_n: int = 8) -> list[str]:
    """Extrae palabras clave por frecuencia ponderada (TF-IDF local simplificado)."""
    words = re.findall(r'\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{4,}\b', text.lower())
    freq = Counter(w for w in words if w not in STOPWORDS)
    # Priorizar palabras técnicas más largas (bonus por longitud)
    scored = {w: count * (1 + len(w) / 20) for w, count in freq.items()}
    top = sorted(scored, key=scored.get, reverse=True)[:top_n]
    return top


# ─── Parseo ───────────────────────────────────────────────────
def parse_articles(filepath: str) -> list[Article]:
    """Parsea el archivo Markdown y extrae artículos individuales."""
    log.info(f"📄 Leyendo {filepath}...")
    raw = Path(filepath).read_text(encoding="utf-8")

    parts = re.split(r"^## Origen:\s*(https?://[^\s\r\n]+)", raw, flags=re.MULTILINE)
    if len(parts) < 3:
        log.error("No se encontraron secciones '## Origen:' en el archivo.")
        sys.exit(1)

    articles = []
    for i in range(1, len(parts), 2):
        url   = parts[i].strip()
        body  = parts[i+1] if i+1 < len(parts) else ""
        idx   = (i // 2) + 1

        # Extraer título (primer H1 o H2)
        title_match = re.search(r"^#{1,2}\s+(.+)$", body, re.MULTILINE)
        title = normalize(title_match.group(1).strip()) if title_match else "Sin título"

        # Limpiar y normalizar el cuerpo
        content = normalize(clean_content(body))

        # Verificar si es página de error o vacía
        error, reason = is_error_page(content)
        if error:
            articles.append(Article(idx, title, url, "", discard_reason=reason))
            continue

        if len(content) < MIN_ARTICLE_CHARS:
            articles.append(Article(idx, title, url, "", discard_reason=f"Contenido insuficiente ({len(content)} chars)"))
            continue

        articles.append(Article(idx, title, url, content))

    valid   = sum(1 for a in articles if not a.discard_reason)
    invalid = len(articles) - valid
    log.info(f"✅ {valid} artículos válidos | ⚠️ {invalid} descartados")
    return articles


# ─── Chunking por secciones Markdown ──────────────────────────
def chunk_article(article: Article) -> list[Chunk]:
    """
    Divide un artículo en chunks por secciones H2/H3.
    Si una sección es muy grande (>600 palabras), la divide por párrafos.
    """
    chunks = []
    # Dividir por H2 (##) y H3 (###)
    sections = re.split(r'(?m)^(#{2,3}\s+.+)$', article.content)

    current_section = "Introducción"
    current_text    = []

    def flush(section_title: str, text_parts: list[str]):
        full_text = "\n".join(text_parts).strip()
        if len(full_text) < MIN_CHUNK_CHARS:
            return  # Descartar sección vacía o trivial

        # Si es muy larga, dividir por párrafos
        words = full_text.split()
        if len(words) > 600:
            paragraphs = re.split(r'\n\n+', full_text)
            buffer_words = 0
            buffer_paras = []
            sub_idx = 0
            for para in paragraphs:
                pw = len(para.split())
                if buffer_words + pw > 300 and buffer_paras:
                    _add_chunk(section_title, "\n\n".join(buffer_paras), sub_idx)
                    sub_idx += 1
                    buffer_paras = []
                    buffer_words = 0
                buffer_paras.append(para)
                buffer_words += pw
            if buffer_paras:
                _add_chunk(section_title, "\n\n".join(buffer_paras), sub_idx)
        else:
            _add_chunk(section_title, full_text, 0)

    def _add_chunk(section: str, text: str, sub_idx: int):
        if len(text.strip()) < MIN_CHUNK_CHARS:
            return
        kws  = extract_keywords(text)
        enriched = f"Artículo: {article.title}\nURL: {article.url}\nSección: {section}\n\n{text}"
        chunks.append(Chunk(
            article_index=article.index,
            article_title=article.title,
            article_url=article.url,
            section=section,
            content=enriched,
            keywords=kws,
            content_hash=hash_content(enriched)
        ))

    for part in sections:
        if re.match(r'^#{2,3}\s+', part):
            # Nueva sección: vaciar buffer anterior
            flush(current_section, current_text)
            current_section = normalize(part.lstrip('#').strip())
            current_text    = []
        else:
            current_text.append(part)

    flush(current_section, current_text)  # Último bloque

    return chunks


# ─── Indexación ───────────────────────────────────────────────
def index_chunks(client: QdrantClient, model: SentenceTransformer,
                 chunks: list[Chunk], seen_hashes: set, start_id: int) -> tuple[int, int]:
    """Vectoriza e inserta chunks en Qdrant. Retorna (insertados, duplicados)."""
    new_chunks = [c for c in chunks if c.content_hash not in seen_hashes]
    dupes      = len(chunks) - len(new_chunks)

    if not new_chunks:
        return 0, dupes

    texts      = [c.content for c in new_chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    points = []
    for i, (chunk, emb) in enumerate(zip(new_chunks, embeddings)):
        points.append(PointStruct(
            id=start_id + i,
            vector=emb.tolist(),
            payload={
                "article_title": chunk.article_title,
                "article_url":   chunk.article_url,
                "section":       chunk.section,
                "keywords":      chunk.keywords,
                "content":       chunk.content,
                "content_hash":  chunk.content_hash,
            }
        ))
        seen_hashes.add(chunk.content_hash)

    # Insertar en lotes
    for i in range(0, len(points), BATCH_SIZE):
        client.upsert(collection_name=COLLECTION_NAME, points=points[i:i+BATCH_SIZE])

    return len(new_chunks), dupes


# ─── Main ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Borra y recrea la colección")
    parser.add_argument("--limit", type=int, default=0, help="Limitar número de artículos (0 = todos)")
    args = parser.parse_args()

    log.info("🚀 Ingesta Smart V3 iniciada")
    log.info(f"   Archivo: {MARKDOWN_FILE}")
    log.info(f"   Colección: {COLLECTION_NAME}")

    # Cargar estado previo
    state = {}
    if os.path.exists(STATE_FILE) and not args.reset:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    seen_hashes    = set(state.get("hashes", []))
    indexed_urls   = set(state.get("urls", []))

    # Conectar Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in collections and args.reset:
        log.info(f"🗑️  Borrando colección {COLLECTION_NAME}...")
        client.delete_collection(COLLECTION_NAME)
        seen_hashes = set()
        indexed_urls = set()
    if COLLECTION_NAME not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        log.info(f"✅ Colección {COLLECTION_NAME} creada")

    # Cargar modelo de embeddings (GPU si disponible)
    log.info(f"🧠 Cargando modelo de embeddings: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Parsear artículos
    all_articles = parse_articles(MARKDOWN_FILE)

    # Filtrar solo los nuevos y válidos
    valid_articles  = [a for a in all_articles if not a.discard_reason]
    new_articles    = [a for a in valid_articles if a.url not in indexed_urls]

    if args.limit > 0:
        new_articles = new_articles[:args.limit]

    total = len(new_articles)
    log.info(f"📚 Artículos a indexar en esta sesión: {total}")

    # Estadísticas de descarte
    discarded = [a for a in all_articles if a.discard_reason]
    for d in discarded[:10]:  # Solo mostramos los primeros 10 en log
        log.info(f"⚠️  DESCARTADO [{d.index}] {d.url[:60]}... → {d.discard_reason}")
    if len(discarded) > 10:
        log.info(f"   ... y {len(discarded) - 10} más descartados.")

    # Procesar
    point_id    = client.get_collection(COLLECTION_NAME).points_count
    total_ins   = 0
    total_dupes = 0
    errors      = 0

    for i, article in enumerate(new_articles):
        try:
            chunks = chunk_article(article)
            if not chunks:
                log.info(f"[{i+1}/{total}] Sin chunks válidos: {article.title[:50]}")
                continue

            inserted, dupes = index_chunks(client, model, chunks, seen_hashes, point_id)
            point_id   += inserted
            total_ins  += inserted
            total_dupes += dupes

            indexed_urls.add(article.url)

            log.info(
                f"[{i+1}/{total}] ✅ {article.title[:45]:<45} | "
                f"chunks={len(chunks)} ins={inserted} dup={dupes} "
                f"kw={chunks[0].keywords[:3] if chunks else []}"
            )

            # Guardar estado cada 10 artículos
            if (i + 1) % 10 == 0:
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"hashes": list(seen_hashes), "urls": list(indexed_urls)}, f)

        except Exception as e:
            log.error(f"[{i+1}/{total}] ❌ Error en artículo {article.title[:40]}: {e}")
            errors += 1

    # Guardar estado final
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"hashes": list(seen_hashes), "urls": list(indexed_urls)}, f)

    log.info("=" * 60)
    log.info(f"🏁 INGESTA COMPLETADA")
    log.info(f"   Artículos procesados : {total}")
    log.info(f"   Puntos insertados    : {total_ins}")
    log.info(f"   Duplicados omitidos  : {total_dupes}")
    log.info(f"   Errores              : {errors}")
    log.info(f"   Total en colección   : {client.get_collection(COLLECTION_NAME).points_count}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
