"""
chask_operational_memory.py — Sistema de Memoria Operativa V2.0
================================================================
Memoria vectorial en tiempo real con Qdrant + Ollama embeddings (nomic-embed-text 768d).

Colecciones:
  - chask_operations: Todo lo que Enjambre hace (éxitos, fallos, soluciones)
  - chask_system_files: Copias versionadas de los ficheros core del sistema
  - chask_skills: Skills, artifacts y herramientas creadas

Uso desde CLI:
  python chask_operational_memory.py log "descripción" --result success --keywords "k1,k2" --project "panel"
  python chask_operational_memory.py recall "inyección stealth falla"
  python chask_operational_memory.py snapshot                    # versiona todos los ficheros core
  python chask_operational_memory.py history chask_stealth_injector.py  # historial de un fichero

Uso desde código (para integrar en el flujo de Enjambre):
  from chask_operational_memory import OperationalMemory
  mem = OperationalMemory()
  mem.log_operation(...)
  mem.recall(...)
"""

import os
import sys
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path

# ── Dependencias ──
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

try:
    import requests as req
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Configuración ──
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
VECTOR_DIM = 768

COLLECTIONS = {
    "operations": "chask_operations",
    "files": "chask_system_files",
    "skills": "chask_skills",
}

# Ficheros core del sistema Chask Swarm
CORE_DIR = r"C:\Program Files\Chask_Swarm"
TOOLS_DIR = os.path.join(CORE_DIR, "Advanced_Tools")

CORE_FILES = [
    # Raíz
    os.path.join(CORE_DIR, "soul.md"),
    os.path.join(CORE_DIR, "memory.md"),
    os.path.join(CORE_DIR, "directives.md"),
    os.path.join(CORE_DIR, "security.md"),
    os.path.join(CORE_DIR, "charm_panel.py"),
    os.path.join(CORE_DIR, "charm_panel_ui.html"),
    os.path.join(CORE_DIR, "panel_launcher.py"),
    os.path.join(CORE_DIR, "unified_daemon.py"),
    os.path.join(CORE_DIR, "Advanced_Tools", "Daemons", "process_watchdog.py"),
    os.path.join(CORE_DIR, "charm_telegram.py"),
    os.path.join(CORE_DIR, "charm_discord.py"),
    os.path.join(CORE_DIR, "Configuracion", "channels_config.json"),
    os.path.join(CORE_DIR, "Configuracion", "authorized_users.json"),
    os.path.join(CORE_DIR, "Configuracion", "master_credentials.json"),
    # Advanced Tools
    os.path.join(TOOLS_DIR, "chask_stealth_injector.py"),
    os.path.join(TOOLS_DIR, "llm_router.py"),
    os.path.join(TOOLS_DIR, "evolutionary_memory.py"),
    os.path.join(TOOLS_DIR, "qdrant_memory_manager.py"),
    os.path.join(TOOLS_DIR, "chask_operational_memory.py"),
    os.path.join(TOOLS_DIR, "reflection_engine.py"),
    os.path.join(TOOLS_DIR, "skill_catalog.py"),
    os.path.join(TOOLS_DIR, "knowledge_orchestrator.py"),
    os.path.join(TOOLS_DIR, "chask_mcp_server.py"),
    os.path.join(TOOLS_DIR, "hive_mind_executor.py"),
    os.path.join(TOOLS_DIR, "mode_router.py"),
    os.path.join(TOOLS_DIR, "channel_adapter.py"),
    os.path.join(TOOLS_DIR, "slash_commands.py"),
    os.path.join(TOOLS_DIR, "audit_logger.py"),
    os.path.join(TOOLS_DIR, "sandbox.py"),
    os.path.join(TOOLS_DIR, "privacy_engine.py"),
    os.path.join(TOOLS_DIR, "backup_system.py"),
]


