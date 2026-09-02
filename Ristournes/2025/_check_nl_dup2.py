# -*- coding: utf-8 -*-
"""Doublons sur les colonnes visibles de la feuille + nature des 'Réf.' partagées
+ validation de la logique de reconstruction des résumés."""
import pandas as pd

BASE = 'D:/Data Analysis/Ristournes/'
r = pd.read_excel(BASE + 'rist_datas.xlsx', sheet_name='Feuil1')
nl = r[r['État'].isin(['En cours', 'Validée'])].copy()

# 1. Doublons sur les colonnes visibles de la feuille « A vérifier »
cols_vis = ['Réf. commande client', 'Réf.', 'Tiers', 'Date de commande', 'État',
            'Auteur', 'tableauProprieteAgences.Agence', 'typeClient']
print('doublons exacts (toutes colonnes) :', int(nl.duplicated(subset=list(nl.columns)).sum()))
print('doublons sur colonnes visibles    :', int(nl.duplicated(subset=cols_vis).sum()))

# 2. Nature des « Réf. » partagées : même commande/ligne copiée ou lignes produits différentes ?
g = nl.groupby('Réf.').size()
multi = g[g > 1]
print('Réf. partagées entre lignes :', len(multi), '| lignes concernées :', int(multi.sum()))
r_ref = nl[nl['Réf.'].isin(multi.index)].sort_values(['Réf.', 'Réf. produit'])
print(r_ref[['Réf.', 'Réf. commande client', 'Tiers', 'Réf. produit', 'Qté commandée',
             'Qté commandée (en tonnes)', 'Montant HT']].head(30).to_string())

# 3. La « Réf. » est-elle unique dans toute l'extraction ?
print('Réf. dupliquées dans toute l\'extraction :', int(r['Réf.'].duplicated().sum()),
      'sur', len(r), 'lignes')

# 4. Validation de la logique des résumés (doit reproduire les valeurs actuelles)
res_g = nl.groupby('État').agg(Commandes=('Réf. commande client', 'nunique'),
                               Lignes=('Réf.', 'size'),
                               Tonnes=('Qté commandée (en tonnes)', 'sum'),
                               Montant_HT=('Montant HT', 'sum')).reset_index()
print('--- Résumé global reconstruit (doit valoir 90/341/130.8802/92352969 et 18/118/66.5710/45586390)')
print(res_g.to_string())

res_c = nl.groupby(['État', 'Tiers', 'tableauProprieteAgences.Agence'], as_index=False).agg(
    Lignes=('Réf.', 'size'),
    Tonnes=('Qté commandée (en tonnes)', 'sum'),
    Montant_HT=('Montant HT', 'sum'))
print('--- Résumé par client reconstruit :', res_c.shape[0], 'lignes (doit valoir 110)')
print(res_c[res_c['Tiers'].isin(['CLIENTS COMPTOIR BERTOUA', 'TEJIATSA BLAISE', 'ATECHI SHADRACK CLOVIS'])].to_string())
