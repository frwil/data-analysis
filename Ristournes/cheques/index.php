<?php
declare(strict_types=1);
/* Application chèques & listings de ristournes — BELGOCAM S.A.
   Pages : ?p=form (formulaire) · ?p=apercu (aperçu groupé) · ?p=imprimer (impression directe)
   Lancer : php -S localhost:8123 (dans le dossier cheques/) puis http://localhost:8123 */
require __DIR__ . '/inc/helpers.php';
require __DIR__ . '/inc/signature.php';
require __DIR__ . '/inc/suivi.php';
$cfg = require __DIR__ . '/inc/config.php';

function up(?string $s): string
{
    return function_exists('mb_strtoupper') ? mb_strtoupper((string) $s, 'UTF-8') : strtoupper((string) $s);
}

/* ---------------------------------------------------------------
 * Chargement des documents selon la période et la sélection
 * --------------------------------------------------------------- */
function charger_documents(): array
{
    $db = db();
    $annees = $db->query('SELECT DISTINCT substr(mois,1,4) FROM detail ORDER BY 1')
                 ->fetchAll(PDO::FETCH_COLUMN);
    $annee = (int) ($_GET['annee'] ?? (int) end($annees));
    if (!in_array((string) $annee, $annees, true)) {
        $annee = (int) end($annees);
    }

    $mois = (string) ($_GET['mois'] ?? 'all');
    $mois_db = $db->query("SELECT DISTINCT mois FROM detail WHERE mois LIKE '$annee-%' ORDER BY mois")
                  ->fetchAll(PDO::FETCH_COLUMN);
    if ($mois !== 'all' && !in_array($mois, $mois_db, true)) {
        $mois = 'all';
    }

    $sel = in_array($_GET['sel'] ?? 'tous', ['tous', 'un', 'liste'], true) ? $_GET['sel'] : 'tous';
    $avec_cheques  = ($_GET['cheques'] ?? '1') !== '0';
    $avec_listings = ($_GET['listings'] ?? '1') !== '0';
    if (!$avec_cheques && !$avec_listings) {
        $avec_cheques = true;
    }

    $ids = [];
    if ($sel !== 'tous') {
        $bruts = $sel === 'un' ? [$_GET['id'] ?? ''] : explode(',', (string) ($_GET['ids'] ?? ''));
        foreach ($bruts as $b) {
            if (ctype_digit(trim($b))) {
                $ids[] = (int) trim($b);
            }
        }
    }

    $sql = 'SELECT rowid AS id, tiers, agence, code, total, code_fallback FROM clients';
    $args = [];
    if ($mois !== 'all') {
        $sql .= " WHERE EXISTS (SELECT 1 FROM detail d WHERE d.tiers = clients.tiers
                  AND d.agence = clients.agence AND d.mois = ?)";
        $args[] = $mois;
    }
    if ($sel === 'un') {
        $sql .= ($args ? ' AND' : ' WHERE') . ' rowid = ?';
        $args[] = $ids[0] ?? -1;
    } elseif ($sel === 'liste') {
        if ($ids) {
            $sql .= ($args ? ' AND' : ' WHERE') . ' rowid IN (' . implode(',', array_fill(0, count($ids), '?')) . ')';
            foreach ($ids as $i) {
                $args[] = $i;
            }
        } else {
            $sql .= ($args ? ' AND' : ' WHERE') . ' 0';
        }
    }
    $sql .= ' ORDER BY tiers COLLATE NOCASE, agence';
    $st = $db->prepare($sql);
    $st->execute($args);
    $clients = $st->fetchAll();

    $mois_liste = mois_periode($annee, $mois !== 'all' ? $mois : null);
    $periode = periode_label($annee, $mois !== 'all' ? $mois : null);

    $docs = [];
    $stDet = $db->prepare('SELECT mois, t_conc, kg_autres, ristourne, commission_conc,
                                  commission_autres, total_mois
                           FROM detail WHERE tiers = ? AND agence = ? AND mois >= ? AND mois <= ?
                           ORDER BY mois');
    foreach ($clients as $cl) {
        $stDet->execute([$cl['tiers'], $cl['agence'], $annee . '-01', $annee . '-12']);
        $par_mois = [];
        foreach ($stDet->fetchAll() as $r) {
            $par_mois[$r['mois']] = $r;
        }
        $rows = [];
        $tot = ['t_conc' => 0.0, 'kg' => 0.0, 'ristourne' => 0.0, 'commission' => 0.0, 'montant' => 0.0];
        foreach ($mois_liste as $mm) {
            $r = $par_mois[$mm] ?? null;
            $t_conc  = (float) ($r['t_conc'] ?? 0);
            $kg      = (float) ($r['kg_autres'] ?? 0);
            $rist    = (float) ($r['ristourne'] ?? 0);
            $comm    = (float) ($r['commission_conc'] ?? 0) + (float) ($r['commission_autres'] ?? 0);
            $gain    = (float) ($r['total_mois'] ?? 0);
            $rows[] = ['label' => mois_label($mm), 't_conc' => $t_conc, 'kg' => $kg,
                       'ristourne' => $rist, 'commission' => $comm, 'gain' => $gain];
            $tot['t_conc']     += $t_conc;
            $tot['kg']         += $kg;
            $tot['ristourne']  += $rist;
            $tot['commission'] += $comm;
            $tot['montant']    += $gain;
        }
        $tiers  = (string) $cl['tiers'];
        $agence = (string) $cl['agence'];
        $uuid   = qr_uuid($tiers, $agence, $annee);
        $docs[] = [
            'id'             => (int) $cl['id'],
            'tiers'          => $tiers,
            'agence'         => $agence,
            'code'           => (string) $cl['code'],
            'code_fallback'  => (int) $cl['code_fallback'],
            'periode'        => $periode,
            'rows'           => $rows,
            'tot'            => $tot,
            'uuid'           => $uuid,
            /* QR en code court (17 car.) : N° + empreinte Ed25519 — voir inc/signature.php.
               Saisissable dans le formulaire de vérification ; l'appli recale
               l'empreinte attendue et détecte toute falsification. */
            'qr'             => qr_code_court($tiers, $agence, $annee, $tot['montant'], $uuid),
        ];
    }
    return ['annee' => $annee, 'mois' => $mois, 'periode' => $periode,
            'avec_cheques' => $avec_cheques, 'avec_listings' => $avec_listings,
            'docs' => $docs];
}

