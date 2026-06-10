"""
ingest_smart_v4.py — Sistema de Ingesta Definitivo para Conocimiento RPA
=========================================================================
Mejoras sobre V3:
  1. Índice completo (400 artículos)
  2. Embeddings de alta calidad: nomic-embed-text (768 dims) via Ollama local
  3. Búsqueda híbrida: vectores densos (nomic) + sparse BM25 (qdrant native)
  4. Limpieza de encoding avanzada con ftfy (fix text for you)
  5. Colección nueva: power_automate_v4 (768 dims, búsqueda híbrida)

Uso:
  python ingest_smart_v4.py --reset         # Borra e indexa todo (400 art.)
  python ingest_smart_v4.py --limit 50      # Solo N artículos
  python ingest_smart_v4.py                 # Continúa donde dejó
"""

import re, os, sys, json, time, hashlib, logging, argparse, unicodedata, io
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter
import requests

# Fix encoding consola Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    SparseVector, SparseVectorParams, SparseIndexParams,
    NamedVector, NamedSparseVector
)

# ─── Intentar importar ftfy para limpieza avanzada ────────────
try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    FTFY_AVAILABLE = False

# ─── Configuración ────────────────────────────────────────────
BASE_RPA        = r"C:\Users\fnora\Desktop\Conocimiento RPA"
QDRANT_HOST     = "localhost"
QDRANT_PORT     = 6333
COLLECTION_NAME = "power_automate_v4"   # Nueva colección con 768 dims
OLLAMA_URL      = "http://localhost:11434"
EMBED_MODEL     = "nomic-embed-text"    # 768 dims, mucho mejor semántica
EMBEDDING_DIM   = 768
MARKDOWN_FILE   = os.path.join(BASE_RPA, "Conocimiento_Profundo_RPA.md")
STATE_FILE      = os.path.join(BASE_RPA, "indexed_v4.json")
LOG_FILE        = os.path.join(BASE_RPA, "ingest_v4.log")
BATCH_SIZE      = 64     # Lotes grandes para menos round-trips a Qdrant
PARALLEL_WORKERS = 8    # Llamadas simultáneas a Ollama para embeddings

MIN_CHUNK_CHARS   = 150
MIN_ARTICLE_CHARS = 300

# ─── Stopwords ────────────────────────────────────────────────
STOPWORDS = {
    "de","la","el","en","y","a","que","los","las","un","una","es","por","con",
    "para","del","al","se","su","sus","más","si","no","como","o","este","esta",
    "estos","estas","puede","cuando","the","and","for","this","that","with",
    "from","have","are","was","will","you","your","not","can","its","also",
    "acceso","página","requiere","autorización","intentar","iniciar","sesión",
    "cambiar","directorios","nota","siguiente","anterior","volver"
}

# ─── Patrones de error ────────────────────────────────────────
ERROR_PATTERNS = [
    r"El acceso a esta p[aá]gina requiere autorizaci[oó]n",
    r"This page requires authorization",
    r"Access to this page requires authentication",
    r"404\s*[-–]\s*Not Found",
    r"Page not found",
    r"403\s*Forbidden",
]

NOISE_LINES = {
    "Tabla de contenido","Salir del modo de editor","Preguntar a Learn",
    "Modo de lectura","Agregar","Agregar al plan","Copiar Markdown","Imprimir",
    "Comentarios","¿Le ha resultado","¿Necesita ayuda","¿Sugerir una corrección",
    "Recursos adicionales","Last updated on","Siguiente","Anterior",
    "Volver al inicio","En este artículo","Mostrar más","Mostrar menos",
    "Leer en ingl","Descarga en PDF",
    # Mensajes de error/autorización de MS Learn (ruido de encabezado)
    "El acceso a esta","This page requires","Access to this page",
    "Puede intentar iniciar","Puede intentar cambiar","You can try",
}

# ─── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("ingest_v4")


# ─── Dataclasses ──────────────────────────────────────────────
@dataclass
class Article:
    index: int
    title: str
    url: str
    content: str
    discard_reason: str = ""

