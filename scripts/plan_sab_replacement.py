"""Capture exact production rows affected by verified SAB reader corrections."""
import json
import sqlite3
from pathlib import Path

ROOT = Path('/app/state/reports/sab-period-correction-review')
db = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
db.row_factory = sqlite3.Row
db.execute('BEGIN')
plan = {'company_id': 'sa:1060', 'production_modified': False, 'sources': [],
        'publication_state': 'pending_history_and_dependent_calculation_repair'}
for report_path in sorted(ROOT.glob('*.review.json')):
    review = json.loads(report_path.read_text())
    assert review['verification']['ok'] is True
    key = review['source_key']
    manifest = json.loads(report_path.with_name(report_path.name.replace('.review.json', '.manifest.json')).read_text())
    old = [dict(row) for row in db.execute('SELECT * FROM data_points WHERE company_id=? AND source_key=? AND is_current=1', ('sa:1060', key))]
    for fact in manifest['facts']:
        assert fact['period_end'] <= review['period'][0]
    plan['sources'].append({'source_key': key, 'correct_period': review['period'],
                            'verification': review['verification'],
                            'current_rows_before_repair': old,
                            'corrected_manifest_path': str(report_path.with_name(report_path.name.replace('.review.json', '.manifest.json'))),
                            'corrected_fact_count': len(manifest['facts'])})
plan['calculated_rows_to_recheck'] = [dict(row) for row in db.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND is_calculated=1")]
plan['required_steps'] = ['backup affected company rows and source versions',
    'preserve erroneous rows in history but remove their current status',
    'publish verified replacement through normal validation and authority rules',
    'rebuild affected calculated metrics and legacy observations',
    'compare company period coverage and source evidence again']
db.close()
target = ROOT/'replacement-plan.json'
target.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'plan':str(target),'sources':len(plan['sources']),
                 'current_affected_rows':sum(len(s['current_rows_before_repair']) for s in plan['sources']),
                 'calculated_rows_to_recheck':len(plan['calculated_rows_to_recheck']),
                 'production_modified':False}),flush=True)
