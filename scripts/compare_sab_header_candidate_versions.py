"""Resumable audit of candidate improvements; never approve publication."""
import json
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path

root=Path('/app/state/reports/sab-period-correction-review')
older=root/'interim-header-candidate-v2'
newer=root/'interim-header-candidate-v3'
output=newer/'version-comparison.json'
assert not output.exists(),'Preserve completed review'
for attempt in range(80):
    if len(list(newer.glob('*.review.json')))==4:break
    time.sleep(15)
else:raise TimeoutError('Candidate batch did not finish within twenty minutes')
results=[]
def identity(f):return (f['metric'],f['period_end'],f['period_kind'])
def amount(f):return Decimal(f['value'])*Decimal(f.get('scale','1'))
for p in sorted(older.glob('*.manifest.json')):
    old=json.loads(p.read_text());new=json.loads((newer/p.name).read_text())
    old_values={identity(f):amount(f) for f in old['facts']}
    new_values={identity(f):amount(f) for f in new['facts']}
    removed=[k for k in old_values if k not in new_values]
    changed=[{'identity':k,'before':str(v),'after':str(new_values[k])}
             for k,v in old_values.items() if k in new_values and new_values[k]!=v]
    added=[f for f in new['facts'] if identity(f) not in old_values]
    verification=json.loads((newer/p.name.replace('.manifest.json','.review.json')).read_text())['verification']
    results.append({'source_hash':p.name.split('.')[0],'before':len(old['facts']),
                    'after':len(new['facts']),'removed':removed,'changed':changed,
                    'added':added,'pages_after':dict(Counter(f['page'] for f in new['facts'])),
                    'verification':verification,'independent_new_value_review':'pending'})
report={'sources':results,'production_modified':False,'publication_approved':False,
        'before':sum(x['before'] for x in results),'after':sum(x['after'] for x in results),
        'removed_count':sum(len(x['removed']) for x in results),
        'changed_count':sum(len(x['changed']) for x in results)}
output.write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='sources'}),flush=True)
