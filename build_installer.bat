@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Optima MTK Tool - Compilation Installateur Inno Setup

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║        Optima MTK Tool - Build Installateur Setup        ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

REM ─── Verification des prerequis ─────────────────────────────────────────────

REM 1. Verifier que le build PyInstaller existe
if not exist "dist\OptimaMTKTool\OptimaMTKTool.exe" (
    echo [ERREUR] dist\OptimaMTKTool\OptimaMTKTool.exe introuvable.
    echo          Lancez d'abord build.bat pour compiler l'application.
    echo.
    pause
    exit /b 1
)
echo [OK] Application PyInstaller trouvee.

REM 2. Verifier le redist VC++
if not exist "redist\VC_redist.x64.exe" (
    echo [AVERT] redist\VC_redist.x64.exe absent.
    echo         Telechargez-le depuis :
    echo         https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    pause
    exit /b 1
)
echo [OK] Visual C++ Redistributable trouve.

REM 3. Verifier l'icone
if not exist "assets\icon.ico" (
    echo [AVERT] assets\icon.ico absent. L'icone par defaut sera utilisee.
)

REM ─── Localisation de ISCC.exe ────────────────────────────────────────────────
set "ISCC="

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto :found_iscc
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto :found_iscc
)
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    goto :found_iscc
)

REM Inno Setup non trouve
echo.
echo [ERREUR] Inno Setup n'est pas installe sur ce systeme.
echo.
echo  Pour installer Inno Setup 6 (gratuit) :
echo    - Telechargez : https://jrsoftware.org/isdl.php
echo    - Installez normalement, puis relancez ce script.
echo.
echo  Alternativement, compilez manuellement :
echo    - Ouvrez installer.iss avec Inno Setup IDE
echo    - Menu Build ^> Compile (Ctrl+F9)
echo.
pause
exit /b 1

:found_iscc
echo [OK] Inno Setup trouve : %ISCC%
echo.

REM ─── Creation du dossier de sortie ───────────────────────────────────────────
if not exist "output" mkdir output

REM ─── Compilation du script Inno Setup ────────────────────────────────────────
echo [INFO] Compilation de installer.iss en cours...
echo.

"%ISCC%" /Q "installer.iss"

if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation Inno Setup a echoue.
    echo          Verifiez les erreurs ci-dessus.
    echo.
    pause
    exit /b 1
)

echo.
echo ══════════════════════════════════════════════════════════
echo  [SUCCES] Installateur genere avec succes !
echo.
echo   Fichier : output\OptimaMTKTool_Setup_v1.0.0.exe
echo ══════════════════════════════════════════════════════════
echo.

REM Ouvrir le dossier output dans l'Explorateur
explorer "output"

pause
exit /b 0
