"""cover.py SYM : sha256 + first-page title text for every pdf of a company (period/entity check)."""
import sys,glob,re,hashlib,pymupdf,os
RAW='C:/Users/Mohammed856/finengine-raw-odd/archive/SA'
for p in sorted(glob.glob(RAW+'/'+sys.argv[1]+'/*')):
    n=os.path.basename(p)
    if not p.endswith('.pdf'): print(n[:8],'NONPDF',n[-10:]); continue
    d=pymupdf.open(p); out=''
    for i in range(min(3,len(d))):
        t=d[i].get_text(); t=re.sub(r'\s+',' ',t).strip()
        if len(t)>40: out=t; break
    print(n[:8],len(d),'|',out[:int(sys.argv[2]) if len(sys.argv)>2 else 230])
