# -*- coding: utf-8 -*-
"""
Restitution finale des ristournes et commissions (BELGOCAM S.A.) — script réutilisable.
- Calcul mois par mois conforme à la PROCÉDURE V6 actualisée (paliers {5, 16, 30} — identiques au fichier Pareto)
- Exclusions : ENTITE (SPC/PDC), SOLDE COMPTA / ND INV / NOTE DE DÉBIT, comptoirs génériques
- Seuil minimum : 5 000 FCFA
Entrées : <EXERCICE>/rist_datas.xlsx, <EXERCICE>/Rs<EXERCICE>_Pareto_20-80.xlsx
Sorties (dans <EXERCICE>/) :
  - Restitution_Ristournes_<EXERCICE>.xlsx (détail mensuel + synthèse client + comparaison Pareto)
  - Analyse_Exploratoire_<EXERCICE>.xlsx (EDA + anomalies)
"""
import pandas as pd
import numpy as np

# ==============================================================
# EXERCICE : année fiscale traitée — changer ici pour 2026, etc.
# ==============================================================
EXERCICE = '2025'
BASE = 'D:/Data Analysis/Ristournes/'
DIR = BASE + EXERCICE + '/'

SEUIL_MIN = 5000

print("Chargement extraction...")
df = pd.read_excel(DIR + 'rist_datas.xlsx', sheet_name='Feuil1')

# ---------------------------------------------------------------
# 1. Filtres
# ---------------------------------------------------------------
# Exclusion ENTITE (filiales : SPC, PDC) — correction vs fichier officiel
n_entite = len(df[df['typeClient'] == 'ENTITE'])
df = df[df['typeClient'] != 'ENTITE']
print(f"Exclues ENTITE : {n_entite} lignes")

# Exclusion tiers spéciaux (ajustements comptables)
masque = df['Tiers'].str.contains('SOLDE COMPTA|NOTE DE DÉBIT|ND INV', case=False, na=False)
n_spec = masque.sum()
df = df[~masque]
print(f"Exclues tiers spéciaux : {n_spec} lignes")

# Exclusion comptoirs génériques (comportement fichier officiel — signalé dans le rapport)
masque_comp = df['Tiers'].str.contains('COMPTOIR', case=False, na=False)
n_comp = masque_comp.sum()
df = df[~masque_comp]
print(f"Exclues comptoirs génériques : {n_comp} lignes")

# Ligne sans propriétés produit : réparée (concentré, conv 0.05) — correction vs fichier officiel
masque_nan = df['tableauPropietesProduits.CategorieProduit'].isna()
n_nan = masque_nan.sum()
if n_nan:
    df.loc[masque_nan, 'tableauPropietesProduits.CategorieProduit'] = 'CONCENTRES'
    df.loc[masque_nan, 'tableauPropietesProduits.convTonne'] = 0.05
    df.loc[masque_nan, 'Qté commandée (en tonnes)'] = df.loc[masque_nan, 'Qté commandée'] * 0.05
    print(f"Réparées : {n_nan} lignes sans propriétés produit (concentré 0.05 T/sac)")

# Ligne annulée après revue ADV (Commandes_non_livrees_a_verifier.xlsx) :
# MEGAMI SO2509-69905 (0,15 T lysine/méthionine) — retirée du calcul
masque_annulee = (df['Réf.'].astype(str) == 'SO2509-69905') & (df['Tiers'] == 'MEGAMI') & (df['État'] == 'Validée')
n_ann = masque_annulee.sum()
df = df[~masque_annulee]
print(f"Exclue ligne annulée (revue ADV) : {n_ann} lignes")

d = df.copy()
d['mois'] = d['Date de commande'].dt.to_period('M')
d['Agence'] = d['tableauProprieteAgences.Agence']
cat = d['tableauPropietesProduits.CategorieProduit']
ref = d['Réf. produit']

LYS_METH = ['I106', 'I107', 'I1061', 'I1071', 'I1063']          # 250 F/sac 25 kg = 10 F/kg
B_10F_KG = ['B100', 'B1001', 'F114', 'F1142', 'F1143', 'F1145', 'F1146', 'F1147',
            'I105', 'I1051', 'P102N2', 'P104N2', 'P109']