class OperationalMemory:
    """Motor de memoria operativa con embeddings reales (nomic-embed-text 768d)."""

    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        if not HAS_QDRANT:
            print("[OpMem] qdrant_client no instalado")
            return
        try:
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=5)
            self._ensure_collections()
        except Exception as e:
            print(f"[OpMem] No se pudo conectar a Qdrant: {e}")
            self.client = None

    def _ensure_collections(self):
        """Crea las colecciones si no existen."""
        if not self.client:
            return
        existing = {c.name for c in self.client.get_collections().collections}
        for key, name in COLLECTIONS.items():
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE)
                )
                print(f"[OpMem] Colección '{name}' creada")

    def _embed(self, text: str) -> list:
        """Genera embedding con nomic-embed-text via Ollama."""
        if not HAS_REQUESTS:
            return self._fallback_embed(text)
        try:
            r = req.post(f"{OLLAMA_URL}/api/embeddings", json={
                "model": EMBED_MODEL,
                "prompt": text
            }, timeout=30)
            if r.status_code == 200:
                vec = r.json().get("embedding", [])
                if len(vec) == VECTOR_DIM:
                    return vec
        except Exception as e:
            print(f"[OpMem] Embedding error: {e}")
        return self._fallback_embed(text)

    def _fallback_embed(self, text: str) -> list:
        """Fallback: pseudo-vector basado en hash (para cuando Ollama no está disponible)."""
        h = hashlib.sha512(text.encode()).digest()
        vec = [float(b) / 255.0 for b in h]
        while len(vec) < VECTOR_DIM:
            h = hashlib.sha512(h).digest()
            vec.extend(float(b) / 255.0 for b in h)
        return vec[:VECTOR_DIM]

    def _gen_id(self) -> int:
        return int(time.time() * 1000) % (2**63 - 1)

    # ═══════════════════════════════════════════════════════
    # 1. OPERACIONES (log de todo lo que hace Enjambre)
    # ═══════════════════════════════════════════════════════
    def log_operation(self, description: str, approach: str = "",
                      result: str = "success", keywords: list = None,
                      project: str = "general", error_msg: str = "",
                      solution: str = "", files_involved: list = None):
        """
        Registra una operación completa en la memoria vectorial.

        Args:
            description: Qué se quería conseguir
            approach: Cómo se abordó el problema
            result: "success" | "failure" | "partial"
            keywords: Lista de palabras clave para recuperación rápida
            project: Nombre del proyecto/contexto
            error_msg: Mensaje de error si falló
            solution: Solución aplicada si se resolvió
            files_involved: Lista de ficheros modificados
        """
        if not self.client:
            return False

        keywords = keywords or []
        files_involved = files_involved or []
        now = datetime.now().isoformat()

        # Texto enriquecido para embedding (máxima recuperabilidad)
        embed_text = f"""
Objetivo: {description}
Enfoque: {approach}
Resultado: {result}
Palabras clave: {', '.join(keywords)}
Proyecto: {project}
Error: {error_msg}
Solución: {solution}
Archivos: {', '.join(files_involved)}
""".strip()

        vector = self._embed(embed_text)

        payload = {
            "description": description,
            "approach": approach,
            "result": result,
            "keywords": keywords,
            "project": project,
            "error_msg": error_msg,
            "solution": solution,
            "files_involved": files_involved,
            "timestamp": now,
            "embed_text": embed_text[:500],
        }

        self.client.upsert(
            collection_name=COLLECTIONS["operations"],
            points=[PointStruct(id=self._gen_id(), vector=vector, payload=payload)]
        )
        status = "[OK]" if result == "success" else "[FAIL]" if result == "failure" else "[WARN]"
        print(f"[OpMem] {status} Operación registrada: {description[:60]}...")
        return True

    def recall(self, query: str, limit: int = 5, result_filter: str = None) -> list:
        """
        Recupera operaciones pasadas relevantes a una consulta.

        Args:
            query: Descripción del problema actual
            limit: Número máximo de resultados
            result_filter: Filtrar por "success", "failure", o None para todos
        """
        if not self.client:
            return []

        vector = self._embed(query)
        filters = None
        if result_filter:
            filters = Filter(must=[
                FieldCondition(key="result", match=MatchValue(value=result_filter))
            ])

        try:
            results = self.client.query_points(
                collection_name=COLLECTIONS["operations"],
                query=vector,
                query_filter=filters,
                limit=limit,
                with_payload=True
            ).points
        except AttributeError:
            results = self.client.search(
                collection_name=COLLECTIONS["operations"],
                query_vector=vector,
                query_filter=filters,
                limit=limit
            )

        memories = []
        for r in results:
            p = r.payload
            memories.append({
                "score": round(r.score, 3) if hasattr(r, 'score') else 0,
                "description": p.get("description", ""),
                "approach": p.get("approach", ""),
                "result": p.get("result", ""),
                "solution": p.get("solution", ""),
                "error_msg": p.get("error_msg", ""),
                "keywords": p.get("keywords", []),
                "project": p.get("project", ""),
                "timestamp": p.get("timestamp", ""),
                "files": p.get("files_involved", []),
            })
        return memories

    def recall_failures(self, query: str, limit: int = 5) -> list:
        """Recupera solo los fallos pasados (para evitar repetir errores)."""
        return self.recall(query, limit=limit, result_filter="failure")

    def recall_successes(self, query: str, limit: int = 5) -> list:
        """Recupera solo los éxitos pasados (para replicar soluciones)."""
        return self.recall(query, limit=limit, result_filter="success")

    # ═══════════════════════════════════════════════════════
    # 2. FICHEROS VERSIONADOS (snapshots del sistema)
    # ═══════════════════════════════════════════════════════
    def snapshot_file(self, filepath: str, version_note: str = ""):
        """Guarda una copia versionada de un fichero en Qdrant."""
        if not self.client or not os.path.exists(filepath):
            return False

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        filename = os.path.basename(filepath)
        file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        now = datetime.now().isoformat()

        embed_text = f"Archivo: {filename}\nRuta: {filepath}\nNota: {version_note}\nContenido (primeros 500 chars): {content[:500]}"
        vector = self._embed(embed_text)

        payload = {
            "filename": filename,
            "filepath": filepath,
            "content": content,
            "hash": file_hash,
            "size_bytes": len(content.encode()),
            "version_note": version_note,
            "timestamp": now,
            "lines": content.count("\n") + 1,
        }

        self.client.upsert(
            collection_name=COLLECTIONS["files"],
            points=[PointStruct(id=self._gen_id(), vector=vector, payload=payload)]
        )
        print(f"[OpMem] (File) Snapshot: {filename} ({payload['lines']} líneas, hash={file_hash})")
        return True

    def snapshot_all(self, note: str = ""):
        """Snapshot de TODOS los ficheros core del sistema."""
        count = 0
        for fp in CORE_FILES:
            if os.path.exists(fp):
                self.snapshot_file(fp, version_note=note or f"Auto-snapshot {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                count += 1
                time.sleep(0.1)  # Rate limiting para Ollama
        print(f"[OpMem] (Core) {count} ficheros versionados")
        return count

    def file_history(self, filename: str, limit: int = 10) -> list:
        """Devuelve el historial de versiones de un fichero."""
        if not self.client:
            return []

        # Buscar por payload filter
        try:
            results = self.client.scroll(
                collection_name=COLLECTIONS["files"],
                scroll_filter=Filter(must=[
                    FieldCondition(key="filename", match=MatchValue(value=filename))
                ]),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )[0]  # scroll returns (points, next_page_offset)
        except Exception as e:
            print(f"[OpMem] Error buscando historial: {e}")
            return []

        history = []
        for r in results:
            p = r.payload
            history.append({
                "timestamp": p.get("timestamp", ""),
                "hash": p.get("hash", ""),
                "lines": p.get("lines", 0),
                "size_bytes": p.get("size_bytes", 0),
                "version_note": p.get("version_note", ""),
            })
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history

    def get_file_version(self, filename: str, target_hash: str = None) -> str:
        """Recupera el contenido de una versión específica de un fichero."""
        if not self.client:
            return ""
        try:
            must = [FieldCondition(key="filename", match=MatchValue(value=filename))]
            if target_hash:
                must.append(FieldCondition(key="hash", match=MatchValue(value=target_hash)))

            results = self.client.scroll(
                collection_name=COLLECTIONS["files"],
                scroll_filter=Filter(must=must),
                limit=1,
                with_payload=True,
                with_vectors=False
            )[0]
            if results:
                return results[0].payload.get("content", "")
        except Exception as e:
            print(f"[OpMem] Error recuperando versión: {e}")
        return ""

    # ═══════════════════════════════════════════════════════
    # 3. SKILLS Y ARTIFACTS
    # ═══════════════════════════════════════════════════════
    def log_skill(self, name: str, description: str, filepath: str = "",
                  skill_type: str = "script", keywords: list = None):
        """Registra una skill o artifact en la memoria."""
        if not self.client:
            return False

        keywords = keywords or []
        now = datetime.now().isoformat()

        content = ""
        if filepath and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        embed_text = f"Skill: {name}\nTipo: {skill_type}\nDescripción: {description}\nKeywords: {', '.join(keywords)}\nContenido: {content[:300]}"
        vector = self._embed(embed_text)

        payload = {
            "name": name,
            "description": description,
            "filepath": filepath,
            "skill_type": skill_type,
            "keywords": keywords,
            "content": content,
            "timestamp": now,
        }

        self.client.upsert(
            collection_name=COLLECTIONS["skills"],
            points=[PointStruct(id=self._gen_id(), vector=vector, payload=payload)]
        )
        print(f"[OpMem] (Skill) Skill registrada: {name}")
        return True

    def find_skill(self, query: str, limit: int = 5) -> list:
        """Busca skills relevantes por semántica."""
        if not self.client:
            return []
        vector = self._embed(query)
        try:
            results = self.client.query_points(
                collection_name=COLLECTIONS["skills"],
                query=vector,
                limit=limit,
                with_payload=True
            ).points
        except AttributeError:
            results = self.client.search(
                collection_name=COLLECTIONS["skills"],
                query_vector=vector,
                limit=limit
            )
        return [{"name": r.payload.get("name"), "description": r.payload.get("description"),
                 "filepath": r.payload.get("filepath"), "type": r.payload.get("skill_type"),
                 "score": round(r.score, 3) if hasattr(r, 'score') else 0} for r in results]

    # ═══════════════════════════════════════════════════════
    # ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════
    def stats(self) -> dict:
        """Estadísticas de todas las colecciones."""
        if not self.client:
            return {}
        result = {}
        for key, name in COLLECTIONS.items():
            try:
                info = self.client.get_collection(name)
                result[key] = {"collection": name, "points": info.points_count}
            except:
                result[key] = {"collection": name, "points": 0}
        return result


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enjambre Operational Memory V2.0")
    sub = parser.add_subparsers(dest="cmd")

    # log
    p_log = sub.add_parser("log", help="Registrar una operación")
    p_log.add_argument("description", help="Qué se quería conseguir")
    p_log.add_argument("--approach", default="", help="Cómo se abordó")
    p_log.add_argument("--result", choices=["success", "failure", "partial"], default="success")
    p_log.add_argument("--keywords", default="", help="Palabras clave separadas por comas")
    p_log.add_argument("--project", default="general")
    p_log.add_argument("--error", default="", help="Mensaje de error si falló")
    p_log.add_argument("--solution", default="", help="Solución aplicada")
    p_log.add_argument("--files", default="", help="Ficheros involucrados (comas)")

    # recall
    p_recall = sub.add_parser("recall", help="Recuperar operaciones pasadas")
    p_recall.add_argument("query", help="Consulta de búsqueda")
    p_recall.add_argument("--limit", type=int, default=5)
    p_recall.add_argument("--filter", choices=["success", "failure"], default=None)

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Versionar todos los ficheros core")
    p_snap.add_argument("--note", default="", help="Nota de versión")

    # history
    p_hist = sub.add_parser("history", help="Historial de versiones de un fichero")
    p_hist.add_argument("filename", help="Nombre del fichero")

    # skill
    p_skill = sub.add_parser("skill", help="Registrar una skill/artifact")
    p_skill.add_argument("name", help="Nombre de la skill")
    p_skill.add_argument("--desc", default="", help="Descripción")
    p_skill.add_argument("--file", default="", help="Ruta al fichero")
    p_skill.add_argument("--type", default="script", help="Tipo: script, artifact, config")
    p_skill.add_argument("--keywords", default="")

    # stats
    sub.add_parser("stats", help="Estadísticas de memoria")

    args = parser.parse_args()
    mem = OperationalMemory()

    if args.cmd == "log":
        kw = [k.strip() for k in args.keywords.split(",") if k.strip()]
        files = [f.strip() for f in args.files.split(",") if f.strip()]
        mem.log_operation(
            description=args.description,
            approach=args.approach,
            result=args.result,
            keywords=kw,
            project=args.project,
            error_msg=args.error,
            solution=args.solution,
            files_involved=files
        )

    elif args.cmd == "recall":
        results = mem.recall(args.query, limit=args.limit, result_filter=args.filter)
        if not results:
            print("Sin recuerdos relevantes.")
        else:
            for i, r in enumerate(results, 1):
                icon = "✅" if r["result"] == "success" else "❌" if r["result"] == "failure" else "⚠️"
                print(f"\n{icon} [{i}] Score={r['score']} | {r['timestamp'][:16]}")
                print(f"  Objetivo: {r['description']}")
                if r['approach']:
                    print(f"  Enfoque:  {r['approach']}")
                if r['solution']:
                    print(f"  Solución: {r['solution']}")
                if r['error_msg']:
                    print(f"  Error:    {r['error_msg']}")
                if r['keywords']:
                    print(f"  Tags:     {', '.join(r['keywords'])}")

    elif args.cmd == "snapshot":
        mem.snapshot_all(note=args.note)

    elif args.cmd == "history":
        history = mem.file_history(args.filename)
        if not history:
            print(f"Sin historial para '{args.filename}'")
        else:
            print(f"\nHistorial de {args.filename} ({len(history)} versiones):")
            for h in history:
                print(f"  [{h['timestamp'][:16]}] hash={h['hash']} lines={h['lines']} size={h['size_bytes']}B | {h['version_note']}")

    elif args.cmd == "skill":
        kw = [k.strip() for k in args.keywords.split(",") if k.strip()]
        mem.log_skill(name=args.name, description=args.desc, filepath=args.file, skill_type=args.type, keywords=kw)

    elif args.cmd == "stats":
        stats = mem.stats()
        print("\n📊 MEMORIA OPERATIVA — Estadísticas:")
        for key, info in stats.items():
            print(f"  {key}: {info['points']} puntos en '{info['collection']}'")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
