# Batch B018 - statement-level audit of raw collected documents

Audited 2026-10-05 by Claude Sonnet 5.5 (independent). Raw files read-only; no network, no data/**, no AWS/Supabase. Amounts: 8150 in SAR thousands as printed; 1323, 1324, 1321, 1322 in full SAR. Three dimensions are kept separate: value correctness, document completeness, company coverage (page-derived periods, not collector labels). No company is claimed complete.

| Symbol | Entity (verified from pages) | Filings value-read | Value correctness | Document completeness | Company coverage |
|---|---|---|---|---|---|
| 8150 | Allied Cooperative Insurance Group (ACIG) | FY2022 (IFRS 4), FY2023, FY2024, FY2025, Q1/H1/9M 2025, Q1 2026, H1 2026 | identities, Q1+Q2=H1 2026, H1+Q3=9M 2025 pass; IFRS 17 and re-presentations declared; four printed source inconsistencies declared (Q1 2025 comparative cash flow, 168 H1 2025 roll, FY2023 closing cash, 1 rounding) | all statement pages image-only; inventory flags 17 of 18 as partial/absent; FY2025 file is a print of a draft workbook | FY2022-FY2025 and 2022 Q1 to 2026 H1 present; 9 interims value-unread; pre-2022 absent |
| 1323 | United Carton Industries Company | all 9 files: FY2022-FY2025, Q1/H1/9M 2025, Q1/H1 2026 | identities and all rolls pass; FY2022 restatement (Note 31) declared | FY2025 and 2025 interims image-only; three annual files share label 2025|FY | FY2022-FY2025 and 2025 Q1 to 2026 H1; no 2022-2024 interims, no pre-2022 |
| 1324 | Saleh Abdulaziz Al Rashed and Sons Company | FY2022 (special purpose, limited liability), FY2023, FY2024, FY2025, Q1 2026, H1 2026 | identities, Q1+Q2=H1 pass; FY2023 and FY2024 cash-flow re-presentations and the special-purpose basis difference declared | Q1/H1 2026 are scans with garbled OCR; four annual files all labelled 2026|FY; Arabic twins unread | FY2022-FY2025 and 2026 Q1/H1 only; no 2022-2025 interims |
| 1321 | East Pipes Integrated Company for Industry (March fiscal year) | FY2023 (scan), FY2024, FY2025, FY2026, Q1-Q3 FY26, Q1 FY27 | identities and rolls pass; 31 Mar 2025 balance sheet and Q1 FY26 operating profit re-presentations declared; 2-riyal printed rounding declared | FY2023 whole-file scan holds full statements (inventory scanned_unreadable); standalone FY2022 statements absent | FY2023-FY2026 and all interim quarters FY23 to Q1 FY27 present; 9 older interims value-unread |
| 1322 | Al Masane Al Kobra Mining Company (AMAK) | FY2022-FY2025, Q1/H1/9M 2025, Q1 2026, H1 2026 | identities and rolls pass; severance-fee restatement of FY2023 and 2024 interims declared; 1-2 riyal printed roundings declared | five image-only statement files; H1 2026 file duplicated from two sources | FY2022-FY2025 and 2022 Q1 to 2026 H1 present; 11 older interims value-unread |

## Cross-batch findings
- Annual labels equal the publication year (FY(n+1)) for 8150, 1324 and 1322; 1323 labels three annual files (FY2022-FY2024) all 2025|FY and 1324 labels four all 2026|FY; 1321 has a March year end so annual labels equal the year-end year and interim labels are calendar-style.
- Image-only statement pages and whole-file scans hold full statements in every company; the inventory partial / no-statement classes come from scanning only text layers.
- Restated or re-presented comparatives were found in every company; each is recorded with both values and a written reason in the transcripts.
- Source filings contain printed internal inconsistencies (8150 Q1 2025 cash-flow comparative carries full-year 2024 lines; one to three riyal roundings elsewhere); they are declared, never corrected.
- Q2 cash flow by subtraction is not validated for any company; notes, audit reports and equity statements were not read for any company.

## Files
Per symbol: `<symbol>.json` (audit record), `transcripts/<symbol>.json` (page values with PDF and printed page, SHA-256 prefix), `tools/` (render, row-reader, record builders, `check_transcripts.py`). Guard test: `tests/test_audit_raw_b018.py`. Renders are not committed.
