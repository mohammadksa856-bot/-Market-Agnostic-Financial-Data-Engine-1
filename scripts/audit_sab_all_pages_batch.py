"""Resumable all-page source triage. Never infer correctness from text presence."""
import collections
import datetime
import hashlib
import json
import re
import sqlite3
from pathlib import Path
import pymupdf

root=Path('/app/state/reports/sab-period-correction-review/all-pages-batch-v1')
root.mkdir(exist_ok=True)
db=sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro',uri=True)
db.row_factory=sqlite3.Row
sources=list(db.execute('SELECT * FROM source_documents WHERE company_id=?',('sa:1060',)))
errors=collections.defaultdict(collections.Counter)
for r in db.execute("SELECT source_key,code FROM exceptions WHERE company_id=? AND status='open'",('sa:1060',)):
    errors[r['source_key']][r['code']]+=1
rows=[]
for source in sources:
    key=source['source_key']; digest=source['content_hash']
    target=root/(hashlib.sha256(key.encode()).hexdigest()+'.json')
    if target.exists():
        result=json.loads(target.read_text())
        if result.get('content_hash')!=digest: raise RuntimeError('Source changed; preserve existing audit')
    else:
        result={'source_key':key,'content_hash':digest,'source_url':source['source_url'],
                'independent_correctness':'not_approved','completeness':'not_approved','pages':[]}
        try:
            path=Path(source['local_path'] or '')
            result['hash_matches']=hashlib.sha256(path.read_bytes()).hexdigest()==digest
            if path.suffix.lower()=='.pdf':
                with pymupdf.open(path) as doc:
                    for i,page in enumerate(doc):
                        text=page.get_text(); flat=re.sub(r'\s+',' ',text.lower())
                        signatures=[]
                        for name,groups in {'balance_sheet':(('total assets',),('total liabilities',)),
                                            'income_statement':(('net income','profit for'),('commission income','operating income')),
                                            'cash_flow':(('operating activities',),('financing activities',))}.items():
                            if all(any(t in flat for t in g) for g in groups): signatures.append(name)
                        result['pages'].append({'page':i+1,'letters':sum(c.isalpha() for c in text),
                                                'arabic_letters':sum('\u0600'<=c<='\u06ff' for c in text),
                                                'statement_candidates':signatures,
                                                'excerpt':flat[:250] if signatures else ''})
                candidates=[p for p in result['pages'] if p['statement_candidates']]
                result['group']='native_statement_candidate' if candidates else ('mostly_textless' if sum(p['letters']<20 for p in result['pages'])>len(result['pages'])/2 else 'arabic_or_unrecognized_layout')
            else: result['group']='non_pdf_route'
        except Exception as error: result.update(group='inspection_error',error=str(error))
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    rows.append({**result,'live_status':source['status'],'open_exception_codes':dict(errors[key])})
    (root/'progress.json').write_text(json.dumps({'checked':len(rows),'total':len(sources),'last_source':key,'production_modified':False}))
summary={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':len(rows),
         'statuses':dict(collections.Counter(r['live_status'] for r in rows)),
         'review_groups':dict(collections.Counter(r['group'] for r in rows if r['live_status']=='review_required')),
         'open_exception_codes':dict(sum(errors.values(),collections.Counter())),
         'current_points':db.execute('SELECT count(*) FROM data_points WHERE company_id=? AND is_current=1',('sa:1060',)).fetchone()[0],
         'production_modified':False,'company_complete':False}
(root/'inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(root/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary),flush=True)
