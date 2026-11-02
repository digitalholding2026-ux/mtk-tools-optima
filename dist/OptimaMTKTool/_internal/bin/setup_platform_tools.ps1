# -*- coding: utf-8 -*-
# =============================================================================
# Optima MTK Tool - Téléchargement Automatique de Platform-Tools (ADB & Fastboot)
# Télécharge les binaires officiels Google et les installe dans le dossier bin/
# =============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$binDir = $PSScriptRoot
$zipUrl = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
$tempZip = Join-Path $env:TEMP "platform-tools-optima.zip"
$tempExtract = Join-Path $env:TEMP "platform-tools-optima"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "    OPTIMA MTK TOOL - INTÉGRATION AUTONOME DE ADB & FASTBOOT          " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1/3] Téléchargement des outils Google Platform-Tools..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip -UseBasicParsing

Write-Host "[2/3] Extraction des binaires vers $tempExtract..." -ForegroundColor Yellow
if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

$sourceTools = Join-Path $tempExtract "platform-tools"
$targetFiles = @("adb.exe", "fastboot.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll")

Write-Host "[3/3] Copie des fichiers requis dans le dossier bin/..." -ForegroundColor Yellow
foreach ($file in $targetFiles) {
    $src = Join-Path $sourceTools $file
    $dst = Join-Path $binDir $file
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dst -Force
        Write-Host "  [OK] $file installé avec succès dans bin/" -ForegroundColor Green
    } else {
        Write-Host "  [AVERTISSEMENT] $file non trouvé dans l'archive" -ForegroundColor DarkYellow
    }
}

# Nettoyage des fichiers temporaires
Remove-Item -Force $tempZip -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $tempExtract -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " Intégration des binaires terminée avec succès !" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
