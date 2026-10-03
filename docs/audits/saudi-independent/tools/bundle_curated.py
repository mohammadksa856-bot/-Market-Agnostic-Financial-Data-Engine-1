"""Priority records (groups 1-4) hand-specified from the batch records and re-checked by the bundle auditor."""
import os, re, json, sys
import pymupdf
from bundle_lib import *

BY = 'bundle auditor (this session, claude/audit-saudi-defect-bundle)'
NUMRE = re.compile(r'^\(?-?[\d,]+(?:\.\d+)?\)?$')
sys.path.insert(0, os.path.join(REPO, 'src'))


def pf(f):
    return dict(metric=f['metric'], caption=f.get('source_label'), value=f['value'], scale=f.get('scale'), period_kind=f.get('period_kind'),
                period_start=f.get('period_start'), period_end=f.get('period_end'), manifest_page=f.get('page'))


def ev(src, sym, manifest, p, zoom=1.0, clip=None, tag=''):
    name = f'{sym}_{manifest}_pdf{p}{tag}.png'
    out = os.path.join(REPO, EVID, name)
    if not os.path.exists(out):
        if not render_png(src, p, out, zoom, clip):
            return None
    return f'{EVID}/{name}'


def row_numbers(src, p, label_start, value=None):
    """Numbers (as printed) on the visual row containing the published value token (or, failing that, the label)."""
    doc = open_pdf(src)
    words = doc[p - 1].get_text('words')
    rows = []
    for w in sorted(words, key=lambda w: (w[1] + w[3]) / 2):
        yc = (w[1] + w[3]) / 2
        if rows and abs(rows[-1][0] - yc) <= 3.2:
            rows[-1][1].append(w)
        else:
            rows.append([yc, [w]])
    cand = []
    for yc, ws in rows:
        ws = sorted(ws, key=lambda w: w[0])
        nums = [w[4] for w in ws if NUMRE.match(w[4])]
        lab = ' '.join(w[4] for w in ws if not NUMRE.match(w[4]))
        cand.append((lab, nums))
    if value is not None:
        hits = [n for l, n in cand if value in [x.strip('()') for x in n]]
        if hits:
            return hits[0]
    for lab, nums in cand:
        if lab.lower().startswith(label_start.lower()):
            return nums
    return None


def mkver(level, checks, notes='', rendered=None, result='confirmed'):
    return dict(level=level, by=BY, result=result, checks=checks, rendered_pages=[x for x in (rendered or []) if x], notes=notes)


def chk(name, ok, detail=''):
    return dict(check=name, result='pass' if ok else 'FAIL', detail=detail)


def allpass(checks):
    return all(c['result'] == 'pass' for c in checks)


def reader_rerun(src, sym, period_end, year, filing_type):
    from finengine.reading import StatementReader
    p = os.path.join(REPO, src['where'][len('worktree: '):])
    return StatementReader(p, enable_ocr=False).read('SA', sym, 'SAR', 'https://example.invalid/x.pdf', '2026-01-01', period_end=period_end,
                                                     fiscal_year=year, filing_type=filing_type, profile='bank')['facts']


