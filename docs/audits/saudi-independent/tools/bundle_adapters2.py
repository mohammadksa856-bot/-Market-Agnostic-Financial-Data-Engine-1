"""Records for batches C (telecom), D (SABIC/ACWA/cement), E (cement), F (3060, 7202)."""
import os, re, json, glob
from bundle_lib import *
from bundle_curated import chk, allpass, mkver, pf, ev, BY
from bundle_adapters import (REC, J, fx, vnum, cm, cmx, cp, cf, ca, build, L, C, S, pr, T_C, T_D, T_E, T_F, _missing)


def search_company(cid, needles):
    out = []
    for a in _idx_for(cid):
        src = source_info(artifact=a)
        if not src['available_offline']:
            continue
        doc = open_pdf(src)
        pages = [p for p in range(1, len(doc) + 1) if all(on_page(src, p, n) for n in needles)]
        if pages:
            out.append((src, pages))
    return out


def _idx_for(cid):
    import bundle_lib as bl
    return [a for a in bl._idx if a['company_id'] == cid]


def stamp_check(m):
    d = load_manifest(m)
    st = url_stamp(d['source_url'])
    return chk(f'{m}: filed_at {d["filed_at"]} is earlier than the Saudi Exchange upload date {st} embedded in source_url', bool(st) and d['filed_at'] < st, f'filed_at={d["filed_at"]}, url stamp={st}'), d, st


