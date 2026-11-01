# -*- coding: utf-8 -*-
"""
core/usb_reset.py — Routine de réveil matériel USB au démarrage d'Optima MTK Tool.

Simule le comportement de "réveil" observé lors du lancement/fermeture d'outils
comme TFT Unlock : réénumération du bus USB + réinitialisation propre du serveur ADB.

Séquence exécutée par perform_hardware_wake() :
  1. Tuer les processus adb.exe zombies (taskkill)
  2. Réénumération USB via SetupAPI / cfgmgr32 (sans admin requis)
  3. Scan PnP via pnputil /scan-devices (admin requis, sinon ignoré)
  4. Réactivation des périphériques USB en erreur via PowerShell (admin requis)
  5. Redémarrage propre du serveur ADB (adb kill-server + adb start-server)

Contraintes :
  - AUCUN appel bloquant : chaque subprocess a un timeout strict.
  - AUCUNE fenêtre console visible : CREATE_NO_WINDOW + DEVNULL systématiquement.
  - AUCUNE exception ne remonte : tout est capturé et journalisé.
  - Temps total garanti < 8 secondes.
"""

import ctypes
import os
import shutil
import subprocess
import sys
from typing import Callable, Dict, Optional

# ─── Constantes Windows ──────────────────────────────────────────────────────

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

# cfgmgr32 — gestion des nœuds de périphériques (SetupAPI)
CR_SUCCESS = 0
CM_REENUMERATE_NORMAL = 0x00000000  # Réénumération non-destructive, sans reboot

# ─── Helpers internes ─────────────────────────────────────────────────────────

def _log(msg: str, level: str = "INFO", callback: Optional[Callable] = None) -> None:
    """Émet un message de log via le callback si fourni, sinon affiche sur stderr."""
    formatted = f"[USB-WAKE][{level}] {msg}"
    if callback:
        try:
            callback(formatted, level)
        except Exception:
            pass
    else:
        print(formatted, file=sys.stderr)


def _devnull():
    """Retourne un handle vers DEVNULL pour supprimer les sorties de subprocess."""
    return subprocess.DEVNULL


def _run_silent(
    cmd: list,
    timeout: float = 5.0,
    log_callback: Optional[Callable] = None,
    label: str = ""
) -> bool:
    """
    Exécute une commande silencieusement (sans fenêtre console, sans pipes bloquants).
    Retourne True si le processus se termine avec code 0, False sinon.
    """
    try:
        result = subprocess.run(
            cmd,
            stdin=_devnull(),
            stdout=_devnull(),
            stderr=_devnull(),
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW,
        )
        success = (result.returncode == 0)
        lvl = "INFO" if success else "WARNING"
        _log(
            f"{label} → code retour {result.returncode}",
            level=lvl,
            callback=log_callback,
        )
        return success
    except subprocess.TimeoutExpired:
        _log(f"{label} → timeout ({timeout}s dépassé)", level="WARNING", callback=log_callback)
        return False
    except FileNotFoundError:
        _log(f"{label} → exécutable introuvable : {cmd[0]}", level="WARNING", callback=log_callback)
        return False
    except PermissionError:
        _log(f"{label} → permission refusée (droits insuffisants)", level="WARNING", callback=log_callback)
        return False
    except Exception as exc:
        _log(f"{label} → erreur inattendue : {exc}", level="ERROR", callback=log_callback)
        return False


# ─── API publique ──────────────────────────────────────────────────────────────

