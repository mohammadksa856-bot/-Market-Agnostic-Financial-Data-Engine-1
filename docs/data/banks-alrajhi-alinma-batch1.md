# Saudi banks — Al Rajhi (1120) and Alinma (1150), batch 1

Branch `claude/banks-alrajhi-alinma-enrichment`, cut from `origin/main` at
`32438bd`. Scope is limited to Al Rajhi Bank (`sa:1120`) and Alinma Bank
(`sa:1150`). No database, deployment, service or worker was changed. Every fact
below was produced by an engine reader from an archived official document and
verified before it was written; nothing was transcribed by hand and nothing was
estimated.

## What changed for the two banks

Measured by a CI-parity bootstrap into a scratch database, before and after.

| | Al Rajhi before | Al Rajhi after | Alinma before | Alinma after |
|---|---|---|---|---|
| Published documents | 2 | 34 | 1 | 31 |
| Current data points | 707 | 2,286 (563 calculated) | 442 | 1,470 (311 calculated) |
| Unique metrics | 92 | 103 | 60 | 89 |
| Fiscal years | 2014–2025 | 2014–2026 | 2018–2025 | 2017–2026 |
| Annual periods | 12 | 12 | 8 | 8 |
| Quarter-end balance sheets | 12 | 38 | 8 | 35 |
| Discrete quarters | none | 10 | none | 16 |
| YTD periods | none | 15 | none | 6 |
| TTM periods | none | none | none | 2 |
| Regulatory capital quarter ends | none | 35 (Dec-2017 → Jun-2026, no gaps) | none | 34 (Dec-2017 → Jun-2026, Sep-2023 missing) |
| Open exceptions in the database | 0 | 0 | 0 | 0 |

Every published Pillar 3 column carries CET1 capital, Tier 1 capital, total
regulatory capital and RWA with the CET1 and Tier 1 ratios; leverage ratio and
its exposure measure cover 35 quarter ends for Al Rajhi and 30 for Alinma, and
LCR/NSFR cover 35 and 26 respectively (the earlier Alinma templates omit those
rows). Whole-directory verification after the write: 1,106 checks passed,
14 warnings, 0 failures. CI-parity bootstrap and `audit --strict-warnings`:
0 failures, and the single audit warning (`enabled_company_coverage` for five US
oil majors) is present on unmodified `main` too.

## Source priority applied

