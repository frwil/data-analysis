<?php
declare(strict_types=1);
/* =============================================================
 * Suivi des impressions des chèques/listings — BELGOCAM S.A.
 * Journal horodaté par document (uuid client+année, base qr.sqlite).
 * Compteurs DÉRIVÉS : SUM(delta) par (uuid, type) — les corrections
 * (-1, réinitialisation) sont des écritures négatives : l'historique
 * reste complet, rien n'est effacé silencieusement.
 *
 * type     : 'directe' (impression depuis l'aperçu) | 'pdf'
 * statut   : 'reussi' | 'echoue' | 'annulee' (directe, delta 0 sauf reussi)
 *            'telecharge' (pdf généré/téléchargé, delta 0, audit serveur)
 *            'reinit' (réinitialisation, delta = -compteur)
 * ============================================================= */

function db_suivi(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('sqlite:' . __DIR__ . '/../data/suivi.sqlite');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        $pdo->exec("CREATE TABLE IF NOT EXISTS impressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('directe','pdf')),
            delta INTEGER NOT NULL DEFAULT 0,
            statut TEXT CHECK (statut IN ('reussi','echoue','annulee','telecharge','reinit')),
            note TEXT,
            moment TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )");
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_imp_uuid_type ON impressions(uuid, type)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_imp_moment ON impressions(moment)');
    }
    return $pdo;
}

