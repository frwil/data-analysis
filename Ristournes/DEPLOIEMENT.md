# Déploiement de l'application chèques sur AlwaysData

Procédure pas à pas pour exécuter `cheques/` sur un hébergement **AlwaysData**
(mutualisé ou VPS). L'application est portable (PHP 8 + SQLite + sodium, chemins
relatifs `__DIR__`) : rien à réécrire, uniquement de la configuration.

> ⚠️ **Décision métier avant tout** : les chèques et listings contiennent des
> données clients (noms, montants, agences). Ne mettre l'application en ligne
> que si ces données peuvent sortir du réseau de l'entreprise.

---

## 1. Créer le site (panneau admin.alwaysdata.com)

1. **Web → Sites → Ajouter un site** : type **PHP**, adresse choisie
   (`votre.domaine.cm` ou le sous-domaine gratuit `compte.alwaysdata.net`),
   répertoire par défaut (ex. `/www`).
2. Sur le site créé : **Version PHP** → choisir **8.2 ou 8.3** (sodium et
   mbstring sont actifs par défaut).
3. **SSL** → activer le certificat **Let's Encrypt** (auto-renouvelé). Le
   cookie de session passe automatiquement en `secure` grâce à la détection
   de `$_SERVER['HTTPS']` dans `inc/auth.php`.
4. L'accès SSH/SFTP est ouvert sur tous les plans : hôte
   `ssh-compte.alwaysdata.net`, dossier de base `/home/compte/` (le docroot
   du site est `/home/compte/www/` pour le répertoire `/www`).

## 2. Déployer uniquement `cheques/` (jamais tout le dépôt)

Envoyer le **contenu** de `cheques/` dans le docroot, par SFTP (WinSCP,
FileZilla) ou `scp` depuis Git Bash :

```bash
scp -r cheques/* compte@ssh-compte.alwaysdata.net:www/
```

Contenu attendu : `index.php`, `router.php` (inutile sur Apache mais
inoffensif), `verif.html`, `assets/`, `inc/`, `data/`, `_gen_verif.php`,
`_test_signature.php` (gardes CLI : inaccessibles en HTTP).

**Fichiers `data/` à envoyer par SSH uniquement** (jamais par e-mail ni par
GitHub) : `ristournes.sqlite` (données clients), `qr.sqlite` (uuids),
`suivi.sqlite` (compteurs d'impression), `users.sqlite` (comptes et rôles),
`sign.key` (**clé privée Ed25519** — sa perte ou sa fuite casserait ou
permettrait de falsifier la vérification des documents déjà imprimés).

## 3. Protéger le serveur (.htaccess — Apache 2.4, activé par défaut)

Créer **`www/.htaccess`** :

```apache
DirectoryIndex index.php
```

Créer **`www/data/.htaccess`** et **`www/inc/.htaccess`** :

```apache
Require all denied
```

→ les `.sqlite`, `sign.key` et les sources PHP de `inc/` renvoient 403 ;
`assets/` et `verif.html` (page publique anti-fraude, par conception)
restent accessibles.

## 4. Comptes utilisateurs (users.sqlite)

Deux options, au choix :

- **A (recommandée, la plus simple)** : envoyer la `data/users.sqlite` locale
  (les comptes et leurs mots de passe y sont déjà). Le seed par variables
  d'environnement ne se déclenchera pas puisque la base existe.
- **B (nouvelle installation)** : ne pas envoyer `users.sqlite`, définir les
  variables d'environnement **`BCP_ADMIN_MDP`** et **`BCP_VERIF_MDP`** dans le
  panneau (Web → Sites → *le site* → **Environnement**), puis ouvrir la page
  de connexion : les comptes `admin` et `GroupeNJS26` sont créés au premier
  accès avec ces mots de passe. Sans ces variables, aucun compte n'est créé
  (la page de login l'indique).

Changer les mots de passe initiaux après la première connexion (menu
« Mot de passe »).

## 5. Génération PDF — le seul point qui dépend du plan

`trouver_navigateur()` cherche Edge/Chrome (Windows) puis Chromium
(Linux). Deux cas :

- **Mutualisé** : aucun navigateur n'est installé et on ne peut pas en
  installer → le bouton « Télécharger PDF » affiche proprement
  « Navigateur introuvable… ». Tout le reste fonctionne, et les utilisateurs
  impriment via **Aperçu puis Ctrl+P → Enregistrer au format PDF**
  (rendu A4 identique, QR compris).
- **VPS AlwaysData** : se connecter en SSH et installer Chromium :
  `sudo apt update && sudo apt install -y chromium` → le bouton PDF
  fonctionne (`/usr/bin/chromium` est détecté). Penser à augmenter
  `max_execution_time` PHP à ≥ 180 s (Panneau → site → PHP).

## 6. Page de vérification des documents (verif.html)

`verif.html` est servie telle quelle par le site : elle est donc en ligne à
`https://votre.domaine/verif.html`. Renseigner alors dans `inc/config.php` :

```php
'qr_verif_url' => 'https://votre.domaine/verif.html#',   // doit se terminer par #
```

puis ré-envoyer `inc/config.php` en SFTP. ⚠️ Les documents **déjà imprimés**
gardent l'URL gravée dans leur QR au moment de l'impression ; ce réglage ne
vaut que pour les nouveaux documents.

## 7. Mise à jour des données (ristournes.sqlite)

La base se reconstruit **en local** (`python _build_cheques_db.py` après
`restitution_finale.py`), puis :

```bash
scp ristournes.sqlite compte@ssh-compte.alwaysdata.net:www/data/
```

(`qr.sqlite` et `suivi.sqlite` ne se remplacent jamais : uuids et compteurs
doivent survivre aux reconstructions.)

## 8. Vérifications après déploiement

- `https://votre.domaine/` → page de connexion (302 si pas connecté).
- Connexion admin puis GroupeNJS26 → bonnes pages, navbar filtrée.
- `https://votre.domaine/data/users.sqlite` → **403**.
- Bouton PDF → PDF correct (VPS) ou message propre (mutualisé).

## 9. Sauvegardes

- Panneau AlwaysData → **Sauvegardes** : activer la sauvegarde automatique du
  site (fichiers + `data/`).
- Minimum vital à préserver : `data/sign.key` (irremplaçable) et
  `data/*.sqlite`. Sans `sign.key`, tous les documents déjà imprimés ne
  peuvent plus être vérifiés ; une clé régénérée les invaliderait.

## Rappels de sécurité

- Ne jamais faire transiter `data/` (surtout `sign.key`) par le dépôt Git
  public ni par e-mail — uniquement SSH/SFTP.
- Le dépôt GitHub ne sert pas de canal de déploiement : il contient bien plus
  que l'application et n'a pas vocation à héberger les données.
- HTTPS est obligatoire (le certificat Let's Encrypt d'AlwaysData est gratuit
  et automatique).
