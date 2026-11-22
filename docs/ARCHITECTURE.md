# ARCHITECTURE — Isolation des dépendances GPL

**Version** 1.0 · **Statut** : décision d'architecture structurante (ADR-001) · **Portée** : toutes les étapes suivantes.

## 1. Contexte

Le cœur de l'outil est **propriétaire**. Deux briques techniques indispensables sont publiées sous **GPLv3** : `mtkclient` (MediaTek) et `edl` (Qualcomm). Les intégrer directement poserait un problème de licence : la GPL est « virale » et s'étend à l'œuvre dérivée.

## 2. Décision

**Le cœur applicatif n'importe, ne lie et ne copie jamais de code GPL.** Les deux moteurs sont exécutés comme des **sous-processus séparés**, via leur interface en ligne de commande officielle, avec un protocole d'échange documenté et figé.

```
cœur propriétaire (Python / PySide6)
        │  argv + fichiers + stdout (contrat d'interface)
        ├──► processus mtkclient (GPLv3)
        └──► processus edl (GPLv3)
```

- Les adaptateurs (`adapters/mtk`, `adapters/qualcomm`) se limitent à : construire la ligne de commande, lancer le processus, borner sa durée de vie, capturer sa sortie et la convertir en types du cœur.
- Aucune classe, fonction ou donnée du moteur GPL n'est exposée dans l'API interne.
- Les données circulent par fichiers sur disque et flux texte ; pas de mémoire partagée, pas de socket locale, pas de lien dynamique.
- Les versions sont épinglées par empreinte ; aucune mise à jour automatique.
- Tout correctif apporté au code GPL est proposé en amont, jamais forké en silence.

## 3. Justification

- **Nature de la licence** : la GPLv3 impose, à quiconque distribue une œuvre dérivée, de fournir le code source sous GPL. Un import de module ou un lien avec le moteur rendrait l'ensemble du produit dérivé, donc diffusable uniquement sous GPL.
- **Frontière reconnue** : l'invocation d'un programme autonome, sans partage d'état interne, est une utilisation « à distance de sécurité » (*arm's length*). La FSF considère qu'un simple appel à un exécutable séparé ne crée pas en soi d'œuvre dérivée, contrairement au lien ou à l'inclusion de code.
- **Effet recherché** : le cœur, l'interface et les données restent sous licence propriétaire ; seule l'interface CLI (données factuelles, non créatives) est partagée.
- **Limite assumée** : cette isolation réduit le risque sans le supprimer ; la qualification juridique définitive appartient à un conseil. Repli prévu en cas d'avis défavorable : livraison séparée du moteur GPL avec procédure d'installation documentée.
- **Distribution** : si les binaires GPL sont livrés, les obligations GPLv3 (code source, texte de licence, notices) sont respectées ; sinon ils ne sont pas embarqués.

## 4. Règles de mise en œuvre (contrat)

- `core/` : 100 % code propriétaire, aucune dépendance GPL dans son arbre.
- `adapters/` : wrappers isolés, sans logique métier et sans état persistant.
- API publique : uniquement des types du cœur (`dataclass`, `Enum`), jamais de types GPL.
- Cycle de vie : `timeout`, annulation, code de sortie converti en `Enum` explicite.
- Journalisation : la sortie brute du sous-processus est conservée comme pièce, pas comme log applicatif.
- CI : analyse de licences (`pip-licenses`), SBOM, échec si une dépendance GPL apparaît dans le périmètre du cœur.
- Réseau : les adaptateurs n'ont aucun accès réseau.

## 5. Alternatives écartées

| Alternative | Motif de rejet |
|---|---|
| Import direct des moteurs | Contamination GPL de l'ensemble du produit. |
| Réimplémentation complète | Coût et dette technique supérieurs au bénéfice. |
| Conteneurisation (Docker) | Inadaptée à l'USB sur poste Windows. |
| Communication par socket locale | Plus lourde que le sous-processus, même frontière juridique. |
| Statut « usage interne » | Le produit est commercialisé : la distribution déclenche la GPL. |

## 6. Conséquences

- L'interface CLI des moteurs devient un **contrat versionné** : toute rupture est testée.
- Les dépendances GPL sont isolées dans un paquet séparé, installable indépendamment.
- Une revue juridique annuelle et un audit SPDX complètent la décision.

## ADR-002 — Élection LGPL pour PySide6 et shiboken6

**Statut** : accepté · **Date** : 2026-11-22 · **Portée** : licence et distribution des dépendances graphiques.

**Contexte** : `PySide6` et `shiboken6` sont publiés sous tri-licence
`LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`.

**Décision** : le projet élit explicitement **LGPL-3.0-only** pour ces deux
dépendances. Ce choix est opposable et documenté ; il ne change pas la licence
du produit, qui reste **propriétaire**.

**Conséquences** :
- Distribution en **onedir**, jamais **onefile** : les bibliothèques Qt
  (`Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll`, `shiboken6*.pyd`…) restent
  remplaçables par l'utilisateur, conformément à `STACK.md` §2.
- Les DLL Qt sont livrées à côté de l'exécutable, jamais fusionnées dans un
  binaire unique.
- La notice LGPL et la procédure de remplacement des bibliothèques sont
  incluses dans la distribution.
- `pip-licenses --fail-on="GPL"` reste le contrôle de non-régression ; il doit
  sortir en 0.
- Toute évolution de PySide6 vers une licence non LGPL impose un nouvel ADR.

**Vérification** : `pip-licenses` affiche `LGPL-3.0-only OR GPL-2.0-only OR
GPL-3.0-only` pour PySide6, PySide6-Essentials, PySide6-Addons et shiboken6 ;
le projet retient LGPL-3.0-only.