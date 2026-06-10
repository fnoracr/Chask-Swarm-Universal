"""
benchmark_search.py — Evaluación de Rendimiento de Búsqueda RAG
================================================================
Realiza 100 búsquedas conceptuales sobre la colección indexada
y evalúa métricas de relevancia, cobertura y velocidad.
"""
import sys, time, json
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_HOST     = "localhost"
QDRANT_PORT     = 6333
COLLECTION_NAME = "power_automate_deep"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K           = 3

# 100 queries conceptuales sobre Power Automate RPA
QUERIES = [
    # Conceptos básicos de flujos
    "qué es un flujo de nube en Power Automate",
    "diferencia entre flujo instantáneo y programado",
    "cómo crear un flujo automatizado desde cero",
    "qué son los desencadenadores de flujo",
    "cómo compartir un flujo con otros usuarios",
    # Flujos de escritorio (RPA)
    "cómo crear un flujo de escritorio",
    "qué es RPA desatendida en Power Automate",
    "cómo ejecutar un flujo de escritorio desde un flujo de nube",
    "grabar acciones de flujo de escritorio",
    "depurar un flujo de escritorio",
    # Aplicación móvil
    "instalar aplicación móvil Power Automate",
    "cambiar entornos en la app móvil",
    "gestionar aprobaciones desde el móvil",
    "recibir notificaciones en Power Automate móvil",
    "limitaciones de la aplicación móvil",
    # Aprobaciones
    "cómo crear un flujo de aprobación",
    "aprobaciones paralelas en Power Automate",
    "aprobaciones secuenciales configurar",
    "opciones de respuesta personalizadas en aprobaciones",
    "administrar solicitudes de aprobación pendientes",
    # Conectores y conexiones
    "qué es un conector en Power Automate",
    "cómo crear un conector personalizado",
    "gestionar conexiones en Power Automate",
    "conector HTTP para llamadas REST API",
    "acciones de SharePoint en Power Automate",
    # Soluciones y ALM
    "qué es una solución en Power Automate",
    "crear un flujo dentro de una solución",
    "exportar e importar una solución",
    "control de versiones para flujos en soluciones",
    "eliminar un flujo de una solución",
    # Variables y datos
    "tipos de variables en flujos de escritorio",
    "notación de porcentaje en variables",
    "palabras clave reservadas en flujos de escritorio",
    "propiedades de tipo de datos de variables",
    "acciones de variables disponibles",
    # Condiciones y control de flujo
    "cómo agregar una condición a un flujo",
    "usar expresiones en condiciones",
    "acciones de control de flujo escritorio",
    "bucles en flujos de escritorio",
    "condicionales avanzados Power Automate",
    # Seguridad y DLP
    "directivas de prevención de pérdida de datos DLP",
    "configurar DLP para flujos de escritorio",
    "seguridad y privacidad en Power Automate",
    "gestionar entradas de texto confidencial contraseñas",
    "autenticación basada en certificados",
    # Automatización web y UI
    "automatizar páginas web con Power Automate",
    "acciones de automatización de interfaz de usuario",
    "automatizar imágenes en flujos de escritorio",
    "crear un selector personalizado",
    "extensiones de navegador Power Automate",
    # Máquinas y RPA hospedado
    "qué son las máquinas en Power Automate",
    "grupos de máquinas hospedadas",
    "registro silencioso de máquinas",
    "ejecutar flujo desatendido en máquina remota",
    "colas de flujo de escritorio",
    # Acciones específicas
    "acciones de correo electrónico en Power Automate",
    "acciones de Excel en flujos de escritorio",
    "acciones de PDF en Power Automate escritorio",
    "acciones de Active Directory Power Automate",
    "acciones FTP disponibles escritorio",
    # Copilot e IA
    "usar Copilot en flujos de nube",
    "crear flujo con Copilot asistente",
    "acciones generativas en flujos de nube",
    "preguntas frecuentes Copilot Power Automate",
    "analizar actividad de flujo con Copilot",
    # Process Mining
    "qué es Process Mining en Power Automate",
    "instalar aplicación Process Mining escritorio",
    "analizar procesos con variantes",
    "filtros en Process Mining",
    "reglas de negocio Process Mining",
    # Colas de trabajo
    "qué son las colas de trabajo Power Automate",
    "crear y gestionar colas de trabajo",
    "importación masiva datos cola de trabajo",
    "limitaciones conocidas colas de trabajo",
    "procesar elementos de cola de trabajo",
    # Licencias y planes
    "diferencia entre licencia gratuita y premium",
    "plan Power Automate Process para RPA",
    "licencias RPA desatendida requisitos",
    "cómo verificar mi licencia actual",
    "bloquear trial en inquilino Microsoft",
    # Integración con servicios Microsoft
    "integrar Power Automate con Teams",
    "flujos de trabajo en SharePoint con Power Automate",
    "usar Power Automate con Dataverse",
    "flujos de proceso de negocio en Dataverse",
    "integración con Dynamics 365",
    # Scripting y código
    "acciones de scripting en Power Automate Desktop",
    "trabajar con flujos de nube desde código",
    "API públicas para flujos de escritorio",
    "acciones de sesión CMD",
    "acciones XML disponibles",
    # Supervisión y monitoreo
    "supervisar ejecuciones de flujo de escritorio",
    "centro de automatización Power Automate",
    "historial de ejecución de flujo de nube",
    "notificaciones en tiempo de ejecución",
    "diagnosticar problemas de rendimiento",
    # Actualización y mantenimiento
    "actualizar Power Automate Desktop automáticamente",
    "instalar Power Automate en silencio",
    "migrar flujos clásicos Dataverse a modernos",
    "comparar cambios en flujo de escritorio",
    "restaurar flujo eliminado Power Automate",
]

