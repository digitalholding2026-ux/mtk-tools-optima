# -*- coding: utf-8 -*-
"""
Optima MTK Tool Pro - Script de Build PyInstaller Python
Automatise la compilation en environnement Windows avec contrôle des dépendances.
"""

import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist", "OptimaMTKTool")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")


def check_and_create_icon():
    """Garantit l'existence de assets/icon.ico avant le build."""
    icon_path = os.path.join(PROJECT_ROOT, "assets", "icon.ico")
    if os.path.isfile(icon_path):
        return icon_path

    print("[*] Génération de l'icône assets/icon.ico...")
    try:
        from PIL import Image, ImageDraw
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        imgs = []
        for w, h in sizes:
            im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle(
                [1, 1, w - 2, h - 2],
                radius=int(w * 0.22),
                fill=(18, 110, 240, 255),
                outline=(0, 200, 255, 255),
                width=max(1, int(w * 0.04))
            )
            cx, cy = w // 2, h // 2
            r = int(w * 0.28)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))
            r2 = int(w * 0.16)
            d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(18, 110, 240, 255))
            imgs.append(im)
        os.makedirs(os.path.dirname(icon_path), exist_ok=True)
        imgs[0].save(icon_path, format='ICO', sizes=sizes, append_images=imgs[1:])
        print("  [OK] assets/icon.ico générée avec succès.")
    except Exception as e:
        print(f"  [AVERTISSEMENT] Impossible de générer l'icône ({e}).")
    return icon_path


def run_build():
    """Exécute la compilation PyInstaller avec tous les drapeaux requis."""
    print("=" * 70)
    print("    OPTIMA MTK TOOL - COMPILATION DU PACKAGE EXÉCUTABLE WINDOWS")
    print("=" * 70)

    icon_path = check_and_create_icon()

    # Nettoyage
    for d in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(d):
            print(f"[*] Suppression de l'ancien dossier : {d}")
            shutil.rmtree(d, ignore_errors=True)

    spec_file = os.path.join(PROJECT_ROOT, "OptimaMTKTool.spec")
    if os.path.isfile(spec_file):
        os.remove(spec_file)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--uac-admin",
        "--name", "OptimaMTKTool",
        f"--icon={icon_path}",
        "--add-data", f"drivers{os.pathsep}drivers",
        "--add-data", f"bin{os.pathsep}bin",
        "--add-data", f"assets{os.pathsep}assets",
        "--add-data", f"data{os.pathsep}data",
        "--hidden-import", "usb.core",
        "--hidden-import", "usb.util",
        "--hidden-import", "usb.backend.libusb1",
        "--hidden-import", "serial.tools.list_ports",
        "--hidden-import", "serial.tools.list_ports_windows",
        "main.py"
    ]

    print("\n[+] Exécution de la commande PyInstaller :")
    print("    " + " ".join(cmd))
    print("-" * 70)

    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(f"\n[ERREUR] PyInstaller s'est terminé avec le code d'erreur {res.returncode}")
        sys.exit(res.returncode)

    # Post-traitement : Structure modulaire d'atelier
    print("\n[*] Post-traitement de la structure d'atelier...")
    # Copie de libusb-1.0.dll à la racine de dist/
    libusb_src = os.path.join(PROJECT_ROOT, "bin", "libusb-1.0.dll")
    if os.path.isfile(libusb_src):
        shutil.copy2(libusb_src, os.path.join(DIST_DIR, "libusb-1.0.dll"))

    # Miroir externe des dossiers d'atelier
    for folder in ["drivers", "bin", "data"]:
        src = os.path.join(PROJECT_ROOT, folder)
        dst = os.path.join(DIST_DIR, folder)
        if os.path.isdir(src) and not os.path.exists(dst):
            shutil.copytree(src, dst)

    print("\n" + "=" * 70)
    print(" COMPILATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 70)
    print(f"Emplacement de l'exécutable : {os.path.join(DIST_DIR, 'OptimaMTKTool.exe')}")


if __name__ == "__main__":
    run_build()
