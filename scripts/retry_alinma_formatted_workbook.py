"""Retry the confirmed formatting-inflated supplement through validation."""
import json
from pathlib import Path
from types import SimpleNamespace
from finengine.database import Database
from finengine.cli import _extract_document_job_handler

db = Database('/app/state/financial.sqlite3', initialize=False)
key = 'document:sa:1150:be77c186e38da8641b207dd67cafb448b50599933b8d228600acba10e68edbdb'
if db.stored_source(key)['status'] == 'published':
    result = {'source_key': key, 'status': 'already_published'}
else:
    result = _extract_document_job_handler(db)(SimpleNamespace(
        company_id='sa:1150', source_key=key,
        payload={'source_key': key, 'registry': '/app/config/companies.json',
                 'raw_dir': '/app/state/raw', 'llm': False}))
Path('/app/state/reports/sa-alinma-compaction-retry.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
