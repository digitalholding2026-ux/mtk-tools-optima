# -*- coding: utf-8 -*-
"""
core/usb_scanner.py — Détection USB bas-niveau via PyUSB / libusb pour Optima MTK Tool.

Avantages par rapport à la détection via ports COM :
  - Intercept les périphériques MediaTek (VID 0x0E8D) AVANT que Windows attribue
    un port COM virtuel — critique pour la fenêtre BROM (~2–4s).
  - Fonctionne même si aucun pilote COM n'est installé (libusb est class-agnostic).
  - Lecture passive : aucun port ouvert, aucun verrou hardware.
  - Détecte tout périphérique USB par son Vendor ID / Product ID brut.

Architecture :
  - UsbScanner  : classe de scan PyUSB avec initialisation de backend libusb autonome.
  - scan_mtk_devices() : fonction de commodité utilisée par DeviceDetector.
  - _get_libusb_backend() : résolution du backend libusb (bundlé tools/ → pip → système).

Compatibilité :
  - Windows : libusb-1.0.dll dans tools/ (livré avec Optima MTK Tool).
  - Linux / macOS : libusb disponible via le gestionnaire de paquets système.
  - Pas de pyusb → dégradation propre (HAS_PYUSB = False), sans crash.

Note sur les pilotes Windows :
  Pour que libusb puisse accéder à un périphérique USB sous Windows, le pilote
  WinUSB, libusb-win32 ou libusbK doit être installé via Zadig pour le périphérique
  cible (MTK BROM, Preloader). Pour les périphériques ADB/Fastboot, les pilotes
  Android standard suffisent. La détection pyserial (COM) reste le chemin de secours.
"""

import os
import sys
import ctypes
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Disponibilité de PyUSB ───────────────────────────────────────────────────

HAS_PYUSB = False
_usb_core = None
_usb_util = None
_usb_backend_libusb1 = None

try:
    import usb.core as _usb_core
    import usb.util as _usb_util
    import usb.backend.libusb1 as _usb_backend_libusb1
    HAS_PYUSB = True
except ImportError:
    pass


# ─── Tables d'identifiants matériels MediaTek ────────────────────────────────

# VID MediaTek et partenaires OEM utilisant des chipsets MTK
MTK_VENDOR_IDS = {
    0x0E8D: "MediaTek Inc.",
    0x0489: "Foxconn / MTK Module",
    0x2717: "Xiaomi / MTK Preloader",
    0x2A70: "OnePlus / Oppo MTK",
}

# PID → (mode, protocole) pour les VID reconnus comme MediaTek
MTK_PRODUCT_MAP = {
    # ── BootROM Hardware (BROM Direct) ──
    0x0003: ("BROM",       "MediaTek MTK USB Port (BootROM VCOM — Accès direct DA)"),
    0x0001: ("BROM",       "MediaTek USB Port (BootROM alternatif)"),
    0x0002: ("BROM",       "MediaTek Download Port (BootROM)"),
    # ── Preloader (chargeur secondaire) ──
    0x2000: ("BROM",       "MediaTek DA USB VCOM (Preloader MTK)"),
    0x2001: ("BROM",       "MediaTek USB VCOM Android (Preloader)"),
    0x2002: ("BROM",       "MediaTek USB Port (Preloader Stage-2)"),
    # ── Modes opérationnels (téléphone allumé) ──
    0x2006: ("NORMAL",     "MTK USB Modem"),
    0x2007: ("NORMAL",     "MTK AT Command Port"),
    0x2008: ("NORMAL",     "MTK Debug / COM Port"),
    0x200E: ("NORMAL",     "MTK CDC Serial"),
    0x201D: ("NORMAL",     "MTK Android Modem"),
    0x201F: ("NORMAL",     "MTK Dual COM Interface"),
    0x202D: ("NORMAL",     "MTK Engineering Mode Port"),
    # ── Modes Android génériques (avec pilote ADB/Fastboot) ──
    0x2005: ("USB_NORMAL", "MTK Android Composite"),
    0x200A: ("USB_NORMAL", "MTK MTP / File Transfer"),
    0x0C03: ("FASTBOOT",   "MTK Fastboot / Download Mode"),
}

