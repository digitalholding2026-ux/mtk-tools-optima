# LEGAL — Cadre juridique

**Version** 1.0 · **Statut** : contrat · **Avertissement** : document de travail, à valider par un conseil juridique avant toute commercialisation.

## 1. Principe directeur

Le FRP est un mécanisme de protection contre le vol. L'outil ne doit permettre son effacement que pour le **propriétaire légitime** de l'appareil, sur présentation d'une **preuve écrite**. Toute opération sans preuve est interdite, sans exception.

## 2. Preuve écrite obligatoire

- **Avant F4 uniquement** : facture d'achat, certificat de cession, ou attestation sur l'honneur signée du propriétaire, accompagnée de sa pièce d'identité.
- **Concordance** : le technicien vérifie que l'IMEI de la preuve correspond à l'IMEI lu par l'outil ; toute divergence bloque l'opération.
- **Dépôt** : la preuve est numérisée (PDF ou image), son empreinte SHA-256 est enregistrée dans le journal ; l'original reste chez la boutique.
- **Refus** : preuve absente, illisible ou non concordante → décision « refus_preuve », tracée et non modifiable.
- **Conservation** : durée proportionnée (proposition : 12 mois après l'opération), à arrêter avec le conseil.

## 3. Journal d'audit

- **Inviolabilité** : ajout uniquement, aucune modification ni suppression ; chaque entrée est chaînée par empreinte (SHA-256 du contenu et de l'entrée précédente).
- **Contenu minimal** : horodatage UTC, poste, opérateur, IMEI ou identifiant, action, paramètres, résultat, empreinte de la preuve.
- **Intégrité** : la chaîne est contrôlée à chaque ouverture de l'application ; toute rupture est signalée et consignée.
- **Export** : sur réquisition officielle, export signé du journal et des preuves associées.

## 4. Conformité RGPD

- **Données traitées** : identité et pièce d'identité du demandeur, IMEI, historique des opérations.
- **Base légale** : à qualifier (intérêt légitime à la prévention de la fraude, ou exécution du contrat de service).
- **Principes** : minimisation, limitation de la durée, exactitude, sécurité.
- **Droits** : information du client, accès, rectification, effacement dans les limites des obligations de conservation.
- **Sécurité** : chiffrement de la base et des preuves, accès par compte nominatif, aucun transfert hors Union européenne.
- **Documentation** : registre des traitements, mentions d'information, procédure de violation de données.

## 5. Encadrement contractuel

- **Licence d'utilisation** : usage professionnel, personnel et non transférable ; interdiction de revente, de location et de mise à disposition de tiers.
- **Responsabilité** : l'éditeur n'est pas responsable d'un usage frauduleux ; l'utilisateur garantit détenir la preuve et respecter la loi.
- **Formation** : la licence est conditionnée à une attestation de formation à la procédure de preuve.
- **Marques** : aucune utilisation des marques de tiers (Android, Qualcomm, MediaTek) dans le nom ou le logo.

## 6. Interdits absolus et risques

Interdits : contournement sans preuve, suppression ou altération des journaux, revente des données clients, usage sur un appareil signalé volé, modification de l'outil pour désactiver les contrôles.

Risques couverts par ces mesures : complicité de recel, atteinte aux systèmes de traitement automatisé de données, non-conformité RGPD. Une revue juridique annuelle complète le dispositif.