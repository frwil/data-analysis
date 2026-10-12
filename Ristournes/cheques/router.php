<?php
declare(strict_types=1);
/* =============================================================
 * Routeur de durcissement pour le serveur intégré PHP.
 * Lancement :  php -S localhost:8123 router.php
 *
 * Le serveur intégré expose par défaut tout le dossier (y compris
 * data/*.sqlite, inc/*.php et les scripts CLI _*.php) : ce routeur
 * refuse ces chemins avant tout accès disque, sert /assets/* en
 * statique, et renvoie tout le reste à index.php (?p=… et POST JSON
 * de suivi_api passent intacts — php -S parse la query string avant
 * d'appeler le routeur). verif.html reste public (anti-fraude : il
 * doit s'ouvrir depuis un téléphone sans authentification).
 * ============================================================= */

$chemin = rawurldecode((string) parse_url((string) ($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_PATH));
$chemin = (string) $chemin;

/* ---- Refus avant tout accès disque ---- */
$normalise = str_replace('\\', '/', $chemin);
if (str_contains($normalise, '..')
    || preg_match('#^/(data|inc)(/|$)#i', $normalise)
    || preg_match('#\.(sqlite|sqlite3|db|log|key|pub)$#i', $normalise)
    || preg_match('#^/_[^/]*\.php(/|$)#i', $normalise)) {
    http_response_code(403);
    exit('Accès refusé.');
}

/* ---- Fichiers statiques du dossier assets/ ---- */
if (preg_match('#^/assets/#i', $normalise) && is_file(__DIR__ . $normalise)) {
    return false;   // php -S sert le fichier lui-même
}

/* ---- Fichiers réels publics (verif.html : page anti-fraude qui doit
       s'ouvrir depuis un téléphone sans authentification) ---- */
if (is_file(__DIR__ . $normalise) && !preg_match('#\.php$#i', $normalise)) {
    return false;
}

/* ---- Tout le reste passe par l'application ---- */
require __DIR__ . '/index.php';
