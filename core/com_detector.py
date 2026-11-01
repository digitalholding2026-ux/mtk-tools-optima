# -*- coding: utf-8 -*-
"""
Détection des ports COM / USB pour les appareils MediaTek.
Émet des signaux lorsqu'un appareil est connecté ou déconnecté.
"""

import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal

try:
    import serial.tools.list_ports as list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class COMDetector(QObject):
    """Détecteur de ports COM / USB pour périphériques MediaTek."""

    device_detected = pyqtSignal(str, str)   # (port, infos)
    device_lost = pyqtSignal(str)            # (port)
    log_message = pyqtSignal(str, str)       # (message, level)

    def __init__(self):
        super().__init__()
        self._monitoring = False
        self._monitor_thread = None
        self._known_ports = set()
        self._current_port = None

    def scan_ports(self):
        """Lance un scan immédiat des ports disponibles."""
        self.log_message.emit("Scan des ports COM en cours...", "info")
        ports = self._list_ports()
        mtk_ports = [p for p in ports if self._is_mtk_device(p)]

        if mtk_ports:
            port = mtk_ports[0]
            info = self._get_device_info(port)
            self._current_port = port
            self.device_detected.emit(port, info)
            self.log_message.emit(f"Appareil MediaTek détecté sur {port}", "success")
        else:
            self.log_message.emit("Aucun appareil MediaTek détecté.", "warning")

    def start_monitoring(self):
        """Démarre la surveillance continue des ports (thread séparé)."""
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Arrête la surveillance continue."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)

    def _monitor_loop(self):
        """Boucle de surveillance des ports COM."""
        while self._monitoring:
            try:
                current = set(self._list_ports())
                added = current - self._known_ports
                removed = self._known_ports - current

                for port in added:
                    if self._is_mtk_device(port):
                        info = self._get_device_info(port)
                        self._current_port = port
                        self.device_detected.emit(port, info)
                        self.log_message.emit(f"Appareil connecté : {port}", "success")

                for port in removed:
                    if port == self._current_port:
                        self.device_lost.emit(port)
                        self._current_port = None
                        self.log_message.emit(f"Appareil déconnecté : {port}", "warning")

                self._known_ports = current
            except Exception as e:
                self.log_message.emit(f"Erreur de surveillance : {str(e)}", "error")

            time.sleep(2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _list_ports(self):
        """Retourne la liste des ports COM disponibles."""
        if HAS_SERIAL:
            return [p.device for p in list_ports.comports()]
        # Fallback Windows : lecture rapide du registre (simplifiée)
        return self._list_ports_windows_fallback()

    def _list_ports_windows_fallback(self):
        """Fallback sans pyserial : tente de lister COM1..COM20."""
        ports = []
        for i in range(1, 21):
            path = f"COM{i}"
            try:
                import serial
                s = serial.Serial(path)
                s.close()
                ports.append(path)
            except Exception:
                pass
        return ports

    def _is_mtk_device(self, port):
        """Détermine si un port correspond à un appareil MediaTek."""
        if not HAS_SERIAL:
            return True  # sans pyserial, on considère tout port comme candidat
        try:
            for p in list_ports.comports():
                if p.device == port:
                    hwid = (p.hwid or "").upper()
                    desc = (p.description or "").upper()
                    vid = p.vid
                    pid = p.pid
                    # VID connus MediaTek (exemples courants)
                    mtk_vids = {0x0E8D, 0x0489, 0x6000}
                    mtk_keywords = ["MEDIATEK", "MTK", "PRELOADER", "BROM", "USB DEBUG"]
                    if vid in mtk_vids:
                        return True
                    if any(k in hwid or k in desc for k in mtk_keywords):
                        return True
        except Exception:
            pass
        return False

    def _get_device_info(self, port):
        """Retourne une chaîne d'informations simplifiée pour le port."""
        if HAS_SERIAL:
            try:
                for p in list_ports.comports():
                    if p.device == port:
                        desc = p.description or "Appareil MediaTek"
                        return f"{desc} (VID={p.vid}, PID={p.pid})"
            except Exception:
                pass
        return "Appareil MediaTek"
