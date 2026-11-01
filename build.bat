@echo off
chcp 65001 >nul
title Optima MTK Tool - Compilation Exécutable PyInstaller
echo ======================================================================
echo       OPTIMA MTK TOOL - COMPILATION DU PACKAGE EXECUTABLE WINDOWS
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Verification de Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas detecte dans le PATH systeme.
    pause
    exit /b 1
)

:: 2. Verification / Installation de PyInstaller
echo [*] Verification de PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [+] PyInstaller non detecte. Installation automatique...
    python -m pip install pyinstaller
)

:: 3. Nettoyage des builds precedents
echo [*] Nettoyage des dossiers build/ et dist/...
if exist "build" rmdir /s /q "build"
if exist "dist\OptimaMTKTool" rmdir /s /q "dist\OptimaMTKTool"
if exist "OptimaMTKTool.spec" del /f /q "OptimaMTKTool.spec"

:: 4. Compilation PyInstaller (onedir, windowed, uac-admin)
echo.
echo ======================================================================
echo [+] Lancement du processus de compilation PyInstaller...
echo ======================================================================

pyinstaller --noconfirm --onedir --windowed --uac-admin --name "OptimaMTKTool" --icon="assets/icon.ico" --add-data "drivers;drivers" --add-data "bin;bin" --add-data "assets;assets" --add-data "data;data" --hidden-import "usb.core" --hidden-import "usb.util" --hidden-import "usb.backend.libusb1" --hidden-import "serial.tools.list_ports" --hidden-import "serial.tools.list_ports_windows" main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Echec de la compilation PyInstaller.
    pause
    exit /b 1
)

:: 5. Organisation de la structure modulaire atelier (TFT Unlock style)
echo.
echo [*] Mise en place de la structure modulaire dans dist\OptimaMTKTool\...
set "DIST_DIR=dist\OptimaMTKTool"

if not exist "%DIST_DIR%\drivers" xcopy /e /i /y "drivers" "%DIST_DIR%\drivers" >nul
if not exist "%DIST_DIR%\bin" xcopy /e /i /y "bin" "%DIST_DIR%\bin" >nul
if not exist "%DIST_DIR%\data" xcopy /e /i /y "data" "%DIST_DIR%\data" >nul
if exist "bin\libusb-1.0.dll" copy /y "bin\libusb-1.0.dll" "%DIST_DIR%\" >nul

:: 6. Controle d'integrite final
echo.
echo [*] Controle d'integrite :
if exist "%DIST_DIR%\OptimaMTKTool.exe" (
    echo   [OK] Executable principal : %DIST_DIR%\OptimaMTKTool.exe
)
if exist "%DIST_DIR%\libusb-1.0.dll" (
    echo   [OK] DLL LibUSB racine   : %DIST_DIR%\libusb-1.0.dll
)
if exist "%DIST_DIR%\bin\adb.exe" (
    echo   [OK] ADB embarque         : %DIST_DIR%\bin\adb.exe
)
if exist "%DIST_DIR%\bin\fastboot.exe" (
    echo   [OK] Fastboot embarque    : %DIST_DIR%\bin\fastboot.exe
)
if exist "%DIST_DIR%\drivers\install_drivers.bat" (
    echo   [OK] Installateur pilotes : %DIST_DIR%\drivers\install_drivers.bat
)

echo.
echo ======================================================================
echo       COMPILATION TERMINEE AVEC SUCCES !
echo ======================================================================
echo.
echo Le dossier autonome pret a l'emploi est disponible :
echo   %~dp0dist\OptimaMTKTool\
echo.
echo Vous pouvez distribuer l'integralite de ce dossier sur n'importe quel PC.
echo.
pause