B_20F_KG = ['E101', 'E1011', 'E1014', 'P105', 'P1051', 'P1053']

d['fam'] = None
d.loc[cat == 'CONCENTRES', 'fam'] = 'CONC'
d.loc[ref.isin(LYS_METH), 'fam'] = 'LYS_METH'
d.loc[ref.isin(B_10F_KG), 'fam'] = '10F'
d.loc[ref.isin(B_20F_KG), 'fam'] = '20F'
assert d['fam'].notna().all(), "Produits non mappés !"

# ---------------------------------------------------------------
# 2. Concentrés : paliers mensuels (règle actualisée : {5, 16, 30}, identique Pareto)
# ---------------------------------------------------------------
conc = d[d['fam'] == 'CONC']
g = conc.groupby(['Tiers', 'Agence', 'mois'], as_index=False)['Qté commandée (en tonnes)'].sum()
g.columns = ['Tiers', 'Agence', 'Mois', 'T_conc']

def palier(t):
    if t < 5:
        return 0
    elif t < 16:      # palier 1 : 5 à < 16 T — identique fichier Pareto
        return 1
    elif t < 30:
        return 2
    else:
        return 3

def montant_concentres(t):
    p = palier(t)
    if p == 0:
        return 0.0, 0.0, 0.0
    rist = t * 3000.0
    comm = t * {1: 4000.0, 2: 5000.0, 3: 7000.0}[p]
    return rist, comm, rist + comm

g[['Ristourne', 'Commission_conc', 'Total_conc']] = g['T_conc'].apply(
    lambda t: pd.Series(montant_concentres(t)))
g['Palier'] = g['T_conc'].apply(palier)

# ---------------------------------------------------------------
# 3. Autres produits
# ---------------------------------------------------------------
autre = d[d['fam'] != 'CONC'].copy()
autre['m_ligne'] = 0.0
autre.loc[autre['fam'] == 'LYS_METH', 'm_ligne'] = autre['Qté commandée (en tonnes)'] * 1000 * 10
autre.loc[autre['fam'] == '10F', 'm_ligne'] = autre['Qté commandée (en tonnes)'] * 1000 * 10
autre.loc[autre['fam'] == '20F', 'm_ligne'] = autre['Qté commandée (en tonnes)'] * 1000 * 20
autres_mensuel = autre.groupby(['Tiers', 'Agence', 'mois'], as_index=False)['m_ligne'].sum()
autres_mensuel.columns = ['Tiers', 'Agence', 'Mois', 'Commission_autres']

detail = pd.merge(g, autres_mensuel, on=['Tiers', 'Agence', 'Mois'], how='outer').fillna(0)
detail['Total_mois'] = detail['Total_conc'] + detail['Commission_autres']

# ---------------------------------------------------------------
# 4. Synthèse par client + seuil
# ---------------------------------------------------------------
synth = detail.groupby(['Tiers', 'Agence'], as_index=False).agg(
    Total=('Total_mois', 'sum'),
    T_conc_total=('T_conc', 'sum'),
    Mois_eligibles=('Palier', lambda s: (s > 0).sum()),
)
synth = synth[synth['Total'] >= SEUIL_MIN].copy()
synth['Total'] = synth['Total'].round(0).astype(int)
synth = synth.sort_values('Total', ascending=False).reset_index(drop=True)

# Code + conformité NIU depuis le Pareto
pareto = pd.read_excel(DIR + f'Rs{EXERCICE}_Pareto_20-80.xlsx', sheet_name='Liste complète', header=2)
pareto = pareto[pareto['Client'].notna() & (pareto['Client'] != 'TOTAL GÉNÉRAL')].copy()
pareto.columns = ['Rang', 'Client', 'Agence', 'Code', 'Conf', 'Montant', 'pct', 'cum', 'Cat']
pareto['Montant'] = pareto['Montant'].astype(int)

