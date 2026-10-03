"""Records for every non-priority defect in the six batch records (groups 3-7 and the non-curated rest of 1-5).
Status is 'proven' only where the bundle auditor re-checked the claim itself (text layer / manifest / filesystem); otherwise 'suspected'."""
import os, re, json, glob
from bundle_lib import *
from bundle_curated import chk, allpass, mkver, pf, ev, BY

REC = []


def J(batch, name):
    return json.load(open(os.path.join(REPO, BUNDLE, batch, name), encoding='utf8'))


def fx(manifest, ref=None):
    m = load_manifest(manifest, ref)
    return m['facts'] if m else []


def vnum(x):
    try:
        return abs(float(str(x).replace(',', '')))
    except Exception:
        return None


# ---- check helpers --------------------------------------------------------------------------
def cm(manifest, metric, value, ref=None, page=None):
    """manifest holds a fact with this metric whose abs numeric value equals `value`."""
    t = vnum(value)
    hits = [f for f in fx(manifest, ref) if f['metric'] == metric and vnum(f['value']) == t and (page is None or f.get('page') == page)]
    return chk(f'manifest {manifest} publishes {metric}={value}' + (f' (page {page})' if page else ''), bool(hits),
               '' if hits else f'values for {metric}: {[f["value"] for f in fx(manifest, ref) if f["metric"] == metric][:6]}')


def cmx(manifest, metric):
    """manifest has NO fact for this metric."""
    h = [f for f in fx(manifest) if f['metric'] == metric]
    return chk(f'manifest {manifest} has no {metric} fact', not h, f'{len(h)} found')


def cp(src, page, needles):
    ok = [bool(on_page(src, page, n)) for n in needles]
    return chk(f'pdf p{page} contains {needles}', all(ok) and bool(ok), '' if all(ok) else f'missing: {[n for n, o in zip(needles, ok) if not o]}' if page_text(src, page) is not None else 'page not available (scanned/absent)')


def cf(src, needles):
    """some page contains all needles; returns (check, pages)."""
    doc = open_pdf(src)
    if doc is None:
        return chk(f'find {needles} in source PDF', False, 'source file not available offline'), []
    pages = [p for p in range(1, len(doc) + 1) if all(on_page(src, p, n) for n in needles)]
    return chk(f'a page of the source PDF contains all of {needles}', bool(pages), f'pdf pages {pages[:8]}'), pages


def ca(src, needle):
    doc = open_pdf(src)
    if doc is None:
        return chk(f'{needle} absent from PDF', False, 'source file not available offline')
    pages = [p for p in range(1, len(doc) + 1) if on_page(src, p, needle)]
    return chk(f'{needle} does not occur anywhere in the PDF text layer', not pages, f'found on {pages[:5]}' if pages else f'{len(doc)} pages scanned')


def build(batch, sym, did, cls, sev, cat, group, manifest, src, loc, pub, cor, comp, ptr, bfile, checks=(), level='text layer + manifest', test=None, scope='',
          fix=NR, claimed=NR, force_status=None, notes='', rendered=None, transcription=None, rank=100, reason=None):
    checks = list(checks)
    if force_status:
        status = force_status
    else:
        status = 'proven' if checks and allpass(checks) else 'suspected'
    if not checks:
        ver = dict(level='batch_only', by='batch auditor', result='not re-checked by bundle', checks=[], rendered_pages=[], notes=reason or notes or 'no bundle re-check performed')
    else:
        ver = mkver(level, checks, notes=notes, rendered=rendered, result='confirmed' if allpass(checks) else 'NOT confirmed (downgraded to suspected)')
    if checks and reason:
        ver['notes'] = ((ver.get('notes') or '') + ' ' + reason).strip()
    r = rec(status=status, batch_claimed_status=claimed, priority_group=group, priority_rank=rank, symbol=sym, defect_id=did, defect_class=cls, severity=sev, category=cat,
            manifest=manifest, source_file=src, location=loc, published_value=pub, correct_value=cor, comparison=comp,
            evidence_link=dict(batch_record=bpath(batch, bfile) + (('#' + ptr) if ptr else ''), batch_branch_path=branch_path(batch, bfile), page_evidence=[x for x in (rendered or []) if x], transcription=transcription),
            pinning_test=dict(test=test or 'none', scope_note=scope), verification=ver, batch_fix=fix)
    REC.append(r)
    return r


