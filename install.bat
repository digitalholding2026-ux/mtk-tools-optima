@echo off
chcp 65001 >nul
title Installation - Optima MTK Tool

echo ==============================================
echo   Installation - Optima MTK Tool
echo ==============================================
echo.

:: 1. Verifier Python
echo [1/3] Verification de Python...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Python detecte :
    python --version
) else (
    echo Python n'est pas installe.
    echo Tentative d'installation via winget...
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo Echec de l'installation automatique.
        echo Veuillez installer Python manuellement depuis https://www.python.org/downloads/
        echo IMPORTANT : cochez "Add Python to PATH" pendant l'installation !
        pause
        exit /b 1
    )
    echo Python installe avec succes.
)

:: 2. Mettre a jour pip
echo.
echo [2/3] Mise a jour de pip...
python -m pip install --upgrade pip

:: 3. Installer les dependances
echo.
echo [3/3] Installation des dependances (PyQt5, pyserial)...
python -m pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ==============================================
    echo   Installation terminee avec succes !
    echo ==============================================
    echo.
    echo Pour lancer l'application :
    echo   python main.py
    echo.
    pause
) else (
    echo.
    echo ERREUR lors de l'installation des dependances.
    pause
    exit /b 1
)
