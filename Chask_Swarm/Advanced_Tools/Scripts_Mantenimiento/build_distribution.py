import os
import shutil
import zipfile

BASE_DIR = r"C:\Program Files\Chask_Swarm"
DIST_DIR = os.path.join(BASE_DIR, "Distribucion")
STAGING_DIR = os.path.join(DIST_DIR, "Staging_Chask_Swarm")
OUTPUT_ZIP = os.path.join(DIST_DIR, "Chask_Swarm_Core.zip")

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

def build_dist():
    print("Iniciando proceso de empaquetado seguro...")
    
    # Clean staging area if exists
    if os.path.exists(STAGING_DIR):
        shutil.rmtree(STAGING_DIR)
    os.makedirs(STAGING_DIR)
    
    # Copy files
    for root, dirs, files in os.walk(BASE_DIR):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        rel_dir = os.path.relpath(root, BASE_DIR)
        
        # Skip if in excluded subdirs
        skip_current = False
        for sub in EXCLUDED_SUBDIRS:
            if rel_dir.endswith(sub) or sub in rel_dir:
                skip_current = True
                break
        if skip_current:
            continue
            
        target_dir = os.path.join(STAGING_DIR, rel_dir) if rel_dir != "." else STAGING_DIR
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        for file in files:
            if not should_exclude(root, file):
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_dir, file)
                shutil.copy2(src_file, dst_file)
                
    print("Archivos copiados al entorno de Staging.")
    
    # -------------------------------------------------------------
    # CREACIÓN DE ESQUELETOS (Templates vacíos para el nuevo usuario)
    # -------------------------------------------------------------
    print("Generando esqueletos vacíos para configuración e historial...")
    
    def read_template(filename, fallback):
        tpl_path = os.path.join(DIST_DIR, "Templates", filename)
        if os.path.exists(tpl_path):
            with open(tpl_path, 'r', encoding='utf-8') as f:
                return f.read()
        return fallback

    skeletons = {
        'Configuracion/master_credentials.json': '{\n  "credentials": {}\n}',
        'Configuracion/authorized_users.json': '[\n]',
        'Configuracion/passport.json': '{\n  "nodes": []\n}',
        'Configuracion/users.json': '{}',
        'Configuracion/channels_config.json': '{\n  "channels": {}\n}',
        'Colas_Mensajes/input_queue.json': '[]',
        'Colas_Mensajes/pending_messages.json': '[]',
        'Colas_Mensajes/channel_messages.json': '{}',
        'memory.md': '# Memoria Corto Plazo\n\n(Archivo de estado en tiempo real. Vacío por defecto.)\n',
        'projects_memory.md': '# Registro Histórico de Proyectos\n\n| Fecha de Finalización | Nombre del Proyecto | Palabras Clave | Estado |\n| :--- | :--- | :--- | :--- |\n',
        'Configuracion/learned_lessons.json': '[]',
        'Configuracion/evolutionary_memory.json': '[]',
        'Configuracion/guardian_state.json': '{}',
        'graph_memory.json': '{}',
        'soul.md': read_template('generic_soul.md', '# Identidad de la IA\n\n(Archivo de personalidad virgen. Define aquí tu identidad y directrices éticas base.)\n'),
        'directives.md': read_template('generic_directives.md', '# Directivas Operativas\n\n(Reglas y protocolos operativos base de la distribución.)\n'),
        'security.md': read_template('generic_security.md', '# Protocolo de Seguridad\n\n(Reglas de seguridad y firewall lógico de la IA.)\n'),
        'Configuracion/workflows_active.json': '[]',
        'Configuracion/workflows_modified.json': '[]',
        'skill_learner_log.json': '[]'
    }
    
    for filename, content in skeletons.items():
        with open(os.path.join(STAGING_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(content)
            
    print("Esqueletos creados.")
    print("Comprimiendo distribución...")
    
    # Create ZIP
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)
        
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(STAGING_DIR):
            for file in files:
                abs_file = os.path.join(root, file)
                arcname = os.path.relpath(abs_file, STAGING_DIR)
                zipf.write(abs_file, arcname)
                
    print(f"ZIP generado exitosamente en: {OUTPUT_ZIP}")
    
    # Cleanup
    shutil.rmtree(STAGING_DIR)
    print("Staging limpiado. Proceso finalizado.")

if __name__ == "__main__":
    build_dist()
