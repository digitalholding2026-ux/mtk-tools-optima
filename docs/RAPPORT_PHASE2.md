# Rapport de fin de phase 2 — Optima Telecom Flash Tool

**Date** : 2026-11-22
**Périmètre** : prompts 2.1 à 2.7
**Environnement** : Windows 10/11, Python 3.11.9, venv `.venv`
**Méthode** : commandes exécutées dans `C:\Users\Docker\Desktop\flash`, sorties brutes collées sans résumé.

## 1. Tableau de conformité par prompt

| Prompt | Éléments demandés | Statut | Preuve |
|---|---|---|---|
| 2.1 | Arborescence `src/core`, `src/adapters/{usb,mtk,qualcomm}`, `src/ui`, `tests`, `scripts`, `docs` avec `__init__.py` vides | Fait | `Get-ChildItem` section 2 ; `src/core/__init__.py` 0 o, `src/ui/__init__.py` 0 o, `src/adapters/mtk/__init__.py` 0 o, `src/adapters/qualcomm/__init__.py` 0 o, `tests/__init__.py` 0 o. `src/adapters/usb/__init__.py` = 173 o (réexports du prompt 2.5). |
| 2.1 | `pyproject.toml` : `name = "optima-flash"`, `requires-python >= 3.11`, PySide6/pyusb/pyyaml, dev pytest/pytest-qt/ruff/mypy/pip-licenses | Fait | `pyproject.toml:6`, `:10`, `:14-16`, `:21-25` |
| 2.1 | `README.md` : prérequis, installation, avertissement légal, section Pilotes USB | Fait | `README.md:1-29` ; renvoi `docs/LEGAL.md` |
| 2.1 | `pip install -e ".[dev]"` réussit ; `pip-licenses --fail-on="GPL"` passe | Fait | Installation `optima-flash 0.1.0` ; `pip-licenses` exit 0 (section 3) |
| 2.2 | `src/core/types.py` : ChipsetType, ConnectionMode, OperationStatus, DeviceInfo, OperationError, OperationResult ; aucun import `usb` | Fait | `types.py:29-55` (enums), `:68-84` (DeviceInfo), `:110-137` (OperationError), `:140-152` (OperationResult), imports `:7-13` (stdlib uniquement) |
| 2.2 | `src/core/config.py` : `load_config`, `config.yaml`/`config.yaml.example`, clés `binaries`/`paths`/`ui`, création des dossiers, `ConfigError` | Fait | `config.py:121-149`, `:133-145`, `:113-118`, `:37` |
| 2.2 | `config.yaml.example` : toutes clés commentées, chemins relatifs, aucun secret | Fait | `config.yaml.example:1-22` |
| 2.2 | Contraintes : mypy strict, aucun réseau, aucune écriture hors dossiers configurés | Fait | `mypy` 0 erreur (section 3) ; imports `types.py:7-13` ; `config.py:113-118` (mkdir uniquement) |
| 2.2 | Tests : YAML valide et YAML malformé (`ConfigError`) | Fait | `tests/test_config.py:10`, `:41` ; `pytest` 30 passed |
| 2.3 | `src/core/logging.py` : `setup_logging`, `RotatingFileHandler` 5 Mo × 5, JSON `timestamp_utc`/`level`/`event`/`operator`/`payload` | Fait | `logging.py:33-35` (constantes), `:47-65` (JSON), `:68-92` (setup) ; `logs/optima.log:1` |
| 2.3 | `get_raw_log_path` : chemin dans `logs/raw/`, sans création | Fait | `logging.py:95-98` ; `tests/test_logging.py:63` |
| 2.3 | `src/core/license.py` : `check_license()` retourne `True`, docstring exacte, aucun `cryptography`/réseau | Fait | `license.py:12-18` ; `grep check_license src` ne renvoie que `license.py` ; aucun import |
| 2.3 | Tests : JSON valide/rotatif, raw sans création, licence `True` sans réseau | Fait | `tests/test_logging.py:23,45,63,74` ; `tests/test_license.py:8,12` ; `mypy` 0 |
| 2.3 | `logs/optima.log` contient du JSON structuré après test | Fait | `logs/optima.log:1-11` |
| 2.4 | `MediaTekAdapter(Protocol)` + `MediaTekAdapterStub`, message Prompt 3 | Fait | `mtk/adapter.py:18`, `:40`, `:44-55` |
| 2.4 | `QualcommAdapter(Protocol)` + `QualcommAdapterStub`, message Prompt 4 | Fait | `qualcomm/adapter.py:18`, `:40`, `:44-55` |
| 2.4 | Tests : chaque méthode lève `NotImplementedError` avec le bon message ; aucun import `usb`/`subprocess`/`mtkclient`/`edl` | Fait | `tests/test_adapters.py:41`, `:50` ; grep exit 1 (section 3) |
| 2.4 | mypy strict ; aucune logique métier, aucun subprocess, aucun appel USB | Fait | `mypy` 0 ; `mtk/adapter.py` et `qualcomm/adapter.py` = 1937 o chacun |
| 2.5 | `src/adapters/usb/detector.py` : `detect_devices()`, `usb.core.find(find_all=True)`, filtres MTK/QC, bus/address/serial, `USBError` → `OperationError` | Fait | `detector.py:17-20`, `:51-79`, `:82-101` ; `tests/test_detector.py:35-110` |
| 2.5 | `src/adapters/usb/__init__.py` réexporte `detect_devices` et `OperationError` | Fait | `usb/__init__.py:3-6` |
| 2.5 | Gestion du backend libusb absent (`usb.core.NoBackendError`) | **Absent** | `detector.py:86` ne capture que `usb.core.USBError` ; `NoBackendError` MRO = `ValueError` (section 3/4) ; traceback réel section 3 |
| 2.5 | Tests + contraintes grep | Fait | `tests/test_detector.py` (6 tests) ; grep exit 1 ; `mypy` 0 |
| 2.6 | `src/adapters/usb/drivers.py` : `check_drivers()` et `open_installer_script()` | Fait | `drivers.py:37-58`, `:61-68` |
| 2.6 | `scripts/install_drivers.ps1` : admin, dépôt `.inf`, `pnputil`, avertissement signature, message final | Fait | `install_drivers.ps1:18`, `:36-38`, `:49`, `:57`, `:69-70`, `:79`, `:83-88` |
| 2.6 | Tests : mock `subprocess.run` (présents/absents), `open_installer_script` + `Popen` mocké | Fait | `tests/test_drivers.py:13`, `:24`, `:34`, `:44` |
| 2.6 | mypy strict ; aucun téléchargement ; aucune exécution automatique du PS1 | Fait | `mypy` 0 ; `drivers.py:67` (`Popen` explorer uniquement) ; script non exécuté |
| 2.6 | Critère `pwsh -NoProfile -Command "Get-Command -Syntax"` | **Partiel** | `pwsh` absent (`Get-Command pwsh` vide) ; PowerShell 5.1 : `Get-Command -Syntax` exit 0 ; `Parser::ParseFile` → `SYNTAX OK` |
| 2.7 | `src/ui/main_window.py` : titre, 900×600, menus, table, scan QThread, barre de statut, Flash/FRP désactivés, entrée `python -m` | Fait | `main_window.py:74`, `:87`, `:89`, `:100`, `:103`, `:114-125`, `:132-144`, `:146-150`, `:174`, `:216`, `:292-301` |
| 2.7 | Tests pytest-qt : fenêtre, scan non bloquant, table remplie, boutons désactivés | Fait | `tests/test_main_window.py:10`, `:30` ; `pytest` 30 passed |
| 2.7 | mypy strict `src/ui`, aucun réseau, aucun accès USB direct | Fait | `mypy` 0 ; `grep "import usb\|from usb" src/ui` → aucun |
| 2.7 | Application se lance ; ruff et mypy propres | Fait | Popen `alive_after_3s: True` (section 3) ; ruff clean ; mypy 0 |

