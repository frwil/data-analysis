<?php
declare(strict_types=1);
/* =============================================================
 * INFORMATIONS ENTREPRISE — À COMPLÉTER
 * Renseigner les champs marqués « … » avant d'imprimer.
 * (En-tête et pied de page des chèques et listings.)
 * ============================================================= */
return [
    'nom'     => 'BELGOCAM S.A.',
    // Titres imprimés en haut à droite des documents
    'titre_cheque'  => 'CHÈQUE DE RISTOURNE',
    'titre_listing' => "LISTING D'ACHATS ET DE GAINS",
    // URL de vérification en ligne, insérée devant la chaîne signée dans le QR :
    // un scan avec l'appareil photo du téléphone ouvre alors cette page, qui
    // vérifie le document (voir verif.html, généré par _gen_verif.php).
    // Laisser '' tant que verif.html n'est pas hébergée en ligne.
    'qr_verif_url' => '',   // ex. 'https://belgocam.cm/verif.html#' (doit se terminer par #)
    // Les 4 niveaux de signature (de gauche à droite)
    'signatures' => [
        'Bénéficiaire (Client)',
        "Chef d'agence (CA)",
        'DCM',
        'DG',
    ],
    // Règle chèques uniquement : part du montant réservée aux COMPLÉMENTS
    // ALIMENTAIRES (10 % du montant, bornée entre 5 000 et 50 000 BLP) —
    // le solde en produits au libellé « Ristournes + Commissions sur Achat ».
    'complements' => ['pct' => 10, 'min' => 5000, 'max' => 50000],
    'slogan'  => '…',                        // optionnel — laisser vide pour masquer
    'adresse' => ['B.P 13288 DLA', 'face Brigade de recherche Bonaberi'],                 // 1 à 3 lignes d'adresse
    'tel'     => '…',                        // ex. « Tél. : +237 6XX XX XX XX »
    'email'   => 'info@belgocam.com',                        // ex. « contact@belgocam.cm »
    'rc'      => '030202',                        // ex. « RC/YAO/2019/B/123 »
    'niu'     => 'M120200015863T',                        // ex. « NIU : M0419XXXXXXX »
    'logo'    => null,                       // ex. 'assets/logo.png' (placé dans cheques/assets/)
    'banque'  => '…',                        // ex. « Chèque tiré sur : UBA Cameroun, compte n° … » — optionnel
    'pied'    => ['Nos agences : ', 'Ndobo:243 740 269; PK11: 675 457 304; Village:653 580 436; Famla:677 130 214; Bamenda (Mbouda):679 617 097; Messassi:677 558 173; Ahala:673 294 468; Bertoua:671 922 621'],                 // 1 à 2 lignes de pied de page (optionnel)
];
