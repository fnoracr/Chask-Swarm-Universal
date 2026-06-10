import os
import ast
import re
import json

BASE_DIR = r"C:\Program Files\Chask_Swarm"

EXCLUDED_DIRS = {
    'Automatizaciones', 'Web_Local', 'Backups', 'Versiones_Antiguas', 'Chask_Backups',
    'Borrados', 'Basura_y_Debug', 'pruebas', 'Charm', 'scratch', 'screenshots',
    '__pycache__', 'Distribucion', 'user_sessions', 'TwitterBotProfile', 'YouTubeBotProfile',
    'InstaBotProfile', 'PatreonBotProfile', 'Chask_Hive_Credenciales_y_Config', 'approvals',
    'reports'
}

EXCLUDED_SUBDIRS = {
    r"Advanced_Tools\modules\YouTube_y_Social",
    r"Advanced_Tools\Archive_OneOffs",
    r"Advanced_Tools\modules\Codex"
}

EXCLUDED_FILES = {
    'Colas_Mensajes/telegram_hashes.txt', 'Configuracion', 'meetcharm_users.db',
    'Colas_Mensajes/telegram_daemon_state.txt', 'Colas_Mensajes', 'telegram_state.txt',
    'Colas_Mensajes/telegram_sentinel_state.txt', 'Colas_Mensajes', 'out_pending.json', 'search_results.json', 
    'llm_usage_today.json', 'topic_state.json', 'reminder_state.json', 'anti_drift_state.json',
    'build_distribution.py', 'generate_arch_canvas.py', 'generate_arch_html.py', 'Advanced_Tools', 'generate_dist_canvas.py',
    'computer_use.py', 'universal_ingest.py', 'janitor.py',
    'architecture_canvas.py', 'ask_gemma.py', 'create_resurrection_drive.py', 
    'diagnostics.py', 'generate_dashboard.py', 'live_dashboard.py', 'send_manual_scheduler.py', 
    'start_if_not_running.py', 'win_telemetry_svc.py', 'analyze_meetcharm.py', 'fix_meetcharm_turn.py', 
    'debug_hub.py', 'fix_hub_venv.py', 'email_chask.py', 'export_browser_cookies.py', 
    'export_youtube_transcripts.py', 'pad_solution_builder.py', 'style_extractor.py', 'temp_orphan_check.py', 
    'chask_test_battery.py', 'codex_publish_skill.py', 'inject_to_codex.py', 'synthesis_reporter.py',
    'chask_web_rag.py', 'Configuracion', 'workflows_backup.json', 'pending_ideas.md', '3_Colmena_Ejemplo_Orquestador.json',
    'excel.json', 'browser_1000_results.json'
}

def should_exclude(root, file_name):
    if file_name in EXCLUDED_FILES: return True
    ext = os.path.splitext(file_name)[1].lower()
    if ext in ['.log', '.tmp', '.old', '.pem', '.key', '.lock']: return True
    f_lower = file_name.lower()
    if 'codex' in f_lower or 'manual' in f_lower or 'report' in f_lower or 'canvas' in f_lower: return True
    if file_name.startswith('vps_') or file_name.startswith('ftp_') or file_name.startswith('test_'): return True
    rel_path = os.path.relpath(root, BASE_DIR)
    for sub in EXCLUDED_SUBDIRS:
        if rel_path.endswith(sub) or sub in rel_path: return True
    return False

file_data = {}
all_scripts = set()
base_name_map = {}

for root, dirs, files in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
    rel_dir = os.path.relpath(root, BASE_DIR)
    
    skip_current = False
    for sub in EXCLUDED_SUBDIRS:
        if rel_dir.endswith(sub) or sub in rel_dir:
            skip_current = True
            break
    if skip_current:
        continue
        
    for f in files:
        if should_exclude(root, f): continue
        if f.endswith(('.py', '.bat', '.json', '.md', '.html', '.sh')):
            rel_path = os.path.relpath(os.path.join(root, f), BASE_DIR).replace('\\', '/')
            all_scripts.add(rel_path)
            
            if f not in base_name_map:
                base_name_map[f] = []
            base_name_map[f].append(rel_path)
            
            folder = os.path.dirname(rel_path)
            if not folder:
                folder = "Root"
            
            file_data[rel_path] = {
                'name': f,
                'path': rel_path,
                'folder': folder,
                'desc': '',
                'uses': {}
            }

