# 🐣 Plan de Livraisons BELGO — Suivi d'Avancement

> Dernière mise à jour : **01/06/2026** — Script plan_livraisons.py opérationnel

---

## 🎯 Objet du Projet

Système de **planification de livraisons** pour l'agence **BELGO Ponte Noire** (production de poussins PONTE CLASSIQUE et PONTE PREMIUM).

**But** : Prendre les commandes client en attente dans l'ERP et les organiser en un **plan de livraison optimisé** sur les jours de production disponibles.

---

## 📚 Documents

| Fichier | Contenu |
|---------|---------|
| `Contraintes du Plan de Livraisons BELGO.md` | 19 sections de règles métier (algo v13, régions, exclusions, etc.) |
| `PLAN DE LIVRAISON SEMAINE.pdf` | Plan de référence avec mapping agence→région |
| `plan_livraisons.py` | Script principal v12 (2275 lignes) — tourne sans erreur |
| `Plan_Livraisons_BELGO_Ponte.xlsx` | Fichier généré (8 feuilles) |

---

## 📊 Fichiers Source

| Fichier | Rôle | Lignes |
|---------|------|--------|
| `16382c5d-...xlsx` | AT — Lignes de commandes | 732 |
| `bbeedece-...xlsx` | EXP — Lignes des expéditions | 407 |

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

## 📈 Dernière Exécution (02/06/2026) — v19 Exceptionnelle

| Métrique | Valeur |
|----------|--------|
| REF_DATE | 02/06/2026 |
| Commandes PONTE | 123 (781 600 sujets) |
| Commandes COQ | 11 (17 550 sujets) |
| Exclusions | 216 |
| **Planifié Réel** | **174 600 / 174 600** |
| **Planifié Marge** | **165 700 / 165 850** |

| Date | Région | Réel |
|------|--------|------|
| Jeu 04/06 | Littoral + Nord | 27 800/27 800 |
| Ven 05/06 | Centre | 35 700/35 700 |
| Mer 10/06 | Centre | 12 800/12 800 |
| Jeu 11/06 | Ouest | 35 300/35 300 |
| Lun 15/06 | Centre + Littoral | 27 100/27 100 |
| Ven 19/06 | Ouest | 35 900/35 900 |

### 🔄 Changements exceptionnels (v19)
- **5 commandes forcées sur le 04/06** : SO2605-56192, SO2603-50402, SO2603-49144, SO2604-51013, SO2605-57283
- **KUATE SO2603-47945** retiré du 04/06 → repositionné le **11/06** (Ouest) ✓
- **SO2605-57283** ajouté au NO_SPLIT (intégralité le 04/06) — 9 750/10 000 placé (manque 250, capacité saturée)
- ⚠️ Littoral conséquent sur 04/06 (40.5% > 25%) — exception acceptée

---

## 🔧 Corrections Appliquées au Script

1. ✅ Chemins fichiers : `upload/` → dossier courant
2. ✅ Ajout `sys.stdout.reconfigure(encoding='utf-8')` (crash Unicode Windows)
3. ✅ Indentation Phase 1 corrigée (était dans le bloc else de l'Étape 0b)

---

## ⏭️ Prochaines Étapes

1. Revoir les paramètres (REF_DATE, PRODUCTION_PLAN) pour le prochain cycle
2. Ajouter les nouvelles commandes à planifier
3. Ajuster les exclusions / assignations forcées si nécessaire
