"""flat.py <sym> <sha> <pages>: text-layer page dump, one physical line per row, blank lines removed (read-only)."""
import sys,pymupdf,pg
sym,h,pgs=sys.argv[1:4]
m,p=pg.find(sym,h);d=pymupdf.open(p)
for n in [int(x) for x in pgs.split(',')]:
    print('--- p',n)
    print(' | '.join(l.strip() for l in d[n-1].get_text().splitlines() if l.strip()))