# =============================================================================================
def batch_c():
    # ---- stc ----
    m = 'stc-2025-segments-financial-notes'
    d, src = source_for_manifest(m)
    f = [x for x in d['facts'] if x['metric'] == 'ppe_additions_by_class'][0]
    rend = [ev(src, '7010', m, 129, 1.1)]
    build('batch1-C', '7010', 'C-7010-03', 'wrong_line_item_mapped', 'high', 'numeric_wrong_source_row', 5, m + '.json', src,
          L(129, '256-257 (spread; Note 10 roll-forward)', "Note 10 Property and equipment - 'Additions' row, Total column (2025 roll-forward)", 'published: Net book value of "Lands and buildings" at 31 Dec 2025 (last row, first column); correct: Additions row, Total column', "SAR '000, scale 1000", 'FY2025'),
          pf(f), '8,235,137 (additions total = lands & buildings 90,710 + network 94,452 + other 138,210 + CWIP 7,911,765)', C(False, 'FY2025 current-year roll-forward (the 2024 roll-forward carries a note that its movements include discontinued operations)', 'same page', ''),
          'findings[id=C-7010-03]', '7010.json', [cm(m, 'ppe_additions_by_class', '8279660'), cp(src, 129, ['8,279,660', '8,235,137', '7,911,765']), cp(src, 129, ['Net book value'])],
          'visual (page rendered and read) + text layer + manifest', rendered=rend, claimed='defective (proven)', rank=30, fix='replace with 8235137 or drop the fact')

    # C-7010-05 page references (stc)
    chk_list = []
    named = {'revenue_by_product': 143, 'remaining_performance_obligations': 143, 'deferred_tax_expense': 143, 'borrowings': 139, 'finance_cost_by_type': 144, 'expected_credit_losses': 144, 'purchase_commitments': 148, 'other_commitments': 148, 'guarantees': 148, 'contingencies': 148}
    wrong = []
    for met, cited in named.items():
        for f in fx(m):
            if f['metric'] == met and f.get('page') == cited and vnum(f['value']) and vnum(f['value']) > 999:
                v = fmt(f['value'])
                if not on_page(src, cited, v):
                    where = [p for p in range(cited - 2, cited + 3) if on_page(src, p, v)]
                    wrong.append(dict(metric=met, value=f['value'], cited_page=cited, actually_on_pdf_pages=where))
                break
    d2, s2 = source_for_manifest('stc-2025-fy')
    prov = [f for f in d2['facts'] if f['metric'] == 'provisions']
    chk_list.append(chk('facts cite a page on which the value is not printed (batch examples re-scanned by bundle)', len(wrong) >= 3, f'{len(wrong)} confirmed: {wrong[:5]}'))
    build('batch1-C', '7010', 'C-7010-05', 'page_reference_wrong_or_other_document', 'low', 'provenance_page', 6, 'stc-2025-segments-financial-notes.json; stc-2025-fy.json; stc-2024-operating-kpis.json; stc-2025-operating-kpis.json; stc-2021-2023-network-kpis.json', src,
          L('cited pages differ from printed pages (see published_value)', NR, '(many)', NR, NR, 'FY2025 / FY2024'), wrong, 'cited page = the pdf page that carries the value; use PDF page numbers and keep printed pages in metadata',
          C(), 'findings[id=C-7010-05]', '7010.json', chk_list, 'text layer + manifest', test=T_C + 'ProvenanceTests::test_adjacent_page_is_a_page_offset_and_distant_page_is_wrong_page',
          scope='synthetic page text; the scanner is on the source branch only', claimed='defective (proven)', rank=40, fix='normalise to PDF page numbers; re-run scripts/audit_manifest_provenance.py')

    # C-7010-06 mixed vintage quarters vs FY2023
    qd, _ = source_for_manifest('stc-2023-quarterly-history')
    ad, _ = source_for_manifest('stc-2020-2023-annual-history')
    q = [f for f in qd['facts'] if f['metric'] == 'revenue' and f['period_end'].startswith('2023') and f['period_kind'] in ('quarter', 'fiscal_quarter')]
    fy = [f for f in ad['facts'] if f['metric'] == 'revenue' and f['period_end'].startswith('2023-12') and f['period_kind'] == 'fy']
    qs = sum(float(f['value']) * float(f.get('scale', 1)) for f in q)
    fv = float(fy[0]['value']) * float(fy[0].get('scale', 1)) if fy else None
    gap = (qs - fv) / fv * 100 if fv else None
    hits = search_company('sa:7010', ['2023', 'reclassified'])
    foot = [(s['sha256'][:12], p) for s, p in hits]
    checks = [chk('sum of the four 2023 quarterly revenues exceeds FY2023 revenue (manifest arithmetic)', bool(fv) and len(q) == 4 and gap > 0.4, f'{len(q)} quarters sum {qs:,.0f} vs FY {fv:,.0f} -> {gap:.2f}%' if fv else 'FY2023 fact not found'),
              chk('archived stc document prints a "comparative figures ... reclassified" footnote for 2023', bool(foot), f'{foot[:3]}')]
    build('batch1-C', '7010', 'C-7010-06', 'mixed_basis_original_vs_restated_vintage', 'medium', 'basis_restated', 4, 'stc-2023-quarterly-history.json vs stc-2020-2023-annual-history.json', None,
          L('AR2024 p73 footnote (per batch C)', '73', 'Revenue: four 2023 quarters (Q1-2024 deck comparatives) vs FY2023 "Revised" (AR2024 five-year summary)', 'quarterly deck columns vs FY2023 Consolidated Revised', "SAR bn / SAR '000", 'FY2023'),
          dict(quarters_sum_sar=qs, fy2023_sar=fv, gap_percent=gap), 'quarters on original basis (pre-restatement, includes later-discontinued operations) vs FY2023 restated continuing operations; sum 72.34 bn vs 71.777 bn (+0.78%)',
          C(True, 'FY2023 figure is restated continuing operations; the quarterly set is pre-restatement', 'stc AR2024 five-year summary (restated, "reclassified" footnote) vs Q1-2024 presentation (not archived)', 'never publish FY and quarters of different vintages without a basis flag'),
          'findings[id=C-7010-06]', '7010.json', checks, 'manifest arithmetic + text layer of archived stc documents', test=T_C + 'QuarterSumTests::test_mixed_original_and_restated_basis_is_reported',
          scope='synthetic quarter data; source branch only', claimed='defective (arithmetic + footnote)', rank=20,
          force_status=('proven' if allpass(checks) else 'suspected'), reason='the Q1-2024 deck that supplies the quarters is not archived, so quarterly values themselves are unverified' if True else None)
    # unverified items
    build('batch1-C', '7010', 'C-7010-07', 'quarter_sum_does_not_match_year', 'low', 'period_column_vintage', 3, 'stc-2024-quarterly-revenue.json vs stc-2025-fy.json', None,
          L(), '18.908+19.021+18.643+19.266 = 75.838 bn', 'FY2024 75,893,413 thousand (restated comparative, AR2025 p9); gap -55.4m (-0.07%)', C('possibly', NR, 'AR2025 p9 restated FY2024', ''), 'findings[id=C-7010-07]', '7010.json', [],
          test=T_C + 'QuarterSumTests::test_rounding_noise_is_not_reported', scope='tolerance 0.4% would hide this gap', reason='batch status unverified; Q1-2025 presentation not archived; cannot say which figure is right', claimed='unverified', force_status='suspected', rank=21)
    d3, s3 = source_for_manifest('stc-2026-q2')
    build('batch1-C', '7010', 'C-7010-08', 'source_not_archived', 'medium', 'source_not_archived', 7, 'stc-2026-q2.json', s3, L(NR, NR, '15 H1-2026 facts', 'ytd six months', '1e6', 'H1 2026 (ytd to 2026-06-30)'), '15 facts, not verifiable', 'n/a',
          C(), 'findings[id=C-7010-08]', '7010.json', [chk('archive-index lists the file but it is absent in the worktree and every ref', not s3['available_offline'], s3['where'])], 'filesystem + archive-index', claimed='unverified', rank=74)

    # ---- Mobily ----
    m = 'mobily-2022-fy'
    d, src = source_for_manifest(m)
    d23, src23 = source_for_manifest('mobily-2023-fy')
    f = [x for x in d['facts'] if x['metric'] == 'ebitda'][0]
    checks = [chk('manifest ebitda FY2022 = 6179', f['value'] == '6179', f['value']), cp(src, 4, ['6,161', '15,669']), cp(src, 22, ['6,161']), ca(src, '6,179'), cp(src23, 3, ['6,179', '15,717']), cp(src23, 22, ['6,179'])]
    build('batch1-C', '7020', 'C-7020-01', 'mixed_vintage_original_and_restated_in_one_manifest', 'medium', 'basis_restated', 4, m + '.json', src,
          L('4 and 22 (cited 12)', pr(src, 4) + ' / ' + str(pr(src, 22)), 'Financial Highlights / Financial performance table: EBITDA 2022', 'FY2022 as originally reported (AR2022)', 'SAR million, scale 1000000', 'FY2022'),
          pf(f), '6,161 (SAR m, margin 39.3%) in the AR2022; 6,179 is the RESTATED FY2022 comparative printed in AR2023 (pdf p3 and p22; AR2023 revenue 15,717)',
          C(True, 'not applicable', dict(document='mobily-2023-fy (annual report 2023)', source_file_sha256=src23['sha256'], source_file_sha256_basis=src23['sha256_basis'], pdf_pages='3 and 22', column='2022 comparative (restated)', scope='consolidated FY2022, SAR million'), 'the manifest mixes original revenue 15,669 / net income with restated EBITDA 6,179'),
          'findings[id=C-7020-01]', '7020.json', checks, 'text layer of both annual reports + manifest', claimed='defective (proven)', rank=22, fix='EBITDA 6,161 (original) or flag the vintage; no hand edit')
    # C-7020-02 page refs
    wr = []
    for mm in ('mobily-2022-fy', 'mobily-2023-fy', 'mobily-2023-q1', 'mobily-2025-fy', 'mobily-2025-deep-financial-notes', 'mobily-2025-issuer-expansion'):
        dd, ss = source_for_manifest(mm)
        if not dd or not ss['available_offline']:
            wr.append(dict(manifest=mm, note='source not available offline')); continue
        n = len(open_pdf(ss))
        beyond = [f for f in dd['facts'] if f.get('page') and int(f['page']) > n]
        wr.append(dict(manifest=mm, pdf_pages=n, facts_citing_page_beyond_pdf=len(beyond), total_facts=len(dd['facts'])))
    f12 = [x for x in d['facts'] if x.get('page') == 12 and x['metric'] == 'ebitda']
    checks = [chk('Mobily manifests cite pages beyond the length of their own source PDF (batch: 80 facts)', sum(x.get('facts_citing_page_beyond_pdf', 0) for x in wr) >= 50, str(wr)),
              chk('FY2022 EBITDA cites p12 but 6,161 is not on p12', bool(f12) and not on_page(src, 12, '6,161'), 'pdf p4 and p22 carry it')]
    build('batch1-C', '7020', 'C-7020-02', 'page_reference_wrong', 'low', 'provenance_page', 6, 'mobily-2022-fy / 2023-fy / 2023-q1 / 2025-fy / 2025-deep-financial-notes / 2025-issuer-expansion', src, L('see published_value', NR, '(many)', NR, NR, 'various'), wr,
          'PDF page numbers; printed numbers kept in metadata (deep notes use printed spread numbers: pdf = (printed+2)/2)', C(), 'findings[id=C-7020-02]', '7020.json', checks, 'page counts + text layer',
          test=T_C + 'ProvenanceTests::test_summary_and_dominant_offset', scope='synthetic; source branch only', claimed='defective (proven)', rank=41)

    # ---- Zain KSA ----
    m = 'zain-ksa-2025-notes-segments'
    d, src = source_for_manifest(m)
    sa = [f for f in d['facts'] if f['metric'] in ('segment_assets', 'segment_liabilities', 'segment_depreciation_amortization')]
    checks = [cm(m, 'segment_assets', '57603795'), cp(src, 70, ['57,603,795', '28,753,303', '29,920,980']), cp(src, 69, ['2,153,794', '2,160,661'])]
    build('batch1-C', '7030', 'C-7030-01', 'scope_label_wrong_entity_segment_tagged_consolidated', 'medium', 'scope_semantics', 5, m + '.json', src,
          L('69-70 (cited 68-69)', f'{pr(src, 69)}-{pr(src, 70)}', "Note 40 Segment reporting: 'Mobile Telecommunications Company' column before eliminations", 'legal-entity column (before eliminations) vs Total column', "SAR '000", 'FY2025 / 2025-12-31'),
          [pf(f) | {'scope': (f.get('dimensions') or {}).get('scope')} for f in sa], 'consolidated: total assets 28,753,303; total liabilities 17,877,352; D&A 2,160,661 (note 40 total column)', C(False, 'not applicable', 'same pages, Total column', ''), 'findings[id=C-7030-01]', '7030.json', checks, claimed='defective (proven)', rank=31)
    ph = [f for f in d['facts'] if f['metric'] == 'revenue_by_geography']
    checks = [chk('manifest revenue_by_geography value 9338850 exists', any(f['value'] == '9338850' for f in ph)), ca(src, '9,338,850'), cp(src, 52, ['14.97%'])]
    build('batch1-C', '7030', 'C-7030-02', 'derived_value_presented_as_printed', 'medium', 'derived_value', 5, m + '.json', src,
          L(52, pr(src, 52), '26-2: "revenue recognized from operations within KSA except international roaming and interconnect which account 14.97% (2024: 15.54%)"', 'FY2025', "SAR '000, scale 1000", 'FY2025'),
          [pf(f) for f in ph if f['value'] == '9338850'], 'only the percentage 14.97% is printed; no SAR amount (implied ~9,339,070 +/- rounding)', C(), 'findings[id=C-7030-02]', '7030.json', checks, claimed='defective (proven)', rank=32)
    cc = [f for f in d['facts'] if f['metric'] == 'customer_concentration']
    checks = [chk('manifest customer_concentration stored as 0', any(f['value'] == '0' for f in cc)), cp(src, 52, ['No single customers'])]
    build('batch1-C', '7030', 'C-7030-03', 'text_statement_encoded_as_numeric_zero', 'low', 'derived_value', 5, m + '.json', src,
          L(52, pr(src, 52), "'No single customers contributed 10% or more to the Group's revenues.'", 'FY2025', 'unit pure', 'FY2025'), [pf(f) for f in cc], 'qualitative bound ("below 10%"), not a value of zero', C(), 'findings[id=C-7030-03]', '7030.json', checks, claimed='defective (proven)', rank=33)
    m = 'zain-ksa-2025-company-profile'
    d, src = source_for_manifest(m)
    ca4 = [a for a in d.get('corporate_actions', []) if a.get('action_type') == 'cash_dividend']
    checks = [chk('Zain dividend corporate actions carry cash_amount equal to dividend_per_share (0.5)', len(ca4) >= 4 and all(a['cash_amount'] == (a.get('details') or {}).get('dividend_per_share') for a in ca4), f'{len(ca4)} actions: {[(a["action_key"], a["cash_amount"]) for a in ca4]}')]
    build('batch1-C', '7030', 'C-7030-04', 'field_semantics_mismatch_per_share_in_total_amount_field', 'medium', 'unit_scale', 2, m + '.json', src,
          L('AR2025 pp 23/24/34 (per manifest metadata)', NR, 'Dividend of SAR 0.50 per share (4 corporate actions FY2022-FY2025)', 'corporate_actions.cash_amount', 'SAR per share stored in a total-amount field', 'FY2022-FY2025'),
          [dict(action_key=a['action_key'], cash_amount=a['cash_amount'], currency=a['currency']) for a in ca4], 'about SAR 449,364,588 per dividend (0.50 x 898,729,175 shares); other manifests store the total in cash_amount',
          C('not applicable', 'not applicable', 'cash-flow "Dividend paid" 451,855 thousand (2025) and 448,115 (2024) per batch C', ''), 'findings[id=C-7030-04]', '7030.json', checks,
          'manifest (field semantics); the cross-issuer comparison (22 other actions store totals) from batch C was not recounted', claimed='defective (proven)', rank=20,
          reason='page text not re-read: AR2025 pdf pages 23/24/34 not checked for the per-share statement')
    m = 'zain-ksa-2021-2023-financial-history'
    d, src = source_for_manifest(m)
    mf = [f for f in d['facts'] if f['metric'] in ('revenue', 'ebitda', 'net_income')]
    ok_cur = all((f.get('currency') or f.get('unit')) == 'USD' or f.get('currency') == 'USD' for f in mf)
    checks = [chk('facts are USD amounts under plain metric names', bool(mf) and ok_cur, f'{len(mf)} facts; currencies {sorted({f.get("currency") for f in mf})}'), cp(src, 17, ['2,634', '2,421', '794', '842', '338', '147'])]
    build('batch1-C', '7030', 'C-7030-05', 'provenance_wrong_page_and_wrong_source_document_plus_currency_basis', 'medium', 'unit_currency_basis', 2, m + '.json', src,
          L('cited 46 (2021), 48 (2022-23); actual AR2023 pdf p17; FY2021 AR2021 p23 / AR2022 p20', NR, 'Revenue / EBITDA / Net profit (USD m)', 'FY2023 | FY2022 (restated in AR2023)', 'USD million under metric names revenue/ebitda/net_income of a SAR-reporting issuer', 'FY2021-FY2023'),
          [pf(f) | {'currency': f.get('currency')} for f in mf], 'numbers are correct; they are USD (group presentation) and sit on AR2023 p17, not p46/p48', C(True, 'not applicable', 'FY2022 as first reported (AR2022 p20) was 2,427/828/133; manifest correctly uses the restated 2,421/842/147', ''),
          'findings[id=C-7030-05]', '7030.json', checks, claimed='defective (proven)', rank=21)
    build('batch1-C', '7030', 'C-7030-07', 'quarter_facts_source_not_archived', 'medium', 'source_not_archived', 7, 'zain-ksa-2023-2025-quarterly-results.json', None, L(), '36 quarterly facts', 'n/a', C(), 'findings[id=C-7030-07]', '7030.json', [],
          reason='batch status unverified: quarterly source announcements not archived', claimed='unverified', force_status='suspected', rank=75)

    # ---- GO ----
    m = 'go-telecom-2021-2025-fy-history'
    d, src = source_for_manifest(m)
    checks = [chk('manifest has no comprehensive_income / cost_of_revenue / operating_expenses fact for FY2021-FY2024', not any(f['metric'] in ('comprehensive_income', 'cost_of_revenue', 'operating_expenses') and f['period_end'] < '2025-03-31' for f in d['facts'])),
              cf(src, ['136,690,984', '160,603,720'])[0], cf(src, ['39,002,488'])[0]]
    build('batch1-C', '7040', 'C-7040-01', 'document_completeness_multi_year_lines_not_extracted', 'medium', 'completeness', 7, m + '.json', src,
          L('31, 32, 33, 35', NR, 'total operating expenses, total comprehensive income, cost of services, other income, investing/financing cash flows, segment revenue split (FY2021-FY2024)', 'five fiscal-year columns', 'SAR', 'FY2021-FY2024 (years ending 31 March)'),
          'not published for FY2021-FY2024', 'printed on the cited pages of the Board report', C(), 'findings[id=C-7040-01]', '7040.json', checks, claimed='defective (proven)', rank=76)
    fg = [f for f in d['facts'] if f['metric'] == 'five_g_coverage']
    checks = [chk('manifest five_g_coverage stored as 0.30', any(f['value'] in ('0.30', '0.3') for f in fg)), cp(src, 22, ['over 30%'])]
    build('batch1-C', '7040', 'C-7040-02', 'approximate_statement_stored_as_exact_value', 'low', 'derived_value', 5, m + '.json', src,
          L(22, pr(src, 22), '"GO deployed its 5G network across 18 cities, covering over 30% of the population"', '2025-03-31', 'ratio', '2025-03-31'), [pf(f) for f in fg], 'lower bound (>30%), not exactly 0.30', C(), 'findings[id=C-7040-02]', '7040.json', checks, claimed='defective (proven)', rank=34)
    build('batch1-C', '7040', 'C-7040-04', 'quarter_sum_vs_fiscal_year', 'low', 'period_column_vintage', 3, 'go-telecom-2023-2025-quarterly-history.json vs go-telecom-2021-2025-fy-history.json', None, L(), 'FY2025 quarterly net profit sum differs from FY by -0.63% (batch C)', 'n/a', C(NR, NR, NR, ''), 'findings[id=C-7040-04]', '7040.json', [],
          reason='batch status unverified; quarterly source not archived', claimed='unverified', force_status='suspected', rank=22)

    # ---- Elm ----
    m = 'elm-2025-fy'
    d, src = source_for_manifest(m)
    pg = sorted({f['page'] for f in d['facts']})
    rend = [ev(src, '7203', m, 8, 1.0)]
    eps = [f for f in d['facts'] if f['metric'] == 'eps_diluted']
    vis = chk('visual read of rendered pdf p8 (statement of profit or loss, printed page 6): Basic 26.86 / 23.51 and Diluted 26.80 / 23.44', True, 'read from rendered image by the bundle auditor')
    build('batch1-C', '7203', 'C-7203-01', 'missing_field_eps_basic', 'low', 'completeness', 7, m + '.json', src,
          L(8, '6', 'Earnings per share from net profit attributable to equity holders of the parent: Basic / Diluted', 'FY2025 | FY2024', 'SAR per share', 'FY2025 / FY2024'), [pf(f) for f in eps] + ['eps_basic: absent'], 'Basic 26.86 (2025) / 23.51 (2024)', C(), 'findings[id=C-7203-01]', '7203.json',
          [cmx(m, 'eps_basic'), vis], 'visual + manifest', rendered=rend, claimed='defective (proven)', rank=77)
    checks = [chk('manifest facts cite printed page numbers (6/7/8/10), i.e. PDF page minus 2', sorted(pg) in ([6, 7, 8, 10], [6, 8, 10], [6, 7, 8, 10, 11]) or max(pg) <= 12, f'cited pages {pg}; PDF has {len(open_pdf(src))} pages')]
    build('batch1-C', '7203', 'C-7203-02', 'page_reference_printed_not_pdf', 'low', 'provenance_page', 6, m + '.json', src, L(f'cited {pg}; actual PDF 8,9,10,12', 'cited printed pages', '(all facts)', NR, NR, 'FY2025/FY2024'),
          f'{len(d["facts"])} facts cite printed page numbers', 'PDF page numbers (offset +2)', C(), 'findings[id=C-7203-02]', '7203.json', checks, 'manifest + PDF length', claimed='defective (documented in manifest notes)', rank=42)
    n7203 = [os.path.basename(p) for p in glob.glob(os.path.join(REPO, 'data/imports', 'elm-*.json'))]
    build('batch1-C', '7203', 'C-7203-03', 'coverage_only_two_fiscal_years', 'medium', 'coverage', 7, '(none)', None, L(), f'{len(n7203)} manifest(s) for 7203: {n7203}', 'FY2022-FY2023 annuals, interims, price history', C(), 'findings[id=C-7203-03]', '7203.json',
          [chk('data/imports holds exactly one Elm manifest (FY2025 with FY2024 comparatives)', len(n7203) == 1, str(n7203))], 'filesystem', claimed='defective (coverage)', rank=78)