Note : la ligne 2.5 « backend absent » n'est pas un livrable explicite du prompt 2.5 ; elle est ajoutée parce qu'elle conditionne le critère fonctionnel F1 du SPEC. Elle est reprise en section 4.

## 2. Arborescence réelle du dépôt

`tree /F src tests scripts` a échoué avec `Too many parameters - tests` (le binaire `tree` de ce Windows n'accepte qu'un seul chemin). Utilisation de `Get-ChildItem -Recurse -Force` comme autorisé par le prompt. Sortie brute :

```text
src\adapters | <DIR>
src\core | <DIR>
src\ui | <DIR>
src\__pycache__ | <DIR>
src\__init__.py | 0
src\adapters\mtk | <DIR>
src\adapters\qualcomm | <DIR>
src\adapters\usb | <DIR>
src\adapters\__pycache__ | <DIR>
src\adapters\__init__.py | 0
src\adapters\mtk\__pycache__ | <DIR>
src\adapters\mtk\adapter.py | 1937
src\adapters\mtk\__init__.py | 0
src\adapters\mtk\__pycache__\adapter.cpython-311.pyc | 3246
src\adapters\mtk\__pycache__\__init__.cpython-311.pyc | 167
src\adapters\qualcomm\__pycache__ | <DIR>
src\adapters\qualcomm\adapter.py | 1937
src\adapters\qualcomm\__init__.py | 0
src\adapters\qualcomm\__pycache__\adapter.cpython-311.pyc | 3251
src\adapters\qualcomm\__pycache__\__init__.cpython-311.pyc | 172
src\adapters\usb\__pycache__ | <DIR>
src\adapters\usb\detector.py | 2708
src\adapters\usb\drivers.py | 2119
src\adapters\usb\__init__.py | 173
src\adapters\usb\__pycache__\detector.cpython-311.pyc | 4494
src\adapters\usb\__pycache__\drivers.cpython-311.pyc | 3134
src\adapters\usb\__pycache__\__init__.cpython-311.pyc | 397
src\adapters\__pycache__\__init__.cpython-311.pyc | 163
src\core\__pycache__ | <DIR>
src\core\config.py | 4586
src\core\license.py | 406
src\core\logging.py | 2880
src\core\types.py | 6421
src\core\__init__.py | 0
src\core\__pycache__\config.cpython-311.pyc | 7968
src\core\__pycache__\license.cpython-311.pyc | 719
src\core\__pycache__\logging.cpython-311.pyc | 5021
src\core\__pycache__\types.cpython-311.pyc | 10063
src\core\__pycache__\__init__.cpython-311.pyc | 159
src\ui\__pycache__ | <DIR>
src\ui\main_window.py | 10350
src\ui\__init__.py | 0
src\ui\__pycache__\main_window.cpython-311.pyc | 19794
src\ui\__pycache__\__init__.cpython-311.pyc | 157
src\__pycache__\__init__.cpython-311.pyc | 154
tests\__pycache__ | <DIR>
tests\conftest.py | 100
tests\test_adapters.py | 1556
tests\test_config.py | 2080
tests\test_detector.py | 3018
tests\test_drivers.py | 1485
tests\test_license.py | 573
tests\test_logging.py | 2573
tests\test_main_window.py | 2113
tests\test_types.py | 2573
tests\__init__.py | 0
tests\__pycache__\conftest.cpython-311-pytest-9.2.0.pyc | 500
tests\__pycache__\test_adapters.cpython-311-pytest-9.2.0.pyc | 6949
tests\__pycache__\test_config.cpython-311-pytest-9.2.0.pyc | 14640
tests\__pycache__\test_detector.cpython-311-pytest-9.2.0.pyc | 11911
tests\__pycache__\test_drivers.cpython-311-pytest-9.2.0.pyc | 6554
tests\__pycache__\test_license.cpython-311-pytest-9.2.0.pyc | 3389
tests\__pycache__\test_logging.cpython-311-pytest-9.2.0.pyc | 12362
tests\__pycache__\test_main_window.cpython-311-pytest-9.2.0.pyc | 20931
tests\__pycache__\test_types.cpython-311-pytest-9.2.0.pyc | 25773
tests\__pycache__\__init__.cpython-311.pyc | 156
scripts\.gitkeep | 0
scripts\install_drivers.ps1 | 3233
```

