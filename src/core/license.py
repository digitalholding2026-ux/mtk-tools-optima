"""Gestion de licence — placeholder MVP.

Aucun import de `cryptography`, aucun appel réseau : la vérification réelle
sera branchée en phase 2.
"""

from __future__ import annotations

__all__ = ["check_license"]


def check_license() -> bool:
    """Placeholder MVP.

    Licence hybride (jeton Ed25519 + grâce hors ligne 72 h) prévue en phase 2
    (voir ARCHITECTURE.md).
    """
    return True