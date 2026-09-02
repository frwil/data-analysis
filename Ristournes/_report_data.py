# -*- coding: utf-8 -*-
"""Données pour le rapport HTML de validation (Audit Ristournes) — script réutilisable.
Recalcule tous les indicateurs (reproduction officielle, périmètre corrigé, anomalies)
et les exporte en JSON pour les graphiques du rapport.
"""
import pandas as pd
import numpy as np
import json

# ==============================================================
# EXERCICE : année fiscale traitée — changer ici pour 2026, etc.
# ==============================================================
EXERCICE = '2025'
BASE = 'D:/Data Analysis/Ristournes/'
DIR = BASE + EXERCICE + '/'

df = pd.read_excel(DIR + 'rist_datas.xlsx', sheet_name='Feuil1')
out = {'brutes': int(len(df))}

col_comm = [c for c in df.columns if ('commande' in str(c).lower()) or ('n°' in str(c).lower())]
col_ht = [c for c in df.columns if 'ht' in str(c).lower()]
out['colonnes'] = {'commande': col_comm, 'ht': col_ht}

out['etats'] = {str(k): int(v) for k, v in df['État'].value_counts().items()}
out['typeClient'] = {str(k): int(v) for k, v in df['typeClient'].value_counts().items()}
out['categories'] = {str(k): int(v) for k, v in df['tableauPropietesProduits.CategorieProduit'].value_counts(dropna=False).items()}
out['n_agences'] = int(df['tableauProprieteAgences.Agence'].nunique())

# Doublons exacts (toutes colonnes identiques)
dup = df.duplicated(subset=list(df.columns))
out['doublons'] = {'lignes': int(dup.sum()),
                   'commandes': int(df.loc[dup, 'Réf.'].nunique())}

# Ligne sans propriétés produit
out['ligne_sans_produit'] = df[df['tableauPropietesProduits.CategorieProduit'].isna()][
    ['Tiers', 'Réf. produit', 'Description du produit', 'Qté commandée', 'État']].to_dict('records')

LYS_METH = ['I106', 'I107', 'I1061', 'I1071', 'I1063']
B_10F_KG = ['B100', 'B1001', 'F114', 'F1142', 'F1143', 'F1145', 'F1146', 'F1147',
            'I105', 'I1051', 'P102N2', 'P104N2', 'P109']
B_20F_KG = ['E101', 'E1011', 'E1014', 'P105', 'P1051', 'P1053']

def map_fam(d):
    d = d.copy()
    cat = d['tableauPropietesProduits.CategorieProduit']
    ref = d['Réf. produit']
    d['fam'] = None
    d.loc[cat == 'CONCENTRES', 'fam'] = 'CONC'
    d.loc[ref.isin(LYS_METH), 'fam'] = 'LYS_METH'
    d.loc[ref.isin(B_10F_KG), 'fam'] = '10F'
    d.loc[ref.isin(B_20F_KG), 'fam'] = '20F'
    return d

def montant_palier(t):
    # Règle actualisée (27/08/2026) : paliers 1 et 2 identiques au fichier Pareto {5, 16, 30}
    if t < 5: return 0.0, 0
    if t < 16: return t * 7000.0, 1
    if t < 30: return t * 8000.0, 2
    return t * 10000.0, 3

def calcul(dfx, seuil_min=5000):
    """Calcule ristournes+commissions par couple (Tiers, Agence)."""
    dfx = map_fam(dfx)
    dfx['mois'] = dfx['Date de commande'].dt.to_period('M')
    conc = dfx[dfx['fam'] == 'CONC']
    g = conc.groupby(['Tiers', 'tableauProprieteAgences.Agence', 'mois'], as_index=False)['Qté commandée (en tonnes)'].sum()
    g.columns = ['Tiers', 'Agence', 'mois', 'tonnes']
    mm = g['tonnes'].apply(montant_palier)
    g['montant'] = mm.apply(lambda x: x[0])
    g['palier'] = mm.apply(lambda x: x[1])
    autre = dfx[dfx['fam'] != 'CONC'].copy()
    autre['m'] = 0.0
    msk = autre['fam'].isin(['LYS_METH', '10F'])
    autre.loc[msk, 'm'] = autre.loc[msk, 'Qté commandée (en tonnes)'] * 1000 * 10
    msk20 = autre['fam'] == '20F'
    autre.loc[msk20, 'm'] = autre.loc[msk20, 'Qté commandée (en tonnes)'] * 1000 * 20
    at = autre.groupby(['Tiers', 'tableauProprieteAgences.Agence'], as_index=False)['m'].sum()
    at.columns = ['Tiers', 'Agence', 'm_autre']
    ct = g.groupby(['Tiers', 'Agence'], as_index=False)['montant'].sum()
    ct.columns = ['Tiers', 'Agence', 'm_conc']
    calc = pd.merge(ct, at, on=['Tiers', 'Agence'], how='outer').fillna(0)
    calc['total'] = calc['m_conc'] + calc['m_autre']
    calc = calc[calc['total'] >= seuil_min].copy()
    calc['total'] = calc['total'].round(0).astype(int)
    return calc, g, dfx

