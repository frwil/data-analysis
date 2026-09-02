# -*- coding: utf-8 -*-
"""
Recalcul des ristournes et commissions 2025 (BELGOCAM S.A.)
Selon la procédure V6 : paliers concentrés mensuels + barème autres produits.
Sortie : comparaison avec Rs2025_Pareto_20-80.xlsx (Liste complète).
"""
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------
# Paramètres (hypothèses à tester)
# ----------------------------------------------------------------------
INCLURE_NON_LIVREES = True      # inclure lignes 'En cours' / 'Validée' ?
DEDUP_LIGNES_IDENTIQUES = False  # retirer les 138 doublons exacts ?
EXCLURE_TIERS_SPECIAUX = True    # SOLDE COMPTA / ND INV / NOTE DE DÉBIT
EXCLURE_COMPTOIRS_GENERIQUES = True  # tiers 'CLIENTS COMPTOIR X' (exclus du Pareto)
LYS_METH_1KG_10F = True          # lysine/méthionine petits packs à 10 F/kg (=250 F/sac équivalent)
PALIER_SUR_PLANCHER = False      # ancienne hypothèse
PALIER_OFFICIEL_16 = True        # règle observée dans le fichier officiel : p1 <16T, p2 <30T, p3 >=30T
REPARER_LIGNE_SANS_PRODUIT = False  # le fichier officiel a EXCLU la ligne sans propriétés produit

SEUIL_MIN = 5000                 # montant minimum pour figurer dans la liste

# ----------------------------------------------------------------------
# Chargement
# ----------------------------------------------------------------------
print("Chargement extraction...")
df = pd.read_excel('rist_datas.xlsx', sheet_name='Feuil1')

print(f"Lignes brutes : {len(df)}")

# --- Filtre état --------------------------------------------------------
if INCLURE_NON_LIVREES:
    f_etat = df
else:
    f_etat = df[df['État'] == 'Livrée']
print(f"Après filtre état Livrée : {len(f_etat)} (exclues: {len(df)-len(f_etat)})")

# --- Déduplication -------------------------------------------------------
if DEDUP_LIGNES_IDENTIQUES:
    f_etat = f_etat.drop_duplicates(subset=list(f_etat.columns))
    print(f"Après déduplication exacte : {len(f_etat)}")

# --- Exclusion tiers spéciaux --------------------------------------------
if EXCLURE_TIERS_SPECIAUX:
    masque = f_etat['Tiers'].str.contains('SOLDE COMPTA|NOTE DE DÉBIT|ND INV', case=False, na=False)
    f_etat = f_etat[~masque]
    print(f"Après exclusion tiers spéciaux : {len(f_etat)}")

# --- Exclusion comptoirs génériques ----------------------------------------
if EXCLURE_COMPTOIRS_GENERIQUES:
    masque_comp = f_etat['Tiers'].str.contains('COMPTOIR', case=False, na=False)
    f_etat = f_etat[~masque_comp]
    print(f"Après exclusion comptoirs génériques : {len(f_etat)}")

# --- Ligne sans propriétés produit ------------------------------------------
# 'BELGO 10% CHAIR 50Kg' sans catégorie ni convTonne (1 ligne, SO2511-76465)
nb_nan = f_etat['tableauPropietesProduits.CategorieProduit'].isna().sum()
if nb_nan:
    if REPARER_LIGNE_SANS_PRODUIT:
        masque_nan = f_etat['tableauPropietesProduits.CategorieProduit'].isna()
        f_etat.loc[masque_nan, 'tableauPropietesProduits.CategorieProduit'] = 'CONCENTRES'
        f_etat.loc[masque_nan, 'tableauPropietesProduits.convTonne'] = 0.05
        f_etat.loc[masque_nan, 'Qté commandée (en tonnes)'] = f_etat.loc[masque_nan, 'Qté commandée'] * 0.05
        print(f"Réparées : {nb_nan} lignes sans propriétés produit (reclassées CONCENTRES)")
    else:
        f_etat = f_etat[f_etat['tableauPropietesProduits.CategorieProduit'].notna()]
        print(f"Exclues : {nb_nan} lignes sans propriétés produit (comportement fichier officiel)")

# ----------------------------------------------------------------------
# Mapping produits -> barème
# ----------------------------------------------------------------------
d = f_etat.copy()
d['mois'] = d['Date de commande'].dt.to_period('M')
cat = d['tableauPropietesProduits.CategorieProduit']
ref = d['Réf. produit']

# Familles autres produits
LYS_METH = ['I106', 'I107', 'I1061', 'I1071', 'I1063']          # 250 F/sac 25kg = 10 F/kg
B_10F_KG = ['B100', 'B1001', 'F114', 'F1142', 'F1143', 'F1145', 'F1146', 'F1147',
            'I105', 'I1051', 'P102N2', 'P104N2', 'P109']        # farine/sulfate/bicarbonate/premix 10 F/kg
B_20F_KG = ['E101', 'E1011', 'E1014', 'P105', 'P1051', 'P1053'] # belgotox/belgofos 20 F/kg

# Mapping : par catégorie + réf
d['fam'] = None
d.loc[cat == 'CONCENTRES', 'fam'] = 'CONC'
d.loc[ref.isin(LYS_METH), 'fam'] = 'LYS_METH'
d.loc[ref.isin(B_10F_KG), 'fam'] = '10F'
d.loc[ref.isin(B_20F_KG), 'fam'] = '20F'
# PREMIX non référencé ci-dessus ? P109 inclus dans B_10F_KG. Vérif restants :
restants = d[d['fam'].isna() & d['tableauPropietesProduits.CategorieProduit'].notna()]
print(f"Produits non mappés : {restants['Réf. produit'].nunique()} ({restants['Description du produit'].unique()[:10]})")

