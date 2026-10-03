"""Build raw-B002/<symbol>.json from: coverage inventory + page scan + transcripts. Read-only on raw files.
usage: build.py SYM [SYM..]"""
import sys, re, json, importlib, pathlib, hashlib, pymupdf
sys.stdout.reconfigure(encoding='utf-8')
HERE = pathlib.Path(__file__).resolve().parent.parent
ROOT = HERE.parents[3]
RAW = pathlib.Path(r"C:\Users\Mohammed856\finengine-raw-odd")
sys.path.insert(0, str(HERE / 'transcripts'))
MONTH = {m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())}
SLOT = {3: 'Q1', 6: 'H1', 9: '9M', 12: 'FY'}
DATE = re.compile(r"(?:ended|ending|as at|as of)\s+(?:the\s+)?(?:(\d{1,2})\w{0,2}\s*)?(january|february|march|april|may|june|july|august|september|october|november|december)\s*,?\s*(?:(\d{1,2})\w{0,2},?\s*)?(20\d\d)", re.I)
RELEASE = re.compile(r"earnings|results|highlights|presentation|reports (first|second|third|fourth)|releases", re.I)
ANNUAL = re.compile(r"annual report|integrated report|board of directors report", re.I)

def norm(t):
    return re.sub(r"[ˢᵗʰⁿᵈʳ]", "", " ".join(t.split()))

def true_period(d):
    txt = norm(" ".join(d[k].get_text() for k in range(min(3, len(d)))))
    ms = [m for m in DATE.finditer(txt)]
    if ms:
        m = ms[0]; mo = MONTH[m.group(2).lower()]; yr = int(m.group(4))
        return f"{yr}|{SLOT.get(mo, 'M%d' % mo)}", norm(txt)[:0] + m.group(0)
    m = re.search(r"annual report (20\d\d)", txt, re.I)
    if m: return f"{m.group(1)}|FY", m.group(0)
    m = re.search(r"\b(Q[1-4]|H1|9M)[ -]?(?:FY)?\s?(20\d\d)|(first|second|third|fourth) quarter (?:and (?:first half|full year|nine months) )?(20\d\d)", txt, re.I)
    if m: return None, m.group(0)
    return None, None

def kind(d, inv):
    txt = norm(" ".join(d[k].get_text() for k in range(min(2, len(d)))))[:600]
    if len(d) <= 14 and RELEASE.search(txt) and not re.search(r"financial statements|financial information", txt, re.I):
        return 'results_release_or_presentation'
    if ANNUAL.search(txt[:300]) or len(d) > 140 and not re.search(r"interim|condensed", txt[:300], re.I):
        return 'annual_report_or_long_pack' if ANNUAL.search(txt) or len(d) > 140 else 'financial_statements'
    if len(d) <= 12 and not re.search(r"statement|financial", txt, re.I): return 'other_or_unreadable_scan'
    return 'financial_statements'

