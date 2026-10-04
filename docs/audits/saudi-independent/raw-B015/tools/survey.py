"""survey.py <sym>: per file, first-page period phrase vs collector label (read-only)."""
import sys,re,json,pymupdf,pg
sym=sys.argv[1]
d=json.load(open(pg.INV+f'/{sym}.json'))
for f in sorted(d['files'],key=lambda f:(f['fiscal_year'] or 0,f['period_slot'] or '')):
    p=__import__('os').path.join(pg.RAW,f['relpath'].replace('/',__import__('os').sep))
    doc=pymupdf.open(p)
    t=' '.join(doc[i].get_text() for i in range(min(3,len(doc))))
    t=re.sub(r'\s+',' ',t)
    m=re.findall(r'(?:ended|ENDED|as at|AS AT|للسنة المنتهية|المنتهية في)[^.]{0,40}?(?:20\d\d|19\d\d)',t)
    yrs=re.findall(r'20[012]\d',t[:600])
    sys.stdout.reconfigure(encoding='utf8');print(f['sha256'][:8],f['fiscal_year'],f['period_slot'],f['pages'],f['file_class'][:22],'|',(m[:1] or [''])[0][:70],'|',t[:110].replace('|',' '))
