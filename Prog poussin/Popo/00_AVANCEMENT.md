# 🐣 Plan de Livraisons BELGO — Suivi d'Avancement

> Dernière mise à jour : **14/07/2026** — v24, nouveau cycle 14–16/07 (en attente d'extractions)

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

## 📊 Fichiers Source (v24)

| Fichier | Rôle | Lignes |
|---------|------|--------|
| `NJS GROUP ERP - Lignes de commandes + multicompany (12).xlsx` | AT — 03/07 | 1 293 |
| `NJS GROUP ERP - Lignes des expeditions + multicompany (6).xlsx` | EXP — 03/07 | 684 |

> ⚠ **Extractions non à jour** — en attente de nouveaux fichiers pour lancer le script.

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
