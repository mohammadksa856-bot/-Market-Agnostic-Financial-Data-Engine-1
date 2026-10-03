"""Evidence-scoped retained earnings correction; isolated dry run before apply."""
import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import pymupdf
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.models import Fact, PeriodKind
from finengine.calculations import Calculator
from finengine.pipeline import Pipeline
from finengine.connectors.file import LocalFileConnector
from finengine.verification import ManifestVerifier

BASE=Path('/app/state/reports/sab-period-correction-review')
ROOT=BASE/'retained-presentation-repair-v2'
KEY='document:sa:1060:71bebafc0e248e3ea46ee0de02a434a7fa5aa6838b3e32d6abea423717304b7c'
TARGETS=[('2025-03-31','15765511000','13710716000'),('2026-03-31','19614412000','17559617000')]

def snapshot(db):
    return {t:[dict(r) for r in db.conn.execute('SELECT * FROM '+t+' WHERE company_id=?',('sa:1060',))]
            for t in ('data_points','observations','source_documents')}

def fingerprint(state):
    return hashlib.sha256(json.dumps(state,sort_keys=True,default=str).encode()).hexdigest()

def raw_fact(row):
    return Fact(company_id=row['company_id'],metric=row['metric_key'],value=Decimal(row['value_decimal']),
        currency=row['currency'],unit=row['unit'],period_start=row['period_start'] or None,
        period_end=row['period_end'],period_kind=PeriodKind(row['period_kind']),fiscal_year=row['fiscal_year'],
        fiscal_quarter=row['fiscal_quarter'] or None,source_key=row['source_key'],source_url=row['source_url'],
        filed_at=row['filed_at'],scope=row['scope'],dimensions=json.loads(row['dimensions_json']),
        quality_score=Decimal(row['quality_score']),metric_version=row['metric_version'])

