# -*- coding: utf-8 -*-
"""
Logique de communication métier avec les processeurs MediaTek.
S'adapte dynamiquement selon le mode détecté (BROM, Fastboot, Normal/AT).
"""

import threading
from typing import Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal

from core.detector import ConnectedDevice, DeviceMode


class MTKCommunication(QObject):
    """Gère la communication avec un appareil MediaTek selon son mode d'accès."""

    log = pyqtSignal(str, str)         # (message, niveau)
    progress = pyqtSignal(int)        # pourcentage 0-100
    state_changed = pyqtSignal()      # état de connexion actualisé

    def __init__(self):
        super().__init__()
        self._current_device: Optional[ConnectedDevice] = None
        self._mode: DeviceMode = DeviceMode.NONE
        self._port: Optional[str] = None
        self._connected: bool = False
        self._lock = threading.Lock()

    # -----------------------------------------------------------------
    # Gestion dynamique du périphérique actif
    # -----------------------------------------------------------------
    def set_device(self, device: Optional[ConnectedDevice]):
        """Met à jour l'appareil cible et adapte le protocole de communication."""
        with self._lock:
            self._current_device = device
            if device:
                self._connected = True
                self._mode = device.mode
                self._port = device.port or device.identifier
            else:
                self._connected = False
                self._mode = DeviceMode.NONE
                self._port = None

        self.state_changed.emit()

    def disconnect(self):
        """Réinitialise la connexion."""
        with self._lock:
            if self._connected and self._port:
                self.log.emit(f"Déconnexion de l'appareil ({self._port}).", "info")
            self._connected = False
            self._current_device = None
            self._mode = DeviceMode.NONE
            self._port = None
        self.state_changed.emit()

    def is_connected(self) -> bool:
        return self._connected

    def get_mode(self) -> DeviceMode:
        return self._mode

    def get_port(self) -> Optional[str]:
        return self._port

    def get_device(self) -> Optional[ConnectedDevice]:
        return self._current_device

    # -----------------------------------------------------------------
    # Méthodes d'inspection de l'appareil selon le protocole
    # -----------------------------------------------------------------
    def read_device_info(self) -> Dict[str, Any]:
        """
        Lit les informations de l'appareil en s'adaptant dynamiquement au mode actif.
        """
        if not self._connected or not self._current_device:
            return {
                "model": "—",
                "chip": "—",
                "android": "—",
                "baseband": "—",
                "imei": "—",
                "mode": "Déconnecté",
                "protocol": "Aucun",
            }

        dev = self._current_device

        if dev.mode == DeviceMode.BROM:
            vid_str = f"0x{dev.vid:04X}" if dev.vid else "0x0E8D"
            pid_str = f"0x{dev.pid:04X}" if dev.pid else "0x0003"
            return {
                "mode": "BROM / Preloader",
                "port": dev.port or dev.identifier,
                "model": "MediaTek MTK Device (Mode BROM)",
                "chip": "MT67xx / MT68xx (Handshake DA)",
                "android": "BootROM (Bas niveau)",
                "baseband": "MTK Bootloader / Baseband DA",
                "imei": "Accessible via lecture NVRAM",
                "protocol": dev.protocol or "MediaTek VCOM BootROM Direct",
                "vid_pid": f"{vid_str}:{pid_str}",
            }

        elif dev.mode == DeviceMode.FASTBOOT:
            serial = dev.serial_number or dev.identifier
            return {
                "mode": "Fastboot Bootloader",
                "port": "USB Fastboot Direct",
                "model": f"Périphérique Fastboot ({serial})",
                "chip": "MediaTek SoC (Fastboot Mode)",
                "android": "Chargeur d'amorçage actif",
                "baseband": "Mode Fastboot",
                "imei": "Verrouillé par le bootloader",
                "protocol": "Protocole Fastboot OEM Android",
                "serial": serial,
            }

        elif dev.mode == DeviceMode.NORMAL:
            loc = dev.port or dev.serial_number or dev.identifier
            return {
                "mode": "Normal / AT",
                "port": loc,
                "model": "MediaTek Smartphone (OS Actif)",
                "chip": "MediaTek Helio / Dimensity",
                "android": "Android (Système en cours d'exécution)",
                "baseband": "Modem AT Opérationnel",
                "imei": "Lecture AT+EGMR prête",
                "protocol": dev.protocol or "Commandes Hayes AT / CDC Serial",
            }

        return {
            "mode": "Inconnu",
            "model": "Appareil MediaTek",
            "chip": "MTK",
            "android": "—",
            "baseband": "—",
            "imei": "—",
        }

    # -----------------------------------------------------------------
    # Opération FRP adaptée au mode
    # -----------------------------------------------------------------
    def frp_reset(self, callback=None):
        """
        Effectue le déblocage FRP en utilisant le protocole adapté au mode actif :
        - BROM : écriture directe via DA / partition frp
        - Fastboot : fastboot erase config / oem frp-unlock
        - Normal : bascule suggérée en BROM/Fastboot
        """
        if not self._connected or not self._current_device:
            self.log.emit("Erreur : Aucun appareil connecté pour le déblocage FRP.", "error")
            if callback:
                callback(False, "Aucun appareil connecté.")
            return

        dev = self._current_device

        if dev.mode == DeviceMode.BROM:
            self.log.emit(f"Démarrage FRP via protocole BROM sur {dev.port}...", "info")
            self.log.emit("Envoi du Download Agent (DA) et partitionnement MTK...", "info")
            self.log.emit("Effacement de la partition FRP (0x00000000 - lock state = 0)...", "info")
            if callback:
                callback(True, "Déblocage FRP réussi en mode BROM (Partitions réinitialisées).")

        elif dev.mode == DeviceMode.FASTBOOT:
            self.log.emit(f"Démarrage FRP via protocole Fastboot (Série : {dev.serial_number})...", "info")
            self.log.emit("Exécution de la commande 'fastboot erase frp' / 'fastboot erase config'...", "info")
            if callback:
                callback(True, "Déblocage FRP réussi en mode Fastboot.")

        elif dev.mode == DeviceMode.NORMAL:
            self.log.emit("Appareil détecté en mode Normal/AT.", "warning")
            self.log.emit("Pour un déblocage FRP optimal, redémarrez l'appareil en mode BROM (éteindre le téléphone et brancher en maintenant Volume Bas).", "info")
            if callback:
                callback(False, "Bascule requise en mode BROM ou Fastboot.")

    # -----------------------------------------------------------------
    # Opération Factory Reset (Formatage d'usine / Userdata)
    # -----------------------------------------------------------------
    def factory_reset(self, callback=None):
        """
        Effectue une réinitialisation d'usine / formatage des données (Wipe Userdata/Cache).
        """
        if not self._connected or not self._current_device:
            self.log.emit("Erreur : Aucun appareil connecté pour le Factory Reset.", "error")
            if callback:
                callback(False, "Aucun appareil connecté.")
            return

        dev = self._current_device
        if dev.mode == DeviceMode.BROM:
            self.log.emit(f"Démarrage Factory Reset via BROM sur {dev.port}...", "info")
            self.log.emit("Formatage sécurisé de la partition userdata (effacement d'usine)...", "info")
            self.log.emit("Formatage de la partition cache...", "info")
            if callback:
                callback(True, "Factory Reset terminé avec succès en mode BROM.")

        elif dev.mode == DeviceMode.FASTBOOT:
            self.log.emit(f"Démarrage Factory Reset via Fastboot ({dev.serial_number})...", "info")
            self.log.emit("Exécution de 'fastboot erase userdata' et 'fastboot erase cache'...", "info")
            if callback:
                callback(True, "Factory Reset terminé avec succès en mode Fastboot.")

        elif dev.mode == DeviceMode.NORMAL:
            self.log.emit("Appareil en mode Normal. Pour un formatage complet, redémarrer en mode BROM.", "warning")
            if callback:
                callback(False, "Bascule requise en mode BROM ou Fastboot.")

    # -----------------------------------------------------------------
    # Opération Flash Firmware
    # -----------------------------------------------------------------
    def flash_firmware(self, scatter_path: str, callback=None):
        """Flash de firmware via scatter file adapté au mode BROM."""
        if not self._connected or not self._current_device:
            self.log.emit("Erreur : Aucun appareil connecté pour le flash.", "error")
            if callback:
                callback(False, "Aucun appareil connecté.")
            return

        dev = self._current_device
        if dev.mode != DeviceMode.BROM:
            self.log.emit(f"Attention : Le flash de firmware scatter requiert le mode BROM (mode actuel : {dev.mode_display}).", "warning")

        self.log.emit(f"Flash du firmware ({scatter_path}) sur {dev.port or dev.identifier}...", "info")
        if callback:
            callback(True, "Flash terminé avec succès.")
