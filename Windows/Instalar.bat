@echo off
title Chask Swarm - Instalador y Configuration
color 0A

:: EULA - Acuerdo de Licencia
echo Set wshShell = CreateObject("WScript.Shell") > eula.vbs
echo result = MsgBox("CHASK SWARM - ACUERDO DE LICENCIA (EULA)" ^& vbCrLf ^& vbCrLf ^& "Al pulsar SI confirmas que:" ^& vbCrLf ^& "1. Este ecosistema de Inteligencia Artificial es GRATUITO exclusivamente para USO PERSONAL y NO COMERCIAL." ^& vbCrLf ^& "2. El uso EMPRESARIAL, PROFESIONAL o COMERCIAL requiere la adquisicion de una Licencia Comercial de Pago." ^& vbCrLf ^& "3. Queda prohibida la reventa o distribucion sin autorizacion expresa." ^& vbCrLf ^& vbCrLf ^& "Este software esta registrado." ^& vbCrLf ^& vbCrLf ^& "¿Aceptas estos terminos para continuar con la instalacion?", 4 + 32, "Licencia Chask Swarm") >> eula.vbs
echo WScript.Quit result >> eula.vbs
cscript //nologo eula.vbs
if %errorlevel% neq 6 (
    echo Instalacion cancelada por el usuario. No se acepto la licencia.
    del eula.vbs
    pause
    exit /b
)
del eula.vbs

:: Verificar [Nombre_IA] Base de Google
if not exist "%USERPROFILE%\.gemini\charm" (
    echo [!] No se ha detectado el motor principal de [Nombre_IA] AI.
    echo [!] Descargando instalador oficial desde https://charm.google/ ...
    curl -L -o [Nombre_IA]_Setup.exe "https://charm.google/download/windows/installer.exe" >nul 2>&1
    if exist [Nombre_IA]_Setup.exe (
        echo Instalando [Nombre_IA]... (Esto abrira el instalador)
        start /wait [Nombre_IA]_Setup.exe
        del [Nombre_IA]_Setup.exe
        echo Instalacion de [Nombre_IA] completada.
    ) else (
        echo No se pudo descargar automaticamente. Abriendo la web oficial...
        start https://charm.google/
        echo Por favor, instalalo manualmente y luego pulsa una tecla.
        pause
    )
)

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando Python automaticamente (esto puede tardar unos minutos)...
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    echo Refrescando entorno...
    call refreshenv >nul 2>&1
)

:: Configuración de Credenciales
echo Set wshShell = CreateObject("WScript.Shell") > temp_box.vbs
echo WScript.StdOut.Write InputBox("Paso 1: Pega tu Token HTTP del Bot de Telegram (ej. 123456:ABC...):", "Configuration de Chask Swarm") >> temp_box.vbs
for /f "tokens=*" %%a in ('cscript //nologo temp_box.vbs') do set bot_token=%%a
del temp_box.vbs

echo Set wshShell = CreateObject("WScript.Shell") > temp_box2.vbs
echo WScript.StdOut.Write InputBox("Paso 2: Pega tu ID Numérico de Telegram:", "Configuration de Chask Swarm") >> temp_box2.vbs
for /f "tokens=*" %%a in ('cscript //nologo temp_box2.vbs') do set user_id=%%a
del temp_box2.vbs

:: Generar archivo config básico
echo {> telegram_config.json
echo   "telegram_bot": "%bot_token%",>> telegram_config.json
echo   "telegram_admin": "%user_id%",>> telegram_config.json
echo   "ffmpeg_path": ".\\ffmpeg.exe",>> telegram_config.json
echo   "email_imap": "",>> telegram_config.json
echo   "email_user": "",>> telegram_config.json
echo   "email_pass": "">> telegram_config.json
echo }>> telegram_config.json

:: Instalación de dependencias de Python
echo Instalando dependencias necesarias...
pip install requests pydub SpeechRecognition pygetwindow pyautogui pyperclip qdrant-client gTTS plyer flask schedule openai ollama cohere groq -q

:: Configurar permisos de escritura para operacion autonoma
:: Esto permite que la IA y los daemons modifiquen archivos sin requerir elevacion UAC
echo Configurando permisos de carpeta para operacion autonoma...
icacls "%~dp0" /grant %USERNAME%:(OI)(CI)F /T /Q >nul 2>&1

:: Crear acceso directo en el escritorio
echo Creando acceso directo de arranque en el Escritorio...
echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Chask Swarm.lnk" >> create_shortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcut.vbs
echo oLink.TargetPath = "%~dp0Inicio.bat" >> create_shortcut.vbs
echo oLink.WorkingDirectory = "%~dp0" >> create_shortcut.vbs
echo oLink.IconLocation = "%~dp0Binaries\chask_logo.ico" >> create_shortcut.vbs
echo oLink.Save >> create_shortcut.vbs
cscript //nologo create_shortcut.vbs
del create_shortcut.vbs

:: Configurar Docker Desktop para iniciar con Windows
echo Configurando Docker Desktop para inicio automatico...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Docker Desktop" /t REG_SZ /d "\"C:\Program Files\Docker\Docker\Docker Desktop.exe\"" /f >nul 2>&1

:: Configurar Chask Swarm para iniciar con Windows (con retraso)
echo Creando script de inicio automatico para Chask Swarm...
set "startupFolder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
echo WScript.Sleep 40000 > "%startupFolder%\Arrancar_Chask_Swarm.vbs"
echo Set WshShell = CreateObject("WScript.Shell") >> "%startupFolder%\Arrancar_Chask_Swarm.vbs"
echo WshShell.Run """%~dp0Inicio.bat""", 0, False >> "%startupFolder%\Arrancar_Chask_Swarm.vbs"

echo.
echo [OK] Instalacion y Configuration completadas.
echo [OK] Ahora puedes usar el archivo 'Inicio.bat' o el acceso directo del escritorio.
echo.
pause