for rel_path_key, data in file_data.items():
    abs_path = os.path.join(BASE_DIR, os.path.normpath(data['path']))
    name = data['name']
    try:
        with open(abs_path, 'r', encoding='utf-8') as file_obj:
            content = file_obj.read()
    except Exception:
        content = ""
        
    if name.endswith('.py'):
        try:
            tree = ast.parse(content)
            doc = ast.get_docstring(tree)
            if doc:
                data['desc'] = doc.split('\n')[0].strip()
        except:
            pass
            
        if not data['desc']:
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('#'):
                    data['desc'] = line.lstrip('#').strip()
                    break
                elif line:
                    break
    elif name.endswith('.bat'):
        for line in content.split('\n'):
            line = line.strip()
            if line.upper().startswith('REM '):
                data['desc'] = line[4:].strip()
                break
            
    desc_file = os.path.join(BASE_DIR, "Configuracion", "canvas_descriptions.json")
    try:
        with open(desc_file, 'r', encoding='utf-8') as df:
            COMMON_DESCS = json.load(df)
    except Exception:
        COMMON_DESCS = {}
    
    if name in COMMON_DESCS:
        data['desc'] = COMMON_DESCS[name]
    elif not data['desc']:
        if name.endswith('.json'):
            data['desc'] = "Archivo de estado o configuración (JSON)"
        elif name.endswith('.md'):
            data['desc'] = "Documento de texto, memoria o directivas (Markdown)"
        elif name.endswith('.bat'):
            data['desc'] = "Script ejecutable de Windows"
        elif name.endswith('.py'):
            data['desc'] = "Módulo Python interno"
        else:
            data['desc'] = "Archivo del Núcleo"

    for other_rel_path in all_scripts:
        if other_rel_path != rel_path_key:
            other_f = os.path.basename(other_rel_path)
            exact_pattern = r'[\'"](?:[^\'"]*[/\\\\])?' + re.escape(other_f) + r'[\'"]'
            if re.search(exact_pattern, content):
                data['uses'][other_rel_path] = 'soft'
            elif other_f.endswith('.bat'):
                base_bat = os.path.splitext(other_f)[0]
                bat_pattern = r'[\'"](?:[^\'"]*[/\\\\])?' + re.escape(base_bat) + r'(?:\.bat)?[\'"]'
                if re.search(bat_pattern, content, re.IGNORECASE):
                    data['uses'][other_rel_path] = 'soft'
                
    if name.endswith('.py'):
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod_base = alias.name.split('.')[-1]
                        target_f = f"{mod_base}.py"
                        if target_f in base_name_map:
                            for target_path in base_name_map[target_f]:
                                data['uses'][target_path] = 'hard'
                        # Paquetes con __init__.py
                        for target_path in all_scripts:
                            if target_path.endswith(f"/{mod_base}/__init__.py") or target_path == f"{mod_base}/__init__.py":
                                data['uses'][target_path] = 'hard'
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod_base = node.module.split('.')[-1]
                        target_f = f"{mod_base}.py"
                        if target_f in base_name_map:
                            for target_path in base_name_map[target_f]:
                                data['uses'][target_path] = 'hard'
                        for target_path in all_scripts:
                            if target_path.endswith(f"/{mod_base}/__init__.py") or target_path == f"{mod_base}/__init__.py":
                                data['uses'][target_path] = 'hard'
                    for alias in node.names:
                        target_f = f"{alias.name}.py"
                        if target_f in base_name_map:
                            for target_path in base_name_map[target_f]:
                                data['uses'][target_path] = 'hard'
                        for target_path in all_scripts:
                            if target_path.endswith(f"/{alias.name}/__init__.py") or target_path == f"{alias.name}/__init__.py":
                                data['uses'][target_path] = 'hard'
        except:
            pass

