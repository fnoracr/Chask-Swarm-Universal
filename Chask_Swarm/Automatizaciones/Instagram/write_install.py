import os
import shutil

univ_dir = r"C:\Users\fnora\Desktop\Distribucion_Universal"
langs_dir = os.path.join(univ_dir, "Langs")

# Rename Install.bat to _Install_Internal.bat in all Langs
for lang in os.listdir(langs_dir):
    lang_path = os.path.join(langs_dir, lang)
    if os.path.isdir(lang_path):
        install_bat = os.path.join(lang_path, "Install.bat")
        internal_bat = os.path.join(lang_path, "_Install_Internal.bat")
        if os.path.exists(install_bat):
            os.rename(install_bat, internal_bat)

bat_content = """@echo off
title Chask Swarm Universal Setup
color 0B

echo ===================================================
echo   CHASK SWARM - UNIVERSAL INSTALLER
echo ===================================================
echo.
echo Select your language / Selecciona tu idioma:
echo.
echo [1] Espanol (ES)
echo [2] English (EN)
echo [3] Portugues (PT)
echo [4] Chinese (ZH)
echo [5] Russian (RU)
echo [6] Francais (FR)
echo.

choice /c 123456 /n /m "Choose an option [1-6]: "

if errorlevel 6 set LANG=FR
if errorlevel 5 set LANG=RU
if errorlevel 4 set LANG=ZH
if errorlevel 3 set LANG=PT
if errorlevel 2 set LANG=EN
if errorlevel 1 set LANG=ES
if "%LANG%"=="" set LANG=ES

echo.
echo Installing Language Pack: %LANG%...
xcopy /Y /E "%~dp0Langs\\%LANG%\\*" "%~dp0" >nul
echo Language Pack Installed.
echo.
echo Starting actual installation...
ping 127.0.0.1 -n 2 >nul

:: Transfer execution to the newly extracted internal installer
start "" "%~dp0_Install_Internal.bat"
exit
"""

with open(os.path.join(univ_dir, "Install.bat"), "w") as f:
    f.write(bat_content)

print("Universal Installer written and internal bats renamed.")
