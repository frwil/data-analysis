# 🐣 Plan de Livraisons BELGO — Suivi d'Avancement

> Dernière mise à jour : **21/09/2026** — v55/v56 : nouveau cycle 23/09 (15 000 réels, Ouest + Centre) — 4 forcées (LEMOKEM 2 000, TAJOUO 10 000/12 000, BIEPIP reliquat 250 PREMIUM, GIC MOS 3 500) = 15 750 (105%). Extraits AT(44)+EXP(15) du 21/09.

---

## 🎯 Objet du Projet

Système de **planification de livraisons** pour l'agence **BELGO Ponte Noire** (production de poussins PONTE CLASSIQUE et PONTE PREMIUM).

**But** : Prendre les commandes client en attente dans l'ERP et les organiser en un **plan de livraison optimisé** sur les jours de production disponibles.

---

## 📚 Documents

| Fichier | Contenu |
|---------|---------|
| `Contraintes du Plan de Livraisons BELGO.md` | Config v24 — 3 dates (14/07–16/07) |
| `plan_livraisons.py` | Script principal |
| `md_config.py` | Parser du .md |

---

## 📊 Fichiers Source (v55)

| Fichier | Rôle | Lignes |
|---------|------|--------|
| `NJS GROUP ERP - Lignes de commandes + multicompany (44).xlsx` | AT — 21/09 | 1 540 |
| `NJS GROUP ERP - Lignes des expeditions + multicompany (15).xlsx` | EXP — 21/09 | 1 380 |

> ✅ **Extractions à jour** (21/09/2026 13:50) — statuts ERP mis à jour dans le `.md` (v55) et plan régénéré (v56).
> ⚠ **AT(35) retéléchargé le 17/09 contient des données figées au 09/09** (Date modif. max = 09/09) — ne pas l'utiliser, l'AT de référence est désormais le (44).
> 📄 `output/Plan_Livraisons_BELGO_Ponte.xlsx` généré le 21/09 (v56) : 23/09 = 15 750/15 000 (105%) — 4 forcées, aucune commande ajoutée par l'algo.

---

## 🗺️ Mapping Agence → Région

| Région | Agences |
|--------|---------|
| **Centre** | BELGO-MESSASSI, BELGO-NKOABANG, BELGO-NKOLBISSON, BELGO AHALA |
| **Ouest** | BELGO-FAMLA, BELGO-NDJELENG, BELGO MBOUDA |
| **Littoral** | BELGO-BERI, BELGO VILLAGE, BELGO-BUEA, BELGO-NKONGSAMBA |
| **Est** | BELGO BERTOUA |
| **Nord** | BELGO-NDERE |

---

## 📈 Statut v38 (02/09/2026) — Cycle 03–11/09 (4 dates)

| Date | Jour | Réel | Marge | Région | Planifié réel |
|------|------|------|-------|--------|---------------|
| 03/09/2026 | Jeu | 21 000 | 19 950 | Nord, Centre, Ouest | 21 300 (+300 Kamgang) |
| 07/09/2026 | Lun | 19 000 | 18 050 | Ouest | 20 100 (+1 100 WANTSA) |
| 09/09/2026 | Mer | 30 000 | 28 500 | Centre | 31 000 (+1 000) |
| 11/09/2026 | Ven | 20 000 | 19 000 | Ouest, Centre | 19 400 (97%, manque 600) |
| **Total** | | **90 000** | **85 500** | | **91 800** |

### 🔄 Chronologie v38 (02/09)

1. **11/09** : KUETCHE SO2607-62349 retirée de §14 et exclue §13 avec MAGNE JOSEPHINE SO2607-62698 (ex-11/09) — toutes deux absentes du plan
2. **11/09** : PROVENDERIE L' ASSURANCE SO2603-50691 (3 000, NON ÉCHUE 07/10) forcée à la place — 19 400 forcés, reste 600
3. **Exécution** : 91 800 / 90 000 réel ; 91 800 / 85 500 marge ; 384 exclusions ; 209 non planifiées (marge)

---

