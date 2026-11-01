# Optima MTK Tool

Application Desktop Windows de flash et déblocage FRP pour processeurs MediaTek.

## Arborescence du projet

```
Optima MTK Tool/
├── main.py                     # Point d'entrée de l'application
├── requirements.txt            # Dépendances Python
├── README.md                   # Ce fichier
│
├── gui/                        # Interface graphique
│   ├── __init__.py
│   ├── main_window.py          # Fenêtre principale (onglets, menu, barre de statut)
│   ├── dashboard.py            # Onglet Accueil (état, actions rapides)
│   ├── frp_tab.py              # Onglet FRP Reset
│   ├── flash_tab.py            # Onglet Flash Tool
│   ├── device_info_tab.py      # Onglet Informations Appareil
│   └── log_panel.py            # Panneau de logs en temps réel
│
├── core/                       # Logique métier
│   ├── __init__.py
│   ├── com_detector.py         # Détection ports COM / USB
│   └── mtk_communication.py    # Communication MTK (BROM, préloader, FRP, flash)
│
└── assets/                     # Ressources visuelles
    ├── .gitkeep                # Placez ici logo_optima.ico, icon.ico, icons/
    └── (logo, icônes à ajouter)
```

## Installation

1. Installer Python 3.x depuis https://python.org (cochez "Add Python to PATH").
2. Ouvrir un terminal dans le dossier du projet.
3. Installer les dépendances :

```powershell
pip install -r requirements.txt
```

## Lancement

```powershell
python main.py
```

## Fonctionnalités incluses (v1.0.0)

- Interface moderne en mode sombre (PyQt5, palette Optima Telecom - bleu accent)
- Onglets : Accueil, FRP Reset, Flash Tool, Informations Appareil
- Panneau de logs en temps réel avec horodatage et coloration
- Bouton de détection des ports COM / USB
- Détection automatique des appareils MediaTek (BROM / préloader)
- Barre de menu (Fichier, Outils, Aide)

## À implémenter (étapes suivantes)

- Remplacer les simulations dans `core/mtk_communication.py` par de vrais appels aux binaires MTK (flash_tool, mtkclient, etc.) ou py-serial.
- Ajouter le logo Optima Telecom dans `assets/`.
- Ajouter la gestion des fichiers scatter et les partitions de flash réelles.
