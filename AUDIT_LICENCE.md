# Rapport d'audit — Optima MTK Tool

**Date :** 2026-11-07  
**Auteur :** Kilo (Senior Python / PyQt5 / Audit Architecture)  
**Scope :** 32 fichiers Python analysés (`main.py`, `core/*`, `gui/*`)  
**Objectif :** Identifier la cause racine du plantage (crash silencieux ou fermeture brutale) survenant lors de la validation d'une clé de licence.

---

## 1. Résumé exécutif

L'application présente une architecture correctement structurée mais comporte plusieurs **anomalies critiques** susceptibles de provoquer des plantages lors de la validation de licence et des interactions ADB. Aucun crash systématique n'est inévitable, mais les conditions de race (race conditions), les chemins relatifs non protégés et les exceptions non captées dans les threads secondaires constituent des vecteurs de défaillance réels.

Les commits `b883e8e` et `7f7822c` traitent déjà la protection anti-crash du bouton "Activer la licence", l'écriture dans `error.log`, le masquage des tokens dans l'UI et la lecture externe des tokens. Les correctifs C.1 à C.5 ci-dessous restent à appliquer pour éliminer définitivement les risques résiduels.

---

## 2. Intégrité de l'architecture et gestion des chemins (paths)

### 2.1 Conforme

| Fichier | Constat |
|---------|---------|
| `core/init_env.py` | Résolution bivalente robuste (`sys.executable` / `sys._MEIPASS` / `__file__`), chemins absolus pour `bin/`, `drivers/`, `data/`, `libusb-1.0.dll`. |
| `core/license_manager.py` | Chemins absolus via `get_base_dir()` pour `license.json`, `tokens.json`, `error.log`. Compatible script + PyInstaller. |
| `main.py` | `ROOT_DIR` résolu selon `frozen` / `__file__`. Icône et `sys.path` corrects. |
| `core/detector.py:230-261` | `get_adb_path()` utilise `sys.executable` et `_MEIPASS` en mode frozen, `__file__` en mode script. |

### 2.2 Anomalie A.1 — Chemin relatif fragile

**Fichier :** `gui/main_window.py` lignes 12-15

```python
_gui_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_gui_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
```

**Problème :** Résolution via `__file__` uniquement, sans prise en compte de `sys.executable` / `sys._MEIPASS`. En mode PyInstaller `--onedir` ou `--onefile`, `__file__` pointe vers l'extractoir temporaire `_MEIPASS`, ce qui peut rendre `ROOT_DIR` incorrect pour l'accès aux ressources externes modifiables (`bin/`, `drivers/`).

**Correctif :** Aligner sur `core/init_env.py:get_app_dir()` / `get_project_root()`.

---

## 3. Traçabilité et gestion des exceptions (anti-crash)

### 3.1 Conforme

| Fichier | Constat |
|---------|---------|
| `core/license_manager.py:142-170` | `activate_token()` enveloppé dans `try/except Exception`, journalisation `error.log`, retour `(ok, message)` sans lever d'exception. |
| `gui/license_dialog.py:215-259` | `_on_activate_clicked()` avec `try/except` global, `QMessageBox.critical()`, écriture `traceback.format_exc()` dans `error.log`. |
| `gui/license_widget.py:103-121` | `_refresh()` protégé par `try/except` (affichage dégradé au lieu de crash). |
| `gui/main_window.py:200-207, 222-232` | `_check_license_startup()` et `_is_action_allowed()` protégés par `try/except`. |
| `core/usb_reset.py` | Toutes les étapes encapsulées individuellement, aucune exception ne remonte. |

### 3.2 Anomalie A.2 — Thread QThread sans protection globale (CRITIQUE)

**Fichier :** `core/detector.py` (boucle de scan, lignes ~280-500)

**Problème :** `DeviceDetector` hérite de `QThread` et tourne en boucle toutes les 1,5s. Si une exception non capturée survient dans `run()` ou dans un slot connecté, le thread plante silencieusement sans alerter l'utilisateur ni écrire dans `error.log`.

**Correctif :** Envelopper le corps de `QThread.run()` dans un `try/except Exception` global qui émet un signal d'erreur vers l'UI et écrit dans `error.log` via `log_error_to_file()`.

```python
def run(self):
    try:
        # ... boucle de détection existante ...
    except Exception as e:
        log_error_to_file(f"Crash thread DeviceDetector : {e}", e)
        self.log_message.emit(f"Erreur détection : {e}", "error")
```

### 3.3 Anomalie A.3 — `reset_adb_server()` sans gestion robuste de FileNotFoundError

**Fichier :** `core/detector.py` lignes 268+

**Problème :** Si `adb.exe` est absent (fichier manquant dans `bin/`), `subprocess.run()` lève `FileNotFoundError`. L'appel en chaîne depuis `main.py:kill_switch_startup_cleanup()` et `detector.reset_adb_server()` peut propager l'exception.

**Correctif :** Capturer `FileNotFoundError` spécifiquement et journaliser, sans bloquer le démarrage.

### 3.4 Anomalie A.4 — `_execute_reboot_direct()` sans protection (moyen)

**Fichier :** `gui/main_window.py` lignes 543-570

**Problème :** Appel direct à `__import__('subprocess').run()` sans `try/except` autour de la création du processus (ligne 549). Si `adb` est introuvable, `FileNotFoundError` remonte.

**Correctif :**

```python
def _execute_reboot_direct(self, target: str):
    try:
        # ... code existant ...
    except Exception as e:
        self._append_log(f"Échec reboot {target} : {e}", "error")
        QMessageBox.critical(self, "Erreur d'exécution", f"{type(e).__name__}: {e}")
        log_error_to_file(f"Reboot {target} échoué : {e}", e)
```

