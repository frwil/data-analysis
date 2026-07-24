# Contraintes du Plan de Livraisons BELGO

## 1. Plan de Production

| Date | Jour | Plan annoncé | Réel | Marge (95%) | Région principale |
|------|------|-------------|------|-------------|-------------------|
| 23/07/2026 | Jeudi | 38 000 | 36 400 | 34 550 | Centre, Nord |
| 24/07/2026 | Vendredi | 16 000 | 16 000 | 15 200 | Ouest |
| 28/07/2026 | Lundi | 38 000 | 36 350 | 34 500 | Ouest, Centre |

- **Plan annoncé** = Production prévue
- **Réel** = Prévision à considérer pour le plan
- **Marge** = 95% du réel, arrondi au multiple de 50
- Capacité totale Réelle : 88 750
- Capacité totale Marge : 84 250
- Capacité totale Annoncée : 92 000

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

- Date de référence = 24/07/2026 (1ère date d'éclosion 23/07 + 1 jour)
- **Équité de programmation (v20)** : pour une commande programmée à une date X, le statut d'échéance est recalculé par rapport à **X + 1 jour** (et non à aujourd'hui). Cela évite de pénaliser une commande repoussée à une date ultérieure et tient compte du délai de mise à disposition post-éclosion.

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

| Date | Régions autorisées |
|------|--------------------|
| 23/07/2026 | Centre, Nord |
| 24/07/2026 | Ouest, Centre |
| 28/07/2026 | Ouest, Centre |

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

| Réf. | Client | Qté | Région | Raison |
|------|--------|-----|--------|--------|
| SO2602-47700 | PEKA TAGNE IGNACE | 9 250 | Ouest | Livraison totale le même jour |
| SO2602-46922 | KUATE NOKAM GUY SALOMON | 1 100 | Ouest | Livraison totale le même jour |
| SO2606-59033 | TCHANGANG GILBERT | 2 800 | Ouest | Livraison totale le même jour |
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
| SO2507-25604 | — | — | — | — | Commande retirée (absente des extractions) |
| SO2509-31314 | — | — | — | — | Échéance hors période : septembre (absente des extractions) |
| SO2506-24935 | — | — | — | — | Commande non sûre (absente des extractions) |
| SO2602-46834 | TOWA LUC | 2 200 | BELGO-FAMLA | 08/07/2026 | **Retirée du plan** — sur demande |
| SO2604-53945 | KOAGNE TCHOUDA DADINE CAROLLE | 3 300 | BELGO-NDJELENG | 15/05/2026 | **Retirée du plan** — sur demande |
| SO2602-46455 | Midland Company Limited | 100 | BELGO-BERI | 01/07/2026 | **Retirée du plan** — sur demande |
| SO2604-51968 | Mogum Fossi Laurence Lor | 2 500 | BELGO-BERI | 04/09/2026 | **Annulée** — commande annulée dans l'ERP |
| SO2604-52480 | TAKAMTSING PROSPER | 200 | BELGO-MESSASSI | 21/04/2026 | **Déjà livrée** — livraison confirmée (COQ) |
| SO2603-49511 | GIC FAMES | 4 200 | BELGO-NKOABANG | 01/08/2026 | **En attente** — livraison ultérieure |
| SO2605-57283 | NGUIMDJOU ROGER | 10 000 | BELGO-NKONGSAMBA | 22/08/2026 | **Reportée** — client pas prêt, programmation ultérieure |
| SO2604-53606 | PRODIPEL SARL | 15 700 | BELGO-NDJELENG | 23/09/2026 | **Non reclassée** — mise en non planifiée |
| SO2605-56687 | Kenne Manfouo Idrice | 34 800 | BELGO-NDJELENG | 02/07/2026 | **En attente** — programmation à partir du 20/07 (retirée du 16/07) |
| SO2602-47700 | PEKA TAGNE IGNACE | 9 250 | BELGO-FAMLA | 01/07/2026 | **En attente** — reprogrammation 03/07 |
| SO2604-52451 | NOUPING | 1 500 | BELGO-BERI | 01/08/2026 | **En attente** — reprogrammation 03/07 |
| SO2607-62689 | Manfouo Mathieu | 4 100 | BELGO-NKONGSAMBA | 19/12/2026 | **Reportée** — attente prochaine programmation |
| SO2606-58836 | TSAFACK ROBERT | 8 500 | BELGO-MESSASSI | 26/06/2026 | **En attente** — programmation ultérieure |
| SO2607-62671 | BOGNING | 4 100 | BELGO-MESSASSI | 14/07/2026 | **En attente** — programmation ultérieure |
| SO2607-61674 | LAMBOU TINO | 3 300 | BELGO-FAMLA | 11/07/2026 | **Reportée** — reprogrammation ultérieure |

---

## 13. Exclusions par Date (EXCLUDED_FROM_DATE)

*Aucune exclusion par date pour le cycle en cours.*

---

## 14. Assignations Forcées (FORCED_ASSIGNMENTS)

### 23/07 (Centre, Nord)