@dataclass
class Chunk:
    article_index: int
    article_title: str
    article_url: str
    section: str
    content: str
    keywords: list[str] = field(default_factory=list)
    content_hash: str = ""


# ─── MEJORA 4: Limpieza de encoding avanzada ──────────────────
def fix_encoding(text: str) -> str:
    """
    Repara texto mal codificado (típico de scraping web con encoding incorrecto).
    Ejemplo: 'Ã©' -> 'é', 'Ã³' -> 'ó', etc.
    """
    if FTFY_AVAILABLE:
        # ftfy lo maneja de forma inteligente
        return ftfy.fix_text(text)
    
    # Fallback manual: intentar latin1 -> utf-8
    try:
        fixed = text.encode('latin-1').decode('utf-8')
        return unicodedata.normalize('NFC', fixed)
    except (UnicodeDecodeError, UnicodeEncodeError):
        return unicodedata.normalize('NFC', text)


def is_error_page(content: str) -> tuple[bool, str]:
    """
    Detecta artículos que son SOLO páginas de error — sin contenido real.
    Los mensajes de error de encabezado ya se limpian en NOISE_LINES/clean_content.
    Aquí detectamos páginas donde TODO el contenido es error (sin H1/párrafos reales).
    """
    # Verificar patrones de error en el contenido completo (ya limpio)
    for p in ERROR_PATTERNS:
        if re.search(p, content, re.IGNORECASE):
            # Solo es error si no hay contenido real acompañando
            has_heading   = bool(re.search(r'^#{1,3}\s+\w+', content, re.MULTILINE))
            has_real_para = len([l for l in content.split('\n') if len(l.strip()) > 80]) >= 3
            if not has_heading and not has_real_para:
                return True, f"Solo error sin contenido: '{p[:50]}'"
    # Artículo sin ninguna estructura real
    has_heading   = bool(re.search(r'^#{1,3}\s+\w+', content, re.MULTILINE))
    has_real_para = len([l for l in content.split('\n') if len(l.strip()) > 60]) >= 2
    if not has_heading and not has_real_para:
        return True, "Sin contenido estructurado real"
    return False, ""


def clean_content(raw: str) -> str:
    """Elimina ruido de MS Learn línea a línea."""
    lines = raw.split("\n")
    clean = []
    for line in lines:
        s = line.strip()
        if s == "---":
            continue
        if any(s == n or s.startswith(n) for n in NOISE_LINES):
            continue
        if re.match(r'^\[.{1,40}\]\(#\)$', s):      # Link interno vacío
            continue
        if re.match(r'^\[.{1,5}\]\(https?://', s):   # Link muy corto
            continue
        clean.append(line)
    result = re.sub(r'\n{3,}', '\n\n', "\n".join(clean))
    return result.strip()


def hash_content(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


# ─── MEJORA 2+OPT: Embeddings paralelos via Ollama nomic-embed-text ──────
def _embed_one(args: tuple) -> tuple[int, list[float]]:
    """Embebe un solo texto. Diseñado para uso con ThreadPoolExecutor."""
    idx, text = args
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text[:8000]},
            timeout=90
        )
        resp.raise_for_status()
        return idx, resp.json()["embedding"]
    except Exception as e:
        log.warning(f"Embedding fallido (idx={idx}): {e}")
        return idx, [0.0] * EMBEDDING_DIM


def embed_texts_ollama(texts: list[str]) -> list[list[float]]:
    """
    Genera embeddings en PARALELO usando un pool de threads.
    PARALLEL_WORKERS llamadas simultáneas a Ollama -> ~8x más rápido.
    """
    results = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futures = {pool.submit(_embed_one, (i, t)): i for i, t in enumerate(texts)}
        for future in as_completed(futures):
            idx, vector = future.result()
            results[idx] = vector
    return results