def _missing(cid):
    import bundle_lib as bl
    out = []
    for a in bl._idx:
        if a['company_id'] == cid and not os.path.exists(os.path.join(REPO, bl.LP(a))) and not bl.refs_holding(bl.LP(a)):
            out.append(a['content_hash'])
    return out


def L(pdf=NR, printed=NR, caption=NR, column=NR, unit=NR, period=NR):
    return dict(pdf_page=pdf, printed_page=printed, caption=caption, column=column, unit_scale=unit, period=period)


def C(restated=NR, cont=NR, source=NR, note=''):
    return dict(restated=restated, continuing_operations=cont, comparison_source=source, note=note)


def S(manifest, ref=None):
    m = load_manifest(manifest, ref)
    return source_info(url=m.get('source_url')) if m else None


def pr(src, p):
    if src is None or not src.get('available_offline') or p in (None, NR):
        return 'not detectable (source file unavailable offline or no printed number in text layer)'
    return printed_page(src, p) or 'no printed page number detected in text layer'


T_A = 'origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::'
T_B = 'origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::'
T_C = 'origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::'
T_D = 'origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::'
T_E = 'origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::'
T_F = 'origin/claude/audit-saudi-batch2-F:tests/test_audit_batch2_f_3060_7202.py::'


