# Unified Saudi audit defect bundle

Base: `origin/codex/telecom-95pct @ ec610f3`. Sources: six independent audit batches (1-A, 1-B, 1-C, 1-D, 2-E, 2-F), copied unchanged under `docs/audits/saudi-independent/bundle/<batch>/`.

**Counts: 101 proven, 15 suspected, 116 total.**

## How "proven" and "suspected" are decided

proven = the bundle auditor re-checked the defect itself against the archived source file (page rendered and read and/or text layer) and the published value in the manifest under data/imports; suspected = proven only in a batch record, or the source file is not available offline, or the check could not be completed.

- Source file SHA-256 is recomputed from the archived file where the bytes are reachable offline (worktree or a local git ref); otherwise it is the `data/raw/archive-index.json` content hash and the record says so. Nothing is invented: `unavailable` means the file is not in this repository.
- `not recorded by batch` means the batch record does not give that field and the bundle did not add it.
- Pinning tests exist only on the six source branches (not on the base); each record states what the test actually asserts. `none` means no test pins the defect.
- Evidence PNGs of pages the bundle auditor rendered and read are in `docs/audits/saudi-independent/bundle-evidence/`.
- Rule for restated figures: a restated comparative is never offered as a replacement for the published original; every record that involves one names the comparison document, its SHA-256, page and scope in `comparison.comparison_source`.

## Priority order

1. ANB (1080) defects D1-D4: 11 proven, 0 suspected
2. stc (7010) scale errors (and other unit/scale-type errors): 4 proven, 0 suspected
3. Quarter-vs-YTD / wrong period-column defects: 3 proven, 2 suspected
4. Zakat basis (D6) and other restated / continuing-operations basis defects: 7 proven, 1 suspected
5. Other numeric value, mapping, sign and definition defects: 34 proven, 6 suspected
6. Provenance and metadata defects (page citations, filed_at, scanned/digital tags): 16 proven, 1 suspected
7. Completeness, coverage and source-availability defects: 26 proven, 5 suspected

# Section: PROVEN defects (101)

## proven: group 1 - ANB (1080) defects D1-D4

### BDL-P1-001 - 1080 Arab National Bank (ANB) - D1 (high)
- Defect class: wrong_table_and_column (commission-rate note bucket published as balance-sheet total); category: numeric_wrong_source_row_and_column; batch claimed: proven
- Manifest: anb-2015-annual-report.json
- Source file SHA-256: `0482608a38c0f746b5230f227529a19ac59b24973df11d5d1b1b3a0e088d4ca3` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [53, 54]; printed page: ["73", "74"]
- Caption/label: Balance-sheet captions (cash, due from/to banks, investments, net loans, customer deposits) read from the commission-rate-sensitivity note
- Column: published: "Within 3 months" bucket of the commission-rate-sensitivity table; correct: current-year column of the primary Statement of Financial Position
- Unit/scale: SAR '000, scale 1000 (both); period: 2015-12-31 (instant)
- Published value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "12089917", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2015-12-31", "manifest_page": 54, "note_pdf_page": 54, "note_printed_page": "74", "remark": "published value is the \"Within 3 months\" bucket of the 2014 PRIOR-YEAR commission-rate table (pdf p54, printed 74), not the 2015 ta ... (full value in defect-bundle.json)
- Correct value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "10428291", "scale": "1000", "period_end": "2015-12-31", "pdf_page": 4, "printed_page": "24", "column": "2015 (current-year column, SAR 000)"}, {"metric": "due_from_banks", "caption": "Due from banks and other financial institutions", "value": "5575020", "scale": "1000", "period_end": "2015-12-31", "pdf_page": 4, "pr ... (full value in defect-bundle.json)
- Restated: false; continuing operations: not applicable; comparison source: same document (anb-2015-annual-report), primary statement pdf p4 (printed 24), current-year column; no restated figure is used; note: No restatement or continuing/discontinued basis is involved. The FY2019 AR restates 2018 comparatives (e.g. deposits 142,055,608 vs original 140,909,422) but those are NOT used here.
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D1]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2015-annual-report_pdf53.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2015-annual-report_pdf54.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2015-annual-report_pdf4.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::NoteColumnFarLeftOfValuesTests::test_rows_with_a_distant_note_column_are_read` - pins the reader root cause (D2) on a synthetic PDF only; no test asserts the republished ANB manifest values; exists only on the source branch, not on the base
- Verification: visual (note and statement pages rendered and read) + text layer + manifest; result: confirmed; 16 check(s); notes: Bucket column identified from the rendered note table; statement values read from the rendered balance sheet.

### BDL-P1-002 - 1080 Arab National Bank (ANB) - D1 (high)
- Defect class: wrong_table_and_column (commission-rate note bucket published as balance-sheet total); category: numeric_wrong_source_row_and_column; batch claimed: proven
- Manifest: anb-2017-annual-report.json
- Source file SHA-256: `91b1d6217433c1e42c32ceaa9a7744237f95dc0adafdcba21521bc11edc1ed79` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [62]; printed page: ["88"]
- Caption/label: Balance-sheet captions (cash, due from/to banks, investments, net loans, customer deposits) read from the commission-rate-sensitivity note
- Column: published: "Within 3 months" bucket of the commission-rate-sensitivity table; correct: current-year column of the primary Statement of Financial Position
- Unit/scale: SAR '000, scale 1000 (both); period: 2017-12-31 (instant)
- Published value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "8002667", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2017-12-31", "manifest_page": 62, "note_pdf_page": 62, "note_printed_page": "88", "remark": null}, {"metric": "due_from_banks", "caption": "Due from banks and other financial institutions", "value": "1010113", "scale": "1000",  ... (full value in defect-bundle.json)
- Correct value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "17251379", "scale": "1000", "period_end": "2017-12-31", "pdf_page": 12, "printed_page": "38", "column": "2017 (current-year column, SAR 000)"}, {"metric": "due_from_banks", "caption": "Due from banks and other financial institutions", "value": "1710123", "scale": "1000", "period_end": "2017-12-31", "pdf_page": 12, " ... (full value in defect-bundle.json)
- Restated: false; continuing operations: not applicable; comparison source: same document (anb-2017-annual-report), primary statement pdf p12 (printed 38), current-year column; no restated figure is used; note: No restatement or continuing/discontinued basis is involved. The FY2019 AR restates 2018 comparatives (e.g. deposits 142,055,608 vs original 140,909,422) but those are NOT used here.
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D1]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2017-annual-report_pdf62.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2017-annual-report_pdf12.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::NoteColumnFarLeftOfValuesTests::test_rows_with_a_distant_note_column_are_read` - pins the reader root cause (D2) on a synthetic PDF only; no test asserts the republished ANB manifest values; exists only on the source branch, not on the base
- Verification: visual (note and statement pages rendered and read) + text layer + manifest; result: confirmed; 16 check(s); notes: Bucket column identified from the rendered note table; statement values read from the rendered balance sheet.

### BDL-P1-003 - 1080 Arab National Bank (ANB) - D1 (high)
- Defect class: wrong_table_and_column (commission-rate note bucket published as balance-sheet total); category: numeric_wrong_source_row_and_column; batch claimed: proven
- Manifest: anb-2018-annual-report.json
- Source file SHA-256: `b5759f230bdce83493db6f4bbfd42425ab612a17807cc9db15b5538b3ef944e3` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [90, 91]; printed page: ["119", "120"]
- Caption/label: Balance-sheet captions (cash, due from/to banks, investments, net loans, customer deposits) read from the commission-rate-sensitivity note
- Column: published: "Within 3 months" bucket of the commission-rate-sensitivity table; correct: current-year column of the primary Statement of Financial Position
- Unit/scale: SAR '000, scale 1000 (both); period: 2018-12-31 (instant)
- Published value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "14312000", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2018-12-31", "manifest_page": 90, "note_pdf_page": 90, "note_printed_page": "119", "remark": null}, {"metric": "due_from_banks", "caption": "Due from banks and other financial institutions", "value": "572746", "scale": "1000", ... (full value in defect-bundle.json)
- Correct value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "22980266", "scale": "1000", "period_end": "2018-12-31", "pdf_page": 10, "printed_page": "39", "column": "2018 (current-year column, SAR 000)"}, {"metric": "due_from_banks", "caption": "Due from banks and other financial institutions", "value": "1134048", "scale": "1000", "period_end": "2018-12-31", "pdf_page": 10, " ... (full value in defect-bundle.json)
- Restated: false; continuing operations: not applicable; comparison source: same document (anb-2018-annual-report), primary statement pdf p10 (printed 39), current-year column; no restated figure is used; note: No restatement or continuing/discontinued basis is involved. The FY2019 AR restates 2018 comparatives (e.g. deposits 142,055,608 vs original 140,909,422) but those are NOT used here.
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D1]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2018-annual-report_pdf90.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2018-annual-report_pdf91.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2018-annual-report_pdf10.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::NoteColumnFarLeftOfValuesTests::test_rows_with_a_distant_note_column_are_read` - pins the reader root cause (D2) on a synthetic PDF only; no test asserts the republished ANB manifest values; exists only on the source branch, not on the base
- Verification: visual (note and statement pages rendered and read) + text layer + manifest; result: confirmed; 16 check(s); notes: Bucket column identified from the rendered note table; statement values read from the rendered balance sheet.

### BDL-P1-004 - 1080 Arab National Bank (ANB) - D1 (high)
- Defect class: wrong_table_and_column (commission-rate note bucket published as balance-sheet total); category: numeric_wrong_source_row_and_column; batch claimed: proven
- Manifest: anb-2019-annual-report.json
- Source file SHA-256: `f05ee3e34dc7d21ff7024272382f4ee0c13af8fefbb36f6f186ed369ca0d395d` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [82, 83]; printed page: ["113", "114"]
- Caption/label: Balance-sheet captions (cash, due from/to banks, investments, net loans, customer deposits) read from the commission-rate-sensitivity note
- Column: published: "Within 3 months" bucket of the commission-rate-sensitivity table; correct: current-year column of the primary Statement of Financial Position
- Unit/scale: SAR '000, scale 1000 (both); period: 2019-12-31 (instant)
- Published value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "8363000", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2019-12-31", "manifest_page": 82, "note_pdf_page": 82, "note_printed_page": "113", "remark": null}, {"metric": "due_from_banks", "caption": "Due from banks and other financial institutions", "value": "938303", "scale": "1000",  ... (full value in defect-bundle.json)
- Correct value: [{"metric": "cash_and_balances_with_central_bank", "caption": "Cash and balances with SAMA", "value": "17167044", "scale": "1000", "period_end": "2019-12-31", "pdf_page": 8, "printed_page": "39", "column": "2019 (current-year column, SAR 000)"}, {"metric": "due_from_banks", "caption": "Due from banks and other financial institutions, net", "value": "2067992", "scale": "1000", "period_end": "2019-12-31", "pdf_page": 8 ... (full value in defect-bundle.json)
- Restated: false; continuing operations: not applicable; comparison source: same document (anb-2019-annual-report), primary statement pdf p8 (printed 39), current-year column; no restated figure is used; note: No restatement or continuing/discontinued basis is involved. The FY2019 AR restates 2018 comparatives (e.g. deposits 142,055,608 vs original 140,909,422) but those are NOT used here.
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D1]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2019-annual-report_pdf82.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2019-annual-report_pdf83.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2019-annual-report_pdf8.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::NoteColumnFarLeftOfValuesTests::test_rows_with_a_distant_note_column_are_read` - pins the reader root cause (D2) on a synthetic PDF only; no test asserts the republished ANB manifest values; exists only on the source branch, not on the base
- Verification: visual (note and statement pages rendered and read) + text layer + manifest; result: confirmed; 16 check(s); notes: Bucket column identified from the rendered note table; statement values read from the rendered balance sheet.

### BDL-P1-005 - 1080 Arab National Bank (ANB) - D2 (high)
- Defect class: reader_bug_note_column (root cause of D1); category: reader_root_cause; batch claimed: proven
- Manifest: anb-2017-annual-report.json (and every ANB annual report 2015-2019)
- Source file SHA-256: `91b1d6217433c1e42c32ceaa9a7744237f95dc0adafdcba21521bc11edc1ed79` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 12; printed page: 38
- Caption/label: Statement rows that carry a note number (cash, due from banks, investments, loans, deposits, due to banks)
- Column: note column sits ~140 pt left of the amount columns
- Unit/scale: SAR '000; period: 2017-12-31
- Published value: primary-statement rows with a note number are dropped: manifest holds only 8 facts from p12 (equity and totals); the six balance-sheet lines are absent
- Correct value: cash 17,251,379; due from banks 1,710,123; investments 32,320,816; loans 114,542,929; deposits 136,048,089; due to banks 2,691,549 (all printed on p12)
- Restated: false; continuing operations: not applicable; comparison source: same page; note: reader defect, not a basis question
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D2]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2017-annual-report_pdf12.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::NoteColumnFarLeftOfValuesTests::test_rows_with_a_distant_note_column_are_read` - synthetic PDF reproducing the layout (also test_label_numbers_are_not_mistaken_for_note_references); source branch only
- Verification: visual + text layer + independent reader re-run; result: confirmed; 3 check(s)

### BDL-P1-006 - 1080 Arab National Bank (ANB) - D3 (high)
- Defect class: quarter_vs_cumulative_confusion; category: period_column; batch claimed: proven
- Manifest: anb-2021-q3.json
- Source file SHA-256: `043f5ec235f1968668b5c31b4703466dadee1405296b84a089090a214c3d30d0` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4; printed page: 2 (typed page number on the scanned statement image; not in the PDF text layer)
- Caption/label: INTERIM CONSOLIDATED STATEMENT OF INCOME FOR THE NINE MONTHS ENDED SEPTEMBER 30, 2021 AND 2020 (all rows)
- Column: published: "For the three months ended September 30, 2021" (first amount column); correct YTD: "For the nine months ended September 30, 2021" (third amount column)
- Unit/scale: SAR '000, scale 1000; period: 9M to 2021-09-30 (ytd) / Q3 2021 (quarter)
- Published value: [{"metric": "dividend_income", "caption": "Dividend income", "value": "22626", "scale": "1000", "period_kind": "ytd", "period_start": "2021-01-01", "period_end": "2021-09-30", "manifest_page": 4, "printed_row_numbers": ["22,626", "15,655", "65,136", "58,996"]}, {"metric": "exchange_income", "caption": "Exchange income, net", "value": "56146", "scale": "1000", "period_kind": "ytd", "period_start": "2021-01-01", "perio ... (full value in defect-bundle.json)
- Correct value: [{"metric": "dividend_income", "caption": "Dividend income", "three_month_2021": "22,626", "nine_month_2021": "65,136"}, {"metric": "exchange_income", "caption": "Exchange income, net", "three_month_2021": "56,146", "nine_month_2021": "158,241"}, {"metric": "financing_expense", "caption": "Special commission expense", "three_month_2021": "131,498", "nine_month_2021": "322,861"}, {"metric": "financing_income", "captio ... (full value in defect-bundle.json)
- Restated: false; continuing operations: not applicable; comparison source: same page: nine-month 2021 column (YTD) and three-month 2021 column (quarter); note: e.g. net income: published ytd 664,557 = Q3; correct ytd 1,715,488; special commission income published ytd 1,383,847 = Q3; correct ytd 3,884,940
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D3]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2021-q3_pdf4.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::TitleYearsDoNotShiftPeriodColumnsTests::test_three_month_and_nine_month_columns_are_not_confused` - synthetic IS page (asserts quarter 1,479,227 / ytd 4,416,797, net income 664,557 / 1,715,488); not asserted against the manifest; source branch only
- Verification: visual (page rendered and read) + text layer + independent reader re-run; result: confirmed; 19 check(s); notes: Rendered page shows the four columns three-months-2021 / three-months-2020 / nine-months-2021 / nine-months-2020.

### BDL-P1-007 - 1080 Arab National Bank (ANB) - D4 (medium)
- Defect class: cash_flow_adjustment_row_mapped_to_income_metric; category: mapping_and_sign; batch claimed: proven
- Manifest: anb-2015-annual-report.json
- Source file SHA-256: `0482608a38c0f746b5230f227529a19ac59b24973df11d5d1b1b3a0e088d4ca3` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [8]; printed page: ["28"]
- Caption/label: Dividend income (cash-flow reconciliation rows)
- Column: current-period column of the cash-flow statement (reconciling adjustment rows)
- Unit/scale: SAR '000, scale 1000; period: fy to 2015-12-31
- Published value: [{"metric": "dividend_income", "caption": "Dividend income", "value": "-46277", "scale": "1000", "period_kind": "fy", "period_start": "2015-01-01", "period_end": "2015-12-31", "manifest_page": 8}]
- Correct value: {"value": "dividend income is a positive income-statement line (+absolute value); the negative figure is the cash-flow deduction row. Statement value for this document is not recorded by the batch.", "bundle_located_absolute_value_on_other_pdf_pages": {"dividend_income": [5, 37]}}
- Restated: false; continuing operations: not applicable; comparison source: same document income statement; note: published rows are reconciling items of the cash-flow statement (dividend income deducted; sukuk commission added back) stored under income-statement metrics
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_income_statement_metrics_are_not_read_from_cash_flow_rows` - synthetic PDF; source branch only; batch A regression shows the fixed reader no longer emits these facts for anb-2020-q1, anb-2021-q1 and alrajhi-2024-q2
- Verification: text layer + manifest (page not rendered); result: confirmed; 2 check(s)

### BDL-P1-008 - 1080 Arab National Bank (ANB) - D4 (medium)
- Defect class: cash_flow_adjustment_row_mapped_to_income_metric; category: mapping_and_sign; batch claimed: proven
- Manifest: anb-2017-annual-report.json
- Source file SHA-256: `91b1d6217433c1e42c32ceaa9a7744237f95dc0adafdcba21521bc11edc1ed79` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [16]; printed page: ["42"]
- Caption/label: Dividend income; Special commission expense on sukuk (cash-flow reconciliation rows)
- Column: current-period column of the cash-flow statement (reconciling adjustment rows)
- Unit/scale: SAR '000, scale 1000; period: fy to 2017-12-31
- Published value: [{"metric": "dividend_income", "caption": "Dividend income", "value": "-53203", "scale": "1000", "period_kind": "fy", "period_start": "2017-01-01", "period_end": "2017-12-31", "manifest_page": 16}, {"metric": "financing_expense", "caption": "Special commission expense on sukuk", "value": "71460", "scale": "1000", "period_kind": "fy", "period_start": "2017-01-01", "period_end": "2017-12-31", "manifest_page": 16}]
- Correct value: {"value": "FY2017 special commission expense 1,370,441 printed in the 2017 comparative column of the FY2018 AR income statement (pdf p11, printed 40); dividend income +53,203 positive in the IS", "source_document": "anb-2018-annual-report", "source_document_sha256": "b5759f230bdce83493db6f4bbfd42425ab612a17807cc9db15b5538b3ef944e3", "pdf_page": 11, "printed_page": "40"}
- Restated: comparative column of a later filing; restated status not established by batch or bundle; continuing operations: not applicable; comparison source: anb-2018-annual-report pdf p11; note: published rows are reconciling items of the cash-flow statement (dividend income deducted; sukuk commission added back) stored under income-statement metrics
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2017-annual-report_pdf16.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_income_statement_metrics_are_not_read_from_cash_flow_rows` - synthetic PDF; source branch only; batch A regression shows the fixed reader no longer emits these facts for anb-2020-q1, anb-2021-q1 and alrajhi-2024-q2
- Verification: visual (anb-2017 cash-flow page rendered and read) + text layer + manifest; result: confirmed; 4 check(s)

