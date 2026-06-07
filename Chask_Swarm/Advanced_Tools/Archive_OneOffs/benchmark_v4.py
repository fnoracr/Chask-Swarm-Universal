"""
benchmark_v4.py — Evaluación de Rendimiento: Búsqueda Híbrida V4
==================================================================
Compara búsqueda densa vs híbrida (densa + sparse BM25) sobre power_automate_v4
"""
import sys, time, json, re, io
from collections import Counter
import requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from qdrant_client import QdrantClient
from qdrant_client.models import (
    SparseVector, NamedVector, NamedSparseVector, Prefetch, FusionQuery, Fusion
)

QDRANT_HOST     = "localhost"
QDRANT_PORT     = 6333
COLLECTION_NAME = "power_automate_v4"
OLLAMA_URL      = "http://localhost:11434"
EMBED_MODEL     = "nomic-embed-text"
TOP_K           = 3
SCORE_THRESHOLD = 0.30

STOPWORDS = {
    "de","la","el","en","y","a","que","los","las","un","una","es","por","con",
    "para","del","al","se","su","sus","más","si","no","como","o","este","esta",
    "cuando","the","and","for","this","that","with","from","have","are","not"
}

QUERIES = [
    "qué es un flujo de nube en Power Automate",
    "diferencia entre flujo instantáneo y programado",
    "cómo crear un flujo automatizado desde cero",
    "qué son los desencadenadores de flujo",
    "cómo compartir un flujo con otros usuarios",
    "cómo crear un flujo de escritorio",
    "qué es RPA desatendida en Power Automate",
    "cómo ejecutar un flujo de escritorio desde un flujo de nube",
    "grabar acciones de flujo de escritorio",
    "depurar un flujo de escritorio",
    "instalar aplicación móvil Power Automate",
    "cambiar entornos en la app móvil",
    "gestionar aprobaciones desde el móvil",
    "recibir notificaciones en Power Automate móvil",
    "limitaciones de la aplicación móvil",
    "cómo crear un flujo de aprobación",
    "aprobaciones paralelas en Power Automate",
    "aprobaciones secuenciales configurar",
    "opciones de respuesta personalizadas en aprobaciones",
    "administrar solicitudes de aprobación pendientes",
    "qué es un conector en Power Automate",
    "cómo crear un conector personalizado",
    "gestionar conexiones en Power Automate",
    "conector HTTP para llamadas REST API",
    "acciones de SharePoint en Power Automate",
    "qué es una solución en Power Automate",
    "crear un flujo dentro de una solución",
    "exportar e importar una solución",
    "control de versiones para flujos en soluciones",
    "eliminar un flujo de una solución",
    "tipos de variables en flujos de escritorio",
    "notación de porcentaje en variables",
    "palabras clave reservadas en flujos de escritorio",
    "propiedades de tipo de datos de variables",
    "acciones de variables disponibles",
    "cómo agregar una condición a un flujo",
    "usar expresiones en condiciones",
    "acciones de control de flujo escritorio",
    "bucles en flujos de escritorio",
    "condicionales avanzados Power Automate",
    "directivas de prevención de pérdida de datos DLP",
    "configurar DLP para flujos de escritorio",
    "seguridad y privacidad en Power Automate",
    "gestionar entradas de texto confidencial contraseñas",
    "autenticación basada en certificados",
    "automatizar páginas web con Power Automate",
    "acciones de automatización de interfaz de usuario",
    "automatizar imágenes en flujos de escritorio",
    "crear un selector personalizado",
    "extensiones de navegador Power Automate",
    "qué son las máquinas en Power Automate",
    "grupos de máquinas hospedadas",
    "registro silencioso de máquinas",
    "ejecutar flujo desatendido en máquina remota",
    "colas de flujo de escritorio",
    "acciones de correo electrónico en Power Automate",
    "acciones de Excel en flujos de escritorio",
    "acciones de PDF en Power Automate escritorio",
    "acciones de Active Directory Power Automate",
    "acciones FTP disponibles escritorio",
    "usar Copilot en flujos de nube",
    "crear flujo con Copilot asistente",
    "acciones generativas en flujos de nube",
    "preguntas frecuentes Copilot Power Automate",
    "analizar actividad de flujo con Copilot",
    "qué es Process Mining en Power Automate",
    "instalar aplicación Process Mining escritorio",
    "analizar procesos con variantes",
    "filtros en Process Mining",
    "reglas de negocio Process Mining",
    "qué son las colas de trabajo Power Automate",
    "crear y gestionar colas de trabajo",
    "importación masiva datos cola de trabajo",
    "limitaciones conocidas colas de trabajo",
    "procesar elementos de cola de trabajo",
    "diferencia entre licencia gratuita y premium",
    "plan Power Automate Process para RPA",
    "licencias RPA desatendida requisitos",
    "cómo verificar mi licencia actual",
    "bloquear trial en inquilino Microsoft",
    "integrar Power Automate con Teams",
    "flujos de trabajo en SharePoint con Power Automate",
    "usar Power Automate con Dataverse",
    "flujos de proceso de negocio en Dataverse",
    "integración con Dynamics 365",
    "acciones de scripting en Power Automate Desktop",
    "trabajar con flujos de nube desde código",
    "API públicas para flujos de escritorio",
    "acciones de sesión CMD",
    "acciones XML disponibles",
    "supervisar ejecuciones de flujo de escritorio",
    "centro de automatización Power Automate",
    "historial de ejecución de flujo de nube",
    "notificaciones en tiempo de ejecución",
    "diagnosticar problemas de rendimiento",
    "actualizar Power Automate Desktop automáticamente",
    "instalar Power Automate en silencio",
    "migrar flujos clásicos Dataverse a modernos",
    "comparar cambios en flujo de escritorio",
    "restaurar flujo eliminado Power Automate",
]

