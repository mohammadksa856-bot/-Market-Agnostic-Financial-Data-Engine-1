"""Audit published TTM support independently of extraction success, no writes."""
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path
from finengine.database import Database
from finengine.models import Fact,PeriodKind

spec=importlib.util.spec_from_file_location('finengine.calculations','/tmp/calculations-ttm-candidate.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
db=Database('/app/state/financial.sqlite3',initialize=False);db.conn.execute('PRAGMA query_only=ON')
rows=[dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND value_type='decimal'")]
def fact(r):
    return Fact(r['company_id'],r['metric_key'],Decimal(r['value_decimal']),r['currency'],r['unit'],
                r['period_start'] or None,r['period_end'],PeriodKind(r['period_kind']),r['fiscal_year'],
                r['fiscal_quarter'] or None,r['source_key'],r['source_url'],r['filed_at'],
                scope=r['scope'],dimensions=json.loads(r['dimensions_json']))
results=[]
for r in rows:
    if r['period_kind']!='ttm' or not r['is_calculated']:continue
    metric=r['metric_key'].removesuffix('_ttm')
    support=[s for s in rows if s['metric_key']==metric and s['period_kind']=='quarter' and s['period_end']<=r['period_end']
             and s['scope']==r['scope'] and s['dimensions_json']==r['dimensions_json'] and s['currency']==r['currency'] and s['unit']==r['unit']]
    expected=module.Calculator()._ttm([fact(s) for s in support],{r['period_end']})
    status='unsupported_noncontiguous_or_missing_quarters'
    if expected:
        target=expected[0]
        status='matched' if target.value==Decimal(r['value_decimal']) and target.period_start==r['period_start'] else 'value_or_period_mismatch'
    results.append({'current':r,'status':status,'support':sorted(support,key=lambda s:s['period_end'])[-4:],
                    'expected_value':str(expected[0].value) if expected else None,
                    'expected_start':expected[0].period_start if expected else None})
root=Path('/app/state/reports/sab-period-correction-review/ttm-integrity-v1');root.mkdir(exist_ok=True)
target=root/'review.json';assert not target.exists(),'Preserve completed audit'
target.write_text(json.dumps({'results':results,'production_modified':False},indent=2))
print(json.dumps([{'id':r['current']['id'],'metric':r['current']['metric_key'],'end':r['current']['period_end'],'status':r['status'],'expected_start':r['expected_start']} for r in results],indent=2))
