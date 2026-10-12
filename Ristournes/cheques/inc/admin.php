<?php
declare(strict_types=1);
/* =============================================================
 * Pages d'administration — utilisateurs et rôles
 * Réservées aux permissions admin.users / admin.roles (le gating
 * est fait dans le routeur d'index.php). Tous les POST exigent le
 * jeton CSRF ; après succès, redirection 303 (anti re-soumission).
 * Gardes : impossible de se désactiver / changer son propre rôle,
 * ni de supprimer le dernier administrateur actif, les rôles
 * système ou un rôle encore attribué.
 * ============================================================= */

function admin_role_existe(int $id): bool
{
    $st = db_users()->prepare('SELECT 1 FROM roles WHERE id = ?');
    $st->execute([$id]);
    return $st->fetchColumn() !== false;
}

function admin_redirige(string $page, string $msg): void
{
    header('Location: index.php?p=' . $page . '&msg=' . rawurlencode($msg), true, 303);
    exit;
}

function admin_msg(): string
{
    $map = [
        'creer_ok'   => 'Utilisateur créé.',
        'role_ok'    => 'Rôle mis à jour.',
        'actif_ok'   => 'Compte mis à jour.',
        'reinit_ok'  => 'Mot de passe réinitialisé — l\'utilisateur devra en choisir un nouveau à sa prochaine connexion.',
        'suppr_ok'   => 'Rôle supprimé.',
    ];
    return $map[(string) ($_GET['msg'] ?? '')] ?? '';
}