# ----------------------------------------------------------------------
# Calcul concentrés : paliers mensuels par (Tiers, Agence)
# ----------------------------------------------------------------------
conc = d[d['fam'] == 'CONC'].copy()
g = conc.groupby(['Tiers', 'tableauProprieteAgences.Agence', 'mois'], as_index=False)['Qté commandée (en tonnes)'].sum()
g.columns = ['Tiers', 'Agence', 'mois', 'tonnes']

def montant_concentres(t):
    if PALIER_OFFICIEL_16:
        # règle observée dans le fichier officiel : seuils {5, 16, 30}
        # (procédure : {5, 15, 30} — écart systématique pour les mois entre 15 et 16 T)
        if t < 5:
            return 0.0
        elif t < 16:
            return t * 7000.0
        elif t < 30:
            return t * 8000.0
        else:
            return t * 10000.0
    else:
        # règle conforme à la procédure V6
        if t < 5:
            return 0.0
        elif t <= 15:
            return t * 7000.0
        elif t <= 30:
            return t * 8000.0
        else:
            return t * 10000.0

g['montant'] = g['tonnes'].apply(montant_concentres)
conc_total = g.groupby(['Tiers', 'Agence'], as_index=False)['montant'].sum()
conc_total.columns = ['Tiers', 'Agence', 'm_conc']

# ----------------------------------------------------------------------
# Calcul autres produits
# ----------------------------------------------------------------------
autre = d[d['fam'] != 'CONC'].copy()
autre['m_ligne'] = 0.0
autre.loc[autre['fam'] == 'LYS_METH', 'm_ligne'] = autre['Qté commandée (en tonnes)'] * 1000 * 10   # 10 F/kg
autre.loc[autre['fam'] == '10F', 'm_ligne'] = autre['Qté commandée (en tonnes)'] * 1000 * 10
autre.loc[autre['fam'] == '20F', 'm_ligne'] = autre['Qté commandée (en tonnes)'] * 1000 * 20
autre_total = autre.groupby(['Tiers', 'tableauProprieteAgences.Agence'], as_index=False)['m_ligne'].sum()
autre_total.columns = ['Tiers', 'Agence', 'm_autre']

# ----------------------------------------------------------------------
# Fusion + seuil
# ----------------------------------------------------------------------
calc = pd.merge(conc_total, autre_total, on=['Tiers', 'Agence'], how='outer').fillna(0)
calc['total'] = calc['m_conc'] + calc['m_autre']
calc = calc[calc['total'] >= SEUIL_MIN].copy()
calc['total'] = calc['total'].round(0).astype(int)
calc = calc.sort_values('total', ascending=False).reset_index(drop=True)
print(f"Résultat calcul : {len(calc)} lignes >= {SEUIL_MIN} FCFA | total = {calc['total'].sum():,} FCFA")

# ----------------------------------------------------------------------
# Comparaison avec Pareto
# ----------------------------------------------------------------------
pareto = pd.read_excel('Rs2025_Pareto_20-80.xlsx', sheet_name='Liste complète', header=2)
pareto = pareto[pareto['Client'].notna() & (pareto['Client'] != 'TOTAL GÉNÉRAL')].copy()
pareto.columns = ['Rang', 'Client', 'Agence', 'Code', 'Conf', 'Montant', 'pct', 'cum', 'Cat']
pareto['Montant'] = pareto['Montant'].astype(int)

calc['cle'] = calc['Tiers'].str.strip().str.upper() + '||' + calc['Agence'].str.strip().str.upper()
pareto['cle'] = pareto['Client'].str.strip().str.upper() + '||' + pareto['Agence'].str.strip().str.upper()

m = pd.merge(calc, pareto[['cle', 'Montant']], on='cle', how='left', suffixes=('', '_par'))
m['ecart'] = m['total'] - m['Montant'].fillna(0)
m['status'] = 'OK'
m.loc[m['Montant'].isna(), 'status'] = 'ABSENT_PARETO'
m.loc[m['Montant'].notna() & (m['ecart'] != 0), 'status'] = 'ECART'

print()
print("=== Résumé de la comparaison ===")
print(m['status'].value_counts().to_string())
print()
print("=== Exemples d'écarts ===")
ec = m[m['status'] == 'ECART']
print(f"{len(ec)} écarts | somme des écarts = {ec['ecart'].sum():,}")
print(ec.head(10).to_string())
print()
print("=== Exemples absents du Pareto ===")
ab = m[m['status'] == 'ABSENT_PARETO']
print(ab.head(10).to_string())
print()
# Lignes Pareto non reproduites
m2 = pd.merge(pareto[['cle', 'Montant']], calc, on='cle', how='left', suffixes=('_par', ''))
missing = m2[m2['total'].isna()]
print(f"=== Lignes Pareto non reproduites : {len(missing)} ===")
print(missing.to_string())
print()
print(f"Somme Pareto = {pareto['Montant'].sum():,} | Somme calcul = {calc['total'].sum():,} | delta = {calc['total'].sum() - pareto['Montant'].sum():,}")

# Sauvegarde pour analyse
m.to_csv('_comparaison.csv', index=False, encoding='utf-8-sig')
print()
print("Comparaison sauvegardée dans _comparaison.csv")