# Prepare nodes
unique_folders = set()
nodes = []
for rel_path_key, data in file_data.items():
    nodes.append({
        "id": rel_path_key,
        "name": data['name'],
        "group": data['folder'],
        "customDesc": data['desc'],
        "customPath": data['path'],
        "val": 1
    })
    unique_folders.add(data['folder'])

all_folders = set()
for f in unique_folders:
    if not f or f == ".":
        all_folders.add(".")
        continue
    parts = f.replace('\\', '/').split('/')
    for i in range(1, len(parts) + 1):
        all_folders.add('/'.join(parts[:i]))
        
if "." not in all_folders:
    all_folders.add(".")

for folder in all_folders:
    nodes.append({
        "id": f"folder_{folder}",
        "name": f"📁 {folder}",
        "group": folder,
        "customDesc": f"Ancla gravitacional para: {folder}",
        "customPath": "",
        "val": 0.001,
        "isFolder": True
    })

# Add Charm Brain Virtual Node
nodes.append({
    "id": "charm_brain",
    "name": "🧠 Charm Brain",
    "group": "Core AI",
    "customDesc": "Tú. La Inteligencia Artificial que orquesta, piensa y ejecuta en este sistema.",
    "customPath": "Entidad Virtual (Sin archivo físico)",
    "val": 10,
    "color": "#ff007f"
})

# Prepare edges
edges_dict = {}
connected_nodes = set()
for rel_path_key, data in file_data.items():
    for used, edge_type in data['uses'].items():
        if rel_path_key != used:
            pair1 = (rel_path_key, used)
            pair2 = (used, rel_path_key)
            connected_nodes.add(rel_path_key)
            connected_nodes.add(used)
            
            is_soft = (edge_type == 'soft')
            
            if pair2 in edges_dict:
                edges_dict[pair2]['bidirectional'] = True
                if not is_soft:
                    edges_dict[pair2]['is_soft'] = False
            else:
                edge_obj = {"source": rel_path_key, "target": used, "bidirectional": False, "is_soft": is_soft}
                edges_dict[pair1] = edge_obj

edges = list(edges_dict.values())

# Structural edges (Invisible constraints to cluster by folder)
for rel_path_key, data in file_data.items():
    f_group = data['folder'] if data['folder'] else "."
    edges.append({
        "source": f"folder_{f_group}",
        "target": rel_path_key,
        "is_file_link": True,
        "is_structural": True,
        "is_soft": True
    })

# Folder to Parent Folder links
for folder in all_folders:
    if folder == ".": continue
    parts = folder.split('/')
    if len(parts) > 1:
        parent = '/'.join(parts[:-1])
    else:
        parent = "."
    edges.append({
        "source": f"folder_{parent}",
        "target": f"folder_{folder}",
        "is_folder_link": True,
        "is_structural": True,
        "is_soft": True
    })

# Conectar la raíz de todo el sistema de carpetas a Charm Brain (gravedad estructural invisible)
edges.append({
    "source": "charm_brain",
    "target": "folder_.",
    "is_brain_link": True,
    "is_structural": True,
    "is_soft": True
})

# Enlaces VISIBLES pero SIN GRAVEDAD desde Charm Brain a los archivos core
core_connections = [
    'local_orchestrator.py', 'meetcharm_main.py', 'qdrant_memory_manager.py', 
    'charm_telegram.py', 'audit_logger.py', 'privacy_engine.py', 
    'Advanced_Tools/Scripts_Mantenimiento/generate_dist_canvas.py', 'build_distribution.py', 'run_safe.py',
    'discord_daemon.py', 'slack_daemon.py', 'n8n_bridge_daemon.py',
    'learning_p2p_daemon.py', 'swarm_ai_watchdog.py', 'skill_privacy.py'
]
for cc in core_connections:
    if cc in base_name_map:
        for p in base_name_map[cc]:
            edges.append({"source": "charm_brain", "target": p, "is_soft": False, "core": True, "is_visual_brain_link": True})
            connected_nodes.add(p)

