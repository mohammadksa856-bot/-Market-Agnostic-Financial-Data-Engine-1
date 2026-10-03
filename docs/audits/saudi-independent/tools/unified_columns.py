"""Heuristic column-position check of every changed/added unified fact.
python unified_columns.py <cmp.json> <out.json>
For the caption row on the cited page, list the printed numbers; the chosen value's position among them is compared with the
expected position (current period = first column; in a 4-column quarter|ytd layout ytd = 3rd). Flags are candidates for manual review."""
import sys, json, os, re, pymupdf
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
cmp_ = json.load(open(sys.argv[1], encoding='utf8')); cache = {}
NUM = re.compile(r'^\(?-?[\d][\d,]*(?:[.,]\d+)?\)?$')
def rows(pdf, page):
    k = (pdf, page)
    if k not in cache:
        d = pymupdf.open(os.path.join(ROOT, pdf)); rs = {}
        for w in d[page - 1].get_text('words'): rs.setdefault(round(w[1] / 5), []).append(w)
        cache[k] = [[w[4] for w in sorted(rs[y], key=lambda w: w[0])] for y in sorted(rs)]
    return cache[k]
def fmt(v):
    f = abs(float(v)); return f'{f:,.0f}' if f == int(f) else f'{f:,.2f}'
out = []; 
for n, e in cmp_['per_manifest'].items():
    pdf = e['pdf']
    items = [(c['fact'], c['new'], c['label_new'], c['page_new'], 'changed') for c in e['unified']['changed']] + \
            [(c['fact'], c['new'], c['label'], c['page'], 'added') for c in e['unified']['added']]
    for fact, val, label, page, kind in items:
        kindp = fact.split('|')[1]; num = fmt(val)
        lab = re.sub(r'\W+', ' ', label.lower()).strip()[:18]
        for i, r in enumerate(rows(pdf, page)):
            if lab not in re.sub(r'\W+', ' ', ' '.join(r).lower()): continue
            cand = r + (rows(pdf, page)[i + 1] if i + 1 < len(rows(pdf, page)) else [])
            toks = [t.strip('()') for t in r if NUM.match(t)]
            if num not in [t for t in toks]: toks = [t.strip('()') for t in cand if NUM.match(t)]
            if num not in toks: continue
            idx = toks.index(num)
            data = [t for t in toks if (',' in t or '.' in t or len(t) > 3)]  # drop bare note numbers
            didx = data.index(num) if num in data else None
            exp = {'quarter': 0, 'fy': 0, 'instant': 0, 'ytd': 2 if len(data) == 4 else 0}.get(kindp)
            if didx is not None and didx != exp and not (len(data) == 3 and kindp == 'ytd' and didx in (1, 2)):
                out.append({'manifest': n, 'fact': fact, 'value': val, 'label': label, 'page': page, 'kind': kind, 'printed_numbers': data, 'chosen_index': didx, 'expected_index': exp})
            break
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(len(out), 'flagged')
for o in out: print(o['manifest'], o['fact'].split('|')[0], o['fact'].split('|')[1], o['value'], o['printed_numbers'], o['chosen_index'], o['expected_index'])
