# -*- coding: utf-8 -*-
"""Contrôle des doublons de commandes — deux niveaux de vérification.

Niveau 0 : une même Réf. rattachée à plusieurs clients (la colonne Réf. est
           censée être unique par client — violation d'unicité).
Niveau 1 : doublons exacts — lignes intégralement identiques répétées dans
           l'extraction (même commande copiée plusieurs fois).

RÈGLE (décision contrôle de gestion, 27/08/2026) : seules les lignes à Réf.
identique constituent des doublons. Deux commandes à Réf. différentes pour le
même client — même date, même auteur, même agence, même montant total et même
composition produits — sont des commandes distinctes, pas des doublons
(l'analyse « commandes proches » menée en 2025 a été écartée sur ce principe).

Écrit <EXERCICE>/Doublons_<EXERCICE>.xlsx — remplace l'ancien
Doublons_exacts_<EXERCICE>.xlsx.
"""
import pandas as pd

# ==============================================================
# EXERCICE : année fiscale traitée — changer ici pour 2026, etc.
# ==============================================================
EXERCICE = '2025'
BASE = 'D:/Data Analysis/Ristournes/'
DIR = BASE + EXERCICE + '/'
fn = DIR + f'Doublons_{EXERCICE}.xlsx'

r = pd.read_excel(DIR + 'rist_datas.xlsx', sheet_name='Feuil1')
print('Extraction :', len(r), 'lignes')

# ---------------------------------------------------------------
# Table des commandes (par Réf.) : contexte ordre, toutes lignes produits
# ---------------------------------------------------------------
cmd = r.groupby('Réf.').agg(
    Tiers=('Tiers', 'first'),
    Date=('Date de commande', 'first'),
    Auteur=('Auteur', 'first'),
    Agence=('tableauProprieteAgences.Agence', 'first'),
    typeClient=('typeClient', 'first'),
    État=('État', 'first'),
    Montant_total=('Montant HT', 'sum'),
    n_lignes=('Montant HT', 'size'),
    Tonnes=('Qté commandée (en tonnes)', 'sum'),
).reset_index()
cmd['Comptoir'] = cmd['Tiers'].str.contains('COMPTOIR', case=False, na=False)
print('Commandes (Réf. distinctes) :', len(cmd))

# ---------------------------------------------------------------
# NIVEAU 0 — Réf. rattachée à plusieurs clients
# ---------------------------------------------------------------
multi_refs = r.groupby('Réf.')['Tiers'].nunique()
multi_refs = multi_refs[multi_refs > 1].index.tolist()
n0 = (r[r['Réf.'].isin(multi_refs)]
      .groupby(['Réf.', 'Tiers'], dropna=False)
      .agg(Date=('Date de commande', 'first'),
           Auteur=('Auteur', 'first'),
           Agence=('tableauProprieteAgences.Agence', 'first'),
           typeClient=('typeClient', 'first'),
           État=('État', 'first'),
           Montant_total=('Montant HT', 'sum'),
           n_lignes=('Montant HT', 'size'),
           Tonnes=('Qté commandée (en tonnes)', 'sum'))
      .reset_index()
      .sort_values(['Réf.', 'Tiers']))
print('N0 — Réf. multi-clients :', len(multi_refs), 'références,' , len(n0), 'lignes')
if len(n0):
    print(n0.to_string())

# ---------------------------------------------------------------
# NIVEAU 1 — doublons exacts (lignes intégralement identiques)
# ---------------------------------------------------------------
dup = r[r.duplicated(subset=list(r.columns), keep=False)].copy()
n_extra = int(len(dup) - dup.drop_duplicates().shape[0])  # lignes comptées en double (en trop)
print('\nN1 — lignes en double :', len(dup), 'impliquées,', n_extra, 'en trop')

d1 = dup.groupby('Réf.').agg(
    n_lignes_dup=('Montant HT', 'size'),
    HT_dup=('Montant HT', 'sum'),
    Tonnes_dup=('Qté commandée (en tonnes)', 'sum'),
).reset_index()
n1 = cmd[cmd['Réf.'].isin(d1['Réf.'].unique())].merge(d1, on='Réf.')
n1 = n1.sort_values(['HT_dup', 'Tiers'], ascending=[False, True])
n1 = n1[['Réf.', 'Tiers', 'Date', 'Auteur', 'Agence', 'typeClient', 'État',
         'Montant_total', 'n_lignes', 'n_lignes_dup', 'HT_dup', 'Tonnes_dup', 'Comptoir']]
print('N1 — commandes concernées :', len(n1), '| HT en double :', int(n1['HT_dup'].sum()))
assert len(n1) == 63, f'Attendu 63 commandes, obtenu {len(n1)}'
assert len(dup) == 138, f'Attendu 138 lignes impliquées, obtenu {len(dup)}'

lignes1 = dup.sort_values(['Réf.', 'Tiers', 'Réf. produit']).copy()

# (Niveau « commandes proches » supprimé : décision — des Réf. différentes ne
#  constituent pas des doublons, même à client/date/auteur/agence/montant
#  total/composition identiques.)

# ---------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------
with pd.ExcelWriter(fn, engine='openpyxl') as w:
    n0.to_excel(w, sheet_name='N0 - Réf multi-clients', index=False)
    n1.to_excel(w, sheet_name='N1 - Commandes', index=False)
    lignes1.to_excel(w, sheet_name='N1 - Lignes dupliquées', index=False)

print('OK ->', fn)
