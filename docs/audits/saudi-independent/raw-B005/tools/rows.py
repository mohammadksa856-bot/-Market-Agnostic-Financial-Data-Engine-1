"""rows.py <sym> <sha> <pages> [filter-regex]: text-layer rows, label followed by its numbers on one line."""
import sys,re,pymupdf,pg
sym,h,pgs=sys.argv[1:4];flt=re.compile(sys.argv[4],re.I) if len(sys.argv)>4 else None
m,p=pg.find(sym,h);d=pymupdf.open(p)
num=re.compile(r'^[\(\-]?[\d,]+(\.\d+)?\)?%?$|^-$')
for n in [int(x) for x in pgs.split(',')]:
    print('--- p',n)
    lab='';nums=[]
    def flush():
        global lab,nums
        if lab or nums:
            s=(lab+'  '+'  '.join(nums)).strip()
            if not flt or flt.search(s): print(s[:200])
        lab='';nums=[]
    for l in d[n-1].get_text().splitlines():
        l=l.strip()
        if not l: continue
        if num.match(l): nums.append(l)
        else:
            if nums: flush()
            lab=(lab+' '+l).strip() if len(lab)<80 and not lab.endswith(')') else l
    flush()
