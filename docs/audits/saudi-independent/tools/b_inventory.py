"""Batch1-B audit helper: inventory manifests -> archived source docs (read-only)."""
import json, glob, os, sys, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
PREFIX = {'1150': 'alinma', '1030': 'saib', '1180': 'snb', '8010': 'tawuniya', '2222': 'aramco'}

def load_index():
    a = json.load(open(os.path.join(ROOT, 'data/raw/archive-index.json'), encoding='utf8'))['artifacts']
    m = collections.defaultdict(list)
    for x in a:
        for mf in x.get('metadata', {}).get('manifests', []):
            m[mf].append(x)
    return m

def inventory(sym):
    idx = load_index()
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data/imports', PREFIX[sym] + '*.json'))):
        name = os.path.basename(f)
        d = json.load(open(f, encoding='utf8'))
        arts = idx.get(name, [])
        facts = d.get('facts', [])
        out.append(dict(manifest=name, period_end=d.get('period_end'), filing_type=d.get('filing_type'),
                        url=d.get('source_url'), n_facts=len(facts), n_excluded=len(d.get('excluded_facts', [])),
                        local=[x['local_path'] for x in arts],
                        scales=sorted({str(x.get('scale')) for x in facts}),
                        kinds=sorted({str(x.get('period_kind')) for x in facts}),
                        pages=sorted({x.get('page') for x in facts if x.get('page') is not None}, key=str)))
    return out

if __name__ == '__main__':
    for r in inventory(sys.argv[1]):
        print(r['manifest'], r['period_end'], r['filing_type'], 'facts', r['n_facts'], 'excl', r['n_excluded'], r['scales'], r['kinds'], [os.path.basename(x)[:8] for x in r['local']], 'pages', r['pages'][:6])
