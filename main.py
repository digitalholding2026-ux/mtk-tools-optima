#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optima MTK Tool - Point d'entrée de l'application
Application de flash et déblocage FRP pour processeurs MediaTek
"""

import sys
import os

# Ajout du répertoire racine au path pour permettre les imports relatifs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from gui.main_window import MainWindow


def main():
    """Fonction principale de lancement de l'application."""
    # 1. Réveil matériel USB + réinitialisation ADB avant tout démarrage de l'UI
    #    (simule le comportement de réveil de TFT Unlock au lancement)
    try:
        from core.usb_reset import perform_hardware_wake, is_admin
        perform_hardware_wake()
        if not is_admin():
            # Avertissement non-bloquant : certaines fonctions BROM peuvent nécessiter les droits admin
            print(
                "[USB-WAKE][WARNING] Application lancée sans droits Administrateur. "
                "La détection BROM/COM peut être limitée.",
                file=sys.stderr,
            )
    except Exception:
        # Fallback : au minimum, on tente de réinitialiser le serveur ADB
        try:
            from core.detector import reset_adb_server
            reset_adb_server()
        except Exception:
            pass

    # Activation du scaling haute DPI sur Windows
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Optima MTK Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Optima Telecom")

    # Chargement de l'icône de l'application si elle existe
    icon_path = os.path.join("assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Style global de l'application (mode sombre)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
