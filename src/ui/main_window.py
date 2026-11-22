"""Fenêtre principale PySide6.

L'interface consomme uniquement les modules existants : aucune logique USB
directe, aucune opération d'écriture. Le scan s'exécute dans un QThread dédié.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QKeySequence,
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.adapters.usb.detector import detect_devices
from src.adapters.usb.drivers import check_backend, check_drivers, open_installer_script
from src.core.license import check_license
from src.core.types import DeviceInfo, OperationError, OperationFailure

__all__ = ["MainWindow", "main"]


class ScanWorker(QObject):
    """Worker de scan exécuté dans un QThread."""

    finished = Signal(object)
    error = Signal(object)

    @Slot()
    def run(self) -> None:
        try:
            devices = detect_devices()
        except OperationFailure as exc:
            self.error.emit(exc)
            return
        except Exception as exc:  # noqa: BLE001 - filet de sécurité pour l'UI
            self.error.emit(OperationFailure(OperationError(f"Erreur inattendue : {exc}")))
            return
        self.finished.emit(devices)


class DriverCheckWorker(QObject):
    """Worker de vérification des pilotes, exécuté dans un QThread."""

    finished = Signal(object)
    error = Signal(str)

    @Slot()
    def run(self) -> None:
        try:
            result = check_drivers()
        except Exception as exc:  # noqa: BLE001 - filet de sécurité pour l'UI
            self.error.emit(str(exc))
            return
        self.finished.emit(result)


class MainWindow(QMainWindow):
    """Fenêtre principale : table des appareils, scan et boutons métier inactifs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._thread: QThread | None = None
        self._worker: ScanWorker | None = None
        self._driver_thread: QThread | None = None
        self._driver_worker: DriverCheckWorker | None = None
        self._status_message = "Prêt"
        self._driver_status = "non vérifié"
        self._license_ok = check_license()
        self._backend_ok = check_backend()

        self.setWindowTitle("Optima Telecom Flash Tool")
        self.resize(900, 600)
        self.setMinimumSize(900, 600)

        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)

        self._backend_banner = QLabel(
            "Backend libusb manquant — Scannez les appareils est désactivé. "
            "Lancez scripts/install_drivers.ps1.",
            central,
        )
        self._backend_banner.setWordWrap(True)
        self._backend_banner.setStyleSheet(
            "background-color: #fff3cd; color: #664d03; padding: 8px;"
        )
        self._backend_banner.setVisible(not self._backend_ok)
        layout.addWidget(self._backend_banner)

        self._model = QStandardItemModel(self)
        self._model.setHorizontalHeaderLabels(
            ["Chipset", "Mode", "VID", "PID", "Bus", "Adresse", "Série"]
        )

        self._table = QTableView(central)
        self._table.setModel(self._model)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

        buttons = QHBoxLayout()

        self._scan_button = QPushButton("Scanner les appareils", central)
        self._scan_button.clicked.connect(self._on_scan_clicked)
        self._scan_button.setEnabled(self._backend_ok)
        buttons.addWidget(self._scan_button)

        self._flash_button = QPushButton("Flash", central)
        self._flash_button.setEnabled(False)
        self._flash_button.setToolTip("Disponible après implémentation du module métier")
        buttons.addWidget(self._flash_button)

        self._frp_button = QPushButton("FRP", central)
        self._frp_button.setEnabled(False)
        self._frp_button.setToolTip("Disponible après implémentation du module métier")
        buttons.addWidget(self._frp_button)

        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.setCentralWidget(central)

        file_menu = self.menuBar().addMenu("&Fichier")
        quit_action = QAction("&Quitter", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        tools_menu = self.menuBar().addMenu("&Outils")
        self._driver_action = QAction("Vérifier les pilotes USB", self)
        self._driver_action.triggered.connect(self._on_verify_drivers)
        tools_menu.addAction(self._driver_action)

        self._status_label = QLabel("", self)
        self.statusBar().addWidget(self._status_label)

    def _refresh_status(self) -> None:
        license_text = "OK (placeholder)" if self._license_ok else "NON"
        backend_text = "OK" if self._backend_ok else "MANQUANT"
        self._status_label.setText(
            f"{self._status_message} · Licence : {license_text} · "
            f"Backend USB : {backend_text} · Pilotes : {self._driver_status}"
        )

    def _set_status_message(self, message: str) -> None:
        self._status_message = message
        self._refresh_status()

    def _populate(self, devices: list[DeviceInfo]) -> None:
        self._model.removeRows(0, self._model.rowCount())
        for device in devices:
            items = [
                QStandardItem(device.chipset.value),
                QStandardItem(device.connection_mode.value),
                QStandardItem(f"0x{device.vid:04X}"),
                QStandardItem(f"0x{device.pid:04X}"),
                QStandardItem(str(device.bus)),
                QStandardItem(str(device.address)),
                QStandardItem(device.serial or ""),
            ]
            for item in items:
                item.setEditable(False)
            self._model.appendRow(items)
        self._table.resizeColumnsToContents()

    @Slot()
    def _on_scan_clicked(self) -> None:
        if not self._backend_ok:
            return
        if self._thread is not None and self._thread.isRunning():
            return

        self._scan_button.setEnabled(False)
        self._set_status_message("Scanner les appareils…")

        thread = QThread(self)
        worker = ScanWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_devices_ready)
        worker.error.connect(self._on_scan_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(self._on_scan_thread_finished)
        thread.start()

        self._thread = thread
        self._worker = worker

    @Slot(object)
    def _on_devices_ready(self, devices: object) -> None:
        if not isinstance(devices, list):
            self._set_status_message("Réponse de scan invalide.")
            return

        typed = [item for item in devices if isinstance(item, DeviceInfo)]
        self._populate(typed)
        self._set_status_message(f"{len(typed)} appareil(s) détecté(s).")

    @Slot(object)
    def _on_scan_error(self, error: object) -> None:
        message = error.message if isinstance(error, OperationFailure) else str(error)
        self._set_status_message(f"Échec du scan : {message}")
        QMessageBox.warning(self, "Scan des appareils", f"Échec du scan : {message}")

    @Slot()
    def _on_scan_thread_finished(self) -> None:
        self._scan_button.setEnabled(True)

    @Slot()
    def _on_verify_drivers(self) -> None:
        if self._driver_thread is not None and self._driver_thread.isRunning():
            return

        self._driver_action.setEnabled(False)
        self._set_status_message("Vérification des pilotes…")

        thread = QThread(self)
        worker = DriverCheckWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_drivers_checked)
        worker.error.connect(self._on_drivers_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(self._on_driver_thread_finished)
        thread.start()

        self._driver_thread = thread
        self._driver_worker = worker

    @Slot(object)
    def _on_drivers_checked(self, result: object) -> None:
        if not isinstance(result, dict):
            self._set_status_message("Résultat de vérification invalide.")
            return

        mtk = bool(result.get("mtk_vcom"))
        qualcomm = bool(result.get("qualcomm_9008"))
        mtk_text = "installé" if mtk else "absent"
        qualcomm_text = "installé" if qualcomm else "absent"

        self._driver_status = f"MTK {mtk_text} · QC {qualcomm_text}"
        self._set_status_message("Pilotes vérifiés")

        box = QMessageBox(self)
        box.setWindowTitle("Vérification des pilotes USB")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(
            "État des pilotes USB :\n"
            f"  • MediaTek VCOM : {mtk_text}\n"
            f"  • Qualcomm 9008 : {qualcomm_text}"
        )
        open_button = box.addButton(
            "Ouvrir le script d'installation", QMessageBox.ButtonRole.AcceptRole
        )
        box.addButton(QMessageBox.StandardButton.Close)
        box.exec()

        if box.clickedButton() is open_button:
            try:
                open_installer_script()
            except OSError as exc:
                QMessageBox.warning(
                    self,
                    "Script d'installation",
                    f"Impossible d'ouvrir le script : {exc}",
                )

    @Slot(str)
    def _on_drivers_error(self, message: str) -> None:
        self._set_status_message("Échec de la vérification des pilotes.")
        QMessageBox.warning(self, "Vérification des pilotes USB", f"Échec : {message}")

    @Slot()
    def _on_driver_thread_finished(self) -> None:
        self._driver_action.setEnabled(True)

    def closeEvent(self, event: QCloseEvent) -> None:
        for thread in (self._thread, self._driver_thread):
            if thread is not None and thread.isRunning():
                thread.quit()
                thread.wait(2000)
        super().closeEvent(event)


def main(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("Optima Telecom Flash Tool")
    window = MainWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())