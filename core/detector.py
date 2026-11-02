# -*- coding: utf-8 -*-
"""
Module de détection automatique et en temps réel des périphériques pour Optima MTK Tool.
Surveille en arrière-plan (QThread non bloquant) les modes :
  - BROM / BootROM (MediaTek VCOM, Preloader, DA USB)
  - FASTBOOT (Fastboot Bootloader via 'fastboot devices')
  - ADB (Débogage USB actif, réponse confirmée par 'adb devices')
  - USB_NORMAL (Appareil branché allumé sans débogage / pont ADB inactif)
"""

import os
import sys
import time
import shutil
import threading
import subprocess
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

from PyQt5.QtCore import QThread, pyqtSignal

try:
    import serial.tools.list_ports as list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

try:
    from core.usb_scanner import UsbScanner, UsbDeviceInfo, scan_mtk_devices, HAS_PYUSB
    _usb_scanner: Optional[UsbScanner] = None  # Initialisé à la première utilisation
    def _get_usb_scanner() -> "UsbScanner":
        global _usb_scanner
        if _usb_scanner is None:
            _usb_scanner = UsbScanner()
        return _usb_scanner
except ImportError:
    HAS_PYUSB = False
    def _get_usb_scanner():
        return None


# =====================================================================
# Modèles de données
# =====================================================================

class DeviceMode(str, Enum):
    """
    Modes de fonctionnement des appareils détectés.

    Hiérarchie de priorité de scan : BROM > FASTBOOT > ADB > USB_NORMAL > NONE
    """
    NONE       = "NONE"         # Aucun appareil détecté
    BROM       = "BROM"         # BootROM matériel / Preloader MediaTek (port VCOM)
    FASTBOOT   = "FASTBOOT"     # Fastboot bootloader Android
    ADB        = "ADB"          # Débogage USB actif (adb devices confirme la réponse)
    USB_NORMAL = "USB_NORMAL"   # Appareil branché allumé, sans pont ADB ni BROM actif
    NORMAL     = "NORMAL"       # Alias rétrocompatibilité (ports AT/Modem MediaTek)


@dataclass
class ConnectedDevice:
    """Représentation unifiée d'un appareil connecté."""
    mode: DeviceMode
    identifier: str                        # Clé unique (ex: 'COM3' ou 'FASTBOOT:0123456789')
    port: Optional[str] = None             # Port COM éventuel (ex: 'COM3')
    serial_number: Optional[str] = None    # N° de série (ex: Fastboot/ADB)
    description: str = ""                  # Description conviviale
    vid: Optional[int] = None              # Vendor ID USB (ex: 0x0E8D)
    pid: Optional[int] = None              # Product ID USB (ex: 0x0003)
    manufacturer: Optional[str] = None
    hwid: Optional[str] = None
    protocol: str = ""                     # Protocole détecté
    details: Dict[str, Any] = field(default_factory=dict)

    def is_brom(self) -> bool:
        return self.mode == DeviceMode.BROM

    def is_fastboot(self) -> bool:
        return self.mode == DeviceMode.FASTBOOT

    def is_normal(self) -> bool:
        """Retourne True pour tous les modes "appareil allumé" (ADB, Normal AT, USB Normal)."""
        return self.mode in (DeviceMode.NORMAL, DeviceMode.ADB, DeviceMode.USB_NORMAL)

    def is_adb(self) -> bool:
        """Retourne True uniquement si le débogage ADB est actif et confirmé."""
        return self.mode == DeviceMode.ADB

    def is_usb_normal(self) -> bool:
        """Retourne True si l'appareil est branché allumé sans pont debug actif."""
        return self.mode == DeviceMode.USB_NORMAL

    @property
    def mode_display(self) -> str:
        """Libellé convivial du mode, utilisé dans les badges et logs."""
        if self.mode == DeviceMode.BROM:
            return "BROM / Preloader"
        elif self.mode == DeviceMode.FASTBOOT:
            return "Fastboot"
        elif self.mode == DeviceMode.ADB:
            return "ADB (Débogage actif)"
        elif self.mode == DeviceMode.USB_NORMAL:
            return "Normal (non sécurisé)"
        elif self.mode == DeviceMode.NORMAL:
            return "Normal / AT"
        return "Aucun"

    @property
    def color(self) -> str:
        """
        Couleur hex associée au mode :
          🟢 Vert  — BROM, Fastboot, ADB actif (opérations possibles)
          🟡 Jaune — USB Normal (branché mais sans protocole debug actif)
          🔴 Rouge — Aucun appareil
        """
        if self.mode in (DeviceMode.BROM, DeviceMode.FASTBOOT, DeviceMode.ADB, DeviceMode.NORMAL):
            return "#2ecc71"        # 🟢 Vert — opérations possibles
        elif self.mode == DeviceMode.USB_NORMAL:
            return "#f1c40f"        # 🟡 Jaune — branché mais inutilisable pour flash/FRP
        return "#e74c3c"            # 🔴 Rouge — aucun appareil

    @property
    def status_emoji(self) -> str:
        """Émoticône représentative du statut."""
        if self.mode in (DeviceMode.BROM, DeviceMode.FASTBOOT, DeviceMode.ADB, DeviceMode.NORMAL):
            return "🟢"
        elif self.mode == DeviceMode.USB_NORMAL:
            return "🟡"
        return "🔴"

    @property
    def badge_title(self) -> str:
        """
        Titre standardisé affiché dans le bandeau de statut et le badge d'en-tête.

        Règles de libellé conformes aux specs Optima Telecom :
          - BROM     → "Connecté en mode BROM / Preloader (Port COM...)"
          - FASTBOOT → "Connecté en mode Fastboot"
          - ADB      → "Connecté en mode ADB (Débogage actif)"
          - USB_NORMAL → "Appareil branché (Mode Normal / Non sécurisé pour flash/FRP)"
          - NORMAL   → "Connecté en mode Normal / AT"
        """
        if self.mode == DeviceMode.BROM:
            port_name = self.port or self.identifier
            return f"Connecté en mode BROM / Preloader (Port {port_name})"
        elif self.mode == DeviceMode.FASTBOOT:
            return "Connecté en mode Fastboot"
        elif self.mode == DeviceMode.ADB:
            return "Connecté en mode ADB (Débogage actif)"
        elif self.mode == DeviceMode.USB_NORMAL:
            return "Appareil branché (Mode Normal / Non sécurisé pour les opérations de flash/FRP)"
        elif self.mode == DeviceMode.NORMAL:
            return "Appareil branché (Mode Normal / Non sécurisé pour les opérations de flash/FRP)"
        return "Aucun appareil détecté"

    @property
    def badge_subtitle(self) -> str:
        """Détail technique affiché sous le titre de badge."""
        if self.mode == DeviceMode.BROM:
            vid_pid = f"VID:{self.vid:04X} PID:{self.pid:04X}" if self.vid and self.pid else "MediaTek VCOM"
            return f"{self.protocol or 'MediaTek BootROM'} • {vid_pid}"
        elif self.mode == DeviceMode.FASTBOOT:
            return f"Protocole Fastboot • Série : {self.serial_number or 'Inconnu'}"
        elif self.mode == DeviceMode.ADB:
            serial = self.serial_number or self.identifier
            state = self.details.get("adb_state", "device")
            return f"ADB Interface ({state}) • Série : {serial}"
        elif self.mode == DeviceMode.USB_NORMAL:
            return "Pour FRP / Flash : éteignez l'appareil et suivez l'assistant de connexion."
        elif self.mode == DeviceMode.NORMAL:
            target = self.port or self.serial_number or self.identifier
            return f"{self.protocol or 'Modem AT / Interface'} • {target}"
        return "Surveillance active (BROM, Fastboot, ADB)…"


