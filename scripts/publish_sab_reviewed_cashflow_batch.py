"""Source-render-reviewed cash-flow controls, never inferred missing values."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import pymupdf
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.pipeline import Pipeline
from finengine.connectors.file import LocalFileConnector
from finengine.verification import ManifestVerifier

root=Path('/app/state/reports/sab-period-correction-review/reviewed-interim-cashflows-v1')
root.mkdir(exist_ok=True)
backup=root/'before-publication.json'
assert not backup.exists(),'Inspect prior attempt before repeating'
# All amounts explicitly printed in SAR thousand, current-period column, PDF page 8.
# Q1 has no tax-payment row: absence is not zero and no fact is created.
rows=[
 ('31dd72c0bb12023c5657736175f6fcb5b0de00f6bc05f67a00b27b7dc129f9b6','2025-03-31',1,[4925591,-3583391,-154065,1188135,5491697,6679832,-138787,-131041,-21703,145692,None]),
 ('2ebc4b865d5762698af873864e54a63aa3253b4e77ceec09913c536e139d2a00','2025-06-30',2,[6587244,-7429095,330853,-510998,5491697,4980699,-369087,-1785948,-48676,361187,-991655]),
 ('f305d8f91e4d579c92391b31c4643e36714113d95b86b62ae0691a82717f92d6','2025-09-30',3,[7143641,-5804213,57234,1396662,5491697,6888359,-579360,-3868507,-88236,553149,-1119863]),
]
metrics=['operating_cash_flow','investing_cash_flow','financing_cash_flow','cash_change','cash_beginning','cash_end','capex','dividends_paid','lease_payments','depreciation_amortization_cash_flow','taxes_paid']
labels=['Net cash generated from operating activities','Net cash (used in) / generated from investing activities',
        'Net cash generated from / (used in) financing activities','Net change in cash and cash equivalents',
        'Cash and cash equivalents at beginning of the period','Cash and cash equivalents at end of the period',
        'Purchase of property, equipment and intangibles, net','Dividends paid','Payment of lease liabilities',
        'Depreciation and amortization','Zakat and income tax paid']
db=Database('/app/state/financial.sqlite3',initialize=False)
company=CompanyRegistry.combined(db.conn,'/app/config/companies.json').get('sa:1060')
before=[dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1")]
current={(r['metric_key'],r['period_end'],r['period_kind']):r for r in before if r['scope']=='consolidated' and r['dimensions_json']=='{}' and not r['is_calculated']}
staged=[];conflicts=[];sources=[]
for digest,end,quarter,amounts in rows:
    source=dict(db.stored_source('document:sa:1060:'+digest));sources.append(source)
    assert hashlib.sha256(Path(source['local_path']).read_bytes()).hexdigest()==source['content_hash']
    assert sum(amounts[:3])==amounts[3] and amounts[4]+amounts[3]==amounts[5]
    text=pymupdf.open(source['local_path'])[7].get_text().replace(',','')
    facts=[];held=[]
    for metric,label,value in zip(metrics,labels,amounts):
        if value is None:continue
        assert str(abs(value)) in text,(digest,metric,'Source value not present')
        fact={'metric':metric,'source_label':label,'value':str(value),'scale':'1000','currency':'SAR','unit':'SAR',
              'period_end':end,'period_kind':'ytd','period_start':'2025-01-01','fiscal_year':2025,
              'fiscal_quarter':quarter,'page':8,'extraction_method':'independent_rendered_source_review'}
        old=current.get((metric,end,'ytd'))
        canonical=Decimal(abs(value) if metric=='capex' else value)*1000
        if old and Decimal(old['value_decimal'])!=canonical:
            held.append({**fact,'reason':'Current fact conflict requires authority review'})
            conflicts.append({'source_key':source['source_key'],'fact':fact,'current':old})
        else:facts.append(fact)
    manifest={'market':'SA','symbol':'1060','company_id':'sa:1060','currency':'SAR','source_url':source['source_url'],
              'filed_at':source['filed_at'],'filing_type':'interim-financial-statements',
              'facts':facts,'excluded_facts':held,'publication_scope':'Reviewed cash-flow controls only; not whole-document completeness.'}
    path=root/(digest+'.json');path.write_text(json.dumps(manifest,indent=2));staged.append((source,path))
verification=ManifestVerifier(root).verify()
assert verification['ok'] and not verification['unmapped_labels'],verification
backup.write_text(json.dumps({'sources':sources,'current':before,'conflicts':conflicts},indent=2))
results=[]
for source,path in staged:
    with db.conn:db.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?",(source['source_key'],))
    result=Pipeline(db,root/'artifacts').run(company,LocalFileConnector(path,source['source_url'],source_key=source['source_key']))
    results.append(result);(root/'progress.json').write_text(json.dumps(results,indent=2,default=str))
    assert result['status']=='published',result
after={(r['metric_key'],r['period_end'],r['period_kind']):r for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND scope='consolidated' AND dimensions_json='{}'")}
checked=0
for _,path in staged:
    for f in json.loads(path.read_text())['facts']:
        value=Decimal(f['value']);value=abs(value) if f['metric']=='capex' else value
        assert Decimal(after[f['metric'],f['period_end'],f['period_kind']]['value_decimal'])==value*1000
        checked+=1
report={'results':results,'verified_input_values':checked,'conflicts':conflicts,'current_before':len(before),
        'current_after':db.conn.execute("SELECT count(*) FROM data_points WHERE company_id='sa:1060' AND is_current=1").fetchone()[0],
        'company_complete':False,'source_complete':False,'reader_globally_deployed':False}
(root/'result.json').write_text(json.dumps(report,indent=2,default=str))
print(json.dumps(report,default=str),flush=True)
