<?php
declare(strict_types=1);
/* =============================================================
 * Signature des QR de chèques/listings — Ed25519 via sodium
 * (natif dans PHP >= 7.2, aucune dépendance).
 *
 * Clé privée : data/sign.key (64 octets) — ne JAMAIS la copier,
 * la partager ni la committer : sa détention permet d'émettre des
 * documents « authentiques ».
 * Clé publique : data/sign.pub — embarquée dans verif.html (page
 * de vérification, générée par _gen_verif.php).
 *
 * Chaîne du QR : [url_verif#]B1.<payload deflaté b64url>.<signature b64url>
 * - payload JSON : {"t":tiers,"a":agence,"y":année,"m":montant BLP,"u":uuid compact}
 * - la signature (détachée) porte sur le JSON non compressé ;
 * - gzdeflate = DEFLATE brut, compatible DecompressionStream('deflate-raw').
 * ============================================================= */

/** Base64 URL-safe sans bourrage (caractères sûrs dans un QR et un fragment d'URL). */
function b64url(string $bin): string
{
    return rtrim(strtr(base64_encode($bin), '+/', '-_'), '=');
}

/** Inverse de b64url() : chaîne b64url -> binaire. */
function b64url_decode(string $s): string
{
    return base64_decode(strtr($s, '-_', '+/') . str_repeat('=', (4 - strlen($s) % 4) % 4));
}

function sign_secret_key(): string
{
    static $cache = null;
    if ($cache !== null) {
        return $cache;
    }
    $f = __DIR__ . '/../data/sign.key';
    if (!is_file($f)) {
        file_put_contents($f, sodium_crypto_sign_secretkey(sodium_crypto_sign_keypair()));
    }
    return $cache = (string) file_get_contents($f);
}

function sign_public_key(): string
{
    $p = __DIR__ . '/../data/sign.pub';
    $pub = sodium_crypto_sign_publickey_from_secretkey(sign_secret_key());
    if (!is_file($p) || file_get_contents($p) !== $pub) {
        file_put_contents($p, $pub);
    }
    return $pub;
}

/** Clé publique en b64url (embarquée dans la page de vérification). */
function sign_public_key_b64url(): string
{
    return b64url(sign_public_key());
}

/** uuid 8-4-4-4-12 -> 22 caractères b64url (16 octets). */
function uuid_compact(string $uuid): string
{
    return b64url(hex2bin(str_replace('-', '', $uuid)));
}

/** uuid compact 22 car. b64url -> forme 8-4-4-4-12 affichée sur le document. */
function uuid_etendre(string $compact): string
{
    if (!preg_match('/^[A-Za-z0-9_-]{22}$/', $compact)) {
        return $compact;
    }
    $h = bin2hex(b64url_decode($compact));
    if (strlen($h) !== 32) {
        return $compact;
    }
    return substr($h, 0, 8) . '-' . substr($h, 8, 4) . '-' . substr($h, 12, 4) . '-'
         . substr($h, 16, 4) . '-' . substr($h, 20);
}

/** JSON signé commun aux deux formats de code (chaîne longue et code court). */
function qr_payload_json(string $tiers, string $agence, int $annee, float $montant,
                         string $uuid): string
{
    return json_encode([
        't' => $tiers, 'a' => $agence, 'y' => $annee,
        'm' => (int) round($montant), 'u' => uuid_compact($uuid),
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
}

/** Chaîne complète du QR pour un client (montant en BLP, arrondi au franc).
 *  Format historique : [url_verif#]B1.<payload déflaté b64url>.<signature b64url> —
 *  conservé pour la vérification des documents déjà imprimés. */
function qr_chaine_signe(string $tiers, string $agence, int $annee, float $montant,
                         string $uuid, string $urlVerif): string
{
    $payload = qr_payload_json($tiers, $agence, $annee, $montant, $uuid);
    $sig = sodium_crypto_sign_detached($payload, sign_secret_key());
    $prefixe = '';
    if ($urlVerif !== '' && $urlVerif !== '…') {
        $prefixe = $urlVerif;
        if (substr($prefixe, -1) !== '#') {
            $prefixe .= '#';   // la chaîne signée doit finir dans le fragment d'URL
        }
    }
    return $prefixe . 'B1.' . b64url(gzdeflate($payload, 9)) . '.' . b64url($sig);
}

/** Code court du QR (17 caractères) : N° du document (8 car. hexa) + empreinte
 *  cryptographique (8 car. b64url = 48 bits de la signature Ed25519 du payload).
 *  Saisissable tel quel dans le formulaire de vérification ; l'application
 *  recalcule l'empreinte attendue depuis la base et la compare — toute
 *  falsification du QR ou du document est détectée. */
function qr_code_court(string $tiers, string $agence, int $annee, float $montant,
                       string $uuid): string
{
    $sig = sodium_crypto_sign_detached(qr_payload_json($tiers, $agence, $annee, $montant, $uuid),
                                       sign_secret_key());
    return substr($uuid, 0, 8) . '-' . b64url(substr($sig, 0, 6));
}
