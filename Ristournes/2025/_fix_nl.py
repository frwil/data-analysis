# -*- coding: utf-8 -*-
"""Modifie la feuille 'A vérifier' de Commandes_non_livrees_a_verifier.xlsx :
- ajoute la colonne 'Ref' (référence de ligne 'Réf.' de l'extraction ERP)
- retire : 'Réf. produit', 'Description du produit', 'Qté commandée', 'Contenance', 'Tonnes', 'Montant HT'
Les feuilles 'Résumé par client' et 'Résumé global' sont conservées telles quelles.
"""
import pandas as pd

BASE = 'D:/Data Analysis/Ristournes/'
fn = BASE + 'Commandes_non_livrees_a_verifier.xlsx'

# ---- Lecture de toutes les feuilles existantes ----
xl = pd.ExcelFile(fn)
d = pd.read_excel(xl, sheet_name='A vérifier')
res_client = pd.read_excel(xl, sheet_name='Résumé par client')
res_global = pd.read_excel(xl, sheet_name='Résumé global')
print('avant:', d.shape)

# ---- Jointure avec l'extraction pour récupérer 'Réf.' (réf. de ligne ERP) ----
r = pd.read_excel(BASE + 'rist_datas.xlsx', sheet_name='Feuil1')
r = r.rename(columns={'Qté commandée (en tonnes)': 'Tonnes'})
r = r[['Réf.', 'Tiers', 'Date de commande', 'Réf. produit', 'Qté commandée', 'Tonnes', 'Montant HT']]

d['Date de commande'] = pd.to_datetime(d['Date de commande'])
r['Date de commande'] = pd.to_datetime(r['Date de commande'])

cles = ['Tiers', 'Date de commande', 'Réf. produit', 'Qté commandée', 'Tonnes', 'Montant HT']
r = r.drop_duplicates(subset=cles, keep='first')  # un Réf. par ligne (doublons exacts partagent la même clé)
d = d.merge(r, on=cles, how='left')
print('après merge:', d.shape, '| Ref manquantes:', int(d['Réf.'].isna().sum()))
assert len(d) == 459, f"Nombre de lignes inattendu : {len(d)}"

# ---- Restructuration des colonnes ----
d = d.rename(columns={'Réf.': 'Ref'})
col_drop = ['Réf. produit', 'Description du produit', 'Qté commandée', 'Contenance', 'Tonnes', 'Montant HT']
d = d.drop(columns=col_drop)
cols = list(d.columns)
pos = cols.index('Réf. commande') + 1
cols.remove('Ref')
cols.insert(pos, 'Ref')
d = d[cols]
print('colonnes finales:', list(d.columns))

# ---- Réécriture du classeur (même ordre de feuilles) ----
with pd.ExcelWriter(fn, engine='openpyxl') as w:
    d.to_excel(w, sheet_name='A vérifier', index=False)
    res_client.to_excel(w, sheet_name='Résumé par client', index=False)
    res_global.to_excel(w, sheet_name='Résumé global', index=False)

print('OK ->', fn)
