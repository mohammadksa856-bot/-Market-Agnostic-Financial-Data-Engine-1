"""tx.py: build a transcript doc entry from text-layer rows of named PDF pages, by label regex and column index (from the right).
Every value is read from the printed page; a key that does not match exactly one row (or the n-th) raises, so nothing is guessed.
Usage as a module: from tx import doc_entry, save ; see spec files in specs/."""
import json, re, sys, pymupdf, pg
NUM = re.compile(r'^\(?-?[\d,]+(\.\d+)?\)?$|^-{1,2}$')
def rows_of(d, n):
    out = []; lab = ''; nums = []
    def flush():
        nonlocal lab, nums
        if lab or nums: out.append((re.sub(r'^[─═\s]+(?:[─═]+\s*)*', '', lab.strip()), nums))
        lab = ''; nums = []
    for l in d[n - 1].get_text().splitlines():
        l = l.strip()
        if not l: continue
        if NUM.match(l): nums.append(l)
        else:
            if nums: flush()
            lab = (lab + ' ' + l).strip() if len(lab) < 80 and not lab.endswith(')') else l
    flush(); return out
def val(s):
    if s in ('-', '--'): return 0
    neg = s.startswith('(') or s.startswith('-')
    v = float(s.strip('()-').replace(',', ''))
    v = int(v) if v == int(v) and '.' not in s else v
    return -v if neg else v
_cache = {}
def getdoc(sym, sha):
    k = (sym, sha)
    if k not in _cache:
        m, p = pg.find(sym, sha); _cache[k] = (m, pymupdf.open(p), pg.sha(p) == m['sha256'])
    return _cache[k]
def grab(sym, sha, page, regex, col, occ=0, minnums=2):
    m, d, ok = getdoc(sym, sha)
    hits = [(lab, nums) for lab, nums in rows_of(d, page) if re.search(regex, lab, re.I) and len(nums) >= minnums]
    if len(hits) <= occ: raise SystemExit(f'NO MATCH p{page} /{regex}/ occ{occ} hits={len(hits)}')
    lab, nums = hits[occ]
    return val(nums[col])
def doc_entry(sym, sha, label, period_end, period_type, prior_period_end, bs_prior_period_end, reading, spec):
    """spec: {stmt: {'page': n, 'cols': {'cur': -2, 'prior': -1}, 'keys': {key: regex | (regex, occ)}}} ; stmt in bs, is, is_q, cf"""
    m, d, ok = getdoc(sym, sha)
    assert ok, 'sha mismatch'
    e = {'sha256_prefix': sha[:8], 'label': label, 'period_end': period_end, 'period_type': period_type,
         'prior_period_end': prior_period_end, 'bs_prior_period_end': bs_prior_period_end, 'reading': reading, 'pages': {}}
    for stmt, s in spec.items():
        e['pages'][stmt] = s['page']
        e[stmt] = {}
        for col, ci in s['cols'].items():
            e[stmt][col] = {}
            for k, rx in s['keys'].items():
                occ = 0
                if isinstance(rx, tuple): rx, occ = rx
                e[stmt][col][k] = grab(sym, sha, s['page'], rx, ci, occ, s.get('minnums', 2))
    return e
