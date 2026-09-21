# -*- coding: utf-8 -*-
"""Génère le fichier des commandes échues au 03/10 (non livrées) + feuille Reclassées.

- Feuille « Echues 03-10 » : commandes agences BELGO non livrées (reste > 0) dont
  date_prévue <= 03/10/2026 (PONTE + COQ, COQ marqués Type=COQ).
- Feuille « Reclassees » : PONTE uniquement (pas de COQ), non livrées (reste > 0),
  date de commande <= aujourd'hui - 2 mois (11/07/2026), reclassée au sens §4
  (date_modif > date_commande ET date_modif < date_prévue - 5j). AUCUN filtre
  d'échéance (indépendante du 03/10).
"""
import sys
from datetime import timedelta

import pandas as pd

from md_config import load_config

AT = 'extractions/NJS GROUP ERP - Lignes de commandes + multicompany (44).xlsx'
OUT = 'output/Commandes_echuees_03-10.xlsx'

REF_DATE_ECHUE = pd.Timestamp('2026-10-03')   # échéance du fichier principal
DATE_CMDE_MAX = pd.Timestamp('2026-07-21')    # aujourd'hui (21/09/2026) - 2 mois

config = load_config('Contraintes du Plan de Livraisons BELGO.md')
EXCLUSIONS = set(config['exclusions'].keys())


def parse_date(d):
    try:
        return pd.to_datetime(d, dayfirst=True)
    except Exception:
        return None


def normalize_region(agence):
    a = str(agence).upper().strip()
    if 'NKOABANG' in a or 'MESSASSI' in a or 'AHA' in a or 'ETOUDI' in a or 'EMANA' in a or 'NKOLBISSON' in a or 'KYE-OSSI' in a or 'KYE' in a:
        return 'Centre'
    elif 'FAMLA' in a or 'NDJELENG' in a or 'CHEFFERIE' in a or 'MBOUDA' in a or 'DSCHANG' in a:
        return 'Ouest'
    elif 'BERTOUA' in a and 'PDC' not in a:
        return 'Est'
    elif 'NDERE' in a or ('BERTOUA' in a and 'PDC' in a) or ('PK15' in a and 'SPC' in a):
        return 'Nord'
    elif 'BERI' in a or 'BUEA' in a or 'NKONGSAMBA' in a or 'TPO' in a or 'VILLAGE' in a or 'PK11' in a or 'YASSA' in a:
        return 'Littoral'
    return 'Inconnu'


at = pd.read_excel(AT, header=1)
at['Réf.'] = at['Réf.'].astype(str).str.strip()

rows = []
for _, r in at.iterrows():
    agence = str(r.get('agence', '')).strip()
    if not agence.upper().startswith('BELGO'):
        continue
    tiers = str(r.get('Tiers', '')).strip()
    produit = str(r.get('Description du produit', '')).strip()
    date_prevue = parse_date(r.get('Date prévue de livraison'))
    date_commande = parse_date(r.get('Date de commande'))
    date_modif = parse_date(r.get('Date modif.'))

    is_reclassee = False
    if (date_modif is not None and date_commande is not None and date_prevue is not None
            and not pd.isna(date_modif) and not pd.isna(date_commande) and not pd.isna(date_prevue)):
        modif_d = date_modif.date()
        cmd_d = date_commande.date()
        prevue_d = date_prevue.date()
        if modif_d > cmd_d and modif_d < prevue_d - timedelta(days=5):
            is_reclassee = True

    rows.append({
        'Réf.': r['Réf.'],
        'Tiers': tiers,
        'Produit': produit,
        'Type': 'COQ' if 'COQ' in produit.upper() else 'PONTE',
        'Agence': agence,
        'Région': normalize_region(agence),
        'Qté commandée': float(r.get('Qté commandée', 0) or 0),
        'Déjà livré': float(r.get('Quantité deja livrée', 0) or 0),
        'Reste': float(r.get('Quantité restante à livrer', 0) or 0),
        'Date prévue': date_prevue,
        'Date commande': date_commande,
        'Date modif.': date_modif,
        'État': str(r.get('État', '')).strip(),
        'Reclassée': is_reclassee,
        'Exclu §12': r['Réf.'] in EXCLUSIONS,
    })

