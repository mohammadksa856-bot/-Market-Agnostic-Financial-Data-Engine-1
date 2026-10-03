"""stmt_pages.py SYM [prefix..] : per PDF, which pages are *actual* primary-statement pages (title near top AND >=12 numeric tokens
in the text layer), versus pages that only mention a title (TOC / notes), plus image-only (no text) pages inside the document body.
A statement is 'text-confirmed' only when such an actual page exists; else 'image-only-or-absent' (needs rendering)."""
import sys,glob,re,os,pymupdf
RAW='C:/Users/Mohammed856/finengine-raw-odd/archive/SA'
T={'BS':r'statement of financial position|balance sheet|financial position|الميزانية|المركز المالي|قائمة المركز',
   'IS':r'statement of profit or loss|statement of income|income statement|statement of comprehensive income|statements? of operations|profit or loss and other|قائمة الدخل|قائمة الربح|الدخل الشامل|قائمة الأرباح',
   'CF':r'statement of cash flows?|cash flows? statement|التدفقات النقدية',
   'EQ':r'changes in (?:shareholders|owners|stockholders)?.{0,10}equity|التغيرات في حقوق'}
NUM=re.compile(r'\(?\d[\d,]{3,}\)?')
def scan(p):
    d=pymupdf.open(p); res={k:[] for k in T}; img=[]
    for i,pg in enumerate(d):
        t=pg.get_text(); tl=t.lower()
        if len(t.strip())<25: img.append(i+1); continue
        head=tl[:450]
        nn=len(NUM.findall(t))
        if re.search(r'notes? to the|table of contents|contents|^\s*\d+\s*$',head[:200]) and nn<12: continue
        for k,pat in T.items():
            if re.search(pat,head) and nn>=12 and not re.search(r'notes to the (?:consolidated|interim|condensed)',head[:160]): res[k].append(i+1)
    return len(d),res,img
if __name__=='__main__':
    sym=sys.argv[1]; pres=sys.argv[2:]
    for p in sorted(glob.glob(RAW+'/'+sym+'/*.pdf')):
        b=os.path.basename(p)[:8]
        if pres and b not in pres: continue
        try: n,res,img=scan(p)
        except Exception as e: print(b,'ERR',e); continue
        conf=''.join(k[0] if res[k] else '-' for k in ('BS','IS','CF','EQ'))
        print(b,n,'text-confirmed[BS,IS,CF,EQ]:',''.join('X' if res[k] else '.' for k in ('BS','IS','CF','EQ')),{k:v[:4] for k,v in res.items() if v},'imgpages',(img if len(img)<=12 else f'{len(img)} pages e.g. {img[:12]}'))
