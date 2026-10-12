<?php
declare(strict_types=1);
/* =============================================================
 * Authentification & permissions — BELGOCAM S.A.
 * Sessions PHP + base data/users.sqlite (rôles et utilisateurs,
 * créée et seedée automatiquement au premier accès).
 *
 * Rôles modulaires : un rôle = un ensemble de permissions
 * (PERM_LABELS). Le rôle Administrateur (perms = '*') a tous les
 * droits. Les comptes par défaut sont créés au premier accès à
 * partir de variables d'environnement (jamais de mot de passe en
 * clair dans le code) :
 *   BCP_ADMIN_MDP  → compte « admin » (Administrateur)
 *   BCP_VERIF_MDP  → compte « GroupeNJS26 » (Vérification)
 * ============================================================= */

/* ---- Session ---- */
ini_set('session.use_strict_mode', '1');
$hoste = (string) ($_SERVER['HTTP_HOST'] ?? '');
$securise = ($_SERVER['HTTPS'] ?? '') === 'on' || $hoste === 'localhost';
session_set_cookie_params([
    'lifetime' => 0, 'path' => '/', 'secure' => $securise,
    'httponly' => true, 'samesite' => 'Lax',
]);
session_name('BCP_SESSION');
session_start();

/* Timeout d'inactivité : 8 heures */
if (!empty($_SESSION['uid']) && isset($_SESSION['derniere_activite'])
    && time() - (int) $_SESSION['derniere_activite'] > 8 * 3600) {
    $_SESSION = [];
}
$_SESSION['derniere_activite'] = time();

/* Libellés des permissions — partagés par l'UI des rôles et les messages 403. */
const PERM_LABELS = [
    'doc.view'        => 'Documents — consulter et générer l\'aperçu',
    'doc.create'      => 'Documents — imprimer / marquer imprimé',
    'doc.pdf'         => 'Documents — télécharger le PDF',
    'suivi.view'      => 'Suivi — consulter les compteurs',
    'suivi.edit'      => 'Suivi — corriger les compteurs (−1, réinitialiser)',
    'analyses.view'   => 'Analyses — consulter',
    'analyses.export' => 'Analyses — exporter CSV / PDF',
    'gagnants.view'   => 'Gagnants — consulter',
    'gagnants.export' => 'Gagnants — exporter PDF',
    'verif.use'       => 'Vérifier un document',
    'admin.users'     => 'Administration — gérer les utilisateurs',
    'admin.roles'     => 'Administration — gérer les rôles',
];