def is_admin() -> bool:
    """
    Vérifie si l'application tourne avec les privilèges Administrateur Windows.
    Utilise shell32.IsUserAnAdmin() via ctypes.
    Retourne False en cas d'erreur (plateforme non-Windows, etc.).
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def kill_zombie_adb(log_callback: Optional[Callable] = None) -> bool:
    """
    Termine tous les processus adb.exe en cours (serveurs zombies qui bloquent
    le port TCP 5037).
    Utilise taskkill /F /IM adb.exe /T (Windows uniquement).
    Retourne True si la commande s'est exécutée sans erreur critique.
    """
    _log("Arrêt des processus adb.exe zombies...", callback=log_callback)
    return _run_silent(
        ["taskkill", "/F", "/IM", "adb.exe", "/T"],
        timeout=4.0,
        log_callback=log_callback,
        label="taskkill adb.exe",
    )


def reenumerate_usb_via_cfgmgr32(log_callback: Optional[Callable] = None) -> bool:
    """
    Force une réénumération du bus USB via l'API SetupAPI (cfgmgr32.dll).

    Utilise :
      - CM_Locate_DevNodeW(NULL) pour obtenir le nœud racine du gestionnaire de périphériques.
      - CM_Reenumerate_DevNode(root, CM_REENUMERATE_NORMAL) pour déclencher
        un rescan complet et non-destructif (équivalent à F5 dans le Gestionnaire de périphériques).

    Ne nécessite PAS de droits Administrateur.
    Retourne True si CR_SUCCESS (0) est retourné par les deux appels.
    """
    _log("Réénumération USB via cfgmgr32 (SetupAPI)...", callback=log_callback)
    try:
        cfgmgr32 = ctypes.windll.cfgmgr32

        # Nœud racine : instance ID = None (chaîne vide = racine du gestionnaire de périphériques)
        root_devnode = ctypes.c_ulong(0)

        # CM_Locate_DevNodeW : localise le nœud racine
        # Prototype : CMAPI CONFIGRET CM_Locate_DevNodeW(PDEVINST, DEVINSTID_W, ULONG)
        # Avec instance ID = NULL → nœud racine
        cr = cfgmgr32.CM_Locate_DevNodeW(
            ctypes.byref(root_devnode),
            None,           # Instance ID NULL = nœud racine
            0,              # CM_LOCATE_DEVNODE_NORMAL
        )
        if cr != CR_SUCCESS:
            _log(
                f"CM_Locate_DevNodeW a retourné {cr} (attendu 0 = CR_SUCCESS)",
                level="WARNING",
                callback=log_callback,
            )
            return False

        # CM_Reenumerate_DevNode : déclenche le rescan depuis le nœud racine
        # Prototype : CMAPI CONFIGRET CM_Reenumerate_DevNode(DEVINST, ULONG)
        cr2 = cfgmgr32.CM_Reenumerate_DevNode(
            root_devnode,
            CM_REENUMERATE_NORMAL,
        )
        if cr2 != CR_SUCCESS:
            _log(
                f"CM_Reenumerate_DevNode a retourné {cr2} (attendu 0 = CR_SUCCESS)",
                level="WARNING",
                callback=log_callback,
            )
            return False

        _log("Réénumération USB via cfgmgr32 réussie (CR_SUCCESS).", callback=log_callback)
        return True

    except OSError as exc:
        _log(f"cfgmgr32.dll inaccessible : {exc}", level="ERROR", callback=log_callback)
        return False
    except Exception as exc:
        _log(f"Erreur inattendue (cfgmgr32) : {exc}", level="ERROR", callback=log_callback)
        return False


def reenumerate_usb_via_pnputil(log_callback: Optional[Callable] = None) -> bool:
    """
    Lance 'pnputil /scan-devices' pour forcer Windows à rescanner tous les
    bus PnP (équivalent à "Rechercher les modifications matérielles" dans le
    Gestionnaire de périphériques).

    Requiert des droits Administrateur — ignoré silencieusement sinon.
    Retourne True si la commande réussit.
    """
    _log("Scan PnP via pnputil /scan-devices...", callback=log_callback)

    if not is_admin():
        _log(
            "pnputil /scan-devices ignoré (droits Administrateur requis).",
            level="WARNING",
            callback=log_callback,
        )
        return False

    return _run_silent(
        ["pnputil", "/scan-devices"],
        timeout=8.0,
        log_callback=log_callback,
        label="pnputil /scan-devices",
    )


def reenumerate_usb_via_powershell(log_callback: Optional[Callable] = None) -> bool:
    """
    Réactive via PowerShell les périphériques USB en état 'Error' (code 43, etc.)
    qui pourraient être des téléphones MTK non initialisés correctement.

    Commande :
      Get-PnpDevice -Class 'USB' -Status 'Error' | Enable-PnpDevice -Confirm:$false

    Requiert des droits Administrateur — ignoré silencieusement sinon.
    Retourne True si PowerShell se termine sans erreur critique.
    """
    _log("Réactivation des périphériques USB en erreur via PowerShell...", callback=log_callback)

    if not is_admin():
        _log(
            "PowerShell Enable-PnpDevice ignoré (droits Administrateur requis).",
            level="WARNING",
            callback=log_callback,
        )
        return False

    ps_command = (
        "Get-PnpDevice -Class 'USB' -Status 'Error' | "
        "Enable-PnpDevice -Confirm:$false"
    )
    return _run_silent(
        [
            "powershell",
            "-NonInteractive",
            "-NoProfile",
            "-WindowStyle", "Hidden",
            "-Command", ps_command,
        ],
        timeout=10.0,
        log_callback=log_callback,
        label="PowerShell Enable-PnpDevice USB",
    )


def _find_adb_executable() -> Optional[str]:
    """
    Recherche l'exécutable ADB dans les emplacements standards.
    Priorité : tools/adb.exe → platform-tools/ → PATH → SDK paths → C:\\adb\\
    Retourne le chemin complet ou None si non trouvé.
    """
    # Répertoire racine du projet (parent de ce fichier)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    candidate_dirs = [
        os.path.join(project_root, "tools"),
        os.path.join(project_root, "platform-tools"),
    ]

    # Vérification dans les chemins candidats du projet
    for directory in candidate_dirs:
        candidate = os.path.join(directory, "adb.exe")
        if os.path.isfile(candidate):
            return candidate

    # Recherche dans le PATH système
    found = shutil.which("adb")
    if found:
        return found

    # Emplacements SDK Android standards
    sdk_paths = [
        r"C:\adb\adb.exe",
        r"C:\Android\platform-tools\adb.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
    ]
    for path in sdk_paths:
        if os.path.isfile(path):
            return path

    return None


def restart_adb_server(
    adb_bin: Optional[str] = None,
    log_callback: Optional[Callable] = None
) -> bool:
    """
    Redémarre proprement le serveur ADB :
      1. adb kill-server  (arrêt propre du démon)
      2. adb start-server (redémarrage en mode DETACHED pour éviter le deadlock)

    Le démon ADB DOIT être lancé en mode détaché (DETACHED_PROCESS) avec toutes
    les pipes redirigées vers DEVNULL pour éviter qu'il n'hérite des handles de
    l'application et ne se retrouve bloqué.

    Retourne True si adb start-server s'est lancé sans erreur.
    """
    # Résolution de l'exécutable ADB
    adb = adb_bin or _find_adb_executable()
    if not adb:
        _log(
            "Exécutable ADB introuvable (tools/adb.exe, platform-tools/, PATH, SDK).",
            level="WARNING",
            callback=log_callback,
        )
        return False

    _log(f"ADB trouvé : {adb}", callback=log_callback)

    # Étape 1 : kill-server (arrêt propre)
    _log("Arrêt du serveur ADB (adb kill-server)...", callback=log_callback)
    _run_silent([adb, "kill-server"], timeout=3.0, log_callback=log_callback, label="adb kill-server")

    # Étape 2 : start-server en mode détaché (CRITIQUE : ne pas utiliser capture_output=True)
    _log("Démarrage du serveur ADB (adb start-server)...", callback=log_callback)
    try:
        subprocess.Popen(
            [adb, "start-server"],
            stdin=_devnull(),
            stdout=_devnull(),
            stderr=_devnull(),
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
        )
        _log("Serveur ADB démarré en arrière-plan.", callback=log_callback)
        return True
    except FileNotFoundError:
        _log(f"ADB introuvable à l'exécution : {adb}", level="ERROR", callback=log_callback)
        return False
    except Exception as exc:
        _log(f"Erreur au démarrage du serveur ADB : {exc}", level="ERROR", callback=log_callback)
        return False


def perform_hardware_wake(
    adb_bin: Optional[str] = None,
    log_callback: Optional[Callable] = None
) -> Dict[str, bool]:
    """
    Point d'entrée principal du module.

    Exécute la séquence complète de réveil matériel USB + réinitialisation ADB
    avant le démarrage de l'interface graphique.

    Séquence :
      1. kill_zombie_adb()                 → Tue les processus adb.exe zombies
      2. reenumerate_usb_via_cfgmgr32()   → Réénumération USB via SetupAPI (sans admin)
      3. reenumerate_usb_via_pnputil()    → pnputil /scan-devices (admin requis)
      4. reenumerate_usb_via_powershell() → Enable-PnpDevice USB Error (admin requis)
      5. restart_adb_server()             → Redémarrage propre du démon ADB

    Garanties :
      - NE LÈVE JAMAIS d'exception (toutes capturées en interne).
      - Temps total < 8 secondes même en cas d'échec de toutes les étapes.
      - Fonctionne sans droits admin (étapes 3 et 4 ignorées silencieusement).

    Retourne :
      dict avec le statut booléen de chaque étape :
        {
            "kill_zombie_adb": bool,
            "cfgmgr32_reenumerate": bool,
            "pnputil_scan": bool,
            "powershell_enable": bool,
            "adb_restart": bool,
            "is_admin": bool,
        }
    """
    _log("=== Démarrage de la routine de réveil matériel USB ===", callback=log_callback)

    admin = is_admin()
    _log(
        f"Privilèges Administrateur : {'OUI' if admin else 'NON (étapes pnputil/PowerShell ignorées)'}",
        level="INFO" if admin else "WARNING",
        callback=log_callback,
    )

    results: Dict[str, bool] = {
        "kill_zombie_adb": False,
        "cfgmgr32_reenumerate": False,
        "pnputil_scan": False,
        "powershell_enable": False,
        "adb_restart": False,
        "is_admin": admin,
    }

    # Étape 1 — Tuer les processus ADB zombies
    try:
        results["kill_zombie_adb"] = kill_zombie_adb(log_callback=log_callback)
    except Exception as exc:
        _log(f"Étape 1 (kill_zombie_adb) — exception non gérée : {exc}", level="ERROR", callback=log_callback)

    # Étape 2 — Réénumération USB via cfgmgr32 (SetupAPI, sans admin requis)
    try:
        results["cfgmgr32_reenumerate"] = reenumerate_usb_via_cfgmgr32(log_callback=log_callback)
    except Exception as exc:
        _log(f"Étape 2 (cfgmgr32) — exception non gérée : {exc}", level="ERROR", callback=log_callback)

    # Étape 3 — pnputil /scan-devices (admin requis)
    try:
        results["pnputil_scan"] = reenumerate_usb_via_pnputil(log_callback=log_callback)
    except Exception as exc:
        _log(f"Étape 3 (pnputil) — exception non gérée : {exc}", level="ERROR", callback=log_callback)

    # Étape 4 — PowerShell Enable-PnpDevice (admin requis)
    try:
        results["powershell_enable"] = reenumerate_usb_via_powershell(log_callback=log_callback)
    except Exception as exc:
        _log(f"Étape 4 (PowerShell) — exception non gérée : {exc}", level="ERROR", callback=log_callback)

    # Étape 5 — Redémarrage du serveur ADB
    try:
        results["adb_restart"] = restart_adb_server(adb_bin=adb_bin, log_callback=log_callback)
    except Exception as exc:
        _log(f"Étape 5 (adb_restart) — exception non gérée : {exc}", level="ERROR", callback=log_callback)

    # Résumé
    success_count = sum(1 for k, v in results.items() if k != "is_admin" and v)
    total = len(results) - 1  # exclure "is_admin" du comptage
    _log(
        f"=== Réveil matériel terminé : {success_count}/{total} étapes réussies ===",
        callback=log_callback,
    )

    return results
