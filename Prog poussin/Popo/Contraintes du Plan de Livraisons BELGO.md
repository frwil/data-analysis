# Contraintes du Plan de Livraisons BELGO

## 1. Plan de Production

| Date | Jour | Plan annoncé | Réel | Marge (95%) | Région principale |
|------|------|-------------|------|-------------|-------------------|
| 29/09/2026 | Mardi | — | 38 000 | 36 100 | Centre |
| 01/10/2026 | Jeudi | — | 38 000 | 36 100 | Nord, Centre |
| 02/10/2026 | Vendredi | — | 30 000 | 28 500 | Littoral, Ouest |

- **Plan annoncé** = Production prévue
- **Réel** = Prévision à considérer pour le plan
- **Marge** = 95% du réel, arrondi au multiple de 50
- Capacité totale Réelle : 106 000
- Capacité totale Marge : 100 700
- Capacité totale Annoncée : —
- **v78** : nouvelle éclosion 02/10/2026 (Vendredi, Littoral + Ouest — 30 000 réel / 28 500 marge) ajoutée au cycle — MARSHAL FARMERS (reliquat 12 200) seul Littoral du jour, reste Ouest
- **v69** : nouveau cycle 29/09 (Mardi, Centre — 38 000 réel / 36 100 marge ; Littoral minime toléré) et 01/10 (Jeudi, Nord + Centre — 38 000 réel / 36 100 marge) ; 23/09 et 25/09 passées retirées
- **v44** : 03/09 et 07/09 passées retirées ; éclosion du 09/09 avortée
- **v55** : nouvelle éclosion 23/09/2026 (Mercredi, Ouest + Centre) — 15 000 réel / 14 250 marge ; 11/09 et 15/09 passées retirées
- **v59** : nouvelle éclosion 25/09/2026 (Vendredi, Ouest — 29 000 réel / 27 550 marge) ; 23/09 conservée dans le cycle

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

### Phase 3 : NON ÉCHUE (priorité 6) — **DÉSACTIVÉE (v20)**
- ⛔ **Phase désactivée** — les commandes NON ÉCHUE sont exclues du plan jusqu'à nouvel ordre
- ~~UNIQUEMENT si plus aucune commande Phase 1+2 ne peut être planifiée~~
- ~~**v13** : Les NON ÉCHUE peuvent remplir TOUTES les dates avec capacité restante (plus de restriction min_date)~~
- ~~Premier passage en région stricte, puis deuxième passage en flexibilité régionale~~
- ~~La validation chronologique garantit qu'aucune date « NON ÉCHUE pure » n'apparaît avant une date prioritaire~~
- ~~Marquées « FORCE MAJEURE » dans les observations~~

---

## 3. Règles de Priorité

- **≤1000 sujets** : critère PRINCIPAL dans TOUTES les catégories d'échéance (pas seulement ÉCHUE, mais aussi RECLASSÉE, SANS DATE, IMMINENTE)
- **FIFO** : par date prévue de livraison (la plus ancienne d'abord)
- **NON ÉCHUE** : toujours en dernier, mais ≤1000 est prioritaire même au sein de NON ÉCHUE
- **NON ÉCHUE ≤1000** : avant NON ÉCHUE >1000

Ordre de tri strict : priorité > ≤1000 > FIFO > quantité

---

## 4. Recalcul Échéance (Colonne K)

- Date de référence = 29/09/2026 (éclosion du 29/09 — cycle 23/09–25/09 clôturé)
- **Équité de programmation (v20)** : pour une commande programmée à une date X, le statut d'échéance est recalculé par rapport à **X + 1 jour** (et non à aujourd'hui). Cela évite de pénaliser une commande repoussée à une date ultérieure et tient compte du délai de mise à disposition post-éclosion.

Classification :
- **ÉCHUE** : date_prévue ≤ ref_date
- **ÉCHUE RECLASSÉE** : échue + date_modif > date_commande ET date_modif < date_prévue - 5j
- **RECLASSÉE** : non échue + date_modif > date_commande ET date_modif < date_prévue - 5j
- **IMMINENTE** : non échue ET date_prévue - ref_date ≤ 10j
- **NON ÉCHUE** : non échue ET date_prévue - ref_date > 10j
- **SANS DATE** : pas de date prévue

### Commandes traitées comme ÉCHUE pure (non reclassées)

Forçage utilisateur : la détection automatique « reclassée » est ignorée pour ces réf. — elles sont classées **ÉCHUE** dès que leur date prévue est dépassée (priorité 1, avant les ÉCHUE RECLASSÉE).

| Réf. |
|------|
| SO2605-55433 |

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

| Date | Régions autorisées |
|------|--------------------|
| 29/09/2026 | Centre |
| 01/10/2026 | Nord, Centre |
| 02/10/2026 | Littoral, Ouest |