### 3.5 Anomalie A.7 — Exception de licence ignorée silencieusement au démarrage

**Fichier :** `main.py` lignes 156-157

```python
except Exception as exc:
    logger.warning(f"[LICENCE] Vérification de licence ignorée : {exc}")
```

**Problème :** En cas d'erreur lors de l'import ou de l'instanciation de `LicenseDialog`, l'exception est logguée en `warning` sans `QMessageBox` ni `error.log`. L'utilisateur n'est pas alerté et l'application continue sans licence.

**Correctif :**

```python
except Exception as exc:
    log_error_to_file(f"Échec critique vérification licence au démarrage : {exc}", exc)
    QMessageBox.critical(
        None, "Erreur critique de licence",
        f"Impossible de vérifier la licence :\n{type(exc).__name__}: {exc}\n\n"
        f"Détails dans error.log."
    )
    logger.warning(f"[LICENCE] Vérification de licence ignorée : {exc}")
```

---

## 4. Cohérence des flux de données et de l'UI

### 4.1 Conforme

- `license.json` : lecture/écriture via `LicenseManager` avec chemins absolus.
- `tokens.json` : lecture dynamique à chaque activation (plus de hardcode, commit `7f7822c`).
- `LicenseWidget` : `QTimer` 1s rafraîchissant l'affichage, protégé par `try/except`.
- Tokens masqués de l'UI (suppression de l'affichage "Tokens valides : ...").

### 4.2 Anomalie A.5 — Double vérification de licence au démarrage

**Fichiers :** `main.py:139-157` et `gui/main_window.py:102-105`

**Problème :** `main.py` vérifie la licence et affiche `LicenseDialog` bloquant (`exec_()`). Puis `main_window.py` ré-instancie `LicenseManager` et appelle `_check_license_startup()` à l'ouverture de la fenêtre principale.

**Risque :** Si `tokens.json` disparaît entre les deux appels (race condition), la fenêtre principale peut se retrouver en état bloqué sans dialog de récupération.

**Correctif :** Centraliser la vérification de licence. `main.py` lance la dialog uniquement si aucune licence n'est trouvée ; `main_window.py` ne re-vérifie pas au démarrage (ou s'appuie sur l'état partagé).

### 4.3 Anomalie A.6 — Conflit UI / Timer pendant l'activation

**Fichier :** `gui/main_window.py:209-213`

**Problème :** `LicenseDialog` est ouverte modale tandis que le `QTimer` du `LicenseWidget` continue de tourner (refresh toutes les secondes), ce qui peut créer un conflit d'état pendant la saisie du token.

**Correctif :**

```python
def _on_license_activate_requested(self):
    from gui.license_dialog import LicenseDialog
    self.license_widget._timer.stop()
    try:
        dlg = LicenseDialog(self)
        if dlg.exec_() == dlg.Accepted:
            self._on_license_activated()
    finally:
        self.license_widget._timer.start()
```

---

## 5. Matrice de synthèse des anomalies

| # | Fichier | Ligne | Gravité | Type | Description | Correctif |
|---|---------|-------|---------|------|-------------|-----------|
| A.1 | `gui/main_window.py` | 12-15 | Moyen | Chemin relatif | Résolution ROOT_DIR via `__file__` uniquement, incompatible PyInstaller | Utiliser `init_env.get_app_dir()` |
| A.2 | `core/detector.py` | ~280-500 | Critique | Thread non protégé | QThread sans try/except global → crash silencieux | try/except + signal erreur + error.log |
| A.3 | `core/detector.py` | 268+ | Moyen | FileNotFoundError | `reset_adb_server()` peut lever si adb absent | Capturer FileNotFoundError |
| A.4 | `gui/main_window.py` | 549 | Moyen | Subprocess non protégé | `subprocess.run` direct sans try/except | try/except + QMessageBox + error.log |
| A.5 | `main.py` / `main_window.py` | 139 / 102 | Moyen | Double vérification | Licence vérifiée 2 fois au démarrage, risque d'incohérence | Centraliser la vérification |
| A.6 | `gui/main_window.py` | 209-213 | Moyen | Conflit UI/Timer | QTimer actif pendant dialog modale | Arrêter/démarrer le timer |
| A.7 | `main.py` | 156-157 | Moyen | Exception ignorée | Erreur licence logguée en warning uniquement, pas d'alerte UI | QMessageBox.critical + error.log |

---

## 6. Recommandations stratégiques

1. **Supprimer `tokens.json` du dépôt avant distribution finale** (déjà créé en local, doit être exclu via `.gitignore` ou `git rm --cached`).
2. **Ajouter `.gitignore`** incluant `__pycache__/`, `*.pyc`, `license.json`, `tokens.json`, `error.log`, `build/`, `dist/`.
3. **Centraliser le logging** : créer un logger unique `OptimaMTK` utilisé par tous les modules, avec un handler fichier pointant vers `error.log` (actuellement dispersé entre `logging` et `log_error_to_file`).
4. **Tester en mode PyInstaller frozen** : vérifier que `tokens.json`, `license.json` et `error.log` s'écrivent bien à côté de l'exécutable (`sys.executable`), pas dans `_MEIPASS` (lecture seule).

---

## 7. État des correctifs déjà appliqués

- `b883e8e` — `fix(license): harden activation with absolute paths, error.log traceback, and crash-safe dialog`
- `7f7822c` — `refactor(license): hide tokens in UI and load activation tokens from external file`

Ces deux commits couvrent les exigences initiales : bloc try/except sur "Activer la licence", QMessageBox.critical, journalisation `error.log`, chemins absolus, suppression de l'affichage des tokens et lecture externe via `tokens.json`.

---

*Fin du rapport.*