/* ---------------------------------------------------------------
 * Blocs communs des documents
 * --------------------------------------------------------------- */
function render_entete(array $d, array $cfg, string $titre): void
{
    ?>
    <header class="entete">
      <div class="entete-logo">
        <?php if ($cfg['logo']): ?><img src="<?= e($cfg['logo']) ?>" alt="logo"><?php endif; ?>
      </div>
      <div class="entete-infos">
        <div class="nom"><?= e($cfg['nom']) ?></div>
        <?php if ($cfg['slogan'] !== '' && $cfg['slogan'] !== '…'): ?><div class="slogan"><?= e($cfg['slogan']) ?></div><?php endif; ?>
        <?php foreach ($cfg['adresse'] as $l): if ($l !== '' && $l !== '…'): ?><div><?= e($l) ?></div><?php endif; endforeach; ?>
        <?php
        // Tél + email sur une ligne, RC + NIU sur une ligne (gain de hauteur)
        $tel = ($cfg['tel'] !== '' && $cfg['tel'] !== '…') ? $cfg['tel'] : '';
        $mail = ($cfg['email'] !== '' && $cfg['email'] !== '…') ? $cfg['email'] : '';
        $rc = ($cfg['rc'] !== '' && $cfg['rc'] !== '…') ? 'RC : ' . $cfg['rc'] : '';
        $niu = ($cfg['niu'] !== '' && $cfg['niu'] !== '…') ? 'NIU : ' . $cfg['niu'] : '';
        $ligTel = trim($tel . ($tel !== '' && $mail !== '' ? ' — ' : '') . $mail);
        $ligId = trim($rc . ($rc !== '' && $niu !== '' ? ' — ' : '') . $niu);
        ?>
        <?php if ($ligTel !== ''): ?><div><?= e($ligTel) ?></div><?php endif; ?>
        <?php if ($ligId !== ''): ?><div><?= e($ligId) ?></div><?php endif; ?>
      </div>
      <div class="entete-titre">
        <div class="titre"><?= e($titre) ?></div>
        <div class="docno">N° <?= e(substr($d['uuid'], 0, 8)) ?></div>
        <div class="docdate">Édité le <?= date('d/m/Y') ?></div>
      </div>
    </header>
    <?php
}

function render_pied(array $d, array $cfg): void
{
    ?>
    <footer class="pied">
      <div class="pied-lignes">
        <?php foreach ($cfg['pied'] as $l): if ($l !== '' && $l !== '…'): ?><div><?= e($l) ?></div><?php endif; endforeach; ?>
      </div>
      <div class="pied-uuid">Document généré le <?= date('d/m/Y à H:i') ?> · UUID <?= e($d['uuid']) ?></div>
    </footer>
    <?php
}

/* ---------------------------------------------------------------
 * Documents
 * --------------------------------------------------------------- */
function render_cheque(array $d, array $cfg): void
{
    ?>
    <div class="doc cheque" data-uuid="<?= e($d['uuid']) ?>" data-tiers="<?= e($d['tiers']) ?>">
      <?php render_entete($d, $cfg, $cfg['titre_cheque']); ?>
      <div class="corps">
        <div class="ligne-ordre">Payez contre ce chèque, à l'ordre de :</div>
        <div class="ligne-client"><?= e(up($d['tiers'])) ?>
          <span class="code">(Code : <?= e($d['code']) ?><?= $d['code_fallback'] ? ' *' : '' ?>)</span></div>
        <div class="ligne">Agence : <b><?= e($d['agence']) ?></b></div>
        <div class="ligne">Période de paiement : <b><?= e($d['periode']) ?></b></div>
        <div class="ligne-somme">La somme de : <em><?= e(montant_lettres($d['tot']['montant'])) ?></em></div>
        <?php $rep = split_complements($d['tot']['montant'], $cfg['complements']); ?>
        <table class="repartition">
          <tbody>
            <tr>
              <td>COMPLÉMENTS ALIMENTAIRES (<?= (int) $cfg['complements']['pct'] ?> %) :</td>
              <td class="num"><?= fmt_f($rep['complements']) ?> BLP</td>
            </tr>
            <tr>
              <td>Ristournes + Commissions sur Achat :</td>
              <td class="num"><?= fmt_f($rep['reste']) ?> BLP</td>
            </tr>
          </tbody>
        </table>
        <div class="ligne-montant"><span class="val"><?= fmt_f($d['tot']['montant']) ?> <small>BLP</small></span></div>
        <?php if ($cfg['banque'] !== '' && $cfg['banque'] !== '…'): ?>
          <div class="ligne-banque"><?= e($cfg['banque']) ?></div>
        <?php endif; ?>
        <div class="nb">
          <b>N.B.</b> — Ce chèque n'est pas un moyen de paiement financier : il donne droit à des
          <b>produits</b> pour un montant exprimé en <b>BLP</b> (BELGO LIVESTOCK PRODUCTS),
          <b>1 BLP = 1 FCFA</b>. Le montant est réglé pour <?= (int) $cfg['complements']['pct'] ?> % en
          COMPLÉMENTS ALIMENTAIRES et pour le solde en produits (Concentrés) au titre
          « Ristournes + Commissions sur Achat », conformément à la procédure de ristournes en vigueur.
        </div>
      </div>
      <div class="bas">
        <div class="signatures">
          <?php foreach ($cfg['signatures'] as $s): ?>
            <div class="sig"><div class="sig-label"><?= e($s) ?></div><div class="sig-espace">Signature</div></div>
          <?php endforeach; ?>
        </div>
        <div class="qr-bloc">
          <div class="qr" data-qr="<?= e($d['qr']) ?>"></div>
          <div class="qr-code"><?= e($d['qr']) ?></div>
        </div>
      </div>
      <?php render_pied($d, $cfg); ?>
    </div>
    <?php
}

