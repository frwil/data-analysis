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

/** Chaîne complète du QR pour un client (montant en BLP, arrondi au franc). */
function qr_chaine_signe(string $tiers, string $agence, int $annee, float $montant,
                         string $uuid, string $urlVerif): string
{
    $payload = json_encode([
        't' => $tiers, 'a' => $agence, 'y' => $annee,
        'm' => (int) round($montant), 'u' => uuid_compact($uuid),
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
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