### 🔄 Chronologie v40 (04/09)

1. **Extraits AT(29)+EXP(9) du 04/09** : statuts ERP croisés avec les refs du `.md`
2. **§14 03/09 −2 livrées** : KAMTA 5 200/5 200 et Kamgang reliquat 300 (1 500/1 500) retirées — restent 15 800 forcés (Nord 6 700 + Ouest 9 100) non encore livrés dans l'ERP
3. **§12 −4** : Gic Emocolit 5 500 + 500, Quay's Idriss 1 100, NJOSSI 50 désormais **Livrée** dans l'ERP → retirées (auto-exclusion État=Livrée)
4. **Nouvelles commandes depuis le 01/09** : 17 (dont Tengemne 25 000 + 13 000 + 12 000) — prises en compte au prochain run
5. **Plan non régénéré** (sur demande)

---

### 🔄 Chronologie v41 (08/09)

1. **09/09 — NGOMPE reliquats** : SO2606-59723 (9 400/15 000 livrés → reliquat 5 600) et SO2606-59718 (13 400/25 000 livrés → reliquat 11 600) — §14 mis à jour (−600)
2. **09/09 — +2 forcées** : LEMOKEM ANDOLAIN SO2606-58898 (1 000, prévue 09/09) et LEMOKEM TIODOU ZEPHIRIN SO2606-59675 (2 000, prévue 12/09) — Validées/Payées, BELGO-NDJELENG
3. **Exécution (v42)** : 09/09 = 33 400/30 000 (111%, +3 400) ; total réel 93 900/90 000 ; marge 92 850/85 500 ; 391 exclusions ; 217 non planifiées (marge)

---

### 🔄 Chronologie v43 (09/09)

1. **Extraits AT(35)+EXP(10) du 09/09** : croisement des refs du `.md` avec l'ERP
2. **§14 03/09 vidé** : 5/5 livrées dans l'ERP — MOTING 3 200, HAMIDOU 1 000, HASSAN 300 + 2 200, NGOMPE 59723 complète (15 000/15 000)
3. **§14 07/09 vidé** : WANTSA 7 000/7 000 livrée ; NGOMPE 59718 : 7 800 expédiés ERP (pas 13 400) → reliquat 17 200 basculé au 09/09
4. **§14 09/09** : 59723 retirée (livrée) ; 59718 → 17 200 — jour inchangé à 33 400 (+3 400)
5. **Plan non régénéré** (sur demande)

---

### 🔄 Chronologie v44/v45 (09/09)

1. **Éclosion du 09/09 avortée** : §1/§6 réduits au 11/09 (03/09 et 07/09 passées retirées), §4 réf = 11/09
2. **§14 11/09** : NGOMPE 59718 reliquat 17 200 + LEMOKEM 1 000 + 2 000 basculées du 09/09 + MAGNE JOSEPHINE SO2607-62698 (1 250) forcée (ex-§13) — 21 450 forcés, dépassement +1 450
3. **Le reste repasse en non planifié** : DASSI 3 200, WAFIN 10 000 (ex-09/09) et les 6 ex-11/09 (YOUMSSI, KUETCHE, TAKAMTSING ×2, AFRIQUE TOPO, PROVENDERIE)
4. **Exécution (v45)** : 11/09 = 21 450/20 000 (107%, Ouest) ; 399 exclusions ; 236 non planifiées (marge)
5. **Échues/reclassées régénéré** (`output/Commandes_echuees_13-09.xlsx`, AT35) : 101 échues au 13/09 — 840 500 sujets (dont 10 ÉCHUE RECLASSÉE, 11 exclues §12) + 25 reclassées (13 non livrées, 149 950 sujets)

---

### 🔄 Chronologie v46/v47 (11/09)