def get_embedding(text: str) -> list[float]:
    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text[:8000]},
        timeout=30
    )
    return resp.json()["embedding"]

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

def run_benchmark():
    print(f"\n{'='*70}")
    print(f"  BENCHMARK V4 — Hibrido (nomic-768 + BM25)")
    print(f"  Coleccion: {COLLECTION_NAME} | Queries: {len(QUERIES)}")
    print(f"{'='*70}\n")

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    try:
        pts = client.get_collection(COLLECTION_NAME).points_count
        print(f"[INFO] Puntos en coleccion: {pts}\n")
    except Exception as e:
        print(f"[ERROR] No se puede conectar a {COLLECTION_NAME}: {e}")
        return

    results    = []
    latencies  = []
    hits_ok    = 0

    for i, query in enumerate(QUERIES):
        t0      = time.time()
        dvec    = get_embedding(query)
        svec    = text_to_sparse(query)
        
        # Busqueda hibrida: densa + sparse fusionada por RRF
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=[
                Prefetch(query=dvec,  using="dense",  limit=TOP_K*2),
                Prefetch(query=svec,  using="sparse", limit=TOP_K*2),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=TOP_K,
            with_payload=True
        )
        hits    = response.points
        latency = time.time() - t0
        latencies.append(latency)

        top_score   = hits[0].score if hits else 0.0
        top_title   = hits[0].payload.get("article_title", "N/A")[:40] if hits else "Sin resultado"
        top_section = hits[0].payload.get("section", "")[:35] if hits else ""
        top_kw      = hits[0].payload.get("keywords", [])[:3] if hits else []
        is_hit      = len(hits) > 0

        if is_hit:
            hits_ok += 1

        results.append({
            "query": query, "score": round(top_score, 4),
            "hit": is_hit, "title": top_title,
            "section": top_section, "keywords": top_kw,
            "latency_ms": round(latency * 1000, 1)
        })

        status = "OK" if is_hit else "MISS"
        print(f"[{i+1:03d}] [{status}] score={top_score:.3f} lat={latency*1000:.0f}ms")
        print(f"       Q: {query[:55]}")
        print(f"       A: {top_title} / {top_section}")
        print()

    avg_lat  = sum(latencies) / len(latencies)
    avg_score = sum(r["score"] for r in results) / len(results)
    hit_rate  = hits_ok / len(QUERIES) * 100

    print(f"\n{'='*70}")
    print(f"  RESUMEN V4 (Hibrido RRF)")
    print(f"{'='*70}")
    print(f"  Hit Rate     : {hit_rate:.1f}% ({hits_ok}/{len(QUERIES)})")
    print(f"  Score medio  : {avg_score:.4f}")
    print(f"  Latencia med : {avg_lat*1000:.1f} ms")
    print(f"  Latencia min : {min(latencies)*1000:.1f} ms")
    print(f"  Latencia max : {max(latencies)*1000:.1f} ms")

    misses = [r for r in results if not r["hit"]]
    if misses:
        print(f"\n  MISSES ({len(misses)}):")
        for r in sorted(misses, key=lambda x: x["score"])[:10]:
            print(f"    score={r['score']:.3f} | {r['query'][:60]}")

    print(f"\n  TOP 5 MEJORES:")
    for r in sorted(results, key=lambda x: x["score"], reverse=True)[:5]:
        print(f"    score={r['score']:.3f} | {r['query'][:60]}")

    report_path = r"C:\Users\fnora\Desktop\Conocimiento RPA\benchmark_v4_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"hit_rate": hit_rate, "avg_score": avg_score,
                   "avg_latency_ms": avg_lat*1000, "results": results}, f,
                  ensure_ascii=False, indent=2)
    print(f"\n  Informe: {report_path}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    run_benchmark()
