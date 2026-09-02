# -*- coding: utf-8 -*-
"""Reconstruit 'A vérifier' avec des lignes uniques : deux lignes ayant les mêmes
informations visibles (mêmes 10 colonnes de la feuille) n'apparaissent qu'une fois.
- Les doublons exacts (même ligne copiée 2 fois — 1 paire TEJIATSA BLAISE) sont
  retirés AVANT le regroupement, pour ne pas compter deux fois leurs tonnes.
- Les lignes produits distinctes d'une même commande (même Ref, même Tiers…)
  sont regroupées en une seule ligne visible ; leurs tonnes/HT restent agrégés
  dans les résumés.
Les feuilles 'Résumé par client' et 'Résumé global' sont recalculées sur ces
lignes uniques. La colonne 'Nouvel état (à remplir)' est vide (vérifié).
"""
import pandas as pd

# ==============================================================
# EXERCICE : année fiscale traitée — changer ici pour 2026, etc.
# ==============================================================
EXERCICE = '2025'
BASE = 'D:/Data Analysis/Ristournes/'
DIR = BASE + EXERCICE + '/'
fn = DIR + 'Commandes_non_livrees_a_verifier.xlsx'

# ---- Fichier actuel : vérif saisies utilisateur ----
xl = pd.ExcelFile(fn)
d_act = pd.read_excel(xl, sheet_name='A vérifier')
n_saisies = int(d_act['Nouvel état (à remplir)'].notna().sum())
print('Saisies utilisateur existantes (Nouvel état) :', n_saisies)
assert n_saisies == 0, 'Des saisies existent : reconstruction interdite.'

# ---- Extraction ----
r = pd.read_excel(DIR + 'rist_datas.xlsx', sheet_name='Feuil1')
nl = r[r['État'].isin(['En cours', 'Validée'])].copy()
print('Lignes non livrées brutes :', len(nl))

# 1. Retrait des doublons exacts (lignes intégralement identiques)
avant = len(nl)
nl = nl.drop_duplicates(subset=list(nl.columns), keep='first')
print('Doublons exacts retirés :', avant - len(nl))

# 2. Lignes uniques sur les informations visibles de la feuille
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
print('Lignes uniques :', len(g), '(sur', len(nl), 'lignes brutes)')
print('Lignes regroupées (produits distincts d\'une même commande) :', int(len(nl) - len(g)))

d = g[KEY].copy()
d['Nouvel état (à remplir)'] = pd.NA
d = d[['Réf. commande', 'Ref', 'Tiers', 'Date de commande', 'mois', 'État',
       'Nouvel état (à remplir)', 'Auteur', 'Agence', 'typeClient']]
print('Ref manquantes :', int(d['Ref'].isna().sum()))
print('Lignes uniques par état :', dict(d['État'].value_counts()))

# ---- Résumés recalculés sur lignes uniques (tonnes/HT des membres agrégés) ----
res_global = g.groupby('État').agg(
    Commandes=('Réf. commande', 'nunique'),
    Lignes=('Montant_HT', 'size'),
    Tonnes=('Tonnes', 'sum'),
    Montant_HT=('Montant_HT', 'sum'),
).reset_index().sort_values('État')
res_client = g.groupby(['État', 'Tiers', 'Agence'], as_index=False).agg(
    Lignes=('Montant_HT', 'size'),
    Tonnes=('Tonnes', 'sum'),
    Montant_HT=('Montant_HT', 'sum'),
).sort_values(['État', 'Tiers', 'Agence']).rename(columns={'Agence': 'tableauProprieteAgences.Agence'})
print('--- Résumé global (lignes uniques) ---')
print(res_global.to_string())
print('Résumé par client :', len(res_client), 'groupes')

with pd.ExcelWriter(fn, engine='openpyxl') as w:
    d.to_excel(w, sheet_name='A vérifier', index=False)
    res_client.to_excel(w, sheet_name='Résumé par client', index=False)
    res_global.to_excel(w, sheet_name='Résumé global', index=False)

print('OK ->', fn)
