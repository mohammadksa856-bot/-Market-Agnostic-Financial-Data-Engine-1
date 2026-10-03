"""Helpers for audit B001 record building (read-only on raw files)."""
import json,glob,hashlib,os
RAW='C:/Users/Mohammed856/finengine-raw-odd/archive/SA'
INV='../raw-coverage/companies/'
_h={}
def sha(sym,pre):
    m=glob.glob(f'{RAW}/{sym}/{pre}*')+glob.glob(f'{RAW}/{sym}/*/{pre}*')
    m=[x for x in m if os.path.isfile(x)]
    assert len(m)==1,(sym,pre,m)
    k=m[0]
    if k not in _h: _h[k]=hashlib.sha256(open(k,'rb').read()).hexdigest()
    assert _h[k].startswith(pre)
    return _h[k]
def inv(sym): return json.load(open(f'{INV}{sym}.json'))
def invfile(sym,pre):
    return [f for f in inv(sym)['files'] if f['sha256'].startswith(pre)][0]
def write(sym,rec):
    with open(f'{sym}.json','w',encoding='utf-8') as f: json.dump(rec,f,ensure_ascii=False,indent=1)
def files_table(sym,verdicts):
    """verdicts: {pre8: dict(actual_period=..., verdict=..., note=...)}; adds inventory facts + verified full sha"""
    out=[]
    for f in sorted(inv(sym)['files'],key=lambda f:(f['fiscal_year'] or 0,f['period_slot'] or '',f['sha256'])):
        pre=f['sha256'][:8]; v=verdicts.get(pre,{})
        out.append({'sha256':sha(sym,f['sha256'][:12]),'collector_label':f"{f['fiscal_year']}|{f['period_slot']}",'inventory_class':f['file_class'],
                    'pages':f['pages'],'inventory_flags':f['flags'],**v})
    missing=set(verdicts)-{f['sha256'][:8] for f in inv(sym)['files']}
    assert not missing,missing
    return out