# =============================================================================================
def batch_d():
    # ---- SABIC ----
    spec = [
        ('2010-D1', 'sabic-2025-fy', 'capex', 'definition_drift_across_periods', 'medium', 'definition', ['8,750,028', '24,777', '10,114,320', '85,909'], 'capex',
         'FY2025 -8,750,028 (PP&E only) vs FY2024 -10,200,229 (PP&E + intangibles)', 'FY2025 on FY2024 basis = -8,774,805 (8,750,028 + 24,777); company-reported Capital expenditures 8.77 Bn (FY2025) / 10.20 Bn (FY2024)', 'printed 137 (cash flow); 42 (summary)'),
        ('2010-D2', 'sabic-2025-fy', 'proceeds_asset_sales', 'definition_drift_across_periods', 'medium', 'definition', ['82,308', '3,605,726', '562,424', '33,343'], 'proceeds_asset_sales',
         'FY2025 82,308 (PP&E only) vs FY2024 595,767 (PP&E + held-for-sale)', 'same basis: FY2025 3,688,034 or FY2024 33,343', 'printed 137'),
        ('2010-D3', 'sabic-2024-fy-comparative', 'depreciation_amortization', 'definition_drift_across_periods', 'low', 'definition', ['11,185,373', '1,184,728'], None,
         'FY2025 12,762,575 (deep notes) vs FY2024 13,009,105 (cash-flow basis)', 'cash-flow basis FY2025 = 12,897,679 (11,185,373 + 1,184,728 + 527,578)', 'printed 136, 186/159'),
        ('2010-D4', 'sabic-2024-fy-comparative', 'equity components', 'incomplete_extraction_breaks_component_sum', 'medium', 'completeness', ['110,889,032'], None,
         'share_capital 30,000,000 + other_reserves -4,112,475 + retained_earnings 19,581,626 = 45,469,151', 'equity_parent 156,358,183 (general reserve 110,889,032 not extracted)', 'printed 132'),
        ('2010-D5', 'sabic-2025-deep-financial-notes', 'borrowings_by_instrument', 'component_double_counted', 'low', 'numeric_composite', ['13,658,398', '998,345', '538,236', '33,546,363'], None,
         'Murabaha 15,195,578', '15,194,979 (13,658,398 + 998,345 + 538,236); published already contains the 599 of conventional short-term borrowings listed again as overdraft', 'printed 184'),
        ('2010-D6', 'sabic-2025-deep-financial-notes', 'related_party_payables', 'derived_sum_arithmetic_error', 'low', 'numeric_composite', ['719,429', '5,520,211', '3,655,683', '2,401,573'], None,
         '12,296,996', '12,296,896 (sum of the four printed rows; the page prints no total)', 'printed 201'),
        ('2010-D7', 'sabic-2025-gap-closure', 'petrochemicals_sales_volume', 'mixed_operating_basis_unflagged', 'medium', 'basis_continuing_ops', ['23.4', '16.2', '23.2', '13.0'], None,
         'gap-closure: Chemicals 23.4 and Polymers 16.2 Mn t; sector-operational: 23.2 and 13.0 (basis=continuing_operations)', '23.4/16.2 = "TOTAL OPERATIONAL FOOTPRINT (Including discontinued operations)"; 23.2/13.0 = "Continuing operations" panel', 'printed 47'),
        ('2010-D8', 'sabic-2025-gap-closure', 'domestic/international_revenue_chemicals', 'mislabelled_metric', 'low', 'mapping', ['18,083,824', '116,525,214', '32,530,448', '23,111,610'], None,
         '18,083,824 / 98,441,390 labelled Chemicals', 'GROUP revenue by customer location (total 116,525,214), not the Chemicals segment (103,935,678)', 'printed 208'),
        ('2010-D9', 'sabic-2021-2025-five-year-financial-history', 'cash', 'cash_flow_cash_published_as_balance_sheet_cash', 'low', 'mapping', ['27,950,605', '27,746,328'], None,
         '42.31 / 40.04 / 33.80 Bn under metric cash (cash-flow table)', 'publish as cash_end; cash-flow cash differs from balance-sheet cash (FY2025 27,950,605 vs 27,746,328)', 'printed 42 and 132/137'),
    ]
    for did, m, metric, cls, sev, cat, needles, mt, pub, cor, pg in spec:
        d, src = source_for_manifest(m)
        c1, pages = cf(src, needles)
        checks = [c1]
        pubf = []
        if mt:
            pubf = [pf(f) for f in d['facts'] if f['metric'] == mt]
            checks.append(chk(f'manifest {m} has {mt} facts', bool(pubf)))
        if did == '2010-D5':
            checks.append(chk('manifest carries Murabaha 15,195,578 in borrowings_by_instrument', '15195578' in json.dumps(d, ensure_ascii=False)))
        if did == '2010-D6':
            checks.append(chk('manifest carries related_party_payables 12,296,996 and the four rows sum to 12,296,896', '12296996' in json.dumps(d, ensure_ascii=False) and 719429 + 5520211 + 3655683 + 2401573 == 12296896))
        if did == '2010-D1':
            checks.append(chk('capex FY2025 -8,750,028 and FY2024 -10,200,229 across the two manifests', any(f['metric'] == 'capex' and f['value'] == '-8750028' for f in fx('sabic-2025-fy')) and any(f['metric'] == 'capex' and f['value'] == '-10200229' for f in fx('sabic-2024-fy-comparative'))))
        if did == '2010-D2':
            checks.append(chk('proceeds_asset_sales FY2025 82308 and FY2024 595767', any(f['metric'] == 'proceeds_asset_sales' and f['value'] == '82308' for f in fx('sabic-2025-fy')) and any(f['metric'] == 'proceeds_asset_sales' and f['value'] == '595767' for f in fx('sabic-2024-fy-comparative'))))
        if did == '2010-D4':
            checks.append(chk('manifest has no general-reserve fact (110,889,032 absent from manifest)', '110889032' not in json.dumps(d, ensure_ascii=False)))
        if did == '2010-D8':
            checks.append(chk('non-KSA rows printed on the page (32,530,448+23,111,610+12,072,642+10,484,225+9,293,022+10,949,443) sum to 98,441,390 = total 116,525,214 - KSA 18,083,824 (group revenue by customer location)', 32530448 + 23111610 + 12072642 + 10484225 + 9293022 + 10949443 == 98441390 == 116525214 - 18083824))
        if did == '2010-D1':
            checks.append(chk('arithmetic: 8,750,028 + 24,777 = 8,774,805; 10,114,320 + 85,909 = 10,200,229', 8750028 + 24777 == 8774805 and 10114320 + 85909 == 10200229))
        if did == '2010-D2':
            checks.append(chk('arithmetic: 82,308 + 3,605,726 = 3,688,034; 33,343 + 562,424 = 595,767', 82308 + 3605726 == 3688034 and 33343 + 562424 == 595767))
        if did == '2010-D3':
            checks.append(chk('arithmetic: 11,185,373 + 1,184,728 + 527,578 = 12,897,679', 11185373 + 1184728 + 527578 == 12897679))
            checks.append(cp(src, pages[0] if pages else 1, ['527,578']))
        if did == '2010-D4':
            checks.append(chk('arithmetic: 30,000,000 - 4,112,475 + 19,581,626 = 45,469,151; adding 110,889,032 -> 156,358,183', 30000000 - 4112475 + 19581626 == 45469151 and 45469151 + 110889032 == 156358183))
        rend7 = None
        if did == '2010-D7':
            rend7 = [ev(src, '2010', m, 47, 0.9)]
            checks.append(chk('visual read of rendered pdf p47: left panel "TOTAL OPERATIONAL FOOTPRINT (Including discontinued operations)" Sales volumes 23.4 (chemicals) / 16.2 (polymers); middle panel "OPERATIONAL FOOTPRINT (Continuing operations)" 23.2 / 13.0', True, 'read from the rendered image by the bundle auditor'))
        if did == '2010-D9':
            checks.append(chk('five-year manifest publishes metric "cash" for FY2021-2023', any(f['metric'] == 'cash' for f in d['facts'])))
        pp = pages[0] if pages else None
        tst = T_D + {'2010-D1': 'DefinitionDriftTests::test_capex_that_adds_intangibles_in_one_year_is_flagged', '2010-D2': 'DefinitionDriftTests::test_capex_that_adds_intangibles_in_one_year_is_flagged',
                     '2010-D5': 'DimensionReconciliationTests::test_component_counted_twice_breaks_the_reconciliation'}.get(did, '')
        build('batch1-D', '2010', did, cls, sev, cat, 5 if did not in ('2010-D7',) else 4, m + '.json', src,
              L(f'{pages[:4]} (found by bundle; batch cites {pg})', pr(src, pp) if pp else NR, metric, 'FY2025 / FY2024 as stated', 'SAR thousand unless stated (see published_value)', 'FY2025 / FY2024'), pubf or pub, cor,
              C(True if did in ('2010-D1', '2010-D2', '2010-D3', '2010-D4') else NR, 'continuing vs discontinued operations panels' if did == '2010-D7' else NR, 'same document (AR2025), pages as located', 'FY2024 comparative is the restated figure in AR2025 (batch D: only the restated FY2024 is retained)' if did in ('2010-D1', '2010-D2', '2010-D3', '2010-D4') else ''),
              f'sources[manifest=data/imports/{m}.json].defects[{did}]', '2010.json', checks, test=tst or 'none', scope='synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests' if tst else '',
              claimed='defective (proven)', rank=50 + int(did[-1]), fix=NR, rendered=rend7)
    d, src = source_for_manifest('sabic-2025-deep-financial-notes')
    sg = [pf(f) for f in d['facts'] if f['metric'] in ('zakat_expense', 'income_tax_expense', 'depreciation_amortization', 'amortization_expense') and vnum(f['value']) and float(f['value']) > 0]
    build('batch1-D', '2010', '2010-D10', 'sign_convention_inconsistent', 'low', 'sign_convention', 5, 'sabic-2025-deep-financial-notes.json', src, L('printed 133, 196, 197', NR, 'Zakat expense / Income tax benefit / D&A', 'FY2025', 'SAR thousand', 'FY2025'), sg,
          'expenses negative as in sabic-2025-fy and sa:2082/3010/3030/3050', C(), 'sources[...].defects[2010-D10]', '2010.json', [chk('deep-notes manifest publishes expense/D&A facts with positive sign', bool(sg), f'{len(sg)} facts')], claimed='defective (proven)', rank=59)

    # ---- ACWA ----
    m = 'acwa-2026-q2'
    d, s = source_for_manifest(m)
    build('batch1-D', '2082', '2082-D1', 'archive_reference_without_file', 'medium', 'source_not_archived', 7, m + '.json', s, L(NR, NR, 'all published Q2-2026 facts', NR, NR, 'Q2 2026'), f'{len(d["facts"])} facts', 'unverifiable until the file is re-archived',
          C(), 'sources[manifest=acwa-2026-q2.json].defects[2082-D1]', '2082.json', [chk('archive-index lists the PDF but no copy exists in the worktree or any ref', not s['available_offline'], s['where'])], 'filesystem + archive-index', claimed='blocked', rank=79)
    st, d, stmp = stamp_check(m)
    build('batch1-D', '2082', '2082-D2', 'metadata_filed_at_inferred', 'low', 'metadata_filed_at', 6, m + '.json', s, L(), dict(filed_at=d['filed_at'], filed_at_basis=d.get('filed_at_basis'), filed_at_confidence=d.get('filed_at_confidence'), filed_at_note=d.get('filed_at_note')),
          'filing date from a verifiable publication stamp', C(), 'sources[manifest=acwa-2026-q2.json].defects[2082-D2]', '2082.json', [chk('manifest declares filed_at as inferred', 'infer' in json.dumps({k: d.get(k) for k in ('filed_at_basis', 'filed_at_confidence', 'filed_at_note')}).lower() or bool(d.get('filed_at_note')), str({k: d.get(k) for k in ('filed_at_basis', 'filed_at_confidence')}))], claimed='proven', rank=62)
    refc = 'origin/claude/data-utilities-1'
    onbase = os.path.exists(os.path.join(REPO, 'data/imports/acwa-power-2025-fy.json'))
    mm = load_manifest('acwa-power-2025-fy', refc)
    h = 'b5dad4f16ad2478b5146880d1b96f9cb52174f3ae9bc724f12e53c686de70295'
    s = source_info(ref=refc, path=f'data/raw/SA/2082/documents/{h}.pdf')
    build('batch1-D', '2082', '2082-D3', 'audited_statements_not_published', 'high', 'coverage', 7, f'acwa-power-2025-fy.json (only on {refc})', s, L(), 'FY2025 audited manifest exists only on ' + refc, 'present on the published (base) branch',
          C(), 'sources[...acwa-power-2025-fy.json].defects[2082-D3]', '2082.json', [chk('acwa-power-2025-fy.json is absent from data/imports on the base branch', not onbase), chk(f'manifest is present on {refc}', mm is not None)], 'filesystem + git', claimed='proven', rank=80)

    # ---- cement 3010/3030/3050 ----
    for sym, m, did1, did2, fn in (('3010', 'arabian-cement-2025-fy', '3010-D1', '3010-D2', '3010.json'), ('3030', 'saudi-cement-2025-fy', '3030-D1', '3030-D2', '3030.json'), ('3050', 'southern-province-cement-2025-fy', '3050-D1', '3050-D2', '3050.json')):
        st, d, stmp = stamp_check(m)
        d, s = source_for_manifest(m)
        build('batch1-D', sym, did1, 'metadata_filed_at_is_board_approval_date', 'low', 'metadata_filed_at', 6, m + '.json', s, L(NR, NR, 'manifest header filed_at', NR, NR, 'FY2025'), dict(filed_at=d['filed_at']),
              f'first public on Saudi Exchange {stmp} (upload date embedded in the fsPdf URL)', C(), f'sources[manifest=data/imports/{m}.json].defects[{did1}]', fn, [st], 'manifest + URL stamp',
              test=T_D + 'FilingDateTests::test_board_approval_date_before_upload_is_flagged', scope='synthetic; source branch only', claimed='proven', rank=60,
              fix='derive filed_at from the URL publication timestamp / audit-report date')
        if sym == '3050':
            rend = [ev(s, '3050', m, 7, 1.1)]
            checks = [chk('visual read of rendered pdf p7 (scanned, printed page 6): column "1 January 2024 (Restated - Note 34)" PPE 2,816,864,176; total assets 4,011,801,700; total equity 3,197,454,749; cash 363,096,531', True, 'read from the rendered image by the bundle auditor'),
                      chk('manifest has no 2023-12-31 / 2024-01-01 instant facts', not any(f.get('period_end') in ('2023-12-31', '2024-01-01') for f in d['facts']))]
            build('batch1-D', sym, did2, 'missing_period_present_in_document', 'medium', 'completeness', 7, m + '.json', s, L('7 (batch cites printed 6)', '6', 'Statement of financial position, column "1 January 2024 (Restated - Note 34)" (= 31 Dec 2023 restated)', 'third balance-sheet column', 'SAR (full riyals)', '2023-12-31 / 2024-01-01'),
                  'absent', 'PPE 2,816,864,176; total assets 4,011,801,700; total equity 3,197,454,749; cash 363,096,531', C(True, 'not applicable', 'same page, "1 January 2024 (Restated - Note 34)" column', ''), f'sources[manifest=...].defects[{did2}]', fn, checks, 'visual (scanned page rendered and read) + manifest', claimed='proven', rank=81, rendered=rend)
        else:
            f = [x for x in d['facts'] if x['metric'] == 'capex']
            other = {'3010': (['94,930', '50'], 'PP&E 94,930 + intangibles 50'), '3030': (['158,704', '12,980'], 'PP&E-only additions (intangible additions (12,980)/(3,811) on the same page)')}[sym]
            c1, pg = cf(s, other[0])
            build('batch1-D', sym, did2, 'definition_inconsistency_across_companies (capex)', 'low', 'definition', 5, m + '.json', s, L(pg[:3], NR, 'capex', 'FY2025 / FY2024', 'SAR (full riyals)', 'FY2025/FY2024'), [pf(x) for x in f],
                  'label faithful to its own definition; ' + other[1] + '; 3010 includes intangibles while 3030/3050 are PP&E-only', C(), f'sources[manifest=...].defects[{did2}]', fn, [c1, chk('manifest publishes capex', bool(f))], claimed='proven (definition drift across issuers)', rank=57,
                  test=T_D + 'DefinitionDriftTests::test_capex_that_adds_intangibles_in_one_year_is_flagged', scope='synthetic; source branch only')


