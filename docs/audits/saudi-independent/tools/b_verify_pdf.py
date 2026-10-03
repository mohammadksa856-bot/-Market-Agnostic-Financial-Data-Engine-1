"""Batch1-B: anchor each manifest fact to a y-aligned row on its cited PDF page. Read-only; prints evidence."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
from b_inventory import ROOT, inventory
from b_pages import rows, nums, npages

def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower().replace('�', ''))

def check_manifest(sym, mf, verbose=True, manifest_path=None, pdf_path=None):
    if pdf_path:  # candidate manifests / documents that live outside this checkout (read-only extracts)
        d = json.load(open(manifest_path, encoding='utf8')); pdfs = [pdf_path]; pdf = pdf_path
    else:
        inv = {r['manifest']: r for r in inventory(sym)}[mf]
        d = json.load(open(os.path.join(ROOT, 'data/imports', mf), encoding='utf8'))
        pdfs = [p for p in inv['local'] if p.lower().endswith('.pdf')]
        if not pdfs: return dict(manifest=mf, error='no pdf in archive', local=inv['local'])
        pdf = os.path.join(ROOT, pdfs[0])
    cache = {}
    res = []
    for f in d.get('facts', []):
        pg = f.get('page')
        if pg is None: res.append((f['metric'], 'nopage')); continue
        if pg not in cache: cache[pg] = rows(pdf, pg)
        lab = norm(f['source_label'])
        val = float(f['value'])
        cand = [(y, t) for y, t in cache[pg] if lab and lab[:25] in norm(t)]
        status, info, fr, rel = 'label_not_found', '', None, None
        for y, t in cand:
            ns = nums(t)
            hit = [i for i, n in enumerate(ns) if abs(abs(n) - abs(val)) < 1e-6 or abs(abs(n) - abs(val) / 100) < 1e-6]
            if hit:
                status = 'ok_col%d_of_%d' % (hit[0], len(ns)); info = t; fr = len(ns) - hit[0]; rel = ('same' if (ns[hit[0]] > 0) == (val > 0) or val == 0 else 'flipped'); break
            status = 'value_not_in_row'; info = t
        res.append((f['metric'], status, f['value'], f.get('period_kind'), f['period_end'], pg, info[:160], fr, rel))
    return dict(manifest=mf, pdf=pdfs[0], results=res)

if __name__ == '__main__':
    sym = sys.argv[1]
    for mf in sys.argv[2:]:
        r = check_manifest(sym, mf)
        print('##', mf, r.get('pdf', r.get('error')))
        for x in r.get('results', []): print('  ', x)


def summarize(sym, mf):
    import collections
    r = check_manifest(sym, mf)
    c = collections.defaultdict(collections.Counter)
    odd = []
    for x in r.get('results', []):
        if len(x) < 9: odd.append(x); continue
        if not x[1].startswith('ok'): odd.append(x)
        c[(x[3], x[5])][x[7]] += 1
    return {str(k): dict(v) for k, v in c.items()}, odd


def sign_relations(sym, manifests):
    import collections
    rel = collections.defaultdict(collections.Counter)
    ex = collections.defaultdict(list)
    for mf in manifests:
        for x in check_manifest(sym, mf).get('results', []):
            if len(x) >= 9 and x[8]:
                rel[x[0]][x[8]] += 1
                if len(ex[(x[0], x[8])]) < 2: ex[(x[0], x[8])].append((mf, x[3], x[4], x[2], x[6][:70]))
    return rel, ex
