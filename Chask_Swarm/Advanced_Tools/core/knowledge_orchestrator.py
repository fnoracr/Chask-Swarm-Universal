"""
knowledge_orchestrator.py — Director del Sistema Universal de Conocimiento
===========================================================================
Orquesta todo el pipeline de aprendizaje profundo:
  1. Detecta temas recurrentes en conversación
  2. Genera el mensaje de oferta al usuario
  3. Lanza scraping + ingesta en background
  4. Enriquece las respuestas con el conocimiento indexado

Integrado con llm_router.py para búsqueda automática en colecciones.

Uso desde llm_router:
    from knowledge_orchestrator import KnowledgeOrchestrator
    orch = KnowledgeOrchestrator()
    
    # Antes de responder: detectar tema y buscar conocimiento relevante
    context = orch.process_query(user_query)
    if context.offer_message:
        # Añadir oferta al inicio de la respuesta
    if context.rag_context:
        # Añadir contexto RAG al system prompt
"""

import os
import re
import sys
import json
import time
import logging
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path

import requests

log = logging.getLogger("knowledge_orchestrator")

# ─── Importar módulos del enjambre ────────────────────────────
try:
    from topic_detector import TopicDetector, KNOWN_SOURCES
    DETECTOR_OK = True
except ImportError:
    DETECTOR_OK = False
    log.warning("topic_detector no disponible")

# ─── Configuración ────────────────────────────────────────────
QDRANT_HOST      = "localhost"
QDRANT_PORT      = 6333
OLLAMA_URL       = "http://localhost:11434"
EMBED_MODEL      = "nomic-embed-text"
EMBEDDING_DIM    = 768
TOP_K_CONTEXT    = 4    # Chunks de contexto RAG a recuperar
SCORE_THRESHOLD  = 0.35 # Score mínimo para usar un resultado

BASE_KNOWLEDGE   = r"C:\Users\fnora\Desktop\Enjambre Datos\knowledge_bases"
TOOLS_DIR        = r"C:\Program Files\Chask_Swarm\Advanced_Tools"
JOBS_FILE        = os.path.join(TOOLS_DIR, "knowledge_jobs.json")


# ─── Dataclasses ──────────────────────────────────────────────
@dataclass
class QueryContext:
    """Contexto enriquecido para una query del usuario."""
    offer_message: str = ""        # Mensaje de oferta de base de conocimiento
    rag_context: str = ""          # Contexto RAG recuperado de colecciones
    sources_used: list[str] = field(default_factory=list)
    topic_detected: str = ""
    collection_used: str = ""


@dataclass
class KnowledgeJob:
    """Trabajo de creación de base de conocimiento."""
    topic: str
    collection: str
    sources: list[str]
    status: str = "pending"      # pending | scraping | indexing | done | error
    progress: int = 0
    created_at: float = 0.0
    message: str = ""