# ---------------------------------------------------------------------------------------------
D1 = {
    'anb-2015-annual-report': dict(year=2015, stmt=4, stmt_pr='24', rows=[
        ('cash_and_balances_with_central_bank', 54, '12,089,917', 'Cash and balances with SAMA', '10,428,291',
         'published value is the "Within 3 months" bucket of the 2014 PRIOR-YEAR commission-rate table (pdf p54, printed 74), not the 2015 table'),
        ('due_from_banks', 53, '3,708,706', 'Due from banks and other financial institutions', '5,575,020', None),
        ('bank_investments', 53, '18,078,127', 'Investments, net', '33,239,175', None),
        ('net_loans', 53, '58,748,903', 'Loans and advances, net', '115,144,322', None),
        ('due_to_banks', 53, '5,487,544', 'Due to banks and other financial institutions', '5,672,883', None)]),
    'anb-2017-annual-report': dict(year=2017, stmt=12, stmt_pr='38', rows=[
        ('cash_and_balances_with_central_bank', 62, '8,002,667', 'Cash and balances with SAMA', '17,251,379', None),
        ('due_from_banks', 62, '1,010,113', 'Due from banks and other financial institutions', '1,710,123', None),
        ('bank_investments', 62, '12,358,717', 'Investments, net', '32,320,816', 'published = "Other investments held at amortised cost" Within-3-months bucket'),
        ('customer_deposits', 62, '39,939,760', "Customers' deposits", '136,048,089', None),
        ('due_to_banks', 62, '2,529,120', 'Due to banks and other financial institutions', '2,691,549', None)]),
    'anb-2018-annual-report': dict(year=2018, stmt=10, stmt_pr='39', rows=[
        ('cash_and_balances_with_central_bank', 90, '14,312,000', 'Cash and balances with SAMA', '22,980,266', None),
        ('due_from_banks', 90, '572,746', 'Due from banks and other financial institutions', '1,134,048', None),
        ('bank_investments', 91, '12,358,717', 'Investments, net', '27,857,183',
         'published value is the Within-3-months bucket of the 2017 PRIOR-YEAR table on pdf p91 (printed 120), not even the 2018 table'),
        ('customer_deposits', 90, '48,176,822', "Customers' deposits", '140,909,422', None),
        ('due_to_banks', 90, '959,623', 'Due to banks and other financial institutions', '1,536,602', None)]),
    'anb-2019-annual-report': dict(year=2019, stmt=8, stmt_pr='39', rows=[
        ('cash_and_balances_with_central_bank', 82, '8,363,000', 'Cash and balances with SAMA', '17,167,044', None),
        ('due_from_banks', 82, '938,303', 'Due from banks and other financial institutions, net', '2,067,992', None),
        ('bank_investments', 83, '12,216,817', 'Investments, net', '38,038,140',
         'published value is the Within-3-months bucket of the 2018 PRIOR-YEAR table on pdf p83 (printed 114)'),
        ('customer_deposits', 82, '40,627,864', "Customers' deposits", '142,128,897', None),
        ('due_to_banks', 82, '2,903,381', 'Due to banks and other financial institutions', '3,082,181', None)]),
}
VISUAL_D1 = {'anb-2015-annual-report': [53, 54, 4], 'anb-2017-annual-report': [62, 12], 'anb-2018-annual-report': [90, 91, 10], 'anb-2019-annual-report': [82, 8]}


def anb_d1():
    out = []
    for m, spec in D1.items():
        d, src = source_for_manifest(m)
        pubs, cors, checks = [], [], []
        for metric, np_, pubval, cap, corval, remark in spec['rows']:
            f = [x for x in d['facts'] if x['metric'] == metric and x['page'] == np_]
            checks.append(chk(f'manifest {m} has {metric}={pubval} (page {np_})', bool(f) and fmt(f[0]['value']) == pubval))
            checks.append(chk(f'published value {pubval} printed on note pdf p{np_}', bool(on_page(src, np_, pubval))))
            checks.append(chk(f'correct value {corval} printed on primary statement pdf p{spec["stmt"]}', bool(on_page(src, spec['stmt'], corval))))
            pubs.append({**(pf(f[0]) if f else {}), 'note_pdf_page': np_, 'note_printed_page': printed_page(src, np_), 'remark': remark})
            cors.append(dict(metric=metric, caption=cap, value=corval.replace(',', ''), scale='1000', period_end=f'{spec["year"]}-12-31',
                             pdf_page=spec['stmt'], printed_page=printed_page(src, spec['stmt']), column=f'{spec["year"]} (current-year column, SAR 000)'))
        checks.append(chk(f'printed page of statement pdf p{spec["stmt"]} is {spec["stmt_pr"]}', printed_page(src, spec['stmt']) == spec['stmt_pr']))
        rend = [ev(src, '1080', m, p) for p in VISUAL_D1[m]]
        out.append(rec(
            status='proven' if allpass(checks) else 'suspected', batch_claimed_status='proven', priority_group=1, priority_rank=10 + spec['year'] - 2015,
            symbol='1080', defect_id='D1', defect_class='wrong_table_and_column (commission-rate note bucket published as balance-sheet total)',
            severity='high', category='numeric_wrong_source_row_and_column', manifest=m + '.json', source_file=src,
            location=dict(pdf_page=sorted({r[1] for r in spec['rows']}), printed_page=sorted({str(printed_page(src, r[1])) for r in spec['rows']}),
                          caption='Balance-sheet captions (cash, due from/to banks, investments, net loans, customer deposits) read from the commission-rate-sensitivity note',
                          column='published: "Within 3 months" bucket of the commission-rate-sensitivity table; correct: current-year column of the primary Statement of Financial Position',
                          unit_scale="SAR '000, scale 1000 (both)", period=f'{spec["year"]}-12-31 (instant)'),
            published_value=pubs, correct_value=cors,
            comparison=dict(restated=False, continuing_operations='not applicable',
                            comparison_source=f'same document ({m}), primary statement pdf p{spec["stmt"]} (printed {spec["stmt_pr"]}), current-year column; no restated figure is used',
                            note='No restatement or continuing/discontinued basis is involved. The FY2019 AR restates 2018 comparatives (e.g. deposits 142,055,608 vs original 140,909,422) but those are NOT used here.'),
            evidence_link=dict(batch_record=bpath('batch1-A', '1080.json') + '#defects[id=D1]', batch_branch_path=branch_path('batch1-A', '1080.json'),
                               page_evidence=[x for x in rend if x], transcription=None),
            pinning_test=dict(test='origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::NoteColumnFarLeftOfValuesTests::test_rows_with_a_distant_note_column_are_read',
                              scope_note='pins the reader root cause (D2) on a synthetic PDF only; no test asserts the republished ANB manifest values; exists only on the source branch, not on the base'),
            verification=mkver('visual (note and statement pages rendered and read) + text layer + manifest', checks, rendered=rend,
                               notes='Bucket column identified from the rendered note table; statement values read from the rendered balance sheet.'),
            batch_fix='Republish after the D2 reader fix (batch record).'))
    return out