def build(sym, notes):
    inv = json.load(open(ROOT / f"docs/audits/saudi-independent/raw-coverage/companies/{sym}.json", encoding='utf-8'))
    scan = {o['sha256']: o for o in json.load(open(HERE / f"scan/{sym}.json", encoding='utf-8'))}
    tr = importlib.import_module('t' + sym).T
    trmap = {t['sha']: t for t in tr}
    files = []
    for f in sorted(inv['files'], key=lambda f: (f['fiscal_year'] or 0, f['period_slot'] or '', f['sha256'])):
        s = scan[f['sha256']]
        d = pymupdf.open(RAW / f['relpath'])
        tp, ev = true_period(d)
        label = f"{f['fiscal_year']}|{f['period_slot']}"
        k = kind(d, f)
        t = next((trmap[x] for x in trmap if f['sha256'].startswith(x)), None)
        rec = dict(sha256=f['sha256'], sha256_recomputed_ok=s['sha_ok'], relpath=f['relpath'], size_bytes=f['size_bytes'], pages=s['pages'],
                   source_url=f.get('source_url'), pdf_created=s['created'], collector_label=label,
                   page_derived_period=tp, period_evidence=ev,
                   label_check=('match' if tp == label else ('collector_label_wrong' if tp else 'not_determinable_from_page')),
                   document_kind_from_pages=k, image_only_pages=s['image_only_pages'][:40], statement_title_pages_text=s['title_pages'],
                   inventory=dict(file_class=f['file_class'], completeness=f['completeness_dimension'], flags=f['flags'], statement_pages=f['statement_pages']))
        if t:
            rec['value_correctness'] = dict(status='extractable_and_verified' if all(x for x in [t['read']]) else 'partial', read_method=t['read'], units=t['units'], identity=t['identity'], period_read=t['true_period'],
                                           statements=[dict(name=x['name'], pdf_page=x['pdf_page'], printed_page=x['printed_page'], values=x['values'], arithmetic_checks_passed=len(x['checks'])) for x in t['statements']], observations=t['observations'])
            rec['document_completeness'] = dict(primary_statements_present_in_file=[x['name'] for x in t['statements']], note=notes.get('doc_note', {}).get(f['sha256'][:8], ''))
        else:
            rec['value_correctness'] = dict(status='not_read', note='values not transcribed; file classified only by page scan (titles, image-only pages, cover/period text)')
        ov = notes.get('override', {}).get(f['sha256'][:8])
        if ov:
            rec.update({k2: v for k2, v in ov.items() if k2 in ('document_kind_from_pages', 'page_derived_period', 'period_evidence')})
            rec['override_note'] = 'classification/period set by auditor from rendered pages (see notes)'
            rec['label_check'] = 'match' if rec['page_derived_period'] == label else 'collector_label_wrong'
        files.append(rec)
    return inv, files

def coverage(inv, files):
    slots = ['Q1', 'H1', '9M', 'FY']
    tbl = {}
    for r in files:
        per = r['page_derived_period'] or r['collector_label']
        e = tbl.setdefault(per, dict(statement_files=[], other_files=[]))
        item = dict(sha8=r['sha256'][:8], kind=r['document_kind_from_pages'], collector_label=r['collector_label'], period_from_page=bool(r['page_derived_period']), read=r['value_correctness']['status'])
        (e['statement_files'] if r['document_kind_from_pages'] in ('financial_statements', 'annual_report_or_long_pack') else e['other_files']).append(item)
    yrs = sorted(int(p.split('|')[0]) for p in tbl)
    exp = [f"{y}|{s}" for y in range(yrs[0], 2027) for s in slots if not (y == 2026 and s in ('9M', 'FY'))]
    missing = [p for p in exp if p not in tbl or not tbl[p]['statement_files']]
    return dict(first_collected_period=min(tbl, key=lambda p: (int(p.split('|')[0]), slots.index(p.split('|')[1]))), expected_from_first_collected_to_2026_H1=len(exp),
                periods_with_statement_file=len(exp) - len(missing), periods_without_statement_file=missing, table=tbl)

if __name__ == '__main__':
    for sym in sys.argv[1:]:
        notes = importlib.import_module('n' + sym).N
        inv, files = build(sym, notes)
        out = dict(symbol=sym, company_id=inv['company_id'], name=inv['name'], batch='B002', base_branch='origin/claude/audit-saudi-raw-coverage',
                   raw_root='C:\\Users\\Mohammed856\\finengine-raw-odd (read-only)', method=notes['method'],
                   dimension_1_value_correctness=notes['d1'], dimension_2_document_completeness=notes['d2'], dimension_3_company_coverage=dict(notes['d3'], page_based_period_table=coverage(inv, files)),
                   inventory_flag_confirmations=notes['flags'], defects=notes['defects'], unread_items=notes['unread'], files=files)
        json.dump(out, open(HERE / f"{sym}.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        n = {}
        for r in files: n[r['label_check']] = n.get(r['label_check'], 0) + 1
        print(sym, len(files), n)
        for r in files:
            if r['label_check'] != 'match': print('  ', r['sha256'][:8], r['collector_label'], '->', r['page_derived_period'], r['document_kind_from_pages'], '|', r['period_evidence'])