# =====================================================================
# Identifiants matériels MediaTek connus
# =====================================================================

MTK_VENDORS = {
    0x0E8D,   # MediaTek Inc. officiel (omniprésent)
    0x0489,   # Foxconn / Modules MTK
    0x6000,   # Périphériques MTK génériques
    0x2717,   # Xiaomi (certains modèles MTK Preloader)
    0x2A70,   # OnePlus / Oppo MTK
}

# PIDs BROM / BootROM matériel (téléchargement direct DA)
MTK_BROM_PIDS = {
    0x0003,   # MediaTek USB Port (Vrai BootROM matériel)
    0x0001,   # MTK USB Port alternatif
    0x0002,   # MTK Download Port
}

# PIDs Preloader (Chargeur d'amorçage secondaire)
MTK_PRELOADER_PIDS = {
    0x2000,   # MediaTek DA USB VCOM Port / Preloader
    0x2001,   # MediaTek USB VCOM (Android)
    0x2002,   # MediaTek USB Port
}

# PIDs Modem / AT / Normal / Diagnostic
MTK_NORMAL_PIDS = {
    0x2006,   # MTK USB Modem
    0x2007,   # MTK AT Port
    0x2008,   # MTK Debug / COM
    0x200E,   # MTK CDC Serial
    0x201D,   # MTK Android Modem
    0x201F,   # MTK Dual COM
    0x202D,   # MTK Engineering Port
}

KEYWORDS_BROM = [
    "BOOTROM", "BROM", "MTK USB PORT", "MEDIATEK USB PORT",
    "PRELOADER", "PRE-LOADER", "DA USB VCOM", "DOWNLOAD AGENT",
    "MTK DA", "MT65XX", "MT67XX", "MT68XX"
]

KEYWORDS_NORMAL = [
    "MODEM", "AT PORT", "AT COMMAND", "USB DEBUG", "CDC ACM",
    "GADGET SERIAL", "ANDROID AT", "INTERFACE AT"
]


# =====================================================================
# Localisation dynamique de l'exécutable ADB
# =====================================================================

