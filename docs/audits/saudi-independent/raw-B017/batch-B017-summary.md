# Batch B017 (insurers) - statement-level audit of raw collected documents

Audited 2026-10-04/05 by Claude Sonnet 5.5 (independent). Raw files read-only; no network, no data/**, no AWS/Supabase. Values are SAR thousands as printed. Three dimensions are kept separate: value correctness, document completeness, company coverage (page-derived periods, not collector labels). No company is claimed complete.

| Symbol | Entity (verified from pages) | Filings value-read | Value correctness | Document completeness | Company coverage |
|---|---|---|---|---|---|
| 8300 | Wataniya Insurance Company | FY2022 (IFRS 4), FY2023, FY2024, FY2025, Q1 2026, H1 2026 | identities, cross-filing and Q1+Q2=H1 rolls pass; IFRS 17 FY2022 restatement declared | all statement pages image-only though inventory flags 11 of 18 partial | FY2022-FY2025 and 2022 Q1 to 2026 H1 present; 12 interims unread; FY2021 and earlier absent |
| 8070 | Arabian Shield Cooperative Insurance Company (merged Al Ahli Takaful 12 Jan 2022 and Alinma Tokio Marine 15 Nov 2023, acquisition accounting) | FY2022 (IFRS 4), FY2023 as issued, FY2024, FY2025, Q1 2026, H1 2026 | pass; IFRS 17 and FY2023 restatements declared; restricted cash explains FY2025 cash difference | H1 2026 file entirely image-only (classed scanned_unreadable) but holds full statements; two 2022/2023 files still unopened scans | FY2022-FY2025 and interims present; 12 unread; no separate Al Ahli Takaful statements exist |
| 8260 | Gulf General Cooperative Insurance Company | FY2022 (IFRS 4), FY2023, FY2024, FY2025, Q1 2026, H1 2026 | pass; IFRS 17 and EPS restatements declared; going-concern material uncertainty at FY2025 and Q1 2026 | 10 older files scanned_unreadable, Arabic twins with scrambled text, not opened | FY2022-FY2025 and interims verified for 2026; 2015-2021 and 2022-2025 interims unread |
| 8280 | Liva Insurance Company (formerly Al Alamiya for Cooperative Insurance) | FY2022 (IFRS 4, as Al Alamiya), FY2023, FY2024, FY2025, Q1 2026, H1 2026 | pass; IFRS 17, FY2023 cash-flow re-presentation and opening-equity restatement declared | FY2025 and H1 2026 files are whole-file scans holding full statements; 4 scanned interims unopened; six 2014/2015 files are one-page monthly statements mislabelled 9M/FY | FY2022-FY2025 and interims present; pre-2022 absent |
| 8060 | Walaa Cooperative Insurance Company (consolidated from FY2025) | FY2023, FY2024, FY2025, Q1 2026, H1 2026 | pass; FY2023 cash flow/EPS and Dec 2025 balance-sheet re-presentations declared | all statement pages image-only; FY2025 file classed annual_report_no_statements but holds statements; 3 interim files mis-classed | FY2022 as issued (facb2cde) and 13 interims unread; FY2021 and earlier absent |

## Cross-batch findings
- Annual FY label equals the publication year (FY(n+1)) in every annual file of all five companies.
- IFRS 4 to IFRS 17 transition: FY2022 as issued and as restated differ for every company; both values are recorded in the transcripts with a written reason, never substituted.
- Inventory partial/unreadable flags are wrong for the latest filings of 8300, 8070, 8260, 8280 and 8060: they contain full primary statements on image pages.
- Interim cash flow: Q2 by subtraction is not validated for any company (different line detail between Q1 and H1 cash flows).
- Insurance service expense is printed as a negative (bracketed) number in every income statement read.
- Insurance Authority insurance-operations / shareholders-operations supplementary statements were not read for any company.

## Files
Per symbol: `<symbol>.json` (audit record), `transcripts/<symbol>.json` (page values with PDF and printed page, SHA-256 prefix), `tools/` (render, row-reader, record builders, `check_transcripts.py`). Guard test: `tests/test_audit_raw_b017.py`. Renders are not committed.