def run(apply=False):
    ROOT.mkdir(exist_ok=True)
    live=Database('/app/state/financial.sqlite3',initialize=False)
    before=snapshot(live);source=dict(live.stored_source(KEY))
    evidence=json.loads((BASE/'restatement-presentation-evidence-v1.json').read_text())
    assert evidence['source_key']==KEY
    assert hashlib.sha256(Path(source['local_path']).read_bytes()).hexdigest()==source['content_hash']
    with pymupdf.open(source['local_path']) as doc:
        equity=doc[6].get_text()
    assert all(v in equity for v in ('13,710,716','17,559,617','2,054,795','Restated'))
    current=[r for r in before['data_points'] if r['is_current'] and not r['is_calculated']]
    for end,old,new in TARGETS:
        rows=[r for r in current if r['metric_key']=='retained_earnings' and r['period_end']==end
              and r['period_kind']=='instant' and r['scope']=='consolidated' and r['dimensions_json']=='{}' and r['currency']=='SAR']
        assert len(rows)==1 and Decimal(rows[0]['value_decimal'])==Decimal(old),(end,rows)
        assert Decimal(old)-Decimal(new)==Decimal('2054795000')
    stage=ROOT/'manifests';stage.mkdir(exist_ok=True)
    manifest={'market':'SA','symbol':'1060','company_id':'sa:1060','currency':'SAR',
              'source_url':source['source_url'],'filed_at':source['filed_at'],'filing_type':'interim-financial-statements',
              'publication_scope':'Two independently source-reviewed retained earnings values, not document completeness.',
              'facts':[{'metric':'retained_earnings','source_label':'Retained earnings','value':str(Decimal(new)/1000),
                        'scale':'1000','unit':'SAR','currency':'SAR','period_end':end,'period_kind':'instant',
                        'fiscal_year':int(end[:4]),'fiscal_quarter':1,'page':7,
                        'extraction_method':'independent_equity_statement_review','restatement_note_page':33}
                       for end,old,new in TARGETS]}
    path=stage/'retained.json';path.write_text(json.dumps(manifest,indent=2))
    verification=ManifestVerifier(stage).verify();assert verification['ok'],verification
    company=CompanyRegistry.combined(live.conn,'/app/config/companies.json').get('sa:1060')
    backup=ROOT/('production-before.json' if apply else 'test-before.json')
    assert not backup.exists(),'Existing attempt: inspect checkpoint before retry'
    if apply:
        proof=json.loads((ROOT/'test-result.json').read_text())
        assert proof['verified'] and proof['baseline_fingerprint']==fingerprint(before),'Live state changed: retest required'
        db=live
    else:
        live.conn.execute('PRAGMA query_only=ON')
        db=Database(ROOT/'test.sqlite3')
        db.conn.execute('PRAGMA foreign_keys=OFF')
        for table in ('companies','metric_definitions','source_documents','data_points','observations'):
            rows=([dict(r) for r in live.conn.execute('SELECT * FROM '+table)] if table=='metric_definitions'
                  else [dict(r) for r in live.conn.execute('SELECT * FROM '+table+' WHERE company_id=?',('sa:1060',))])
            for row in rows:
                cols=','.join(row);marks=','.join('?' for _ in row)
                db.conn.execute('INSERT OR REPLACE INTO '+table+' ('+cols+') VALUES ('+marks+')',tuple(row.values()))
        db.conn.commit();db.conn.execute('PRAGMA foreign_keys=ON')
    backup.write_text(json.dumps(before,indent=2))
    with db.conn:
        for end,old,new in TARGETS:
            db.conn.execute("UPDATE data_points SET is_current=0 WHERE company_id='sa:1060' AND metric_key='retained_earnings' AND period_end=? AND period_kind='instant' AND scope='consolidated' AND dimensions_json='{}' AND currency='SAR' AND is_current=1 AND is_calculated=0",(end,))
            db.conn.execute("UPDATE observations SET is_current=0 WHERE company_id='sa:1060' AND metric='retained_earnings' AND period_end=? AND period_kind='instant' AND currency='SAR' AND is_current=1 AND is_calculated=0",(end,))
        for table in ('data_points','observations'):
            db.conn.execute('UPDATE '+table+" SET is_current=0 WHERE company_id='sa:1060' AND is_calculated=1 AND calculation LIKE '%retained_earnings%' AND period_end IN ('2025-03-31','2026-03-31')")
        db.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?",(KEY,))
    result=Pipeline(db,ROOT/('production-artifacts' if apply else 'test-artifacts')).run(company,LocalFileConnector(path,source['source_url'],source_key=KEY))
    assert result['status']=='published',result
    facts=[raw_fact(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND is_calculated=0 AND value_type='decimal'")]
    generated=[f for f in Calculator().calculate(facts) if 'retained_earnings' in (f.calculation or '') and f.period_end in {t[0] for t in TARGETS}]
    db.publish_batch(generated)
    after=snapshot(db)
    for end,old,new in TARGETS:
        values=[r['value_decimal'] for r in after['data_points'] if r['is_current'] and r['metric_key']=='retained_earnings' and r['period_end']==end and r['period_kind']=='instant' and r['scope']=='consolidated' and r['dimensions_json']=='{}' and r['currency']=='SAR']
        assert len(values)==1 and Decimal(values[0])==Decimal(new),(end,values)
    before_ids={r['id'] for r in before['data_points']};after_ids={r['id'] for r in after['data_points']}
    assert before_ids<=after_ids,'History was lost'
    preserved=[r for r in current if not (r['metric_key']=='retained_earnings' and r['period_end'] in {t[0] for t in TARGETS} and r['period_kind']=='instant' and r['scope']=='consolidated' and r['dimensions_json']=='{}' and r['currency']=='SAR')]
    after_current={r['id']:r for r in after['data_points'] if r['is_current']}
    assert all(after_current.get(r['id'])==r for r in preserved),'Unrelated raw data changed'
    natural=lambda r:(r['metric_key'],r['period_end'],r['period_kind'],r['scope'],r['dimensions_json'],r['currency'])
    after_by_key={natural(r):r for r in after['data_points'] if r['is_current']}
    unaffected_calculations=[r for r in before['data_points'] if r['is_current'] and r['is_calculated']
                             and not ('retained_earnings' in (r['calculation'] or '') and r['period_end'] in {t[0] for t in TARGETS})]
    assert all(natural(r) in after_by_key and Decimal(after_by_key[natural(r)]['value_decimal'])==Decimal(r['value_decimal']) for r in unaffected_calculations),'Unrelated calculations changed or disappeared'
    report={'verified':True,'production_modified':apply,'baseline_fingerprint':fingerprint(before),'targets':TARGETS,
            'current_before':sum(r['is_current'] for r in before['data_points']),
            'current_after':sum(r['is_current'] for r in after['data_points']),
            'history_preserved':True,'unrelated_raw_values_preserved':True,'generated_calculations':len(generated),
            'pipeline':result,'company_complete':False}
    (ROOT/('production-result.json' if apply else 'test-result.json')).write_text(json.dumps(report,indent=2,default=str))
    print(json.dumps(report,default=str),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');run(parser.parse_args().apply)