def anb_d2():
    m = 'anb-2017-annual-report'
    d, src = source_for_manifest(m)
    p12 = [f['metric'] for f in d['facts'] if f['page'] == 12]
    miss = [x for x in ('cash_and_balances_with_central_bank', 'due_from_banks', 'bank_investments', 'net_loans', 'customer_deposits', 'due_to_banks') if x not in p12]
    checks = [chk('manifest has none of cash/due-from/investments/loans/deposits/due-to from primary statement pdf p12', len(miss) == 6, f'p12 facts: {p12}'),
              chk('the six values are printed on p12', all(on_page(src, 12, v) for v in ('17,251,379', '1,710,123', '32,320,816', '114,542,929', '136,048,089', '2,691,549')))]
    try:
        got = [f['metric'] for f in reader_rerun(src, '1080', '2017-12-31', 2017, 'financial-statements') if f['page'] == 12]
        checks.append(chk('re-ran src/finengine/reading.py (base ec610f3) on the archived PDF: still no cash/loans/deposits fact from p12', not set(got) & {'cash_and_balances_with_central_bank', 'net_loans', 'customer_deposits'}, f'p12 metrics now: {got}'))
    except Exception as e:  # pragma: no cover
        checks.append(chk('reader re-run', False, repr(e)))
    rend = [ev(src, '1080', m, 12)]
    return rec(status='proven' if allpass(checks) else 'suspected', batch_claimed_status='proven', priority_group=1, priority_rank=20,
               symbol='1080', defect_id='D2', defect_class='reader_bug_note_column (root cause of D1)', severity='high', category='reader_root_cause',
               manifest=m + '.json (and every ANB annual report 2015-2019)', source_file=src,
               location=dict(pdf_page=12, printed_page=printed_page(src, 12), caption='Statement rows that carry a note number (cash, due from banks, investments, loans, deposits, due to banks)',
                             column='note column sits ~140 pt left of the amount columns', unit_scale="SAR '000", period='2017-12-31'),
               published_value='primary-statement rows with a note number are dropped: manifest holds only 8 facts from p12 (equity and totals); the six balance-sheet lines are absent',
               correct_value='cash 17,251,379; due from banks 1,710,123; investments 32,320,816; loans 114,542,929; deposits 136,048,089; due to banks 2,691,549 (all printed on p12)',
               comparison=dict(restated=False, continuing_operations='not applicable', comparison_source='same page', note='reader defect, not a basis question'),
               evidence_link=dict(batch_record=bpath('batch1-A', '1080.json') + '#defects[id=D2]', batch_branch_path=branch_path('batch1-A', '1080.json'), page_evidence=[x for x in rend if x]),
               pinning_test=dict(test='origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::NoteColumnFarLeftOfValuesTests::test_rows_with_a_distant_note_column_are_read',
                                 scope_note='synthetic PDF reproducing the layout (also test_label_numbers_are_not_mistaken_for_note_references); source branch only'),
               verification=mkver('visual + text layer + independent reader re-run', checks, rendered=rend),
               batch_fix='widen note-reference detection (src/finengine/reading.py on the batch1-A branch)')


