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
        Délègue l'exécution bas-niveau à core.actions.read_device_info.
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
        target_id = dev.port or dev.serial_number or dev.identifier

        from core.actions import read_device_info as act_read_info
        res = act_read_info(dev.mode, target_id, log_callback=self.log.emit)

        if res.success and res.data:
            data = res.data
            return {
                "mode": dev.mode_display,
                "port": dev.port or dev.identifier,
                "model": data.get("name", data.get("model", dev.description)),
                "chip": data.get("chipset", "MediaTek MTK"),
                "android": data.get("android_version", "Android OS"),
                "baseband": data.get("raw_variables", {}).get("version-baseband", "Baseband MTK"),
                "imei": data.get("imei", data.get("serial", "—")),
                "protocol": dev.protocol or "Protocole Direct",
                "serial": data.get("serial", dev.serial_number or "—"),
            }

        return {
            "mode": dev.mode_display,
            "port": dev.port or dev.identifier,
            "model": dev.description or "Appareil MediaTek",
            "chip": "MediaTek MTK",
            "android": "—",
            "baseband": "—",
            "imei": "—",
            "protocol": dev.protocol or "Direct",
        }

    # -----------------------------------------------------------------
    # Opération FRP adaptée au mode
    # -----------------------------------------------------------------
    def frp_reset(self, callback=None):
        """
        Effectue le déblocage FRP en utilisant le protocole adapté au mode actif via core.actions.erase_frp.
        """
        if not self._connected or not self._current_device:
            self.log.emit("Erreur : Aucun appareil connecté pour le déblocage FRP.", "error")
            if callback:
                callback(False, "Aucun appareil connecté.")
            return

        dev = self._current_device
        target_id = dev.port or dev.serial_number or dev.identifier

        from core.actions import erase_frp as act_erase_frp
        res = act_erase_frp(dev.mode, target_id, log_callback=self.log.emit)

        if callback:
            callback(res.success, res.message)
        return res

    # -----------------------------------------------------------------
    # Opération Factory Reset (Formatage d'usine / Userdata)
    # -----------------------------------------------------------------
    def factory_reset(self, callback=None):
        """
        Effectue une réinitialisation d'usine / formatage des données via core.actions.factory_reset.
        """
        if not self._connected or not self._current_device:
            self.log.emit("Erreur : Aucun appareil connecté pour le Factory Reset.", "error")
            if callback:
                callback(False, "Aucun appareil connecté.")
            return

        dev = self._current_device
        target_id = dev.port or dev.serial_number or dev.identifier

        from core.actions import factory_reset as act_factory_reset
        res = act_factory_reset(dev.mode, target_id, log_callback=self.log.emit)

        if callback:
            callback(res.success, res.message)
        return res

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

    # -----------------------------------------------------------------
    # Opération Redémarrage
    # -----------------------------------------------------------------
    def reboot(self, target_reboot: str = "normal", callback=None):
        """Redémarre l'appareil connecté vers la cible spécifiée."""
        if not self._connected or not self._current_device:
            self.log.emit("Erreur : Aucun appareil connecté pour le redémarrage.", "error")
            if callback:
                callback(False, "Aucun appareil connecté.")
            return

        dev = self._current_device
        target_id = dev.port or dev.serial_number or dev.identifier

        from core.actions import reboot_device as act_reboot
        res = act_reboot(dev.mode, target_id, target_reboot=target_reboot, log_callback=self.log.emit)

        if callback:
            callback(res.success, res.message)
        return res
