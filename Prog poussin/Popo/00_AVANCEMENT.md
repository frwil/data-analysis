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

## 📈 Dernière Exécution (01/06/2026)

| Métrique | Valeur |
|----------|--------|
| REF_DATE | 26/05/2026 |
| Commandes PONTE | 103 (571 100 sujets) |
| Commandes COQ | 7 (850 sujets) |
| Exclusions | 131 |
| **Planifié Réel** | **106 400 / 106 700** |

| Date | Région | Réel |
|------|--------|------|
| Lun 25/05 | Centre | 30 000/30 000 |
| Mar 26/05 | Littoral + Ouest | 38 400/38 700 |
| Ven 29/05 | Centre + Littoral + Ouest | 38 000/38 000 |

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
