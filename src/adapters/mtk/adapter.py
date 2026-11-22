"""Contrat d'adaptateur MediaTek.

Cette interface fige le contrat que le module métier devra respecter au
Prompt 3. Le moteur GPL sera appelé dans un processus séparé : ce fichier ne
contient aucune logique, aucun appel système et aucune dépendance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from src.core.types import DeviceInfo, OperationResult

__all__ = ["MediaTekAdapter", "MediaTekAdapterStub"]


class MediaTekAdapter(Protocol):
    """Contrat d'un adaptateur MediaTek."""

    def detect(self) -> list[DeviceInfo]:
        """Détecte les appareils MediaTek pris en charge."""
        ...

    def read_info(self, device: DeviceInfo) -> dict[str, Any]:
        """Lit les informations non destructives de l'appareil."""
        ...

    def flash_partition(
        self, device: DeviceInfo, partition: str, image_path: Path
    ) -> OperationResult:
        """Écrit une image sur une partition."""
        ...

    def erase_frp(self, device: DeviceInfo, proof_hash: str) -> OperationResult:
        """Efface le FRP après preuve écrite."""
        ...


class MediaTekAdapterStub(MediaTekAdapter):
    """Implémentation vide : contrat uniquement, aucune logique métier."""

    def detect(self) -> list[DeviceInfo]:
        raise NotImplementedError("Module MediaTek — implémentation prévue au Prompt 3.")

    def read_info(self, device: DeviceInfo) -> dict[str, Any]:
        raise NotImplementedError("Module MediaTek — implémentation prévue au Prompt 3.")

    def flash_partition(
        self, device: DeviceInfo, partition: str, image_path: Path
    ) -> OperationResult:
        raise NotImplementedError("Module MediaTek — implémentation prévue au Prompt 3.")

    def erase_frp(self, device: DeviceInfo, proof_hash: str) -> OperationResult:
        raise NotImplementedError("Module MediaTek — implémentation prévue au Prompt 3.")