df = pd.DataFrame(rows)

# --- Feuille 1 : Échues au 03/10 (non livrées, État Validée/En cours uniquement) ---
ETATS_OK = ['Validée', 'En cours']
ech = df[(df['État'].isin(ETATS_OK)) & (df['Date prévue'].notna()) & (df['Date prévue'] <= REF_DATE_ECHUE) & (df['Reste'] > 0)].copy()
ech['Échéance'] = ech['Reclassée'].map({True: 'ÉCHUE RECLASSÉE', False: 'ÉCHUE'})
ech = ech.sort_values(['Date prévue', 'Reste'], ascending=[True, False])
ech_out = ech[['Réf.', 'Tiers', 'Produit', 'Type', 'Agence', 'Région', 'Qté commandée',
               'Déjà livré', 'Reste', 'Date prévue', 'Date commande', 'État', 'Échéance', 'Exclu §12']].copy()
for c in ['Date prévue', 'Date commande']:
    ech_out[c] = ech_out[c].dt.strftime('%d/%m/%Y')

# --- Feuille 2 : Reclassées (PONTE uniquement, non livrées, État Validée/En cours, date commande <= 2 mois, SANS filtre d'échéance) ---
rec = df[(df['État'].isin(ETATS_OK)) & (df['Type'] == 'PONTE') & (df['Reclassée']) & (df['Reste'] > 0)
         & (df['Date commande'].notna()) & (df['Date commande'] <= DATE_CMDE_MAX)].copy()
rec = rec.sort_values(['Date commande', 'Reste'], ascending=[True, False])
rec_out = rec[['Réf.', 'Tiers', 'Produit', 'Agence', 'Région', 'Qté commandée',
               'Déjà livré', 'Reste', 'Date commande', 'Date modif.', 'Date prévue', 'État', 'Exclu §12']].copy()
for c in ['Date commande', 'Date modif.', 'Date prévue']:
    rec_out[c] = rec_out[c].dt.strftime('%d/%m/%Y')

with pd.ExcelWriter(OUT, engine='openpyxl') as writer:
    for sheet, d in [('Echues 03-10', ech_out), ('Reclassees', rec_out)]:
        d.to_excel(writer, sheet_name=sheet, index=False)
        ws = writer.sheets[sheet]
        ws.freeze_panes = 'A2'
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        for col, width in zip(d.columns, [14, 32, 24, 8, 16, 10, 13, 11, 9, 12, 12, 12, 16, 9]):
            ws.column_dimensions[ws.cell(row=1, column=d.columns.get_loc(col) + 1).column_letter].width = width

# --- Résumé console ---
print(f"\n=== Fichier généré : {OUT} ===")
print(f"\nEchues au 03/10 (non livrées) : {len(ech_out)} commandes — {ech['Reste'].sum():,.0f} sujets")
print(f"  PONTE : {len(ech[ech['Type']=='PONTE'])} | COQ : {len(ech[ech['Type']=='COQ'])}")
print(f"  ÉCHUE RECLASSÉE : {len(ech[ech['Échéance']=='ÉCHUE RECLASSÉE'])} | Exclues §12 : {len(ech[ech['Exclu §12']])}")
print("\n  Par région (sujets):")
for reg in ['Centre', 'Ouest', 'Nord', 'Est', 'Littoral', 'Inconnu']:
    sub = ech[ech['Région'] == reg]
    if len(sub):
        print(f"    {reg}: {len(sub)} commandes, {sub['Reste'].sum():,.0f} sujets")

print(f"\nReclassées (PONTE non livrées, date commande <= 21/07/2026, sans filtre d'échéance) : {len(rec_out)} commandes")
if len(rec):
    print(f"  dont non livrées (reste > 0) : {len(rec[rec['Reste']>0])} — {rec[rec['Reste']>0]['Reste'].sum():,.0f} sujets")
    print(f"  Exclues §12 : {len(rec[rec['Exclu §12']])}")
