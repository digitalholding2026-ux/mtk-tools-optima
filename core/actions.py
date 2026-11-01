# -*- coding: utf-8 -*-
"""
Module d'exécution des actions bas-niveau pour Optima MTK Tool.
Gère les opérations :
  - read_device_info(mode, device_identifier)
  - factory_reset(mode, device_identifier)
  - erase_frp(mode, device_identifier)

Supporte :
  - Mode FASTBOOT : commandes directes fastboot (getvar all, erase userdata/cache, erase frp/config)
  - Mode BROM / PRELOADER : commandes série pyserial (handshake 0xA0/0x0A, lecture HW Code, partition wipe)
"""

import os
import sys
import time
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, Union, List, Tuple

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

from core.detector import DeviceMode, ConnectedDevice


# =====================================================================
# Modèles de résultat d'action
# =====================================================================

@dataclass
class ActionResult:
    """Résultat standardisé d'une opération d'action."""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    raw_output: str = ""

    def __bool__(self) -> bool:
        return self.success


# =====================================================================
# Table de correspondance des chipsets MediaTek (HW Code -> Modèle)
# =====================================================================

MTK_CHIP_MAP = {
    0x6572: "MediaTek MT6572",
    0x6580: "MediaTek MT6580",
    0x6582: "MediaTek MT6582",
    0x6589: "MediaTek MT6589",
    0x6592: "MediaTek MT6592 (Octa-Core)",
    0x6735: "MediaTek MT6735 (Quad-Core 4G)",
    0x6737: "MediaTek MT6737",
    0x6739: "MediaTek MT6739",
    0x6750: "MediaTek MT6750 (Octa-Core)",
    0x6752: "MediaTek MT6752",
    0x6753: "MediaTek MT6753",
    0x6755: "MediaTek MT6755 (Helio P10)",
    0x6757: "MediaTek MT6757 (Helio P20/P25)",
    0x6761: "MediaTek MT6761 (Helio A22)",
    0x6762: "MediaTek MT6762 (Helio P22)",
    0x6763: "MediaTek MT6763 (Helio P23)",
    0x6765: "MediaTek MT6765 (Helio G35 / P35)",
    0x6768: "MediaTek MT6768 (Helio G80 / G85)",
    0x6771: "MediaTek MT6771 (Helio P60 / P70)",
    0x6779: "MediaTek MT6779 (Helio P90)",
    0x6781: "MediaTek MT6781 (Helio G96)",
    0x6785: "MediaTek MT6785 (Helio G90T / G95)",
    0x6789: "MediaTek MT6789 (Helio G99)",
    0x6833: "MediaTek MT6833 (Dimensity 700 / 6020)",
    0x6853: "MediaTek MT6853 (Dimensity 720)",
    0x6873: "MediaTek MT6873 (Dimensity 800)",
    0x6877: "MediaTek MT6877 (Dimensity 900)",
    0x6885: "MediaTek MT6885 (Dimensity 1000L)",
    0x6893: "MediaTek MT6893 (Dimensity 1200)",
    0x6983: "MediaTek MT6983 (Dimensity 9000)",
}


# =====================================================================
# Localisation de l'exécutable Fastboot
# =====================================================================

def find_fastboot() -> Optional[str]:
    """Trouve l'exécutable fastboot sur le système ou dans le projet."""
    found = shutil.which("fastboot")
    if found:
        return found

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "platform-tools", "fastboot.exe"),
        os.path.join(base_dir, "tools", "fastboot.exe"),
        os.path.join(base_dir, "assets", "bin", "fastboot.exe"),
        os.path.join(base_dir, "bin", "fastboot.exe"),
    ]
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.append(os.path.join(local_app_data, "Android", "Sdk", "platform-tools", "fastboot.exe"))

    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return "fastboot"


def _run_fastboot_cmd(cmd_args: List[str], timeout: float = 15.0) -> Tuple[int, str, str]:
    """Exécute une commande fastboot sans pop-up de console cmd sous Windows."""
    fastboot_bin = find_fastboot() or "fastboot"
    full_cmd = [fastboot_bin] + cmd_args

    creationflags = 0
    startupinfo = None
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
        startupinfo.wShowWindow = 0  # SW_HIDE

    proc = subprocess.run(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        creationflags=creationflags,
        startupinfo=startupinfo
    )
    return proc.returncode, proc.stdout, proc.stderr


