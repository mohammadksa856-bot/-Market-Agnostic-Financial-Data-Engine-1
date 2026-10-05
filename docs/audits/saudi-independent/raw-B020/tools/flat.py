"""flat.py <sym> <sha> <pages>: page text flattened to one line (pipe separated), for statement pages with clean text layers."""
import sys,pymupdf,pg
sym,h,pgs=sys.argv[1:4];m,p=pg.find(sym,h);d=pymupdf.open(p)
for n in [int(x) for x in pgs.split(',')]:
    print('--- p',n);print('|'.join(l.strip() for l in d[n-1].get_text().splitlines() if l.strip()))