| Réf. | Client | Qté | Agence | Raison |
|------|--------|-----|--------|--------|
| SO2604-52423 | Groupe D'initiative Commune Des Jeunes Producteurs Agropastoraux De L'est (Gic/Jepro-Agro) | 6 600 | BELGO-MESSASSI | Assignée au 23/07 — ÉCHUE Centre |
| SO2603-48511 | DJEMENI KAMENI | 1 700 | BELGO-NKOLBISSON | Assignée au 23/07 — ÉCHUE Centre |
| SO2606-59999 | SEUYA GILDAS DIDIER (SEUYA GILDAS DIDIER) | 1 500 | BELGO-NKONGSAMBA | Assignée au 23/07 — ÉCHUE Littoral |
| SO2606-59007 | LAMINE BOUBA | 4 500 | BELGO-NDERE | Assignée au 23/07 — ÉCHUE Nord |
| SO2605-54348 | Ngouana Anselme | 3 000 | BELGO-NDERE | Assignée au 23/07 — ÉCHUE Nord |
| SO2604-53962 | Haman Soudi | 3 000 | BELGO-NDERE | Assignée au 23/07 — ÉCHUE Nord |
| SO2605-57151 | HAMIDOU MOUSSA | 1 300 | BELGO-NDERE | Assignée au 23/07 — ÉCHUE Nord |
| SO2605-56126 | Sandeep Tirkey | 1 000 | BELGO-NDERE | Assignée au 23/07 — ÉCHUE Nord |
| SO2607-62732 | DJEMENI KAMENI | 300 | BELGO-NKOLBISSON | Assignée au 23/07 — ÉCHUE Centre (≤1000) |

### 24/07 (Ouest, Centre)

| Réf. | Client | Qté | Agence | Raison |
|------|--------|-----|--------|--------|
| SO2606-59715 | LEMOKEM TIODOU ZEPHIRIN | 13 700 | BELGO-FAMLA | Assignée au 24/07 — ÉCHUE Ouest (split 1/2) |
| SO2606-58677 | LAMBO NGOUO RIVALDO | 2 300 | BELGO-BERI | Assignée au 24/07 — Littoral |

### 28/07 (Ouest, Centre)

| Réf. | Client | Qté | Agence | Raison |
|------|--------|-----|--------|--------|
| SO2606-59715 | LEMOKEM TIODOU ZEPHIRIN | 14 300 | BELGO-FAMLA | Assignée au 28/07 — split 2/2 |
| SO2603-48726 | GLOBAL BUSINESS | 5 950 | BELGO-MESSASSI | Reliquat — Assignée au 28/07 |
| SO2606-58519 | KUHLIFARM COOP-BOD (KUMBA KOPEFUL LIVESTOCK FARMERS) | 5 000 | BELGO-BERI | Assignée au 28/07 — Littoral |
| SO2606-58995 | ETAPE GRACE EKUME | 500 | BELGO-BERI | Assignée au 28/07 — Littoral |
| SO2606-61325 | GIC DES AGRICULTEURS DE TSINGBEU | 3 000 | BELGO-FAMLA | Assignée au 28/07 — ÉCHUE Ouest |
| SO2606-60951 | NGOBESING BLAISIUS NGWA | 2 300 | BELGO MBOUDA | Assignée au 28/07 — ÉCHUE Ouest |

---

## 15. Inclusions Exceptionnelles (SPECIAL_INCLUDE)

Commandes non-BELGO incluses exceptionnellement avec surcharge de région et agence :

| Réf. | Client | Agence d'origine | Agence surchargée | Région surchargée |
|------|--------|------------------|-------------------|-------------------|
| SO2602-47515 | SHOUEP ROGER ANDERZIL | AGRO-TMC-AKWA | BELGO-FAMLA | Ouest |

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

## 19. Fichiers Source (v25)

| Fichier | Rôle |
|---------|------|
| NJS GROUP ERP - Lignes de commandes + multicompany (1).xlsx | AT principal — 21/07/2026 — 1 407 lignes |
| NJS GROUP ERP - Lignes des expeditions + multicompany.xlsx | EXP principal — 21/07/2026 — 762 lignes |

**v25** : Nouveau cycle 23–28/07 (3 dates, 86 750 réel / 82 350 marge). Nouvelles extractions du 21/07. Ancien cycle 14-16/07 clôturé — toutes les forcées livrées et retirées.

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
| v24 | 14/07/2026 | Nouveau cycle 14–16/07 (3 dates, 86 450 réel / 82 100 marge). Régions : Ouest, Ouest, Ouest+Centre. Forcées 03/07 retirées (date passée). Extractions en attente de mise à jour. |
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

## 22. Dernière Exécution

> Exécutée le **24/07/2026** — Réf: **24/07/2026**

### Résumé

| Métrique | Valeur |
|----------|--------|
| Commandes PONTE | 194 |
| Commandes COQ | 19 |
| Exclusions | 320 |
| Planifié Réel | 88,750 / 88,750 |
| Planifié Marge | 84,650 / 84,250 |
| Non planifiées (marge) | 171 |
| Nouvelles auto-exclusions | 301 |

### Plan Réel par date

| Date | Jour | Région | Livré | Capacité | Taux |
|------|------|--------|-------|----------|------|
| 23/07/2026 | Jeu | Centre, Littoral, Nord | 36,400 | 36,400 | 100% |
| 24/07/2026 | Ven | Littoral, Ouest | 16,000 | 16,000 | 100% |
| 28/07/2026 | Mar | Centre, Littoral, Ouest | 36,350 | 36,350 | 100% |

### Répartition par priorité

| Priorité | Commandes | Qté restante |
|----------|-----------|-------------|
| IMMINENTE | 8 | 46,900 |
| NON ÉCHUE | 133 | 958,200 |
| RECLASSÉE | 13 | 85,800 |
| ÉCHUE | 34 | 179,150 |
| ÉCHUE RECLASSÉE | 6 | 50,800 |
