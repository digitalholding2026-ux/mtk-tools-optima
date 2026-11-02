# Optima MTK Tool Pro — Dossier Pilotes d'Atelier (`drivers/`)

Ce dossier regroupe tous les pilotes nécessaires pour la détection et la communication avec les appareils Android et processeurs MediaTek (MTK) en atelier GSM.

---

## 📁 Structure des Pilotes

```text
drivers/
├── install_drivers.bat      # Lanceur rapide avec élévation Administrateur automatique (UAC)
├── install_drivers.ps1      # Script PowerShell d'intégration silencieuse via PnPUtil
│
├── vcom/                    # Pilotes MediaTek Port COM Virtuel
│   └── cdc-acm.inf          # USB\VID_0E8D&PID_2000 (Preloader), PID_2001 (DA), PID_0003 (BROM)
│
├── libusb_filter/           # Filtre WinUSB / LibUSB pour détection ultra-rapide (<3s)
│   └── mtk_brom_filter.inf  # Accès direct PyUSB / LibUSB au BootROM matériel sans port COM
│
└── adb_fastboot/            # Pilotes Android officiels
    └── android_winusb.inf   # Débogage USB ADB (PID_2005) & Mode Fastboot (PID_0C03)
```

---

## 🚀 Installation en Un Clic

1. Faites un clic-droit sur `install_drivers.bat`.
2. Sélectionnez **"Exécuter en tant qu'administrateur"**.
3. Le script appelle `pnputil.exe` pour intégrer silencieusement l'ensemble des `.inf` dans le magasin de pilotes Windows (*Windows Driver Store*).

---

## 🛠️ Dépannage Atelier

- **Code 10 / Code 28 dans le Gestionnaire de périphériques** :
  Relancez `install_drivers.bat` puis débranchez/rebranchez le câble USB en maintenant `Volume Bas` ou `Volume Haut + Bas`.
- **Fenêtre BROM éphémère (Infinix / Tecno / Xiaomi)** :
  Grâce au filtre LibUSB (`libusb_filter/`), Optima MTK Tool intercepte le périphérique au niveau du bus matériel en quelques millisecondes avant même que Windows n'attribue un port COM.
- **Remplacement forcé avec Zadig (optionnel)** :
  Si Windows force un pilote incompatible, ouvrez Zadig, cochez *Options > List All Devices*, sélectionnez `MediaTek USB Port (VID 0E8D PID 0003)` et installez le pilote **WinUSB** ou **libusb-win32**.
