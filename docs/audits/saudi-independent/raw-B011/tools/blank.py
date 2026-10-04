"""blank.py <sym> <shaprefix>...: list textless pages (image-only) and pages whose text mentions financial position, per file."""
import sys, re, pymupdf, pg
sym = sys.argv[1]
for h in sys.argv[2:]:
    m, p = pg.find(sym, h); d = pymupdf.open(p)
    blank = [i + 1 for i in range(len(d)) if len(d[i].get_text().strip()) < 40]
    txt = [i + 1 for i in range(min(len(d), 20)) if re.search(r"statement of financial position|statement of profit|statement of cash", d[i].get_text()[:600], re.I)]
    print(h, m['fiscal_year'], m['period_slot'], 'pages', len(d), 'blank', blank[:14], 'stmt-title-text', txt)
