# Batch B004 raw-document statement audit: 4310 KEC, 4190 Jarir, 4263 SAL, 4030 Bahri, 4031 SGS

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Method as in B003: SHA-256 recomputed per document, image-only statement pages rendered and read by eye, born-digital pages read from the text layer (marked per document), identities in `tools/check_transcripts.py` (balance sheet, cash-flow sum and roll, gross profit incl. bunker subsidy, NI split, quarter sums, and a cross-filing detector that fails on any undeclared difference between a filing and the later filing repeating the same period; both values are recorded in `restatements`). Guard test `tests/test_audit_raw_b004_transcripts.py`. Renders are not in git.

Three dimensions are kept separate. No company is claimed complete; unread items are listed in each `<symbol>.json`.

| Symbol | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 4310 KEC | 18 filings (FY2022-25, Q1 2022 - H1 2026): full BS/IS/CF for 11, headline-only for 7 interims (liabilities, CFF, closing cash unread); 21 re-presentations declared (FY2022 CFO -4.66m vs -26.09m, FY2024 PPE and operating loss) | all 18 files contain all primary statements; inventory wrong for 9 (3 "no statements"/scanned, 6 "partial"); 4 annual files labelled publication year | 2022|Q1 to 2026|H1 present (18/18); 2011-2021 never collected |
| 4190 Jarir | 18 filings, BS/IS/CF all read from images, all identities pass; FY2024/Q1-H1 2025 revenue re-presented lower in 2026 filings (gross profit unchanged), EPS restated for 10:1 split | all 18 complete (all statement pages image-only); inventory shows 0 complete, 16 partial, 2 scanned_unreadable; 4 annual labels = publication year | 2022|Q1 to 2026|H1 present; pre-2022 not collected |
| 4263 SAL | 13 statement filings read (FY2022-25, 9M 2023, Q1-9M 2024, Q1-9M 2025, Q1-H1 2026); CFO/CFI re-presented in later filings (11 pairs), revenue and profit never | 13 of 29 files are FS and complete; 2 fully scanned FS and 4 interims wrongly classed; 3 press releases wrongly "scanned_unreadable"; 2 integrated annual reports duplicate FS | 2023|Q1 and 2023|H1 filings absent, no 2022 interims, IPO Nov 2023 |
| 4030 Bahri | 16 filings (FY2022-25, Q1 2023 - H1 2026) BS/IS/CF read; 30 declared differences (EPS after bonus issues, CFO re-presentations, 2026 cost split); FY2025 unaudited year-end interim and audited FS differ in cash flow (CFO 3,256,845 vs 3,214,077) | all 16 complete on image pages; inventory classes 12 of them other/partial/scanned; 4 annual labels = publication year; 2022 interims (9 files) classed scanned, only covers read | 2022-2026 present; 2014-2021 (about 100 files) NOT read; 2011-2013 interim gap |
| 4031 SGS | 18 English filings (FY2022-25, Q1 2022 - H1 2026) read; 24 declared pairs (2022 interims as first printed vs re-presented, PPE Dec 2021, 2025 operating profits in 2026 filings) | all 18 complete; inventory wrong for 10; English FY2022 labelled 2023 but Arabic FY2022 labelled 2022; most periods duplicated in Arabic | 2022|Q1 to 2026|H1 present; 2012-2014, 2017, 2019 gaps; 2011-2021 files not read |

## Defects (general)

1. **Image-only statement pages classified as partial / no statements / scanned_unreadable** (all five companies; 4190 has zero files counted complete although all 18 are). Same root cause as B003: the classifier sees only note text.
2. **Annual period label = publication year** (all five; 4031 only for the English files).
3. **Re-presented comparatives**: the same period has different values in different filings (cash-flow subtotals, cost/gross profit splits, operating profit, PPE, EPS after share splits, 4310 FY2022 CFO). Net profit and total assets are stable. Every pair is declared with both values in `transcripts/<symbol>.json`; the checker fails on undeclared differences.
4. **Two documents for one period** (4030 FY2025 unaudited year-end interim vs audited FS; 4263 and 4030 annual reports re-printing FS; Arabic/English twins) with differing cash flows; the audited filing is authoritative.
5. Press releases and scanned one-page investor material classified as `scanned_unreadable` statements (4263, 4030).

## Unread (explicit)

Notes in every file; equity and OCI statement values; 4310 headline-only interims (liabilities, financing cash flow, closing cash); 4030 files 2008-2021 (about 100) and nine 2022 interim files; 4031 files 2011-2021 (about 40) and Arabic duplicates; 4263 FY2022, H1 2025 and 9M 2025 not independently rendered (text layer); 4263/4190/4310 pre-2022 history not collected. See each JSON `unread_items`.