Les fichiers `__pycache__/*.pyc` sont des artefacts Python présents sur disque ; ils sont ignorés par git (`.gitignore:2`).

## 3. Résultats des contrôles automatiques

### 3.1 `pytest -q`

Commande : `.\.venv\Scripts\python.exe -m pytest -q`

```text
..............................                                           [100%]
```

La version 9.2.0 de pytest n'a pas imprimé la ligne de résumé dans cette capture. Commande complémentaire `.\.venv\Scripts\python.exe -m pytest` :

```text
..............................                                           [100%]
30 passed in 0.47s
EXIT=0
```

### 3.2 `ruff check src/`

Commande : `.\.venv\Scripts\python.exe -m ruff check src/`

```text
All checks passed!
EXIT=0
```

### 3.3 `mypy --strict src/core src/adapters src/ui`

Commande : `.\.venv\Scripts\python.exe -m mypy --strict src/core src/adapters src/ui`

```text
Success: no issues found in 15 source files
EXIT=0
```

### 3.4 `pip-licenses --fail-on="GPL"`

Commande : `.\.venv\Scripts\pip-licenses.exe --fail-on="GPL"`

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

Observation factuelle : PySide6 et shiboken6 sont sous tri-licence `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`. La commande sort en 0. Le choix LGPL n'est pas écrit explicitement dans `docs/` à ce jour (voir écart n°8).

