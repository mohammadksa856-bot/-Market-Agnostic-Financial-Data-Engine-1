"""Verify unified-vs-base differences against the source PDF page.
python unified_verify.py <cmp.json> <out.json>
For each changed/added fact: is the stored |value| printed on the cited page in the row of its caption (new), and was the old one (old)?
Printed-row evidence only; column/period choice is checked by hand for sampled rows (see the report)."""
import sys, json, os, re, pymupdf
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
cmp_ = json.load(open(sys.argv[1], encoding='utf8'))
def fmt(v):
    f = abs(float(v)); s = f'{f:,.0f}' if f == int(f) else f'{f:,.2f}'
    return s
cache = {}
def rows(pdf, page):
    k = (pdf, page)
    if k not in cache:
        d = pymupdf.open(os.path.join(ROOT, pdf)); p = d[page - 1]; rs = {}
        for w in p.get_text('words'): rs.setdefault(round(w[1] / 5), []).append(w)
        cache[k] = [' '.join(w[4] for w in sorted(rs[y], key=lambda w: w[0])) for y in sorted(rs)]
    return cache[k]
def printed(pdf, page, label, value):
    if value is None: return None
    rs = rows(pdf, page); lab = re.sub(r'\W+', ' ', label.lower()).strip()[:18]; num = fmt(value)
    for i, r in enumerate(rs):
        if lab and lab in re.sub(r'\W+', ' ', r.lower()):
            if num in r or (i + 1 < len(rs) and num in rs[i + 1]) or (i > 0 and num in rs[i - 1]): return True
    return any(num in r for r in rs) and 'page-only'
out = {}
for n, e in cmp_['per_manifest'].items():
    pdf = e['pdf']; o = []
    for c in e['unified']['changed']:
        o.append({'kind': 'changed', 'fact': c['fact'], 'old': c['old'], 'new': c['new'],
                  'old_printed': printed(pdf, c['page_old'], c['label_old'], c['old']),
                  'new_printed': printed(pdf, c['page_new'], c['label_new'], c['new'])})
    for c in e['unified']['added']:
        o.append({'kind': 'added', 'fact': c['fact'], 'new': c['new'], 'label': c['label'], 'page': c['page'], 'new_printed': printed(pdf, c['page'], c['label'], c['new'])})
    for c in e['unified']['disappeared']:
        o.append({'kind': 'disappeared', 'fact': c['fact'], 'old': c['old'], 'label': c['label'], 'page': c['page']})
    out[n] = o
json.dump(out, open(sys.argv[2], 'w'), indent=1)
import collections
cnt = collections.Counter((x['kind'], str(x.get('new_printed'))) for o in out.values() for x in o)
print(cnt)
