@echo off
title Servidor n8n Local
echo ==================================================
echo Iniciando n8n Local...
echo ==================================================
echo.
echo Por favor, no cierres esta ventana mientras uses n8n.
echo Para apagar n8n, simplemente cierra esta ventana.
echo.

:: Esperar 3 segundos y abrir el navegador en segundo plano
start "" /b powershell -c "Start-Sleep -Seconds 3; Start-Process 'http://localhost:5678'"

:: Cambiar al directorio de n8n para que encuentre sus archivos
cd /d C:\Users\fnora\n8n_local

:: Arrancar n8n
"C:\Users\fnora\node22\node-v22.14.0-win-x64\node.exe" "C:\Users\fnora\node_modules\n8n\bin\n8n" start
