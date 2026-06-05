@echo off
title Chask Swarm - Ejecutando Enjambre
color 0A

echo [1/4] Levantando Memoria Vectorial (Docker Qdrant) y Automatización (Docker n8n)...
docker start qdrant >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Qdrant no estaba creado. Intentando levantar nuevo contenedor...
    docker run -d --name qdrant --restart=always -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant >nul 2>&1
)

docker start n8n >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] n8n no estaba creado. Será manejado por el watchdog o revisa Docker Desktop.
)

:: ================================================================
:: [2/4] Lanzar TODOS los daemons como procesos INDEPENDIENTES
:: Se usa WScript.Shell.Run con flag 0 (oculto) para que cada
:: proceso pythonw sea completamente independiente del bat y del IDE.
:: Asi, cerrar [Nombre_IA] NO mata los daemons.
:: ================================================================
echo [2/4] Activando daemons como procesos independientes...

set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
set "PW=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"

:: Daemon unificado (Telegram + Discord + Web) — con python.exe para permisos de UI
wmic process where "commandline like '%%unified_channel_daemon.py%%'" get processid | findstr [0-9] >nul
if errorlevel 1 (
    echo [2.1] Lanzando daemon unificado...
    start "ChaskDaemon" /MIN "%PY%" "%~dp0Advanced_Tools\unified_channel_daemon.py"
) else (
    echo [2.1] Daemon unificado ya esta corriendo, omitiendo.
)

:: Limpieza de procesos zombies antes de arrancar (CRÍTICO)
echo [2.0] Purgando procesos zombies antiguos...
"%PY%" Advanced_Tools\shutdown_cleanup.py

:: Daemons secundarios (no necesitan UI, pueden usar pythonw)
set "LAUNCH_VBS=%~dp0_launch_daemons.vbs"
> "%LAUNCH_VBS%" echo Set WshShell = CreateObject("WScript.Shell")
>> "%LAUNCH_VBS%" echo WshShell.CurrentDirectory = "%~dp0"
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\process_watchdog.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\backup_system.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\daily_report.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\web_monitor.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\auto_updater.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\1_wakeup_daemon.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\swarm_ai_watchdog.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\win_telemetry_svc.py", 0, False
>> "%LAUNCH_VBS%" echo WshShell.Run """%PW%"" Advanced_Tools\modules\N8N_Integration\n8n_bridge_daemon.py", 0, False

wscript //nologo "%LAUNCH_VBS%"
del "%LAUNCH_VBS%" >nul 2>&1


:: ================================================================
:: [3/4] Abrir IDE de [Nombre_IA] DESPUES de los daemons
:: ================================================================
echo [3/4] Levantando Interfaz Neuronal (IDE [Nombre_IA])...

set "IDE_PATH=%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe"
set "LAUNCH_IDE_VBS=%~dp0_launch_ide.vbs"

> "%LAUNCH_IDE_VBS%" echo Set WshShell = CreateObject("WScript.Shell")
>> "%LAUNCH_IDE_VBS%" echo Set fso = CreateObject("Scripting.FileSystemObject")
>> "%LAUNCH_IDE_VBS%" echo idePath = "%IDE_PATH%"
>> "%LAUNCH_IDE_VBS%" echo If Not fso.FileExists(idePath) Then
>> "%LAUNCH_IDE_VBS%" echo     idePath = ""
>> "%LAUNCH_IDE_VBS%" echo End If
>> "%LAUNCH_IDE_VBS%" echo If idePath ^<^> "" Then
>> "%LAUNCH_IDE_VBS%" echo     WshShell.Run """" ^& idePath ^& """", 1, False
>> "%LAUNCH_IDE_VBS%" echo     WScript.Sleep 5000
>> "%LAUNCH_IDE_VBS%" echo End If

wscript //nologo "%LAUNCH_IDE_VBS%"
del "%LAUNCH_IDE_VBS%" >nul 2>&1


:: [4/4] Inyectar contexto Enjambre
:: ================================================================
echo [4/4] Inyectando Alma y Memoria (Contexto Enjambre)...
python Advanced_Tools\boot_injection.py >nul 2>&1

echo.
echo ===================================================
echo   CHASK SWARM - ESTADO: ONLINE (SEGUNDO PLANO)
echo ===================================================
echo [OK] Enjambre esta escuchando en modo invisible.
echo [OK] Comunicaciones: Telegram + Discord + Web via unified_daemon.py
echo [OK] Daemons INDEPENDIENTES del IDE.
echo [OK] Puedes cerrar [Nombre_IA] sin matar el enjambre.
echo ===================================================
echo.
echo Esta ventana se cerrara automaticamente en 5 segundos...
ping 127.0.0.1 -n 6 > nul
exit
