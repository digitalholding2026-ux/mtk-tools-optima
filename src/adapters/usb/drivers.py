"""Diagnostic des pilotes USB — lecture seule.

Aucune installation automatique : ce module se contente de vérifier la
présence des pilotes et, sur demande explicite, d'ouvrir le script PowerShell
d'aide à l'installation dans l'explorateur.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

__all__ = ["check_backend", "check_drivers", "get_backend_path", "open_installer_script"]

_LOGGER = logging.getLogger(__name__)

_MTK_MARKER = "MTK_VCOM"
_QUALCOMM_MARKER = "QUALCOMM_9008"

_PS_QUERY = """
$mtk = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object {
        $_.InstanceId -match 'VID_0E8D' -and
        ($_.FriendlyName -match 'VCOM|PreLoader|Preloader')
    }
$qualcomm = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object {
        $_.InstanceId -match 'VID_05C6&PID_9008' -or
        $_.FriendlyName -match 'QDLoader 9008'
    }
if ($mtk) { 'MTK_VCOM' }
if ($qualcomm) { 'QUALCOMM_9008' }
"""


def _backend_candidates() -> list[Path]:
    cwd = Path.cwd()
    try:
        python_dir = Path(sys.executable).resolve().parent
    except OSError:
        python_dir = cwd
    return [
        cwd / "libusb-1.0.dll",
        cwd / "drivers" / "libusb-1.0.dll",
        python_dir / "libusb-1.0.dll",
    ]


def get_backend_path() -> Path | None:
    """Retourne le premier libusb-1.0.dll trouvé, ou None."""
    for candidate in _backend_candidates():
        if candidate.exists():
            return candidate
    return None


def check_backend() -> bool:
    """Vérifie la présence de libusb-1.0.dll, sans appel réseau."""
    return get_backend_path() is not None


def check_drivers() -> dict[str, bool]:
    """Retourne la présence des pilotes MediaTek VCOM, Qualcomm 9008 et du backend."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_QUERY],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _LOGGER.warning(
            "driver_check_failed",
            extra={"event": "driver_check_failed", "payload": {"error": str(exc)}},
        )
        return {
            "mtk_vcom": False,
            "qualcomm_9008": False,
            "libusb_backend": check_backend(),
        }

    output = (result.stdout or "").upper()
    return {
        "mtk_vcom": _MTK_MARKER in output,
        "qualcomm_9008": _QUALCOMM_MARKER in output,
        "libusb_backend": check_backend(),
    }


def open_installer_script() -> Path:
    """Retourne le chemin du script d'installation et l'ouvre dans l'explorateur."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "install_drivers.ps1"
    if not script.is_file():
        raise FileNotFoundError(f"Script d'installation introuvable : {script}")

    subprocess.Popen(["explorer", str(script)])
    return script