/* ---- Base des comptes (auto-créée) ---- */
function db_users(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('sqlite:' . __DIR__ . '/../data/users.sqlite');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        $pdo->exec('PRAGMA foreign_keys = ON');
        $pdo->exec("CREATE TABLE IF NOT EXISTS roles (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nom       TEXT NOT NULL UNIQUE,
            perms     TEXT NOT NULL DEFAULT '[]',
            is_system INTEGER NOT NULL DEFAULT 0
        )");
        $pdo->exec('CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role_id       INTEGER NOT NULL REFERENCES roles(id),
            actif         INTEGER NOT NULL DEFAULT 1,
            doit_changer  INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT NOT NULL DEFAULT (datetime(\'now\',\'localtime\')),
            last_login    TEXT
        )');
        /* Seed idempotent : INSERT OR IGNORE — ne touche jamais à un rôle
           personnalisé ni à un compte existant (y compris désactivé).
           Les mots de passe des comptes par défaut sont lus dans les
           variables d'environnement (aucun mot de passe en clair dans
           le code) : variable absente ou vide → compte non créé. */
        $pdo->exec("INSERT OR IGNORE INTO roles (id, nom, perms, is_system) VALUES
            (1, 'Administrateur', '*', 1),
            (2, 'Vérification', '[\"verif.use\"]', 1)");
        $seed = [];
        $mdpAdmin = getenv('BCP_ADMIN_MDP');
        if (is_string($mdpAdmin) && $mdpAdmin !== '') {
            $seed[] = ['admin', $mdpAdmin, 1];
        }
        $mdpVerif = getenv('BCP_VERIF_MDP');
        if (is_string($mdpVerif) && $mdpVerif !== '') {
            $seed[] = ['GroupeNJS26', $mdpVerif, 2];
        }
        $st = $pdo->prepare('INSERT OR IGNORE INTO users (username, password_hash, role_id, actif, doit_changer)
                             VALUES (?, ?, ?, 1, 0)');
        foreach ($seed as [$user, $mdp, $role]) {
            $st->execute([$user, password_hash($mdp, PASSWORD_DEFAULT), $role]);
        }
    }
    return $pdo;
}

/** Utilisateur connecté (JOIN rôle), ou null. Cache statique par requête,
 *  invalidé si l'utilisateur de session change en cours de requête
 *  (ex. juste après la connexion dans page_login). */
function current_user(): ?array
{
    static $u = false, $uid_cache = null;   // false = pas encore résolu
    $uid = !empty($_SESSION['uid']) ? (int) $_SESSION['uid'] : null;
    if ($u === false || $uid_cache !== $uid) {
        $uid_cache = $uid;
        $u = null;
        if ($uid !== null) {
            $st = db_users()->prepare(
                'SELECT u.id, u.username, u.actif, u.doit_changer, u.last_login,
                        r.id AS role_id, r.nom AS role_nom, r.perms AS role_perms
                 FROM users u JOIN roles r ON r.id = u.role_id WHERE u.id = ?');
            $st->execute([$uid]);
            $ligne = $st->fetch();
            if ($ligne && (int) $ligne['actif'] === 1) {
                $u = $ligne;
            } else {
                unset($_SESSION['uid']);   // compte supprimé ou désactivé
            }
        }
    }
    return $u;
}

/** Le rôle courant possède-t-il la permission ? ('*' passe tout) */
function perm(string $cle): bool
{
    $u = current_user();
    if ($u === null) {
        return false;
    }
    if ($u['role_perms'] === '*') {
        return true;
    }
    $liste = json_decode((string) $u['role_perms'], true);
    return is_array($liste) && in_array($cle, $liste, true);
}

/** Première page accessible pour l'utilisateur courant (après login). */
function premiere_page(): string
{
    $ordre = [
        'doc.view'      => 'index.php?p=form',
        'suivi.view'    => 'index.php?p=suivi',
        'analyses.view' => 'index.php?p=analyses',
        'gagnants.view' => 'index.php?p=gagnants',
        'verif.use'     => 'index.php?p=verifier',
        'admin.users'   => 'index.php?p=utilisateurs',
    ];
    foreach ($ordre as $cle => $url) {
        if (perm($cle)) {
            return $url;
        }
    }
    return 'index.php?p=changer_mdp';
}

/** Exige une connexion : sinon redirection vers la page de login. */
function require_login(): void
{
    if (current_user() === null) {
        header('Location: index.php?p=login&next=' . rawurlencode((string) ($_SERVER['REQUEST_URI'] ?? 'index.php')));
        exit;
    }
}

/** Exige une permission : non connecté → login ; sans droit → 403 stylé. */
function require_perm(string $cle): void
{
    $u = current_user();
    if ($u === null) {
        header('Location: index.php?p=login&next=' . rawurlencode((string) ($_SERVER['REQUEST_URI'] ?? 'index.php')));
        exit;
    }
    if ((int) $u['doit_changer'] === 1) {
        header('Location: index.php?p=changer_mdp');
        exit;
    }
    if (!perm($cle)) {
        http_response_code(403);
        page_debut('Accès refusé — Ristournes');
        ?>
        <div class="wrap-form">
          <h1>⛔ Accès refusé</h1>
          <p>Votre compte <b><?= e((string) $u['username']) ?></b> (rôle : <?= e((string) $u['role_nom']) ?>)
             n'a pas la permission « <?= e(PERM_LABELS[$cle] ?? $cle) ?> ».</p>
          <p><a class="btn-mini" href="<?= e(premiere_page()) ?>">Retour à la page d'accueil</a></p>
        </div>
        <?php
        page_fin();
        exit;
    }
}

/* ---- Jetons CSRF (un par session) ---- */
function csrf_token(): string
{
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(16));
    }
    return (string) $_SESSION['csrf'];
}

function csrf_valide(?string $j): bool
{
    return is_string($j) && $j !== '' && !empty($_SESSION['csrf'])
        && hash_equals((string) $_SESSION['csrf'], $j);
}

function auth_logout(): void
{
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', time() - 42000, $p['path'], $p['domain'], $p['secure'], $p['httponly']);
    }
    session_destroy();
    header('Location: index.php?p=login');
    exit;
}

/* ---------------------------------------------------------------
 * Barre de navigation unique — rendue par page_debut() sur toutes
 * les pages (sauf login) ; chaque lien n'apparaît que si le rôle
 * courant possède la permission correspondante.
 * --------------------------------------------------------------- */
function render_nav(): void
{
    $u = current_user();
    if ($u === null) {
        return;
    }
    $p = (string) ($_GET['p'] ?? '');
    $lien = function (string $cle, string $page, string $label) use ($p): string {
        if (!perm($cle)) {
            return '';
        }
        return '<a href="index.php?p=' . $page . '"'
             . ($p === $page ? ' class="actif" aria-current="page"' : '')
             . '>' . e($label) . '</a>';
    };
    ?>
    <nav class="navbar no-print" aria-label="Navigation principale">
      <span class="nav-brand">Ristournes — <em>BELGOCAM</em></span>
      <button class="nav-toggle" type="button" aria-label="Menu" aria-expanded="false">☰</button>
      <div class="nav-links">
        <?= $lien('doc.view', 'form', 'Formulaire') ?>
        <?= $lien('suivi.view', 'suivi', 'Suivi') ?>
        <?= $lien('analyses.view', 'analyses', 'Analyses') ?>
        <?= $lien('gagnants.view', 'gagnants', 'Gagnants') ?>
        <?= $lien('verif.use', 'verifier', 'Vérifier') ?>
        <?= $lien('admin.users', 'utilisateurs', 'Utilisateurs') ?>
        <?= $lien('admin.roles', 'roles', 'Rôles') ?>
        <span class="spacer"></span>
        <span class="nav-user" title="<?= e((string) $u['username']) ?> — <?= e((string) $u['role_nom']) ?>"><?= e((string) $u['username']) ?> · <?= e((string) $u['role_nom']) ?></span>
        <a href="index.php?p=changer_mdp" class="nav-mineur">Mot de passe</a>
        <a href="index.php?p=logout" class="nav-mineur">Déconnexion</a>
      </div>
    </nav>
    <?php
}

/* ---------------------------------------------------------------
 * Page de connexion (sans navbar)
 * --------------------------------------------------------------- */
function page_login(): void
{
    if (current_user() !== null) {
        $next = (string) ($_GET['next'] ?? '');
        header('Location: ' . (preg_match('#^index\.php#i', $next) ? $next : premiere_page()));
        exit;
    }
    $err = '';
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!csrf_valide($_POST['csrf'] ?? null)) {
            $err = 'Session expirée — réessayez.';
        } else {
            usleep(600000);   /* temporisation anti force brute */
            $st = db_users()->prepare('SELECT * FROM users WHERE username = ?');
            $st->execute([trim((string) ($_POST['username'] ?? ''))]);
            $ligne = $st->fetch();
            $mdp = (string) ($_POST['password'] ?? '');
            if ($ligne && password_verify($mdp, (string) $ligne['password_hash'])) {
                if ((int) $ligne['actif'] !== 1) {
                    $err = 'Compte désactivé — contactez un administrateur.';
                } else {
                    session_regenerate_id(true);
                    $_SESSION['uid'] = (int) $ligne['id'];
                    db_users()->prepare("UPDATE users SET last_login = datetime('now','localtime') WHERE id = ?")
                              ->execute([(int) $ligne['id']]);
                    $next = (string) ($_POST['next'] ?? '');
                    $dest = (int) $ligne['doit_changer'] === 1
                          ? 'index.php?p=changer_mdp'
                          : (preg_match('#^index\.php#i', $next) ? $next : premiere_page());
                    header('Location: ' . $dest);
                    exit;
                }
            } else {
                $err = 'Identifiants incorrects.';
            }
        }
    }
    $aucun = (int) db_users()->query('SELECT COUNT(*) FROM users')->fetchColumn() === 0;
    page_debut('Connexion — Ristournes', false);
    ?>
    <div class="login-page">
      <div class="login-card">
        <div class="login-brand">BELGOCAM <span>S.A.</span></div>
        <h1>Chèques &amp; listings de ristournes</h1>
        <p class="login-sous">Connectez-vous pour accéder à l'application.</p>
        <?php if ($aucun): ?><p class="login-info">Aucun compte n'est configuré. Au premier lancement,
        définissez les variables d'environnement <b>BCP_ADMIN_MDP</b> (et <b>BCP_VERIF_MDP</b>)
        puis rechargez cette page pour créer les comptes par défaut — voir README.</p><?php endif; ?>
        <?php if ($err !== ''): ?><p class="login-err" role="alert"><?= e($err) ?></p><?php endif; ?>
        <form method="post" action="index.php?p=login" autocomplete="on">
          <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
          <input type="hidden" name="next" value="<?= e((string) ($_GET['next'] ?? '')) ?>">
          <label>Identifiant
            <input type="text" name="username" required autofocus
                   autocomplete="username" value="<?= e((string) ($_POST['username'] ?? '')) ?>">
          </label>
          <label>Mot de passe
            <input type="password" name="password" required autocomplete="current-password">
          </label>
          <div class="barre-actions"><button type="submit" class="btn-principal">Se connecter</button></div>
        </form>
      </div>
    </div>
    <?php
    page_fin();
}

