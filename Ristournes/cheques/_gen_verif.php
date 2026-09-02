<?php
declare(strict_types=1);
/* =============================================================
 * Génère verif.html, la page autonome de vérification des QR :
 * - injecte la clé publique (data/sign.pub, créée au besoin) ;
 * - inline les libs jsQR (scan caméra) et tweetnacl (vérif Ed25519).
 *
 * Usage :  php _gen_verif.php   (depuis le dossier cheques/)
 * À relancer si la clé privée data/sign.key est régénérée.
 * verif.html est un fichier unique : à héberger en ligne (site,
 * Netlify, GitHub Pages…) puis à renseigner dans inc/config.php
 * ('qr_verif_url') pour que le QR contienne l'URL de vérification.
 * ============================================================= */
require __DIR__ . '/inc/signature.php';

$tpl  = file_get_contents(__DIR__ . '/inc/verif_template.html');
$jsqr = file_get_contents(__DIR__ . '/assets/jsQR.js');
$nacl = file_get_contents(__DIR__ . '/assets/nacl-fast.min.js');
$pub  = sign_public_key_b64url();

$html = str_replace(['__PUBKEY__', '/*__JSQR__*/', '/*__NACL__*/'],
                    [$pub, $jsqr, $nacl], $tpl);
file_put_contents(__DIR__ . '/verif.html', $html);

echo "verif.html généré (clé publique $pub)\n";