function render_listing(array $d, array $cfg): void
{
    ?>
    <div class="doc listing" data-uuid="<?= e($d['uuid']) ?>" data-tiers="<?= e($d['tiers']) ?>">
      <?php render_entete($d, $cfg, $cfg['titre_listing']); ?>
      <div class="resume">
        <div>Client : <b><?= e($d['tiers']) ?></b>
          <span class="code">(Code : <?= e($d['code']) ?><?= $d['code_fallback'] ? ' *' : '' ?>)</span></div>
        <div>Agence : <b><?= e($d['agence']) ?></b> · Période : <b><?= e($d['periode']) ?></b></div>
      </div>
      <div class="tables">
        <table class="tab">
          <caption>ACHATS</caption>
          <thead><tr><th>Mois</th><th class="num">Concentrés (T)</th><th class="num">Autres (kg)</th></tr></thead>
          <tbody>
            <?php foreach ($d['rows'] as $r): ?>
              <tr><td><?= e($r['label']) ?></td>
                  <td class="num"><?= fmt_dec($r['t_conc']) ?></td>
                  <td class="num"><?= fmt_dec($r['kg'], 1) ?></td></tr>
            <?php endforeach; ?>
            <tr class="tot"><td>Total</td>
                <td class="num"><?= fmt_dec($d['tot']['t_conc']) ?></td>
                <td class="num"><?= fmt_dec($d['tot']['kg'], 1) ?></td></tr>
          </tbody>
        </table>
        <table class="tab">
          <caption>GAINS (BLP)</caption>
          <thead><tr><th>Mois</th><th class="num">Ristourne</th><th class="num">Commission</th><th class="num">Gain</th></tr></thead>
          <tbody>
            <?php foreach ($d['rows'] as $r): ?>
              <tr><td><?= e($r['label']) ?></td>
                  <td class="num"><?= fmt_f($r['ristourne']) ?></td>
                  <td class="num"><?= fmt_f($r['commission']) ?></td>
                  <td class="num"><?= fmt_f($r['gain']) ?></td></tr>
            <?php endforeach; ?>
            <tr class="tot"><td>Total</td>
                <td class="num"><?= fmt_f($d['tot']['ristourne']) ?></td>
                <td class="num"><?= fmt_f($d['tot']['commission']) ?></td>
                <td class="num"><?= fmt_f($d['tot']['montant']) ?></td></tr>
          </tbody>
        </table>
      </div>
      <div class="mention-bcp">Montants en BLP (BELGO LIVESTOCK PRODUCTS) — 1 BLP = 1 FCFA — paiement en produits, sans valeur financière.</div>
      <div class="ligne-somme">La somme de : <em><?= e(montant_lettres($d['tot']['montant'])) ?></em></div>
      <div class="ligne-montant"><span class="val"><?= fmt_f($d['tot']['montant']) ?> <small>BLP</small></span></div>
      <div class="bas">
        <div class="signatures">
          <?php foreach ($cfg['signatures'] as $s): ?>
            <div class="sig"><div class="sig-label"><?= e($s) ?></div><div class="sig-espace">Signature</div></div>
          <?php endforeach; ?>
        </div>
        <div class="qr-bloc">
          <div class="qr" data-qr="<?= e($d['qr']) ?>"></div>
          <div class="qr-code"><?= e($d['qr']) ?></div>
        </div>
      </div>
      <?php render_pied($d, $cfg); ?>
    </div>
    <?php
}

/* ---------------------------------------------------------------
 * Page enveloppe (formulaire ou documents)
 * --------------------------------------------------------------- */
function page_debut(string $titre): void
{
    ?><!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= e($titre) ?></title>
<link rel="stylesheet" href="assets/app.css">
<script src="assets/qrcode.min.js"></script>
<script src="assets/app.js" defer></script>
</head>
<body>
<?php
}

function page_fin(): void
{
    ?></body></html><?php
}

/* ---------------------------------------------------------------
 * Formulaire
 * --------------------------------------------------------------- */
