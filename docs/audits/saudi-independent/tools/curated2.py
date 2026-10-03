"""Curated findings, part 2 (SAIB, SNB, Tawuniya, Aramco). Imported by curated.py."""
import json, os
from b_inventory import inventory

STALE_P3 = dict(
    id='P3-STALE', defect_class='stale_catalog_exclusion_pillar3', severity='medium',
    summary=('KM1 rows CET1 amount, Tier 1 amount, leverage exposure/ratio, HQLA, net cash outflow, LCR, available/required '
             'stable funding and NSFR are excluded with reason catalog_field_missing, although the current '
             'Pillar3KeyMetricsReader publishes them (re-read of the same archived PDF gives 56-70 publishable facts vs 4-20 '
             'in the manifest; the Alinma manifests, produced later, publish them). Result: no CET1/Tier-1 amounts, '
             'leverage, LCR or NSFR for this issuer in the published data.'),
    fix=('regenerate Pillar 3 manifests with the current reader and run reconcile_vintages across the set; '
         'tools/p3_regen_dryrun.py reports the delta without writing anything; Codex to publish'))

P3_MISSING = ['cet1_capital', 'tier1_capital', 'leverage_ratio_exposure', 'leverage_ratio', 'high_quality_liquid_assets',
              'net_cash_outflow', 'liquidity_coverage_ratio', 'available_stable_funding', 'required_stable_funding',
              'net_stable_funding_ratio']


def p3_entries(sym):
    out = {}
    for r in inventory(sym):
        if 'pillar3' in r['manifest']:
            out[r['manifest']] = dict(defects=[dict(STALE_P3)], completeness=dict(missing_fields=P3_MISSING),
                                      checks_manual=['cross-document comparison of the same quarter across all issuer disclosures (tools/b_p3_cross.py): only restatements by the issuer differ'])
    return out


