"""Value-on-page anchor for manifests without source labels (e.g. Aramco SAR-million tables)."""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from b_pages import rows, nums
from b_inventory import ROOT

def fmt_variants(v):
    a = abs(float(v))
    out = set()
    if a == int(a): out |= {a}
    out.add(a)
    return out

def check(manifest_path, pdf, label_key=('label', 'metric')):
    d = json.load(open(manifest_path, encoding='utf8'))
    cache, res = {}, []
    for f in d.get('facts', []):
        pg = f.get('page')
        if not pg: res.append((f.get('label') or f.get('metric'), 'nopage', f['value'])); continue
        if pg not in cache: cache[pg] = rows(pdf, pg)
        val = abs(float(f['value']))
        lab = re.sub(r'[^a-z0-9]', '', str(f.get('label') or '').lower())
        hit = None
        for y, t in cache[pg]:
            ns = [abs(n) for n in nums(t)]
            if any(abs(n - val) < 1e-9 or abs(n - val * 1.0) < 1e-6 for n in ns):
                tl = re.sub(r'[^a-z0-9]', '', t.lower())
                if not lab or lab[:18] in tl:
                    hit = ('label+value', t[:130]); break
                hit = hit or ('value_only', t[:130])
        res.append((f.get('label') or f.get('metric'), hit[0] if hit else 'NOT_FOUND', f['value'], f['period_end'] if 'period_end' in f else None, pg, hit[1] if hit else ''))
    return res

if __name__ == '__main__':
    mf = sys.argv[1]; pdf = sys.argv[2]
    r = check(mf, pdf)
    print(collections.Counter(x[1] for x in r))
    for x in r:
        if x[1] != 'label+value': print('   ', x)
