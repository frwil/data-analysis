# -*- coding: utf-8 -*-
"""Reconstruit 'A vérifier' directement depuis l'extraction (mêmes 459 lignes)
pour garantir la colonne 'Ref' (= 'Réf.' de l'ERP). Les feuilles de résumé
sont conservées telles quelles. La colonne 'Nouvel état (à remplir)' est vide
dans le fichier actuel (aucune saisie utilisateur à préserver) — vérifié ci-dessous.
"""
import pandas as pd

BASE = 'D:/Data Analysis/Ristournes/'
fn = BASE + 'Commandes_non_livrees_a_verifier.xlsx'

# ---- Fichier actuel : feuilles de résumé + vérif saisies utilisateur ----
xl = pd.ExcelFile(fn)
d_act = pd.read_excel(xl, sheet_name='A vérifier')
res_client = pd.read_excel(xl, sheet_name='Résumé par client')
res_global = pd.read_excel(xl, sheet_name='Résumé global')
n_saisies = int(d_act['Nouvel état (à remplir)'].notna().sum())
print('Saisies utilisateur existantes (Nouvel état) :', n_saisies)
assert n_saisies == 0, 'Des saisies existent : reconstruction interdite.'

# ---- Reconstruction depuis l'extraction ----
r = pd.read_excel(BASE + 'rist_datas.xlsx', sheet_name='Feuil1')
nl = r[r['État'].isin(['En cours', 'Validée'])].copy()
print('Lignes non livrées dans l\'extraction :', len(nl))
assert len(nl) == 459

nl = nl.sort_values(['Tiers', 'Date de commande', 'Réf. produit'])
d = nl[['Réf. commande client', 'Réf.', 'Tiers', 'Date de commande', 'État',
        'Auteur', 'tableauProprieteAgences.Agence', 'typeClient']].copy()
d['mois'] = d['Date de commande'].dt.to_period('M').astype(str)
d = d.rename(columns={'Réf. commande client': 'Réf. commande', 'Réf.': 'Ref',
                      'tableauProprieteAgences.Agence': 'Agence'})
d['Nouvel état (à remplir)'] = pd.NA
d = d[['Réf. commande', 'Ref', 'Tiers', 'Date de commande', 'mois', 'État',
       'Nouvel état (à remplir)', 'Auteur', 'Agence', 'typeClient']]
print('Ref manquantes :', int(d['Ref'].isna().sum()))
print('colonnes finales :', list(d.columns))

with pd.ExcelWriter(fn, engine='openpyxl') as w:
    d.to_excel(w, sheet_name='A vérifier', index=False)
    res_client.to_excel(w, sheet_name='Résumé par client', index=False)
    res_global.to_excel(w, sheet_name='Résumé global', index=False)

print('OK ->', fn)