# =============================================================================================
def batch_ef():
    # E: filed_at x5
    for sym, m in (('3002', 'najran-cement-2025-fy'), ('3003', 'city-cement-2025-fy'), ('3005', 'umm-al-qura-cement-2025-fy'), ('3020', 'yamama-cement-2025-fy'), ('3040', 'qassim-cement-2025-fy')):
        if not load_manifest(m):
            cand = [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(REPO, 'data/imports', '*.json')) if load_manifest(os.path.basename(p)) and load_manifest(os.path.basename(p)).get('symbol') == sym and load_manifest(os.path.basename(p)).get('filing_type') == 'financial-statements']
            m = cand[0] if cand else m
        st, d, stmp = stamp_check(m)
        d, s = source_for_manifest(m)
        build('batch2-E', sym, f'AUDIT-E-META-1-{sym}', 'metadata / point-in-time (filed_at = Board approval date)', 'medium-low', 'metadata_filed_at', 6, m + '.json', s, L(NR, NR, 'manifest.filed_at', NR, NR, 'FY2025'), dict(filed_at=d['filed_at']),
              f'on or after the Saudi Exchange publication date {stmp} (and, for 3002, the 6 April 2026 audit-opinion date)', C(), 'dimension_1_numeric_correctness.defects[AUDIT-E-META-1-' + sym + ']', sym + '.json', [st], 'manifest + URL stamp',
              test=T_E + 'test_filed_at_not_before_publication', scope='strict xfail parametrised over the five manifests: flips to a failure once filed_at is fixed (marker must then be removed); source branch only', claimed='proven',
              rank=61, transcription=f'{BUNDLE}/batch2-E/e_transcripts/{sym}.json', fix='derive filed_at from the URL timestamp / audit-report date; keep board date in notes')
    # E 3020 composite impairment + capex
    m = [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(REPO, 'data/imports', '*.json')) if (load_manifest(os.path.basename(p)) or {}).get('symbol') == '3020' and (load_manifest(os.path.basename(p)) or {}).get('filing_type') == 'financial-statements'][0]
    d, s = source_for_manifest(m)
    imp = [f for f in d['facts'] if f['metric'] == 'impairment_charges']
    build('batch2-E', '3020', 'AUDIT-E-3020-1', 'classification: composite mixes statement positions', 'low', 'mapping', 5, m + '.json', s,
          L(8, pr(s, 8), 'Provision for expected credit loss (ECL) (above Income from main activities) + Provision for impairment of spare parts (below, under Other (expenses)/income)', 'FY2025', 'SAR (full riyals)', 'FY2025'),
          [pf(f) for f in imp], 'split: ECL (20,185,882) deducted above operating income; spare-parts impairment (31,801,775) below; sum -51,987,657 fits neither bridge', C(), 'dimension_1_numeric_correctness.defects[AUDIT-E-3020-1]', '3020.json',
          [cm(m, 'impairment_charges', '51987657'), cp(s, 8, ['20,185,882', '31,801,775', '418,694,182', '495,877,524'])], 'text layer + manifest', claimed='defective (low)', rank=58, transcription=f'{BUNDLE}/batch2-E/e_transcripts/3020.json',
          test=T_E + 'test_manifest_matches_page_transcription', scope='pins every published value to the transcription (the composite value is pinned as published, not flagged as a defect)')
    cap = [f for f in d['facts'] if f['metric'] == 'capex']
    build('batch2-E', '3020', 'AUDIT-E-3020-2', 'definition: capex omits intangibles', 'low', 'definition', 5, m + '.json', s, L('10 (batch cites printed 8)', pr(s, 10), "Purchase of Intangible assets (294,281 / 1,470,413) omitted from capex", 'FY2025 | FY2024', 'SAR (full riyals)', 'FY2025/FY2024'),
          [pf(f) for f in cap], 'policy decision: City (2024) and Qassim include intangibles', C(), 'dimension_1_numeric_correctness.defects[AUDIT-E-3020-2]', '3020.json', [cp(s, 10, ['294,281', '1,470,413'])] + [chk('manifest publishes capex', bool(cap))],
          claimed='defective (low)', rank=58, transcription=f'{BUNDLE}/batch2-E/e_transcripts/3020.json')
    # F
    m = 'yanbu-cement-2025-fy'
    d, s = source_for_manifest(m)
    scanned = 'scanned' in json.dumps(d, ensure_ascii=False).lower()
    build('batch2-F', '3060', 'F-3060-1', 'provenance_description_wrong (statements tagged scanned)', 'low', 'provenance_tag', 6, m + '.json', s, L('6-10 (statements), 3-5 (auditor report scanned)', NR, 'manifest notes / reader tag / archive-index capture_method', NR, NR, 'FY2025'),
          'statements described as scanned images', 'PDF pp6-10 carry a full born-digital text layer; only the auditor report pp3-5 is scanned', C(),
          'findings[id=F-3060-1]', '3060.json', [chk('manifest text calls the statements scanned', scanned), cp(s, 6, ['Revenue', '1,083,964,180']), chk('pdf p6 has a text layer', len(page_text(s, 6) or '') > 200)], 'text layer + manifest', claimed='defective (low)', rank=63,
          transcription=f'{BUNDLE}/batch2-F/f_transcripts/3060.json')
    for sym, m, ax, did, bfile in (('3060', 'yanbu-cement-2025-fy', ['11 March 2026'], 'F-3060-2', '3060.json'), ('7202', 'stc-solutions-2025-fy', ['February 19, 2026'], 'F-7202-2', '7202.json')):
        st, d, stmp = stamp_check(m)
        d, s = source_for_manifest(m)
        build('batch2-F', sym, did, 'filed_at_semantics (Board approval date)', 'medium-low', 'metadata_filed_at', 6, m + '.json', s, L(NR, NR, 'manifest.filed_at', NR, NR, 'FY2025'), dict(filed_at=d['filed_at']),
              'on or after the audit-report date and the Saudi Exchange upload date ' + str(stmp), C(), f'findings[id={did}]', bfile, [st], 'manifest + URL stamp',
              test=T_F + 'test_filed_at_not_before_publication', scope='strict xfail for both manifests; source branch only', claimed='defective', rank=61, transcription=f'{BUNDLE}/batch2-F/f_transcripts/{sym}.json')
    m = 'stc-solutions-2025-fy'
    d, s = source_for_manifest(m)
    checks = [cp(s, 64, ['557,229', '559,813', '3,886,613', '3,885,729', '22,034', '25,502']), chk('manifest notes do not mention the Note 43 PPA adjustment of FY2024 comparatives', not re.search(r'note 43|purchase price allocation|adjusted', json.dumps(d.get('notes'), ensure_ascii=False).lower()))]
    build('batch2-F', '7202', 'F-7202-1', 'undisclosed_adjusted_comparatives', 'low-medium', 'basis_restated', 4, m + '.json', s,
          L(64, pr(s, 64), 'Note 43: FY2024 balance sheet adjusted for the LABS purchase price allocation: intangibles 557,229 -> 559,813; trade payables/accruals 3,886,613 -> 3,885,729; NCI 22,034 -> 25,502', 'FY2024 comparative column (31 Dec 2024)', "SAR '000, scale 1000", '2024-12-31'),
          'published FY2024 values equal the ADJUSTED figures: intangible_assets 559,813; accounts_payable 3,885,729; noncontrolling_interests 25,502', 'values are correct as printed in the FY2025 report, but not flagged as adjusted vs the FY2024 filing (557,229 / 3,886,613 / 22,034)',
          C(True, 'not applicable', dict(document='stc-solutions-2025-fy (FY2025 audited FS), Note 43', source_file_sha256=s['sha256'], pdf_page=64, scope='consolidated, FY2024 comparative balance sheet after PPA adjustment'), 'the originally filed FY2024 statements are not in the repo'),
          'findings[id=F-7202-1]', '7202.json', checks, 'text layer + manifest', test=T_F + 'test_7202_notes_disclose_comparative_adjustment', scope='strict xfail pinning the missing disclosure; source branch only', claimed='defective (low-medium)', rank=23,
          transcription=f'{BUNDLE}/batch2-F/f_transcripts/7202.json', fix='state the adjustment in the manifest notes')
    d, s = source_for_manifest('yanbu-cement-2025-fy')
    build('batch2-F', '3060', 'F-3060-3', 'missing_fields (basic/diluted EPS only as diluted, OCI components, cash-flow lines)', 'low', 'completeness', 7, 'yanbu-cement-2025-fy.json', s, L('6, 7, 10', NR, 'Basic and diluted EPS 0.66 | 1.00; OCI re-measurement (1,316,459) | (6,164,977); employees benefits paid (13,844,438) | (10,582,809)', 'FY2025 | FY2024', 'SAR', 'FY2025/FY2024'),
          'only eps_diluted published', 'also printed: OCI components, employee benefits paid, FVTPL flows', C(), 'findings[id=F-3060-3]', '3060.json',
          [cp(s, 6, ['0.66', '1.00']), cp(s, 7, ['1,316,459']), cp(s, 10, ['13,844,438', '10,582,809'])], claimed='defective (low)', rank=82, transcription=f'{BUNDLE}/batch2-F/f_transcripts/3060.json')
    d, s = source_for_manifest('stc-solutions-2025-fy')
    rend = [ev(s, '7202', 'stc-solutions-2025-fy', 9, 1.0)]
    vis = chk('visual read of rendered pdf p9 (scanned P&L, printed page 7): EPS Basic 12.62 | 13.42 and Diluted 12.52 | 13.31', True, 'read from the rendered image by the bundle auditor (page has no text layer)')
    build('batch2-F', '7202', 'F-7202-3', 'missing_fields (basic EPS 12.62/13.42, OCI components, cash-flow detail)', 'low', 'completeness', 7, 'stc-solutions-2025-fy.json', s, L(9, '7', 'Earnings per share: Basic 12.62 | 13.42; Diluted 12.52 | 13.31', 'FY2025 | FY2024', 'SAR per share', 'FY2025/FY2024'),
          'eps_diluted 12.52 / 13.31 published; basic absent', 'Basic 12.62 / 13.42', C(), 'findings[id=F-7202-3]', '7202.json', [cmx('stc-solutions-2025-fy', 'eps_basic'), vis], 'visual (scanned page rendered and read) + manifest',
          claimed='defective (low)', rank=83, rendered=rend, transcription=f'{BUNDLE}/batch2-F/f_transcripts/7202.json')
    for sym, bf, nm in (('3060', '3060.json', 'F-3060-4'), ('7202', '7202.json', 'F-7202-4')):
        mans = [os.path.basename(p) for p in glob.glob(os.path.join(REPO, 'data/imports', '*.json')) if (load_manifest(os.path.basename(p)) or {}).get('symbol') == sym]
        build('batch2-F', sym, nm, 'coverage_only_two_fiscal_years', 'medium', 'coverage', 7, '(none)', None, L(), f'{len(mans)} manifest(s): {mans}', 'earlier annual and interim statements, original FY2024 filing', C(), f'findings[id={nm}]', bf,
              [chk('data/imports holds exactly one manifest for the symbol', len(mans) == 1, str(mans))], 'filesystem', claimed='defective (coverage)', rank=84)
    # E coverage THIN for the five cement
    for sym in ('3002', '3003', '3005', '3020', '3040'):
        mans = [os.path.basename(p) for p in glob.glob(os.path.join(REPO, 'data/imports', '*.json')) if (load_manifest(os.path.basename(p)) or {}).get('symbol') == sym]
        build('batch2-E', sym, f'COVERAGE-{sym}', 'coverage_thin (dimension 3: FY2025 + FY2024 comparatives only)', 'medium', 'coverage', 7, '(none)', None, L(), f'{len(mans)} manifest(s): {mans}', 'quarterly/interim and pre-2024 history', C(), 'dimension_3_company_coverage', sym + '.json',
              [chk('data/imports holds exactly one manifest for the symbol', len(mans) == 1, str(mans))], 'filesystem', claimed='THIN (batch E dimension 3)', rank=85)


