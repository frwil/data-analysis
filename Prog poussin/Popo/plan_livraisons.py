#!/usr/bin/env python3
"""
Plan de Livraisons BELGO - v15 (15/05/2026)
============================================
Mise à jour v15:
- Restauration du 14/05 dans le plan de production (Centre, 30 000)
- REGION_LOCK_DATES: 14/05→Centre, 20/05→Ouest+Littoral, 25/05→Centre
- Ajout NO_SPLIT: commandes à livrer intégralement (SO2604-51319, SO2602-47700)
- Refonte FORCED_ASSIGNMENTS par date (14/05, 15/05, 20/05, 26/05)
- SPECIAL_INCLUDE: SO2603-47945 réactivé (AGRO-TMC-AKWA → BELGO-FAMLA)
- Nouvelles exclusions: SO2604-52423, SO2601-42254
- REF_DATE = 15/05/2026

Historique v11-v14:
- RÈGLE LITTORAL: Le Littoral peut être inséré tous les jours.
  La contrainte de max 2 régions/jour ne compte pas le Littoral
  si ses qtés sont minimes (≤25% capacité du jour).
- ALGORITHME PAR PHASES STRICTES:
  Phase 1: ÉCHUE + ÉCHUE RECLASSÉE + RECLASSÉE + SANS DATE
  Phase 2: IMMINENTE (force majeure, si Phase 1 complète)
  Phase 3: NON ÉCHUE (force majeure, si Phase 1+2 complète)

Feuilles de sortie:
- Plan Réel / Plan Marge / Commandes non planifiées / Analyse Expéditions
- Détail Expéditions / Livraisons Coq / Plan de Production
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta, date
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Force UTF-8 pour la console Windows
sys.stdout.reconfigure(encoding='utf-8')

# Charger la configuration depuis le fichier de contraintes .md
from md_config import load_config, write_execution_results

MD_PATH = 'Contraintes du Plan de Livraisons BELGO.md'
config = load_config(MD_PATH)

# ============================================================================
# CONFIGURATION
# ============================================================================

ATR_FILE = os.path.join('extractions', 'AT_2026-06-02.xlsx')
EXP_FILE = os.path.join('extractions', 'EXP_2026-06-02.xlsx')
OUTPUT_FILE = os.path.join('output', 'Plan_Livraisons_BELGO_Ponte.xlsx')

REF_DATE = config['ref_date'] or datetime(2026, 5, 15)

# Seules les agences dont le nom COMMENCE par BELGO sont BELGO
# SPC et PDC ne sont PAS des agences BELGO
BELGO_PREFIX = 'BELGO'

# EXCLUSIONS chargées depuis le .md (source unique de vérité)
EXCLUSIONS = dict(config['exclusions'])

# Stockage pour les nouvelles auto-exclusions découvertes lors de l'exécution
NEW_AUTO_EXCLUSIONS = {}

CLIENT_EXCLU = 'TEDONGMO YEMDJI FRANCK'

# FORCED_ASSIGNMENTS chargées depuis le .md
FORCED_ASSIGNMENTS = dict(config['forced_assignments'])

TAMATIO_CLIENT = 'TAMATIO'

# SPECIAL_INCLUDE chargé depuis le .md
SPECIAL_INCLUDE = dict(config['special_include'])

# NO_SPLIT chargé depuis le .md
NO_SPLIT = set(config['no_split'])

# ============================================================================
# RÈGLE DE SPLIT (Contrainte n°13)
# ============================================================================
# Règle : au moins la moitié de la quantité totale si pas encore splitée,
# sinon totalité du reste à livrer.
# - Premier split : la livraison doit être >= 50% de la qté totale restante
# - Si déjà splitée : on doit livrer la totalité du reste (pas de 2e split)
# Cela évite des splits non pertinents (ex: livrer 1000 sur 25000).
# La capacité non utilisée est marquée "Qté manquante" dans le plan.
MIN_SPLIT_FIRST_RATIO = 0.5   # Premier split : minimum 50% de la qté totale

# ============================================================================
# CONTRAINTES DE JOURS PAR RÉGION
# ============================================================================
# Nord et Est ne peuvent PAS être planifiés le mardi
# (sauf exception explicite dans FORCED_ASSIGNMENTS)
# Lundi=0, Mardi=1, Mercredi=2, Jeudi=3, Vendredi=4, Samedi=5, Dimanche=6
RESTRICTED_DAYS = {
    'Nord': {1},   # Pas le mardi
    'Est':  {1},   # Pas le mardi
}

def is_day_allowed(region, date):
    """Vérifie si une région peut être planifiée à cette date.
    Exception: les assignations forcées contournent cette règle."""
    if region in RESTRICTED_DAYS:
        if date.weekday() in RESTRICTED_DAYS[region]:
            return False
    return True

# Plan de production chargé depuis le .md
PRODUCTION_PLAN = dict(config['production_plan'])

# Région principale chargée depuis le .md
PRODUCTION_REGIONS = dict(config['production_regions'])

# Verrouillage régional chargé depuis le .md
REGION_LOCK_DATES = dict(config['region_lock_dates'])

# Dates autorisant le complément NON ÉCHUE (toutes les dates de production)
DATES_NON_ECHUE_FILL = set(config['production_plan'].keys())

# Commandes exclues de dates spécifiques — chargées depuis le .md
EXCLUDED_FROM_DATE = {}
for ref, dates_set in config['excluded_from_date'].items():
    EXCLUDED_FROM_DATE[ref] = dates_set

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

print("Chargement des données...")

df_atr = pd.read_excel(ATR_FILE, header=1)
df_exp = pd.read_excel(EXP_FILE, header=1)

print(f"  AT: {len(df_atr)} lignes")
print(f"  EXP: {len(df_exp)} lignes")

# ============================================================================
# v14: NOUVEAU FORMAT AT — colonnes directement disponibles
# Le nouveau fichier AT (12) contient directement les colonnes 'agence',
# 'Quantité deja livrée' et 'Quantité restante à livrer'.
# Plus besoin de mapping depuis les anciens fichiers.
# ============================================================================

# Vérifier que les colonnes nécessaires sont présentes
required_atr_cols = {'Réf.', 'Tiers', 'Qté commandée', 'État', 'agence', 
                     'Quantité deja livrée', 'Quantité restante à livrer'}
missing_atr = required_atr_cols - set(df_atr.columns)
if missing_atr:
    print(f"  ⚠ Colonnes AT manquantes: {missing_atr}")
    print(f"  ⚠ Abandon de la mise à jour — colonnes incomplètes")
else:
    print(f"  ✓ Toutes les colonnes AT requises sont présentes")

required_exp_cols = {'Ref. Commande', 'Auteur', 'Status Commande', 'Agence'}
missing_exp = required_exp_cols - set(df_exp.columns)
if missing_exp:
    print(f"  ⚠ Colonnes EXP manquantes: {missing_exp}")
else:
    print(f"  ✓ Toutes les colonnes EXP requises sont présentes")

# ============================================================================
# IDENTIFICATION PROCTOR AI + STATUS COMMANDE
# ============================================================================

print("\nIdentification Proctor Ai + Status Commande...")

# Règle: Proctor Ai + "Livrée" = livraison réelle
#         Proctor Ai + "En cours" = mouvement système
proctor_livree_refs = set()   # Proctor Ai mais vraiment livré
proctor_en_cours_refs = set() # Proctor Ai = mouvement système uniquement

for ref in df_atr['Réf.'].unique():
    ref_str = str(ref).strip()
    exp_rows = df_exp[df_exp['Ref. Commande'] == ref_str]
    if len(exp_rows) == 0:
        continue
    
    proctor_rows = exp_rows[exp_rows['Auteur'] == 'Proctor Ai']
    non_proctor_rows = exp_rows[exp_rows['Auteur'] != 'Proctor Ai']
    
    if len(proctor_rows) > 0 and len(non_proctor_rows) == 0:
        # Toutes les expéditions sont Proctor Ai
        if 'Status Commande' in exp_rows.columns:
            statuses = set(exp_rows['Status Commande'].dropna().unique())
            if 'Livrée' in statuses:
                # Au moins une livrée → livraison réelle
                proctor_livree_refs.add(ref_str)
            else:
                # Que "En cours" → mouvement système
                proctor_en_cours_refs.add(ref_str)
        else:
            proctor_en_cours_refs.add(ref_str)

print(f"  Proctor Ai 'Livrée' (livraison réelle): {len(proctor_livree_refs)} commandes")
print(f"  Proctor Ai 'En cours' (mouvement système): {len(proctor_en_cours_refs)} commandes")

# ============================================================================
# AUTO-EXCLUSION: État="Livrée" dans le nouveau AT
# Le nouveau AT contient TOUTES les commandes (pas seulement À traiter).
# Les commandes avec État="Livrée" sont déjà livrées et doivent être exclues.
# ============================================================================

print("\nAuto-exclusion (État=Livrée dans AT)...")
if 'État' in df_atr.columns and 'agence' in df_atr.columns:
    livree_in_at = df_atr[df_atr['État'] == 'Livrée']
    for _, row in livree_in_at.iterrows():
        ref_str = str(row.get('Réf.', '')).strip()
        agence = str(row.get('agence', '')).strip()
        if agence.upper().startswith(BELGO_PREFIX):
            if ref_str not in EXCLUSIONS:
                raison = "Auto-exclue: État='Livrée' dans AT (commande déjà livrée)"
                EXCLUSIONS[ref_str] = raison
                NEW_AUTO_EXCLUSIONS[ref_str] = raison
    print(f"  Commandes auto-exclues État=Livrée: {len(livree_in_at)} refs")

# Auto-exclusion: Status Commande="Livrée" dans EXP (pour commandes pas dans AT)
if 'Status Commande' in df_exp.columns and 'Agence' in df_exp.columns:
    livree_refs_exp = df_exp[df_exp['Status Commande'] == 'Livrée']
    at_refs = set(df_atr['Réf.'].dropna().unique())
    auto_excluded_refs = set(livree_refs_exp['Ref. Commande'].dropna().unique()) - at_refs

    for _, row in livree_refs_exp[livree_refs_exp['Ref. Commande'].isin(auto_excluded_refs)].iterrows():
        ref_str = str(row.get('Ref. Commande', '')).strip()
        agence = str(row.get('Agence', '')).strip()
        if agence.upper().startswith(BELGO_PREFIX):
            if ref_str not in EXCLUSIONS:
                raison = "Auto-exclue: Status Commande='Livrée' et absente de AT"
                EXCLUSIONS[ref_str] = raison
                NEW_AUTO_EXCLUSIONS[ref_str] = raison

    print(f"  Commandes auto-exclues EXP Livrée hors AT: {len(auto_excluded_refs)}")

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def parse_date(d):
    if pd.isna(d):
        return None
    if isinstance(d, datetime):
        return d
    try:
        return pd.to_datetime(d, dayfirst=True)
    except:
        return None

def normalize_region(region, agence=''):
    r = str(region).upper().strip()
    a = str(agence).upper().strip()
    # Centre : BELGO AHALA, BELGO-MESSASSI, BELGO-NKOABANG, BELGO-NKOLBISSON, PDC Emana, SPC KYE-OSSI
    if 'CENTRE' in r or 'NKOABANG' in a or 'MESSASSI' in a or 'AHA' in a or 'ETOUDI' in a or 'EMANA' in a or 'NKOLBISSON' in a or 'KYE-OSSI' in a or 'KYE' in a:
        return 'Centre'
    # Ouest : BELGO MBOUDA, BELGO-FAMLA, BELGO-NDJELENG, SPC BAF-CHEFFERIE, SPC MBOUDA, SPC-DSCHANG
    elif 'OUEST' in r or 'FAMLA' in a or 'NDJELENG' in a or 'CHEFFERIE' in a or 'MBOUDA' in a or 'DSCHANG' in a:
        return 'Ouest'
    # Est : BELGO BERTOUA (sans PDC)
    elif 'EST' in r or ('BERTOUA' in a and 'PDC' not in a):
        return 'Est'
    # Nord : BELGO-NDERE, PDC BERTOUA, SPC-NDERE, SPC PK15
    elif 'NORD' in r or 'NDERE' in a or ('BERTOUA' in a and 'PDC' in a) or ('PK15' in a and 'SPC' in a):
        return 'Nord'
    # Littoral : BELGO PK11, BELGO PK15, BELGO VILLAGE, BELGO-BERI, BELGO-BUEA, BELGO-NKONGSAMBA, SPC-BUEA, SPC-DLA-BERI, SPC-TPO, SPC-YASSA
    elif 'LITTORAL' in r or 'BERI' in a or 'BUEA' in a or 'NKONGSAMBA' in a or 'TPO' in a or 'VILLAGE' in a or 'PK11' in a or 'YASSA' in a:
        return 'Littoral'
    else:
        return 'Inconnu'

# ============================================================================
# PRÉPARATION DES COMMANDES
# ============================================================================

print("\nPréparation des commandes...")

orders = []
agence_not_found = []
for _, row in df_atr.iterrows():
    ref = str(row.get('Réf.', '')).strip()
    if not ref or ref == 'nan':
        continue
    
    # v14: Agence vient directement de la colonne 'agence' du nouveau AT
    agence = str(row.get('agence', '')).strip()
    if not agence or agence == 'nan':
        agence_not_found.append(ref)
        continue
    
    is_belgo = agence.upper().startswith(BELGO_PREFIX)
    is_special = ref in SPECIAL_INCLUDE  # Inclusion exceptionnelle (agence non-BELGO)
    if not is_belgo and not is_special:
        continue
    
    if ref in EXCLUSIONS:
        continue
    
    tiers = str(row.get('Tiers', '')).strip()
    if CLIENT_EXCLU in tiers:
        continue
    
    statut_facture = str(row.get('StatutFacture', '')).strip()
    if statut_facture == 'Impayée':
        continue
    
    # v12: Le nouveau AT a la colonne État (Livrée/Validée/En cours/Brouillon)
    # Utiliser État pour filtrer les commandes déjà livrées ou en brouillon
    etat_atr = str(row.get('État', '')).strip()
    if etat_atr == 'Brouillon' or statut_facture == 'Brouillon':
        continue
    
    qte_commandee = float(row.get('Qté commandée', 0))
    ref_produit = str(row.get('Réf. produit', '')).strip()
    
    # v14: Le nouveau AT (12) contient directement les colonnes
    # 'Quantité deja livrée' et 'Quantité restante à livrer'
    qte_livree_sys = float(row.get('Quantité deja livrée', 0))
    qte_restante_sys = float(row.get('Quantité restante à livrer', 0))
    
    # Ajustement Proctor Ai avec Status Commande
    # IMPORTANT: Si qte_restante_sys = 0, on fait confiance à l'AT
    # (la commande est réellement livrée, même si Proctor Ai est "En cours")
    if qte_restante_sys <= 0:
        qte_livree_reelle = qte_livree_sys
        qte_restante = qte_restante_sys
    elif ref in proctor_en_cours_refs:
        # Proctor Ai "En cours" = mouvement système → les qtés "livrées" sont gonflées
        # On réinitialise: rien n'a été réellement livré
        qte_livree_reelle = 0
        qte_restante = qte_commandee
    elif ref in proctor_livree_refs:
        # Proctor Ai "Livrée" = livraison réelle → les quantités système sont correctes
        qte_livree_reelle = qte_livree_sys
        qte_restante = qte_restante_sys
    else:
        # Pas d'expédition Proctor Ai ou mixte → quantités système
        qte_livree_reelle = qte_livree_sys
        qte_restante = qte_restante_sys
    
    if qte_restante <= 0:
        continue
    
    date_prevue = parse_date(row.get('Date prévue de livraison'))
    date_commande = parse_date(row.get('Date de commande'))
    date_modif = parse_date(row.get('Date modif.'))
    
    region_norm = normalize_region('', agence)
    produit = str(row.get('Description du produit', '')).strip()
    ref_produit = str(row.get('Réf. produit', '')).strip()
    
    # SPECIAL_INCLUDE: surcharger agence et région si inclusion exceptionnelle
    if is_special:
        override = SPECIAL_INCLUDE[ref]
        agence = override.get('agence', agence)
        region_norm = override.get('region', region_norm)
    
    # Classification
    if date_prevue is None or pd.isna(date_prevue):
        priority_num, priority_label = 5, 'SANS DATE'
    else:
        is_reclassee = False
        if (date_modif and not pd.isna(date_modif) and date_commande and not pd.isna(date_commande)
            and isinstance(date_modif, datetime) and isinstance(date_commande, datetime) 
            and isinstance(date_prevue, datetime)):
            # Comparer les dates (pas les heures) pour éviter les faux positifs
            # quand date_modif = date_commande (même jour, heure différente)
            modif_date = date_modif.date()
            cmd_date = date_commande.date()
            prevue_date = date_prevue.date()
            if modif_date > cmd_date and modif_date < prevue_date - timedelta(days=5):
                is_reclassee = True
        
        is_echue = date_prevue <= REF_DATE
        is_imminente = not is_echue and (date_prevue - REF_DATE).days <= 10
        
        if is_echue and is_reclassee:
            priority_num, priority_label = 2, 'ÉCHUE RECLASSÉE'
        elif is_echue:
            priority_num, priority_label = 1, 'ÉCHUE'
        elif is_reclassee:
            priority_num, priority_label = 3, 'RECLASSÉE'
        elif is_imminente:
            priority_num, priority_label = 4, 'IMMINENTE'
        else:
            priority_num, priority_label = 6, 'NON ÉCHUE'
    
    is_coq = 'COQ' in produit.upper()
    
    orders.append({
        'ref': ref,
        'tiers': tiers,
        'agence': agence,
        'region': '',
        'region_norm': region_norm,
        'produit': produit,
        'ref_produit': ref_produit,
        'qte_commandee': int(qte_commandee),
        'qte_livree_sys': int(qte_livree_sys),
        'qte_livree_reelle': int(qte_livree_reelle),
        'qte_restante': int(qte_restante),
        'date_prevue': date_prevue,
        'date_commande': date_commande,
        'date_modif': date_modif,
        'priority_num': priority_num,
        'priority_label': priority_label,
        'proctor_only': ref in proctor_en_cours_refs,
        'forced_date': FORCED_ASSIGNMENTS.get(ref),
        'is_tamatio': TAMATIO_CLIENT in tiers.upper(),
        'is_coq': is_coq,
        'statut_facture': statut_facture,
    })

df_orders = pd.DataFrame(orders)

# Rapporter les agences non trouvées
if agence_not_found:
    unique_not_found = set(agence_not_found)
    print(f"  ⚠ {len(unique_not_found)} refs sans agence dans le mapping (exclues du plan):")
    for ref in sorted(unique_not_found)[:10]:
        print(f"    {ref}")
    if len(unique_not_found) > 10:
        print(f"    ... et {len(unique_not_found) - 10} autres")

# Séparer PONTE et COQ
df_ponte = df_orders[~df_orders['is_coq']].copy()
df_coq = df_orders[df_orders['is_coq']].copy()

print(f"  PONTE: {len(df_ponte)} commandes, {df_ponte['qte_restante'].sum():,} sujets")
print(f"  COQ: {len(df_coq)} commandes, {df_coq['qte_restante'].sum():,} sujets")

# Vérifier les régions
print(f"\n  Répartition par région (PONTE):")
for region in ['Centre', 'Ouest', 'Nord', 'Est', 'Littoral', 'Inconnu']:
    count = len(df_ponte[df_ponte['region_norm'] == region])
    qty = df_ponte[df_ponte['region_norm'] == region]['qte_restante'].sum()
    print(f"    {region}: {count} commandes, {qty:,} sujets")

# Vérifier les inconnus
inconnu = df_ponte[df_ponte['region_norm'] == 'Inconnu']
if len(inconnu) > 0:
    print(f"\n  ⚠ Agences non mappées:")
    for _, o in inconnu.iterrows():
        print(f"    {o['ref']}: agence={o['agence']}, tiers={o['tiers']}")

# ============================================================================
# PLANIFICATION PONTE — v10 (Algorithme par phases strictes)
# ============================================================================
#
# PRINCIPE CLÉ :
# - Phase 1 : ÉCHUE + ÉCHUE RECLASSÉE + RECLASSÉE + SANS DATE (priorités 1-3, 5)
#   → Ces commandes sont planifiées EN PREMIER, toutes régions confondues
#   → Flexibilité régionale : si la région principale du jour est pleine,
#     les commandes ÉCHUE d'autres régions peuvent remplir la capacité restante
#
# - Phase 2 : IMMINENTE (priorité 4) — FORCE MAJEURE UNIQUEMENT
#   → N'entre QUE si TOUTES les commandes de Phase 1 sont planifiées
#   → Respect strict de la région du jour (pas de cross-région)
#
# - Phase 3 : NON ÉCHUE (priorité 6) — FORCE MAJEURE UNIQUEMENT
#   → N'entre QUE si TOUTES les commandes de Phase 1+2 sont planifiées
#   → Respect strict de la région du jour (pas de cross-région)
#
# TRI STRICT dans chaque phase :
#   1. Priorité (ÉCHUE > ÉCHUE RECLASSÉE > RECLASSÉE > SANS DATE)
#   2. ≤1000 sujets EN PREMIER dans chaque catégorie d'échéance (1-3)
#   3. FIFO par date_prévue (la plus ancienne d'abord)
# ============================================================================

print("\nPlanification PONTE (v11 — algorithme par phases + règle Littoral)...")

# Ordre de planification:
#   Phase 1: ÉCHUE(1) → ÉCHUE RECLASSÉE(2) → RECLASSÉE(3) → SANS DATE(5)
#   Phase 2: IMMINENTE ≤1000 (4) — force majeure mais ≤1000 prioritaire
#   Phase 3: IMMINENTE >1000 (4) — force majeure
#   Phase 4: NON ÉCHUE (6) — force majeure, SEULEMENT si tout le reste est épuisé
#
# RÈGLE: un cas de force majeure NON ÉCHUE ne peut être inséré QUE si on a
# épuisé toutes les possibilités des commandes ÉCHUE, ÉCHUE RECLASSÉE,
# et inférieures à 1000 (de TOUTES catégories confondues).
SCHEDULE_PRIORITY = {1: 1, 2: 2, 3: 3, 5: 4, 4: 5, 6: 6}

# Phase 1 = priorités haute (1-3, 5) ; Phase 2 = IMMINENTE ≤1000 ; Phase 3 = IMMINENTE >1000 ; Phase 4 = NON ÉCHUE (6)
HIGH_PRIORITY_NUMS = {1, 2, 3, 5}  # ÉCHUE, ÉCHUE RECLASSÉE, RECLASSÉE, SANS DATE
IMMINENTE_NUM = 4
NON_ECHUE_NUM = 6

# Clé de tri strict: priorité > ≤1000 > FIFO > quantité
# ≤1000 est un critère PRINCIPAL dans TOUTES les catégories d'échéance
# (pas seulement ÉCHUE, mais aussi RECLASSÉE, SANS DATE, IMMINENTE)
def strict_sort_key(row):
    sp = SCHEDULE_PRIORITY[row['priority_num']]
    # ≤1000 en priorité dans TOUTES les catégories (critère PRINCIPAL avant FIFO)
    # NON ÉCHUE est toujours en dernier, mais ≤1000 est prioritaire même au sein de NON ÉCHUE
    if row['priority_num'] == NON_ECHUE_NUM:
        if row['qte_restante'] <= 1000:
            sub = 2  # NON ÉCHUE ≤1000 : avant NON ÉCHUE >1000
        else:
            sub = 3  # NON ÉCHUE >1000 : tout à la fin
    elif row['qte_restante'] <= 1000:
        sub = 0  # ≤1000 toujours en priorité
    else:
        sub = 1  # >1000
    # FIFO par date prévue
    dp = row['date_prevue'] if pd.notna(row['date_prevue']) else pd.Timestamp('2099-12-31')
    return (sp, sub, dp, -row['qte_restante'])

df_ponte['sort_key'] = df_ponte.apply(strict_sort_key, axis=1)
df_ponte = df_ponte.sort_values('sort_key').reset_index(drop=True)

prod_dates = sorted(PRODUCTION_PLAN.keys())

print(f"  Dates de production: {[d.strftime('%d/%m') for d in prod_dates]}")
total_cap_reelle = sum(PRODUCTION_PLAN[d][0] for d in prod_dates)
total_cap_marge = sum(PRODUCTION_PLAN[d][1] for d in prod_dates)
print(f"  Capacité totale Réelle: {total_cap_reelle:,}")
print(f"  Capacité totale Marge: {total_cap_marge:,}")

# Afficher le tri pour vérification
print(f"\n  Ordre de planification (10 premières):")
for i, (_, r) in enumerate(df_ponte.head(10).iterrows()):
    dp = r['date_prevue'].strftime('%d/%m/%Y') if pd.notna(r['date_prevue']) else 'N/A'
    print(f"    {i+1}. {r['ref']} | {r['priority_label']:20s} | qte={r['qte_restante']:,} | date_prevue={dp} | region={r['region_norm']}")

# Allocation pour Plan Réel et Plan Marge
def run_allocation(df_orders, capacity_key):
    """
    Algorithme d'allocation par phases strictes (v10):
    
    Phase 1 : Commandes ÉCHUE/ÉCHUE RECLASSÉE/RECLASSÉE/SANS DATE
      - Planifiées en PREMIER, toutes régions confondues
      - Flexibilité régionale : les ÉCHUE d'autres régions peuvent utiliser
        la capacité restante d'un jour assigné à une autre région
      - Tri: priorité > ≤1000 > FIFO
    
    Phase 2 : IMMINENTE (force majeure)
      - UNIQUEMENT si plus aucune commande Phase 1 ne peut être planifiée
      - Respect strict de la région (pas de cross-région)
      - Marquées "FORCE MAJEURE" dans les observations
    
    Phase 3 : NON ÉCHUE (force majeure)
      - UNIQUEMENT si plus aucune commande Phase 1+2 ne peut être planifiée
      - Respect strict de la région (pas de cross-région)
      - Marquées "FORCE MAJEURE" dans les observations
    """
    
    allocations = {d: {'regions': set(), 'orders': [], 'qty_used': 0} for d in prod_dates}
    remaining_qty = dict(zip(df_orders['ref'], df_orders['qte_restante']))
    scheduled_refs = set()
    # Utiliser un contenteur mutable pour le suivre à travers les closures
    tamatio_state = {'preferred_date': None}
    
    def get_total_littoral_remaining():
        """Total quantité Littoral restante (non encore planifiée)."""
        total = 0
        for _, o in df_orders[df_orders['region_norm'] == 'Littoral'].iterrows():
            total += remaining_qty.get(o['ref'], 0)
        return total
    
    def get_cap(date):
        real_cap, marge_cap = PRODUCTION_PLAN[date]
        cap = marge_cap if capacity_key == 'marge' else real_cap
        return cap - allocations[date]['qty_used']
    
    # =====================================================================
    # RÈGLE LITTORAL (v11):
    # - Si les qtés ÉCHUE du Littoral sont CONSÉQUENTES (>25% capacité),
    #   le Littoral doit avoir sa PROPRE JOURNÉE dédiée.
    # - Si les qtés sont MINIMES (≤25% capacité), le Littoral peut être
    #   inséré dans la journée d'une autre région sans compter dans la
    #   limite des 2 régions par jour.
    # Seuil: "conséquent" si qté > 25% de la capacité du jour.
    # =====================================================================
    LITTORAL_MINIMAL_RATIO = 0.25  # 25% de la capacité du jour
    
    def get_littoral_qty(date):
        """Total quantité Littoral déjà allouée sur cette date."""
        return sum(o['qte'] for o in allocations[date]['orders'] if o['region'] == 'Littoral')
    
    def is_littoral_significant(date, additional_littoral_qty=0):
        """Détermine si les qtés Littoral sont conséquentes sur cette date.
        Se base uniquement sur les qtés déjà allouées + la commande en cours.
        Le total Littoral restant est vérifié séparément dans la logique
        de pré-planification."""
        littoral_qty = get_littoral_qty(date) + additional_littoral_qty
        if littoral_qty <= 0:
            return False
        cap = PRODUCTION_PLAN[date][0 if capacity_key == 'reelle' else 1]
        return littoral_qty > cap * LITTORAL_MINIMAL_RATIO
    
    def effective_region_count(regions_set, date, additional_littoral_qty=0):
        """Compte les régions effectives: non-Littoral + Littoral si conséquent.
        Littoral 'conséquent' si qtés > 25% de la capacité du jour.
        Si minime, Littoral ne compte pas dans le total."""
        non_litt = len([r for r in regions_set if r != 'Littoral'])
        # Vérifier si Littoral est conséquent
        if 'Littoral' in regions_set or additional_littoral_qty > 0:
            if is_littoral_significant(date, additional_littoral_qty):
                return non_litt + 1  # Littoral conséquent = compte comme région
        return non_litt  # Littoral minime = ne compte pas
    
    def regions_compatible_strict(existing, new_region, date=None, new_qty=0):
        """Compatibilité région stricte pour Phase 2/3.
        - Même région ou Est+Nord: toujours OK
        - Littoral conséquent: doit avoir sa PROPRE journée (refusé si autres régions)
        - Littoral minime: insérable sans compter dans la limite
        - Max 2 régions effectives
        - En mode strict, pas de 2ème région hors-Littoral sauf Est+Nord"""
        if not existing:
            return True
        if new_region in existing:
            return True
        est_nord = {'Est', 'Nord'}
        if existing.issubset(est_nord) and new_region in est_nord:
            return True
        # Littoral: comportement dépend de ses qtés
        if new_region == 'Littoral':
            non_litt_existing = [r for r in existing if r != 'Littoral']
            if non_litt_existing and is_littoral_significant(date, new_qty):
                # Littoral conséquent + autres régies présentes → REFUSÉ
                # Le Littoral doit avoir sa propre journée dédiée
                return False
            # Littoral minime: insérable sans compter
            # Mais vérifier quand même le compte effectif max 2
            new_regions = existing | {new_region}
            eff_count = effective_region_count(new_regions, date, new_qty)
            return eff_count <= 2
        # Non-Littoral: en mode strict, pas de 2ème région hors-Littoral
        # sauf si seule région existante est Littoral (minime ou pas)
        non_litt_existing = [r for r in existing if r != 'Littoral']
        if len(non_litt_existing) == 0:
            # Seul Littoral présent → vérifier si Littoral est conséquent
            if 'Littoral' in existing and is_littoral_significant(date):
                # Littoral conséquent déjà là → pas d'autre région (jour dédié)
                return False
            # Littoral minime ou absent → on peut ajouter une non-Littoral
            return True
        return False
    
    def regions_compatible_flexible(existing, new_region, date=None, new_qty=0, order_priority_num=None):
        """Compatibilité région flexible pour Phase 1.
        - Même région ou Est+Nord: toujours OK
        - Littoral conséquent: doit avoir sa PROPRE journée (refusé si autres régions)
        - Littoral minime: insérable sans compter dans la limite
        - 2ème région hors-Littoral: ÉCHUE uniquement (priorités 1-3)
        - Max 2 régions effectives"""
        if not existing:
            return True
        if new_region in existing:
            return True
        est_nord = {'Est', 'Nord'}
        if existing.issubset(est_nord) and new_region in est_nord:
            return True
        # Littoral: comportement dépend de ses qtés
        if new_region == 'Littoral':
            non_litt_existing = [r for r in existing if r != 'Littoral']
            if non_litt_existing and is_littoral_significant(date, new_qty):
                # Littoral conséquent + autres régions présentes → REFUSÉ
                # Le Littoral doit avoir sa propre journée dédiée
                return False
            # Littoral minime: insérable sans compter dans la limite
            new_regions = existing | {new_region}
            eff_count = effective_region_count(new_regions, date, new_qty)
            return eff_count <= 2
        # Ajout d'une région hors-Littoral
        non_litt_existing = [r for r in existing if r != 'Littoral']
        if len(non_litt_existing) >= 2:
            return False  # Déjà 2 régions hors-Littoral
        # Vérifier si Littoral conséquent est déjà présent (jour dédié)
        if 'Littoral' in existing and is_littoral_significant(date):
            # Littoral conséquent déjà là → pas d'autre région (jour dédié)
            return False
        # Ajout 2ème région hors-Littoral: ÉCHUE uniquement
        if len(non_litt_existing) == 1:
            if order_priority_num is not None and order_priority_num <= 3:
                # Vérifier aussi le compte effectif
                new_regions = existing | {new_region}
                eff_count = effective_region_count(new_regions, date)
                return eff_count <= 2
            return False  # Pas de 2ème région hors-Littoral pour non-ÉCHUE
        # Aucune non-Littoral existante → on peut ajouter
        return True
    
    def assign(ref, tiers, agence, region, produit, qty, priority, date_prevue, date, 
               forced=False, force_majeure=False):
        alloc = allocations[date]
        alloc['qty_used'] += qty
        alloc['regions'].add(region)
        alloc['orders'].append({
            'ref': ref, 'tiers': tiers, 'agence': agence, 'region': region,
            'produit': produit, 'qte': qty, 'priority': priority,
            'date_prevue': date_prevue, 'forced': forced,
            'force_majeure': force_majeure,
        })
    
    def try_schedule_order(order, qty_left, flexible_region=False, prefer_early_dates=False, min_date=None):
        """Tente de planifier une commande sur les dates disponibles.
        Retourne la quantité restante non planifiée.
        
        Args:
            prefer_early_dates: Si True, préfère les dates les plus tôt (pour Phase 1)
            min_date: Si spécifié, ne planifie QUE sur des dates >= min_date (pour NON ÉCHUE)
        """
        ref = order['ref']
        region = order['region_norm']
        is_tamatio = order['is_tamatio']
        priority_num = order['priority_num']
        
        # Trouver les dates compatibles, triées par préférence
        compatible_dates = []
        for date in prod_dates:
            # CONTRAINTE: date minimum (pour NON ÉCHUE: ne pas planifier avant les ÉCHUE)
            if min_date is not None and date < min_date:
                continue
            
            # CONTRAINTE: commande exclue de cette date
            if ref in EXCLUDED_FROM_DATE and date in EXCLUDED_FROM_DATE[ref]:
                continue

            # CONTRAINTE: verrouillage régional (REGION_LOCK_DATES)
            # Le Littoral est toujours exempté des verrouillages régionaux
            if date in REGION_LOCK_DATES and region != 'Littoral' and region not in REGION_LOCK_DATES[date]:
                continue

            # Vérification de compatibilité région
            existing = allocations[date]['regions']
            if flexible_region:
                if not regions_compatible_flexible(existing, region, date=date, new_qty=qty_left, order_priority_num=priority_num):
                    continue
            else:
                if not regions_compatible_strict(existing, region, date=date, new_qty=qty_left):
                    continue
            # CONTRAINTE: Nord/Est ne peuvent pas être planifiés le mardi
            # (sauf assignations forcées qui contournent cette règle)
            if not is_day_allowed(region, date):
                continue
            cap = get_cap(date)
            if cap <= 0:
                continue
            
            # Score de préférence (plus bas = meilleur)
            # 1. Région assignée au jour (PRODUCTION_REGIONS): forte préférence si correspondance
            region_match = 0
            assigned_region = PRODUCTION_REGIONS.get(date)
            if assigned_region:
                if region == assigned_region:
                    region_match = -2  # Forte préférence: ce jour est assigné à cette région
                else:
                    region_match = 1   # Région différente: moins préféré
            
            # 2. TAMATIO: préférer la date déjà assignée à TAMATIO
            tamatio_pref = 0
            if is_tamatio:
                if tamatio_state['preferred_date'] is not None and date == tamatio_state['preferred_date']:
                    tamatio_pref = -1  # Forte préférence
                else:
                    tamatio_pref = 1
            
            # 2. Littoral conséquent: forte préférence pour journée dédiée (seul)
            littoral_dedicated = 0
            if region == 'Littoral':
                non_litt_on_day = [r for r in allocations[date]['regions'] if r != 'Littoral']
                if not non_litt_on_day and not allocations[date]['regions']:
                    littoral_dedicated = -2  # Jour vide → parfait pour journée dédiée
                elif 'Littoral' in allocations[date]['regions'] and not non_litt_on_day:
                    littoral_dedicated = -2  # Déjà Littoral seul → parfait
                elif not non_litt_on_day:
                    littoral_dedicated = -1  # Pas de non-Littoral → bon
                else:
                    littoral_dedicated = 1   # Autres régions présentes → moins bon
            
            # 3. Région déjà présente sur ce jour (évite multi-région inutile)
            has_region = 0 if region in allocations[date]['regions'] else (1 if allocations[date]['regions'] else 0)
            
            # 4. Date: pour Phase 1 (prefer_early_dates), les dates les plus tôt sont
            #    fortement préférées pour que les ÉCHUE remplissent les premiers jours.
            #    Pour Phase 2/3, on préfère les dates avec plus de capacité.
            if prefer_early_dates:
                # CLÉ: Date en priorité pour Phase 1 → ÉCHUE remplit les dates les plus tôt
                # On utilise un score de date normalisé pour qu'il soit comparable à neg_cap
                date_score = (date - prod_dates[0]).days  # 0 = premier jour, 1 = deuxième, etc.
            else:
                date_score = 0  # Ne pas influencer le tri par date pour Phase 2/3
            
            # 5. Préférer les dates avec plus de capacité restante (minimise les splits)
            #    Pour Phase 1 (prefer_early_dates), ce critère est secondaire après la date
            neg_cap = -cap
            
            # 6. Est+Nord: préférer jeu/ven
            day_pref = 0
            if region in ('Est', 'Nord') and date.weekday() in (3, 4):  # Jeu=3, Ven=4
                day_pref = -1
            
            if prefer_early_dates:
                # Phase 1: date tôt est PLUS IMPORTANT que capacité restante
                compatible_dates.append((region_match, tamatio_pref, littoral_dedicated, has_region, date_score, day_pref, neg_cap, date))
            else:
                # Phase 2/3: capacité restante est plus importante
                compatible_dates.append((region_match, tamatio_pref, littoral_dedicated, has_region, neg_cap, day_pref, date))
        
        compatible_dates.sort()
        
        # NO_SPLIT: si la commande ne doit pas être splitée, on ne la place
        # que sur une date où la totalité de la quantité peut tenir
        is_no_split = ref in NO_SPLIT
        
        for entry in compatible_dates:
            date = entry[-1]  # La date est toujours le dernier élément
            if qty_left <= 0:
                break
            cap = get_cap(date)
            if cap <= 0:
                continue
            # NO_SPLIT: sauter les dates où la quantité complète ne tient pas
            if is_no_split and cap < qty_left:
                continue
            qty_assign = min(qty_left, cap)
            # Vérification règle de split (Contrainte n°13) :
            # Si on ne peut pas tout placer (qty_assign < qty_left), c'est un split.
            # - Si pas encore splitée (qty_left == qte_restante): la livraison doit être
            #   >= 50% de la qté totale (MIN_SPLIT_FIRST_RATIO)
            # - Si déjà splitée (qty_left < qte_restante): on doit livrer la totalité
            #   du reste (pas de 2e split) → on saute cette date
            if qty_assign < qty_left:  # c'est un split
                if qty_left < order['qte_restante']:
                    # Déjà splitée → pas de 2e split, on doit tout livrer
                    continue
                else:
                    # Premier split → minimum 50% de la qté totale
                    if qty_assign < qty_left * MIN_SPLIT_FIRST_RATIO:
                        continue  # Split trop petit → on saute cette date
            assign(ref, order['tiers'], order['agence'], region,
                   order['produit'], qty_assign, order['priority_label'],
                   order['date_prevue'], date)
            qty_left -= qty_assign
            remaining_qty[ref] = qty_left
            
            if is_tamatio and tamatio_state['preferred_date'] is None:
                tamatio_state['preferred_date'] = date
            
            if qty_left <= 0:
                scheduled_refs.add(ref)
                break
        
        return qty_left
    
    # =======================================================================
    # ÉTAPE 0: Assignations forcées
    # =======================================================================
    print(f"\n  [{capacity_key.upper()}] Étape 0: Assignations forcées...")
    for ref, forced_date in FORCED_ASSIGNMENTS.items():
        if ref not in remaining_qty:
            continue
        order = df_orders[df_orders['ref'] == ref]
        if len(order) == 0:
            continue
        order = order.iloc[0]
        qty = remaining_qty[ref]
        cap = get_cap(forced_date)
        if cap > 0:
            qty_assign = min(qty, cap)
            assign(ref, order['tiers'], order['agence'], order['region_norm'],
                   order['produit'], qty_assign, order['priority_label'],
                   order['date_prevue'], forced_date, forced=True)
            remaining_qty[ref] -= qty_assign
            if remaining_qty[ref] <= 0:
                scheduled_refs.add(ref)
            print(f"    {ref}: {qty_assign:,} → {forced_date.strftime('%d/%m')}")
    
    # =======================================================================
    # ÉTAPE 0b: PRÉ-PLANIFICATION LITTORAL (si qtés ÉCHUE conséquentes)
    # Si le total Littoral ÉCHUE restant est > 25% de la capacité d'un jour,
    # on réserve une journée dédiée au Littoral AVANT les autres régions.
    # Sinon, le Littoral sera inséré dans la journée d'une autre région
    # sans compter dans la limite des 2 régions.
    # =======================================================================
    total_littoral_echue = 0
    for _, o in df_orders[(df_orders['region_norm'] == 'Littoral') & 
                          (df_orders['priority_num'].isin(HIGH_PRIORITY_NUMS))].iterrows():
        total_littoral_echue += remaining_qty.get(o['ref'], 0)
    
    if total_littoral_echue > 0:
        # Vérifier si les qtés Littoral ÉCHUE sont conséquentes
        # (comparer à la capacité moyenne d'un jour)
        avg_cap = sum(PRODUCTION_PLAN[d][0 if capacity_key == 'reelle' else 1] for d in prod_dates) / len(prod_dates)
        littoral_is_consequent = total_littoral_echue > avg_cap * LITTORAL_MINIMAL_RATIO
        
        if littoral_is_consequent:
            # Trouver le meilleur jour dédié pour le Littoral:
            # - Jour sans autre région (ou avec le moins de régions)
            # - v12: Préférer les dates les plus tôt (les ÉCHUE doivent remplir les premiers jours)
            # - Maximum de capacité disponible
            best_date = None
            best_score = None
            for date in prod_dates:
                if not is_day_allowed('Littoral', date):
                    continue
                cap = get_cap(date)
                if cap <= 0:
                    continue
                existing = allocations[date]['regions']
                non_litt = [r for r in existing if r != 'Littoral']
                # Score: préférer jour vide, puis date tôt, puis capacité
                emptiness = len(non_litt)  # 0 = parfait (jour vide ou Littoral seul)
                date_priority = (date - prod_dates[0]).days  # 0 = premier jour
                score = (emptiness, date_priority, -cap)
                if best_score is None or score < best_score:
                    best_score = score
                    best_date = date
            
            if best_date is not None:
                print(f"  [{capacity_key.upper()}] Étape 0b: Pré-planification Littoral (qtés ÉCHUE conséquentes: {total_littoral_echue:,})...")
                print(f"    Jour dédié choisi: {best_date.strftime('%d/%m')} ({['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][best_date.weekday()]})")
                
                # Planifier toutes les commandes Littoral ÉCHUE sur ce jour dédié
                littoral_echue_orders = df_orders[
                    (df_orders['region_norm'] == 'Littoral') & 
                    (df_orders['priority_num'].isin(HIGH_PRIORITY_NUMS))
                ].sort_values('sort_key')
                
                for _, order in littoral_echue_orders.iterrows():
                    ref = order['ref']
                    qty_left = remaining_qty.get(ref, 0)
                    if qty_left <= 0:
                        continue
                    
                    # Essayer d'abord le jour dédié
                    cap = get_cap(best_date)
                    if cap > 0:
                        qty_assign = min(qty_left, cap)
                        assign(ref, order['tiers'], order['agence'], 'Littoral',
                               order['produit'], qty_assign, order['priority_label'],
                               order['date_prevue'], best_date)
                        qty_left -= qty_assign
                        remaining_qty[ref] = qty_left
                        if qty_left <= 0:
                            scheduled_refs.add(ref)
                    
                    # Si reste, chercher d'autres jours vides (dates tôt en priorité)
                    if qty_left > 0:
                        qty_left = try_schedule_order(order, qty_left, flexible_region=False, prefer_early_dates=True)
                
                littoral_scheduled = total_littoral_echue - sum(
                    remaining_qty.get(o['ref'], 0) 
                    for _, o in littoral_echue_orders.iterrows() 
                    if remaining_qty.get(o['ref'], 0) >= 0
                )
                # Recalculer plus précisément
                littoral_remaining = sum(
                    remaining_qty.get(o['ref'], 0) 
                    for _, o in littoral_echue_orders.iterrows() 
                    if remaining_qty.get(o['ref'], 0) > 0
                )
                littoral_placed = total_littoral_echue - littoral_remaining
                print(f"    Littoral ÉCHUE planifié: {littoral_placed:,} sujets | Restant: {littoral_remaining:,}")
        else:
            print(f"  [{capacity_key.upper()}] Étape 0b: Littoral ÉCHUE minime ({total_littoral_echue:,}) → insertion dans journée autre région")
    else:
        print(f"  [{capacity_key.upper()}] Étape 0b: Pas de Littoral ÉCHUE à planifier")
    
    # =======================================================================
    # PHASE 1: ÉCHUE + ÉCHUE RECLASSÉE + RECLASSÉE + SANS DATE
    # Planifiées en PREMIER avec flexibilité régionale
    # =======================================================================
    print(f"  [{capacity_key.upper()}] Phase 1: Commandes prioritaires (ÉCHUE, RECLASSÉE, SANS DATE)...")
    
    phase1_orders = df_orders[df_orders['priority_num'].isin(HIGH_PRIORITY_NUMS)].copy()
    phase1_total_before = sum(remaining_qty.get(r, 0) for r in phase1_orders['ref'] if remaining_qty.get(r, 0) > 0)
    
    # Premier passage : essayer d'abord avec région stricte (même région)
    # v12: prefer_early_dates=True → les ÉCHUE remplissent les dates les plus tôt en premier
    for _, order in phase1_orders.iterrows():
        ref = order['ref']
        qty_left = remaining_qty.get(ref, 0)
        if qty_left <= 0:
            continue
        qty_left = try_schedule_order(order, qty_left, flexible_region=False, prefer_early_dates=True)
    
    # Deuxième passage : les commandes non encore placées essaient avec flexibilité régionale
    # (permet aux ÉCHUE d'autres régions d'utiliser la capacité restante)
    for _, order in phase1_orders.iterrows():
        ref = order['ref']
        qty_left = remaining_qty.get(ref, 0)
        if qty_left <= 0:
            continue
        qty_left = try_schedule_order(order, qty_left, flexible_region=True, prefer_early_dates=True)
    
    phase1_scheduled = phase1_total_before - sum(remaining_qty.get(r, 0) for r in phase1_orders['ref'] if remaining_qty.get(r, 0) > 0)
    phase1_remaining = sum(remaining_qty.get(r, 0) for r in phase1_orders['ref'] if remaining_qty.get(r, 0) > 0)
    print(f"    Planifiées: {phase1_scheduled:,} sujets | Restantes: {phase1_remaining:,} sujets")
    
    # =======================================================================
    # RÉÉQUILIBRAGE: Déplacer les commandes Phase 1 des dates tardives
    # vers les dates plus tôt ayant de la capacité disponible.
    # CRITIQUE: Aucune commande force majeure ne doit prendre la place
    # d'une commande ÉCHUE qui aurait pu être planifiée plus tôt.
    # =======================================================================
    print(f"  [{capacity_key.upper()}] Rééquilibrage: optimisation placement Phase 1...")
    rebalance_total = 0
    rebalance_round = 0
    
    # Déterminer le priority_num depuis le label
    def label_to_priority_num(label):
        if 'ÉCHUE RECLASSÉE' in label: return 2
        elif 'ÉCHUE' in label: return 1
        elif 'RECLASSÉE' in label: return 3
        elif 'SANS DATE' in label: return 5
        else: return None
    
    while True:
        rebalance_round += 1
        moved_this_round = 0
        
        for early_idx, early_date in enumerate(prod_dates):
            early_remaining = get_cap(early_date)
            if early_remaining <= 0:
                continue
            
            # Chercher des commandes Phase 1 sur des dates ultérieures
            for late_date in prod_dates[early_idx + 1:]:
                late_alloc = allocations[late_date]
                
                # Lister les commandes Phase 1 (non force majeure, non forcée) sur cette date tardive
                phase1_orders_on_late = [o for o in late_alloc['orders'] 
                                         if not o.get('force_majeure') and not o.get('forced')]
                
                for order in list(phase1_orders_on_late):
                    region = order['region']
                    qty_on_late = order['qte']
                    p_num = label_to_priority_num(order['priority'])
                    if p_num is None:
                        continue
                    
                    # EXCLUDED_FROM_DATE: ne pas déplacer vers une date exclue
                    if order['ref'] in EXCLUDED_FROM_DATE and early_date in EXCLUDED_FROM_DATE[order['ref']]:
                        continue
                    
                    # NO_SPLIT: ne déplacer que si la totalité peut tenir sur la date tôt
                    is_no_split = order['ref'] in NO_SPLIT
                    if is_no_split and qty_on_late > early_remaining:
                        continue  # Sauter: pas assez de place pour la commande entière
                    
                    # Vérifier si cette commande est déjà splitée sur d'autres dates
                    is_already_split = False
                    total_order_qty = qty_on_late  # Default: ce qu'on a sur cette date
                    for d2 in prod_dates:
                        if d2 == late_date:
                            continue
                        for o2 in allocations[d2]['orders']:
                            if o2['ref'] == order['ref']:
                                is_already_split = True
                                total_order_qty += o2['qte']
                                break
                    if not is_already_split:
                        total_order_qty = qty_on_late  # Pas splitée, qté totale = qté sur cette date
                    
                    # Quantité à déplacer: min(qty sur date tardive, capacité restante sur date tôt)
                    move_qty = min(qty_on_late, early_remaining)
                    
                    # Règle de split (Contrainte n°13):
                    # Si le déplacement partiel crée un nouveau split:
                    # - Premier split: la part déplacée (date tôt) doit être >= 50% du total
                    # - Déjà split: pas de 2e split supplémentaire (déplacement complet uniquement)
                    if move_qty < qty_on_late:  # Déplacement partiel = création ou extension de split
                        if is_already_split:
                            # Déjà splitée → pas de fractionnement supplémentaire
                            continue
                        else:
                            # Premier split → la part déplacée doit être >= 50%
                            if move_qty < total_order_qty * MIN_SPLIT_FIRST_RATIO:
                                continue
                    if move_qty <= 0:
                        continue
                    
                    # Vérifier compatibilité région sur la date tôt
                    existing = allocations[early_date]['regions']
                    if not regions_compatible_flexible(existing, region, date=early_date, 
                                                       new_qty=move_qty, order_priority_num=p_num):
                        continue
                    
                    # Vérifier contrainte de jour (Nord/Est pas le mardi)
                    if not is_day_allowed(region, early_date):
                        continue
                    
                    # Vérifier verrouillage régional (REGION_LOCK_DATES)
                    if early_date in REGION_LOCK_DATES and region != 'Littoral' and region not in REGION_LOCK_DATES[early_date]:
                        continue
                    
                    # DÉPLACER la commande de late_date vers early_date
                    if move_qty >= qty_on_late:
                        # Déplacement complet: retirer de late_date
                        late_alloc['orders'].remove(order)
                        late_alloc['qty_used'] -= qty_on_late
                        actual_move = qty_on_late
                    else:
                        # Déplacement partiel: réduire qté sur late_date
                        order['qte'] -= move_qty
                        late_alloc['qty_used'] -= move_qty
                        actual_move = move_qty
                    
                    # Recalculer régions sur late_date
                    late_alloc['regions'] = set(o['region'] for o in late_alloc['orders']) if late_alloc['orders'] else set()
                    
                    # Ajouter sur early_date
                    assign(order['ref'], order['tiers'], order['agence'], region,
                           order['produit'], actual_move, order['priority'],
                           order['date_prevue'], early_date)
                    
                    early_remaining -= actual_move
                    moved_this_round += actual_move
                    
                    if early_remaining <= 0:
                        break
                
                if early_remaining <= 0:
                    break
        
        rebalance_total += moved_this_round
        if moved_this_round == 0:
            break  # Plus aucun déplacement possible
    
    if rebalance_total > 0:
        print(f"    {rebalance_total:,} sujets déplacés vers des dates plus tôt ({rebalance_round} tour(s))")
    else:
        print(f"    Aucun déplacement nécessaire - placement déjà optimal")
    
    # =======================================================================
    # PHASE 2: IMMINENTE — FORCE MAJEURE UNIQUEMENT
    # Condition: plus aucune commande Phase 1 ne peut être planifiée
    # =======================================================================
    # Vérifier s'il reste des commandes Phase 1 non planifiées qui pourraient tenir
    has_high_pri_left = any(
        remaining_qty.get(r, 0) > 0 
        for r in phase1_orders['ref']
    )
    
    # Même s'il reste des Phase 1, vérifier si elles peuvent VRAIMENT tenir
    # (vérifier s'il existe au moins une date avec capacité, jour autorisé et région compatible)
    can_still_schedule_high = False
    if has_high_pri_left:
        for _, order in phase1_orders.iterrows():
            ref = order['ref']
            if remaining_qty.get(ref, 0) <= 0:
                continue
            region = order['region_norm']
            priority_num = order['priority_num']
            for date in prod_dates:
                # Vérifier aussi EXCLUDED_FROM_DATE et REGION_LOCK_DATES
                if ref in EXCLUDED_FROM_DATE and date in EXCLUDED_FROM_DATE[ref]:
                    continue
                if date in REGION_LOCK_DATES and region != 'Littoral' and region not in REGION_LOCK_DATES[date]:
                    continue
                if (get_cap(date) > 0 
                    and is_day_allowed(region, date)
                    and regions_compatible_flexible(allocations[date]['regions'], region, date=date, new_qty=remaining_qty.get(ref, 0), order_priority_num=priority_num)):
                    can_still_schedule_high = True
                    break
            if can_still_schedule_high:
                break
    
    if can_still_schedule_high:
        print(f"    ⚠ Impossible de planifier toutes les Phase 1 — IMMINENTE/NON ÉCHUE bloquées")
        print(f"    Commandes Phase 1 restantes sans date compatible:")
        for _, order in phase1_orders.iterrows():
            if remaining_qty.get(order['ref'], 0) > 0:
                print(f"      {order['ref']}: {remaining_qty[order['ref']]:,} | {order['priority_label']} | {order['region_norm']}")
    
    # Phase 2 : IMMINENTE (force majeure)
    phase2_scheduled_qty = 0
    if not can_still_schedule_high:
        print(f"  [{capacity_key.upper()}] Phase 2: IMMINENTE (force majeure)...")
        phase2_orders = df_orders[df_orders['priority_num'] == IMMINENTE_NUM].copy()
        
        for _, order in phase2_orders.iterrows():
            ref = order['ref']
            qty_left = remaining_qty.get(ref, 0)
            if qty_left <= 0:
                continue
            qty_before = qty_left
            # IMMINENTE : région stricte uniquement (pas de flexibilité), dates tôt préférées
            qty_left = try_schedule_order(order, qty_left, flexible_region=False, prefer_early_dates=True)
            scheduled_this = qty_before - qty_left
            if scheduled_this > 0:
                phase2_scheduled_qty += scheduled_this
                # Marquer comme force majeure
                for date in prod_dates:
                    for o in allocations[date]['orders']:
                        if o['ref'] == ref and not o.get('force_majeure'):
                            o['force_majeure'] = True
        
        print(f"    IMMINENTE planifiées: {phase2_scheduled_qty:,} sujets")
    
    # =======================================================================
    # v12: CONTRAINTE CHRONOLOGIQUE STRICTE
    # Les commandes ÉCHUE/IMMINENTE/≤1000 doivent TOUJOURS être AVANT les
    # NON ÉCHUE. Donc on calcule la dernière date où une commande prioritaire
    # est planifiée, et les NON ÉCHUE ne peuvent aller que sur des dates
    # ≥ cette date (pour ne jamais apparaître avant une commande prioritaire).
    # =======================================================================
    latest_priority_date = None
    for date in prod_dates:
        alloc = allocations[date]
        for o in alloc['orders']:
            if o.get('force_majeure') and o['priority'] == 'IMMINENTE':
                # IMMINENTE est planifiée → cette date contient une commande prioritaire
                if latest_priority_date is None or date > latest_priority_date:
                    latest_priority_date = date
            elif not o.get('force_majeure'):
                # Phase 1 (ÉCHUE, RECLASSÉE, SANS DATE) → commande prioritaire
                if latest_priority_date is None or date > latest_priority_date:
                    latest_priority_date = date
    
    if latest_priority_date is not None:
        print(f"  [{capacity_key.upper()}] v12: Dernière date avec commande prioritaire (ÉCHUE/IMMINENTE): {latest_priority_date.strftime('%d/%m')}")
        print(f"    → Les NON ÉCHUE ne seront planifiées qu'à partir de cette date")
    else:
        # Aucune commande prioritaire planifiée → NON ÉCHUE peut aller n'importe où
        print(f"  [{capacity_key.upper()}] v12: Aucune commande prioritaire planifiée → NON ÉCHUE libre")
    
    # Phase 3 : NON ÉCHUE (force majeure)
    # RÈGLE v12: NON ÉCHUE ne peut être inséré QUE si:
    #   1. On a épuisé toutes les possibilités des commandes ÉCHUE, ÉCHUE RECLASSÉE,
    #      IMMINENTE et ≤1000 (de TOUTES catégories confondues)
    #   2. NON ÉCHUE ne peut être planifiée que sur des dates ≥ latest_priority_date
    #      (pour garantir qu'aucune NON ÉCHUE n'apparaît avant une commande prioritaire)
    phase3_scheduled_qty = 0
    if not can_still_schedule_high:
        # Vérifier s'il reste des IMMINENTE qui pourraient tenir
        phase2_orders_check = df_orders[df_orders['priority_num'] == IMMINENTE_NUM]
        can_still_schedule_imminente = False
        for _, order in phase2_orders_check.iterrows():
            if remaining_qty.get(order['ref'], 0) <= 0:
                continue
            region = order['region_norm']
            for date in prod_dates:
                # Vérifier aussi EXCLUDED_FROM_DATE et REGION_LOCK_DATES
                if order['ref'] in EXCLUDED_FROM_DATE and date in EXCLUDED_FROM_DATE[order['ref']]:
                    continue
                if date in REGION_LOCK_DATES and region != 'Littoral' and region not in REGION_LOCK_DATES[date]:
                    continue
                if (get_cap(date) > 0 
                    and is_day_allowed(region, date)
                    and regions_compatible_strict(allocations[date]['regions'], region, date=date, new_qty=remaining_qty.get(order['ref'], 0))):
                    can_still_schedule_imminente = True
                    break
            if can_still_schedule_imminente:
                break
        
        # Vérifier aussi s'il reste des commandes ≤1000 (de TOUTES catégories)
        # qui pourraient encore tenir quelque part
        can_still_schedule_le1000 = False
        if not can_still_schedule_imminente:
            all_remaining = df_orders[
                (df_orders['priority_num'] != NON_ECHUE_NUM) &  # Exclure NON ÉCHUE
                (df_orders['qte_restante'] <= 1000)
            ]
            for _, order in all_remaining.iterrows():
                if remaining_qty.get(order['ref'], 0) <= 0:
                    continue
                region = order['region_norm']
                priority_num = order['priority_num']
                for date in prod_dates:
                    # Vérifier aussi EXCLUDED_FROM_DATE et REGION_LOCK_DATES
                    if order['ref'] in EXCLUDED_FROM_DATE and date in EXCLUDED_FROM_DATE[order['ref']]:
                        continue
                    if date in REGION_LOCK_DATES and region != 'Littoral' and region not in REGION_LOCK_DATES[date]:
                        continue
                    if (get_cap(date) > 0 
                        and is_day_allowed(region, date)
                        and regions_compatible_flexible(allocations[date]['regions'], region, date=date, new_qty=remaining_qty.get(order['ref'], 0), order_priority_num=priority_num)):
                        can_still_schedule_le1000 = True
                        break
                if can_still_schedule_le1000:
                    break
        
        # v17: En force majeure, les NON ÉCHUE remplissent TOUJOURS la capacité restante,
        # même s'il reste des IMMINENTE ou ≤1000 théoriquement planifiables.
        # Ces commandes prioritaires n'ont pas pu être placées (contraintes régionales,
        # split, NO_SPLIT, etc.) — laisser la capacité vide serait pire.
        force_majeure_warning = []
        if can_still_schedule_imminente:
            force_majeure_warning.append('IMMINENTE restantes non placées (contraintes)')
        if can_still_schedule_le1000:
            force_majeure_warning.append('≤1000 restantes non placées (contraintes)')

        if True:  # Toujours procéder en force majeure
            # v13: Les NON ÉCHUE peuvent remplir TOUTES les dates avec capacité restante.
            # La restriction min_date (qui bloquait les NON ÉCHUE après la dernière date
            # prioritaire) a été supprimée car elle empêchait le remplissage des dates
            # intermédiaires (25/05, 26/05) qui ont déjà des commandes prioritaires.
            # La validation chronologique en fin d'algorithme garantit la cohérence.
            
            print(f"  [{capacity_key.upper()}] Phase 3: NON ÉCHUE (force majeure)...")
            print(f"    v13: NON ÉCHUE planifiées sur toutes les dates avec capacité restante")
            phase3_orders = df_orders[df_orders['priority_num'] == NON_ECHUE_NUM].copy()
            
            # Premier passage: région stricte (même région que le jour)
            for _, order in phase3_orders.iterrows():
                ref = order['ref']
                qty_left = remaining_qty.get(ref, 0)
                if qty_left <= 0:
                    continue
                qty_before = qty_left
                # v13: plus de min_date — NON ÉCHUE peut aller sur toutes les dates
                qty_left = try_schedule_order(order, qty_left, flexible_region=False, min_date=None)
                scheduled_this = qty_before - qty_left
                if scheduled_this > 0:
                    phase3_scheduled_qty += scheduled_this
                    for date in prod_dates:
                        for o in allocations[date]['orders']:
                            if o['ref'] == ref and not o.get('force_majeure'):
                                o['force_majeure'] = True
            
            # Deuxième passage: flexibilité régionale (comme Phase 1)
            # Permet aux NON ÉCHUE d'autres régions d'utiliser la capacité restante
            phase3_flexible_qty = 0
            for _, order in phase3_orders.iterrows():
                ref = order['ref']
                qty_left = remaining_qty.get(ref, 0)
                if qty_left <= 0:
                    continue
                qty_before = qty_left
                qty_left = try_schedule_order(order, qty_left, flexible_region=True, min_date=None)
                scheduled_this = qty_before - qty_left
                if scheduled_this > 0:
                    phase3_flexible_qty += scheduled_this
                    phase3_scheduled_qty += scheduled_this
                    for date in prod_dates:
                        for o in allocations[date]['orders']:
                            if o['ref'] == ref and not o.get('force_majeure'):
                                o['force_majeure'] = True
            
            print(f"    NON ÉCHUE planifiées: {phase3_scheduled_qty:,} sujets (dont {phase3_flexible_qty:,} en flexibilité régionale)")
        if force_majeure_warning:
            for w in force_majeure_warning:
                print(f"    ⚠ Force majeure: {w} — NON ÉCHUE comble la capacité restante")
    
    # =======================================================================
    # v13: VALIDATION CHRONOLOGIQUE — ÉCHUE AVANT NON ÉCHUE
    # Vérifier qu'aucune date "NON ÉCHUE pure" (sans commande prioritaire)
    # n'est antérieure à une date contenant des commandes prioritaires.
    # Si une date a DÉJÀ des commandes prioritaires, ajouter des NON ÉCHUE
    # est parfaitement acceptable (v13: elles partagent la même journée).
    # =======================================================================
    # Identifier les dates avec commandes prioritaires vs NON ÉCHUE
    priority_dates = set()  # dates contenant au moins une commande prioritaire
    non_echue_only_dates = set()  # dates contenant UNIQUEMENT des NON ÉCHUE (pas de prioritaire)
    non_echue_dates = set()  # dates contenant au moins une commande NON ÉCHUE
    for date in prod_dates:
        alloc = allocations[date]
        has_priority = False
        has_non_echue = False
        for o in alloc['orders']:
            if o['priority'] == 'NON ÉCHUE' and o.get('force_majeure'):
                has_non_echue = True
            elif not o.get('force_majeure') or o['priority'] == 'IMMINENTE':
                has_priority = True
        if has_priority:
            priority_dates.add(date)
        if has_non_echue:
            non_echue_dates.add(date)
        # v13: une date est "NON ÉCHUE pure" si elle n'a PAS de commande prioritaire
        if has_non_echue and not has_priority:
            non_echue_only_dates.add(date)
    
    # Trouver les violations: date "NON ÉCHUE pure" < date avec commande prioritaire
    # (les dates mixtes prioritaire+NON ÉCHUE ne sont PAS des violations)
    violations = []
    for ne_date in non_echue_only_dates:
        for p_date in priority_dates:
            if p_date > ne_date:
                violations.append((ne_date, p_date))
                break  # Une seule violation par date NON ÉCHUE suffit
    
    if violations:
        print(f"  [{capacity_key.upper()}] v12: ⚠ Violation chronologique détectée!")
        for ne_date, p_date in violations:
            print(f"    NON ÉCHUE le {ne_date.strftime('%d/%m')} mais commande prioritaire le {p_date.strftime('%d/%m')}")
        
        # Tentative de swap: déplacer les NON ÉCHUE vers les dates tardives
        # et les commandes prioritaires vers les dates tôt
        swap_total = 0
        for ne_date, p_date in sorted(violations):
            ne_alloc = allocations[ne_date]
            p_alloc = allocations[p_date]
            
            # Collecter les commandes NON ÉCHUE sur la date tôt
            ne_orders = [o for o in ne_alloc['orders'] if o['priority'] == 'NON ÉCHUE' and o.get('force_majeure')]
            
            # Collecter les commandes prioritaires sur la date tardive
            p_orders = [o for o in p_alloc['orders'] if not o.get('force_majeure') or o['priority'] == 'IMMINENTE']
            
            for ne_order in list(ne_orders):
                for p_order in list(p_orders):
                    ne_region = ne_order['region']
                    p_region = p_order['region']
                    ne_qty = ne_order['qte']
                    p_qty = p_order['qte']
                    
                    # Vérifier si le swap est possible:
                    # 1. La commande prioritaire peut-elle aller sur la date NON ÉCHUE? (région + jour)
                    # 2. La commande NON ÉCHUE peut-elle aller sur la date prioritaire? (région + jour)
                    p_num = label_to_priority_num(p_order['priority'])
                    if p_num is None:
                        continue
                    
                    # Vérifier région + jour pour la commande prioritaire sur la date NON ÉCHUE
                    ne_existing = set(o['region'] for o in ne_alloc['orders'] if o != ne_order)
                    if not (is_day_allowed(p_region, ne_date) and
                            regions_compatible_flexible(ne_existing, p_region, date=ne_date, new_qty=p_qty, order_priority_num=p_num)):
                        continue
                    
                    # Vérifier verrouillage régional pour la commande prioritaire sur la date NON ÉCHUE
                    if ne_date in REGION_LOCK_DATES and p_region != 'Littoral' and p_region not in REGION_LOCK_DATES[ne_date]:
                        continue
                    
                    # Vérifier région + jour pour la commande NON ÉCHUE sur la date prioritaire
                    p_existing = set(o['region'] for o in p_alloc['orders'] if o != p_order)
                    if not (is_day_allowed(ne_region, p_date) and
                            regions_compatible_strict(p_existing, ne_region, date=p_date, new_qty=ne_qty)):
                        continue
                    
                    # Vérifier verrouillage régional pour la commande NON ÉCHUE sur la date prioritaire
                    if p_date in REGION_LOCK_DATES and ne_region != 'Littoral' and ne_region not in REGION_LOCK_DATES[p_date]:
                        continue
                    
                    # Effectuer le swap
                    swap_qty = min(ne_qty, p_qty)
                    if swap_qty <= 0:
                        continue
                    
                    # Retirer les quantités des deux dates
                    if swap_qty >= ne_qty:
                        ne_alloc['orders'].remove(ne_order)
                        ne_alloc['qty_used'] -= ne_qty
                    else:
                        ne_order['qte'] -= swap_qty
                        ne_alloc['qty_used'] -= swap_qty
                    
                    if swap_qty >= p_qty:
                        p_alloc['orders'].remove(p_order)
                        p_alloc['qty_used'] -= p_qty
                    else:
                        p_order['qte'] -= swap_qty
                        p_alloc['qty_used'] -= swap_qty
                    
                    # Ajouter commande prioritaire sur date NON ÉCHUE (date tôt)
                    assign(p_order['ref'], p_order['tiers'], p_order['agence'], p_region,
                           p_order['produit'], swap_qty, p_order['priority'],
                           p_order['date_prevue'], ne_date)
                    
                    # Ajouter commande NON ÉCHUE sur date prioritaire (date tardive)
                    assign(ne_order['ref'], ne_order['tiers'], ne_order['agence'], ne_region,
                           ne_order['produit'], swap_qty, ne_order['priority'],
                           ne_order['date_prevue'], p_date, force_majeure=True)
                    
                    # Recalculer régions
                    ne_alloc['regions'] = set(o['region'] for o in ne_alloc['orders']) if ne_alloc['orders'] else set()
                    p_alloc['regions'] = set(o['region'] for o in p_alloc['orders']) if p_alloc['orders'] else set()
                    
                    swap_total += swap_qty
                    break  # Passer à la prochaine commande NON ÉCHUE
        
        if swap_total > 0:
            print(f"    v12: {swap_total:,} sujets échangés (NON ÉCHUE → dates tardives, ÉCHUE → dates tôt)")
        
        # Vérification finale
        remaining_violations = []
        priority_dates2 = set()
        non_echue_dates2 = set()
        for date in prod_dates:
            alloc = allocations[date]
            for o in alloc['orders']:
                if o['priority'] == 'NON ÉCHUE' and o.get('force_majeure'):
                    non_echue_dates2.add(date)
                elif not o.get('force_majeure') or o['priority'] == 'IMMINENTE':
                    priority_dates2.add(date)
        
        for ne_date in non_echue_dates2:
            for p_date in priority_dates2:
                if p_date > ne_date:
                    remaining_violations.append((ne_date, p_date))
                    break
        
        if remaining_violations:
            print(f"    v12: ⚠ Violations résiduelles (contraintes régionales):")
            for ne_date, p_date in remaining_violations:
                print(f"      NON ÉCHUE le {ne_date.strftime('%d/%m')} — prioritaire le {p_date.strftime('%d/%m')}")
                # Afficher les détails
                ne_alloc = allocations[ne_date]
                p_alloc = allocations[p_date]
                ne_fm = [o for o in ne_alloc['orders'] if o['priority'] == 'NON ÉCHUE']
                p_pri = [o for o in p_alloc['orders'] if not o.get('force_majeure')]
                for o in ne_fm:
                    print(f"        NON ÉCHUE: {o['ref']} | {o['region']} | {o['qte']:,}")
                for o in p_pri:
                    print(f"        Prioritaire: {o['ref']} | {o['region']} | {o['qte']:,} | {o['priority']}")
        else:
            print(f"    v12: ✓ Validation réussie — Aucune NON ÉCHUE avant une commande prioritaire")
    
    # Résumé de l'allocation
    total_scheduled = sum(alloc['qty_used'] for alloc in allocations.values())
    print(f"\n  [{capacity_key.upper()}] Résumé:")
    for date in prod_dates:
        alloc = allocations[date]
        real_cap, marge_cap = PRODUCTION_PLAN[date]
        cap = marge_cap if capacity_key == 'marge' else real_cap
        regions_str = '+'.join(sorted(alloc['regions'])) if alloc['regions'] else '-'
        # Afficher le compte effectif des régions (Littoral minime ne compte pas)
        eff_count = effective_region_count(alloc['regions'], date)
        litt_qty = get_littoral_qty(date)
        litt_echue_qty = sum(o['qte'] for o in alloc['orders'] if o['region'] == 'Littoral' and not o.get('force_majeure'))
        litt_tag = ''
        if 'Littoral' in alloc['regions']:
            if litt_qty <= cap * LITTORAL_MINIMAL_RATIO:
                litt_tag = f' [Littoral minime: {litt_qty:,} (ÉCHUE: {litt_echue_qty:,})]'
            else:
                litt_tag = f' [Littoral conséquent: {litt_qty:,} (ÉCHUE: {litt_echue_qty:,})]'
        print(f"    {date.strftime('%d/%m')} ({['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][date.weekday()]}): "
              f"{alloc['qty_used']:,}/{cap:,} | Régions: {regions_str} | Eff: {eff_count}{litt_tag}")
    
    unscheduled_total = sum(v for v in remaining_qty.values() if v > 0)
    print(f"    Total planifié: {total_scheduled:,} | Non planifié: {unscheduled_total:,}")
    
    return allocations, remaining_qty, scheduled_refs

# Exécuter les deux allocations
alloc_reelle, remaining_reelle, scheduled_reelle = run_allocation(df_ponte, 'reelle')
alloc_marge, remaining_marge, scheduled_marge = run_allocation(df_ponte, 'marge')

# ============================================================================
# GÉNÉRATION EXCEL (FORMAT ORIGINAL)
# ============================================================================

print("\nGénération du fichier Excel (format original)...")

wb = Workbook()

# Styles
header_font = Font(bold=True, size=11)
title_font = Font(bold=True, size=12)
section_font = Font(bold=True, size=11, color="003366")
subtotal_font = Font(bold=True, size=10, italic=True)
legend_font = Font(size=9, italic=True)
obs_font = Font(size=9, color="666666")
forced_font = Font(bold=True, color="CC0000")

header_fill = PatternFill(start_color="003366", end_color="003366", fill_type="solid")
header_font_white = Font(bold=True, size=10, color="FFFFFF")
subtotal_fill = PatternFill(start_color="E6F0FF", end_color="E6F0FF", fill_type="solid")
date_section_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
total_fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
legend_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

def add_plan_sheet(wb, sheet_name, allocations, capacity_key):
    """Génère une feuille Plan Réel ou Plan Marge."""
    ws = wb.create_sheet(title=sheet_name)
    
    # Largeurs de colonnes
    col_widths = [3, 16, 20, 35, 15, 14, 20, 12, 20, 22, 18, 70]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    
    row = 1
    row += 1
    
    # Plan de production résumé
    prod_summary = " | ".join([
        f"{['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][d.weekday()]} {d.strftime('%d/%m')} = {PRODUCTION_PLAN[d][0 if capacity_key=='reelle' else 1]:,}"
        for d in prod_dates
    ])
    ws.cell(row=row, column=2, value=f"Plan de production : {prod_summary}").font = title_font
    row += 2
    
    # En-têtes
    headers = ['Date éclosion', 'Capacité production', 'Tiers', 'Réf. Tiers', 
               'Qté à livrer', 'Qté totale commande', 'Région', 'Agence',
               'Date prévue livraison', 'Statut échéance', 'Observation']
    for col_idx, header in enumerate(headers, 2):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = thin_border
    row += 1
    
    total_qty = 0
    
    for date in prod_dates:
        alloc = allocations[date]
        real_cap, marge_cap = PRODUCTION_PLAN[date]
        cap = marge_cap if capacity_key == 'marge' else real_cap
        used = alloc['qty_used']
        non_utilise = max(0, cap - used)
        regions_str = ' + '.join(sorted(alloc['regions'])) if alloc['regions'] else '-'
        
        day_names = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']
        day_name = day_names[date.weekday()]
        
        est_nord_tag = ' EST+NORD MEME JOUR' if alloc['regions'] == {'Est', 'Nord'} or alloc['regions'] == {'Nord', 'Est'} else ''
        
        # Tag Littoral minime/significatif
        litt_qty = sum(o['qte'] for o in alloc['orders'] if o['region'] == 'Littoral')
        litt_echue_qty = sum(o['qte'] for o in alloc['orders'] if o['region'] == 'Littoral' and not o.get('force_majeure'))
        litt_tag = ''
        if 'Littoral' in alloc['regions']:
            if litt_qty <= cap * 0.25:
                litt_tag = f' [Littoral minime: {litt_qty:,} (ÉCHUE: {litt_echue_qty:,})]'
            else:
                litt_tag = f' [Littoral conséquent: {litt_qty:,} (ÉCHUE: {litt_echue_qty:,})]'
        
        # Ligne de section date
        section_text = f"{day_name} {date.strftime('%d/%m/%Y')} — Production: {cap:,} | Region: {regions_str} | Place libre: {non_utilise:,}{est_nord_tag}{litt_tag}"
        cell = ws.cell(row=row, column=2, value=section_text)
        cell.font = section_font
        cell.fill = date_section_fill
        for c in range(2, 13):
            ws.cell(row=row, column=c).fill = date_section_fill
        row += 1
        
        date_subtotal = 0
        
        for order in alloc['orders']:
            date_eclosion = date.strftime('%d/%m/%Y')
            date_prevue_str = order['date_prevue'].strftime('%d/%m/%Y') if order.get('date_prevue') and not pd.isna(order['date_prevue']) else 'N/A'
            
            # Observation
            obs_parts = []
            if order['qte'] <= 1000:
                obs_parts.append('<=1000')
            
            # Check if this order has a Proctor Ai expedition (En cours only)
            order_data = df_ponte[df_ponte['ref'] == order['ref']]
            if len(order_data) > 0 and order_data.iloc[0]['proctor_only']:
                obs_parts.append('Mouvement systeme (pas de livraison reelle)')
            
            # Check if split delivery
            total_order_qty = order_data.iloc[0]['qte_restante'] if len(order_data) > 0 else order['qte']
            if order['qte'] < total_order_qty:
                obs_parts.append('LIVRAISON PARTIELLE')
                for next_date in prod_dates:
                    if next_date > date:
                        for next_order in allocations[next_date]['orders']:
                            if next_order['ref'] == order['ref']:
                                diff_days = (next_date - date).days
                                if diff_days <= 3:
                                    obs_parts.append(f"Suite -> {next_date.strftime('%d/%m')} ({diff_days}j)")
                                else:
                                    obs_parts.append(f"Suite -> {next_date.strftime('%d/%m')} ({diff_days}j)")
                                break
                        break
                obs_parts.append('Partiel (solde -> production ulterieure)')
            
            if order.get('forced'):
                obs_parts.append('FORCEE')
            
            if order.get('force_majeure'):
                obs_parts.append('FORCE MAJEURE')
            
            if est_nord_tag:
                obs_parts.append('Est+Nord meme jour')
            
            observation = ' | '.join(obs_parts)
            
            values = [
                date_eclosion, cap, order['tiers'], order['ref'],
                order['qte'], total_order_qty, order['region'], order['agence'],
                date_prevue_str, order['priority'], observation
            ]
            
            for col_idx, val in enumerate(values, 2):
                cell = ws.cell(row=row, column=col_idx, value=val)
                cell.border = thin_border
                cell.alignment = Alignment(wrap_text=True)
                if col_idx == 12:  # Observation
                    cell.font = Font(size=9)
                if order.get('forced'):
                    cell.font = forced_font
            
            date_subtotal += order['qte']
            row += 1
        
        # Sous-total
        cell = ws.cell(row=row, column=2, value=f"Sous-total {day_name} {date.strftime('%d/%m')}")
        cell.font = subtotal_font
        cell.fill = subtotal_fill
        for c in range(2, 13):
            ws.cell(row=row, column=c).fill = subtotal_fill
        ws.cell(row=row, column=6, value=date_subtotal).font = subtotal_font
        ws.cell(row=row, column=6).fill = subtotal_fill
        total_qty += date_subtotal
        row += 1
        
        # Qté manquante (informative) — capacité non utilisée
        if non_utilise > 0:
            missing_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
            missing_font = Font(size=9, italic=True, color="996600")
            cell = ws.cell(row=row, column=2, value=f"Qté manquante pour compléter la production")
            cell.font = missing_font
            cell.fill = missing_fill
            for c in range(2, 13):
                ws.cell(row=row, column=c).fill = missing_fill
            ws.cell(row=row, column=6, value=non_utilise).font = Font(size=9, italic=True, bold=True, color="CC6600")
            ws.cell(row=row, column=6).fill = missing_fill
            ws.cell(row=row, column=12, value="Capacité disponible pour insertion ultérieure").font = missing_font
            row += 1
        
        row += 1
    
    # Total général
    cell = ws.cell(row=row, column=2, value="TOTAL GENERAL LIVRE")
    cell.font = Font(bold=True, size=12)
    cell.fill = total_fill
    for c in range(2, 13):
        ws.cell(row=row, column=c).fill = total_fill
    ws.cell(row=row, column=6, value=total_qty).font = Font(bold=True, size=12)
    ws.cell(row=row, column=6).fill = total_fill
    row += 1
    
    # Total qté manquante (capacité non utilisée)
    total_missing = 0
    for date in prod_dates:
        alloc_d = allocations[date]
        real_cap_d, marge_cap_d = PRODUCTION_PLAN[date]
        cap_d = marge_cap_d if capacity_key == 'marge' else real_cap_d
        total_missing += max(0, cap_d - alloc_d['qty_used'])
    
    if total_missing > 0:
        missing_total_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        cell = ws.cell(row=row, column=2, value="TOTAL QTE MANQUANTE (capacité disponible)")
        cell.font = Font(bold=True, size=11, italic=True, color="996600")
        cell.fill = missing_total_fill
        for c in range(2, 13):
            ws.cell(row=row, column=c).fill = missing_total_fill
        ws.cell(row=row, column=6, value=total_missing).font = Font(bold=True, size=11, italic=True, color="CC6600")
        ws.cell(row=row, column=6).fill = missing_total_fill
        row += 1
    
    row += 1
    
    # Légende
    legend_items = [
        ('ECHUE', 'Commande dont la date prevue de livraison est depassee'),
        ('ECHUE RECLASSEE', 'Commande echue + reclassee (date_modif < date_prevue - 5j)'),
        ('IMMINENTE', 'Livraison prevue <=10j — integree uniquement en force majeure'),
        ('NON ECHUE', 'Livraison pas encore due — non integrable'),
        ('SPLIT', 'Livraison partielle — premier split >= 50% de la qte totale, pas de 2e split'),
        ('FORCE MAJEURE', 'Commande imminente integree pour remplir la capacite'),
        ('EST+NORD', 'Est et Nord toujours programmes le meme jour (preference jeu/ven)'),
        ('MOUVEMENT SYSTEME', 'Mouvement automatique Proctor Ai "En cours" (pas de livraison reelle)'),
        ('QTE MANQUANTE', 'Capacite non utilisee — disponible pour insertion ulterieure (pas de split force)'),
    ]
    
    cell = ws.cell(row=row, column=2, value="Legende :")
    cell.font = Font(bold=True, size=10)
    row += 1
    
    for term, desc in legend_items:
        ws.cell(row=row, column=2, value=term).font = Font(bold=True, size=9)
        ws.cell(row=row, column=4, value=desc).font = legend_font
        row += 1
    
    row += 1
    cell = ws.cell(row=row, column=2, value="Contraintes appliquees :")
    cell.font = Font(bold=True, size=10)
    row += 1
    
    constraints = [
        "1. FIFO par date de livraison prevue (echues en priorite)",
        "2. Commandes <=1000 echues traitees en premier (sauf Est/Nord -> meme jour)",
        "3. Est et Nord TOUJOURS programmes le meme jour (preference jeu/ven pour eclosion)",
        "4. Une region principale par jour (completee si capacite restante)",
        "5. Client TEDONGMO YEMDJI FRANCK exclu",
        "6. Commandes en statut Brouillon exclues",
        "7. Proctor Ai 'En cours' = mouvement systeme / Proctor Ai 'Livree' = livraison reelle",
        "8. Commandes non echues integrees uniquement en force majeure",
        "9. Livraison en 2 fois possible : 2-3j meme semaine, 4-5j cross-semaine",
        "10. Quantites deja livrees (reelles) deduites via fichier A traiter",
        "11. Cross-reference expeditions pour filtrage Proctor Ai + Status Commande",
        "12. Date de reference: 09/05/2026 (dates anterieures exclues)",
        f"13. Pas de split non pertinent: premier split >= 50% de la qte totale, pas de 2e split (totalite du reste) — capacite restante = qte manquante informative",
    ]
    
    for c in constraints:
        ws.cell(row=row, column=2, value=c).font = Font(size=9)
        row += 1
    
    return ws

# Supprimer la feuille par défaut
if 'Sheet' in wb.sheetnames:
    del wb['Sheet']

# Feuille 1: Plan Réel
print("  Plan Réel...")
add_plan_sheet(wb, 'Plan Réel', alloc_reelle, 'reelle')

# Feuille 2: Plan Marge
print("  Plan Marge...")
add_plan_sheet(wb, 'Plan Marge', alloc_marge, 'marge')

# ============================================================================
# Feuille 3: Commandes non planifiées
# ============================================================================

print("  Commandes non planifiées...")

ws3 = wb.create_sheet(title='Commandes non planifiées')
col_widths_3 = [3, 35, 15, 14, 14, 12, 20, 12, 22]
for i, w in enumerate(col_widths_3, 1):
    ws3.column_dimensions[get_column_letter(i)].width = w

row = 2
ws3.cell(row=row, column=2, value="Commandes non couvertes par ce plan de livraison").font = title_font
row += 2

headers_3 = ['Tiers', 'Réf. Tiers', 'Qté restante', 'Qté totale', 'Région', 'Agence', 'Échéance', 'Date prévue livraison']
for col_idx, h in enumerate(headers_3, 2):
    cell = ws3.cell(row=row, column=col_idx, value=h)
    cell.font = header_font_white
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center')
row += 1

unscheduled = df_ponte[df_ponte['ref'].apply(lambda r: remaining_marge.get(r, 0) > 0)].copy()
unscheduled = unscheduled.sort_values(['priority_num', 'date_prevue'])

for _, order in unscheduled.iterrows():
    qty_remaining = remaining_marge.get(order['ref'], 0)
    if qty_remaining <= 0:
        continue
    
    date_prevue_str = order['date_prevue'].strftime('%d/%m/%Y') if order.get('date_prevue') and not pd.isna(order['date_prevue']) else 'N/A'
    
    values = [
        order['tiers'], order['ref'], qty_remaining, order['qte_restante'],
        order['region_norm'], order['agence'], order['priority_label'], date_prevue_str
    ]
    
    for col_idx, val in enumerate(values, 2):
        cell = ws3.cell(row=row, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True)
    row += 1

# ============================================================================
# Feuille 4: Commandes exclues
# ============================================================================

print("  Commandes exclues...")

ws_excl = wb.create_sheet(title='Commandes exclues')
col_widths_excl = [3, 16, 35, 14, 50]
for i, w in enumerate(col_widths_excl, 1):
    ws_excl.column_dimensions[get_column_letter(i)].width = w

row = 2
ws_excl.cell(row=row, column=2, value="Commandes exclues du plan de livraison").font = title_font
row += 2

headers_excl = ['Réf. Commande', 'Tiers', 'Qté', 'Raison exclusion']
for col_idx, h in enumerate(headers_excl, 2):
    cell = ws_excl.cell(row=row, column=col_idx, value=h)
    cell.font = header_font_white
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center')
row += 1

for ref, reason in sorted(EXCLUSIONS.items()):
    # Try to get tiers and qty from AT
    atr_row = df_atr[df_atr['Réf.'] == ref]
    tiers = str(atr_row.iloc[0]['Tiers']).strip() if len(atr_row) > 0 else ''
    qte = int(atr_row.iloc[0]['Qté commandée']) if len(atr_row) > 0 else 0
    
    # If not in AT, try EXP
    if not tiers and 'Agence' in df_exp.columns:
        exp_row = df_exp[df_exp['Ref. Commande'] == ref]
        tiers = str(exp_row.iloc[0]['Tiers']).strip() if len(exp_row) > 0 else ''
    
    values = [ref, tiers, qte, reason]
    for col_idx, val in enumerate(values, 2):
        cell = ws_excl.cell(row=row, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True)
    row += 1

# ============================================================================
# Feuille 5: Analyse Expéditions
# ============================================================================

print("  Analyse Expéditions...")

ws4 = wb.create_sheet(title='Analyse Expéditions')
col_widths_4 = [3, 16, 30, 14, 12, 14, 16, 10, 30, 16, 16, 30, 16, 60]
for i, w in enumerate(col_widths_4, 1):
    ws4.column_dimensions[get_column_letter(i)].width = min(w, 40)

row = 2
ws4.cell(row=row, column=2, value="Analyse Expéditions — Cross-référence Commandes vs Expéditions BELGO").font = title_font
row += 1
ws4.cell(row=row, column=2, value='Règle : Proctor Ai "Livrée" = livraison réelle / Proctor Ai "En cours" = mouvement système').font = legend_font
row += 2

headers_4 = ['Réf. Commande', 'Tiers', 'Qté commandée', 'Région', 'État commande', 
             'Classification', 'Nb lignes expéd.', 'Date modif.', 'Date prévue',
             'Diff (j)', 'Auteurs expédition', 'Statut expédition', 'Observation']
for col_idx, h in enumerate(headers_4, 2):
    cell = ws4.cell(row=row, column=col_idx, value=h)
    cell.font = header_font_white
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center', wrap_text=True)
row += 1

# Pour chaque commande BELGO dans les expéditions
belgo_exp_refs = set()
for _, exp_row in df_exp.iterrows():
    ref = str(exp_row.get('Ref. Commande', '')).strip()
    agence = str(exp_row.get('Agence', '')).strip()
    if agence.upper().startswith(BELGO_PREFIX):
        belgo_exp_refs.add(ref)

for ref in sorted(belgo_exp_refs):
    exp_rows = df_exp[df_exp['Ref. Commande'] == ref]
    atr_row = df_atr[df_atr['Réf.'] == ref]
    
    tiers = exp_rows.iloc[0]['Tiers'] if len(exp_rows) > 0 else ''
    qte_cmd = int(atr_row.iloc[0]['Qté commandée']) if len(atr_row) > 0 else 0
    
    # Region from agence in AT or EXP
    agence = str(atr_row.iloc[0].get('agence', '')).strip() if len(atr_row) > 0 else ''
    if not agence and len(exp_rows) > 0:
        agence = str(exp_rows.iloc[0].get('Agence', '')).strip()
    region = normalize_region('', agence)
    etat = str(atr_row.iloc[0].get('État', '')).strip() if len(atr_row) > 0 else ''
    
    authors = ', '.join(sorted(set(exp_rows['Auteur'].unique())))
    all_proctor = set(exp_rows['Auteur'].unique()) == {'Proctor Ai'}
    
    # Classification avec Status Commande
    if 'Status Commande' in exp_rows.columns:
        statuses = set(exp_rows['Status Commande'].dropna().unique())
        if all_proctor and 'Livrée' in statuses:
            classification = 'Livraison réelle (Proctor Ai Livrée)'
        elif all_proctor:
            classification = 'Mouvement système (Proctor Ai En cours)'
        else:
            classification = 'Expédition réelle'
    else:
        classification = 'Mouvement système' if all_proctor else 'Expédition réelle'
    
    date_modif = parse_date(exp_rows.iloc[0]['Date modif.']) if len(exp_rows) > 0 else None
    date_prevue = parse_date(exp_rows.iloc[0]['Date prévue de livraison']) if len(exp_rows) > 0 else None
    
    diff_days = ''
    if date_modif and date_prevue and isinstance(date_modif, datetime) and isinstance(date_prevue, datetime):
        diff_days = (date_modif - date_prevue).days
    
    statut_exp = exp_rows.iloc[0].get('Status Commande', '') if len(exp_rows) > 0 else ''
    statut_fact = exp_rows.iloc[0].get('StatutFacture', '') if len(exp_rows) > 0 else ''
    
    obs = ''
    if all_proctor and 'Livrée' in statuses if 'Status Commande' in exp_rows.columns else False:
        obs = 'Proctor Ai mais Status=Livrée → livraison réelle confirmée'
    elif all_proctor:
        obs = 'Mouvement système Proctor Ai — ne compte pas comme livraison réelle'
    elif 'Proctor Ai' in authors:
        obs = 'Expédition mixte (Proctor Ai + humain) — vérifier livraisons réelles'
    
    values = [
        ref, tiers, qte_cmd, region, etat, classification,
        len(exp_rows), 
        date_modif.strftime('%d/%m/%Y %H:%M') if date_modif and isinstance(date_modif, datetime) else '',
        date_prevue.strftime('%d/%m/%Y') if date_prevue and isinstance(date_prevue, datetime) else '',
        diff_days, authors, f"{statut_exp} | {statut_fact}", obs
    ]
    
    for col_idx, val in enumerate(values, 2):
        cell = ws4.cell(row=row, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True)
    row += 1

# ============================================================================
# Feuille 6: Détail Expéditions
# ============================================================================

print("  Détail Expéditions...")

ws5 = wb.create_sheet(title='Détail Expéditions')
col_widths_5 = [3, 16, 14, 25, 30, 16, 16, 16, 10, 14, 16]
for i, w in enumerate(col_widths_5, 1):
    ws5.column_dimensions[get_column_letter(i)].width = min(w, 40)

row = 2
ws5.cell(row=row, column=2, value="Détail des lignes expédition pour les commandes BELGO").font = title_font
row += 2

headers_5 = ['Réf. Commande', 'Réf. produit', 'Description', 'Tiers', 'Date prévue',
             'Auteur', 'Date modif.', 'Facturé', 'Status Cmd', 'Agence']
for col_idx, h in enumerate(headers_5, 2):
    cell = ws5.cell(row=row, column=col_idx, value=h)
    cell.font = header_font_white
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center', wrap_text=True)
row += 1

for _, exp_row in df_exp.iterrows():
    ref = str(exp_row.get('Ref. Commande', '')).strip()
    agence = str(exp_row.get('Agence', '')).strip()
    if not agence.upper().startswith(BELGO_PREFIX):
        continue
    
    date_prevue = parse_date(exp_row.get('Date prévue de livraison'))
    date_modif = parse_date(exp_row.get('Date modif.'))
    
    values = [
        ref,
        str(exp_row.get('Réf. produit', '')),
        str(exp_row.get('Description du produit', '')),
        str(exp_row.get('Tiers', '')),
        date_prevue.strftime('%d/%m/%Y') if date_prevue and isinstance(date_prevue, datetime) else '',
        str(exp_row.get('Auteur', '')),
        date_modif.strftime('%d/%m/%Y %H:%M') if date_modif and isinstance(date_modif, datetime) else '',
        str(exp_row.get('Facturé', '')),
        str(exp_row.get('Status Commande', '')),
        agence,
    ]
    
    for col_idx, val in enumerate(values, 2):
        cell = ws5.cell(row=row, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True)
        if exp_row.get('Auteur') == 'Proctor Ai':
            cell.font = Font(color="999999")
    row += 1

# ============================================================================
# Feuille 7: Livraisons Coq
# ============================================================================

print("  Livraisons Coq...")

ws6 = wb.create_sheet(title='Livraisons Coq')
col_widths_6 = [3, 30, 16, 14, 22, 12, 20, 22, 18, 22, 18, 50]
for i, w in enumerate(col_widths_6, 1):
    ws6.column_dimensions[get_column_letter(i)].width = min(w, 50)

row = 2
ws6.cell(row=row, column=2, value="Pas de plan de production COQ — Livraisons alignées sur les PONTE quand possible").font = title_font
row += 2

headers_6 = ['Tiers', 'Réf. Commande', 'Qté commandée', 'Description', 'Région',
             'Agence', 'Date prévue livraison', 'Statut échéance', 'Date livraison PONTE',
             'Planning COQ', 'Observation']
for col_idx, h in enumerate(headers_6, 2):
    cell = ws6.cell(row=row, column=col_idx, value=h)
    cell.font = header_font_white
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center', wrap_text=True)
row += 1

total_coq = 0
ponte_clients = 0
coq_only = 0

for _, order in df_coq.iterrows():
    date_prevue_str = order['date_prevue'].strftime('%d/%m/%Y') if order.get('date_prevue') and not pd.isna(order['date_prevue']) else 'N/A'
    
    client_ponte = df_ponte[df_ponte['tiers'] == order['tiers']]
    ponte_date = 'Non planifiée'
    planning_coq = 'En attente PONTE'
    observation = ''
    
    if len(client_ponte) > 0:
        ponte_clients += 1
        for d in prod_dates:
            for o in alloc_marge[d]['orders']:
                if o['ref'] in set(client_ponte['ref']):
                    ponte_date = d.strftime('%d/%m/%Y')
                    planning_coq = d.strftime('%d/%m/%Y')
                    observation = f"Même jour que PONTE ({ponte_date})"
                    break
            if ponte_date != 'Non planifiée':
                break
        if ponte_date == 'Non planifiée':
            observation = "Même jour que PONTE (non planifiée)"
    else:
        coq_only += 1
        planning_coq = 'Dès que possible'
        observation = "Dès que possible — client sans commande PONTE"
    
    values = [
        order['tiers'], order['ref'], order['qte_restante'], order['produit'],
        order['region_norm'], order['agence'], date_prevue_str, order['priority_label'],
        ponte_date, planning_coq, observation
    ]
    
    for col_idx, val in enumerate(values, 2):
        cell = ws6.cell(row=row, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True)
    
    total_coq += order['qte_restante']
    row += 1

# Total
row += 1
ws6.cell(row=row, column=2, value="TOTAL COQ").font = Font(bold=True)
ws6.cell(row=row, column=4, value=total_coq).font = Font(bold=True)
row += 2

ws6.cell(row=row, column=2, value="Résumé par statut :").font = Font(bold=True)
row += 1
ws6.cell(row=row, column=2, value=f"Client avec PONTE : {ponte_clients} commandes").font = legend_font
row += 1
ws6.cell(row=row, column=2, value=f"Client COQ uniquement : {coq_only} commandes").font = legend_font

# ============================================================================
# Feuille 8: Plan de Production
# ============================================================================

print("  Plan de Production...")

ws7 = wb.create_sheet(title='Plan de Production')
col_widths_7 = [3, 14, 12, 14, 14, 10, 20, 40]
for i, w in enumerate(col_widths_7, 1):
    ws7.column_dimensions[get_column_letter(i)].width = w

row = 2
ws7.cell(row=row, column=2, value="Plan de Production — Poussin Ponte").font = title_font
row += 2

headers_7 = ['Date', 'Jour', 'Plan Réel', 'Plan Marge', 'Écart', 'Région principale', 'Observation']
for col_idx, h in enumerate(headers_7, 2):
    cell = ws7.cell(row=row, column=col_idx, value=h)
    cell.font = header_font_white
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center')
row += 1

day_names = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']
total_reel = 0
total_marge = 0

for date in prod_dates:
    real_cap, marge_cap = PRODUCTION_PLAN[date]
    ecart = real_cap - marge_cap
    
    regions_str = ' + '.join(sorted(alloc_reelle[date]['regions'])) if alloc_reelle[date]['regions'] else '-'
    
    obs = ''
    if alloc_reelle[date]['regions'] == {'Est', 'Nord'} or alloc_reelle[date]['regions'] == {'Nord', 'Est'}:
        obs = 'Est+Nord même jour'
    
    values = [
        date.strftime('%d/%m/%Y'), day_names[date.weekday()],
        real_cap, marge_cap, ecart, regions_str, obs
    ]
    
    for col_idx, val in enumerate(values, 2):
        cell = ws7.cell(row=row, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center')
    
    total_reel += real_cap
    total_marge += marge_cap
    row += 1

# Total
values_total = ['TOTAL', '', total_reel, total_marge, total_reel - total_marge, '', '']
for col_idx, val in enumerate(values_total, 2):
    cell = ws7.cell(row=row, column=col_idx, value=val)
    cell.font = Font(bold=True)
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center')

# ============================================================================
# SAUVEGARDE
# ============================================================================

print(f"\nSauvegarde: {OUTPUT_FILE}")
wb.save(OUTPUT_FILE)

# Résumé
print("\n" + "="*70)
print("RESUME")
print("="*70)
print(f"Date de reference: {REF_DATE.strftime('%d/%m/%Y')}")
print(f"Plan Réel - Total planifié: {sum(a['qty_used'] for a in alloc_reelle.values()):,}")
print(f"Plan Marge - Total planifié: {sum(a['qty_used'] for a in alloc_marge.values()):,}")
print(f"Commandes PONTE: {len(df_ponte)}")
print(f"Commandes COQ: {len(df_coq)}")
print(f"Commandes exclues: {len(EXCLUSIONS)}")
print(f"Non planifiées (marge): {sum(1 for r in remaining_marge.values() if r > 0)}")
print(f"Capacité Réelle totale: {total_cap_reelle:,}")
print(f"Capacité Marge totale: {total_cap_marge:,}")

# Détail par date
print("\nPlan Réel par date:")
plan_reel_summary = {}
for date in prod_dates:
    alloc = alloc_reelle[date]
    cap = PRODUCTION_PLAN[date][0]
    used = alloc['qty_used']
    missing = max(0, cap - used)
    regions = ', '.join(sorted(alloc['regions'])) if alloc['regions'] else '-'
    plan_reel_summary[date] = {'used': used, 'cap': cap, 'regions': regions}
    day_name = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][date.weekday()]
    pct = used/cap*100 if cap > 0 else 0
    miss_str = f" | Manque: {missing:,}" if missing > 0 else ""
    print(f"  {day_name} {date.strftime('%d/%m')}: {used:,}/{cap:,} ({pct:.0f}%) ({regions}){miss_str}")

# Détail priorités
by_priority = {}
print("\nRépartition par priorité (PONTE):")
for p_num, p_label in [(1, 'ÉCHUE'), (2, 'ÉCHUE RECLASSÉE'), (3, 'RECLASSÉE'), (4, 'IMMINENTE'), (5, 'SANS DATE'), (6, 'NON ÉCHUE')]:
    count = len(df_ponte[df_ponte['priority_num'] == p_num])
    qty = df_ponte[df_ponte['priority_num'] == p_num]['qte_restante'].sum()
    if count > 0:
        print(f"  {p_label}: {count} commandes, {qty:,} sujets")
        by_priority[p_label] = {'count': count, 'qty': int(qty)}

# =======================================================================
# MISE À JOUR DU FICHIER DE CONTRAINTES .MD
# =======================================================================
plan_marge_summary = {}
for date in prod_dates:
    alloc = alloc_marge[date]
    cap = PRODUCTION_PLAN[date][1]
    used = alloc['qty_used']
    regions = ', '.join(sorted(alloc['regions'])) if alloc['regions'] else '-'
    plan_marge_summary[date] = {'used': used, 'cap': cap, 'regions': regions}

results = {
    'ref_date': REF_DATE,
    'total_ponte': len(df_ponte),
    'total_coq': len(df_coq),
    'total_exclusions': len(EXCLUSIONS),
    'plan_reel': plan_reel_summary,
    'plan_marge': plan_marge_summary,
    'total_reel': sum(a['qty_used'] for a in alloc_reelle.values()),
    'total_marge': sum(a['qty_used'] for a in alloc_marge.values()),
    'cap_reelle': total_cap_reelle,
    'cap_marge': total_cap_marge,
    'non_planifiees': sum(1 for r in remaining_marge.values() if r > 0),
    'new_auto_exclusions': NEW_AUTO_EXCLUSIONS,
    'by_priority': by_priority,
}

print(f"\nMise à jour du fichier de contraintes: {MD_PATH}")
write_execution_results(MD_PATH, results)
print("  ✓ Fichier de contraintes mis à jour")