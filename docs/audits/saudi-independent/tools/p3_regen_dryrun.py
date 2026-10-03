"""Dry run: re-read the archived Pillar 3 PDFs with the CURRENT reader, reconcile vintages, and report what would change
versus the published manifests. Writes only the report JSON given as argv[2]; never touches data/**."""
import sys, os, json, glob, collections
sys.path.insert(0, os.environ.get('FINENGINE_SRC') or os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))
from finengine.reading_pillar3 import Pillar3KeyMetricsReader
from finengine.manifest_vintages import reconcile_vintages
from b_inventory import ROOT, inventory

def run(sym):
    published, fresh = {}, []
    for r in inventory(sym):
        if 'pillar3' not in r['manifest'] or not r['local']: continue
        d = json.load(open(os.path.join(ROOT, 'data/imports', r['manifest']), encoding='utf8'))
        for f in d['facts']: published[(f['metric'], f['period_end'])] = f['value']
        try:
            m = Pillar3KeyMetricsReader(os.path.join(ROOT, r['local'][0])).read('SA', sym, 'SAR', d['source_url'], d['filed_at'])
        except Exception as e:
            print('ERR', r['manifest'], e); continue
        fresh.append(m)
    rec = reconcile_vintages(fresh)
    new = {}
    for m in rec:
        for f in m['facts']: new[(f['metric'], f['period_end'])] = f['value']
    added = sorted(set(new) - set(published)); gone = sorted(set(published) - set(new))
    changed = sorted(k for k in set(new) & set(published) if new[k] != published[k])
    by_metric = collections.Counter(k[0] for k in added)
    return dict(symbol=sym, manifests_reread=len(fresh), published_now=len(published), publishable_after=len(new),
                added=len(added), added_by_metric=dict(by_metric), removed=[list(k) for k in gone], value_changed=[dict(key=list(k), published=published[k], regenerated=new[k]) for k in changed])

if __name__ == '__main__':
    out = {s: run(s) for s in sys.argv[1].split(',')}
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
    for s, v in out.items(): print(s, {k: (v[k] if not isinstance(v[k], list) else len(v[k])) for k in v})
