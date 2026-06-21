# 🐣 Plan de Livraisons BELGO — Suivi d'Avancement

> Dernière mise à jour : **21/06/2026** — Nouveau cycle 24/06–30/06

---

## 🎯 Objet du Projet

Système de **planification de livraisons** pour l'agence **BELGO Ponte Noire** (production de poussins PONTE CLASSIQUE et PONTE PREMIUM).

**But** : Prendre les commandes client en attente dans l'ERP et les organiser en un **plan de livraison optimisé** sur les jours de production disponibles.

---

## 📚 Documents

| Fichier | Contenu |
|---------|---------|
| `Contraintes du Plan de Livraisons BELGO.md` | Config v20 — 3 dates (24/06–30/06) |
| `plan_livraisons.py` | Script principal — prêt pour le nouveau cycle |
| `md_config.py` | Parser du .md |

---

## 📊 Fichiers Source (v20)

| Fichier | Rôle | Lignes |
|---------|------|--------|
| `NJS GROUP ERP - Lignes de commandes + multicompany (5).xlsx` | AT — 21/06 | 1 221 |
| `NJS GROUP ERP - Lignes des expeditions + multicompany (3).xlsx` | EXP — 21/06 | 829 |

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

## 📈 Nouveau Cycle v20 (21/06/2026)

| Date | Jour | Réel | Marge | Région |
|------|------|------|-------|--------|
| 24/06/2026 | Mer | 38 000 | 35 500 | Ouest |
| 25/06/2026 | Jeu | 30 000 | 27 700 | Centre |
| 30/06/2026 | Mar | 30 000 | 27 450 | À définir |
| **Total** | | **98 000** | **90 650** | |

### 🔄 Changements v20

- **15 commandes livrées** retirées de la config (§10, §12, §14, §15)
- **3 exclusions « Déjà livrée »** redevenues actives : SO2601-44631, SO2604-52536, SO2601-42254
- **SO2602-46160** livré partiellement : 11 650 PONTE + 200 COQ livrés, reste 15 350 PONTE
- **Commandes non livrées conservées** : SO2605-55879 (10 000), SO2512-38407 (21 500)

### ⚠️ En attente

- **Régions principales** pour les 3 nouvelles dates (à définir)
- **REGION_LOCK** à configurer

---

## ⏭️ Prochaines Étapes

1. Définir les régions pour les 3 dates de production
2. Vérifier les commandes à inclure/exclure
3. Lancer `plan_livraisons.py`
