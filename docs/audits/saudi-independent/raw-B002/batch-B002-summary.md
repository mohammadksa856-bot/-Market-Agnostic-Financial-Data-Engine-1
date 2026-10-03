# Batch B002 raw-document audit: 8230, 1211, 1302, 2223, 2290

Base: `origin/claude/audit-saudi-raw-coverage`. Raw files read-only from `C:\Users\Mohammed856\finengine-raw-odd`; no data/**, AWS, Supabase or network used.
Per-company records: `8230.json 1211.json 1302.json 2223.json 2290.json` (every file: SHA-256 recomputed and equal to the inventory, page-derived period, kind, image-only pages, inventory vs page verdict). Transcriptions with PDF and printed page numbers and arithmetic checks: `transcripts/t*.py`. Tools: `tools/` (pg, loc, scan, sheet, kv, build). Offline tests: `tests/test_audit_raw_b002.py` (20 pass).

Three dimensions are kept apart. "Verified" means the value was read from the printed page and its sub-totals re-added; nothing is published to compare with.

| Symbol | (1) Value correctness | (2) Document completeness | (3) Company coverage |
|---|---|---|---|
| 8230 Al Rajhi Takaful | Verified: FY2025 BS/IS/CF, H1 2026 and Q1 2026 BS/IS/CF (Q1+Q2=H1 exact), FY2024 BS/IS; headline totals of the three 2022 scans. Not read: SOCI/SOCE/notes of all files, FY2023/FY2022 originals, other interims | 18 of 18 files are genuine statement documents; primary statements sit on IMAGE pages inside text PDFs, so the inventory's partial/no-statement/missing-cash-flow classes (13 files) are false negatives | Q1 2022 to H1 2026 all 18 periods have a statement document (incl. FY2022 to FY2025). 2011-2021 never collected |
| 1211 Ma'aden | Verified: FY2025 BS/P&L/CF (image pages, exact), H1 2026 BS/P&L/CF (text, exact), Q1 2026 totals, FY2024 BS. Not read: FY2022/FY2023 statements, FY2025 OCI/equity, annual reports 2011-2021, other interims | 42 files: 18 FS documents, 11 annual/integrated reports, 13 earnings releases. The six inventory 'scanned unreadable' files are image-only earnings releases, not statements | 18 of 18 periods Q1 2022 to H1 2026 present; FY2011 and FY2015-2021 only as annual-report PDFs (not read); FY2012-2014 and 2011-2021 interims not collected |
| 1302 Bawan | Verified: FY2025 BS/P&L/CF, H1 2026 BS/P&L/CF, Q1 2026 P&L, FY2024 BS/P&L/CF, H1 2022 BS headline. Not read: 14 other statement files, equity/OCI | 18 statement documents + 2 PPA clarification documents; 59cf0d1d (inventory unknown scan) is a real H1 2022 interim | 18 of 18 periods Q1 2022 to H1 2026; nothing earlier |
| 2223 Luberef | Verified: FY2025, H1 2026, Q1 2026 (full, exact); FY2024 BS/P&L/CF; FY2023 and FY2022 BS/P&L. Not read: equity pages, other interims | 19 statement documents (18 periods + an Arabic duplicate of Q1 2026), 8 decks/releases (3 mis-kinded as statements by the classifier) | 18 of 18 periods Q1 2022 to H1 2026; FY2022 statements exist (inventory wrongly says non-statement only); pre-IPO 2022 interims are on a private-company basis |
| 2290 YANSAB | Verified: FY2025, H1 2026, Q1 2026 (exact); FY2024/FY2023/FY2022 headline totals. Not read: 13 other statement files, notes | 20 statement documents (two byte-different duplicate pairs: FY2023, FY2024), 14 decks, 1 board report | 18 of 18 periods Q1 2022 to H1 2026; nothing earlier |

## Defects (page evidence in each company JSON)

1. Publication-year FY labels (all five): SE statement PDFs labelled FY(n+1). The inventory therefore shows a false FY2022 gap and a false "extra" FY2026; 2290's label 2023|FY holds two different fiscal years. Source-dependent: annual reports/decks use the fiscal year.
2. Image-only statement pages inside text PDFs (8230 all files, 1211 FY2024-FY2025, 1302, 2223): the Step-1 classifier marks statements partial/missing. Not proof of absence.
3. Unit scale: 1211 annual in full SAR vs interim in SAR thousands, plus USD columns; 2223 FY2022 original in full SAR vs thousands elsewhere.
4. Restatements: 1302 H1 2025 NI 99,208 original vs 185,302 restated (PPA bargain gain), FY2024 gross profit reclassified; 2223 FY2022/FY2021 re-presented; 8230 H1 2026 bonus issue changes share count.
5. Text-layer sign hazard: 1302 interim cash flows print negatives as `)x(`.
6. Duplicates: 2290 (two pairs), 1211 FY2024 release x2, 2223 Arabic Q1 2026.
7. Inventory 'scanned_unreadable' files that are really: 8230/1302 interim FS (readable by eye), 1211 earnings releases.

## Unread (explicit)

All SOCI/SOCE/notes pages except where listed; every statement file not named as verified (8230: 2023-2025 interims, FY2023/22; 1211: 2022-2025 interims, FY2022/23, annual reports 2011-2021; 1302: 14 files; 2223: 13 interim files; 2290: 13 files); all decks/releases by value. No company is claimed complete beyond "statement document present for the period", and value verification is limited to the documents named above.
