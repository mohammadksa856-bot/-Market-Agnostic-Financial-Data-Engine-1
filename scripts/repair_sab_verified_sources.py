"""Test a scoped version-preserving repair on a clone; explicit apply only."""
import argparse
import json
import shutil
import sqlite3
from decimal import Decimal
from pathlib import Path
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.pipeline import Pipeline
from finengine.connectors.file import LocalFileConnector
from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind

ROOT = Path('/app/state/reports/sab-period-correction-review')
LIVE = Path('/app/state/financial.sqlite3')
CLONE = ROOT/'repair-test.sqlite3'


def raw_fact(row):
    return Fact(company_id=row['company_id'],metric=row['metric_key'],value=Decimal(row['value_decimal']),
        currency=row['currency'],unit=row['unit'],period_start=row['period_start'] or None,
        period_end=row['period_end'],period_kind=PeriodKind(row['period_kind']),fiscal_year=row['fiscal_year'],
        fiscal_quarter=row['fiscal_quarter'] or None,source_key=row['source_key'],source_url=row['source_url'],
        filed_at=row['filed_at'],scope=row['scope'],dimensions=json.loads(row['dimensions_json']),
        quality_score=Decimal(row['quality_score']),metric_version=row['metric_version'])


def snapshot(conn):
    return {table: [dict(r) for r in conn.execute('SELECT * FROM '+table+' WHERE company_id=?', ('sa:1060',))]
            for table in ('data_points','observations','source_documents')}


def repair(path, apply):
    db=Database(str(path),initialize=False)
    before=snapshot(db.conn)
    backup=ROOT/('production-before-repair.json' if apply else 'test-before-repair.json')
    if apply:
        assert not backup.exists(), 'Already attempted: inspect prior repair before repeating'
        baseline=json.loads((ROOT/'test-before-repair.json').read_text())
        for table in ('data_points','observations'):
            current=lambda data: {r['id']:r for r in data[table] if r['is_current']}
            assert current(before)==current(baseline), 'Company changed since dry run; retest before production'
    backup.write_text(json.dumps(before,ensure_ascii=False,indent=2))
    company=CompanyRegistry.combined(db.conn,'/app/config/companies.json').get('sa:1060')
    reviews=[json.loads(p.read_text()) for p in sorted(ROOT.glob('*.review.json'))]
    assert len(reviews)==3 and all(r['verification']['ok'] for r in reviews)
    keys=[r['source_key'] for r in reviews]
    placeholders=','.join('?' for _ in keys)
    with db.conn:
        for table in ('data_points','observations'):
            db.conn.execute(f"UPDATE {table} SET is_current=0 WHERE company_id='sa:1060' AND (source_key IN ({placeholders}) OR is_calculated=1)",keys)
        for key in keys:
            db.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?",(key,))
    results=[]
    for review in reviews:
        key=review['source_key'];digest=key.split(':')[-1]
        source=db.stored_source(key)
        manifest=ROOT/(digest+'.manifest.json')
        result=Pipeline(db,ROOT/('production-repair-artifacts' if apply else 'test-artifacts')).run(
            company,LocalFileConnector(manifest,source['source_url'],source_key=key))
        assert result['status']=='published',result
        results.append({k:result.get(k) for k in ('source_key','status','published','inserted','restated','duplicates','exceptions')})
    # Rebuild company calculations from current raw facts after retiring stale
    # derived values; do not keep downstream ratios based on erroneous dates.
    facts=[raw_fact(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND is_calculated=0 AND value_type='decimal' ORDER BY period_end,id")]
    calculator=Calculator()
    calculated=calculator.calculate(facts)
    assert all(f.company_id=='sa:1060' for f in facts+calculated)
    states=db.publish_batch(calculated)
    for review in reviews:
        for table in ('data_points','observations'):
            count=db.conn.execute(f'SELECT count(*) FROM {table} WHERE source_key=? AND is_current=1 AND period_end>?', (review['source_key'],review['period'][0])).fetchone()[0]
            assert count==0,(table,review['source_key'],count)
    assets=db.conn.execute("SELECT value_decimal FROM data_points WHERE company_id='sa:1060' AND metric_key='total_assets' AND period_end='2022-12-31' AND period_kind='instant' AND is_current=1 AND scope='consolidated' AND dimensions_json='{}'").fetchall()
    assert assets and all(Decimal(r[0])==Decimal('314450677000') for r in assets),[tuple(r) for r in assets]
    after=snapshot(db.conn)
    result={'status':'repair_verified','production_modified':apply,'sources':results,
            'calculated_generated':len(calculated),'calculated_published_states':{s:states.count(s) for s in set(states)},
            'current_before':sum(r['is_current'] for r in before['data_points']),
            'current_after':sum(r['is_current'] for r in after['data_points']),
            'history_rows_before':len(before['data_points']),'history_rows_after':len(after['data_points']),
            'retained_all_prior_versions':len(after['data_points'])>=len(before['data_points']),
            'scope':'Three verified source corrections only; company completeness NOT approved.'}
    target=ROOT/('production-repair-result.json' if apply else 'repair-test-result.json')
    target.write_text(json.dumps(result,indent=2)+'\n')
    db.conn.close()
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if args.apply:
        proof=json.loads((ROOT/'repair-test-result.json').read_text())
        assert proof['status']=='repair_verified' and not proof['production_modified']
        repair(LIVE,True)
    else:
        assert not CLONE.exists(), 'Preserve previous test database; inspect it first'
        assert shutil.disk_usage(ROOT).free > LIVE.stat().st_size+512*1024*1024, 'Insufficient safe disk space for clone'
        origin=sqlite3.connect('file:'+str(LIVE)+'?mode=ro',uri=True)
        destination=sqlite3.connect(CLONE)
        origin.backup(destination,pages=1000,sleep=0.05)
        destination.close();origin.close()
        repair(CLONE,False)
