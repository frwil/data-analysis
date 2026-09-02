# -*- coding: utf-8 -*-
"""Construit la base SQLite de l'application chèques/listings (cheques/).

Entrées :
  - <EXERCICE>/Restitution_Ristournes_<EXERCICE>.xlsx (feuilles 'Synthèse client'
    et 'Détail mensuel') : clients, gains mensuels, tonnes concentrés.
  - <EXERCICE>/rist_datas.xlsx : kg des autres produits par mois, recalculés
    avec le MÊME périmètre que restitution_finale.py (ENTITE, tiers spéciaux,
    comptoirs et ligne annulée exclus ; ligne TIWA réparée).
    ⚠ Garder ce périmètre synchronisé avec restitution_finale.py.

Codes clients :
  - pris dans la restitution ; les clients sans code reçoivent un code provisoire
    X<EXERCICE>-<NNN> (liste écrite dans cheques/data/codes_fallback.csv) ;
  - surcharge possible via cheques/data/codes_override.csv (Tiers;Agence;Code).

Sortie : cheques/data/ristournes.sqlite
  clients  (tiers, agence, code, total, t_conc_total, mois_eligibles,
            conformite_niu, code_fallback)
  detail   (tiers, agence, mois, t_conc, ristourne, commission_conc, total_conc,
            palier, commission_autres, total_mois, kg_autres)
"""
import csv
import os
import sqlite3

import pandas as pd

# ==============================================================
# EXERCICE : année fiscale traitée — changer ici pour 2026, etc.
# ==============================================================
EXERCICE = '2025'
BASE = 'D:/Data Analysis/Ristournes/'
DIR = BASE + EXERCICE + '/'
APP = BASE + 'cheques/'
DB = APP + 'data/ristournes.sqlite'
os.makedirs(APP + 'data', exist_ok=True)

# ---------------------------------------------------------------
# 1. Restitution : synthèse + détail mensuel
# ---------------------------------------------------------------
rest = pd.read_excel(DIR + f'Restitution_Ristournes_{EXERCICE}.xlsx',
                     sheet_name=['Synthèse client', 'Détail mensuel'])
synth = rest['Synthèse client'].copy()
detail = rest['Détail mensuel'].copy()
print('Synthèse :', len(synth), 'couples client-agence | total =',
      f"{int(synth['Total'].sum()):,} F")
assert int(synth['Total'].sum()) == 89264312, 'Total de référence inattendu'
assert synth.duplicated(['Tiers', 'Agence']).sum() == 0