function render_form(): void
{
    $db = db();
    $annees = $db->query('SELECT DISTINCT substr(mois,1,4) FROM detail ORDER BY 1')
                 ->fetchAll(PDO::FETCH_COLUMN);
    $annee = (int) ($_GET['annee'] ?? (int) end($annees));
    if (!in_array((string) $annee, $annees, true)) {
        $annee = (int) end($annees);
    }
    $mois_db = $db->query("SELECT DISTINCT mois FROM detail WHERE mois LIKE '$annee-%' ORDER BY mois")
                  ->fetchAll(PDO::FETCH_COLUMN);
    $mois = (string) ($_GET['mois'] ?? 'all');
    if ($mois !== 'all' && !in_array($mois, $mois_db, true)) {
        $mois = 'all';
    }
    $sel = in_array($_GET['sel'] ?? 'tous', ['tous', 'un', 'liste'], true) ? $_GET['sel'] : 'tous';
    $cheques  = ($_GET['cheques'] ?? '1') !== '0';
    $listings = ($_GET['listings'] ?? '1') !== '0';
    $ids_presel = [];
    if ($sel !== 'tous') {
        $bruts = $sel === 'un' ? [$_GET['id'] ?? ''] : explode(',', (string) ($_GET['ids'] ?? ''));
        foreach ($bruts as $b) {
            if (ctype_digit(trim($b))) {
                $ids_presel[] = (int) trim($b);
            }
        }
    }
    $clients = $db->query('SELECT rowid AS id, code, tiers, agence FROM clients
                           ORDER BY tiers COLLATE NOCASE, agence')->fetchAll();
    /* Badges du suivi des impressions : lecture seule (aucun qr_uuid() ici —
       il insère ; les badges ne couvrent que les documents déjà édités) */
    $stats = suivi_stats_par_client();

    page_debut('Édition chèques & listings — Ristournes');
    ?>
    <div class="wrap-form">
      <h1>Chèques &amp; listings de ristournes</h1>
      <p class="sous-titre">BELGOCAM S.A. — édition des chèques et listings d'achat · format A4 portrait, 2 documents par page (½ A4 chacun)</p>

      <form id="filtres" method="get" action="index.php">
        <input type="hidden" name="p" value="apercu">
        <input type="hidden" name="id" value="">
        <input type="hidden" name="ids" value="">

        <fieldset>
          <legend>Période de paiement</legend>
          <div class="ligne-champs">
            <label>Année
              <select name="annee">
                <?php foreach ($annees as $a): ?>
                  <option value="<?= e($a) ?>" <?= (int) $a === $annee ? 'selected' : '' ?>><?= e($a) ?></option>
                <?php endforeach; ?>
              </select>
            </label>
            <label>Mois
              <select name="mois">
                <option value="all" <?= $mois === 'all' ? 'selected' : '' ?>>Toute l'année</option>
                <?php foreach ($mois_db as $mm): ?>
                  <option value="<?= e($mm) ?>" <?= $mm === $mois ? 'selected' : '' ?>><?= e(mois_label($mm)) ?></option>
                <?php endforeach; ?>
              </select>
            </label>
          </div>
        </fieldset>

        <fieldset>
          <legend>Documents à éditer</legend>
          <div class="ligne-champs">
            <label class="case"><input type="checkbox" name="cheques" value="1" <?= $cheques ? 'checked' : '' ?>> Chèques</label>
            <label class="case"><input type="checkbox" name="listings" value="1" <?= $listings ? 'checked' : '' ?>> Listings d'achat</label>
          </div>
        </fieldset>

        <fieldset>
          <legend>Clients</legend>
          <div class="ligne-champs">
            <label class="case"><input type="radio" name="sel" value="tous" <?= $sel === 'tous' ? 'checked' : '' ?>> Tous les clients</label>
            <label class="case"><input type="radio" name="sel" value="un" <?= $sel === 'un' ? 'checked' : '' ?>> Un client</label>
            <label class="case"><input type="radio" name="sel" value="liste" <?= $sel === 'liste' ? 'checked' : '' ?>> Une liste de clients</label>
          </div>
          <div id="picker" <?= $sel === 'tous' ? 'hidden' : '' ?>>
            <div class="picker-bar">
              <input type="text" id="filtre" placeholder="Filtrer par code, nom ou agence…">
              <span id="compteur">Aucun client sélectionné</span>
              <span class="spacer"></span>
              <button type="button" class="btn-mini" id="btn-tous">Tout</button>
              <button type="button" class="btn-mini" id="btn-aucun">Aucun</button>
            </div>
            <div class="picklist" id="liste-clients">
              <?php foreach ($clients as $c): $q = function_exists('mb_strtolower') ? mb_strtolower($c['code'] . ' ' . $c['tiers'] . ' ' . $c['agence'], 'UTF-8') : strtolower($c['code'] . ' ' . $c['tiers'] . ' ' . $c['agence']); $cle = $c['tiers'] . '|' . $c['agence']; ?>
                <label data-q="<?= e($q) ?>">
                  <input type="checkbox" name="choix[]" value="<?= (int) $c['id'] ?>"
                         <?= in_array((int) $c['id'], $ids_presel, true) ? 'checked' : '' ?>>
                  <span class="code"><?= e($c['code']) ?></span>
                  <span class="tiers"><?= e($c['tiers']) ?></span>
                  <span class="ag"><?= e($c['agence']) ?></span>
                  <span class="imp" title="Impressions : directes · échecs · PDF"
                        data-imp="<?= e(json_encode($stats[$cle] ?? new stdClass(), JSON_UNESCAPED_UNICODE)) ?>"><?= e(badge_imp($stats[$cle][$annee] ?? null)) ?></span>
                </label>
              <?php endforeach; ?>
            </div>
            <p class="note-picker">
              En mode « Un client » : un seul choix possible. En mode « Une liste » : plusieurs choix possibles.
              Les deux documents (chèque + listing) d'un même client partagent le même code QR.
            </p>
          </div>
        </fieldset>

        <div class="barre-actions">
          <button type="submit" class="btn-principal">Générer l'aperçu</button>
        </div>
      </form>
    </div>
    <?php
    page_fin();
}

/* ---------------------------------------------------------------
 * Aperçu / impression
 * --------------------------------------------------------------- */
function render_documents(array $res, bool $auto_print): void
{
    $docs = $res['docs'];
    $n_docs = count($docs) * ($res['avec_cheques'] + $res['avec_listings']);
    page_debut('Aperçu — chèques & listings');
    ?>
    <div class="toolbar">
      <a class="lien-retour" href="index.php?p=form&amp;annee=<?= (int) $res['annee'] ?>&amp;mois=<?= e($res['mois']) ?>&amp;sel=<?= e($_GET['sel'] ?? 'tous') ?>&amp;id=<?= e($_GET['id'] ?? '') ?>&amp;ids=<?= e($_GET['ids'] ?? '') ?>&amp;cheques=<?= $res['avec_cheques'] ? '1' : '0' ?>&amp;listings=<?= $res['avec_listings'] ? '1' : '0' ?>">← Retour au formulaire</a>
      <a class="lien-retour" href="index.php?p=verifier">🔎 Vérifier un document</a>
      <a class="lien-retour" href="index.php?p=suivi&amp;annee=<?= (int) $res['annee'] ?>">📊 Suivi des impressions</a>
      <span class="tb-info"><?= count($docs) ?> client(s) · <?= $n_docs ?> document(s) · <?= e($res['periode']) ?></span>
      <span class="spacer"></span>
      <button class="btn-principal" onclick="lancerImpression()">🖨 Imprimer (Ctrl+P)</button>
      <a class="btn-pdf" data-action-pdf="1" data-nom="<?= (int) $res['annee'] ?>"
         title="Génère le PDF via le navigateur (peut prendre quelques secondes pour les gros lots)"
         href="index.php?p=pdf&amp;annee=<?= (int) $res['annee'] ?>&amp;mois=<?= e($res['mois']) ?>&amp;sel=<?= e($_GET['sel'] ?? 'tous') ?>&amp;id=<?= e($_GET['id'] ?? '') ?>&amp;ids=<?= e($_GET['ids'] ?? '') ?>&amp;cheques=<?= $res['avec_cheques'] ? '1' : '0' ?>&amp;listings=<?= $res['avec_listings'] ? '1' : '0' ?>">⬇ Télécharger PDF</a>
    </div>
    <?php if (!$docs): ?>
      <div class="vide">Aucun client sur cette période.</div>
    <?php else: ?>
      <?php
      /* Regroupement 2 documents par feuille A4 portrait (½ A4 chacun) */
      $parts = [];
      foreach ($docs as $d) {
          if ($res['avec_cheques']) {
              ob_start();
              render_cheque($d, $GLOBALS['cfg']);
              $parts[] = ob_get_clean();
          }
          if ($res['avec_listings']) {
              ob_start();
              render_listing($d, $GLOBALS['cfg']);
              $parts[] = ob_get_clean();
          }
      }
      foreach (array_chunk($parts, 2) as $paire): ?>
        <div class="feuille"><?= implode('', $paire) ?></div>
      <?php endforeach; ?>
    <?php endif; ?>
    <?php if ($auto_print): ?>
      <script>window.__autoPrint = true;</script>
    <?php endif; ?>
    <?php
    page_fin();
}

/* ---------------------------------------------------------------
 * Export PDF : rendu par le navigateur installé (Edge/Chrome) en
 * mode headless, à partir de la MÊME page d'aperçu — le CSS @page
 * A4 portrait (2 documents par page) s'applique donc à l'identique,
 * QR compris.
 * --------------------------------------------------------------- */
function trouver_navigateur(): ?string
{
    foreach ([
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
        'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    ] as $p) {
        if (is_file($p)) {
            return $p;
        }
    }
    return null;
}

function render_pdf(): void
{
    if (!function_exists('exec')) {
        http_response_code(500);
        echo "La fonction exec() de PHP est désactivée : utilisez l'aperçu puis Ctrl+P → « Enregistrer au format PDF ».";
        return;
    }
    $exe = trouver_navigateur();
    if ($exe === null) {
        http_response_code(500);
        echo "Navigateur introuvable pour la génération PDF. Utilisez l'aperçu puis Ctrl+P → « Enregistrer au format PDF ».";
        return;
    }
    /* Le serveur intégré de PHP est mono-thread : le navigateur headless ne peut
       pas rappeler http://localhost pendant la requête PDF. On écrit donc
       l'aperçu dans un fichier HTML temporaire (assets en file://) et on
       imprime ce fichier — même rendu, aucun aller-retour réseau. */
    $res = charger_documents();
    ob_start();
    render_documents($res, false);
    $html = ob_get_clean();
    /* CSS et JS inlinés : une page HTML locale ne peut pas charger ses
       sous-ressources en mode headless (PDF vide ou non stylé). */
    $css = file_get_contents(__DIR__ . '/assets/app.css');
    $jsQr = file_get_contents(__DIR__ . '/assets/qrcode.min.js');
    $js = file_get_contents(__DIR__ . '/assets/app.js');
    $html = str_replace(
        ['<link rel="stylesheet" href="assets/app.css">',
         '<script src="assets/qrcode.min.js"></script>',
         '<script src="assets/app.js" defer></script>'],
        ['<style>' . $css . '</style>',
         '<script>' . $jsQr . '</script>',
         '<script>' . $js . '</script>'],
        $html);
    $dirHtml = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'bcp_html';
    if (!is_dir($dirHtml)) {
        mkdir($dirHtml, 0777, true);
    }
    $fhtml = $dirHtml . DIRECTORY_SEPARATOR . 'apercu_' . bin2hex(random_bytes(6)) . '.html';
    file_put_contents($fhtml, $html);
    $pdf = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'bcp_' . bin2hex(random_bytes(6)) . '.pdf';
    $profil = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'bcp-headless';
    $urlFichier = 'file:///' . str_replace(['\\', ' '], ['/', '%20'], $fhtml);
    $out = [];
    for ($essai = 0; $essai < 3 && (!is_file($pdf) || filesize($pdf) < 500); $essai++) {
        if ($essai > 0) {
            @unlink($pdf);
        }
        $cmd = '"' . $exe . '" --headless=new --disable-gpu --no-pdf-header-footer'
             . ' --no-first-run --no-default-browser-check --disable-background-networking'
             . ' --user-data-dir="' . $profil . ($essai > 0 ? '-' . $essai : '') . '"'
             . ' --print-to-pdf="' . $pdf . '" "' . $urlFichier . '"';
        exec($cmd . ' 2>&1', $out, $code);
    }
    $attendu = 0;
    while (!is_file($pdf) || filesize($pdf) < 500) {
        usleep(250000);
        $attendu += 250;
        if ($attendu > 120000) {
            http_response_code(500);
            echo 'La génération du PDF a dépassé le délai de 3 minutes. Détail : '
               . ($out ? e(implode("\n", array_slice($out, -3))) : 'aucun');
            @unlink($pdf);
            @unlink($fhtml);
            return;
        }
    }
    /* Suivi : le PDF est généré et téléchargé — écriture d'audit (delta 0).
       La confirmation d'impression est demandée côté navigateur. */
    foreach ($res['docs'] as $d) {
        suivi_log((string) $d['uuid'], 'pdf', 'telecharge', 0);
    }
    $nom = 'Ristournes_' . ((int) ($_GET['annee'] ?? 2025)) . '_BLP.pdf';
    header('Content-Type: application/pdf');
    header('Content-Disposition: attachment; filename="' . $nom . '"');
    header('Content-Length: ' . filesize($pdf));
    readfile($pdf);
    @unlink($pdf);
    @unlink($fhtml);
}

/* ---------------------------------------------------------------
 * Suivi des impressions
 * --------------------------------------------------------------- */
function page_suivi(): void
{
    $q = db_qr();
    $annees = array_map('intval', $q->query('SELECT DISTINCT annee FROM qr ORDER BY annee DESC')
                                     ->fetchAll(PDO::FETCH_COLUMN));
    $annee = (int) ($_GET['annee'] ?? ($annees[0] ?? (int) date('Y')));
    if ($annees && !in_array($annee, $annees, true)) {
        $annee = $annees[0];
    }

    /* code + rowid des clients (base ristournes) pour libellés et lien Aperçu */
    $codePar = $idPar = [];
    foreach (db()->query('SELECT rowid AS id, tiers, agence, code FROM clients')->fetchAll() as $c) {
        $cle = $c['tiers'] . '|' . $c['agence'];
        $codePar[$cle] = $c['code'];
        $idPar[$cle] = (int) $c['id'];
    }

    $lignes = [];
    foreach (suivi_stats_par_client() as $cle => $parAnnee) {
        if (!isset($parAnnee[$annee])) {
            continue;
        }
        $s = $parAnnee[$annee];
        [$tiers, $agence] = explode('|', $cle, 2);
        $lignes[] = [
            'tiers' => $tiers, 'agence' => $agence,
            'code' => $codePar[$cle] ?? '',
            'id' => $idPar[$cle] ?? 0,
            'uuid' => (string) $s['uuid'],
            'directe' => $s['directe'], 'pdf' => $s['pdf'],
            'echecs' => $s['echecs'], 'dernier' => $s['dernier'],
        ];
    }
    usort($lignes, function (array $a, array $b): int {
        return strcasecmp($a['tiers'], $b['tiers']) ?: strcasecmp($a['agence'], $b['agence']);
    });
    $histo = suivi_histo();

    page_debut('Suivi des impressions — Ristournes');
    ?>
    <div class="toolbar">
      <a class="lien-retour" href="index.php?p=form">← Retour au formulaire</a>
      <a class="lien-retour" href="index.php?p=apercu">Aperçu →</a>
      <span class="spacer"></span>
    </div>
    <div class="wrap-suivi">
      <h1>📊 Suivi des impressions</h1>
      <p class="sous-titre">Compteurs par document (chèque + listing partagent le même compteur).
        Les corrections (−1, réinitialisation) sont écrites en négatif dans l'historique : rien n'est effacé.</p>
      <form method="get" action="index.php" class="ligne-annees">
        <input type="hidden" name="p" value="suivi">
        <label>Année
          <select name="annee" onchange="this.form.submit()">
            <?php foreach ($annees as $a): ?>
              <option value="<?= $a ?>" <?= $a === $annee ? 'selected' : '' ?>><?= $a ?></option>
            <?php endforeach; ?>
          </select>
        </label>
      </form>
      <?php if (!$lignes): ?>
        <div class="vide">Aucune impression enregistrée pour cette année.</div>
      <?php else: ?>
        <table class="tab suivi-tab">
          <thead><tr>
            <th>Code</th><th>Client</th><th>Agence</th>
            <th class="num">🖨 Directes</th><th class="num">✗ Échecs/annulées</th><th class="num">📄 PDF</th>
            <th>Dernière impression</th><th>Actions</th>
          </tr></thead>
          <tbody>
            <?php foreach ($lignes as $l): ?>
              <tr data-ligne data-uuid="<?= e($l['uuid']) ?>">
                <td><?= e($l['code']) ?></td>
                <td><?= e($l['tiers']) ?></td>
                <td><?= e($l['agence']) ?></td>
                <td class="num"><?= $l['directe'] ?></td>
                <td class="num"><?= $l['echecs'] ?></td>
                <td class="num"><?= $l['pdf'] ?></td>
                <td class="mineur"><?= e(str_replace('T', ' ', $l['dernier'])) ?></td>
                <td class="actions">
                  <button class="btn-mini" data-ajuster data-type="directe" <?= $l['directe'] <= 0 ? 'disabled' : '' ?>>−1 directe</button>
                  <button class="btn-mini" data-reset data-type="directe" <?= $l['directe'] <= 0 ? 'disabled' : '' ?>>réinit directe</button>
                  <button class="btn-mini" data-ajuster data-type="pdf" <?= $l['pdf'] <= 0 ? 'disabled' : '' ?>>−1 PDF</button>
                  <button class="btn-mini" data-reset data-type="pdf" <?= $l['pdf'] <= 0 ? 'disabled' : '' ?>>réinit PDF</button>
                  <?php if ($l['id']): ?>
                    <a class="btn-mini" href="index.php?p=apercu&amp;annee=<?= $annee ?>&amp;mois=all&amp;sel=un&amp;id=<?= $l['id'] ?>&amp;cheques=1&amp;listings=1">Aperçu</a>
                  <?php endif; ?>
                </td>
              </tr>
            <?php endforeach; ?>
            <tr class="tot">
              <td colspan="3">Total — <?= count($lignes) ?> document(s)</td>
              <td class="num"><?= array_sum(array_column($lignes, 'directe')) ?></td>
              <td class="num"><?= array_sum(array_column($lignes, 'echecs')) ?></td>
              <td class="num"><?= array_sum(array_column($lignes, 'pdf')) ?></td>
              <td colspan="2"></td>
            </tr>
          </tbody>
        </table>
      <?php endif; ?>

      <h2>Historique récent</h2>
      <?php if (!$histo): ?>
        <div class="vide">Aucun événement.</div>
      <?php else: ?>
        <table class="tab">
          <thead><tr><th>Moment</th><th>Document</th><th>Type</th><th>Statut</th><th>Δ</th><th>Note</th></tr></thead>
          <tbody>
            <?php foreach ($histo as $h): $lab = $h['label']; ?>
              <tr>
                <td class="mineur"><?= e(str_replace('T', ' ', (string) $h['moment'])) ?></td>
                <td><?= $lab ? e($lab['tiers'] . ' — ' . $lab['agence'] . ' (' . $lab['annee'] . ')') : e((string) $h['uuid']) ?></td>
                <td><?= $h['type'] === 'directe' ? '🖨 directe' : '📄 PDF' ?></td>
                <td><?= e((string) $h['statut']) ?></td>
                <td class="num"><?= $h['delta'] > 0 ? '+' . $h['delta'] : $h['delta'] ?></td>
                <td class="mineur"><?= e((string) $h['note']) ?></td>
              </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      <?php endif; ?>
    </div>
    <script>
    /* Actions −1 / réinitialiser : POST JSON, puis rechargement de la page */
    document.querySelectorAll('.suivi-tab [data-ajuster], .suivi-tab [data-reset]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var action = btn.hasAttribute('data-reset') ? 'reset' : 'ajuster';
        if (action === 'reset' && !confirm('Réinitialiser ce compteur à zéro ? L\'opération restera visible dans l\'historique.')) { return; }
        btn.disabled = true;
        fetch('index.php?p=suivi_api', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: action,
            uuid: btn.closest('tr').getAttribute('data-uuid'),
            type: btn.getAttribute('data-type')
          })
        }).then(function (r) { return r.json(); })
          .then(function (res) {
            if (!res.ok) { alert('Opération refusée : ' + (res.message || 'erreur inconnue')); btn.disabled = false; return; }
            location.reload();
          })
          .catch(function () { alert('Erreur réseau — opération non appliquée.'); btn.disabled = false; });
      });
    });
    </script>
    <?php
    page_fin();
}

