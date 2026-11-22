"""Contrat d'adaptateur Qualcomm.

Cette interface fige le contrat que le module métier devra respecter au
Prompt 4. Le moteur GPL sera appelé dans un processus séparé : ce fichier ne
contient aucune logique, aucun appel système et aucune dépendance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from src.core.types import DeviceInfo, OperationResult

__all__ = ["QualcommAdapter", "QualcommAdapterStub"]


class QualcommAdapter(Protocol):
    """Contrat d'un adaptateur Qualcomm."""

    def detect(self) -> list[DeviceInfo]:
        """Détecte les appareils Qualcomm pris en charge."""
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


class QualcommAdapterStub(QualcommAdapter):
    """Implémentation vide : contrat uniquement, aucune logique métier."""

    def detect(self) -> list[DeviceInfo]:
        raise NotImplementedError("Module Qualcomm — implémentation prévue au Prompt 4.")

    def read_info(self, device: DeviceInfo) -> dict[str, Any]:
        raise NotImplementedError("Module Qualcomm — implémentation prévue au Prompt 4.")

    def flash_partition(
        self, device: DeviceInfo, partition: str, image_path: Path
    ) -> OperationResult:
        raise NotImplementedError("Module Qualcomm — implémentation prévue au Prompt 4.")

    def erase_frp(self, device: DeviceInfo, proof_hash: str) -> OperationResult:
        raise NotImplementedError("Module Qualcomm — implémentation prévue au Prompt 4.")