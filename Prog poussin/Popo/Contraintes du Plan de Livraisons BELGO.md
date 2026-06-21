# Contraintes du Plan de Livraisons BELGO

## 1. Plan de Production

| Date | Jour | Réel | Marge (95%) | Région principale |
|------|------|------|-------------|-------------------|
| 24/06/2026 | Mercredi | 35 500 | 33 700 | Ouest |
| 25/06/2026 | Jeudi | 27 700 | 26 300 | Centre |
| 30/06/2026 | Mardi | 27 450 | 26 050 | Ouest |

- **Réel** = Prévision à considérer pour le plan
- **Marge** = 95% du réel, arrondi au multiple de 50
- Capacité totale Réelle : 90 650
- Capacité totale Marge : 86 050

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

- Date de référence = 24/06/2026 (date d'éclosion cible)
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
| 24/06/2026 | Ouest uniquement |
| 25/06/2026 | Centre, Nord, Est |
| 30/06/2026 | Ouest, Centre |

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
| SO2605-55879 | TCHEMBENG ANTOINE | 10 000 | Ouest | Livraison totale le même jour |
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
| SO2603-50721 | CHRISTY NJIE | 500 | BELGO-BERI | 20/06/2026 | **Livrée** — confirmé livré |
| SO2602-46834 | TOWA LUC | 2 200 | BELGO-FAMLA | 08/07/2026 | **Retirée du plan** — sur demande |
| SO2604-53945 | KOAGNE TCHOUDA DADINE CAROLLE | 3 300 | BELGO-NDJELENG | 15/05/2026 | **Retirée du plan** — sur demande |
| SO2602-46455 | Midland Company Limited | 100 | BELGO-BERI | 01/07/2026 | **Retirée du plan** — sur demande |
| SO2604-51968 | Mogum Fossi Laurence Lor | 2 500 | BELGO-BERI | 04/09/2026 | **Annulée** — commande annulée dans l'ERP |
| SO2605-57283 | NGUIMDJOU ROGER | 10 000 | BELGO-NKONGSAMBA | 22/08/2026 | **Reportée** — client pas prêt, programmation ultérieure |
| SO2604-53606 | PRODIPEL SARL | 15 700 | BELGO-NDJELENG | 23/09/2026 | **Non reclassée** — mise en non planifiée |
| SO2604-52536 | TAMATIO | 1 100 | BELGO AHALA | — | **Déjà livrée** — confirmé livré |
| SO2601-42254 | Gic Producteurs De Mais De Yaounde | 7 000 | BELGO AHALA | — | **Déjà livrée** — confirmé livré |

---

## 13. Exclusions par Date (EXCLUDED_FROM_DATE)

| Réf. | Dates exclues |
|------|---------------|
| SO2604-53962 | 25/06/2026 |
| SO2605-54348 | 25/06/2026 |
| SO2605-56126 | 25/06/2026 |
| SO2605-56535 | 25/06/2026 |
| SO2605-57151 | 25/06/2026 |
| SO2606-59007 | 25/06/2026 |
| SO2606-59009 | 25/06/2026 |
| SO2606-59204 | 25/06/2026 |
| SO2606-59223 | 25/06/2026 |
| SO2606-60214 | 25/06/2026 |
| SO2605-57161 | 25/06/2026 |
| SO2603-48511 | 25/06/2026 |

---

## 14. Assignations Forcées (FORCED_ASSIGNMENTS)

### 24/06 (Ouest)

| Réf. | Client | Qté | Agence | Raison |
|------|--------|-----|--------|--------|
| SO2602-46160 | KUETCHE MUKAM ARMAND AIME | 15 350 | SPC BAF-CHEFFERIE | Relicat PONTE — 11 650 PONTE + 200 COQ déjà livrés, reste 15 350 PONTE |

### 25/06 (Nord)

| Réf. | Client | Qté | Agence | Raison |
|------|--------|-----|--------|--------|
| SO2603-50402 | Tchinda Zephirin | 4 100 | BELGO-NDERE | Échue 19/06 |
| SO2606-58000 | LAMINE BOUBA | 1 050 | BELGO-NDERE | Échue 19/06 |
| SO2606-58005 | LAMINE BOUBA | 2 200 | BELGO-NDERE | Échue 19/06 |
| SO2606-58344 | GIC AMITIE | 2 100 | BELGO-NDERE | Échue 19/06 |
| SO2603-50650 | TEFACK DASSI HERVE | 3 600 | BELGO-NDERE | Échue 26/06 |
| SO2604-52437 | ABDOUL AZIZ | 1 000 | BELGO-NDERE | Échue 26/06 |
| SO2604-53285 | Menquele Rodrigue | 1 100 | BELGO-NDERE | Échue 26/06 |
| SO2604-53967 | NOUMSSI HERVE | 2 700 | BELGO-NDERE | Échue 26/06 |
| SO2606-59141 | NOVEACAM (FOCHUE YEMZEU JEAN-CLAUDE) | 4 000 | BELGO AHALA | Sur demande — 25/06 |

### 30/06 (Ouest prioritaire)

| Réf. | Client | Qté | Agence | Raison |
|------|--------|-----|--------|--------|
| SO2606-59672 | TCHINDA KAAWE SOL PLEISIS | 7 500 | BELGO-FAMLA | Échue 20/06 |
| SO2606-59763 | TCHOUNDJIN WATAT ERIC JOEL | 10 000 | BELGO-FAMLA | RECLASSÉE 27/06 — 1er split 10 000/15 000 (≥50%) |

> **Historique cycle précédent** : 15/06 (3 commandes, toutes livrées ✓) et 19/06 (7 commandes, 5 livrées ✓, 2 reportées).

---

## 15. Inclusions Exceptionnelles (SPECIAL_INCLUDE)

Commandes non-BELGO incluses exceptionnellement avec surcharge de région et agence :

| Réf. | Client | Agence d'origine | Agence surchargée | Région surchargée |
|------|--------|------------------|-------------------|-------------------|
| SO2512-38407 | Tchana Heumi Gervais Ronce | AGRO-TMC-AKWA | BELGO-MESSASSI | Centre |
| SO2602-46160 | KUETCHE MUKAM ARMAND AIME | SPC BAF-CHEFFERIE | SPC BAF-CHEFFERIE | Ouest |

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

## 19. Fichiers Source (v20)

| Fichier | Rôle |
|---------|------|
| NJS GROUP ERP - Lignes de commandes + multicompany (5).xlsx | AT principal — 21/06/2026 — 1 221 lignes |
| NJS GROUP ERP - Lignes des expeditions + multicompany (3).xlsx | EXP principal — 21/06/2026 — 829 lignes |

**v20** : Nouvelles extractions du 21/06. Nettoyage des commandes livrées (15 exclusions/assignations retirées).

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
| v20 | 21/06/2026 | Nouvelles extractions (AT 5, EXP 3). Nouveau cycle 24/06–30/06 (3 dates, 98 000 réel / 90 650 marge). Nettoyage livrées : 15 commandes retirées de §10/§12/§14/§15. 3 exclusions redevenues actives. Livraison partielle SO2602-46160 (11 650+200 livrés, reste 15 350). |
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

## 22. Dernière Exécution

> Exécutée le **21/06/2026** — Réf: **24/06/2026**

### Résumé

| Métrique | Valeur |
|----------|--------|
| Commandes PONTE | 158 |
| Commandes COQ | 23 |
| Exclusions | 252 |
| Planifié Réel | 90,550 / 90,650 |
| Planifié Marge | 85,750 / 86,050 |
| Non planifiées (marge) | 139 |
| Nouvelles auto-exclusions | 239 |

### Plan Réel par date

| Date | Jour | Région | Livré | Capacité | Taux |
|------|------|--------|-------|----------|------|
| 24/06/2026 | Mer | Littoral, Ouest | 35,250 | 35,500 | 99% |
| 25/06/2026 | Jeu | Centre, Nord | 27,850 | 27,700 | 101% |
| 30/06/2026 | Mar | Ouest | 27,450 | 27,450 | 100% |

### Répartition par priorité

| Priorité | Commandes | Qté restante |
|----------|-----------|-------------|
| IMMINENTE | 19 | 63,850 |
| NON ÉCHUE | 102 | 713,800 |
| RECLASSÉE | 19 | 143,100 |
| ÉCHUE | 14 | 72,150 |
| ÉCHUE RECLASSÉE | 4 | 55,350 |
