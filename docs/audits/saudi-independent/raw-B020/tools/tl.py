import json,sys,pymupdf,pg,os
d=json.load(open(pg.INV+'/'+sys.argv[1]+'.json'))
for f in sorted(d['files'],key=lambda f:(f['fiscal_year'] or 0,f['period_slot'] or '')):
    if f['file_class'] not in('results_announcement','other_no_statements_found','presentation'):
        doc=pymupdf.open(os.path.join(pg.RAW,f['relpath'].replace('/',os.sep)))
        tl=[i+1 for i,x in enumerate(doc) if len(x.get_text().strip())<30]
        print(f['sha256'][:8],f['fiscal_year'],f['period_slot'],f['file_class'][:12],len(doc),'textless',tl,f['statement_pages'])
