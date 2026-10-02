"""Enqueue only stale sources whose latest job died on a fixed/transient error."""
import json
from pathlib import Path
from finengine.database import Database
from finengine.jobs import DurableJobQueue

db = Database('/app/state/financial.sqlite3')
queue = DurableJobQueue(db)
results = []
for source in db.conn.execute("SELECT source_key,company_id,status FROM source_documents WHERE status='awaiting_extraction'").fetchall():
    jobs = db.conn.execute("SELECT * FROM jobs WHERE source_key=? AND job_type='extract_document' ORDER BY updated_at DESC,rowid DESC", (source['source_key'],)).fetchall()
    if not jobs or any(j['status'] in ('queued','running') for j in jobs):
        continue
    job = jobs[0]
    if job['status'] != 'dead' or job['last_error'] not in ("cannot access local variable 'reader_source' where it is not associated with a value", 'worker lease expired'):
        continue
    payload = json.loads(job['payload_json'])
    payload['llm'] = False
    job_id, created = queue.enqueue('extract_document', payload, source['company_id'], source['source_key'], idempotency_key='stale-recovery-20261002:'+source['source_key'], priority=10, max_attempts=2)
    results.append({'source_key': source['source_key'], 'previous_job': job['job_id'], 'reason': job['last_error'], 'retry_job': job_id, 'created': created})
Path('/app/state/reports/sa-stale-job-retries.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results))
