"""Genera el documento HTML de capacidades de Chask Swarm."""
import json, os, sys
from pathlib import Path
from datetime import datetime

OUT = Path(r"C:\Users\fnora\Desktop\Chask_Swarm_Guia_Completa.html")

sections = [
    ("Que es Chask Swarm", """Chask Swarm es un ecosistema de inteligencia artificial autonoma que se instala en tu ordenador y aprende de ti. No es una aplicacion mas: es un asistente personal que crece contigo, recuerda tus proyectos, automatiza tareas y se comunica contigo por multiples canales. A diferencia de ChatGPT o similares, Chask Swarm vive en tu maquina, protege tu privacidad, y puede actuar sin que estes delante."""),
    
    ("Instalacion y Primer Arranque", """<b>Requisitos:</b> Windows 10/11, Python 3.11+, conexion a internet.<br><br>
<b>Pasos:</b><ol>
<li>Descarga el instalador desde GitHub</li>
<li>Ejecuta <code>Instalar.bat</code> — instala todas las dependencias automaticamente</li>
<li>Ejecuta <code>Inicio.bat</code> — arranca el enjambre completo</li>
<li>Se abre automaticamente el Panel de Control en tu navegador (<code>http://localhost:7860</code>)</li>
<li>Un cuestionario inicial (<code>Cuestionario_Soul.md</code>) te pregunta tu nombre, preferencias y estilo de comunicacion</li>
</ol>
A partir de ese momento, tu IA personal esta activa y escuchando."""),

    ("Panel de Control Web", """El Panel de Control es tu centro de mando. Se accede desde el navegador en <code>http://localhost:7860</code>.<br><br>
<b>Desde aqui puedes:</b><ul>
<li>Chatear directamente con tu IA</li>
<li>Ver el estado de todos los servicios (activos/inactivos)</li>
<li>Gestionar usuarios y sus permisos</li>
<li>Configurar canales de comunicacion (Telegram, Discord, Email)</li>
<li>Configurar la red de enjambres (local y global)</li>
<li>Ver la memoria y el historial del sistema</li>
<li>Controlar el filtro parental</li>
<li>Ajustar los proveedores de IA (gratuitos o de pago)</li>
<li>Iniciar y detener servicios del sistema</li>
<li>Programar tareas automaticas</li>
</ul>
<b>26 endpoints de configuracion</b> permiten controlar absolutamente todo sin tocar un solo archivo."""),

    ("Comunicacion Multicanal", """Tu IA puede hablar contigo por varios canales simultaneamente:<br><br>
<b>Telegram:</b> Envia y recibe mensajes, fotos, notas de voz y documentos. Es el canal principal de control remoto. Puedes hablarle desde el movil estando fuera de casa.<br><br>
<b>Discord:</b> Bot bidireccional completo con comandos. Ideal para comunidades o equipos de trabajo.<br><br>
<b>Email:</b> Monitoriza tu bandeja de entrada, clasifica emails automaticamente (Urgente/Importante/Info/Spam) y puede responder por ti.<br><br>
<b>Panel Web:</b> Chat directo desde el navegador con respuestas en tiempo real.<br><br>
<b>Regla del Espejo:</b> La IA siempre responde por el mismo canal por el que le hablas. Si le escribes por Telegram, responde por Telegram."""),

    ("Inteligencia Artificial: Pool de Modelos", """Chask Swarm no depende de una sola IA. Tiene un <b>router inteligente</b> que elige el mejor modelo para cada tarea:<br><br>
<b>Por defecto usa modelos gratuitos</b> (no necesitas pagar nada):<ul>
<li>Google Gemini, Meta Llama, Mistral, Qwen, DeepSeek, y mas</li>
</ul>
<b>Si lo deseas, puedes anadir modelos de pago:</b><ul>
<li>OpenAI GPT-4, Anthropic Claude, etc.</li>
</ul>
El sistema analiza la complejidad de cada pregunta y elige automaticamente el modelo mas adecuado. Las preguntas sencillas se resuelven con modelos rapidos; las complejas se escalan a modelos potentes.<br><br>
<b>Todo configurable</b> desde el Panel de Control."""),

    ("Memoria y Aprendizaje", """Tu IA recuerda todo:<br><br>
<b>Memoria Operativa (<code>memory.md</code>):</b> Que esta haciendo ahora mismo, en que paso va, cuando se actualizo por ultima vez.<br><br>
<b>Memoria Vectorial (Qdrant):</b> Base de datos de conocimiento que permite buscar por significado, no solo por palabras exactas. Recuerda conversaciones pasadas, lecciones aprendidas, y contexto de proyectos.<br><br>
<b>Memoria de Grafo:</b> Relaciones entre conceptos (personas, proyectos, tecnologias) conectadas entre si.<br><br>
<b>Memoria Evolutiva:</b> El sistema aprende de sus errores y aciertos. Cada patron exitoso se guarda para reutilizarse en el futuro.<br><br>
<b>Skill Learner:</b> Automaticamente detecta tareas que hace bien y las convierte en "habilidades" reutilizables que mejoran con el tiempo."""),

    ("Sistema de Habilidades (Skills)", """Las habilidades son como "recetas" que tu IA aprende:<br><br>
<b>Habilidades incluidas:</b><ul>
<li>Generacion de documentos HTML profesionales</li>
<li>Gestion de emails</li>
<li>Analisis de privacidad de datos</li>
<li>Evolucion autonoma del enjambre</li>
<li>Fusion de documentos HTML</li>
<li>Monitorizacion de servicios</li>
</ul>
<b>Aprendizaje automatico:</b> Cuando la IA resuelve una tarea nueva con exito, puede convertirla en una habilidad reutilizable automaticamente.<br><br>
<b>Comunidad:</b> Al ser open source, cualquier usuario puede crear y compartir habilidades con la comunidad."""),

    ("Seguridad y Privacidad", """<b>Proteccion Anti-Inyeccion:</b> Si alguien intenta manipular la IA a traves de documentos, webs o correos con instrucciones ocultas ("ignora tus ordenes"), el sistema lo detecta, lo ignora y alerta al administrador.<br><br>
<b>Zero Trust:</b> Solo obedece ordenes del teclado local o del Telegram/Discord autorizado.<br><br>
<b>Cifrado E2E:</b> Todas las comunicaciones entre enjambres usan AES-256-GCM con HMAC-SHA256.<br><br>
<b>Sandbox de Seguridad:</b> El codigo sospechoso se ejecuta en un entorno aislado (Windows Sandbox, Docker, o proceso restringido) antes de tocar tu sistema real. Analisis AST previo y auditoria con hash chain.<br><br>
<b>Motor de Privacidad:</b> Anonimiza datos personales antes de enviarlos a cualquier IA externa.<br><br>
<b>Auditoria:</b> Cada accion critica se registra con fecha, hora y descripcion."""),

    ("Sistema Multiusuario", """El administrador puede crear cuentas para familiares, companeros o clientes:<br><br>
<b>6 Roles predefinidos:</b><ul>
<li><b>Admin:</b> Control total (20 capacidades)</li>
<li><b>Power:</b> Todo excepto gestionar usuarios (17 caps)</li>
<li><b>User:</b> Uso general (10 caps)</li>
<li><b>Teen:</b> Adolescente con filtro moderado (6 caps)</li>
<li><b>Child:</b> Nino con filtro estricto (4 caps)</li>
<li><b>Guest:</b> Solo consultas basicas (2 caps)</li>
</ul>
<b>Capacidades granulares:</b> Puedes dar o quitar permisos individuales a cada usuario (por ejemplo, permitir usar la IA pero no ejecutar codigo).<br><br>
<b>Canales por usuario:</b> Cada usuario puede tener su propio Telegram y Discord vinculado.<br><br>
<b>Sesiones aisladas:</b> Cada usuario tiene su propia memoria y preferencias separadas."""),

    ("Filtro Parental", """Proteccion especial para menores de edad:<br><br>
<b>Modo Estricto (menores de 13):</b> Bloquea automaticamente cualquier contenido relacionado con violencia, drogas, contenido sexual, armas, acoso, apuestas o ideologias extremistas. La IA adapta su lenguaje para ser apropiada para ninos.<br><br>
<b>Modo Moderado (13-17 anos):</b> Bloquea contenido explicito pero permite temas educativos tratados de forma apropiada.<br><br>
<b>Bidireccional:</b> Filtra tanto lo que el menor envia como lo que la IA le responde.<br><br>
<b>Alertas al admin:</b> Cuando se bloquea contenido, el administrador recibe una notificacion automatica por Telegram."""),

    ("Red Local de Enjambres (LAN)", """Multiples instancias de Chask Swarm en la misma red WiFi pueden colaborar:<br><br>
<b>Descubrimiento automatico:</b> Los enjambres se encuentran solos via UDP broadcast.<br><br>
<b>Cifrado total:</b> Todas las comunicaciones entre enjambres estan cifradas con AES-256-GCM.<br><br>
<b>Cluster Key:</b> Solo los enjambres que tengan la misma clave pueden participar. Ningun intruso puede colarse.<br><br>
<b>Delegacion de tareas:</b> Si un enjambre necesita ayuda, la pide a la red. El protocolo es:<ol>
<li>REQUEST: El enjambre pide ayuda</li>
<li>BID: Los enjambres capaces responden</li>
<li>ACCEPT: El solicitante elige y confirma</li>
<li>EXECUTE: Solo tras confirmacion se ejecuta la tarea</li>
<li>RESULT: El resultado vuelve cifrado al solicitante</li>
</ol>
<b>Ningun enjambre ejecuta nada sin recibir permiso explicito.</b>"""),

    ("Internet de Enjambres (Red Global)", """Los enjambres de todo el mundo pueden colaborar a traves de internet:<br><br>
<b>Nodo Central (Hub):</b> Un servidor central mantiene el registro de todos los enjambres y enrutadores activos.<br><br>
<b>Enrutadores:</b> Enjambres voluntarios que redirigen solicitudes de ayuda a otros enjambres de la red.<br><br>
<b>Funcionamiento:</b><ol>
<li>Al instalar, tu enjambre se registra en el Hub</li>
<li>El Hub te envia la lista de enrutadores activos</li>
<li>Cada hora, tu enjambre hace un "ping" para confirmar que sigue vivo</li>
<li>Cuando necesitas ayuda, la solicitud viaja: tu enjambre → enrutador → otro enrutador → enjambre capaz</li>
</ol>
<b>Politicas:</b><ul>
<li>La ayuda entre enjambres usa <b>solo IAs gratuitas</b> por defecto (configurable)</li>
<li>Si no quieres participar, puedes desconectarte, pero entonces no podras recibir ayuda de otros</li>
<li>Maximo 3 saltos de enrutamiento para evitar bucles</li>
</ul>"""),

    ("Automatizacion y Tareas Programadas", """<b>Scheduler integrado:</b> Programa tareas que se ejecutan automaticamente:<ul>
<li>Backup diario del sistema</li>
<li>Informe diario con metricas y graficas (HTML premium)</li>
<li>Aprendizaje automatico cada 2 horas</li>
<li>Health check cada 30 minutos</li>
<li>Monitorizacion de email</li>
</ul>
<b>Servicios de Windows:</b> Los daemons criticos se instalan como servicios del sistema que sobreviven reinicios y arrancan con Windows.<br><br>
<b>Watchdog:</b> Un vigilante supervisa constantemente que todos los servicios esten funcionando. Si alguno cae, lo reinicia automaticamente."""),

    ("Orquestacion Multi-Agente (Hive Mind)", """Para tareas complejas, el sistema activa el protocolo <b>Hive Mind</b>:<br><br>
<b>4 fases automaticas:</b><ol>
<li><b>Alpha (Planificar):</b> Analiza la tarea y la divide en sub-tareas</li>
<li><b>Beta (Investigar):</b> Multiples IAs investigan en paralelo</li>
<li><b>Gamma (Ejecutar):</b> Consolida resultados y ejecuta</li>
<li><b>Delta (Verificar):</b> Comprueba la calidad del resultado</li>
</ol>
<b>Patrones avanzados:</b><ul>
<li><b>Map-Reduce:</b> Divide el trabajo, procesa en paralelo, y agrega resultados</li>
<li><b>Supervisor-Worker:</b> Un agente supervisor gestiona trabajadores, revisa fallos y reintenta</li>
<li><b>Grafos de Estado:</b> Flujos de trabajo con checkpointing — si el sistema se cae, retoma donde lo dejo</li>
</ul>"""),

    ("Vision Artificial", """La IA puede "ver" y analizar imagenes:<br><br>
<b>Cadena de fallback inteligente:</b><ol>
<li>Cloud Vision (GPT-4V o Gemini) — maxima calidad</li>
<li>Ollama local (llava) — sin conexion a internet</li>
<li>OCR (EasyOCR) — extraccion de texto de imagenes</li>
</ol>
Envia una foto por Telegram y la IA te describira su contenido, extraera texto, o analizara lo que vea."""),

    ("Comandos Rapidos (Slash Commands)", """Escribe comandos rapidos desde cualquier canal:<br><br>
<table><tr><th>Comando</th><th>Funcion</th></tr>
<tr><td>/status</td><td>Estado del sistema</td></tr>
<tr><td>/help</td><td>Lista de comandos</td></tr>
<tr><td>/modo</td><td>Cambiar modo de la IA</td></tr>
<tr><td>/skill</td><td>Ejecutar una habilidad</td></tr>
<tr><td>/kb</td><td>Buscar en la base de conocimiento</td></tr>
<tr><td>/memoria</td><td>Ver la memoria actual</td></tr>
<tr><td>/config</td><td>Ver configuracion</td></tr>
<tr><td>/set</td><td>Cambiar configuracion</td></tr>
<tr><td>/learn</td><td>Forzar aprendizaje</td></tr>
<tr><td>/sandbox</td><td>Ejecutar codigo aislado</td></tr>
<tr><td>/services</td><td>Gestionar servicios</td></tr>
<tr><td>/user</td><td>Gestionar usuarios</td></tr>
<tr><td>/swarm</td><td>Estado de la red de enjambres</td></tr>
<tr><td>/deploy</td><td>Desplegar cambios</td></tr>
<tr><td>/fix</td><td>Reparar problemas</td></tr>
<tr><td>/analiza</td><td>Analizar archivos o codigo</td></tr>
<tr><td>/reflexion</td><td>Reflexion sobre el trabajo</td></tr>
</table>"""),

    ("Informes Automaticos", """Cada dia se genera automaticamente un informe visual en HTML con:<ul>
<li>Numero de interacciones y tareas completadas</li>
<li>Uso de cada modelo de IA (grafico de barras)</li>
<li>Estado de la memoria vectorial (colecciones y puntos)</li>
<li>Registro de seguridad (acciones auditadas)</li>
<li>Resumen de la memoria operativa</li>
</ul>
El informe se envia automaticamente por Telegram como documento."""),

    ("Integraciones y Conectores", """<b>MCP (Model Context Protocol):</b> Servidor MCP integrado que permite conectar Chask Swarm con otras herramientas compatibles.<br><br>
<b>Slack y Teams:</b> Adaptadores para integracion empresarial.<br><br>
<b>n8n:</b> Compatible con flujos de automatizacion n8n.<br><br>
<b>Git:</b> Gestor de repositorios con worktrees para despliegues.<br><br>
<b>Docker:</b> Integracion con contenedores para ejecucion aislada.<br><br>
<b>Qdrant:</b> Base de datos vectorial para memoria semantica."""),

    ("Open Source y Comunidad", """Chask Swarm es <b>100% codigo abierto</b> (GitHub).<br><br>
<b>Que significa esto para ti:</b><ul>
<li>Es gratis para siempre</li>
<li>Puedes ver exactamente que hace el codigo (transparencia total)</li>
<li>La comunidad puede contribuir con mejoras y habilidades</li>
<li>Puedes adaptarlo a tus necesidades</li>
<li>Tus datos nunca salen de tu maquina (a menos que tu lo decidas)</li>
</ul>
<b>Contribuir:</b> Cualquier usuario puede crear y compartir habilidades, adaptadores, o mejoras con la comunidad."""),
]