/* ---------------------------------------------------------------
 * Changement du mot de passe personnel (tout utilisateur connecté)
 * --------------------------------------------------------------- */
function page_changer_mdp(): void
{
    require_login();
    $u = current_user();
    $err = '';
    $ok = '';
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!csrf_valide($_POST['csrf'] ?? null)) {
            $err = 'Session expirée — réessayez.';
        } else {
            $actuel = (string) ($_POST['actuel'] ?? '');
            $nouveau = (string) ($_POST['nouveau'] ?? '');
            $conf = (string) ($_POST['confirmation'] ?? '');
            $st = db_users()->prepare('SELECT password_hash FROM users WHERE id = ?');
            $st->execute([(int) $u['id']]);
            $hash = (string) $st->fetchColumn();
            if (!password_verify($actuel, $hash)) {
                $err = 'Mot de passe actuel incorrect.';
            } elseif (mb_strlen($nouveau) < 6) {
                $err = 'Le nouveau mot de passe doit comporter au moins 6 caractères.';
            } elseif ($nouveau !== $conf) {
                $err = 'La confirmation ne correspond pas au nouveau mot de passe.';
            } else {
                db_users()->prepare('UPDATE users SET password_hash = ?, doit_changer = 0 WHERE id = ?')
                          ->execute([password_hash($nouveau, PASSWORD_DEFAULT), (int) $u['id']]);
                $ok = 'Mot de passe modifié.';
            }
        }
    }
    page_debut('Changer de mot de passe — Ristournes');
    ?>
    <div class="wrap-form wrap-mdp">
      <h1>🔑 Changer de mot de passe</h1>
      <p class="sous-titre">Compte : <b><?= e((string) $u['username']) ?></b> (<?= e((string) $u['role_nom']) ?>)</p>
      <?php if ($ok !== ''): ?><p class="admin-ok"><?= e($ok) ?></p><?php endif; ?>
      <?php if ($err !== ''): ?><p class="admin-err" role="alert"><?= e($err) ?></p><?php endif; ?>
      <form method="post" action="index.php?p=changer_mdp">
        <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
        <div class="mdp-champs">
          <label>Mot de passe actuel
            <input type="password" name="actuel" required autocomplete="current-password">
          </label>
          <label>Nouveau mot de passe (6 caractères min.)
            <input type="password" name="nouveau" required minlength="6" autocomplete="new-password">
          </label>
          <label>Confirmation
            <input type="password" name="confirmation" required minlength="6" autocomplete="new-password">
          </label>
        </div>
        <div class="barre-actions"><button type="submit" class="btn-principal">Enregistrer</button></div>
      </form>
    </div>
    <?php
    page_fin();
}