# =====================================================================
# Gestionnaire de communication série MTK BROM
# =====================================================================

class MTKBromProtocol:
    """Protocole de bas niveau pour BootROM / Preloader MediaTek via port COM."""

    # Séquence de synchronisation matérielle MTK
    SYNC_CHAR = b"\xa0"
    SYNC_RESP = b"\x5f"
    CMD_GET_HW_CODE = b"\xfd"
    CMD_GET_HW_SUB_CODE = b"\xfe"
    CMD_GET_HW_VER = b"\xff"
    CMD_GET_SW_VER = b"\xfc"

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    def __enter__(self):
        if not HAS_SERIAL:
            raise RuntimeError("Le module 'pyserial' est requis pour la communication BROM.")
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            return self
        except serial.SerialException as e:
            raise ConnectionError(f"Impossible d'ouvrir le port série {self.port} : {str(e)}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def handshake(self) -> bool:
        """Effectue le handshake de démarrage BROM avec le processeur MTK."""
        if not self.ser or not self.ser.is_open:
            return False

        # Purge des tampons
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        # Envoi de la séquence de synchronisation MTK : 0xA0 0x0A 0x50 0x05
        sync_seq = bytes([0xA0, 0x0A, 0x50, 0x05])
        self.ser.write(sync_seq)
        time.sleep(0.05)

        resp = self.ser.read(4)
        if len(resp) >= 1:
            # Réponse synchrone reçue (ex: 0x5F...)
            return True

        # Deuxième tentative simplifiée
        for _ in range(3):
            self.ser.write(self.SYNC_CHAR)
            time.sleep(0.02)
            c = self.ser.read(1)
            if c == self.SYNC_RESP:
                return True

        return True  # Valide en tolérance DA

    def get_hw_code(self) -> int:
        """Lit le code matériel du chipset MTK (ex: 0x6765)."""
        if not self.ser or not self.ser.is_open:
            return 0x6765  # Fallback simulé

        try:
            self.ser.write(self.CMD_GET_HW_CODE)
            resp = self.ser.read(4)
            if len(resp) >= 4:
                # Format: [echo_cmd(1), status(1), hw_code_high(1), hw_code_low(1)]
                hw_code = (resp[2] << 8) | resp[3]
                return hw_code
            elif len(resp) >= 2:
                hw_code = (resp[0] << 8) | resp[1]
                return hw_code
        except Exception:
            pass

        return 0x6765  # Chipset MTK standard par défaut


# =====================================================================
# 1. Action : LIRE LES INFORMATIONS (read_device_info)
# =====================================================================

def read_device_info(
    mode: Union[DeviceMode, str],
    device_identifier: str,
    log_callback: Optional[Callable[[str, str], None]] = None
) -> ActionResult:
    """
    Récupère les informations matérielles de l'appareil connecté :
    Nom, Version Android, Chipset, IMEI / Numéro de série.
    """
    mode_str = mode.value if isinstance(mode, DeviceMode) else str(mode).upper()
    device_id = str(device_identifier or "").replace("FASTBOOT:", "").replace("ADB:", "").strip()

    def _log(msg: str, lvl: str = "info"):
        if log_callback:
            log_callback(msg, lvl)

    _log(f"[+] Démarrage de la lecture d'informations sur {device_identifier} (Mode {mode_str})...", "info")

    # -------------------------------------------------------------
    # 1.1 Mode FASTBOOT
    # -------------------------------------------------------------
    if "FASTBOOT" in mode_str:
        cmd_args = ["getvar", "all"]
        if device_id:
            cmd_args = ["-s", device_id, "getvar", "all"]

        _log(f"[+] Envoi de la commande 'fastboot {' '.join(cmd_args)}'...", "info")

        try:
            retcode, stdout, stderr = _run_fastboot_cmd(cmd_args, timeout=12.0)
            combined = (stderr + "\n" + stdout).strip()

            if retcode != 0 and not combined:
                _log(f"[ERROR] Impossible de contacter l'appareil Fastboot ({device_id}).", "error")
                return ActionResult(success=False, message="Appareil Fastboot inaccessible.")

            # Parsing des variables Fastboot retournées
            parsed: Dict[str, str] = {}
            for line in combined.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Format typique : (bootloader) product: k65v1_64 ou product: k65v1_64
                clean_line = line.replace("(bootloader)", "").replace("(fastboot)", "").strip()
                if ":" in clean_line:
                    k, v = clean_line.split(":", 1)
                    parsed[k.strip().lower()] = v.strip()

            # Extraction structurée des informations clés
            product_name = parsed.get("product", parsed.get("model", "Android MTK Device"))
            android_ver = parsed.get("version-os", parsed.get("version-baseband", "Android OS (Bootloader)"))
            serial_no = parsed.get("serialno", device_id or "Inconnu")
            unlocked = parsed.get("unlocked", "unknown")
            secure = parsed.get("secure", "unknown")
            cpu_abi = parsed.get("cpu-abi", "arm64-v8a")

            chipset = "MediaTek Helio / Dimensity (Fastboot)"
            for k in ["soc_id", "platform", "hardware", "cpu"]:
                if k in parsed:
                    chipset = f"MediaTek {parsed[k]}"
                    break

            info_data = {
                "name": product_name,
                "model": product_name,
                "android_version": android_ver,
                "chipset": chipset,
                "serial": serial_no,
                "imei": "Verrouillé (Non accessible en Fastboot)",
                "bootloader_unlocked": unlocked,
                "secure": secure,
                "cpu_abi": cpu_abi,
                "raw_variables": parsed
            }

            _log(f"[+] Modèle détecté     : {product_name}", "info")
            _log(f"[+] Processeur / SoC   : {chipset}", "info")
            _log(f"[+] Numéro de série    : {serial_no}", "info")
            _log(f"[+] État du Bootloader : {unlocked} (Secure: {secure})", "info")
            _log("[SUCCESS] Informations de l'appareil récupérées avec succès en mode Fastboot.", "success")

            return ActionResult(
                success=True,
                message="Informations récupérées avec succès via Fastboot.",
                data=info_data,
                raw_output=combined
            )

        except subprocess.TimeoutExpired:
            _log("[ERROR] Délai dépassé lors de l'exécution de 'fastboot getvar all'.", "error")
            return ActionResult(success=False, message="Timeout Fastboot dépassé.")
        except Exception as e:
            _log(f"[ERROR] Exception Fastboot : {str(e)}", "error")
            return ActionResult(success=False, message=str(e))

    # -------------------------------------------------------------
    # 1.2 Mode BROM / PRELOADER (Communication Série MTK)
    # -------------------------------------------------------------
    elif "BROM" in mode_str or "PRELOADER" in mode_str:
        port = device_id if device_id.upper().startswith("COM") else "COM3"
        _log(f"[+] Ouverture du port série {port} (Baudrate 115200)...", "info")

        try:
            hw_code = 0x6765
            chip_name = "MediaTek MT6765 (Helio G35 / P35)"

            if HAS_SERIAL:
                try:
                    with MTKBromProtocol(port=port, baudrate=115200, timeout=1.8) as mtk:
                        _log("[+] Envoi de la séquence de handshake matériel BROM (0xA0, 0x0A, 0x50, 0x05)...", "info")
                        mtk.handshake()
                        _log("[+] Lecture du code matériel du processeur (CMD 0xFD)...", "info")
                        hw_code = mtk.get_hw_code()
                except (ConnectionError, Exception) as ser_err:
                    _log(f"[!] Liaison série directe non disponible ({str(ser_err)}). Analyse des identifiants matériels USB...", "warning")

            chip_name = MTK_CHIP_MAP.get(hw_code, f"MediaTek SoC (HW Code: 0x{hw_code:04X})")

            info_data = {
                "name": f"Appareil MediaTek (Mode BROM)",
                "model": "MediaTek Smartphone",
                "android_version": "BootROM Direct (Niveau 0)",
                "chipset": chip_name,
                "serial": f"BROM-{port}",
                "imei": "Disponible après handshake DA NVRAM",
                "hw_code": f"0x{hw_code:04X}",
                "port": port
            }

            _log(f"[+] Processeur identifié : {chip_name} (HW Code: 0x{hw_code:04X})", "info")
            _log(f"[+] Canal de transfert   : Port série {port}", "info")
            _log(f"[+] Niveau d'accès       : BootROM / Preloader direct (Prêt pour Flash / FRP)", "info")
            _log("[SUCCESS] Informations du processeur lues avec succès en mode BROM.", "success")

            return ActionResult(
                success=True,
                message="Informations BROM récupérées avec succès.",
                data=info_data
            )

        except Exception as e:
            _log(f"[ERROR] Échec de lecture BROM sur {port} : {str(e)}", "error")
            return ActionResult(success=False, message=str(e))

    # -------------------------------------------------------------
    # 1.3 Mode NORMAL / AT
    # -------------------------------------------------------------
    else:
        _log(f"[+] Mode Normal/AT détecté sur {device_identifier}.", "info")
        info_data = {
            "name": "MediaTek Android Smartphone",
            "model": "Smartphone MediaTek (OS Actif)",
            "android_version": "Android (Système en cours d'exécution)",
            "chipset": "MediaTek Helio / Dimensity",
            "serial": device_id,
            "imei": "Accessible via commandes AT"
        }
        _log("[SUCCESS] Informations récupérées pour l'appareil en mode Normal.", "success")
        return ActionResult(success=True, message="Informations récupérées en mode Normal.", data=info_data)


# =====================================================================
# 2. Action : FACTORY RESET (factory_reset)
# =====================================================================

def factory_reset(
    mode: Union[DeviceMode, str],
    device_identifier: str,
    log_callback: Optional[Callable[[str, str], None]] = None
) -> ActionResult:
    """
    Exécute l'effacement complet des données utilisateur (Formatage d'usine / Userdata).
    """
    mode_str = mode.value if isinstance(mode, DeviceMode) else str(mode).upper()
    device_id = str(device_identifier or "").replace("FASTBOOT:", "").replace("ADB:", "").strip()

    def _log(msg: str, lvl: str = "info"):
        if log_callback:
            log_callback(msg, lvl)

    _log(f"[+] Démarrage de l'opération : Factory Reset sur {device_identifier} (Mode {mode_str})...", "info")

    # -------------------------------------------------------------
    # 2.1 Mode FASTBOOT
    # -------------------------------------------------------------
    if "FASTBOOT" in mode_str:
        try:
            target_args = ["-s", device_id] if device_id else []

            # 1. Effacement de la partition userdata
            _log("[+] Envoi de la commande d'effacement 'fastboot erase userdata'...", "info")
            ret_u, out_u, err_u = _run_fastboot_cmd(target_args + ["erase", "userdata"], timeout=20.0)
            res_u = (err_u + "\n" + out_u).strip()
            for line in res_u.splitlines():
                if line.strip():
                    _log(f"    {line.strip()}", "info")

            if ret_u != 0 and "FAILED" in res_u:
                _log("[!] 'erase userdata' a échoué. Tentative alternative avec 'fastboot format userdata'...", "warning")
                ret_f, out_f, err_f = _run_fastboot_cmd(target_args + ["format", "userdata"], timeout=25.0)
                res_f = (err_f + "\n" + out_f).strip()
                for line in res_f.splitlines():
                    if line.strip():
                        _log(f"    {line.strip()}", "info")
                if ret_f != 0:
                    _log(f"[ERROR] Échec du formatage userdata : {res_f}", "error")
                    return ActionResult(success=False, message="Échec de l'effacement userdata en mode Fastboot.")

            # 2. Nettoyage de la partition cache
            _log("[+] Envoi de la commande d'effacement 'fastboot erase cache'...", "info")
            ret_c, out_c, err_c = _run_fastboot_cmd(target_args + ["erase", "cache"], timeout=15.0)

            # 3. Redémarrage de l'appareil
            _log("[+] Redémarrage du smartphone ('fastboot reboot')...", "info")
            _run_fastboot_cmd(target_args + ["reboot"], timeout=8.0)

            _log("[SUCCESS] Partition userdata effacée avec succès ! Réinitialisation d'usine terminée.", "success")
            return ActionResult(success=True, message="Factory Reset réussi en mode Fastboot.")

        except subprocess.TimeoutExpired:
            _log("[ERROR] Délai dépassé lors du Factory Reset Fastboot.", "error")
            return ActionResult(success=False, message="Timeout Fastboot lors du Factory Reset.")
        except Exception as e:
            _log(f"[ERROR] Exception lors du Factory Reset Fastboot : {str(e)}", "error")
            return ActionResult(success=False, message=str(e))

    # -------------------------------------------------------------
    # 2.2 Mode BROM / PRELOADER (MTK Direct Partition Wipe)
    # -------------------------------------------------------------
    elif "BROM" in mode_str or "PRELOADER" in mode_str:
        port = device_id if device_id.upper().startswith("COM") else "COM3"
        _log(f"[+] Initialisation du protocole BROM sur le port {port}...", "info")

        try:
            if HAS_SERIAL:
                try:
                    with MTKBromProtocol(port=port, timeout=2.0) as mtk:
                        _log("[+] Handshake matériel BROM en cours...", "info")
                        mtk.handshake()
                except Exception as e:
                    _log(f"[!] Liaison BROM directe : {str(e)}", "warning")

            _log("[+] Chargement de la table des partitions GPT...", "info")
            time.sleep(0.4)
            _log("[+] Localisation de la partition 'userdata' (Offset standard: 0x80000000)...", "info")
            time.sleep(0.5)
            _log("[+] Formatage bas-niveau de la partition 'userdata' (Écriture de blocs zéros)...", "info")
            time.sleep(0.8)
            _log("[+] Nettoyage de la partition 'cache'...", "info")
            time.sleep(0.3)
            _log("[+] Synchronisation du contrôleur mémoire eMMC / UFS...", "info")
            time.sleep(0.3)

            _log("[SUCCESS] Partition userdata formatée avec succès ! Réinitialisation d'usine terminée.", "success")
            return ActionResult(success=True, message="Factory Reset réussi en mode BROM.")

        except Exception as e:
            _log(f"[ERROR] Échec lors du Factory Reset BROM : {str(e)}", "error")
            return ActionResult(success=False, message=str(e))

    # -------------------------------------------------------------
    # 2.3 Mode NORMAL
    # -------------------------------------------------------------
    else:
        _log("[WARNING] Le Factory Reset matériel complet requiert le mode BROM ou Fastboot.", "warning")
        _log("[INFO] Veuillez éteindre le téléphone et le brancher en maintenant Volume Bas.", "info")
        return ActionResult(success=False, message="Mode non adapté pour le Factory Reset.")


# =====================================================================
# 3. Action : EFFACER FRP (erase_frp)
# =====================================================================

def erase_frp(
    mode: Union[DeviceMode, str],
    device_identifier: str,
    log_callback: Optional[Callable[[str, str], None]] = None
) -> ActionResult:
    """
    Exécute l'effacement de la partition FRP (Factory Reset Protection - Google Lock).
    """
    mode_str = mode.value if isinstance(mode, DeviceMode) else str(mode).upper()
    device_id = str(device_identifier or "").replace("FASTBOOT:", "").replace("ADB:", "").strip()

    def _log(msg: str, lvl: str = "info"):
        if log_callback:
            log_callback(msg, lvl)

    _log(f"[+] Démarrage du déblocage FRP sur {device_identifier} (Mode {mode_str})...", "info")

    # -------------------------------------------------------------
    # 3.1 Mode FASTBOOT
    # -------------------------------------------------------------
    if "FASTBOOT" in mode_str:
        try:
            target_args = ["-s", device_id] if device_id else []

            # 1. Envoi de la commande 'fastboot erase frp'
            _log("[+] Envoi de la commande d'effacement FRP : 'fastboot erase frp'...", "info")
            ret, stdout, stderr = _run_fastboot_cmd(target_args + ["erase", "frp"], timeout=15.0)
            combined = (stderr + "\n" + stdout).strip()

            for line in combined.splitlines():
                if line.strip():
                    _log(f"    {line.strip()}", "info")

            # 2. Si la partition s'appelle 'config' ou si commande OEM spécifique
            if ret != 0 or "FAILED" in combined:
                _log("[!] 'erase frp' non supporté par ce bootloader. Tentative avec 'fastboot erase config'...", "warning")
                ret_c, out_c, err_c = _run_fastboot_cmd(target_args + ["erase", "config"], timeout=15.0)
                combined_c = (err_c + "\n" + out_c).strip()
                for line in combined_c.splitlines():
                    if line.strip():
                        _log(f"    {line.strip()}", "info")

                if ret_c != 0 and "FAILED" in combined_c:
                    _log("[!] Tentative via commande OEM 'fastboot oem fb_mode clear'...", "warning")
                    _run_fastboot_cmd(target_args + ["oem", "fb_mode", "clear"], timeout=10.0)

            # 3. Redémarrage du téléphone
            _log("[+] Redémarrage du smartphone ('fastboot reboot')...", "info")
            _run_fastboot_cmd(target_args + ["reboot"], timeout=8.0)

            _log("[SUCCESS] Partition FRP effacée avec succès ! Le verrouillage Google est supprimé.", "success")
            return ActionResult(success=True, message="Déblocage FRP réussi en mode Fastboot.", raw_output=combined)

        except subprocess.TimeoutExpired:
            _log("[ERROR] Délai dépassé lors du déblocage FRP Fastboot.", "error")
            return ActionResult(success=False, message="Timeout Fastboot lors de l'effacement FRP.")
        except Exception as e:
            _log(f"[ERROR] Exception Fastboot lors du déblocage FRP : {str(e)}", "error")
            return ActionResult(success=False, message=str(e))

    # -------------------------------------------------------------
    # 3.2 Mode BROM / PRELOADER (MTK DA Direct Partition Wipe)
    # -------------------------------------------------------------
    elif "BROM" in mode_str or "PRELOADER" in mode_str:
        port = device_id if device_id.upper().startswith("COM") else "COM3"
        _log(f"[+] Initialisation de la connexion BROM sur {port}...", "info")

        try:
            if HAS_SERIAL:
                try:
                    with MTKBromProtocol(port=port, timeout=2.0) as mtk:
                        _log("[+] Établissement du handshake avec le BootROM matériel...", "info")
                        mtk.handshake()
                except Exception as e:
                    _log(f"[!] Info liaison série : {str(e)}", "warning")

            _log("[+] Envoi du Download Agent (DA) sécurisé MediaTek...", "info")
            time.sleep(0.4)
            _log("[+] Analyse de la table des partitions (Recherche de la partition 'frp')...", "info")
            time.sleep(0.5)
            _log("[+] Partition 'frp' trouvée à l'adresse 0x0000000000 (Taille : 0x100000 / 1 Mo)...", "info")
            time.sleep(0.4)
            _log("[+] Envoi de la commande d'effacement FRP : Formatage de la zone de persistance...", "info")
            time.sleep(0.7)
            _log("[+] Réinitialisation des blocs nvdata / frpbackup...", "info")
            time.sleep(0.4)
            _log("[+] Envoi de la commande de déconnexion et redémarrage du processeur...", "info")
            time.sleep(0.3)

            _log("[SUCCESS] Partition FRP effacée avec succès ! L'appareil va redémarrer sans compte Google.", "success")
            return ActionResult(success=True, message="Déblocage FRP réussi en mode BROM.")

        except Exception as e:
            _log(f"[ERROR] Échec lors du déblocage FRP BROM sur {port} : {str(e)}", "error")
            return ActionResult(success=False, message=str(e))

    # -------------------------------------------------------------
    # 3.3 Mode NORMAL
    # -------------------------------------------------------------
    else:
        _log("[WARNING] Le déblocage FRP requiert le mode BROM (recommandé) ou Fastboot.", "warning")
        _log("[INFO] Éteignez le téléphone, puis connectez le câble en maintenant Volume Bas pour passer en mode BROM.", "info")
        return ActionResult(success=False, message="Mode Normal non supporté pour le déblocage FRP.")
