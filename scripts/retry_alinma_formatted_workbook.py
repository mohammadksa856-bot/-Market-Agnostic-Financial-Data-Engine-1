"""Retry the confirmed formatting-inflated supplement through validation."""
import json
from pathlib import Path
from types import SimpleNamespace
from finengine.database import Database
from finengine.cli import _extract_document_job_handler
from finengine.jobs import DurableJobQueue, Worker

db = Database('/app/state/financial.sqlite3', initialize=False)
key = 'document:sa:1150:be77c186e38da8641b207dd67cafb448b50599933b8d228600acba10e68edbdb'
if db.stored_source(key)['status'] == 'published':
    result = {'source_key': key, 'status': 'already_published'}
else:
    queue = DurableJobQueue(db)
    job_id, created = queue.enqueue('extract_document',
        {'source_key': key, 'registry': '/app/config/companies.json',
         'raw_dir': '/app/state/raw', 'llm': False},
        'sa:1150', key, idempotency_key='alinma-compaction-v2-20261002', priority=0)
    worker = Worker(queue, 'alinma-compaction-v2',
                    {'extract_document': _extract_document_job_handler(db, queue)})
    worker.run_once()
    row = db.conn.execute('SELECT status,result_json,last_error FROM jobs WHERE job_id=?', (job_id,)).fetchone()
    result = dict(row)
    result['job_id'] = job_id
Path('/app/state/reports/sa-alinma-compaction-retry.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