# Enlaces VISIBLES pero SIN GRAVEDAD desde Charm Brain a los huérfanos
for rel_path_key in file_data.keys():
    if rel_path_key not in connected_nodes and rel_path_key != "charm_brain":
        edges.append({
            "source": "charm_brain", 
            "target": rel_path_key, 
            "is_soft": True,
            "orphan": True,
            "is_visual_brain_link": True
        })


html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Canvas 3D - Chask Swarm</title>
    <script src="https://unpkg.com/three@0.136.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three-spritetext@1.6.5/dist/three-spritetext.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.70.5/dist/3d-force-graph.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; background-color: #0d0d12; color: #ffffff; font-family: 'Inter', sans-serif; overflow: hidden; }}
        #network-container {{ position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; }}
        #side-panel {{ position: absolute; right: 0; top: 0; width: 400px; height: 100vh; box-sizing: border-box; background: rgba(20, 20, 30, 0.95); backdrop-filter: blur(10px); border-left: 1px solid #333; padding: 30px; display: flex; flex-direction: column; overflow-y: auto; z-index: 9999; box-shadow: -5px 0 25px rgba(0,0,0,0.8); }}
        h2 {{ color: #a178ff; margin-top: 0; font-size: 24px; border-bottom: 1px solid #444; padding-bottom: 10px; }}
        .field-label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-top: 20px; margin-bottom: 5px; }}
        .field-value {{ font-size: 16px; line-height: 1.5; background: rgba(0, 0, 0, 0.3); padding: 12px; border-radius: 8px; border: 1px solid #2a2a35; word-wrap: break-word; }}
        .path {{ font-family: monospace; color: #4fc3f7; }}
        #placeholder {{ color: #666; text-align: center; margin-top: 50%; font-style: italic; }}
        .card-content {{ display: none; }}
        .active .card-content {{ display: block; }}
        .active #placeholder {{ display: none; }}
        
        /* Controles 3D y Leyenda */
        #legend-panel {{
            position: absolute;
            bottom: 80px;
            left: 30px;
            background: rgba(20, 20, 30, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            z-index: 5;
            font-size: 13px;
            color: #ddd;
        }}
        #legend-panel h4 {{ margin: 0 0 10px 0; color: #a178ff; font-size: 14px; }}
        #legend-panel ul {{ margin: 0; padding-left: 20px; }}
        #legend-panel li {{ margin-bottom: 6px; }}

        #camera-controls {{
            position: absolute;
            bottom: 30px;
            left: 30px;
            display: flex;
            flex-direction: row;
            gap: 10px;
            z-index: 5;
        }}
        .cam-btn {{
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}
        .cam-btn:hover {{ background: rgba(161, 120, 255, 0.5); border-color: #a178ff; }}
    </style>
</head>
<body>

<div id="network-container"></div>
<div id="legend-panel">
    <h4>Controles del Mapa</h4>
    <ul>
        <li><strong>Girar:</strong> Clic Izquierdo + Arrastrar</li>
        <li><strong>Desplazar:</strong> Clic Derecho + Arrastrar</li>
        <li><strong>Zoom:</strong> Rueda del Ratón</li>
        <li><strong>Avanzar/Retroceder:</strong> Botones ↑/↓ o teclas <strong>W/S</strong></li>
    </ul>
</div>
<div id="camera-controls">
    <button class="cam-btn" id="cam-in" title="Avanzar (Zoom In)">↑</button>
    <button class="cam-btn" id="cam-out" title="Retroceder (Zoom Out)">↓</button>
</div>
<div id="side-panel">
    <div id="placeholder">Haz clic en un nodo del mapa 3D para inspeccionar sus propiedades.</div>
    <div class="card-content">
        <h2 id="pName">Nombre</h2>
        <div class="field-label">Ruta Relativa</div>
        <div class="field-value path" id="pPath">ruta/archivo.py</div>
        <div class="field-label">Carpeta Base</div>
        <div class="field-value" id="pFolder">Carpeta</div>
        <div class="field-label">Propósito / Descripción</div>
        <div class="field-value" id="pDesc">Descripción...</div>
        <div class="field-label" style="color: #ffb74d;">Archivos que usa (Saliente)</div>
        <div class="field-value" id="pUses" style="font-size: 14px;">-</div>
        <div class="field-label" style="color: #81c784;">Archivos que le usan (Entrante)</div>
        <div class="field-value" id="pUsedBy" style="font-size: 14px;">-</div>
    </div>
</div>

<script type="text/javascript">
    const gData = {{
        nodes: {json.dumps(nodes)},
        links: {json.dumps(edges)}
    }};

    const container = document.getElementById('network-container');
    const Graph = ForceGraph3D()(container)
        .graphData(gData)
        .nodeId('id')
        .nodeAutoColorBy('group')
        .nodeVisibility(node => !node.isFolder)
        .nodeVal('val')
        .nodeThreeObjectExtend(true)
        .nodeThreeObject(node => {{
            const isBrain = node.id === 'charm_brain';
            if (node.isFolder) {{
                // Nodos de carpeta completamente invisibles para agrupar sin ensuciar
                return new THREE.Object3D();
            }}
            const sprite = new SpriteText(node.name);
            sprite.color = '#ffffff';
            sprite.textHeight = isBrain ? 6 : 3;
            sprite.position.x = isBrain ? 12 : 8;
            sprite.position.y = 0;
            return sprite;
        }})
        .linkDirectionalArrowLength(link => link.is_structural ? 0 : (link.is_soft ? 2 : 3.5))
        .linkDirectionalArrowRelPos(1)
        .linkColor(link => {{
            // Ocultar TODO enlace estructural para que no haya líneas que apuntan "a la nada" (carpetas invisibles)
            if (link.is_structural) return "rgba(0,0,0,0)"; 
            
            // Mostrar enlaces reales de código
            if (link.is_visual_brain_link || link.core) return "rgba(255, 50, 150, 0.9)"; // Rayos rosas desde el Cerebro a los archivos
            if (link.orphan) return "rgba(255, 100, 150, 0.4)";
            if (link.is_soft) return "rgba(180, 180, 220, 0.4)";
            return "rgba(200, 160, 255, 0.6)";
        }})
        .onNodeClick(node => {{
            // Animación de cámara al nodo evitando divisiones por cero
            const distance = 100;
            const hyp = Math.hypot(node.x, node.y, node.z);
            const distRatio = 1 + distance / (hyp || 1);
            Graph.cameraPosition(
                {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
                node,
                1500
            );

            // Actualizar panel lateral
            const sidePanel = document.getElementById('side-panel');
            document.getElementById('pName').innerText = node.name;
            document.getElementById('pPath').innerText = node.customPath;
            document.getElementById('pFolder').innerText = node.group;
            document.getElementById('pDesc').innerText = node.customDesc;
            
            let uses = []; let usedBy = [];
            gData.links.forEach(e => {{
                const srcId = typeof e.source === 'object' ? e.source.id : e.source;
                const tgtId = typeof e.target === 'object' ? e.target.id : e.target;
                
                if (srcId === node.id && tgtId !== node.id) {{
                    uses.push(tgtId);
                    if (e.bidirectional) usedBy.push(tgtId);
                }}
                else if (tgtId === node.id && srcId !== node.id) {{
                    usedBy.push(srcId);
                    if (e.bidirectional) uses.push(srcId);
                }}
            }});
            
            document.getElementById('pUses').innerText = uses.length > 0 ? [...new Set(uses)].join('\\n') : 'Ninguno';
            document.getElementById('pUsedBy').innerText = usedBy.length > 0 ? [...new Set(usedBy)].join('\\n') : 'Ninguno';
            
            sidePanel.classList.add('active');
        }});

    // Físicas del sistema planetario
    Graph.d3Force('charge').strength(node => {{
        if (node.id === 'charm_brain') return -5000; // El sol repele masivamente
        return node.isFolder ? -3000 : -100; // Gran repulsión entre archivos para que formen una esfera hueca y amplia
    }}); 
    
    // Distancias orbitales
    Graph.d3Force('link').distance(link => {{
        if (link.is_file_link) return 150;      // Órbita gigante para los archivos, para que tengan muchísimo espacio
        if (link.is_folder_link) return 600;    // Distancia colosal entre carpetas
        if (link.is_brain_link) return 600;     // Distancia colosal al cerebro
        return 300;                             
    }});
    
    // Fuerza (gravedad) de los enlaces: Este es el secreto para que no sea un lío
    Graph.d3Force('link').strength(link => {{
        if (link.is_structural) return 1; // Ataduras estructurales rígidas (invisibles)
        if (link.is_visual_brain_link) return 0.01; // Los rayos rosas al cerebro NO tiran físicamente
        return 0.01; // Las dependencias de código NO ejercen fuerza física
    }});


    // Control de cámara (Desplazamiento Horizontal / Vertical / Zoom)
    function panCamera(dx, dy) {{
        const cam = Graph.camera();
        const controls = Graph.controls();
        
        const oldX = cam.position.x;
        const oldY = cam.position.y;
        const oldZ = cam.position.z;
        
        cam.translateX(dx);
        cam.translateY(dy);
        
        controls.target.x += (cam.position.x - oldX);
        controls.target.y += (cam.position.y - oldY);
        controls.target.z += (cam.position.z - oldZ);
        
        controls.update();
    }}
    
    function zoomCamera(dz) {{
        const cam = Graph.camera();
        const controls = Graph.controls();
        
        const oldX = cam.position.x;
        const oldY = cam.position.y;
        const oldZ = cam.position.z;
        
        cam.translateZ(dz);
        
        // Mover el target de rotación a la par que la cámara para permitir VUELO INFINITO
        controls.target.x += (cam.position.x - oldX);
        controls.target.y += (cam.position.y - oldY);
        controls.target.z += (cam.position.z - oldZ);
        
        controls.update();
    }}
    
    const ZOOM_STEP = 50;

    document.getElementById('cam-in').addEventListener('click', () => zoomCamera(-ZOOM_STEP));
    document.getElementById('cam-out').addEventListener('click', () => zoomCamera(ZOOM_STEP));

    // Movimiento continuo y fluido hacia delante/atrás
    const activeKeys = {{ w: false, s: false, ArrowUp: false, ArrowDown: false }};
    
    window.addEventListener('keydown', (e) => {{
        const key = e.key === 'w' || e.key === 'W' ? 'w' : (e.key === 's' || e.key === 'S' ? 's' : e.key);
        if (activeKeys.hasOwnProperty(key)) activeKeys[key] = true;
    }});
    
    window.addEventListener('keyup', (e) => {{
        const key = e.key === 'w' || e.key === 'W' ? 'w' : (e.key === 's' || e.key === 'S' ? 's' : e.key);
        if (activeKeys.hasOwnProperty(key)) activeKeys[key] = false;
    }});

    function movementLoop() {{
        let dz = 0;
        const speed = 15; // Velocidad de vuelo continuo
        if (activeKeys.w || activeKeys.ArrowUp) dz -= speed;
        if (activeKeys.s || activeKeys.ArrowDown) dz += speed;
        
        if (dz !== 0) {{
            zoomCamera(dz);
        }}
        requestAnimationFrame(movementLoop);
    }}
    movementLoop();

    // Agrandar la caja de arena visual (Frustum Culling) para universos gigantes
    setTimeout(() => {{
        const cam = Graph.camera();
        cam.far = 100000; // Visión prácticamente infinita
        cam.updateProjectionMatrix();
    }}, 500);

</script>
</body>
</html>
"""

output_path = r"C:\Users\fnora\Desktop\Chask_Swarm_Dist_Canvas.html"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Canvas distribuido generado exitosamente en: {output_path}")