def anb_d3():
    m = 'anb-2021-q3'
    d, src = source_for_manifest(m)
    pubs, cors, checks = [], [], []
    for f in d['facts']:
        if f['period_kind'] != 'ytd' or f['page'] != 4:
            continue
        lab = f['source_label']
        pv = fmt(f['value']) if f['metric'] != 'eps_diluted' else f['value']
        rn = row_numbers(src, 4, lab[:22], pv)
        cor = None
        if rn:
            r2 = [x.strip('()') for x in rn]
            if pv in r2:
                i = r2.index(pv)
                cor = dict(three_month_2021=rn[i], nine_month_2021=rn[i + 2] if i + 2 < len(rn) else None)
        pubs.append({**pf(f), 'printed_row_numbers': rn})
        cors.append(dict(metric=f['metric'], caption=lab, **(cor or {'row': rn})))
        checks.append(chk(f'{f["metric"]}: published ytd {pv} equals the first (three-month 2021) number of the printed row', bool(cor), str(rn)))
    checks.append(chk('at least 15 published p4 IS facts are labelled ytd while equal to the three-month column', len(pubs) >= 15, f'{len(pubs)} facts'))
    try:
        facts = reader_rerun(src, '1080', '2021-09-30', 2021, 'interim-report')
        v = {(x['metric'], x['period_kind']): x['value'] for x in facts}
        checks.append(chk('re-ran base reader: net_income ytd is still 664557 (the three-month figure)', v.get(('net_income', 'ytd')) == '664557', f'net_income ytd={v.get(("net_income", "ytd"))}'))
    except Exception as e:
        checks.append(chk('reader re-run', False, repr(e)))
    rend = [ev(src, '1080', m, 4)]
    return rec(status='proven' if allpass(checks) else 'suspected', batch_claimed_status='proven', priority_group=1, priority_rank=30,
               symbol='1080', defect_id='D3', defect_class='quarter_vs_cumulative_confusion', severity='high', category='period_column',
               manifest=m + '.json', source_file=src,
               location=dict(pdf_page=4, printed_page='2 (typed page number on the scanned statement image; not in the PDF text layer)',
                             caption='INTERIM CONSOLIDATED STATEMENT OF INCOME FOR THE NINE MONTHS ENDED SEPTEMBER 30, 2021 AND 2020 (all rows)',
                             column='published: "For the three months ended September 30, 2021" (first amount column); correct YTD: "For the nine months ended September 30, 2021" (third amount column)',
                             unit_scale="SAR '000, scale 1000", period='9M to 2021-09-30 (ytd) / Q3 2021 (quarter)'),
               published_value=pubs, correct_value=cors,
               comparison=dict(restated=False, continuing_operations='not applicable', comparison_source='same page: nine-month 2021 column (YTD) and three-month 2021 column (quarter)',
                               note='e.g. net income: published ytd 664,557 = Q3; correct ytd 1,715,488; special commission income published ytd 1,383,847 = Q3; correct ytd 3,884,940'),
               evidence_link=dict(batch_record=bpath('batch1-A', '1080.json') + '#defects[id=D3]', batch_branch_path=branch_path('batch1-A', '1080.json'), page_evidence=[x for x in rend if x]),
               pinning_test=dict(test='origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::TitleYearsDoNotShiftPeriodColumnsTests::test_three_month_and_nine_month_columns_are_not_confused',
                                 scope_note='synthetic IS page (asserts quarter 1,479,227 / ytd 4,416,797, net income 664,557 / 1,715,488); not asserted against the manifest; source branch only'),
               verification=mkver('visual (page rendered and read) + text layer + independent reader re-run', checks, rendered=rend,
                                  notes='Rendered page shows the four columns three-months-2021 | three-months-2020 | nine-months-2021 | nine-months-2020.'),
               batch_fix='_header_row_hits keeps only the header row (batch1-A reading.py)')


D4DOCS = {'anb-2015-annual-report': 8, 'anb-2017-annual-report': 16, 'anb-2019-annual-report': 13, 'anb-2020-q1': 7, 'anb-2021-q1': 7, 'alrajhi-2024-q2': 9}
D4CORRECT = {
    'anb-2017-annual-report': dict(src_manifest='anb-2018-annual-report', page=11, needles=['1,370,441', '53,203'],
                                   note='FY2017 special commission expense 1,370,441 printed in the 2017 comparative column of the FY2018 AR income statement (pdf p11, printed 40); dividend income +53,203 positive in the IS'),
    'anb-2019-annual-report': dict(src_manifest='anb-2019-annual-report', page=9, needles=['2,079,685', '84,531'],
                                   note='FY2019 special commission expense 2,079,685 and dividend income +84,531 on the income statement (pdf p9, printed 40)'),
}


