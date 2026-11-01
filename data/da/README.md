# Répertoire Download Agents (`data/da/`)

Ce dossier est dédié aux fichiers Download Agent (DA) officiels et personnalisés pour processeurs MediaTek.

## Rôle en Atelier GSM
Le Download Agent est un mini-binaire exécuté dans la SRAM/DRAM du SoC cible lors de la négociation BROM pour :
- Initialiser le contrôleur de mémoire eMMC / UFS.
- Fournir un canal de communication haute vitesse pour les opérations de lecture/écriture de partitions.
- Déverrouiller les protections de sécurité SLA / DAA.

## Fichiers Types
- `MTK_AllInOne_DA.bin` : DA standard multi-processeurs (MT65xx, MT67xx).
- `DA_PL.bin` : Second stage Preloader DA.
- `DA_SWSEC.bin` : DA pour processeurs avec Secure Boot activé (Oppo, Realme, Vivo).