# Build HTML
css = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a1a;color:#e0e0e0;line-height:1.7}
.hero{background:linear-gradient(135deg,#0d0d2b 0%,#1a1a3e 50%,#0d0d2b 100%);padding:80px 40px;text-align:center;border-bottom:2px solid rgba(0,212,255,0.3)}
.hero h1{font-size:48px;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px}
.hero p{font-size:18px;color:#aaa;max-width:700px;margin:0 auto}
.hero .ver{font-size:13px;color:#555;margin-top:16px;letter-spacing:2px}
nav{background:rgba(15,15,35,0.95);padding:24px 40px;border-bottom:1px solid rgba(255,255,255,0.06)}
nav h2{color:#00d4ff;font-size:14px;letter-spacing:3px;text-transform:uppercase;margin-bottom:16px}
nav ol{columns:2;column-gap:40px;padding-left:20px}
nav li{margin-bottom:6px;font-size:15px}
nav a{color:#ccc;text-decoration:none;transition:color 0.2s}
nav a:hover{color:#00d4ff}
.content{max-width:900px;margin:0 auto;padding:40px 40px 80px}
section{margin-bottom:48px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:32px;transition:border-color 0.3s}
section:hover{border-color:rgba(0,212,255,0.3)}
section h2{font-size:26px;color:#fff;margin-bottom:16px;padding-bottom:10px;border-bottom:2px solid rgba(123,47,247,0.4);display:flex;align-items:center;gap:10px}
section h2 .num{background:linear-gradient(135deg,#7b2ff7,#00d4ff);color:#fff;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
ul,ol{padding-left:24px;margin:10px 0}
li{margin-bottom:6px}
b{color:#fff}
code{background:rgba(0,212,255,0.1);color:#00d4ff;padding:2px 7px;border-radius:4px;font-size:13px}
table{width:100%;border-collapse:collapse;margin:12px 0}
th{background:rgba(123,47,247,0.2);color:#bb88ff;padding:10px;text-align:left;border:1px solid rgba(255,255,255,0.1)}
td{padding:8px 10px;border:1px solid rgba(255,255,255,0.06)}
tr:hover{background:rgba(0,212,255,0.03)}
footer{text-align:center;padding:40px;color:#555;font-size:13px;border-top:1px solid rgba(255,255,255,0.06)}
"""

toc = ""
body = ""
for i, (title, content) in enumerate(sections, 1):
    slug = f"s{i}"
    toc += f'<li><a href="#{slug}">{title}</a></li>\n'
    body += f'<section id="{slug}"><h2><span class="num">{i}</span>{title}</h2>{content}</section>\n'

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chask Swarm — Guia Completa de Capacidades</title>
<style>{css}</style>
</head>
<body>
<div class="hero">
<h1>Chask Swarm</h1>
<p>Guia completa de capacidades para usuarios</p>
<div class="ver">Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} — v2.0</div>
</div>
<nav>
<h2>Indice</h2>
<ol>{toc}</ol>
</nav>
<div class="content">{body}</div>
<footer>Chask Swarm &copy; 2026 — Proyecto Open Source<br>Este documento refleja las capacidades reales del sistema a fecha de generacion.</footer>
</body></html>"""

OUT.write_text(html, encoding="utf-8")
print(f"OK: {OUT} ({len(html)} bytes, {len(sections)} secciones)")