# ---------------------------------------------------------------
# REPRODUCTION DU FICHIER OFFICIEL (règle {5,16,30}, périmètre Pareto)
# ---------------------------------------------------------------
fo = df.copy()
fo = fo[fo['tableauPropietesProduits.CategorieProduit'].notna()]  # ligne sans produit exclue (comportement officiel)
fo = fo[~fo['Tiers'].str.contains('SOLDE COMPTA|NOTE DE DÉBIT|ND INV', case=False, na=False)]
fo = fo[~fo['Tiers'].str.contains('COMPTOIR', case=False, na=False)]
calc_o, _, _ = calcul(fo)

pareto = pd.read_excel(DIR + f'Rs{EXERCICE}_Pareto_20-80.xlsx', sheet_name='Liste complète', header=2)
pareto = pareto[pareto['Client'].notna() & (pareto['Client'] != 'TOTAL GÉNÉRAL')].copy()
pareto.columns = ['Rang', 'Client', 'Agence', 'Code', 'Conf', 'Montant', 'pct', 'cum', 'Cat']
pareto['Montant'] = pareto['Montant'].astype(int)

calc_o['cle'] = calc_o['Tiers'].str.strip().str.upper() + '||' + calc_o['Agence'].str.strip().str.upper()
pareto['cle'] = pareto['Client'].str.strip().str.upper() + '||' + pareto['Agence'].str.strip().str.upper()
m = pd.merge(calc_o, pareto[['cle', 'Montant']], on='cle', how='left', suffixes=('', '_par'))
m['ecart'] = m['total'] - m['Montant'].fillna(0)
m['status'] = 'OK'
m.loc[m['Montant'].isna(), 'status'] = 'ABSENT_PARETO'
m.loc[m['Montant'].notna() & (m['ecart'] != 0), 'status'] = 'ECART'

out['repro'] = {
    'lignes_calc': int(len(calc_o)),
    'ok': int((m['status'] == 'OK').sum()),
    'ecarts_n': int((m['status'] == 'ECART').sum()),
    'absents_n': int((m['status'] == 'ABSENT_PARETO').sum()),
    'somme_calc': int(calc_o['total'].sum()),
    'somme_pareto_liste': int(pareto['Montant'].sum()),
    'somme_pareto_synthese': 91783812,  # vérifié sur la feuille Synthèse du fichier Pareto
    'ecarts_liste': m[m['status'] == 'ECART'][['Tiers', 'Agence', 'total', 'Montant', 'ecart']].to_dict('records'),
}

# ---------------------------------------------------------------
# ENTITE (SPC / PDC) incluses par l'officiel
# ---------------------------------------------------------------
ent = df[df['typeClient'] == 'ENTITE']
calc_e, _, _ = calcul(ent)
spc_pdc_pareto = pareto[pareto['Client'].isin(['SPC', 'PROVENDERIE DU CENTRE (PDC) (FILIALE GROUPE NJS)'])]
out['entite'] = {
    'lignes': int(len(ent)),
    'valeur_pareto': int(spc_pdc_pareto['Montant'].sum()),
    'liste_pareto': spc_pdc_pareto[['Client', 'Agence', 'Montant']].to_dict('records'),
    'valeur_isolee': int(calc_e['total'].sum()),
}

# ---------------------------------------------------------------
# COMPTOIRS GÉNÉRIQUES (exclus par l'officiel)
# ---------------------------------------------------------------
comp = df[df['Tiers'].str.contains('COMPTOIR', case=False, na=False)]
calc_c, _, _ = calcul(comp)
out['comptoirs'] = {
    'lignes': int(len(comp)),
    'pct_lignes': round(len(comp) / len(df) * 100, 1),
    'valeur_rist': int(calc_c['total'].sum()),
    'clients_seuil': int(len(calc_c)),
}