### 3.5 `grep -R "mtkclient\|edl\|subprocess" src/adapters/mtk src/adapters/qualcomm`

Commande : `& "C:\Program Files\Git\usr\bin\grep.exe" -R "mtkclient\|edl\|subprocess" src/adapters/mtk src/adapters/qualcomm`

```text
EXIT=1
```

Aucune sortie : aucun occurrence dans les deux adaptateurs.

### 3.6 `grep -R "ctrl_transfer\|\.write\|\.read" src/adapters/usb`

Commande : `& "C:\Program Files\Git\usr\bin\grep.exe" -R "ctrl_transfer\|\.write\|\.read" src/adapters/usb`

```text
EXIT=1
```

Aucune sortie : aucun appel `ctrl_transfer`, `.write` ou `.read` dans `src/adapters/usb`.

### 3.7 Vérification réelle du backend USB

Commande : `.\.venv\Scripts\python.exe -c "from src.adapters.usb.detector import detect_devices; print('detect_devices() =', detect_devices())"`

```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "C:\Users\Docker\Desktop\flash\src\adapters\usb\detector.py", line 85, in detect_devices
    candidates = usb.core.find(find_all=True)
                 ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Docker\Desktop\flash\.venv\Lib\site-packages\usb\core.py", line 1321, in find
    raise NoBackendError('No backend available')
usb.core.NoBackendError: No backend available
```

Commande : `.\.venv\Scripts\python.exe -c "import usb.core; print(usb.core.NoBackendError.__mro__); print(issubclass(usb.core.NoBackendError, usb.core.USBError))"`

```text
NoBackendError MRO: (<class 'usb.core.NoBackendError'>, <class 'ValueError'>, <class 'Exception'>, <class 'BaseException'>, <class 'object'>)
is USBError subclass: False
```

### 3.8 `check_drivers()` réel

Commande : `.\.venv\Scripts\python.exe -c "from src.adapters.usb.drivers import check_drivers; print('check_drivers() =', check_drivers())"`

```text
check_drivers() = {'mtk_vcom': False, 'qualcomm_9008': False}
```

### 3.9 `python -m src.ui.main_window` (smoke test offscreen)

Commande : lancement du module avec `QT_QPA_PLATFORM=offscreen`, attente 3 s, puis terminaison.

```text
alive_after_3s: True
returncode: 1
stdout: ''
stderr: ''
```

Le `returncode: 1` provient de la terminaison explicite du processus après 3 s, pas d'un crash au démarrage.

### 3.10 Script PowerShell — analyse syntaxique

`pwsh` n'est pas installé : `Get-Command pwsh` ne retourne rien.

Commande de remplacement avec Windows PowerShell 5.1 :

```text
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Command -Syntax .\scripts\install_drivers.ps1"
install_drivers.ps1 [[-DriverFolder] <string>] [<CommonParameters>]
exit=0
```

Commande `Parser::ParseFile` :

```text
SYNTAX OK
exit=0
```

## 4. Écarts et manques identifiés

1. **Backend libusb absent — `NoBackendError` non géré**
   - **Où** : `src/adapters/usb/detector.py:82-87` et `:93-99`.
   - **Quoi** : `detect_devices()` ne capture que `usb.core.USBError`. Or `usb.core.NoBackendError` n'est pas une sous-classe de `USBError` (MRO : `NoBackendError -> ValueError -> Exception`). Sur ce poste, l'appel lève `NoBackendError` (traceback section 3.7) au lieu de retourner `[]` ou de lever `OperationError(code="USB_ENUM_FAILED")`.
   - **Impact** : **bloquant** pour la recette fonctionnelle du scan sur un poste sans backend libusb ; **non bloquant** pour le développement de la phase 3 (les tests utilisent des mocks). Le critère « liste vide si aucun appareil » n'est pas vérifiable en réel dans cet environnement.
   - **Suggestion** : capturer explicitement `usb.core.NoBackendError` et retourner `[]` (ou lever `OperationError(code="USB_ENUM_FAILED")`), avec un message dédié dans l'UI.

