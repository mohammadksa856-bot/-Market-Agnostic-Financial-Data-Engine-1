"""Repair stale source status only from an explicit terminal job result."""
import json
import sqlite3
from pathlib import Path

db = sqlite3.connect('/app/state/financial.sqlite3', timeout=60)
db.row_factory = sqlite3.Row
db.execute('BEGIN IMMEDIATE')
changes = []
for source in db.execute("SELECT * FROM source_documents WHERE status IN ('awaiting_extraction','extracting')").fetchall():
    jobs = db.execute("SELECT * FROM jobs WHERE source_key=? AND job_type='extract_document' ORDER BY updated_at DESC,rowid DESC", (source['source_key'],)).fetchall()
    if not jobs or any(job['status'] in ('queued', 'running') for job in jobs):
        continue
    job = jobs[0]
    result = json.loads(job['result_json'] or '{}')
    if job['status'] != 'succeeded' or result.get('status') != 'review_required':
        continue
    if result.get('source_key') != source['source_key'] or result.get('published') != 0 or not result.get('code'):
        continue
    changes.append({'source_before': dict(source), 'job_id': job['job_id'], 'result': result, 'new_status': 'review_required'})
out = Path('/app/state/reports/sa-terminal-source-reconciliation-v2.json')
if out.exists():
    raise RuntimeError('Audit file already exists; inspect before repeating')
out.write_text(json.dumps(changes, indent=2) + '\n')
for change in changes:
    db.execute("UPDATE source_documents SET status='review_required' WHERE source_key=? AND status=?", (change['source_before']['source_key'], change['source_before']['status']))
db.commit()
print(json.dumps({'reconciled': len(changes), 'evidence': str(out)}))
