# Rapport de correction 2.8 — 2.9

**Date** : 2026-11-22
**Périmètre** : corrections 2.8 (backend libusb, bannière UI) et 2.9 (hygiène : `OperationError`/`OperationFailure`, README, ADR-002, `.gitignore`, licence).
**Méthode** : commandes exécutées dans `C:\Users\Docker\Desktop\flash`, sorties brutes collées.

## 1. Tableau de conformité

| Élément | Statut | Preuve |
|---|---|---|
| `OperationError` est une `@dataclass(frozen=True)` sans hériter de `Exception` | Fait | `src/core/types.py:112` ; `grep -R "class OperationError.*Exception" src` → exit 1, aucune sortie |
| `OperationFailure(Exception)` porte un `OperationError` | Fait | `src/core/types.py:137` ; `tests/test_types.py:test_operation_failure_wraps_error` |
| `detector.py` lève `OperationFailure(OperationError(...))` | Fait | `src/adapters/usb/detector.py:75, 77, 118, 120, 132, 134` ; `tests/test_detector.py` (7 tests) |
| `main_window.py` capture `OperationFailure` | Fait | `src/ui/main_window.py:50, 54, 227` |
| README sans « à venir » ni « prompt 2.6 », script décrit, procédure libusb | Fait | `README.md:22-50` ; `Select-String "à venir\|prompt 2.6"` → aucun |
| ADR-002 — élection LGPL pour PySide6 et shiboken6 | Fait | `docs/ARCHITECTURE.md:60` |
| `license = { text = "Proprietary" }` | Fait | `pyproject.toml:11` |
| `.gitignore` contient `__pycache__/`, `*.pyc`, `.venv/`, `logs/`, `optima.db`, `optima.db-*`, `config.yaml` ; pas de `drivers/` | Fait | `Get-Content .gitignore` (section 2.8) |
| `pytest` | Fait | 35 passed (section 2.1) |
| `ruff check src tests` | Fait | All checks passed (section 2.2) |
| `mypy --strict src/core src/adapters src/ui` | Fait | 15 fichiers, 0 erreur (section 2.3) |
| `pip-licenses --fail-on="GPL"` | Fait | exit 0 (section 2.4) |
| `grep -R "class OperationError.*Exception" src` | Fait | exit 1, aucune sortie (section 2.5) |
| `ast_serialize` et `librt` | Fait | Dépendances transitives de `mypy` (MIT), `Required-by: mypy` (sections 2.6 et 2.7) |
| `check_backend()` réel | Fait | `False` (section 2.9) |
| `detect_devices()` réel avec `libusb-1.0.dll` | Fait | `[]` (section 2.10) |
| Syntaxe PowerShell 5.1 du script | Fait | `install_drivers.ps1 [[-DriverFolder] <string>] [<CommonParameters>]`, exit 0 (section 2.11) |

## 2. Sorties brutes

### 2.1 `pytest -q`

```text
...................................                                      [100%]
EXIT=0
```

Commande complémentaire `pytest` : `35 passed in 0.34s`.

### 2.2 `ruff check src tests`

```text
All checks passed!
EXIT=0
```

### 2.3 `mypy --strict src/core src/adapters src/ui`

```text
Success: no issues found in 15 source files
EXIT=0
```

### 2.4 `pip-licenses --fail-on="GPL"`

```text
 Name                Version     License                                       
 PySide6             6.12.0      LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only 
 PySide6_Addons      6.12.0      LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only 
 PySide6_Essentials  6.12.0      LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only 
 PySide6_Pdf         6.12.0.140  LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only 
 PySide6_WebEngine   6.12.0.140  LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only 
 PyYAML              6.0.4       MIT License                                   
 Pygments            2.21.0      BSD-2-Clause                                  
 ast_serialize       0.13.1      MIT                                           
 colorama            0.4.6       BSD License                                   
 iniconfig           2.3.1       MIT                                           
 librt               0.17.0      MIT                                           
 mypy                2.4.1       MIT                                           
 mypy_extensions     1.2.0       MIT                                           
 optima-flash        0.1.0       Proprietary                                   
 packaging           26.3        Apache-2.0 OR BSD-2-Clause                    
 pathspec            1.1.1       Mozilla Public License 2.0 (MPL 2.0)          
 pluggy              1.7.0       MIT License                                   
 pytest              9.2.0       MIT                                           
 pytest-qt           4.5.0       MIT License                                   
 pyusb               1.3.1       BSD License                                   
 ruff                0.17.6      MIT                                           
 shiboken6           6.12.0      LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only 
 typing_extensions   4.16.0      PSF-2.0                                       
EXIT=0
```