# =============================================================================================
# Batch A (banks 1080, 1010, 1140, 1020, 1120)
# =============================================================================================
def batch_a():
    # D4b add-back signs (suspected: repo sign convention disputed by batch E)
    for sym, docs, fn in [('1080', ['anb-2015-annual-report', 'anb-2017-annual-report', 'anb-2019-annual-report', 'anb-2020-q1', 'anb-2021-q1'], '1080.json'),
                          ('1140', ['albilad-2019-fy', 'albilad-2020-fy', 'albilad-2020-q1', 'albilad-2021-q3', 'albilad-2022-q1', 'albilad-2023-q1', 'albilad-2024-q1'], '1140.json'),
                          ('1010', ['riyad-2018-q2', 'riyad-2018-q3'], '1010.json')]:
        pub = []
        for m in docs:
            for f in fx(m):
                if f['metric'] in ('depreciation_amortization', 'provision_expense') and vnum(f['value']) and float(f['value']) > 0:
                    pub.append(dict(manifest=m, **pf(f)))
        build('batch1-A', sym, 'D4 (add-back sign part)', 'cash_flow_add_back_published_positive', 'low', 'sign_convention', 5, ', '.join(d + '.json' for d in docs), None,
              L('cash-flow statement pages (see published_value)', NR, 'Depreciation and amortization / impairment charge add-back rows', 'current-period column', "SAR '000, scale 1000", 'per document'),
              pub, 'batch A: add-backs published positive while income-statement expenses are negative; batch E documents "depreciation_amortization stored negative although the add-back is printed positive" as a repo convention (engine uses abs) - the two batches disagree on whether this is a defect',
              C('not applicable', 'not applicable', 'same document income statement', 'sign only'), 'defects[id=D4]', fn, [],
              test=T_A + 'CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_cash_flow_addbacks_take_the_expense_sign', scope='synthetic PDF; source branch only',
              reason='batch-only; candidate facts enumerated by sign rule; repo sign convention disputed between batch A and batches E/F, so not proven', claimed='proven (batch A, 13+8 facts)', force_status='suspected', rank=60, fix='add-back sign flip in reading.py (batch1-A)')

    # D5 Al Jazira 2008
    for m in ('aljazira-2008-q2', 'aljazira-2008-q3'):
        d, src = source_for_manifest(m)
        bi = [f for f in d['facts'] if f['metric'] == 'bank_investments']
        if m.endswith('q2'):
            f = bi[0]
            checks = [cm(m, 'bank_investments', '13312'), cp(src, 4, ['13,312', 'Gain on non-trading investments, net']), cp(src, 3, ['4,431,820', 'Investments'])]
            rend = [ev(src, '1020', m, 4)]
            build('batch1-A', '1020', 'D5', 'wrong_row_wrong_column_and_missing_statement', 'high', 'numeric_wrong_source_row', 5, m + '.json', src,
                  L(f'{f["page"]} (published), 3 (correct)', f'{pr(src, 4)} / {pr(src, 3)}', 'published as bank_investments; printed label on p4 is "Gain on non-trading investments, net"; correct caption "Investments" (balance sheet p3)',
                    'published: Three Months Ended June 30, 2007 (prior-year comparative) income-statement cell; correct: balance sheet 30 Jun 2008', "SAR '000, scale 1000", '2008-06-30 (instant)'),
                  pf(f), '4,431,820 (balance sheet Investments, pdf p3, note 4); the 13,312 is a 2007 income-statement comparative', C(False, 'not applicable', f'{m} pdf p3 current-period balance sheet', 'rendered p4 shows 13,312 under "Three Months Ended June 30, 2007"'),
                  'defects[id=D5]', '1020.json', checks, 'visual (p4 rendered and read) + text layer + manifest', test=T_A + 'PluralStatementHeadingTests::test_plural_income_statement_is_read',
                  scope='synthetic PDF with plural "STATEMENTS OF INCOME" heading; source branch only; does not assert the manifest', claimed='proven', rank=20, rendered=rend, fix='plural statement anchors (batch1-A reading.py)')
        else:
            t4 = (page_text(src, 4) or '').lower()
            checks = [chk('manifest has no income-statement facts (net_income / total_operating_income / financing_income absent)', not any(f['metric'] in ('net_income', 'total_operating_income', 'financing_income', 'net_financing_income') for f in d['facts'])),
                      chk('pdf p4 is the consolidated statements of income', 'statements of income' in t4 or 'statement of income' in t4, t4[:80].replace(chr(10), ' '))]
            build('batch1-A', '1020', 'D5', 'missing_statement (income statement not extracted; same plural-heading cause)', 'medium', 'completeness', 7, m + '.json', src,
                  L(4, pr(src, 4), 'CONSOLIDATED STATEMENTS OF INCOME (plural heading not an anchor)', 'three/nine months', "SAR '000", '2008-09-30'), [pf(f) for f in bi] or 'no bank_investments fact; no income-statement facts', 'income statement facts present on p4',
                  C(), 'defects[id=D5]', '1020.json', checks, test=T_A + 'PluralStatementHeadingTests::test_plural_headings_are_recognised', scope='synthetic; source branch only', claimed='listed under D5 (statement missing)', rank=72)

    # D7 anb-2025 held-for-sale mapping, alrajhi equity incl sukuk
    m = 'anb-2025-annual-report'
    d, src = source_for_manifest(m)
    f = [x for x in d['facts'] if x['metric'] == 'assets_held_for_sale']
    checks = [cm(m, 'assets_held_for_sale', '11358'), cp(src, 7, ['11,358', '250,085', 'Liabilities associated with assets held for sale'])]
    build('batch1-A', '1080', 'D7', 'wrong_metric_mapping_and_semantics', 'medium', 'mapping', 5, m + '.json', src,
          L(7, pr(src, 7), 'published assets_held_for_sale; printed row is "Liabilities associated with assets held for sale 39 11,358" (assets held for sale 39 250,085 not extracted)', 'FY2025 column', "SAR '000, scale 1000", '2025-12-31'),
          [pf(x) for x in f], 'assets_held_for_sale = 250,085 (the 11,358 is the LIABILITIES line)', C(False, 'held-for-sale classification (IFRS 5); not a continuing-operations comparison', 'same page', ''),
          'defects[id=D7]', '1080.json', checks, claimed='proven', rank=22, fix='none recorded')
    m = 'alrajhi-2025-fy'
    d, src = source_for_manifest(m)
    eq = [f for f in d['facts'] if f['metric'] == 'equity_parent']
    rj = ev(src, '1120', m, 9)
    vis = chk('visual read of rendered pdf p9 (scanned page, no text layer): "Equity attributable to the Bank shareholders 114,854,169", "Equity sukuk 27,907,879", "Equity attributable to the Bank equity holders 142,762,048" (printed page 1)', True,
              'values read from the rendered image by the bundle auditor; FY2024 column 972,444,354 total assets also read')
    build('batch1-A', '1120', 'D7', 'wrong_metric_mapping_and_semantics (equity_parent includes equity sukuk)', 'medium', 'mapping_semantics', 5, m + '.json', src,
          L(9, '1 (typed on the scanned statement image)', 'equity_parent published = "Equity attributable to the Bank equity holders" (includes Equity sukuk); shareholders-only line is "Equity attributable to the Bank shareholders"', 'FY2025 (31 December 2025) column', "SAR '000, scale 1000", '2025-12-31'), [pf(f) for f in eq],
          'shareholders-only equity 114,854,169 (printed row above Equity sukuk 27,907,879); 142,762,048 is shareholders + sukuk', C(False, 'not applicable', 'same page', 'comparability issue vs banks that publish shareholders-only equity'),
          'defects[id=D7]', '1120.json', [cm(m, 'equity_parent', '142762048'), vis], 'visual (scanned page rendered and read) + manifest', claimed='proven', rank=23, rendered=[rj])
    # D8 other_expense sign (3 companies) computed from manifests
    for sym, pref, fn in [('1080', 'anb-', '1080.json'), ('1010', 'riyad-', '1010.json'), ('1020', 'aljazira-', '1020.json')]:
        inst = []
        for p in sorted(glob.glob(os.path.join(REPO, 'data/imports', pref + '*.json'))):
            m = os.path.basename(p)
            for f in fx(m):
                if f['metric'] == 'other_expense' and vnum(f['value']) and float(f['value']) > 0:
                    inst.append(dict(manifest=m, value=f['value'], period_kind=f['period_kind'], period_end=f['period_end'], page=f['page'], caption=f['source_label']))
        ev_src = S('aljazira-2008-q2') if sym == '1020' else None
        checks = [chk(f'manifests with prefix {pref} publish other_expense with a POSITIVE value (repo convention: expenses negative)', bool(inst), f'{len(inst)} facts counted by bundle')]
        if ev_src:
            checks.append(cp(ev_src, 4, ['Other operating expenses', '1,273']))
        build('batch1-A', sym, 'D8', 'sign_convention (other_expense unsigned)', 'medium', 'sign_convention', 5, f'{len(set(i["manifest"] for i in inst))} manifests with prefix {pref}', None,
              L(NR, NR, 'Other operating expenses / Other expenses', 'current-period column', "SAR '000", 'various'), inst, 'same absolute value with negative sign (every other expense metric is stored negative)',
              C('not applicable', 'not applicable', 'repo sign convention (batch E/F: outflows/expenses stored negative)', 'batch A counted 72 facts across ANB/Riyad/Aljazira'), 'defects[id=D8]', fn, checks,
              test=T_A + 'OtherExpenseSignTests::test_other_operating_expenses_are_natural_negative', scope='synthetic PDF; source branch only', claimed='proven', rank=61,
              fix='other_expense added to _BANK_NATURAL_NEGATIVE_METRICS (batch1-A reading.py)')

    # D9 completeness per company: re-run batch's own per-document check
    for sym in ('1080', '1010', '1140', '1020'):
        d = J('batch1-A', sym + '.json')
        entries, ok, bad = [], 0, 0
        for doc in d['documents']:
            un = doc.get('document_completeness_unextracted_lines_present_in_document') or {}
            if not un:
                continue
            m = doc['manifest']
            mm = load_manifest(m)
            src = source_info(url=mm['source_url']) if mm else None
            for metric, (page, label, vals) in un.items():
                absent = bool(mm) and not any(f['metric'] == metric for f in mm['facts'])
                lab_ok = on_page(src, page, label[:30]) if src and src.get('available_offline') else None
                val_ok = on_page(src, page, [v for v in vals if len(v) > 3][0]) if src and src.get('available_offline') and [v for v in vals if len(v) > 3] else None
                good = absent and bool(lab_ok) and bool(val_ok)
                ok += good
                bad += (not good)
                entries.append(dict(manifest=m, metric=metric, pdf_page=page, printed_caption=label, printed_values=vals, manifest_has_metric=not absent, label_on_page=lab_ok, value_on_page=val_ok))
        checks = [chk(f'{sym}: batch-listed unextracted lines re-checked (metric absent from manifest AND printed label and value on cited page)', ok > 0 and ok / max(1, ok + bad) >= 0.9, f'{ok} confirmed / {bad} not confirmed of {ok + bad}')]
        build('batch1-A', sym, 'D9', 'document_completeness_label_gaps', 'medium', 'completeness', 7, f'{len(set(e["manifest"] for e in entries))} manifests (see published_value)', None,
              L('per entry', 'per entry', 'lines present on statement pages but not published (cash-flow subtotals, financing income, fees, impairments...)', NR, NR, 'per document'),
              'not published: ' + f'{len(entries)} (metric, document) pairs', entries, C(), 'defects[id=D9]', sym + '.json', checks, 'text layer + manifest (re-run of the batch method)',
              claimed='proven', rank=70, fix='add labels to BANK_LINE_MAP (planned, not applied)')

    # D10 notes (suspected, batch-only)
    for sym in ('1120', '1020', '1010', '1140'):
        build('batch1-A', sym, 'D10', 'pillar3_and_supplement_notes', 'low', 'completeness_and_notes', 7, 'Pillar 3 and XLSX supplement manifests', None, L(), NR,
              'see batch record: only oldest column published per Pillar 3 doc; rows 8-12/LCR/NSFR for old docs and non-KM1 templates not extracted; supplements: EPS rounded to 2dp; Al Rajhi workbook duplicate FY columns (FY2023 DPS 1.15 col T vs 2.3 col BF) - original column published, restated column unverified',
              C('possibly (Al Rajhi duplicate columns)', NR, 'XLSX workbook columns (not opened by bundle)', ''), 'defects[id=D10]', sym + '.json', [], reason='batch-only; XLSX workbooks and Pillar 3 cells not re-checked by bundle', claimed='low-severity notes', force_status='suspected', rank=80)

    # D11 alrajhi FY2025 comparatives not published
    m = 'alrajhi-2025-fy'
    d, src = source_for_manifest(m)
    vis = chk('visual read of rendered pdf p9: FY2024 comparative column printed (Total assets 972,444,354; Equity sukuk 23,553,815 in FY2024, 27,907,879 in FY2025)', True, 'read from rendered image; the page has no text layer')
    checks = [vis, cmx(m, 'net_fee_income'), chk('manifest publishes only FY2025 balance-sheet instants (no 2024-12-31 instant)', not any(f.get('period_end') == '2024-12-31' for f in d['facts']))]
    build('batch1-A', '1120', 'D11', 'coverage_and_completeness', 'medium', 'completeness', 7, m + '.json', src, L(9, '1', 'Total assets 1,043,268,297 | 972,444,354 (FY2024 comparatives, net fee income, equity sukuk not published)', 'FY2024 comparative column', "SAR '000", 'FY2024'),
          'FY2024 comparatives, net_fee_income (5,869,207), equity sukuk (27,907,879) and shareholders equity (114,854,169) not published', 'printed on the same pages of the same document', C(), 'defects[id=D11]', '1120.json', checks,
          'visual (page 9) + manifest', claimed='proven', rank=71, rendered=[ev(src, '1120', m, 9)])

    # D12 duplicate manifests
    a, b = fx('anb-2025-annual-report'), fx('anb-2025-fy')
    da = {(f['metric'], f['period_kind'], f['period_end']): f['value'] for f in a}
    db = {(f['metric'], f['period_kind'], f['period_end']): f['value'] for f in b}
    common = set(da) & set(db)
    same = all(da[k] == db[k] for k in common)
    build('batch1-A', '1080', 'D12', 'duplicate_manifests', 'low', 'duplicates', 7, 'anb-2025-annual-report.json, anb-2025-fy.json', None, L(), f'{len(a)} and {len(b)} facts', 'single manifest', C(),
          'defects[id=D12]', '1080.json', [chk('overlapping (metric, period) facts of the two manifests carry identical values', bool(common) and same, f'{len(common)} overlapping keys')], claimed='proven (no conflict)', rank=82)


