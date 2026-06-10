@echo off
title Chask Swarm - Recuperacion de Estado
color 0C
echo.
echo [RECUPERACION] Restaurando estado desde backup 20260516_185141...
echo.
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\charm_telegram.py" "C:\Program Files\Chask_Swarm\charm_telegram.py" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\telegram_config.json" "C:\Program Files\Chask_Swarm\telegram_config.json" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\memory.md" "C:\Program Files\Chask_Swarm\memory.md" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\projects_memory.md" "C:\Program Files\Chask_Swarm\projects_memory.md" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\directives.md" "C:\Program Files\Chask_Swarm\directives.md" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\security.md" "C:\Program Files\Chask_Swarm\security.md" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\Cuestionario_Soul.md" "C:\Program Files\Chask_Swarm\Cuestionario_Soul.md" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\Prompt_Telegram_Charm.md" "C:\Program Files\Chask_Swarm\Prompt_Telegram_Charm.md" >nul
xcopy /E /I /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\Advanced_Tools" "C:\Program Files\Chask_Swarm\Advanced_Tools" >nul
xcopy /E /I /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\Hive_Framework" "C:\Program Files\Chask_Swarm\Hive_Framework" >nul
copy /Y "C:\Program Files\Chask_Swarm\Chask_Backups\pre_change\backup_20260516_185141\Instalar_Dependencias.bat" "C:\Program Files\Chask_Swarm\Instalar_Dependencias.bat" >nul

echo.
echo [OK] Sistema restaurado al estado del 20260516_185141
echo [OK] Reinicia Chask Swarm para aplicar los cambios.
echo.
pause
