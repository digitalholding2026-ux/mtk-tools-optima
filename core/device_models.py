# -*- coding: utf-8 -*-
"""
Base de données des marques et modèles supportés par Optima MTK Tool.
Couvre les architectures MediaTek (SoC générique) et les constructeurs majeurs :
Infinix, Tecno, Samsung, Xiaomi, Oppo, Realme, Vivo.
"""

from typing import Dict, List, Any


# Marques principales supportées avec icône et identifiant
SUPPORTED_BRANDS = [
    {"id": "MEDIATEK", "name": "MediaTek", "icon": "⚡", "desc": "SoC Générique MTK (Tous modèles)"},
    {"id": "INFINIX",  "name": "Infinix",  "icon": "📱", "desc": "Séries Hot, Note, Smart, Zero"},
    {"id": "TECNO",    "name": "Tecno",    "icon": "🔥", "desc": "Séries Spark, Camon, Pova, Pop"},
    {"id": "SAMSUNG",  "name": "Samsung",  "icon": "🔵", "desc": "Galaxy Séries A, M MTK"},
    {"id": "XIAOMI",   "name": "Xiaomi",   "icon": "🟠", "desc": "Redmi, POCO Séries MTK"},
    {"id": "OPPO",     "name": "Oppo / Realme", "icon": "🟢", "desc": "Séries A, Reno, Realme C"},
    {"id": "VIVO",     "name": "Vivo",     "icon": "🟣", "desc": "Séries Y, V MTK"},
]

