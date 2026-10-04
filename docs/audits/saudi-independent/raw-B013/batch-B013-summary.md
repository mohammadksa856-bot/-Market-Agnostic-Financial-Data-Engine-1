# Batch B013 raw-document statement audit: 6017 Jahez, 6018 Sport Clubs, 6016 Burgerizzr, 6004 Catrion, 6012 Raydan

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Image-only statement pages and whole-file scans were rendered and read by eye; born-digital pages were read from the text layer and tied by arithmetic. Transcripts in `transcripts/`, checks in `tools/check_transcripts.py` (BS identity, cash-flow sum and roll with FX, gross profit, profit before zakat to net profit incl. discontinued, owners + NCI, cross-filing comparatives that fail on any undeclared difference, Q1 + Q2 = H1 rolls; all pass), guard test `tests/test_audit_raw_b013.py`. Per-company `documents[]` carry the full SHA-256 verified against the raw file; `files_not_audited_for_values[]` lists every other inventory file.

Three dimensions are kept separate. No company is claimed complete.

| Symbol (full SAR) | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 6017 JAHEZ | 8 filings: FY2022 to FY2025 (+ FY2025 AR copy), H1 2025, Q1 and H1 2026; FY2022 EPS 5.7 vs 0.29 declared | FY2025 and FY2023 FS image-only/scan; FY2022 and FY2021 FS scans; 3 interims classed partial though complete | FY2021 to FY2025; interims with gaps (no 2022 Q1/9M, 2023 Q1/9M, 2024 Q1); 39 files not value-read |
| 6018 SPORT CLUBS | 7 filings: FY2022 (standalone as issued), FY2023, FY2024 (as issued), FY2025, H1 2025, Q1 and H1 2026; two restatement chains recorded | H1 2025 statement pages image-only; 3 FY files share label 2025\|FY | FY2022 to FY2025, 2024 H1 to 2026 H1; no Q1 2024; 14 files not value-read |
| 6016 BURGERIZZR | 7 filings: FY2022 to FY2025, H1 2025, Q1 and H1 2026; FY2024 and 2025 restated (Iqama fees) | all 7 filings image-only statements, mis-classed | FY2022 to FY2025, interims 2022 H1 to 2026 H1; no 2022 Q1/9M, 2023 Q1; 10 files not value-read |
| 6004 CATRION | 7 filings: FY2022 to FY2025, H1 2025 (headline), Q1 and H1 2026; no restatement | annual FS and Q1 2026 image-only; H1 2026 and H1 2025 text layers scrambled/incomplete | FY2022 to FY2025, every interim 2022 Q1 to 2026 H1 has a file; 11 files not value-read |
| 6012 RAYDAN | 8 filings: FY2022 to FY2025, Q1 and H1 2025, Q1 and H1 2026; cash-flow reclassifications and discontinued-operations re-presentation declared | 7 of 8 image-only statement pages, mis-classed; 2 scans | FY2022 to FY2025, every interim 2022 Q1 to 2026 H1 has a file; 10 files not value-read |

## Defects (general)

1. Image-only statement pages classed other_no_statements_found, partial_statements, results_announcement or scanned_unreadable: all five companies.
2. Annual FY label equals publication year for FS files in all five (6017 mixes conventions: annual reports use the fiscal year, one slot holds four documents; 6018 has three FY files under 2025|FY).
3. Restated or re-presented comparatives: 6018 (FY2024; FY2022/FY2021), 6016 (FY2024; 6M 2025), 6012 (FY2023 cash, FY2022 cash flow, 6M 2025 discontinued operations, FY2025 balance sheet), 6017 (FY2022 EPS), 6004 none.
4. Garbled or incomplete text layers: 6004 H1 2026 and H1 2025.
5. Duplicate registry symbols: 36 of 47 files under 6017 are byte-identical to all files in archive/SA/9526 (no inventory record; absent from live list; Jahez was first on Nomu, symbol history inferred not verified); two 6016 files identical to archive/SA/9520. Entities verified from pages.
6. Interim cash-flow Q2 by subtraction not valid (6017, 6016, 6004, 6012); company renames (6004 Saudi Airlines Catering, 6016 Bait Alshateera, 6012 Ridan).

## Unread (explicit)

Notes in every file; most equity statements; Arabic twins; annual reports; the long lists of unread interims and early history in each JSON `unread_items` and `files_not_audited_for_values`.