def run_benchmark():
    print(f"\n{'='*70}")
    print(f"  BENCHMARK RAG — Colección: {COLLECTION_NAME}")
    print(f"  Queries: {len(QUERIES)} | Top-K: {TOP_K}")
    print(f"{'='*70}\n")

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    model  = SentenceTransformer(EMBEDDING_MODEL)

    total_points = client.get_collection(COLLECTION_NAME).points_count
    print(f"[INFO] Puntos en colección: {total_points}\n")

    results = []
    latencies = []
    hits_above_threshold = 0
    SCORE_THRESHOLD = 0.35  # Score mínimo para considerar resultado relevante

    for i, query in enumerate(QUERIES):
        t0 = time.time()
        embedding = model.encode(query, normalize_embeddings=True)
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding.tolist(),
            limit=TOP_K,
            with_payload=True
        )
        hits = response.points
        latency = time.time() - t0
        latencies.append(latency)

        top_score  = hits[0].score if hits else 0.0
        top_title  = hits[0].payload.get("article_title", "N/A")[:40] if hits else "Sin resultado"
        top_section= hits[0].payload.get("section", "")[:30] if hits else ""
        top_kw     = hits[0].payload.get("keywords", [])[:3] if hits else []
        is_hit     = top_score >= SCORE_THRESHOLD

        if is_hit:
            hits_above_threshold += 1

        results.append({
            "query": query,
            "score": round(top_score, 4),
            "hit": is_hit,
            "title": top_title,
            "section": top_section,
            "keywords": top_kw,
            "latency_ms": round(latency * 1000, 1)
        })

        status = "OK" if is_hit else "MISS"
        print(f"[{i+1:03d}] [{status}] score={top_score:.3f} lat={latency*1000:.0f}ms")
        print(f"       Q: {query[:55]}")
        print(f"       A: {top_title} / {top_section}")
        print()

    # Resumen estadístico
    avg_lat  = sum(latencies) / len(latencies)
    max_lat  = max(latencies)
    min_lat  = min(latencies)
    avg_score = sum(r["score"] for r in results) / len(results)
    hit_rate  = hits_above_threshold / len(QUERIES) * 100

    print(f"\n{'='*70}")
    print(f"  RESUMEN DE RENDIMIENTO")
    print(f"{'='*70}")
    print(f"  Hit Rate (score >= {SCORE_THRESHOLD}): {hit_rate:.1f}% ({hits_above_threshold}/{len(QUERIES)})")
    print(f"  Score promedio : {avg_score:.4f}")
    print(f"  Latencia media : {avg_lat*1000:.1f} ms")
    print(f"  Latencia mín   : {min_lat*1000:.1f} ms")
    print(f"  Latencia máx   : {max_lat*1000:.1f} ms")

    # Peores resultados (para análisis de mejora)
    misses = sorted([r for r in results if not r["hit"]], key=lambda x: x["score"])
    print(f"\n  PEORES RESULTADOS (score más bajo):")
    for r in misses[:10]:
        print(f"    score={r['score']:.3f} | {r['query'][:60]}")

    print(f"\n  MEJORES RESULTADOS (score más alto):")
    bests = sorted(results, key=lambda x: x["score"], reverse=True)
    for r in bests[:5]:
        print(f"    score={r['score']:.3f} | {r['query'][:60]}")

    # Guardar informe JSON
    report = {
        "total_queries": len(QUERIES),
        "hit_rate": hit_rate,
        "avg_score": avg_score,
        "avg_latency_ms": avg_lat * 1000,
        "threshold": SCORE_THRESHOLD,
        "results": results
    }
    report_path = r"C:\Users\fnora\Desktop\Conocimiento RPA\benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  Informe completo guardado en: {report_path}")
    print(f"{'='*70}\n")

    return report

if __name__ == "__main__":
    run_benchmark()