- **v78** : 02/10 verrouillée Littoral + Ouest (éclosion dédiée — MARSHAL seul Littoral, reste Ouest)
- **v69** : 29/09 verrouillée Centre ; 01/10 verrouillée Nord + Centre (Littoral exempté comme toujours) — 23/09 et 25/09 passées retirées
- 11/09 et 15/09 passées retirées (v55) — 23/09 verrouillée Ouest + Centre
- **v59** : 25/09 verrouillée Ouest (éclosion réservée à l'Ouest ; Littoral exempté comme toujours)

- **Le Littoral est exempté** de tous les verrouillages — il peut s'insérer partout (minime ≤25% du jour)
- Les commandes d'autres régions ne peuvent pas y être planifiées, même en mode flexible

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

*Aucune commande NO_SPLIT active — SO2602-47700 (PEKA TAGNE IGNACE, 9 250) livrée hors ERP (v32, exclue §12).*

L'algorithme ne place ces commandes que sur des dates où la totalité de la quantité peut tenir.

---

## 11. TAMATIO

- Toutes les commandes du client TAMATIO doivent être planifiées le même jour
- Préférence pour la date où la première commande TAMATIO a été assignée

---

## 12. Exclusions Complètes (EXCLUSIONS)

Commandes totalement exclues du plan (hors commandes déjà livrées = auto-exclusion État=Livrée) :

| Réf. | Client | Qté | Agence | Date prévue | Raison |
|------|--------|-----|--------|-------------|--------|
| SO2601-42244 | GIC AMOUR | 300 | BELGO-FAMLA | 25/02/2026 | Client exclu — 7 700/8 000 déjà livrés |
| SO2601-42302 | METAFE GNITEYO SONYA MIGLANCHE | 38 000 | BELGO-BERI | 28/01/2026 | **Déjà livrée** — livraison confirmée hors ERP (reste 38 000 dans l'ERP) |
| SO2507-25604 | — | — | — | — | Commande retirée (absente des extractions) |
| SO2509-31314 | — | — | — | — | Échéance hors période : septembre (absente des extractions) |
| SO2506-24935 | — | — | — | — | Commande non sûre (absente des extractions) |
| SO2602-46455 | Midland Company Limited | 100 | BELGO-BERI | 01/07/2026 | **Retirée du plan** — sur demande |
| SO2602-47700 | PEKA TAGNE IGNACE | 9 250 | BELGO-FAMLA | 01/07/2026 | **Déjà livrée** — livraison confirmée hors ERP (reste 9 250 dans l'ERP) |
| SO2604-52480 | TAKAMTSING PROSPER | 200 | BELGO-MESSASSI | 21/04/2026 | **Déjà livrée** — livraison confirmée (COQ), hors ERP (reste 200 dans l'ERP) |
| SO2604-53606 | PRODIPEL SARL | 16 000 | BELGO-NDJELENG | 23/09/2026 | **Non reclassée** — mise en non planifiée (2 lignes ERP : 15 700 + 300) |
| SO2605-55242 | PEKA TAGNE IGNACE | 12 750 | BELGO-NDJELENG | 15/07/2026 | **Déjà livrée** — livraison confirmée hors ERP (reste 12 750 dans l'ERP) |
| SO2606-60929 | COMPTE TEMPORAIRE | 700 | BELGO-MESSASSI | 26/09/2026 | Client COMPTE TEMPORAIRE — **à ne jamais programmer** |
| SO2606-61347 | COMPTE TEMPORAIRE | 50 | BELGO-MESSASSI | 24/07/2026 | Client COMPTE TEMPORAIRE — **à ne jamais programmer** |
| SO2606-59715 | LEMOKEM TIODOU ZEPHIRIN | 28 000 | BELGO-FAMLA | 20/06/2026 | **Livrée définitivement** — remplacée par SO2607-64515 PONTE PREMIUM (28 000/28 000 livrés) |
| SO2604-51968 | MOGUM FOSSI LAURENCE LOR | 2 500 | BELGO-BERI | 04/09/2026 | **Déjà livrée** — commande modifiée en poussins chair (retirée définitivement du plan PONTE) |

---

## 13. Exclusions par Date (EXCLUDED_FROM_DATE)

| Réf. | Dates exclues |
|------|---------------|
| SO2609-69839 | 29/09/2026, 01/10/2026, 02/10/2026 |
| SO2609-69890 | 29/09/2026, 01/10/2026, 02/10/2026 |
| SO2608-66549 | 29/09/2026, 01/10/2026 |
| SO2608-66550 | 29/09/2026, 01/10/2026 |
| SO2608-66552 | 29/09/2026, 01/10/2026 |
| SO2608-66553 | 29/09/2026, 01/10/2026 |
| SO2609-69666 | 29/09/2026, 01/10/2026, 02/10/2026 |
| SO2609-69647 | 29/09/2026, 01/10/2026, 02/10/2026 |
| SO2607-61870 | 29/09/2026, 01/10/2026 |
| SO2607-61869 | 29/09/2026, 01/10/2026 |
| SO2609-69211 | 29/09/2026, 01/10/2026 |
| SO2609-69158 | 29/09/2026, 01/10/2026 |
| SO2609-69314 | 29/09/2026, 01/10/2026 |
| SO2609-69306 | 29/09/2026, 01/10/2026 |
| SO2609-69312 | 29/09/2026, 01/10/2026 |
| SO2609-69316 | 29/09/2026, 01/10/2026 |
| SO2605-57737 | 02/10/2026 |
| SO2606-60066 | 01/10/2026 |
| SO2609-70124 | 01/10/2026 |
| SO2604-51281 | 29/09/2026 |
| SO2604-52840 | 29/09/2026, 01/10/2026, 02/10/2026 |

### Commandes à ne pas programmer avant une date (MIN_DATES)

Contrainte durable : ces commandes ne peuvent être programmées qu'à partir de la date indiquée (toutes les dates antérieures sont interdites). **Ne pas vider cette table lors du nettoyage de §13** — elle ne dépend pas du cycle en cours.

| Réf. | Date minimale |
|------|---------------|
| SO2607-62419 | 20/10/2026 |

**v81** : 01/10 — SO2606-60066 (1 500) et SO2609-70124 (2 150) retirées du 01/10 (demande utilisateur), remplacées par GIC MOS SO2609-69619 (3 500) forcée §14 → non planifiées pour ce cycle (29/09 et 02/10 déjà pleins).

**30/09** : SO2604-52840 (MEMGBA MESSI ALBERTINE FLEUR, 5 300, MESSASSI) doit rester **non planifiée pour le moment** (décision utilisateur) — exclue des 3 dates du cycle, à replacer sur un futur cycle.

**v76** : restructuration 29/09–01/10 (demande utilisateur) — Alfred Fon Ja-Ai SO2609-69666 (5 300), OTANG VALENTINE SO2609-69647 (500) et TAKAMTSING PROSPER SO2607-61870 (4 650) + SO2607-61869 (1 500) retirées du 29/09 → non planifiées, remplacées par MARSHAL FARMERS SO2605-54941 (split forcé §14 : 5 800 le 29/09 + 12 200 le 01/10) et Fotie Tagoumtse SO2607-63625 (10 000, totalité, 29/09). 01/10 réservé Nord : seules SCOOPS DYFER CAM SO2607-65229 (5 200) gardée, forcée §14 — les 6 autres Nord (69211 1 000, 69158 2 700, 69314 900, 69306 3 000, 69312 2 000, 69316 1 100) → non planifiées. TEULONG YOTA IGOR SO2606-61062 (3 300) forcée le 01/10 (§14). MARSHAL retirée de §13. Correctif script : agrégation des réf. multi-lignes (54941 = 18 000 + 200) + Littoral non compté comme région sur date verrouillée (v28 étendu).

**v75** : WETE MANGA WILLIAM SO2607-62419 (BELGO-BERI, Littoral, 1 100) — à programmer **à partir du 20/10/2026** (demande utilisateur) → MIN_DATES, retirée du 29/09.

**v72** : MIAKAUG EPSE SODEA DIANE (Nord, NDERE) — les 4 commandes (SO2608-66549 1 200 + SO2608-66550 1 000 + SO2608-66552 1 400 + SO2608-66553 1 800 = 5 400, échues 26/09) retirées du cycle 29/09–01/10 → **non planifiées, à intégrer dans un programme à partir de la semaine prochaine** (demande utilisateur).

**v69** : 29/09 et 01/10 Centre/Nord prioritaires (choix utilisateur) — Littoral limité au minime : MARSHAL FARMERS SO2605-54941 (18 000), NGNIMPEYE SO2609-69839 (4 200) et TCHANTCHOU SO2609-69890 (3 100) exclues du cycle 29/09–01/10 → restent en attente (Littoral 29/09 = 7 900 ≤ 9 500 minime ; sans exclusion des deux dates elles se déversaient sur le 01/10 à 66% du jour). §13 vidé des exclusions du 25/09 (date passée, précédent v55) : OTANG VALENTINE, ALFRED FON JA-AI, WAYAP SO2606-59891, MAGDALENE, WETE MANGA et PENKA redeviennent éligibles sur le cycle 29/09–01/10.

**v68** : DJUISSI SO2609-68591 retirée — **livrée** (1 000/1 000, expédition SH2609-5217 Traitée, AT(46)+EXP(13) du 26/09) → désormais auto-exclue (État=Livrée).

**v63** : 25/09 — WAYAP SO2606-59891 (2 200) retirée de §14 et exclue ; MAGDALENE 1 000, WETE MANGA 1 100, PENKA reliquat 550 et DJUISSI 1 000 exclues — remplacées par TUMENTA 2 000 + LEMNYUY 1 000 + WAYAP SO2609-69790 2 700 forcées (§14, toutes MBOUDA).

**v61** : OTANG VALENTINE SO2609-69647 (500) et Alfred Fon Ja-Ai SO2609-69666 (5 300) — BELGO-BUEA, Littoral — retirées du 25/09, remplacées par ALEMAWO 4 000 + WAYAP 2 200 forcées (§14).

*Cycle 23/09 (v55) : §13 vidé — les exclusions portaient sur des dates passées (11/09, 15/09). 62349 désormais État=Livrée (auto-exclue). 61870/61869 restent éligibles (aucune protection demandée pour le 23/09).*

---

## 14. Assignations Forcées (FORCED_ASSIGNMENTS)

*Cycle 25–28/08 clôturé (v32) : 10/10 forcées livrées (Kenne 34 800, PEKA 9 250, PEKA 12 750, MBE CRIYAUS, TALLA EMILE, TIWA, Chefor, DOM KANSE, LAMINE BOUBA, Gic Emocolit 5 500) — PEKA ×2 et Gic Emocolit confirmées livrées hors ERP (exclues §12).*

### 11/09/2026 (Ouest, Centre)

*Section vidée (v54) — extraits AT(39) du 16/09 : 3/4 livrées dans l'ERP — NGOMPE 59718 en totalité (25 000/25 000, reste 0), LEMOKEM ANDOLAIN 1 000/1 000, LEMOKEM TIODOU 2 000/2 000 retirées. MAGNE JOSEPHINE SO2607-62698 (1 250) **NON livrée** (0/1 250, En cours) → repasse en non planifiée (à repositionner).*

*Historique : éclosion du 09/09 avortée (v44) — total forcé 11/09 : 21 450, dépassement +1 450 vs réel 20 000 (tout Ouest). Les 6 commandes Centre ex-11/09 et WAFIN 10 000 basculées au 15/09 (v46) ; DASSI 3 200 repasse en non planifié.*

### 15/09/2026 (Centre)

*Section vidée (v54) — extraits AT(39) du 16/09 + EXP(12) du 17/09 : **8/8 forcées livrées** — YOUMSSI 3 000/3 000, KUETCHE 3 050/3 050, AFRIQUE TOPO 4 200/4 200, PROVENDERIE 3 000/3 000, WAFIN 10 000/10 000, KAFAB 2 300/2 300, MEKA FOKO 10 000/10 000, BOUKAR ISAIE 3 100/3 100. Cycle 11/09–15/09 entièrement exécuté (38 650 livrés le 15/09).*

### 23/09/2026 (Ouest, Centre)

*Section vidée (v68) — extraits AT(46) + EXP(13) du 26/09 : LEMOKEM SO2606-59894 **livrée** (2 000/2 000, SH2609-1744 Traitée), TAJOUO SO2606-60657 **livrée** (12 000/12 000, SH2609-5320 Traitée). GIC MOS SO2609-69619 **NON livrée** (0/3 500, Validée, prévue désormais au 03/02/2027) → repasse en non planifiée (à repositionner sur un futur cycle).*

### 25/09/2026 (Ouest)

*Section vidée (v68) — extraits AT(46) + EXP(13) du 26/09 : **8/8 forcées livrées** — NGOUADJEU 3 300 (SH2609-1705), KAMGANG 5 800 (SH2609-1702), BIEPIP reliquat 250 (SH2609-1809, 7 800/7 800 au total), TESEHKOUE 10 150 (SH2607-5344), ALEMAWO 4 000 (SH2609-4187), TUMENTA 2 000 (SH2609-2951), LEMNYUY 1 000 (SH2609-2983), WAYAP SO2609-69790 2 700 (SH2609-2986). Cycle 23/09–25/09 exécuté (10/11 forcées livrées au total ; GIC MOS non livrée → non planifiée).*

### 29/09/2026 (Centre, Littoral, Ouest)

| Réf. | Client | Qté | Notes |
|------|--------|-----|-------|
| SO2605-54941 | MARSHAL FARMERS | 5 800 | Split part 1 — remplace 69666 + 69647 (mêmes qtés) |
| SO2607-63625 | Fotie Tagoumtse Constantin Legrand | 10 000 | Totalité — remplace 61870 + 61869 |
| SO2605-55433 | Groupe D'initiative Commune Des Jeunes Producteurs Agropastoraux De L'est (Gic/Jepro-Agro) | 6 500 | Totalité le 29/09 (demande utilisateur — ex-split 2 700 + 3 800) |
| SO2606-60066 | Kemajou Dorette | 1 500 | Totalité le 29/09 (demande utilisateur — restaure l'ancien plan, ex-38 500 avec les 200 coqs) |

### 01/10/2026 (Nord, Centre)

| Réf. | Client | Qté | Notes |
|------|--------|-----|-------|
| SO2606-61062 | TEULONG YOTA IGOR | 3 300 | Reliquat livré le 01/10 (5 800/9 100 déjà livrés) |
| SO2607-65229 | SCOOPS DYFER CAM (SILEDJE MBOUGANG RICHARD) | 5 200 | Seule commande Nord gardée le 01/10 (demande utilisateur) |
| SO2604-52011 | SOFAB PROVENDERIE | 4 400 | Totalité le 01/10 (demande utilisateur — ex-split 3 700/700) |
| SO2604-51270 | KENNE TCHUENTE JILDAS ANICET | 3 000 | Remplace MARSHAL (part) — demande utilisateur |
| SO2606-59829 | MOFFO FOBOU MERLIN | 5 600 | Remplace MARSHAL (part) — demande utilisateur |
| SO2605-55637 | Moromte Oscar | 2 500 | Remplace MARSHAL (part) — demande utilisateur |
| SO2606-61428 | TAMATIO | 1 100 | Remplace MARSHAL (part) — demande utilisateur |
| SO2609-69619 | GIC MOS (NDJANA YVES BERTRAND NOEL) | 3 500 | Totalité le 01/10 — remplace 60066 + 70124 (demande utilisateur) |
| SO2604-51281 | SANDJONG ELIE | 1 000 | Part 1 000 le 01/10 — restaure l'ancien plan (reste 1 200 non planifié, 29/09 exclu §13) |
| SO2604-51756 | PIEBJOU MICHEL | 2 100 | Totalité le 01/10 — restaure l'ancien plan (ex-split 1 400 + 700) |

### 02/10/2026 (Littoral, Ouest)

| Réf. | Client | Qté | Notes |
|------|--------|-----|-------|
| SO2605-54941 | MARSHAL FARMERS | 12 200 | Split part 2 — déplacée au 02/10, seul Littoral du jour (demande utilisateur) |
| SO2605-57744 | Kenne Manfouo Idrice | 16 000 | Totalité le 02/10 — à la place des autres commandes du jour (demande utilisateur) |
| SO2606-58801 | DJIDJOU ETIENNE ARLEX | 2 000 | Totalité le 02/10 — à la place des autres commandes du jour (demande utilisateur) |

---

## 15. Inclusions Exceptionnelles (SPECIAL_INCLUDE)

Commandes non-BELGO incluses exceptionnellement avec surcharge de région et agence :

*Aucune inclusion exceptionnelle — SO2602-47515 (SHOUEP ROGER ANDERZIL) livrée 3 500/3 500.*

---

## 16. Filtrage Agences

- Seules les agences dont le nom COMMENCE par "BELGO" sont incluses dans le plan
- SPC et PDC ne sont PAS des agences BELGO
- Les agences non-BELGO sont exclues sauf inclusion exceptionnelle via SPECIAL_INCLUDE
- Client exclu : TEDONGMO YEMDJI FRANCK (GIC AMOUR) — toutes ses commandes exclues
- Client exclu : COMPTE TEMPORAIRE — à ne **jamais** programmer (toutes ses commandes exclues)

---

## 17. Proctor Ai

Règle de classification des expéditions Proctor Ai :
- **Proctor Ai + Status "Livrée"** = livraison réelle → les quantités déjà livrées sont comptées
- **Proctor Ai + Status "En cours"** = mouvement système uniquement → la commande est considérée comme non livrée (qte_restante = qte_commandée) — **sauf si l'AT enregistre des quantités déjà livrées** (Quantité deja livrée > 0, ex : expéditions Traitées avec facture) : dans ce cas, faire confiance à l'AT (v55)

---

## 18. Auto-Exclusions

Le script exclut automatiquement :
- État = "Livrée" dans le fichier AT (commande déjà livrée)
- État = "Brouillon" ou "Annulée" dans le fichier AT
- StatutFacture = "Impayée" ou "Brouillon"
- Quantité restante à livrer = 0
- Status Commande = "Livrée" dans le fichier EXP (si absente de AT)

**Exception (v78)** : une commande **forcée par l'utilisateur (§14)** passe malgré État = "Brouillon" ou StatutFacture = "Brouillon" — le forcing exprime la volonté de l'utilisateur et prime sur l'auto-exclusion.

---

## 19. Fichiers Source (v68)

| Fichier | Rôle |
|---------|------|
| NJS GROUP ERP - Lignes de commandes + multicompany (46).xlsx | AT principal — 26/09/2026 — 1 565 lignes |
| NJS GROUP ERP - Lignes des expeditions + multicompany (13).xlsx | EXP principal — 26/09/2026 — 1 424 lignes |

**v68** : Extraits AT(46) + EXP(13) du 26/09/2026 (12:22 — Date modif. max 26/09 10:00, données fraîches, pas de fichier figé). Mise à jour des statuts ERP : §14 23/09 et 25/09 vidés (10/11 forcées livrées — LEMOKEM, TAJOUO, NGOUADJEU, KAMGANG, BIEPIP, TESEHKOUE, ALEMAWO, TUMENTA, LEMNYUY, WAYAP) ; GIC MOS 69619 non livrée (prévue 03/02/2027) → non planifiée ; §13 −1 (DJUISSI 68591 livrée, SH2609-5217 Traitée). §12 inchangé (aucune exclusion devenue Livrée dans l'ERP).

**v59** : Nouvelle éclosion 25/09/2026 (Vendredi, Ouest — 29 000 réel / 27 550 marge), 23/09 conservée. Extraits inchangés : AT(44) + EXP(15) du 21/09. ⚠ AT(35) (re-téléchargé le 21/09 15:38 mais données figées au 09/09) déplacé vers `extractions/archive/` — le script pointait dessus par mtime.

**v55** : Extraits AT(44) + EXP(15) du 21/09/2026 (13:50). Nouveau cycle 23/09 (15 000 réels). BIEPIP SO2606-60194 : 7 550/7 800 livrés dans l'ERP (expédition SH2608-1631 Traitée) → reliquat 250 PONTE PREMIUM forcé. COQ SO2609-69601 livrée (150/150). §17 affiné : Proctor Ai « En cours » + livraisons réelles dans l'AT → confiance à l'AT.

**v54** : Extraits AT(39) du 16/09 + EXP(12) du 17/09. Statuts ERP : §14 11/09 vidé 3/4 (NGOMPE 25 000/25 000, LEMOKEM ×2 livrées ; MAGNE JOSEPHINE 1 250 NON livrée → non planifiée), §14 15/09 vidé 8/8 livrées (38 650). §12 inchangé. 62349 désormais État=Livrée. 72 nouvelles commandes depuis le 09/09 (33 BELGO — dont TEIKING 26 000 FAMLA, IBII OTTO 10 150 PK11, KOM BLAISE 10 200, KUEGHANG 10 850, SOFAB ×3). ⚠ AT(35) retéléchargé le 17/09 contient des données figées au 09/09 — ne pas l'utiliser (AT de référence : (39)).

**v52** : 15/09 — TAKAMTSING SO2604-51282 (5 800, NKOABANG) retirée de §14 (repasse en non planifiée), remplacée par BOUKAR ISAIE SO2604-52017 (3 100, BELGO-BERI — Littoral minime, Payée, 0 livré, prévue 12/09). Total forcé 15/09 : 38 650 (+1 150 vs 37 500).

**v50** : 15/09 — MEKA FOKO SO2607-63332 forcée en totalité 10 000 (ex-split 6 600/10 000, §13 retirée) ; TAKAMTSING SO2604-51282 (5 800, NKOABANG) forcée en totalité (ex-ajout algo). Total forcé 15/09 : 41 350 (dépassement +3 850 vs 37 500). 61870/61869 restent exclues §13.

**v48** : Remplacements sur le 15/09 — TAKAMTSING 61870 (4 650) et 61869 (1 500) retirées et exclues §13 du 15/09, remplacées par MEKA FOKO SO2607-63332 splitée 6 600/10 000 (reste 3 400 pour date ultérieure, exclu §13 du 15/09) ; KUETCHE 62349 remplacée par KAFAB SO2604-53917 (2 300, PREMIUM) — exclue §13 du 15/09. Total forcé 15/09 : 32 150.

**v46** : Nouvelle éclosion 15/09/2026 (Mardi, Centre — 37 500 réel / 35 650 marge). §1/§6 + 15/09 Centre. §14 15/09 : les 6 commandes Centre ex-11/09 (YOUMSSI 3 000, KUETCHE 3 050, TAKAMTSING 4 650 + 1 500, AFRIQUE TOPO 4 200, PROVENDERIE 3 000) + WAFIN GAELLE 10 000 (ex-09/09) — 29 400 forcés, 8 100 libres.

**v44** : Éclosion du 09/09 avortée — pas de nouvelles extractions. Reconfiguration : §1/§6 réduits au 11/09 (03/09 et 07/09 passées retirées), §4 réf = 11/09. §13 : 62698 retirée. §14 11/09 : NGOMPE 59718 reliquat 17 200 + LEMOKEM 1 000 + 2 000 (basculées du 09/09) + MAGNE JOSEPHINE 62698 1 250 forcée — 21 450 (+1 450). Le reste (DASSI, WAFIN, 6 ex-11/09) repasse en non planifié.

**v43** : Nouvelles extractions du 09/09/2026 (AT 35, EXP 10). Mise à jour des statuts ERP : §14 03/09 vidé (5/5 livrées : MOTING, HAMIDOU, HASSAN ×2, NGOMPE 59723 complète 15 000/15 000), §14 07/09 vidé (WANTSA 7 000/7 000 ; NGOMPE 59718 7 800 expédiés → reliquat 17 200 basculé au 09/09), §14 09/09 : 59723 retirée (livrée), 59718 → 17 200 (jour inchangé à 33 400, +3 400). Plan non régénéré.

**v32** : Nouvelles extractions du 01/09/2026. Mise à jour des statuts ERP : §14 vidé (10/10 forcées livrées — PEKA ×2 et Gic Emocolit confirmées hors ERP), §10 vidé (PEKA 9 250 livrée hors ERP), §13 −1 livrée (Manfouo Mathieu 4 100), §12 −1 redevenue active (Mogum Fossi 2 500) + LEMOKEM SO2606-59715 ré-exclue définitivement (remplacée par SO2607-64515 PONTE PREMIUM livrée 28 000/28 000) + 3 livrées hors ERP (PEKA 9 250, PEKA 12 750, Gic Emocolit 5 500).

**v33** : Nouveau cycle 03–11/09/2026 (3 dates : 03/09, 07/09, 11/09 — 60 000 réel / 57 000 marge). §4 réf = 07/09/2026. §6 verrouillages : 03/09 Nord+Centre+Ouest, 07/09 Ouest, 11/09 Ouest+Centre. §14 forcées : 03/09 21 000 = plein (5 refs 11 900 + NGOMPE 59723 split 9 100/15 000) ; 07/09 13 100 (NGOMPE 59718 split 13 100/25 000 — 5 900 libres Ouest) ; 11/09 17 800 (NGOMPE 11 900 + 5 900 — 2 200 libres Centre). §13 exclusions par date à redéfinir. Plan non généré.

**v34** : 11/09 : Mogum Fossi SO2604-51968 retirée définitivement (commande modifiée en poussins chair → déjà livrée, exclue §12). 11/09 revient à Ouest+Centre (17 800 forcés, 2 200 libres Centre). 07/09 : WANTSA GILBERT SO2606-60227 (7 000, MBOUDA, en totalité) forcée à la place de MOFFO BERTIN — jour à 20 100 (+1 100).

**v36** : Nouvelle éclosion 09/09/2026 (Mercredi, Centre) — 30 000 réel / 28 500 marge (§1, §6). §12 +3 livrées hors ERP (Quay's Idriss SO2608-68066, Gic Emocolit SO2605-57513, NJOSSI SO2608-67701). §14 03/09 + Kamgang Emmanuel SO2606-58332 reliquat 300 (1 200/1 500 déjà livrés) — jour à 21 300 (+300).

**v37** : Restructuration §14 : NGOMPE 59723/59718 splits 2/2 (5 900 + 11 900) déplacés du 11/09 au 09/09 ; + DASSI 58150 (3 200) + WAFIN 49436 (10 000) forcées au 09/09 — jour à 31 000 (+1 000). 6 commandes Centre forcées au 11/09 (YOUMSSI 3 000, KUETCHE 3 050 + reliquat 1 200, TAKAMTSING 4 650 + 1 500, AFRIQUE TOPO 4 200) — 17 600, reste 2 400.

**v38** : 11/09 : KUETCHE SO2607-62349 retirée (exclue §13 avec MAGNE JOSEPHINE SO2607-62698, ex-11/09) ; PROVENDERIE L' ASSURANCE SO2603-50691 (3 000, NON ÉCHUE 07/10) forcée à la place — jour à 19 400 forcés, reste 600.

**v40** : Nouvelles extractions du 04/09/2026 (AT 29, EXP 9). Mise à jour des statuts ERP : §14 03/09 −2 livrées (KAMTA 5 200/5 200, Kamgang reliquat 300 → 1 500/1 500), §12 −4 livrées dans l'ERP (Gic Emocolit 5 500 + 500, Quay's Idriss 1 100, NJOSSI 50). Nouvelles commandes depuis le 01/09 : 17 (dont Tengemne 25 000 + 13 000 + 12 000). Plan non régénéré.

**v27** : Nouvelles extractions du 17/08/2026. Mise à jour des statuts ERP : §10 −2 livrées (KUATE, TCHANGANG), §12 −2 livrées (GIC TSINGBEU, NOUPING) + 3 qtés mises à jour (PRODIPEL 16 000, BOGNING 5 000, LAMBOU 8 500), §14 vidé — 11/13 forcées livrées, 2 à repositionner (Kenne 8 300, PENKA 2 550), §15 −1 livrée (SHOUEP).

**v28** : Nouveau cycle 27–28/08 (2 dates, 65 400 réel / 62 100 marge). Régions : 27/08 Ouest+Centre (Ouest ≥ 28 000), 28/08 Centre. Forcées 27/08 : Kenne 8 300 + PEKA 9 250 + PEKA 12 750 + PENKA 2 550 (Ouest 32 850) + DOM KANSE 2 000 (Centre). §12 : 6 Reportée retirées (NGUIMDJOU, PEKA, WANTSA, MOTING, Manfouo Mathieu, LAMBOU). §13 : WANTSA + DASSI exclues du 27/08.

**v30** : Éclosion du 27/08 déplacée au **25/08** (Mardi). Le reste inchangé (§4 réf 28/08, §6 verrouillages, §13/§14 suivent la nouvelle date).

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
| v82 | 29/09/2026 | **Restauration du 29/09 à l'ancien plan (demande utilisateur)** : SO2606-60066 (Kemajou Dorette, 1 500) remise au 29/09 (§14, forcée en totalité) — elle n'avait pas été demandée sur le 01/10, elle était déjà au 29/09 dans l'ancien plan (38 500 avec les 200 COQ). SO2604-51281 retirée du 29/09 (§13, date exclue). 01/10 verrouillé à l'état approuvé : 51281 part 1 000 + 51756 PIEBJOU MICHEL 2 100 forcées (§14) pour empêcher l'algo de déverser le reliquat de 51281. Exécution : **planifié 106 000/106 000 (100%)** — 29/09 = **38 300** (54941 5 800 + 63625 10 000 + 55433 6 500 + 57737 1 000 + 58836 8 500 + 62671 5 000 + 60066 1 500, +300 toléré ≤500), 01/10 = 37 500 inchangé, 02/10 = 30 200 inchangé. **Diff vérifié** : Plan Réel 29/09 = seul changement (+60066 1 500 / −51281 1 200), 01/10 et 02/10 identiques au plan approuvé ; la Marge (projection 95 %) se recompose mais conserve ses totaux (36 100 / 35 100 / 30 200). 439 exclusions, 243 non planifiées. |
| v81 | 29/09/2026 | **01/10 : SO2606-60066 (Kemajou Dorette, 1 500) et SO2609-70124 (SOFAB PROVENDERIE, 2 150) retirées** (§13, date exclue 01/10 → non planifiées), remplacées par **GIC MOS SO2609-69619 (3 500, PONTE PREMIUM, MESSASSI) forcée au 01/10 en totalité** (§14, demande utilisateur). Exécution : **planifié 105 700/106 000 (100%)** — 29/09 = 38 000 plein, 01/10 = 37 500 (manque 500 : la place libérée n'a pas été intégralement recomblée — seuls des candidates > place libre restaient), 02/10 = 30 200 (+200 toléré), 439 exclusions, 244 non planifiées. **Diff v80→v81 vérifié** : Plan Réel 29/09 et 02/10 inchangés, 01/10 = swap seul ; la Marge 01/10 a en plus évincé 51281 (2 200) + 51756 (2 100) — mécanique de la projection 95 % (60066/70124 n'y étaient pas), validée par l'utilisateur. |
| v80 | 29/09/2026 | **Différenciation PONTE/COQ dans les commandes mixtes** (demande utilisateur : le MARSHAL 200 du 29/09 est du COQ) — correctif script : l'agrégation des réf. multi-lignes (v76) se fait désormais **par (réf., PONTE/COQ)** au lieu de tout fusionner. Résultat : SO2605-54941 = **18 000 PONTE + 200 COQ séparés** — les 200 partent au **plan COQ du 29/09** (même jour que la 1ʳᵉ livraison PONTE du client), plus dans le plan PONTE ; idem SO2605-56506 = 1 000 PONTE + 300 COQ (COQ non planifié : règle « client a du PONTE mais non planifié »). Exécution : **planifié 105 850/106 000 (100%)** — 29/09 = 38 000 plein (sans les 200 COQ), 01/10 = 37 650 (manque 350), 02/10 = 30 200 (+200 toléré) ; COQ : 15 commandes 3 800 sujets (1 750 planifiés, 2 050 non planifiés). 439 exclusions, 243 non planifiées. |
| v79 | 28/09/2026 | **02/10 réservé à MARSHAL + 2 commandes Ouest** (demande utilisateur) : **SO2605-57744 (Kenne Manfouo Idrice, 16 000, NDJELENG) et SO2606-58801 (DJIDJOU ETIENNE ARLEX, 2 000, FAMLA) forcées au 02/10 (§14)** à la place de toutes les autres commandes du jour — total forcé 02/10 = 30 200 (12 200 + 16 000 + 2 000), jour plein, l'Ouest rempli par l'algo (18 000) est évincé → non planifiées. Exécution : **planifié 106 700/106 000 (101%)** — 29/09 = 38 500 (+500 toléré ≤500, reliquat MARSHAL 200 remonté du 01/10 + 60066), 01/10 = 38 000 plein (MEMGBA 52840 partiellement replacée : split 2 800/5 300), 02/10 = 30 200/30 000 (+200 toléré — Marge 30 200/28 500, dépassement forcé assumé), 439 exclusions, 243 non planifiées. |
| v78 | 28/09/2026 | **Nouvelle éclosion 02/10 (Vendredi, Littoral + Ouest — 30 000 réel / 28 500 marge)** : §1/§6 mis à jour, §6 verrouille 02/10 sur Littoral+Ouest. **Reliquat MARSHAL FARMERS SO2605-54941 (12 200) forcé au 02/10 (§14)** — seul Littoral du jour. **Remplacements du 01/10** (demande utilisateur, §14) : SO2604-51270 (3 000) + SO2606-59829 (5 600) + SO2605-55637 (2 500) + SO2606-61428 (1 100) = 12 200 forcés au 01/10. §13 étendu au 02/10 pour les Littoral (69839, 69890, 69666, 69647, 66549, 66550, 66552, 66553), 57737 exclue du 02/10 seul. **§18 exception (correctif script)** : une commande forcée §14 passe malgré État/StatutFacture = Brouillon (55637 bloquée sinon). Exécution : **planifié 106 050/106 000 (100%)** — 29/09 = 38 000 plein, 01/10 = 37 850 (manque 150), 02/10 = 30 200 (+200 toléré ≤500), 439 exclusions, 238 non planifiées. |
| v77 | 28/09/2026 | **SOFAB PROVENDERIE SO2604-52011 (4 400) forcée au 01/10 en totalité** (ex-split 3 700/700) et **GIC JEPRO SO2605-55433 (6 500) forcée au 29/09 en totalité** (ex-split 2 700 + 3 800) — §14, demande utilisateur, reste inchangé. Exécution : planifié **76 700/76 000 (101%)** — 29/09 = 38 500 (+500 toléré ≤500 : 60066 1 500 placée en entier), 01/10 = 38 200 (+200 toléré ≤500 : 51756 2 100 placée en entier), 439 exclusions, 249 non planifiées. 52840 MEMGBA (5 300) reste non planifiée. |
| v76 | 28/09/2026 | **Restructuration 29/09–01/10 (demande utilisateur)** : ① 69666 (5 300) + 69647 (500) retirées → §13, remplacées par MARSHAL FARMERS SO2605-54941 en **split forcé §14 : 5 800 le 29/09 (mêmes qtés) + 12 200 le 01/10** — retirée de §13. ② 61870 (4 650) + 61869 (1 500) retirées → §13, remplacées par SO2607-63625 (10 000) **en totalité, forcée au 29/09**. ③ TEULONG SO2606-61062 (3 300) **forcée au 01/10** (§14). ④ 01/10 réservé Nord : seule 65229 (5 200) gardée, **forcée §14** — 69211, 69158, 69314, 69306, 69312, 69316 → §13 (non planifiées). **Correctifs script** : agrégation des réf. multi-lignes (54941 = 18 000 + 200 → 18 200 ; le reliquat 200 se place sur le 29/09) + Littoral non compté comme région effective sur date verrouillée (extension v28, sinon 12 200 Littoral bloquaient Nord+Centre le 01/10). **Exécution : planifié 76 000/76 000 (100%)** — 29/09 = 38 000 plein (55433 split 2 700 + 52011 3 700), 01/10 = 38 000 plein (55433 3 800, MARSHAL 12 200, 61062, 65229), 439 exclusions, **247 non planifiées**. Évincées par les forcées : 52840 MEMGBA (5 300) et 700 de 52011 SOFAB → non planifiées. |
| v75 | 28/09/2026 | **SO2607-62419 (WETE MANGA WILLIAM, Littoral, 1 100) : à programmer à partir du 20/10/2026** (demande utilisateur) — nouveau mécanisme **MIN_DATES** (§13, sous-table « Date minimale », contrainte durable indépendante du cycle) : parser `min_dates` (md_config) + contraintes dans try_schedule_order, Étape 0b Littoral, check Phase 2 et équité v20. Retirée du 29/09 → non planifiées. Exécution : planifié 76 450/76 000 (29/09 = 38 450 — +450 toléré ≤500 (SO2604-51281 2 200 placée avec dépassement 450) ; 01/10 = 38 000 plein), 439 exclusions, 238 non planifiées. |
| v74 | 28/09/2026 | **SO2605-55433 (Gic/Jepro-Agro, Centre, 6 500) traitée comme ÉCHUE pure** (demande utilisateur) — nouveau mécanisme §4 « Commandes traitées comme ÉCHUE pure (non reclassées) » : tableau config + `force_echue_pure` dans md_config.py + surcharge de la détection reclassée (classification initiale et priorité dynamique v20, paramètre `order_ref`). Résultat : classée ÉCHUE (priorité 1) et **planifiée au 29/09 (6 500, Centre)**. Exécution : planifié 75 350/76 000 (29/09 = 37 350 — manque 650 non comblable : seules des ÉCHUE Ouest/Nord ≤1 000 restaient, incompatibles avec le verrouillage Centre du 29/09 ; 01/10 = 38 000 plein), 439 exclusions, 237 non planifiées. |
| v72 | 28/09/2026 | MIAKAUG EPSE SODEA DIANE (Nord, NDERE) : les 4 commandes (SO2608-66549 1 200 + SO2608-66550 1 000 + SO2608-66552 1 400 + SO2608-66553 1 800 = 5 400, échues 26/09) retirées du cycle → §13 (29/09 + 01/10), **à intégrer dans un programme à partir de la semaine prochaine** (demande utilisateur). Exécution : planifié 76 000/76 000 (29/09 = 38 000, 01/10 = 38 000 — les 5 400 libérés recomblés, dépassement +450 résorbé), 439 exclusions, 237 non planifiées. |
| v71 | 28/09/2026 | Surbrillance **CLIENT MULTI-CMD** dans le plan (orange FCE4D6) : lignes d'un même client (Tiers) à livrer avec plusieurs commandes dans la même éclosion — appliquée sur Plan Réel, Plan Marge et Plan Livraisons COQ + entrée de légende dédiée. Règle 5 des contraintes mise à jour (COMPTE TEMPORAIRE ajouté). Exécution : planifié 76 450/76 000 (29/09 = 38 000, 01/10 = 38 450), 439 exclusions, 234 non planifiées. Multi-cmd détectés : TAKAMTSING PROSPER ×3 (29/09), MIAKAUG EPSE SODEA DIANE ×4 + SCOOP EXCELLENCE PLUS ×2 + COGESDI SARL ×2 (01/10). |
| v70 | 28/09/2026 | Client **COMPTE TEMPORAIRE** : à ne jamais programmer (règle utilisateur) — §16 client exclu, CLIENT_EXCLU du script (tuple), §12 +1 (SO2606-60929, 700 — ex-planifiée au 29/09) et SO2606-61347 (50) raison mise à jour. Exécution : planifié 76 450/76 000 (29/09 = 38 000 plein, 01/10 = 38 450 — +450 toléré ≤500), 439 exclusions, 234 non planifiées. |
| v69 | 27/09/2026 | Nouveau cycle 29/09 (Mardi, Centre — 38 000 réel / 36 100 marge) + 01/10 (Jeudi, Nord + Centre — 38 000 réel / 36 100 marge) : §1/§4/§6 mis à jour, §4 réf = 29/09. §13 vidé (exclusions 25/09 passées) puis +3 : MARSHAL FARMERS 18 000, NGNIMPEYE 4 200, TCHANTCHOU 3 100 exclues du cycle (29/09 Centre prioritaire — Littoral limité au minime 7 900). Exécution : planifié 75 350/76 000 (29/09 = 37 350, manque 650 ; 01/10 = 38 000 plein), 438 exclusions, 244 non planifiées. |
| v68 | 26/09/2026 | Exécution automatique. Planifié 44,000/44,000. 438 exclusions. |
| v67 | 25/09/2026 | §12 +1 : SO2601-42302 METAFE (38 000, BERI, PONTE PREMIUM) — **déjà livrée**, livraison confirmée hors ERP (reste 38 000 dans l'ERP, StatutFacture=Brouillon). Exécution : planifié 46 700/44 000 (inchangé), 425 exclusions, 246 non planifiées. |
| v66 | 25/09/2026 | §12 −3 : SO2606-61062 TEULONG (reste 3 300), SO2606-58836 TSAFACK (8 500) et SO2607-62671 BOGNING (5 000) — commandes « En attente — programmation ultérieure » / « Retirée du plan » remises dans les non planifiées. Exécution : planifié 46 700/44 000 (23/09 = 17 500, 25/09 = 29 200), 424 exclusions, 246 non planifiées. |
| v65 | 24/09/2026 | §14 : BIEPIP SO2606-60194 reliquat 250 (PONTE PREMIUM, 7 550/7 800 livrés) basculé du 23/09 au 25/09. Total forcé 23/09 : 17 500 (117%) ; 25/09 : 29 200 (101%, +200). Exécution : planifié 46 700/44 000, 427 exclusions. |
| v64 | 23/09/2026 | Exécution automatique. Planifié 46,700/44,000. 427 exclusions. |
| v63 | 23/09/2026 | 25/09 : WAYAP SO2606-59891 retirée, MAGDALENE + WETE MANGA + PENKA + DJUISSI exclues (§13) — remplacées par TUMENTA SO2604-53701 2 000 + LEMNYUY SO2606-59760 1 000 + WAYAP SO2609-69790 2 700 (MBOUDA) forcées (§14). Total forcé 25/09 : 28 950. |
| v62 | 23/09/2026 | Exécution automatique. Planifié 46,850/44,000. 427 exclusions. |
| v61 | 23/09/2026 | 25/09 : OTANG 500 et Alfred Fon Ja-Ai 5 300 (BUEA, Littoral) retirées du 25/09 (§13), remplacées par ALEMAWO SO2607-61638 4 000 (BERI) + WAYAP SO2606-59891 2 200 (FAMLA) forcées (§14). Total forcé 25/09 : 25 450 (88%). |
| v60 | 23/09/2026 | Exécution automatique. Planifié 47,250/44,000. 427 exclusions. |
| v59 | 23/09/2026 | Nouvelle éclosion 25/09/2026 (Vendredi, Ouest — 29 000 réel / 27 550 marge). §1/§6 + 25/09 Ouest ; 23/09 conservée. §14 25/09 : NGOUADJEU 3 300 (NKONGSAMBA, Littoral minime) + KAMGANG 5 800 (NDJELENG) + TESEHKOUE 10 150 (FAMLA) — 19 250 forcés, toutes Payées/ÉCHUE. AT(35) figé archivé (hors extractions/). |
| v58 | 21/09/2026 | Exécution automatique. Planifié 17,750/15,000. 427 exclusions. |
| v57 | 21/09/2026 | §14 23/09 : TAJOUO 12 000/12 000 en totalité (ex-10 000/12 000) — dépassement d'éclosion assumé. Total forcé : 17 750 (118% vs 15 000). |
| v55 | 21/09/2026 | Nouveau cycle 23/09/2026 (Mercredi, Ouest + Centre — 15 000 réel / 14 250 marge). Extraits AT(44)+EXP(15) du 21/09. 11/09 et 15/09 retirées (§1/§4/§6), §13 vidé. §14 23/09 : LEMOKEM 2 000 + TAJOUO 10 000/12 000 + BIEPIP reliquat 250 + GIC MOS 3 500 — 15 750 forcés (105%). §17 affiné (confiance AT si livraisons réelles). |
| v56 | 21/09/2026 | Exécution automatique. Planifié 15,750/15,000. 427 exclusions. |
| v54 | 17/09/2026 | Statuts ERP AT(39) 16/09 + EXP(12) 17/09 : §14 11/09 vidé 3/4 livrées (MAGNE JOSEPHINE 1 250 non livrée → non planifiée), §14 15/09 vidé 8/8 livrées (38 650). §12 inchangé. 62349 désormais État=Livrée. 72 nouvelles commandes (33 BELGO). Plan non régénéré. |
| v52 | 14/09/2026 | 15/09 : TAKAMTSING 51282 retirée de §14 (repasse en non planifiée), remplacée par BOUKAR ISAIE SO2604-52017 (3 100, BELGO-BERI — Littoral minime). Total forcé 15/09 : 38 650 (+1 150 vs 37 500). |
| v53 | 14/09/2026 | Exécution automatique. Planifié 60,100/57,500. 399 exclusions. |
| v50 | 11/09/2026 | 15/09 : MEKA FOKO 63332 forcée en totalité 10 000 (ex-split 6 600, §13 retirée) ; TAKAMTSING 51282 (5 800, NKOABANG) forcée en totalité (ex-ajout algo). Total forcé 15/09 : 41 350 (+3 850 vs 37 500). 61870/61869 restent exclues §13. |
| v51 | 11/09/2026 | Exécution automatique. Planifié 62,800/57,500. 399 exclusions. |
| v48 | 11/09/2026 | 15/09 : TAKAMTSING 61870/61869 retirées (exclues §13) remplacées par MEKA FOKO 63332 splitée 6 600/10 000 (reste 3 400 date ultérieure, exclu §13) ; KUETCHE 62349 remplacée par KAFAB 53917 (2 300). Total forcé 15/09 : 32 150. |
| v49 | 11/09/2026 | Exécution automatique. Planifié 59,400/57,500. 399 exclusions. |
| v46 | 11/09/2026 | Nouvelle éclosion 15/09/2026 (Mardi, Centre — 37 500 réel / 35 650 marge). §1/§6 + 15/09 Centre. §14 15/09 : 6 ex-11/09 (YOUMSSI, KUETCHE, TAKAMTSING ×2, AFRIQUE TOPO, PROVENDERIE = 19 400) + WAFIN GAELLE 10 000 (ex-09/09) — 29 400 forcés, 8 100 libres. |
| v47 | 11/09/2026 | Exécution automatique. Planifié 59,400/57,500. 399 exclusions. |
| v44 | 09/09/2026 | Éclosion du 09/09 avortée : §1/§6 réduits au 11/09 (03/09 et 07/09 passées retirées), §4 réf = 11/09. §13 : 62698 retirée. §14 11/09 : NGOMPE 59718 reliquat 17 200 + LEMOKEM 1 000 + 2 000 (basculées du 09/09) + MAGNE JOSEPHINE 62698 1 250 forcée — 21 450 (+1 450 vs 20 000). Le reste (DASSI, WAFIN, 6 ex-11/09) repasse en non planifié. |
| v45 | 09/09/2026 | Exécution automatique. Planifié 21,450/20,000. 399 exclusions. |
| v43 | 09/09/2026 | Statuts ERP AT(35)+EXP(10) du 09/09 : §14 03/09 vidé (5/5 livrées), §14 07/09 vidé (WANTSA 7 000/7 000, NGOMPE 59718 7 800 expédiés → reliquat basculé 09/09), §14 09/09 : 59723 retirée (livrée 15 000/15 000), 59718 → 17 200. Jour inchangé à 33 400 (+3 400). Plan non régénéré. |
| v41 | 08/09/2026 | 09/09 : NGOMPE 59723/59718 passées en reliquats (5 600 + 11 600 — 9 400/15 000 et 13 400/25 000 livrés) ; SO2606-58898 (1 000) et SO2606-59675 (2 000) forcées — jour à 33 400 (+3 400). |
| v42 | 08/09/2026 | Exécution automatique. Planifié 93,900/90,000. 391 exclusions. |
| v40 | 04/09/2026 | Nouvelles extractions AT(29)+EXP(9) du 04/09. Statuts ERP : §14 03/09 −2 livrées (KAMTA 5 200/5 200, Kamgang 1 500/1 500), §12 −4 livrées dans l'ERP (Gic Emocolit ×2, Quay's Idriss, NJOSSI). 17 nouvelles commandes depuis le 01/09. Plan non régénéré. |
| v38 | 02/09/2026 | 11/09 : KUETCHE SO2607-62349 retirée, exclue §13 avec MAGNE JOSEPHINE SO2607-62698 (ex-11/09) ; PROVENDERIE L' ASSURANCE SO2603-50691 (3 000) forcée à la place — 19 400 forcés, reste 600. |
| v39 | 02/09/2026 | Exécution automatique. Planifié 91,800/90,000. 384 exclusions. |
| v37 | 02/09/2026 | §14 : NGOMPE 59723/59718 splits 2/2 (5 900 + 11 900) déplacés du 11/09 au 09/09 ; + DASSI 3 200 + WAFIN 10 000 forcées au 09/09 (jour à 31 000, +1 000). 11/09 : 6 commandes Centre forcées (YOUMSSI 3 000, KUETCHE 3 050 + reliquat 1 200, TAKAMTSING 4 650 + 1 500, AFRIQUE TOPO 4 200) — 17 600, reste 2 400. |
| v38 | 02/09/2026 | Exécution automatique. Planifié 92,800/90,000. 384 exclusions. |
| v36 | 02/09/2026 | Nouvelle éclosion 09/09/2026 (Mercredi, Centre) — 30 000 réel / 28 500 marge. §12 +3 livrées hors ERP (Quay's Idriss 1 100, Gic Emocolit 500, NJOSSI 50). §14 03/09 + Kamgang Emmanuel reliquat 300 (1 200/1 500 livrés) — jour à 21 300 (+300). |
| v37 | 02/09/2026 | Exécution automatique. Planifié 91,550/90,000. 384 exclusions. |
| v34 | 01/09/2026 | 11/09 : Mogum Fossi retirée définitivement (modifiée en poussins chair → §12) — 11/09 revient à Ouest+Centre (17 800 forcés, 2 200 libres). 07/09 : SO2606-60227 WANTSA 7 000 (MBOUDA, en totalité) forcée (remplace MOFFO BERTIN — 20 100, +1 100). |
| v35 | 01/09/2026 | Exécution automatique. Planifié 61,100/60,000. 381 exclusions. |
| v35 | 01/09/2026 | Exécution automatique. Planifié 61,400/60,000. 380 exclusions. |
| v35 | 01/09/2026 | Exécution automatique. Planifié 60,300/60,000. 380 exclusions. |
| v35 | 01/09/2026 | Exécution automatique. Planifié 60,300/60,000. 380 exclusions. |
| v35 | 01/09/2026 | Exécution automatique. Planifié 60,300/60,000. 355 exclusions. |
| v33 | 01/09/2026 | Nouveau cycle 03–11/09 (03/09 Jeudi 21 000, 07/09 Lundi 19 000, 11/09 Vendredi 20 000 — 60 000 réel / 57 000 marge). §4 réf = 07/09/2026. §6 : 03/09 Nord+Centre+Ouest, 07/09 Ouest, 11/09 Ouest+Centre. §14 : 03/09 21 000 forcés (5 refs + NGOMPE 59723 split 9 100), 07/09 13 100 (NGOMPE 59718 split), 11/09 17 800 (NGOMPE fin des 2 splits). §13 à redéfinir. Plan non généré. |
| v32 | 01/09/2026 | Nouvelles extractions AT(28)+EXP(8) du 01/09. Statuts ERP : §14 vidé (10/10 livrées — PEKA ×2, Gic Emocolit confirmées hors ERP), §10 vidé (PEKA livrée), §13 −1 livrée (Manfouo Mathieu), §12 −1 redevenue active (Mogum Fossi 2 500) + LEMOKEM 28 000 ré-exclue définitivement (remplacée par SO2607-64515 PREMIUM livrée 28 000/28 000) + 3 hors ERP (PEKA 9 250, PEKA 12 750, Gic Emocolit 5 500). En attente des nouvelles dates d'éclosion. |
| v30 | 24/08/2026 | Éclosion 27/08 déplacée au 25/08 (Mardi). §1/§6/§13/§14 mis à jour sur 25/08 ; 28/08 inchangé. |
| v31 | 28/08/2026 | Exécution automatique. Planifié 67,250/65,400. 353 exclusions. |
| v31 | 24/08/2026 | Exécution automatique. Planifié 67,250/65,400. 353 exclusions. |
| v31 | 24/08/2026 | Exécution automatique. Planifié 67,250/65,400. 353 exclusions. |
| v28 | 20/08/2026 | Nouveau cycle 27–28/08 (65 400 réel / 62 100 marge). Régions : 27/08 Ouest+Centre, 28/08 Centre. Forcées 27/08 : Kenne 8 300 + PEKA 9 250 + PEKA 12 750 + PENKA 2 550 + DOM KANSE 2 000. §12 : 6 Reportée retirées. §13 : WANTSA + DASSI exclues du 27/08. |
| v29 | 20/08/2026 | Exécution automatique. Planifié 67,250/65,400. 353 exclusions. |
| v29 | 20/08/2026 | Exécution automatique. Planifié 68,000/65,400. 353 exclusions. |
| v29 | 20/08/2026 | Exécution automatique. Planifié 65,200/65,400. 353 exclusions. |
| v29 | 20/08/2026 | Exécution automatique. Planifié 65,200/65,400. 353 exclusions. |
| v29 | 20/08/2026 | Exécution automatique. Planifié 65,200/65,400. 353 exclusions. |
| v27 | 20/08/2026 | Nouvelles extractions AT(17)+EXP(7) du 17/08. Mise à jour des statuts : §10 −2 livrées, §12 −2 livrées + 3 qtés mises à jour, §14 vidé (11 livrées, 2 à repositionner), §15 −1 livrée. En attente des nouvelles dates d'éclosion. |
| v24 | 14/07/2026 | Nouveau cycle 14–16/07 (3 dates, 86 450 réel / 82 100 marge). Régions : Ouest, Ouest, Ouest+Centre. Forcées 03/07 retirées (date passée). Extractions en attente de mise à jour. |
| v25 | 06/08/2026 | Exécution automatique. Planifié 52,900/50,200. 341 exclusions. |
| v25 | 05/08/2026 | Exécution automatique. Planifié 52,900/50,200. 341 exclusions. |
| v25 | 04/08/2026 | Exécution automatique. Planifié 52,900/50,200. 341 exclusions. |
| v25 | 03/08/2026 | Exécution automatique. Planifié 52,900/50,200. 340 exclusions. |
| v25 | 03/08/2026 | Exécution automatique. Planifié 52,900/50,200. 340 exclusions. |
| v25 | 03/08/2026 | Exécution automatique. Planifié 52,750/50,200. 338 exclusions. |
| v25 | 03/08/2026 | Exécution automatique. Planifié 52,750/50,200. 337 exclusions. |
| v25 | 28/07/2026 | Exécution automatique. Planifié 36,450/36,350. 332 exclusions. |
| v25 | 28/07/2026 | Exécution automatique. Planifié 36,800/36,350. 332 exclusions. |
| v25 | 27/07/2026 | Exécution automatique. Planifié 37,900/36,350. 331 exclusions. |
| v25 | 27/07/2026 | Exécution automatique. Planifié 35,900/36,350. 332 exclusions. |
| v25 | 27/07/2026 | Exécution automatique. Planifié 36,350/36,350. 331 exclusions. |
| v25 | 24/07/2026 | Exécution automatique. Planifié 88,750/88,750. 320 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 90,700/86,750. 320 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 96,750/86,750. 319 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 97,200/86,750. 319 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 97,250/86,750. 319 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 96,750/86,750. 317 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 86,950/86,750. 316 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 86,750/86,750. 317 exclusions. |
| v25 | 21/07/2026 | Exécution automatique. Planifié 87,000/86,750. 298 exclusions. |
| v25 | 15/07/2026 | Exécution automatique. Planifié 87,600/86,450. 297 exclusions. |
| v25 | 15/07/2026 | Exécution automatique. Planifié 88,900/86,450. 297 exclusions. |
| v25 | 15/07/2026 | Exécution automatique. Planifié 87,300/86,450. 297 exclusions. |
| v25 | 15/07/2026 | Exécution automatique. Planifié 87,300/86,450. 296 exclusions. |
| v25 | 14/07/2026 | Exécution automatique. Planifié 95,350/86,450. 297 exclusions. |
| v25 | 14/07/2026 | Exécution automatique. Planifié 95,550/86,450. 287 exclusions. |
| v25 | 14/07/2026 | Exécution automatique. Planifié 94,900/86,450. 287 exclusions. |
| v20 | 21/06/2026 | Nouvelles extractions (AT 5, EXP 3). Nouveau cycle 24/06–30/06 (3 dates, 98 000 réel / 90 650 marge). Nettoyage livrées : 15 commandes retirées de §10/§12/§14/§15. 3 exclusions redevenues actives. Livraison partielle SO2602-46160 (11 650+200 livrés, reste 15 350). |
| v21 | 03/07/2026 | Exécution automatique. Planifié 66,150/65,550. 290 exclusions. |
| v21 | 03/07/2026 | Exécution automatique. Planifié 66,150/65,550. 290 exclusions. |
| v21 | 03/07/2026 | Exécution automatique. Planifié 65,050/65,550. 290 exclusions. |
| v21 | 03/07/2026 | Exécution automatique. Planifié 65,050/65,550. 292 exclusions. |
| v21 | 01/07/2026 | Exécution automatique. Planifié 65,250/65,550. 291 exclusions. |
| v21 | 01/07/2026 | Exécution automatique. Planifié 65,250/65,550. 291 exclusions. |
| v21 | 01/07/2026 | Exécution automatique. Planifié 65,250/65,550. 291 exclusions. |
| v21 | 30/06/2026 | Exécution automatique. Planifié 92,100/92,850. 285 exclusions. |
| v21 | 30/06/2026 | Exécution automatique. Planifié 92,600/92,850. 285 exclusions. |
| v21 | 30/06/2026 | Exécution automatique. Planifié 93,050/92,850. 285 exclusions. |
| v21 | 30/06/2026 | Exécution automatique. Planifié 92,600/92,850. 284 exclusions. |
| v21 | 30/06/2026 | Exécution automatique. Planifié 92,600/92,850. 284 exclusions. |
| v21 | 30/06/2026 | Exécution automatique. Planifié 93,050/92,850. 257 exclusions. |
| v22 | 30/06/2026 | Nouvelles extractions AT(8)+EXP(4). Nettoyage livrées : 17 commandes retirées (§10:1, §12:3, §13:2, §14:11, §15:1). Nouvelles prévisions : 30/06, 02/07, 03/07, 16/07 (120 300 réel). |
| v21 | 25/06/2026 | Exécution automatique. Planifié 55,000/55,150. 258 exclusions. |
| v21 | 25/06/2026 | Exécution automatique. Planifié 55,000/55,150. 257 exclusions. |
| v21 | 25/06/2026 | Exécution automatique. Planifié 55,150/55,150. 256 exclusions. |
| v21 | 25/06/2026 | Exécution automatique. Planifié 54,900/55,150. 256 exclusions. |
| v21 | 25/06/2026 | Exécution automatique. Planifié 54,900/55,150. 255 exclusions. |
| v21 | 22/06/2026 | Exécution automatique. Planifié 90,250/90,650. 253 exclusions. |
| v21 | 22/06/2026 | Exécution automatique. Planifié 90,250/90,650. 253 exclusions. |
| v21 | 22/06/2026 | Exécution automatique. Planifié 90,250/90,650. 253 exclusions. |
| v21 | 22/06/2026 | Exécution automatique. Planifié 90,250/90,650. 253 exclusions. |
| v21 | 22/06/2026 | Exécution automatique. Planifié 90,250/90,650. 253 exclusions. |
| v21 | 22/06/2026 | Exécution automatique. Planifié 90,250/90,650. 253 exclusions. |
| v21 | 22/06/2026 | Exécution automatique. Planifié 90,750/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,800/90,650. 253 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,550/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 90,400/90,650. 252 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 87,650/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 87,600/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 88,300/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 87,850/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 88,300/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 61,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 63,600/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 64,600/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 65,100/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 65,100/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 64,650/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 64,650/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 64,900/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 64,700/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 64,700/90,650. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 69,500/98,000. 250 exclusions. |
| v21 | 21/06/2026 | Exécution automatique. Planifié 69,500/98,000. 250 exclusions. |
| v17 | 02/06/2026 | Nouveau cycle juin 2026 : 6 éclosions (04/06–19/06). Capacité 189 000 réel / 174 600 marge. Régions : Ouest+Nord+Est, Centre, Ouest. Reset des forced assignments, excluded_from_date et region_locks du cycle précédent. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 61,850/62,000. 248 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 61,850/62,000. 248 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 61,850/62,000. 246 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 61,650/62,000. 246 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 61,850/62,000. 245 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 97,150/97,300. 244 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 97,250/97,300. 244 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 97,250/97,300. 244 exclusions. |
| v18 | 15/06/2026 | Exécution automatique. Planifié 71,550/97,300. 237 exclusions. |
| v18 | 14/06/2026 | Exécution automatique. Planifié 87,250/97,300. 236 exclusions. |
| v18 | 11/06/2026 | Exécution automatique. Planifié 96,500/97,300. 236 exclusions. |
| v18 | 11/06/2026 | Exécution automatique. Planifié 96,500/97,300. 236 exclusions. |
| v18 | 11/06/2026 | Exécution automatique. Planifié 97,400/97,300. 235 exclusions. |
| v18 | 11/06/2026 | Exécution automatique. Planifié 171,100/174,100. 235 exclusions. |
| v18 | 11/06/2026 | Exécution automatique. Planifié 172,900/174,100. 225 exclusions. |
| v18 | 09/06/2026 | Exécution automatique. Planifié 174,400/174,100. 225 exclusions. |
| v18 | 09/06/2026 | Exécution automatique. Planifié 174,200/174,100. 224 exclusions. |
| v18 | 04/06/2026 | Exécution automatique. Planifié 175,000/174,100. 224 exclusions. |
| v18 | 04/06/2026 | Exécution automatique. Planifié 176,500/175,850. 223 exclusions. |
| v18 | 03/06/2026 | Exécution automatique. Planifié 176,800/175,850. 223 exclusions. |
| v18 | 03/06/2026 | Exécution automatique. Planifié 175,800/175,850. 222 exclusions. |
| v18 | 03/06/2026 | Exécution automatique. Planifié 176,850/175,850. 223 exclusions. |
| v18 | 03/06/2026 | Exécution automatique. Planifié 175,800/175,850. 222 exclusions. |
| v18 | 03/06/2026 | Exécution automatique. Planifié 180,100/175,250. 222 exclusions. |
| v18 | 03/06/2026 | Exécution automatique. Planifié 175,800/175,250. 222 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,350/175,250. 223 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,350/175,250. 223 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,350/175,250. 223 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,450/175,250. 222 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,450/175,250. 222 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,550/175,250. 222 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,050/174,600. 222 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,050/174,600. 222 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,250/174,600. 221 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,250/174,600. 221 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,650/174,600. 221 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,100/174,600. 220 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,100/174,600. 220 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,950/174,600. 218 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,950/174,600. 218 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,950/174,600. 218 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,850/174,600. 217 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,300/174,600. 216 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 175,050/174,600. 216 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,600/174,600. 216 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,600/174,600. 216 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,450/174,600. 216 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 128,000/174,600. 216 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 128,000/174,600. 216 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 174,450/174,600. 120 exclusions. |
| v18 | 02/06/2026 | Exécution automatique. Planifié 144,400/174,600. 120 exclusions. |
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

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

## 22. Dernière Exécution

> Exécutée le **29/09/2026** — Réf: **29/09/2026**

### Résumé

| Métrique | Valeur |
|----------|--------|
| Commandes PONTE | 261 |
| Commandes COQ | 15 |
| Exclusions | 439 |
| Planifié Réel | 106,000 / 106,000 |
| Planifié Marge | 101,400 / 100,700 |
| Non planifiées (marge) | 242 |
| Nouvelles auto-exclusions | 425 |

### Plan Réel par date

| Date | Jour | Région | Livré | Capacité | Taux |
|------|------|--------|-------|----------|------|
| 29/09/2026 | Mar | Centre, Littoral, Ouest | 38,300 | 38,000 | 101% |
| 01/10/2026 | Jeu | Centre, Nord | 37,500 | 38,000 | 99% |
| 02/10/2026 | Ven | Littoral, Ouest | 30,200 | 30,000 | 101% |

### Répartition par priorité

| Priorité | Commandes | Qté restante |
|----------|-----------|-------------|
| IMMINENTE | 19 | 72,750 |
| NON ÉCHUE | 131 | 1,140,750 |
| RECLASSÉE | 14 | 96,350 |
| ÉCHUE | 89 | 660,050 |
| ÉCHUE RECLASSÉE | 8 | 125,400 |
