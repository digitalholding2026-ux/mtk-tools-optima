# -*- coding: utf-8 -*-
"""
=============================================================================
Optima MTK Tool Pro - Module d'Initialisation de l'Environnement Bas-Niveau
=============================================================================
Architecture d'Atelier GSM & Dépendances Mobiles Autonomes (Compatible PyInstaller)

Ce module garantit le fonctionnement 100% autonome de l'application sur
n'importe quel poste Windows d'atelier, aussi bien en exécution script qu'en
mode binaire compilé PyInstaller (.exe / --onedir) :
  1. Résolution dynamique et bivalente des dossiers (sys._MEIPASS + dossier de l'exécutable).
  2. Encapsulation et liaison native de libusb-1.0.dll (WinUSB / LibUSB) pour PyUSB.
  3. Enregistrement sécurisé des répertoires DLL (os.add_dll_directory) sous Windows.
  4. Injection de bin/ et tools/ dans os.environ["PATH"] pour adb.exe et fastboot.exe.
  5. Détection de l'architecture (x64 / x86) et isolation des incompatibilités ABI.
=============================================================================
"""

import os
import sys
import platform
import logging
import ctypes
from typing import Optional, Dict, Any, List

logger = logging.getLogger("OptimaMTK.InitEnv")

# Drapeau d'initialisation unique (Singleton)
_ENV_INITIALIZED = False
_CACHED_LIBUSB_BACKEND = None
_DLL_DIRECTORIES = []


def is_frozen() -> bool:
    """Indique si l'application s'exécute sous forme d'exécutable compilé (PyInstaller)."""
    return getattr(sys, "frozen", False)


def get_app_dir() -> str:
    """
    Retourne le répertoire physique contenant l'exécutable (.exe) sous PyInstaller,
    ou la racine du projet en mode développement.
    Permet d'accéder aux dossiers externes modifiables (drivers, data, logs).
    """
    if is_frozen() and sys.executable:
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_project_root() -> str:
    """
    Retourne la racine des ressources du projet.
    Sous PyInstaller, priorise sys._MEIPASS (dossier interne bundle),
    avec repli sur le répertoire de l'exécutable.
    """
    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.isdir(meipass):
            return os.path.abspath(meipass)
        return get_app_dir()
    # core/init_env.py -> .. -> Racine du projet
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_search_roots() -> List[str]:
    """Retourne la liste ordonnée des racines où chercher les ressources et binaires."""
    roots = []
    root1 = get_project_root()
    root2 = get_app_dir()
    if root1 and root1 not in roots:
        roots.append(root1)
    if root2 and root2 not in roots:
        roots.append(root2)
    return roots


def get_bin_dir() -> str:
    """Retourne le chemin absolu du dossier des binaires embarqués (bin/ prioritaire, tools/ fallback)."""
    for root in get_search_roots():
        bin_path = os.path.join(root, "bin")
        if os.path.isdir(bin_path):
            return bin_path
        tools_path = os.path.join(root, "tools")
        if os.path.isdir(tools_path):
            return tools_path
    return os.path.join(get_project_root(), "bin")


def get_drivers_dir() -> str:
    """Retourne le chemin absolu du dossier des pilotes d'atelier (drivers/)."""
    for root in get_search_roots():
        drivers_path = os.path.join(root, "drivers")
        if os.path.isdir(drivers_path):
            return drivers_path
    return os.path.join(get_project_root(), "drivers")


def get_data_dir() -> str:
    """Retourne le chemin absolu du dossier de données et DA (data/)."""
    for root in get_search_roots():
        data_path = os.path.join(root, "data")
        if os.path.isdir(data_path):
            return data_path
    return os.path.join(get_project_root(), "data")


def is_64bit_python() -> bool:
    """Détermine si l'interpréteur Python actif est 64-bit ou 32-bit."""
    return sys.maxsize > 2**32