1. **Nouvelle éclosion 15/09/2026** (Mardi, Centre — 37 500 réel / 35 650 marge) : §1/§6 mis à jour
2. **§14 15/09** : les 6 ex-11/09 (YOUMSSI 3 000, KUETCHE 3 050, TAKAMTSING 4 650 + 1 500, AFRIQUE TOPO 4 200, PROVENDERIE 3 000) + WAFIN GAELLE 10 000 (ex-09/09) — 29 400 forcés, 8 100 libres
3. **Exécution (v47)** : 11/09 = 21 450/20 000 (107%) ; 15/09 = 37 950/37 500 (101%, Centre) ; 399 exclusions ; 228 non planifiées (marge)
4. **Échues au 03/10 + reclassées non livrées** (`output/Commandes_echuees_03-10.xlsx`, AT35) : 145 échues — 976 700 sujets (dont 18 ÉCHUE RECLASSÉE, 13 exclues §12) + 13 reclassées non livrées (149 950 sujets)

---

### 🔄 Chronologie v48/v49 (11/09)

1. **15/09 — KUETCHE remplacée** : SO2607-62349 (reliquat Proctor Ai 2 750) retirée de §14 → remplacée par **KAFAB SO2604-53917** (2 300, MESSASSI, ÉCHUE 04/09, PREMIUM, Payée)
2. **15/09 — TAKAMTSING remplacée** : SO2607-61870 (4 650) + SO2607-61869 (1 500) retirées de §14 → remplacées par **MEKA FOKO SO2607-63332** (10 000, PREMIUM, Payée) **splitée 6 600 le 15/09**, reste 3 400 pour une date ultérieure
3. **§13** : 62349, 61870, 61869 exclues du 15/09 ; **63332 exclue du 15/09** (protège le reste du split — l'Étape 0 forcée ignore §13, la Phase 1 le respecte)
4. **§14 15/09** : 7 forcées = 32 150 (5 350 libres réel / 3 500 marge)
5. **Exécution (v49)** : 11/09 = 21 450/20 000 (107%) ; 15/09 = 37 950/37 500 (101%, Centre) — l'algo a rempli la place libre avec TAKAMTSING SO2604-51282 (5 800) ; **vérifié : 63332 n'apparaît qu'à 6 600, le reste 3 400 n'est pas planifié** ✓

---

### 🔄 Chronologie v50/v51 (11/09)

1. **MEKA FOKO 63332 en totalité** : split 6 600/10 000 annulé — **10 000 forcés le 15/09**, §13 retirée (plus de reste à protéger)
2. **TAKAMTSING 51282 en totalité** : **5 800 forcés le 15/09** (NKOABANG, ÉCHUE 22/08, En cours, 0 livré, Payée) — ex-ajout algo, forcée sur demande
3. **61870/61869 restent exclues §13** du 15/09
4. **Exécution (v51)** : 11/09 = 21 450/20 000 (107%) ; 15/09 = **41 350/37 500 (110%, +3 850)** — 8 forcées, aucune commande ajoutée par l'algo (capacité dépassée)

---

### 🔄 Chronologie v52/v53 (14/09)

1. **15/09 — TAKAMTSING retirée** : SO2604-51282 (5 800, NKOABANG) retirée de §14 → repasse en non planifiée (vérifié dans le plan)
2. **15/09 — remplacée par BOUKAR ISAIE** : **SO2604-52017** (3 100, BELGO-BERI — Littoral minime ≤25%, exempté du verrouillage Centre) forcée sur demande — En cours, 0 livré, Payée, prévue 12/09 → classée ÉCHUE au 15/09 (équité X+1)
3. **Exécution (v53)** : 11/09 = 21 450/20 000 (107%) ; 15/09 = **38 650/37 500 (103%, +1 150)** — 8 forcées, aucune commande ajoutée par l'algo (capacité dépassée)

---

### 🔄 Chronologie v54 (17/09)

1. **Extraits AT(39) du 16/09 + EXP(12) du 17/09** : croisement des refs du `.md` avec l'ERP
2. **§14 11/09 vidé 3/4** : NGOMPE 59718 livrée en totalité (25 000/25 000, reste 0), LEMOKEM ANDOLAIN 1 000/1 000, LEMOKEM TIODOU 2 000/2 000 — retirées
3. **MAGNE JOSEPHINE 62698 (1 250) NON livrée** (0/1 250, En cours) → repasse en non planifiée (à repositionner)
4. **§14 15/09 vidé 8/8 livrées** : YOUMSSI, KUETCHE, AFRIQUE TOPO, PROVENDERIE, WAFIN, KAFAB, MEKA FOKO, BOUKAR ISAIE — 38 650 livrés, cycle 11/09–15/09 entièrement exécuté
5. **§12 inchangé** : aucune exclusion devenue livrée dans l'ERP
6. **§13** : 62349 désormais État=Livrée (1 550/2 750, reste 1 200) ; 61870/61869 toujours En cours, 0 livré — dates exclues passées, §13 à redéfinir au prochain cycle
7. **72 nouvelles commandes** depuis le 09/09 (33 BELGO — dont TEIKING 26 000, IBII OTTO 10 150, KOM BLAISE 10 200, KUEGHANG 10 850, SOFAB ×3)
8. ⚠ **AT(35) retéléchargé le 17/09 = données figées au 09/09** — à ne pas utiliser ; ⚠ EXP(11) du 16/09 était un export sans colonnes Agence/Statut Expédition (remplacé par EXP(12))
9. **Plan non régénéré** (dates du cycle passées — en attente du prochain cycle)

---

### 🔄 Chronologie v55/v56 (21/09)

1. **Nouveau cycle 23/09/2026** (Mercredi, Ouest + Centre — 15 000 réel / 14 250 marge) : §1/§4/§6 mis à jour, 11/09 et 15/09 passées retirées, §13 vidé
2. **Extraits AT(44)+EXP(15) du 21/09 13:50** : BIEPIP SO2606-60194 = **7 550/7 800 livrés dans l'ERP** (expédition SH2608-1631 Traitée, facture IN2609-68336) → reliquat **250 PONTE PREMIUM** ; COQ SO2609-69601 livrée (150/150) ; LEMOKEM 2 000 En cours ; TAJOUO 12 000 Validée ; GIC MOS 3 500 Validée
3. **§14 23/09** : LEMOKEM 2 000 + TAJOUO 10 000/12 000 + BIEPIP reliquat 250 + GIC MOS 3 500 — **15 750 forcés (105%, +750)**
4. **Correctif script (§17)** : Proctor Ai « En cours » + livraisons réelles dans l'AT (Quantité deja livrée > 0) → confiance à l'AT — impacte BIEPIP 60194 et PENKA DEFFO 62511 (3 700/4 250 livrés) ; GIC AMOUR déjà exclue §12
5. **Exécution (v56)** : 23/09 = **15 750/15 000 (105%, Centre+Ouest)** — aucune commande ajoutée par l'algo (capacité dépassée) ; 254 PONTE, 17 COQ, 427 exclusions, 251 non planifiées (marge) ; ÉCHUE 74 (606 800), ÉCHUE RECLASSÉE 8 (120 750), RECLASSÉE 14 (97 400), IMMINENTE 24 (78 200)

---

### Historique v37 (02/09)

- NGOMPE splits 2/2 (5 900 + 11 900) + DASSI 3 200 + WAFIN 10 000 forcées au 09/09 (31 000, +1 000) ; 6 commandes Centre forcées au 11/09 (17 600) ; exécution 92 800 réel / 91 550 marge.

---

### Historique v36 (02/09)

- Nouvelle éclosion 09/09 (30 000/28 500, Centre) ; §12 +3 livrées hors ERP (Quay's Idriss, Gic Emocolit, NJOSSI) ; Kamgang reliquat 300 forcé au 03/09 (21 300, +300) ; exécution 91 550 réel / 88 900 marge.

---

## 📈 Statut v24 (14/07/2026) — Cycle 14/07–16/07

| Date | Jour | Réel | Marge | Région | Forcé |
|------|------|------|-------|--------|-------|
| 14/07/2026 | Mar | 27 850 | 26 450 | Ouest | **27 500** |
| 15/07/2026 | Mer | 28 750 | 27 300 | Ouest | 20 000 |
| 16/07/2026 | Jeu | 29 850 | 28 350 | Ouest, Centre | 38 500 ⚠ |
| **Total** | | **86 450** | **82 100** | | **86 000** |

- ⚠ **Script non exécuté** — en attente de nouveaux extraits ERP
- ⚠ **16/07 en dépassement** : 38 500 forcés / 29 850 capacité (+8 650)
- 14/07 : Mardi → Nord/Est interdits (conforme : Ouest uniquement)
- **Total forcé** : 78 500 / 86 450 (91% de la capacité)

### 🔄 Chronologie v24 (14/07)

1. **Nouveau cycle** : 3 dates de production (14, 15, 16/07)
2. **Capacité totale** : 86 450 réel / 82 100 marge
3. **03/07 clôturé** : forcées retirées de §14
4. **TASSE HUBERT** : 2 commandes (SO2605-56363, SO2605-56364) — 50 000 forcées 14-15-16/07 (20k/20k/10k)
5. **Libération §12** : 3 ÉCHUE Ouest (7 500) → §14 14/07 — KOAGNE, Kenne, Biepip
6. **16/07 en dépassement** : 38 500 forcés / 29 850 capacité

### 📋 Commandes forcées

#### 14/07 (Ouest)

| Réf. | Client | Qté | Agence |
|------|--------|-----|--------|
| SO2605-56363 | NOUTCHOGOUI TASSE HUBERT | 20 000 | BELGO-NDJELENG |
| SO2606-59744 | Kenne Manfouo Idrice | 1 200 | BELGO-FAMLA |
| SO2605-57754 | KOAGNE ALAIN | 4 200 | BELGO-NDJELENG |
| SO2606-59060 | Biepip Ngoufo Dolf Brice | 2 100 | BELGO-NDJELENG |

#### 15/07 (Ouest)

| Réf. | Client | Qté | Agence |
|------|--------|-----|--------|
| SO2605-56364 | NOUTCHOGOUI TASSE HUBERT | 20 000 | BELGO-NDJELENG |

#### 16/07 (Ouest, Centre)

| Réf. | Client | Qté | Agence |
|------|--------|-----|--------|
| SO2605-56687 | Kenne Manfouo Idrice | 17 000 | BELGO-NDJELENG |
| SO2606-59142 | FERME MODERNE DU SUD | 500 | BELGO-MESSASSI |
| SO2606-58791 | FERME MODERNE DU SUD | 7 000 | BELGO-MESSASSI |
| SO2606-59141 | NOVEACAM (FOCHUE YEMZEU JEAN-CLAUDE) | 4 000 | BELGO AHALA |
| SO2605-56364 | NOUTCHOGOUI TASSE HUBERT | 10 000 | BELGO-NDJELENG |

### ⚠️ En attente

- **Extractions ERP** : nouveaux fichiers AT + EXP nécessaires pour refléter les livraisons du 03/07
- **Exclusions** : §12 à nettoyer après réception des nouveaux extraits (commandes livrées le 03/07 à retirer)
- **NON ÉCHUE** : 115 commandes, 928 350 sujets — Phase 3 désactivée (v20)

---

## ✅ Prêt

- **§1** : 3 dates (14, 15, 16/07) — 86 450 réel / 82 100 marge
- **§4** : Date de référence = 15/07/2026
- **§6** : Verrouillage Ouest / Ouest / Ouest+Centre
- **§10** : 3 NO_SPLIT (SO2602-47700, SO2602-46922, SO2606-59033)
- **§12** : 22 exclusions manuelles (à nettoyer après nouveaux extraits)
- **§14** : 5 forcées 14/07 + 1 forcée 15/07 + 5 forcées 16/07
- **§15** : 1 inclusion spéciale (SO2602-47515)

---

## ⏭️ Prochaines Étapes

1. **Récupérer les nouveaux extraits** ERP (AT + EXP) post-03/07
2. **Nettoyer §12** : retirer les commandes livrées le 03/07
3. **Lancer** `plan_livraisons.py` sur la config v24
4. Réactiver la Phase 3 (NON ÉCHUE) si besoin — 928 350 sujets en attente