def save(sym, header, entries, extra=None):
    import os
    fn = os.path.join(os.path.dirname(__file__), '..', 'transcripts', f'{sym}.json')
    t = dict(header); t['docs'] = entries
    if extra: t.update(extra)
    json.dump(t, open(fn, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('saved', fn, len(entries))

# ---- standard insurer key table (regex on the row label; first row with enough numbers) ----
STD = {
 'bs': {'total_assets': r'^total assets$', 'total_liabilities': r'^total liabilities$', 'total_equity': r'^total (shareholders.? )?equity$', 'cash': r'cash and cash equivalents', 'insurance_contract_liabilities': r'^(liabilities )?insurance contract liabilities'},
 'is': {'insurance_revenue': r'(^|000 |revenue )insurance revenue', 'insurance_service_expenses': r'^insurance service expenses', 'insurance_service_result': r'^(net )?insurance service result', 'net_investment_income': r'^net investment income', 'pbt': r'(income|loss|profit|earnings).{0,60}before zakat', 'zakat_tax': r'^((provision|\(expense\) / income|expense|reversal) (for )?)?zakat( and (income )?tax)?( charge| expense| provision)?$', 'income_tax': r'^income tax( charge| expense)?$', 'net_income': r'^net (income|loss|profit|\(loss\)|\(income\)).{0,80}after zakat', 'eps': r'(earnings|loss|\(loss\)|income).{0,30}per share'},
 'cf': {'cfo': r'^net cash.{0,45}operating', 'cfi': r'^net cash.{0,45}investing', 'cff': r'^net cash.{0,45}financing', 'net_change': r'^net (change|increase|decrease|\(decrease\)|increase / \(decrease\)).{0,30}cash', 'cash_begin': r'^cash and cash equivalents.{0,5}(at the )?beginning', 'cash_end': r'^cash and cash equivalents.{0,5}(at the )?end'},
}
def grab_opt(sym, sha, page, regex, col, occ=0):
    m, d, ok = getdoc(sym, sha)
    hits = [(lab, nums) for lab, nums in rows_of(d, page) if re.search(regex, lab, re.I) and len(nums) >= (abs(col) if col < 0 else col + 1)]
    if len(hits) <= occ: return None
    return val(hits[occ][1][col])
def std(sym, sha, label, period_end, period_type, prior_period_end, bs_prior_period_end, reading, spec, drop=(), add=None, patch=None):
    """spec: {stmt: {'page': n, 'cols': {...}, 'drop': [keys], 'add': {key: regex|(regex,occ)}}} ; stmt may be 'is_q' (uses 'is' key table)"""
    m, d, ok = getdoc(sym, sha); assert ok, 'sha mismatch'
    e = {'sha256_prefix': sha[:8], 'label': label, 'period_end': period_end, 'period_type': period_type,
         'prior_period_end': prior_period_end, 'bs_prior_period_end': bs_prior_period_end, 'reading': reading, 'pages': {}}
    missing = []
    for stmt, s in spec.items():
        tab = dict(STD['is' if stmt == 'is_q' else stmt])
        for k in s.get('drop', []): tab.pop(k, None)
        tab.update(s.get('add', {}))
        e['pages'][stmt] = s['page']; e[stmt] = {}
        for col, ci in s['cols'].items():
            e[stmt][col] = {}
            for k, rx in tab.items():
                occ = 0
                if isinstance(rx, tuple): rx, occ = rx
                v = grab_opt(sym, sha, s['page'], rx, ci, occ)
                if v is None: missing.append((stmt, col, k))
                else: e[stmt][col][k] = v
    for (stmt, col), kv in (patch or {}).items():
        e[stmt][col].update(kv)
    ms = sorted({(a, c) for a, b, c in missing})
    print(label, 'missing:', ms)
    return e

def quarter_sums(years, have, keys=('insurance_revenue', 'pbt', 'net_income'), tol=None):
    """auto-generate Q1+Q2=H1 and H1+Q3=9M chains (exact; tol = {(year,key,chain): (tol, note)} for declared rounding)."""
    out = []; tol = tol or {}
    for y in years:
        for k in keys:
            for chain, parts, total in (('Q1+Q2=H1', [[f'Q1 {y}', 'is', 'cur', k], [f'H1 {y}', 'is_q', 'cur', k]], [f'H1 {y}', 'is', 'cur', k]),
                                        ('H1+Q3=9M', [[f'H1 {y}', 'is', 'cur', k], [f'9M {y}', 'is_q', 'cur', k]], [f'9M {y}', 'is', 'cur', k])):
                if not all(x[0] in have for x in parts + [total]): continue
                q = {'key': k, 'note': f'{y} {chain}', 'parts': parts, 'total': total}
                if (y, k, chain) in tol: q['tol'], q['note'] = tol[(y, k, chain)][0], f'{y} {chain}: {tol[(y, k, chain)][1]}'
                out.append(q)
    return out
