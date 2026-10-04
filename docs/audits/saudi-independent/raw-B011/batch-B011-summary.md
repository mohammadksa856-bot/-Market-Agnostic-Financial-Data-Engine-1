# Batch B011 summary (raw statement-level audit)

Companies: 7201 ARAB SEA (plan batch B010), 3080 EPCCO (Eastern Province Cement), 3091 JOUF CEMENT, 3092 RIYADH CEMENT, 1090 SAMBA, 6019 ALMASAR ALSHAMIL.
Method: statement pages rendered or read from the text layer, headline values transcribed with PDF page and file SHA-256 (recomputed against the inventory), arithmetic and cross-filing checks in `tools/check_transcripts.py` (undeclared differences between filings repeating a period fail). Records: `<symbol>.json`, page transcriptions: `transcripts/<symbol>.json`, guard test: `tests/test_audit_raw_b011.py`. Nothing under `data/**`, raw files, earlier audits, AWS or Supabase was touched.

Three dimensions are kept apart. No company is claimed complete as a company history.

| Symbol | Value correctness (from pages) | Document completeness | Company coverage (page-derived) |
|---|---|---|---|
| 7201 | 10 filings 2024 to 2026 H1 read; 80 declared restatement differences (FY2024 exists in three versions) | 18 of 18 files hold statements; 8 scanned or image 2022-2023 files unread | 2022 Q1 to 2026 H1 present (consecutive); 2016-2021 absent |
| 3080 | 18 filings 2022 Q1 to 2026 H1 read; 78 declared differences | 18 of 18 stand-alone statement files complete; 7 annual reports 2012-2020 unread | 2022 Q1 to 2026 H1 present; 2016, 2017, 2021 annual absent |
| 3091 | 17 filings read; 126 declared differences (2023 and 2024 interims restated) | 23 files: 17 read, 2 English 2023 interims located only, 4 Arabic twins unread | 2022 Q1 to 2026 H1 present; 2023 H1 and 9M unread; 2013-2021 absent |
| 3092 | 14 filings read; 18 declared differences (revenue and net profit never differ) | 14 complete statement files, 1 partly read (H1 2023), 3 earnings releases | 2022 H1 to 2026 H1 with Q1/9M 2022 and Q1/9M 2023 having no file; 2020-2021 absent |
| 1090 | 5 filings of 2020 vintage read (FY2019, FY2020, Q1/H1/9M 2020); 8 declared differences (31 Dec 2019 balance sheet restated) | 16 files located as statement sets; 11 read only to cover and layout | 2017 Q1 to 2020 FY in documents; 2011-2016 absent; 2021+ does not exist (merged into SNB); no overlap with 1180 found |
| 6019 | 8 English files read; 6 declared differences | 8 English files complete; 7 Arabic twins and 2 annual reports unread | FY2021 to FY2025 and 2025 Q1 to 2026 H1 (plus H1 2024); 2024 Q1 and 9M only as comparatives |

## Defect classes found
- Annual files labelled with the publication year (fiscal_year one above the cover period): 7201, 3080, 3091, 3092, 1090, 6019. Creates false gaps and extras.
- Inventory file classes wrong because statements are image pages inside text PDFs: all six companies.
- Mislabelled or non-statement files: 3091 ef7e16e4 (FY2022 year-end set labelled 2022|Q1), 6019 b72eb2f6 (combined FY2021-H1 2024 set labelled 2025|FY), 3092 earnings releases counted as statements.
- Restated or re-presented comparatives (declared with both values, never substituted): all six, largest in 7201 (FY2024 net loss -17.7m, -23.6m), 3091 (2023 net profit 84.7m vs 37.7m; 2024 interims flipped from profit to loss).
- Cash-flow reclassifications between filings (quarterly cash flow by subtraction across vintages would be wrong): 3080, 3091, 3092, 6019.
- A footing error in a source statement: 7201 FY2024 CFO is 1,000,000 above its own components.
- Arabic twins of English filings: 3091, 1090, 6019.

## Unread items (all companies)
Notes in every file; equity statements (located, not transcribed); the files listed per company in `unread_items`.