# ---------------------------------------------------------------
# LIGNES NON LIVRÉES (incluses par l'officiel)
# ---------------------------------------------------------------
nl = df[df['État'].isin(['En cours', 'Validée'])]
calc_nl, _, _ = calcul(nl)
out['non_livrees'] = {
    'lignes': int(len(nl)),
    'commandes': int(nl[col_comm[0]].nunique()) if col_comm else 0,
    'tonnes': round(float(nl['Qté commandée (en tonnes)'].sum()), 2),
    'ht': int(nl[col_ht[0]].sum()) if col_ht else None,
    'valeur_rist_isolee': int(calc_nl['total'].sum()),
    'par_etat': {
        str(e): {
            'lignes': int(grp.shape[0]),
            'commandes': int(grp[col_comm[0]].nunique()) if col_comm else 0,
            'tonnes': round(float(grp['Qté commandée (en tonnes)'].sum()), 2),
            'ht': int(grp[col_ht[0]].sum()) if col_ht else None,
        }
        for e, grp in nl.groupby('État')
    },
}

# Revue ADV (fichier Commandes_non_livrees_a_verifier.xlsx mis à jour)
rev = pd.read_excel(DIR + 'Commandes_non_livrees_a_verifier.xlsx', sheet_name='A vérifier')
out['non_livrees']['revue'] = {str(k): int(v) for k, v in rev['Nouvel état (à remplir)'].value_counts().items()}

# ---------------------------------------------------------------
# PÉRIMÈTRE CORRIGÉ (règle actualisée : {5,16,30}, hors ENTITE, hors comptoirs,
# ligne réparée, ligne annulée après revue ADV)
# ---------------------------------------------------------------
fc = df.copy()
fc = fc[fc['typeClient'] != 'ENTITE']
fc = fc[~fc['Tiers'].str.contains('SOLDE COMPTA|NOTE DE DÉBIT|ND INV', case=False, na=False)]
fc = fc[~fc['Tiers'].str.contains('COMPTOIR', case=False, na=False)]
nan_m = fc['tableauPropietesProduits.CategorieProduit'].isna()
fc.loc[nan_m, 'tableauPropietesProduits.CategorieProduit'] = 'CONCENTRES'
fc.loc[nan_m, 'tableauPropietesProduits.convTonne'] = 0.05
fc.loc[nan_m, 'Qté commandée (en tonnes)'] = fc.loc[nan_m, 'Qté commandée'] * 0.05
# Ligne annulée après revue ADV : MEGAMI SO2509-69905 (0,15 T lysine/méthionine)
masque_annulee = (fc['Réf.'].astype(str) == 'SO2509-69905') & (fc['Tiers'] == 'MEGAMI') & (fc['État'] == 'Validée')
n_ann = int(masque_annulee.sum())
fc = fc[~masque_annulee].copy()
out['annulee'] = {'lignes': n_ann}
calc_cor, g_c, d_c = calcul(fc)

out['corrige'] = {
    'clients': int(len(calc_cor)),
    'total': int(calc_cor['total'].sum()),
    'paliers': {str(k): int(v) for k, v in g_c['palier'].value_counts().sort_index().items()},
    't_conc': round(float(d_c.loc[d_c['fam'] == 'CONC', 'Qté commandée (en tonnes)'].sum()), 1),
    't_autres': round(float(d_c.loc[d_c['fam'] != 'CONC', 'Qté commandée (en tonnes)'].sum()), 1),
}

# Volumes mensuels par famille (périmètre corrigé)
vol = d_c.groupby(['mois', 'fam']).agg(T=('Qté commandée (en tonnes)', 'sum')).reset_index()
vol_p = vol.pivot_table(index='mois', columns='fam', values='T', fill_value=0).reindex(columns=['CONC', '10F', '20F', 'LYS_METH'])
out['vol_mensuels'] = [{'mois': str(mo), **{f: round(float(row[f]), 1) for f in vol_p.columns}}
                       for mo, row in vol_p.iterrows()]

# Top 20 clients (périmètre corrigé)
top20 = calc_cor.sort_values('total', ascending=False).head(20)
out['top20'] = [{'Tiers': str(r.Tiers), 'Agence': str(r.Agence), 'total': int(r.total)} for r in top20.itertuples()]
out['top20_sum'] = int(top20['total'].sum())
out['top20_pct'] = round(float(top20['total'].sum() / calc_cor['total'].sum() * 100), 1)
out['famla_pct_lignes'] = round(float(d_c['Tiers'].str.contains('FAMLA', case=False, na=False).mean() * 100), 1)