synth['cle'] = synth['Tiers'].str.strip().str.upper() + '||' + synth['Agence'].str.strip().str.upper()
pareto['cle'] = pareto['Client'].str.strip().str.upper() + '||' + pareto['Agence'].str.strip().str.upper()
synth = synth.merge(pareto[['cle', 'Code', 'Conf', 'Montant']], on='cle', how='left')
synth['Ecart_vs_Pareto'] = synth['Total'] - synth['Montant'].fillna(0).astype(int)
synth = synth.drop(columns='cle').rename(columns={'Montant': 'Montant_Pareto', 'Conf': 'Conformite_NIU'})

# ---------------------------------------------------------------
# 5. Détail mensuel enrichi (export)
# ---------------------------------------------------------------
detail_out = detail.merge(
    synth[['Tiers', 'Agence', 'Code', 'Total']].rename(columns={'Total': 'Total_annuel'}),
    on=['Tiers', 'Agence'], how='left')
detail_out = detail_out.sort_values(['Tiers', 'Agence', 'Mois'])
detail_out['Mois'] = detail_out['Mois'].astype(str)
for c in ['T_conc', 'Ristourne', 'Commission_conc', 'Total_conc', 'Commission_autres', 'Total_mois']:
    detail_out[c] = detail_out[c].round(2)

# ---------------------------------------------------------------
# 6. Écarts ciblés pour le rapport
# ---------------------------------------------------------------
# Valeur des lignes exclues dans notre version corrigée vs officiel
print()
print(f"SPC + PDC inclus par l'officiel (à exclure) : {pareto[pareto['Client'].isin(['SPC','PROVENDERIE DU CENTRE (PDC) (FILIALE GROUPE NJS)'])]['Montant'].sum():,.0f} FCFA")

# ---------------------------------------------------------------
# 7. Export Restitution
# ---------------------------------------------------------------
with pd.ExcelWriter(DIR + f'Restitution_Ristournes_{EXERCICE}.xlsx', engine='openpyxl') as w:
    detail_out.to_excel(w, sheet_name='Détail mensuel', index=False)
    synth.to_excel(w, sheet_name='Synthèse client', index=False)
    # Comparaison globale
    comp = synth[['Tiers', 'Agence', 'Code', 'Conformite_NIU', 'Total', 'Montant_Pareto', 'Ecart_vs_Pareto']].copy()
    comp.to_excel(w, sheet_name='Comparaison Pareto', index=False)

print()
print(f"Restitution écrite : {len(synth)} clients | total = {synth['Total'].sum():,.0f} FCFA")
print(f"Total Pareto officiel = {pareto['Montant'].sum():,.0f} FCFA")
print(f"Écart total = {synth['Total'].sum() - pareto['Montant'].sum():,.0f} FCFA")

# ---------------------------------------------------------------
# 8. Analyse exploratoire (EDA)
# ---------------------------------------------------------------
print()
print("Construction EDA...")
eda = {}

# KPI globaux (sur données filtrées = périmètre du calcul)
eda['KPI'] = pd.DataFrame({
    'Indicateur': [
        'Lignes de commande retenues', 'Clients (Tiers) distincts', 'Couples client-agence',
        'Lignes concentrés', 'Lignes autres produits',
        'Tonnes concentrés (année)', 'Tonnes autres produits (année)',
        'Montant total ristournes+commissions (>= 5 000 F)', 'Nombre de clients retenus (>= 5 000 F)',
        'Mois-clients éligibles concentrés', 'Mois-clients non éligibles (< 5 T)',
        'Lignes comptoir exclues (règle)',
    ],
    'Valeur': [
        len(d), d['Tiers'].nunique(), len(synth),
        (d['fam'] == 'CONC').sum(), (d['fam'] != 'CONC').sum(),
        round(conc['Qté commandée (en tonnes)'].sum(), 1),
        round(autre['Qté commandée (en tonnes)'].sum(), 1),
        synth['Total'].sum(), len(synth),
        (g['Palier'] > 0).sum(), (g['Palier'] == 0).sum(),
        n_comp,
    ]
})

# Volumes mensuels par famille
vol = d.groupby(['mois', 'fam']).agg(Tonnes=('Qté commandée (en tonnes)', 'sum'),
                                     Lignes=('Réf.', 'size')).reset_index()