/* ---------------------------------------------------------------
 * Vérification d'un document (code scanné ou N° tapé)
 * --------------------------------------------------------------- */

/** Analyse un code saisi : code court du QR (N° + empreinte, 17 car.),
 *  chaîne signée complète historique (B1.…) ou N° de document. */
function verifier_code(string $code): array
{
    $code = trim($code);
    /* Code court du QR : N° (8 car. hexa) + empreinte cryptographique (8 car.) */
    if (preg_match('/^([0-9a-f]{8})-([A-Za-z0-9_-]{8})$/i', $code, $m)) {
        return verif_par_empreinte(strtolower($m[1]), $m[2]);
    }
    /* [url#]B1.<données b64url>.<signature b64url> */
    if (preg_match('/^(?:https?:\/\/[^#]*#)?(B1)\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)$/', $code, $m)) {
        try {
            $json = @gzinflate(b64url_decode($m[2]));
            if ($json === false) {
                return ['statut' => 'invalide', 'message' => 'Code endommagé ou illisible.'];
            }
            if (!sodium_crypto_sign_verify_detached(b64url_decode($m[3]), $json, sign_public_key())) {
                return ['statut' => 'invalide',
                        'message' => 'Signature invalide — ce document n’est PAS authentique (contrefaçon ou falsification).'];
            }
            $d = json_decode($json, true);
            if (!is_array($d) || !isset($d['t'], $d['a'], $d['y'], $d['m'], $d['u'])) {
                return ['statut' => 'invalide', 'message' => 'Signature valide mais contenu illisible.'];
            }
            return verif_par_uuid(uuid_etendre((string) $d['u']), [
                't' => (string) $d['t'], 'a' => (string) $d['a'],
                'y' => (int) $d['y'], 'm' => (int) $d['m'],
            ]);
        } catch (Throwable $e) {
            return ['statut' => 'invalide', 'message' => 'Code endommagé ou illisible.'];
        }
    }
    if (preg_match('/^[A-Za-z0-9_-]{22}$/', $code)) {
        return verif_par_uuid(uuid_etendre($code), null);
    }
    if (preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $code)) {
        return verif_par_uuid(strtolower($code), null);
    }
    /* N° court : les 8 premiers caractères imprimés en haut à droite du document */
    if (preg_match('/^[0-9a-f]{8}$/i', $code)) {
        return verif_par_prefixe(strtolower($code));
    }
    return ['statut' => 'format',
            'message' => 'Code non reconnu : collez la chaîne complète du QR ou tapez le N° du document.'];
}