/** Nombre d'administrateurs actifs (rôle perms = '*'). */
function admin_nb_actifs(): int
{
    return (int) db_users()->query(
        "SELECT COUNT(*) FROM users u JOIN roles r ON r.id = u.role_id
         WHERE u.actif = 1 AND r.perms = '*'")->fetchColumn();
}

/* ---------------------------------------------------------------
 * Utilisateurs
 * --------------------------------------------------------------- */
function page_utilisateurs(): void
{
    $pdo = db_users();
    $u = current_user();
    $err = '';

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!csrf_valide($_POST['csrf'] ?? null)) {
            $err = 'Session expirée — réessayez.';
        } else {
            $action = (string) ($_POST['action'] ?? '');
            if ($action === 'creer') {
                $user = trim((string) ($_POST['username'] ?? ''));
                $mdp = (string) ($_POST['password'] ?? '');
                $role = (int) ($_POST['role_id'] ?? 0);
                if ($user === '' || $mdp === '' || $role <= 0) {
                    $err = 'Identifiant, mot de passe et rôle sont requis.';
                } elseif (mb_strlen($mdp) < 6) {
                    $err = 'Le mot de passe doit comporter au moins 6 caractères.';
                } else {
                    $st = $pdo->prepare('SELECT 1 FROM users WHERE username = ?');
                    $st->execute([$user]);
                    if ($st->fetchColumn()) {
                        $err = 'Cet identifiant existe déjà.';
                    } elseif (!admin_role_existe($role)) {
                        $err = 'Rôle inconnu.';
                    } else {
                        $pdo->prepare('INSERT INTO users (username, password_hash, role_id, actif, doit_changer)
                                       VALUES (?, ?, ?, 1, 0)')
                            ->execute([$user, password_hash($mdp, PASSWORD_DEFAULT), $role]);
                        admin_redirige('utilisateurs', 'creer_ok');
                    }
                }
            } elseif (in_array($action, ['modifier_role', 'basculer_actif', 'reinit_mdp'], true)) {
                $cible = (int) ($_POST['id'] ?? 0);
                $st = $pdo->prepare('SELECT u.id, u.actif, u.role_id, r.perms FROM users u
                                     JOIN roles r ON r.id = u.role_id WHERE u.id = ?');
                $st->execute([$cible]);
                $c = $st->fetch();
                if (!$c) {
                    $err = 'Utilisateur inconnu.';
                } else {
                    $estAdmin = $c['perms'] === '*';
                    if ($action === 'modifier_role') {
                        $role = (int) ($_POST['role_id'] ?? 0);
                        if (!admin_role_existe($role)) {
                            $err = 'Rôle inconnu.';
                        } elseif ($cible === (int) $u['id'] && $role !== (int) $c['role_id']) {
                            $err = 'Vous ne pouvez pas changer votre propre rôle.';
                        } elseif ($estAdmin && admin_nb_actifs() <= 1 && $role !== (int) $c['role_id']) {
                            $err = 'Impossible : c\'est le dernier administrateur actif.';
                        } else {
                            $pdo->prepare('UPDATE users SET role_id = ? WHERE id = ?')
                                ->execute([$role, $cible]);
                            admin_redirige('utilisateurs', 'role_ok');
                        }
                    } elseif ($action === 'basculer_actif') {
                        $nouveau = (int) $c['actif'] === 1 ? 0 : 1;
                        if ($cible === (int) $u['id']) {
                            $err = 'Vous ne pouvez pas désactiver votre propre compte.';
                        } elseif ($nouveau === 0 && $estAdmin && admin_nb_actifs() <= 1) {
                            $err = 'Impossible : c\'est le dernier administrateur actif.';
                        } else {
                            $pdo->prepare('UPDATE users SET actif = ? WHERE id = ?')
                                ->execute([$nouveau, $cible]);
                            admin_redirige('utilisateurs', 'actif_ok');
                        }
                    } else { /* reinit_mdp */
                        $mdp = (string) ($_POST['password'] ?? '');
                        if (mb_strlen($mdp) < 6) {
                            $err = 'Le nouveau mot de passe doit comporter au moins 6 caractères.';
                        } else {
                            $pdo->prepare('UPDATE users SET password_hash = ?, doit_changer = 1 WHERE id = ?')
                                ->execute([password_hash($mdp, PASSWORD_DEFAULT), $cible]);
                            admin_redirige('utilisateurs', 'reinit_ok');
                        }
                    }
                }
            } else {
                $err = 'Action inconnue.';
            }
        }
    }

    $users = $pdo->query('SELECT u.*, r.nom AS role_nom FROM users u
                          JOIN roles r ON r.id = u.role_id
                          ORDER BY u.username COLLATE NOCASE')->fetchAll();
    $roles = $pdo->query('SELECT * FROM roles ORDER BY id')->fetchAll();

    page_debut('Utilisateurs — Ristournes');
    ?>
    <div class="wrap-admin">
      <h1>👥 Utilisateurs</h1>
      <p class="sous-titre">Comptes de l'application : rôle, activation et réinitialisation de mot de passe.
        Les mots de passe sont hachés (password_hash) — jamais stockés en clair.</p>
      <?php if (($msg = admin_msg()) !== ''): ?><p class="admin-ok"><?= e($msg) ?></p><?php endif; ?>
      <?php if ($err !== ''): ?><p class="admin-err" role="alert"><?= e($err) ?></p><?php endif; ?>

      <div class="tab-scroll">
        <table class="tab admin-tab">
          <thead><tr>
            <th>Identifiant</th><th>Rôle</th><th>Statut</th><th>Créé le</th>
            <th>Dernière connexion</th><th>Actions</th>
          </tr></thead>
          <tbody>
            <?php foreach ($users as $usr): $actif = (int) $usr['actif'] === 1; $soi = (int) $usr['id'] === (int) $u['id']; ?>
              <tr>
                <td><?= e((string) $usr['username']) ?><?= $soi ? ' <span class="noms-differents">vous</span>' : '' ?></td>
                <td>
                  <?php if ($soi): ?>
                    <?= e((string) $usr['role_nom']) ?>
                  <?php else: ?>
                    <form method="post" action="index.php?p=utilisateurs" class="form-inline">
                      <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
                      <input type="hidden" name="action" value="modifier_role">
                      <input type="hidden" name="id" value="<?= (int) $usr['id'] ?>">
                      <select name="role_id" onchange="this.form.submit()" title="Changer le rôle">
                        <?php foreach ($roles as $r): ?>
                          <option value="<?= (int) $r['id'] ?>" <?= (int) $r['id'] === (int) $usr['role_id'] ? 'selected' : '' ?>><?= e((string) $r['nom']) ?></option>
                        <?php endforeach; ?>
                      </select>
                    </form>
                  <?php endif; ?>
                </td>
                <td><?= $actif ? '<span class="badge badge-ok">Actif</span>' : '<span class="badge badge-off">Désactivé</span>' ?></td>
                <td class="mineur"><?= e((string) substr((string) $usr['created_at'], 0, 10)) ?></td>
                <td class="mineur"><?= $usr['last_login'] !== null ? e(str_replace('T', ' ', (string) $usr['last_login'])) : '—' ?></td>
                <td class="actions">
                  <form method="post" action="index.php?p=utilisateurs" class="form-inline">
                    <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
                    <input type="hidden" name="action" value="basculer_actif">
                    <input type="hidden" name="id" value="<?= (int) $usr['id'] ?>">
                    <button type="submit" class="btn-mini" <?= $soi ? 'disabled title="Votre propre compte"' : '' ?>><?= $actif ? 'Désactiver' : 'Activer' ?></button>
                  </form>
                  <form method="post" action="index.php?p=utilisateurs" class="form-inline form-reinit">
                    <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
                    <input type="hidden" name="action" value="reinit_mdp">
                    <input type="hidden" name="id" value="<?= (int) $usr['id'] ?>">
                    <input type="password" name="password" placeholder="Nouveau mdp" minlength="6"
                           title="Le mot de passe est réinitialisé et l'utilisateur devra en choisir un nouveau à sa prochaine connexion.">
                    <button type="submit" class="btn-mini">Réinit mdp</button>
                  </form>
                </td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      </div>

      <h2>Nouvel utilisateur</h2>
      <form method="post" action="index.php?p=utilisateurs" class="admin-form">
        <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
        <input type="hidden" name="action" value="creer">
        <div class="ligne-champs">
          <label>Identifiant <input type="text" name="username" required autocomplete="off"></label>
          <label>Mot de passe <input type="password" name="password" required minlength="6" autocomplete="new-password"></label>
          <label>Rôle
            <select name="role_id">
              <?php foreach ($roles as $r): ?>
                <option value="<?= (int) $r['id'] ?>"><?= e((string) $r['nom']) ?></option>
              <?php endforeach; ?>
            </select>
          </label>
          <button type="submit" class="btn-principal">Créer le compte</button>
        </div>
      </form>
    </div>
    <?php
    page_fin();
}

/* ---------------------------------------------------------------
 * Rôles & permissions
 * --------------------------------------------------------------- */
function page_roles(): void
{
    $pdo = db_users();
    $err = '';

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!csrf_valide($_POST['csrf'] ?? null)) {
            $err = 'Session expirée — réessayez.';
        } else {
            $action = (string) ($_POST['action'] ?? '');
            if ($action === 'creer' || $action === 'enregistrer') {
                $nom = trim((string) ($_POST['nom'] ?? ''));
                $tous = ($_POST['tous'] ?? '') === '1';
                $cles = $tous ? '*'
                    : json_encode(array_values(array_intersect(
                        array_keys(PERM_LABELS), (array) ($_POST['perms'] ?? []))), JSON_UNESCAPED_UNICODE);
                if ($nom === '') {
                    $err = 'Le nom du rôle est requis.';
                } elseif ($action === 'creer') {
                    $st = $pdo->prepare('SELECT 1 FROM roles WHERE nom = ?');
                    $st->execute([$nom]);
                    if ($st->fetchColumn()) {
                        $err = 'Un rôle porte déjà ce nom.';
                    } else {
                        $pdo->prepare('INSERT INTO roles (nom, perms, is_system) VALUES (?, ?, 0)')
                            ->execute([$nom, $cles]);
                        admin_redirige('roles', 'role_ok');
                    }
                } else {
                    $id = (int) ($_POST['id'] ?? 0);
                    $st = $pdo->prepare('SELECT is_system FROM roles WHERE id = ?');
                    $st->execute([$id]);
                    $sys = $st->fetchColumn();
                    if ($sys === false) {
                        $err = 'Rôle inconnu.';
                    } elseif ($id === 1) {
                        $pdo->exec("UPDATE roles SET perms = '*' WHERE id = 1");   // Administrateur : toujours '*'
                        admin_redirige('roles', 'role_ok');
                    } else {
                        $pdo->prepare('UPDATE roles SET nom = ?, perms = ? WHERE id = ?')
                            ->execute([$nom, $cles, $id]);
                        admin_redirige('roles', 'role_ok');
                    }
                }
            } elseif ($action === 'supprimer') {
                $id = (int) ($_POST['id'] ?? 0);
                $st = $pdo->prepare('SELECT is_system,
                                     (SELECT COUNT(*) FROM users u WHERE u.role_id = roles.id) AS n
                                     FROM roles WHERE id = ?');
                $st->execute([$id]);
                $r = $st->fetch();
                if (!$r) {
                    $err = 'Rôle inconnu.';
                } elseif ((int) $r['is_system'] === 1) {
                    $err = 'Les rôles système ne peuvent pas être supprimés.';
                } elseif ((int) $r['n'] > 0) {
                    $err = 'Ce rôle est attribué à des utilisateurs : réaffectez-les d\'abord.';
                } else {
                    $pdo->prepare('DELETE FROM roles WHERE id = ?')->execute([$id]);
                    admin_redirige('roles', 'suppr_ok');
                }
            } else {
                $err = 'Action inconnue.';
            }
        }
    }

    $roles = $pdo->query('SELECT r.*, (SELECT COUNT(*) FROM users u WHERE u.role_id = r.id) AS n_users
                          FROM roles r ORDER BY r.id')->fetchAll();
    $edition = (int) ($_GET['edit'] ?? 0);
    $roleEdit = null;
    foreach ($roles as $r) {
        if ((int) $r['id'] === $edition) {
            $roleEdit = $r;
            break;
        }
    }

    page_debut('Rôles & permissions — Ristournes');
    ?>
    <div class="wrap-admin">
      <h1>🔐 Rôles &amp; permissions</h1>
      <p class="sous-titre">Un rôle est un ensemble de permissions par domaine. Le rôle « Administrateur »
        a tous les droits. Chaque utilisateur ne voit dans la barre de navigation que les pages
        auxquelles son rôle donne accès.</p>
      <?php if (($msg = admin_msg()) !== ''): ?><p class="admin-ok"><?= e($msg) ?></p><?php endif; ?>
      <?php if ($err !== ''): ?><p class="admin-err" role="alert"><?= e($err) ?></p><?php endif; ?>

      <div class="tab-scroll">
        <table class="tab admin-tab">
          <thead><tr><th>Rôle</th><th>Permissions</th><th>Utilisateurs</th><th>Actions</th></tr></thead>
          <tbody>
            <?php foreach ($roles as $r):
                $perms = $r['perms'] === '*' ? null : (json_decode((string) $r['perms'], true) ?: []); ?>
              <tr>
                <td><?= e((string) $r['nom']) ?><?= (int) $r['is_system'] === 1 ? ' <span class="noms-differents">système</span>' : '' ?></td>
                <td class="mineur"><?= $perms === null ? 'Tous les droits' : count($perms) . ' permission(s)' ?></td>
                <td class="num"><?= (int) $r['n_users'] ?></td>
                <td class="actions">
                  <a class="btn-mini" href="index.php?p=roles&amp;edit=<?= (int) $r['id'] ?>">Modifier</a>
                  <?php if ((int) $r['is_system'] === 0): ?>
                    <form method="post" action="index.php?p=roles" class="form-inline">
                      <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
                      <input type="hidden" name="action" value="supprimer">
                      <input type="hidden" name="id" value="<?= (int) $r['id'] ?>">
                      <button type="submit" class="btn-mini" onclick="return confirm('Supprimer ce rôle ?')">Supprimer</button>
                    </form>
                  <?php endif; ?>
                </td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      </div>

      <?php
      $clesEdit = $roleEdit !== null && $roleEdit['perms'] !== '*'
          ? (json_decode((string) $roleEdit['perms'], true) ?: []) : [];
      $tousEdit = $roleEdit !== null && $roleEdit['perms'] === '*';
      $estAdmin = $roleEdit !== null && (int) $roleEdit['id'] === 1;
      $domaines = [
          'Documents'    => ['doc.view', 'doc.create', 'doc.pdf'],
          'Suivi'        => ['suivi.view', 'suivi.edit'],
          'Analyses'     => ['analyses.view', 'analyses.export'],
          'Gagnants'     => ['gagnants.view', 'gagnants.export'],
          'Vérification' => ['verif.use'],
          'Administration' => ['admin.users', 'admin.roles'],
      ];
      ?>
      <h2><?= $roleEdit !== null ? 'Modifier « ' . e((string) $roleEdit['nom']) . ' »' : 'Nouveau rôle' ?></h2>
      <form method="post" action="index.php?p=roles" class="admin-form">
        <input type="hidden" name="csrf" value="<?= e(csrf_token()) ?>">
        <input type="hidden" name="action" value="<?= $roleEdit !== null ? 'enregistrer' : 'creer' ?>">
        <?php if ($roleEdit !== null): ?><input type="hidden" name="id" value="<?= (int) $roleEdit['id'] ?>"><?php endif; ?>
        <label class="ligne-nom">Nom du rôle
          <input type="text" name="nom" required value="<?= $roleEdit !== null ? e((string) $roleEdit['nom']) : '' ?>"
                 <?= $roleEdit !== null && (int) $roleEdit['is_system'] === 1 ? 'readonly' : '' ?>>
        </label>
        <?php if ($estAdmin): ?>
          <p class="note">Le rôle Administrateur a tous les droits — non modifiable.</p>
        <?php else: ?>
          <label class="case tous-droits">
            <input type="checkbox" name="tous" value="1" <?= $tousEdit ? 'checked' : '' ?>>
            Tous les droits (équivalent administrateur)
          </label>
          <div class="perm-grid">
            <?php foreach ($domaines as $dom => $cles): ?>
              <fieldset>
                <legend><?= e($dom) ?></legend>
                <?php foreach ($cles as $cle): ?>
                  <label class="case"><input type="checkbox" name="perms[]" value="<?= e($cle) ?>"
                         <?= in_array($cle, $clesEdit, true) ? 'checked' : '' ?>> <?= e(PERM_LABELS[$cle] ?? $cle) ?></label>
                <?php endforeach; ?>
              </fieldset>
            <?php endforeach; ?>
          </div>
        <?php endif; ?>
        <div class="barre-actions">
          <button type="submit" class="btn-principal"><?= $roleEdit !== null ? 'Enregistrer' : 'Créer le rôle' ?></button>
        </div>
      </form>
    </div>
    <?php
    page_fin();
}