### 2.5 `grep -R "class OperationError.*Exception" src`

```text
EXIT=1
```

Aucune sortie : aucun `OperationError` n'hérite de `Exception`.

### 2.6 `pip show ast_serialize librt`

```text
Name: ast_serialize
Version: 0.13.1
Summary: Python bindings for mypy AST serialization
Home-page: https://github.com/mypyc/ast_serialize
Author: 
Author-email: Jukka Lehtosalo <jukka.lehtosalo@iki.fi>
License-Expression: MIT
Location: C:\Users\Docker\Desktop\flash\.venv\Lib\site-packages
Requires: 
Required-by: mypy
---
Name: librt
Version: 0.17.0
Summary: Mypyc runtime library
Home-page: https://github.com/mypyc/librt
Author: 
Author-email: Jukka Lehtosalo <jukka.lehtosalo@iki.fi>, Ivan Levkivskyi <levkivskyi@gmail.com>
License-Expression: MIT
Location: C:\Users\Docker\Desktop\flash\.venv\Lib\site-packages
Requires: mypy_extensions
Required-by: mypy
```

Conclusion : dépendances transitives légitimes de `mypy` (MIT), sans GPL. Aucune investigation supplémentaire nécessaire.

### 2.7 `pip show -f <paquet> | Select-String "Required-by"`

```text
--- ast_serialize ---

Required-by: mypy
--- librt ---

Required-by: mypy
```

### 2.8 `Get-Content .gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyc
*.egg-info/
.eggs/
build/
dist/

# Environnements
.venv/
venv/
env/

# Données locales
logs/
*.raw
optima.db
optima.db-*
*.db
config.yaml

# Outils
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
```

### 2.9 `check_backend()` et `check_drivers()` réels

```text
check_backend = False
check_drivers = {'mtk_vcom': False, 'qualcomm_9008': False, 'libusb_backend': False}
```

### 2.10 `detect_devices()` réel avec `libusb-1.0.dll`

DLL x64 extraite temporairement de l'historique git (commit `12a505c`, `bin/libusb-1.0.dll`), copiée dans `.venv\Scripts\`, puis supprimée.

```text
check_backend = True
detect_devices = []
--- RETRAIT ---
check_backend apres retrait = False
```

Aucun appareil n'était branché ; `detect_devices()` retourne bien `[]` sans crash.

### 2.11 Syntaxe du script PowerShell

```text
install_drivers.ps1 [[-DriverFolder] <string>] [<CommonParameters>]
EXIT=0
```

## 3. Écarts résiduels

1. **Matériel réel non testé** : aucun appareil MediaTek ou Qualcomm n'était branché ; le parcours complet « appareil en preloader / EDL 9008 » n'a pas été exécuté. Impact : non bloquant pour la phase 3, mais la recette matérielle reste à faire.
2. **Script PowerShell non exécuté** : conformément à la contrainte, `scripts/install_drivers.ps1` n'a pas été lancé ; seule sa syntaxe a été analysée. Impact : non bloquant.
3. **`pwsh` absent** : la syntaxe a été validée avec Windows PowerShell 5.1 (`Get-Command -Syntax`, `Parser::ParseFile`). Impact : non bloquant.
4. **Tri-licence PySide6** : `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` ; le projet élit LGPL-3.0-only (ADR-002). `pip-licenses --fail-on="GPL"` sort en 0. Impact : non bloquant, choix documenté.
5. **`drivers/` non ignoré** : volontaire, pour permettre au technicien de versionner ses DLL locales. Impact : aucun.
6. **Modifications 2.8 non commitées** : `scripts/install_drivers.ps1`, `src/adapters/usb/drivers.py`, `tests/test_drivers.py` et `tests/test_main_window.py` apparaissent dans `git status` ; ils portent le travail 2.8 et n'ont pas été touchés pendant la 2.9. Impact : aucun (gestion de version).

## 4. Verdict

**SOCLE PRÊT POUR PHASE 3**