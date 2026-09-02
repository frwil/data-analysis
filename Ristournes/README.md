# Ristournes & commissions — BELGOCAM S.A.

Validation indépendante du calcul des ristournes clients (procédure V6 — paliers concentrés {5, 16, 30} T,
gains par agence sans cumul, comptoirs exclus, seuil 5 000 F).

## Structure

- **Racine** : uniquement les scripts réutilisables d'un exercice à l'autre.
- **`2025/`** : toutes les données et livrables de l'exercice 2025 (extraction, Pareto officiel,
  restitutions, rapport HTML, revue ADV, doublons, procédure V6) + scripts d'analyse ponctuels archivés.
- Pour 2026 : créer un dossier `2026/` avec l'extraction (`rist_datas.xlsx`) et le fichier Pareto
  (`Rs2026_Pareto_20-80.xlsx`), puis changer `EXERCICE = '2026'` en tête de chaque script.

## Scripts (dans l'ordre d'utilisation pour un nouvel exercice)

| Script | Rôle |
|---|---|
| `_fix_nl3.py` | Construit `Commandes_non_livrees_a_verifier.xlsx` : feuille « A vérifier » en lignes uniques (pas de doublons, pas de colonne Montant HT) + résumés. À faire remplir par l'ADV. |
| `_review_nl.py` | Après la revue ADV : rebâtit les résumés selon « Nouvel état (à remplir) » sans toucher la feuille remplie. |
| `_doublons.py` | Contrôle des doublons (N0 Réf. multi-clients, N1 doublons exacts — lignes intégralement identiques, même Réf.) → `Doublons_<EXERCICE>.xlsx`. Règle : des Réf. différentes ne constituent pas des doublons. |
| `restitution_finale.py` | Calcul mois par mois (concentrés par paliers + autres produits), seuil 5 000 F → `Restitution_Ristournes_<EXERCICE>.xlsx` et `Analyse_Exploratoire_<EXERCICE>.xlsx`. |
| `_report_data.py` | Recalcule les indicateurs du rapport (reproduction officielle au franc, périmètre corrigé, anomalies) → `<EXERCICE>/_report_data.json`. |
| `_patch_report.py` | Injecte le JSON dans le bloc `var DATA` du rapport HTML `<EXERCICE>/Rapport_Audit_Ristournes_<EXERCICE>.html`. |
| `_build_cheques_db.py` | Construit la base de l'application chèques (`cheques/data/ristournes.sqlite`) : clients + détail mensuel + kg autres produits (même périmètre que `restitution_finale.py`). |

Ordre d'exécution pour 2026 :
1. `_fix_nl3.py` → revue ADV → `_review_nl.py`
2. `restitution_finale.py`
3. `_report_data.py` puis `_patch_report.py`
4. Adapter les textes du rapport HTML et les commentaires d'écarts propres à l'exercice (constantes annuelles).

## Application chèques & listings (`cheques/`)

Application PHP locale d'édition des **chèques de ristourne** et **listings d'achats et de gains**
(format A4 portrait, 2 documents par page — ½ A4 chacun, marges @page 10 × 12 mm), avec **code QR signé**
(Ed25519) identique sur les deux documents d'un même client : le QR **authentifie** le document
(bénéficiaire, agence, année, montant) et détecte toute contrefaçon ou falsification.

**Démarrage**
1. Construire la base : `python _build_cheques_db.py` (après `restitution_finale.py`).
2. Lancer le serveur : `php -S localhost:8123` depuis le dossier `cheques/`, puis ouvrir
   `http://localhost:8123`.

**Personnalisation**
- `cheques/inc/config.php` : en-tête et pied de page de l'entreprise (nom, adresse, téléphone,
  email, RC, NIU, logo, banque). Renseigner les champs marqués « … » avant impression.
- `cheques/data/codes_override.csv` (optionnel) : surcharges de codes clients
  (colonnes `Tiers;Agence;Code`), relues à chaque reconstruction de la base.
- `cheques/data/codes_fallback.csv` (généré) : clients sans code, codes provisoires `X2025-NNN` à
  remplacer par les vrais codes via `codes_override.csv`.
- `cheques/data/codes_partages.csv` (généré) : codes identiques portés par plusieurs clients dans
  la même agence (variantes d'orthographe) — à vérifier.

**Authentification des documents (anti-fraude)**
- Le QR contient une chaîne signée : `B1.<données>.<signature Ed25519>` (précédée de
  `qr_verif_url` si renseigné dans `inc/config.php` — ex. `https://belgocam.cm/verif.html#`).
  La signature couvre **bénéficiaire, agence, année, montant total et N° du document** :
  modifier un montant ou un nom sur le papier casse la vérification.
- `inc/signature.php` : signature côté émission (sodium, natif PHP ≥ 7.2). Test :
  `php _test_signature.php` (format, signature, anti-falsification). Clé privée :
  `data/sign.key` — **ne jamais la supprimer, la copier ni la partager** (non versionnée,
  voir `cheques/.gitignore`) : sa détention permet d'émettre des documents « authentiques ».
  Une clé régénérée invalide la vérification de tous les documents déjà imprimés.
- `verif.html` : page autonome de vérification (scan caméra **ou** collage du code,
  vérification faite dans le téléphone, aucune donnée envoyée). Générée par
  `php _gen_verif.php` (clé publique + libs jsQR/tweetnacl inlinées) ; à relancer si la
  clé est régénérée. À **héberger en ligne** (site, Netlify, GitHub Pages…) puis renseigner
  `qr_verif_url` dans `inc/config.php` : le scan avec l'appareil photo du téléphone ouvre
  alors directement la vérification.
- Limite connue : la signature ne détecte pas la **double présentation** du même document
  (à couvrir par les contrôles internes : 4 signatures, registres d'agence).

**Fonctionnement**
- Formulaire : période (année + mois ou toute l'année), documents (chèques et/ou listings),
  sélection (tous / un client / une liste avec filtre) → aperçu avant impression (unique ou groupé).
- Bouton « Télécharger PDF » : génère le PDF via le navigateur installé (Edge/Chrome) en mode
  headless, à partir du même HTML d'aperçu — même rendu que l'impression (A4 portrait,
  2 documents par page, QR inclus).
- Montants exprimés en **BLP** (BELGO LIVESTOCK PRODUCTS — 1 BLP = 1 FCFA) : paiement en
  produits, pas en numéraire (mention N.B. sur le chèque).
- Chèques uniquement : part **COMPLÉMENTS ALIMENTAIRES** (10 % du montant, bornée 5 000 – 50 000 BLP,
  réglable via `complements` dans `config.php`), le solde en produits (Concentrés) au libellé
  « Ristournes + Commissions sur Achat ».
- 4 niveaux de signature : Bénéficiaire (Client), Chef d'agence (CA), DCM, DG
  (libellés modifiables dans `config.php`).
- Les uuid sont persistés dans `cheques/data/qr.sqlite` par (client, agence, année) : le QR
  ne change pas quand la base est reconstruite.

## Résultat 2025 (référence)

- Reproduction du fichier officiel au franc près : 540/547 lignes, 7 écarts de ±1 F, total 91 783 812 F.
- Total conforme (procédure actualisée + revue ADV) : **544 clients, 89 264 312 F**.
- Écart net : +2 519 500 F = +2 525 000 (SPC/PDC) − 7 000 (TIWA RENE) + 1 500 (MEGAMI annulée).
