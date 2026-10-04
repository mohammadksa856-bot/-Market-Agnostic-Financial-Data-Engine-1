# Batch B008 raw-document statement audit: 2380 Petro Rabigh, 2350 Saudi Kayan, 4240 Cenomi Retail, 4323 Sumou, 4020 Al Akaria

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Statement pages without a usable text layer were rendered and read by eye; born-digital pages were read from the text layer with identity checks and visual verification where cells were garbled. Page transcripts are in `transcripts/`, arithmetic and cross-filing checks in `tools/check_transcripts.py` (BS identity, cash-flow sum and roll, NI split, comparatives versus the filing that reports the period with explicit restated flags, Q1+Q2=H1 rolls; all pass), guard test `tests/test_audit_raw_b008.py`. Per-company `documents[]` carry the full SHA-256 (recomputed against the raw file), PDF page and printed page.

Three dimensions are kept separate. No company is claimed complete; every record lists unread items.

| Symbol | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 2380 PETRO RABIGH (SAR thousand) | FY2025, FY2024, H1 2026 in full; Q1 2026 and original H1 2025 income statement only | statement pages image-only in 10 recent files flagged partial; 4 whole-file scans 2019-2020 and 2 H1 2022 scans unread; duplicate Q1 2022 and H1 2022 files | files for 2019 Q1/9M, 2020, 2022 to 2026 H1; 2021 interims and FY2020 absent; only FY2024 onward value-read |
| 2350 SAUDI KAYAN (SAR thousand) | FY2025, FY2024, H1 2026 in full, Q1 2026 income statement; no restatement found | statements image-only in annual and some interim files; 9 earnings releases are not statements; Q1 2022 whole-file scan | 18 periods 2022 Q1 to 2026 H1 have a file; nothing before 2022 Q1; 4 of 18 value-read |
| 4240 CENOMI RETAIL (full SAR) | 7 filings: FY Mar-2022, 9M transition 2022, FY2023, FY2024, FY2025, Q1 2026, H1 2026 | FY2024 image-only; ~40 interim and 17 scan files unread; Q1 2026 and FY2023 twins | fiscal year-end changed from March to December in 2022; as-filed vs restated versions for Mar-2022, Dec-2022, FY2023, FY2024, Dec-2025; nothing before 2020 |
| 4323 SUMOU (full SAR) | FY2024, FY2025, Q1 2026, H1 2026 | whole-file scans; H1 2026 text layer scrambled; 11 further scans identified by cover only | 15 periods 2022 H1 to 2026 H1 have a file; 4 value-read; 2020-2021 and 2022 Q1/9M absent |
| 4020 AL AKARIA (SAR thousand) | FY2023, FY2024, FY2025, Q1 2026, H1 2026 (FY2022 as comparative) | born-digital except 6 scans; two 2025 interims flagged partial not opened | 2022 Q1 to 2026 H1 present in files; 5 value-read; nothing before 2022 Q1 |

## Defects (general)

1. **Annual label equals publication year** in 2380, 2350, 4323, 4020 (FY(n) filed in n+1 is labelled n+1). 4240 is different: it changed year-end from 31 March to 31 December through a nine-month transition period to 31 Dec 2022, and the collector labels the transition filing 2023|FY; the inventory still carries fiscal_year_end_month 3.
2. **Image-only statement pages in text PDFs or whole-file scans** misclassify files as partial or unreadable (all five).
3. **Restated and re-presented comparatives**: 2380 revenue netted for marketer charge-backs (FY2024 39,349,068 -> 38,662,135; H1 2025 15,544,215 -> 15,160,959); 4240 five generations of restated balance sheets (31 Mar 2022 total assets 8,546,601,232 / 8,241,206,787 / 7,362,827,074; 31 Dec 2025 total assets 4,023,468,164 / 4,025,727,650 / 4,544,423,857 after a lease-term correction); 4323 FY2024 cash 184,062,121 -> 3,282,421 and CFO 70,289,671 -> 3,148,091 (restricted cash reclass); 4020 FY2024 CFO 735,698 -> 928,030 (finance charges paid moved to financing). 2350 shows none for FY2024.
4. **Q1+Q2=H1 does not hold across restatement**: 4240 (Q1 2026 filed before the H1 restatement: loss -47,329,981 + -78,418,176 vs H1 -131,024,107). It holds exactly for 2380, 2350, 4323, 4020.
5. **Unit scale**: 2380, 2350, 4020 in SAR thousand; 4240, 4323 in full SAR; no annual versus interim difference found.
6. **Garbled or scrambled text layers**: 4323 H1 2026 (digits split, would parse wrong), 4020 isolated cells, 4240 FY2025 merged rows; render before trusting.
7. **Printed inconsistency**: 4020 FY2025 prints a 2024 CFO subtotal (959,311) that does not reconcile (928,030).
8. **Duplicates and renames**: 4240 Q1 2026 and FY2023 twin files; 4240 renamed AFG International Company; 4323 files also stored under symbol 9511 (same issuer, verified from covers).
9. **Cash definitions**: BS cash differs from cash-flow ending cash for 4240 at Dec 2022 and Dec 2023 (bank overdraft).

## Unread (explicit)

Notes in every file; most equity statements; all annual reports; Arabic files; per-company lists in each JSON `unread_items`. Not done: value reading of most interims 2019-2025 for all five companies, whole-file scans identified only by cover (2380: 4+2; 4240: ~17; 4323: 11; 4020: 6; 2350: 1).
