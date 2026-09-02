# -*- coding: utf-8 -*-
"""Rebâtit les résumés du fichier Commandes_non_livrees_a_verifier.xlsx
selon la revue ADV (« Nouvel état (à remplir) » : 250 Livrée, 1 Annulée).
- La feuille « A vérifier » est préservée telle quelle (remplie par l'utilisateur).
- « Résumé global » et « Résumé par client » sont recalculés sur les lignes
  uniques, regroupées par le nouvel état saisi par l'ADV.
"""
import pandas as pd

# ==============================================================
# EXERCICE : année fiscale traitée — changer ici pour 2026, etc.
# ==============================================================
EXERCICE = '2025'
BASE = 'D:/Data Analysis/Ristournes/'
DIR = BASE + EXERCICE + '/'
fn = DIR + 'Commandes_non_livrees_a_verifier.xlsx'

# ---- Feuille remplie par l'ADV (à préserver) ----
d_adv = pd.read_excel(fn, sheet_name='A vérifier')
print('A vérifier :', len(d_adv), 'lignes')
print(d_adv['Nouvel état (à remplir)'].value_counts(dropna=False).to_string())
n_na = int(d_adv['Nouvel état (à remplir)'].isna().sum())
print('Sans nouvel état :', n_na)
assert n_na == 0, 'Des lignes restent sans nouvel état.'

# ---- Lignes uniques reconstruites depuis l'extraction (même clé que _fix_nl3) ----
r = pd.read_excel(DIR + 'rist_datas.xlsx', sheet_name='Feuil1')
nl = r[r['État'].isin(['En cours', 'Validée'])].copy()
nl = nl.drop_duplicates(subset=list(nl.columns), keep='first')
nl = nl.sort_values(['Tiers', 'Date de commande', 'Réf. produit'])
nl['mois'] = nl['Date de commande'].dt.to_period('M').astype(str)
nl = nl.rename(columns={'Réf. commande client': 'Réf. commande', 'Réf.': 'Ref',
                        'tableauProprieteAgences.Agence': 'Agence'})
KEY = ['Réf. commande', 'Ref', 'Tiers', 'Date de commande', 'mois', 'État',
       'Auteur', 'Agence', 'typeClient']
g = nl.groupby(KEY, as_index=False, dropna=False).agg(
    Tonnes=('Qté commandée (en tonnes)', 'sum'),
    Montant_HT=('Montant HT', 'sum'),
    n_lignes=('Montant HT', 'size'),
)
print('Lignes uniques reconstruites :', len(g))

# ---- Jointure avec le nouvel état saisi (intégrité) ----
m = pd.merge(g, d_adv[KEY + ['Nouvel état (à remplir)']], on=KEY, how='left')
n_manq = int(m['Nouvel état (à remplir)'].isna().sum())
print('Lignes uniques sans correspondance ADV :', n_manq)
assert n_manq == 0, 'La feuille ADV ne couvre pas toutes les lignes uniques.'
n_surnum = len(d_adv) - len(g)
print('Lignes en trop dans la feuille ADV :', n_surnum)
assert n_surnum == 0, 'La feuille ADV contient des lignes inconnues.'

# ---- Résumés par nouvel état ----
res_global = m.groupby('Nouvel état (à remplir)').agg(
    Commandes=('Réf. commande', 'nunique'),
    Lignes=('Montant_HT', 'size'),
    Tonnes=('Tonnes', 'sum'),
    Montant_HT=('Montant_HT', 'sum'),
).reset_index().rename(columns={'Nouvel état (à remplir)': 'État'}).sort_values('État')
res_client = m.groupby(['Nouvel état (à remplir)', 'Tiers', 'Agence'], as_index=False).agg(
    Lignes=('Montant_HT', 'size'),
    Tonnes=('Tonnes', 'sum'),
    Montant_HT=('Montant_HT', 'sum'),
).rename(columns={'Nouvel état (à remplir)': 'État',
                  'Agence': 'tableauProprieteAgences.Agence'}).sort_values(['État', 'Tiers'])
print('--- Résumé global (après revue ADV) ---')
print(res_global.to_string())
print('Résumé par client :', len(res_client), 'groupes')
print('Contrôle tonnes :', round(float(m['Tonnes'].sum()), 4), 'T | HT :', int(m['Montant_HT'].sum()))

with pd.ExcelWriter(fn, engine='openpyxl') as w:
    d_adv.to_excel(w, sheet_name='A vérifier', index=False)
    res_client.to_excel(w, sheet_name='Résumé par client', index=False)
    res_global.to_excel(w, sheet_name='Résumé global', index=False)

print('OK ->', fn)
