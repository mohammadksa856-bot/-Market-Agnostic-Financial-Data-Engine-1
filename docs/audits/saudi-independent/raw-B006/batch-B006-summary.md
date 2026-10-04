# Batch B006 raw-document statement audit: 4004, 4001, 4002, 7200, 5110

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Image-only statement pages were rendered and read by eye; born-digital pages read from the text layer. Identity checks (balance sheet, cash-flow sum and roll, income split) in `tools/check_transcripts.py`, guard test `tests/test_audit_raw_b006.py`. Nothing is claimed complete; unread items are listed in each company JSON.

| Symbol | Value correctness | Document completeness | Company coverage (page-derived) |
|---|---|---|---|
| 4004 Dallah Health | FY2022-FY2025, Q1 2024 to H1 2026 and 9M 2023 verified (full SAR); 2 re-presentations recorded | 29 files: 4 annual + 14 interim statement sets, 9 infographics/presentations; inventory wrong for 11 (image-only or scanned); 4 annual files mislabelled (publication year) | 18 periods Q1 2022 to H1 2026 with statements, no gap; before 2022 absent |
| 4001 A.Othaim | FY2022-FY2025, 9M 2025, Q1/H1 2026 verified; H1/Q1 2025 income only; 5 restatements recorded (FY2023 net income 497.3m -> 488.6m) | 21 statement sets, all flagged partial wrongly (image-only pages); 3 Q4 year-end interims labelled Q1; 4 annual files mislabelled | 21 periods 2022 to H1 2026 (Q4 2025 absent); 2010-2021 absent |
| 4002 Mouwasat | FY2022-FY2025, 9M 2025, Q1/H1 2026 verified; H1/Q1 2025 P&L only; gross profit re-presented 4 times | 18 statement sets; 13 mis-classed (10 other_no_statements, 1 scanned, 2 partial); 4 annual files mislabelled | 18 periods 2022 to H1 2026; 2012-2021 absent |
| 7200 MIS | FY2022-FY2025, Q1/H1 2026, 9M/H1 2025 verified; FY2024 restated (CFO -87.9m -> -181.9m) | 36 files incl. 10 Arabic duplicates and 8 annual reports; 15 files labelled 2026 for 2022-2025 periods; scanned files classed unreadable | 18 periods 2022 to H1 2026 (several only as scanned or image pages, values unread); 2019-2021 absent |
| 5110 Saudi Energy | Only FY2024, FY2025 and H1 2026 headline (thousand SAR, Arabic-Indic digits, identity-closing values only); 35 of 38 files unread | 25 statement files, all image-only Arabic after 2020; 2 scanned; 1 mojibake; 2 with missing slot | statement files 2020 to H1 2026, values read for 3 periods; 2012-2019 annual reports only |

## Defects (general)

1. Annual statements labelled with publication year for 4004, 4001, 4002 and the English annual files of 7200; 5110 is fiscal-year labelled.
2. Image-only statement pages inside text PDFs make the inventory classify complete statement sets as partial / no statements; fully scanned PDFs are "scanned_unreadable" although covers show reviewed statements.
3. Re-presented comparatives change the same period between filings (4004 FY2022 CFI, 4001 FY2023 and FY2024, 4002 gross profit, 7200 FY2024 net income and CFO, 5110 FY2024 assets and CFO).
4. Arabic duplicates and annual reports in 7200 are labelled 2026 for earlier periods.
5. 5110 reports in thousand SAR; the others in full SAR.
6. Arabic-Indic digit reading is error-prone (several 50 to 700 unit misreads caught only by identity checks in 5110); OCR must be followed by identities.

## Unread (explicit)

Notes in all files; equity and OCI statements; most interim files outside the verified list; scanned covers only; Arabic duplicates (7200); annual reports; 5110 files other than FY2024, FY2025 and H1 2026.