# ─── Orquestador ──────────────────────────────────────────────
class KnowledgeOrchestrator:

    def __init__(self):
        self.detector = TopicDetector() if DETECTOR_OK else None
        self.jobs     = self._load_jobs()

        # Conectar Qdrant (lazy)
        self._qdrant = None
        self._known_collections = set()
        self._refresh_collections()

    def _load_jobs(self) -> dict:
        if os.path.exists(JOBS_FILE):
            try:
                with open(JOBS_FILE, encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_jobs(self):
        with open(JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, ensure_ascii=False, indent=2)

    def _get_qdrant(self):
        if not self._qdrant:
            try:
                from qdrant_client import QdrantClient
                self._qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            except Exception as e:
                log.error(f"No se puede conectar a Qdrant: {e}")
        return self._qdrant

    def _refresh_collections(self):
        """Actualiza el set de colecciones disponibles."""
        client = self._get_qdrant()
        if client:
            try:
                self._known_collections = {
                    c.name for c in client.get_collections().collections
                }
            except Exception:
                pass

    def _embed_query(self, text: str) -> list[float] | None:
        """Genera embedding para una query."""
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text[:4000]},
                timeout=30
            )
            return resp.json()["embedding"]
        except Exception as e:
            log.warning(f"Error embedding query: {e}")
            return None

    def _search_collection(self, query: str, collection: str) -> list[dict]:
        """Busca en una colección con auto-detección de formato."""
        client = self._get_qdrant()
        if not client or collection not in self._known_collections:
            return []

        # Saltar colecciones vacías
        try:
            info = client.get_collection(collection)
            if info.points_count == 0:
                return []
        except Exception:
            return []

        dvec = self._embed_query(query)
        if not dvec:
            return []

        try:
            from qdrant_client.models import SparseVector, Prefetch, FusionQuery, Fusion
            import re
            from collections import Counter

            # Sparse vector
            words = re.findall(r'\b[a-záéíóúüña-z]{3,}\b', query.lower())
            freq  = Counter(words)
            max_f = max(freq.values()) if freq else 1
            seen  = {}
            for w, c in freq.items():
                idx = abs(hash(w)) % 100000
                val = c / max_f
                if idx not in seen or val > seen[idx]:
                    seen[idx] = val
            svec = SparseVector(
                indices=list(seen.keys()),
                values=list(seen.values())
            )

            # Intento 1: Colección V4 híbrida (dense + sparse)
            try:
                response = client.query_points(
                    collection_name=collection,
                    prefetch=[
                        Prefetch(query=dvec,  using="dense",  limit=TOP_K_CONTEXT*2),
                        Prefetch(query=svec,  using="sparse", limit=TOP_K_CONTEXT*2),
                    ],
                    query=FusionQuery(fusion=Fusion.RRF),
                    limit=TOP_K_CONTEXT,
                    with_payload=True
                )
                return [
                    {"content": h.payload.get("content",""),
                     "title":   h.payload.get("article_title",""),
                     "url":     h.payload.get("article_url",""),
                     "section": h.payload.get("section",""),
                     "score":   h.score}
                    for h in response.points if h.score >= SCORE_THRESHOLD
                ]
            except Exception:
                pass

            # Intento 2: Colección con vector nombrado "dense" solo
            try:
                response = client.query_points(
                    collection_name=collection,
                    query=dvec,
                    using="dense",
                    limit=TOP_K_CONTEXT,
                    with_payload=True
                )
                return [
                    {"content": h.payload.get("content",""),
                     "title":   h.payload.get("article_title",""),
                     "url":     h.payload.get("article_url",""),
                     "score":   h.score}
                    for h in response.points if h.score >= SCORE_THRESHOLD
                ]
            except Exception:
                pass

            # Intento 3: Colección legacy (vector sin nombre)
            response = client.query_points(
                collection_name=collection,
                query=dvec,
                limit=TOP_K_CONTEXT,
                with_payload=True
            )
            return [
                {"content": h.payload.get("content",""),
                 "title":   h.payload.get("article_title",""),
                 "url":     h.payload.get("article_url",""),
                 "score":   h.score}
                for h in response.points if h.score >= SCORE_THRESHOLD
            ]

        except Exception as e:
            log.debug(f"Búsqueda fallida en {collection}: {e}")
            return []


    def _find_best_collection(self, query: str) -> tuple[str, list[dict]]:
        """
        Busca en TODAS las colecciones disponibles y devuelve la que
        tenga los mejores resultados para la query dada.
        """
        self._refresh_collections()
        best_collection = ""
        best_results    = []
        best_score      = 0.0

        for col in self._known_collections:
            results = self._search_collection(query, col)
            if results and results[0]["score"] > best_score:
                best_score      = results[0]["score"]
                best_collection = col
                best_results    = results

        return best_collection, best_results

    def _build_rag_context(self, results: list[dict]) -> str:
        """Formatea los resultados RAG en contexto para el LLM."""
        if not results:
            return ""
        parts = ["### Contexto de conocimiento indexado:\n"]
        for i, r in enumerate(results[:TOP_K_CONTEXT], 1):
            title   = r.get("title", "")
            section = r.get("section", "")
            url     = r.get("url", "")
            content = r.get("content", "")
            # Limpiar el preámbulo del chunk (Artículo:, URL:, etc.)
            content_clean = re.sub(r'^(Tema|Artículo|URL|Sección|Palabras clave):.*\n', '',
                                   content, flags=re.MULTILINE).strip()
            parts.append(f"**[{i}] {title}** — {section}")
            if url:
                parts.append(f"Fuente: {url}")
            parts.append(content_clean[:800])
            parts.append("")
        return "\n".join(parts)

    def _build_offer_message(self, topic: str, count: int,
                              collection: str, sources: list[str],
                              already_indexed: bool) -> str:
        """Genera el mensaje de oferta de base de conocimiento."""
        if already_indexed:
            return (
                f"💡 Ya tengo una base de conocimiento sobre **{topic}** "
                f"disponible en mi memoria. La estoy usando en esta respuesta."
            )

        sources_str = "\n".join(f"  • {s}" for s in sources[:3])
        return (
            f"💡 He notado que me has preguntado sobre **{topic}** {count} veces. "
            f"¿Quieres que cree una **base de conocimiento profundo** sobre este tema?\n\n"
            f"Haré lo siguiente:\n"
            f"1. Scrapear y descargar documentación oficial\n"
            f"2. Indexarla en mi memoria vectorial con búsqueda híbrida\n"
            f"3. Usarla automáticamente en todas tus preguntas futuras\n\n"
            f"Fuentes que usaré:\n{sources_str}\n\n"
            f"Responde **'sí, crea la base de {topic}'** para activarlo."
        )

    # ─── API Principal ────────────────────────────────────────
    def process_query(self, user_query: str,
                      search_all: bool = True) -> QueryContext:
        """
        Procesa una query del usuario:
        1. Detecta si hay tema recurrente (ofrece KB)
        2. Busca contexto RAG en colecciones disponibles
        """
        context = QueryContext()

        # 1. Detección de tema recurrente
        if self.detector:
            result = self.detector.analyze(user_query)
            if result.should_offer:
                context.offer_message = self._build_offer_message(
                    topic=result.topic,
                    count=result.count,
                    collection=result.collection_name,
                    sources=result.suggested_sources,
                    already_indexed=result.already_indexed
                )
                context.topic_detected = result.topic

        # 2. Búsqueda RAG en colecciones disponibles
        if search_all and self._known_collections:
            col, results = self._find_best_collection(user_query)
            if results:
                context.rag_context  = self._build_rag_context(results)
                context.collection_used = col
                context.sources_used = [r.get("url", "") for r in results if r.get("url")]

        return context

    def start_knowledge_pipeline(self, topic: str, sources: list[str],
                                  collection: str) -> str:
        """
        Inicia el pipeline completo de scraping + ingesta en background.
        Devuelve el ID del job para seguimiento.
        """
        job_id = f"job_{int(time.time())}_{re.sub(r'[^a-z0-9]', '_', topic.lower())}"
        self.jobs[job_id] = {
            "topic": topic, "collection": collection,
            "sources": sources, "status": "starting",
            "progress": 0, "created_at": time.time(), "message": ""
        }
        self._save_jobs()

        # Lanzar en thread background
        thread = threading.Thread(
            target=self._run_pipeline,
            args=(job_id, topic, sources, collection),
            daemon=True
        )
        thread.start()
        log.info(f"Pipeline iniciado: job_id={job_id} topic='{topic}'")
        return job_id

    def _run_pipeline(self, job_id: str, topic: str,
                      sources: list[str], collection: str):
        """Ejecuta el pipeline completo de forma asíncrona."""
        def update_job(status, progress, message=""):
            self.jobs[job_id]["status"]   = status
            self.jobs[job_id]["progress"] = progress
            self.jobs[job_id]["message"]  = message
            self._save_jobs()

        try:
            # FASE 1: Scraping
            update_job("scraping", 10, f"Iniciando scraping de {len(sources)} fuentes...")
            safe = re.sub(r'[^a-z0-9_]', '_', topic.lower())
            output_file = os.path.join(BASE_KNOWLEDGE, safe, f"{safe}_knowledge.md")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            scraper_cmd = [
                sys.executable,
                os.path.join(BASE_DIR, "skills", "utilities", "universal_scraper.py"),
                "--topic", topic,
                "--urls", *sources,
                "--depth", "2",
                "--pages", "150",
            ]
            result = subprocess.run(scraper_cmd, capture_output=True,
                                    text=True, timeout=1800)
            if result.returncode != 0:
                update_job("error", 0, f"Error scraping: {result.stderr[:200]}")
                return

            update_job("indexing", 50, "Scraping completado. Iniciando indexación...")

            # FASE 2: Ingesta
            from universal_ingest import run_ingest
            stats = run_ingest(topic, output_file, collection, reset=True)

            if "error" in stats:
                update_job("error", 0, stats["error"])
                return

            # FASE 3: Marcar como indexado
            if self.detector:
                self.detector.mark_as_indexed(collection)
            self._refresh_collections()

            msg = (f"Base de conocimiento '{topic}' creada: "
                   f"{stats['points_inserted']} puntos en '{collection}'")
            update_job("done", 100, msg)
            log.info(f"Pipeline completado: {msg}")

            # Notificar por Telegram si está disponible
            try:
                subprocess.Popen([
                    sys.executable,
                    os.path.join(r"C:\Program Files\Chask_Swarm", "charm_telegram.py"),
                    "send",
                    f"✅ Base de conocimiento '{topic}' lista: "
                    f"{stats['points_inserted']} fragmentos indexados."
                ])
            except Exception:
                pass

        except Exception as e:
            update_job("error", 0, str(e))
            log.error(f"Error en pipeline {job_id}: {e}")

    def get_job_status(self, job_id: str) -> dict:
        return self.jobs.get(job_id, {"status": "not_found"})

    def list_jobs(self) -> list[dict]:
        return [{"id": k, **v} for k, v in self.jobs.items()]

    def list_collections(self) -> list[dict]:
        """Lista todas las colecciones de conocimiento disponibles."""
        self._refresh_collections()
        client = self._get_qdrant()
        result = []
        if client:
            for col in self._known_collections:
                try:
                    info = client.get_collection(col)
                    result.append({
                        "name": col,
                        "points": info.points_count,
                    })
                except Exception:
                    pass
        return sorted(result, key=lambda x: x["points"], reverse=True)


