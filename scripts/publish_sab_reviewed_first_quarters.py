"""Publish reviewed Q1 identities as calculated, never as new raw disclosures."""
import importlib.util
import sys
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import pymupdf
from finengine.database import Database
from finengine.models import Fact,PeriodKind

spec=importlib.util.spec_from_file_location('finengine.calculations','/tmp/calculations-q1-candidate.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
root=Path('/app/state/reports/sab-period-correction-review/reviewed-first-quarters-v1');root.mkdir(exist_ok=True)
backup=root/'before.json';assert not backup.exists(),'Inspect prior attempt before retry'
db=Database('/app/state/financial.sqlite3',initialize=False)
before=[dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1")]
expected={('net_income',f'{year}-03-31'):Decimal(value) for year,value in
          [(2022,'1004198000'),(2023,'1764570000'),(2024,'2043019000'),(2025,'2135287000'),(2026,'2086161000')]}
expected.update({('operating_cash_flow','2025-03-31'):Decimal('4925591000'),
                 ('capex','2025-03-31'):Decimal('138787000'),
                 ('free_cash_flow','2025-03-31'):Decimal('4786804000')})
facts=[];evidence=[]
for (metric,end),value in expected.items():
    rows=[r for r in before if r['metric_key']==metric and r['period_end']==end and r['period_kind']=='ytd'
          and r['scope']=='consolidated' and r['dimensions_json']=='{}' and r['currency']=='SAR']
    assert len(rows)==1,(metric,end,len(rows))
    r=rows[0];assert Decimal(r['value_decimal'])==value and r['period_start']==end[:4]+'-01-01' and r['fiscal_quarter']==1
    source=dict(db.stored_source(r['source_key']));assert hashlib.sha256(Path(source['local_path']).read_bytes()).hexdigest()==source['content_hash']
    with pymupdf.open(source['local_path']) as doc:
        pages=[i+1 for i,p in enumerate(doc) if str(value/1000).split('.')[0] in p.get_text().replace(',','')]
    assert pages or metric=='free_cash_flow',(metric,'Source number missing')
    evidence.append({'parent_id':r['id'],'metric':metric,'period':end,'value':str(value),'source_key':r['source_key'],
                     'source_hash':source['content_hash'],'numeric_occurrence_pages':pages,
                     'source_review':'Income statement rendered review; 2023 additionally matched 2024 comparator; 2025 cash flow rendered review and reconciled controls.',
                     'meaning':'Identical Q1 and Q1-YTD interval; source completeness not approved'})
    facts.append(Fact(r['company_id'],metric,value,r['currency'],r['unit'],r['period_start'],end,
                      PeriodKind.YTD,r['fiscal_year'],1,r['source_key'],r['source_url'],r['filed_at']))
quarters=module.Calculator()._first_quarters(facts)
assert len(quarters)==8 and all(f.is_calculated and f.period_kind==PeriodKind.QUARTER for f in quarters)
assert not any(r['period_kind']=='quarter' and (r['metric_key'],r['period_end']) in expected for r in before),'Quarter already exists; review conflict'
backup.write_text(json.dumps({'current':before,'evidence':evidence},indent=2))
states=db.publish_batch(quarters)
after=[dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1")]
by_id={r['id']:r for r in after};assert all(by_id.get(r['id'])==r for r in before),'Existing value changed'
for f in quarters:
    r=[r for r in after if r['metric_key']==f.metric and r['period_end']==f.period_end and r['period_kind']=='quarter']
    assert len(r)==1 and Decimal(r[0]['value_decimal'])==f.value and r[0]['is_calculated']
result={'published_calculated_quarters':len(quarters),'states':states,'current_before':len(before),'current_after':len(after),
        'new_raw_facts':0,'existing_points_preserved':True,'production_modified':True,'company_complete':False}
(root/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