# =============================================================================================
# Batch B (1150 Alinma, 1030, 1180, 8010, 2222)
# =============================================================================================
def batch_b():
    j = J('batch1-B', '1150.json')
    srcs = {s['source_document']['manifest']: s for s in j['sources']}
    # ALN-2 net published as gross
    for m in ('alinma-2018-fy', 'alinma-2018-q3', 'alinma-2019-fy', 'alinma-2020-fy', 'alinma-2020-q1', 'alinma-2020-q2', 'alinma-2020-q3'):
        d, src = source_for_manifest(m)
        fi = [f for f in d['facts'] if f['metric'] == 'financing_income']
        checks = []
        for f in fi:
            pv = fmt(f['value'])
            checks.append(chk(f'{m}: published financing_income {pv} (label "{f["source_label"]}") printed on pdf p{f["page"]}', bool(on_page(src, f['page'], pv)) and 'investments and financing' in (page_text(src, f['page']) or '').lower().replace('\n', ' ')))
            checks.append(chk('source label of the published fact is the NET line', 'net' in f['source_label'].lower() or f['source_label'].rstrip().endswith(','), f['source_label']))
        gross = {'alinma-2019-fy': 'gross 5,608,762; return on time investments (1,214,303); net 4,394,459 (page 9)'}.get(m, 'gross line printed above it on the same page, not published')
        if m == 'alinma-2019-fy':
            checks.append(cp(src, 9, ['5,608,762', '1,214,303', '4,394,459']))
        build('batch1-B', '1150', 'ALN-2', 'metric_mapping_net_published_as_gross', 'medium', 'mapping', 5, m + '.json', src,
              L(sorted({f['page'] for f in fi}), sorted({str(pr(src, f['page'])) for f in fi}), 'Income from investments and financing, net (NET line, published under gross metric financing_income)', 'current period (see period_kind of facts)', "SAR '000, scale 1000", '; '.join(sorted({f'{f["period_kind"]} {f["period_end"]}' for f in fi}))),
              [pf(f) for f in fi], 'metric should be net_financing_income (same value); gross financing_income not published: ' + gross,
              C('vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restatement', 'not applicable', 'XLSX supplement series publishes gross under financing_income', ''),
              f'sources[manifest={m}.json].defects[ALN-2]', '1150.json', checks, test=T_B + 'test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined',
              scope='asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only', claimed='proven', rank=62, fix='BANK_LINE_MAP net/gross mapping (batch1-B reading.py)')
    # ALN-3 wrapped caption
    for m, needles in (('alinma-2018-q2', ['942,390', '1,838,667', '1,185,931']), ('alinma-2019-q2', ['1,079,559', '2,072,658', '1,378,495', '2,685,608'])):
        d, src = source_for_manifest(m)
        fi = [f for f in d['facts'] if f['metric'] == 'financing_income']
        checks = [cp(src, 4, needles)] + [cm(m, 'financing_income', f['value']) for f in fi][:2]
        build('batch1-B', '1150', 'ALN-3', 'wrapped_caption_mapped_to_gross_line', 'medium', 'mapping', 5, m + '.json', src,
              L(4, pr(src, 4), 'Income from investments and financing, net (caption wrapped over two rows)', 'quarter and ytd', "SAR '000, scale 1000", f'quarter/ytd {d["period_end"]}'),
              [pf(f) for f in fi], 'net line published nowhere: ' + ' / '.join(needles[:2]) + ' (net, quarter / ytd)', C(), f'sources[manifest={m}.json].defects[ALN-3]', '1150.json', checks,
              test=T_B + 'test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined', scope='Q2-2019 asserted only; source branch only', claimed='proven', rank=63)
    # ALN-4 Pillar 3 2021-09
    m = 'alinma-pillar-3-tables-final-september-2021-pillar3'
    d, src = source_for_manifest(m)
    checks = [cm(m, 'cet1_capital', '30887221'), cp(src, 1, ['30,887,221'])]
    later = [(k, v) for k, v in [(x['source_document']['manifest'], x) for x in j['sources']] if 'pillar-3' in k and k != m]
    build('batch1-B', '1150', 'ALN-4', 'restated_or_corrected_later_by_issuer_not_adopted (unresolved issuer conflict)', 'high', 'basis_restated_conflict', 4, m + '.json', src,
          L(1, pr(src, 1), 'KM1 row 1 Common Equity Tier 1 (CET1) capital; row 2 Tier 1', 'column a (2021-09-30)', 'SAR (as printed in the template; see manifest scale)', '2021-09-30'),
          [pf(f) for f in d['facts'] if f['metric'] in ('cet1_capital', 'cet1_ratio', 'tier1_capital_ratio')],
          'UNRESOLVED: later Alinma disclosures (Dec-2021 p15 col b, Mar-2022, Jun-2022) print CET1 25,887,221 / 17.35% for the same quarter; neither pair reconciles (batch B). Do not overwrite the original.',
          C(True, 'not applicable', 'later Alinma Pillar 3 disclosures Dec-2021 (p15 col b), Mar-2022, Jun-2022 (not re-opened by bundle)', 'issuer-restated comparative; scope and reason not stated by the issuer'),
          f'sources[manifest={m}.json].defects[ALN-4]', '1150.json', checks, 'text layer of the Sep-2021 document + manifest (later disclosures not re-checked)', claimed='defective_suspect', rank=64,
          force_status='suspected', reason='only the original-vintage half was re-checked; the issuer-conflict claim depends on later documents that the bundle did not open')

    # P3-STALE
    for sym, bf, n in (('1030', '1030.json', 19), ('1180', '1180.json', 10)):
        jj = J('batch1-B', bf)
        docs = [s['source_document']['manifest'] for s in jj['sources'] if 'pillar' in s['source_document']['manifest'].lower() and 'supplement' not in s['source_document']['manifest'].lower()]
        stale = []
        for m in docs:
            mm = load_manifest(m)
            if not mm:
                continue
            exc = [e for e in (mm.get('excluded_facts') or []) if 'catalog_field_missing' in json.dumps(e)]
            stale.append(dict(manifest=m, excluded_catalog_field_missing=len(exc), published=len(mm['facts'])))
        checks = [chk('Pillar 3 manifests carry excluded facts with reason catalog_field_missing (published manifests lack CET1/T1/leverage/LCR/NSFR amounts)', bool(stale) and sum(s['excluded_catalog_field_missing'] for s in stale) > 0, f'{sum(s["excluded_catalog_field_missing"] for s in stale)} excluded facts in {len(stale)} manifests')]
        build('batch1-B', sym, 'P3-STALE', 'stale_catalog_exclusion_pillar3', 'medium', 'completeness_stale_reader', 7, f'{len(stale)} Pillar 3 manifests', None,
              L('KM1 template', NR, 'CET1 amount, Tier 1 amount, leverage exposure/ratio, HQLA, net cash outflow, LCR, available/required stable funding, NSFR', 'per disclosure date', 'as printed', 'per document'),
              stale, 'publishable with the current reader (batch B dry run: SAIB 132 -> 446 facts, SNB 72 -> 247; Alinma unchanged 400)', C(), 'sources[*].defects[P3-STALE]', bf, checks,
              'manifest excluded_facts (published side only; dry-run delta taken from batch B p3-regeneration-dryrun-batch1-B.json, not re-run)', claimed='proven', rank=72,
              fix='regenerate Pillar 3 manifests with the current reader (batch B tools/p3_regen_dryrun.py)')
    # TAW-1
    m = 'tawuniya-2023-fy'
    ref = 'origin/claude/insurance-tawuniya-bupa-enrichment'
    mm = load_manifest(m, ref)
    sj = [s for s in J('batch1-B', '8010.json')['sources'] if s['source_document'].get('manifest', '').startswith(m)][0]
    path = sj['source_document']['archived_path']
    src = source_info(ref=ref, path=path)
    if not src.get('available_offline'):
        src = dict(sha256=path.split('/')[-1].split('.')[0], sha256_basis='filename of archived path recorded by batch B (equals content hash by the repo convention); file bytes not reachable offline', archive_path=path, available_offline=False,
                   where=UN + f'; manifest and PDF live on {ref} per batch B; not present on base or other local refs', url=(mm or {}).get('source_url'))
    fcheck = [chk('manifest (on the candidate branch) publishes cash_change = -106248', bool(mm) and any(f['metric'] == 'cash_change' and f['value'] == '-106248' for f in mm['facts']))] if mm else []
    cps = []
    if src.get('available_offline'):
        cps = [cp(src, 179, ['422,514', '106,248'])]
    build('batch1-B', '8010', 'TAW-1', 'two_panel_layout_wrong_pairing_sign_and_magnitude (candidate manifest, unmerged)', 'high', 'numeric_wrong_source_row', 5, m + '.json (on ' + ref + ', not on base)', src,
          L(179, '179 (printed, per batch B)', 'Net change in cash and cash equivalents during the period', 'right-hand panel 2023 column (published value is from the left panel row "Reinsurance contract assets")', 'SAR (as printed in the report; see manifest scale)', 'FY2023'),
          dict(metric='cash_change', value='-106248'), '422,514 (2022: 471,057); proof 1,591,389 - 1,044,024 - 124,851 = 422,514', C(False, 'not applicable', 'same page right-hand panel', ''),
          'sources[manifest=tawuniya-2023-fy.json].defects[TAW-1]', '8010.json', fcheck + cps, 'manifest on candidate branch' + (' + text layer' if cps else ''), claimed='proven (candidate manifest, unmerged)', rank=24,
          force_status='suspected', reason='source PDF and manifest are not on the base branch; bundle could not render/read p179' if not cps else None, fix='two-panel pairing fix not applied (plan recorded by batch B)')
    # ARA-1 and Aramco unverified
    arch = [a for a in [BYURL.get(m['source_url']) for m in [load_manifest('aramco-2025-annual-metrics')] if m] if a]
    src = source_info(url=load_manifest('aramco-2025-annual-metrics')['source_url'])
    build('batch1-B', '2222', 'ARA-1', 'wrong_page_citation', 'low', 'provenance_page', 6, 'aramco-2025-annual-metrics.json', src,
          L('cited 177-180/243/244; actual pdf 174/176/177/178/235 (batch B)', 'printed 172 for the income statement (batch B)', 'Revenue 1,559,342; Net income 350,210; EPS 1.44 ...', NR, NR, 'FY2025'),
          '160 of 176 facts cite a page on which the value does not occur', 'derive page from the archived PDF', C(), 'sources[manifest=aramco-2025-annual-metrics.json].defects[ARA-1]', '2222.json', [],
          reason='source PDF listed in archive-index but not available offline in any ref; bundle could not re-check', claimed='defective (values correct)', force_status='suspected', rank=50)
    unv = [s['source_document']['manifest'] for s in J('batch1-B', '2222.json')['sources'] if str(s.get('numeric_correctness', '')).startswith('unverified')]
    build('batch1-B', '2222', 'ARA-UNVERIFIED', 'source_documents_not_archived (11+ manifests unverified)', 'medium', 'source_not_archived', 7, f'{len(unv)} manifests (see published_value)', None, L(), unv,
          'cannot be established: archived source PDFs for Aramco FY2019-FY2024, FY2025 full/notes and 2026 interims are absent from every local ref', C(), 'sources[*].numeric_correctness=unverified', '2222.json',
          [chk('archive-index lists sa:2222 PDFs whose files are absent in the worktree and every ref', len(_missing('sa:2222')) > 0, f'{len(_missing("sa:2222"))} of {sum(1 for a in __import__("bundle_lib")._idx if a["company_id"] == "sa:2222")} sa:2222 archive-index files absent')], 'archive-index + filesystem', claimed='unverified', rank=73)


def adapt_a_b():
    batch_a()
    batch_b()
    return REC
