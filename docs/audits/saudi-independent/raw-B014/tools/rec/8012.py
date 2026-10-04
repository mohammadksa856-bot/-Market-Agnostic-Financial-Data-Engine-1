NAME = 'JAZIRA TAKAFUL (Aljazira Takaful Taawuni Company, Tadawul 8012)'
SPEC = 'jazira.py'
SCOPE = 'raw collected files in C:/Users/Mohammed856/finengine-raw-odd (read-only); no network, no data/**, no AWS/Supabase; SHA-256 recomputed for every document listed (18 files in the inventory, all match). Entity: Aljazira Takaful Taawuni Company on every cover 2022 to H1 2026 (no rename or merger seen). SAR thousand as printed. The balance sheet carries about SAR 1.6bn of investments held to cover unit-linked liabilities (matched by unit reserves in insurance contract liabilities) and goodwill 232,255, so total assets are not comparable with non-life peers.'
METHOD = 'Statement pages located by text and inventory statement_pages; values read from the clean text layer by label for 2022 to H1 2026 filings (box-drawing characters stripped, merged rows resolved by position); FY2025 income statement (p8) rendered and checked by eye; the Q1 2025 file has image-only primary statements (pp4-8) and was rendered at 1.8x and read by eye. Every transcribed column passes the identities in tools/check_transcripts.py (BS equation; insurance service result; net insurance and investment chain; income before zakat; net income after zakat and tax; cash-flow sum and roll; Q1+Q2=H1 and H1+Q3=9M chains); three one-unit quarter-sum roundings are declared, and 16 cross-filing differences are declared with both values and reasons.'
DIMENSIONS = {
 'value_correctness': {
  'status': 'verified_from_pages_for_12_statement_sets_FY2022_to_H1_2026_with_declared_IFRS17_restatement',
  'summary': 'SAR thousand. Transcribed sets: FY2022 (IFRS 4 original), FY2023, FY2024, FY2025; Q1/H1/9M 2024; Q1/H1/9M 2025; Q1 2026, H1 2026. Findings: (1) IFRS 17 transition restated 2022: income before zakat 30,284 -> 40,450, net income 28,354 -> 38,520, equity 841,477 -> 892,718, total assets 2,652,046 -> 2,533,534, cash 263,185 -> 254,752 (declared against the FY2023 annual). (2) FY2024 operating cash flow re-presented in the FY2025 annual: 72,596 -> 72,024 and financing -21,885 -> -21,313. (3) Results are dominated by unit-linked and FVTPL investment returns offset by finance expense (H1 2026: net investment return 144,148 vs net finance expense 126,147), so net income is thin: H1 2026 net income 100 (Q1 7,461, Q2 -7,361) vs H1 2025 20,193; FY2025 39,841; FY2024 37,203; FY2023 44,254; FY2022 28,354 (IFRS 4) / 38,520 (IFRS 17). (4) Q1+Q2=H1 and H1+Q3=9M chains hold for 2024, 2025 and 2026 apart from three declared one-unit roundings. (5) The H1 2026 dividend paid 26,400 appears in financing cash flow. Seasonality: 9M and H1 quarters differ widely because of FVTPL swings, Q3 is not run-rate of H1.',
  'not_read': ['notes to the statements in all files', 'equity statements and OCI (located, not transcribed)', 'balance-sheet component lines other than totals, cash and insurance contract liabilities', 'Q1/H1/9M 2022 and Q1/H1/9M 2023 interim statements (covers only; IFRS 4 for 2022 and the 2023 IFRS 17 first-year interims)']},
 'document_completeness': {
  'status': 'all_18_files_are_single_period_english_statement_sets_one_has_image_only_primary_statements',
  'summary': 'All 18 files are full single-period English statement sets; no Arabic twins, no scans except e655fe25 (Q1 2025) whose primary statements are image pages 4-8 (the inventory lists statement_pages 15 and 21, which are segment notes, and flags cash flows missing). The inventory also flags 440eccd9, b05cbba4 and d057a23f missing cash flows although the CF page 8 is present with clean text in all three. The inventory flags 2022|FY as an internal gap; the FY2022 audited annual is labelled 2023|FY.'},
 'company_coverage': {
  'status': 'complete_Q1_2022_to_H1_2026_by_page_derived_periods_values_transcribed_for_FY2022_to_FY2025_and_2024_2026_interims',
  'present_page_derived': ['FY2022', 'FY2023', 'FY2024', 'FY2025', 'Q1/H1/9M 2022', 'Q1/H1/9M 2023', 'Q1/H1/9M 2024', 'Q1/H1/9M 2025', 'Q1 2026', 'H1 2026'],
  'derivable_from_comparatives': ['Q4 of each year by subtraction (never filed stand-alone)', 'Q2/Q3 quarter columns printed in H1/9M filings (verified 2024-2026)'],
  'missing': ['FY2021 and earlier annuals (the FY2022 annual carries 2021 comparatives only); history before 2022', 'FY2026 and 9M 2026 (not yet due)'],
  'inventory_correction': 'The inventory reports 2022|FY as an internal gap; page evidence shows the file labelled 2023|FY is the FY2022 audited statements, so no FY2022 gap exists, and annual labels 2023|FY to 2026|FY are FY2022 to FY2025 (publication year).'}}
