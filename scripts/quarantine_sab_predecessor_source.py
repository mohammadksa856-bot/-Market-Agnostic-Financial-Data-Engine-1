"""Retire confirmed predecessor-scoped facts; preserve versions and rebuild ratios."""
import json
from pathlib import Path
from finengine.database import Database
from finengine.calculations import Calculator
from repair_sab_verified_sources import raw_fact

root = Path('/app/state/reports/company-audits/sa-1060')
key = 'document:sa:1060:8a788ea3fc0756df5073015541c2e0b5730e6b4def52e8f021b3b305220d5d56'
proof = json.loads((root / 'predecessor-cover-review-20261002.json').read_text())
assert any(r['source_key'] == key and r['document_entity'] == 'Saudi Hollandi Bank'
           and r['archive_hash_matched'] for r in proof['sources'])
db = Database('/app/state/financial.sqlite3', initialize=False)
backup = root / 'before-predecessor-quarantine.json'
assert not backup.exists(), 'Inspect previous attempt before repeating'
before = {table: [dict(r) for r in db.conn.execute(
    'SELECT * FROM ' + table + " WHERE company_id='sa:1060' AND is_current=1")]
    for table in ('data_points', 'observations')}
before['source'] = dict(db.stored_source(key))
backup.write_text(json.dumps(before, ensure_ascii=False, indent=2))
retired = sum(r['source_key'] == key for r in before['data_points'])
with db.conn:
    for table in ('data_points', 'observations'):
        db.conn.execute('UPDATE ' + table + " SET is_current=0 WHERE company_id='sa:1060' AND (source_key=? OR is_calculated=1)", (key,))
    db.conn.execute("UPDATE source_documents SET status='review_required' WHERE source_key=?", (key,))
facts = [raw_fact(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND is_calculated=0 AND value_type='decimal' ORDER BY period_end,id")]
calculated = Calculator().calculate(facts)
assert all(f.company_id == 'sa:1060' and f.source_key != key for f in calculated)
db.publish_batch(calculated)
with db.conn:
    db.conn.execute("UPDATE source_documents SET status='review_required' WHERE source_key=?", (key,))
assert db.conn.execute('SELECT count(*) FROM data_points WHERE source_key=? AND is_current=1', (key,)).fetchone()[0] == 0
report = {'retired_current_points': retired, 'calculated_generated': len(calculated),
          'current_before': len(before['data_points']), 'current_after': db.conn.execute(
              "SELECT count(*) FROM data_points WHERE company_id='sa:1060' AND is_current=1").fetchone()[0],
          'history_preserved': True, 'company_completeness_approved': False}
(root / 'predecessor-quarantine-result.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report), flush=True)
