"""Whole-document value locator: where does each published value occur; is the cited page one of them (as PDF index or printed number = index-2)?"""
import sys, re, json, collections, fitz
def load(pdf):
    d = fitz.open(pdf); return [re.sub(r'\s+', ' ', p.get_text()) for p in d]
def variants(v, scale=None):
    a = abs(float(v)); out = set()
    if a == int(a):
        out.add('{:,}'.format(int(a))); out.add(str(int(a)))
    else:
        for dec in (1, 2, 3, 4):
            out.add(('{:,.%df}' % dec).format(a))
        s = repr(a); out.add(s)
    return out
def run(manifest, pdf, offset=2):
    texts = load(pdf)
    d = json.load(open(manifest, encoding='utf8'))
    res = []
    for f in d.get('facts', []):
        vs = variants(f['value'])
        pages = [i + 1 for i, t in enumerate(texts) if any(re.search(r'(?<![\d,.])' + re.escape(v) + r'(?![\d,]|\.\d)', t) for v in vs)]
        pg = f.get('page')
        cited = 'nopage' if pg is None else ('cited_ok_pdf' if pg in pages else ('cited_ok_printed' if (pg + offset) in pages else 'cited_NOT_found'))
        res.append((f.get('label') or f.get('metric'), f['value'], f.get('period_end'), pg, cited, pages[:6] if pages else 'ABSENT'))
    return res
if __name__ == '__main__':
    r = run(sys.argv[1], sys.argv[2])
    print(collections.Counter(x[4] for x in r), 'absent:', sum(1 for x in r if x[5] == 'ABSENT'))
    for x in r:
        if x[4] == 'cited_NOT_found' or x[5] == 'ABSENT': print('   ', x)
