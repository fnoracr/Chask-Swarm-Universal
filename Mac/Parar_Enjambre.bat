@echo off
title Chask Swarm - Deteniendo Enjambre
color 0C

echo [1/4] Deteniendo proceso guardián (Watchdog)...
wmic process where "commandline like '%%process_watchdog.py%%'" call terminate >nul 2>&1

echo [2/4] Deteniendo todos los daemons de Python...
wmic process where "commandline like '%%Chask_Swarm%%' and name='pythonw.exe'" call terminate >nul 2>&1
wmic process where "commandline like '%%Chask_Swarm%%' and name='python.exe'" call terminate >nul 2>&1

echo [3/4] Deteniendo Memoria Vectorial (Docker Qdrant)...
docker stop qdrant >nul 2>&1

echo [4/4] Apagando Antigravity...
taskkill /F /IM Antigravity.exe >nul 2>&1

echo ===================================================
echo   CHASK SWARM - ESTADO: OFFLINE
echo ===================================================
exit
