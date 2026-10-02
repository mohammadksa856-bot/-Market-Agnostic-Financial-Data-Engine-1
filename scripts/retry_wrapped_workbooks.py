"""Re-read only the two confirmed ZIP-wrapped issuer workbooks."""
import json
from pathlib import Path
from types import SimpleNamespace
from finengine.database import Database
from finengine.cli import _extract_document_job_handler

db = Database('/app/state/financial.sqlite3')
handler = _extract_document_job_handler(db)
results = []
for digest in ('f974895d6fa4d520a32ba67d21a056a1781ca666f2701c51d3b2cb1d1ca7a479', 'a6163c17930326aa95e585d914af5643f7734453de2caaf887dc51809c3c2bb0'):
    key = 'document:sa:1120:' + digest
    source = db.stored_source(key)
    if source['status'] == 'published':
        results.append({'source_key': key, 'status': 'already_published'})
        continue
    result = handler(SimpleNamespace(company_id='sa:1120', source_key=key, payload={'source_key': key, 'registry': '/app/config/companies.json', 'raw_dir': '/app/state/raw', 'llm': False}))
    results.append(result)
    print(json.dumps(result), flush=True)
Path('/app/state/reports/sa-wrapped-workbook-retry-results.json').write_text(json.dumps(results, indent=2)+'\n')