def anb_d4():
    out = []
    rank = 40
    for m, cfp in D4DOCS.items():
        d, src = source_for_manifest(m)
        sym = '1120' if m.startswith('alrajhi') else '1080'
        sel = [f for f in d['facts'] if (f['metric'] == 'dividend_income' and float(f['value']) < 0) or (f['metric'] == 'financing_expense' and 'sukuk' in f['source_label'].lower())]
        checks = []
        for f in sel:
            t = (page_text(src, f['page']) or '')
            checks.append(chk(f'{f["metric"]}={f["value"]} ("{f["source_label"]}") printed on cash-flow pdf p{f["page"]}', bool(on_page(src, f['page'], fmt(f['value']))) and f['source_label'].lower()[:15] in t.lower()))
        t = (page_text(src, cfp) or '').lower()
        checks.append(chk('cited page is the cash-flow statement', 'cash flow' in t or 'cash flows' in t, f'pdf p{cfp}'))
        cor = D4CORRECT.get(m)
        if cor:
            _, s2 = source_for_manifest(cor['src_manifest'])
            checks.append(chk('correct IS values printed on ' + cor['src_manifest'] + f' pdf p{cor["page"]}', all(on_page(s2, cor['page'], v) for v in cor['needles'])))
            cinfo = dict(value=cor['note'], source_document=cor['src_manifest'], source_document_sha256=s2['sha256'], pdf_page=cor['page'], printed_page=printed_page(s2, cor['page']))
        else:
            other = {}
            for f in sel:
                other[f['metric']] = [p for p in range(1, len(open_pdf(src)) + 1) if p != f['page'] and on_page(src, p, fmt(f['value']))][:6]
            cinfo = dict(value='dividend income is a positive income-statement line (+absolute value); the negative figure is the cash-flow deduction row. Statement value for this document is not recorded by the batch.',
                         bundle_located_absolute_value_on_other_pdf_pages=other)
        rend = [ev(src, sym, m, cfp)] if m == 'anb-2017-annual-report' else []
        fn = '1080.json' if sym == '1080' else '1120.json'
        out.append(rec(
            status='proven' if allpass(checks) else 'suspected', batch_claimed_status='proven', priority_group=1 if sym == '1080' else 5, priority_rank=rank,
            symbol=sym, defect_id='D4', defect_class='cash_flow_adjustment_row_mapped_to_income_metric', severity='medium', category='mapping_and_sign',
            manifest=m + '.json', source_file=src,
            location=dict(pdf_page=sorted({f['page'] for f in sel}), printed_page=sorted({str(printed_page(src, f['page'])) for f in sel}),
                          caption='; '.join(sorted({f['source_label'] for f in sel})) + ' (cash-flow reconciliation rows)',
                          column='current-period column of the cash-flow statement (reconciling adjustment rows)', unit_scale="SAR '000, scale 1000",
                          period='; '.join(sorted({f'{f["period_kind"]} to {f["period_end"]}' for f in sel}))),
            published_value=[pf(f) for f in sel], correct_value=cinfo,
            comparison=dict(restated=('comparative column of a later filing; restated status not established by batch or bundle' if cor and cor['src_manifest'] != m else False), continuing_operations='not applicable',
                            comparison_source=(f'{cor["src_manifest"]} pdf p{cor["page"]}' if cor else 'same document income statement'),
                            note='published rows are reconciling items of the cash-flow statement (dividend income deducted; sukuk commission added back) stored under income-statement metrics'),
            evidence_link=dict(batch_record=bpath('batch1-A', fn) + '#defects[id=D4]', batch_branch_path=branch_path('batch1-A', fn), page_evidence=[x for x in rend if x]),
            pinning_test=dict(test='origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_income_statement_metrics_are_not_read_from_cash_flow_rows',
                              scope_note='synthetic PDF; source branch only; batch A regression shows the fixed reader no longer emits these facts for anb-2020-q1, anb-2021-q1 and alrajhi-2024-q2'),
            verification=mkver('visual (anb-2017 cash-flow page rendered and read) + text layer + manifest' if rend else 'text layer + manifest (page not rendered)', checks, rendered=rend),
            batch_fix='_CASH_FLOW_REJECTED_METRICS + add-back sign flip (batch1-A reading.py)'))
        rank += 1
    return out


