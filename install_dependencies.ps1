# -*- coding: utf-8 -*-
# Script d'installation automatique pour Optima MTK Tool
# Exécuter ce script en tant qu'Administrateur (clic droit -> "Exécuter avec PowerShell")

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Installation - Optima MTK Tool" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# --- 1. Vérifier si Python est installé ---
Write-Host "[1/3] Vérification de Python..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$python3Cmd = Get-Command python3 -ErrorAction SilentlyContinue

if ($pythonCmd -or $python3Cmd) {
    $pyPath = if ($pythonCmd) { $pythonCmd.Source } else { $python3Cmd.Source }
    Write-Host "Python d�tect� : $pyPath" -ForegroundColor Green
    python --version
} else {
    Write-Host "Python n'est pas install�." -ForegroundColor Red

    # Tenter l'installation via winget
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Tentative d'installation de Python via winget..." -ForegroundColor Yellow
        winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Python install� avec succ�s via winget." -ForegroundColor Green
        } else {
            Write-Host "Échec de l'installation via winget." -ForegroundColor Red
            Write-Host "Veuillez installer Python manuellement depuis https://www.python.org/downloads/" -ForegroundColor Red
            Write-Host "IMPORTANT : cochez 'Add Python to PATH' pendant l'installation !" -ForegroundColor Yellow
            Read-Host "Appuyez sur Entr�e pour quitter"
            exit 1
        }
    } else {
        Write-Host "winget n'est pas disponible." -ForegroundColor Red
        Write-Host "Veuillez installer Python manuellement depuis https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "Puis relancer ce script." -ForegroundColor Yellow
        Read-Host "Appuyez sur Entr�e pour quitter"
        exit 1
    }
}

# Rafraîchir l'environnement PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# --- 2. Mettre à jour pip ---
Write-Host ""
Write-Host "[2/3] Mise à jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# --- 3. Installer les dépendances ---
Write-Host ""
Write-Host "[3/3] Installation des d�pendances (PyQt5, pyserial)..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Green
    Write-Host "  Installation termin�e avec succ�s !" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pour lancer l'application :" -ForegroundColor Cyan
    Write-Host "  python main.py" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Appuyez sur Entr�e pour quitter"
} else {
    Write-Host ""
    Write-Host "ERREUR lors de l'installation des d�pendances." -ForegroundColor Red
    Read-Host "Appuyez sur Entr�e pour quitter"
    exit 1
}
