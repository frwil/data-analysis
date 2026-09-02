# -*- coding: utf-8 -*-
"""Analyse des doublons parmi les 459 lignes non livrées (En cours / Validée)
et structure des feuilles de résumé actuelles."""
import pandas as pd

BASE = 'D:/Data Analysis/Ristournes/'
r = pd.read_excel(BASE + 'rist_datas.xlsx', sheet_name='Feuil1')
nl = r[r['État'].isin(['En cours', 'Validée'])].copy()
print('lignes non livrées :', len(nl))

dup_all = nl.duplicated(subset=list(nl.columns))
print('doublons exacts (toutes colonnes) :', int(dup_all.sum()))
print('lignes concernées (keep=False) :', int(nl.duplicated(subset=list(nl.columns), keep=False).sum()))
print('Réf. (réf. de ligne ERP) dupliquées :', int(nl['Réf.'].duplicated().sum()))
dup_rows = nl[nl.duplicated(subset=list(nl.columns), keep=False)]
print('commandes avec doublons :', dup_rows['Réf. commande client'].nunique())
print(dup_rows[['Réf. commande client', 'Réf.', 'Tiers', 'Date de commande', 'État']].to_string())

xl = pd.ExcelFile(BASE + 'Commandes_non_livrees_a_verifier.xlsx')
print('feuilles :', xl.sheet_names)
for s in ['Résumé par client', 'Résumé global']:
    d = pd.read_excel(xl, sheet_name=s)
    print('---', s, d.shape)
    print(d.columns.tolist())
    print(d.head(8).to_string())