2. **Chaîne d'installation USB incomplète — le backend libusb n'est pas fourni**
   - **Où** : `scripts/install_drivers.ps1:49-79` ; `README.md:27-28`.
   - **Quoi** : le script installe les pilotes `.inf` via `pnputil` mais ne déploie pas `libusb-1.0.dll`, qui est un prérequis de `pyusb` documenté dans le README. Sans ce fichier, le scan échoue avec `NoBackendError` (écart n°1).
   - **Impact** : **bloquant** pour la recette sur poste neuf ; **non bloquant** pour la phase 3.
   - **Suggestion** : ajouter la distribution/installation de `libusb-1.0.dll` au script ou prévoir un contrôle explicite au démarrage avec un message d'action.

3. **`OperationError` est une dataclass ET une exception**
   - **Où** : `src/core/types.py:110-111`.
   - **Quoi** : le prompt 2.2 demandait `@dataclass(frozen=True)` pour `OperationError`. Il l'est, mais il hérite aussi de `Exception` (ajout non prévu) pour permettre le `raise` exigé par le prompt 2.5.
   - **Impact** : non bloquant.
   - **Suggestion** : documenter cette évolution dans le contrat de types, ou séparer la valeur `OperationError` de l'exception `OperationFailure`.

4. **Critère `pwsh` du prompt 2.6 non exécuté tel quel**
   - **Où** : prompt 2.6 ; `scripts/install_drivers.ps1`.
   - **Quoi** : `pwsh` n'est pas installé sur ce poste. La syntaxe a été validée avec Windows PowerShell 5.1 : `Get-Command -Syntax` (exit 0) et `Parser::ParseFile` (`SYNTAX OK`).
   - **Impact** : non bloquant (le script est compatible 5.1).
   - **Suggestion** : refaire le contrôle avec `pwsh` sur un poste disposant de PowerShell 7.

5. **`README.md` obsolète sur le script d'installation**
   - **Où** : `README.md:28` et `:36`.
   - **Quoi** : le texte indique « fourni au prompt 2.6 » et « scripts d'installation (à venir) », alors que `scripts/install_drivers.ps1` existe (3233 octets).
   - **Impact** : non bloquant.
   - **Suggestion** : retirer les mentions « à venir » et décrire le script.