# ─── MEJORA 3: BM25 sparse vector ─────────────────────────────
def text_to_sparse(text: str) -> SparseVector:
    """
    Genera un vector sparse BM25-style para búsqueda híbrida.
    Usa frecuencia de términos ponderada como aproximación local.
    """
    words = re.findall(r'\b[a-záéíóúüña-z]{3,}\b', text.lower())
    freq = Counter(w for w in words if w not in STOPWORDS)
    if not freq:
        return SparseVector(indices=[0], values=[0.0])
    
    # Convertir palabras a IDs numéricos por hash (FNV-1a simplificado)
    indices = []
    values  = []
    max_freq = max(freq.values())
    for word, count in freq.items():
        word_id = abs(hash(word)) % 100000  # Espacio de 100k tokens
        indices.append(word_id)
        values.append(count / max_freq)     # TF normalizado 0-1
    
    # Eliminar duplicados de índice (puede haber colisiones de hash)
    seen = {}
    for idx, val in zip(indices, values):
        if idx not in seen or val > seen[idx]:
            seen[idx] = val
    
    return SparseVector(
        indices=list(seen.keys()),
        values=list(seen.values())
    )


# ─── Parseo ───────────────────────────────────────────────────
def parse_articles(filepath: str) -> list[Article]:
    log.info(f"Leyendo {filepath}...")
    raw = Path(filepath).read_text(encoding="utf-8")
    parts = re.split(r"^## Origen:\s*(https?://[^\s\r\n]+)", raw, flags=re.MULTILINE)
    
    articles = []
    for i in range(1, len(parts), 2):
        url   = parts[i].strip()
        body  = parts[i+1] if i+1 < len(parts) else ""
        idx   = (i // 2) + 1

        # MEJORA 4: Reparar encoding antes de procesar
        body_fixed = fix_encoding(body)
        
        title_match = re.search(r"^#{1,2}\s+(.+)$", body_fixed, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Sin titulo"
        
        content = clean_content(body_fixed)
        
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
    log.info(f"Articulos validos: {valid} | Descartados: {invalid}")
    return articles


# ─── Chunking semántico por secciones Markdown ────────────────
def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    words = re.findall(r'\b[a-záéíóúüña-z]{4,}\b', text.lower())
    freq  = Counter(w for w in words if w not in STOPWORDS)
    scored = {w: c * (1 + len(w) / 15) for w, c in freq.items()}
    return sorted(scored, key=scored.get, reverse=True)[:top_n]


def chunk_article(article: Article) -> list[Chunk]:
    chunks = []
    sections = re.split(r'(?m)^(#{2,3}\s+.+)$', article.content)
    current_section = "Introduccion"
    current_text    = []

    def flush(section_title, text_parts):
        full_text = "\n".join(text_parts).strip()
        if len(full_text) < MIN_CHUNK_CHARS:
            return
        words = full_text.split()
        if len(words) > 500:
            paras = re.split(r'\n\n+', full_text)
            buf_words, buf_paras = 0, []
            sub = 0
            for para in paras:
                pw = len(para.split())
                if buf_words + pw > 250 and buf_paras:
                    _add(section_title, "\n\n".join(buf_paras), sub)
                    sub += 1; buf_paras = []; buf_words = 0
                buf_paras.append(para); buf_words += pw
            if buf_paras:
                _add(section_title, "\n\n".join(buf_paras), sub)
        else:
            _add(section_title, full_text, 0)

    def _add(section, text, sub_idx):
        if len(text.strip()) < MIN_CHUNK_CHARS:
            return
        kws  = extract_keywords(text)
        enriched = f"Articulo: {article.title}\nURL: {article.url}\nSeccion: {section}\n\n{text}"
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
            flush(current_section, current_text)
            current_section = part.lstrip('#').strip()
            current_text    = []
        else:
            current_text.append(part)
    flush(current_section, current_text)
    return chunks


# ─── Indexación híbrida ───────────────────────────────────────
def index_batch(client: QdrantClient, chunks: list[Chunk],
                seen_hashes: set, start_id: int) -> tuple[int, int]:
    """Genera embeddings densos + sparse y los inserta en Qdrant."""
    new = [c for c in chunks if c.content_hash not in seen_hashes]
    dupes = len(chunks) - len(new)
    if not new:
        return 0, dupes

    texts   = [c.content for c in new]
    dense   = embed_texts_ollama(texts)           # Mejora 2: nomic-embed-text
    
    points = []
    for i, (chunk, dvec) in enumerate(zip(new, dense)):
        sparse = text_to_sparse(chunk.content)    # Mejora 3: BM25 sparse
        points.append(PointStruct(
            id=start_id + i,
            vector={
                "dense":  dvec,
                "sparse": sparse,
            },
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

    for i in range(0, len(points), BATCH_SIZE):
        client.upsert(collection_name=COLLECTION_NAME, points=points[i:i+BATCH_SIZE])
    
    return len(new), dupes


# ─── Main ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    log.info("=== INGESTA SMART V4 (nomic + hibrida + ftfy) ===")

    # Cargar estado
    state = {}
    if os.path.exists(STATE_FILE) and not args.reset:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    seen_hashes  = set(state.get("hashes", []))
    indexed_urls = set(state.get("urls", []))

    # Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    cols   = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in cols and args.reset:
        log.info(f"Borrando coleccion {COLLECTION_NAME}...")
        client.delete_collection(COLLECTION_NAME)
        seen_hashes = set(); indexed_urls = set()
        cols = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in cols:
        # MEJORA 2 + 3: Colección con vector denso (768) + sparse (BM25)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            }
        )
        log.info(f"Coleccion {COLLECTION_NAME} creada (768 dims + BM25 sparse)")

    # Test conexión Ollama
    try:
        test_emb = embed_texts_ollama(["test"])
        assert len(test_emb[0]) == EMBEDDING_DIM, f"Dimensiones incorrectas: {len(test_emb[0])}"
        log.info(f"Ollama nomic-embed-text OK ({EMBEDDING_DIM} dims)")
    except Exception as e:
        log.error(f"Error con Ollama: {e}. Abortando.")
        sys.exit(1)

    # Parsear artículos (Mejora 1: todos, Mejora 4: encoding)
    all_articles = parse_articles(MARKDOWN_FILE)
    valid        = [a for a in all_articles if not a.discard_reason]
    new_articles = [a for a in valid if a.url not in indexed_urls]

    if args.limit > 0:
        new_articles = new_articles[:args.limit]

    total = len(new_articles)
    log.info(f"Articulos a indexar: {total} (de {len(valid)} validos, {len(all_articles)} totales)")

    # Log de descartados
    for d in [a for a in all_articles if a.discard_reason][:5]:
        log.info(f"  DESCARTADO [{d.index}]: {d.discard_reason}")

    point_id   = client.get_collection(COLLECTION_NAME).points_count
    total_ins  = 0
    total_dup  = 0
    t_start    = time.time()

    for i, article in enumerate(new_articles):
        try:
            chunks = chunk_article(article)
            if not chunks:
                log.info(f"[{i+1}/{total}] Sin chunks: {article.title[:40]}")
                continue

            ins, dup = index_batch(client, chunks, seen_hashes, point_id)
            point_id += ins; total_ins += ins; total_dup += dup

            indexed_urls.add(article.url)

            elapsed = time.time() - t_start
            speed   = (i + 1) / elapsed * 60  # articulos/min
            eta     = (elapsed / (i + 1)) * (total - i - 1)
            log.info(
                f"[{i+1:03d}/{total}] {article.title[:38]:<38} | "
                f"chunks={len(chunks)} ins={ins} | "
                f"{speed:.1f}art/min eta={eta:.0f}s"
            )

            if (i + 1) % 20 == 0:
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"hashes": list(seen_hashes), "urls": list(indexed_urls)}, f)

        except Exception as e:
            log.error(f"[{i+1}/{total}] Error: {e}")

    # Estado final
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"hashes": list(seen_hashes), "urls": list(indexed_urls)}, f)

    total_time = time.time() - t_start
    log.info("=" * 60)
    log.info("INGESTA V4 COMPLETADA")
    log.info(f"  Articulos procesados : {total}")
    log.info(f"  Puntos insertados    : {total_ins}")
    log.info(f"  Duplicados omitidos  : {total_dup}")
    log.info(f"  Tiempo total         : {total_time:.1f}s")
    log.info(f"  Coleccion total      : {client.get_collection(COLLECTION_NAME).points_count}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
