"""peek.py sym sha [pages]: locate primary statement pages (earliest page with headline rows) and print key rows with all numeric columns."""
import sys, re, tx, pg
sym, sha = sys.argv[1:3]
m, d, ok = tx.getdoc(sym, [f for f in __import__('json').load(open(pg.INV + f'/{sym}.json', encoding='utf8'))['files'] if f['sha256'].startswith(sha)][0]['sha256'])
print(sha, m['fiscal_year'], m['period_slot'], 'pages', len(d), 'sha_ok', ok)
KEY = re.compile(r'(total assets|total liabilities|total (share|equity)|^(assets )?cash and cash|insurance revenue|insurance service|before zakat|after zakat|net (income|loss|profit)|per share|net cash|net (change|increase|decrease)|beginning|end of|zakat|income tax|gross written|net earned|total revenues|total (expenses|operating|underwriting)|statement of|net surplus|surplus)', re.I)
def pages_of(pred):
    return [i + 1 for i in range(len(d)) if pred(d[i].get_text())]
if len(sys.argv) > 3:
    pgs = [int(x) for x in sys.argv[3].split(',')]
else:
    A = pages_of(lambda t: re.search(r'total assets', t, re.I) and re.search(r'total liabilities', t, re.I) and not re.search(r'\bindex\b', t[:400], re.I))
    I = pages_of(lambda t: re.search(r'before zakat|net (income|loss|surplus)|per share', t, re.I) and re.search(r'revenue|premium|underwriting', t, re.I))
    C = pages_of(lambda t: re.search(r'operating activities', t, re.I) and re.search(r'investing activities', t, re.I) and re.search(r'financing', t, re.I))
    print('cand BS', A[:6], 'IS', I[:8], 'CF', C[:6])
    pgs = sorted(set(A[:2] + I[:3] + C[:2]))
for n in pgs:
    print('--- p', n)
    for lab, nums in tx.rows_of(d, n):
        if nums and KEY.search(lab): print('  ', lab[:105], '|', ' '.join(nums))
        elif not nums and re.search(r'statement of|for the (three|six|nine|year|period)|as at|31 december|30 (sept|june)|31 march', lab, re.I) and len(lab) < 200: print('  #', lab[:160])
