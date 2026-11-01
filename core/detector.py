# -*- coding: utf-8 -*-
"""
Module de détection automatique et en temps réel des périphériques pour Optima MTK Tool.
Surveille en arrière-plan (QThread non bloquant) les modes :
  - BROM / BootROM (MediaTek VCOM, Preloader, DA USB)
  - Fastboot (USB Fastboot Bootloader via 'fastboot devices')
  - Normal / AT (Ports AT/Modem MediaTek et USB Debug ADB)
"""

import os
import sys
import time
import shutil
import subprocess
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from PyQt5.QtCore import QThread, pyqtSignal

try:
    import serial.tools.list_ports as list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


# =====================================================================
# Modèles de données
# =====================================================================

class DeviceMode(str, Enum):
    """Modes de fonctionnement des appareils détectés."""
    NONE = "NONE"
    BROM = "BROM"                # BootROM matériel / Preloader MediaTek
    FASTBOOT = "FASTBOOT"        # Fastboot bootloader Android
    NORMAL = "NORMAL"            # Mode Normal / AT Modem / ADB Android


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
        return self.mode == DeviceMode.NORMAL

    @property
    def mode_display(self) -> str:
        if self.mode == DeviceMode.BROM:
            return "BROM / Preloader"
        elif self.mode == DeviceMode.FASTBOOT:
            return "Fastboot"
        elif self.mode == DeviceMode.NORMAL:
            return "Normal / AT"
        return "Aucun"

    @property
    def color(self) -> str:
        """Couleur hex associée au mode."""
        if self.mode == DeviceMode.BROM:
            return "#2ecc71"        # Vert émeraude (MTK Flash/BROM prêt)
        elif self.mode == DeviceMode.FASTBOOT:
            return "#00c3ff"        # Bleu cyan vif (Fastboot)
        elif self.mode == DeviceMode.NORMAL:
            return "#a29bfe"        # Violet / Mauve (Normal / Modem AT)
        return "#8a92a8"            # Gris (En attente)

    @property
    def badge_title(self) -> str:
        """Titre compact pour affichage dans l'en-tête."""
        if self.mode == DeviceMode.BROM:
            return f"Appareil détecté en mode BROM ({self.port or self.identifier})"
        elif self.mode == DeviceMode.FASTBOOT:
            return f"Appareil détecté en mode Fastboot ({self.serial_number or self.identifier})"
        elif self.mode == DeviceMode.NORMAL:
            return f"Appareil détecté en mode Normal/AT ({self.port or self.identifier})"
        return "En attente de connexion..."

    @property
    def badge_subtitle(self) -> str:
        """Détail technique sous le titre de badge."""
        if self.mode == DeviceMode.BROM:
            vid_pid = f"VID:{self.vid:04X} PID:{self.pid:04X}" if self.vid and self.pid else "MediaTek VCOM"
            return f"{self.protocol or 'MediaTek BootROM'} • {vid_pid}"
        elif self.mode == DeviceMode.FASTBOOT:
            return f"Protocole Fastboot • Série : {self.serial_number or 'Inconnu'}"
        elif self.mode == DeviceMode.NORMAL:
            target = self.port or self.serial_number or self.identifier
            return f"{self.protocol or 'Modem AT / Interface'} • {target}"
        return "Surveillance active (BROM, Fastboot, Normal)"


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
        self._fastboot_bin = self._find_fastboot_executable()
        self._adb_bin = self._find_adb_executable()

    # -----------------------------------------------------------------
    # Localisation des binaires utilitaires (fastboot, adb)
    # -----------------------------------------------------------------
    def _find_fastboot_executable(self) -> Optional[str]:
        """Localise l'exécutable fastboot dans PATH ou dans les dossiers du projet."""
        found = shutil.which("fastboot")
        if found:
            return found

        # Chemins relatifs possibles
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base_dir, "platform-tools", "fastboot.exe"),
            os.path.join(base_dir, "tools", "fastboot.exe"),
            os.path.join(base_dir, "assets", "bin", "fastboot.exe"),
            os.path.join(base_dir, "bin", "fastboot.exe"),
        ]

        # Chemins standards Android SDK sous Windows
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidates.append(os.path.join(local_app_data, "Android", "Sdk", "platform-tools", "fastboot.exe"))

        for path in candidates:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return "fastboot"  # Fallback sur la commande système

    def _find_adb_executable(self) -> Optional[str]:
        """Localise l'exécutable adb pour détection complémentaire en mode Normal."""
        found = shutil.which("adb")
        if found:
            return found

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base_dir, "platform-tools", "adb.exe"),
            os.path.join(base_dir, "tools", "adb.exe"),
            os.path.join(base_dir, "assets", "bin", "adb.exe"),
        ]

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidates.append(os.path.join(local_app_data, "Android", "Sdk", "platform-tools", "adb.exe"))

        for path in candidates:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return "adb"

    # -----------------------------------------------------------------
    # Cycle de vie du thread
    # -----------------------------------------------------------------
    def start_monitoring(self):
        """Démarre le thread de surveillance en continu."""
        if self.isRunning():
            return
        self._running = True
        self.start()
        self.log_message.emit("Service de détection automatique USB démarré (BROM / Fastboot / Normal).", "info")

    def stop_monitoring(self):
        """Arrête le thread proprement."""
        self._running = False
        self.wait(2000)

    def scan_now(self):
        """Force une analyse immédiate sans attendre l'intervalle."""
        self._perform_scan()

    def run(self):
        """Boucle de surveillance d'arrière-plan."""
        self._running = True
        while self._running:
            try:
                self._perform_scan()
            except Exception as e:
                self.log_message.emit(f"Erreur lors de la détection automatique : {str(e)}", "error")

            # Sommeil par micro-intervalles pour arrêt immédiat lors de la fermeture
            steps = int(self._interval * 10)
            for _ in range(max(1, steps)):
                if not self._running:
                    break
                self.msleep(100)

    # -----------------------------------------------------------------
    # Logique d'analyse des périphériques
    # -----------------------------------------------------------------
    def _perform_scan(self):
        """Scanne les ports COM et Fastboot, puis met à jour l'état si changement."""
        devices = self._scan_all_candidates()

        # Sélection de l'appareil prioritaire : BROM > FASTBOOT > NORMAL
        detected: Optional[ConnectedDevice] = None
        if devices:
            priority_order = {DeviceMode.BROM: 1, DeviceMode.FASTBOOT: 2, DeviceMode.NORMAL: 3}
            devices.sort(key=lambda d: priority_order.get(d.mode, 99))
            detected = devices[0]

        # Comparaison avec l'état précédent
        old = self._current_device

        if detected is None and old is not None:
            # Périphérique déconnecté
            self._current_device = None
            self._notify_lost(old)
            self._emit_status_update(None)

        elif detected is not None and old is None:
            # Nouveau périphérique connecté
            self._current_device = detected
            self._notify_detected(detected)
            self._emit_status_update(detected)

        elif detected is not None and old is not None:
            # Vérifier si l'appareil ou le mode a changé
            if (detected.identifier != old.identifier) or (detected.mode != old.mode):
                self._current_device = detected
                self._notify_lost(old)
                self._notify_detected(detected)
                self._emit_status_update(detected)

    def _scan_all_candidates(self) -> List[ConnectedDevice]:
        """Collecte l'ensemble des périphériques détectés."""
        results: List[ConnectedDevice] = []

        # 1. Analyse des ports COM (BROM, Preloader, Normal/AT)
        com_devices = self._scan_com_ports()
        results.extend(com_devices)

        # 2. Analyse Fastboot (via commande 'fastboot devices')
        fastboot_dev = self._scan_fastboot()
        if fastboot_dev:
            results.append(fastboot_dev)

        # 3. Analyse ADB si aucun Fastboot ni BROM n'est présent (mode Normal d'appoint)
        if not results:
            adb_dev = self._scan_adb()
            if adb_dev:
                results.append(adb_dev)

        return results

    # -----------------------------------------------------------------
    # 1. Détection Ports COM / USB (MediaTek BROM, Preloader, AT)
    # -----------------------------------------------------------------
    def _scan_com_ports(self) -> List[ConnectedDevice]:
        """Inspecte les ports COM disponibles via serial.tools.list_ports."""
        detected = []
        if not HAS_SERIAL:
            return detected

        try:
            for p in list_ports.comports():
                dev = self._classify_com_port(p)
                if dev:
                    detected.append(dev)
        except Exception as e:
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
    def _scan_fastboot(self) -> Optional[ConnectedDevice]:
        """Exécute 'fastboot devices' sans bloquer l'UI et sans pop-up de console cmd."""
        if not self._fastboot_bin:
            return None

        cmd = [self._fastboot_bin, "devices"]
        output = self._run_command_silent(cmd, timeout=0.8)
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

    # -----------------------------------------------------------------
    # 3. Détection ADB (Appareil allumé en mode Normal)
    # -----------------------------------------------------------------
    def _scan_adb(self) -> Optional[ConnectedDevice]:
        """Vérifie si un appareil est joignable via adb devices (Mode Normal)."""
        if not self._adb_bin:
            return None

        cmd = [self._adb_bin, "devices"]
        output = self._run_command_silent(cmd, timeout=0.8)
        if not output:
            return None

        lines = [line.strip() for line in output.splitlines() if line.strip()]
        for line in lines[1:]:  # Ignorer la ligne 'List of devices attached'
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() in ("device", "recovery", "unauthorized"):
                serial = parts[0]
                state = parts[1].lower()
                return ConnectedDevice(
                    mode=DeviceMode.NORMAL,
                    identifier=f"ADB:{serial}",
                    port=None,
                    serial_number=serial,
                    description=f"Appareil Android Normal/ADB ({serial})",
                    protocol=f"ADB Interface ({state})",
                    details={"serial": serial, "adb_state": state}
                )

        return None

    # -----------------------------------------------------------------
    # Exécution silencieuse sous Windows (sans fenêtre noire cmd)
    # -----------------------------------------------------------------
    def _run_command_silent(self, cmd: List[str], timeout: float = 1.0) -> Optional[str]:
        """Lance une commande externe de manière totalement transparente."""
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
                "En attente de connexion...",
                "Surveillance active (BROM, Fastboot, Normal)",
                "#8a92a8"
            )
        else:
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
        self.target_modes = target_modes or [DeviceMode.BROM, DeviceMode.FASTBOOT, DeviceMode.NORMAL]
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

