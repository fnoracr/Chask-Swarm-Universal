"""
universal_ingest.py — Motor de Ingesta Universal para Cualquier Colección
=========================================================================
Versión generalizada de ingest_smart_v4.py.
Indexa cualquier archivo Markdown en cualquier colección de Qdrant
usando nomic-embed-text (768 dims) + BM25 híbrido + deduplicación.

Uso:
  python universal_ingest.py --topic "Docker" --file "ruta/al/knowledge.md"
  python universal_ingest.py --topic "Docker" --reset
  python universal_ingest.py --list   # Lista todas las colecciones indexadas
"""

import re, os, sys, json, time, hashlib, logging, argparse, io
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    SparseVector, SparseVectorParams, SparseIndexParams,
)

try:
    import ftfy
    FTFY_OK = True
except ImportError:
    FTFY_OK = False

# ─── Configuración global ─────────────────────────────────────
QDRANT_HOST      = "localhost"
QDRANT_PORT      = 6333
OLLAMA_URL       = "http://localhost:11434"
EMBED_MODEL      = "nomic-embed-text"
EMBEDDING_DIM    = 768
PARALLEL_WORKERS = 8
BATCH_SIZE       = 64
MIN_CHUNK_CHARS  = 150
MIN_ART_CHARS    = 300
BASE_KNOWLEDGE   = r"C:\Users\fnora\Desktop\Enjambre Datos\knowledge_bases"

STOPWORDS = {
    "de","la","el","en","y","a","que","los","las","un","una","es","por","con",
    "para","del","al","se","su","sus","más","si","no","como","o","este","esta",
    "cuando","the","and","for","this","that","with","from","have","are","not",
    "can","its","also","will","you","your","their","they","been","has","had",
}

# ─── Noise de MS Learn y webs de documentación ────────────────
NOISE_LINES = {
    "Tabla de contenido","Salir del modo de editor","Preguntar a Learn",
    "Modo de lectura","Agregar","Agregar al plan","Copiar Markdown","Imprimir",
    "Comentarios","Recursos adicionales","Last updated on","Siguiente","Anterior",
    "Volver al inicio","En este artículo","Mostrar más","Mostrar menos",
    "Leer en ingl","Descarga en PDF","El acceso a esta","This page requires",
    "Access to this page","Puede intentar","You can try","Skip to main content",
    "Skip to content","Table of contents","On this page","In this article",
    "Was this helpful","Give feedback","Edit this page","View on GitHub",
    "Previous","Next","Back to top","Share this","Print","Copy",
}


# ─── Logging ──────────────────────────────────────────────────
def setup_logging(log_file: str):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger("universal_ingest")


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


# ─── Utilidades ───────────────────────────────────────────────
def fix_text(text: str) -> str:
    if FTFY_OK:
        return ftfy.fix_text(text)
    return text

