# Contraintes du Plan de Livraisons BELGO

## 1. Plan de Production

| Date | Jour | Réel | Marge (95%) | Région principale |
|------|------|------|-------------|-------------------|
| 04/06/2026 | Jeudi | 27 800 | 26 400 | Ouest+Nord+Est |
| 05/06/2026 | Vendredi | 35 700 | 33 900 | Centre |
| 10/06/2026 | Mercredi | 12 800 | 12 150 | Centre |
| 11/06/2026 | Jeudi | 35 300 | 33 550 | Ouest |
| 15/06/2026 | Lundi | 27 100 | 25 750 | Centre |
| 19/06/2026 | Vendredi | 35 900 | 34 100 | Ouest |

- **Réel** = Qté à programmer (capacité réelle après gap d'éclosion)
- **Marge** = 95% du réel, arrondi au multiple de 50
- **Prévisionnel** (conservé pour analyse d'impact) : 30 000 / 38 000 / 15 000 / 38 000 / 30 000 / 38 000
- Capacité totale Réelle : 174 600
- Capacité totale Marge : 165 850
- **v17** : Nouveau cycle juin 2026 — 6 dates d'éclosion, gap moyen -8%

---

## 2. Algorithme par Phases Strictes (v14)

### Phase 1 : ÉCHUE + ÉCHUE RECLASSÉE + RECLASSÉE + SANS DATE (priorités 1-3, 5)
- Planifiées EN PREMIER, toutes régions confondues
- Flexibilité régionale : les ÉCHUE d'autres régions peuvent utiliser la capacité restante d'un jour assigné à une autre région
- Tri : priorité > ≤1000 > FIFO par date prévue
- Préférence pour les dates les plus tôt (prefer_early_dates)

### Phase 2 : IMMINENTE (priorité 4) — force majeure
- UNIQUEMENT si plus aucune commande Phase 1 ne peut être planifiée
- Respect strict de la région (pas de cross-région)
- Marquées « FORCE MAJEURE » dans les observations
- ≤1000 avant >1000

### Phase 3 : NON ÉCHUE (priorité 6) — force majeure
- UNIQUEMENT si plus aucune commande Phase 1+2 ne peut être planifiée
- **v13** : Les NON ÉCHUE peuvent remplir TOUTES les dates avec capacité restante (plus de restriction min_date)
- Premier passage en région stricte, puis deuxième passage en flexibilité régionale
- La validation chronologique garantit qu'aucune date « NON ÉCHUE pure » n'apparaît avant une date prioritaire
- Marquées « FORCE MAJEURE » dans les observations

---

## 3. Règles de Priorité

- **≤1000 sujets** : critère PRINCIPAL dans TOUTES les catégories d'échéance (pas seulement ÉCHUE, mais aussi RECLASSÉE, SANS DATE, IMMINENTE)
- **FIFO** : par date prévue de livraison (la plus ancienne d'abord)
- **NON ÉCHUE** : toujours en dernier, mais ≤1000 est prioritaire même au sein de NON ÉCHUE
- **NON ÉCHUE ≤1000** : avant NON ÉCHUE >1000

Ordre de tri strict : priorité > ≤1000 > FIFO > quantité

---

## 4. Recalcul Échéance (Colonne K)

- Date de référence = `max(date_éclosion, aujourd'hui)`
- Si date_éclosion > aujourd'hui → le statut d'échéance est recalculé par rapport à la date d'éclosion
- Si date_éclosion ≤ aujourd'hui → référence = aujourd'hui (02/06/2026)

Classification :
- **ÉCHUE** : date_prévue ≤ ref_date
- **ÉCHUE RECLASSÉE** : échue + date_modif > date_commande ET date_modif < date_prévue - 5j
- **RECLASSÉE** : non échue + date_modif > date_commande ET date_modif < date_prévue - 5j
- **IMMINENTE** : non échue ET date_prévue - ref_date ≤ 10j
- **NON ÉCHUE** : non échue ET date_prévue - ref_date > 10j
- **SANS DATE** : pas de date prévue

---

## 5. Contraintes Régionales

### Max 2 régions par jour
- Maximum 2 régions effectives par jour de production
- Hors-Littoral : max 2 régions
- Le Littoral peut être inséré sans compter dans la limite si ses qtés sont minimes

### Nord/Est interdits le mardi
- Nord et Est ne peuvent PAS être planifiés le mardi (weekday=1)
- Exception : les assignations forcées contournent cette règle

### Est + Nord toujours compatibles
- Est et Nord peuvent toujours être planifiés le même jour
- Ils ne comptent que comme une seule région effective

### Règle Littoral (v11)
- **Littoral minime** (≤25% de la capacité du jour) : insérable sans compter dans la limite des 2 régions
- **Littoral conséquent** (>25% de la capacité du jour) : doit avoir sa PROPRE journée dédiée, ne peut pas être mélangé avec d'autres régions
- Le Littoral peut être inséré tous les jours (pas de restriction de jour)

### Flexibilité régionale Phase 1
- 2ème région hors-Littoral autorisée UNIQUEMENT pour les commandes ÉCHUE (priorités 1-3)
- En mode strict (Phase 2/3), pas de 2ème région hors-Littoral sauf Est+Nord

---

## 6. Verrouillage Régional (REGION_LOCK_DATES)

*Aucun verrouillage défini pour ce cycle.*

Les commandes d'autres régions ne peuvent pas y être planifiées, même en mode flexible.

---

## 7. Complément NON ÉCHUE (v13)

**v13** : Les commandes NON ÉCHUE peuvent remplir TOUTES les dates avec capacité restante, sans restriction de date minimum. L'ancienne contrainte `DATES_NON_ECHUE_FILL` (14/05, 15/05, 20/05, 25/05) a été remplacée par une règle plus générale : après planification de toutes les commandes prioritaires (Phase 1+2), les NON ÉCHUE comblent la capacité restante sur toutes les dates.

La validation chronologique en fin d'algorithme garantit la cohérence : une date qui ne contient QUE des NON ÉCHUE ne peut pas être antérieure à une date contenant des commandes prioritaires.

---

## 8. Multiples de 50

- Toutes les quantités livrées doivent être des multiples de 50
- La quantité restante est arrondie au multiple de 50 le plus proche avant planification

---

## 9. Règle de Split (Contrainte n°13)

**v14** : Pas de split non pertinent. Les règles sont :
- **Premier split** : la livraison doit être **≥ 50% de la qté totale** de la commande
- **Si déjà splitée** : on doit livrer la **totalité du reste** (pas de 2ème split)
- La capacité non utilisée est marquée **"Qté manquante"** informativement dans le plan
- Cela évite des splits non pertinents (ex: livrer 1 000 sur 25 000)

---

## 10. Livraison Intégrale (NO_SPLIT)

Commandes qui ne doivent PAS être splitées sur plusieurs dates — livrées intégralement le même jour :

| Réf. | Client | Qté | Région | Raison |
|------|--------|-----|--------|--------|
| SO2604-51319 | GIC LOIC | 18 200 | Centre | Livraison totale le même jour |
| SO2602-47700 | PEKA TAGNE IGNACE | 9 250 | Ouest | Livraison totale le même jour |

L'algorithme ne place ces commandes que sur des dates où la totalité de la quantité peut tenir.

---

## 11. TAMATIO

- Toutes les commandes du client TAMATIO doivent être planifiées le même jour
- Préférence pour la date où la première commande TAMATIO a été assignée

---

## 12. Exclusions Complètes (EXCLUSIONS)

Commandes totalement exclues du plan :

| Réf. | Client | Raison |
|------|--------|--------|
| SO2601-42244 | GIC AMOUR (TEDONGMO YEMDJI FRANCK) | Client exclu |
| SO2507-25604 | — | Commande retirée |
| SO2603-48874 | ABDOUL NASSER HAMADOU | Livraison partielle : 2000 déjà livrées (réelle) |
| SO2509-31314 | — | Échéance hors période : septembre |
| SO2511-37631 | — | Pas prêt à livrer |
| SO2512-39755 | — | Livraison partielle : reste 200 |
| SO2604-53606 | PRODIPEL SARL | **Reportée** — prise en intégralité, livraison reportée |
| SO2506-24935 | — | Commande non sûre |
| SO2602-45862 | ABOUBAKAR SADJO | Commande déjà livrée |
| SO2604-52536 | TAMATIO | Commande déjà livrée |
| SO2601-44631 | TCHINDA KAAWE SOL PLEISIS | Déjà livrée (problème système — non mis à jour) |
| SO2603-50721 | CHRISTY NJIE | **Retirée du plan** — sur demande |
| SO2602-46834 | TOWA LUC | **Retirée du plan** — sur demande |
| SO2604-53945 | KOAGNE TCHOUDA DADINE CAROLLE | **Retirée du plan** — sur demande |
| SO2604-53949 | TAMOU JEAN ROBERT | **Retirée du plan** — sur demande |
| SO2602-46455 | Midland Company Limited | **Retirée du plan** — sur demande |
| SO2604-52423 | GIC Jeunes Producteurs Agropastoraux | Commande déjà livrée |
| SO2601-42254 | Gic Producteurs De Mais De Yaounde | Commande déjà livrée |

---

## 13. Exclusions par Date (EXCLUDED_FROM_DATE)

*Aucune exclusion par date définie pour ce cycle.*

---

## 14. Assignations Forcées (FORCED_ASSIGNMENTS)

*Aucune assignation forcée définie pour ce cycle.*

- Sont planifiées en priorité absolue (Étape 0)
- Sont protégées contre le rééquilibrage
- Contournent les restrictions de jour (Nord/Est le mardi)

---

## 15. Inclusions Exceptionnelles (SPECIAL_INCLUDE)

Commandes non-BELGO incluses exceptionnellement avec surcharge de région et agence :

| Réf. | Client | Agence d'origine | Agence surchargée | Région surchargée |
|------|--------|------------------|-------------------|-------------------|
| SO2603-47945 | KUATE KENGNE MATHIAS | AGRO-TMC-AKWA | BELGO-FAMLA | Ouest |

---

## 16. Filtrage Agences

- Seules les agences dont le nom COMMENCE par "BELGO" sont incluses dans le plan
- SPC et PDC ne sont PAS des agences BELGO
- Les agences non-BELGO sont exclues sauf inclusion exceptionnelle via SPECIAL_INCLUDE
- Client exclu : TEDONGMO YEMDJI FRANCK (GIC AMOUR) — toutes ses commandes exclues

---

## 17. Proctor Ai

Règle de classification des expéditions Proctor Ai :
- **Proctor Ai + Status "Livrée"** = livraison réelle → les quantités déjà livrées sont comptées
- **Proctor Ai + Status "En cours"** = mouvement système uniquement → la commande est considérée comme non livrée (qte_restante = qte_commandée)

---

## 18. Auto-Exclusions

Le script exclut automatiquement :
- État = "Livrée" dans le fichier AT (commande déjà livrée)
- État = "Brouillon" ou "Annulée" dans le fichier AT
- StatutFacture = "Impayée" ou "Brouillon"
- Quantité restante à livrer = 0
- Status Commande = "Livrée" dans le fichier EXP (si absente de AT)

---

## 19. Fichiers Source (v14)

| Fichier | Rôle |
|---------|------|
| NJS GROUP ERP - Lignes de commandes + multicompany (12).xlsx | AT principal — **v14** : contient directement agence, qté livrée, qté restante |
| NJS GROUP ERP - Lignes des expeditions + multicompany (9).xlsx | EXP principal |

**v14** : Plus besoin des anciens fichiers pour le mapping agence/quantités. Le nouveau AT (12) contient toutes les colonnes nécessaires.

---

## 20. Format Sortie Excel

### Feuilles
1. **Plan Réel** : planification avec capacité réelle
2. **Plan Marge** : planification avec capacité marge (95%)
3. **Commandes non planifiées** : commandes qui n'ont pas pu être intégrées
4. **Commandes exclues** : liste des exclusions avec raisons
5. **Analyse Expéditions** : cross-référence commandes vs expéditions
6. **Détail Expéditions** : lignes d'expédition détaillées
7. **Livraisons Coq** : commandes COQ alignées sur PONTE
8. **Plan de Production** : récapitulatif production par date

### Colonnes Plan Réel/Marge
Date éclosion | Capacité production | Tiers | Réf. Tiers | Qté à livrer | Qté totale commande | Région | Agence | Date prévue livraison | Statut échéance | Observation

### Code Couleur
- **Lignes forcées** : texte rouge gras
- **Qté manquante** : fond jaune clair (#FFF2CC) + texte italique doré — capacité disponible pour insertion ultérieure
- **En-têtes** : fond bleu foncé, texte blanc
- **Sous-totaux** : fond bleu clair
- **Sections date** : fond bleu gris
- **Total général** : fond jaune/orange

---

## 21. Historique des Versions

| Version | Date | Changement |
|---------|------|------------|
| v17 | 02/06/2026 | Nouveau cycle juin 2026 : 6 éclosions (04/06–19/06). Capacité 189 000 réel / 174 600 marge. Régions : Ouest+Nord+Est, Centre, Ouest. Reset des forced assignments, excluded_from_date et region_locks du cycle précédent. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,500/174,600. 124 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 188,650/189,000. 124 exclusions. |
| v16 | 01/06/2026 | Exécution automatique. Planifié 204,400/204,700. 124 exclusions. |
| v15 | 15/05/2026 | Restauration du 14/05 dans le plan de production. Forced assignments restaurés vers le 14/05. REGION_LOCK 14/05→Centre ajouté. Mise à jour du md avec noms de tiers dans les exclusions. |
| v14 | 15/05/2026 | Retrait du 14/05 (date passée). Ajout SO2604-52423 et SO2601-42254 aux exclusions (déjà livrées). Contrainte n°13 : min 50% pour premier split. |
| v13 | 14/05/2026 | NON ÉCHUE peut remplir toutes les dates. Ajout SPECIAL_INCLUDE pour SO2603-47945. |
---

---


---

---

---

## 22. Dernière Exécution

> Exécutée le **02/06/2026** — Réf: **02/06/2026**

### Résumé

| Métrique | Valeur |
|----------|--------|
| Commandes PONTE | 110 |
| Commandes COQ | 7 |
| Exclusions | 124 |
| Planifié Réel | 174,500 / 174,600 |
| Planifié Marge | 165,750 / 165,850 |
| Non planifiées (marge) | 68 |
| Nouvelles auto-exclusions | 106 |

### Plan Réel par date

| Date | Jour | Région | Livré | Capacité | Taux |
|------|------|--------|-------|----------|------|
| 04/06/2026 | Jeu | Centre, Littoral, Ouest | 27,800 | 27,800 | 100% |
| 05/06/2026 | Ven | Centre, Ouest | 35,700 | 35,700 | 100% |
| 10/06/2026 | Mer | Ouest | 12,750 | 12,800 | 100% |
| 11/06/2026 | Jeu | Ouest | 35,300 | 35,300 | 100% |
| 15/06/2026 | Lun | Centre | 27,050 | 27,100 | 100% |
| 19/06/2026 | Ven | Centre, Littoral | 35,900 | 35,900 | 100% |

### Répartition par priorité

| Priorité | Commandes | Qté restante |
|----------|-----------|-------------|
| IMMINENTE | 6 | 29,650 |
| NON ÉCHUE | 81 | 486,800 |
| RECLASSÉE | 4 | 23,500 |
| ÉCHUE | 18 | 59,300 |
| ÉCHUE RECLASSÉE | 1 | 3,000 |
