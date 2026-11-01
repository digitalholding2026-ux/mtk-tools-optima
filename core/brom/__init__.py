# -*- coding: utf-8 -*-
"""
Package core.brom - Protocole bas-niveau BootROM MediaTek (BROM).
Gestion du handshake matériel, lecture des codes processeurs (MEID, SOC ID)
et préparation pour l'injection des Download Agents (DA).
"""

from core.brom.handshake import (
    MTKBromHandshake,
    BROM_CMD_START,
    BROM_CMD_GET_HW_CODE,
    BROM_CMD_GET_HW_SUB_CODE,
    BROM_CMD_GET_HW_VER,
    BROM_CMD_GET_SW_VER,
)

__all__ = [
    "MTKBromHandshake",
    "BROM_CMD_START",
    "BROM_CMD_GET_HW_CODE",
    "BROM_CMD_GET_HW_SUB_CODE",
    "BROM_CMD_GET_HW_VER",
    "BROM_CMD_GET_SW_VER",
]
