"""Read-only whole-company triage; stage keys, never publish or approve."""
import collections
import datetime
import json
from pathlib import Path
import sqlite3
import pymupdf

root=Path('/app/state/reports/sab-period-correction-review/company-batch-v1')
root.mkdir(exist_ok=True)
db=sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro',uri=True)
db.row_factory=sqlite3.Row
rows=list(db.execute('SELECT * FROM source_documents WHERE company_id=?',('sa:1060',)))
inventory=[]; keys=[]
for source in rows:
    item={'source_key':source['source_key'],'status':source['status'],'classification':'other_format'}
    path=Path(source['local_path'] or '')
    if path.suffix.lower()=='.pdf':
        try:
            with pymupdf.open(path) as doc:
                texts=[p.get_text().lower() for p in list(doc)[:11]]
                cover=' '.join(texts[:3])
                if 'hollandi' in cover or ('alawwal' in cover and 'saudi british' not in cover and 'saudi awwal' not in cover):
                    item['classification']='predecessor_identity_review'
                else:
                    candidates=[i+1 for i,t in enumerate(texts) if ('total assets' in t and 'total liabilities' in t) or ('operating activities' in t and 'financing activities' in t) or ('net income' in t and 'commission income' in t)]
                    item['candidate_pages']=candidates
                    item['classification']='native_statement_candidate' if candidates else 'no_native_signature'
                    if candidates and source['status']=='review_required': keys.append(source['source_key'])
        except Exception as error: item.update(classification='inspection_error',error=str(error))
    inventory.append(item)
(root/'candidate-keys.json').write_text(json.dumps(keys,indent=2))
(root/'inventory.json').write_text(json.dumps(inventory,indent=2))
summary={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':len(rows),'statuses':dict(collections.Counter(r['status'] for r in rows)),'groups':dict(collections.Counter(r['classification'] for r in inventory)),'candidate_retry_count':len(keys),'production_modified':False,'correctness_approved':False}
(root/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary),flush=True)