def resolve_libusb_dll_path() -> Optional[str]:
    """
    Localise la DLL libusb-1.0.dll compatible avec l'architecture courante.
    Ordre de recherche modulaire sur toutes les racines disponibles (bundle + install) :
      1. bin/x64/libusb-1.0.dll ou bin/x86/libusb-1.0.dll selon le runtime
      2. bin/libusb-1.0.dll (racine bin)
      3. tools/libusb-1.0.dll (compatibilité ascendante)
      4. Racine directe de l'exécutable (à côté de OptimaMTKTool.exe)
    """
    arch_subfolder = "x64" if is_64bit_python() else "x86"

    candidates = []
    for root in get_search_roots():
        candidates.extend([
            os.path.join(root, "bin", arch_subfolder, "libusb-1.0.dll"),
            os.path.join(root, "bin", "libusb-1.0.dll"),
            os.path.join(root, "tools", arch_subfolder, "libusb-1.0.dll"),
            os.path.join(root, "tools", "libusb-1.0.dll"),
            os.path.join(root, "libusb-1.0.dll"),
        ])

    for candidate in candidates:
        if os.path.isfile(candidate):
            try:
                ctypes.CDLL(candidate)
                logger.debug(f"[INIT-ENV] LibUSB DLL validée : {candidate}")
                return os.path.abspath(candidate)
            except OSError as err:
                logger.warning(f"[INIT-ENV] DLL détectée mais incompatible ABI ({candidate}) : {err}")
                continue

    return None


def configure_windows_dll_directories():
    """
    Configure la résolution de DLL pour Windows (Python 3.8+).
    Sous Windows 10/11, ctypes ne recherche plus dans PATH ni dans CWD
    sans appel explicite à os.add_dll_directory().
    """
    global _DLL_DIRECTORIES
    if sys.platform != "win32":
        return

    arch_subfolder = "x64" if is_64bit_python() else "x86"

    search_dirs = []
    for root in get_search_roots():
        search_dirs.extend([
            root,
            os.path.join(root, "bin"),
            os.path.join(root, "bin", arch_subfolder),
            os.path.join(root, "tools"),
            os.path.join(root, "tools", arch_subfolder),
        ])

    # os.add_dll_directory disponible depuis Python 3.8
    if hasattr(os, "add_dll_directory"):
        for directory in search_dirs:
            if os.path.isdir(directory):
                try:
                    cookie = os.add_dll_directory(directory)
                    _DLL_DIRECTORIES.append(cookie)
                    logger.debug(f"[INIT-ENV] os.add_dll_directory : {directory}")
                except Exception as err:
                    logger.debug(f"[INIT-ENV] Impossible d'ajouter {directory} : {err}")

    # Injection dans os.environ["PATH"] pour les processus enfants (adb.exe, fastboot.exe)
    existing_path = os.environ.get("PATH", "")
    new_paths = []
    for directory in search_dirs:
        if os.path.isdir(directory) and directory not in existing_path:
            new_paths.append(directory)

    if new_paths:
        os.environ["PATH"] = os.pathsep.join(new_paths) + os.pathsep + existing_path
        logger.debug(f"[INIT-ENV] PATH mis à jour avec les dossiers binaires : {new_paths}")


def get_libusb_backend():
    """
    Fournit le backend PyUSB LibUSB 1.0 configuré de façon autonome.
    Ordre de priorité :
      1. DLL embarquée (bin/ ou tools/) liée via find_library lambda
      2. Module autonome pip 'libusb-package'
      3. Backend système PyUSB standard
      4. None (Dégradation propre si LibUSB absent)
    """
    global _CACHED_LIBUSB_BACKEND
    if _CACHED_LIBUSB_BACKEND is not None:
        return _CACHED_LIBUSB_BACKEND

    try:
        import usb.backend.libusb1 as usb_libusb1
    except ImportError:
        logger.warning("[INIT-ENV] Le module 'pyusb' n'est pas installé. Détection passive désactivée.")
        return None

    # 1. Liaison avec la DLL locale ou embarquée
    dll_path = resolve_libusb_dll_path()
    if dll_path:
        try:
            backend = usb_libusb1.get_backend(find_library=lambda x: dll_path)
            if backend is not None:
                logger.info(f"[INIT-ENV] Backend LibUSB initialisé avec succès : {dll_path}")
                _CACHED_LIBUSB_BACKEND = backend
                return backend
        except Exception as err:
            logger.warning(f"[INIT-ENV] Échec du chargement du backend local ({dll_path}) : {err}")

    # 2. Secours via le paquet pip 'libusb-package'
    try:
        import libusb_package
        backend = libusb_package.get_libusb1_backend()
        if backend is not None:
            logger.info("[INIT-ENV] Backend LibUSB initialisé via le paquet 'libusb-package'.")
            _CACHED_LIBUSB_BACKEND = backend
            return backend
    except ImportError:
        pass
    except Exception as err:
        logger.debug(f"[INIT-ENV] libusb-package a échoué : {err}")

    # 3. Secours via auto-découverte système standard PyUSB
    try:
        backend = usb_libusb1.get_backend()
        if backend is not None:
            logger.info("[INIT-ENV] Backend LibUSB initialisé via la configuration système.")
            _CACHED_LIBUSB_BACKEND = backend
            return backend
    except Exception as err:
        logger.debug(f"[INIT-ENV] Auto-découverte PyUSB système échouée : {err}")

    logger.warning(
        "[INIT-ENV] Aucun backend LibUSB valide n'a pu être initialisé. "
        "Vérifiez la présence de 'libusb-1.0.dll' dans bin/ ou installez 'libusb-package'."
    )
    return None


