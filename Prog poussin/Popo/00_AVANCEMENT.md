# 🐣 Plan de Livraisons BELGO — Suivi d'Avancement

> Dernière mise à jour : **30/09/2026** — v82 : 29/09 restauré à l'ancien plan — Kemajou Dorette 60066 (1 500) remise au 29/09 (§14), 51281 retirée du 29/09 (§13), 01/10 verrouillé (51281 part 1 000 + 51756 2 100 forcées). Plan : 106 000/106 000 (100%) — 29/09 = **38 300** (38 500 de l'ancien plan − 200 COQ), 01/10 = 37 500, 02/10 = 30 200. 439 exclusions, 243 non planifiées. 52840 MEMGBA reste non planifiée pour le moment (décision 30/09, §13).

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

## 📊 Fichiers Source (v68)

| Fichier | Rôle | Lignes |
|---------|------|--------|
| `NJS GROUP ERP - Lignes de commandes + multicompany (46).xlsx` | AT — 26/09 | 1 565 |
| `NJS GROUP ERP - Lignes des expeditions + multicompany (13).xlsx` | EXP — 26/09 | 1 424 |

> ✅ **Extractions à jour** (26/09/2026 12:22) — statuts ERP mis à jour dans le `.md` (v68) et plan régénéré.
> ⚠ Date modif. max des extraits = 26/09 10:00 (données fraîches, pas de fichier figé — vérifié avant lancement).
> 📄 `output/Plan_Livraisons_BELGO_Ponte.xlsx` généré le 27/09 (v69) : 29/09 = 37 350/38 000 (98%, Centre 29 450 + Littoral minime 7 900) ; 01/10 = 38 000/38 000 (100%, Nord 21 300 + Centre 16 700).

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

### 🔄 Chronologie v77 (28/09)

1. **SOFAB PROVENDERIE SO2604-52011 (4 400) forcée au 01/10 en totalité** (§14) — ex-split 3 700 (29/09) + 700 (non planifié)
2. **GIC JEPRO SO2605-55433 (6 500) forcée au 29/09 en totalité** (§14) — ex-split 2 700 (29/09) + 3 800 (01/10)
3. **Reste sans changement** (demande utilisateur)
4. **Exécution (v77)** : **76 700/76 000 (101%)** — 29/09 = 38 500 (+500 toléré ≤500 : 60066 placée en entier), 01/10 = 38 200 (+200 toléré ≤500 : 51756 placée en entier). **439 exclusions**, **249 non planifiées**. 52840 MEMGBA (5 300) reste non planifiée

---

### 🔄 Chronologie v82 (29/09)

