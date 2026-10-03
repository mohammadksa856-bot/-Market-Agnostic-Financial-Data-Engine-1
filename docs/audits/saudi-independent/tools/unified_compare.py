"""Compare unified_reread.py outputs: python unified_compare.py <workdir> <out.json>  (workdir holds base/A/B/unified.json)"""
import sys, json, os
w, out = sys.argv[1], sys.argv[2]
V = {n: json.load(open(os.path.join(w, n + '.json'), encoding='utf8')) for n in ('base', 'A', 'B', 'unified')}
names = sorted(k for k in V['base'] if k != 'reader_file')
res = {'manifests': len(names), 'errors': {}, 'per_manifest': {}, 'totals': {}}
def val(v): return v['value'] if v else None
for n in names:
    recs = {k: V[k][n] for k in V}
    if any(not r['ok'] for r in recs.values()):
        res['errors'][n] = {k: r['error'] for k, r in recs.items() if not r['ok']}
        continue
    entry = {}
    for var in ('A', 'B', 'unified'):
        b, x = recs['base']['facts'], recs[var]['facts']
        ch = [{'fact': k, 'old': b[k]['value'], 'new': x[k]['value'], 'label_old': b[k]['label'], 'label_new': x[k]['label'], 'page_old': b[k]['page'], 'page_new': x[k]['page']}
              for k in sorted(set(b) & set(x)) if b[k]['value'] != x[k]['value']]
        gone = [{'fact': k, 'old': b[k]['value'], 'label': b[k]['label'], 'page': b[k]['page']} for k in sorted(set(b) - set(x))]
        add = [{'fact': k, 'new': x[k]['value'], 'label': x[k]['label'], 'page': x[k]['page']} for k in sorted(set(x) - set(b))]
        if ch or gone or add: entry[var] = {'changed': ch, 'disappeared': gone, 'added': add}
    if entry:
        entry['pdf'] = recs['base']['pdf']
        res['per_manifest'][n] = entry
res['changed_manifests'] = {v: sum(1 for e in res['per_manifest'].values() if v in e) for v in ('A', 'B', 'unified')}
res['unchanged_manifests'] = res['manifests'] - len(res['errors']) - len(res['per_manifest'])
json.dump(res, open(out, 'w', encoding='utf8'), indent=1, ensure_ascii=False)
print('manifests', res['manifests'], 'errors', len(res['errors']), 'any-variant-changed', len(res['per_manifest']), 'by variant', res['changed_manifests'])
for n, e in res['per_manifest'].items():
    print(n, {v: (len(e[v]['changed']), len(e[v]['disappeared']), len(e[v]['added'])) for v in ('A', 'B', 'unified') if v in e})
