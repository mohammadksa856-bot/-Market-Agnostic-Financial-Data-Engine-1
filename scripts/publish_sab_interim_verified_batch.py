"""Publish source-checked nonconflicting interim facts; preserve incomplete status."""
import json
from decimal import Decimal
from pathlib import Path
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.pipeline import Pipeline
from finengine.connectors.file import LocalFileConnector
from finengine.verification import ManifestVerifier

root=Path('/app/state/reports/sab-period-correction-review/interim-header-candidate-v2')
approved=root/'approved-nonconflicts'
approved.mkdir(exist_ok=True)
backup=root/'before-verified-batch-publication.json'
assert not backup.exists(), 'Inspect previous attempt before repeating'
db=Database('/app/state/financial.sqlite3',initialize=False)
company=CompanyRegistry.combined(db.conn,'/app/config/companies.json').get('sa:1060')
before=[dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1")]
current={(r['metric_key'],r['period_end'],r['period_kind']):r for r in before
         if r['scope']=='consolidated' and r['dimensions_json']=='{}' and not r['is_calculated']}
# Independently read from rendered page 5 of each original PDF, SAR thousand.
income_controls={
 '2ebc4b86':{'quarter':'2126600','ytd':'4261887'},
 '31dd72c0':{'ytd':'2135287'},
 '71bebafc':{'ytd':'2086161'},
 'f305d8f9':{'quarter':'2143584','ytd':'6405471'},
}
sources=[]; staged=[]; held=[]
for path in sorted(root.glob('*.manifest.json')):
    digest=path.name.split('.')[0];key='document:sa:1060:'+digest
    source=dict(db.stored_source(key));sources.append(source)
    manifest=json.loads(path.read_text())
    controls=income_controls[digest[:8]]
    for kind,value in controls.items():
        f=[f for f in manifest['facts'] if f['metric']=='net_income' and f['period_kind']==kind]
        assert len(f)==1 and Decimal(f[0]['value'])==Decimal(value) and Decimal(f[0]['scale'])==1000
        assert f[0]['page']==5 and f[0]['currency']=='SAR'
    included=[];excluded=[]
    for fact in manifest['facts']:
        old=current.get((fact['metric'],fact['period_end'],fact['period_kind']))
        value=Decimal(fact['value'])*Decimal(fact.get('scale','1'))
        if old and Decimal(old['value_decimal'])!=value:
            excluded.append({**fact,'reason':'Conflicts with current published fact; authority/presentation review remains pending.'})
            held.append({'source_key':key,'fact':fact,'current_value':old['value_decimal'],'current_source':old['source_key']})
        else:included.append(fact)
    manifest['facts']=included
    manifest['excluded_facts']=manifest.get('excluded_facts',[])+excluded
    manifest['source_url']=source['source_url']
    manifest['publication_scope']='Partial primary-statement extraction only; source completeness not approved.'
    target=approved/path.name
    target.write_text(json.dumps(manifest,indent=2))
    staged.append((source,target,len(included)))
verification=ManifestVerifier(approved).verify()
assert verification['ok'] and not verification['unmapped_labels'],verification
assert sum(n for _,_,n in staged)==148 and len(held)==1,'Inspect changed extraction/diff before publication'
backup.write_text(json.dumps({'sources':sources,'company_current':before,'held_conflicts':held,
                             'visual_income_controls_SAR_thousand':income_controls},indent=2))
results=[]
for source,target,n in staged:
    with db.conn:db.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?",(source['source_key'],))
    result=Pipeline(db,root/'publication-artifacts').run(company,LocalFileConnector(target,source['source_url'],source_key=source['source_key']))
    results.append({'source_key':source['source_key'],'input_facts':n,'result':result})
    (root/'batch-publication-progress.json').write_text(json.dumps(results,indent=2,default=str))
    assert result['status']=='published',result
    db.exception('sa:1060',source['source_key'],'extraction','interim_partial_coverage',
                 'Header recovery enabled partial extraction. Missing statement rows/pages and comparative periods still need full audit; not completeness-approved.')
after={(r['metric_key'],r['period_end'],r['period_kind']):dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND scope='consolidated' AND dimensions_json='{}'")}
checked=0
for _,target,_ in staged:
    for f in json.loads(target.read_text())['facts']:
        assert Decimal(after[f['metric'],f['period_end'],f['period_kind']]['value_decimal'])==Decimal(f['value'])*Decimal(f.get('scale','1'))
        checked+=1
report={'sources':results,'verified_input_values':checked,'held_conflicts':held,
        'current_before':len(before),'current_after':db.conn.execute("SELECT count(*) FROM data_points WHERE company_id='sa:1060' AND is_current=1").fetchone()[0],
        'company_complete':False,'source_complete':False,'reader_globally_deployed':False}
(root/'batch-publication-result.json').write_text(json.dumps(report,indent=2,default=str))
print(json.dumps(report,default=str),flush=True)
