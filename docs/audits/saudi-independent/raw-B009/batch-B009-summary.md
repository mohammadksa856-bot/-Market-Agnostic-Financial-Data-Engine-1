# Batch B009 raw-document statement audit: 4300 Dar Alarkan, 4200 Aldrees, 4280 Kingdom, 4003 Extra, 4007 Alhammadi

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Image-only and whole-file-scan statement pages were rendered and read by eye; born-digital pages were read from the text layer and tied by arithmetic. Transcripts in `transcripts/`, checks in `tools/check_transcripts.py` (BS identity, cash-flow sum and roll, gross profit, profit before tax to net profit incl. discontinued, owners + NCI, cross-filing comparatives with explicit restated flags, Q1+Q2=H1 rolls; all pass), guard test `tests/test_audit_raw_b009.py`. Per-company `documents[]` carry the full SHA-256 verified against the raw file; `files_not_audited_for_values[]` lists every other inventory file with what was (or was not) identified.

Three dimensions are kept separate. No company is claimed complete.

| Symbol | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 4300 DAR ALARKAN (SAR thousand) | 8 filings: FY2020 and FY2021 (text), FY2022 to FY2025 (rendered), Q1 and H1 2026 | 54 of 65 files are whole-file scans classed unreadable but hold full statements; FY2023 CF 2023 column clipped in the FY2024 file | files 2014 to 2026 H1 by label; 57 files not value-read; 2006-2013 absent |
| 4200 ALDREES (full SAR) | 6 filings: FY2022, FY2023, FY2024 (original), FY2025, Q1 and H1 2026; FY2024 restated in FY2025 filing | 37 of 39 files scans; all opened have 4 statements; FY2022 copy sits in 2023|FY | 22 periods 2021 Q1 to 2026 H1 have a file; 33 files not value-read |
| 4280 KINGDOM (SAR thousand) | 5 filings: FY2023, FY2024, FY2025, Q1 and H1 2026; no restatement found | all 45 files image-only statements; inventory unreliable; 24 files without fiscal year; labels 2029 and 2006 wrong | 22 periods 2021 Q1 to 2026 H1 have a file; 40 files not value-read |
| 4003 EXTRA (SAR thousand) | 6 filings: FY2021, FY2022, FY2024, FY2025, H1 2025, H1 2026 | FY2024 has a garbled OCR text layer; FY2023 standalone FS file absent | FY2018 to FY2025 (no FY2023 FS) and interims 2022-2026; 16 files not value-read |
| 4007 ALHAMMADI (full SAR) | 9 filings: FY2022 to FY2025, Q1/H1/9M 2025, Q1/H1 2026 | Q1 2025 text layer drops the current-period column; image-only statements in several files | 21 periods 2021 Q1 to 2026 H1 have a file; 24 files not value-read |

## Defects (general)

1. Annual FY label = publication year for 4007, 4300, 4280, 4200 (from 2022/2023); 4003 labels are correct.
2. Image-only statement pages and whole-file scans classed partial, unreadable or no-statements (all five).
3. Restated or re-presented comparatives: 4200 FY2024 (net income 338,047,048 -> 344,650,993, equity -62.7m) and FY2022; 4300 FY2022/FY2023 cash flows (lease principal and 9,902 reclassified); 4003 EPS (FY2021, H1 2025); 4007 FY2022/FY2023 line items.
4. Text layer errors: 4007 Q1 2025 income statement shows the 2024 column as current; 4003 FY2024 OCR corruption.
5. Cash definition: 4280 annual cash flow excludes restricted cash while interim opening cash equals the balance sheet; 4280 Q1 vs H1 cash-flow lines differ in presentation.
6. Wrong fiscal-year labels (4280: 2029, 2006), duplicates and Arabic twins counted as separate period files.

## Unread (explicit)

Notes in every file; most equity statements; all annual reports; Arabic files; the long lists of unread interims and pre-2021 history in each JSON `unread_items` and `files_not_audited_for_values`.
