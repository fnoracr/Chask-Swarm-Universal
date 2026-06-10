@echo off
REM start_swarm.bat — Arranca el enjambre Chask Swarm (Arquitectura V3)
REM Motor maestro: process_watchdog.py como orquestador principal.

SET BASE=C:\Program Files\Chask_Swarm
SET PYTHON=C:\Users\fnora\AppData\Local\Programs\Python\Python311\pythonw.exe
SET IDE=C:\Users\fnora\AppData\Local\Programs\Antigravity\Antigravity.exe

REM ================================================================
REM [0/4] Eliminar el Kill Switch Lock (permite que el watchdog actúe)
REM ================================================================
if exist "%BASE%\kill_switch.lock" del /F /Q "%BASE%\kill_switch.lock"

REM Configurar Workspace de Charm automáticamente
python "%BASE%\setup_charm_workspace.py"

REM ================================================================
REM [1/4] Levantar memoria vectorial y automatización (Docker)
REM ================================================================
echo [1/4] Levantando Qdrant y N8N via Docker...
docker start qdrant >nul 2>&1
if %errorlevel% neq 0 (
    docker run -d --name qdrant --restart=always -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant >nul 2>&1
)
docker start n8n >nul 2>&1

REM Usaremos un script de python para prevenir duplicados de manera robusta
SET LAUNCHER="%PYTHON%" "%BASE%\Advanced_Tools\start_if_not_running.py"
SET AUDIT_LOG="%BASE%\Logs_Sistema\swarm_power_audit.log"

REM Iniciamos los tres guardianes clave
echo [%date% %time%] [BATCH] Ejecutando launcher para process_watchdog.py... >> %AUDIT_LOG%
%LAUNCHER% "Advanced_Tools/Daemons/process_watchdog.py" "%PYTHON%" "%BASE%\Advanced_Tools\Daemons\process_watchdog.py"

echo [%date% %time%] [BATCH] Ejecutando launcher para unified_channel_daemon.py... >> %AUDIT_LOG%
%LAUNCHER% "unified_channel_daemon.py" "%PYTHON%" "%BASE%\Advanced_Tools\Daemons\unified_channel_daemon.py"

REM echo [%date% %time%] [BATCH] Ejecutando launcher para nora_queue_watcher.py... >> %AUDIT_LOG%
REM %LAUNCHER% "nora_queue_watcher.py" "%PYTHON%" "%BASE%\Advanced_Tools\Daemons\nora_queue_watcher.py"

echo [%date% %time%] [BATCH] Ejecutando launcher para n8n_bridge_daemon.py... >> %AUDIT_LOG%
%LAUNCHER% "n8n_bridge_daemon.py" "%PYTHON%" "%BASE%\Advanced_Tools\modules\N8N_Integration\n8n_bridge_daemon.py"

echo [%date% %time%] [BATCH] Ejecutando launcher para telegram_sentinel.py... >> %AUDIT_LOG%
%LAUNCHER% "telegram_sentinel.py" "%PYTHON%" "%BASE%\Advanced_Tools\Daemons\telegram_sentinel.py"

echo [%date% %time%] [BATCH] Ejecutando launcher para guardian_daemon.py... >> %AUDIT_LOG%
%LAUNCHER% "guardian_daemon.py" "%PYTHON%" "%BASE%\Advanced_Tools\Daemons\guardian_daemon.py"

REM 4. Abrir el IDE Antigravity (Unica Instancia)
tasklist /FI "IMAGENAME eq Antigravity.exe" 2>NUL | find /I /N "Antigravity.exe">NUL
if "%ERRORLEVEL%"=="0" goto skip_ide

echo [%date% %time%] [BATCH] Levantando IDE Antigravity (Instancia Unica Nora)... >> %AUDIT_LOG%
set "LAUNCH_IDE_VBS=%BASE%\_launch_ide_tg.vbs"
> "%LAUNCH_IDE_VBS%" echo Set WshShell = CreateObject("WScript.Shell")
>> "%LAUNCH_IDE_VBS%" echo WshShell.Run """" ^& "%IDE%" ^& """ ""%BASE%\Charm""", 1, False
wscript //nologo "%LAUNCH_IDE_VBS%"
del "%LAUNCH_IDE_VBS%" >nul 2>&1

:skip_ide
echo [%date% %time%] [BATCH] Antigravity check finalizado. >> %AUDIT_LOG%


exit
