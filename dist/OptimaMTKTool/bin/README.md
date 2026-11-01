# Optima MTK Tool Pro — Binaires Embarqués (`bin/`)

Ce dossier contient l'ensemble des exécutables bas-niveau et bibliothèques dynamiques requis pour opérer de manière 100% autonome sur n'importe quel ordinateur Windows d'atelier, sans nécessiter l'installation du SDK Android ou d'autres packages système.

---

## 📁 Architecture des Fichiers

```text
bin/
├── adb.exe                   # Android Debug Bridge v35+
├── fastboot.exe              # Fastboot Protocol CLI
├── AdbWinApi.dll             # Dépendance Windows USB pour ADB
├── AdbWinUsbApi.dll          # Dépendance WinUSB pour ADB
├── libusb-1.0.dll            # Bibliothèque LibUSB 1.0 (Copie par défaut)
│
├── x64/                      # Binaires natifs Windows 64-bit (AMD64)
│   └── libusb-1.0.dll        # DLL vérifiée pour Python 64-bit
│
├── x86/                      # Binaires natifs Windows 32-bit (x86)
│   └── libusb-1.0.dll        # DLL pour environnements Python 32-bit (optionnel)
│
└── setup_platform_tools.ps1  # Script PowerShell de mise à jour des outils Google
```

---

## ⚡ Résolution et Priorité

Dans Optima MTK Tool, la résolution des dépendances s'effectue dans l'ordre strict :
1. `bin/` ou `bin/<architecture>/` (Priorité maximale - Exécutable et DLL locaux)
2. `tools/` (Dossier historique - Rétrocompatibilité assurée)
3. Variables d'environnement système `PATH`
4. Android SDK (`%LOCALAPPDATA%\Android\Sdk\platform-tools`)

---

## 🔄 Mise à Jour Automatique

Pour mettre à jour ou réinstaller les derniers binaires officiels Google :
```powershell
powershell -ExecutionPolicy Bypass -File bin\setup_platform_tools.ps1
```
