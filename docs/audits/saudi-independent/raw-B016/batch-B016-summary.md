# Batch B016 raw-document statement audit: 8313 Rasan, 8120 Gulf Union Alahlia, 8180 Al Sagr, 8100 SAICO, 8170 Al-Etihad

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Born-digital pages were read from the text layer; image-only, scanned or garbled-OCR statement pages (all of 8100 and 8170, the FY2022/FY2023 pages of 8120, 8180 FY2022 and H1 2026) were rendered and read by eye. Transcripts in `transcripts/`, checks in `tools/check_transcripts.py` (balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat/tax to net result, cross-filing comparatives that fail on any undeclared difference, Q1+Q2=H1 and H1+Q3=9M rolls, plus a new `declared_break` form for a roll that does not close and must carry the exact difference and a reason). Guard test `tests/test_audit_raw_b016.py`. Per-company `documents[]` carry the full SHA-256 verified against the raw file; `files_not_audited_for_values[]` lists every other inventory file.

Three dimensions are kept separate. No company is claimed complete.

| Symbol (units) | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 8313 RASAN (full SAR) | 9 filings: FY2021-FY2025, Q1 2026, H1 2026, 9M 2025, H1 2025. H1 2026 filing restates 31 Dec 2025 balance sheet (total assets 1,347.9m to 988.8m) and H1 2025 profit (75.0m to 64.9m); an unexplained 680,547 break in 2026 Q1+Q2 vs H1 profit | born digital; 6 scanned_unreadable files are infographics/decks, not statements; 2 scrambled EY twins misclassed | FY2021-FY2025, interims 2024 Q1 to 2026 H1; 2022-2023 interims absent (pre-IPO); 4 interims not value-read. Not an insurer (insurtech/fintech) |
| 8120 GULF UNION ALAHLIA (full SAR) | 7 filings read (FY2022 as issued, FY2024, FY2025, 9M 2025, H1 2025, Q1 2026, H1 2026; FY2023 only as comparative). FY2023 filing (image-only) and 9M 2022 scan NOT read, so the IFRS 17 restated FY2022 is unverified | FY2023 and 9M 2022 image-only/unread; 9M 2022 whole-file scan flagged unreadable (content not viewed); 8 other interims textless statement pages | contiguous Q1 2022 to H1 2026; 11 interims by cover only or unread; nothing before 2022 |
| 8180 AL SAGR (full SAR) | 4 filings: FY2023, FY2024, FY2025, Q1 2026 (restated FY2022 as comparative; 2023 EPS restatement verified). FY2022 as issued and H1 2026 image pages NOT read | two whole-file scans (9M 2022, 9M 2023) flagged unreadable (covers only); FY2022 OCR garbled; H1 2026 image-only | contiguous Q1 2022 to H1 2026; 14 files unread or cover only |
| 8100 SAICO (SAR '000; FY2022 in full SAR) | 8 filings: FY2022-FY2025, 9M 2025, H1 2025, Q1 2026, H1 2026; IFRS 17/9 restatement of FY2022, unit change and FY2023 re-presentation declared | all statement pages image-only or garbled OCR; Q1/H1 2022 whole-file scans; 2 non-statement files mislabelled | contiguous Q1 2022 to H1 2026; 10 interims by cover only |
| 8170 AL-ETIHAD (SAR '000; FY2022 in full SAR) | 6 filings: FY2022-FY2025, Q1 2026 (partial), H1 2026; IFRS 17 restatement of FY2022, FY2024 reclassification, unit change declared; going-concern material uncertainty in H1 2026 review report | all statement pages image-only; H1 2026 whole-file scan flagged unreadable but holds report and statements | contiguous Q1 2022 to H1 2026; 12 interims by cover only |

## Defects (general)

1. Annual FY label equals publication year in every annual FS file of all five companies (2023|FY holds FY2022 etc.); 8313 additionally has three annual items in one slot (2024|FY).
2. Whole-file or image-only scans (verified only where a record says so; 8120 FY2023/9M 2022 and 8180 FY2022/H1 2026 pages were not viewable and are unread) classed scanned_unreadable, partial_statements or other_no_statements_found that hold full statements: 8120 9M 2022, 8180 9M 2022 and 9M 2023, 8100 Q1/H1 2022, 8170 H1 2026; the converse (scanned_unreadable files that are infographics or decks, not statements) for 8313.
3. IFRS 4 to IFRS 17 transition: FY2022 restated in the FY2023 filing for 8120, 8180, 8100, 8170; both values are verified only for 8100 and 8170; for 8120 and 8180 the as-issued or restated side was not read and the restatement size is unverified. Further restatements: 8313 H1 2026 note 20 (31 Dec 2025 balance sheet, H1 2025 results), 8170 FY2024 reclassification (note 35).
4. Unit scale change from full SAR (FY2022) to SAR thousands (FY2023 onwards) for 8100 and 8170.
5. Going concern: 8170 H1 2026 material uncertainty (net loss 92.2m, solvency margin below minimum); 8120 and 8180 FY2025 losses with a going-concern basis stated.
6. Interim cash flows are cumulative; Q2 by subtraction not validated (8100, 8313 note).
7. Registry sector null for 8313: Rasan is an insurtech/fintech platform, not an insurer.
8. No duplicate-hash entries for these five symbols beyond the correct period_mismatch flags; no renamed or merged entity found in the pages read (Gulf Union Alahlia and Al-Etihad keep their names throughout).

## Unread (explicit)

Notes in every file except named passages, most equity statements, interims identified by cover only (see each JSON `unread_items` and `files_not_audited_for_values`), Arabic twins (8313), pre-2022 history (no files exist), 8170 Q1 2026 operating cash flows.

## Correction note

A first push of 8120, 8180 and 8100 contained values for image pages that could not be viewed at the time. They were removed in the correction commit; only values read from text layers or viewed images remain. 8100 FY2025 and FY2024 are marked partly read.
