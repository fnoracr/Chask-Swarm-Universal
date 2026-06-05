@echo off
echo ==============================================================
echo Instalador Automatico de Dependencias para [Nombre_IA] AI
echo ==============================================================
echo.
echo Comprobando si Python y PIP estan instalados...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se ha detectado Python.
    echo Por favor, instala Python 3 desde python.org y asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b
)

echo Instalando librerias de Python necesarias...
pip install requests pydub SpeechRecognition pygetwindow pyautogui pyperclip qdrant-client gTTS plyer

echo.
echo ==============================================================
echo [EXITO] Las librerias se han instalado correctamente.
echo.
echo NOTA: Hemos incluido el archivo ffmpeg.exe en esta misma 
echo carpeta, asi que ya NO necesitas instalarlo manualmente para 
echo transcribir notas de voz.
echo ==============================================================
pause