/** Code court du QR (N° + empreinte) : retrouve le document par préfixe puis
 *  recalcule l'empreinte attendue (signature Ed25519 du payload en base) et la
 *  compare — une empreinte qui ne correspond pas signale un QR falsifié ou un
 *  document modifié depuis son impression. */
function verif_par_empreinte(string $prefixe, string $empreinte): array
{
    $st = db_qr()->prepare('SELECT tiers, agence, annee, uuid FROM qr WHERE uuid LIKE ?');
    $st->execute([$prefixe . '%']);
    $lignes = $st->fetchAll();
    if (!$lignes) {
        return ['statut' => 'format', 'message' => 'N° de document inconnu de la base.'];
    }
    /* Plusieurs documents partagent ce N° : l'empreinte départage le bon. */
    foreach ($lignes as $l) {
        $st2 = db()->prepare('SELECT total FROM clients WHERE tiers = ? AND agence = ?');
        $st2->execute([$l['tiers'], $l['agence']]);
        $c = $st2->fetch();
        $montant = $c ? (float) $c['total'] : 0.0;
        $attendu = qr_code_court((string) $l['tiers'], (string) $l['agence'],
                                 (int) $l['annee'], $montant, (string) $l['uuid']);
        if (hash_equals($prefixe . '-' . $empreinte, $attendu)) {
            return verif_par_uuid((string) $l['uuid'], [
                't' => (string) $l['tiers'], 'a' => (string) $l['agence'],
                'y' => (int) $l['annee'], 'm' => (int) round($montant),
            ]);
        }
    }
    if (count($lignes) === 1) {
        return ['statut' => 'invalide',
                'message' => 'Empreinte invalide — ce QR ne correspond pas au document enregistré (contrefaçon ou falsification).'];
    }
    return ['statut' => 'plusieurs', 'candidats' => $lignes];
}

