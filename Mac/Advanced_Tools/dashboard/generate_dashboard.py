"""Genera el dashboard HTML de Enjambre vs Agentes IA."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", "utilities"))
from html_builder import *

OUT = r"C:\Users\fnora\Desktop\Enjambre Datos\chask_dashboard.html"

b = HTMLBuilder("Enjambre v3.0 Prometheus — Dashboard de Evolución", theme="dark")
b.add_css(DARK_CSS)

# ── HERO ──
b.add_section(f'''<div class="hero"><div class="container">
<h1>🧠 ENJAMBRE v3.0 — Codename Prometheus</h1>
<p class="subtitle">Dashboard de evolución del ecosistema Chask Swarm vs la industria de agentes IA</p>
</div></div>''')

# ── SCORES COMPARATIVOS ──
scores = [
    ("Enjambre", 82, "#00f5d4"),
    ("OpenClaw", 61, "#f72585"),
    ("Hermes", 58, "#7b61ff"),
    ("OpenSwarm", 65, "#ffd60a"),
]
rings = "".join(score_ring(name, val, col) for name, val, col in scores)
b.add_section(f'''<div class="container">
<h2>📊 Puntuación Global (0-100)</h2>
<div class="grid-4" style="justify-items:center">{rings}</div>
</div>''')

# ── TABLA COMPARATIVA DETALLADA ──
categories = [
    ["Aprendizaje continuo",     "✅ 4 pilares (Mem0+Reflexión+Skills+Evolución)", "❌ Estático (YAML manual)", "✅ Loop procedimental", "❌ No aprende"],
    ["Autonomía 24/7",           "✅ Daemons persistentes auto-arranque", "⚠️ Requiere host activo", "⚠️ Cloud-dependent", "❌ Requiere app abierta"],
    ["Multicanal",               "✅ Telegram+Web+IDE+Cola", "✅ 24+ canales", "⚠️ Limitado", "❌ Solo desktop"],
    ["Búsqueda híbrida RAG",     "✅ Nomic 768d + BM25 RRF", "❌ No tiene", "❌ No tiene", "❌ No tiene"],
    ["Knowledge auto-indexing",  "✅ Scraper+Ingest universal", "❌ No tiene", "❌ No tiene", "❌ No tiene"],
    ["HITL (Aprobaciones)",      "✅ Botones inline Telegram", "⚠️ Básico", "❌ No tiene", "✅ Canvas visual"],
    ["Slash Commands",           "✅ 15 comandos + aliases", "❌ No tiene", "❌ No tiene", "⚠️ Parcial"],
    ["Auto-evolución prompts",   "✅ Detecta correcciones auto", "❌ No tiene", "✅ Su punto fuerte", "❌ No tiene"],
    ["MCP Tools",                "⚠️ Esqueleto (4 tools)", "❌ No tiene", "❌ No tiene", "✅ Registry completo"],
    ["Agent Modes",              "✅ 5 modos + routing", "❌ No tiene", "⚠️ Roles fijos", "✅ 5 modos + custom"],
    ["Pool IAs gratuitas",       "✅ 8+ proveedores + Ollama", "⚠️ Limitado", "⚠️ APIs de pago", "❌ Solo Anthropic ($)"],
    ["Seguridad Zero-Trust",     "✅ Audit+Sandbox+Privacy", "⚠️ Básica", "⚠️ Estándar", "⚠️ Básica"],
    ["Modelos locales GPU",      "✅ RTX 4060 optimizado", "✅ Soporta Ollama", "✅ Nous nativo", "✅ Soporta Ollama"],
    ["Personalidad evolutiva",   "✅ soul.md + lecciones", "❌ No tiene", "❌ No tiene", "❌ No tiene"],
    ["Dashboard visual",         "⚠️ Gradio básico", "⚠️ Web simple", "❌ Terminal", "✅ Canvas React"],
    ["Git Worktree isolation",   "🔲 Pendiente", "❌ No tiene", "❌ No tiene", "✅ Implementado"],
    ["Hive Mind paralelo real",  "🔲 Pendiente", "❌ No tiene", "⚠️ Parcial", "✅ Multi-agente canvas"],
    ["Expansión Discord/Slack",  "🔲 Pendiente", "✅ 24+ integraciones", "❌ No tiene", "❌ No tiene"],
    ["Coste operativo mensual",  "0€ (local+pool gratuito)", "Bajo", "Variable (APIs)", "Alto (Anthropic)"],
]
headers = ["Capacidad", "Enjambre (Chask Swarm)", "OpenClaw", "Hermes (Nous)", "OpenSwarm"]
tbl = table(headers, categories)
b.add_section(f'<div class="container"><h2>⚔️ Comparativa Detallada por Capacidad</h2>{tbl}</div>')

# ── SCORING DETALLADO ──
scoring_cats = [
    ("Aprendizaje", [("Enjambre",95,"#00f5d4"),("OpenClaw",20,"#f72585"),("Hermes",85,"#7b61ff"),("OpenSwarm",15,"#ffd60a")]),
    ("Autonomía", [("Enjambre",95,"#00f5d4"),("OpenClaw",60,"#f72585"),("Hermes",40,"#7b61ff"),("OpenSwarm",30,"#ffd60a")]),
    ("Multicanal", [("Enjambre",70,"#00f5d4"),("OpenClaw",95,"#f72585"),("Hermes",30,"#7b61ff"),("OpenSwarm",20,"#ffd60a")]),
    ("RAG/Knowledge", [("Enjambre",90,"#00f5d4"),("OpenClaw",10,"#f72585"),("Hermes",40,"#7b61ff"),("OpenSwarm",15,"#ffd60a")]),
    ("Orquestación", [("Enjambre",60,"#00f5d4"),("OpenClaw",40,"#f72585"),("Hermes",50,"#7b61ff"),("OpenSwarm",90,"#ffd60a")]),
    ("Seguridad", [("Enjambre",90,"#00f5d4"),("OpenClaw",40,"#f72585"),("Hermes",50,"#7b61ff"),("OpenSwarm",40,"#ffd60a")]),
    ("UI/Dashboard", [("Enjambre",35,"#00f5d4"),("OpenClaw",50,"#f72585"),("Hermes",25,"#7b61ff"),("OpenSwarm",90,"#ffd60a")]),
    ("Coste", [("Enjambre",100,"#00f5d4"),("OpenClaw",70,"#f72585"),("Hermes",50,"#7b61ff"),("OpenSwarm",20,"#ffd60a")]),
]
bars_html = ""
for cat, agents in scoring_cats:
    bars = "".join(progress_bar(name, val, 100, col) for name, val, col in agents)
    bars_html += f'<div class="card"><h3>{cat}</h3>{bars}</div>'
b.add_section(f'<div class="container"><h2>📈 Scoring por Categoría (0-100)</h2><div class="grid-2">{bars_html}</div></div>')

# ── ESTADO DE IMPLEMENTACIÓN ──
implemented = [
    ("llm_router.py", "Pool de 8+ IAs gratuitas", "✅"),
    ("evolutionary_memory.py", "Memoria evolutiva Mem0 + Qdrant", "✅"),
    ("reflection_engine.py", "Reflexión y lecciones aprendidas", "✅"),
    ("skill_catalog.py", "Catálogo de skills reutilizables", "✅"),
    ("mode_router.py + agent_modes.json", "5 modos de agente con routing", "✅"),
    ("knowledge_orchestrator.py", "RAG universal multi-colección", "✅"),
    ("universal_scraper.py", "Scraper web adaptable por tema", "✅"),
    ("universal_ingest.py", "Ingesta V4 (nomic-768 + BM25)", "✅"),
    ("topic_detector.py", "Detección de temas recurrentes", "✅"),
    ("ingest_smart_v4.py", "Ingesta Power Automate 400 arts", "✅"),
    ("slash_commands.py", "15 slash commands + aliases", "✅"),
    ("auto_evolve_prompts.py", "Auto-evolución de system prompts", "✅"),
    ("hitl_telegram.py", "Botones HITL inline en Telegram", "✅"),
    ("telegram_daemon.py", "Daemon 24/7 con soporte HITL", "✅"),
    ("audit_logger.py", "Log de auditoría de acciones", "✅"),
    ("sandbox.py", "Ejecución aislada de código", "✅"),
    ("privacy_engine.py", "Anonimización PII automática", "✅"),
    ("backup_system.py", "Backups automáticos", "✅"),
    ("chask_mcp_server.py", "Servidor MCP (esqueleto)", "⚠️"),
    ("html_builder.py", "Generador de HTML largos", "✅"),
]
pending = [
    ("hive_mind_executor.py", "Delegación multi-modelo en paralelo real", "Fase 2"),
    ("Mode routing semántico", "Embeddings en vez de keywords", "Fase 2"),
    ("Reflexión automática", "Activar al detectar inactividad", "Fase 2"),
    ("MCP Server completo", "Exponer todas las 15+ tools", "Fase 3"),
    ("Memoria con decadencia temporal", "Hechos pierden peso si no se confirman", "Fase 3"),
    ("skill_generator.py", "Auto-generación de skills con LLM", "Fase 3"),
    ("channel_adapter.py", "Framework base para multicanal", "Fase 4"),
    ("discord_adapter.py", "Bot Discord conectado al enjambre", "Fase 4"),
    ("notification_manager.py", "Notificaciones inteligentes agrupadas", "Fase 4"),
    ("Dashboard React", "Canvas visual moderno con WebSocket", "Fase 5"),
    ("MCP Client", "Consumir tools MCP externas", "Fase 5"),
    ("Modos custom dinámicos", "Crear modos en runtime", "Fase 5"),
    ("git_worktree_manager.py", "Aislamiento por Git worktrees", "Fase 6"),
    ("slack_adapter.py", "Bot Slack conectado", "Fase 6"),
    ("teams_adapter.py", "Bot Microsoft Teams", "Fase 6"),
]

impl_rows = [[f'<code>{f}</code>', d, f'<span class="badge" style="background:#00f5d420;color:#00f5d4">{s}</span>'] for f, d, s in implemented]
pend_rows = [[f'<code>{f}</code>', d, f'<span class="phase-tag tag-pending">{p}</span>'] for f, d, p in pending]

t1 = table(["Archivo", "Descripción", "Estado"], impl_rows)
t2 = table(["Componente", "Descripción", "Fase"], pend_rows)
b.add_section(f'''<div class="container">
<h2>✅ Implementado ({len(implemented)} módulos)</h2>{t1}
<h2>🔲 Pendiente ({len(pending)} mejoras)</h2>{t2}
</div>''')

# ── ROADMAP FASES ──
phases = [
    ("Fase 1", "Transformacional", "100", "tag-done", "HITL Telegram + Slash Commands + Auto-Evolve Prompts"),
    ("Fase 2", "Inteligencia Real", "0", "tag-active", "Hive Mind Executor + Mode Semántico + Reflexión Auto"),
    ("Fase 3", "Madurez", "0", "tag-pending", "MCP Completo + Memoria Temporal + Skills Auto"),
    ("Fase 4", "Alcance", "0", "tag-pending", "Framework Adaptadores + Discord + Notificaciones"),
    ("Fase 5", "Polish", "0", "tag-pending", "Dashboard React + MCP Client + Modos Custom"),
    ("Fase 6", "Expansión", "0", "tag-pending", "Git Worktrees + Slack + Teams"),
]
phases_html = ""
for name, label, pct, cls, desc in phases:
    col = "#00f5d4" if pct == "100" else "#7b61ff" if cls == "tag-active" else "#444"
    phases_html += f'''<div class="card">
<span class="phase-tag {cls}">{name}</span> <strong>{label}</strong>
<div style="margin-top:12px">{progress_bar("Progreso", int(pct), 100, col)}</div>
<p style="font-size:.85rem;color:#888;margin-top:8px">{desc}</p></div>'''
b.add_section(f'<div class="container"><h2>🗺️ Roadmap de Fases</h2><div class="grid-2">{phases_html}</div></div>')

# ── FOOTER ──
b.add_section('<footer><div class="container">Chask Swarm © 2026 — Generado automáticamente por Enjambre usando html_builder.py</div></footer>')

# ── ANIMACIÓN JS ──
b.add_script("""
document.addEventListener('DOMContentLoaded', () => {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => { if(e.isIntersecting) e.target.style.opacity = 1; e.target.style.transform = 'translateY(0)'; });
  }, {threshold: 0.1});
  document.querySelectorAll('.card,.score-ring').forEach(el => {
    el.style.opacity = 0; el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });
});
""")

b.save(OUT)
print(f"Dashboard listo: {OUT}")
