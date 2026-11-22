<#
.SYNOPSIS
    Installe les pilotes USB nécessaires à Optima Telecom Flash Tool.

.DESCRIPTION
    Script d'aide à l'installation, à exécuter en tant qu'administrateur.
    Il n'installe rien automatiquement : il vérifie les droits, indique où
    déposer les fichiers .inf, puis affiche les commandes pnputil à lancer
    manuellement.

.NOTES
    Aucun téléchargement n'est effectué par ce script.
    La désactivation de la signature de pilotes est affichée à titre
    informatif et n'est jamais exécutée.
#>

[CmdletBinding()]
param(
    [string]$DriverFolder = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\drivers'))
)

$ErrorActionPreference = 'Stop'

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Warn {
    param([string]$Message)
    Write-Warning $Message
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Warn "Ce script doit être exécuté en tant qu'administrateur."
    Write-Host "Relancez PowerShell en tant qu'administrateur, puis réexécutez :"
    Write-Host "  powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit 1
}

Write-Step "Droits administrateur : OK"

$DriverFolder = [System.IO.Path]::GetFullPath($DriverFolder)
if (-not (Test-Path -LiteralPath $DriverFolder)) {
    New-Item -ItemType Directory -Path $DriverFolder -Force | Out-Null
}

Write-Step "Déposez les fichiers .inf dans : $DriverFolder"
Write-Host "  - MediaTek : pilote WinUSB/VCOM (Zadig ou fournisseur du fabricant)"
Write-Host "  - Qualcomm : pilote QDLoader 9008"
Write-Host ""

$infFiles = @(Get-ChildItem -LiteralPath $DriverFolder -Filter *.inf -File -ErrorAction SilentlyContinue)
if ($infFiles.Count -eq 0) {
    Write-Warn "Aucun fichier .inf trouvé dans $DriverFolder."
    Write-Host "Déposez les .inf, puis relancez ce script."
    exit 1
}

foreach ($inf in $infFiles) {
    Write-Host "Pilote trouvé : $($inf.Name)"
}
Write-Host ""

Write-Warn "AVERTISSEMENT : désactiver la signature de pilotes abaisse la sécurité du poste."
Write-Warn "Cette option est affichée à titre informatif et N'EST PAS exécutée par ce script."
Write-Host "Si un pilote n'est pas signé, vous pouvez, à vos risques, redémarrer en mode"
Write-Host "sans vérification de signature :"
Write-Host "  Paramètres > Récupération > Démarrage avancé > Redémarrer > Dépannage"
Write-Host "  > Options avancées > Paramètres de démarrage > Désactiver le contrôle de signature"
Write-Host ""

Write-Step "Commandes à exécuter manuellement dans une console administrateur :"
foreach ($inf in $infFiles) {
    Write-Host "  pnputil /add-driver `"$($inf.FullName)`" /install"
}
Write-Host ""

Write-Host "Étapes suivantes :"
Write-Host "  1. Exécutez les commandes pnputil ci-dessus."
Write-Host "  2. Redémarrez le poste."
Write-Host "  3. Rebranchez l'appareil."
Write-Host "  4. Relancez Optima Telecom Flash Tool."
Write-Host ""
Write-Host "Ce script n'installe aucun pilote automatiquement."