NOTES = {
 '868c2e31': {'note': 'inventory label 2023|FY is publication year (FY2022, IFRS 4 original); fills the 2022|FY gap the inventory reports'},
 '3f4c9afd': {'note': 'inventory label 2024|FY is publication year (FY2023); first IFRS 17 annual with 2022 and 1 Jan 2022 restated'},
 'dbdca144': {'note': 'inventory label 2025|FY is publication year (FY2024)'},
 '71d4dcb1': {'note': 'inventory label 2026|FY is publication year (FY2025)'},
 'e655fe25': {'class_ok': False, 'statements': 'VISUAL: BS p4, IS p5, CF p8 image pages rendered and read by eye', 'note': 'inventory missing cash_flows is wrong; statement_pages 15 and 21 are segment notes'},
 '440eccd9': {'class_ok': False, 'note': 'inventory missing cash_flows is wrong: CF page 8 present'},
 'b05cbba4': {'class_ok': False, 'note': 'inventory missing cash_flows is wrong: CF page 8 present'},
 'd057a23f': {'class_ok': False, 'note': 'inventory missing cash_flows is wrong: CF page 8 present'},
}
for _s in ['3f26ae97', 'fb77d5e7', 'dc0750dc', '10743483', 'eca00812', '7c97e6ec']:
    NOTES.setdefault(_s, {})['statements'] = 'not transcribed (period confirmed from cover only)'
DEFECTS = [
 {'id': 'B014-8012-1', 'klass': 'annual_period_label_is_publication_year', 'severity': 'high', 'evidence': '868c2e31 (FY2022), 3f4c9afd (FY2023), dbdca144 (FY2024), 71d4dcb1 (FY2025) are labelled 2023|FY, 2024|FY, 2025|FY, 2026|FY; the inventory therefore reports a false 2022|FY gap'},
 {'id': 'B014-8012-2', 'klass': 'ifrs17_transition_restatement_of_2022', 'severity': 'high', 'evidence': 'FY2022 as published (IFRS 4): income before zakat 30,284, net income 28,354, equity 841,477, cash 263,185; FY2023 annual restated 2022: 40,450, 38,520, 892,718, 254,752'},
 {'id': 'B014-8012-3', 'klass': 'cash_flow_comparative_represented', 'severity': 'medium', 'evidence': 'FY2024 operating cash flow 72,596 and financing -21,885 in the FY2024 annual, 72,024 and -21,313 as the comparative in the FY2025 annual (net change 52,166 identical)'},
 {'id': 'B014-8012-4', 'klass': 'inventory_false_missing_cash_flows_and_image_only_pages', 'severity': 'medium', 'evidence': 'inventory flags 440eccd9, b05cbba4, d057a23f, e655fe25 as missing cash flows; the first three have CF on clean page 8, the fourth has image-only pages 4-8 holding BS, IS and CF'},
 {'id': 'B014-8012-5', 'klass': 'rounding_between_filings', 'severity': 'low', 'evidence': '2025 Q1+Q2 vs H1 income before zakat 22,636 vs 22,637 and net income 20,192 vs 20,193; H1+Q3 vs 9M income before zakat differs by 1'},
]
UNREAD = [
 'notes to the statements in all files',
 'equity statements and OCI (located, not transcribed)',
 'Q1/H1/9M 2022 (dc0750dc, fb77d5e7, 3f26ae97) and Q1/H1/9M 2023 (7c97e6ec, eca00812, 10743483) statements: covers only, values not transcribed',
 'FY2021 and earlier annuals are not in the raw set',
]
CONCLUSION = 'Value correctness: headline three-statement values verified from pages for 12 sets (FY2022-FY2025, Q1/H1/9M 2024 and 2025, Q1/H1 2026) with the IFRS 17 restatement of 2022 and a cash-flow re-presentation declared with both values. Document completeness: all 18 files are single-period English statement sets; one has image-only primary statements read visually; inventory missing-cash-flow flags are false. Company coverage: every period Q1 2022 to H1 2026 present once by page evidence (the inventory 2022|FY gap is a label artefact). INCOMPLETE as a value history: six 2022-2023 interim sets not transcribed.'
