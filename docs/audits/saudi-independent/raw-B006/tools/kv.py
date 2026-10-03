"""kv.py <sym> <shaprefix> [maxpages]: find statement pages by title in the text layer and print key rows (read-only)."""
import sys,re,pymupdf,pg
sym,h=sys.argv[1:3]
m,p=pg.find(sym,h);d=pymupdf.open(p)
titles=re.compile(r'statement of (financial position|profit|income|comprehensive income|cash flows|changes in)|balance sheet|STATEMENT OF (FINANCIAL POSITION|PROFIT|INCOME|CASH FLOWS)',re.I)
key=re.compile(r'total assets|total liabilities|total equity|revenue|sales|gross profit|operating (profit|income)|profit|income for the|net income|attributable|owners|non-?controlling|per share|cash and cash|net cash|net (increase|decrease|change)|beginning|end of|acquisition of prop|purchase of prop|capital expend|total current|total non',re.I)
num=re.compile(r'^[\(\-]?[\d,]+(\.\d+)?\)?%?$|^-$|^--$')
print(h,m['fiscal_year'],m['period_slot'],'pages',len(d),'sha_ok',pg.sha(p)==m['sha256'])
for i,x in enumerate(d,1):
    t=x.get_text()
    if len(t.strip())<30: continue
    head=' '.join(t.split()[:60])
    if titles.search(head) and not re.search(r'contents|index',head,re.I):
        print('--- pdf p%d: %s'%(i,head[:110]))
        lab='';nums=[]
        out=[]
        for l in t.splitlines():
            l=l.strip()
            if not l: continue
            if num.match(l): nums.append(l)
            else:
                if nums or lab:
                    out.append((lab+'  '+'  '.join(nums)).strip());lab='';nums=[]
                lab=(lab+' '+l).strip() if len(lab)<60 and not lab.endswith(')') else l
        out.append((lab+'  '+'  '.join(nums)).strip())
        for s in out:
            if key.search(s) and re.search(r'\d{3}',s): print('  ',s[:170])