def get_adb_path() -> str:
    """
    Localise l'exécutable ADB local (bin/adb.exe) de manière ciblée au lieu de la commande globale.
    Priorité absolue sur le dossier local bin/adb.exe de l'application.
    """
    if getattr(sys, 'frozen', False):
        # Mode exécutable compilé (PyInstaller)
        base_path = os.path.dirname(sys.executable)
        candidates = [
            os.path.join(base_path, "bin", "adb.exe"),
            os.path.join(getattr(sys, '_MEIPASS', ''), "bin", "adb.exe"),
            os.path.join(base_path, "_internal", "bin", "adb.exe"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return os.path.abspath(c)
    else:
        # Mode script de développement
        base_path = os.path.abspath(os.path.dirname(__file__))
        # Si le fichier est dans core/, remonter à la racine du projet
        if not os.path.exists(os.path.join(base_path, "bin", "adb.exe")):
            parent = os.path.dirname(base_path)
            if os.path.exists(os.path.join(parent, "bin", "adb.exe")):
                base_path = parent

    # Pointe vers bin/adb.exe
    adb_path = os.path.join(base_path, "bin", "adb.exe")
    if not os.path.exists(adb_path):
        # Repli de secours sur tools/ ou adb global
        fallback_tools = os.path.join(base_path, "tools", "adb.exe")
        if os.path.exists(fallback_tools):
            return os.path.abspath(fallback_tools)
        adb_path = "adb"  # Fallback global si introuvable
    else:
        adb_path = os.path.abspath(adb_path)
    return adb_path


# =====================================================================
# Nettoyage et initialisation autonome du serveur ADB
# =====================================================================

def reset_adb_server(adb_bin: Optional[str] = None) -> bool:
    """
    Nettoie et réinitialise proprement le serveur ADB au démarrage de l'outil.
    Exécute de façon robuste et masquée (CREATE_NO_WINDOW sous Windows) :
      subprocess.run([get_adb_path(), "kill-server"], capture_output=True, timeout=2)
      subprocess.run([get_adb_path(), "start-server"], capture_output=True, timeout=2)

    Garantit que le daemon ADB est propre, réactif et actif dès le lancement,
    rendant Optima MTK Tool totalement autonome sans dépendre d'un outil tiers.
    """
    if not adb_bin:
        adb_bin = get_adb_path()

    creationflags = 0
    startupinfo = None
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
        startupinfo.wShowWindow = 0  # SW_HIDE

    # 1. Purge vigoureuse des processus adb orphelins ou figés sous Windows
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "adb.exe", "/T"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1,
                creationflags=creationflags,
                startupinfo=startupinfo
            )
        except Exception:
            pass

    # 2. Kill standard du serveur ADB
    try:
        subprocess.run(
            [adb_bin, "kill-server"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            creationflags=creationflags,
            startupinfo=startupinfo
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        pass
    except Exception:
        pass

    # 3. Démarrage du serveur ADB propre sans héritage de descripteurs de pipe
    # (Évite le deadlock où le daemon en arrière-plan maintient le pipe stdout ouvert)
    try:
        detached_flags = creationflags
        if sys.platform == "win32":
            detached_flags |= getattr(subprocess, "DETACHED_PROCESS", 0x00000008)

        res = subprocess.run(
            [adb_bin, "start-server"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            creationflags=detached_flags,
            startupinfo=startupinfo
        )
        return res.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        return False
    except Exception:
        return False


# =====================================================================
# Service de détection en arrière-plan
# =====================================================================

class DeviceDetector(QThread):
    """
    Worker d'arrière-plan inspectant périodiquement les ports COM et Fastboot.
    Émet des signaux Qt thread-safe pour rafraîchir l'interface sans figer l'UI.
    """

    # Signaux d'événements
    device_detected = pyqtSignal(object)           # Emis à la détection (ConnectedDevice)
    device_lost = pyqtSignal(object)               # Emis à la déconnexion (ConnectedDevice)
    device_changed = pyqtSignal(object)            # Emis à chaque changement (ConnectedDevice ou None)
    status_updated = pyqtSignal(str, str, str, str)# (mode_str, title, subtitle, color_hex)
    log_message = pyqtSignal(str, str)             # (message, level: "info"|"success"|"warning"|"error")

    def __init__(self, interval: float = 1.5, parent=None):
        super().__init__(parent)
        self._interval = interval
        self._running = False
        self._current_device: Optional[ConnectedDevice] = None
        self._scan_lock = threading.Lock()
        self._fastboot_bin = self._find_fastboot_executable()
        self._adb_bin = self._find_adb_executable()

    # -----------------------------------------------------------------
    # Localisation des binaires utilitaires (fastboot, adb)
    # -----------------------------------------------------------------
    def _find_fastboot_executable(self) -> Optional[str]:
        """Localise l'exécutable fastboot dans bin/, tools/, PATH ou Android SDK."""
        try:
            from core.init_env import get_fastboot_path
            fb_path = get_fastboot_path()
            if fb_path:
                return fb_path
        except Exception:
            pass

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base_dir, "tools", "fastboot.exe"),
            os.path.join(base_dir, "tools", "fastboot"),
            os.path.join(base_dir, "platform-tools", "fastboot.exe"),
            os.path.join(base_dir, "assets", "bin", "fastboot.exe"),
            os.path.join(base_dir, "bin", "fastboot.exe"),
        ]
        for path in candidates:
            if os.path.isfile(path) and (sys.platform != "win32" or os.access(path, os.X_OK)):
                return path

        found = shutil.which("fastboot") or shutil.which("fastboot.exe")
        if found:
            return found

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        user_profile = os.environ.get("USERPROFILE", "")
        sdk_candidates = []
        if local_app_data:
            sdk_candidates.append(os.path.join(local_app_data, "Android", "Sdk", "platform-tools", "fastboot.exe"))
        if user_profile:
            sdk_candidates.append(os.path.join(user_profile, "AppData", "Local", "Android", "Sdk", "platform-tools", "fastboot.exe"))

        sdk_candidates.extend([
            r"C:\adb\fastboot.exe",
            r"C:\platform-tools\fastboot.exe",
            r"C:\Program Files\Android\platform-tools\fastboot.exe",
            r"C:\Program Files (x86)\Android\platform-tools\fastboot.exe",
        ])
        for path in sdk_candidates:
            if os.path.isfile(path):
                return path

        return "fastboot"  # Fallback sur la commande système

    def _find_adb_executable(self) -> str:
        """Localise l'exécutable local bin/adb.exe via get_adb_path()."""
        return get_adb_path()

    # -----------------------------------------------------------------
    # Cycle de vie du thread
    # -----------------------------------------------------------------
    def start_monitoring(self):
        """Démarre le thread de surveillance en continu."""
        if self.isRunning():
            return

        # Réinitialisation propre du serveur ADB dès le démarrage pour autonomie totale
        try:
            reset_adb_server(self._adb_bin)
        except Exception:
            pass

        self._running = True
        self.start()
        self.log_message.emit("Service de détection automatique USB démarré (BROM / Fastboot / ADB / Normal).", "info")

    def stop_monitoring(self):
        """Arrête le thread proprement."""
        self._running = False
        self.wait(2000)

    def scan_now(self, force_refresh: bool = True) -> Optional[ConnectedDevice]:
        """
        Force une analyse synchrone et immédiate sans attendre l'intervalle de polling.
        Émet instantanément les signaux Qt vers l'interface graphique (GUI).
        Retourne l'appareil détecté ou None.
        """
        return self._perform_scan(force_emit=force_refresh)

    def run(self):
        """Boucle de surveillance d'arrière-plan résiliente."""
        self._running = True
        while self._running:
            try:
                self._perform_scan(force_emit=False)
            except FileNotFoundError:
                # Binaire (adb, fastboot) introuvable dans le système ou tools/
                pass
            except PermissionError:
                # Accès refusé temporaire sur un port USB/COM en cours d'énumération
                pass
            except subprocess.TimeoutExpired:
                # Timeout d'une commande subprocess
                pass
            except (subprocess.SubprocessError, OSError):
                pass
            except Exception as e:
                # Toute autre exception inattendue est capturée pour ne jamais tuer le thread
                pass

            # Sommeil par micro-intervalles pour arrêt immédiat lors de la fermeture
            steps = int(self._interval * 10)
            for _ in range(max(1, steps)):
                if not self._running:
                    break
                self.msleep(100)

    # -----------------------------------------------------------------
    # Logique d'analyse des périphériques
    # -----------------------------------------------------------------
    def _perform_scan(self, force_emit: bool = False) -> Optional[ConnectedDevice]:
        """
        Scanne les ports COM, Fastboot et ADB en respectant la hiérarchie.
        Thread-safe grâce à un verrou exclusif.
        Émet les signaux d'interface dès que l'état change ou si force_emit est True.
        """
        with self._scan_lock:
            try:
                devices = self._scan_all_candidates()
            except Exception:
                devices = []

            # Sélection de l'appareil prioritaire : BROM > FASTBOOT > ADB > USB_NORMAL > NORMAL
            detected: Optional[ConnectedDevice] = None
            if devices:
                priority_order = {
                    DeviceMode.BROM: 1,
                    DeviceMode.FASTBOOT: 2,
                    DeviceMode.ADB: 3,
                    DeviceMode.USB_NORMAL: 4,
                    DeviceMode.NORMAL: 5,
                }
                devices.sort(key=lambda d: priority_order.get(d.mode, 99))
                detected = devices[0]

            # Comparaison avec l'état précédent
            old = self._current_device

            if detected is None:
                if old is not None or force_emit:
                    self._current_device = None
                    if old is not None:
                        self._notify_lost(old)
                    self._emit_status_update(None)

            else:
                # Appareil détecté
                state_changed = (
                    old is None or
                    (detected.identifier != old.identifier) or
                    (detected.mode != old.mode)
                )
                if state_changed or force_emit:
                    self._current_device = detected
                    if old is not None and (old.identifier != detected.identifier or old.mode != detected.mode):
                        self._notify_lost(old)
                    self._notify_detected(detected)
                    self._emit_status_update(detected)

            return detected

    def _scan_all_candidates(self) -> List[ConnectedDevice]:
        """
        Collecte l'ensemble des périphériques détectés en respectant la hiérarchie :
          USB-Direct(PyUSB) > BROM(COM) > FASTBOOT > ADB > USB_NORMAL

        RÈGLES D'AUTONOMIE & PERFORMANCE :
        0. [PRIORITÉ MAX] Scan USB bas-niveau via PyUSB/libusb :
           Détecte VID 0x0E8D directement sur le bus USB, avant l'attribution d'un
           port COM par Windows. Capture la fenêtre BROM critique (~2–4s).
           Fonctionne sans pilote COM (uniquement WinUSB/libusb-win32 via Zadig).
        1. Ports COM inspectés passivement via list_ports.comports() (zéro serial.Serial()).
        2. Priorité BROM immédiate : Si un port BROM ou Preloader est détecté, on le retourne
           instantanément sans perdre de temps à appeler fastboot/adb pour ne pas rater
           la fenêtre critique d'amorçage BootROM MediaTek.
        3. ADB n'est déclaré que si 'adb devices' répond réellement (state 'device'/'recovery').
        """
        results: List[ConnectedDevice] = []

        # 0. [NOUVEAU] Scan USB direct via PyUSB / libusb (VID 0x0E8D, avant le port COM)
        #    Détection la plus rapide — aucune subprocess, lecture hardware directe.
        try:
            usb_devices = self._scan_usb_direct()
            results.extend(usb_devices)
        except Exception:
            pass

        # Si un BROM est déjà détecté en USB direct → retour immédiat (priorité absolue)
        if any(d.mode == DeviceMode.BROM for d in results):
            return results

        # 1. Analyse passive des ports COM (BROM, Preloader, AT/Modem)
        try:
            com_devices = self._scan_com_ports()
            # Dédoublonnage : éviter les doublons si le même périphérique est vu par COM ET PyUSB
            existing_vid_pids = {(d.vid, d.pid) for d in results if d.vid and d.pid}
            for com_dev in com_devices:
                if com_dev.vid and com_dev.pid and (com_dev.vid, com_dev.pid) in existing_vid_pids:
                    continue  # Déjà détecté via PyUSB, on ne duplique pas
                results.append(com_dev)
        except Exception:
            pass

        # Si un mode BROM ou Preloader est déjà détecté, priorité absolue : retour immédiat
        if any(d.mode == DeviceMode.BROM for d in results):
            return results

        # 2. Analyse Fastboot (via commande 'fastboot devices')
        try:
            fastboot_dev = self._scan_fastboot()
            if fastboot_dev:
                results.append(fastboot_dev)
        except Exception:
            pass

        # 3. Analyse ADB uniquement si pas encore de BROM ni Fastboot
        #    → sépare ADB "actif" de "unauthorized" (USB Normal)
        if not any(d.mode in (DeviceMode.BROM, DeviceMode.FASTBOOT) for d in results):
            try:
                adb_dev, usb_normal_dev = self._scan_adb_detailed()
                if adb_dev:
                    results.append(adb_dev)
                elif usb_normal_dev and not results:
                    results.append(usb_normal_dev)
            except Exception:
                pass

        return results

    # -----------------------------------------------------------------
    # 0. [NOUVEAU] Détection USB directe via PyUSB / libusb (VID 0x0E8D)
    # -----------------------------------------------------------------
    def _scan_usb_direct(self) -> List[ConnectedDevice]:
        """
        Scanne le bus USB directement via PyUSB / libusb (lecture hardware brute).

        Avantages par rapport au scan COM classique :
          • Détecte le chipset MTK AVANT que Windows attribue un port COM virtuel.
          • Capture la fenêtre BootROM critique (~2–4 secondes) même sans pilote COM.
          • Fonctionne avec les pilotes WinUSB / libusb-win32 installés via Zadig.
          • Aucun handle conservé entre les scans — lecture 100% passive.

        Retourne [] si PyUSB / libusb ne sont pas disponibles (pas de crash).
        Note sur les pilotes : Pour détecter le BROM via cette méthode, le pilote
        WinUSB ou libusb-win32 doit être associé au VID 0x0E8D PID 0x0003 via Zadig.
        En l'absence de ce pilote, la détection COM classique reste le chemin principal.
        """
        if not HAS_PYUSB:
            return []

        scanner = _get_usb_scanner()
        if scanner is None or not scanner.is_available:
            return []

        results: List[ConnectedDevice] = []

        try:
            usb_devices = scanner.scan_mtk_devices()
        except Exception as exc:
            # Le scan USB ne doit JAMAIS faire crasher le thread de détection
            return []

        for usb_dev in usb_devices:
            try:
                # Conversion UsbDeviceInfo → ConnectedDevice (modèle unifié du détecteur)
                if usb_dev.mode == "BROM":
                    device_mode = DeviceMode.BROM
                    protocol = usb_dev.protocol or "MediaTek USB (PyUSB Direct)"
                elif usb_dev.mode == "FASTBOOT":
                    device_mode = DeviceMode.FASTBOOT
                    protocol = usb_dev.protocol or "Fastboot via USB Direct"
                elif usb_dev.mode == "NORMAL":
                    device_mode = DeviceMode.NORMAL
                    protocol = usb_dev.protocol or "Protocole AT / Modem MTK"
                else:
                    device_mode = DeviceMode.USB_NORMAL
                    protocol = usb_dev.protocol or "Périphérique USB MediaTek"

                # Identifiant stable unique (bus:addr ou serial si disponible)
                identifier = usb_dev.identifier

                connected = ConnectedDevice(
                    mode=device_mode,
                    identifier=identifier,
                    port=None,       # Pas de port COM en détection USB directe
                    serial_number=usb_dev.serial_number or None,
                    description=usb_dev.description,
                    vid=usb_dev.vid,
                    pid=usb_dev.pid,
                    manufacturer=usb_dev.manufacturer,
                    hwid=f"USB\\VID_{usb_dev.vid:04X}&PID_{usb_dev.pid:04X}",
                    protocol=protocol,
                    details={
                        "vid": usb_dev.vid,
                        "pid": usb_dev.pid,
                        "bus": usb_dev.bus,
                        "address": usb_dev.address,
                        "source": "pyusb_direct",
                        "type": usb_dev.mode,
                    }
                )
                results.append(connected)

                # Log informatif (une seule fois par détection nouvelle, pas en boucle)
                mode_lbl = {
                    DeviceMode.BROM: "BROM/Preloader",
                    DeviceMode.NORMAL: "Normal/AT",
                    DeviceMode.FASTBOOT: "Fastboot",
                    DeviceMode.USB_NORMAL: "USB Normal",
                }.get(device_mode, device_mode.value)
                self.log_message.emit(
                    f"[PyUSB] Périphérique MediaTek détecté — {usb_dev.vid_pid_str} "
                    f"mode {mode_lbl} ({usb_dev.description})",
                    "info"
                )

            except Exception:
                continue

        return results

    # -----------------------------------------------------------------
    # 1. Détection Ports COM / USB (MediaTek BROM, Preloader, AT)
    # -----------------------------------------------------------------
    def _scan_com_ports(self) -> List[ConnectedDevice]:
        """
        Inspecte les ports COM disponibles STRICTEMENT via serial.tools.list_ports.comports().

        RÈGLE ABSOLUE DE SÉCURITÉ MATÉRIELLE (Spécification d'Atelier) :
        Il est formellement INTERDIT d'instancier serial.Serial() ou d'ouvrir
        un port en lecture/écriture pendant la phase de scan/détection en arrière-plan.
        L'ouverture d'un port série BROM/Preloader le verrouille immédiatement
        et bloque tout le système ou les opérations ultérieures de flash/FRP.
        On lit EXCLUSIVEMENT les attributs passifs (port_info.device, description, hwid, vid, pid).
        """
        detected = []
        if not HAS_SERIAL:
            return detected

        try:
            # Inspection 100% passive via les descripteurs matériels Windows SetupAPI / Registry
            for p in list_ports.comports():
                dev = self._classify_com_port(p)
                if dev:
                    detected.append(dev)
        except Exception:
            # Évite d'interrompre la boucle de détection en cas d'erreur ponctuelle d'accès USB
            pass

        return detected

    def _classify_com_port(self, port_info) -> Optional[ConnectedDevice]:
        """Classifie un port COM en BROM, Preloader ou Normal/AT."""
        port_name = port_info.device or ""
        desc = (port_info.description or "").strip()
        hwid = (port_info.hwid or "").strip()
        vid = port_info.vid
        pid = port_info.pid
        mfg = port_info.manufacturer or ""

        desc_upper = desc.upper()
        hwid_upper = hwid.upper()

        is_mtk_vendor = (vid in MTK_VENDORS)
        has_mtk_keywords = any(k in desc_upper or k in hwid_upper for k in ["MEDIATEK", "MTK"])

        if not (is_mtk_vendor or has_mtk_keywords):
            return None

        # Mode BROM ou Preloader
        is_explicit_brom = (pid in MTK_BROM_PIDS) or any(k in desc_upper or k in hwid_upper for k in KEYWORDS_BROM)
        is_explicit_preloader = (pid in MTK_PRELOADER_PIDS) or ("PRELOADER" in desc_upper or "PRELOADER" in hwid_upper)

        if is_explicit_brom:
            protocol = "MediaTek BootROM (BROM Direct Download)"
            if pid == 0x0003:
                protocol = "MediaTek MTK USB Port (BootROM VCOM)"
            return ConnectedDevice(
                mode=DeviceMode.BROM,
                identifier=port_name,
                port=port_name,
                description=desc or "MediaTek BootROM VCOM",
                vid=vid,
                pid=pid,
                manufacturer=mfg,
                hwid=hwid,
                protocol=protocol,
                details={"vid": vid, "pid": pid, "type": "BROM"}
            )

        if is_explicit_preloader:
            return ConnectedDevice(
                mode=DeviceMode.BROM,
                identifier=port_name,
                port=port_name,
                description=desc or "MediaTek Preloader VCOM",
                vid=vid,
                pid=pid,
                manufacturer=mfg,
                hwid=hwid,
                protocol="MediaTek Preloader USB VCOM",
                details={"vid": vid, "pid": pid, "type": "Preloader"}
            )

        # Mode Normal / AT / Modem
        is_normal = (pid in MTK_NORMAL_PIDS) or any(k in desc_upper or k in hwid_upper for k in KEYWORDS_NORMAL)
        if is_normal:
            return ConnectedDevice(
                mode=DeviceMode.NORMAL,
                identifier=port_name,
                port=port_name,
                description=desc or "Port Modem / AT MediaTek",
                vid=vid,
                pid=pid,
                manufacturer=mfg,
                hwid=hwid,
                protocol="Protocole AT / Commandes Série",
                details={"vid": vid, "pid": pid, "type": "AT"}
            )

        # Par défaut pour un VID 0x0E8D non filtré : considéré comme BROM/Preloader
        if is_mtk_vendor:
            return ConnectedDevice(
                mode=DeviceMode.BROM,
                identifier=port_name,
                port=port_name,
                description=desc or "Périphérique VCOM MediaTek",
                vid=vid,
                pid=pid,
                manufacturer=mfg,
                hwid=hwid,
                protocol="MediaTek USB VCOM",
                details={"vid": vid, "pid": pid, "type": "Generic_MTK"}
            )

        return None

    # -----------------------------------------------------------------
    # 2. Détection Fastboot ('fastboot devices')
    # -----------------------------------------------------------------
    def _execute_fastboot_devices(self) -> Optional[str]:
        """
        Exécute 'fastboot devices' de façon robuste selon les spécifications :
        - subprocess.run([fb_bin, "devices"], capture_output=True, text=True, timeout=2)
        - Évite le blocage indéfini si le service ne répond pas
        - Masque la fenêtre cmd console sous Windows (CREATE_NO_WINDOW / SW_HIDE)
        - Capture proprement FileNotFoundError, TimeoutExpired, etc.
        """
        fb_bin = self._find_fastboot_executable() or "fastboot"
        cmd = [fb_bin, "devices"]

        creationflags = 0
        startupinfo = None
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
            startupinfo.wShowWindow = 0  # SW_HIDE

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=creationflags,
                startupinfo=startupinfo
            )
            if res.stdout:
                return res.stdout
            if res.returncode == 0:
                return res.stdout or ""
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
            return None
        except Exception:
            return None

    def _scan_fastboot(self) -> Optional[ConnectedDevice]:
        """Exécute 'fastboot devices' sans bloquer l'UI et sans pop-up de console cmd."""
        try:
            output = self._execute_fastboot_devices()
            if not output:
                return None

            # Format typique de la sortie :
            # 0123456789ABCDEF\tfastboot
            # ou 0123456789ABCDEF fastboot
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[1].lower() == "fastboot":
                    serial = parts[0]
                    return ConnectedDevice(
                        mode=DeviceMode.FASTBOOT,
                        identifier=f"FASTBOOT:{serial}",
                        port=None,
                        serial_number=serial,
                        description=f"Appareil Android Fastboot ({serial})",
                        protocol="Protocole Fastboot Bootloader",
                        details={"serial": serial, "fastboot": True}
                    )
            return None
        except Exception:
            return None

    # -----------------------------------------------------------------
    # 3. Détection ADB — distingue "actif" et "non autorisé / USB Normal"
    # -----------------------------------------------------------------
    def _execute_adb_devices(self) -> Optional[str]:
        """
        Exécute 'adb devices' de façon robuste selon les spécifications :
        - subprocess.run([get_adb_path(), "devices"], capture_output=True, text=True, timeout=2)
        - Évite le blocage indéfini si le serveur ADB ne répond pas
        - Masque la fenêtre cmd console sous Windows (CREATE_NO_WINDOW / SW_HIDE)
        - Capture proprement FileNotFoundError, TimeoutExpired, etc.
        """
        adb_bin = get_adb_path()
        cmd = [adb_bin, "devices"]

        creationflags = 0
        startupinfo = None
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
            startupinfo.wShowWindow = 0  # SW_HIDE

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=creationflags,
                startupinfo=startupinfo
            )
            # Vérifier stdout en priorité (contient la liste des devices)
            if res.stdout:
                return res.stdout
            if res.returncode == 0:
                return res.stdout or ""
            return None
        except FileNotFoundError:
            # ADB non installé ou introuvable dans PATH / tools
            return None
        except subprocess.TimeoutExpired:
            # ADB serveur bloqué ou ne répondant pas dans les 2 secondes
            return None
        except (PermissionError, OSError):
            return None
        except Exception:
            return None

    def _scan_adb_detailed(self) -> Tuple[Optional[ConnectedDevice], Optional[ConnectedDevice]]:
        """
        Interroge 'adb devices' et retourne un tuple (adb_device, usb_normal_device).

        - Si l'appareil répond en état 'device', 'recovery' ou 'sideload' :
            → ADB actif (🟢 "Connecté en mode ADB (Débogage actif)")
        - Si l'appareil répond en état 'unauthorized', 'offline' ou 'authorizing' :
            → USB Normal (🟡 "Appareil branché (Mode Normal / Non sécurisé pour les opérations de flash/FRP)")
        - Si aucune réponse valide :
            → (None, None)

        Règle d'or : On ne déclare JAMAIS "ADB actif" si ADB ne répond pas réellement.
        """
        try:
            output = self._execute_adb_devices()
            if not output:
                return None, None

            lines = [line.strip() for line in output.splitlines() if line.strip()]
            header_found = False

            for line in lines:
                # Ignorer les messages de démarrage daemon
                if line.startswith("*") or "daemon" in line.lower():
                    continue

                if "list of devices attached" in line.lower():
                    header_found = True
                    continue

                if not header_found and "attached" not in line.lower():
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                serial = parts[0]
                state = parts[1].lower()

                # Extraction d'attributs supplémentaires si présents (ex: model)
                product_name = ""
                for part in parts[2:]:
                    if part.startswith("model:"):
                        product_name = part.split(":", 1)[1].replace("_", " ")

                if state in ("device", "recovery", "sideload"):
                    # ── ADB actif et confirmé (débogage USB autorisé) ──────
                    desc = f"Smartphone Android ({product_name})" if product_name else f"Appareil Android ({serial})"
                    return ConnectedDevice(
                        mode=DeviceMode.ADB,
                        identifier=f"ADB:{serial}",
                        port=None,
                        serial_number=serial,
                        description=desc,
                        protocol=f"ADB Interface ({state})",
                        details={
                            "serial": serial,
                            "adb_state": state,
                            "product_name": product_name or "Smartphone Android"
                        }
                    ), None

                elif state in ("unauthorized", "offline", "authorizing"):
                    # ── USB branché, débogage non autorisé / désactivé ──────
                    # → Traité comme USB Normal (🟡), jamais comme ADB actif
                    desc = f"Appareil Android ({serial}) — Débogage non autorisé"
                    return None, ConnectedDevice(
                        mode=DeviceMode.USB_NORMAL,
                        identifier=f"USB:{serial}",
                        port=None,
                        serial_number=serial,
                        description=desc,
                        protocol="USB Standard (débogage non autorisé)",
                        details={
                            "serial": serial,
                            "adb_state": state,
                            "product_name": product_name
                        }
                    )

            return None, None
        except Exception:
            return None, None

    def _scan_adb(self) -> Optional[ConnectedDevice]:
        """
        Compatibilité rétrograde : retourne uniquement l'appareil ADB actif (pas USB_NORMAL).
        Utilisé par JITConnectionWorker._scan_all_candidates via l'ancien chemin.
        """
        adb_dev, _ = self._scan_adb_detailed()
        return adb_dev

    # -----------------------------------------------------------------
    # Exécution silencieuse sous Windows (sans fenêtre noire cmd)
    # -----------------------------------------------------------------
    def _run_command_silent(self, cmd: List[str], timeout: float = 2.0) -> Optional[str]:
        """Lance une commande externe de manière totalement transparente avec timeout strict."""
        creationflags = 0
        startupinfo = None

        if sys.platform == "win32":
            # Empêche l'apparition furtive d'une fenêtre console
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
            startupinfo.wShowWindow = 0  # SW_HIDE

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creationflags,
                startupinfo=startupinfo
            )
            if res.returncode == 0:
                return res.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError):
            return None
        except Exception:
            return None

        return None

    # -----------------------------------------------------------------
    # Gestion des notifications et logs propres
    # -----------------------------------------------------------------
    def _notify_detected(self, device: ConnectedDevice):
        """Notifie l'interface et produit un log propre lors du branchement."""
        self.device_detected.emit(device)
        self.device_changed.emit(device)

        # Construction d'un message de log propre et précis selon le mode
        if device.mode == DeviceMode.BROM:
            info_parts = []
            if device.vid and device.pid:
                info_parts.append(f"VID: 0x{device.vid:04X}, PID: 0x{device.pid:04X}")
            if device.protocol:
                info_parts.append(device.protocol)
            extra = f" ({' | '.join(info_parts)})" if info_parts else ""
            msg = f"Appareil MediaTek détecté sur {device.port} en mode BROM{extra}"
            self.log_message.emit(msg, "info")

        elif device.mode == DeviceMode.FASTBOOT:
            serial = device.serial_number or "Inconnu"
            msg = f"Appareil détecté en mode Fastboot (N° série : {serial})"
            self.log_message.emit(msg, "info")

        elif device.mode == DeviceMode.ADB:
            serial = device.serial_number or "Inconnu"
            state = device.details.get("adb_state", "device")
            msg = f"Appareil connecté en mode ADB — Débogage actif (Série : {serial}, État : {state})"
            self.log_message.emit(msg, "success")

        elif device.mode == DeviceMode.USB_NORMAL:
            serial = device.serial_number or device.identifier
            msg = (
                f"Appareil branché en mode Normal ({serial}) — "
                "ADB non actif. Pour le FRP/Flash, éteignez l'appareil et suivez l'assistant."
            )
            self.log_message.emit(msg, "warning")

        elif device.mode == DeviceMode.NORMAL:
            loc = device.port or device.serial_number or device.identifier
            proto = device.protocol or "Interface Standard"
            msg = f"Appareil MediaTek détecté sur {loc} en mode Normal/AT ({proto})"
            self.log_message.emit(msg, "info")

    def _notify_lost(self, device: ConnectedDevice):
        """Notifie l'interface et produit un log propre lors du débranchement."""
        self.device_lost.emit(device)
        self.device_changed.emit(None)

        loc = device.port or device.serial_number or device.identifier
        msg = f"Appareil déconnecté ({loc} - Mode {device.mode.value})"
        self.log_message.emit(msg, "warning")

    def _emit_status_update(self, device: Optional[ConnectedDevice]):
        """Transmet les informations formatées pour le badge de statut dans l'UI."""
        if device is None:
            self.status_updated.emit(
                DeviceMode.NONE.value,
                "Aucun appareil détecté",
                "Surveillance continue active (BROM, Fastboot, ADB)…",
                "#e74c3c"
            )
        else:
            # Utilise la couleur propre au mode (vert, jaune, etc.)
            self.status_updated.emit(
                device.mode.value,
                device.badge_title,
                device.badge_subtitle,
                device.color
            )

    # -----------------------------------------------------------------
    # Méthodes publiques de consultation
    # -----------------------------------------------------------------
    def get_current_device(self) -> Optional[ConnectedDevice]:
        """Retourne l'appareil actuellement connecté ou None."""
        return self._current_device

    def is_device_connected(self) -> bool:
        """Indique si un appareil est actuellement présent."""
        return self._current_device is not None