# Modèles par marque avec détails du chipset et méthodes supportées
DEVICES_DATABASE: Dict[str, List[Dict[str, Any]]] = {
    "MEDIATEK": [
        {"model": "MediaTek MT6765 (Helio G35 / P35)", "chipset": "MT6765", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6768 (Helio G85)", "chipset": "MT6768", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6769 (Helio G70 / G80)", "chipset": "MT6769", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6761 (Helio A22)", "chipset": "MT6761", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6762 (Helio P22)", "chipset": "MT6762", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6781 (Helio G96)", "chipset": "MT6781", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6785 (Helio G90T / G95)", "chipset": "MT6785", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6789 (Helio G99)", "chipset": "MT6789", "type": "Generic BROM/Preloader", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek MT6833 (Dimensity 700 / 6020)", "chipset": "MT6833", "type": "5G Dimensity", "modes": ["BROM", "FASTBOOT"]},
        {"model": "MediaTek MT6877 (Dimensity 900)", "chipset": "MT6877", "type": "5G Dimensity", "modes": ["BROM", "FASTBOOT"]},
        {"model": "MediaTek MT6893 (Dimensity 1200)", "chipset": "MT6893", "type": "5G Dimensity", "modes": ["BROM", "FASTBOOT"]},
        {"model": "MediaTek MT6580 (Legacy 3G)", "chipset": "MT6580", "type": "Legacy Smartphone", "modes": ["BROM", "META"]},
        {"model": "MediaTek MT6739 (Quad-Core 4G)", "chipset": "MT6739", "type": "Entry Level", "modes": ["BROM", "FASTBOOT", "META"]},
        {"model": "MediaTek Auto-Detect Universal", "chipset": "AUTO", "type": "Handshake matériel automatique", "modes": ["BROM", "FASTBOOT", "META"]},
    ],
    "INFINIX": [
        {"model": "Infinix Hot 11 Play (X688B)", "chipset": "MT6765 (Helio G35)", "type": "Hot Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Hot 10 Play (X688C)", "chipset": "MT6762 / MT6765", "type": "Hot Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Hot 12 Play (X6816)", "chipset": "MT6765 (Helio G35)", "type": "Hot Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Hot 20 (X6826)", "chipset": "MT6769 (Helio G85)", "type": "Hot Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Note 11 (X663)", "chipset": "MT6781 (Helio G88)", "type": "Note Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Note 12 (X663D)", "chipset": "MT6781 (Helio G88)", "type": "Note Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Smart 5 (X657)", "chipset": "MT6761 (Helio A20)", "type": "Smart Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Smart 6 (X6511)", "chipset": "MT6761 (Helio A22)", "type": "Smart Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Smart 7 (X6515)", "chipset": "MT6761 (Helio A22)", "type": "Smart Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Zero 5G (X6815)", "chipset": "MT6877 (Dimensity 900)", "type": "Zero Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Infinix Zero X Neo (X6810)", "chipset": "MT6785 (Helio G95)", "type": "Zero Series", "modes": ["BROM", "FASTBOOT"]},
    ],
    "TECNO": [
        {"model": "Tecno Spark 7 (KF6)", "chipset": "MT6761 / MT6765", "type": "Spark Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Spark 8 (KG6)", "chipset": "MT6762 (Helio P22)", "type": "Spark Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Spark 8C (KG5k)", "chipset": "MT6765 (Helio G35)", "type": "Spark Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Spark 9 (KH7)", "chipset": "MT6765 (Helio G37)", "type": "Spark Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Spark 10C (KI5k)", "chipset": "MT6765", "type": "Spark Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Camon 17 (CG6)", "chipset": "MT6769 (Helio G85)", "type": "Camon Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Camon 18 (CH6)", "chipset": "MT6781 (Helio G88)", "type": "Camon Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Camon 19 (CI6)", "chipset": "MT6781 (Helio G85)", "type": "Camon Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Camon 20 (CK6)", "chipset": "MT6781 (Helio G85)", "type": "Camon Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Pova 2 (LE7)", "chipset": "MT6769 (Helio G85)", "type": "Pova Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Pova 4 (LG7n)", "chipset": "MT6789 (Helio G99)", "type": "Pova Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Pop 5 (BD2p)", "chipset": "MT6580 / MT6761", "type": "Pop Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Tecno Pop 6 (BE7)", "chipset": "MT6761 (Helio A22)", "type": "Pop Series", "modes": ["BROM", "FASTBOOT"]},
    ],
    "SAMSUNG": [
        {"model": "Samsung Galaxy A01 Core (SM-A013F)", "chipset": "MT6739WW", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A02 (SM-A022F)", "chipset": "MT6739W", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A03s (SM-A037F)", "chipset": "MT6765 (Helio P35)", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A04 (SM-A045F)", "chipset": "MT6765 (Helio P35)", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A04e (SM-A042F)", "chipset": "MT6765", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A12 (SM-A125F)", "chipset": "MT6765 (Helio P35)", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A13 (SM-A137F)", "chipset": "MT6769 (Helio G80)", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A22 5G (SM-A226B)", "chipset": "MT6833 (Dimensity 700)", "type": "Galaxy A 5G", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy A32 (SM-A325F)", "chipset": "MT6769 (Helio G80)", "type": "Galaxy A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Samsung Galaxy M01 Core (SM-M013F)", "chipset": "MT6739WW", "type": "Galaxy M Series", "modes": ["BROM", "FASTBOOT"]},
    ],
    "XIAOMI": [
        {"model": "Xiaomi Redmi 6A (cactus)", "chipset": "MT6761 (Helio A22)", "type": "Redmi Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Xiaomi Redmi 9A (dandelion)", "chipset": "MT6762G (Helio G25)", "type": "Redmi Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Xiaomi Redmi 9C (angelica)", "chipset": "MT6765G (Helio G35)", "type": "Redmi Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Xiaomi Redmi 10A (dandelion_c3l2)", "chipset": "MT6762G (Helio G25)", "type": "Redmi Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Xiaomi Redmi Note 8 Pro (begonia)", "chipset": "MT6785 (Helio G90T)", "type": "Note Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Xiaomi Redmi Note 9 (merlin)", "chipset": "MT6769 (Helio G85)", "type": "Note Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Xiaomi Redmi Note 10S (rosemary)", "chipset": "MT6785 (Helio G95)", "type": "Note Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Xiaomi Redmi Note 11S (fleur)", "chipset": "MT6781 (Helio G96)", "type": "Note Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "POCO M3 Pro 5G (camellian)", "chipset": "MT6833 (Dimensity 700)", "type": "POCO Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "POCO C40 (frost)", "chipset": "JR510 / MTK Compatible", "type": "POCO Series", "modes": ["BROM", "FASTBOOT"]},
    ],
    "OPPO": [
        {"model": "Oppo A15 (CPH2185)", "chipset": "MT6765 (Helio P35)", "type": "Oppo A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Oppo A16 (CPH2269)", "chipset": "MT6765 (Helio G35)", "type": "Oppo A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Oppo A54 (CPH2239)", "chipset": "MT6765 (Helio P35)", "type": "Oppo A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Oppo A57 2022 (CPH2387)", "chipset": "MT6765 (Helio G35)", "type": "Oppo A Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Oppo Reno 6 5G (CPH2251)", "chipset": "MT6877 (Dimensity 900)", "type": "Reno Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Realme C11 2021 (RMX3231)", "chipset": "MT6765", "type": "Realme C Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Realme C21 (RMX3201)", "chipset": "MT6765 (Helio G35)", "type": "Realme C Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Realme C30 (RMX3581)", "chipset": "MT6765", "type": "Realme C Series", "modes": ["BROM", "FASTBOOT"]},
    ],
    "VIVO": [
        {"model": "Vivo Y12 (V1901)", "chipset": "MT6762 (Helio P22)", "type": "Vivo Y Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Vivo Y15 (V1901)", "chipset": "MT6762 (Helio P22)", "type": "Vivo Y Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Vivo Y20G (V2038)", "chipset": "MT6769 (Helio G80)", "type": "Vivo Y Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Vivo Y21 2021 (V2111)", "chipset": "MT6765 (Helio P35)", "type": "Vivo Y Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Vivo Y30 (V1938)", "chipset": "MT6765 (Helio P35)", "type": "Vivo Y Series", "modes": ["BROM", "FASTBOOT"]},
        {"model": "Vivo Y33s (V2109)", "chipset": "MT6769 (Helio G80)", "type": "Vivo Y Series", "modes": ["BROM", "FASTBOOT"]},
    ],
}


def get_all_brands() -> List[Dict[str, str]]:
    """Retourne la liste des marques supportées."""
    return SUPPORTED_BRANDS


def get_models_for_brand(brand_id: str) -> List[Dict[str, Any]]:
    """Retourne la liste des modèles pour une marque donnée."""
    return DEVICES_DATABASE.get(brand_id.upper(), DEVICES_DATABASE["MEDIATEK"])


def search_models(query: str, brand_id: str = None) -> List[Dict[str, Any]]:
    """Recherche dynamique de modèles par mot-clé et marque."""
    q = query.strip().lower()
    results = []

    if brand_id and brand_id.upper() in DEVICES_DATABASE:
        brands_to_search = [brand_id.upper()]
    else:
        brands_to_search = list(DEVICES_DATABASE.keys())

    for b in brands_to_search:
        for item in DEVICES_DATABASE[b]:
            target_str = f"{item['model']} {item['chipset']} {item.get('type', '')}".lower()
            if not q or q in target_str:
                results.append({**item, "brand_id": b})

    return results
