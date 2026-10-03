"""Page-level scan of every statement-bucket file of a company (read-only). usage: scan.py SYM
Writes raw-B002/scan/<sym>.json: sha256 recomputed, pages, image-only page list, statement-title pages, cover text, period phrases."""
import sys, re, json, pathlib, hashlib, pymupdf
sys.stdout.reconfigure(encoding='utf-8')
HERE = pathlib.Path(__file__).resolve().parent.parent
ROOT = HERE.parents[3]
RAW = pathlib.Path(r"C:\Users\Mohammed856\finengine-raw-odd")
T = re.compile(r"statements?\s+of\s+(financial\s+position|financial\s+condition|income|profit|comprehensive|cash\s+flows?|changes\s+in|operations)|balance\s+sheet|income\s+statement|cash\s+flows?\s+statement|statement\s+of\s+insurance\s+operations", re.I)
PER = re.compile(r"(for the (?:\w+[- ])?(?:year|period|quarter|three|six|nine|twelve)[^\n]{0,60}?(?:ended|ending)\s+[^\n]{0,40}\d{4}|as at\s+[^\n]{0,30}\d{4})", re.I)
sym = sys.argv[1]
inv = json.load(open(ROOT / f"docs/audits/saudi-independent/raw-coverage/companies/{sym}.json", encoding='utf-8'))
out = []
for f in sorted(inv['files'], key=lambda f: (f['fiscal_year'] or 0, f['period_slot'] or '', f['sha256'])):
    p = RAW / f['relpath']
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    d = pymupdf.open(p)
    empty, titles = [], []
    for i, pg in enumerate(d):
        t = pg.get_text()
        if len(t.strip()) < 60: empty.append(i + 1); continue
        head = " ".join(t.split())[:300]
        if T.search(head) and not re.search(r"notes? to the|\bindex\b|^\W*note\b", head[:120], re.I):
            titles.append(i + 1)
    cover = " ".join(" ".join(d[k].get_text() for k in range(min(2, len(d)))).split())[:260]
    pers = []
    for k in range(min(len(d), 14)):
        for m in PER.finditer(d[k].get_text()):
            s = " ".join(m.group(0).split())[:90]
            if s not in pers: pers.append(s)
    out.append(dict(sha256=h, sha_ok=h == f['sha256'], relpath=f['relpath'], label=f"{f['fiscal_year']}|{f['period_slot']}", pages=len(d), image_only_pages=empty,
                    title_pages=titles[:20], cover=cover, period_phrases=pers[:4], created=d.metadata.get('creationDate'), source_url=f.get('source_url'), inv_class=f['file_class'], inv_flags=f['flags']))
(HERE / "scan").mkdir(exist_ok=True)
json.dump(out, open(HERE / f"scan/{sym}.json", "w", encoding='utf-8'), ensure_ascii=False, indent=1)
for o in out:
    print(o['sha256'][:8], o['label'], o['pages'], 'ok' if o['sha_ok'] else 'SHA!', 'img', o['image_only_pages'][:12], 'ttl', o['title_pages'][:8], '|', o['period_phrases'][:2], '|', o['cover'][:90])
