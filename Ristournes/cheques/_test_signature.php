<?php
declare(strict_types=1);
/* Test de la chaîne signée : format, compression, signature, interop.
   Usage : php _test_signature.php
   Écrit aussi un fixture JSON dans le dossier temporaire pour le test
   d'interop node (_test_interop.mjs, crypto native node). */
require __DIR__ . '/inc/signature.php';

function b64u_dec(string $s): string
{
    return base64_decode(strtr($s, '-_', '+/'));
}

$chain = qr_chaine_signe('GIC TEST ELEVEUR — Élevage OK', 'Douala', 2025, 89264.4,
                         '3f2a7c91-0b4e-4d2a-9c1f-8e5b2d1a6c3f',
                         'https://verif.belgocam.cm/verif.html#');
echo "CHAÎNE ($chain)\n";
echo 'Longueur : ' . strlen($chain) . " caractères\n";

preg_match('/^(https?:\/\/[^#]*)#(.*)$/', $chain, $m);
$base = $m[2] ?? $chain;
$p = explode('.', $base);
if (count($p) !== 3 || $p[0] !== 'B1') {
    fwrite(STDERR, "ÉCHEC : format B1.<data>.<sig> attendu\n");
    exit(1);
}

$json  = gzinflate(b64u_dec($p[1]));
$ok    = sodium_crypto_sign_verify_detached(b64u_dec($p[2]), $json, sign_public_key());
echo "Signature vérifiée (sodium) : " . ($ok ? 'OUI' : 'NON') . "\n";
echo "JSON : $json\n";

$alt = str_replace('"m":89264', '"m":89265', $json);
$okAlt = sodium_crypto_sign_verify_detached(b64u_dec($p[2]), $alt, sign_public_key());
echo 'Signature résiste à un montant falsifié : ' . (!$okAlt ? 'OUI' : 'NON') . "\n";

if (!$ok || $okAlt) {
    exit(1);
}

file_put_contents(sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'bcp_test_fixture.json', json_encode([
    'chain' => $chain, 'pub' => sign_public_key_b64url(),
    'data' => $p[1], 'sig' => $p[2], 'json' => $json,
], JSON_UNESCAPED_UNICODE));
echo "Fixture écrit pour _test_interop.mjs\n";