# =====================================================================
# Écoute active temporaire (Just-In-Time / Assistant d'action)
# =====================================================================

class JITConnectionWorker(QThread):
    """
    Worker d'écoute active temporaire (Just-In-Time) pour l'assistant d'instructions.
    Surveille à haute fréquence (250ms) l'apparition d'un appareil dès l'ouverture
    de la boîte de dialogue, et s'arrête immédiatement dès détection ou timeout.
    """
    device_found = pyqtSignal(object)       # ConnectedDevice
    timeout_reached = pyqtSignal()          # Emis à l'expiration du délai max
    tick = pyqtSignal(int)                  # Secondes restantes (60..0)
    cancelled = pyqtSignal()                # Emis en cas d'annulation

    def __init__(self, target_modes: Optional[List[DeviceMode]] = None,
                 timeout_seconds: int = 60, poll_interval: float = 0.25, parent=None):
        super().__init__(parent)
        self.target_modes = target_modes or [DeviceMode.BROM, DeviceMode.FASTBOOT, DeviceMode.ADB, DeviceMode.NORMAL]
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self._running = False
        self._helper = DeviceDetector(interval=self.poll_interval)

    def stop(self):
        """Arrête immédiatement l'écoute active."""
        self._running = False
        self.wait(1000)

    def run(self):
        self._running = True
        start_time = time.time()
        last_remaining = self.timeout_seconds
        self.tick.emit(last_remaining)

        while self._running:
            # Calcul du temps restant
            elapsed = time.time() - start_time
            remaining = max(0, int(self.timeout_seconds - elapsed))

            if remaining != last_remaining:
                last_remaining = remaining
                self.tick.emit(remaining)

            if elapsed >= self.timeout_seconds:
                self.timeout_reached.emit()
                break

            # Scan haute fréquence
            try:
                candidates = self._helper._scan_all_candidates()
                if candidates:
                    valid = [d for d in candidates if d.mode in self.target_modes]
                    if valid:
                        # Appareil détecté !
                        self.device_found.emit(valid[0])
                        break
            except Exception:
                pass

            # Micro-sommeil pour arrêt instantané dès le clic sur Annuler
            steps = int(max(1, self.poll_interval * 20))
            for _ in range(steps):
                if not self._running:
                    break
                self.msleep(50)

