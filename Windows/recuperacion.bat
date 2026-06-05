@echo off
title Chask Swarm - Recuperacion de Estado
color 0C
echo.
echo [RECUPERACION] Restaurando estado desde backup 20260516_185141...
echo.
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\charm_telegram.py" "C:\Program Files\Chask_Swarn\charm_telegram.py" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\telegram_config.json" "C:\Program Files\Chask_Swarn\telegram_config.json" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\memory.md" "C:\Program Files\Chask_Swarn\memory.md" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\projects_memory.md" "C:\Program Files\Chask_Swarn\projects_memory.md" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\directives.md" "C:\Program Files\Chask_Swarn\directives.md" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\security.md" "C:\Program Files\Chask_Swarn\security.md" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\Cuestionario_Soul.md" "C:\Program Files\Chask_Swarn\Cuestionario_Soul.md" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\Prompt_Telegram_[Nombre_IA].md" "C:\Program Files\Chask_Swarn\Prompt_Telegram_[Nombre_IA].md" >nul
xcopy /E /I /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\Advanced_Tools" "C:\Program Files\Chask_Swarn\Advanced_Tools" >nul
xcopy /E /I /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\Hive_Framework" "C:\Program Files\Chask_Swarn\Hive_Framework" >nul
copy /Y "C:\Program Files\Chask_Swarn\Chask_Backups\pre_change\backup_20260516_185141\Instalar_Dependencias.bat" "C:\Program Files\Chask_Swarn\Instalar_Dependencias.bat" >nul

echo.
echo [OK] Sistema restaurado al estado del 20260516_185141
echo [OK] Reinicia Chask Swarm para aplicar los cambios.
echo.
pause