# VID des téléphones Android non-MTK mais communs en atelier (pour log seulement)
ANDROID_VENDOR_IDS = {
    0x04E8: "Samsung",
    0x2916: "Samsung (Kies)",
    0x18D1: "Google / Pixel / AOSP",
    0x1004: "LG Electronics",
    0x0BB4: "HTC",
    0x12D1: "Huawei",
    0x05C6: "Qualcomm / Snapdragon",
    0x1EBF: "Tecno / Transsion",
    0x1D45: "Infinix / Transsion",
    0x201E: "Itel / Transsion",
    0x22D9: "Oppo / Realme / OnePlus",
    0x2D95: "Vivo / iQOO",
    0x22B8: "Motorola",
    0x2E04: "Nothing Phone",
}


# ─── Résolution du backend libusb ────────────────────────────────────────────

def _get_libusb_backend():
    """
    Résout le backend libusb via le module central d'initialisation (core.init_env).
    Garantit une encapsulation autonome (bin/ ou tools/ -> libusb-package -> système).
    """
    if not HAS_PYUSB:
        return None

    try:
        from core.init_env import get_libusb_backend
        backend = get_libusb_backend()
        if backend is not None:
            return backend
    except Exception as exc:
        logger.debug(f"[USB-SCANNER] Délégation init_env a échoué ({exc}), passage au secours local")

    # ── 1. DLL embarquée dans bin/ ──────────────────────────────────────────
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for candidate in [
        os.path.join(project_root, "bin", "x64", "libusb-1.0.dll"),
        os.path.join(project_root, "bin", "libusb-1.0.dll"),
    ]:
        if os.path.isfile(candidate):
            try:
                backend = _usb_backend_libusb1.get_backend(find_library=lambda x: candidate)
                if backend is not None:
                    logger.debug(f"[USB-SCANNER] Backend libusb : DLL embarquée ({candidate})")
                    return backend
            except Exception as exc:
                logger.debug(f"[USB-SCANNER] DLL embarquée inutilisable ({candidate}) : {exc}")

    # ── 2. libusb-package (pip install libusb-package) ────────────────────────
    try:
        import libusb_package
        backend = libusb_package.get_libusb1_backend()
        if backend is not None:
            logger.debug("[USB-SCANNER] Backend libusb : libusb-package (pip)")
            return backend
    except (ImportError, Exception):
        pass

    # ── 3. Auto-découverte PyUSB (PATH système) ───────────────────────────────
    try:
        backend = _usb_backend_libusb1.get_backend()
        if backend is not None:
            logger.debug("[USB-SCANNER] Backend libusb : auto-découverte système")
            return backend
    except Exception:
        pass

    logger.warning(
        "[USB-SCANNER] Aucun backend libusb disponible. "
        "Installez libusb-package (pip install libusb-package) ou "
        "placez libusb-1.0.dll dans le dossier tools/."
    )
    return None


# ─── Structures de résultat ──────────────────────────────────────────────────

class UsbDeviceInfo:
    """Représentation légère d'un périphérique USB détecté par PyUSB."""

    __slots__ = (
        "vid", "pid", "serial_number", "manufacturer",
        "product", "bus", "address",
        "mode", "protocol", "description",
        "is_mtk", "vendor_name",
    )

    def __init__(
        self,
        vid: int,
        pid: int,
        serial_number: str = "",
        manufacturer: str = "",
        product: str = "",
        bus: int = 0,
        address: int = 0,
        mode: str = "UNKNOWN",
        protocol: str = "",
        description: str = "",
        is_mtk: bool = False,
        vendor_name: str = "",
    ):
        self.vid = vid
        self.pid = pid
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.product = product
        self.bus = bus
        self.address = address
        self.mode = mode
        self.protocol = protocol
        self.description = description
        self.is_mtk = is_mtk
        self.vendor_name = vendor_name

    def __repr__(self) -> str:
        return (
            f"UsbDeviceInfo(VID={self.vid:04X} PID={self.pid:04X} "
            f"mode={self.mode} sn={self.serial_number!r} desc={self.description!r})"
        )

    @property
    def vid_pid_str(self) -> str:
        return f"VID:0x{self.vid:04X} PID:0x{self.pid:04X}"

    @property
    def identifier(self) -> str:
        """Identifiant unique stable pour comparaison d'état."""
        if self.serial_number:
            return f"USB:{self.vid:04X}:{self.pid:04X}:{self.serial_number}"
        return f"USB:{self.vid:04X}:{self.pid:04X}:{self.bus}:{self.address}"


# ─── Classe principale de scan ────────────────────────────────────────────────

