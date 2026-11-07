#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Optima MTK Tool Pro - Point d'Entrée Principal de l'Application
=============================================================================
Application d'Atelier pour Flash, Déblocage FRP & Bootloader MediaTek (MTK).
Architecture pure GUI Windows autonome, sans fenêtre console / DOS.
=============================================================================
"""

import sys
import os
import time
import subprocess
import logging

# Configuration logging interne
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("OptimaMTK.Main")


# ─── 1. Suppression absolue de la console DOS & protection des flux ─────────
def ensure_pure_gui():
    """
    Masque totalement toute invite de commandes Windows résiduelle et protège
    les flux standards sys.stdout / sys.stderr contre les crashs en mode --windowed.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
        except Exception:
            pass

    # En mode PyInstaller --windowed, sys.stdout et sys.stderr sont None.
    # Redirection vers os.devnull pour éviter AttributeError sur les appels print().
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


ensure_pure_gui()


# ─── 2. Résolution dynamique de la racine du projet ─────────────────────────
if getattr(sys, "frozen", False):
    # En mode binaire compilé PyInstaller : dossier de l'exécutable en priorité
    _exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    _meipass = getattr(sys, "_MEIPASS", None)
    ROOT_DIR = _exe_dir
    # Ajouter les deux chemins potentiels au sys.path
    for _p in (_exe_dir, _meipass):
        if _p and _p not in sys.path:
            sys.path.insert(0, _p)
else:
    # En mode script Python de développement
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# ─── 3. Nettoyage et purge au démarrage (Kill-switch automatique) ────────────
def kill_switch_startup_cleanup():
    """
    Purge bloquante et libération des ressources au tout début de l'exécution :
      1. Exécute taskkill /F /IM adb.exe /T pour libérer le port TCP 5037 et tuer les démons zombies.
      2. Exécute taskkill /F /IM fastboot.exe /T pour fermer tout processus fastboot orphelin.
      3. Réinitialise les sockets et bus matériels USB via perform_hardware_wake()
         afin d'empêcher tout verrouillage hérité sur les ports BROM / Preloader (Infinix/MTK).
    """
    creationflags = 0
    startupinfo = None
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
        startupinfo.wShowWindow = 0  # SW_HIDE

    # 1. Extermination sans fenêtre noire des démons ADB et Fastboot orphelins
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/IM", "adb.exe", "/T"],
                capture_output=True,
                creationflags=creationflags,
                startupinfo=startupinfo,
                timeout=3.0,
            )
            subprocess.run(
                ["taskkill", "/F", "/IM", "fastboot.exe", "/T"],
                capture_output=True,
                creationflags=creationflags,
                startupinfo=startupinfo,
                timeout=3.0,
            )
        else:
            subprocess.run(["killall", "-9", "adb"], capture_output=True, timeout=2.0)
            subprocess.run(["killall", "-9", "fastboot"], capture_output=True, timeout=2.0)
    except Exception as exc:
        logger.debug(f"[KILL-SWITCH] Purge des processus : {exc}")

    # 2. Vérification et libération du port socket TCP 5037
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", 5037)) == 0:
                time.sleep(0.2)
    except Exception:
        pass

    # 3. Réinitialisation des bus matériels USB et réveil contrôleurs d'hôtes (MTK)
    try:
        from core.usb_reset import perform_hardware_wake
        perform_hardware_wake()
    except Exception as exc:
        logger.debug(f"[KILL-SWITCH] Réveil matériel USB : {exc}")


# ─── 4. Fonction Principale (Démarrage GUI) ──────────────────────────────────
def main():
    """Initialise l'environnement, exécute la purge et lance l'interface graphique."""
    # A. Purge automatique bloquante au démarrage (Kill-switch ADB/TCP 5037/USB)
    kill_switch_startup_cleanup()

    # B. Initialisation des dépendances bas-niveau (LibUSB DLL, PATH bin/, drivers/)
    try:
        from core.init_env import init_environment
        init_environment()
    except Exception as exc:
        logger.warning(f"[INIT-ENV] Initialisation partielle de l'environnement : {exc}")

    # C. Vérification de la licence OFFLINE avant lancement de l'interface
    try:
        from core.license_manager import LicenseManager
        from gui.license_dialog import LicenseDialog
        from PyQt5.QtWidgets import QApplication

        license_mgr = LicenseManager()
        is_valid, msg, _ = license_mgr.is_license_valid()
        if not is_valid:
            # L'application nécessite une licence valide ; on affiche la dialog d'activation
            app_tmp = QApplication.instance()
            if app_tmp is None:
                app_tmp = QApplication([])
            dlg = LicenseDialog()
            if dlg.exec_() != LicenseDialog.Accepted:
                # L'utilisateur n'a pas activé de licence : sortie propre
                logger.info("[LICENCE] Aucun token activé. Arrêt de l'application.")
                return
    except Exception as exc:
        logger.warning(f"[LICENCE] Vérification de licence ignorée : {exc}")

    # D. Lancement de l'interface graphique PyQt5
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt
    from gui.main_window import MainWindow

    # Support haute résolution écran
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Optima MTK Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Optima Telecom")

    # Chargement de l'icône de l'application
    icon_path = os.path.join(ROOT_DIR, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Thème sombre moderne atelier
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