def hash_content(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def clean_content(raw: str) -> str:
    lines = raw.split("\n")
    clean = []
    for line in lines:
        s = line.strip()
        if s == "---":
            continue
        if any(s == n or s.startswith(n) for n in NOISE_LINES):
            continue
        if re.match(r'^\[.{1,40}\]\(#\)$', s):
            continue
        clean.append(line)
    return re.sub(r'\n{3,}', '\n\n', "\n".join(clean)).strip()

def is_garbage(content: str) -> tuple[bool, str]:
    """Detecta contenido sin valor real."""
    has_heading   = bool(re.search(r'^#{1,3}\s+\w+', content, re.MULTILINE))
    has_real_para = len([l for l in content.split('\n') if len(l.strip()) > 60]) >= 2
    if not has_heading and not has_real_para:
        return True, "Sin estructura real"
    # Ratio de palabras únicas vs totales (texto muy repetitivo = basura)
    words = re.findall(r'\b\w+\b', content.lower())
    if words and len(set(words)) / len(words) < 0.15:
        return True, "Contenido muy repetitivo (posible nav/menu)"
    return False, ""

def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    words = re.findall(r'\b[a-záéíóúüña-z]{4,}\b', text.lower())
    freq  = Counter(w for w in words if w not in STOPWORDS)
    scored = {w: c * (1 + len(w) / 15) for w, c in freq.items()}
    return sorted(scored, key=scored.get, reverse=True)[:top_n]

def text_to_sparse(text: str) -> SparseVector:
    words = re.findall(r'\b[a-záéíóúüña-z]{3,}\b', text.lower())
    freq  = Counter(w for w in words if w not in STOPWORDS)
    if not freq:
        return SparseVector(indices=[0], values=[0.0])
    max_f = max(freq.values())
    seen  = {}
    for w, c in freq.items():
        idx = abs(hash(w)) % 100000
        val = c / max_f
        if idx not in seen or val > seen[idx]:
            seen[idx] = val
    return SparseVector(indices=list(seen.keys()), values=list(seen.values()))


# ─── Embeddings paralelos ─────────────────────────────────────
def _embed_one(args: tuple) -> tuple[int, list[float]]:
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
        logging.warning(f"Embedding fallido idx={idx}: {e}")
        return idx, [0.0] * EMBEDDING_DIM

def embed_parallel(texts: list[str]) -> list[list[float]]:
    results = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futures = {pool.submit(_embed_one, (i, t)): i for i, t in enumerate(texts)}
        for f in as_completed(futures):
            idx, vec = f.result()
            results[idx] = vec
    return results


# ─── Parseo de Markdown ───────────────────────────────────────
def parse_markdown(filepath: str, log) -> list[Article]:
    """
    Parsea un archivo Markdown con formato ## Origen: URL
    Compatible con los archivos generados por universal_scraper.py
    """
    log.info(f"Leyendo {filepath}...")
    raw   = Path(filepath).read_text(encoding="utf-8")
    raw   = fix_text(raw)
    parts = re.split(r"^## Origen:\s*(https?://[^\s\r\n]+)", raw, flags=re.MULTILINE)

    if len(parts) < 3:
        # Intentar formato alternativo sin URL (artículos separados por ##)
        parts_alt = re.split(r"^## (.+)$", raw, flags=re.MULTILINE)
        articles = []
        for i in range(1, len(parts_alt), 2):
            title   = parts_alt[i].strip()
            body    = parts_alt[i+1] if i+1 < len(parts_alt) else ""
            content = clean_content(fix_text(body))
            if len(content) >= MIN_ART_CHARS:
                ok, reason = is_garbage(content)
                if not ok:
                    articles.append(Article(i//2+1, title, "", content))
        log.info(f"Formato alternativo: {len(articles)} artículos")
        return articles

    articles = []
    for i in range(1, len(parts), 2):
        url     = parts[i].strip()
        body    = parts[i+1] if i+1 < len(parts) else ""
        idx     = (i // 2) + 1
        body_fx = fix_text(body)

        title_m = re.search(r"^#{1,2}\s+(.+)$", body_fx, re.MULTILINE)
        title   = title_m.group(1).strip() if title_m else f"Artículo {idx}"

        content = clean_content(body_fx)

        garbage, reason = is_garbage(content)
        if garbage or len(content) < MIN_ART_CHARS:
            articles.append(Article(idx, title, url, "",
                discard_reason=reason or f"Corto ({len(content)} chars)"))
            continue

        articles.append(Article(idx, title, url, content))

    valid   = sum(1 for a in articles if not a.discard_reason)
    invalid = len(articles) - valid
    log.info(f"Artículos válidos: {valid} | Descartados: {invalid}")
    return articles


# ─── Chunking ─────────────────────────────────────────────────
def chunk_article(article: Article, topic: str) -> list[Chunk]:
    chunks   = []
    sections = re.split(r'(?m)^(#{2,3}\s+.+)$', article.content)
    cur_sect = "Introducción"
    cur_text = []

    def flush(sect, parts):
        full = "\n".join(parts).strip()
        if len(full) < MIN_CHUNK_CHARS:
            return
        words = full.split()
        if len(words) > 400:
            paras = re.split(r'\n\n+', full)
            buf, bw, sub = [], 0, 0
            for p in paras:
                pw = len(p.split())
                if bw + pw > 200 and buf:
                    _add(sect, "\n\n".join(buf), sub, topic)
                    sub += 1; buf = []; bw = 0
                buf.append(p); bw += pw
            if buf:
                _add(sect, "\n\n".join(buf), sub, topic)
        else:
            _add(sect, full, 0, topic)

    def _add(sect, text, sub, topic):
        if len(text.strip()) < MIN_CHUNK_CHARS:
            return
        kws  = extract_keywords(text)
        rich = (f"Tema: {topic}\n"
                f"Artículo: {article.title}\n"
                f"URL: {article.url}\n"
                f"Sección: {sect}\n"
                f"Palabras clave: {', '.join(kws[:5])}\n\n"
                f"{text}")
        chunks.append(Chunk(
            article_index=article.index,
            article_title=article.title,
            article_url=article.url,
            section=sect,
            content=rich,
            keywords=kws,
            content_hash=hash_content(rich)
        ))

    for part in sections:
        if re.match(r'^#{2,3}\s+', part):
            flush(cur_sect, cur_text)
            cur_sect = part.lstrip('#').strip()
            cur_text = []
        else:
            cur_text.append(part)
    flush(cur_sect, cur_text)
    return chunks


# ─── Indexación ───────────────────────────────────────────────
def ensure_collection(client: QdrantClient, name: str, log):
    cols = [c.name for c in client.get_collections().collections]
    if name not in cols:
        client.create_collection(
            collection_name=name,
            vectors_config={
                "dense": VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))
            }
        )
        log.info(f"Colección creada: {name} (768 dims + BM25)")

def index_batch(client, chunks, collection, seen_hashes, start_id, log):
    new   = [c for c in chunks if c.content_hash not in seen_hashes]
    dupes = len(chunks) - len(new)
    if not new:
        return 0, dupes

    texts     = [c.content for c in new]
    embeddings = embed_parallel(texts)

    points = []
    for i, (chunk, dvec) in enumerate(zip(new, embeddings)):
        sparse = text_to_sparse(chunk.content)
        points.append(PointStruct(
            id=start_id + i,
            vector={"dense": dvec, "sparse": sparse},
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
        client.upsert(collection_name=collection, points=points[i:i+BATCH_SIZE])
    return len(new), dupes


# ─── Main ─────────────────────────────────────────────────────
def run_ingest(topic: str, filepath: str, collection: str,
               reset: bool = False, limit: int = 0) -> dict:
    """
    Función principal llamable desde código o CLI.
    Devuelve dict con estadísticas de la ingesta.
    """
    safe = re.sub(r'[^a-z0-9_]', '_', topic.lower())
    log_file = os.path.join(BASE_KNOWLEDGE, safe, "ingest.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log = setup_logging(log_file)

    state_file = os.path.join(BASE_KNOWLEDGE, safe, "ingest_state.json")
    state = {}
    if os.path.exists(state_file) and not reset:
        with open(state_file, encoding='utf-8') as f:
            state = json.load(f)
    seen_hashes  = set(state.get("hashes", []))
    indexed_urls = set(state.get("urls", []))

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    if reset:
        cols = [c.name for c in client.get_collections().collections]
        if collection in cols:
            client.delete_collection(collection)
            log.info(f"Colección borrada: {collection}")
        seen_hashes = set(); indexed_urls = set()
    ensure_collection(client, collection, log)

    # Test Ollama
    try:
        test = embed_parallel(["test"])
        assert len(test[0]) == EMBEDDING_DIM
        log.info(f"Ollama OK — {EMBED_MODEL} ({EMBEDDING_DIM} dims)")
    except Exception as e:
        log.error(f"Ollama no disponible: {e}")
        return {"error": str(e)}

    # Parsear
    all_articles = parse_markdown(filepath, log)
    valid        = [a for a in all_articles if not a.discard_reason]
    new_arts     = [a for a in valid if a.url not in indexed_urls]
    if limit > 0:
        new_arts = new_arts[:limit]

    total     = len(new_arts)
    point_id  = client.get_collection(collection).points_count
    total_ins = 0; total_dup = 0; errors = 0
    t_start   = time.time()

    log.info(f"Indexando {total} artículos en colección '{collection}'")

    for i, article in enumerate(new_arts):
        try:
            chunks = chunk_article(article, topic)
            if not chunks:
                continue
            ins, dup = index_batch(client, chunks, collection, seen_hashes, point_id, log)
            point_id += ins; total_ins += ins; total_dup += dup
            indexed_urls.add(article.url)

            elapsed = time.time() - t_start
            speed   = (i+1) / elapsed * 60
            eta     = (elapsed / (i+1)) * (total - i - 1)
            log.info(f"[{i+1:03d}/{total}] {article.title[:40]:<40} | "
                     f"chunks={len(chunks)} ins={ins} | "
                     f"{speed:.1f}art/min eta={eta:.0f}s")

            if (i+1) % 20 == 0:
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump({"hashes": list(seen_hashes), "urls": list(indexed_urls)}, f)
        except Exception as e:
            log.error(f"Error en artículo {i+1}: {e}")
            errors += 1

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump({"hashes": list(seen_hashes), "urls": list(indexed_urls)}, f)

    total_time = time.time() - t_start
    final_count = client.get_collection(collection).points_count
    stats = {
        "topic": topic, "collection": collection,
        "articles_processed": total,
        "points_inserted": total_ins,
        "duplicates_skipped": total_dup,
        "errors": errors,
        "total_in_collection": final_count,
        "time_seconds": round(total_time, 1),
    }
    log.info("=" * 55)
    log.info(f"INGESTA COMPLETADA: {total_ins} puntos en '{collection}'")
    log.info("=" * 55)
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic",      required=True, help="Nombre del tema")
    parser.add_argument("--file",       help="Ruta al archivo Markdown de conocimiento")
    parser.add_argument("--collection", help="Nombre de colección Qdrant (auto si no se indica)")
    parser.add_argument("--reset",      action="store_true")
    parser.add_argument("--limit",      type=int, default=0)
    parser.add_argument("--list",       action="store_true", help="Listar colecciones")
    args = parser.parse_args()

    if args.list:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        cols   = client.get_collections().collections
        print("\nColecciones de conocimiento en Qdrant:")
        for c in cols:
            info = client.get_collection(c.name)
            print(f"  {c.name:<35} {info.points_count:>6} puntos")
        return

    collection = args.collection or f"kb_{re.sub(r'[^a-z0-9_]', '_', args.topic.lower())}"
    filepath   = args.file

    if not filepath:
        # Buscar archivo automáticamente
        safe = re.sub(r'[^a-z0-9_]', '_', args.topic.lower())
        filepath = os.path.join(BASE_KNOWLEDGE, safe, f"{safe}_knowledge.md")
        if not os.path.exists(filepath):
            print(f"No se encontró el archivo de conocimiento para '{args.topic}'")
            print(f"Ejecuta primero: python universal_scraper.py --topic \"{args.topic}\"")
            sys.exit(1)

    stats = run_ingest(args.topic, filepath, collection,
                       reset=args.reset, limit=args.limit)
    print(f"\nEstadísticas finales: {json.dumps(stats, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
