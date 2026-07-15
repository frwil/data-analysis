#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md_config.py — Parser / écrivain du fichier de contraintes BELGO.
===============================================================
Lit TOUTE la configuration depuis `Contraintes du Plan de Livraisons BELGO.md`
et écrit les résultats de chaque exécution dans ce même fichier.

Source unique de vérité : le .md
"""

import re
import os
from datetime import datetime, date
from collections import defaultdict

# ============================================================
# PARSING BAS NIVEAU
# ============================================================

def parse_md_table(text):
    """
    Parse un tableau markdown en liste de dicts.
    Retourne (headers, rows) où headers est une liste de strings
    et rows une liste de dicts {header: value}.
    """
    lines = text.strip().split('\n')
    if len(lines) < 2:
        return [], []

    # Ligne d'en-têtes
    headers = [h.strip() for h in lines[0].strip('|').split('|')]
    headers = [h for h in headers if h]  # remove empty strings from leading/trailing |

    # Ligne de séparation (|---|...) — on l'ignore
    sep_idx = 1
    if sep_idx < len(lines) and all(c in '|-: ' for c in lines[sep_idx]):
        sep_idx = 2
    else:
        sep_idx = 1

    rows = []
    for line in lines[sep_idx:]:
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        # Remove leading/trailing empty
        if len(cells) > len(headers):
            cells = cells[1:] if cells[0] == '' else cells
        if len(cells) > len(headers):
            cells = cells[:-1] if cells[-1] == '' else cells

        row = {}
        for i, h in enumerate(headers):
            if i < len(cells):
                row[h] = cells[i]
            else:
                row[h] = ''
        rows.append(row)
    return headers, rows


def extract_section(md_text, section_num):
    """
    Extrait une section par son numéro (ex: 1, 6, 12).
    Retourne le texte entre `## {section_num}. ` et le prochain `## `.
    """
    pattern = rf'^## {section_num}\. .*$'
    lines = md_text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            start = i
            break
    if start is None:
        return ''

    # Trouver la fin (prochain ## ou fin du fichier)
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.match(r'^## \d+\. ', lines[i]):
            end = i
            break

    return '\n'.join(lines[start:end])


def extract_subsections(md_text, section_num):
    """
    Découpe une section en sous-sections par `### `.
    Retourne un dict {titre_sous_section: contenu}.
    """
    section_text = extract_section(md_text, section_num)
    lines = section_text.split('\n')
    subsections = {}
    current_title = '_header'
    current_lines = []

    for line in lines:
        if line.startswith('### '):
            if current_lines:
                subsections[current_title] = '\n'.join(current_lines)
            current_title = line.replace('### ', '').strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        subsections[current_title] = '\n'.join(current_lines)

    return subsections


def find_first_table(text):
    """Trouve le premier tableau markdown dans un texte."""
    lines = text.split('\n')
    table_lines = []
    in_table = False
    for line in lines:
        if line.strip().startswith('|') and not in_table:
            in_table = True
            table_lines.append(line)
        elif in_table and line.strip().startswith('|'):
            table_lines.append(line)
        elif in_table and not line.strip().startswith('|'):
            break
    return '\n'.join(table_lines) if table_lines else ''


def find_all_tables(text):
    """Trouve tous les tableaux markdown dans un texte."""
    lines = text.split('\n')
    tables = []
    table_lines = []
    in_table = False
    for line in lines:
        if line.strip().startswith('|') and not in_table:
            in_table = True
            table_lines = [line]
        elif in_table and line.strip().startswith('|'):
            table_lines.append(line)
        elif in_table and not line.strip().startswith('|'):
            tables.append('\n'.join(table_lines))
            table_lines = []
            in_table = False
    if table_lines:
        tables.append('\n'.join(table_lines))
    return tables


# ============================================================
# PARSING DES DATES
# ============================================================

def parse_french_date(s, default_year=2026):
    """Parse une date au format JJ/MM/AAAA, JJ/MM/AA, JJ/MM ou AAAA-MM-JJ."""
    s = s.strip()
    for fmt in ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d']:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Essayer jour/mois seulement (ex: '14/05')
    try:
        parts = s.split('/')
        if len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            return datetime(default_year, month, day)
    except (ValueError, IndexError):
        pass
    return None


def parse_date_list(s, ref_year=2026):
    """Parse une liste de dates séparées par des virgules (ex: '15/05, 26/05' ou '15/05/2026')."""
    dates = []
    for part in s.split(','):
        part = part.strip()
        dt = parse_french_date(part)
        if dt:
            dates.append(dt)
        else:
            # Essayer avec jour/mois seulement (ex: '15/05')
            try:
                parts = part.split('/')
                if len(parts) == 2:
                    day, month = int(parts[0]), int(parts[1])
                    dates.append(datetime(ref_year, month, day))
            except (ValueError, IndexError):
                pass
    return dates


# ============================================================
# PARSING DES SECTIONS SPÉCIFIQUES
# ============================================================

def parse_production_plan(md_text):
    """Parse §1: Plan de Production → dict {date: (reel, marge)}."""
    section = extract_section(md_text, 1)
    table = find_first_table(section)
    if not table:
        return {}
    _, rows = parse_md_table(table)
    result = {}
    for row in rows:
        date_str = row.get('Date', '')
        reel_str = row.get('Réel', '').replace(' ', '').replace(' ', '')
        marge_str = row.get('Marge (95%)', '').replace(' ', '').replace(' ', '')
        dt = parse_french_date(date_str)
        reel = int(reel_str) if reel_str else 0
        marge = int(marge_str) if marge_str else 0
        if dt:
            result[dt] = (reel, marge)
    return result


def parse_production_regions(md_text):
    """Parse §1: extrait les régions principales."""
    section = extract_section(md_text, 1)
    table = find_first_table(section)
    if not table:
        return {}
    _, rows = parse_md_table(table)
    result = {}
    for row in rows:
        date_str = row.get('Date', '')
        region = row.get('Région principale', '')
        dt = parse_french_date(date_str)
        if dt and region:
            result[dt] = region
    return result


def parse_region_locks(md_text):
    """Parse §6: REGION_LOCK_DATES → dict {date: set(regions)}."""
    section = extract_section(md_text, 6)
    table = find_first_table(section)
    if not table:
        return {}
    _, rows = parse_md_table(table)
    result = {}
    for row in rows:
        date_str = row.get('Date', '')
        regions_str = row.get('Régions autorisées', '')
        dt = parse_french_date(date_str)
        if dt and regions_str:
            regions = {r.strip() for r in regions_str.replace('uniquement', '').replace(' + ', ',').replace('+', ',').split(',') if r.strip()}
            result[dt] = regions
    return result


def parse_no_split(md_text):
    """Parse §10: NO_SPLIT → set de refs."""
    section = extract_section(md_text, 10)
    table = find_first_table(section)
    if not table:
        return set()
    _, rows = parse_md_table(table)
    return {row.get('Réf.', '') for row in rows if row.get('Réf.', '')}


def parse_exclusions(md_text):
    """Parse §12: EXCLUSIONS → dict {ref: raison}."""
    section = extract_section(md_text, 12)
    table = find_first_table(section)
    if not table:
        return {}
    _, rows = parse_md_table(table)
    result = {}
    for row in rows:
        ref = row.get('Réf.', '')
        raison = row.get('Raison', '')
        if ref:
            result[ref] = raison
    return result


def parse_excluded_from_date(md_text):
    """Parse §13: EXCLUDED_FROM_DATE → dict {ref: set(dates)}."""
    section = extract_section(md_text, 13)
    table = find_first_table(section)
    if not table:
        return {}
    _, rows = parse_md_table(table)
    result = {}
    for row in rows:
        ref = row.get('Réf.', '')
        dates_str = row.get('Dates exclues', '')
        if ref and dates_str:
            result[ref] = set(parse_date_list(dates_str))
    return result


def parse_forced_assignments(md_text):
    """Parse §14: FORCED_ASSIGNMENTS → dict {ref: (date, qty)}.
    Les dates sont dans les titres de sous-section (### 14/05 (Centre)).
    La qté est lue depuis la colonne Qté du tableau (prioritaire sur l'ERP)."""
    section = extract_section(md_text, 14)
    if not section:
        return {}

    result = {}
    lines = section.split('\n')
    current_date = None

    for line in lines:
        # Détecter ### 14/05 (Centre) ou ### 15/05/2026 (Ouest)
        m = re.match(r'^###\s+(\d{1,2}/\d{1,2}(?:/\d{4})?).*', line)
        if m:
            current_date = parse_french_date(m.group(1))
            continue

        # Détecter une ligne de tableau de données
        if line.strip().startswith('|') and current_date:
            # Ignorer les en-têtes et séparateurs
            stripped = line.strip().strip('|')
            if 'Réf.' in stripped or '|---' in stripped or '------' in stripped:
                continue
            cells = [c.strip() for c in stripped.split('|')]
            if len(cells) >= 1 and cells[0]:
                ref = cells[0]
                if ref.startswith('SO'):
                    # Lire la qté forcée si présente (colonne 3, index 2)
                    qty = None
                    if len(cells) >= 3:
                        qty_str = cells[2].replace(' ', '').replace(' ', '')
                        try:
                            qty = int(qty_str)
                        except ValueError:
                            qty = None
                    if ref not in result:
                        result[ref] = []
                    result[ref].append((current_date, qty))

    return result


def parse_special_include(md_text):
    """Parse §15: SPECIAL_INCLUDE → dict {ref: {agence, region}}."""
    section = extract_section(md_text, 15)
    table = find_first_table(section)
    if not table:
        return {}
    _, rows = parse_md_table(table)
    result = {}
    for row in rows:
        ref = row.get('Réf.', '')
        agence = row.get('Agence surchargée', '')
        region = row.get('Région surchargée', '')
        if ref:
            result[ref] = {'agence': agence, 'region': region}
    return result


def parse_non_echue_enabled(md_text):
    """Parse §2: détecte si la Phase 3 (NON ÉCHUE) est activée ou désactivée.
    Retourne False si la phase est marquée DÉSACTIVÉE, True sinon."""
    section = extract_section(md_text, 2)
    if not section:
        return True  # Par défaut: activée
    # Cherche le marqueur de désactivation dans la section Phase 3
    if 'DÉSACTIVÉE' in section or 'désactivée' in section.lower():
        return False
    return True


def parse_ref_date(md_text):
    """Parse §4: extrait la date de référence (aujourd'hui)."""
    section = extract_section(md_text, 4)
    # Cherche "aujourd'hui (15/05/2026)"
    m = re.search(r"aujourd'hui\s*\((\d{2}/\d{2}/\d{4})\)", section)
    if m:
        return parse_french_date(m.group(1))
    # Fallback: chercher n'importe quelle date
    m = re.search(r'référence\s*=\s*(\d{2}/\d{2}/\d{4})', section)
    if m:
        return parse_french_date(m.group(1))
    return None


# ============================================================
# FONCTION PRINCIPALE DE LECTURE
# ============================================================

def load_config(md_path):
    """
    Charge TOUTE la configuration depuis le fichier .md.
    Retourne un dict avec toutes les sections parsées.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    config = {
        'production_plan': parse_production_plan(md_text),
        'production_regions': parse_production_regions(md_text),
        'region_lock_dates': parse_region_locks(md_text),
        'no_split': parse_no_split(md_text),
        'exclusions': parse_exclusions(md_text),
        'excluded_from_date': parse_excluded_from_date(md_text),
        'forced_assignments': parse_forced_assignments(md_text),
        'special_include': parse_special_include(md_text),
        'ref_date': parse_ref_date(md_text),
        'non_echue_enabled': parse_non_echue_enabled(md_text),
    }

    return config


# ============================================================
# ÉCRITURE DES RÉSULTATS DANS LE .MD
# ============================================================

def write_execution_results(md_path, results):
    """
    Ajoute/Met à jour la section 'Dernière Exécution' dans le .md.
    Ajoute aussi les nouvelles auto-exclusions détectées à §12.
    Met à jour l'historique des versions §21.

    results = {
        'ref_date': datetime,
        'total_ponte': int,
        'total_coq': int,
        'total_exclusions': int,
        'plan_reel': {date: {'used': int, 'cap': int, 'regions': str}},
        'plan_marge': {date: {'used': int, 'cap': int, 'regions': str}},
        'total_reel': int,
        'total_marge': int,
        'cap_reelle': int,
        'cap_marge': int,
        'non_planifiees': int,
        'new_auto_exclusions': {ref: raison},  # découvertes pendant l'exécution
        'by_priority': {label: {'count': int, 'qty': int}},
    }
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 1. Mettre à jour l'historique §21
    md_text = _update_history(md_text, results)

    # 3. Remplacer/Mettre à jour §22 (Dernière Exécution)
    md_text = _update_last_execution(md_text, results)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_text)


def _update_history(md_text, results):
    """Ajoute une entrée à l'historique des versions §21."""
    section21 = extract_section(md_text, 21)
    if not section21:
        return md_text

    today = date.today().strftime('%d/%m/%Y')
    planified = results.get('total_reel', 0)
    cap = results.get('cap_reelle', 0)

    # Extraire la dernière version
    last_v = re.findall(r'\| v(\d+) \|', section21)
    next_v = int(last_v[0]) + 1 if last_v else 16

    new_entry = f'| v{next_v} | {today} | Exécution automatique. Planifié {planified:,}/{cap:,}. {results.get("total_exclusions", 0)} exclusions. |'

    lines = md_text.split('\n')
    # Trouver le tableau d'historique et insérer après la ligne de séparation
    in_s21 = False
    for i, line in enumerate(lines):
        if line.startswith('## 21.'):
            in_s21 = True
            continue
        if in_s21 and line.startswith('| v') and i + 1 < len(lines):
            # Insérer après cette ligne
            lines.insert(i + 1, new_entry)
            break

    return '\n'.join(lines)


def _update_last_execution(md_text, results):
    """Remplace ou crée la section §22: Dernière Exécution."""

    # Supprimer l'ancienne section §22 si elle existe
    lines = md_text.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if line.startswith('## 22. Dernière Exécution'):
            skip = True
            continue
        if skip and (line.startswith('## ') or line.startswith('---')) and not line.startswith('### '):
            skip = False
            # On garde le séparateur
        if not skip:
            new_lines.append(line)

    md_text = '\n'.join(new_lines)

    # Construire la section
    today = date.today().strftime('%d/%m/%Y')
    ref_date = results.get('ref_date')
    ref_str = ref_date.strftime('%d/%m/%Y') if ref_date else 'N/A'

    section = f"""
---

## 22. Dernière Exécution

> Exécutée le **{today}** — Réf: **{ref_str}**

### Résumé

| Métrique | Valeur |
|----------|--------|
| Commandes PONTE | {results.get('total_ponte', 0)} |
| Commandes COQ | {results.get('total_coq', 0)} |
| Exclusions | {results.get('total_exclusions', 0)} |
| Planifié Réel | {results.get('total_reel', 0):,} / {results.get('cap_reelle', 0):,} |
| Planifié Marge | {results.get('total_marge', 0):,} / {results.get('cap_marge', 0):,} |
| Non planifiées (marge) | {results.get('non_planifiees', 0)} |
| Nouvelles auto-exclusions | {len(results.get('new_auto_exclusions', {}))} |

### Plan Réel par date

| Date | Jour | Région | Livré | Capacité | Taux |
|------|------|--------|-------|----------|------|
"""

    day_names = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    plan_reel = results.get('plan_reel', {})
    for dt in sorted(plan_reel.keys()):
        info = plan_reel[dt]
        day = day_names[dt.weekday()] if hasattr(dt, 'weekday') else '?'
        cap = info.get('cap', 0)
        used = info.get('used', 0)
        pct = f"{used/cap*100:.0f}%" if cap > 0 else 'N/A'
        section += f'| {dt.strftime("%d/%m/%Y") if hasattr(dt, "strftime") else dt} | {day} | {info.get("regions", "-")} | {used:,} | {cap:,} | {pct} |\n'

    # Répartition par priorité
    by_pri = results.get('by_priority', {})
    if by_pri:
        section += '\n### Répartition par priorité\n\n'
        section += '| Priorité | Commandes | Qté restante |\n'
        section += '|----------|-----------|-------------|\n'
        for label, info in sorted(by_pri.items()):
            section += f'| {label} | {info.get("count", 0)} | {info.get("qty", 0):,} |\n'

    md_text += section
    return md_text


# ============================================================
# TEST
# ============================================================

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    md_path = 'Contraintes du Plan de Livraisons BELGO.md'
    config = load_config(md_path)

    print("=== Configuration chargée depuis le .md ===\n")
    print(f"REF_DATE: {config['ref_date']}")
    print(f"\nPRODUCTION_PLAN ({len(config['production_plan'])} dates):")
    for dt, (r, m) in sorted(config['production_plan'].items()):
        print(f"  {dt.strftime('%d/%m/%Y')}: Réel={r:,} Marge={m:,}")

    print(f"\nPRODUCTION_REGIONS:")
    for dt, r in sorted(config['production_regions'].items()):
        print(f"  {dt.strftime('%d/%m/%Y')}: {r}")

    print(f"\nREGION_LOCK_DATES:")
    for dt, regions in sorted(config['region_lock_dates'].items()):
        print(f"  {dt.strftime('%d/%m/%Y')}: {regions}")

    print(f"\nNO_SPLIT ({len(config['no_split'])} refs): {config['no_split']}")
    print(f"\nEXCLUSIONS ({len(config['exclusions'])} refs):")
    for ref in sorted(config['exclusions'])[:5]:
        print(f"  {ref}: {config['exclusions'][ref][:60]}...")
    print(f"  ... et {len(config['exclusions'])-5} autres")

    print(f"\nEXCLUDED_FROM_DATE ({len(config['excluded_from_date'])} refs):")
    for ref in sorted(config['excluded_from_date'])[:5]:
        print(f"  {ref}: {config['excluded_from_date'][ref]}")

    print(f"\nFORCED_ASSIGNMENTS ({len(config['forced_assignments'])} refs):")
    for ref, dt in sorted(config['forced_assignments'].items()):
        print(f"  {ref}: {dt.strftime('%d/%m/%Y')}")

    print(f"\nSPECIAL_INCLUDE ({len(config['special_include'])} refs):")
    for ref, info in config['special_include'].items():
        print(f"  {ref}: {info}")
