@echo off
REM kill_switch_daemon.bat — Mantiene vivo el NSS ([Nombre_IA] Core Supervisor) V3
REM Este script debe ejecutarse al inicio y siempre estar corriendo

SET BASE=C:\Program Files\Chask_Swarn
SET PYTHON=C:\Users\fnora\AppData\Local\Programs\Python\Python311\python.exe
SET DAEMON="%BASE%\Nueva_Arquitectura\nora_core_supervisor.py"
SET LOG="%BASE%\nora_core_batch.log"

:LOOP
echo [%DATE% %TIME%] Iniciando nora_core_supervisor... >> %LOG%
"%PYTHON%" %DAEMON% >> %LOG% 2>&1
echo [%DATE% %TIME%] Daemon caido, reiniciando en 5s... >> %LOG%
timeout /t 5 /nobreak >nul
goto LOOP