### BDL-P1-009 - 1080 Arab National Bank (ANB) - D4 (medium)
- Defect class: cash_flow_adjustment_row_mapped_to_income_metric; category: mapping_and_sign; batch claimed: proven
- Manifest: anb-2019-annual-report.json
- Source file SHA-256: `f05ee3e34dc7d21ff7024272382f4ee0c13af8fefbb36f6f186ed369ca0d395d` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [13]; printed page: ["44"]
- Caption/label: Dividend income; Special commission expense on sukuk (cash-flow reconciliation rows)
- Column: current-period column of the cash-flow statement (reconciling adjustment rows)
- Unit/scale: SAR '000, scale 1000; period: fy to 2019-12-31
- Published value: [{"metric": "dividend_income", "caption": "Dividend income", "value": "-84531", "scale": "1000", "period_kind": "fy", "period_start": "2019-01-01", "period_end": "2019-12-31", "manifest_page": 13}, {"metric": "financing_expense", "caption": "Special commission expense on sukuk", "value": "85129", "scale": "1000", "period_kind": "fy", "period_start": "2019-01-01", "period_end": "2019-12-31", "manifest_page": 13}]
- Correct value: {"value": "FY2019 special commission expense 2,079,685 and dividend income +84,531 on the income statement (pdf p9, printed 40)", "source_document": "anb-2019-annual-report", "source_document_sha256": "f05ee3e34dc7d21ff7024272382f4ee0c13af8fefbb36f6f186ed369ca0d395d", "pdf_page": 9, "printed_page": "40"}
- Restated: false; continuing operations: not applicable; comparison source: anb-2019-annual-report pdf p9; note: published rows are reconciling items of the cash-flow statement (dividend income deducted; sukuk commission added back) stored under income-statement metrics
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_income_statement_metrics_are_not_read_from_cash_flow_rows` - synthetic PDF; source branch only; batch A regression shows the fixed reader no longer emits these facts for anb-2020-q1, anb-2021-q1 and alrajhi-2024-q2
- Verification: text layer + manifest (page not rendered); result: confirmed; 4 check(s)

### BDL-P1-010 - 1080 Arab National Bank (ANB) - D4 (medium)
- Defect class: cash_flow_adjustment_row_mapped_to_income_metric; category: mapping_and_sign; batch claimed: proven
- Manifest: anb-2020-q1.json
- Source file SHA-256: `bb7acd369c118165c3e1a141710b282807541c74a8278e50e13b96727f300087` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [7]; printed page: ["5"]
- Caption/label: Dividend income; Special commission expense on Sukuk (cash-flow reconciliation rows)
- Column: current-period column of the cash-flow statement (reconciling adjustment rows)
- Unit/scale: SAR '000, scale 1000; period: ytd to 2020-03-31
- Published value: [{"metric": "dividend_income", "caption": "Dividend income", "value": "-13223", "scale": "1000", "period_kind": "ytd", "period_start": "2020-01-01", "period_end": "2020-03-31", "manifest_page": 7}, {"metric": "financing_expense", "caption": "Special commission expense on Sukuk", "value": "18944", "scale": "1000", "period_kind": "ytd", "period_start": "2020-01-01", "period_end": "2020-03-31", "manifest_page": 7}]
- Correct value: {"value": "dividend income is a positive income-statement line (+absolute value); the negative figure is the cash-flow deduction row. Statement value for this document is not recorded by the batch.", "bundle_located_absolute_value_on_other_pdf_pages": {"dividend_income": [4], "financing_expense": []}}
- Restated: false; continuing operations: not applicable; comparison source: same document income statement; note: published rows are reconciling items of the cash-flow statement (dividend income deducted; sukuk commission added back) stored under income-statement metrics
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_income_statement_metrics_are_not_read_from_cash_flow_rows` - synthetic PDF; source branch only; batch A regression shows the fixed reader no longer emits these facts for anb-2020-q1, anb-2021-q1 and alrajhi-2024-q2
- Verification: text layer + manifest (page not rendered); result: confirmed; 3 check(s)

### BDL-P1-011 - 1080 Arab National Bank (ANB) - D4 (medium)
- Defect class: cash_flow_adjustment_row_mapped_to_income_metric; category: mapping_and_sign; batch claimed: proven
- Manifest: anb-2021-q1.json
- Source file SHA-256: `34a845e4794654c46add4d0de50b1738722fbb585b12de26f6910ac38683b5d5` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [7]; printed page: ["5"]
- Caption/label: Dividend income; Special commission expense on Sukuk (cash-flow reconciliation rows)
- Column: current-period column of the cash-flow statement (reconciling adjustment rows)
- Unit/scale: SAR '000, scale 1000; period: ytd to 2021-03-31
- Published value: [{"metric": "dividend_income", "caption": "Dividend income", "value": "-16162", "scale": "1000", "period_kind": "ytd", "period_start": "2021-01-01", "period_end": "2021-03-31", "manifest_page": 7}, {"metric": "financing_expense", "caption": "Special commission expense on Sukuk", "value": "23386", "scale": "1000", "period_kind": "ytd", "period_start": "2021-01-01", "period_end": "2021-03-31", "manifest_page": 7}]
- Correct value: {"value": "dividend income is a positive income-statement line (+absolute value); the negative figure is the cash-flow deduction row. Statement value for this document is not recorded by the batch.", "bundle_located_absolute_value_on_other_pdf_pages": {"dividend_income": [4], "financing_expense": []}}
- Restated: false; continuing operations: not applicable; comparison source: same document income statement; note: published rows are reconciling items of the cash-flow statement (dividend income deducted; sukuk commission added back) stored under income-statement metrics
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_income_statement_metrics_are_not_read_from_cash_flow_rows` - synthetic PDF; source branch only; batch A regression shows the fixed reader no longer emits these facts for anb-2020-q1, anb-2021-q1 and alrajhi-2024-q2
- Verification: text layer + manifest (page not rendered); result: confirmed; 3 check(s)

## proven: group 2 - stc (7010) scale errors (and other unit/scale-type errors)

### BDL-P2-001 - 7010 stc (Saudi Telecom) - C-7010-01 (high)
- Defect class: scale_error_text_millions_stored_as_raw_scale_1; category: scale; batch claimed: defective (proven)
- Manifest: stc-2025-segments-financial-notes.json
- Source file SHA-256: `7dccc9e19eb2627fd7e455fab047b79044ad893071a327f6c23eb92663c7ad21` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 128; printed page: 254-255 (spread; text on right-hand page 255)
- Caption/label: Information about major customers - revenues from Government entities
- Column: FY2025 amount in running text
- Unit/scale: printed in SAR millions (running text); stored as value 11298000 with scale 1 (engine normalises raw*scale); period: FY2025 (2025-01-01..2025-12-31)
- Published value: {"metric": "customer_concentration", "caption": "Revenue from Government entities", "value": "11298000", "scale": "1", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 128, "normalised_sar": 11298000}
- Correct value: {"value": "11298000", "scale": "1000", "normalised_sar": 11298000000, "printed_as": "approximately SAR 11,298 million (2024: SAR 11,145 million)"}
- Restated: false; continuing operations: not applicable (group-level note disclosure); comparison source: same page; note: value unchanged; only the scale is wrong (1000x too small)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-01]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/7010_stc-2025-segments-financial-notes_pdf128.png`
- Pinning test: `origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::ProvenanceTests::test_million_text_stored_as_thousands_with_scale_one_is_a_scale_suspect` - synthetic page text for the detector (src/finengine/manifest_audit.py, source branch only); batch C reports the detector reproduces this defect on real data, but no test asserts the corrected manifest value
- Verification: visual (page rendered and read) + text layer + manifest; result: confirmed; 4 check(s)

### BDL-P2-002 - 7010 stc (Saudi Telecom) - C-7010-02 (high)
- Defect class: scale_error_text_millions_stored_as_raw_scale_1; category: scale; batch claimed: defective (proven)
- Manifest: stc-2025-segments-financial-notes.json
- Source file SHA-256: `7dccc9e19eb2627fd7e455fab047b79044ad893071a327f6c23eb92663c7ad21` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 141; printed page: 280-281 (spread; text on right-hand page 281)
- Caption/label: 27.2 Defined contribution plans - expense recognised for the year
- Column: FY2025 amount in running text
- Unit/scale: printed in SAR millions (running text); stored as value 631000 with scale 1 (engine normalises raw*scale); period: FY2025 (2025-01-01..2025-12-31)
- Published value: {"metric": "employee_benefit_expense", "caption": "Defined contribution plan expense", "value": "631000", "scale": "1", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 141, "normalised_sar": 631000}
- Correct value: {"value": "631000", "scale": "1000", "normalised_sar": 631000000, "printed_as": "SAR 631 million (2024: SAR 675 million)"}
- Restated: false; continuing operations: not applicable (group-level note disclosure); comparison source: same page; note: value unchanged; only the scale is wrong (1000x too small)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-02]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/7010_stc-2025-segments-financial-notes_pdf141.png`
- Pinning test: `origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::ProvenanceTests::test_million_text_stored_as_thousands_with_scale_one_is_a_scale_suspect` - synthetic page text for the detector (src/finengine/manifest_audit.py, source branch only); batch C reports the detector reproduces this defect on real data, but no test asserts the corrected manifest value
- Verification: visual (page rendered and read) + text layer + manifest; result: confirmed; 3 check(s)

### BDL-P2-003 - 7030 Zain KSA - C-7030-04 (medium)
- Defect class: field_semantics_mismatch_per_share_in_total_amount_field; category: unit_scale; batch claimed: defective (proven)
- Manifest: zain-ksa-2025-company-profile.json
- Source file SHA-256: `23f6d19a79de8c10bcc12e19128f9dd672e4c52333106d9e277ea7d75c524c44` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: AR2025 pp 23/24/34 (per manifest metadata); printed page: not recorded by batch
- Caption/label: Dividend of SAR 0.50 per share (4 corporate actions FY2022-FY2025)
- Column: corporate_actions.cash_amount
- Unit/scale: SAR per share stored in a total-amount field; period: FY2022-FY2025
- Published value: [{"action_key": "sa:7030:dividend:fy2022", "cash_amount": 0.5, "currency": "SAR"}, {"action_key": "sa:7030:dividend:fy2023", "cash_amount": 0.5, "currency": "SAR"}, {"action_key": "sa:7030:dividend:fy2024", "cash_amount": 0.5, "currency": "SAR"}, {"action_key": "sa:7030:dividend:fy2025", "cash_amount": 0.5, "currency": "SAR"}]
- Correct value: about SAR 449,364,588 per dividend (0.50 x 898,729,175 shares); other manifests store the total in cash_amount
- Restated: not applicable; continuing operations: not applicable; comparison source: cash-flow "Dividend paid" 451,855 thousand (2025) and 448,115 (2024) per batch C
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7030.json#findings[id=C-7030-04]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7030.json`
- Pinning test: `none`
- Verification: manifest (field semantics); the cross-issuer comparison (22 other actions store totals) from batch C was not recounted; result: confirmed; 1 check(s); notes: page text not re-read: AR2025 pdf pages 23/24/34 not checked for the per-share statement

