# 🐣 Plan de Livraisons BELGO — Suivi d'Avancement

> Dernière mise à jour : **04/09/2026** — v40 : Nouvelles extractions AT(29)+EXP(9). Statuts ERP mis à jour : §14 03/09 −2 livrées (KAMTA, Kamgang), §12 −4 livrées ERP. Plan non régénéré (sur demande).

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

## 📊 Fichiers Source (v40)

| Fichier | Rôle | Lignes |
|---------|------|--------|
| `NJS GROUP ERP - Lignes de commandes + multicompany (29).xlsx` | AT — 04/09 | 1 406 |
| `NJS GROUP ERP - Lignes des expeditions + multicompany (9).xlsx` | EXP — 04/09 | 1 252 |

> ✅ **Extractions à jour** (04/09/2026) — statuts ERP mis à jour dans le `.md` (v40).

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
