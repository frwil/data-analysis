# Guide Utilisateur — Plan de Livraisons BELGO Ponte

> Projet de planification des livraisons de poussins PONTE pour l'agence BELGO.

## 🎯 Principe général

Le script `plan_livraisons.py` lit les extractions ERP (commandes clients en attente) et les organise en un **plan de livraison optimisé** sur les jours d'éclosion disponibles. Toute la configuration est centralisée dans `Contraintes du Plan de Livraisons BELGO.md` (le « .md »).

**Règle d'or** : On modifie le `.md`, pas le script. Le script est le moteur, le `.md` est le volant.

---

## 🗂️ Fichiers du projet

| Fichier | Rôle |
|---------|------|
| `Contraintes du Plan de Livraisons BELGO.md` | **Configuration unique** — dates, règles, exclusions, assignations forcées |
| `plan_livraisons.py` | Moteur de planification |
| `md_config.py` | Parseur du `.md` |
| `00_AVANCEMENT.md` | Suivi d'avancement et historique |
| `extractions/` | Fichiers source ERP (AT + EXP) |
| `output/` | Fichiers générés (plan Excel) |

---

## 🚀 Commandes utilisateur

Toutes les instructions se donnent en **langage naturel**. Voici le mapping de ce que tu peux demander :

### « La commande X est déjà livrée »
→ Ajoute la commande à la liste d'exclusions (§12) avec le motif « Déjà livrée ».  
*Exemple : « la commande SO2601-44631 est déjà livrée (problème d'expédition système) »*

### « Retirer la commande X du plan »
→ Ajoute la commande à §12 avec le motif « Retirée du plan — sur demande ».  
*Exemple : « retire la commande SO2603-50721 du plan »*

### « Mettre la commande X en attente d'une prochaine programmation »
→ Ajoute la commande à §12 avec le motif « Reportée — attente prochaine programmation ».  
Ces exclusions sont **temporaires** : elles seront retirées au prochain cycle.  
*Exemple : « mets la commande SO2605-57780 en attente d'une prochaine programmation »*

### « Reporter la commande X pour la regrouper avec une prochaine commande du même client »
→ Ajoute à §12 avec mention spéciale. Noté en mémoire pour le prochain cycle.  
*Exemple : « retirer SO2603-48511 pour reprogrammation ultérieure avec une nouvelle commande du même client »*

### « Forcer la commande X à la date JJ/MM »
→ Ajoute une assignation forcée dans §14 sous la date correspondante.  
*Exemple : « force la commande SO2512-38407 au 05/06 »*

### « Insérer la commande X (non-BELGO) à la date JJ/MM »
→ Ajoute en §15 (inclusion exceptionnelle avec surcharge agence+région) + §14 (forcée).  
*Exemple : « insère SO2603-49935 le 19 »*

### « Faire un switch entre les commandes X, Y et celles du JJ/MM »
→ Déplace des commandes par assignations forcées, l'algo rééquilibre le reste.  
*Exemple : « switchons SO2605-55641 et SO2605-55799 avec des commandes du 15/06 »*

### « Mettre la commande X en livraison complète le JJ/MM »
→ Ajoute en §10 (NO_SPLIT) + §14 (forcée).  
*Exemple : « mets SO2605-55438 en livraison complète le 05/06 »*

### « Augmenter la capacité du JJ/MM à X »
→ Modifie le plan de production dans §1.  
*Exemple : « passe la capacité du 05/06 à 36 350 »*

### « Recalculer le statut d'échéance »
→ Applique la règle d'équité §4 : recalcule le statut de chaque commande par rapport à sa date de programmation effective (et non par rapport à aujourd'hui).

### « Relancer le plan »
→ Ré-exécute `plan_livraisons.py` avec la configuration actuelle.

---

## 📊 Comprendre le résultat

Après chaque exécution, le script affiche un résumé :

```
Plan Réel par date:
  Jeu 04/06: 28,050/27,800 (101%) (Littoral, Nord)
  Ven 05/06: 36,350/36,350 (100%) (Centre)
  ...
```

| Colonne | Signification |
|---------|--------------|
| `28,050/27,800` | Qté livrée / Capacité du jour |
| `(101%)` | Taux de remplissage (>100% = léger dépassement) |
| `(Littoral, Nord)` | Régions effectives ce jour-là |
| `Manque: 400` | Capacité restante non utilisée |

Le fichier Excel généré contient 8 feuilles :
1. **Plan Réel** — planification avec capacité réelle
2. **Plan Marge** — planification avec capacité marge (95%)
3. **Commandes non planifiées** — n'ont pas pu être intégrées
4. **Commandes exclues** — exclusions avec raisons
5. **Analyse Expéditions** — cross-référence commandes vs expéditions
6. **Détail Expéditions** — lignes d'expédition détaillées
7. **Livraisons Coq** — commandes COQ alignées sur PONTE
8. **Plan de Production** — récapitulatif par date

---

## 🔧 Structure du fichier de configuration (.md)

| Section | Rôle | Quand modifier |
|---------|------|---------------|
| §1 — Plan de Production | Dates, capacités, régions | Nouveau cycle, ajustement capacité |
| §4 — Recalcul Échéance | Règles de classification | Changement de règle métier |
| §5 — Contraintes Régionales | Règles Littoral, Nord/Est, etc. | Changement de règle métier |
| §6 — Verrouillage Régional | Quelles régions sont autorisées par date | Ajustement régional |
| §10 — NO_SPLIT | Commandes à livrer en intégralité | Ajout/retrait |
| §11 — TAMATIO | Regroupement client TAMATIO | Ajout/retrait |
| §12 — Exclusions | Commandes exclues du plan | Très fréquent |
| §13 — Exclusions par Date | Commandes exclues de dates spécifiques | Rare |
| §14 — Assignations Forcées | Commandes forcées à une date | Fréquent |
| §15 — Inclusions Exceptionnelles | Commandes non-BELGO à inclure | Occasionnel |

---

## ⚠️ Points d'attention

- **Ne pas modifier le script** pour un changement de config — tout passe par le `.md`
- **Fermer Excel** avant de relancer le script (sinon erreur `PermissionError`)
- **Vérifier les extractions** avant chaque cycle : les colonnes requises doivent être présentes
- **Les exclusions « Reportée »** sont automatiquement signalées pour retrait au prochain cycle
- **L'équité §4** recalcule l'échéance par rapport à la date de programmation (une commande repoussée au 19/06 n'est plus jugée par rapport à aujourd'hui)
