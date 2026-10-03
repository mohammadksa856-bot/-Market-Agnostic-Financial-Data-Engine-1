# Batch B001 - statement-level audit of raw collected documents

Companies: 1810 SEERA, 1111 TADAWUL GROUP, 6010 NADEC, 8210 BUPA ARABIA, 8250 GIG (Gulf Insurance Group).
Branch: claude/audit-saudi-raw-B001 (from claude/audit-saudi-raw-coverage). Raw files read-only; nothing under data/**, AWS or Supabase touched.
Records: `<symbol>.json` in this folder. Tools: pg.py, kv.py, cover.py, periods.py, montage.py, stmt_pages.py, rb.py, build/b_<symbol>.py. Test: tests/test_audit_raw_b001.py (offline, 21 tests).

Three dimensions are kept apart in every record:
1. value correctness: "extractable and verified" means read from the page (text layer or rendered image) and cross-footed; everything else is "not read".
2. document completeness: does the file hold all primary statements, is it the right company/period.
3. company coverage: periods present vs expected, corrected from the pages.

## Per company

| Symbol | Value correctness (verified from pages) | Document completeness | Coverage (corrected) |
|---|---|---|---|
| 1810 SEERA | FY2025 + restated FY2024 comparatives, Q1 2026, H1 2026 (scan, read visually), Q1 2024 (garbled text, read visually), FY2011 scan (totals only; CF subtotals unverified). 13 other files not transcribed. | 16 PDFs complete; Q1 2024 wrongly flagged non-statement; 2 scans readable; 2 xlsx issuer supplements (not primary). | 2022 Q1 - 2026 H1: 18 of 18 interim and FY2022-FY2025 present (inventory said 15 of 56). Gap: FY2012-FY2021 and 2012-2021 interims (supplement xlsx gives FY2018-FY2025 headline series). |
| 1111 TADAWUL | FY2025 (+FY2024), Q1 2026, H1 2026, FY2024 BS from rendered image pages. Most other sets presence-only. | ~44 statement sets; statements are image-only pages (no text layer); ~16 summary bulletins and 7 press releases are not statements (2 are unrelated news). | Q1 2022 - H1 2026 and FY2022-FY2025 present (Arabic and English twins). FY2021 and earlier absent. |
| 6010 NADEC | FY2025 (annual report text + standalone FS BS render), H1 2026, Q1 2026 P&L, FY2021/FY2020 (AR 2021). | Standalone FS and interims are complete but image-only; 8 interim files misclassed other_no_statements; AR 2015 text layer has corrupted digits. | Q1 2022 - H1 2026 and FY2022-FY2025 present; ARs only for FY2015-FY2021; no interims before 2022. |
| 8210 BUPA | FY2025 (+FY2024), Q1 2026, H1 2026 in full; FY2023/FY2022 headline; 9M 2023 and Q1 2024 P&L from images. | 18 of 18 complete; 2 with image-only statement pages (flagged partial). | Q1 2022 - H1 2026 and FY2022-FY2025 present; FY2021 and earlier absent. IFRS 17 restatement documented. |
| 8250 GIG | FY2025 (+FY2024), H1 2026 (rendered), Q1 2026 headline, FY2023/FY2024 headline, FY2022 original headline (rendered). | 18 of 18 complete; formerly AXA Cooperative; 2 scans and 5 files with blank/garbled statement text. | Q1 2022 - H1 2026 and FY2022-FY2025 present; FY2021 and earlier absent. IFRS 17 restatement documented. |

No company is claimed complete beyond the pages listed; each record lists its unread items.

## Defects found (general, apply beyond this batch)

1. FY label equals publication year (all five companies, Saudi-Exchange-sourced FY files): FY2022 is filed as 2023|FY, FY2023 as 2024|FY, FY2024 as 2025|FY, FY2025 as 2026|FY, and one hash can sit under two labels. The inventory therefore shows 2022|FY absent (it exists) and ambiguous 2025|FY. Fix: derive the fiscal year from the cover/period-end text, not the publication date.
2. Statement detection is fooled by notes, TOC and summary pages and misses image-only statement pages (1111, 6010, 8250, partly 8210): the inventory flags (statement_pages, files_with_all_three, text_extractable, other_no_statements, partial_statements_only, missing_primary_statement) are unreliable for these files. About 8 NADEC and several GIG/Bupa/Seera files were called non-statement or partial but are complete when rendered.
3. Text layers can be absent, garbled or digit-corrupted: Seera Q1 2024 (garbled), GIG H1 2026 (garbled), NADEC AR 2015 (digits mapped wrongly, silently plausible).
4. Investor bulletins/press releases are classed as financial statements (Tadawul 7-page and 12-page bulletins; two Tadawul press releases are unrelated news filed under results periods).
5. Restated or revised comparatives: Seera FY2024 and Dec-2023 (three vintages); Bupa and GIG FY2022 and 1 Jan 2022 under IFRS 17 (GIG FY2022 net income 75,802 -> 15,913). Series must carry the vintage.
6. Scale/basis traps: Bupa and GIG statements are in SAR thousands and IFRS 17 (insurance revenue); Tadawul balance sheet grosses up clearing-participant assets and liabilities (about SAR 3.8bn each side).
7. Seera has issuer data-supplement xlsx files (annual FY2018-FY2025, quarterly 1Q22-2Q26) that cover the 2018-2021 gap at headline level (not primary statements, not row-verified).

## Unread items (explicit)

Equity statements and notes in every document; non-transcribed interim sets for each company (period/entity/presence confirmed only); annual reports not transcribed (NADEC 2016-2020, 2022-2024; Tadawul 2022-2024); Arabic twins (Tadawul) not rendered; Seera FY2011 scan cash-flow subtotals at digit level; H1 2026 CFO lines for Tadawul (split) and GIG (derived, not read).
