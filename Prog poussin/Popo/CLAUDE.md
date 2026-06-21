# CLAUDE.md — Plan de Livraisons BELGO

## Ordre de lecture par défaut

Quand l'utilisateur fait une demande **sans spécifier de fichier**, lire dans cet ordre :

| Priorité | Fichier | Rôle |
|----------|---------|------|
| 1 | `00_AVANCEMENT.md` | État du projet, dernier run, décisions en cours |
| 2 | `Contraintes du Plan de Livraisons BELGO.md` | **Source unique de vérité** — config, règles, exclusions |
| 3 | `plan_livraisons.py` | Script principal (si la demande concerne l'algo) |
| 4 | `md_config.py` | Parser du .md (si la demande concerne la config) |
| 5 | `extractions/` | Fichiers source ERP (AT + EXP) |
| 6 | `plans finaux/` | Plans manuels de référence |

## Conventions

- **Toute la configuration** vient du `.md` (pas de valeurs codées en dur dans le script)
- `md_config.py` lit/écrit le `.md` — le script ne modifie jamais le `.md` directement
- Les fichiers source (AT, EXP) se déposent dans `extractions/`
- Les fichiers générés vont dans `output/`
- Le `.md` est mis à jour automatiquement (§22) à chaque exécution
- **Lecture progressive des extractions** : les fichiers d'extraction (AT, EXP) sont volumineux — toujours les lire par morceaux (ex: `nrows`, `skiprows`, ou slices) plutôt que de charger l'intégralité en mémoire d'un coup, pour éviter les OOM (Out Of Memory)
- **Recherche dans les extractions** : toute recherche de commande (par référence, client, statut, etc.) doit **TOUJOURS** se faire dans les fichiers Excel d'extraction (`extractions/`) avec pandas, et **pas uniquement via grep** dans les fichiers texte du projet. Les `.xlsx` ne sont pas lisibles par grep. Méthode à utiliser :
  ```python
  import pandas as pd
  # ⚠️ header=1 obligatoire : la ligne 0 est le titre (ex: "AGROCAM SA - NJS GROUP ERP...")
  df = pd.read_excel('extractions/<fichier>.xlsx', header=1)
  result = df[df['Réf.'].astype(str).str.contains('XXXXX', na=False)]
  ```
  - Rechercher systématiquement dans **tous** les fichiers d'extraction (AT et EXP), pas seulement le plus récent
  - Vérifier les colonnes de statut (`État`, `Status Commande`) pour connaître l'état réel de la commande dans l'ERP
  - Si la commande est absente de toutes les extractions → le signaler clairement et demander confirmation avant de procéder

## Types de demandes

| Demande | Action |
|---------|--------|
| Modification des règles métier | Modifier `Contraintes du Plan de Livraisons BELGO.md` |
| Nouveau cycle de production | Mettre à jour §1 et §4 du `.md` |
| Nouveaux extraits ERP | Déposer dans `extractions/`, relancer `plan_livraisons.py` |
| Ajustement du plan | Modifier §12/§13/§14 du `.md`, relancer |
| Debug/optimisation | Lire `plan_livraisons.py`, appliquer les correctifs |

## Vérifications pré-lancement

Avant **tout** lancement de `plan_livraisons.py`, deux vérifications obligatoires :

### 1. Colonnes requises dans les extractions

Vérifier que les fichiers d'extraction contiennent toutes les colonnes nécessaires :

| Fichier | Colonnes requises |
|---------|-------------------|
| AT | `Réf.`, `Tiers`, `Qté commandée`, `État`, `agence`, `Quantité deja livrée`, `Quantité restante à livrer` |
| EXP | `Ref. Commande`, `Auteur`, `Status Commande`, `Agence` |

Si une colonne est manquante → **signaler l'erreur et ne pas lancer le script**.  
Le script fait déjà cette vérification (lignes 148-163), mais il faut la faire **en amont** pour éviter un lancement inutile.

### 2. Détection de changement des extractions

Si les fichiers dans `extractions/` n'ont **pas changé** depuis la dernière exécution (même hash, même taille, même contenu), **ne pas relancer le script**. La réalité n'a pas bougé, le plan serait identique.

Pour vérifier : comparer les hashs SHA-256 des fichiers actuels avec ceux stockés dans `output/` ou `00_AVANCEMENT.md` (§ dernière exécution).

Si les extractions sont identiques → signaler et attendre de nouveaux extraits.

## Workflow standard

Quand l'utilisateur donne une **instruction en langage naturel** (ex: "ajoute la commande X au 30/05", "exclure Y", "ajouter une date le...") :

1. **Interpréter** l'intention → mapper vers la section du `.md` concernée
2. **Mettre à jour** le `.md` (jamais modifier le script pour un changement de config)
3. **Relancer** `plan_livraisons.py`
4. **Rapporter** le résultat (plan mis à jour, capacités, manques)

### Mapping intention → section

| L'utilisateur veut... | Section à modifier |
|-----------------------|-------------------|
| Ajouter/retirer une date de production | §1 |
| Forcer une commande à une date | §14 (ajouter sous la bonne date) |
| Exclure une commande | §12 |
| Empêcher une commande à une date | §13 |
| Une commande non-BELGO à inclure | §15 |
| Une commande à ne pas split | §10 |
| Changer la capacité d'un jour | §1 |
| Changer la référence de date | §4 |