# ─── Función de integración para llm_router ───────────────────
_orchestrator_instance = None

def get_orchestrator() -> KnowledgeOrchestrator:
    """Singleton del orquestador para uso en llm_router."""
    global _orchestrator_instance
    if not _orchestrator_instance:
        _orchestrator_instance = KnowledgeOrchestrator()
    return _orchestrator_instance


def enrich_prompt(user_query: str, system_prompt: str) -> tuple[str, str]:
    """
    Función de integración lista para usar en llm_router.py:
    
        from knowledge_orchestrator import enrich_prompt
        system, offer = enrich_prompt(user_query, current_system)
        if offer:
            prepend offer to response
    
    Devuelve (system_prompt_enriquecido, mensaje_de_oferta)
    """
    try:
        orch    = get_orchestrator()
        context = orch.process_query(user_query)

        enriched_system = system_prompt
        if context.rag_context:
            enriched_system = f"{system_prompt}\n\n{context.rag_context}"

        return enriched_system, context.offer_message
    except Exception as e:
        log.error(f"Error en enrich_prompt: {e}")
        return system_prompt, ""


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--query",   help="Probar detección de tema")
    parser.add_argument("--create",  help="Crear base de conocimiento para tema")
    parser.add_argument("--status",  help="Ver estado de un job")
    parser.add_argument("--list",    action="store_true", help="Listar colecciones")
    args = parser.parse_args()

    orch = KnowledgeOrchestrator()

    if args.list:
        print("\nColecciones disponibles:")
        for col in orch.list_collections():
            print(f"  {col['name']:<40} {col['points']:>6} puntos")

    elif args.query:
        ctx = orch.process_query(args.query)
        if ctx.offer_message:
            print(f"\nOFERTA:\n{ctx.offer_message}")
        if ctx.rag_context:
            print(f"\nCONTEXTO RAG (colección: {ctx.collection_used}):\n{ctx.rag_context[:500]}...")
        if not ctx.offer_message and not ctx.rag_context:
            print("Sin oferta ni contexto RAG disponible.")

    elif args.create:
        topic  = args.create
        sources = KNOWN_SOURCES.get(topic.lower(), [])
        if not sources:
            print(f"No se encontraron fuentes para '{topic}'")
        else:
            col    = f"kb_{re.sub(r'[^a-z0-9_]', '_', topic.lower())}"
            job_id = orch.start_knowledge_pipeline(topic, sources, col)
            print(f"Pipeline iniciado: job_id={job_id}")
            # Esperar y mostrar progreso
            while True:
                status = orch.get_job_status(job_id)
                print(f"  [{status['status']}] {status['progress']}% — {status['message']}")
                if status['status'] in ('done', 'error'):
                    break
                time.sleep(10)

    elif args.status:
        print(json.dumps(orch.get_job_status(args.status), indent=2))
