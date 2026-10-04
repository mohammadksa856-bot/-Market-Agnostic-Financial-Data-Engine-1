"""mkrecord.py <symbol>: build raw-B014/<symbol>.json from the inventory (sha recomputed), the first-page period phrase read from each file, the transcript and a hand-written spec (tools/rec/<symbol>.py)."""
import sys, os, re, json, importlib.util, pymupdf, pg
MONTHS = {m: i + 1 for i, m in enumerate('january february march april may june july august september october november december'.split())}
AR = {'يناير': 1, 'فبراير': 2, 'مارس': 3, 'أبريل': 4, 'ابريل': 4, 'مايو': 5, 'يونيو': 6, 'يوليو': 7, 'أغسطس': 8, 'اغسطس': 8, 'سبتمبر': 9, 'أكتوبر': 10, 'اكتوبر': 10, 'نوفمبر': 11, 'ديسمبر': 12}
DUR = [(r'three[- ]*months?|3 months|ثلاثة أشهر|الثلاثة أشهر', 'Q'), (r'six[- ]*months?|6 months|ستة أشهر|الستة أشهر', 'H'), (r'nine[- ]*months?|9 months|تسعة أشهر|التسعة أشهر', '9M'), (r'year ended|for the year|السنة المنتهية|للسنة', 'FY')]
def cover_period(doc):
    t = ' '.join(doc[i].get_text() for i in range(min(4, len(doc))))
    t = re.sub(r'\s+', ' ', t)
    low = t.lower()
    m = re.search(r'(?:ended|as at|as of)\s+(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\s+(20\d\d)', low)
    dur = None
    for rx, k in DUR:
        if re.search(rx, low): dur = k; break
    if m: return f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}", dur
    m = re.search(r'(\d{1,2})\s+(' + '|'.join(AR) + r')\s+(20\d\d)', t)
    if m: return f"{m.group(3)}-{AR[m.group(2)]:02d}-{int(m.group(1)):02d}", dur
    return None, dur
def slot_of(pe, dur):
    if not pe: return None
    y, mth = int(pe[:4]), int(pe[5:7])
    return {3: 'Q1', 6: 'H1', 9: '9M', 12: 'FY'}.get(mth, f'month{mth}'), y
def load(sym):
    p = os.path.join(os.path.dirname(__file__), 'rec', f'{sym}.py')
    spec = importlib.util.spec_from_file_location('rec_' + sym, p); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def main(sym):
    R = load(sym)
    inv = json.load(open(os.path.join(pg.INV, sym + '.json'), encoding='utf8'))
    tr = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'transcripts', sym + '.json'), encoding='utf8'))
    tmap = {}
    for d in tr['docs']: tmap.setdefault(d['sha256_prefix'], []).append(d['label'])
    docs = []
    for f in sorted(inv['files'], key=lambda f: (f['fiscal_year'] or 0, f['period_slot'] or '', f['sha256'])):
        path = os.path.join(pg.RAW, f['relpath'].replace('/', os.sep))
        ok = pg.sha(path) == f['sha256']
        doc = pymupdf.open(path)
        pe, dur = cover_period(doc)
        s = slot_of(pe, dur)
        pre = f['sha256'][:8]
        # actual period
        if pe and s:
            sl, y = s
            actual = f"{sl} {y} (period end {pe})" if sl != 'FY' else f"FY {y} (period end {pe})"
        else:
            actual = f"not detected from cover text (inventory text-detected: {f.get('period_end_detected_in_text')})"
        lab = f"{f['fiscal_year']}|{f['period_slot']}"
        label_ok = None
        if s:
            sl, y = s
            label_ok = (str(f['fiscal_year']) == str(y) and f['period_slot'] == sl)
        d = {'actual_period': actual, 'label_ok': label_ok,
             'statements': 'transcribed from pages (see transcripts)' if pre in tmap else 'not transcribed',
             'transcript_docs': tmap.get(pre, []),
             'sha256': f['sha256'], 'sha256_recomputed_ok': ok, 'relpath': f['relpath'], 'size_bytes': f['size_bytes'], 'pdf_pages_total': len(doc),
             'inventory_label': lab, 'inventory_class': f['file_class'], 'inventory_language': f['language'], 'inventory_statement_pages': f.get('statement_pages')}
        d.update(R.NOTES.get(pre, {}))
        docs.append(d)
    rec = {'schema_version': 1, 'symbol': sym, 'name': R.NAME,
           'audit': {'audited_on': '2026-10-04', 'auditor': 'Claude Sonnet 5.5 (independent, raw-B014)', 'scope': R.SCOPE, 'method': R.METHOD,
                     'tools': ['tools/pg.py', 'tools/rows.py', 'tools/peek.py', 'tools/tx.py', 'tools/decl.py', 'tools/survey.py', 'tools/sheet.py', 'tools/check_transcripts.py', 'tools/mkrecord.py', f'tools/specs/{R.SPEC}', f'transcripts/{sym}.json']},
           'dimensions': R.DIMENSIONS, 'documents': docs, 'defects': R.DEFECTS, 'unread_items': R.UNREAD, 'conclusion': R.CONCLUSION}
    out = os.path.join(os.path.dirname(__file__), '..', f'{sym}.json')
    json.dump(rec, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('wrote', os.path.normpath(out), len(docs), 'docs; sha ok', all(d['sha256_recomputed_ok'] for d in docs))
    for d in docs:
        print(d['sha256'][:8], d['inventory_label'], '->', d['actual_period'], 'label_ok', d['label_ok'], d['transcript_docs'])
if __name__ == '__main__':
    main(sys.argv[1])
