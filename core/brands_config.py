# -*- coding: utf-8 -*-
"""
core/brands_config.py — Configuration dynamique des fonctionnalités et menus par Marque.
Permet d'adapter dynamiquement l'interface graphique (onglets, boutons d'action,
badges et instructions d'atelier) selon la marque et le modèle sélectionnés.
"""

from typing import Dict, List, Any


# ─── Configuration complète des fonctionnalités par Marque ───────────────────

BRANDS_CONFIG: Dict[str, Dict[str, Any]] = {
    "MEDIATEK": {
        "name": "MediaTek Universal",
        "badge": "UNIVERSAL MTK",
        "icon": "⚡",
        "description": "Chipsets MediaTek MT65xx, MT67xx, MT68xx (Helio & Dimensity)",
        "workshop_instructions": [
            "• BROM Universel : Éteindre + Maintenir Vol- + Brancher câble USB",
            "• Fastboot Mode : Éteindre + Maintenir Vol- & Power",
            "• DAA/SLA Bypass : Indispensable pour SoC récents (Helio G90/G95/G99)",
            "• Pilotes requis : MediaTek USB VCOM Driver (cdc-acm.inf)",
        ],
        "actions": {
            "SECURITY": [
                {"key": "BROM_ERASE_FRP", "badge": "BROM", "title": "ERASE FRP (GOOGLE LOCK)", "subtitle": "Effacement partition persist matérielle", "color": "#10b981"},
                {"key": "FASTBOOT_ERASE_FRP", "badge": "FASTBOOT", "title": "ERASE FRP (OEM)", "subtitle": "Commandes fastboot erase frp/config", "color": "#06b6d4"},
                {"key": "BROM_UNLOCK_BL", "badge": "BROM", "title": "UNLOCK BOOTLOADER", "subtitle": "Déverrouille seccfg instantanément en BROM", "color": "#f59e0b"},
                {"key": "BROM_RELOCK_BL", "badge": "BROM", "title": "RELOCK BOOTLOADER", "subtitle": "Reverrouille la sécurité bootloader", "color": "#64748b"},
                {"key": "FASTBOOT_OEM_UNLOCK", "badge": "FASTBOOT", "title": "OEM UNLOCK (BL)", "subtitle": "fastboot flashing unlock / oem unlock", "color": "#3b82f6"},
                {"key": "BROM_AUTH_BYPASS", "badge": "BROM", "title": "DISABLE DAA / SLA", "subtitle": "Désactive la signature de sécurité MTK", "color": "#8b5cf6"},
            ],
            "FUNCTION": [
                {"key": "BROM_FACTORY_RESET", "badge": "BROM", "title": "FACTORY RESET (USERDATA)", "subtitle": "Formatage complet de la partition userdata", "color": "#ef4444"},
                {"key": "ADB_FACTORY_RESET", "badge": "ADB", "title": "FACTORY RESET (ADB)", "subtitle": "Réinitialisation usine via pont ADB actif", "color": "#ef4444"},
                {"key": "BROM_SAFE_FORMAT", "badge": "BROM", "title": "SAFE FORMAT (CACHE WIPE)", "subtitle": "Effacement sans supprimer les photos/données", "color": "#10b981"},
                {"key": "BROM_READ_INFO", "badge": "BROM", "title": "READ DEVICE INFO (HW)", "subtitle": "Lecture hardware code, chip ID, MEID", "color": "#3b82f6"},
                {"key": "BROM_REMOVE_DEMO", "badge": "BROM", "title": "REMOVE DEMO / PAYJOY", "subtitle": "Suppression des restrictions de démonstration", "color": "#8b5cf6"},
                {"key": "ADB_READ_INFO", "badge": "ADB", "title": "READ FULL SYSTEM SPECS", "subtitle": "Lecture version Android, build, IMEI via ADB", "color": "#06b6d4"},
                {"key": "REBOOT_FASTBOOT", "badge": "ADB", "title": "REBOOT TO FASTBOOT", "subtitle": "Redémarre l'appareil en Fastboot via ADB", "color": "#f59e0b"},
            ],
            "FASTBOOT": [
                {"key": "FASTBOOT_GETVAR", "badge": "FASTBOOT", "title": "READ INFO (GETVAR ALL)", "subtitle": "Inspection des variables globales bootloader", "color": "#06b6d4"},
                {"key": "FASTBOOT_ERASE_USERDATA", "badge": "FASTBOOT", "title": "ERASE USERDATA", "subtitle": "fastboot erase userdata & cache", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "FASTBOOT", "title": "REBOOT TO SYSTEM", "subtitle": "fastboot reboot", "color": "#10b981"},
                {"key": "REBOOT_RECOVERY", "badge": "FASTBOOT", "title": "REBOOT TO RECOVERY", "subtitle": "fastboot reboot recovery", "color": "#8b5cf6"},
                {"key": "REBOOT_FASTBOOT", "badge": "FASTBOOT", "title": "REBOOT TO BOOTLOADER", "subtitle": "fastboot reboot-bootloader", "color": "#3b82f6"},
                {"key": "FASTBOOT_OEM_CLEAR", "badge": "FASTBOOT", "title": "OEM FB_MODE CLEAR", "subtitle": "Suppression des drapeaux fabricant", "color": "#f59e0b"},
            ],
            "RECOVERY": [
                {"key": "RECOVERY_READ_INFO", "badge": "RECOVERY", "title": "READ RECOVERY SPECS", "subtitle": "Lecture statut sideload et OS version", "color": "#06b6d4"},
                {"key": "RECOVERY_FORMAT", "badge": "SIDELOAD", "title": "FACTORY RESET / WIPE", "subtitle": "Formatage via script de récupération", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "RECOVERY", "title": "REBOOT TO SYSTEM", "subtitle": "Redémarrage propre dans Android", "color": "#10b981"},
                {"key": "REBOOT_FASTBOOT", "badge": "RECOVERY", "title": "REBOOT TO BOOTLOADER", "subtitle": "Redémarrage direct vers Fastboot", "color": "#3b82f6"},
            ],
            "META": [
                {"key": "META_READ_INFO", "badge": "META", "title": "READ FACTORY INFO", "subtitle": "Lecture données d'usine, IMEI, Baseband", "color": "#8b5cf6"},
                {"key": "META_FACTORY_RESET", "badge": "META", "title": "FACTORY RESET (META)", "subtitle": "Remise à zéro sans perte de calibration", "color": "#ef4444"},
                {"key": "META_BACKUP_NV", "badge": "META", "title": "BACKUP NVRAM / NVDATA", "subtitle": "Sauvegarde de secours des partitions réseau", "color": "#f59e0b"},
                {"key": "META_REBOOT_NORMAL", "badge": "META", "title": "REBOOT TO NORMAL", "subtitle": "Sortie du mode Meta et redémarrage Android", "color": "#10b981"},
            ]
        }
    },

    "SAMSUNG": {
        "name": "Samsung Galaxy",
        "badge": "SAMSUNG GALAXY MTK",
        "icon": "🔵",
        "description": "Samsung Galaxy Séries A et M avec processeurs MediaTek",
        "workshop_instructions": [
            "• FRP Appel d'urgence (*#0*#) : Allumer -> Appel d'urgence -> Composer *#0*# -> Lancer l'action",
            "• BROM Knox FRP : Éteindre -> Maintenir Vol+ et Vol- -> Brancher le câble USB",
            "• Mode Download : Éteindre -> Maintenir Vol+ & Vol- -> Insérer câble -> Appuyer Vol+",
            "• Pilotes requis : Samsung Android USB Driver + MediaTek USB VCOM",
        ],
        "actions": {
            "SECURITY": [
                {"key": "SAMSUNG_FRP_TESTMODE", "badge": "MTP/ADB", "title": "FRP (*#0*# TEST MODE)", "subtitle": "Déblocage FRP via menu d'urgence et script ADB", "color": "#10b981"},
                {"key": "SAMSUNG_ERASE_FRP", "badge": "BROM", "title": "ERASE FRP (KNOX MTK)", "subtitle": "Suppression directe partition Knox/FRP en BROM", "color": "#8b5cf6"},
                {"key": "SAMSUNG_KNOX_ENROLL", "badge": "ADB", "title": "DISABLE KNOX ENROLLMENT", "subtitle": "Désactivation des services de verrouillage d'entreprise", "color": "#f59e0b"},
                {"key": "BROM_UNLOCK_BL", "badge": "BROM", "title": "UNLOCK BOOTLOADER (MTK)", "subtitle": "Déverrouille le bootloader Samsung MTK", "color": "#3b82f6"},
                {"key": "BROM_AUTH_BYPASS", "badge": "BROM", "title": "DISABLE SECURE BOOT (SLA)", "subtitle": "Contournement protection matérielle Samsung MTK", "color": "#8b5cf6"},
            ],
            "FUNCTION": [
                {"key": "SAMSUNG_READ_INFO_MTP", "badge": "MTP", "title": "READ INFO (MTP MODE)", "subtitle": "Lecture modèle, CSC, SN, version PDA/AP via MTP", "color": "#06b6d4"},
                {"key": "ADB_FACTORY_RESET", "badge": "ADB", "title": "FACTORY RESET (ADB)", "subtitle": "Réinitialisation usine complète via ADB actif", "color": "#ef4444"},
                {"key": "BROM_FACTORY_RESET", "badge": "BROM", "title": "FACTORY RESET (BROM)", "subtitle": "Formatage complet de la partition userdata en BROM", "color": "#ef4444"},
                {"key": "SAMSUNG_REBOOT_DOWNLOAD", "badge": "MTP/ADB", "title": "REBOOT DOWNLOAD MODE", "subtitle": "Basculement direct vers le mode Odin / Download", "color": "#3b82f6"},
                {"key": "ADB_READ_INFO", "badge": "ADB", "title": "READ SYSTEM SPECS (ADB)", "subtitle": "Vérification CSC, build et niveau de patch sécurité", "color": "#06b6d4"},
            ],
            "FASTBOOT": [
                {"key": "FASTBOOT_GETVAR", "badge": "FASTBOOT", "title": "READ INFO (GETVAR)", "subtitle": "Variables de démarrage et statut du bootloader", "color": "#06b6d4"},
                {"key": "REBOOT_NORMAL", "badge": "FASTBOOT", "title": "REBOOT TO SYSTEM", "subtitle": "Redémarrage classique vers One UI", "color": "#10b981"},
                {"key": "REBOOT_RECOVERY", "badge": "FASTBOOT", "title": "REBOOT TO RECOVERY", "subtitle": "Redémarrage vers le Recovery Stock", "color": "#8b5cf6"},
            ],
            "RECOVERY": [
                {"key": "RECOVERY_READ_INFO", "badge": "RECOVERY", "title": "READ RECOVERY SPECS", "subtitle": "Inspection version CSC/AP en mode Recovery", "color": "#06b6d4"},
                {"key": "RECOVERY_FORMAT", "badge": "SIDELOAD", "title": "WIPE DATA / FACTORY RESET", "subtitle": "Effacement complet via commande recovery", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "RECOVERY", "title": "REBOOT TO SYSTEM", "subtitle": "Sortie du mode Recovery et redémarrage", "color": "#10b981"},
            ],
            "META": [
                {"key": "META_READ_INFO", "badge": "META", "title": "READ FACTORY INFO", "subtitle": "Lecture IMEI et calibration modem en mode Meta", "color": "#8b5cf6"},
                {"key": "META_FACTORY_RESET", "badge": "META", "title": "FACTORY RESET (META)", "subtitle": "Formatage d'usine bas-niveau Samsung MTK", "color": "#ef4444"},
            ]
        }
    },

    "INFINIX": {
        "name": "Infinix Mobility",
        "badge": "INFINIX TRANSSION MTK",
        "icon": "📱",
        "description": "Smartphones Infinix Séries Hot, Note, Smart, Zero (SoC Helio/Dimensity)",
        "workshop_instructions": [
            "• Connexion BROM : Éteindre -> Maintenir Vol- (ou Vol+) -> Brancher câble USB",
            "• Déblocage MDM / PayJoy : Exécuter l'action en BROM avant le premier démarrage",
            "• Fastboot Mode : Éteindre -> Maintenir Vol- & Power jusqu'au logo Fastboot",
            "• Pilotes requis : MediaTek USB VCOM CDC ACM Driver",
        ],
        "actions": {
            "SECURITY": [
                {"key": "BROM_ERASE_FRP", "badge": "BROM", "title": "ERASE FRP (GOOGLE LOCK)", "subtitle": "Effacement FRP matériel pour puces Helio Infinix", "color": "#10b981"},
                {"key": "TRANSSION_REMOVE_MDM", "badge": "BROM", "title": "REMOVE MDM / PAYJOY", "subtitle": "Suppression verrous opérateur et finance Transsion", "color": "#8b5cf6"},
                {"key": "BROM_UNLOCK_BL", "badge": "BROM", "title": "UNLOCK BOOTLOADER (BROM)", "subtitle": "Déverrouille le bootloader sans délai d'attente", "color": "#f59e0b"},
                {"key": "FASTBOOT_ERASE_FRP", "badge": "FASTBOOT", "title": "FASTBOOT ERASE FRP", "subtitle": "fastboot erase frp sur partitions Transsion", "color": "#06b6d4"},
                {"key": "BROM_AUTH_BYPASS", "badge": "BROM", "title": "BYPASS SLA / DAA (SECURITY)", "subtitle": "Désactive la sécurité de handshake MediaTek", "color": "#8b5cf6"},
            ],
            "FUNCTION": [
                {"key": "BROM_FACTORY_RESET", "badge": "BROM", "title": "FACTORY RESET (USERDATA)", "subtitle": "Formatage complet userdata (supprime schémas/codes)", "color": "#ef4444"},
                {"key": "ADB_FACTORY_RESET", "badge": "ADB", "title": "FACTORY RESET (ADB)", "subtitle": "Remise aux paramètres d'usine via le pont ADB", "color": "#ef4444"},
                {"key": "BROM_SAFE_FORMAT", "badge": "BROM", "title": "SAFE FORMAT (CACHE WIPE)", "subtitle": "Wipe cache/dalvik sans toucher aux données personnelles", "color": "#10b981"},
                {"key": "BROM_READ_INFO", "badge": "BROM", "title": "READ HARDWARE INFO", "subtitle": "Dump MEID, Chip ID et table des partitions", "color": "#3b82f6"},
                {"key": "ADB_READ_INFO", "badge": "ADB", "title": "READ XOS SPECS (ADB)", "subtitle": "Lecture version XOS, build et patch sécurité", "color": "#06b6d4"},
                {"key": "REBOOT_FASTBOOT", "badge": "ADB", "title": "REBOOT TO FASTBOOT", "subtitle": "Redémarrage direct vers le bootloader Infinix", "color": "#f59e0b"},
            ],
            "FASTBOOT": [
                {"key": "FASTBOOT_GETVAR", "badge": "FASTBOOT", "title": "READ VARS (GETVAR ALL)", "subtitle": "Lecture paramètres de boot XOS", "color": "#06b6d4"},
                {"key": "FASTBOOT_ERASE_USERDATA", "badge": "FASTBOOT", "title": "ERASE USERDATA", "subtitle": "Effacement partition userdata en Fastboot", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "FASTBOOT", "title": "REBOOT TO SYSTEM", "subtitle": "Redémarrage propre sous XOS Android", "color": "#10b981"},
                {"key": "REBOOT_RECOVERY", "badge": "FASTBOOT", "title": "REBOOT TO RECOVERY", "subtitle": "Redémarrage vers le Recovery Infinix", "color": "#8b5cf6"},
            ],
            "RECOVERY": [
                {"key": "RECOVERY_READ_INFO", "badge": "RECOVERY", "title": "READ RECOVERY SPECS", "subtitle": "Inspection version XOS Recovery", "color": "#06b6d4"},
                {"key": "RECOVERY_FORMAT", "badge": "SIDELOAD", "title": "FACTORY RESET (WIPE)", "subtitle": "Formatage usine via Sideload", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "RECOVERY", "title": "REBOOT TO SYSTEM", "subtitle": "Sortie Recovery et redémarrage", "color": "#10b981"},
            ],
            "META": [
                {"key": "META_READ_INFO", "badge": "META", "title": "READ FACTORY SPECS", "subtitle": "Inspection calibration Transsion et IMEI", "color": "#8b5cf6"},
                {"key": "META_FACTORY_RESET", "badge": "META", "title": "FACTORY RESET (META)", "subtitle": "Remise à zéro sans affecter la calibration", "color": "#ef4444"},
                {"key": "META_BACKUP_NV", "badge": "META", "title": "BACKUP NVRAM / NVDATA", "subtitle": "Sauvegarde des partitions réseau et baseband", "color": "#f59e0b"},
            ]
        }
    },

    "TECNO": {
        "name": "Tecno Mobile",
        "badge": "TECNO TRANSSION MTK",
        "icon": "🔥",
        "description": "Smartphones Tecno Séries Spark, Camon, Pova, Pop (MTK Helio/Dimensity)",
        "workshop_instructions": [
            "• Connexion BROM : Éteindre -> Maintenir Vol- -> Insérer le câble USB",
            "• Séries Spark / Camon : Désactiver SLA/DAA si le handshake échoue",
            "• Suppression PayJoy / MDM : Lancer l'action en BROM avec batterie chargée à 50%+",
            "• Pilotes requis : MediaTek USB VCOM CDC ACM Driver",
        ],
        "actions": {
            "SECURITY": [
                {"key": "BROM_ERASE_FRP", "badge": "BROM", "title": "ERASE FRP (GOOGLE LOCK)", "subtitle": "Effacement direct FRP partition persist pour Tecno", "color": "#10b981"},
                {"key": "TRANSSION_REMOVE_MDM", "badge": "BROM", "title": "REMOVE MDM / PAYJOY", "subtitle": "Suppression des restrictions de paiement Tecno", "color": "#8b5cf6"},
                {"key": "BROM_UNLOCK_BL", "badge": "BROM", "title": "UNLOCK BOOTLOADER (BROM)", "subtitle": "Déverrouille le bootloader instantanément", "color": "#f59e0b"},
                {"key": "FASTBOOT_ERASE_FRP", "badge": "FASTBOOT", "title": "FASTBOOT ERASE FRP", "subtitle": "fastboot erase frp/config", "color": "#06b6d4"},
                {"key": "BROM_AUTH_BYPASS", "badge": "BROM", "title": "BYPASS SLA / DAA", "subtitle": "Désactive la sécurité de démarrage sécurisé MTK", "color": "#8b5cf6"},
            ],
            "FUNCTION": [
                {"key": "BROM_FACTORY_RESET", "badge": "BROM", "title": "FACTORY RESET (USERDATA)", "subtitle": "Formatage complet userdata (supprime schémas/PIN)", "color": "#ef4444"},
                {"key": "ADB_FACTORY_RESET", "badge": "ADB", "title": "FACTORY RESET (ADB)", "subtitle": "Réinitialisation usine via pont ADB actif", "color": "#ef4444"},
                {"key": "BROM_SAFE_FORMAT", "badge": "BROM", "title": "SAFE FORMAT (CACHE WIPE)", "subtitle": "Nettoyage du cache sans supprimer les données", "color": "#10b981"},
                {"key": "BROM_READ_INFO", "badge": "BROM", "title": "READ HARDWARE INFO", "subtitle": "Lecture HW code, chip ID et serial", "color": "#3b82f6"},
                {"key": "ADB_READ_INFO", "badge": "ADB", "title": "READ HIOS SPECS (ADB)", "subtitle": "Lecture version HiOS, build et patch sécurité", "color": "#06b6d4"},
                {"key": "REBOOT_FASTBOOT", "badge": "ADB", "title": "REBOOT TO FASTBOOT", "subtitle": "Redémarrage direct vers le bootloader Tecno", "color": "#f59e0b"},
            ],
            "FASTBOOT": [
                {"key": "FASTBOOT_GETVAR", "badge": "FASTBOOT", "title": "READ VARS (GETVAR ALL)", "subtitle": "Variables système et statut bootloader", "color": "#06b6d4"},
                {"key": "FASTBOOT_ERASE_USERDATA", "badge": "FASTBOOT", "title": "ERASE USERDATA", "subtitle": "Effacement partition userdata en Fastboot", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "FASTBOOT", "title": "REBOOT TO SYSTEM", "subtitle": "Redémarrage sous HiOS Android", "color": "#10b981"},
                {"key": "REBOOT_RECOVERY", "badge": "FASTBOOT", "title": "REBOOT TO RECOVERY", "subtitle": "Redémarrage vers le Recovery Tecno", "color": "#8b5cf6"},
            ],
            "RECOVERY": [
                {"key": "RECOVERY_READ_INFO", "badge": "RECOVERY", "title": "READ RECOVERY SPECS", "subtitle": "Inspection version HiOS Recovery", "color": "#06b6d4"},
                {"key": "RECOVERY_FORMAT", "badge": "SIDELOAD", "title": "FACTORY RESET (WIPE)", "subtitle": "Formatage usine via Sideload", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "RECOVERY", "title": "REBOOT TO SYSTEM", "subtitle": "Sortie Recovery et redémarrage", "color": "#10b981"},
            ],
            "META": [
                {"key": "META_READ_INFO", "badge": "META", "title": "READ FACTORY SPECS", "subtitle": "Inspection calibration Tecno et IMEI", "color": "#8b5cf6"},
                {"key": "META_FACTORY_RESET", "badge": "META", "title": "FACTORY RESET (META)", "subtitle": "Remise à zéro sans affecter la calibration", "color": "#ef4444"},
                {"key": "META_BACKUP_NV", "badge": "META", "title": "BACKUP NVRAM / NVDATA", "subtitle": "Sauvegarde des partitions réseau et baseband", "color": "#f59e0b"},
            ]
        }
    },

    "XIAOMI": {
        "name": "Xiaomi / Redmi / POCO",
        "badge": "XIAOMI REDMI MTK",
        "icon": "🟠",
        "description": "Appareils Xiaomi, Redmi et POCO équipés de puces MediaTek",
        "workshop_instructions": [
            "• BROM Mode : Éteindre -> Maintenir Vol- -> Brancher câble USB (TestPoint si sécurisé)",
            "• Mi Account Bypass : Effectuer en BROM avant de connecter l'appareil au Wi-Fi",
            "• Fastboot Mode : Éteindre -> Maintenir Vol- & Power jusqu'au logo FASTBOOT",
            "• Recovery Mi Assistant : Éteindre -> Maintenir Vol+ & Power -> Connect with MIAssistant",
        ],
        "actions": {
            "SECURITY": [
                {"key": "XIAOMI_MI_ACCOUNT_BYPASS", "badge": "BROM", "title": "BYPASS MI ACCOUNT", "subtitle": "Désactivation du verrouillage compte Mi Cloud MTK", "color": "#8b5cf6"},
                {"key": "BROM_ERASE_FRP", "badge": "BROM", "title": "ERASE FRP (GOOGLE LOCK)", "subtitle": "Suppression partition FRP persist matérielle", "color": "#10b981"},
                {"key": "FASTBOOT_OEM_UNLOCK", "badge": "FASTBOOT", "title": "UNLOCK BOOTLOADER (FASTBOOT)", "subtitle": "Déverrouillage bootloader Mi Flash / Fastboot", "color": "#3b82f6"},
                {"key": "FASTBOOT_ERASE_FRP", "badge": "FASTBOOT", "title": "FASTBOOT ERASE FRP", "subtitle": "Effacement partition FRP via commandes Fastboot", "color": "#06b6d4"},
                {"key": "BROM_AUTH_BYPASS", "badge": "BROM", "title": "DISABLE SLA / DAA (SECURITY)", "subtitle": "Bypass de l'authentification serveur Xiaomi MTK", "color": "#8b5cf6"},
            ],
            "FUNCTION": [
                {"key": "BROM_FACTORY_RESET", "badge": "BROM", "title": "FACTORY RESET (USERDATA)", "subtitle": "Formatage complet userdata (supprime schémas/codes)", "color": "#ef4444"},
                {"key": "ADB_FACTORY_RESET", "badge": "ADB", "title": "FACTORY RESET (ADB)", "subtitle": "Réinitialisation usine via pont ADB actif", "color": "#ef4444"},
                {"key": "BROM_READ_INFO", "badge": "BROM", "title": "READ DEVICE INFO (HW)", "subtitle": "Lecture nom de code (ex: begonia, merlin, rosemary)", "color": "#3b82f6"},
                {"key": "ADB_READ_INFO", "badge": "ADB", "title": "READ MIUI / HYPEROS SPECS", "subtitle": "Vérification version MIUI/HyperOS, région et build", "color": "#06b6d4"},
                {"key": "REBOOT_FASTBOOT", "badge": "ADB", "title": "REBOOT TO FASTBOOT", "subtitle": "Redémarrage direct vers le bootloader Xiaomi", "color": "#f59e0b"},
            ],
            "FASTBOOT": [
                {"key": "FASTBOOT_GETVAR", "badge": "FASTBOOT", "title": "READ GETVAR ALL (SPECS)", "subtitle": "Vérification statut lock/unlock et version produit", "color": "#06b6d4"},
                {"key": "FASTBOOT_ERASE_USERDATA", "badge": "FASTBOOT", "title": "ERASE USERDATA", "subtitle": "Formatage userdata via protocole Fastboot", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "FASTBOOT", "title": "REBOOT TO SYSTEM", "subtitle": "fastboot reboot", "color": "#10b981"},
                {"key": "REBOOT_RECOVERY", "badge": "FASTBOOT", "title": "REBOOT TO RECOVERY", "subtitle": "Redémarrage vers Mi Recovery", "color": "#8b5cf6"},
            ],
            "RECOVERY": [
                {"key": "RECOVERY_READ_INFO", "badge": "RECOVERY", "title": "READ MI ASSISTANT SPECS", "subtitle": "Lecture statut appareil via protocole Sideload Mi", "color": "#06b6d4"},
                {"key": "RECOVERY_FORMAT", "badge": "SIDELOAD", "title": "WIPE ALL DATA (SIDELOAD)", "subtitle": "Formatage d'usine via protocole Recovery", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "RECOVERY", "title": "REBOOT TO SYSTEM", "subtitle": "Redémarrage du système Android", "color": "#10b981"},
            ],
            "META": [
                {"key": "META_READ_INFO", "badge": "META", "title": "READ FACTORY SPECS", "subtitle": "Lecture IMEI et calibrage modem Xiaomi MTK", "color": "#8b5cf6"},
                {"key": "META_BACKUP_NV", "badge": "META", "title": "BACKUP NVRAM / NVDATA", "subtitle": "Sauvegarde de secours des partitions réseau Xiaomi", "color": "#f59e0b"},
            ]
        }
    },

    "OPPO": {
        "name": "Oppo / Realme",
        "badge": "OPPO REALME MTK",
        "icon": "🟢",
        "description": "Smartphones Oppo Séries A/Reno et Realme Séries C/Narzo MTK",
        "workshop_instructions": [
            "• Connexion BROM : Éteindre -> Maintenir Vol+ et Vol- -> Brancher câble USB",
            "• Fastboot Mode : Éteindre -> Maintenir Vol- & Power",
            "• Oppo ID / HeyTap : Effectuer en BROM sans carte SIM insérée",
            "• Pilotes requis : Oppo Preloader Driver + MediaTek USB VCOM",
        ],
        "actions": {
            "SECURITY": [
                {"key": "OPPO_ID_BYPASS", "badge": "BROM", "title": "BYPASS OPPO ID / HEYTAP", "subtitle": "Contournement compte de sécurité Oppo/Realme", "color": "#8b5cf6"},
                {"key": "BROM_ERASE_FRP", "badge": "BROM", "title": "ERASE FRP (GOOGLE LOCK)", "subtitle": "Suppression partition FRP persist matérielle", "color": "#10b981"},
                {"key": "BROM_UNLOCK_BL", "badge": "BROM", "title": "UNLOCK BOOTLOADER (BROM)", "subtitle": "Déverrouille le bootloader sans compte développeur", "color": "#f59e0b"},
                {"key": "FASTBOOT_ERASE_FRP", "badge": "FASTBOOT", "title": "FASTBOOT ERASE FRP", "subtitle": "fastboot erase frp sur partitions ColorOS", "color": "#06b6d4"},
                {"key": "BROM_AUTH_BYPASS", "badge": "BROM", "title": "BYPASS SECURE BOOT (SLA)", "subtitle": "Désactive la sécurité de handshake ColorOS", "color": "#8b5cf6"},
            ],
            "FUNCTION": [
                {"key": "BROM_FACTORY_RESET", "badge": "BROM", "title": "FACTORY RESET (USERDATA)", "subtitle": "Formatage complet userdata (supprime schémas/mots de passe)", "color": "#ef4444"},
                {"key": "ADB_FACTORY_RESET", "badge": "ADB", "title": "FACTORY RESET (ADB)", "subtitle": "Réinitialisation usine via pont ADB actif", "color": "#ef4444"},
                {"key": "BROM_SAFE_FORMAT", "badge": "BROM", "title": "SAFE FORMAT (CACHE WIPE)", "subtitle": "Nettoyage du cache sans supprimer les photos/données", "color": "#10b981"},
                {"key": "BROM_READ_INFO", "badge": "BROM", "title": "READ HARDWARE INFO", "subtitle": "Lecture HW code, chip ID et serial Oppo", "color": "#3b82f6"},
                {"key": "ADB_READ_INFO", "badge": "ADB", "title": "READ COLOROS SPECS", "subtitle": "Lecture version ColorOS/RealmeUI et build", "color": "#06b6d4"},
                {"key": "REBOOT_FASTBOOT", "badge": "ADB", "title": "REBOOT TO FASTBOOT", "subtitle": "Redémarrage direct vers le bootloader ColorOS", "color": "#f59e0b"},
            ],
            "FASTBOOT": [
                {"key": "FASTBOOT_GETVAR", "badge": "FASTBOOT", "title": "READ VARS (GETVAR ALL)", "subtitle": "Variables système et statut bootloader", "color": "#06b6d4"},
                {"key": "FASTBOOT_ERASE_USERDATA", "badge": "FASTBOOT", "title": "ERASE USERDATA", "subtitle": "Effacement partition userdata en Fastboot", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "FASTBOOT", "title": "REBOOT TO SYSTEM", "subtitle": "Redémarrage sous ColorOS Android", "color": "#10b981"},
            ],
            "RECOVERY": [
                {"key": "RECOVERY_READ_INFO", "badge": "RECOVERY", "title": "READ RECOVERY SPECS", "subtitle": "Inspection version ColorOS Recovery", "color": "#06b6d4"},
                {"key": "RECOVERY_FORMAT", "badge": "SIDELOAD", "title": "WIPE DATA / FACTORY RESET", "subtitle": "Formatage usine via Sideload", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "RECOVERY", "title": "REBOOT TO SYSTEM", "subtitle": "Sortie Recovery et redémarrage", "color": "#10b981"},
            ],
            "META": [
                {"key": "META_READ_INFO", "badge": "META", "title": "READ FACTORY SPECS", "subtitle": "Inspection calibration Oppo et IMEI", "color": "#8b5cf6"},
                {"key": "META_BACKUP_NV", "badge": "META", "title": "BACKUP NVRAM / NVDATA", "subtitle": "Sauvegarde des partitions réseau ColorOS", "color": "#f59e0b"},
            ]
        }
    },

    "VIVO": {
        "name": "Vivo Mobile",
        "badge": "VIVO FUNTOUCH MTK",
        "icon": "🟣",
        "description": "Smartphones Vivo Séries Y et V équipés de puces MediaTek",
        "workshop_instructions": [
            "• Connexion BROM : Éteindre -> Maintenir Vol- & Vol+ -> Brancher câble USB",
            "• Suppression Demo Mode : Exécuter l'action en BROM puis redémarrer",
            "• Fastboot Mode : Éteindre -> Maintenir Vol+ & Power -> Choisir Fastboot",
            "• Pilotes requis : Vivo USB Driver + MediaTek USB VCOM",
        ],
        "actions": {
            "SECURITY": [
                {"key": "BROM_REMOVE_DEMO", "badge": "BROM", "title": "REMOVE DEMO MODE (VIVO)", "subtitle": "Suppression définitive des restrictions magasin Vivo", "color": "#8b5cf6"},
                {"key": "BROM_ERASE_FRP", "badge": "BROM", "title": "ERASE FRP (GOOGLE LOCK)", "subtitle": "Effacement direct partition persist FRP Vivo", "color": "#10b981"},
                {"key": "BROM_UNLOCK_BL", "badge": "BROM", "title": "UNLOCK BOOTLOADER (BROM)", "subtitle": "Déverrouille le bootloader instantanément", "color": "#f59e0b"},
                {"key": "FASTBOOT_ERASE_FRP", "badge": "FASTBOOT", "title": "FASTBOOT ERASE FRP", "subtitle": "fastboot erase frp sur partitions FuntouchOS", "color": "#06b6d4"},
                {"key": "BROM_AUTH_BYPASS", "badge": "BROM", "title": "BYPASS SLA / DAA (SECURITY)", "subtitle": "Désactive la sécurité de handshake Vivo MTK", "color": "#8b5cf6"},
            ],
            "FUNCTION": [
                {"key": "BROM_FACTORY_RESET", "badge": "BROM", "title": "FACTORY RESET (USERDATA)", "subtitle": "Formatage complet userdata (supprime schémas/codes)", "color": "#ef4444"},
                {"key": "ADB_FACTORY_RESET", "badge": "ADB", "title": "FACTORY RESET (ADB)", "subtitle": "Réinitialisation usine via pont ADB actif", "color": "#ef4444"},
                {"key": "BROM_SAFE_FORMAT", "badge": "BROM", "title": "SAFE FORMAT (CACHE WIPE)", "subtitle": "Nettoyage du cache sans supprimer les données", "color": "#10b981"},
                {"key": "BROM_READ_INFO", "badge": "BROM", "title": "READ HARDWARE INFO", "subtitle": "Lecture HW code, chip ID et serial Vivo", "color": "#3b82f6"},
                {"key": "ADB_READ_INFO", "badge": "ADB", "title": "READ FUNTOUCHOS SPECS", "subtitle": "Lecture version FuntouchOS/OriginOS et build", "color": "#06b6d4"},
                {"key": "REBOOT_FASTBOOT", "badge": "ADB", "title": "REBOOT TO FASTBOOT", "subtitle": "Redémarrage direct vers le bootloader Vivo", "color": "#f59e0b"},
            ],
            "FASTBOOT": [
                {"key": "FASTBOOT_GETVAR", "badge": "FASTBOOT", "title": "READ VARS (GETVAR ALL)", "subtitle": "Variables système et statut bootloader", "color": "#06b6d4"},
                {"key": "FASTBOOT_ERASE_USERDATA", "badge": "FASTBOOT", "title": "ERASE USERDATA", "subtitle": "Effacement partition userdata en Fastboot", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "FASTBOOT", "title": "REBOOT TO SYSTEM", "subtitle": "Redémarrage sous FuntouchOS Android", "color": "#10b981"},
            ],
            "RECOVERY": [
                {"key": "RECOVERY_READ_INFO", "badge": "RECOVERY", "title": "READ RECOVERY SPECS", "subtitle": "Inspection version Vivo Recovery", "color": "#06b6d4"},
                {"key": "RECOVERY_FORMAT", "badge": "SIDELOAD", "title": "WIPE DATA / FACTORY RESET", "subtitle": "Formatage usine via Sideload", "color": "#ef4444"},
                {"key": "REBOOT_NORMAL", "badge": "RECOVERY", "title": "REBOOT TO SYSTEM", "subtitle": "Sortie Recovery et redémarrage", "color": "#10b981"},
            ],
            "META": [
                {"key": "META_READ_INFO", "badge": "META", "title": "READ FACTORY SPECS", "subtitle": "Inspection calibration Vivo et IMEI", "color": "#8b5cf6"},
                {"key": "META_BACKUP_NV", "badge": "META", "title": "BACKUP NVRAM / NVDATA", "subtitle": "Sauvegarde des partitions réseau Vivo", "color": "#f59e0b"},
            ]
        }
    }
}


# ─── Fonctions d'accès et d'aide ─────────────────────────────────────────────

def get_brand_config(brand_id: str) -> Dict[str, Any]:
    """Retourne la configuration complète pour une marque donnée."""
    b_id = (brand_id or "MEDIATEK").upper()
    return BRANDS_CONFIG.get(b_id, BRANDS_CONFIG["MEDIATEK"])


def get_brand_actions(brand_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Retourne le dictionnaire des actions par catégorie pour une marque."""
    cfg = get_brand_config(brand_id)
    return cfg.get("actions", BRANDS_CONFIG["MEDIATEK"]["actions"])


def get_brand_instructions(brand_id: str) -> List[str]:
    """Retourne les conseils et instructions d'atelier spécifiques à la marque."""
    cfg = get_brand_config(brand_id)
    return cfg.get("workshop_instructions", BRANDS_CONFIG["MEDIATEK"]["workshop_instructions"])


def get_brand_badge(brand_id: str) -> str:
    """Retourne le texte de badge pour la marque."""
    cfg = get_brand_config(brand_id)
    return cfg.get("badge", f"{brand_id.upper()} MTK")