### BDL-P2-004 - 7030 Zain KSA - C-7030-05 (medium)
- Defect class: provenance_wrong_page_and_wrong_source_document_plus_currency_basis; category: unit_currency_basis; batch claimed: defective (proven)
- Manifest: zain-ksa-2021-2023-financial-history.json
- Source file SHA-256: `c3d63156bb98c10362c6627f3cb144ad0f2655facf84c2cbb89da946592bc62b` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: cited 46 (2021), 48 (2022-23); actual AR2023 pdf p17; FY2021 AR2021 p23 / AR2022 p20; printed page: not recorded by batch
- Caption/label: Revenue / EBITDA / Net profit (USD m)
- Column: FY2023 / FY2022 (restated in AR2023)
- Unit/scale: USD million under metric names revenue/ebitda/net_income of a SAR-reporting issuer; period: FY2021-FY2023
- Published value: [{"metric": "revenue", "caption": "Revenue (USD m)", "value": "2111", "scale": "1000000", "period_kind": "fy", "period_start": "2021-01-01", "period_end": "2021-12-31", "manifest_page": 46, "currency": "USD"}, {"metric": "ebitda", "caption": "EBITDA (USD m)", "value": "836", "scale": "1000000", "period_kind": "fy", "period_start": "2021-01-01", "period_end": "2021-12-31", "manifest_page": 46, "currency": "USD"}, {"me ... (full value in defect-bundle.json)
- Correct value: numbers are correct; they are USD (group presentation) and sit on AR2023 p17, not p46/p48
- Restated: true; continuing operations: not applicable; comparison source: FY2022 as first reported (AR2022 p20) was 2,427/828/133; manifest correctly uses the restated 2,421/842/147
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7030.json#findings[id=C-7030-05]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7030.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 2 check(s)

## proven: group 3 - Quarter-vs-YTD / wrong period-column defects

### BDL-P3-001 - 1150 Alinma Bank - ALN-1 (high)
- Defect class: quarter_vs_cumulative_confusion; category: period_column; batch claimed: proven (ALN-1)
- Manifest: alinma-2018-q2.json
- Source file SHA-256: `a6f2b183dd7b9b30e9c1035c1aef133b37743653bc678726c1904063e525921b` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4; printed page: 3
- Caption/label: INTERIM CONSOLIDATED STATEMENT OF INCOME (all rows read as ytd)
- Column: published: "For the three months period ended" 2018 column; correct ytd: "For the six/nine months period ended" 2018 column
- Unit/scale: SAR '000, scale 1000 (EPS in SAR); period: ytd to 2018-06-30
- Published value: [{"metric": "depreciation_amortization", "caption": "Depreciation and amortization", "value": "-46098", "scale": "1000", "period_kind": "ytd", "period_start": "2018-01-01", "period_end": "2018-06-30", "manifest_page": 4, "printed_row_numbers": ["46,098", "44,177", "92,060", "107,801"]}, {"metric": "dividend_income", "caption": "Dividend income", "value": "22649", "scale": "1000", "period_kind": "ytd", "period_start": ... (full value in defect-bundle.json)
- Correct value: [{"metric": "depreciation_amortization", "caption": "Depreciation and amortization", "three_month": "46,098", "cumulative": "92,060"}, {"metric": "dividend_income", "caption": "Dividend income", "three_month": "22,649", "cumulative": "32,443"}, {"metric": "exchange_income", "caption": "Exchange income, net", "three_month": "45,868", "cumulative": "85,403"}, {"metric": "financing_income", "caption": "Income from inves ... (full value in defect-bundle.json)
- Restated: false; continuing operations: not applicable; comparison source: same page, cumulative 2018 column (third number of each printed row); note: 2017 comparative columns on the Q3 page are marked "Restated" but are not used
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2018-q2.json].defects[ALN-1]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1150_alinma-2018-q2_pdf4.png`
- Pinning test: `none for alinma-2018-q2 itself; only the Q3-2018 document is asserted by origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_nine_month_subtitle_does_not_turn_quarter_into_ytd` - asserts reader output on the archived Q3-2018 PDF (total operating income 1,211,698 / 3,552,462; net income 653,266 / 1,856,403); source branch only; does not assert the manifest
- Verification: visual (page rendered and read) + text layer + manifest; result: confirmed; 11 check(s)

### BDL-P3-002 - 1150 Alinma Bank - ALN-1 (high)
- Defect class: quarter_vs_cumulative_confusion; category: period_column; batch claimed: proven (ALN-1)
- Manifest: alinma-2018-q3.json
- Source file SHA-256: `8eae5c4221d8d630cf02132020d89b659a654e2448c9a7ed7a40703e45b48306` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4; printed page: 3
- Caption/label: INTERIM CONSOLIDATED STATEMENT OF INCOME (all rows read as ytd)
- Column: published: "For the three months period ended" 2018 column; correct ytd: "For the six/nine months period ended" 2018 column
- Unit/scale: SAR '000, scale 1000 (EPS in SAR); period: ytd to 2018-09-30
- Published value: [{"metric": "depreciation_amortization", "caption": "Depreciation and amortization", "value": "-46067", "scale": "1000", "period_kind": "ytd", "period_start": "2018-01-01", "period_end": "2018-09-30", "manifest_page": 4, "printed_row_numbers": ["46,067", "44,288", "138,127", "152,089"]}, {"metric": "dividend_income", "caption": "Dividend income", "value": "753", "scale": "1000", "period_kind": "ytd", "period_start":  ... (full value in defect-bundle.json)
- Correct value: [{"metric": "depreciation_amortization", "caption": "Depreciation and amortization", "three_month": "46,067", "cumulative": "138,127"}, {"metric": "dividend_income", "caption": "Dividend income", "three_month": "753", "cumulative": "33,196"}, {"metric": "eps_diluted", "caption": "Basic and diluted earnings per share (SAR)", "three_month": "0.44", "cumulative": "1.25"}, {"metric": "exchange_income", "caption": "Exchan ... (full value in defect-bundle.json)
- Restated: false; continuing operations: not applicable; comparison source: same page, cumulative 2018 column (third number of each printed row); note: 2017 comparative columns on the Q3 page are marked "Restated" but are not used
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2018-q3.json].defects[ALN-1]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1150_alinma-2018-q3_pdf4.png`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_nine_month_subtitle_does_not_turn_quarter_into_ytd` - asserts reader output on the archived Q3-2018 PDF (total operating income 1,211,698 / 3,552,462; net income 653,266 / 1,856,403); source branch only; does not assert the manifest
- Verification: visual (page rendered and read) + text layer + manifest; result: confirmed; 12 check(s)

### BDL-P3-005 - 7010 stc (Saudi Telecom) - C-7010-04 (medium)
- Defect class: wrong_period_column_prior_year_value_taken; category: period_column; batch claimed: defective (proven)
- Manifest: stc-2025-operating-kpis.json
- Source file SHA-256: `7dccc9e19eb2627fd7e455fab047b79044ad893071a327f6c23eb92663c7ad21` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 38; printed page: 74-75 (spread; chart on right-hand page 75; manifest cites 75)
- Caption/label: Subscribers at a glance - Fixed subscribers: fixed-wired broadband subscriptions (millions)
- Column: published: Q4 24 bar (1.3); correct: Q4 25 bar (1.4)
- Unit/scale: millions (chart labels), stored as count 1,300,000 scale 1; period: 2025-12-31 (Q4 25)
- Published value: {"metric": "broadband_subscribers", "caption": "Wired broadband subscribers 1.3 million", "value": "1300000", "scale": "1", "period_kind": "instant", "period_start": null, "period_end": "2025-12-31", "manifest_page": 75}
- Correct value: 1,400,000 (Q4 25 wired broadband 1.4 million); 1.3 million is the Q4 24 comparative
- Restated: false; continuing operations: not applicable; comparison source: same chart, Q4 25 bar; note: zoomed chart read: Q4 24 = 3.9 + 1.3 + 0.5 = 5.7; Q4 25 = 4.1 + 1.4 + 0.5 = 6.0
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-04]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/7010_stc-2025-operating-kpis_pdf38.png`, `docs/audits/saudi-independent/bundle-evidence/7010_stc-2025-operating-kpis_pdf38_zoom.png`
- Pinning test: `none` - no test pins this value (batch C added a generic provenance detector only; it cannot see chart values)
- Verification: visual (chart rendered at 3x and read) + manifest; result: confirmed; 2 check(s)

## proven: group 4 - Zakat basis (D6) and other restated / continuing-operations basis defects

### BDL-P4-001 - 1010 Riyad Bank - D6 (high)
- Defect class: restated_comparative_and_zakat_basis_discontinuity; category: basis_zakat; batch claimed: proven
- Manifest: riyad-2018-fy.json
- Source file SHA-256: `3584a14d3495e39d720b3442a8b0bb3a8fcd30caf662bbb4a975c41426b7dd42` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 9; printed page: 2
- Caption/label: Net income for the year (published as metric net_income; FY2018 PRE-zakat basis)
- Column: FY2018 current-year column of the FY2018 statements (original basis: zakat charged to equity, not to income)
- Unit/scale: SAR '000, scale 1000; period: FY2018 (2018-01-01..2018-12-31)
- Published value: {"metric": "net_income", "caption": "Net income for the year", "value": "4716085", "scale": "1000", "period_kind": "fy", "period_start": "2018-01-01", "period_end": "2018-12-31", "manifest_page": 9, "eps": ["1.57"]}
- Correct value: {"note": "DO NOT replace the published number. The FY2018 net income is correct as printed in the original FY2018 statements (pre-zakat basis); what is defective is the unflagged basis: later periods are after-zakat, so the series is not like-for-like.", "restated_after_zakat_net_income": "3092277", "restated_eps": "1.03", "detail": "Net income for the year before zakat 4,716,085 (identical to the originally publishe ... (full value in defect-bundle.json)
- Restated: true; continuing operations: not applicable (no discontinued operations involved; the restatement is the change in zakat/tax presentation); comparison source: {"document": "riyad-2019-fy", "source_file_sha256": "6f026edbf873539a2504ac673ed98fdd92a1cd28fe7d3477e78cd9fa8a2a17bd", "source_file_sha256_basis": "recomputed from archived file in this worktree; equals archive-index content_hash", "pdf_page": 8, "printed_page": "2", "column": "\"2018 (Restated)\" column of the FY2019 statement of income", "scope": "consoli ... (full value in defect-bundle.json); note: batch A cited pdf p2 of riyad-2019-fy; p2 is the auditor report - the restated income statement is pdf p8 (printed "Page 2 of 82")
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1010.json#defects[id=D6]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1010.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1010_riyad-2018-fy_pdf9.png`, `docs/audits/saudi-independent/bundle-evidence/1010_riyad-2019-fy_pdf8.png`
- Pinning test: `none` - batch A proposes ingesting comparatives as restated vintages (manifest_vintages) and tagging net_income basis, but wrote no test for D6
- Verification: visual (both pages rendered and read) + text layer + manifest; result: confirmed; 4 check(s); notes: batch A cited pdf p2 of riyad-2019-fy; p2 is the auditor report - the restated income statement is pdf p8 (printed "Page 2 of 82")

### BDL-P4-002 - 1080 Arab National Bank (ANB) - D6 (high)
- Defect class: restated_comparative_and_zakat_basis_discontinuity; category: basis_zakat; batch claimed: proven
- Manifest: anb-2018-annual-report.json
- Source file SHA-256: `b5759f230bdce83493db6f4bbfd42425ab612a17807cc9db15b5538b3ef944e3` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 11; printed page: 40
- Caption/label: Net income for the year (published as metric net_income; FY2018 PRE-zakat basis)
- Column: FY2018 current-year column of the FY2018 statements (original basis: zakat charged to equity, not to income)
- Unit/scale: SAR '000, scale 1000; period: FY2018 (2018-01-01..2018-12-31)
- Published value: {"metric": "net_income", "caption": "Net income for the year", "value": "3311817", "scale": "1000", "period_kind": "fy", "period_start": "2018-01-01", "period_end": "2018-12-31", "manifest_page": 11, "eps": []}
- Correct value: {"note": "DO NOT replace the published number. The FY2018 net income is correct as printed in the original FY2018 statements (pre-zakat basis); what is defective is the unflagged basis: later periods are after-zakat, so the series is not like-for-like.", "restated_after_zakat_net_income": "3970659", "restated_eps": "2.65", "detail": "Net income before zakat and income tax 3,311,817 (equals the originally published ne ... (full value in defect-bundle.json)
- Restated: true; continuing operations: not applicable (no discontinued operations involved; the restatement is the change in zakat/tax presentation); comparison source: {"document": "anb-2019-annual-report", "source_file_sha256": "f05ee3e34dc7d21ff7024272382f4ee0c13af8fefbb36f6f186ed369ca0d395d", "source_file_sha256_basis": "recomputed from archived file in this worktree; equals archive-index content_hash", "pdf_page": 9, "printed_page": "40", "column": "\"2018 (Restated)\" column of the FY2019 statement of income", "scope" ... (full value in defect-bundle.json); note: the restated figure is a comparative inside a later filing = different vintage/basis; to be ingested as a separate restated vintage, never overwriting the original
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D6]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1080_anb-2018-annual-report_pdf11.png`, `docs/audits/saudi-independent/bundle-evidence/1080_anb-2019-annual-report_pdf9.png`
- Pinning test: `none` - batch A proposes ingesting comparatives as restated vintages (manifest_vintages) and tagging net_income basis, but wrote no test for D6
- Verification: visual (both pages rendered and read) + text layer + manifest; result: confirmed; 4 check(s)

### BDL-P4-003 - 1140 Bank Albilad - D6 (high)
- Defect class: restated_comparative_and_zakat_basis_discontinuity; category: basis_zakat; batch claimed: proven
- Manifest: albilad-2018-fy.json
- Source file SHA-256: `cba48e96aa0a3a5597fd8c2eb873104b936a7debadbe0f9f288b9abab7bf443e` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 43; printed page: 85
- Caption/label: Net income for the year (published as metric net_income; FY2018 PRE-zakat basis)
- Column: FY2018 current-year column of the FY2018 statements (original basis: zakat charged to equity, not to income)
- Unit/scale: SAR '000, scale 1000; period: FY2018 (2018-01-01..2018-12-31)
- Published value: {"metric": "net_income", "caption": "Net income for the year", "value": "1110510", "scale": "1000", "period_kind": "fy", "period_start": "2018-01-01", "period_end": "2018-12-31", "manifest_page": 43, "eps": ["1.85"]}
- Correct value: {"note": "DO NOT replace the published number. The FY2018 net income is correct as printed in the original FY2018 statements (pre-zakat basis); what is defective is the unflagged basis: later periods are after-zakat, so the series is not like-for-like.", "restated_after_zakat_net_income": "612693", "restated_eps": "0.82", "detail": "Net income before zakat 1,110,510 (equals the originally published net income); zakat ... (full value in defect-bundle.json)
- Restated: true; continuing operations: not applicable (no discontinued operations involved; the restatement is the change in zakat/tax presentation); comparison source: {"document": "albilad-2019-fy", "source_file_sha256": "ec46ea3ca369f1d246a6bc5c823528622ac327943ce40464b4f3e202f47d7c56", "source_file_sha256_basis": "recomputed from archived file in this worktree; equals archive-index content_hash", "pdf_page": 8, "printed_page": "2", "column": "\"2018 Restated\" column of the FY2019 statement of income", "scope": "consoli ... (full value in defect-bundle.json); note: the restated figure is a comparative inside a later filing = different vintage/basis; to be ingested as a separate restated vintage, never overwriting the original
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1140.json#defects[id=D6]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1140.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1140_albilad-2018-fy_pdf43.png`, `docs/audits/saudi-independent/bundle-evidence/1140_albilad-2019-fy_pdf8.png`
- Pinning test: `none` - batch A proposes ingesting comparatives as restated vintages (manifest_vintages) and tagging net_income basis, but wrote no test for D6
- Verification: visual (both pages rendered and read) + text layer + manifest; result: confirmed; 4 check(s)

### BDL-P4-004 - 7010 stc (Saudi Telecom) - C-7010-06 (medium)
- Defect class: mixed_basis_original_vs_restated_vintage; category: basis_restated; batch claimed: defective (arithmetic + footnote)
- Manifest: stc-2023-quarterly-history.json vs stc-2020-2023-annual-history.json
- Source file SHA-256: 2 source files (see JSON): `unavailable`, `unavailable`
- PDF page: AR2024 p73 footnote (per batch C); printed page: 73
- Caption/label: Revenue: four 2023 quarters (Q1-2024 deck comparatives) vs FY2023 "Revised" (AR2024 five-year summary)
- Column: quarterly deck columns vs FY2023 Consolidated Revised
- Unit/scale: SAR bn / SAR '000; period: FY2023
- Published value: {"quarters_sum_sar": 72340000000.0, "fy2023_sar": 71777161000.0, "gap_percent": 0.7841477597588459}
- Correct value: quarters on original basis (pre-restatement, includes later-discontinued operations) vs FY2023 restated continuing operations; sum 72.34 bn vs 71.777 bn (+0.78%)
- Restated: true; continuing operations: FY2023 figure is restated continuing operations; the quarterly set is pre-restatement; comparison source: stc AR2024 five-year summary (restated, "reclassified" footnote) vs Q1-2024 presentation (not archived); note: never publish FY and quarters of different vintages without a basis flag
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-06]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::QuarterSumTests::test_mixed_original_and_restated_basis_is_reported` - synthetic quarter data; source branch only
- Verification: manifest arithmetic + text layer of archived stc documents; result: confirmed; 2 check(s); notes: the Q1-2024 deck that supplies the quarters is not archived, so quarterly values themselves are unverified

### BDL-P4-005 - 7020 Mobily - C-7020-01 (medium)
- Defect class: mixed_vintage_original_and_restated_in_one_manifest; category: basis_restated; batch claimed: defective (proven)
- Manifest: mobily-2022-fy.json
- Source file SHA-256: `e42befe5f4129e3b6a9d6679215e0fb96349889753873b4f485525dc7f450fde` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4 and 22 (cited 12); printed page: 6 / 42
- Caption/label: Financial Highlights / Financial performance table: EBITDA 2022
- Column: FY2022 as originally reported (AR2022)
- Unit/scale: SAR million, scale 1000000; period: FY2022
- Published value: {"metric": "ebitda", "caption": "EBITDA", "value": "6179", "scale": "1000000", "period_kind": "fy", "period_start": "2022-01-01", "period_end": "2022-12-31", "manifest_page": 12}
- Correct value: 6,161 (SAR m, margin 39.3%) in the AR2022; 6,179 is the RESTATED FY2022 comparative printed in AR2023 (pdf p3 and p22; AR2023 revenue 15,717)
- Restated: true; continuing operations: not applicable; comparison source: {"document": "mobily-2023-fy (annual report 2023)", "source_file_sha256": "62cf5d09d66b28e404b1ceed630b8947496af1f2f76c6990031433bc6337ea9b", "source_file_sha256_basis": "recomputed from archived file in this worktree; equals archive-index content_hash", "pdf_pages": "3 and 22", "column": "2022 comparative (restated)", "scope": "consolidated FY2022, SAR mill ... (full value in defect-bundle.json); note: the manifest mixes original revenue 15,669 / net income with restated EBITDA 6,179
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7020.json#findings[id=C-7020-01]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7020.json`
- Pinning test: `none`
- Verification: text layer of both annual reports + manifest; result: confirmed; 6 check(s)

### BDL-P4-006 - 7202 solutions by stc - F-7202-1 (low-medium)
- Defect class: undisclosed_adjusted_comparatives; category: basis_restated; batch claimed: defective (low-medium)
- Manifest: stc-solutions-2025-fy.json
- Source file SHA-256: `287f14a69420bbc31ddb70ab916b1aef480ffe14ac951fc1622d7a0e9ab2e2ca` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 64; printed page: no printed page number detected in text layer
- Caption/label: Note 43: FY2024 balance sheet adjusted for the LABS purchase price allocation: intangibles 557,229 -> 559,813; trade payables/accruals 3,886,613 -> 3,885,729; NCI 22,034 -> 25,502
- Column: FY2024 comparative column (31 Dec 2024)
- Unit/scale: SAR '000, scale 1000; period: 2024-12-31
- Published value: published FY2024 values equal the ADJUSTED figures: intangible_assets 559,813; accounts_payable 3,885,729; noncontrolling_interests 25,502
- Correct value: values are correct as printed in the FY2025 report, but not flagged as adjusted vs the FY2024 filing (557,229 / 3,886,613 / 22,034)
- Restated: true; continuing operations: not applicable; comparison source: {"document": "stc-solutions-2025-fy (FY2025 audited FS), Note 43", "source_file_sha256": "287f14a69420bbc31ddb70ab916b1aef480ffe14ac951fc1622d7a0e9ab2e2ca", "pdf_page": 64, "scope": "consolidated, FY2024 comparative balance sheet after PPA adjustment"}; note: the originally filed FY2024 statements are not in the repo
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/7202.json#findings[id=F-7202-1]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/7202.json`; transcription `docs/audits/saudi-independent/bundle/batch2-F/f_transcripts/7202.json`
- Pinning test: `origin/claude/audit-saudi-batch2-F:tests/test_audit_batch2_f_3060_7202.py::test_7202_notes_disclose_comparative_adjustment` - strict xfail pinning the missing disclosure; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P4-007 - 2010 SABIC - 2010-D7 (medium)
- Defect class: mixed_operating_basis_unflagged; category: basis_continuing_ops; batch claimed: defective (proven)
- Manifest: sabic-2025-gap-closure.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [47] (found by bundle; batch cites printed 47); printed page: no printed page number detected in text layer
- Caption/label: petrochemicals_sales_volume
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: gap-closure: Chemicals 23.4 and Polymers 16.2 Mn t; sector-operational: 23.2 and 13.0 (basis=continuing_operations)
- Correct value: 23.4/16.2 = "TOTAL OPERATIONAL FOOTPRINT (Including discontinued operations)"; 23.2/13.0 = "Continuing operations" panel
- Restated: not recorded by batch; continuing operations: continuing vs discontinued operations panels; comparison source: same document (AR2025), pages as located
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2025-gap-closure.json].defects[2010-D7]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/2010_sabic-2025-gap-closure_pdf47.png`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 2 check(s)

## proven: group 5 - Other numeric value, mapping, sign and definition defects

### BDL-P5-001 - 1020 Bank AlJazira - D5 (high)
- Defect class: wrong_row_wrong_column_and_missing_statement; category: numeric_wrong_source_row; batch claimed: proven
- Manifest: aljazira-2008-q2.json
- Source file SHA-256: `a78ffb4406599076425915e7b33b085ea1c0185d10903894138c989b2dfcc38c` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4 (published), 3 (correct); printed page: no printed page number detected in text layer / no printed page number detected in text layer
- Caption/label: published as bank_investments; printed label on p4 is "Gain on non-trading investments, net"; correct caption "Investments" (balance sheet p3)
- Column: published: Three Months Ended June 30, 2007 (prior-year comparative) income-statement cell; correct: balance sheet 30 Jun 2008
- Unit/scale: SAR '000, scale 1000; period: 2008-06-30 (instant)
- Published value: {"metric": "bank_investments", "caption": "Gain on non-trading investments, net", "value": "13312", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2008-06-30", "manifest_page": 4}
- Correct value: 4,431,820 (balance sheet Investments, pdf p3, note 4); the 13,312 is a 2007 income-statement comparative
- Restated: false; continuing operations: not applicable; comparison source: aljazira-2008-q2 pdf p3 current-period balance sheet; note: rendered p4 shows 13,312 under "Three Months Ended June 30, 2007"
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1020.json#defects[id=D5]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1020.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1020_aljazira-2008-q2_pdf4.png`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::PluralStatementHeadingTests::test_plural_income_statement_is_read` - synthetic PDF with plural "STATEMENTS OF INCOME" heading; source branch only; does not assert the manifest
- Verification: visual (p4 rendered and read) + text layer + manifest; result: confirmed; 3 check(s)

### BDL-P5-002 - 1080 Arab National Bank (ANB) - D7 (medium)
- Defect class: wrong_metric_mapping_and_semantics; category: mapping; batch claimed: proven
- Manifest: anb-2025-annual-report.json
- Source file SHA-256: `b32c41d05bb4b2800383174f7c43ddefd5aa62c858eafb78e72c17540340df88` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 7; printed page: 10
- Caption/label: published assets_held_for_sale; printed row is "Liabilities associated with assets held for sale 39 11,358" (assets held for sale 39 250,085 not extracted)
- Column: FY2025 column
- Unit/scale: SAR '000, scale 1000; period: 2025-12-31
- Published value: [{"metric": "assets_held_for_sale", "caption": "Liabilities associated with assets held for sale", "value": "11358", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2025-12-31", "manifest_page": 7}]
- Correct value: assets_held_for_sale = 250,085 (the 11,358 is the LIABILITIES line)
- Restated: false; continuing operations: held-for-sale classification (IFRS 5); not a continuing-operations comparison; comparison source: same page
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D7]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-003 - 1120 Al Rajhi Bank - D7 (medium)
- Defect class: wrong_metric_mapping_and_semantics (equity_parent includes equity sukuk); category: mapping_semantics; batch claimed: proven
- Manifest: alrajhi-2025-fy.json
- Source file SHA-256: `67b6f23b571e6bc1171b21c620aa52f0992174d6e926d4acd97ed729a43b4a52` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 9; printed page: 1 (typed on the scanned statement image)
- Caption/label: equity_parent published = "Equity attributable to the Bank equity holders" (includes Equity sukuk); shareholders-only line is "Equity attributable to the Bank shareholders"
- Column: FY2025 (31 December 2025) column
- Unit/scale: SAR '000, scale 1000; period: 2025-12-31
- Published value: [{"metric": "equity_parent", "caption": "Equity attributable to the Bank's equity holders", "value": "142762048", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2025-12-31", "manifest_page": 9}]
- Correct value: shareholders-only equity 114,854,169 (printed row above Equity sukuk 27,907,879); 142,762,048 is shareholders + sukuk
- Restated: false; continuing operations: not applicable; comparison source: same page; note: comparability issue vs banks that publish shareholders-only equity
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1120.json#defects[id=D7]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1120.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1120_alrajhi-2025-fy_pdf9.png`
- Pinning test: `none`
- Verification: visual (scanned page rendered and read) + manifest; result: confirmed; 2 check(s)

### BDL-P5-005 - 7010 stc (Saudi Telecom) - C-7010-03 (high)
- Defect class: wrong_line_item_mapped; category: numeric_wrong_source_row; batch claimed: defective (proven)
- Manifest: stc-2025-segments-financial-notes.json
- Source file SHA-256: `7dccc9e19eb2627fd7e455fab047b79044ad893071a327f6c23eb92663c7ad21` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 129; printed page: 256-257 (spread; Note 10 roll-forward)
- Caption/label: Note 10 Property and equipment - 'Additions' row, Total column (2025 roll-forward)
- Column: published: Net book value of "Lands and buildings" at 31 Dec 2025 (last row, first column); correct: Additions row, Total column
- Unit/scale: SAR '000, scale 1000; period: FY2025
- Published value: {"metric": "ppe_additions_by_class", "caption": "Additions to property and equipment", "value": "8279660", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 129}
- Correct value: 8,235,137 (additions total = lands & buildings 90,710 + network 94,452 + other 138,210 + CWIP 7,911,765)
- Restated: false; continuing operations: FY2025 current-year roll-forward (the 2024 roll-forward carries a note that its movements include discontinued operations); comparison source: same page
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-03]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/7010_stc-2025-segments-financial-notes_pdf129.png`
- Pinning test: `none`
- Verification: visual (page rendered and read) + text layer + manifest; result: confirmed; 3 check(s)

### BDL-P5-006 - 7030 Zain KSA - C-7030-01 (medium)
- Defect class: scope_label_wrong_entity_segment_tagged_consolidated; category: scope_semantics; batch claimed: defective (proven)
- Manifest: zain-ksa-2025-notes-segments.json
- Source file SHA-256: `bee6f9b63c9d81f625abb5675852d96679bb2776b746ef6f1bf2b1e7e26d192c` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 69-70 (cited 68-69); printed page: no printed page number detected in text layer-195
- Caption/label: Note 40 Segment reporting: 'Mobile Telecommunications Company' column before eliminations
- Column: legal-entity column (before eliminations) vs Total column
- Unit/scale: SAR '000; period: FY2025 / 2025-12-31
- Published value: [{"metric": "segment_depreciation_amortization", "caption": "Zain KSA depreciation and amortization", "value": "-2153794", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 68, "scope": null}, {"metric": "segment_assets", "caption": "Mobile Telecommunications Company assets", "value": "57603795", "scale": "1000", "period_kind": "instant", "period_start":  ... (full value in defect-bundle.json)
- Correct value: consolidated: total assets 28,753,303; total liabilities 17,877,352; D&A 2,160,661 (note 40 total column)
- Restated: false; continuing operations: not applicable; comparison source: same pages, Total column
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7030.json#findings[id=C-7030-01]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7030.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 3 check(s)

### BDL-P5-007 - 7030 Zain KSA - C-7030-02 (medium)
- Defect class: derived_value_presented_as_printed; category: derived_value; batch claimed: defective (proven)
- Manifest: zain-ksa-2025-notes-segments.json
- Source file SHA-256: `bee6f9b63c9d81f625abb5675852d96679bb2776b746ef6f1bf2b1e7e26d192c` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 52; printed page: no printed page number detected in text layer
- Caption/label: 26-2: "revenue recognized from operations within KSA except international roaming and interconnect which account 14.97% (2024: 15.54%)"
- Column: FY2025
- Unit/scale: SAR '000, scale 1000; period: FY2025
- Published value: [{"metric": "revenue_by_geography", "caption": "Revenue from operations within KSA excluding international roaming and interconnect", "value": "9338850", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 51}]
- Correct value: only the percentage 14.97% is printed; no SAR amount (implied ~9,339,070 +/- rounding)
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7030.json#findings[id=C-7030-02]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7030.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 3 check(s)

### BDL-P5-008 - 7030 Zain KSA - C-7030-03 (low)
- Defect class: text_statement_encoded_as_numeric_zero; category: derived_value; batch claimed: defective (proven)
- Manifest: zain-ksa-2025-notes-segments.json
- Source file SHA-256: `bee6f9b63c9d81f625abb5675852d96679bb2776b746ef6f1bf2b1e7e26d192c` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 52; printed page: no printed page number detected in text layer
- Caption/label: 'No single customers contributed 10% or more to the Group's revenues.'
- Column: FY2025
- Unit/scale: unit pure; period: FY2025
- Published value: [{"metric": "customer_concentration", "caption": "No single customer contributed 10% or more to Group revenue", "value": "0", "scale": null, "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 51}]
- Correct value: qualitative bound ("below 10%"), not a value of zero
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7030.json#findings[id=C-7030-03]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7030.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-009 - 7040 GO Telecom - C-7040-02 (low)
- Defect class: approximate_statement_stored_as_exact_value; category: derived_value; batch claimed: defective (proven)
- Manifest: go-telecom-2021-2025-fy-history.json
- Source file SHA-256: `d76f55f907fc95a16d3fc852616c135f9a0e61d7d698e96c9ab2cc52e0ef34fe` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 22; printed page: 43
- Caption/label: "GO deployed its 5G network across 18 cities, covering over 30% of the population"
- Column: 2025-03-31
- Unit/scale: ratio; period: 2025-03-31
- Published value: [{"metric": "five_g_coverage", "caption": "5G network ... covering over 30% of the population", "value": "0.30", "scale": null, "period_kind": "instant", "period_start": null, "period_end": "2025-03-31", "manifest_page": 22}]
- Correct value: lower bound (>30%), not exactly 0.30
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7040.json#findings[id=C-7040-02]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7040.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-010 - 1120 Al Rajhi Bank - D4 (medium)
- Defect class: cash_flow_adjustment_row_mapped_to_income_metric; category: mapping_and_sign; batch claimed: proven
- Manifest: alrajhi-2024-q2.json
- Source file SHA-256: `76558c1f4730d8e186f4929500a4b53f03546c7c5ecc5be6af5c07612818c795` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [9]; printed page: ["None"]
- Caption/label: Dividend income (cash-flow reconciliation rows)
- Column: current-period column of the cash-flow statement (reconciling adjustment rows)
- Unit/scale: SAR '000, scale 1000; period: ytd to 2024-06-30
- Published value: [{"metric": "dividend_income", "caption": "Dividend income", "value": "-74037", "scale": "1000", "period_kind": "ytd", "period_start": "2024-01-01", "period_end": "2024-06-30", "manifest_page": 9}]
- Correct value: {"value": "dividend income is a positive income-statement line (+absolute value); the negative figure is the cash-flow deduction row. Statement value for this document is not recorded by the batch.", "bundle_located_absolute_value_on_other_pdf_pages": {"dividend_income": [10]}}
- Restated: false; continuing operations: not applicable; comparison source: same document income statement; note: published rows are reconciling items of the cash-flow statement (dividend income deducted; sukuk commission added back) stored under income-statement metrics
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1120.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1120.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_income_statement_metrics_are_not_read_from_cash_flow_rows` - synthetic PDF; source branch only; batch A regression shows the fixed reader no longer emits these facts for anb-2020-q1, anb-2021-q1 and alrajhi-2024-q2
- Verification: text layer + manifest (page not rendered); result: confirmed; 2 check(s)

### BDL-P5-011 - 2010 SABIC - 2010-D1 (medium)
- Defect class: definition_drift_across_periods; category: definition; batch claimed: defective (proven)
- Manifest: sabic-2025-fy.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [137] (found by bundle; batch cites printed 137 (cash flow); 42 (summary)); printed page: no printed page number detected in text layer
- Caption/label: capex
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: [{"metric": "capex", "caption": "Purchase of property, plant and equipment", "value": "-8750028", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 137}]
- Correct value: FY2025 on FY2024 basis = -8,774,805 (8,750,028 + 24,777); company-reported Capital expenditures 8.77 Bn (FY2025) / 10.20 Bn (FY2024)
- Restated: true; continuing operations: not recorded by batch; comparison source: same document (AR2025), pages as located; note: FY2024 comparative is the restated figure in AR2025 (batch D: only the restated FY2024 is retained)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2025-fy.json].defects[2010-D1]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::DefinitionDriftTests::test_capex_that_adds_intangibles_in_one_year_is_flagged` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 4 check(s)

### BDL-P5-012 - 2010 SABIC - 2010-D2 (medium)
- Defect class: definition_drift_across_periods; category: definition; batch claimed: defective (proven)
- Manifest: sabic-2025-fy.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [137] (found by bundle; batch cites printed 137); printed page: no printed page number detected in text layer
- Caption/label: proceeds_asset_sales
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: [{"metric": "proceeds_asset_sales", "caption": "Proceeds from sale of property, plant and equipment", "value": "82308", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 137}]
- Correct value: same basis: FY2025 3,688,034 or FY2024 33,343
- Restated: true; continuing operations: not recorded by batch; comparison source: same document (AR2025), pages as located; note: FY2024 comparative is the restated figure in AR2025 (batch D: only the restated FY2024 is retained)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2025-fy.json].defects[2010-D2]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::DefinitionDriftTests::test_capex_that_adds_intangibles_in_one_year_is_flagged` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 4 check(s)

### BDL-P5-013 - 2010 SABIC - 2010-D3 (low)
- Defect class: definition_drift_across_periods; category: definition; batch claimed: defective (proven)
- Manifest: sabic-2024-fy-comparative.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [136] (found by bundle; batch cites printed 136, 186/159); printed page: no printed page number detected in text layer
- Caption/label: depreciation_amortization
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: FY2025 12,762,575 (deep notes) vs FY2024 13,009,105 (cash-flow basis)
- Correct value: cash-flow basis FY2025 = 12,897,679 (11,185,373 + 1,184,728 + 527,578)
- Restated: true; continuing operations: not recorded by batch; comparison source: same document (AR2025), pages as located; note: FY2024 comparative is the restated figure in AR2025 (batch D: only the restated FY2024 is retained)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2024-fy-comparative.json].defects[2010-D3]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 3 check(s)

### BDL-P5-014 - 2010 SABIC - 2010-D4 (medium)
- Defect class: incomplete_extraction_breaks_component_sum; category: completeness; batch claimed: defective (proven)
- Manifest: sabic-2024-fy-comparative.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [132, 135] (found by bundle; batch cites printed 132); printed page: no printed page number detected in text layer
- Caption/label: equity components
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: share_capital 30,000,000 + other_reserves -4,112,475 + retained_earnings 19,581,626 = 45,469,151
- Correct value: equity_parent 156,358,183 (general reserve 110,889,032 not extracted)
- Restated: true; continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: same document (AR2025), pages as located; note: FY2024 comparative is the restated figure in AR2025 (batch D: only the restated FY2024 is retained)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2024-fy-comparative.json].defects[2010-D4]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 3 check(s)

### BDL-P5-015 - 2010 SABIC - 2010-D5 (low)
- Defect class: component_double_counted; category: numeric_composite; batch claimed: defective (proven)
- Manifest: sabic-2025-deep-financial-notes.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [184] (found by bundle; batch cites printed 184); printed page: no printed page number detected in text layer
- Caption/label: borrowings_by_instrument
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: Murabaha 15,195,578
- Correct value: 15,194,979 (13,658,398 + 998,345 + 538,236); published already contains the 599 of conventional short-term borrowings listed again as overdraft
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: same document (AR2025), pages as located
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2025-deep-financial-notes.json].defects[2010-D5]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::DimensionReconciliationTests::test_component_counted_twice_breaks_the_reconciliation` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-016 - 2010 SABIC - 2010-D6 (low)
- Defect class: derived_sum_arithmetic_error; category: numeric_composite; batch claimed: defective (proven)
- Manifest: sabic-2025-deep-financial-notes.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [201] (found by bundle; batch cites printed 201); printed page: no printed page number detected in text layer
- Caption/label: related_party_payables
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: 12,296,996
- Correct value: 12,296,896 (sum of the four printed rows; the page prints no total)
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: same document (AR2025), pages as located
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2025-deep-financial-notes.json].defects[2010-D6]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-017 - 3010 Arabian Cement - 3010-D2 (low)
- Defect class: definition_inconsistency_across_companies (capex); category: definition; batch claimed: proven (definition drift across issuers)
- Manifest: arabian-cement-2025-fy.json
- Source file SHA-256: `95310e37c7e8adf82177a557e2949da2438f240300def0cbed6b61a0be75b261` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [14]; printed page: not recorded by batch
- Caption/label: capex
- Column: FY2025 / FY2024
- Unit/scale: SAR (full riyals); period: FY2025/FY2024
- Published value: [{"metric": "capex", "caption": "Additions in property, plant and equipment + Additions in intangible assets", "value": "-94980", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 12}, {"metric": "capex", "caption": "Additions in property, plant and equipment + Additions in intangible assets", "value": "-31544", "scale": "1000", "period_kind": "fy", "peri ... (full value in defect-bundle.json)
- Correct value: label faithful to its own definition; PP&E 94,930 + intangibles 50; 3010 includes intangibles while 3030/3050 are PP&E-only
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/3010.json#sources[manifest=...].defects[3010-D2]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/3010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::DefinitionDriftTests::test_capex_that_adds_intangibles_in_one_year_is_flagged` - synthetic; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-018 - 3030 Saudi Cement - 3030-D2 (low)
- Defect class: definition_inconsistency_across_companies (capex); category: definition; batch claimed: proven (definition drift across issuers)
- Manifest: saudi-cement-2025-fy.json
- Source file SHA-256: `799306475fca27d3cf24a9300db797e973b753662f1f2fe1bda250a7b57103ab` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [10]; printed page: not recorded by batch
- Caption/label: capex
- Column: FY2025 / FY2024
- Unit/scale: SAR (full riyals); period: FY2025/FY2024
- Published value: [{"metric": "capex", "caption": "Additions to property, plant and equipment", "value": "-158704", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 9}, {"metric": "capex", "caption": "Additions to property, plant and equipment", "value": "-82031", "scale": "1000", "period_kind": "fy", "period_start": "2024-01-01", "period_end": "2024-12-31", "manifest_pag ... (full value in defect-bundle.json)
- Correct value: label faithful to its own definition; PP&E-only additions (intangible additions (12,980)/(3,811) on the same page); 3010 includes intangibles while 3030/3050 are PP&E-only
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/3030.json#sources[manifest=...].defects[3030-D2]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/3030.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::DefinitionDriftTests::test_capex_that_adds_intangibles_in_one_year_is_flagged` - synthetic; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-019 - 2010 SABIC - 2010-D8 (low)
- Defect class: mislabelled_metric; category: mapping; batch claimed: defective (proven)
- Manifest: sabic-2025-gap-closure.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [208] (found by bundle; batch cites printed 208); printed page: no printed page number detected in text layer
- Caption/label: domestic/international_revenue_chemicals
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: 18,083,824 / 98,441,390 labelled Chemicals
- Correct value: GROUP revenue by customer location (total 116,525,214), not the Chemicals segment (103,935,678)
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: same document (AR2025), pages as located
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2025-gap-closure.json].defects[2010-D8]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-020 - 3020 Yamama Cement - AUDIT-E-3020-1 (low)
- Defect class: classification: composite mixes statement positions; category: mapping; batch claimed: defective (low)
- Manifest: yamama-cement-2025-fy.json
- Source file SHA-256: `5f522341d6ad40c84c4ba13fec7de717f89c31dd93365088f382b097eea802a0` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 8; printed page: no printed page number detected in text layer
- Caption/label: Provision for expected credit loss (ECL) (above Income from main activities) + Provision for impairment of spare parts (below, under Other (expenses)/income)
- Column: FY2025
- Unit/scale: SAR (full riyals); period: FY2025
- Published value: [{"metric": "impairment_charges", "caption": "Provision for expected credit loss (ECL) + Provision for impairment of spare parts for Plants and equipment", "value": "-51987657", "scale": "1", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 6}]
- Correct value: split: ECL (20,185,882) deducted above operating income; spare-parts impairment (31,801,775) below; sum -51,987,657 fits neither bridge
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3020.json#dimension_1_numeric_correctness.defects[AUDIT-E-3020-1]`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3020.json`; transcription `docs/audits/saudi-independent/bundle/batch2-E/e_transcripts/3020.json`
- Pinning test: `origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::test_manifest_matches_page_transcription` - pins every published value to the transcription (the composite value is pinned as published, not flagged as a defect)
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-021 - 3020 Yamama Cement - AUDIT-E-3020-2 (low)
- Defect class: definition: capex omits intangibles; category: definition; batch claimed: defective (low)
- Manifest: yamama-cement-2025-fy.json
- Source file SHA-256: `5f522341d6ad40c84c4ba13fec7de717f89c31dd93365088f382b097eea802a0` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 10 (batch cites printed 8); printed page: no printed page number detected in text layer
- Caption/label: Purchase of Intangible assets (294,281 / 1,470,413) omitted from capex
- Column: FY2025 / FY2024
- Unit/scale: SAR (full riyals); period: FY2025/FY2024
- Published value: [{"metric": "capex", "caption": "Purchase of property, plant, and equipment + Additions to capital works in progress", "value": "-415983274", "scale": "1", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 8}, {"metric": "capex", "caption": "Purchase of property, plant, and equipment + Additions to capital works in progress", "value": "-983767109", "scale": "1", "period_k ... (full value in defect-bundle.json)
- Correct value: policy decision: City (2024) and Qassim include intangibles
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3020.json#dimension_1_numeric_correctness.defects[AUDIT-E-3020-2]`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3020.json`; transcription `docs/audits/saudi-independent/bundle/batch2-E/e_transcripts/3020.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-022 - 2010 SABIC - 2010-D9 (low)
- Defect class: cash_flow_cash_published_as_balance_sheet_cash; category: mapping; batch claimed: defective (proven)
- Manifest: sabic-2021-2025-five-year-financial-history.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [137] (found by bundle; batch cites printed 42 and 132/137); printed page: no printed page number detected in text layer
- Caption/label: cash
- Column: FY2025 / FY2024 as stated
- Unit/scale: SAR thousand unless stated (see published_value); period: FY2025 / FY2024
- Published value: 42.31 / 40.04 / 33.80 Bn under metric cash (cash-flow table)
- Correct value: publish as cash_end; cash-flow cash differs from balance-sheet cash (FY2025 27,950,605 vs 27,746,328)
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: same document (AR2025), pages as located
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[manifest=data/imports/sabic-2021-2025-five-year-financial-history.json].defects[2010-D9]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::` - synthetic detector tests (report-only module audit_consistency.py, source branch only); no test asserts the SABIC manifests
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-023 - 2010 SABIC - 2010-D10 (low)
- Defect class: sign_convention_inconsistent; category: sign_convention; batch claimed: defective (proven)
- Manifest: sabic-2025-deep-financial-notes.json
- Source file SHA-256: `888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: printed 133, 196, 197; printed page: not recorded by batch
- Caption/label: Zakat expense / Income tax benefit / D&A
- Column: FY2025
- Unit/scale: SAR thousand; period: FY2025
- Published value: [{"metric": "amortization_expense", "caption": "Intangible asset amortisation charge", "value": "392474", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 160}, {"metric": "depreciation_amortization", "caption": "Total depreciation and amortisation", "value": "12762575", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2 ... (full value in defect-bundle.json)
- Correct value: expenses negative as in sabic-2025-fy and sa:2082/3010/3030/3050
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2010.json#sources[...].defects[2010-D10]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2010.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 1 check(s)

### BDL-P5-027 - 1010 Riyad Bank - D8 (medium)
- Defect class: sign_convention (other_expense unsigned); category: sign_convention; batch claimed: proven
- Manifest: 37 manifests with prefix riyad-
- Source file SHA-256: 37 source files (see JSON): `b0727e848ec1`, `6f8d9435d5b1`, `c5805a1bfce2`, `3a4f0e40afa1` ...
- PDF page: not recorded by batch; printed page: not recorded by batch
- Caption/label: Other operating expenses / Other expenses
- Column: current-period column
- Unit/scale: SAR '000; period: various
- Published value: [{"manifest": "riyad-2014-fy.json", "value": "46163", "period_kind": "fy", "period_end": "2014-12-31", "page": 4, "caption": "Other operating expenses"}, {"manifest": "riyad-2014-q1.json", "value": "13280", "period_kind": "quarter", "period_end": "2014-03-31", "page": 2, "caption": "Other operating expenses"}, {"manifest": "riyad-2014-q2.json", "value": "9029", "period_kind": "quarter", "period_end": "2014-06-30", "p ... (full value in defect-bundle.json)
- Correct value: same absolute value with negative sign (every other expense metric is stored negative)
- Restated: not applicable; continuing operations: not applicable; comparison source: repo sign convention (batch E/F: outflows/expenses stored negative); note: batch A counted 72 facts across ANB/Riyad/Aljazira
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1010.json#defects[id=D8]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::OtherExpenseSignTests::test_other_operating_expenses_are_natural_negative` - synthetic PDF; source branch only
- Verification: text layer + manifest; result: confirmed; 1 check(s)

### BDL-P5-028 - 1020 Bank AlJazira - D8 (medium)
- Defect class: sign_convention (other_expense unsigned); category: sign_convention; batch claimed: proven
- Manifest: 4 manifests with prefix aljazira-
- Source file SHA-256: 4 source files (see JSON): `7045ec72af6b`, `bb90a4c79285`, `bd6b51db25cd`, `db8653ef306a`
- PDF page: not recorded by batch; printed page: not recorded by batch
- Caption/label: Other operating expenses / Other expenses
- Column: current-period column
- Unit/scale: SAR '000; period: various
- Published value: [{"manifest": "aljazira-2013-q3.json", "value": "995", "period_kind": "quarter", "period_end": "2013-09-30", "page": 4, "caption": "Other operating expenses"}, {"manifest": "aljazira-2013-q3.json", "value": "4381", "period_kind": "ytd", "period_end": "2013-09-30", "page": 4, "caption": "Other operating expenses"}, {"manifest": "aljazira-2014-q3.json", "value": "876", "period_kind": "quarter", "period_end": "2014-09-3 ... (full value in defect-bundle.json)
- Correct value: same absolute value with negative sign (every other expense metric is stored negative)
- Restated: not applicable; continuing operations: not applicable; comparison source: repo sign convention (batch E/F: outflows/expenses stored negative); note: batch A counted 72 facts across ANB/Riyad/Aljazira
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1020.json#defects[id=D8]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1020.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::OtherExpenseSignTests::test_other_operating_expenses_are_natural_negative` - synthetic PDF; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-029 - 1080 Arab National Bank (ANB) - D8 (medium)
- Defect class: sign_convention (other_expense unsigned); category: sign_convention; batch claimed: proven
- Manifest: 8 manifests with prefix anb-
- Source file SHA-256: 8 source files (see JSON): `dd647cf992a4`, `eb3df59a5c58`, `117d2f58c7e0`, `93ed25e002f4` ...
- PDF page: not recorded by batch; printed page: not recorded by batch
- Caption/label: Other operating expenses / Other expenses
- Column: current-period column
- Unit/scale: SAR '000; period: various
- Published value: [{"manifest": "anb-2004-q1.json", "value": "9250", "period_kind": "quarter", "period_end": "2004-03-31", "page": 3, "caption": "Other operating expenses"}, {"manifest": "anb-2004-q2.json", "value": "9252", "period_kind": "ytd", "period_end": "2004-06-30", "page": 3, "caption": "Other operating expenses"}, {"manifest": "anb-2004-q3.json", "value": "115", "period_kind": "quarter", "period_end": "2004-09-30", "page": 3, ... (full value in defect-bundle.json)
- Correct value: same absolute value with negative sign (every other expense metric is stored negative)
- Restated: not applicable; continuing operations: not applicable; comparison source: repo sign convention (batch E/F: outflows/expenses stored negative); note: batch A counted 72 facts across ANB/Riyad/Aljazira
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D8]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::OtherExpenseSignTests::test_other_operating_expenses_are_natural_negative` - synthetic PDF; source branch only
- Verification: text layer + manifest; result: confirmed; 1 check(s)

### BDL-P5-030 - 1150 Alinma Bank - ALN-2 (medium)
- Defect class: metric_mapping_net_published_as_gross; category: mapping; batch claimed: proven
- Manifest: alinma-2018-fy.json
- Source file SHA-256: `fe2c8548cb0621b272f4c9b1b018a7d147e01b0d36fcd4bce5aa1584b2799988` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [9]; printed page: ["3"]
- Caption/label: Income from investments and financing, net (NET line, published under gross metric financing_income)
- Column: current period (see period_kind of facts)
- Unit/scale: SAR '000, scale 1000; period: fy 2018-12-31
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing, net", "value": "3797832", "scale": "1000", "period_kind": "fy", "period_start": "2018-01-01", "period_end": "2018-12-31", "manifest_page": 9}]
- Correct value: metric should be net_financing_income (same value); gross financing_income not published: gross line printed above it on the same page, not published
- Restated: vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restat ... (full value in defect-bundle.json); continuing operations: not applicable; comparison source: XLSX supplement series publishes gross under financing_income
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2018-fy.json].defects[ALN-2]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-031 - 1150 Alinma Bank - ALN-2 (medium)
- Defect class: metric_mapping_net_published_as_gross; category: mapping; batch claimed: proven
- Manifest: alinma-2018-q3.json
- Source file SHA-256: `8eae5c4221d8d630cf02132020d89b659a654e2448c9a7ed7a40703e45b48306` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [4]; printed page: ["3"]
- Caption/label: Income from investments and financing, net (NET line, published under gross metric financing_income)
- Column: current period (see period_kind of facts)
- Unit/scale: SAR '000, scale 1000; period: ytd 2018-09-30
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing, net", "value": "987214", "scale": "1000", "period_kind": "ytd", "period_start": "2018-01-01", "period_end": "2018-09-30", "manifest_page": 4}]
- Correct value: metric should be net_financing_income (same value); gross financing_income not published: gross line printed above it on the same page, not published
- Restated: vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restat ... (full value in defect-bundle.json); continuing operations: not applicable; comparison source: XLSX supplement series publishes gross under financing_income
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2018-q3.json].defects[ALN-2]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-032 - 1150 Alinma Bank - ALN-2 (medium)
- Defect class: metric_mapping_net_published_as_gross; category: mapping; batch claimed: proven
- Manifest: alinma-2019-fy.json
- Source file SHA-256: `13a6ea5f65a40a19de042300a7eccea6d2c83c4eb14b0c61955685258ed1fef3` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [9]; printed page: ["8"]
- Caption/label: Income from investments and financing, net (NET line, published under gross metric financing_income)
- Column: current period (see period_kind of facts)
- Unit/scale: SAR '000, scale 1000; period: fy 2019-12-31
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing, net", "value": "4394459", "scale": "1000", "period_kind": "fy", "period_start": "2019-01-01", "period_end": "2019-12-31", "manifest_page": 9}]
- Correct value: metric should be net_financing_income (same value); gross financing_income not published: gross 5,608,762; return on time investments (1,214,303); net 4,394,459 (page 9)
- Restated: vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restat ... (full value in defect-bundle.json); continuing operations: not applicable; comparison source: XLSX supplement series publishes gross under financing_income
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2019-fy.json].defects[ALN-2]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only
- Verification: text layer + manifest; result: confirmed; 3 check(s)

### BDL-P5-033 - 1150 Alinma Bank - ALN-2 (medium)
- Defect class: metric_mapping_net_published_as_gross; category: mapping; batch claimed: proven
- Manifest: alinma-2020-fy.json
- Source file SHA-256: `116d48bf0a7fb01542195649ca41e7f76afb46667ee4bc74fa24018777a53e1f` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [11]; printed page: ["10"]
- Caption/label: Income from investments and financing, net (NET line, published under gross metric financing_income)
- Column: current period (see period_kind of facts)
- Unit/scale: SAR '000, scale 1000; period: fy 2020-12-31
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing, net", "value": "4647823", "scale": "1000", "period_kind": "fy", "period_start": "2020-01-01", "period_end": "2020-12-31", "manifest_page": 11}]
- Correct value: metric should be net_financing_income (same value); gross financing_income not published: gross line printed above it on the same page, not published
- Restated: vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restat ... (full value in defect-bundle.json); continuing operations: not applicable; comparison source: XLSX supplement series publishes gross under financing_income
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2020-fy.json].defects[ALN-2]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-034 - 1150 Alinma Bank - ALN-2 (medium)
- Defect class: metric_mapping_net_published_as_gross; category: mapping; batch claimed: proven
- Manifest: alinma-2020-q1.json
- Source file SHA-256: `89d71c740db890b509c6750dd9c8bda3ae33ddfd813ce35ffab00de93739b299` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [4]; printed page: ["3"]
- Caption/label: Income from investments and financing, net (NET line, published under gross metric financing_income)
- Column: current period (see period_kind of facts)
- Unit/scale: SAR '000, scale 1000; period: quarter 2020-03-31
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing, net", "value": "1121155", "scale": "1000", "period_kind": "quarter", "period_start": "2020-01-01", "period_end": "2020-03-31", "manifest_page": 4}]
- Correct value: metric should be net_financing_income (same value); gross financing_income not published: gross line printed above it on the same page, not published
- Restated: vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restat ... (full value in defect-bundle.json); continuing operations: not applicable; comparison source: XLSX supplement series publishes gross under financing_income
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2020-q1.json].defects[ALN-2]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-035 - 1150 Alinma Bank - ALN-2 (medium)
- Defect class: metric_mapping_net_published_as_gross; category: mapping; batch claimed: proven
- Manifest: alinma-2020-q2.json
- Source file SHA-256: `bdf81ec9b72d82ada659362996917cc785dd3f37c5d43db5930068b849d70640` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [4]; printed page: ["3"]
- Caption/label: Income from investments and financing, net (NET line, published under gross metric financing_income)
- Column: current period (see period_kind of facts)
- Unit/scale: SAR '000, scale 1000; period: quarter 2020-06-30; ytd 2020-06-30
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing,", "value": "1122261", "scale": "1000", "period_kind": "quarter", "period_start": "2020-04-01", "period_end": "2020-06-30", "manifest_page": 4}, {"metric": "financing_income", "caption": "Income from investments and financing,", "value": "2243416", "scale": "1000", "period_kind": "ytd", "period_start": "2020-01-01", "period_end": "2020- ... (full value in defect-bundle.json)
- Correct value: metric should be net_financing_income (same value); gross financing_income not published: gross line printed above it on the same page, not published
- Restated: vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restat ... (full value in defect-bundle.json); continuing operations: not applicable; comparison source: XLSX supplement series publishes gross under financing_income
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2020-q2.json].defects[ALN-2]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only
- Verification: text layer + manifest; result: confirmed; 4 check(s)

### BDL-P5-036 - 1150 Alinma Bank - ALN-2 (medium)
- Defect class: metric_mapping_net_published_as_gross; category: mapping; batch claimed: proven
- Manifest: alinma-2020-q3.json
- Source file SHA-256: `ebac72dd938ce0735d85c22a56f9544ccd5f51384b42218f434f1a4f081439a1` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: [4]; printed page: ["3"]
- Caption/label: Income from investments and financing, net (NET line, published under gross metric financing_income)
- Column: current period (see period_kind of facts)
- Unit/scale: SAR '000, scale 1000; period: quarter 2020-09-30; ytd 2020-09-30
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing, net", "value": "1167441", "scale": "1000", "period_kind": "quarter", "period_start": "2020-07-01", "period_end": "2020-09-30", "manifest_page": 4}, {"metric": "financing_income", "caption": "Income from investments and financing, net", "value": "3410857", "scale": "1000", "period_kind": "ytd", "period_start": "2020-01-01", "period_end" ... (full value in defect-bundle.json)
- Correct value: metric should be net_financing_income (same value); gross financing_income not published: gross line printed above it on the same page, not published
- Restated: vintage reconciler labels the line-item difference "restated_in_higher_ranked_publication" (batch B) - not a true restat ... (full value in defect-bundle.json); continuing operations: not applicable; comparison source: XLSX supplement series publishes gross under financing_income
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2020-q3.json].defects[ALN-2]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - asserts reader output on Q2-2019/FY2019 only; does not cover other periods or the manifests; source branch only
- Verification: text layer + manifest; result: confirmed; 4 check(s)

### BDL-P5-037 - 1150 Alinma Bank - ALN-3 (medium)
- Defect class: wrapped_caption_mapped_to_gross_line; category: mapping; batch claimed: proven
- Manifest: alinma-2018-q2.json
- Source file SHA-256: `a6f2b183dd7b9b30e9c1035c1aef133b37743653bc678726c1904063e525921b` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4; printed page: 3
- Caption/label: Income from investments and financing, net (caption wrapped over two rows)
- Column: quarter and ytd
- Unit/scale: SAR '000, scale 1000; period: quarter/ytd 2018-06-30
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing", "value": "1185931", "scale": "1000", "period_kind": "ytd", "period_start": "2018-01-01", "period_end": "2018-06-30", "manifest_page": 4}]
- Correct value: net line published nowhere: 942,390 / 1,838,667 (net, quarter / ytd)
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2018-q2.json].defects[ALN-3]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - Q2-2019 asserted only; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P5-038 - 1150 Alinma Bank - ALN-3 (medium)
- Defect class: wrapped_caption_mapped_to_gross_line; category: mapping; batch claimed: proven
- Manifest: alinma-2019-q2.json
- Source file SHA-256: `ae1cabb24272054a057459ed9bd8e383204a6b9036bb762cd7a5881aa2a95c11` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4; printed page: 3
- Caption/label: Income from investments and financing, net (caption wrapped over two rows)
- Column: quarter and ytd
- Unit/scale: SAR '000, scale 1000; period: quarter/ytd 2019-06-30
- Published value: [{"metric": "financing_income", "caption": "Income from investments and financing", "value": "1378495", "scale": "1000", "period_kind": "quarter", "period_start": "2019-04-01", "period_end": "2019-06-30", "manifest_page": 4}, {"metric": "financing_income", "caption": "Income from investments and financing", "value": "2685608", "scale": "1000", "period_kind": "ytd", "period_start": "2019-01-01", "period_end": "2019-06 ... (full value in defect-bundle.json)
- Correct value: net line published nowhere: 1,079,559 / 2,072,658 (net, quarter / ytd)
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-2019-q2.json].defects[ALN-3]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `origin/claude/audit-saudi-batch1-B:tests/test_audit_alinma_interim_columns.py::test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined` - Q2-2019 asserted only; source branch only
- Verification: text layer + manifest; result: confirmed; 3 check(s)

## proven: group 6 - Provenance and metadata defects (page citations, filed_at, scanned/digital tags)

### BDL-P6-001 - 7010 stc (Saudi Telecom) - C-7010-05 (low)
- Defect class: page_reference_wrong_or_other_document; category: provenance_page; batch claimed: defective (proven)
- Manifest: stc-2025-segments-financial-notes.json; stc-2025-fy.json; stc-2024-operating-kpis.json; stc-2025-operating-kpis.json; stc-2021-2023-network-kpis.json
- Source file SHA-256: `7dccc9e19eb2627fd7e455fab047b79044ad893071a327f6c23eb92663c7ad21` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: cited pages differ from printed pages (see published_value); printed page: not applicable (page-citation defect, value not in question)
- Caption/label: (many)
- Column: not applicable (page-citation defect, value not in question)
- Unit/scale: not applicable (page-citation defect, value not in question); period: FY2025 / FY2024
- Published value: [{"metric": "revenue_by_product", "value": "63312089", "cited_page": 143, "actually_on_pdf_pages": [144]}, {"metric": "remaining_performance_obligations", "value": "5360000", "cited_page": 143, "actually_on_pdf_pages": []}, {"metric": "deferred_tax_expense", "value": "-23000", "cited_page": 143, "actually_on_pdf_pages": []}, {"metric": "finance_cost_by_type", "value": "399420", "cited_page": 144, "actually_on_pdf_pag ... (full value in defect-bundle.json)
- Correct value: cited page = the pdf page that carries the value; use PDF page numbers and keep printed pages in metadata
- Restated: not applicable (page-citation defect, value not in question); continuing operations: not applicable (page-citation defect, value not in question); comparison source: not applicable (page-citation defect, value not in question)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-05]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::ProvenanceTests::test_adjacent_page_is_a_page_offset_and_distant_page_is_wrong_page` - synthetic page text; the scanner is on the source branch only
- Verification: text layer + manifest; result: confirmed; 1 check(s)

### BDL-P6-002 - 7020 Mobily - C-7020-02 (low)
- Defect class: page_reference_wrong; category: provenance_page; batch claimed: defective (proven)
- Manifest: mobily-2022-fy / 2023-fy / 2023-q1 / 2025-fy / 2025-deep-financial-notes / 2025-issuer-expansion
- Source file SHA-256: `e42befe5f4129e3b6a9d6679215e0fb96349889753873b4f485525dc7f450fde` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: see published_value; printed page: not applicable (page-citation defect, value not in question)
- Caption/label: (many)
- Column: not applicable (page-citation defect, value not in question)
- Unit/scale: not applicable (page-citation defect, value not in question); period: various
- Published value: [{"manifest": "mobily-2022-fy", "pdf_pages": 99, "facts_citing_page_beyond_pdf": 0, "total_facts": 3}, {"manifest": "mobily-2023-fy", "pdf_pages": 107, "facts_citing_page_beyond_pdf": 0, "total_facts": 3}, {"manifest": "mobily-2023-q1", "pdf_pages": 17, "facts_citing_page_beyond_pdf": 0, "total_facts": 3}, {"manifest": "mobily-2025-fy", "pdf_pages": 144, "facts_citing_page_beyond_pdf": 0, "total_facts": 48}, {"manife ... (full value in defect-bundle.json)
- Correct value: PDF page numbers; printed numbers kept in metadata (deep notes use printed spread numbers: pdf = (printed+2)/2)
- Restated: not applicable (page-citation defect, value not in question); continuing operations: not applicable (page-citation defect, value not in question); comparison source: not applicable (page-citation defect, value not in question)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7020.json#findings[id=C-7020-02]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7020.json`
- Pinning test: `origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::ProvenanceTests::test_summary_and_dominant_offset` - synthetic; source branch only
- Verification: page counts + text layer; result: confirmed; 2 check(s)

### BDL-P6-003 - 7203 Elm - C-7203-02 (low)
- Defect class: page_reference_printed_not_pdf; category: provenance_page; batch claimed: defective (documented in manifest notes)
- Manifest: elm-2025-fy.json
- Source file SHA-256: `363810a1a59f0d824d5c053286e35900c0bd4092b22807a125003cddb0c11600` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: cited [6, 7, 8, 10]; actual PDF 8,9,10,12; printed page: cited printed pages
- Caption/label: (all facts)
- Column: not applicable (page-citation defect, value not in question)
- Unit/scale: not applicable (page-citation defect, value not in question); period: FY2025/FY2024
- Published value: 136 facts cite printed page numbers
- Correct value: PDF page numbers (offset +2)
- Restated: not applicable (page-citation defect, value not in question); continuing operations: not applicable (page-citation defect, value not in question); comparison source: not applicable (page-citation defect, value not in question)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7203.json#findings[id=C-7203-02]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7203.json`
- Pinning test: `none`
- Verification: manifest + PDF length; result: confirmed; 1 check(s)

### BDL-P6-005 - 3010 Arabian Cement - 3010-D1 (low)
- Defect class: metadata_filed_at_is_board_approval_date; category: metadata_filed_at; batch claimed: proven
- Manifest: arabian-cement-2025-fy.json
- Source file SHA-256: `95310e37c7e8adf82177a557e2949da2438f240300def0cbed6b61a0be75b261` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest header filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-02-15"}
- Correct value: first public on Saudi Exchange 2026-02-23 (upload date embedded in the fsPdf URL)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/3010.json#sources[manifest=data/imports/arabian-cement-2025-fy.json].defects[3010-D1]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/3010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::FilingDateTests::test_board_approval_date_before_upload_is_flagged` - synthetic; source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-006 - 3030 Saudi Cement - 3030-D1 (low)
- Defect class: metadata_filed_at_is_board_approval_date; category: metadata_filed_at; batch claimed: proven
- Manifest: saudi-cement-2025-fy.json
- Source file SHA-256: `799306475fca27d3cf24a9300db797e973b753662f1f2fe1bda250a7b57103ab` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest header filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-03-09"}
- Correct value: first public on Saudi Exchange 2026-03-16 (upload date embedded in the fsPdf URL)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/3030.json#sources[manifest=data/imports/saudi-cement-2025-fy.json].defects[3030-D1]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/3030.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::FilingDateTests::test_board_approval_date_before_upload_is_flagged` - synthetic; source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-007 - 3050 Southern Province Cement - 3050-D1 (low)
- Defect class: metadata_filed_at_is_board_approval_date; category: metadata_filed_at; batch claimed: proven
- Manifest: southern-province-cement-2025-fy.json
- Source file SHA-256: `25c47e79e1906fafa75c4b40f84c260ec662059feb1c5668b62e0b44fcf09acb` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest header filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-03-30"}
- Correct value: first public on Saudi Exchange 2026-04-07 (upload date embedded in the fsPdf URL)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/3050.json#sources[manifest=data/imports/southern-province-cement-2025-fy.json].defects[3050-D1]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/3050.json`
- Pinning test: `origin/claude/audit-saudi-batch1-D:tests/test_audit_consistency.py::FilingDateTests::test_board_approval_date_before_upload_is_flagged` - synthetic; source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-008 - Saudi Exchange fsPdf manifests (all symbols) multiple companies (see published_value) - META-FILED-AT-ALL (medium-low)
- Defect class: filed_at earlier than Saudi Exchange upload date (repo-wide scan re-run by bundle); category: metadata_filed_at; batch claimed: proven (11 of 12 per batch E)
- Manifest: 11 of 13 manifests whose source_url carries an upload timestamp
- Source file SHA-256: 11 source files (see JSON): `95310e37c7e8`, `6958b51f874c`, `363810a1a59f`, `759a24ad88cd` ...
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: not applicable (metadata field, not a reported amount)
- Published value: [{"manifest": "arabian-cement-2025-fy.json", "symbol": "3010", "filed_at": "2026-02-15", "url_upload_date": "2026-02-23", "filed_at_basis": null}, {"manifest": "city-cement-2025-fy.json", "symbol": "3003", "filed_at": "2026-03-16", "url_upload_date": "2026-03-24", "filed_at_basis": null}, {"manifest": "elm-2025-fy.json", "symbol": "7203", "filed_at": "2026-02-26", "url_upload_date": "2026-03-05", "filed_at_basis": nu ... (full value in defect-bundle.json)
- Correct value: filed_at >= publication/audit-report date
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/batch2-E-summary.md#summary + tools/e_filed_at_check.py (re-implemented by bundle)`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/batch2-E-summary.md`
- Pinning test: `origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication` - strict xfail covering the five Group-E manifests only
- Verification: manifest scan; result: confirmed; 1 check(s)

### BDL-P6-009 - 3002 Najran Cement - AUDIT-E-META-1-3002 (medium-low)
- Defect class: metadata / point-in-time (filed_at = Board approval date); category: metadata_filed_at; batch claimed: proven
- Manifest: najran-cement-2025-fy.json
- Source file SHA-256: `759a24ad88cd92b8c6c5c0d59299024ff321a3cd296787ba39bd7443819b9167` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-03-29"}
- Correct value: on or after the Saudi Exchange publication date 2026-04-06 (and, for 3002, the 6 April 2026 audit-opinion date)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3002.json#dimension_1_numeric_correctness.defects[AUDIT-E-META-1-3002]`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3002.json`; transcription `docs/audits/saudi-independent/bundle/batch2-E/e_transcripts/3002.json`
- Pinning test: `origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication` - strict xfail parametrised over the five manifests: flips to a failure once filed_at is fixed (marker must then be removed); source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-010 - 3003 City Cement - AUDIT-E-META-1-3003 (medium-low)
- Defect class: metadata / point-in-time (filed_at = Board approval date); category: metadata_filed_at; batch claimed: proven
- Manifest: city-cement-2025-fy.json
- Source file SHA-256: `6958b51f874c338076467a8c7bac0e93f7a3aa13b944206be95bc6f3025127cd` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-03-16"}
- Correct value: on or after the Saudi Exchange publication date 2026-03-24 (and, for 3002, the 6 April 2026 audit-opinion date)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3003.json#dimension_1_numeric_correctness.defects[AUDIT-E-META-1-3003]`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3003.json`; transcription `docs/audits/saudi-independent/bundle/batch2-E/e_transcripts/3003.json`
- Pinning test: `origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication` - strict xfail parametrised over the five manifests: flips to a failure once filed_at is fixed (marker must then be removed); source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-011 - 3005 Umm Al-Qura Cement - AUDIT-E-META-1-3005 (medium-low)
- Defect class: metadata / point-in-time (filed_at = Board approval date); category: metadata_filed_at; batch claimed: proven
- Manifest: umm-al-qura-cement-2025-fy.json
- Source file SHA-256: `c1c7da561e2bcdec8cc3e8a8a116389c7e0799a58b3ca5edcfd74c9fa0848c67` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-03-12"}
- Correct value: on or after the Saudi Exchange publication date 2026-03-17 (and, for 3002, the 6 April 2026 audit-opinion date)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3005.json#dimension_1_numeric_correctness.defects[AUDIT-E-META-1-3005]`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3005.json`; transcription `docs/audits/saudi-independent/bundle/batch2-E/e_transcripts/3005.json`
- Pinning test: `origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication` - strict xfail parametrised over the five manifests: flips to a failure once filed_at is fixed (marker must then be removed); source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-012 - 3020 Yamama Cement - AUDIT-E-META-1-3020 (medium-low)
- Defect class: metadata / point-in-time (filed_at = Board approval date); category: metadata_filed_at; batch claimed: proven
- Manifest: yamama-cement-2025-fy.json
- Source file SHA-256: `5f522341d6ad40c84c4ba13fec7de717f89c31dd93365088f382b097eea802a0` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-02-16"}
- Correct value: on or after the Saudi Exchange publication date 2026-02-25 (and, for 3002, the 6 April 2026 audit-opinion date)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3020.json#dimension_1_numeric_correctness.defects[AUDIT-E-META-1-3020]`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3020.json`; transcription `docs/audits/saudi-independent/bundle/batch2-E/e_transcripts/3020.json`
- Pinning test: `origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication` - strict xfail parametrised over the five manifests: flips to a failure once filed_at is fixed (marker must then be removed); source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-013 - 3040 Qassim Cement - AUDIT-E-META-1-3040 (medium-low)
- Defect class: metadata / point-in-time (filed_at = Board approval date); category: metadata_filed_at; batch claimed: proven
- Manifest: qassim-cement-2025-fy.json
- Source file SHA-256: `17ca838773025846d9b502f6f78c2bfbabcf18463c9399c37d5eea62b8308aa1` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-02-16"}
- Correct value: on or after the Saudi Exchange publication date 2026-02-25 (and, for 3002, the 6 April 2026 audit-opinion date)
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3040.json#dimension_1_numeric_correctness.defects[AUDIT-E-META-1-3040]`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3040.json`; transcription `docs/audits/saudi-independent/bundle/batch2-E/e_transcripts/3040.json`
- Pinning test: `origin/claude/audit-saudi-batch2-E:tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication` - strict xfail parametrised over the five manifests: flips to a failure once filed_at is fixed (marker must then be removed); source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-014 - 3060 Yanbu Cement - F-3060-2 (medium-low)
- Defect class: filed_at_semantics (Board approval date); category: metadata_filed_at; batch claimed: defective
- Manifest: yanbu-cement-2025-fy.json
- Source file SHA-256: `7aa24367df35cb17de610dc6b94d1d0be084c710ad44eb5a1f6cb3cf607343b9` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-03-03"}
- Correct value: on or after the audit-report date and the Saudi Exchange upload date 2026-03-11
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/3060.json#findings[id=F-3060-2]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/3060.json`; transcription `docs/audits/saudi-independent/bundle/batch2-F/f_transcripts/3060.json`
- Pinning test: `origin/claude/audit-saudi-batch2-F:tests/test_audit_batch2_f_3060_7202.py::test_filed_at_not_before_publication` - strict xfail for both manifests; source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-015 - 7202 solutions by stc - F-7202-2 (medium-low)
- Defect class: filed_at_semantics (Board approval date); category: metadata_filed_at; batch claimed: defective
- Manifest: stc-solutions-2025-fy.json
- Source file SHA-256: `287f14a69420bbc31ddb70ab916b1aef480ffe14ac951fc1622d7a0e9ab2e2ca` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: manifest.filed_at
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: FY2025
- Published value: {"filed_at": "2026-02-15"}
- Correct value: on or after the audit-report date and the Saudi Exchange upload date 2026-02-23
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/7202.json#findings[id=F-7202-2]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/7202.json`; transcription `docs/audits/saudi-independent/bundle/batch2-F/f_transcripts/7202.json`
- Pinning test: `origin/claude/audit-saudi-batch2-F:tests/test_audit_batch2_f_3060_7202.py::test_filed_at_not_before_publication` - strict xfail for both manifests; source branch only
- Verification: manifest + URL stamp; result: confirmed; 1 check(s)

### BDL-P6-016 - 2082 ACWA Power - 2082-D2 (low)
- Defect class: metadata_filed_at_inferred; category: metadata_filed_at; batch claimed: proven
- Manifest: acwa-2026-q2.json
- Source file SHA-256: `90a94668088c628e9e6f96cece87c7eb51e56635870a40bb31ff4788c0530c0e` (archive-index.json content_hash only; file bytes NOT available offline in this worktree or any local ref (not re-hashed))
- PDF page: not recorded by batch; printed page: not applicable (metadata field, not a reported amount)
- Caption/label: not applicable (metadata field, not a reported amount)
- Column: not applicable (metadata field, not a reported amount)
- Unit/scale: not applicable (metadata field, not a reported amount); period: not applicable (metadata field, not a reported amount)
- Published value: {"filed_at": "2026-08-06", "filed_at_basis": "pdf_creation_metadata", "filed_at_confidence": "inferred", "filed_at_note": "The issuer document did not expose a machine-readable publication timestamp; this date is retained from the PDF metadata and is not an exchange filing time."}
- Correct value: filing date from a verifiable publication stamp
- Restated: not applicable (metadata field, not a reported amount); continuing operations: not applicable (metadata field, not a reported amount); comparison source: not applicable (metadata field, not a reported amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2082.json#sources[manifest=acwa-2026-q2.json].defects[2082-D2]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2082.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 1 check(s)

### BDL-P6-017 - 3060 Yanbu Cement - F-3060-1 (low)
- Defect class: provenance_description_wrong (statements tagged scanned); category: provenance_tag; batch claimed: defective (low)
- Manifest: yanbu-cement-2025-fy.json
- Source file SHA-256: `7aa24367df35cb17de610dc6b94d1d0be084c710ad44eb5a1f6cb3cf607343b9` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 6-10 (statements), 3-5 (auditor report scanned); printed page: not applicable (provenance text, no amount)
- Caption/label: manifest notes / reader tag / archive-index capture_method
- Column: not applicable (provenance text, no amount)
- Unit/scale: not applicable (provenance text, no amount); period: FY2025
- Published value: statements described as scanned images
- Correct value: PDF pp6-10 carry a full born-digital text layer; only the auditor report pp3-5 is scanned
- Restated: not applicable (provenance text, no amount); continuing operations: not applicable (provenance text, no amount); comparison source: not applicable (provenance text, no amount)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/3060.json#findings[id=F-3060-1]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/3060.json`; transcription `docs/audits/saudi-independent/bundle/batch2-F/f_transcripts/3060.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 3 check(s)

## proven: group 7 - Completeness, coverage and source-availability defects

### BDL-P7-001 - 1010 Riyad Bank - D9 (medium)
- Defect class: document_completeness_label_gaps; category: completeness; batch claimed: proven
- Manifest: 38 manifests (see published_value)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: per entry; printed page: per entry
- Caption/label: lines present on statement pages but not published (cash-flow subtotals, financing income, fees, impairments...)
- Column: not applicable (completeness gap, nothing published to compare)
- Unit/scale: not applicable (completeness gap, nothing published to compare); period: per document
- Published value: not published: 183 (metric, document) pairs
- Correct value: [{"manifest": "riyad-2014-fy.json", "metric": "operating_cash_flow", "pdf_page": 7, "printed_caption": "Net cash from (used in) operating activities", "printed_values": ["10,549,393", "(818,044)"], "manifest_has_metric": false, "label_on_page": true, "value_on_page": true}, {"manifest": "riyad-2014-fy.json", "metric": "financing_cash_flow", "pdf_page": 7, "printed_caption": "Net cash (used in) from financing activiti ... (full value in defect-bundle.json)
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1010.json#defects[id=D9]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1010.json`
- Pinning test: `none`
- Verification: text layer + manifest (re-run of the batch method); result: confirmed; 1 check(s)

### BDL-P7-002 - 1020 Bank AlJazira - D9 (medium)
- Defect class: document_completeness_label_gaps; category: completeness; batch claimed: proven
- Manifest: 6 manifests (see published_value)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: per entry; printed page: per entry
- Caption/label: lines present on statement pages but not published (cash-flow subtotals, financing income, fees, impairments...)
- Column: not applicable (completeness gap, nothing published to compare)
- Unit/scale: not applicable (completeness gap, nothing published to compare); period: per document
- Published value: not published: 53 (metric, document) pairs
- Correct value: [{"manifest": "aljazira-2008-q2.json", "metric": "operating_cash_flow", "pdf_page": 7, "printed_caption": "Net cash used in operating activities", "printed_values": ["(927,427)", "(180,702)"], "manifest_has_metric": false, "label_on_page": true, "value_on_page": true}, {"manifest": "aljazira-2008-q2.json", "metric": "cash_end", "pdf_page": 7, "printed_caption": "Other real estate, net Cash and cash equivalents at the ... (full value in defect-bundle.json)
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1020.json#defects[id=D9]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1020.json`
- Pinning test: `none`
- Verification: text layer + manifest (re-run of the batch method); result: confirmed; 1 check(s)

### BDL-P7-003 - 1080 Arab National Bank (ANB) - D9 (medium)
- Defect class: document_completeness_label_gaps; category: completeness; batch claimed: proven
- Manifest: 77 manifests (see published_value)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: per entry; printed page: per entry
- Caption/label: lines present on statement pages but not published (cash-flow subtotals, financing income, fees, impairments...)
- Column: not applicable (completeness gap, nothing published to compare)
- Unit/scale: not applicable (completeness gap, nothing published to compare); period: per document
- Published value: not published: 293 (metric, document) pairs
- Correct value: [{"manifest": "anb-2003-q2.json", "metric": "operating_cash_flow", "pdf_page": 5, "printed_caption": "Net cash used in operating activities", "printed_values": ["(736,921)", "(731,098)"], "manifest_has_metric": false, "label_on_page": true, "value_on_page": true}, {"manifest": "anb-2003-q2.json", "metric": "investing_cash_flow", "pdf_page": 5, "printed_caption": "Net cash (used in) from investing activities", "printe ... (full value in defect-bundle.json)
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D9]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `none`
- Verification: text layer + manifest (re-run of the batch method); result: confirmed; 1 check(s)

### BDL-P7-004 - 1140 Bank Albilad - D9 (medium)
- Defect class: document_completeness_label_gaps; category: completeness; batch claimed: proven
- Manifest: 29 manifests (see published_value)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: per entry; printed page: per entry
- Caption/label: lines present on statement pages but not published (cash-flow subtotals, financing income, fees, impairments...)
- Column: not applicable (completeness gap, nothing published to compare)
- Unit/scale: not applicable (completeness gap, nothing published to compare); period: per document
- Published value: not published: 149 (metric, document) pairs
- Correct value: [{"manifest": "albilad-2011-fy.json", "metric": "cash_end", "pdf_page": 25, "printed_caption": "Cash and cash equivalents at end of the year", "printed_values": ["24", "9,007,824", "3,841,864"], "manifest_has_metric": false, "label_on_page": true, "value_on_page": true}, {"manifest": "albilad-2011-fy.json", "metric": "cash_beginning", "pdf_page": 25, "printed_caption": "Cash and cash equivalents at beginning of the y ... (full value in defect-bundle.json)
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1140.json#defects[id=D9]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1140.json`
- Pinning test: `none`
- Verification: text layer + manifest (re-run of the batch method); result: confirmed; 1 check(s)

### BDL-P7-005 - 1120 Al Rajhi Bank - D11 (medium)
- Defect class: coverage_and_completeness; category: completeness; batch claimed: proven
- Manifest: alrajhi-2025-fy.json
- Source file SHA-256: `67b6f23b571e6bc1171b21c620aa52f0992174d6e926d4acd97ed729a43b4a52` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 9; printed page: 1
- Caption/label: Total assets 1,043,268,297 / 972,444,354 (FY2024 comparatives, net fee income, equity sukuk not published)
- Column: FY2024 comparative column
- Unit/scale: SAR '000; period: FY2024
- Published value: FY2024 comparatives, net_fee_income (5,869,207), equity sukuk (27,907,879) and shareholders equity (114,854,169) not published
- Correct value: printed on the same pages of the same document
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1120.json#defects[id=D11]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1120.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/1120_alrajhi-2025-fy_pdf9.png`
- Pinning test: `none`
- Verification: visual (page 9) + manifest; result: confirmed; 3 check(s)

### BDL-P7-006 - 1020 Bank AlJazira - D5 (medium)
- Defect class: missing_statement (income statement not extracted; same plural-heading cause); category: completeness; batch claimed: listed under D5 (statement missing)
- Manifest: aljazira-2008-q3.json
- Source file SHA-256: `60e460bef3499143e2f4e7fabc14eab5826208f519d7f4ecf1ea8dd9132a016c` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 4; printed page: no printed page number detected in text layer
- Caption/label: CONSOLIDATED STATEMENTS OF INCOME (plural heading not an anchor)
- Column: three/nine months
- Unit/scale: SAR '000; period: 2008-09-30
- Published value: no bank_investments fact; no income-statement facts
- Correct value: income statement facts present on p4
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1020.json#defects[id=D5]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1020.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::PluralStatementHeadingTests::test_plural_headings_are_recognised` - synthetic; source branch only
- Verification: text layer + manifest; result: confirmed; 2 check(s)

### BDL-P7-007 - 1030 Saudi Investment Bank (SAIB) - P3-STALE (medium)
- Defect class: stale_catalog_exclusion_pillar3; category: completeness_stale_reader; batch claimed: proven
- Manifest: 19 Pillar 3 manifests
- Source file SHA-256: 19 source files (see JSON): `c10ad4105fab`, `a2f6188faabb`, `b8f8336839bd`, `c5c8c5ce7d33` ...
- PDF page: KM1 template; printed page: not applicable (completeness gap)
- Caption/label: CET1 amount, Tier 1 amount, leverage exposure/ratio, HQLA, net cash outflow, LCR, available/required stable funding, NSFR
- Column: per disclosure date
- Unit/scale: as printed; period: per document
- Published value: [{"manifest": "saib-2024-05-pillar-3-workbook-pillar3.json", "excluded_catalog_field_missing": 50, "published": 4}, {"manifest": "saib-2024-08-saib-pillar-3-q2-2024-pillar3.json", "excluded_catalog_field_missing": 50, "published": 4}, {"manifest": "saib-2024-11-pillar-3-disclosure-q3-2024-pillar3.json", "excluded_catalog_field_missing": 50, "published": 4}, {"manifest": "saib-2025-04-pillar-3-workbook-dec-31-2024-pil ... (full value in defect-bundle.json)
- Correct value: publishable with the current reader (batch B dry run: SAIB 132 -> 446 facts, SNB 72 -> 247; Alinma unchanged 400)
- Restated: not applicable (completeness gap); continuing operations: not applicable (completeness gap); comparison source: not applicable (completeness gap)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1030.json#sources[*].defects[P3-STALE]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1030.json`
- Pinning test: `none`
- Verification: manifest excluded_facts (published side only; dry-run delta taken from batch B p3-regeneration-dryrun-batch1-B.json, not re-run); result: confirmed; 1 check(s)

### BDL-P7-008 - 1180 Saudi National Bank (SNB) - P3-STALE (medium)
- Defect class: stale_catalog_exclusion_pillar3; category: completeness_stale_reader; batch claimed: proven
- Manifest: 9 Pillar 3 manifests
- Source file SHA-256: 9 source files (see JSON): `f1231091a312`, `4e03ee3c6159`, `4d3b5bcc7c02`, `3d165a484055` ...
- PDF page: KM1 template; printed page: not applicable (completeness gap)
- Caption/label: CET1 amount, Tier 1 amount, leverage exposure/ratio, HQLA, net cash outflow, LCR, available/required stable funding, NSFR
- Column: per disclosure date
- Unit/scale: as printed; period: per document
- Published value: [{"manifest": "snb-2023-q1-pillar3.json", "excluded_catalog_field_missing": 45, "published": 20}, {"manifest": "snb-2024-q2-pillar3.json", "excluded_catalog_field_missing": 35, "published": 8}, {"manifest": "snb-2024-q4-pillar3.json", "excluded_catalog_field_missing": 50, "published": 4}, {"manifest": "snb-2025-q1-pillar3.json", "excluded_catalog_field_missing": 50, "published": 4}, {"manifest": "snb-2025-q2-pillar3. ... (full value in defect-bundle.json)
- Correct value: publishable with the current reader (batch B dry run: SAIB 132 -> 446 facts, SNB 72 -> 247; Alinma unchanged 400)
- Restated: not applicable (completeness gap); continuing operations: not applicable (completeness gap); comparison source: not applicable (completeness gap)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1180.json#sources[*].defects[P3-STALE]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1180.json`
- Pinning test: `none`
- Verification: manifest excluded_facts (published side only; dry-run delta taken from batch B p3-regeneration-dryrun-batch1-B.json, not re-run); result: confirmed; 1 check(s)

### BDL-P7-009 - 2222 Saudi Aramco - ARA-UNVERIFIED (medium)
- Defect class: source_documents_not_archived (11+ manifests unverified); category: source_not_archived; batch claimed: unverified
- Manifest: 19 manifests (see published_value)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (source file missing)
- Caption/label: not applicable (source file missing)
- Column: not applicable (source file missing)
- Unit/scale: not applicable (source file missing); period: not applicable (source file missing)
- Published value: ["aramco-2019-fy-historical.json", "aramco-2020-fy-historical.json", "aramco-2021-annual-metrics.json", "aramco-2021-fy-historical.json", "aramco-2022-annual-metrics.json", "aramco-2022-fy-historical.json", "aramco-2023-annual-metrics.json", "aramco-2023-fy.json", "aramco-2024-annual-metrics.json", "aramco-2024-full-notes-comparative.json", "aramco-2024-fy-comparative.json", "aramco-2025-deep-dimensional-notes.json", ... (full value in defect-bundle.json)
- Correct value: cannot be established: archived source PDFs for Aramco FY2019-FY2024, FY2025 full/notes and 2026 interims are absent from every local ref
- Restated: not applicable (source file missing); continuing operations: not applicable (source file missing); comparison source: not applicable (source file missing)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/2222.json#sources[*].numeric_correctness=unverified`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/2222.json`
- Pinning test: `none`
- Verification: archive-index + filesystem; result: confirmed; 1 check(s)

### BDL-P7-010 - 7010 stc (Saudi Telecom) - C-7010-08 (medium)
- Defect class: source_not_archived; category: source_not_archived; batch claimed: unverified
- Manifest: stc-2026-q2.json
- Source file SHA-256: `0f09bdc60326169636537a58f078496bd58aeefc5c733380b54de6db2784d7b0` (archive-index.json content_hash only; file bytes NOT available offline in this worktree or any local ref (not re-hashed))
- PDF page: not recorded by batch; printed page: not applicable (source file missing)
- Caption/label: 15 H1-2026 facts
- Column: ytd six months
- Unit/scale: 1e6; period: H1 2026 (ytd to 2026-06-30)
- Published value: 15 facts, not verifiable
- Correct value: n/a
- Restated: not applicable (source file missing); continuing operations: not applicable (source file missing); comparison source: not applicable (source file missing)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-08]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`
- Pinning test: `none`
- Verification: filesystem + archive-index; result: confirmed; 1 check(s)

### BDL-P7-012 - 7040 GO Telecom - C-7040-01 (medium)
- Defect class: document_completeness_multi_year_lines_not_extracted; category: completeness; batch claimed: defective (proven)
- Manifest: go-telecom-2021-2025-fy-history.json
- Source file SHA-256: `d76f55f907fc95a16d3fc852616c135f9a0e61d7d698e96c9ab2cc52e0ef34fe` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 31, 32, 33, 35; printed page: not applicable (completeness gap, nothing published to compare)
- Caption/label: total operating expenses, total comprehensive income, cost of services, other income, investing/financing cash flows, segment revenue split (FY2021-FY2024)
- Column: five fiscal-year columns
- Unit/scale: SAR; period: FY2021-FY2024 (years ending 31 March)
- Published value: not published for FY2021-FY2024
- Correct value: printed on the cited pages of the Board report
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7040.json#findings[id=C-7040-01]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7040.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 3 check(s)

### BDL-P7-013 - 7203 Elm - C-7203-01 (low)
- Defect class: missing_field_eps_basic; category: completeness; batch claimed: defective (proven)
- Manifest: elm-2025-fy.json
- Source file SHA-256: `363810a1a59f0d824d5c053286e35900c0bd4092b22807a125003cddb0c11600` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 8; printed page: 6
- Caption/label: Earnings per share from net profit attributable to equity holders of the parent: Basic / Diluted
- Column: FY2025 / FY2024
- Unit/scale: SAR per share; period: FY2025 / FY2024
- Published value: [{"metric": "eps_diluted", "caption": "Earnings per share - Diluted", "value": "26.80", "scale": null, "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 6}, {"metric": "eps_diluted", "caption": "Earnings per share - Diluted", "value": "23.44", "scale": null, "period_kind": "fy", "period_start": "2024-01-01", "period_end": "2024-12-31", "manifest_page": 6}, "eps_basic: abs ... (full value in defect-bundle.json)
- Correct value: Basic 26.86 (2025) / 23.51 (2024)
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7203.json#findings[id=C-7203-01]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7203.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/7203_elm-2025-fy_pdf8.png`
- Pinning test: `none`
- Verification: visual + manifest; result: confirmed; 2 check(s)

### BDL-P7-014 - 7203 Elm - C-7203-03 (medium)
- Defect class: coverage_only_two_fiscal_years; category: coverage; batch claimed: defective (coverage)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s) for 7203: ['elm-2025-fy.json']
- Correct value: FY2022-FY2023 annuals, interims, price history
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7203.json#findings[id=C-7203-03]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7203.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

### BDL-P7-015 - 2082 ACWA Power - 2082-D1 (medium)
- Defect class: archive_reference_without_file; category: source_not_archived; batch claimed: blocked
- Manifest: acwa-2026-q2.json
- Source file SHA-256: `90a94668088c628e9e6f96cece87c7eb51e56635870a40bb31ff4788c0530c0e` (archive-index.json content_hash only; file bytes NOT available offline in this worktree or any local ref (not re-hashed))
- PDF page: not recorded by batch; printed page: not applicable (source file missing)
- Caption/label: all published Q2-2026 facts
- Column: not applicable (source file missing)
- Unit/scale: not applicable (source file missing); period: Q2 2026
- Published value: 39 facts
- Correct value: unverifiable until the file is re-archived
- Restated: not applicable (source file missing); continuing operations: not applicable (source file missing); comparison source: not applicable (source file missing)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2082.json#sources[manifest=acwa-2026-q2.json].defects[2082-D1]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2082.json`
- Pinning test: `none`
- Verification: filesystem + archive-index; result: confirmed; 1 check(s)

### BDL-P7-020 - 2082 ACWA Power - 2082-D3 (high)
- Defect class: audited_statements_not_published; category: coverage; batch claimed: proven
- Manifest: acwa-power-2025-fy.json (only on origin/claude/data-utilities-1)
- Source file SHA-256: `b5dad4f16ad2478b5146880d1b96f9cb52174f3ae9bc724f12e53c686de70295` (recomputed via git show origin/claude/data-utilities-1:data/raw/SA/2082/documents/b5dad4f16ad2478b5146880d1b96f9cb52174f3ae9bc724f12e53c686de70295.pdf)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: FY2025 audited manifest exists only on origin/claude/data-utilities-1
- Correct value: present on the published (base) branch
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/2082.json#sources[...acwa-power-2025-fy.json].defects[2082-D3]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/2082.json`
- Pinning test: `none`
- Verification: filesystem + git; result: confirmed; 2 check(s)

### BDL-P7-021 - 3050 Southern Province Cement - 3050-D2 (medium)
- Defect class: missing_period_present_in_document; category: completeness; batch claimed: proven
- Manifest: southern-province-cement-2025-fy.json
- Source file SHA-256: `25c47e79e1906fafa75c4b40f84c260ec662059feb1c5668b62e0b44fcf09acb` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 7 (batch cites printed 6); printed page: 6
- Caption/label: Statement of financial position, column "1 January 2024 (Restated - Note 34)" (= 31 Dec 2023 restated)
- Column: third balance-sheet column
- Unit/scale: SAR (full riyals); period: 2023-12-31 / 2024-01-01
- Published value: absent
- Correct value: PPE 2,816,864,176; total assets 4,011,801,700; total equity 3,197,454,749; cash 363,096,531
- Restated: true; continuing operations: not applicable; comparison source: same page, "1 January 2024 (Restated - Note 34)" column
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/3050.json#sources[manifest=...].defects[3050-D2]`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/3050.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/3050_southern-province-cement-2025-fy_pdf7.png`
- Pinning test: `none`
- Verification: visual (scanned page rendered and read) + manifest; result: confirmed; 2 check(s)

### BDL-P7-022 - 1080 Arab National Bank (ANB) - D12 (low)
- Defect class: duplicate_manifests; category: duplicates; batch claimed: proven (no conflict)
- Manifest: anb-2025-annual-report.json, anb-2025-fy.json
- Source file SHA-256: 2 source files (see JSON): `b32c41d05bb4`, `d05a366caba3`
- PDF page: not recorded by batch; printed page: not applicable (duplicate manifests)
- Caption/label: not applicable (duplicate manifests)
- Column: not applicable (duplicate manifests)
- Unit/scale: not applicable (duplicate manifests); period: not applicable (duplicate manifests)
- Published value: 33 and 94 facts
- Correct value: single manifest
- Restated: not applicable (duplicate manifests); continuing operations: not applicable (duplicate manifests); comparison source: not applicable (duplicate manifests)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D12]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 1 check(s)

### BDL-P7-023 - 3060 Yanbu Cement - F-3060-3 (low)
- Defect class: missing_fields (basic/diluted EPS only as diluted, OCI components, cash-flow lines); category: completeness; batch claimed: defective (low)
- Manifest: yanbu-cement-2025-fy.json
- Source file SHA-256: `7aa24367df35cb17de610dc6b94d1d0be084c710ad44eb5a1f6cb3cf607343b9` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 6, 7, 10; printed page: not applicable (completeness gap, nothing published to compare)
- Caption/label: Basic and diluted EPS 0.66 / 1.00; OCI re-measurement (1,316,459) / (6,164,977); employees benefits paid (13,844,438) / (10,582,809)
- Column: FY2025 / FY2024
- Unit/scale: SAR; period: FY2025/FY2024
- Published value: only eps_diluted published
- Correct value: also printed: OCI components, employee benefits paid, FVTPL flows
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/3060.json#findings[id=F-3060-3]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/3060.json`; transcription `docs/audits/saudi-independent/bundle/batch2-F/f_transcripts/3060.json`
- Pinning test: `none`
- Verification: text layer + manifest; result: confirmed; 3 check(s)

### BDL-P7-024 - 7202 solutions by stc - F-7202-3 (low)
- Defect class: missing_fields (basic EPS 12.62/13.42, OCI components, cash-flow detail); category: completeness; batch claimed: defective (low)
- Manifest: stc-solutions-2025-fy.json
- Source file SHA-256: `287f14a69420bbc31ddb70ab916b1aef480ffe14ac951fc1622d7a0e9ab2e2ca` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 9; printed page: 7
- Caption/label: Earnings per share: Basic 12.62 / 13.42; Diluted 12.52 / 13.31
- Column: FY2025 / FY2024
- Unit/scale: SAR per share; period: FY2025/FY2024
- Published value: eps_diluted 12.52 / 13.31 published; basic absent
- Correct value: Basic 12.62 / 13.42
- Restated: not applicable (completeness gap, nothing published to compare); continuing operations: not applicable (completeness gap, nothing published to compare); comparison source: not applicable (completeness gap, nothing published to compare)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/7202.json#findings[id=F-7202-3]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/7202.json`; transcription `docs/audits/saudi-independent/bundle/batch2-F/f_transcripts/7202.json`; rendered pages `docs/audits/saudi-independent/bundle-evidence/7202_stc-solutions-2025-fy_pdf9.png`
- Pinning test: `none`
- Verification: visual (scanned page rendered and read) + manifest; result: confirmed; 2 check(s)

### BDL-P7-025 - 3060 Yanbu Cement - F-3060-4 (medium)
- Defect class: coverage_only_two_fiscal_years; category: coverage; batch claimed: defective (coverage)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s): ['yanbu-cement-2025-fy.json']
- Correct value: earlier annual and interim statements, original FY2024 filing
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/3060.json#findings[id=F-3060-4]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/3060.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

### BDL-P7-026 - 7202 solutions by stc - F-7202-4 (medium)
- Defect class: coverage_only_two_fiscal_years; category: coverage; batch claimed: defective (coverage)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s): ['stc-solutions-2025-fy.json']
- Correct value: earlier annual and interim statements, original FY2024 filing
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-F/7202.json#findings[id=F-7202-4]`; branch path `origin/claude/audit-saudi-batch2-F:docs/audits/saudi-independent/7202.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

### BDL-P7-027 - 3002 Najran Cement - COVERAGE-3002 (medium)
- Defect class: coverage_thin (dimension 3: FY2025 + FY2024 comparatives only); category: coverage; batch claimed: THIN (batch E dimension 3)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s): ['najran-cement-2025-fy.json']
- Correct value: quarterly/interim and pre-2024 history
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3002.json#dimension_3_company_coverage`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3002.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

### BDL-P7-028 - 3003 City Cement - COVERAGE-3003 (medium)
- Defect class: coverage_thin (dimension 3: FY2025 + FY2024 comparatives only); category: coverage; batch claimed: THIN (batch E dimension 3)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s): ['city-cement-2025-fy.json']
- Correct value: quarterly/interim and pre-2024 history
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3003.json#dimension_3_company_coverage`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3003.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

### BDL-P7-029 - 3005 Umm Al-Qura Cement - COVERAGE-3005 (medium)
- Defect class: coverage_thin (dimension 3: FY2025 + FY2024 comparatives only); category: coverage; batch claimed: THIN (batch E dimension 3)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s): ['umm-al-qura-cement-2025-fy.json']
- Correct value: quarterly/interim and pre-2024 history
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3005.json#dimension_3_company_coverage`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3005.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

### BDL-P7-030 - 3020 Yamama Cement - COVERAGE-3020 (medium)
- Defect class: coverage_thin (dimension 3: FY2025 + FY2024 comparatives only); category: coverage; batch claimed: THIN (batch E dimension 3)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s): ['yamama-cement-2025-fy.json']
- Correct value: quarterly/interim and pre-2024 history
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3020.json#dimension_3_company_coverage`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3020.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

### BDL-P7-031 - 3040 Qassim Cement - COVERAGE-3040 (medium)
- Defect class: coverage_thin (dimension 3: FY2025 + FY2024 comparatives only); category: coverage; batch claimed: THIN (batch E dimension 3)
- Manifest: (none)
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (coverage gap, no reported amount involved)
- Caption/label: not applicable (coverage gap, no reported amount involved)
- Column: not applicable (coverage gap, no reported amount involved)
- Unit/scale: not applicable (coverage gap, no reported amount involved); period: not applicable (coverage gap, no reported amount involved)
- Published value: 1 manifest(s): ['qassim-cement-2025-fy.json']
- Correct value: quarterly/interim and pre-2024 history
- Restated: not applicable (coverage gap, no reported amount involved); continuing operations: not applicable (coverage gap, no reported amount involved); comparison source: not applicable (coverage gap, no reported amount involved)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch2-E/3040.json#dimension_3_company_coverage`; branch path `origin/claude/audit-saudi-batch2-E:docs/audits/saudi-independent/3040.json`
- Pinning test: `none`
- Verification: filesystem; result: confirmed; 1 check(s)

# Section: SUSPECTED defects (15)

## suspected: group 3 - Quarter-vs-YTD / wrong period-column defects

### BDL-P3-003 - 7010 stc (Saudi Telecom) - C-7010-07 (low)
- Defect class: quarter_sum_does_not_match_year; category: period_column_vintage; batch claimed: unverified
- Manifest: stc-2024-quarterly-revenue.json vs stc-2025-fy.json
- Source file SHA-256: 2 source files (see JSON): `unavailable`, `aeec895e88a6`
- PDF page: not recorded by batch; printed page: not recorded by batch
- Caption/label: not recorded by batch
- Column: not recorded by batch
- Unit/scale: not recorded by batch; period: not recorded by batch
- Published value: 18.908+19.021+18.643+19.266 = 75.838 bn
- Correct value: FY2024 75,893,413 thousand (restated comparative, AR2025 p9); gap -55.4m (-0.07%)
- Restated: possibly; continuing operations: not recorded by batch; comparison source: AR2025 p9 restated FY2024
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7010.json#findings[id=C-7010-07]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-C:tests/test_manifest_audit.py::QuarterSumTests::test_rounding_noise_is_not_reported` - tolerance 0.4% would hide this gap
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch status unverified; Q1-2025 presentation not archived; cannot say which figure is right

### BDL-P3-004 - 7040 GO Telecom - C-7040-04 (low)
- Defect class: quarter_sum_vs_fiscal_year; category: period_column_vintage; batch claimed: unverified
- Manifest: go-telecom-2023-2025-quarterly-history.json vs go-telecom-2021-2025-fy-history.json
- Source file SHA-256: 2 source files (see JSON): `unavailable`, `d76f55f907fc`
- PDF page: not recorded by batch; printed page: not recorded by batch
- Caption/label: not recorded by batch
- Column: not recorded by batch
- Unit/scale: not recorded by batch; period: not recorded by batch
- Published value: FY2025 quarterly net profit sum differs from FY by -0.63% (batch C)
- Correct value: n/a
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7040.json#findings[id=C-7040-04]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7040.json`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch status unverified; quarterly source not archived

## suspected: group 4 - Zakat basis (D6) and other restated / continuing-operations basis defects

### BDL-P4-008 - 1150 Alinma Bank - ALN-4 (high)
- Defect class: restated_or_corrected_later_by_issuer_not_adopted (unresolved issuer conflict); category: basis_restated_conflict; batch claimed: defective_suspect
- Manifest: alinma-pillar-3-tables-final-september-2021-pillar3.json
- Source file SHA-256: `a85ff5038946145ea4905c0be0a7ebdba9aad1b7c682edde5267c2893cf0949d` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 1; printed page: 1
- Caption/label: KM1 row 1 Common Equity Tier 1 (CET1) capital; row 2 Tier 1
- Column: column a (2021-09-30)
- Unit/scale: SAR (as printed in the template; see manifest scale); period: 2021-09-30
- Published value: [{"metric": "cet1_capital", "caption": "Common Equity Tier 1 (CET 1) (after transitional arrangement for IFRS 9)", "value": "30887221", "scale": "1000", "period_kind": "instant", "period_start": null, "period_end": "2021-09-30", "manifest_page": 1}, {"metric": "cet1_ratio", "caption": "Common Equity Tier 1 ratio (%)", "value": "0.2126", "scale": "1", "period_kind": "instant", "period_start": null, "period_end": "2021 ... (full value in defect-bundle.json)
- Correct value: UNRESOLVED: later Alinma disclosures (Dec-2021 p15 col b, Mar-2022, Jun-2022) print CET1 25,887,221 / 17.35% for the same quarter; neither pair reconciles (batch B). Do not overwrite the original.
- Restated: true; continuing operations: not applicable; comparison source: later Alinma Pillar 3 disclosures Dec-2021 (p15 col b), Mar-2022, Jun-2022 (not re-opened by bundle); note: issuer-restated comparative; scope and reason not stated by the issuer
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/1150.json#sources[manifest=alinma-pillar-3-tables-final-september-2021-pillar3.json].defects[ALN-4]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/1150.json`
- Pinning test: `none`
- Verification: text layer of the Sep-2021 document + manifest (later disclosures not re-checked); result: confirmed; 2 check(s); notes: only the original-vintage half was re-checked; the issuer-conflict claim depends on later documents that the bundle did not open

## suspected: group 5 - Other numeric value, mapping, sign and definition defects

### BDL-P5-004 - 8010 Tawuniya - TAW-1 (high)
- Defect class: two_panel_layout_wrong_pairing_sign_and_magnitude (candidate manifest, unmerged); category: numeric_wrong_source_row; batch claimed: proven (candidate manifest, unmerged)
- Manifest: tawuniya-2023-fy.json (on origin/claude/insurance-tawuniya-bupa-enrichment, not on base)
- Source file SHA-256: `1975790ff3fd29669340e72aba0507fae6c6a9f2efe9676186d46965bdfdda37` (filename of archived path recorded by batch B (equals content hash by the repo convention); file bytes not reachable offline)
- PDF page: 179; printed page: 179 (printed, per batch B)
- Caption/label: Net change in cash and cash equivalents during the period
- Column: right-hand panel 2023 column (published value is from the left panel row "Reinsurance contract assets")
- Unit/scale: SAR (as printed in the report; see manifest scale); period: FY2023
- Published value: {"metric": "cash_change", "value": "-106248"}
- Correct value: 422,514 (2022: 471,057); proof 1,591,389 - 1,044,024 - 124,851 = 422,514
- Restated: false; continuing operations: not applicable; comparison source: same page right-hand panel
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/8010.json#sources[manifest=tawuniya-2023-fy.json].defects[TAW-1]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/8010.json`
- Pinning test: `none`
- Verification: manifest on candidate branch; result: confirmed; 1 check(s); notes: source PDF and manifest are not on the base branch; bundle could not render/read p179

### BDL-P5-024 - 1010 Riyad Bank - D4 (add-back sign part) (low)
- Defect class: cash_flow_add_back_published_positive; category: sign_convention; batch claimed: proven (batch A, 13+8 facts)
- Manifest: riyad-2018-q2.json, riyad-2018-q3.json
- Source file SHA-256: 2 source files (see JSON): `4cc76e17a183`, `0bf2b74010cb`
- PDF page: cash-flow statement pages (see published_value); printed page: not recorded by batch
- Caption/label: Depreciation and amortization / impairment charge add-back rows
- Column: current-period column
- Unit/scale: SAR '000, scale 1000; period: per document
- Published value: [{"manifest": "riyad-2018-q2", "metric": "provision_expense", "caption": "Impairment charge for credit losses and other provisions, net", "value": "477652", "scale": "1000", "period_kind": "ytd", "period_start": "2018-01-01", "period_end": "2018-06-30", "manifest_page": 6}, {"manifest": "riyad-2018-q3", "metric": "provision_expense", "caption": "Impairment charge for credit losses and other provisions, net", "value": ... (full value in defect-bundle.json)
- Correct value: batch A: add-backs published positive while income-statement expenses are negative; batch E documents "depreciation_amortization stored negative although the add-back is printed positive" as a repo convention (engine uses abs) - the two batches disagree on whether this is a defect
- Restated: not applicable; continuing operations: not applicable; comparison source: same document income statement; note: sign only
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1010.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1010.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_cash_flow_addbacks_take_the_expense_sign` - synthetic PDF; source branch only
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch-only; candidate facts enumerated by sign rule; repo sign convention disputed between batch A and batches E/F, so not proven

### BDL-P5-025 - 1080 Arab National Bank (ANB) - D4 (add-back sign part) (low)
- Defect class: cash_flow_add_back_published_positive; category: sign_convention; batch claimed: proven (batch A, 13+8 facts)
- Manifest: anb-2015-annual-report.json, anb-2017-annual-report.json, anb-2019-annual-report.json, anb-2020-q1.json, anb-2021-q1.json
- Source file SHA-256: 5 source files (see JSON): `0482608a38c0`, `91b1d6217433`, `f05ee3e34dc7`, `bb7acd369c11` ...
- PDF page: cash-flow statement pages (see published_value); printed page: not recorded by batch
- Caption/label: Depreciation and amortization / impairment charge add-back rows
- Column: current-period column
- Unit/scale: SAR '000, scale 1000; period: per document
- Published value: [{"manifest": "anb-2015-annual-report", "metric": "depreciation_amortization", "caption": "Depreciation and amortization of property and equipment", "value": "199323", "scale": "1000", "period_kind": "fy", "period_start": "2015-01-01", "period_end": "2015-12-31", "manifest_page": 8}, {"manifest": "anb-2017-annual-report", "metric": "depreciation_amortization", "caption": "Depreciation and amortization of property and ... (full value in defect-bundle.json)
- Correct value: batch A: add-backs published positive while income-statement expenses are negative; batch E documents "depreciation_amortization stored negative although the add-back is printed positive" as a repo convention (engine uses abs) - the two batches disagree on whether this is a defect
- Restated: not applicable; continuing operations: not applicable; comparison source: same document income statement; note: sign only
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1080.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1080.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_cash_flow_addbacks_take_the_expense_sign` - synthetic PDF; source branch only
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch-only; candidate facts enumerated by sign rule; repo sign convention disputed between batch A and batches E/F, so not proven

### BDL-P5-026 - 1140 Bank Albilad - D4 (add-back sign part) (low)
- Defect class: cash_flow_add_back_published_positive; category: sign_convention; batch claimed: proven (batch A, 13+8 facts)
- Manifest: albilad-2019-fy.json, albilad-2020-fy.json, albilad-2020-q1.json, albilad-2021-q3.json, albilad-2022-q1.json, albilad-2023-q1.json, albilad-2024-q1.json
- Source file SHA-256: 7 source files (see JSON): `ec46ea3ca369`, `46353fb92a63`, `f9dca6151a95`, `00d11cbf298a` ...
- PDF page: cash-flow statement pages (see published_value); printed page: not recorded by batch
- Caption/label: Depreciation and amortization / impairment charge add-back rows
- Column: current-period column
- Unit/scale: SAR '000, scale 1000; period: per document
- Published value: [{"manifest": "albilad-2019-fy", "metric": "depreciation_amortization", "caption": "Depreciation and amortization", "value": "248924", "scale": "1000", "period_kind": "fy", "period_start": "2019-01-01", "period_end": "2019-12-31", "manifest_page": 12}, {"manifest": "albilad-2019-fy", "metric": "provision_expense", "caption": "Impairment charge for expected credit losses, net", "value": "535623", "scale": "1000", "per ... (full value in defect-bundle.json)
- Correct value: batch A: add-backs published positive while income-statement expenses are negative; batch E documents "depreciation_amortization stored negative although the add-back is printed positive" as a repo convention (engine uses abs) - the two batches disagree on whether this is a defect
- Restated: not applicable; continuing operations: not applicable; comparison source: same document income statement; note: sign only
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1140.json#defects[id=D4]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1140.json`
- Pinning test: `origin/claude/audit-saudi-batch1-A:tests/test_reading_saudi_audit_batch1a.py::CashFlowRowsDoNotPopulateIncomeStatementMetricsTests::test_cash_flow_addbacks_take_the_expense_sign` - synthetic PDF; source branch only
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch-only; candidate facts enumerated by sign rule; repo sign convention disputed between batch A and batches E/F, so not proven

### BDL-P5-039 - 7030 Zain KSA - LEAD-7030-segment-revenue (low)
- Defect class: segment_revenue_sum_exceeds_revenue (lead handed over by batch D; may be inter-segment eliminations); category: definition; batch claimed: lead (not a proven defect)
- Manifest: zain-ksa-2025-notes-segments.json
- Source file SHA-256: `bee6f9b63c9d81f625abb5675852d96679bb2776b746ef6f1bf2b1e7e26d192c` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: 68; printed page: no printed page number detected in text layer
- Caption/label: Consumer / Business / Wholesale revenue (segment note)
- Column: FY2025
- Unit/scale: SAR '000, scale 1000; period: FY2025
- Published value: [{"metric": "segment_revenue", "caption": "Consumer revenue", "value": "6911555", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 68}, {"metric": "segment_revenue", "caption": "Business revenue", "value": "1804454", "scale": "1000", "period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "manifest_page": 68}, {"metric": "segment_r ... (full value in defect-bundle.json)
- Correct value: unknown: batch C states segment revenue includes internal sales; whether an elimination row exists on the page was not established
- Restated: not applicable; continuing operations: not applicable; comparison source: zain-ksa-2025-fy revenue 10,983,264 (pdf p9)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/batch1-D-summary.md#summary: Repo-wide run also flags sa:7030 segment_revenue`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/batch1-D-summary.md`
- Pinning test: `none`
- Verification: manifest arithmetic + text layer; result: NOT confirmed (downgraded to suspected); 2 check(s); notes: arithmetic gap confirmed, but whether it is an extraction defect or legitimate intersegment eliminations is not established

### BDL-P5-040 - 1080 / 1120 multiple companies (see published_value) - LEAD-1080-1120-DA-label (low)
- Defect class: depreciation_amortization label drift (lead only); category: definition; batch claimed: lead (not a proven defect)
- Manifest: anb / alrajhi manifests
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not recorded by batch
- Caption/label: not recorded by batch
- Column: not recorded by batch
- Unit/scale: not recorded by batch; period: not recorded by batch
- Published value: not recorded by batch
- Correct value: not recorded by batch
- Restated: not recorded by batch; continuing operations: not recorded by batch; comparison source: not recorded by batch
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-D/batch1-D-summary.md#summary: RC-CAPEX-DEFINITION (also seen for ... sa:1080/1120 D&A labels, leads for other auditors)`; branch path `origin/claude/audit-saudi-batch1-D:docs/audits/saudi-independent/batch1-D-summary.md`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch D names this as a lead for other auditors without evidence; no batch A record confirms it; not re-checked

## suspected: group 6 - Provenance and metadata defects (page citations, filed_at, scanned/digital tags)

### BDL-P6-004 - 2222 Saudi Aramco - ARA-1 (low)
- Defect class: wrong_page_citation; category: provenance_page; batch claimed: defective (values correct)
- Manifest: aramco-2025-annual-metrics.json
- Source file SHA-256: `78bb678e8e45f5c58fa1b2402ab5a29c5ad10adfda8ba5e7ee5f4d1ad76cd227` (recomputed from archived file in this worktree; equals archive-index content_hash)
- PDF page: cited 177-180/243/244; actual pdf 174/176/177/178/235 (batch B); printed page: printed 172 for the income statement (batch B)
- Caption/label: Revenue 1,559,342; Net income 350,210; EPS 1.44 ...
- Column: not applicable (page-citation defect, value not in question)
- Unit/scale: not applicable (page-citation defect, value not in question); period: FY2025
- Published value: 160 of 176 facts cite a page on which the value does not occur
- Correct value: derive page from the archived PDF
- Restated: not applicable (page-citation defect, value not in question); continuing operations: not applicable (page-citation defect, value not in question); comparison source: not applicable (page-citation defect, value not in question)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-B/2222.json#sources[manifest=aramco-2025-annual-metrics.json].defects[ARA-1]`; branch path `origin/claude/audit-saudi-batch1-B:docs/audits/saudi-independent/2222.json`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: source PDF listed in archive-index but not available offline in any ref; bundle could not re-check

## suspected: group 7 - Completeness, coverage and source-availability defects

### BDL-P7-011 - 7030 Zain KSA - C-7030-07 (medium)
- Defect class: quarter_facts_source_not_archived; category: source_not_archived; batch claimed: unverified
- Manifest: zain-ksa-2023-2025-quarterly-results.json
- Source file SHA-256: 1 source files (see JSON): `unavailable`
- PDF page: not recorded by batch; printed page: not applicable (source file missing)
- Caption/label: not applicable (source file missing)
- Column: not applicable (source file missing)
- Unit/scale: not applicable (source file missing); period: not applicable (source file missing)
- Published value: 36 quarterly facts
- Correct value: n/a
- Restated: not applicable (source file missing); continuing operations: not applicable (source file missing); comparison source: not applicable (source file missing)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-C/7030.json#findings[id=C-7030-07]`; branch path `origin/claude/audit-saudi-batch1-C:docs/audits/saudi-independent/7030.json`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch status unverified: quarterly source announcements not archived

### BDL-P7-016 - 1010 Riyad Bank - D10 (low)
- Defect class: pillar3_and_supplement_notes; category: completeness_and_notes; batch claimed: low-severity notes
- Manifest: Pillar 3 and XLSX supplement manifests
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (completeness gap)
- Caption/label: not applicable (completeness gap)
- Column: not applicable (completeness gap)
- Unit/scale: not applicable (completeness gap); period: not applicable (completeness gap)
- Published value: not recorded by batch
- Correct value: see batch record: only oldest column published per Pillar 3 doc; rows 8-12/LCR/NSFR for old docs and non-KM1 templates not extracted; supplements: EPS rounded to 2dp; Al Rajhi workbook duplicate FY columns (FY2023 DPS 1.15 col T vs 2.3 col BF) - original column published, restated column unverified
- Restated: possibly (Al Rajhi duplicate columns); continuing operations: not applicable (completeness gap); comparison source: XLSX workbook columns (not opened by bundle)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1010.json#defects[id=D10]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1010.json`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch-only; XLSX workbooks and Pillar 3 cells not re-checked by bundle

### BDL-P7-017 - 1020 Bank AlJazira - D10 (low)
- Defect class: pillar3_and_supplement_notes; category: completeness_and_notes; batch claimed: low-severity notes
- Manifest: Pillar 3 and XLSX supplement manifests
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (completeness gap)
- Caption/label: not applicable (completeness gap)
- Column: not applicable (completeness gap)
- Unit/scale: not applicable (completeness gap); period: not applicable (completeness gap)
- Published value: not recorded by batch
- Correct value: see batch record: only oldest column published per Pillar 3 doc; rows 8-12/LCR/NSFR for old docs and non-KM1 templates not extracted; supplements: EPS rounded to 2dp; Al Rajhi workbook duplicate FY columns (FY2023 DPS 1.15 col T vs 2.3 col BF) - original column published, restated column unverified
- Restated: possibly (Al Rajhi duplicate columns); continuing operations: not applicable (completeness gap); comparison source: XLSX workbook columns (not opened by bundle)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1020.json#defects[id=D10]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1020.json`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch-only; XLSX workbooks and Pillar 3 cells not re-checked by bundle

### BDL-P7-018 - 1120 Al Rajhi Bank - D10 (low)
- Defect class: pillar3_and_supplement_notes; category: completeness_and_notes; batch claimed: low-severity notes
- Manifest: Pillar 3 and XLSX supplement manifests
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (completeness gap)
- Caption/label: not applicable (completeness gap)
- Column: not applicable (completeness gap)
- Unit/scale: not applicable (completeness gap); period: not applicable (completeness gap)
- Published value: not recorded by batch
- Correct value: see batch record: only oldest column published per Pillar 3 doc; rows 8-12/LCR/NSFR for old docs and non-KM1 templates not extracted; supplements: EPS rounded to 2dp; Al Rajhi workbook duplicate FY columns (FY2023 DPS 1.15 col T vs 2.3 col BF) - original column published, restated column unverified
- Restated: possibly (Al Rajhi duplicate columns); continuing operations: not applicable (completeness gap); comparison source: XLSX workbook columns (not opened by bundle)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1120.json#defects[id=D10]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1120.json`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch-only; XLSX workbooks and Pillar 3 cells not re-checked by bundle

### BDL-P7-019 - 1140 Bank Albilad - D10 (low)
- Defect class: pillar3_and_supplement_notes; category: completeness_and_notes; batch claimed: low-severity notes
- Manifest: Pillar 3 and XLSX supplement manifests
- Source file SHA-256: not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item (n/a)
- PDF page: not recorded by batch; printed page: not applicable (completeness gap)
- Caption/label: not applicable (completeness gap)
- Column: not applicable (completeness gap)
- Unit/scale: not applicable (completeness gap); period: not applicable (completeness gap)
- Published value: not recorded by batch
- Correct value: see batch record: only oldest column published per Pillar 3 doc; rows 8-12/LCR/NSFR for old docs and non-KM1 templates not extracted; supplements: EPS rounded to 2dp; Al Rajhi workbook duplicate FY columns (FY2023 DPS 1.15 col T vs 2.3 col BF) - original column published, restated column unverified
- Restated: possibly (Al Rajhi duplicate columns); continuing operations: not applicable (completeness gap); comparison source: XLSX workbook columns (not opened by bundle)
- Evidence: batch record `docs/audits/saudi-independent/bundle/batch1-A/1140.json#defects[id=D10]`; branch path `origin/claude/audit-saudi-batch1-A:docs/audits/saudi-independent/1140.json`
- Pinning test: `none`
- Verification: batch_only; result: not re-checked by bundle; 0 check(s); notes: batch-only; XLSX workbooks and Pillar 3 cells not re-checked by bundle
