@echo off
chcp 65001 >nul
title Optima MTK Tool - Installateur de Pilotes d'Atelier
echo ======================================================================
echo       OPTIMA MTK TOOL - INSTALLATION DES PILOTES MOBILES D'ATELIER
echo ======================================================================
echo.

:: Vérification des privilèges Administrateur
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Élévation des privilèges requise...
    echo     Demande d'autorisation Administrateur (UAC)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo [+] Exécution du script d'installation silencieuse PnPUtil...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_drivers.ps1"

echo.
echo ======================================================================
echo Fin de l'opération.
echo ======================================================================
pause
