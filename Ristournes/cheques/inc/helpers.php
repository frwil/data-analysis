<?php
declare(strict_types=1);
/** Fonctions communes de l'application chèques/listings. */

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('sqlite:' . __DIR__ . '/../data/ristournes.sqlite');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    }
    return $pdo;
}

/** Base des QR : un uuid stable par (client, agence, année) — partagé entre chèque et listing. */
function db_qr(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO('sqlite:' . __DIR__ . '/../data/qr.sqlite');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->exec('CREATE TABLE IF NOT EXISTS qr (
            tiers TEXT NOT NULL, agence TEXT NOT NULL, annee INTEGER NOT NULL,
            uuid TEXT NOT NULL, PRIMARY KEY (tiers, agence, annee))');
    }
    return $pdo;
}

function uuid4(): string
{
    $b = random_bytes(16);
    $b[6] = chr((ord($b[6]) & 0x0f) | 0x40);
    $b[8] = chr((ord($b[8]) & 0x3f) | 0x80);
    $h = bin2hex($b);
    return substr($h, 0, 8) . '-' . substr($h, 8, 4) . '-' . substr($h, 12, 4)
         . '-' . substr($h, 16, 4) . '-' . substr($h, 20, 12);
}

function qr_uuid(string $tiers, string $agence, int $annee): string
{
    $q = db_qr();
    $st = $q->prepare('SELECT uuid FROM qr WHERE tiers = ? AND agence = ? AND annee = ?');
    $st->execute([$tiers, $agence, $annee]);
    $u = $st->fetchColumn();
    if ($u === false) {
        $u = uuid4();
        $q->prepare('INSERT INTO qr (tiers, agence, annee, uuid) VALUES (?, ?, ?, ?)')
          ->execute([$tiers, $agence, $annee, $u]);
    }
    return (string) $u;
}

function e(?string $s): string
{
    return htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8');
}

/* ---------------------------------------------------------------
 * Nombres en lettres (français)
 * --------------------------------------------------------------- */

function _unites(int $n): string
{
    static $u = ['zéro', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept',
                 'huit', 'neuf', 'dix', 'onze', 'douze', 'treize', 'quatorze',
                 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf'];
    return $u[$n];
}

function _sous_mille(int $n): string
{
    if ($n < 20) {
        return _unites($n);
    }
    if ($n < 100) {
        $d = intdiv($n, 10);
        $r = $n % 10;
        if ($d === 7) {
            return 'soixante' . ($r === 1 ? ' et onze' : '-' . _sous_mille(10 + $r));
        }
        if ($d === 9) {
            return 'quatre-vingt-' . _sous_mille(10 + $r);
        }
        if ($d === 8) {
            return $r === 0 ? 'quatre-vingts' : 'quatre-vingt-' . _unites($r);
        }
        $diz = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante'][$d];
        if ($r === 0) {
            return $diz;
        }
        return $diz . ($r === 1 ? ' et un' : '-' . _unites($r));
    }
    $c = intdiv($n, 100);
    $r = $n % 100;
    $s = $c === 1 ? 'cent' : _unites($c) . ' cent' . ($r === 0 ? 's' : '');
    return $r === 0 ? $s : $s . ' ' . _sous_mille($r);
}

function nombre_lettres(int $n): string
{
    if ($n === 0) {
        return 'zéro';
    }
    $parties = [];
    foreach ([['milliard', 1000000000], ['million', 1000000], ['mille', 1000]] as [$nom, $p]) {
        if ($n >= $p) {
            $q = intdiv($n, $p);
            $n %= $p;
            if ($nom === 'mille') {
                $parties[] = $q === 1 ? 'mille' : _sous_mille($q) . ' mille';
            } else {
                $parties[] = $q === 1 ? 'un ' . $nom : _sous_mille($q) . ' ' . $nom . 's';
            }
        }
    }
    if ($n > 0) {
        $parties[] = _sous_mille($n);
    }
    return implode(' ', $parties);
}

/** Montant en lettres, exprimé en BLP (BELGO LIVESTOCK PRODUCTS, 1 BLP = 1 FCFA). */
function montant_lettres(float $m): string
{
    $f = (int) floor($m + 1e-6);
    $c = (int) round(($m - floor($m)) * 100);
    $s = nombre_lettres($f) . ' BLP';
    if ($c > 0) {
        $s .= ' et ' . nombre_lettres($c) . ' centime' . ($c > 1 ? 's' : '');
    }
    return ucfirst($s);
}

/** Répartition du chèque : part COMPLÉMENTS ALIMENTAIRES (pourcentage borné
 *  entre min et max) et solde « Ristournes + Commissions sur Achat ».
 *  La part ne dépasse jamais le montant total. */
function split_complements(float $total, array $regle): array
{
    $comp = round($total * (float) $regle['pct'] / 100);
    $comp = max($comp, (float) $regle['min']);
    $comp = min($comp, (float) $regle['max'], $total);
    return ['complements' => $comp, 'reste' => round($total - $comp)];
}

/* ---------------------------------------------------------------
 * Formats d'affichage
 * --------------------------------------------------------------- */

/** 89264312 -> « 89 264 312 » */
function fmt_f(float $n): string
{
    return number_format(round($n), 0, ',', ' ');
}

/** 30.25 -> « 30,25 » ; 1225.0 -> « 1 225 » ; 0.5 -> « 0,5 » */
function fmt_dec(float $n, int $maxd = 2): string
{
    $s = number_format(round($n, $maxd), $maxd, ',', ' ');
    if (strpos($s, ',') !== false) {
        $s = rtrim(rtrim($s, '0'), ',');
    }
    return $s;
}

const MOIS_FR = [1 => 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

/** Libellé de la période : « Jan-Déc 2025 » ou « Juillet 2025 ». */
function periode_label(int $annee, ?string $mois): string
{
    if ($mois === null) {
        return 'Jan-Déc ' . $annee;
    }
    $m = (int) substr($mois, 5, 2);
    return ucfirst(MOIS_FR[$m]) . ' ' . $annee;
}

/** Les mois affichés dans les tableaux : 12 mois de l'année ou un seul mois. */
function mois_periode(int $annee, ?string $mois): array
{
    if ($mois !== null) {
        return [$mois];
    }
    $out = [];
    for ($m = 1; $m <= 12; $m++) {
        $out[] = sprintf('%04d-%02d', $annee, $m);
    }
    return $out;
}

/** « 2025-07 » -> « Juillet » */
function mois_label(string $mois): string
{
    return ucfirst(MOIS_FR[(int) substr($mois, 5, 2)]);
}
