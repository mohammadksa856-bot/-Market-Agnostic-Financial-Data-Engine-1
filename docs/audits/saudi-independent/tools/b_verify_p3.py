"""Pillar-3 KM1 verifier: each published/excluded fact vs the y-aligned PDF row at its cell column."""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from b_inventory import ROOT, inventory
from b_pages import rows, nums

def check(sym, mf):
    inv = {r['manifest']: r for r in inventory(sym)}[mf]
    d = json.load(open(os.path.join(ROOT, 'data/imports', mf), encoding='utf8'))
    pdf = os.path.join(ROOT, inv['local'][0])
    allf = [('pub', x) for x in d.get('facts', [])] + [('exc', x) for x in d.get('excluded_facts', [])]
    ncols = max((ord(x['cell']) - 96 for _, x in allf if x.get('cell')), default=0)
    cache = {}
    out = []
    for kind, x in allf:
        pg = x['page']
        if pg not in cache: cache[pg] = rows(pdf, pg)
        row = str(x['row'])
        val = float(x['value'])
        status, text = 'row_not_found', ''
        R = cache[pg]
        for i, (y, t) in enumerate(R):
            toks = t.split()
            if toks and toks[0] == row:
                # wrapped captions: numbers may sit on the next 1-2 physical rows (before the next row-number row)
                j = i + 1
                while len(nums(' '.join(t.split()[1:]) if False else t)) < ncols + 0 and j < len(R) and j <= i + 2 and not (R[j][1].split() and R[j][1].split()[0].isdigit() and len(R[j][1].split()) > 2 and R[j][1].split()[0] != row):
                    t = t + '  ' + R[j][1]; j += 1
                ns = nums(t)
                tail = ns[-ncols:] if len(ns) >= ncols else ns
                idx = ord(x['cell']) - 97
                if idx < len(tail):
                    got = tail[idx]
                    ok = abs(abs(got) - abs(val)) < 1e-6 or abs(abs(got) - abs(val) * 100) < 1e-6
                    status = 'ok' if ok else 'MISMATCH(got %s)' % got
                    text = t
                    if ok: break
                else:
                    status, text = 'short_row', t
        out.append((kind, x['metric'], x['period_end'], x['cell'], x['value'], status, x.get('reason'), text[:140]))
    return ncols, out

if __name__ == '__main__':
    sym = sys.argv[1]
    tot = collections.Counter()
    for r in inventory(sym):
        if 'pillar3' not in r['manifest'] and 'pillar-3' not in r['manifest']: continue
        try: n, out = check(sym, r['manifest'])
        except Exception as e: print(r['manifest'], 'ERR', e); continue
        c = collections.Counter(o[5].split('(')[0] for o in out)
        tot.update(c)
        print(r['manifest'][:60].ljust(60), 'ncols', n, dict(c))
        for o in out:
            if o[5] != 'ok' and o[0]=='pub': print('     ', o)
    print(tot)


MONTHS = {m: i + 1 for i, m in enumerate(['january','february','march','april','may','june','july','august','september','october','november','december'])}
MON3 = {k[:3]: v for k, v in MONTHS.items()}
import datetime
def _dates_in(txt):
    found = []
    for m in re.finditer(r'(?:(\d{1,2})[\s-]+)?([A-Za-z]{3,9})[\.\s-]+(?:(\d{1,2}),?[\s-]+)?(\d{4})', txt):
        d1, mon, d2, yr = m.groups()
        k = mon.lower()
        mm = MONTHS.get(k) or (MON3.get(k[:3]) if k[:3] in MON3 and len(k) <= 9 else None)
        if not mm: continue
        day = int(d1 or d2 or 0)
        try: found.append(datetime.date(int(yr), mm, day).isoformat())
        except ValueError:
            import calendar
            found.append(datetime.date(int(yr), mm, calendar.monthrange(int(yr), mm)[1]).isoformat())
    return found

def header_dates(rowlist, need=5, ymax=260):
    """Left-to-right dates of the best header row (single physical row with the most dates; else concatenation of adjacent rows)."""
    best = []
    for y, t in rowlist:
        if y > ymax: break
        ds = _dates_in(t)
        if len(ds) > len(best): best = ds
    if len(best) >= need: return best
    # header split across two or three adjacent rows ("September 30," / "2021"): join
    for k in range(len(rowlist)):
        if rowlist[k][0] > ymax: break
        t = ' '.join(r[1] for r in rowlist[k:k + 3])
        ds = _dates_in(t)
        if len(ds) > len(best): best = ds
    return best

def check_headers(sym, mf):
    inv = {r['manifest']: r for r in inventory(sym)}[mf]
    d = json.load(open(os.path.join(ROOT, 'data/imports', mf), encoding='utf8'))
    pdf = os.path.join(ROOT, inv['local'][0])
    res = collections.Counter(); bad = []
    allf = d.get('facts', []) + d.get('excluded_facts', [])
    pages = {x['page'] for x in allf}
    hd = {p: header_dates(rows(pdf, p)) for p in pages}
    for x in allf:
        hs = hd[x['page']]
        idx = ord(x['cell']) - 97
        if idx < len(hs):
            ok = hs[idx] == x['period_end']
            res['ok' if ok else 'BAD'] += 1
            if not ok: bad.append((x['metric'], x['cell'], x['period_end'], hs))
        else: res['no_header'] += 1
    return dict(res), bad[:3], hd


def seq_check(sym, mf):
    """cell letters must map to consecutive quarter-ends stepping back from the manifest period_end (col a = newest)."""
    import calendar
    d = json.load(open(os.path.join(ROOT, 'data/imports', mf), encoding='utf8'))
    allf = d.get('facts', []) + d.get('excluded_facts', [])
    pe = datetime.date.fromisoformat(d['period_end'])
    bycell = collections.defaultdict(set)
    for x in allf: bycell[x['cell']].add(x['period_end'])
    issues = []
    for c, ds in sorted(bycell.items()):
        k = ord(c) - 97
        y, m = pe.year, pe.month - 3 * k
        while m <= 0: m += 12; y -= 1
        exp = datetime.date(y, m, calendar.monthrange(y, m)[1]).isoformat()
        if ds != {exp}: issues.append((c, sorted(ds), exp))
    return issues
