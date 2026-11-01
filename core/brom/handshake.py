# -*- coding: utf-8 -*-
"""
core.brom.handshake - Séquences de négociation bas-niveau MTK BROM.
Protocole matériel pour initialiser la communication série / USB avec le BootROM.
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("OptimaMTK.BROM")

# Commandes standard BROM MediaTek
BROM_CMD_START           = 0xA0
BROM_CMD_GET_HW_CODE     = 0xFD
BROM_CMD_GET_HW_SUB_CODE = 0xFC
BROM_CMD_GET_HW_VER      = 0xFB
BROM_CMD_GET_SW_VER      = 0xFA
BROM_CMD_SEND_DA         = 0xD7
BROM_CMD_JUMP_DA         = 0xD5

# Table des SoCs MediaTek reconnus par code matériel (HW Code)
MTK_CHIP_TABLE: Dict[int, str] = {
    0x0321: "MediaTek MT6580",
    0x0335: "MediaTek MT6735",
    0x0337: "MediaTek MT6737",
    0x0279: "MediaTek MT6755 (Helio P10)",
    0x0326: "MediaTek MT6750",
    0x0679: "MediaTek MT6757 (Helio P20)",
    0x0551: "MediaTek MT6763 (Helio P23)",
    0x0707: "MediaTek MT6765 (Helio G25 / G35 / P35)",
    0x0766: "MediaTek MT6768 (Helio P65 / G85)",
    0x0788: "MediaTek MT6761 (Helio A22)",
    0x0816: "MediaTek MT6771 (Helio P60 / P70)",
    0x0886: "MediaTek MT6779 (Helio P90)",
    0x0830: "MediaTek MT6781 (Helio G96)",
    0x0952: "MediaTek MT6785 (Helio G90T / G95)",
    0x0989: "MediaTek MT6789 (Helio G99)",
    0x0851: "MediaTek MT6833 (Dimensity 700)",
    0x0922: "MediaTek MT6853 (Dimensity 720)",
    0x0933: "MediaTek MT6877 (Dimensity 900)",
    0x0811: "MediaTek MT6873 (Dimensity 800)",
    0x0813: "MediaTek MT6885 (Dimensity 1000)",
    0x0893: "MediaTek MT6893 (Dimensity 1200)",
    0x0983: "MediaTek MT6983 (Dimensity 9000)",
}


class MTKBromHandshake:
    """
    Exécute la synchronisation d'entrée BootROM avec un SoC MediaTek.
    Peut opérer sur une connexion série (PySerial) ou un endpoint USB direct (PyUSB).
    """

    def __init__(self, serial_conn=None):
        self.conn = serial_conn

    def execute_handshake(self, timeout_sec: float = 3.0) -> bool:
        """
        Envoie la séquence binaire d'initialisation BROM :
          Hôte -> 0xA0  SoC -> 0x5F
          Hôte -> 0x0A  SoC -> 0xF5
          Hôte -> 0x50  SoC -> 0xAF
          Hôte -> 0x05  SoC -> 0xFA
        """
        if not self.conn:
            return False

        seq = [
            (bytes([0xA0]), bytes([0x5F])),
            (bytes([0x0A]), bytes([0xF5])),
            (bytes([0x50]), bytes([0xAF])),
            (bytes([0x05]), bytes([0xFA])),
        ]

        deadline = time.time() + timeout_sec
        try:
            for tx, expected_rx in seq:
                self.conn.write(tx)
                self.conn.flush()
                resp = self.conn.read(1)
                if resp != expected_rx:
                    logger.debug(f"[BROM-HANDSHAKE] Réponse inattendue pour TX {tx.hex()}: {resp.hex() if resp else 'TIMEOUT'}")
                    return False
                if time.time() > deadline:
                    return False
            logger.info("[BROM-HANDSHAKE] Handshake matériel BROM réussi !")
            return True
        except Exception as err:
            logger.error(f"[BROM-HANDSHAKE] Erreur d'échange matériel : {err}")
            return False

    def read_hw_code(self) -> Optional[int]:
        """Lit le registre matériel du processeur via BROM_CMD_GET_HW_CODE (0xFD)."""
        if not self.conn:
            return None
        try:
            self.conn.write(bytes([BROM_CMD_GET_HW_CODE]))
            self.conn.flush()
            # Le SoC répond avec statut (0x00) + 2 octets Big Endian HW Code + statut de fin (0x00)
            data = self.conn.read(4)
            if len(data) >= 3:
                # Format standard: status(1) + hw_code(2)
                hw_code = int.from_bytes(data[1:3], byteorder="big")
                return hw_code
        except Exception as err:
            logger.error(f"[BROM-HANDSHAKE] Erreur lors de la lecture du code HW : {err}")
        return None

    def get_chipset_name(self, hw_code: int) -> str:
        """Résout le nom commercial du chipset d'après son code matériel."""
        return MTK_CHIP_TABLE.get(hw_code, f"MediaTek MTK (HW: 0x{hw_code:04X})")
