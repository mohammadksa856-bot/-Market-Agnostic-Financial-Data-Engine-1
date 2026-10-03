"""Build docs/audits/saudi-independent/unified-reading-before-after.{md,json} from the work dir (cmp.json, verify.json).
python unified_report.py <workdir> <outdir>"""
import sys, json, os, collections
w, out = sys.argv[1], sys.argv[2]
cmp_ = json.load(open(os.path.join(w, 'cmp.json'), encoding='utf8'))
ver = json.load(open(os.path.join(w, 'verify.json')))
pm = cmp_['per_manifest']

# Hand-verified against the source pages (see md): findings that are NOT plain improvements.
REGRESSIONS = []  # none: no fact that was correct under base is wrong or missing under unified
BORDERLINE = [{
    'manifest': 'alinma-2020-q1.json', 'fact': 'net_income|ytd|2020-03-31', 'old': '370265',
    'note': ("Page 5 (statement of comprehensive income, three-month column only) used to be labelled ytd because the "
             "THREE MONTHS subtitle sat below the fixed y=155 cut. It is now labelled quarter and de-duplicated with the "
             "identical page-4 net_income quarter fact (370265, unchanged). Q1 year-to-date equals the quarter figure; the "
             "value is retained, only the redundant ytd duplicate is gone.")}]
NEW_WRONG = [
    {'manifest': 'aljazira-2008-q2.json', 'source': 'A',
     'facts': {'exchange_income|ytd': ('7273', '9037'), 'trading_income|ytd': ('11841', '1784'),
               'dividend_income|ytd': ('6602', '6330'), 'other_income|ytd': ('3787', '2717'),
               'eps_diluted|ytd': ('1.70', '0.84')},
     'note': ("Page 4, columns Q2-08 | Q2-07 | 6M-08 | 6M-07. Narrow right-aligned numbers in the 3rd column fall outside the "
              "45pt column window so the 4th (prior-year) number is picked. Base emitted none of these facts (the income "
              "statement was not parsed), so this is a latent column-window defect exposed by A, not a regression; the "
              "other facts spot-checked on the page are correct.")},
    {'manifest': 'anb-2019-annual-report.json', 'source': 'A', 'facts': {'eps_diluted|fy': ('202', '2.02')},
     'note': ("Page 9 prints EPS with a decimal comma (2,02); A's distant-note-column rule now lets the row parse and "
              "_parse_number treats the comma as a thousands separator. Base emitted no EPS fact.")}]
PRE_EXISTING = [
    {'manifest': 'aljazira-2013-q3.json', 'fact': 'provision_expense|ytd|2013-09-30', 'base': '-1283152', 'unified': '1283152',
     'note': ("Both values are wrong-source: page 15 is a restatement note table, not the income statement. A's cash-flow "
              "add-back sign rule fires because the page mentions a cash-flow statement; the sign flipped but the fact was "
              "wrong before and after.")},
    {'manifest': 'alrajhi-2024-q2.json', 'fact': 'dividend_income|ytd|2024-06-30', 'base': '-74037', 'unified': '(absent)',
     'note': ("Base value came from the cash-flow statement add-back (p9), not the income statement; removal is correct. "
              "No income-statement dividend_income fact exists in either version (pre-existing gap).")}]

tot = collections.Counter()
for n, e in pm.items():
    u = e['unified']
    for k in ('changed', 'disappeared', 'added'):
        tot[k] += len(u[k])
nver = lambda kind: sum(1 for o in ver.values() for x in o if x['kind'] == kind and x.get('new_printed') is True)
summary = {
    'branch': 'claude/audit-saudi-unified-reading',
    'manifests_in_data_imports': 497,
    'reader_manifests_finengine_reading_1': cmp_['manifests'],
    'manifests_re_read': cmp_['manifests'] - len(cmp_['errors']),
    'not_re_readable': cmp_['errors'],
    'changed_unified': len(pm), 'changed_A_only': cmp_['changed_manifests']['A'], 'changed_B_only': cmp_['changed_manifests']['B'],
    'unchanged': cmp_['unchanged_manifests'], 'overlap_manifests_changed_by_both_A_and_B': 0,
    'unified_equals_A_union_B': True, 'fact_totals_unified': dict(tot),
    'regressions': len(REGRESSIONS), 'borderline': len(BORDERLINE),
    'new_wrong_facts': sum(len(x['facts']) for x in NEW_WRONG),
    'added_facts_value_printed_on_cited_page': nver('added'),
    'changed_facts_value_printed_on_cited_page': nver('changed'),
}
doc = {'summary': summary, 'regressions': REGRESSIONS, 'borderline': BORDERLINE, 'new_wrong_facts': NEW_WRONG,
       'wrong_before_and_after_or_neutral': PRE_EXISTING,
       'per_manifest': {n: {'pdf': e['pdf'], 'changed_by': [v for v in ('A', 'B') if v in e], **e['unified']} for n, e in pm.items()}}
json.dump(doc, open(os.path.join(out, 'unified-reading-before-after.json'), 'w', encoding='utf8'), indent=1, ensure_ascii=False)

L = ['# Unified reading.py: before / after re-read of reader-produced manifests', '',
     ('Variants re-read (read-only, OCR off, identical arguments): (a) base ec610f3, (b) A-only 83a70f7, (c) B-only ae11b2d, '
      '(d) unified (this branch). Tools: tools/unified_reread.py, unified_compare.py, unified_verify.py, unified_columns.py, '
      'unified_page.py, unified_report.py. Nothing under data/ was written.'), '', '## Counts', '']
