import json,sys,pg
sys.stdout.reconfigure(encoding='utf8')
d=json.load(open(pg.INV+'/'+sys.argv[1]+'.json',encoding='utf8'))
for f in sorted(d['files'],key=lambda f:(f['fiscal_year'] or 0,f['period_slot'] or '')):
    print(f['sha256'][:8],f['fiscal_year'],f['period_slot'],f['pages'],f['file_class'][:24],f.get('language'),f.get('statement_pages'),f['relpath'][-40:])
