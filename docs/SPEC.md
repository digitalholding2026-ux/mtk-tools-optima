# SPEC — MVP Optima Telecom Flash Tool

**Version** 1.0 · **Statut** : contrat de cadrage, gelé jusqu'à validation · **Langue** : français

## 1. Objet et positionnement

MVP mono-poste, mono-technicien, un appareil à la fois. Il couvre le parcours « détection → lecture → flash → FRP → preuve ». Sont hors de cette étape : le cloud, la facturation, les tokens et la version gratuite ; ces éléments relèvent de la phase 2 et ne doivent apparaître dans aucun module du MVP.

## 2. Fonctionnalités prioritaires (5)

Le journal d'opérations et la gestion des autorisations client constituent un seul sous-système de traçabilité : ils sont donc regroupés en F5.

### F1 — Détection automatique du chipset
- Énumération USB, identification du VID/PID, du mode de connexion (normal, preloader, EDL 9008, fastboot) et du fabricant (MediaTek ou Qualcomm).
- Bascule automatique en mode téléchargement lorsque l'appareil le permet.
- Sélection du moteur correspondant (mtkclient ou edl) et affichage du diagnostic.
- Critère : ≥ 95 % des appareils du parc de test détectés en moins de 10 s, sans intervention manuelle.

### F2 — Lecture des informations
- Collecte non destructive : modèle, identifiants plateforme, état du chargeur d'amorçage, liste des partitions, version du micrologiciel.
- Affichage synthétique et export JSON horodaté.
- Critère : aucune écriture sur l'appareil ; chaque champ est marqué « fiable » ou « inconnu ».

### F3 — Flash de partitions
- Sélection d'images par partition, sauvegarde préalable optionnelle, vérification après écriture.
- Garde-fous : refus si batterie < 30 %, image de taille incohérente, ou partition critique non sauvegardée.
- Critère : reflash complet d'un appareil de référence sans perte de fonctionnalité.

### F4 — Effacement FRP
- Effacement de la partition FRP ou des données utilisateur, après autorisation client (F5) et confirmation explicite.
- Contrôle post-redémarrage : le compte n'est plus demandé.
- Critère : parcours complet validé sur trois appareils de test de marques différentes.

### F5 — Traçabilité : journal d'opérations et autorisations client
- Journal append-only : opérateur, appareil (IMEI ou identifiant), horodatage UTC, action, paramètres, résultat, empreinte de la preuve.
- Autorisations : dépôt de la preuve écrite du propriétaire, vérification de concordance IMEI, décision motivée (accordée ou refusée).
- Critère : chaque opération F3 ou F4 est retrouvable et rattachée à une preuve valide.

## 3. Exigences transverses

- Audit : toute écriture produit une entrée de journal immuable et exportable.
- Ergonomie : le parcours F4 est réalisable en moins de cinq minutes, sans connaissance technique.
- Fiabilité : annulation propre, reprise après erreur, interface jamais bloquée.
- Sécurité : aucun secret en clair, aucune donnée client transmise sur le réseau.

## 4. Hors périmètre (3 exclusions)

- **H1 —** Root, déverrouillage du chargeur d'amorçage et réparation d'IMEI.
- **H2 —** Contournement de l'écran de verrouillage ou d'un compte antivol autre que le FRP.
- **H3 —** Plateformes hors MediaTek et Qualcomm (Samsung, Apple, Unisoc, Exynos) et mode cloud / gestion de flotte.

## 5. Critères de fin

Les quatre documents de `docs/` sont validés ; F1 à F5 sont démontrées sur le parc de test ; le journal permet de reconstituer intégralement une opération ; les exclusions H1 à H3 sont vérifiées par revue de code.