def leads():
    m = 'zain-ksa-2025-notes-segments'
    d, src = source_for_manifest(m)
    seg = [f for f in d['facts'] if f['metric'] == 'segment_revenue']
    tot = sum(float(f['value']) for f in seg)
    rev = [f for f in fx('zain-ksa-2025-fy') if f['metric'] == 'revenue' and f['period_end'] == '2025-12-31'][0]
    t = page_text(src, 68) or ''
    checks = [chk('segment_revenue facts sum to more than consolidated revenue (manifest arithmetic)', tot > float(rev['value']), f'sum {tot:,.0f} vs revenue {float(rev["value"]):,.0f}: difference {tot - float(rev["value"]):,.0f} (batch D: 862,572)'),
              cp(src, 68, ['6,911,555', '1,804,454', '3,129,827'])]
    build('batch1-D', '7030', 'LEAD-7030-segment-revenue', 'segment_revenue_sum_exceeds_revenue (lead handed over by batch D; may be inter-segment eliminations)', 'low', 'definition', 5, m + '.json', src,
          L(68, pr(src, 68), 'Consumer / Business / Wholesale revenue (segment note)', 'FY2025', "SAR '000, scale 1000", 'FY2025'), [pf(f) for f in seg], 'unknown: batch C states segment revenue includes internal sales; whether an elimination row exists on the page was not established',
          C('not applicable', 'not applicable', 'zain-ksa-2025-fy revenue 10,983,264 (pdf p9)', ''), 'summary: Repo-wide run also flags sa:7030 segment_revenue', 'batch1-D-summary.md', checks, 'manifest arithmetic + text layer',
          force_status='suspected', reason='arithmetic gap confirmed, but whether it is an extraction defect or legitimate intersegment eliminations is not established', claimed='lead (not a proven defect)', rank=64)
    build('batch1-D', '1080 / 1120', 'LEAD-1080-1120-DA-label', 'depreciation_amortization label drift (lead only)', 'low', 'definition', 5, 'anb / alrajhi manifests', None, L(), NR, NR, C(), 'summary: RC-CAPEX-DEFINITION (also seen for ... sa:1080/1120 D&A labels, leads for other auditors)', 'batch1-D-summary.md', [],
          force_status='suspected', reason='batch D names this as a lead for other auditors without evidence; no batch A record confirms it; not re-checked', claimed='lead (not a proven defect)', rank=65)


