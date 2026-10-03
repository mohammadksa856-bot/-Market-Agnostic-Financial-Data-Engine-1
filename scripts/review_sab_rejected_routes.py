"""Deterministic routing review over all rejected sources; no publishing."""
import json
from pathlib import Path
import collections
from finengine import cli
from finengine.database import Database
from finengine.registry import CompanyRegistry
import pymupdf

base=Path('/app/state/reports/sab-period-correction-review')
root=base/'rejected-routes-v1';root.mkdir(exist_ok=True)
inventory=json.loads((base/'all-pages-batch-v1/inventory.json').read_text())
db=Database('/app/state/financial.sqlite3',initialize=False);db.conn.execute('PRAGMA query_only=ON')
company=CompanyRegistry.combined(db.conn,'/app/config/companies.json').get('sa:1060')
results=[]
for row in inventory:
    if row['live_status']!='review_required':continue
    key=row['source_key'];source=dict(db.stored_source(key));target=root/(key.rsplit(':',1)[1]+'.review.json')
    if target.exists():results.append(json.loads(target.read_text()));continue
    result={'source_key':key,'source_url':source['source_url'],'prior_group':row['group'],'production_modified':False}
    try:
        with pymupdf.open(source['local_path']) as doc:
            texts=[page.get_text() for page in doc]
        text='\n'.join(texts);lower=text.lower()
        arabic=sum(p['arabic_letters'] for p in row['pages']);letters=sum(p['letters'] for p in row['pages'])
        result['arabic_share']=round(arabic/max(1,letters),3)
        result['cover_excerpt']='\n'.join(texts[:3])[:1200]
        if ('common equity tier' in lower or 'cet1' in lower) and ('km1' in lower or 'key metrics' in lower):
            result['route']='pillar3_candidate'
            manifest,verification,reader=cli._read_pillar3_manifest(Path(source['local_path']),company,source)
            result.update(facts=len(manifest.get('facts',[])),verification=verification,reader=reader)
            (root/(key.rsplit(':',1)[1]+'.manifest.json')).write_text(json.dumps(manifest,indent=2,default=str))
        elif result['arabic_share']>.5:result['route']='arabic_reader_required'
        elif row['group']=='mostly_textless':result['route']='ocr_layout_review_required'
        else:result['route']='native_layout_review_required'
        if row['group']=='native_statement_candidate':
            pages=[p['page'] for p in row['pages'] if p['statement_candidates']]
            result['candidate_page_text']={str(p):texts[p-1][:10000] for p in pages[:4]}
    except Exception as error:result.update(route='inspection_error',error=str(error))
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str));results.append(result)
    (root/'progress.json').write_text(json.dumps({'reviewed':len(results),'total':95,'last_source':key}))
summary={'sources':len(results),'routes':dict(collections.Counter(r['route'] for r in results)),
         'pillar3_verified':sum(r.get('verification',{}).get('ok',False) for r in results),'production_modified':False}
(root/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