1. **Issuer IR (primary).** Al Rajhi
   [Investor Relations](https://www.alrajhibank.com.sa/en/About-alrajhi-bank/Investor-Relations)
   (quarterly Data Supplements, financial results) and
   [Basel Disclosure](https://www.alrajhibank.com.sa/en/About-alrajhi-bank/Investor-Relations/Basel-Disclosure)
   (Pillar 3); Alinma
   [Financial Statements](https://www.alinma.com/en/About-the-Bank/Financial-Reports/Financial-Statements)
   and [Basel III Disclosures](https://www.alinma.com/en/About-the-Bank/Financial-Reports/Basel-III-Disclosures).
   Both Basel pages were added to `config/companies.json`.
2. **Saudi Exchange.** Not used in this batch; it is the next route for the
   scanned statements listed under exceptions.
3. **Regulator.** Not needed; Pillar 3 is the SAMA-mandated disclosure itself.

## Catalog additions (platform-visible)

The Basel III KM1 template publishes capital and liquidity figures that had no
governed field, so they were held in `excluded_facts` as `catalog_field_missing`.
Added to the `banking_v1` pack, usable by every bank:

* amounts — `cet1_capital`, `tier1_capital`, `leverage_ratio_exposure`,
  `high_quality_liquid_assets`, `net_cash_outflow`, `available_stable_funding`,
  `required_stable_funding`;
* ratios — `leverage_ratio`, `liquidity_coverage_ratio`, `net_stable_funding_ratio`.

`regulatory_capital`, `risk_weighted_assets`, `cet1_ratio`, `tier1_capital_ratio`
and `capital_adequacy_ratio` already existed and were not duplicated; the names
follow the existing catalog style rather than the longer BCBS row titles.
`capital_adequacy_ratio` stays engine-calculated from published
`regulatory_capital` / `risk_weighted_assets`, with the printed ratio kept as a
reconciled cross-check. The KM1 reader now publishes every row that has a field,
and a column is still published only when its printed CET1, Tier 1 and total
capital ratios reproduce from the printed amounts.

## Reusable engine changes

All with regression tests:

* `reading_pillar3.py`
  * row captions may carry `(after transitional arrangement for IFRS 9)` and
    `(CET 1)` with a space (Alinma), `(RWA)-Pillar - 1`, and the caption may wrap
    onto the continuation line that carries the figures (Alinma 2019–2022);
  * a bare `'000s` token declares the thousands unit when the `SAR` word sits
    elsewhere in the page's text order (Al Rajhi 2025–2026);
  * a figure printed without its `%` sign (Al Rajhi Q4-2019 CET1 ratio) is
    dropped from the caption instead of breaking the row match; that column is
    left unpublished because its cell cannot be read.
* `fetching.py` — an explicit `.pdf`/`.xlsx` extension in the URL outranks the
  link text, so Al Rajhi's PDF "Data Supplement" quarters are no longer rejected
  as corrupt workbooks (`_document_content_type`).
* `cli.py` — `reader_source` is set on the XLSX extraction-failure path, which
  previously raised `UnboundLocalError` while reporting the exception.
* `saudi_market.py` — the Saudi Exchange entity selector is matched on the
  symbol's digits, so an issuer listed as `01150` / `SA1150` is found instead of
  failing the whole market-history fetch (Alinma).
* `config/supplements/1120.json`, `1150.json` — both maps now declare
  `period_kinds` (quarterly and YTD columns, not only fiscal years), round to the
  issuer's reported precision, and carry `SAR/share` scale and unit on the
  per-share rows; Alinma's EPS and DPS were previously scaled as millions of SAR.
  Regulatory capital and RWA are no longer mapped from either supplement: the
  Pillar 3 KM1 is the source of record and reconciles its own printed ratios.

## Vintage reconciliation

Pillar 3 filings repeat five quarter ends and each supplement repeats every prior
quarter, so `reconcile_vintages` keeps one source of record per fact (assurance,
then latest period covered, then `filed_at`); statements use `by_period=True`.
The pre-existing `alrajhi-supplement.json` (the 4Q-2025 workbook) is retired
because the 2Q-2026 vintage carries every fact it held — keeping both published
the same figures twice, with the older copy still holding spreadsheet float noise.

## Exceptions

125 candidate documents were reviewed; 64 manifests are published, 8 more were
superseded in full by a later vintage of the same series and are not written.

### Remaining (not published; each needs the proposed action)

| Bank | Periods / documents | Code | Evidence | Proposed action |
|---|---|---|---|---|
| Al Rajhi | 14 statement filings: FY2022 and Q1–Q3 2022, FY2023 and Q2-2023, FY2024 and Q3-2024, FY2025 and Q1–Q3 2025, Q1–Q2 2026 | `image_only_statements` | the primary statement pages carry no text layer (scanned); the reader returns no facts | OCR review or Saudi Exchange filings; the Data Supplement already publishes the same lines |
| Al Rajhi | statements Q1-2023 | `partial_text_layer` | only 15 facts read and the balance-sheet identity fails | same as above; a partial read is not published |
| Al Rajhi | Pillar 3 Q4-2017 | `km1_table_not_found` | the 2017 disclosure predates the BCBS KM1 template | none; Dec-2017 is published from the Q4-2018 filing |
| Al Rajhi | Data Supplement vintages 1Q-2020, 4Q-2020, 1Q-2021, 2Q-2021 | `issuer_identity_mismatch` | FY2016 prints provision −2,142.242 mn against the same sheet's total −7,215.420 mn; from 3Q-2021 the issuer restated it to −2,208.165 mn, which reconciles | none; the later vintages publish FY2016 and every other period they covered |
| Alinma | 10 Pillar 3 filings: Jun-2016, Dec-2016, Mar-2017, Jun-2017, Sep-2017, Mar-2018, Jun-2018, Sep-2018, Mar-2019, Jun-2019 | `km1_table_not_found` | pre-KM1 Basel disclosure format | none for the earliest; Dec-2017 onward is published from later filings |
| Alinma | Pillar 3 Mar-2023 and Sep-2023 | `unit_not_declared` | the KM1 page prints no amount unit, and neither do the neighbouring pages | Sep-2023 capital stays missing; ask the issuer or use the Saudi Exchange copy |
| Alinma | 21 statement filings: Q1-2018, Q1-2019, and every filing from Q3-2021 to Q2-2026 | `image_only_statements` | statement pages are scanned; text begins only at the notes | OCR review or Saudi Exchange; the Data Supplement covers the same lines from FY2021 |
| Alinma | Data Supplement vintages before 4Q-2025 | `source_host_unreachable` | `ir.alinma.com` (Euroland-hosted IR site) does not answer from this network; only the vintage already archived on `main` could be read | retry from a network that can reach the IR host, then add the older vintages |

## Documents and manifests

All archived under `data/raw/SA/<symbol>/documents/<sha256>.<ext>` and indexed in
`data/raw/archive-index.json`. `filed_at` is inferred from PDF creation or workbook
last-modified metadata (`filed_at_basis` in each manifest).

### Al Rajhi Bank (sa:1120) — 33 manifests

| Manifest | Type | Facts | Periods | SHA-256 (first 16) | Official URL |
|---|---|---:|---|---|---|
| `alrajhi-2018-q4-pillar3.json` | regulatory-disclosure | 12 | 2017-12-31 | `a7bff09834386fcd` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2018/Pillar-III-Disclosures-Q4-2018.pdf) |
| `alrajhi-2019-q1-pillar3.json` | regulatory-disclosure | 12 | 2018-03-31 | `a85a585e7a053c57` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/PDFS/investor-relation/Financials/Basel-Disclosures-en/Q1_Pillar_III_Report_2019.pdf) |
| `alrajhi-2019-q2-pillar3.json` | regulatory-disclosure | 24 | 2018-06-30 → 2019-03-31 (2) | `5890447712399372` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/PDFS/investor-relation/Financials/Basel-Disclosures-en/2019_Q2_Pillar_III_Report.pdf) |
| `alrajhi-2019-q3-pillar3.json` | regulatory-disclosure | 12 | 2018-09-30 | `68bb45381caae528` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/PDFS/investor-relation/Financials/Basel-Disclosures-en/2019-Q3-Pillar-III-Report-final.pdf) |
| `alrajhi-2019-q4-pillar3.json` | regulatory-disclosure | 12 | 2018-12-31 | `d14f088edd205ace` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2019/2019-Q4-Pillar-III-Report-final.pdf) |
| `alrajhi-2020-q2-pillar3.json` | regulatory-disclosure | 12 | 2019-06-30 | `e5d544f729e09f4b` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2020/Pillar_III_Disclosures-June_30_2020.pdf) |
| `alrajhi-2020-q3-pillar3.json` | regulatory-disclosure | 12 | 2019-09-30 | `5e7e8ae698039575` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2020/Pillar_III_Disclosures-September_30_2020.pdf) |
| `alrajhi-2020-q4-pillar3.json` | regulatory-disclosure | 12 | 2019-12-31 | `0b51b47966ee45f0` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/PDFS/investor-relation/Financials/Basel-Disclosures-en/2020-Q4-Pillar-III-Report.pdf) |
| `alrajhi-2021-q1-pillar3.json` | regulatory-disclosure | 12 | 2020-03-31 | `e9dd699b5cacc022` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/PDFS/investor-relation/Financials/Basel-Disclosures-ar/2021_Q1_Pillar_III_Report.pdf) |
| `alrajhi-2021-q2-pillar3.json` | regulatory-disclosure | 12 | 2020-06-30 | `cd2bf0ccd0ac6465` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/PDFS/investor-relation/Financials/Basel-Disclosures-ar/2021_Q2_Pillar_III_Report.pdf) |
| `alrajhi-2021-q3-pillar3.json` | regulatory-disclosure | 12 | 2020-09-30 | `7c62fb25c3f377ca` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2021/Q3/2021_Q3_Pillar_III_Report.pdf) |
| `alrajhi-2021-q4-pillar3.json` | regulatory-disclosure | 12 | 2020-12-31 | `ff88c05fcf6df1d6` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2021/Q4/2021_Q4_Pillar_III_Report.pdf) |
| `alrajhi-2022-q1-pillar3.json` | regulatory-disclosure | 12 | 2021-03-31 | `0c7de76560754345` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/PDFS/investor-relation/Financials/Basel-Disclosures-ar/2022_Q1_Pillar_III_Disclosures.pdf) |
| `alrajhi-2022-q2-pillar3.json` | regulatory-disclosure | 12 | 2021-06-30 | `de8b2a0b311259dd` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2022/2022-Q2-Pillar-3-Disclosures.pdf) |
| `alrajhi-2022-q3-pillar3.json` | regulatory-disclosure | 12 | 2021-09-30 | `cbafdd0a9669c63a` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2022/Pillar-III-Disclosures-Q3-2022-Final.pdf) |
| `alrajhi-2022-q4-pillar3.json` | regulatory-disclosure | 27 | 2021-12-31 → 2022-09-30 (4) | `e96f81a5e29a5410` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2022/2022-Q4-Pillar-III.pdf) |
| `alrajhi-2023-q1-pillar3.json` | regulatory-disclosure | 8 | 2022-03-31 | `e1c291f20260be98` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/Home/Personal/Offers/2023/Q1-2024/Pillar_III_Disclosures.pdf) |
| `alrajhi-2023-q2-pillar3.json` | regulatory-disclosure | 8 | 2022-06-30 | `59e27ec49f7c11c6` | [link](https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Images/o/Pillar%20III%20Disclosures%20Q2-2023.pdf) |
| `alrajhi-2023-q3-pillar3.json` | regulatory-disclosure | 8 | 2022-09-30 | `fb9e2efc2efdba7c` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2023/Pillar-III-Q3-2023.pdf) |
| `alrajhi-2023-q3.json` | interim-report | 33 | 2023-09-30 | `8c8bf4bcd40df90f` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Financial-Materials/2023/Q3/Financial-Results/353_0_2023-10-30_17-24-32_En.pdf) |
| `alrajhi-2023-q4-pillar3.json` | regulatory-disclosure | 14 | 2022-12-31 | `a42fa0f794834f56` | [link](https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Images/o/Pillar%20III%20Disclosures%20Q4-2023.pdf) |
| `alrajhi-2024-q1-pillar3.json` | regulatory-disclosure | 14 | 2023-03-31 | `b9348b31f9159c34` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/Home/Personal/Offers/2023/Q1-2024/Pillar-III-Disclosures-Q1-2024.pdf) |
| `alrajhi-2024-q2-pillar3.json` | regulatory-disclosure | 14 | 2023-06-30 | `35be432357b148a6` | [link](https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Images/o/Pillar%20III%20Disclosures%20Q2-2024.pdf) |
| `alrajhi-2024-q2.json` | interim-report | 40 | 2024-06-30 | `76558c1f4730d8e1` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Financial-Materials/2024/Q2/Financial-Results/2Q24-Financial-statement---EN.pdf) |
| `alrajhi-2024-q3-pillar3.json` | regulatory-disclosure | 14 | 2023-09-30 | `5e5f8ecc97513181` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Annual-Reports/Pillar-III-Disclosures-Q3-2024.pdf) |
| `alrajhi-2024-q4-pillar3.json` | regulatory-disclosure | 14 | 2023-12-31 | `a47aea404b798749` | [link](https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Images/o/Pillar%20III%20Disclosures%20Q4-2024.pdf) |
| `alrajhi-2025-q1-pillar3.json` | regulatory-disclosure | 14 | 2024-03-31 | `49730c6a2956cdf4` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlrajhiPWS/Shared/Home/Personal/Offers/2025/Pillar-III-Disclosures-Q1-2025/Pillar-III-Disclosures-Q1-2025.pdf) |
| `alrajhi-2025-q2-pillar3.json` | regulatory-disclosure | 14 | 2024-06-30 | `5133fe97bb008703` | [link](https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Images/o/Pillar%20III%20Disclosures%20Q2-2025.pdf) |
| `alrajhi-2025-q3-pillar3.json` | regulatory-disclosure | 14 | 2024-09-30 | `4ab19aa680645950` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2025/Pillar-III-Disclosures-Q3-2025.pdf) |
| `alrajhi-2025-q4-pillar3.json` | regulatory-disclosure | 14 | 2024-12-31 | `663bce4399494e53` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2025/Pillar-III-Disclosures-Q4-2025.pdf) |
| `alrajhi-2026-q1-pillar3.json` | regulatory-disclosure | 14 | 2025-03-31 | `2aa91e2ceb0ae8ef` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2026/Pillar-III-Disclosures-Q1-2026.pdf) |
| `alrajhi-2026-q2-pillar3.json` | regulatory-disclosure | 70 | 2025-06-30 → 2026-06-30 (5) | `7ec728c0cefee5a7` | [link](https://www.alrajhibank.com.sa/en/-/media/Project/AlRajhi/ARBRevamp/Investor-Relation/Basel_Reports/2026/Pillar-III-Disclosures-Q2-2026-1.pdf) |
| `alrajhi-2026-q2-supplement.json` | data-supplement | 1152 | 2014-12-31 → 2026-06-30 (32) | `9d6a222116cbe796` | [link](https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Images/o/ARB%20External%20Data%20Supplement%20-%202Q2026.xlsx) |

### Alinma Bank (sa:1150) — 31 manifests

| Manifest | Type | Facts | Periods | SHA-256 (first 16) | Official URL |
|---|---|---:|---|---|---|
| `alinma-2018-fy.json` | financial-statements | 25 | 2018-12-31 | `fe2c8548cb0621b2` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2018/FSEnglish2018FinalwithAuditReport.pdf) |
| `alinma-2018-q2.json` | interim-report | 27 | 2018-06-30 | `a6f2b183dd7b9b30` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2018/FS-Q-2_2018_-_English-Final_with_AR.pdf) |
| `alinma-2018-q3.json` | interim-report | 24 | 2018-09-30 | `8eae5c4221d8d630` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2018/FS-Q-3_2018_-_English-Final.pdf) |
| `alinma-2019-fy.json` | financial-statements | 29 | 2019-12-31 | `13a6ea5f65a40a19` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2019/Signed_FS_2019_-_FinalSigned_FS-English_2019.pdf) |
| `alinma-2019-q2.json` | interim-report | 39 | 2019-06-30 | `ae1cabb24272054a` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2019/FSQ22019Englishv11zakatinPLFinal.pdf) |
| `alinma-2020-fy.json` | financial-statements | 24 | 2020-12-31 | `116d48bf0a7fb015` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2020/20210218_FS-English_2020_Final.pdf) |
| `alinma-2020-q1.json` | interim-report | 25 | 2020-03-31 | `89d71c740db890b5` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2020/20200514_FS-Q-1_2020_-_English_FS_v16_-_Final.pdf) |
| `alinma-2020-q2.json` | interim-report | 36 | 2020-06-30 | `bdf81ec9b72d82ad` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2020/20200730_FS-Q-2_2020-_English_v9_-_Final_with_Audit_report.pdf) |
| `alinma-2020-q3.json` | interim-report | 37 | 2020-09-30 | `ebac72dd938ce073` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Financial-Statements--EN/2020/20201025FSQ32020Englishv75Final.pdf) |
| `alinma-pillar-3-disclosure-dec-2021-final-pillar3.json` | regulatory-disclosure | 13 | 2020-12-31 | `28b16b54ecd27b2d` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma_Pillar_3-_disclosure-Dec_2021-Final.pdf) |
| `alinma-pillar-3-disclosure-dec-2022-final-pillar3.json` | regulatory-disclosure | 47 | 2021-12-31 → 2022-12-31 (5) | `424fbfc8a6437a5a` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma_Pillar_3-_disclosure-Dec_2022-Final.pdf) |
| `alinma-pillar-3-disclosure-dec-2024-final-pillar3.json` | regulatory-disclosure | 6 | 2023-12-31 | `06cc59d9f8956e00` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma-Pillar-3--disclosure-Dec-2024---Final.pdf) |
| `alinma-pillar-3-disclosure-dec-2025-final-pillar3.json` | regulatory-disclosure | 7 | 2024-12-31 | `520d9288489c59e0` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma-Pillar-3--disclosure-Dec-2025---Final.pdf) |
| `alinma-pillar-3-disclosure-jun-2023-final-pillar3.json` | regulatory-disclosure | 30 | 2022-06-30 → 2023-06-30 (5) | `78bc5fbab476a542` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma_Pillar_3-_disclosure-Jun_2023-Final.pdf) |
| `alinma-pillar-3-disclosure-june-2020-final-pillar3.json` | regulatory-disclosure | 13 | 2019-06-30 | `10e01d507029dc13` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma_Pillar_3-_disclosure-June_2020-Final.pdf) |
| `alinma-pillar-3-disclosure-june-2021-final-pillar3.json` | regulatory-disclosure | 13 | 2020-06-30 | `061dcef3f3f3feae` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma_Pillar_3-_disclosure-June_2021-Final.pdf) |
| `alinma-pillar-3-disclosure-june-2022-final-pillar3.json` | regulatory-disclosure | 13 | 2021-06-30 | `76abb97345dd748d` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma_Pillar_3-_disclosure-June_2022-Final.pdf) |
| `alinma-pillar-3-disclosure-june-2025-pillar3.json` | regulatory-disclosure | 7 | 2024-06-30 | `7e19b32f9433f313` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma-Pillar-3--disclosure-June-2025.pdf) |
| `alinma-pillar-3-disclosure-june-2026-pillar3.json` | regulatory-disclosure | 70 | 2025-06-30 → 2026-06-30 (5) | `19f15f4823cc6b73` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma-Pillar-3--disclosure-June-2026.pdf) |
| `alinma-pillar-3-disclosure-mar-2025-pillar3.json` | regulatory-disclosure | 8 | 2024-03-31 → 2024-06-30 (2) | `70fb0471d486e0ff` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/alinma-Pillar-3--disclosure-Mar-2025.pdf) |
| `alinma-pillar-3-disclosure-mar-2026-final-v4-pillar3.json` | regulatory-disclosure | 7 | 2025-03-31 | `e868c227641fcbe6` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma-Pillar-3--disclosure-Mar-2026---Final-v4.pdf) |
| `alinma-pillar-3-disclosure-sep-2025-pillar3.json` | regulatory-disclosure | 10 | 2024-09-30 → 2025-03-31 (3) | `2c1af01a5ec9b051` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma-Pillar-3--disclosure-Sep-2025.pdf) |
| `alinma-pillar-3-disclosures-september-2019-pillar3.json` | regulatory-disclosure | 26 | 2018-09-30 → 2018-12-31 (2) | `6ac29c0ed95a8069` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Pillar_3_disclosures_-_September_2019.pdf) |
| `alinma-pillar-3-qualitative-and-quantitative-disclosu-pillar3.json` | regulatory-disclosure | 13 | 2017-12-31 | `b7f9ee9c7f887bac` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Basel_III_Pillar_3-Qualitative_and_Quantitative_disclosure-December_2018.pdf) |
| `alinma-pillar-3-tables-final-march-2019-pillar3.json` | regulatory-disclosure | 26 | 2018-03-31 → 2018-06-30 (2) | `b4e29aa6f320c18e` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Alinma_Pillar_3_tables-Final-March_2019.pdf) |
| `alinma-pillar-3-tables-final-march-2020-pillar3.json` | regulatory-disclosure | 13 | 2019-03-31 | `d5521eb73794eb08` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Pillar_3_tables-Final-March_2020.pdf) |
| `alinma-pillar-3-tables-final-march-2021-pillar3.json` | regulatory-disclosure | 13 | 2020-03-31 | `97fa4fc90acee440` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Pillar_3_tables-Final-March_2021.pdf) |
| `alinma-pillar-3-tables-final-march-2022-pillar3.json` | regulatory-disclosure | 13 | 2021-03-31 | `94486d46c3f01481` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Pillar_3_tables-Final-March_2022.pdf) |
| `alinma-pillar-3-tables-final-sept-2020-pillar3.json` | regulatory-disclosure | 26 | 2019-09-30 → 2019-12-31 (2) | `adb231211d0b1c23` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Pillar_3_tables-Final-Sept_2020.pdf) |
| `alinma-pillar-3-tables-final-september-2021-pillar3.json` | regulatory-disclosure | 26 | 2020-09-30 → 2021-09-30 (2) | `a85ff5038946145e` | [link](https://www.alinma.com/-/media/Project/Alinma/PDF-Files/Basel-III-Disclosures-EN/Pillar_3_tables-Final-September_2021.pdf) |
| `alinma-supplement.json` | data-supplement | 493 | 2021-12-31 → 2025-12-31 (14) | `451026b7baa73614` | [link](https://ir.alinma.com/media/k0wfq1td/alinma-data-supplement-4q-2025.xlsx) |
