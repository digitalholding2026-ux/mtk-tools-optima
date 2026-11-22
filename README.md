# Optima Flash — socle du dépôt

Socle du projet Optima Telecom Flash Tool. Cette étape ne contient **aucun code
métier** : uniquement l'arborescence, la configuration du projet et la
documentation.

> **Avertissement légal** — Le FRP ne doit être effacé que pour le propriétaire
> légitime de l'appareil, sur présentation d'une preuve écrite. Voir
> [docs/LEGAL.md](docs/LEGAL.md).

## Prérequis

- Windows 10/11 64 bits.
- Python 3.11 ou plus récent.

## Installation

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Pilotes USB

Les pilotes USB (MediaTek preloader, Qualcomm EDL 9008, backend libusb) seront
installés par `scripts/install_drivers.ps1`, fourni au prompt 2.6. Aucun pilote
n'est installé à cette étape.

## Arborescence

```text
flash/
├── docs/                  # documents de cadrage (contrat)
├── scripts/               # scripts d'installation (à venir)
├── src/
│   ├── core/              # types, configuration, journalisation (à venir)
│   ├── adapters/
│   │   ├── usb/           # détection passive (à venir)
│   │   ├── mtk/           # interface MediaTek (à venir)
│   │   └── qualcomm/      # interface Qualcomm (à venir)
│   └── ui/                # interface PySide6 (à venir)
├── tests/                 # tests unitaires (à venir)
├── pyproject.toml
└── README.md
```

## Vérifications

```powershell
python -m pip install -e ".[dev]"
pip-licenses --fail-on="GPL"
```