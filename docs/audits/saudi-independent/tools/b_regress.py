"""Re-read archived PDFs with the CURRENT reader and diff against published manifests (offline; nothing written)."""
import sys, os, json, glob, collections
sys.path.insert(0, os.environ.get('FINENGINE_SRC') or os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
from finengine.reading import StatementReader
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
idx = collections.defaultdict(list)
for x in json.load(open(os.path.join(ROOT, 'data/raw/archive-index.json'), encoding='utf8'))['artifacts']:
    for m in x['metadata'].get('manifests', []): idx[m].append(x)
def key(f): return (f['metric'], f['period_kind'], f['period_end'], f.get('scope', ''), json.dumps(f.get('dimensions') or {}, sort_keys=True))
only = sys.argv[1:] 
changed = 0; total = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'data/imports/*.json'))):
    name = os.path.basename(f)
    if only and not any(name.startswith(o) for o in only): continue
    d = json.load(open(f, encoding='utf8'))
    if d.get('reader') != 'finengine.reading/1' or not d.get('facts'): continue
    arts = [a for a in idx.get(name, []) if a['local_path'].endswith('.pdf') and os.path.exists(os.path.join(ROOT, a['local_path']))]
    if not arts: continue
    try:
        r = StatementReader(os.path.join(ROOT, arts[0]['local_path']), enable_ocr=False).read(
            d['market'], d['symbol'], 'SAR', d['source_url'], d['filed_at'], period_end=d['period_end'],
            fiscal_year=int(d['period_end'][:4]), filing_type=d['filing_type'], profile=d.get('profile', 'corporate'))
    except Exception as e:
        print('ERR', name, str(e)[:80]); continue
    total += 1
    a = {key(x): x['value'] for x in d['facts']}; b = {key(x): x['value'] for x in r['facts']}
    add = set(b) - set(a); gone = set(a) - set(b); diff = {k for k in set(a) & set(b) if a[k] != b[k]}
    if add or gone or diff:
        changed += 1
        print('DIFF', name, 'added', len(add), 'removed', len(gone), 'changed', len(diff), [k[:3] for k in list(gone)[:3]])
print('manifests re-read', total, 'with differences', changed)