def stc_scale():
    out = []
    specs = [
        ('C-7010-01', 'customer_concentration', 128, 'Information about major customers - revenues from Government entities', 'approximately SAR 11,298 million (2024: SAR 11,145 million)', '11298000', '254-255 (spread; text on right-hand page 255)', ['11,298 million', '11,145']),
        ('C-7010-02', 'employee_benefit_expense', 141, '27.2 Defined contribution plans - expense recognised for the year', 'SAR 631 million (2024: SAR 675 million)', '631000', '280-281 (spread; text on right-hand page 281)', ['631 million', '675 million']),
    ]
    for i, (did, metric, pg, cap, printed, val, prp, needles) in enumerate(specs):
        m = 'stc-2025-segments-financial-notes'
        d, src = source_for_manifest(m)
        f = [x for x in d['facts'] if x['metric'] == metric][0]
        checks = [chk(f'manifest fact {metric}: value {f["value"]} scale {f["scale"]} (normalised raw*scale = SAR {int(float(f["value"]) * float(f["scale"])):,})', f['value'] == val and f['scale'] == '1'),
                  chk(f'cited pdf p{pg} text states the amount in MILLIONS ("{printed}")', all(on_page(src, pg, n) for n in needles)),
                  chk('the page header says amounts are in SAR thousands unless otherwise stated; this sentence is an exception printed in millions', bool(on_page(src, pg, 'Saudi Riyals thousands unless otherwise stated')))]
        if i == 0:
            prof = load_manifest('stc-2025-company-profile')
            hit = bool(prof) and 'approximately SAR 11.298 billion' in json.dumps(prof, ensure_ascii=False)
            checks.append(chk('sibling manifest stc-2025-company-profile (body_text) states the same fact as approximately SAR 11.298 billion', hit))
        rend = [ev(src, '7010', m, pg, 0.9)]
        f1 = float(f['value'])
        out.append(rec(
            status='proven' if allpass(checks) else 'suspected', batch_claimed_status='defective (proven)', priority_group=2, priority_rank=10 + i,
            symbol='7010', defect_id=did, defect_class='scale_error_text_millions_stored_as_raw_scale_1', severity='high', category='scale',
            manifest=m + '.json', source_file=src,
            location=dict(pdf_page=pg, printed_page=prp, caption=cap, column='FY2025 amount in running text',
                          unit_scale='printed in SAR millions (running text); stored as value ' + f['value'] + ' with scale 1 (engine normalises raw*scale)', period='FY2025 (2025-01-01..2025-12-31)'),
            published_value=dict(**pf(f), normalised_sar=int(f1)), correct_value=dict(value=val, scale='1000', normalised_sar=int(f1 * 1000), printed_as=printed),
            comparison=dict(restated=False, continuing_operations='not applicable (group-level note disclosure)', comparison_source='same page', note='value unchanged; only the scale is wrong (1000x too small)'),
            evidence_link=dict(batch_record=bpath('batch1-C', '7010.json') + f'#findings[id={did}]', batch_branch_path=branch_path('batch1-C', '7010.json'), page_evidence=[x for x in rend if x]),
            pinning_test=dict(test='origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::ProvenanceTests::test_million_text_stored_as_thousands_with_scale_one_is_a_scale_suspect',
                              scope_note='synthetic page text for the detector (src/finengine/manifest_audit.py, source branch only); batch C reports the detector reproduces this defect on real data, but no test asserts the corrected manifest value'),
            verification=mkver('visual (page rendered and read) + text layer + manifest', checks, rendered=rend),
            batch_fix='set scale to 1000 on this fact (value unchanged)'))
    return out


def stc_wired_bb():
    m = 'stc-2025-operating-kpis'
    d, src = source_for_manifest(m)
    f = [x for x in d['facts'] if x['metric'] == 'broadband_subscribers' and 'wired' in x['source_label'].lower() and 'wireless' not in x['source_label'].lower()][0]
    t = page_text(src, 38) or ''
    checks = [chk('manifest wired broadband = 1,300,000 at 2025-12-31', f['value'] == '1300000'),
              chk('chart pdf p38 prints 1.3 (Q4 24) and 1.4 (Q4 25) for fixed-wired broadband', '1.3' in t and '1.4' in t)]
    rend = [ev(src, '7010', m, 38, 1.0), ev(src, '7010', m, 38, 3.0, clip=pymupdf.Rect(840, 100, 1180, 310), tag='_zoom')]
    return rec(status='proven' if allpass(checks) else 'suspected', batch_claimed_status='defective (proven)', priority_group=3, priority_rank=40, symbol='7010', defect_id='C-7010-04',
               defect_class='wrong_period_column_prior_year_value_taken', severity='medium', category='period_column', manifest=m + '.json', source_file=src,
               location=dict(pdf_page=38, printed_page='74-75 (spread; chart on right-hand page 75; manifest cites 75)', caption='Subscribers at a glance - Fixed subscribers: fixed-wired broadband subscriptions (millions)',
                             column='published: Q4 24 bar (1.3); correct: Q4 25 bar (1.4)', unit_scale='millions (chart labels), stored as count 1,300,000 scale 1', period='2025-12-31 (Q4 25)'),
               published_value=pf(f), correct_value='1,400,000 (Q4 25 wired broadband 1.4 million); 1.3 million is the Q4 24 comparative',
               comparison=dict(restated=False, continuing_operations='not applicable', comparison_source='same chart, Q4 25 bar', note='zoomed chart read: Q4 24 = 3.9 + 1.3 + 0.5 = 5.7; Q4 25 = 4.1 + 1.4 + 0.5 = 6.0'),
               evidence_link=dict(batch_record=bpath('batch1-C', '7010.json') + '#findings[id=C-7010-04]', batch_branch_path=branch_path('batch1-C', '7010.json'), page_evidence=[x for x in rend if x]),
               pinning_test=dict(test='none', scope_note='no test pins this value (batch C added a generic provenance detector only; it cannot see chart values)'),
               verification=mkver('visual (chart rendered at 3x and read) + manifest', checks, rendered=rend),
               batch_fix='change value to 1400000 and label to 1.4 million')