class UsbScanner:
    """
    Scanner USB bas-niveau via PyUSB / libusb.

    Méthode principale : scan_mtk_devices() → List[UsbDeviceInfo]
    Méthode secondaire : scan_all_devices()  → List[UsbDeviceInfo]

    Utilisation par DeviceDetector :
        scanner = UsbScanner()
        mtk_devices = scanner.scan_mtk_devices()

    Le scanner est thread-safe pour les opérations de lecture.
    Il ne maintient AUCUN handle ouvert entre les scans (pas de verrou hardware).
    """

    def __init__(self):
        self._backend = _get_libusb_backend()
        self._available = (HAS_PYUSB and self._backend is not None)

    @property
    def is_available(self) -> bool:
        """True si PyUSB + libusb sont opérationnels."""
        return self._available

    def _read_string_descriptor(self, device, index: int, default: str = "") -> str:
        """
        Lit un descripteur de chaîne USB en toute sécurité.
        Certains périphériques (BROM, bootloaders) refusent les requêtes GET_DESCRIPTOR
        en milieu d'initialisation — on retourne la valeur par défaut sans lever d'exception.
        """
        if not index:
            return default
        try:
            return _usb_util.get_string(device, index, langid=0x0409)  # 0x0409 = English US
        except Exception:
            return default

    def _classify_usb_device(self, device) -> Optional[UsbDeviceInfo]:
        """
        Classifie un périphérique USB brut (objet usb.core.Device) en UsbDeviceInfo.

        Retourne None si le périphérique n'est ni MediaTek ni un Android reconnu.
        """
        try:
            vid = device.idVendor
            pid = device.idProduct
            bus = device.bus
            address = device.address
        except Exception:
            return None

        is_mtk = vid in MTK_VENDOR_IDS
        is_android = vid in ANDROID_VENDOR_IDS
        vendor_name = MTK_VENDOR_IDS.get(vid, ANDROID_VENDOR_IDS.get(vid, ""))

        if not is_mtk and not is_android:
            return None  # Hors périmètre — on ignore les périphériques non-téléphonie

        # Lecture sécurisée des descripteurs de chaînes
        manufacturer = self._read_string_descriptor(device, getattr(device, "iManufacturer", 0))
        product_str   = self._read_string_descriptor(device, getattr(device, "iProduct", 0))
        serial_number = self._read_string_descriptor(device, getattr(device, "iSerialNumber", 0))

        # Classification par PID et VID
        if is_mtk:
            mode, protocol = MTK_PRODUCT_MAP.get(pid, ("USB_NORMAL", "MediaTek USB (mode inconnu)"))
        else:
            mode = "USB_NORMAL"
            protocol = f"Périphérique USB Android ({vendor_name or 'Mode Normal'})"

        # Description conviviale
        if product_str:
            description = f"{product_str} ({vendor_name})"
        elif vendor_name:
            description = f"Smartphone {vendor_name} — VID:0x{vid:04X} PID:0x{pid:04X}"
        else:
            description = f"Périphérique USB MTK — VID:0x{vid:04X} PID:0x{pid:04X}"

        return UsbDeviceInfo(
            vid=vid,
            pid=pid,
            serial_number=serial_number,
            manufacturer=manufacturer or vendor_name,
            product=product_str,
            bus=bus,
            address=address,
            mode=mode,
            protocol=protocol,
            description=description,
            is_mtk=is_mtk,
            vendor_name=vendor_name,
        )

    def scan_mtk_devices(self) -> List[UsbDeviceInfo]:
        """
        Scanne le bus USB et retourne la liste des périphériques MediaTek (VID 0x0E8D
        et VID alliés) détectés, quelle que soit la présence d'un pilote COM.

        Caractéristiques :
          - Lecture 100% passive (aucune ouverture de port, aucun handle conservé).
          - Détecte les BROM en dehors de la fenêtre d'attribution des ports COM Windows.
          - Thread-safe.
          - Retourne [] si PyUSB non disponible (pas de crash).

        Retourne : Liste de UsbDeviceInfo, triée par priorité BROM > NORMAL > USB_NORMAL.
        """
        if not self._available:
            return []

        results: List[UsbDeviceInfo] = []

        try:
            # Recherche ciblée sur les VID MediaTek et constructeurs Android courants
            target_vids = (
                0x0E8D, 0x0489, 0x2717, 0x2A70,  # MediaTek & alliés
                0x04E8, 0x1EBF, 0x1D45, 0x201E, 0x22D9, 0x2D95, 0x22B8, 0x18D1  # Constructeurs Android
            )
            raw_devices = []
            for target_vid in target_vids:
                try:
                    extras = list(_usb_core.find(
                        idVendor=target_vid,
                        find_all=True,
                        backend=self._backend,
                    ))
                    raw_devices.extend(extras)
                except Exception:
                    pass

        except Exception as exc:
            logger.debug(f"[USB-SCANNER] Erreur lors du scan USB : {exc}")
            return []

        # Classification de chaque périphérique brut
        for device in raw_devices:
            try:
                info = self._classify_usb_device(device)
                if info is not None:
                    results.append(info)
            except Exception as exc:
                logger.debug(f"[USB-SCANNER] Erreur de classification : {exc}")

        # Tri par priorité : BROM en premier
        priority = {"BROM": 0, "NORMAL": 1, "USB_NORMAL": 2, "FASTBOOT": 3, "UNKNOWN": 9}
        results.sort(key=lambda d: priority.get(d.mode, 9))

        if results:
            logger.debug(f"[USB-SCANNER] {len(results)} périphérique(s) MTK détecté(s) via PyUSB.")

        return results

    def scan_all_devices(self) -> List[UsbDeviceInfo]:
        """
        Scanne tous les périphériques USB visibles (debug / diagnostic uniquement).
        Retourne UsbDeviceInfo uniquement pour les VID MediaTek et Android reconnus.
        """
        if not self._available:
            return []

        results: List[UsbDeviceInfo] = []
        try:
            raw_devices = list(_usb_core.find(find_all=True, backend=self._backend))
        except Exception:
            return []

        for device in raw_devices:
            try:
                vid = device.idVendor
                pid = device.idProduct
                bus = device.bus
                address = device.address

                is_mtk = vid in MTK_VENDOR_IDS
                vendor_name = MTK_VENDOR_IDS.get(vid, ANDROID_VENDOR_IDS.get(vid, ""))

                mode, protocol = MTK_PRODUCT_MAP.get(pid, ("USB_NORMAL", ""))
                if not is_mtk:
                    mode = "USB_NORMAL"
                    protocol = f"Périphérique Android ({vendor_name})" if vendor_name else ""

                manufacturer = self._read_string_descriptor(device, getattr(device, "iManufacturer", 0))
                product_str   = self._read_string_descriptor(device, getattr(device, "iProduct", 0))
                serial_number = self._read_string_descriptor(device, getattr(device, "iSerialNumber", 0))

                description = product_str or vendor_name or f"VID:{vid:04X} PID:{pid:04X}"

                results.append(UsbDeviceInfo(
                    vid=vid, pid=pid,
                    serial_number=serial_number,
                    manufacturer=manufacturer,
                    product=product_str,
                    bus=bus, address=address,
                    mode=mode, protocol=protocol,
                    description=description,
                    is_mtk=is_mtk,
                    vendor_name=vendor_name,
                ))
            except Exception:
                pass

        return results

    def find_mtk_device(self) -> Tuple[bool, Optional[int]]:
        """
        Fonction de commodité : retourne (trouvé: bool, idProduct: Optional[int]).
        Compatible avec la signature de la spécification initiale.

        Usage :
            found, pid = scanner.find_mtk_device()
            if found:
                print(f"MTK détecté, PID=0x{pid:04X}")
        """
        if not self._available:
            return False, None
        try:
            device = _usb_core.find(idVendor=0x0E8D, backend=self._backend)
            if device is not None:
                return True, device.idProduct
            return False, None
        except Exception:
            return False, None


# ─── Singleton partagé ────────────────────────────────────────────────────────

# Instance unique réutilisée par DeviceDetector (évite de recréer le backend à chaque scan)
_scanner_instance: Optional[UsbScanner] = None


def get_usb_scanner() -> UsbScanner:
    """Retourne l'instance singleton du scanner USB (création lazy)."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = UsbScanner()
    return _scanner_instance


def scan_mtk_devices() -> List[UsbDeviceInfo]:
    """
    Fonction de commodité pour un scan MTK rapide depuis n'importe quel module.

    Usage :
        from core.usb_scanner import scan_mtk_devices
        devices = scan_mtk_devices()
        for d in devices:
            print(d.vid_pid_str, d.mode, d.description)
    """
    return get_usb_scanner().scan_mtk_devices()


def find_mtk_device() -> Tuple[bool, Optional[int]]:
    """
    Recherche simple : est-ce qu'un périphérique MediaTek (VID 0x0E8D) est connecté ?

    Usage minimal (conforme à la spécification) :
        from core.usb_scanner import find_mtk_device
        found, pid = find_mtk_device()
    """
    return get_usb_scanner().find_mtk_device()