for k in ('reader_manifests_finengine_reading_1', 'manifests_re_read', 'changed_unified', 'changed_A_only', 'changed_B_only',
          'unchanged', 'regressions', 'borderline', 'new_wrong_facts'):
    L.append(f'- {k}: {summary[k]}')
L += [f'- facts (unified vs base): {tot["changed"]} value changes, {tot["disappeared"]} disappeared, {tot["added"]} added',
      '- Not re-readable (source PDF absent from data/raw): ' + ', '.join(cmp_['errors']),
      ('- Scope: 175 finengine.reading/1 manifests. The other 322 files in data/imports come from other producers (pillar3 '
       'reader, xlsx reader, manual/vision, reviewed tables) that do not call reading.py and are untouched.'),
      (f'- Facts whose value is printed in the caption row of the cited page: added {summary["added_facts_value_printed_on_cited_page"]} '
       f'of {tot["added"]}; changed {summary["changed_facts_value_printed_on_cited_page"]} of {tot["changed"]}. '
       'Period-column choice was checked by position heuristics (unified_columns.py) and hand inspection.'), '',
      '## How the two header approaches were reconciled', '',
      ('They act at different stages and are kept side by side. A (_header_row_hits, called from _column_blocks) chooses which '
       'period tokens define the amount columns by discarding title-line years above the real header row. B (_header_limit, used '
       'in _period_column_groups) chooses how far down the heading band extends when the text above each column is read to decide '
       'three-month vs year-to-date, replacing the fixed y < 155. Neither filters the other\'s input; git merged the two edits with '
       'no textual conflict in reading.py. On all 175 manifests the unified output equals A\'s output where A changed something and '
       'B\'s where B changed something, and no manifest is touched by both (A hits ANB/Riyad/Albilad/AlJazira/BSF/Al Rajhi, B hits '
       'Alinma only), so no interaction was observed. The only add/add conflict was the audit helper tools/build_records.py: B\'s '
       'copy kept, A\'s saved as build_records_batch1A.py.'), '',
      '## Regressions', '',
      ('**None.** No fact that was correct under the base reader is wrong or missing under the unified reader. Checked: all 6 '
       'disappeared facts, every changed fact (value printed in the cited row), 4-column period layouts by position, and page '
       'inspection of Alinma Q2-2018, ANB Q3-2021, Al Jazira Q2-2008, ANB 2017/2023/2025.'), '',
      '### Borderline (counted as 0 regressions, flagged)', '']
for b in BORDERLINE:
    L.append(f'- {b["manifest"]} {b["fact"]}: {b["old"]} -> (gone). {b["note"]}')
L += ['', '### Removed facts that were wrong (improvements)', '']
for n, e in pm.items():
    for g in e['unified']['disappeared']:
        if n != 'alinma-2020-q1.json':
            L.append(f'- {n} {g["fact"]} = {g["old"]} ("{g["label"]}", p{g["page"]}): cash-flow add-back row, not the income statement.')
L += ['', '## New wrong facts (previously absent, now emitted incorrectly; unresolved)', '']
for x in NEW_WRONG:
    L.append(f'- {x["manifest"]} (from {x["source"]}): ' + '; '.join(f'{k} {a} (page prints {b})' for k, (a, b) in x['facts'].items()) + '. ' + x['note'])
L += ['', '## Wrong before and still wrong (not regressions)', '']
for x in PRE_EXISTING:
    L.append(f'- {x["manifest"]} {x["fact"]}: {x["base"]} -> {x["unified"]}. {x["note"]}')
L += ['', '## Change patterns', '',
      ('- A: bank other_expense printed as a positive deduction is now stored negative like every other bank expense (74 facts, '
       'sign only); cash-flow add-back depreciation/provision stored with expense sign (25); cash-flow rows such as dividend income '
       'and sukuk commission no longer populate income-statement metrics; ANB 2015-2023 annual reports and ANB/Riyad/Al Jazira '
       'interims gain income-statement and balance-sheet facts previously mis-paired or taken from notes (e.g. anb-2023-fy '
       'customer_deposits 158,681 note extract -> 165,861,338 balance sheet; ANB 2017 financing_expense fy 71,460 sukuk line -> '
       '1,370,441 total).'),
      ('- B: Alinma three/six/nine-month filings now classify the three-month column as quarter and the cumulative column as ytd '
       '(Q2-2018 financing_income ytd 1,185,931 -> 2,299,017; Q3-2018 net_income ytd 653,266 -> 1,856,403); gross financing_income '
       'no longer takes the net line (FY2018 3,797,832 -> 4,893,617) and gains financing_expense and net_financing_income.'), '',
      '## Every change, per source file', '',
      'Format: field (period kind): old -> new. added = absent under base. Labels and pages are in the .json.', '']
for n, e in pm.items():
    u = e['unified']
    L.append(f'### {n} (changed by {"/".join(v for v in ("A", "B") if v in e)}; pdf {e["pdf"]})')
    for c in u['changed']:
        m, k = c['fact'].split('|')[:2]
        L.append(f'- {m} ({k}): {c["old"]} -> {c["new"]}  [{c["label_old"]} p{c["page_old"]} -> {c["label_new"]} p{c["page_new"]}]')
    for c in u['disappeared']:
        m, k = c['fact'].split('|')[:2]
        L.append(f'- DISAPPEARED {m} ({k}): {c["old"]}  [{c["label"]} p{c["page"]}]')
    for c in u['added']:
        m, k = c['fact'].split('|')[:2]
        L.append(f'- added {m} ({k}): {c["new"]}  [{c["label"]} p{c["page"]}]')
    L.append('')
open(os.path.join(out, 'unified-reading-before-after.md'), 'w', encoding='utf8').write('\n'.join(L))
print(json.dumps(summary, indent=1)[:1500])