ALN = {
    'alinma-2018-q2': dict(period='2018-06-30', printed='3', tests='test_nine_month_subtitle_does_not_turn_quarter_into_ytd'),
    'alinma-2018-q3': dict(period='2018-09-30', printed='3', tests='test_nine_month_subtitle_does_not_turn_quarter_into_ytd'),
}


def alinma_ytd():
    out = []
    for i, (m, sp) in enumerate(ALN.items()):
        d, src = source_for_manifest(m)
        pubs, cors, checks = [], [], []
        for f in d['facts']:
            if f['period_kind'] != 'ytd' or f['page'] != 4:
                continue
            pv = fmt(f['value']) if f['metric'] != 'eps_diluted' else f['value']
            rn = row_numbers(src, 4, f['source_label'][:20], pv)
            cor = None
            if rn:
                r2 = [x.strip('()') for x in rn]
                if pv in r2:
                    j = r2.index(pv)
                    cor = dict(three_month=rn[j], cumulative=rn[j + 2] if j + 2 < len(rn) else None)
            pubs.append({**pf(f), 'printed_row_numbers': rn})
            cors.append(dict(metric=f['metric'], caption=f['source_label'], **(cor or {'row': rn})))
            checks.append(chk(f'{f["metric"]} published ytd {pv} equals the first (three-month) printed number', bool(cor), str(rn)))
        rend = [ev(src, '1150', m, 4)]
        pt = 'origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::' + sp['tests']
        out.append(rec(
            status='proven' if allpass(checks) and len(pubs) >= 8 else 'suspected', batch_claimed_status='proven (ALN-1)', priority_group=3, priority_rank=10 + i, symbol='1150', defect_id='ALN-1',
            defect_class='quarter_vs_cumulative_confusion', severity='high', category='period_column', manifest=m + '.json', source_file=src,
            location=dict(pdf_page=4, printed_page=sp['printed'], caption='INTERIM CONSOLIDATED STATEMENT OF INCOME (all rows read as ytd)',
                          column='published: "For the three months period ended" 2018 column; correct ytd: "For the six/nine months period ended" 2018 column', unit_scale="SAR '000, scale 1000 (EPS in SAR)", period=f'ytd to {sp["period"]}'),
            published_value=pubs, correct_value=cors,
            comparison=dict(restated=False, continuing_operations='not applicable', comparison_source='same page, cumulative 2018 column (third number of each printed row)',
                            note='2017 comparative columns on the Q3 page are marked "Restated" but are not used'),
            evidence_link=dict(batch_record=bpath('batch1-B', '1150.json') + f'#sources[manifest={m}.json].defects[ALN-1]', batch_branch_path=branch_path('batch1-B', '1150.json'), page_evidence=[x for x in rend if x]),
            pinning_test=dict(test=pt if m == 'alinma-2018-q3' else 'none for alinma-2018-q2 itself; only the Q3-2018 document is asserted by ' + pt,
                              scope_note='asserts reader output on the archived Q3-2018 PDF (total operating income 1,211,698 / 3,552,462; net income 653,266 / 1,856,403); source branch only; does not assert the manifest'),
            verification=mkver('visual (page rendered and read) + text layer + manifest', checks, rendered=rend),
            batch_fix='_header_limit in reading.py instead of hard-coded y<155 (batch1-B)'))
    return out


ZAKAT = [
    dict(sym='1010', pub='riyad-2018-fy', cmp='riyad-2019-fy', pub_page=9, cmp_page=8, pub_val='4,716,085', cmp_val='3,092,277', eps=('1.57', '1.03'),
         cmp_cols='"2018 (Restated)" column of the FY2019 statement of income', batch_page_wrong='batch A cited pdf p2 of riyad-2019-fy; p2 is the auditor report - the restated income statement is pdf p8 (printed "Page 2 of 82")',
         detail='Net income for the year before zakat 4,716,085 (identical to the originally published net income); zakat for the year 430,249 + zakat for previous years 1,193,559 = total zakat 1,623,808; net income for the year (after zakat) 3,092,277; EPS 1.03',
         rank=10),
    dict(sym='1080', pub='anb-2018-annual-report', cmp='anb-2019-annual-report', pub_page=11, cmp_page=9, pub_val='3,311,817', cmp_val='3,970,659', eps=('3.31', '2.65'),
         cmp_cols='"2018 (Restated)" column of the FY2019 statement of income', batch_page_wrong=None,
         detail='Net income before zakat and income tax 3,311,817 (equals the originally published net income); zakat 182,051; zakat reversal for the prior year (1,113,261); income tax 272,368; net income for the year (restated) 3,970,659; EPS 2.65',
         rank=11),
    dict(sym='1140', pub='albilad-2018-fy', cmp='albilad-2019-fy', pub_page=43, cmp_page=8, pub_val='1,110,510', cmp_val='612,693', eps=('1.85', '0.82'),
         cmp_cols='"2018 Restated" column of the FY2019 statement of income', batch_page_wrong=None,
         detail='Net income before zakat 1,110,510 (equals the originally published net income); zakat for the year 497,817; net income after zakat 612,693; EPS 0.82',
         rank=12),
]