/** Écrit une ligne dans le journal (l'uuid doit exister dans la base qr). */
function suivi_log(string $uuid, string $type, ?string $statut, int $delta, string $note = ''): void
{
    if (!preg_match('/^[0-9a-f-]{36}$/i', $uuid)) {
        return;
    }
    $q = db_qr();
    $st = $q->prepare('SELECT 1 FROM qr WHERE uuid = ?');
    $st->execute([$uuid]);
    if (!$st->fetchColumn()) {
        return; // uuid inconnu : aucune écriture
    }
    db_suivi()->prepare('INSERT INTO impressions (uuid, type, delta, statut, note)
                         VALUES (?, ?, ?, ?, ?)')
              ->execute([$uuid, $type, $delta, $statut, $note]);
}

/** Compteurs courants d'un document : ['directe' => n, 'pdf' => n]. */
function suivi_compteurs(string $uuid): array
{
    $st = db_suivi()->prepare(
        'SELECT type, SUM(delta) AS n FROM impressions WHERE uuid = ? GROUP BY type');
    $st->execute([$uuid]);
    $out = ['directe' => 0, 'pdf' => 0];
    foreach ($st->fetchAll() as $r) {
        $out[$r['type']] = (int) $r['n'];
    }
    return $out;
}

/** Statistiques groupées par uuid : compteurs + échecs/annulations + dernière écriture.
 *  Retour : [uuid => ['directe' => n, 'pdf' => n, 'echecs' => n, 'dernier' => moment]] */
function suivi_stats(): array
{
    $rows = db_suivi()->query(
        "SELECT uuid,
                SUM(CASE WHEN type = 'directe' THEN delta ELSE 0 END) AS d,
                SUM(CASE WHEN type = 'pdf' THEN delta ELSE 0 END) AS p,
                SUM(CASE WHEN type = 'directe' AND statut IN ('echoue','annulee') THEN 1 ELSE 0 END) AS x,
                MAX(moment) AS dernier
         FROM impressions GROUP BY uuid")->fetchAll();
    $out = [];
    foreach ($rows as $r) {
        $out[$r['uuid']] = [
            'directe' => (int) $r['d'],
            'pdf'     => (int) $r['p'],
            'echecs'  => (int) $r['x'],
            'dernier' => (string) $r['dernier'],
        ];
    }
    return $out;
}

/** Statistiques par (tiers, agence, annee) — pour les badges du formulaire
 *  et le tableau de la page de suivi.
 *  Retour : ['<tiers>|<agence>' => [annee => ['directe'…]]] */
function suivi_stats_par_client(): array
{
    $q = db_qr();
    $qr = $q->query('SELECT uuid, tiers, agence, annee FROM qr')->fetchAll();
    $stats = suivi_stats();
    $out = [];
    foreach ($qr as $r) {
        $cle = $r['tiers'] . '|' . $r['agence'];
        if (!isset($out[$cle])) {
            $out[$cle] = [];
        }
        $s = $stats[$r['uuid']] ?? null;
        if ($s !== null) {
            $s['annee'] = (int) $r['annee'];
            $s['uuid'] = $r['uuid'];
            $out[$cle][(int) $r['annee']] = $s;
        }
    }
    return $out;
}

/** Les 60 derniers événements du journal, libellés (tiers, agence, année). */
function suivi_histo(int $limite = 60): array
{
    $s = db_suivi();
    $rows = $s->query("SELECT id, uuid, type, delta, statut, note, moment
                       FROM impressions ORDER BY id DESC LIMIT " . (int) $limite)->fetchAll();
    if (!$rows) {
        return [];
    }
    $uuids = array_values(array_unique(array_column($rows, 'uuid')));
    $q = db_qr();
    $in = implode(',', array_fill(0, count($uuids), '?'));
    $st = $q->prepare("SELECT uuid, tiers, agence, annee FROM qr WHERE uuid IN ($in)");
    $st->execute($uuids);
    $lab = [];
    foreach ($st->fetchAll() as $r) {
        $lab[$r['uuid']] = ['tiers' => $r['tiers'], 'agence' => $r['agence'], 'annee' => (int) $r['annee']];
    }
    foreach ($rows as &$r) {
        $r['label'] = $lab[$r['uuid']] ?? null;
    }
    return $rows;
}

/** Badge compact des compteurs d'un client pour une année donnée :
 *  « 🖨2 ✗1 📄1 » — toujours visible : « 🖨0 📄0 » quand aucun événement
 *  (élément visuel du compteur dans la liste des clients). */
function badge_imp(?array $s): string
{
    $d = (int) ($s['directe'] ?? 0);
    $x = (int) ($s['echecs'] ?? 0);
    $p = (int) ($s['pdf'] ?? 0);
    $parts = ['🖨' . $d, '📄' . $p];
    if ($x > 0) {
        $parts[] = '✗' . $x;
    }
    return implode(' ', $parts);
}

/* ---------------------------------------------------------------
 * API JSON (p=suivi_api) — actions :
 *   log     {uuid, type, statut}            directe : reussi (+1) sinon 0
 *   log_lot {type, statut, delta, uuids[]}  une écriture par uuid
 *   ajuster {uuid, type}                    -1 (seulement si compteur > 0)
 *   reset   {uuid, type}                    delta = -compteur courant
 * --------------------------------------------------------------- */
function suivi_action(array $r): array
{
    $action = (string) ($r['action'] ?? '');
    $uuid = (string) ($r['uuid'] ?? '');
    $type = (string) ($r['type'] ?? '');
    $okTypes = ['directe', 'pdf'];
    switch ($action) {
        case 'log':
            $statut = (string) ($r['statut'] ?? '');
            if (!in_array($type, $okTypes, true)
                || !in_array($statut, ['reussi', 'echoue', 'annulee'], true)) {
                return ['ok' => false, 'message' => 'paramètres invalides'];
            }
            suivi_log($uuid, $type, $statut, $statut === 'reussi' ? 1 : 0);
            return ['ok' => true, 'compteurs' => suivi_compteurs($uuid)];

        case 'log_lot':
            $statut = (string) ($r['statut'] ?? '');
            $delta = (int) ($r['delta'] ?? ($statut === 'reussi' ? 1 : 0));
            $uuids = is_array($r['uuids'] ?? null)
                ? array_values(array_unique(array_map('strval', $r['uuids']))) : [];
            if (!in_array($type, $okTypes, true) || !$uuids) {
                return ['ok' => false, 'message' => 'paramètres invalides'];
            }
            foreach ($uuids as $u) {
                suivi_log($u, $type, $statut !== '' ? $statut : null, $delta);
            }
            return ['ok' => true];

        case 'ajuster':
            if (!in_array($type, $okTypes, true)) {
                return ['ok' => false, 'message' => 'type invalide'];
            }
            if (suivi_compteurs($uuid)[$type] <= 0) {
                return ['ok' => false, 'message' => 'compteur déjà à zéro'];
            }
            suivi_log($uuid, $type, null, -1, 'correction manuelle -1');
            return ['ok' => true, 'compteurs' => suivi_compteurs($uuid)];

        case 'reset':
            if (!in_array($type, $okTypes, true)) {
                return ['ok' => false, 'message' => 'type invalide'];
            }
            $n = suivi_compteurs($uuid)[$type];
            if ($n > 0) {
                suivi_log($uuid, $type, 'reinit', -$n, 'réinitialisation manuelle');
            }
            return ['ok' => true, 'compteurs' => suivi_compteurs($uuid)];
    }
    return ['ok' => false, 'message' => 'action inconnue'];
}