vol_piv = vol.pivot_table(index='mois', columns='fam', values='Tonnes', fill_value=0)
vol_piv = vol_piv.reindex(columns=['CONC', '10F', '20F', 'LYS_METH'])
eda['Volumes mensuels (T)'] = vol_piv.reset_index()

# Par agence
ag = d.groupby('Agence').agg(Lignes=('Réf.', 'size'),
                             Clients=('Tiers', 'nunique'),
                             T_conc=('Qté commandée (en tonnes)', lambda s: s[d.loc[s.index, 'fam'] == 'CONC'].sum()),
                             ).reset_index()
ag = ag.sort_values('Lignes', ascending=False)
eda['Par agence'] = ag

# Top clients (montant recalculé)
top = synth.head(20)[['Tiers', 'Agence', 'Code', 'Total', 'T_conc_total', 'Mois_eligibles']].copy()
eda['Top 20 clients'] = top

# Distribution des montants
bins = [0, 5000, 25000, 50000, 100000, 250000, 500000, 1000000, 3000000]
labels = ['<5k (exclus)', '5k-25k', '25k-50k', '50k-100k', '100k-250k', '250k-500k', '500k-1M', '1M-3M']
synth['tranche'] = pd.cut(synth['Total'], bins=bins, labels=labels, right=False)
dist = synth.groupby('tranche', observed=False).agg(Nb_clients=('Tiers', 'size'),
                                                    Montant=('Total', 'sum')).reset_index()
eda['Distribution montants'] = dist

# Anomalies détectées
anom = pd.DataFrame({
    'Anomalie': [
        'SPC (Ndobo + Famla) et PDC (filiales, typeClient ENTITE) inclus dans le fichier officiel',
        '1 ligne sans propriétés produit exclue du fichier officiel (SO2511-76465, TIWA RENE, 1 T concentré)',
        '459 lignes non livrées (341 En cours + 118 Validée) incluses dans le calcul officiel',
        '1 ligne annulée après revue ADV (MEGAMI — SO2509-69905, 0,15 T lysine/méthionine)',
        '70 lignes en doublon exact (138 lignes concernées au total), sur 63 commandes — comptées deux fois',
        '17 tiers d\'ajustements comptables (SOLDE COMPTA / ND INV / NOTE DE DÉBIT) exclus — 38 lignes',
        'Total du fichier Pareto : incohérence interne de 7 FCFA entre Synthèse et Liste complète',
        'Règle actualisée : paliers 1 et 2 identiques au fichier Pareto (palier 2 dès 16 T)',
        'Règle confirmée : ventes comptoir génériques exclues du rapport final (30 311 lignes, 43,1 %)',
    ],
    'Impact': [
        'Surévaluation de 2 525 000 FCFA (SPC : 1 465 000 Ndobo + 310 000 Famla ; PDC : 750 000)',
        'Sous-paiement de 7 000 FCFA pour TIWA RENE',
        'Revue ADV terminée : 250 lignes marquées Livrée (déjà incluses — conforme), 1 Annulée retirée',
        'Retirée du calcul : −1 500 FCFA (MEGAMI Ahala : 42 140 → 40 640 F)',
        'Risque de double comptage de volumes (impact non isolable sans identifiant de ligne)',
        'Exclusion justifiée (ajustements comptables, pas des achats réels)',
        'Négligeable (arrondis flottants ±1 FCFA sur 7 clients)',
        '17 mois-clients entre 15 et 16 T payés au palier 1 (7 000 F/T) — conforme, aucun rattrapage',
        'Exclusion conforme — ≈ 8,9 M FCFA de ristournes théoriques hors de la liste finale',
    ]
})
eda['Anomalies'] = anom

with pd.ExcelWriter(DIR + f'Analyse_Exploratoire_{EXERCICE}.xlsx', engine='openpyxl') as w:
    for nom, table in eda.items():
        table.to_excel(w, sheet_name=nom[:31], index=False)

print(f"EDA écrite : {EXERCICE}/Analyse_Exploratoire_{EXERCICE}.xlsx")
print("Terminé.")