/** N° court (8 caractères) : retrouve le document par préfixe.
 *  Rare, mais possible : plusieurs documents partagent le même préfixe. */
function verif_par_prefixe(string $prefixe): array
{
    $st = db_qr()->prepare('SELECT tiers, agence, annee, uuid FROM qr WHERE uuid LIKE ?');
    $st->execute([$prefixe . '%']);
    $lignes = $st->fetchAll();
    if (count($lignes) === 1) {
        return verif_par_uuid($lignes[0]['uuid'], null);
    }
    if (!$lignes) {
        return ['statut' => 'format', 'message' => 'N° de document inconnu de la base.'];
    }
    return ['statut' => 'plusieurs', 'candidats' => $lignes];
}

/** Retrouve le document par son N° et le rapproche de la base clients. */
function verif_par_uuid(string $uuid, ?array $signe): array
{
    $out = [
        'statut' => $signe === null ? 'trouve' : 'valide',
        'uuid' => $uuid,
        'signe' => $signe,
        'tiers' => null, 'agence' => null, 'annee' => null,
        'client_id' => null, 'montant_base' => null,
    ];
    $st = db_qr()->prepare('SELECT tiers, agence, annee FROM qr WHERE uuid = ?');
    $st->execute([$uuid]);
    $r = $st->fetch();
    if ($r) {
        $out['tiers'] = (string) $r['tiers'];
        $out['agence'] = (string) $r['agence'];
        $out['annee'] = (int) $r['annee'];
        $st2 = db()->prepare('SELECT rowid, total FROM clients WHERE tiers = ? AND agence = ?');
        $st2->execute([$r['tiers'], $r['agence']]);
        $c = $st2->fetch();
        if ($c) {
            $out['client_id'] = (int) $c['rowid'];
            $out['montant_base'] = (float) $c['total'];
        }
    }
    return $out;
}