def get_adb_path() -> Optional[str]:
    """Retourne le chemin de l'exécutable adb.exe (bin/ prioritaire, puis tools/, puis PATH)."""
    import shutil
    candidates = []
    for root in get_search_roots():
        candidates.extend([
            os.path.join(root, "bin", "adb.exe"),
            os.path.join(root, "tools", "adb.exe"),
            os.path.join(root, "adb.exe"),
            os.path.join(root, "bin", "adb"),
            os.path.join(root, "tools", "adb"),
        ])

    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return os.path.abspath(c)

    sys_adb = shutil.which("adb")
    if sys_adb:
        return sys_adb
    return None


def get_fastboot_path() -> Optional[str]:
    """Retourne le chemin de l'exécutable fastboot.exe (bin/ prioritaire, puis tools/, puis PATH)."""
    import shutil
    candidates = []
    for root in get_search_roots():
        candidates.extend([
            os.path.join(root, "bin", "fastboot.exe"),
            os.path.join(root, "tools", "fastboot.exe"),
            os.path.join(root, "fastboot.exe"),
            os.path.join(root, "bin", "fastboot"),
            os.path.join(root, "tools", "fastboot"),
        ])

    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return os.path.abspath(c)

    sys_fb = shutil.which("fastboot")
    if sys_fb:
        return sys_fb
    return None


def init_environment() -> Dict[str, Any]:
    """
    Point d'entrée principal pour initialiser l'ensemble des dépendances bas-niveau.
    À exécuter tout en haut de main.py avant les imports Qt ou communications série.
    """
    global _ENV_INITIALIZED
    if _ENV_INITIALIZED:
        return get_environment_diagnostics()

    # 1. Configurer répertoires DLL et variable d'environnement PATH
    configure_windows_dll_directories()

    # 2. Préparer le backend PyUSB
    backend = get_libusb_backend()

    _ENV_INITIALIZED = True
    diag = get_environment_diagnostics()

    status_str = "OK" if diag["libusb_available"] else "PARTIEL"
    logger.info(
        f"[INIT-ENV] Environnement d'atelier initialisé [{status_str}] : "
        f"Frozen={diag['is_frozen']}, Arch={diag['arch']}, "
        f"LibUSB={'Présent' if diag['libusb_available'] else 'Absent'}, "
        f"ADB={'Présent' if diag['adb_path'] else 'Absent'}, "
        f"Fastboot={'Présent' if diag['fastboot_path'] else 'Absent'}"
    )

    return diag


def get_environment_diagnostics() -> Dict[str, Any]:
    """Génère un rapport complet sur l'état des composants matériels et binaires."""
    dll_path = resolve_libusb_dll_path()
    adb_path = get_adb_path()
    fastboot_path = get_fastboot_path()

    has_backend = (_CACHED_LIBUSB_BACKEND is not None) or (get_libusb_backend() is not None)

    return {
        "is_frozen": is_frozen(),
        "project_root": get_project_root(),
        "app_dir": get_app_dir(),
        "bin_dir": get_bin_dir(),
        "drivers_dir": get_drivers_dir(),
        "data_dir": get_data_dir(),
        "arch": "x64 (64-bit)" if is_64bit_python() else "x86 (32-bit)",
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "libusb_dll_path": dll_path,
        "libusb_available": has_backend,
        "adb_path": adb_path,
        "fastboot_path": fastboot_path,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    print("--- Test du Bootstrap d'Environnement Optima MTK Tool ---")
    report = init_environment()
    for k, v in report.items():
        print(f"  {k:20}: {v}")
