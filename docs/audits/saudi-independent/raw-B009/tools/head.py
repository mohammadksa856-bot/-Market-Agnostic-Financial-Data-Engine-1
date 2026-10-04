import sys,pymupdf,pg,re
sym,h=sys.argv[1:3]
m,p=pg.find(sym,h);d=pymupdf.open(p)
print(h,m['fiscal_year'],m['period_slot'],'pages',len(d),'sha_ok',pg.sha(p)==m['sha256'])
for i,pgx in enumerate(d):
    t=pgx.get_text()
    if i<2: print('p%d'%(i+1),' | '.join(l.strip() for l in t.splitlines() if l.strip())[:300] or '[no text]')
empty=[i+1 for i,pgx in enumerate(d) if len(pgx.get_text().strip())<30]
print('textless pages',empty)
