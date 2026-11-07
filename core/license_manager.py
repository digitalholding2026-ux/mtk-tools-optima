# -*- coding: utf-8 -*-
"""
core/license_manager.py — Système de licence offline Optima MTK Tool.
Gère l'activation par token (5 tokens valides), la durée de validité (14 jours),
le stockage local (license.json) et le calcul du temps restant.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple


# ─── Tokens valides en dur ──────────────────────────────────────────────
VALID_TOKENS = [
    "OPTIMA-14D-A1B2",
    "OPTIMA-14D-C3D4",
    "OPTIMA-14D-E5F6",
    "OPTIMA-14D-G7H8",
    "OPTIMA-14D-I9J0",
]

LICENSE_DURATION_DAYS = 14


def _get_license_path() -> str:
    """Retourne le chemin du fichier license.json à la racine du projet."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "license.json")


class LicenseManager:
    """
    Gestionnaire de licence offline pour Optima MTK Tool.

    Responsabilités :
      - Valider un token d'activation parmi les 5 tokens autorisés.
      - Enregistrer la date d'activation + expiration (J+14) dans license.json.
      - Vérifier la validité de la licence (non expirée).
      - Calculer le temps restant (affichage type horloge compte à rebours).
      - Bloquer l'accès aux fonctions si la licence est expirée ou absente.
    """

    def __init__(self):
        self.license_path = _get_license_path()
        self._license_data: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Validation de token
    # ------------------------------------------------------------------
    def is_valid_token(self, token: str) -> bool:
        """Vérifie si un token figure dans la liste des 5 tokens valides."""
        return token.strip().upper() in [t.upper() for t in VALID_TOKENS]

    def activate_token(self, token: str) -> Tuple[bool, str]:
        """
        Active un token valide : écrit license.json avec date d'activation
        et date d'expiration (activation + 14 jours).
        """
        token = token.strip().upper()
        if not self.is_valid_token(token):
            return False, "Token invalide ou non reconnu."

        now = datetime.now()
        expiry = now + timedelta(days=LICENSE_DURATION_DAYS)

        license_data = {
            "token": token,
            "activated_at": now.isoformat(),
            "expires_at": expiry.isoformat(),
            "duration_days": LICENSE_DURATION_DAYS,
        }

        try:
            with open(self.license_path, "w", encoding="utf-8") as f:
                json.dump(license_data, f, indent=2, ensure_ascii=False)
            self._license_data = license_data
            return True, (
                f"Licence activée avec succès. Valide jusqu'au "
                f"{expiry.strftime('%d/%m/%Y %H:%M')}."
            )
        except Exception as e:
            return False, f"Erreur lors de l'enregistrement de la licence : {str(e)}"

    # ------------------------------------------------------------------
    # Lecture / état de la licence
    # ------------------------------------------------------------------
    def load_license(self) -> Optional[Dict[str, Any]]:
        """Charge les données de licence depuis license.json (en cache)."""
        if self._license_data is not None:
            return self._license_data
        if not os.path.exists(self.license_path):
            return None
        try:
            with open(self.license_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._license_data = data
            return data
        except Exception:
            return None

    def is_license_valid(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Vérifie si la licence est encore valide (non expirée).
        Retourne (is_valid, message, license_data).
        """
        data = self.load_license()
        if not data:
            return False, "Aucune licence trouvée. Veuillez activer un token.", None

        expires_at_str = data.get("expires_at")
        if not expires_at_str:
            return False, "Licence invalide (date d'expiration manquante).", data

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except Exception:
            return False, "Licence invalide (format de date incorrect).", data

        now = datetime.now()
        if now > expires_at:
            return (
                False,
                f"Licence expirée le {expires_at.strftime('%d/%m/%Y %H:%M')}. "
                "Veuillez réactiver un token.",
                data,
            )

        remaining = expires_at - now
        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(rem, 60)
        msg = f"Licence valide — Reste : {days}j {hours:02d}h {minutes:02d}m"
        return True, msg, data

    def get_time_remaining(self) -> Optional[timedelta]:
        """Retourne le temps restant avant expiration, ou None si pas de licence."""
        data = self.load_license()
        if not data:
            return None
        expires_at_str = data.get("expires_at")
        if not expires_at_str:
            return None
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except Exception:
            return None
        now = datetime.now()
        if now > expires_at:
            return timedelta(0)
        return expires_at - now

    def get_license_status_text(self) -> str:
        """Retourne le texte de statut de la licence pour l'affichage UI."""
        is_valid, msg, _ = self.is_license_valid()
        return msg

    def is_expired(self) -> bool:
        """Indique si la licence est expirée ou absente."""
        is_valid, _, _ = self.is_license_valid()
        return not is_valid
