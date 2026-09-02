# -*- coding: utf-8 -*-
"""Régénère le bloc var DATA = {...} du rapport HTML depuis _report_data.json.
Script réutilisable — pointe sur le dossier de l'exercice (EXERCICE).
"""
import json
import re

# ==============================================================
# EXERCICE : année fiscale traitée — changer ici pour 2026, etc.
# ==============================================================
EXERCICE = '2025'
BASE = 'D:/Data Analysis/Ristournes/'
DIR = BASE + EXERCICE + '/'

html_path = DIR + f'Rapport_Audit_Ristournes_{EXERCICE}.html'
d = json.load(open(DIR + '_report_data.json', encoding='utf-8'))

def js_val(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))

lines = [
    '  vol_mensuels: ' + js_val(d['vol_mensuels']) + ',',
    '  corrige: ' + js_val(d['corrige']) + ',',
    '  top20: ' + js_val(d['top20']) + ',',
    '  distribution: ' + js_val([r for r in d['distribution'] if r['n'] > 0]) + ',',
    '  agences: ' + js_val(d['agences']) + ',',
    '  palier16_liste: ' + js_val(d['palier16']['liste']) + ',',
    '  ecarts_liste: ' + js_val([{'Tiers': r['Tiers'], 'Agence': r['Agence'],
                                  'total': r['total'], 'Montant': r['Montant']}
                                 for r in d['repro']['ecarts_liste']]),
]
block = 'var DATA = {\n' + '\n'.join(lines) + '\n};'

html = open(html_path, encoding='utf-8').read()
pat = re.compile(r'var DATA = \{.*?\n\};', re.S)
new_html, n = pat.subn(lambda m: block, html)
print('blocs remplacés :', n)
assert n == 1
open(html_path, 'w', encoding='utf-8', newline='\n').write(new_html)
print('OK ->', html_path)
