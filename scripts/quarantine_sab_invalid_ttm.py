"""Retire only independently proven non-12-month derived values; keep history."""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from finengine.database import Database

root=Path('/app/state/reports/sab-period-correction-review/ttm-integrity-v1')
review=json.loads((root/'review.json').read_text())
bad=[r for r in review['results'] if r['status']!='matched']
assert len(bad)==3
db=Database('/app/state/financial.sqlite3',initialize=False)
before=[dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060'")]
ids={r['current']['id'] for r in bad}
for r in bad:
    original=r['current'];live=next(p for p in before if p['id']==original['id'])
    assert live==original and live['is_calculated'] and live['period_kind']=='ttm'
    assert (date.fromisoformat(live['period_end'])-date.fromisoformat(live['period_start'])).days+1>371
    assert sum(Decimal(s['value_decimal']) for s in r['support'])==Decimal(live['value_decimal'])
    assert len(r['support'])==4
dependencies=[r for r in before if r['is_current'] and r['is_calculated'] and r['id'] not in ids and 'net_income_ttm' in (r['calculation'] or '')]
assert not dependencies,'Dependent calculations need explicit review before quarantine'
backup=root/'before-quarantine.json';assert not backup.exists(),'Inspect existing attempt'
backup.write_text(json.dumps(before,indent=2))
with db.conn:
    for r in bad:
        f=r['current']
        db.conn.execute("UPDATE data_points SET is_current=0 WHERE id=? AND company_id='sa:1060'",(f['id'],))
        db.conn.execute("UPDATE observations SET is_current=0 WHERE company_id='sa:1060' AND metric=? AND period_end=? AND period_kind='ttm' AND source_key=? AND is_calculated=1 AND is_current=1",(f['metric_key'],f['period_end'],f['source_key']))
for r in bad:
    f=r['current']
    db.exception('sa:1060',f['source_key'],'calculation','noncontiguous_quarters_not_ttm',
                 'Published TTM spans more than 12 months because available quarters have gaps.',
                 payload={'retired_id':f['id'],'evidence_path':str(root/'review.json'),'missing_quarters_require_extraction':True})
after=[dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060'")]
assert len(before)==len(after),'No financial history may be deleted'
now={r['id']:r for r in after}
assert all(now[r['id']]==r for r in before if r['id'] not in ids),'Unrelated row changed'
assert all(not now[i]['is_current'] for i in ids)
result={'retired_invalid_ttm':len(ids),'current_before':sum(r['is_current'] for r in before),
        'current_after':sum(r['is_current'] for r in after),'history_preserved':True,
        'all_other_rows_preserved':True,'production_modified':True,'company_complete':False}
(root/'quarantine-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
