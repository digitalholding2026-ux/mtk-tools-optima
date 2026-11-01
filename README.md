# Optima MTK Tool Pro

**Optima MTK Tool Pro** est une application Desktop Windows modulaire pour atelier GSM, dédiée au diagnostic, flashage et déblocage FRP/Bootloader sur processeurs **MediaTek (MTK)**.

Son architecture s'inspire directement des standards d'outils d'atelier professionnels (UnlockTool, SP Flash Tool, Chimera Tool, MTKClient), garantissant un fonctionnement **100% autonome et portable** sans installation préalable du SDK Android ou de bibliothèques système externes.

---

## 🏗️ Architecture Modulaire d'Atelier

```text
Optima MTK Tool/
│
├── bin/                          # Binaires bas-niveau et dépendances dynamiques embarquées
│   ├── adb.exe                   # Android Debug Bridge
│   ├── fastboot.exe              # Fastboot Protocol CLI
│   ├── AdbWinApi.dll             # Dépendance USB Windows ADB
│   ├── AdbWinUsbApi.dll          # Dépendance WinUSB ADB
│   ├── libusb-1.0.dll            # DLL LibUSB 1.0 (Copie racine)
│   ├── x64/                      # Bibliothèque native 64-bit AMD64
│   │   └── libusb-1.0.dll
│   ├── x86/                      # Bibliothèque native 32-bit x86 (fallback)
│   │   └── libusb-1.0.dll
│   ├── setup_platform_tools.ps1  # Script de téléchargement automatique Google Platform-Tools
│   └── README.md
│
├── core/                         # Cœur applicatif, protocoles et communications bas-niveau
│   ├── init_env.py               # ⭐ Bootstrap d'environnement (DLLs, PATH, PyUSB Backend)
│   ├── brom/                     # Sous-module protocole MediaTek BootROM
│   │   ├── __init__.py
│   │   └── handshake.py          # Séquence de handshake matériel BROM (0xA0, 0x0A, 0x50, 0x05)
│   ├── detector.py               # Moteur de détection JIT multi-modes (BROM, Fastboot, ADB)
│   ├── usb_scanner.py            # Scanner matériel PyUSB / LibUSB brut (< 3 secondes)
│   ├── usb_reset.py              # Réinitialisation USB et réveil matériel
│   ├── com_detector.py           # Détection ports COM / VCOM (SetupAPI / PySerial)
│   ├── mtk_communication.py      # Communication série / handshake BROM
│   ├── actions.py                # Commandes FRP, Format, Flash, Read Info
│   ├── device_models.py          # Base de données chipsets MTK / DA
│   └── __init__.py
│
├── drivers/                      # Pilotes d'atelier et installateurs automatiques
│   ├── install_drivers.bat       # Lanceur avec élévation automatique Administrateur (UAC)
│   ├── install_drivers.ps1       # Script PowerShell d'intégration silencieuse via PnPUtil
│   ├── vcom/                     # Pilotes MediaTek Port COM Virtuel (Preloader / DA / BROM)
│   │   └── cdc-acm.inf
│   ├── libusb_filter/            # Filtre WinUSB / LibUSB pour BootROM direct sans port COM
│   │   └── mtk_brom_filter.inf
│   ├── adb_fastboot/             # Pilotes Android officiels (ADB / Fastboot)
│   │   └── android_winusb.inf
│   └── README.md
│
├── data/                         # Fichiers de données et payloads atelier
│   ├── da/                       # Download Agents officiels (MTK_AllInOne_DA.bin)
│   │   └── README.md
│   └── auth/                     # Fichiers d'authentification SLA/DAA (auth_sv5.auth)
│       └── README.md
│
├── gui/                          # Interface graphique PyQt5 (Style Atelier Sombre / TFT)
│   ├── main_window.py            # Fenêtre principale et barre de statut
│   ├── dashboard.py              # Tableau de bord principal
│   ├── frp_tab.py                # Onglet Déblocage FRP
│   ├── flash_tab.py              # Onglet Flash Partition / Scatter
│   ├── device_info_tab.py        # Fiche technique matérielle détaillée
│   ├── tools_tab.py              # Outils système et actions directes
│   ├── connection_assistant.py   # Assistant visuel de branchement MTK
│   ├── device_status_widget.py   # Widget d'état temps réel
│   ├── tft_widgets.py            # Composants graphiques spécialisés atelier
│   └── log_panel.py              # Console de log avec coloration syntaxique
│
├── assets/                       # Icônes et logos de l'application
├── audit_usb.py                  # Script de diagnostic autonome (console)
├── install.bat                   # Installation des dépendances Python
├── install_dependencies.ps1      # Script PowerShell d'installation
├── main.py                       # Point d'entrée de l'application
└── requirements.txt              # Dépendances Python (PyQt5, pyserial, pyusb, libusb-package)
```

---

## 🔌 Encapsulation LibUSB & PyUSB

Optima MTK Tool embarque nativement `libusb-1.0.dll` dans son dossier `bin/` :
1. **Résolution dynamique sans PATH système** : Le module `core/init_env.py` associe le backend PyUSB directement à la DLL embarquée via `usb.backend.libusb1.get_backend(find_library=...)`.
2. **Support Windows 10/11 & Python 3.8+** : Enregistrement automatique des répertoires DLL avec `os.add_dll_directory()`.
3. **Architecture Multi-Bitness** : Détection automatique de la version de l'interpréteur Python (64-bit AMD64 ou 32-bit x86) et sélection de la DLL correspondante.
4. **Détection éphémère (<3s)** : Permet de capturer les BootROMs MediaTek ultra-courts (Infinix, Tecno, Xiaomi) directement au niveau USB, avant même que Windows n'attribue un port COM virtuel.

---

## 🚀 Installation & Démarrage

### 1. Installation des Pilotes (Obligatoire pour l'Atelier)
Faites un clic-droit sur `drivers/install_drivers.bat` puis **"Exécuter en tant qu'administrateur"**. Le script intègre silencieusement les pilotes VCOM, LibUSB et Android WinUSB via `PnPUtil`.

### 2. Installation des Dépendances Python
Double-cliquez sur `install.bat` ou lancez en PowerShell :
```powershell
pip install -r requirements.txt
```

### 3. Lancement de l'Application
```powershell
python main.py
```

### 4. Audit Matériel Sans Interface Graphique (Diagnostic rapide)
```powershell
python audit_usb.py
```