def filed_at_all():
    hits = []
    n_fs = 0
    for pth in sorted(glob.glob(os.path.join(REPO, 'data/imports', '*.json'))):
        m = load_manifest(os.path.basename(pth))
        if not m or not m.get('source_url'):
            continue
        st = url_stamp(m['source_url'])
        if not st:
            continue
        n_fs += 1
        if m.get('filed_at') and m['filed_at'] < st:
            hits.append(dict(manifest=os.path.basename(pth), symbol=m.get('symbol'), filed_at=m['filed_at'], url_upload_date=st, filed_at_basis=m.get('filed_at_basis')))
    build('batch2-E', 'Saudi Exchange fsPdf manifests (all symbols)', 'META-FILED-AT-ALL', 'filed_at earlier than Saudi Exchange upload date (repo-wide scan re-run by bundle)', 'medium-low', 'metadata_filed_at', 6,
          f'{len(hits)} of {n_fs} manifests whose source_url carries an upload timestamp', None, L(NR, NR, 'manifest.filed_at', NR, NR, NR), hits, 'filed_at >= publication/audit-report date', C(),
          'summary + tools/e_filed_at_check.py (re-implemented by bundle)', 'batch2-E-summary.md', [chk('at least one manifest has filed_at earlier than the upload date in its URL', bool(hits), f'{len(hits)} of {n_fs}')], 'manifest scan',
          test=T_E + 'test_filed_at_not_before_publication', scope='strict xfail covering the five Group-E manifests only', claimed='proven (11 of 12 per batch E)', rank=60)


def adapt_c_f():
    batch_c()
    batch_d()
    batch_ef()
    filed_at_all()
    leads()
    return REC
