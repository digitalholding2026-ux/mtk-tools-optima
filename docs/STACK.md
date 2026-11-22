# STACK — Choix techniques

**Version** 1.0 · **Statut** : contrat · **Cible** : Windows 10/11 x64, poste de technicien, connexion USB.

## 1. Socle

| Choix | Version | Rôle |
|---|---|---|
| Python | 3.11+ | Langage unique du cœur et de l'interface. |
| PySide6 | 6.6+ | Interface graphique (LGPLv3, liaison dynamique). |
| pyusb | 1.2+ | Accès USB. |
| libusb | 1.0 | Backend USB (LGPLv2.1, DLL remplaçable). |
| SQLite | stdlib | Journal et données locales. |
| PyInstaller | 6.x | Empaquetage en mode *onedir*. |

## 2. Interface

- **PySide6** (Qt) : widgets, `QThread` et signaux pour ne jamais bloquer l'interface.
- **Pourquoi** : maturité, licence LGPLv3 compatible avec un produit propriétaire en liaison dynamique, documentation abondante, rendu natif Windows.
- **Rejeté** : PyQt (GPL ou licence commerciale), Tkinter (capacités limitées), Electron (poids et surface d'attaque), Kivy (orientation tactile).
- **Contrainte LGPL** : distribution en *onedir*, jamais *onefile*, afin que les bibliothèques Qt restent remplaçables par l'utilisateur.

## 3. Communication USB

- **pyusb + libusb**, pilote WinUSB installé via Zadig ; aucun appel direct à la WinAPI.
- Identifiants de référence : MediaTek preloader `VID 0x0E8D`, Qualcomm EDL `VID 0x05C6 / PID 0x9008`.
- La couche USB est isolée dans `adapters/usb/` ; elle expose des événements typés, pas des transferts bruts.
- Les moteurs MediaTek et Qualcomm restent appelés en sous-processus (voir ARCHITECTURE.md).

## 4. Stockage local

- **SQLite** (module `sqlite3`), fichier unique `optima.db`, mode WAL, schéma versionné par `PRAGMA user_version`.
- Tables principales : `appareils`, `operations`, `preuves`, `utilisateurs`, `audit`.
- **Audit** : ajout uniquement, déclencheurs interdisant `UPDATE` et `DELETE`, chaînage par SHA-256.
- **Preuves** : fichiers PDF ou images sur disque, empreinte en base, chiffrement applicatif des données sensibles.
- Export JSON pour l'interopérabilité, PDF via `QPdfWriter` pour les rapports.

## 5. Journalisation

- Une entrée d'audit par opération : horodatage UTC, opérateur, appareil, action, résultat, empreinte.
- La sortie brute des sous-processus est archivée à part, jamais dans le journal applicatif.
- Contrôle d'intégrité à chaque ouverture ; export signé sur demande.

## 6. Sécurité

- Aucun secret dans le dépôt ; secrets éventuels via DPAPI ou fichier local chiffré.
- Base et preuves chiffrées au repos ; accès par compte nominatif.
- Binaires signés, vérification de l'éditeur, mises à jour contrôlées par empreinte.

## 7. Build et qualité

- CI Windows : `ruff`, `mypy`, `pytest` et `pytest-qt`.
- Analyse de licences et SBOM à chaque build ; échec si une dépendance GPL apparaît dans le cœur.
- PyInstaller est sous GPL-2.0 avec exception d'usage : il peut empaqueter un logiciel propriétaire sans contamination, à condition de ne pas le modifier ni le distribuer comme bibliothèque.
- Empaquetage reproductible, version et empreinte publiées.

## 8. Invariants

1. Aucune dépendance GPL dans le cœur.
2. Toute opération matérielle passe par un sous-processus typé.
3. Une seule base SQLite, pas de fichiers texte pour les opérations.
4. L'interface ne bloque jamais ; annulation et reprise possibles.
5. Toute action sensible produit une entrée d'audit.