"""periods.py SYM : for each pdf, distinct 'ended/as at <date>' phrases from the first 10 pages (period/label audit)."""
import sys,glob,re,os,pymupdf,collections
RAW='C:/Users/Mohammed856/finengine-raw-odd/archive/SA'
pat=re.compile(r"(?i)(?:period|periods|year|years|months?|as at|as of|ended|ending)\s+(?:ended\s+)?(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|spe|oct|nov|dec)[a-z]*\s+20\d\d)")
for p in sorted(glob.glob(RAW+'/'+sys.argv[1]+'/*.pdf')):
    d=pymupdf.open(p); c=collections.Counter()
    for i in range(min(10,len(d))):
        t=re.sub(r'\s+',' ',d[i].get_text())
        for m in pat.finditer(t): c[m.group(1).lower()[:20]]+=1
    print(os.path.basename(p)[:8],len(d),dict(c.most_common(4)))
