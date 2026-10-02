"""Apply independently reviewed cover identity corrections; keep source history."""
import json
import hashlib
from pathlib import Path
from finengine.database import Database
from finengine.calculations import Calculator
from repair_sab_verified_sources import raw_fact

root = Path('/app/state/reports/company-audits/sa-1060')
sources = {
    'e0f6af2446c309d97c08b6c77c0d65ca5a8bbdac0cf9b9e8226386955b6a13d0': ('Alawwal Bank', '2018-03-31'),
    'b38ed6f690397aae2dcf4af1442926fda13912fde3d21fa22b035146c63f0aa4': ('Alawwal Bank', '2018-09-30'),
    '3787cddf436c0da61b993379539180d49767a209963cf8ba573ab53751b1e0a4': ('Saudi Hollandi Bank', '2013-03-31'),
}
db = Database('/app/state/financial.sqlite3', initialize=False)
keys = ['document:sa:1060:' + digest for digest in sources]
evidence = []
for digest, (entity, end) in sources.items():
    source = dict(db.stored_source('document:sa:1060:' + digest))
    assert hashlib.sha256(Path(source['local_path']).read_bytes()).hexdigest() == digest
    assert (root / 'identity-covers' / (digest + '.png')).exists()
    evidence.append({'source_key': source['source_key'], 'document_entity': entity,
                     'cover_period_end': end, 'cover_page': 1,
                     'inspection': 'independent_visual_cover_review',
                     'source_url': source['source_url'], 'source_before': source})
backup = root / 'before-predecessor-quarantine-batch2.json'
assert not backup.exists(), 'Inspect previous attempt before repeating'
before = {table: [dict(r) for r in db.conn.execute(
    'SELECT * FROM ' + table + " WHERE company_id='sa:1060' AND is_current=1")]
    for table in ('data_points', 'observations')}
backup.write_text(json.dumps({'rows': before, 'evidence': evidence}, ensure_ascii=False, indent=2))
retired = sum(r['source_key'] in keys for r in before['data_points'])
with db.conn:
    for table in ('data_points', 'observations'):
        db.conn.execute('UPDATE ' + table + " SET is_current=0 WHERE company_id='sa:1060' AND is_calculated=1")
        db.conn.executemany('UPDATE ' + table + ' SET is_current=0 WHERE source_key=?', [(key,) for key in keys])
facts = [raw_fact(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND is_calculated=0 AND value_type='decimal' ORDER BY period_end,id")]
calculated = Calculator().calculate(facts)
assert all(f.company_id == 'sa:1060' and f.source_key not in keys for f in calculated)
db.publish_batch(calculated)
with db.conn:
    db.conn.executemany("UPDATE source_documents SET status='review_required' WHERE source_key=?", [(key,) for key in keys])
for key in keys:
    for table in ('data_points', 'observations'):
        assert db.conn.execute('SELECT count(*) FROM ' + table + ' WHERE source_key=? AND is_current=1', (key,)).fetchone()[0] == 0
report = {'retired_raw_current_points': retired, 'calculated_generated': len(calculated),
          'current_before': len(before['data_points']), 'current_after': db.conn.execute(
              "SELECT count(*) FROM data_points WHERE company_id='sa:1060' AND is_current=1").fetchone()[0],
          'source_evidence': evidence, 'history_preserved': True,
          'company_completeness_approved': False}
(root / 'predecessor-quarantine-batch2-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({k:v for k,v in report.items() if k != 'source_evidence'}), flush=True)