/** Rendu du résultat + ré-affichage du document concerné pour comparaison. */
function render_verif_resultat(array $res): void
{
    $uuid = isset($res['uuid']) ? uuid_etendre($res['uuid']) : '';
    if ($res['statut'] === 'valide') {
        $s = $res['signe'];
        $ecart = ($res['montant_base'] !== null && (int) round($res['montant_base']) !== (int) $s['m']);
        ?>
        <div class="verif-card ok">
          <div class="titre">✓ Document authentique — signature numérique vérifiée</div>
          <table>
            <tr><td>Bénéficiaire</td><td><b><?= e($s['t']) ?></b></td></tr>
            <tr><td>Agence</td><td><?= e($s['a']) ?></td></tr>
            <tr><td>Exercice</td><td><?= (int) $s['y'] ?></td></tr>
            <tr><td>Montant</td><td><b><?= fmt_f((float) $s['m']) ?> BLP</b></td></tr>
            <tr><td>N° du document</td><td><?= e($uuid) ?></td></tr>
          </table>
          <?php if ($res['tiers'] !== null): ?>
            <div class="conseil">Document retrouvé dans la base (<?= e($res['tiers']) ?>, <?= e($res['agence']) ?>) et affiché ci-dessous pour comparaison.</div>
          <?php else: ?>
            <div class="conseil">Document inconnu de la base locale — la signature reste valide.</div>
          <?php endif; ?>
          <?php if ($ecart): ?>
            <div class="avert">⚠ Le montant signé (<?= fmt_f((float) $s['m']) ?>) diffère du montant actuel en base (<?= fmt_f((float) $res['montant_base']) ?>) — vérifier la version du document.</div>
          <?php endif; ?>
        </div>
        <?php
    } elseif ($res['statut'] === 'trouve') {
        ?>
        <div class="verif-card moyen">
          <div class="titre">Document retrouvé — code court (sans signature)</div>
          <table>
            <tr><td>Bénéficiaire</td><td><b><?= e((string) $res['tiers']) ?></b></td></tr>
            <tr><td>Agence</td><td><?= e((string) $res['agence']) ?></td></tr>
            <tr><td>Exercice</td><td><?= (int) $res['annee'] ?></td></tr>
            <tr><td>Montant en base</td><td><b><?= fmt_f((float) $res['montant_base']) ?> BLP</b></td></tr>
            <tr><td>N° du document</td><td><?= e($uuid) ?></td></tr>
          </table>
          <div class="avert">Ce code n'est pas une preuve cryptographique : comparez visuellement le document ci-dessous avec le papier.</div>
        </div>
        <?php
    } elseif ($res['statut'] === 'plusieurs') {
        ?>
        <div class="verif-card moyen">
          <div class="titre">Plusieurs documents correspondent à ce N°</div>
          <table>
            <?php foreach ($res['candidats'] as $c): ?>
            <tr>
              <td><?= e((string) $c['tiers']) ?> — <?= e((string) $c['agence']) ?> (<?= (int) $c['annee'] ?>)</td>
              <td><a href="index.php?p=verifier&amp;code=<?= e((string) $c['uuid']) ?>">Ouvrir →</a></td>
            </tr>
            <?php endforeach; ?>
          </table>
          <div class="conseil">Choisissez le document qui correspond au papier.</div>
        </div>
        <?php
        return;
    } elseif ($res['statut'] === 'invalide') {
        ?>
        <div class="verif-card ko">
          <div class="titre">✗ <?= e($res['message']) ?></div>
          <div class="conseil">Si ce code provient d'un document présenté comme original, contactez la direction avant tout paiement.</div>
        </div>
        <?php
        return;
    } else {
        ?>
        <div class="verif-card">
          <div class="titre"><?= e($res['message']) ?></div>
        </div>
        <?php
        return;
    }
    /* Ré-affichage du document pour comparaison visuelle */
    if ($res['client_id'] !== null) {
        $_GET['annee'] = (string) $res['annee'];
        $_GET['mois'] = 'all';
        $_GET['sel'] = 'un';
        $_GET['id'] = (string) $res['client_id'];
        $_GET['cheques'] = '1';
        $_GET['listings'] = '1';
        $vres = charger_documents();
        if ($vres['docs']) {
            $d = $vres['docs'][0];
            ob_start();
            render_cheque($d, $GLOBALS['cfg']);
            $ch = ob_get_clean();
            ob_start();
            render_listing($d, $GLOBALS['cfg']);
            $li = ob_get_clean();
            ?>
            <div class="feuille"><?= $ch . $li ?></div>
            <p class="note-picker">
              <a href="index.php?p=apercu&amp;annee=<?= (int) $res['annee'] ?>&amp;mois=all&amp;sel=un&amp;id=<?= (int) $res['client_id'] ?>&amp;cheques=1&amp;listings=1">Ouvrir l'aperçu complet de ce client →</a>
            </p>
            <?php
        }
    }
}

function page_verifier(): void
{
    $code = trim((string) ($_GET['code'] ?? ''));
    $res = $code === '' ? null : verifier_code($code);
    page_debut('Vérifier un document — Ristournes');
    ?>
    <div class="toolbar">
      <a class="lien-retour" href="index.php?p=form">← Retour au formulaire</a>
      <span class="spacer"></span>
      <a class="lien-retour" href="index.php?p=apercu">Aperçu →</a>
    </div>
    <div class="wrap-verif">
      <h1>🔎 Vérification d'un document</h1>
      <p class="sous-titre">Collez le code obtenu en scannant le QR du document, ou tapez le <b>N° du document</b> imprimé en haut à droite (8 caractères, ex. <code>3fa9c1d2</code>).</p>
      <form method="get" action="index.php">
        <input type="hidden" name="p" value="verifier">
        <textarea name="code" autofocus placeholder="Chaîne scannée (B1.…) ou N° du document…"><?= e($code) ?></textarea>
        <div class="barre-actions"><button type="submit" class="btn-principal">Vérifier</button></div>
      </form>
      <?php if ($res !== null) { render_verif_resultat($res); } ?>
    </div>
    <?php
    page_fin();
}

/* ---------------------------------------------------------------
 * Routage
 * --------------------------------------------------------------- */
$p = $_GET['p'] ?? 'form';
if ($p === 'form') {
    render_form();
} elseif ($p === 'pdf') {
    render_pdf();
} elseif ($p === 'apercu' || $p === 'imprimer') {
    render_documents(charger_documents(), $p === 'imprimer');
} elseif ($p === 'suivi') {
    page_suivi();
} elseif ($p === 'suivi_api') {
    header('Content-Type: application/json; charset=UTF-8');
    $req = json_decode((string) file_get_contents('php://input'), true);
    echo json_encode(suivi_action(is_array($req) ? $req : []), JSON_UNESCAPED_UNICODE);
} elseif ($p === 'verifier') {
    page_verifier();
} else {
    http_response_code(404);
    echo 'Page inconnue.';
}
