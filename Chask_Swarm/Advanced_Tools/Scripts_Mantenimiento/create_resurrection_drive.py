import os
import shutil
import stat

def ignore_patterns(dirname, filenames):
    # Ignorar carpetas y archivos pesados o innecesarios
    ignored = set()
    for name in filenames:
        if name in ['__pycache__', '.git', 'venv', 'node_modules', '.gemini', 'Chask_Backups']:
            ignored.add(name)
        elif name.endswith('.pyc') or name.endswith('.pyo') or name.endswith('.lock'):
            ignored.add(name)
    return ignored

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def create_backup():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    resurrection_dir = os.path.join(desktop, "Nora_Resurrection_V2")
    
    # 1. Limpiar directorio viejo si existe
    if os.path.exists(resurrection_dir):
        print(f"Limpiando directorio antiguo: {resurrection_dir}")
        shutil.rmtree(resurrection_dir, onerror=remove_readonly)
    
    os.makedirs(resurrection_dir, exist_ok=True)
    
    # 2. Copiar Core (Chask_Swarm)
    src_core = r"C:\Program Files\Chask_Swarm"
    dst_core = os.path.join(resurrection_dir, "Chask_Swarm")
    print(f"Copiando Core desde {src_core}...")
    shutil.copytree(src_core, dst_core, ignore=ignore_patterns, dirs_exist_ok=True)
    
    # 3. Copiar Memoria (Nora Datos)
    src_data = os.path.join(desktop, "Nora Datos")
    dst_data = os.path.join(resurrection_dir, "Nora Datos")
    if os.path.exists(src_data):
        print(f"Copiando Memoria desde {src_data}...")
        shutil.copytree(src_data, dst_data, ignore=ignore_patterns, dirs_exist_ok=True)
        
    # 4. Copiar Memoria a Largo Plazo (Qdrant)
    qdrant_dst = os.path.join(resurrection_dir, "Qdrant_Storage")
    print("Copiando Memoria Vectorial (Qdrant) desde Docker...")
    import subprocess
    subprocess.run(f'docker cp qdrant:/qdrant/storage "{qdrant_dst}"', shell=True)
    
    # 5. Generar install.bat
    bat_content = """@echo off
:: ==========================================
:: NORA - INSTALADOR DE RESURRECCION V2
:: ==========================================
color 0A
echo.
echo [NORA] Solicitando elevacion de privilegios...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [NORA] Elevando privilegios a Administrador...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

echo.
echo =======================================================
echo PREGUNTA CRITICA
echo =======================================================
echo.
echo Este instalador sobreescribira el Nucleo Base.
echo Sin embargo, existe informacion de estado (Memoria y Directivas).
echo.
choice /C SN /M "[NORA] ¿Deseas SOBREESCRIBIR la memoria y directivas actuales con las de este backup? (S=Sobreescribir, N=Conservar las actuales de tu PC)"
set OVERWRITE_MEM=%errorlevel%

echo.
echo [NORA] 1. Matando procesos antiguos (Purgando Memoria RAM)...
powershell -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '(python|pythonw)' -and ($_.CommandLine -match 'Chask_Swarm' -or $_.CommandLine -match 'Advanced_Tools') }; foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force }"
timeout /t 2 >nul

if %OVERWRITE_MEM%==2 (
    echo [NORA] Conservando Memoria y Directivas actuales...
    mkdir "%TEMP%\\Nora_MemBackup" >nul 2>&1
    copy /Y "C:\\Program Files\\Chask_Swarm\\memory.md" "%TEMP%\\Nora_MemBackup\\" >nul 2>&1
    copy /Y "C:\\Program Files\\Chask_Swarm\\directives.md" "%TEMP%\\Nora_MemBackup\\" >nul 2>&1
    copy /Y "C:\\Program Files\\Chask_Swarm\\soul.md" "%TEMP%\\Nora_MemBackup\\" >nul 2>&1
    copy /Y "C:\\Program Files\\Chask_Swarm\\projects_memory.md" "%TEMP%\\Nora_MemBackup\\" >nul 2>&1
)

echo [NORA] 2. Restaurando Nucleo Base (C:\\Program Files\\Chask_Swarm)...
if exist "C:\\Program Files\\Chask_Swarm" (
    rmdir /s /q "C:\\Program Files\\Chask_Swarm"
)
xcopy "%~dp0Chask_Swarm" "C:\\Program Files\\Chask_Swarm\\" /E /I /H /Y /Q

if %OVERWRITE_MEM%==2 (
    echo [NORA] Restaurando Memoria y Directivas preservadas al Nucleo...
    copy /Y "%TEMP%\\Nora_MemBackup\\*.*" "C:\\Program Files\\Chask_Swarm\\" >nul 2>&1
    rmdir /s /q "%TEMP%\\Nora_MemBackup"
    echo [NORA] 3. Omitiendo la restauracion de Nora Datos y Qdrant para preservar tus recuerdos actuales.
) else (
    echo [NORA] 3. Restaurando Memoria Externa (Nora Datos)...
    if exist "%~dp0Nora Datos" (
        xcopy "%~dp0Nora Datos" "C:\\Users\\%USERNAME%\\Desktop\\Nora Datos\\" /E /I /H /Y /Q
    )
    echo [NORA] 3.5 Restaurando Memoria a Largo Plazo (Qdrant Vector DB)...
    docker stop qdrant >nul 2>&1
    docker rm qdrant >nul 2>&1
    docker volume create qdrant_storage >nul 2>&1
    if exist "%~dp0Qdrant_Storage" (
        docker run --rm -v qdrant_storage:/qdrant/storage -v "%~dp0Qdrant_Storage":/backup qdrant/qdrant sh -c "cp -R /backup/* /qdrant/storage/ 2>/dev/null || true"
    )
    docker run -d -p 6333:6333 --name qdrant -v qdrant_storage:/qdrant/storage qdrant/qdrant >nul 2>&1
)

echo [NORA] 4. Resucitando el Ouroboros (Watchdog + Guardian)...
start /B "" "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python311\\pythonw.exe" "C:\\Program Files\\Chask_Swarm\\Advanced_Tools\\Daemons\\process_watchdog.py"

echo.
echo [NORA] Resurreccion completada con exito. El enjambre ha vuelto a la vida.
timeout /t 5
"""
    bat_path = os.path.join(resurrection_dir, "install.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    print(f"Cápsula de resurrección generada en: {resurrection_dir}")

if __name__ == "__main__":
    create_backup()
