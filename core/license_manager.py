# -*- coding: utf-8 -*-
"""
core/license_manager.py — Système de licence offline Optima MTK Tool.
Gère l'activation par token (lecture tokens.json / fallback intégré),
la durée de validité (14 jours), le stockage local (license.json)
et le calcul du temps restant. Journalise les erreurs dans error.log.
"""

import json
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List


# ─── Tokens valides (fallback) ───────────────────────────────────────────
VALID_TOKENS = [
    "OPTIMA-14D-A1B2",
    "OPTIMA-14D-C3D4",
    "OPTIMA-14D-E5F6",
    "OPTIMA-14D-G7H8",
    "OPTIMA-14D-I9J0",
]

LICENSE_DURATION_DAYS = 14


def get_base_dir() -> str:
    """Répertoire d'exécution absolu (compatible script et PyInstaller)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_license_path() -> str:
    """Chemin absolu de license.json."""
    return os.path.join(get_base_dir(), "license.json")


def get_tokens_path() -> str:
    """Chemin absolu de tokens.json."""
    return os.path.join(get_base_dir(), "tokens.json")


def get_error_log_path() -> str:
    """Chemin absolu de error.log."""
    return os.path.join(get_base_dir(), "error.log")


def log_error_to_file(message: str, exc: Optional[BaseException] = None) -> None:
    """Écrit un message d'erreur et sa trace dans error.log (ne lève jamais)."""
    try:
        log_path = get_error_log_path()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trace = traceback.format_exc() if exc is not None or sys.exc_info()[0] else ""
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
            if trace and trace.strip() != "NoneType: None":
                f.write(trace)
            f.write("-" * 80 + "\n")
    except Exception:
        # Dernier recours : ne jamais crasher sur le logging
        pass


def load_valid_tokens() -> List[str]:
    """Charge les tokens depuis tokens.json (chemin absolu) avec fallback."""
    tokens_path = get_tokens_path()
    try:
        if os.path.exists(tokens_path):
            with open(tokens_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Supporte: ["TOK1", ...] ou {"tokens": ["TOK1", ...]} ou {"valid_tokens": [...]}
            if isinstance(data, list):
                tokens = [str(t).strip().upper() for t in data if str(t).strip()]
            elif isinstance(data, dict):
                raw = data.get("tokens") or data.get("valid_tokens") or data.get("VALID_TOKENS") or []
                tokens = [str(t).strip().upper() for t in raw if str(t).strip()]
            else:
                tokens = []
            if tokens:
                return tokens
    except Exception as e:
        log_error_to_file(f"Lecture de tokens.json échouée ({tokens_path}) : {e}", e)
    return [t.strip().upper() for t in VALID_TOKENS]


# Compatibilité ascendante
_get_license_path = get_license_path


class LicenseManager:
    """
    Gestionnaire de licence offline pour Optima MTK Tool.

    Responsabilités :
      - Valider un token d'activation (tokens.json si présent, sinon fallback intégré).
      - Enregistrer la date d'activation + expiration (J+14) dans license.json.
      - Vérifier la validité de la licence (non expirée).
      - Calculer le temps restant (affichage type horloge compte à rebours).
      - Bloquer l'accès aux fonctions si la licence est expirée ou absente.
    """

    def __init__(self):
        self.base_dir = get_base_dir()
        self.license_path = get_license_path()
        self.tokens_path = get_tokens_path()
        self.error_log_path = get_error_log_path()
        self._license_data: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Validation de token
    # ------------------------------------------------------------------
    def is_valid_token(self, token: str) -> bool:
        """Vérifie si un token figure dans tokens.json (ou fallback intégré)."""
        token_norm = (token or "").strip().upper()
        if not token_norm:
            return False
        return token_norm in load_valid_tokens()

    def activate_token(self, token: str) -> Tuple[bool, str]:
        """
        Active un token valide : écrit license.json (chemin absolu) avec
        date d'activation et date d'expiration (activation + 14 jours).
        Retourne (ok, message). En cas d'exception, journalise dans error.log.
        """
        try:
            token_norm = (token or "").strip().upper()
            if not token_norm:
                return False, "Veuillez saisir un token d'activation."

            # Lecture/validation des tokens (tokens.json + fallback)
            valid_tokens = load_valid_tokens()
            if token_norm not in valid_tokens:
                return False, (
                    "Token invalide ou non reconnu.\n"
                    f"(Source tokens: {self.tokens_path})"
                )

            now = datetime.now()
            expiry = now + timedelta(days=LICENSE_DURATION_DAYS)

            license_data = {
                "token": token_norm,
                "activated_at": now.isoformat(),
                "expires_at": expiry.isoformat(),
                "duration_days": LICENSE_DURATION_DAYS,
            }

            # Écriture robuste de license.json (chemin absolu)
            license_dir = os.path.dirname(self.license_path)
            if license_dir and not os.path.exists(license_dir):
                os.makedirs(license_dir, exist_ok=True)
            with open(self.license_path, "w", encoding="utf-8") as f:
                json.dump(license_data, f, indent=2, ensure_ascii=False)

            self._license_data = license_data
            return True, (
                f"Licence activée avec succès. Valide jusqu'au "
                f"{expiry.strftime('%d/%m/%Y %H:%M')}."
            )
        except Exception as e:
            log_error_to_file(
                f"Erreur critique lors de l'activation de la licence "
                f"(token='{(token or '').strip()}', license_path='{self.license_path}', "
                f"tokens_path='{self.tokens_path}'): {e}",
                e,
            )
            return False, f"{type(e).__name__}: {e}"

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