# Distribution des montants
bins = [0, 5000, 25000, 50000, 100000, 250000, 500000, 1000000, 3000000]
labels = ['< 5k (exclus)', '5k–25k', '25k–50k', '50k–100k', '100k–250k', '250k–500k', '500k–1M', '1M–3M']
calc_cor['tranche'] = pd.cut(calc_cor['total'], bins=bins, labels=labels, right=False)
calc_cor['tranche'] = calc_cor['tranche'].cat.add_categories('> 3M').fillna('> 3M')
dist = calc_cor.groupby('tranche', observed=False).agg(n=('Tiers', 'size'), montant=('total', 'sum'))
out['distribution'] = [{'tranche': str(i), 'n': int(r['n']), 'montant': int(r['montant'])} for i, r in dist.iterrows()]

# Par agence
ag = d_c.groupby('tableauProprieteAgences.Agence').agg(
    lignes=('Tiers', 'size'),
    clients=('Tiers', 'nunique'),
    t_conc=('Qté commandée (en tonnes)', lambda s: s[d_c.loc[s.index, 'fam'] == 'CONC'].sum()),
).reset_index().sort_values('lignes', ascending=False)
out['agences'] = [{'agence': str(r[1]), 'lignes': int(r[2]), 'clients': int(r[3]), 't_conc': round(float(r[4]), 1)}
                  for r in ag.itertuples()]

# Mois entre 15 et 16 T : payés au palier 1 (7 000 F/T) — règle actualisée, identique au fichier
m16 = g_c[(g_c['tonnes'] > 15) & (g_c['tonnes'] < 16)].copy()
m16['montant'] = (m16['tonnes'] * 7000).round(0).astype(int)
out['palier16'] = {
    'n_mois': int(len(m16)),
    'n_clients': int(m16['Tiers'].nunique()),
    'montant': int(m16['montant'].sum()),
    'liste': [{'Tiers': str(r.Tiers), 'Agence': str(r.Agence), 'mois': str(r.mois),
               'tonnes': float(r.tonnes), 'montant': int(r.montant)} for r in m16.itertuples()],
}

# Mois à exactement 30 T : surpayés par l'officiel (10 000 au lieu de 8 000 F/T)
m30 = g_c[g_c['tonnes'] == 30.0].copy()
out['exactement_30'] = {
    'n_mois': int(len(m30)),
    'liste': [{'Tiers': str(r.Tiers), 'Agence': str(r.Agence), 'mois': str(r.mois)} for r in m30.itertuples()],
}

# Tiers spéciaux (ajustements comptables)
spec = df[df['Tiers'].str.contains('SOLDE COMPTA|NOTE DE DÉBIT|ND INV', case=False, na=False)]
out['tiers_speciaux'] = {'lignes': int(len(spec)), 'tiers': int(spec['Tiers'].nunique())}

def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(x) for x in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, (pd.Period, pd.Timestamp)): return str(o)
    return o

with open(DIR + '_report_data.json', 'w', encoding='utf-8') as f:
    json.dump(clean(out), f, ensure_ascii=False, indent=1)

print("=== Synthèse ===")
print(f"Reproduction : {out['repro']['ok']} OK / {out['repro']['ecarts_n']} écarts ±1 / somme calc = {out['repro']['somme_calc']:,}")
print(f"Corrigé : {out['corrige']['clients']} clients | {out['corrige']['total']:,} F")
print(f"ENTITE : pareto = {out['entite']['valeur_pareto']:,} | isolé = {out['entite']['valeur_isolee']:,}")
print(f"Comptoirs : {out['comptoirs']['lignes']} lignes ({out['comptoirs']['pct_lignes']} %) | rist = {out['comptoirs']['valeur_rist']:,}")
print(f"Non livrées : {out['non_livrees']['lignes']} lignes | rist isolée = {out['non_livrees']['valeur_rist_isolee']:,}")
print(f"Revue ADV : {out['non_livrees']['revue']} | annulée : {out['annulee']['lignes']} ligne")
print(f"Bande 15-16 T (palier 1 confirmé) : {out['palier16']['n_mois']} mois-clients | montant = {out['palier16']['montant']:,}")
print(f"Exactement 30 T : {out['exactement_30']['n_mois']} mois-clients")
print(f"Doublons : {out['doublons']['lignes']} lignes / {out['doublons']['commandes']} commandes")
print(f"Paliers (corrigé) : {out['corrige']['paliers']}")
print("OK -> _report_data.json")
