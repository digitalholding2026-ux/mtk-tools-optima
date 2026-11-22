# Optima Flash — Optima Telecom Flash Tool

Socle applicatif du projet : cœur typé, configuration, journalisation, détection USB passive, diagnostic des pilotes et interface PySide6. Aucune opération d'écriture sur un appareil n'est implémentée à ce stade.

> **Avertissement légal** — Le FRP ne doit être effacé que pour le propriétaire légitime de l'appareil, sur présentation d'une preuve écrite. Voir [docs/LEGAL.md](docs/LEGAL.md).

## Prérequis

- Windows 10/11 64 bits.
- Python 3.11 ou plus récent.
- Droits administrateur pour exécuter `scripts/install_drivers.ps1`.

## Installation

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Pilotes USB

`scripts/install_drivers.ps1` est un **guide d'installation**, pas un installeur automatique.

**Ce qu'il fait**
- Vérifie que PowerShell est exécuté en tant qu'administrateur (sinon il s'arrête).
- Crée le dossier `drivers/` s'il manque.
- Recherche `libusb-1.0.dll` dans `drivers/` et dans `%SystemRoot%\System32\`.
- Si le DLL est dans `drivers/`, propose de le copier à côté de `python.exe` du venv (confirmation `Read-Host`).
- Si le DLL est absent, affiche l'URL officielle `https://libusb.info/` et la procédure à suivre.
- Liste les fichiers `.inf` présents dans `drivers/` et affiche les commandes `pnputil /add-driver "<inf>" /install` à exécuter manuellement.
- Affiche un avertissement sur la désactivation de la signature de pilotes, sans jamais l'exécuter.
- Termine par les étapes : redémarrer, rebrancher l'appareil, relancer Optima.

**Ce qu'il ne fait pas**
- Il ne télécharge rien.
- Il n'installe aucun pilote automatiquement.
- Il ne désactive pas la signature de pilotes.
- Il ne redémarre pas le poste.

**Backend libusb**
1. Télécharger l'archive officielle sur <https://libusb.info/> (releases → libusb 1.0.x, archive Windows).
2. Extraire `libusb-1.0.dll` **64 bits** (dossier `x64` ou `MS64`).
3. Copier `libusb-1.0.dll` dans `drivers/`.
4. Relancer `scripts/install_drivers.ps1` ; confirmer la copie à côté de `python.exe` du venv.
5. Vérifier la barre de statut d'Optima : `Backend USB : OK`.

Sans ce DLL, `check_backend()` renvoie `False`, le bandeau « Backend libusb manquant » s'affiche et le bouton « Scanner les appareils » est désactivé.

## Arborescence

```text
flash/
├── docs/                  # documents de cadrage et rapports
├── scripts/               # install_drivers.ps1
├── src/
│   ├── core/              # types, configuration, journalisation, licence
│   ├── adapters/
│   │   ├── usb/           # détection passive et diagnostic pilotes
│   │   ├── mtk/           # contrat d'adaptateur MediaTek
│   │   └── qualcomm/      # contrat d'adaptateur Qualcomm
│   └── ui/                # interface PySide6
├── tests/                 # tests unitaires
├── pyproject.toml
└── README.md
```

## Vérifications

```powershell
python -m pip install -e ".[dev]"
pytest
ruff check src tests
mypy --strict src/core src/adapters src/ui
pip-licenses --fail-on="GPL"
```

## Licence

Le produit est propriétaire (`license = { text = "Proprietary" }`). PySide6 et shiboken6 sont utilisés sous LGPL-3.0-only (voir `docs/ARCHITECTURE.md`, ADR-002).