6. **`check_license()` n'est appelé par aucun module**
   - **Où** : `src/core/license.py:12` ; `src/ui/main_window.py:148`.
   - **Quoi** : `grep check_license src` ne renvoie que `license.py:9,12`. L'UI affiche « Licence : MVP (non vérifiée) » codé en dur.
   - **Impact** : non bloquant (le placeholder est conforme au prompt 2.3 ; l'UI n'était pas tenue de l'appeler).
   - **Suggestion** : brancher `check_license()` dans la barre de statut, ou documenter que l'état est un placeholder d'UI.

7. **Signaux UI déclarés `object` au lieu de `list[DeviceInfo]` / `OperationError`**
   - **Où** : `src/ui/main_window.py:42-43` et `:61-62`.
   - **Quoi** : `ScanWorker.finished = Signal(object)` et `error = Signal(object)` ; `DriverCheckWorker.finished = Signal(object)`. Le prompt 2.7 demandait `finished(list[DeviceInfo])` et `error(OperationError)`. Le contenu émis est bien une `list[DeviceInfo]` / un `OperationError`, mais le type déclaré est `object`.
   - **Impact** : non bloquant.
   - **Suggestion** : documenter le choix PySide6 ou utiliser `Signal(list)` si la conversion est acceptable.

8. **Tri-licence PySide6 incluant GPL non documentée**
   - **Où** : `pip-licenses` section 3.4 ; `pyproject.toml:14`.
   - **Quoi** : PySide6 et shiboken6 sont sous `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`. La commande `--fail-on="GPL"` sort en 0. Le choix LGPL n'est pas écrit explicitement dans `docs/`.
   - **Impact** : non bloquant (LGPL retenu), mais à valider juridiquement.
   - **Suggestion** : mentionner l'élection LGPL dans `docs/ARCHITECTURE.md` ou `docs/LEGAL.md`.

9. **`pytest -q` n'imprime pas la ligne de résumé dans ce terminal**
   - **Où** : section 3.1.
   - **Quoi** : `pytest -q` ne montre que les points et `[100%]` ; `pytest` sans `-q` affiche `30 passed in 0.47s`.
   - **Impact** : non bloquant (outillage/terminal).
   - **Suggestion** : utiliser `pytest` sans `-q` pour les rapports.

10. **`__pycache__` et `.pyc` présents dans l'arborescence**
    - **Où** : section 2.
    - **Quoi** : les artefacts Python sont sur disque ; ils sont ignorés par git (`.gitignore:2`) mais rendent le listing brut plus long.
    - **Impact** : non bloquant.
    - **Suggestion** : nettoyer avant livraison.

11. **Aucun test matériel**
    - **Où** : `tests/test_detector.py`, `tests/test_main_window.py`.
    - **Quoi** : les tests USB et UI utilisent des mocks ; aucun appareil MediaTek ou Qualcomm n'a été branché.
    - **Impact** : non bloquant pour la phase 3, mais la recette matérielle reste à faire.
    - **Suggestion** : prévoir une campagne de recette sur banc avec appareils réels.

## 5. Vérifications fonctionnelles manuelles

| Vérification | Fait / Non fait | Observation |
|---|---|---|
| `python -m src.ui.main_window` → fenêtre s'affiche | **Fait** (offscreen) | Processus maintenu 3 s (`alive_after_3s: True`), stdout/stderr vides ; smoke test antérieur : `Optima Telecom Flash Tool`, 900 × 600, `Flash/FRP = False/False`, statut `Prêt · Licence : MVP (non vérifiée) · Pilotes : non vérifié`. Pas de vérification visuelle dans une session graphique. |
| Clic « Scanner les appareils » sans appareil → pas de blocage, table vide | **Non fait** (test réel non concluant) | Le test automatisé `test_scan_populates_table_without_blocking` passe (30 passed) avec un mock. En réel, `detect_devices()` lève `NoBackendError` sur ce poste (section 3.7) : le clic afficherait une erreur, pas une table vide. Aucun appareil n'était branché. |
| Clic « Scanner » avec MediaTek preloader | **Non fait** | Aucun appareil MediaTek disponible. |
| Clic « Scanner » avec Qualcomm 9008 | **Non fait** | Aucun appareil Qualcomm disponible. |
| Menu « Vérifier les pilotes USB » → statut affiché, script ouvrable | **Non fait** (interaction modale non automatisée) | `check_drivers()` réel retourne `{'mtk_vcom': False, 'qualcomm_9008': False}` (section 3.8). `open_installer_script()` est testé avec `Popen` mocké (`tests/test_drivers.py:44`). Le clic sur le bouton du `QMessageBox` n'a pas été exécuté. |
| Boutons Flash et FRP désactivés avec tooltip | **Fait** | `main_window.py:118-125` ; `tests/test_main_window.py:10-27` ; smoke test `False False`. |

## 6. Verdict de fin de phase

**SOCLE NON PRÊT — voir écarts bloquants.**

## 7. Recommandations pour le prompt 3 (module MediaTek)

- Figer le contrat CLI de `mtkclient` (version épinglée par empreinte, flags, format de sortie) avant d'écrire `MediaTekAdapter`, conformément à `docs/ARCHITECTURE.md` §2.
- Traiter `usb.core.NoBackendError` dans `src/adapters/usb/detector.py` et ajouter un test, car c'est le chemin d'entrée du module MediaTek.
- Décider du mode d'échange avec `mtkclient` (stdout JSON ou fichiers) et documenter le mapping `DeviceInfo` ↔ sortie CLI, ainsi que la conversion en `OperationResult`/`OperationError`.
- Prévoir la gestion des partitions MediaTek (table GPT/PMT, sauvegarde/restauration) et le passage par les statuts `OperationStatus` dans `flash_partition`, sans écrire dans `src/core/`.
- Mettre à jour le README (retirer « à venir ») et documenter l'élection LGPL de PySide6 avant de figer la chaîne de release.