def zakat():
    out = []
    for z in ZAKAT:
        pd, psrc = source_for_manifest(z['pub'])
        cd, csrc = source_for_manifest(z['cmp'])
        pubf = [f for f in pd['facts'] if f['metric'] == 'net_income'][0]
        epsf = [f for f in pd['facts'] if f['metric'] in ('eps_diluted', 'eps_basic')]
        checks = [chk(f'manifest {z["pub"]} net_income = {z["pub_val"]} (as originally printed)', fmt(pubf['value']) == z['pub_val'], f'page {pubf["page"]}'),
                  chk(f'original value printed on {z["pub"]} pdf p{z["pub_page"]}', bool(on_page(psrc, z['pub_page'], z['pub_val']))),
                  chk(f'restated after-zakat value {z["cmp_val"]} printed on {z["cmp"]} pdf p{z["cmp_page"]}', bool(on_page(csrc, z['cmp_page'], z['cmp_val']))),
                  chk('comparison column is labelled Restated on that page', 'restated' in (page_text(csrc, z['cmp_page']) or '').lower())]
        rend = [ev(psrc, z['sym'], z['pub'], z['pub_page']), ev(csrc, z['sym'], z['cmp'], z['cmp_page'])]
        fn = z['sym'] + '.json'
        out.append(rec(
            status='proven' if allpass(checks) else 'suspected', batch_claimed_status='proven', priority_group=4, priority_rank=z['rank'], symbol=z['sym'], defect_id='D6',
            defect_class='restated_comparative_and_zakat_basis_discontinuity', severity='high', category='basis_zakat', manifest=z['pub'] + '.json', source_file=psrc,
            location=dict(pdf_page=z['pub_page'], printed_page=printed_page(psrc, z['pub_page']) or 'none detected in text layer', caption='Net income for the year (published as metric net_income; FY2018 PRE-zakat basis)',
                          column='FY2018 current-year column of the FY2018 statements (original basis: zakat charged to equity, not to income)', unit_scale="SAR '000, scale 1000", period='FY2018 (2018-01-01..2018-12-31)'),
            published_value=dict(**pf(pubf), eps=[e['value'] for e in epsf]),
            correct_value=dict(note=('DO NOT replace the published number. The FY2018 net income is correct as printed in the original FY2018 statements (pre-zakat basis); '
                                     'what is defective is the unflagged basis: later periods are after-zakat, so the series is not like-for-like.'),
                               restated_after_zakat_net_income=z['cmp_val'].replace(',', ''), restated_eps=z['eps'][1], detail=z['detail']),
            comparison=dict(restated=True, continuing_operations='not applicable (no discontinued operations involved; the restatement is the change in zakat/tax presentation)',
                            comparison_source=dict(document=z['cmp'], source_file_sha256=csrc['sha256'], source_file_sha256_basis=csrc['sha256_basis'], pdf_page=z['cmp_page'],
                                                   printed_page=printed_page(csrc, z['cmp_page']) or 'none detected', column=z['cmp_cols'],
                                                   scope='consolidated full-year FY2018 comparative restated for zakat/income tax, SAR 000, as printed on that page'),
                            note=z['batch_page_wrong'] or 'the restated figure is a comparative inside a later filing = different vintage/basis; to be ingested as a separate restated vintage, never overwriting the original'),
            evidence_link=dict(batch_record=bpath('batch1-A', fn) + '#defects[id=D6]', batch_branch_path=branch_path('batch1-A', fn), page_evidence=[x for x in rend if x]),
            pinning_test=dict(test='none', scope_note='batch A proposes ingesting comparatives as restated vintages (manifest_vintages) and tagging net_income basis, but wrote no test for D6'),
            verification=mkver('visual (both pages rendered and read) + text layer + manifest', checks, rendered=rend, notes=z['batch_page_wrong'] or ''),
            batch_fix='Ingest comparative columns as restated vintages (manifest_vintages) and tag net_income basis; no hand edits (batch record)'))
    return out


def curated():
    out = []
    out += anb_d1() + [anb_d2(), anb_d3()] + anb_d4()
    out += stc_scale()
    out += alinma_ytd() + [stc_wired_bb()]
    out += zakat()
    return out