def apply(CURATED):
    saib, snb, tw, ac = CURATED['1030'], CURATED['1180'], CURATED['8010'], CURATED['2222']
    saib['company'].update(
        numeric_correctness_summary=('no numeric defect found: FY2025 audited statements (page images read, all 83 facts), 19 Pillar 3 manifests '
                                     '(1,370 facts incl. excluded) and 5 XLSX supplements anchor exactly to source; classification notes only'),
        document_completeness_summary=('FY2025 FS: 83 facts of ~200 printed lines; Pillar 3 KM1 amounts beyond RWA/total capital/CET1 ratio/Tier-1 ratio '
                                       'are excluded (P3-STALE)'),
        coverage=dict(have=['FY2025 and restated FY2024 (audited PDF)', 'quarterly 17-line series 1Q2021-2Q2026 and FY2021-2023 via XLSX supplements',
                            'Pillar 3 KM1: 2018-06, 2018-12, 2019-06, 2019-12, 2022-03/06/09/12, 2023-03/06/09/12, 2024-03/06/09/12, 2025-06/09, 2026-06 documents'],
                      absent=['audited FS for FY2024-and-earlier as originally filed', 'every interim FS PDF', 'cash-flow statement outside FY2025/FY2024',
                              'Pillar 3 documents for 2019-09..2021-12 and 2025-03/2025-12 not archived']))
    saib['manifests'].update(p3_entries('1030'))
    saib['manifests']['saib-2025-fy.json'] = dict(
        numeric_correctness='verified_correct',
        checks=['pdf p9 (financial position) page image read: all 15+14 published balance-sheet values match (Total assets 172,720,276; Customers deposits 109,619,007; Investments 47,196,978)',
                'pdf p10 (income): 19+19 values match incl. signs and EPS 1.68/1.43; 3,527,768+374,227+257,465+87,459+11,123+536,140 = 4,794,182 foots',
                'pdf p14-15 (cash flow): operating 1,387,085; investing (6,375,408); financing 1,436,708; net change (3,551,616); begin 6,137,954; end 2,586,338; capex (362,286); dividends (997,860) and all 2024 comparatives match',
                'columns: 2025 = first numeric column; 2024 = the Restated column (published with period_end 2024-12-31)'],
        semantic_notes=['metric debt_securities_issued is fed by the printed line "Term Loans, net" 2,789,722 (a term loan, not securities)',
                        'total_equity 22,433,472 includes Tier-1 sukuk 5,312,500; shareholders equity 17,120,972 is not published',
                        'FY2024 values are restated comparatives; the originally filed FY2024 statements are not archived'],
        completeness=dict(missing_fields=['Positive/negative fair values of derivatives 622,360 / 47,714', 'Investments in associates 1,083,124', 'Other real estate 593,010',
                                          'Intangible assets 818,858', 'Treasury shares (34,979)', 'Tier I Sukuk 5,312,500', 'Shareholders equity 17,120,972',
                                          'Gains on disposals of FVOCI debt securities 11,123', 'Rent and premises 61,049', 'Operating income 2,715,837',
                                          'Share in earnings of associates 124,683', 'cash-flow detail lines (statutory deposit, loans, deposits, zakat paid, sukuk cost (334,731))']))
    snb['company'].update(
        numeric_correctness_summary=('no numeric defect found: FY2025 audited statements (pages 9, 10, 13 row-aligned), 4 interim statements, 10 XLSX supplements and 10 Pillar 3 documents '
                                     'anchor exactly; sign conventions consistent; the NCI sign flip from the workbook is intentional and matches the PDF'),
        document_completeness_summary='FY2025: 96 facts of ~120 printed lines; Pillar 3 KM1 beyond four metrics excluded (P3-STALE)',
        coverage=dict(have=['FY2025 (+FY2024 comparatives); interim 2Q-2025, 3Q-2025, 1Q-2026, 2Q-2026 PDFs', 'XLSX supplements 2Q2024..2Q2026 quarters, FY2022-2025',
                            'Pillar 3: 2023Q1, 2024Q2, 2024Q4, 2025Q1-Q4, 2026Q1-Q2'],
                      absent=['audited FY2024 and earlier as filed', '1Q-2025 interim PDF', 'stand-alone 4Q-2025 quarter (supplement only)',
                              'everything before 2024 except FY2022/23 supplement lines and Pillar 3 2023Q1', 'cash flow outside FY2025/FY2024 and interim ytd']))
    snb['manifests'].update(p3_entries('1180'))
    snb['manifests']['snb-2025-fy.json'] = dict(
        numeric_correctness='verified_correct',
        checks=['pdf p9 balance sheet: 17 values anchored (Total assets 1,210,031,553; Customers deposits 636,094,377; equity 203,827,248)',
                'pdf p10 income: all published incl. EPS diluted 4.03; net income parent 25,013,279 / NCI (21,718) on separate rows',
                'pdf p13 cash flow: totals match; dividends_paid (12,000,000) = final 6,000,000 + interim 6,000,000 (derived sum of two printed lines); FX effect (433,513) read from a wrapped caption',
                'cash roll: 21,001,893 + 5,513,671 - 433,513 = 26,082,051'],
        semantic_notes=['equity_parent 203,278,511 is "Equity attributable to equity holders of the Bank" and includes Tier-1 sukuk 17,652,684 (185,625,827 not published)',
                        'depreciation_amortization excludes amortisation of intangibles 820,280 (separate printed line)',
                        'other_income is negative: printed "Other operating expenses, net"'],
        completeness=dict(missing_fields=['Goodwill 34,006,782', 'Intangible assets 4,921,688', 'Property/equipment 13,065,976', 'Derivative fair values', 'Share premium 63,701,800',
                                          'Treasury shares (2,586,243)', 'Tier 1 Sukuk 17,652,684', 'Equity attributable to shareholders 185,625,827', 'FVIS gains 2,819,579',
                                          'Non-FVIS gains 558,687', 'Rent 485,853', 'Amortisation of intangibles 820,280', 'Income from operations 28,288,040',
                                          'Other non-operating (391,307)', 'basic EPS 4.04 (only diluted published)']))
    for mf in ('snb-2025-q2.json', 'snb-2025-q3.json', 'snb-2026-q1.json', 'snb-2026-q2.json'):
        snb['manifests'][mf] = dict(
            numeric_correctness='verified_correct',
            checks=['income statement (pdf p5): quarter facts come from the first (three-month) column, ytd from the third; Q1 has a single pair',
                    'balance sheet (pdf p4): first (current-date) column of three', 'cash flow (pdf p8): current-period column',
                    'sign convention consistent: expenses negative; impairment reversal printed (172,900) stored +172,900'])
    tw['company'].update(
        numeric_correctness_summary=('published FY2025 manifest: all 30 facts match the annual-report statements (page images); '
                                     'unmerged candidate manifests: one defect (tawuniya-2023-fy cash_change)'),
        document_completeness_summary='30 facts of ~75 printed statement lines; no EPS, zakat, profit before zakat, term deposits, investments, statutory deposit, cash-flow detail',
        coverage=dict(have=['FY2025 only on main / telecom-95pct'],
                      absent=['FY2023 and Q3-2024..Q4-2025 manifests exist ONLY on origin/claude/insurance-tawuniya-bupa-enrichment (2985be4), not merged',
                              'Q1-Q4 2023, Q1/Q2 2024 statements', 'FY2024 audited statement (only comparative columns)',
                              'all eight Tawuniya source PDFs are absent from main and from the audited branch; they exist only on the enrichment branch, so the published manifest cannot be re-verified from main']))
    tw['manifests']['tawuniya-2025-fy.json'] = dict(
        numeric_correctness='verified_correct', status='done',
        checks=['PDF extracted read-only from origin/claude/insurance-tawuniya-bupa-enrichment (fce6dcdf..., 20 MB); pdf p89 is the spread of printed pages 176 (financial position) and 177 (income): page image read, all published values match',
                'pdf p91 cash flow: 7 values + 2024 comparatives anchor', 'foots: 21,403,177 - 18,016,361 - 2,613,920 + 343,355 = 1,116,251'],
        semantic_notes=['cited page numbers are PDF indices (89/91), printed numbers are 176/177/179'],
        completeness=dict(missing_fields=['Insurance service result before reinsurance 3,386,816', 'Net insurance finance expense (101,768)', 'Insurance and non-insurance results 1,918,625',
                                          'Net profit before Zakat 1,226,621', 'Zakat charge (123,507)', 'EPS basic 7.37 / diluted 7.35', 'Term deposits 7,933,741',
                                          'Investments 4,578,024', 'Receivable from brokers 2,977,221', 'Statutory deposit 149,988', 'Commission income 524,998']))
    ac['company'].update(
        numeric_correctness_summary=('2025-sourced manifests: values are in the archived 2025 annual report (income statement printed p172 / pdf p174 verified line by line: '
                                     'revenue 1,559,342 ... net income 350,210, EPS 1.44); page citations wrong for that block; every other manifest unverified (source not archived)'),
        document_completeness_summary='no quarterly data for 2025; statements represented through derived annual-metrics, gap-fill and notes manifests',
        coverage=dict(have=['FY2019-FY2025 annual metrics', '2026 Q1 (8 facts) and Q2 (12 facts) interim'],
                      absent=['2025 and earlier quarters', 'source PDFs for the FY2019-FY2024 reports, the FY2025 full-financials PDF (5a3db2...), Q1-2026 and H1-2026 interim reports are not in any branch (only 78bb678e... = 2025 annual report is archived)']))
    ac['manifests']['aramco-2025-annual-metrics.json'] = dict(
        numeric_correctness='verified_correct_values_defective_citations',
        defects=[dict(id='ARA-1', defect_class='wrong_page_citation', severity='low',
                      summary=('160 of 176 facts cite a page on which the value does not occur. Income-statement facts cite page 177 but sit on pdf page 174 (printed 172); '
                               'cash-flow/other facts cite 177-180 vs pdf 176/178; dividends and EPS cite 243/244 vs pdf 177/235/174. The cited numbers fit neither pdf index nor printed page.'),
                      evidence='pdf p174 rows: Revenue 1,559,342; Other income related to sales 111,862; Net income 350,210; Earnings per share 1.44',
                      fix='derive the page from the archived PDF when regenerating; add a test that the cited page contains the value')],
        checks=['15 consolidated income-statement facts verified line by line on pdf p174 (signs, SAR-million scale)',
                'value locator: 167 of 176 present in the archived annual report; 9 not printed as such (base dividends 317,159 = 320,447 - 3,288 derived; one-decimal rounded operating metrics)'])
    for mf in ('aramco-2025-segment-ebitda-inputs.json', 'aramco-2025-other-reserve-components.json'):
        ac['manifests'][mf] = dict(numeric_correctness='verified_correct',
                                   checks=['all values located on the cited pdf page with matching label; scale SAR millions per page heading'])
    for mf in ('aramco-2025-operational-precision.json', 'aramco-2025-lease-interest.json', 'aramco-2025-gap-fill.json',
               'aramco-2025-deep-dimensional-notes.json', 'aramco-2025-full-notes.json', 'aramco-2025-fy.json',
               'aramco-2024-fy-comparative.json', 'aramco-2024-full-notes-comparative.json'):
        ac['manifests'][mf] = dict(
            numeric_correctness='unverified_partial',
            checks=['value presence only: values found in the archived 2025 annual report text (gap-fill 75/75, deep notes 168/171, full notes 26/27, fy/fy-comparative 7/7, lease 2/2, operational 3/3); row/column semantics NOT verified - the manifest source (full-financials PDF 5a3db2...) is not archived'])
    for mf in ('aramco-2019-fy-historical.json', 'aramco-2020-fy-historical.json', 'aramco-2021-annual-metrics.json', 'aramco-2021-fy-historical.json',
               'aramco-2022-annual-metrics.json', 'aramco-2022-fy-historical.json', 'aramco-2023-annual-metrics.json', 'aramco-2023-fy.json',
               'aramco-2024-annual-metrics.json', 'aramco-2026-q1.json', 'aramco-2026-q2.json'):
        ac['manifests'][mf] = dict(numeric_correctness='unverified', status='pending',
                                   note='source PDF (older annual report / 2026 interim) is not archived in any branch; cannot be compared with its source')
