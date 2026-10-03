"""Re-read every finengine.reading/1 manifest in data/imports (read-only) with the reader in a given src tree.

usage: python unified_reread.py <src_dir> <out.json> [repo_root]
Nothing under data/ is written. Output: {manifest: {"ok":bool,"error":str|None,"facts":{key: {...}}}}
"""
import sys, os, json, glob, collections, traceback
src, out = sys.argv[1], sys.argv[2]
ROOT = os.path.abspath(sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.abspath(src))
from finengine.reading import StatementReader
import finengine.reading as R
idx = collections.defaultdict(list)
for x in json.load(open(os.path.join(ROOT, 'data/raw/archive-index.json'), encoding='utf8'))['artifacts']:
    for m in x['metadata'].get('manifests', []): idx[m].append(x)

def key(f):
    return '|'.join([f['metric'], f['period_kind'], f['period_end'], f.get('scope', '') or '', json.dumps(f.get('dimensions') or {}, sort_keys=True)])

res = {'reader_file': R.__file__}
for f in sorted(glob.glob(os.path.join(ROOT, 'data/imports/*.json'))):
    name = os.path.basename(f)
    d = json.load(open(f, encoding='utf8'))
    if d.get('reader') != 'finengine.reading/1':
        continue
    arts = [a for a in idx.get(name, []) if a['local_path'].lower().endswith('.pdf')]
    path = None
    for a in arts:
        p = os.path.join(ROOT, a['local_path'].replace(chr(92), '/'))
        if os.path.exists(p): path = p; break
    rec = {'ok': False, 'error': None, 'pdf': path and os.path.relpath(path, ROOT).replace(chr(92), '/'),
           'manifest_facts': {key(x): x['value'] for x in d.get('facts', [])}, 'facts': {}}
    if path is None:
        rec['error'] = 'source PDF not on disk'
    else:
        try:
            r = StatementReader(path, enable_ocr=False).read(
                d['market'], d['symbol'], d.get('currency') or 'SAR', d['source_url'], d['filed_at'],
                period_end=d['period_end'], fiscal_year=int(d['period_end'][:4]),
                filing_type=d['filing_type'], profile=d.get('profile', 'corporate'))
            rec['ok'] = True
            for x in r['facts']:
                rec['facts'][key(x)] = {'value': x['value'], 'label': x.get('source_label'), 'page': x.get('page')}
        except Exception as e:
            rec['error'] = (type(e).__name__ + ': ' + str(e))[:200]
    res[name] = rec
    print(name, rec['ok'], rec['error'] or len(rec['facts']), flush=True)
json.dump(res, open(out, 'w', encoding='utf8'), ensure_ascii=False)