# ---------------------------------------------------------------
# 2. Codes clients : surcharges puis fallback
# ---------------------------------------------------------------
ovr = {}
try:
    with open(APP + 'data/codes_override.csv', encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            ovr[(str(row['Tiers']).strip(), str(row['Agence']).strip())] = str(row['Code']).strip()
    print('Surcharges de codes lues :', len(ovr))
except FileNotFoundError:
    pass

synth['code_fallback'] = 0
n_fallback = 0
for i, row in synth.iterrows():
    code = ovr.get((str(row['Tiers']).strip(), str(row['Agence']).strip()))
    if not code and pd.notna(row['Code']):
        code = str(row['Code']).strip()
    if not code:
        n_fallback += 1
        code = f'X{EXERCICE}-{n_fallback:03d}'
        synth.at[i, 'code_fallback'] = 1
    synth.at[i, 'Code'] = code
if n_fallback:
    fb = synth[synth['code_fallback'] == 1][['Code', 'Tiers', 'Agence', 'Total']]
    fb.to_csv(APP + 'data/codes_fallback.csv', index=False, encoding='utf-8-sig')
    print(f'Codes provisoires (X{EXERCICE}-NNN) :', n_fallback,
          '-> cheques/data/codes_fallback.csv')

# Codes partagés par plusieurs clients (même code + agence) — à revoir
dup_codes = synth[synth.duplicated(['Code', 'Agence'], keep=False)].copy()
if len(dup_codes):
    dup_codes[['Code', 'Tiers', 'Agence', 'Total']].to_csv(
        APP + 'data/codes_partages.csv', index=False, encoding='utf-8-sig')
    print('Codes partagés entre clients (à revoir) :', len(dup_codes),
          'lignes -> cheques/data/codes_partages.csv')

# ---------------------------------------------------------------
# 3. kg autres produits par mois (périmètre identique au calcul)
# ---------------------------------------------------------------
df = pd.read_excel(DIR + 'rist_datas.xlsx', sheet_name='Feuil1')
df = df[df['typeClient'] != 'ENTITE']
df = df[~df['Tiers'].str.contains('SOLDE COMPTA|NOTE DE DÉBIT|ND INV', case=False, na=False)]
df = df[~df['Tiers'].str.contains('COMPTOIR', case=False, na=False)]

m_nan = df['tableauPropietesProduits.CategorieProduit'].isna()
df.loc[m_nan, 'tableauPropietesProduits.CategorieProduit'] = 'CONCENTRES'
df.loc[m_nan, 'tableauPropietesProduits.convTonne'] = 0.05
df.loc[m_nan, 'Qté commandée (en tonnes)'] = df.loc[m_nan, 'Qté commandée'] * 0.05

df = df[~((df['Réf.'].astype(str) == 'SO2509-69905') & (df['Tiers'] == 'MEGAMI')
          & (df['État'] == 'Validée'))]

cat = df['tableauPropietesProduits.CategorieProduit']
ref = df['Réf. produit']
LYS_METH = ['I106', 'I107', 'I1061', 'I1071', 'I1063']
B_10F_KG = ['B100', 'B1001', 'F114', 'F1142', 'F1143', 'F1145', 'F1146', 'F1147',
            'I105', 'I1051', 'P102N2', 'P104N2', 'P109']
B_20F_KG = ['E101', 'E1011', 'E1014', 'P105', 'P1051', 'P1053']
fam = pd.Series('AUTRE', index=df.index)
fam[cat == 'CONCENTRES'] = 'CONC'
assert fam.notna().all()

autres = df[fam != 'CONC'].copy()
autres['mois'] = autres['Date de commande'].dt.to_period('M').astype(str)
kg = (autres.groupby(['Tiers', 'tableauProprieteAgences.Agence', 'mois'],
                     as_index=False)['Qté commandée (en tonnes)'].sum()
      .rename(columns={'tableauProprieteAgences.Agence': 'Agence'}))
kg['kg_autres'] = (kg['Qté commandée (en tonnes)'] * 1000).round(1)
kg = kg[['Tiers', 'Agence', 'mois', 'kg_autres']]

# ---------------------------------------------------------------
# 4. Détail : uniquement les couples retenus + kg_autres joints
# ---------------------------------------------------------------
det = detail.merge(synth[['Tiers', 'Agence']], on=['Tiers', 'Agence'], how='inner')
det = det.merge(kg, left_on=['Tiers', 'Agence', 'Mois'],
                right_on=['Tiers', 'Agence', 'mois'], how='left')
det['kg_autres'] = det['kg_autres'].fillna(0.0)
det = det.drop(columns='mois')
det = det.rename(columns={
    'T_conc': 't_conc', 'Ristourne': 'ristourne', 'Commission_conc': 'commission_conc',
    'Total_conc': 'total_conc', 'Palier': 'palier',
    'Commission_autres': 'commission_autres', 'Total_mois': 'total_mois',
    'Mois': 'mois'})
det = det[['Tiers', 'Agence', 'mois', 't_conc', 'ristourne', 'commission_conc',
           'total_conc', 'palier', 'commission_autres', 'total_mois', 'kg_autres']]
det = det.sort_values(['Tiers', 'Agence', 'mois'])
print('Détail mensuel :', len(det), 'lignes pour', det.groupby(['Tiers', 'Agence']).ngroups, 'documents')
assert det.duplicated(['Tiers', 'Agence', 'mois']).sum() == 0

# ---------------------------------------------------------------
# 5. Écriture SQLite
# ---------------------------------------------------------------
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
# Noms de colonnes en minuscules : SQLite renvoie les clés telles que déclarées
# (sensible à la casse dans le jeu de résultats) — PHP interroge en minuscules.
synth_sql = synth.rename(columns=str.lower)
det_sql = det.rename(columns=str.lower)
synth_sql[['tiers', 'agence', 'code', 'total', 't_conc_total', 'mois_eligibles',
           'conformite_niu', 'code_fallback']].to_sql('clients', con, index=False)
det_sql.to_sql('detail', con, index=False)
con.execute('CREATE INDEX idx_detail ON detail(tiers, agence, mois)')
con.commit()
con.close()
print('OK ->', DB)
