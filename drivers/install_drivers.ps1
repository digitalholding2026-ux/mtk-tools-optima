# -*- coding: utf-8 -*-
# =============================================================================
# Optima MTK Tool - Script d'Installation Automatisée des Pilotes
# Utilise PnPUtil (Windows Driver Store) pour enregistrer et installer
# l'ensemble des packages INF sans interaction manuelle.
# =============================================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "       INSTALLATION AUTOMATIQUE DES PILOTES MEDIATEK & ANDROID        " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Vérification Administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERREUR] Ce script doit être exécuté avec les privilèges Administrateur !" -ForegroundColor Red
    Write-Host "Veuillez lancer install_drivers.bat par clic-droit -> 'Exécuter en tant qu'administrateur'." -ForegroundColor Yellow
    exit 1
}

$driversDir = $PSScriptRoot
Write-Host "[*] Répertoire des pilotes : $driversDir" -ForegroundColor Gray

# Recherche récursive de tous les fichiers .inf
$infFiles = Get-ChildItem -Path $driversDir -Filter "*.inf" -Recurse

if ($infFiles.Count -eq 0) {
    Write-Host "[AVERTISSEMENT] Aucun package .inf trouvé dans $driversDir !" -ForegroundColor Yellow
    Write-Host "Déposez vos pilotes .inf dans les dossiers mtk/, libusb/ et adb_fastboot/." -ForegroundColor Yellow
    exit 0
}

Write-Host "[+] $($infFiles.Count) package(s) de pilotes détecté(s) :" -ForegroundColor Green
foreach ($inf in $infFiles) {
    Write-Host "  - $($inf.Name) [Dossier: $($inf.Directory.Name)]" -ForegroundColor White
}
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($inf in $infFiles) {
    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "[+] Installation de : $($inf.Name)..." -ForegroundColor Yellow
    
    # Tentative via pnputil (méthode moderne Windows 10/11)
    $pnpResult = pnputil.exe /add-driver "$($inf.FullName)" /install 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 3010) {
        Write-Host "    [OK] Pilote intégré avec succès dans le Driver Store." -ForegroundColor Green
        $successCount++
    } else {
        # Secours via SetupAPI DefaultInstall
        Write-Host "    [!] PnPUtil a renvoyé le code $LASTEXITCODE. Tentative via SetupAPI..." -ForegroundColor Gray
        try {
            $setupProcess = Start-Process -FilePath "rundll32.exe" -ArgumentList "setupapi,InstallHinfSection DefaultInstall 132 `"$($inf.FullName)`"" -Wait -PassThru
            if ($setupProcess.ExitCode -eq 0) {
                Write-Host "    [OK] Pilote installé via SetupAPI." -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "    [ERREUR] Échec de l'installation pour $($inf.Name)." -ForegroundColor Red
                $failCount++
            }
        } catch {
            Write-Host "    [ERREUR] Exception : $_" -ForegroundColor Red
            $failCount++
        }
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " RÉSULTAT : $successCount package(s) installé(s), $failCount échec(s)." -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Conseil atelier : Redémarrez le PC si certains périphériques MTK" -ForegroundColor Gray
Write-Host "nécessitent une réinitialisation du bus USB ou du filtre WinUSB." -ForegroundColor Gray
Write-Host ""
