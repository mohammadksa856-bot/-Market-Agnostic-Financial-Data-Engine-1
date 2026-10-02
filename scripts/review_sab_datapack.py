"""Read-only staged datapack review with exact source arithmetic and current diffs."""
import json
import sqlite3
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from finengine.reading_xlsx import SupplementReader
from finengine.verification import ManifestVerifier

root = Path('/app/state/reports/sab-period-correction-review/datapack-review')
root.mkdir(exist_ok=True)
assert not (root / 'review-checkpoint.json').exists(), 'Preserve completed audit; use a new version for further reviews'
conn = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
digest = '76acffa163e24985e1c3b9ea9a2d986656291d3698da73b3608df030956c5d0c'
source = conn.execute('SELECT * FROM source_documents WHERE source_key=?', ('document:sa:1060:' + digest,)).fetchone()
manifest = SupplementReader(source['local_path'], '/tmp/sab-1060-map.json').read(
    'SA', '1060', 'SAR', source['filed_at'], period_kinds=('quarter',))
manifest['source_url'] = source['source_url']
path = root / 'sab-q2-2026-stocks.json'
path.write_text(json.dumps(manifest, indent=2))
verification = ManifestVerifier(root).verify(prefix=path.stem)
assert verification['ok'] and not verification['unmapped_labels']
existing = {}
for row in conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND is_calculated=0 AND dimensions_json='{}' AND scope='consolidated'"):
    existing[(row['metric_key'], row['period_end'], row['period_kind'])] = dict(row)
periods = defaultdict(dict)
conflicts = []
for fact in manifest['facts']:
    value = Decimal(fact['value']) * Decimal(fact['scale'])
    periods[fact['period_end']][fact['metric']] = value
    prior = existing.get((fact['metric'], fact['period_end'], fact['period_kind']))
    if prior and Decimal(prior['value_decimal']) != value:
        conflicts.append({'metric': fact['metric'], 'period_end': fact['period_end'],
                          'candidate': str(value), 'current': prior['value_decimal'],
                          'current_source': prior['source_key']})
arithmetic = []
for end, values in sorted(periods.items()):
    delta = values['total_assets'] - values['total_liabilities'] - values['total_equity']
    arithmetic.append({'period_end': end, 'delta_SAR': str(delta),
                       'within_source_thousand_precision': abs(delta) <= Decimal('1500')})
report = {'production_modified': False, 'facts': len(manifest['facts']),
          'dates': len(periods), 'verify': {k: verification[k] for k in ('checks','passed','failures','warnings')},
          'source_arithmetic': arithmetic, 'current_conflicts': conflicts,
          'publication_approved': False,
          'remaining_work': 'Resolve source arithmetic and differences against audited statement authority before publication. Income and segment rows remain unmapped.'}
(root / 'review-checkpoint.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('current_conflicts','source_arithmetic')}), flush=True)
print('conflicts', len(conflicts), 'arithmetic_attention', sum(not r['within_source_thousand_precision'] for r in arithmetic))