1. **Restauration du 29/09 à l'ancien plan** (demande utilisateur : « dans l'ancien plan nous n'avions pas SO2604-51281 le 29 mais plutôt la cliente Kemajou Dorette avec 1500 et le total nous donnais 38500 (vu que tu avais mis la commande de 200 coqs de Marshal Farm) ») : **SO2606-60066 (Kemajou Dorette, 1 500) remise au 29/09** (§14, forcée en totalité — elle était déjà au 29/09 dans l'ancien plan, jamais demandée sur le 01/10) et **SO2604-51281 retirée du 29/09** (§13, date exclue — sa part de 1 200 quitte le jour)
2. **01/10 verrouillé à l'état approuvé** : 51281 part 1 000 + 51756 PIEBJOU MICHEL 2 100 forcées (§14) — sans cela l'algo déversait le reliquat de 51281 (1 200) sur le 01/10 en compressant 51756 (1 400 + 700)
3. **Exécution (v82)** : **106 000/106 000 (100%)** — 29/09 = **38 300** (54941 5 800 + 63625 10 000 + 55433 6 500 + 57737 1 000 + 58836 8 500 + 62671 5 000 + 60066 1 500 — l'ancien 38 500 moins les 200 COQ partis au plan COQ en v80, +300 toléré ≤500), 01/10 = 37 500 inchangé, 02/10 = 30 200 inchangé
4. **Diff vérifié** : Plan Réel — 29/09 = seul changement (+60066 1 500 / −51281 1 200), 01/10 et 02/10 **identiques** au plan approuvé ; COQ et exclues inchangés ; la Marge (projection 95 %) se recompose mais conserve ses totaux (36 100 / 35 100 / 30 200). **439 exclusions**, **243 non planifiées**
5. **Décision (30/09)** : SO2604-52840 (MEMGBA MESSI ALBERTINE FLEUR, 5 300, MESSASSI) **reste non planifiée pour le moment** (demande utilisateur) — exclue des 3 dates du cycle (§13), à replacer sur un futur cycle. Plan inchangé (elle était déjà non planifiée) → pas de nouvelle exécution

---

### 🔄 Chronologie v81 (29/09)

1. **01/10 : SO2606-60066 (Kemajou Dorette, 1 500, Centre) et SO2609-70124 (SOFAB PROVENDERIE, 2 150, Centre) retirées** (demande utilisateur) → §13 date exclue 01/10 → non planifiées (29/09 et 02/10 déjà pleins)
2. **GIC MOS SO2609-69619 (3 500, PONTE PREMIUM, MESSASSI/Centre, Payée) forcée au 01/10 en totalité** (§14) — ex-non planifiée (Validée, prévue au 03/02/2027)
3. **Exécution (v81)** : **105 700/106 000 (100%)** — 29/09 = 38 000 plein, 01/10 = 37 500 (manque 500 : les candidates Centre restantes dépassaient la place libre), 02/10 = 30 200 (+200 toléré). **439 exclusions**, **244 non planifiées**
4. **Diff v80→v81 vérifié** (remarque utilisateur sur les dérives) : Plan Réel 29/09 et 02/10 **inchangés**, 01/10 = swap seul ✓ ; la Marge 01/10 a en plus évincé 51281 (2 200) + 51756 (2 100) — mécanique de la projection 95 % (60066/70124 n'y étaient pas planifiées), laissée telle quelle sur validation utilisateur

---

### 🔄 Chronologie v80 (29/09)

1. **Différenciation PONTE/COQ** (demande utilisateur : « le MARSHAL 200 du 29/09 est du COQ ») : correctif script — l'agrégation des réf. multi-lignes (v76) se fait désormais **par (réf., PONTE/COQ)** au lieu de tout fusionner en PONTE
2. **Résultat** : **SO2605-54941 = 18 000 PONTE + 200 COQ séparés** — les 200 (POUSSIN COQ VACCINE) partent au **plan COQ du 29/09** (même jour que la 1ʳᵉ livraison PONTE du client), plus dans le plan PONTE ; **SO2605-56506 = 1 000 PONTE + 300 COQ** — COQ non planifié (règle « client a du PONTE mais non planifié », PONTE Ouest IMMINENTE non planifiée aussi)
3. **Exécution (v80)** : **105 850/106 000 (100%)** — 29/09 = 38 000 plein (sans les 200 COQ), 01/10 = 37 650 (manque 350, recomposition), 02/10 = 30 200 (+200 toléré, inchangé : MARSHAL 12 200 + 57744 + 58801). COQ : 15 commandes 3 800 sujets (1 750 planifiés). **439 exclusions**, **243 non planifiées**

---

### 🔄 Chronologie v79 (28/09)

1. **02/10 réservé à 3 commandes** (demande utilisateur : « 57744 et 58801 à la place de toutes les autres commandes en dehors de MARSHAL ») : **SO2605-57744** (Kenne Manfouo Idrice, 16 000, NDJELENG — ex-non planifiée) et **SO2606-58801** (DJIDJOU ETIENNE ARLEX, 2 000, FAMLA — ex-non planifiée) **forcées au 02/10 (§14)**
2. **Total forcé 02/10 = 30 200** (MARSHAL 12 200 + 16 000 + 2 000) — jour plein, plus aucune place : les 18 000 Ouest ajoutés par l'algo en v78 sont évincés → non planifiées
3. **Exécution (v79)** : **106 700/106 000 (101%)** — 29/09 = 38 500 (+500 toléré ≤500 : reliquat MARSHAL 200 remonté du 01/10 + 60066 1 500), 01/10 = 38 000 plein (MEMGBA 52840 partiellement replacée : split 2 800/5 300), 02/10 = 30 200 (+200 toléré — **Marge 30 200/28 500, dépassement forcé +1 700 assumé**). **439 exclusions**, **243 non planifiées**

---

### 🔄 Chronologie v78 (28/09)

1. **Nouvelle éclosion 02/10 (Vendredi, Littoral + Ouest — 30 000 réel / 28 500 marge)** : §1/§6 mis à jour, §6 verrouille 02/10 sur Littoral+Ouest (demande utilisateur : « 30000 pour littoral et ouest »)
2. **Reliquat MARSHAL FARMERS SO2605-54941 (12 200) forcé au 02/10** (§14) — seul Littoral du jour
3. **Remplacements du 01/10** (demande utilisateur) : SO2604-51270 (3 000) + SO2606-59829 (5 600) + SO2605-55637 (2 500) + SO2606-61428 (1 100) = **12 200 forcés au 01/10** (§14) — exactement la qté libérée par MARSHAL
4. **§13 étendu au 02/10** pour les Littoral (69839, 69890, 69666, 69647, 66549, 66550, 66552, 66553 — sinon elles fuyaient sur la nouvelle éclosion via l'Étape 0b) ; 57737 (MAGDALENE) exclue du 02/10 seul
5. **Correctif script + §18 exception (v78)** : une commande forcée §14 passe malgré État/StatutFacture = Brouillon (55637 était filtrée par l'auto-exclusion)
6. **Exécution (v78)** : **106 050/106 000 (100%)** — 29/09 = 38 000 plein, 01/10 = 37 850 (manque 150), 02/10 = 30 200 (+200 toléré ≤500). **439 exclusions**, **238 non planifiées**. MARSHAL = 5 800 (29/09) + 12 200 (02/10)

---

### 🔄 Chronologie v76 (28/09)

1. **Restructuration 29/09–01/10** (demande utilisateur) : ① 69666 (5 300) + 69647 (500) retirées → §13, remplacées par **MARSHAL FARMERS SO2605-54941 en split forcé §14 : 5 800 le 29/09 (mêmes qtés) + 12 200 le 01/10** (retirée de §13) ; ② 61870 (4 650) + 61869 (1 500) retirées → §13, remplacées par **SO2607-63625 (10 000) en totalité, forcée au 29/09** ; ③ **TEULONG SO2606-61062 (3 300) forcée au 01/10** ; ④ 01/10 réservé Nord : **seule 65229 (5 200) gardée, forcée §14** — les 6 autres Nord (69211, 69158, 69314, 69306, 69312, 69316) → §13
2. **Correctifs script** : ① agrégation des réf. multi-lignes (une commande = une réf. — 54941 = 18 000 + 200 → 18 200 ; `remaining_qty` ne gardait que la dernière ligne, le split forcé aurait cassé) ; ② Littoral non compté comme région effective sur date verrouillée (extension v28 — sinon les 12 200 Littoral du 01/10 bloquaient l'ajout Nord+Centre, 3 régions effectives > 2)
3. **Exécution (v76)** : **76 000/76 000 (100%)** — 29/09 = 38 000 plein (MARSHAL 6 000 dont reliquat 200, 63625 10 000, 57737 1 000, Centre : 55433 2 700 split + 51282 5 800 + 51281 2 200 + 51270 3 000 + 51756 2 100 + 60066 1 500 + 52011 3 700), 01/10 = 38 000 plein (MARSHAL 12 200, 61062 3 300, 65229 5 200, Centre : 58836 8 500 + 62671 5 000 + 55433 3 800). **439 exclusions**, **247 non planifiées**. Évincées par les forcées : **52840 MEMGBA (5 300)** et 700 de 52011 SOFAB → non planifiées

---

### 🔄 Chronologie v75 (28/09)

1. **SO2607-62419 à programmer à partir du 20/10** (demande utilisateur) : WETE MANGA WILLIAM (BELGO-BERI, Littoral, 1 100, échue 18/09) retirée du 29/09
2. **Nouveau mécanisme MIN_DATES** (§13, sous-table « Commandes à ne pas programmer avant une date ») — contrainte durable indépendante du cycle : parser `min_dates` (md_config) + contrôles dans `try_schedule_order`, Étape 0b (pré-planification Littoral), vérification Phase 2 et équité dynamique v20. **La sous-table doit survivre aux nettoyages de §13** (elle ne dépend pas des dates du cycle)
3. **Exécution (v75)** : 29/09 = 38 450/38 000 (101%, +450 toléré ≤500 — SO2604-51281 2 200 placée avec dépassement 450 ; les 1 100 libérés + 650 du trou v74 recomblés), 01/10 = 38 000 (100%). **439 exclusions**, **238 non planifiées** (62419 incluse ✓)

---

### 🔄 Chronologie v74 (28/09)

1. **SO2605-55433 traitée comme ÉCHUE pure** (demande utilisateur) : nouveau mécanisme config-driven — sous-section **§4 « Commandes traitées comme ÉCHUE pure (non reclassées) »** (tableau de réf.) → `force_echue_pure` parsé par `md_config.py` → surcharge de la détection « reclassée » dans `plan_livraisons.py` (classification initiale + priorité dynamique v20)
2. **Résultat** : Gic/Jepro-Agro (Centre, 6 500, prévue 15/07) reclassée ÉCHUE pure (priorité 1) et **planifiée au 29/09** — elle était avant #99 de la file (derrière 98 ÉCHUE) en ÉCHUE RECLASSÉE
3. **Exécution (v74)** : 29/09 = 37 350/38 000 (98%) — manque 650 non comblable (seules des ÉCHUE Ouest/Nord ≤1 000 restaient, bloquées par le verrouillage Centre du 29/09) ; 01/10 = 38 000 (100%). **439 exclusions**, **237 non planifiées**. Correctif bug : paramètre `order_ref` dans `get_dynamic_priority` (le paramètre `ref` était écrasé par la date de référence)

---

### 🔄 Chronologie v72 (28/09)

1. **MIAKAUG EPSE SODEA DIANE (Nord, NDERE) sortie du cycle** (demande utilisateur) : les 4 commandes §13 des deux dates — SO2608-66549 (1 200), SO2608-66550 (1 000), SO2608-66552 (1 400), SO2608-66553 (1 800) = **5 400** → « Commandes non planifiées », **à intégrer dans un programme à partir de la semaine prochaine**
2. **Exécution (v72)** : 29/09 = 38 000 (100%), 01/10 = 38 000 (100%) — les 5 400 libérés recomblés par l'algo, le dépassement +450 (MEMGBA 5 300) est résorbé. **439 exclusions**, **237 non planifiées** (234 + 4 MIAKAUG − 1 remontée dans le plan). Surbrillance multi-cmd : TAKAMTSING ×3 (29/09), SCOOP EXCELLENCE ×2 + COGESDI ×2 (01/10)

---

### 🔄 Chronologie v71 (28/09)

1. **Surbrillance CLIENT MULTI-CMD** (demande utilisateur) : un même client (Tiers) à livrer avec **plusieurs commandes dans la même éclosion** → lignes colorées en **orange FCE4D6** dans Plan Réel, Plan Marge et Plan Livraisons COQ, avec entrée de légende dédiée (détection par date de production, pas en cumul sur le cycle)
2. Règle 5 des contraintes (bas de feuille) mise à jour : « Clients TEDONGMO YEMDJI FRANCK **et COMPTE TEMPORAIRE** exclus »
3. **Vérification** : 11 lignes colorées — TAKAMTSING PROSPER ×3 (29/09), MIAKAUG EPSE SODEA DIANE ×4 + SCOOP EXCELLENCE PLUS ×2 + COGESDI SARL ×2 (01/10) ✓ ; COQ : aucune (1 seule commande COQ au 29/09) ; plan inchangé (76 450/76 000, 439 exclusions, 234 non planifiées)

---

### 🔄 Chronologie v70 (28/09)

1. **Règle utilisateur : client COMPTE TEMPORAIRE à ne JAMAIS programmer** — appliquée à 3 niveaux : §16 (client exclu), `CLIENT_EXCLU` du script passé en tuple `('TEDONGMO YEMDJI FRANCK', 'COMPTE TEMPORAIRE')`, §12 +1 (SO2606-60929, 700 — ex-planifiée au 29/09) et SO2606-61347 (50) raison mise à jour
2. **Exécution (v70)** : COMPTE TEMPORAIRE vérifié absent du plan ✓ — le 700 libéré recomblé (29/09 = 38 000 plein, Centre 30 100) ; 01/10 = 38 450 (101%, +450 toléré ≤ 500 : MEMGBA 3 500 → 5 300, SANDJONG splité 850/…). **439 exclusions (+1)**, 234 non planifiées

---

### 🔄 Chronologie v69 (27/09)

1. **Nouveau cycle 29/09 + 01/10** (§1) : 29/09 (Mardi, Centre — 38 000 réel / 36 100 marge) et 01/10 (Jeudi, Nord + Centre — 38 000 réel / 36 100 marge) ; 23/09 et 25/09 retirées. §4 réf = 29/09. §6 : 29/09 verrouillée Centre, 01/10 Nord + Centre
2. **§13 vidé** (exclusions 25/09 passées — précédent v55) : OTANG, ALFRED FON JA-AI, WAYAP 59891, MAGDALENE, WETE MANGA, PENKA redeviennent éligibles → les 4 premières planifiées le 29/09
3. **29/09 Centre prioritaire (choix utilisateur)** : Étape 0b avait réservé le 29/09 au Littoral (33 200 échues = 87%) → MARSHAL FARMERS 18 000 + NGNIMPEYE 4 200 + TCHANTCHOU 3 100 **exclues du cycle (§13)** — Littoral 29/09 limité au minime 7 900 (22%) ✓ (sans exclusion des deux dates, elles se déversaient sur le 01/10 à 66% du jour)
4. **Exécution (v69)** : 29/09 = 37 350/38 000 (98% — Centre 29 450 + Littoral 7 900, manque 650) ; 01/10 = 38 000/38 000 (100% — Nord 21 300 + Centre 16 700). 438 exclusions (inchangé), **244 non planifiées** — les 3 Littoral exclues vérifiées dans « Commandes non planifiées » ✓

---

### 🔄 Chronologie v68 (26/09)

1. **Nouveaux extraits AT(46) + EXP(13) du 26/09/2026** (12:22 — Date modif. max 26/09 10:00, données fraîches) — §19 mis à jour
2. **§14 23/09 vidé** : LEMOKEM 2 000/2 000 ✓ (SH2609-1744), TAJOUO 12 000/12 000 ✓ (SH2609-5320) ; **GIC MOS 69619 NON livrée** (0/3 500, Validée, prévue désormais au 03/02/2027) → repasse en non planifiée (à repositionner sur un futur cycle)
3. **§14 25/09 vidé 8/8 livrées** : NGOUADJEU 3 300, KAMGANG 5 800, BIEPIP 250 (7 800/7 800), TESEHKOUE 10 150, ALEMAWO 4 000, TUMENTA 2 000, LEMNYUY 1 000, WAYAP 2 700 — **cycle 23/09–25/09 exécuté (10/11 forcées livrées)**
4. **§13 −1** : DJUISSI SO2609-68591 livrée (1 000/1 000, SH2609-5217 Traitée) → retirée (auto-exclusion État=Livrée). Les 6 autres restent (MAGDALENE, WAYAP 59891, WETE MANGA, PENKA 550, OTANG, Alfred Fon) — à reconsidérer au prochain cycle (dates exclues 25/09 passées)
5. **§12 inchangé** : aucune exclusion devenue Livrée dans l'ERP
6. **Exécution (v68)** : plan régénéré sur les dates du cycle (passées) — 23/09 = 15 000/15 000, 25/09 = 29 000/29 000 (échues Littoral+Ouest) ; **438 exclusions (+13)**, 250 non planifiées (marge) — GIC MOS vérifiée dans « Commandes non planifiées » ✓
7. ⏭️ **Prochain cycle à définir** (§1/§4) — les éclosions 23/09 et 25/09 sont passées

---

### 🔄 Chronologie v67 (25/09)

1. **SO2601-42302 METAFE GNITEYO SONYA MIGLANCHE** (38 000, BELGO-BERI, PONTE PREMIUM) **ajoutée à §12** — déjà livrée, livraison confirmée hors ERP (reste 38 000 dans l'ERP)
2. **Exécution (v67)** : plan inchangé (23/09 = 17 500, 25/09 = 29 200) ; **425 exclusions (+1)**, 246 non planifiées
3. ⚠ Note : la commande était déjà hors des pools du plan (StatutFacture=Brouillon dans l'ERP — filtrée par le script) — l'exclusion la documente et la protège si le statut facture passe à Validée

---

### 🔄 Chronologie v66 (24–25/09)

1. **§12 −3 commandes remises en non planifiées** : SO2606-61062 TEULONG (reste 3 300), SO2606-58836 TSAFACK (8 500, 0 livré), SO2607-62671 BOGNING (5 000, 0 livré) — toutes MESSASSI (Centre), ÉCHUE, En cours
2. **Exécution (v66)** : 23/09 = 17 500/15 000 (117%) ; 25/09 = 29 200/29 000 (101%) — inchangés ; **424 exclusions (−3), 246 non planifiées (+3)** — les 3 commandes vérifiées dans la feuille « Commandes non planifiées » ✓

---

### 🔄 Chronologie v65 (24/09)

1. **BIEPIP SO2606-60194 reliquat 250** (PONTE PREMIUM, 7 550/7 800 livrés dans l'ERP — AT(44)) basculé du 23/09 au 25/09 dans §14
2. **§14 23/09** : 17 500 (3 forcées — LEMOKEM 2 000, TAJOUO 12 000, GIC MOS 3 500)
3. **§14 25/09** : +BIEPIP 250 → **8 forcées, 29 200 (100,7%, +200)** — Ouest : KAMGANG 5 800, BIEPIP 250, TESEHKOUE 10 150, TUMENTA 2 000, LEMNYUY 1 000, WAYAP 2 700 ; Littoral : NGOUADJEU 3 300 + ALEMAWO 4 000
4. **Exécution (v65)** : 23/09 = 17 500/15 000 (117%) ; 25/09 = **29 200/29 000 (101%)** — forcées uniquement, 0 ajoutée par l'algo ; 427 exclusions ; 243 non planifiées (marge)

---

### 🔄 Chronologie v63 (23/09)

1. **25/09 — 5 retirées (§13)** : WAYAP SO2606-59891 (2 200, forcée — retirée de §14 + exclue), MAGDALENE SO2605-57737 1 000, WETE MANGA SO2607-62419 1 100, PENKA SO2607-62511 550 (reliquat), DJUISSI SO2609-68591 1 000 — toutes repassent en non planifiées (vérifié dans le plan)
2. **25/09 — remplacées par 3 forcées (§14)** : TUMENTA GRACE SO2604-53701 2 000 (prévue 04/09, ÉCHUE), LEMNYUY BETILLA SO2606-59760 1 000 (prévue 23/09, ÉCHUE), WAYAP SO2609-69790 2 700 (prévue 25/09, IMMINENTE) — toutes **BELGO MBOUDA (Ouest)**, Payées, 0 livré — total forcé 25/09 : **28 950 (99,8%)**
3. **Exécution (v64)** : 23/09 = 17 750/15 000 (118%) ; 25/09 = **28 950/29 000 (100%, Littoral+Ouest)** — les 7 forcées uniquement, 0 ajoutée par l'algo ; 427 exclusions ; 243 non planifiées (marge)

---

### 🔄 Chronologie v61 (23/09)

1. **25/09 — OTANG + Alfred Fon retirées (§13)** : SO2609-69647 OTANG VALENTINE (500) et SO2609-69666 Alfred Fon Ja-Ai (5 300) — BELGO-BUEA, Littoral — exclues du 25/09, repassent en non planifiées (vérifié dans le plan)
2. **25/09 — remplacées par 2 forcées (§14)** : ALEMAWO SO2607-61638 4 000 (BERI, Littoral — prévue 23/09, Payée) + WAYAP SO2606-59891 2 200 (FAMLA, Ouest — prévue 04/08, Payée) — total forcé 25/09 : **25 450 (88%)**
3. **Correctif `md_config.py`** : numérotation §21 calculée sur le **max** des versions (plus de doublon) + nouvelle entrée insérée **en tête** de l'historique
4. **Exécution (v62)** : 23/09 = 17 750/15 000 (118%) ; 25/09 = **29 100/29 000 (100%, Littoral+Ouest)** — 5 forcées + MAGDALENE 1 000, WETE MANGA 1 100 (BERI) + PENKA 550, DJUISSI 1 000 (FAMLA) ; 427 exclusions ; 242 non planifiées (marge)

---

### 🔄 Chronologie v59 (23/09)

1. **Nouvelle éclosion 25/09/2026** (Vendredi, Ouest — 29 000 réel / 27 550 marge) : §1/§6 mis à jour, **23/09 conservée** dans le cycle (sur demande)
2. **§14 25/09 — 3 forcées (19 250, 66%)** : NGOUADJEU SO2605-56216 3 300 (NKONGSAMBA — Littoral minime 11,4% ≤ 25%), KAMGANG SO2606-58404 5 800 (NDJELENG), TESEHKOUE SO2606-61310 10 150 (FAMLA) — toutes Payées, 0 livré, ÉCHUE (prévues 04/09, 12/09, 08/07)
3. **Étape 0b — Littoral échue 7 900** pré-planifiées le 25/09 (MAGDALENE KUKU 1 000, WETE MANGA 1 100, OTANG 500, Alfred Fon Ja-Ai 5 300 — BERI/BUEA) : **gardées sur validation** (journée dédiée Littoral §5, Littoral total 11 200 = 38% du jour)
4. ⚠ **AT(35) re-téléchargé le 21/09 15:38** (mtime le plus récent du dossier) mais **toujours figé au 09/09** → déplacé vers `extractions/archive/` pour que le script reprenne AT(44) par mtime
5. **Exécution (v60)** : 23/09 = 17 750/15 000 (118%) ; 25/09 = **29 500/29 000 (102%, Littoral+Ouest)** — 3 forcées + 7 900 Littoral échue + 2 350 Ouest ≤1000 ; 427 exclusions ; 242 non planifiées (marge)

---

### 🔄 Chronologie v57 (21/09)

1. **TAJOUO SO2606-60657 passée à 12 000/12 000 en totalité** dans §14 (ex-10 000/12 000) — dépassement d'éclosion assumé : **17 750/15 000 (118%, +2 750)**
2. **Exécution (v57)** : 23/09 = **17 750/15 000** — 4 forcées (LEMOKEM 2 000, TAJOUO 12 000, BIEPIP 250, GIC MOS 3 500), aucune commande ajoutée par l'algo (capacité dépassée) ; ⚠ DÉPASSEMENT +2 750 (réel) / +3 500 (marge)

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
