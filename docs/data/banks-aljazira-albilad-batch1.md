# Saudi banks batch: Bank AlJazira and Bank Albilad

Scope: `sa:1020` (Bank AlJazira) and `sa:1140` (Bank Albilad). Every published fact
comes from a document the issuer published itself, archived under
`data/raw/SA/<symbol>/documents/` and recorded in `data/raw/archive-index.json` with
its official URL, SHA-256, media type, byte size and the index page it was taken from.
No value is estimated, and nothing is published that the accounting verifier rejects.

## Before and after

| Bank | Documents | Facts | Metrics | Period ends | Span |
| --- | --- | --- | --- | --- | --- |
| Bank AlJazira (`sa:1020`) before | 1 | 86 | 43 | 2 | 2024-12-31..2025-12-31 |
| Bank AlJazira (`sa:1020`) after | 39 | 1063 | 61 | 39 | 2008-06-30..2026-06-30 |
| Bank Albilad (`sa:1140`) before | 1 | 86 | 43 | 2 | 2024-12-31..2025-12-31 |
| Bank Albilad (`sa:1140`) after | 60 | 1573 | 61 | 37 | 2011-12-31..2026-06-30 |

## Current data points, from a CI-parity bootstrap

Counted the way `audit` counts them: rows in `data_points` with `is_current = 1`, in a
scratch database built from `data/imports` alone. The TTM column is the engine's own
derivation - no manifest carries a TTM fact.

| Bank | Current points | Calculated | Metrics | Fiscal years | Annual | Instant | Quarter | YTD | TTM | Open exceptions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bank AlJazira before | 133 | 47 | 73 | 2024-2025 | 2 | 2 | 0 | 0 | 0 | 0 |
| Bank AlJazira after | 1264 | 201 | 93 | 2008-2026 | 149 | 770 | 230 | 108 | 7 | 0 |
| Bank Albilad before | 133 | 47 | 73 | 2024-2025 | 2 | 2 | 0 | 0 | 0 | 0 |
| Bank Albilad after | 1959 | 386 | 98 | 2011-2026 | 307 | 1038 | 290 | 308 | 16 | 0 |

The eight banks merged before this batch are unchanged, measured in the same database:
SAB 231, SNB 838, Riyad 2,255, SAIB 1,418, Al Rajhi 2,286, Alinma 1,470, BSF 2,573,
ANB 3,937 current data points, each matching the figure its own batch published.

## Period kinds, sources and regulatory coverage

**Bank AlJazira**

- Period kinds: fy 104, instant 649, quarter 210, ytd 100
- Documents by kind: Data Supplement 6, Financial statements 1, Interim statements 6, Pillar 3 (KM1) 26
- Excluded facts retained as evidence: 2397
- Capital metrics (8): `cet1_capital`, `cet1_ratio`, `leverage_ratio`, `leverage_ratio_exposure`, `regulatory_capital`, `risk_weighted_assets`, `tier1_capital`, `tier1_capital_ratio`
- Liquidity metrics (6): `available_stable_funding`, `high_quality_liquid_assets`, `liquidity_coverage_ratio`, `net_cash_outflow`, `net_stable_funding_ratio`, `required_stable_funding`
- Pillar 3 quarter ends: 33, 2018-06-30..2026-06-30

**Bank Albilad**

- Period kinds: fy 189, instant 798, quarter 290, ytd 296
- Documents by kind: Annual report 3, Financial statements 6, Interim statements 20, Pillar 3 (KM1) 31
- Excluded facts retained as evidence: 1425
- Capital metrics (8): `cet1_capital`, `cet1_ratio`, `leverage_ratio`, `leverage_ratio_exposure`, `regulatory_capital`, `risk_weighted_assets`, `tier1_capital`, `tier1_capital_ratio`
- Liquidity metrics (6): `available_stable_funding`, `high_quality_liquid_assets`, `liquidity_coverage_ratio`, `net_cash_outflow`, `net_stable_funding_ratio`, `required_stable_funding`
- Pillar 3 quarter ends: 35, 2017-12-31..2026-06-30

## Sources

Issuer sites only; Tadawul was not reachable from this network (HTTP 403) and no
aggregator or news site was used.

| Bank | Index page |
| --- | --- |
| Bank AlJazira | https://ir.aljazirabank.com.sa/en/financial-information/financial-results/ |
| Bank AlJazira | https://ir.aljazirabank.com.sa/en/financial-information/basel-iii-disclosures/ |
| Bank Albilad | https://www.bankalbilad.com.sa/en/about/investor-relations/financial-information/Pages/financial-results.aspx |
| Bank Albilad | https://www.bankalbilad.com.sa/en/about/investor-relations/financial-information/Pages/basel-disclosures.aspx |
| Bank Albilad | https://www.bankalbilad.com.sa/en/about/investor-relations/Pages/annual-reports.aspx |

Bank Albilad publishes no data supplement; its quarterly spine is the statements plus
the Pillar 3 disclosures. Bank AlJazira's primary statements are scanned images, so its
spine is the Data Supplement workbooks plus the Pillar 3 KM1 tables.

## Engine changes, and the test that pins each one

All are in `tests/test_bank_aljazira_layouts.py` unless stated otherwise.

| Change | Why | Test |
| --- | --- | --- |
| `SAR,000` accepted as a thousands declaration | AlJazira writes the KM1 unit with a comma | `test_comma_form_of_the_thousands_declaration` |
| Quarter headers punctuated `Q1, 2022` | the comma stands where others print a space | `test_comma_punctuated_quarter_headers_are_dated` |
| Columns tagged `T, T-1 ... T-4` anchored on the quarter the page states | AlJazira prints position tags and no dates; the anchor is read, not guessed | `test_relative_tag_columns_anchor_on_the_quarter_stated_on_the_page`, `test_relative_tags_are_not_dated_when_the_page_names_two_quarters` |
| Amounts carrying both separators and decimals (`12,545,339.89`) | otherwise the figure joins the caption and the row is lost | `test_amount_carrying_separators_and_decimals_is_a_figure` |
| Caption closing a bracket it never opened | `Common Equity Tier 1 (CET1) )` | `test_caption_closing_a_bracket_it_never_opened_is_read` |
| Unit taken from the document when the KM1 page states none | AlJazira declares it on the report's other templates; a document declaring nothing, or both units, still fails | `test_unit_is_taken_from_the_document_when_the_km1_page_omits_it`, `test_a_document_declaring_no_unit_anywhere_still_fails` |
| Worksheet name matched with whitespace collapsed | the supplement tab is shipped as `Income Statment ` one quarter and `Income Statment` the next | `test_worksheet_named_with_a_stray_space_still_matches` |
| Cash-flow opening line mapped to `income_before_income_taxes_and_zakat` | four wordings of `Net income ... before zakat` resolved to the shorter net-income caption and published a pre-zakat amount as net income | `tests/test_bank_albilad_cash_flow.py` |

### Effect on the eight banks already merged

Every merged bank's Pillar 3 and statement documents were re-read with these changes and
compared fact by fact with the manifests on `main`:

- **No published value changes.** 114 Pillar 3 manifests and 136 statement documents
  re-read; zero conflicting values.
- The cash-flow mapping **adds** 18 `income_before_income_taxes_and_zakat` facts
  (BSF, Al Rajhi, Alinma) that were previously dropped. Their data is not rebuilt in
  this batch.
- The `fee_income` differences on Riyad Bank (26 values, 29 removed, 55 `net_fee_income`
  added) reproduce identically on untouched `origin/main`, so they are the drift already
  documented in the BSF/ANB batch, not an effect of this one. Riyad Bank's manifests are
  untouched here, as instructed.
- All 279 merged-bank manifest files are byte-for-byte unchanged on disk.

## Vintage reconciliation

Statements reconcile per period and Pillar 3 per metric, with the two curated manifests
(`aljazira-2025-fy.json`, `albilad-2025-fy.json`) held fixed: they take part in ranking,
win ties and are never rewritten. Audited statements outrank the Data Supplement, which
is why the supplement never overwrites a figure the statements already carry.

## Documents not published

| Bank | Period | Kind | Reason | Proposed resolution |
| --- | --- | --- | --- | --- |
| Bank AlJazira | 1 document(s) | Financial statements | the curated manifest already covers it | none needed |
| Bank AlJazira | 2 document(s) | Pillar 3 (KM1) | every fact is carried by a higher-assurance vintage | none needed |
| Bank AlJazira | 4 document(s) | Pillar 3 | the document carries no KM1 table: AlJazira's 2017-2019 files predate the template, and Bank Albilad's is an LCR and leverage annex rather than a full disclosure | none available; the capital figures for these quarters are carried by the adjacent Pillar 3 filings where they exist |
| Bank AlJazira | 10 document(s) | Financial statements | primary statements are scanned images with no text layer | reviewed OCR, or an issuer re-publication with a text layer |
| Bank AlJazira | 48 document(s) | Interim statements | primary statements are scanned images with no text layer | reviewed OCR, or an issuer re-publication with a text layer |
| Bank AlJazira | 1 document(s) | Pillar 3 | neither the KM1 page nor the document states the amount unit | adjacent quarters carry the same columns; re-read when the issuer restates the unit |
| Bank Albilad | 1 document(s) | Financial statements | the curated manifest already covers it | none needed |
| Bank Albilad | 1 document(s) | Financial statements | every fact is carried by a higher-assurance vintage | none needed |
| Bank Albilad | 1 document(s) | Pillar 3 | the document carries no KM1 table: AlJazira's 2017-2019 files predate the template, and Bank Albilad's is an LCR and leverage annex rather than a full disclosure | none available; the capital figures for these quarters are carried by the adjacent Pillar 3 filings where they exist |
| Bank Albilad | 6 document(s) | Annual report | primary statements are scanned images with no text layer | reviewed OCR, or an issuer re-publication with a text layer |

Bank AlJazira's statements from 2016 onward carry text for the notes but deliver the
primary statements as page images, so the reader publishes nothing from them; OCR is not
used for automatic publication. The 2008-2013 quarterly filings are scans throughout.
Bank Albilad's 2005-2010 annual reports are image-only. Bank Albilad's own server
returns HTTP 404 for every statement it links before 2019-Q4, so that history cannot be
retrieved from the issuer at all.

## Checks

| Check | Result |
| --- | --- |
| `verify --imports data/imports` | ok, 0 failures, 1,749 checks passed |
| verify warnings | 14, identical to `origin/main` (pre-existing cross-manifest conflicts) |
| Pipeline publication of all 99 manifests | 0 failures |
| `bootstrap` in a temporary database | exit 0 |
| `audit --project-root . --strict-warnings` | ready, 23,127 current facts; exits 1 only on the pre-existing `enabled_company_coverage` warning (us:COP, CVX, EOG, OXY, XOM) |
| Merged-bank manifests changed | 0 of 279 |

## Manifests

### Bank AlJazira (39)

| Manifest | Filing | Period | Facts | Source |
| --- | --- | --- | --- | --- |
| `aljazira-2008-q2.json` | Interim statements | 2008-06-30 | 10 | https://ir.aljazirabank.com.sa/media/xxhlsmft/baj_fs_2q08_final-english.pdf |
| `aljazira-2008-q3.json` | Interim statements | 2008-09-30 | 10 | https://ir.aljazirabank.com.sa/media/rg1hgxni/baj_fs_3q08_final-english.pdf |
| `aljazira-2013-q3.json` | Interim statements | 2013-09-30 | 36 | https://ir.aljazirabank.com.sa/media/hhpbmvvk/baj_fs_3q_2013_english.pdf |
| `aljazira-2014-q3.json` | Interim statements | 2014-09-30 | 39 | https://ir.aljazirabank.com.sa/media/4gmhowo5/fs-q3-2014-en.pdf |
| `aljazira-2015-q1.json` | Interim statements | 2015-03-31 | 27 | https://ir.aljazirabank.com.sa/media/fahpppfm/baj-fs-31march2015-signed-en.pdf |
| `aljazira-2015-q3.json` | Interim statements | 2015-09-30 | 35 | https://ir.aljazirabank.com.sa/media/agflsh5b/baj-english-signed-fs-q32015.pdf |
| `aljazira-2019-q2-pillar3.json` | Pillar 3 (KM1) | 2019-06-30 | 18 | https://ir.aljazirabank.com.sa/media/vvmn4hgz/pillar-iii-disclosures-qualitative-quantitative-disclosures-q2-2019.pdf |
| `aljazira-2019-q4-pillar3.json` | Pillar 3 (KM1) | 2019-12-31 | 6 | https://ir.aljazirabank.com.sa/media/zhep3d4c/pillar-iii-disclosures-qualitative-quantitative-disclosures-q4-2019.pdf |
| `aljazira-2020-q1-pillar3.json` | Pillar 3 (KM1) | 2020-03-31 | 6 | https://ir.aljazirabank.com.sa/media/1nffmfuz/pillar-3-disclosures-q1-2020.pdf |
| `aljazira-2020-q2-pillar3.json` | Pillar 3 (KM1) | 2020-06-30 | 12 | https://ir.aljazirabank.com.sa/media/brfof4yo/pillar-3-disclosures-q2-2020.pdf |
| `aljazira-2020-q3-pillar3.json` | Pillar 3 (KM1) | 2020-09-30 | 24 | https://ir.aljazirabank.com.sa/media/0yagcei1/pillar-3-disclosures-q3-2020.pdf |
| `aljazira-2021-q1-pillar3.json` | Pillar 3 (KM1) | 2021-03-31 | 12 | https://ir.aljazirabank.com.sa/media/qfmhvhzr/pillar-3-disclosures-q1-2021.pdf |
| `aljazira-2021-q2-pillar3.json` | Pillar 3 (KM1) | 2021-06-30 | 12 | https://ir.aljazirabank.com.sa/media/e3pf1cph/pillar-3-disclosures-q2-2021.pdf |
| `aljazira-2021-q3-pillar3.json` | Pillar 3 (KM1) | 2021-09-30 | 12 | https://ir.aljazirabank.com.sa/media/v3xnovwe/pillar-3-disclosures-q3-2021.pdf |
| `aljazira-2021-q4-pillar3.json` | Pillar 3 (KM1) | 2021-12-31 | 12 | https://ir.aljazirabank.com.sa/media/qcdhlp55/pillar-3-disclosures-q4-2021.pdf |
| `aljazira-2022-q1-pillar3.json` | Pillar 3 (KM1) | 2022-03-31 | 12 | https://ir.aljazirabank.com.sa/media/ki0pyg5j/pillar-3-disclosures-q1-2022.pdf |
| `aljazira-2022-q2-pillar3.json` | Pillar 3 (KM1) | 2022-06-30 | 12 | https://ir.aljazirabank.com.sa/media/pd3cqzdq/pillar-3-disclosures-q2-2022.pdf |
| `aljazira-2022-q3-pillar3.json` | Pillar 3 (KM1) | 2022-09-30 | 12 | https://ir.aljazirabank.com.sa/media/41cbmwy1/pillar-3-disclosures-q3-2022.pdf |
| `aljazira-2022-q4-pillar3.json` | Pillar 3 (KM1) | 2022-12-31 | 24 | https://ir.aljazirabank.com.sa/media/zzqjwsnk/pillar-3-disclosures-q4-2022.pdf |
| `aljazira-2023-q2-pillar3.json` | Pillar 3 (KM1) | 2023-06-30 | 14 | https://ir.aljazirabank.com.sa/media/w0jifisx/pillar-3-disclosures-q2-2023.pdf |
| `aljazira-2023-q3-pillar3.json` | Pillar 3 (KM1) | 2023-09-30 | 14 | https://ir.aljazirabank.com.sa/media/m54pneyh/pillar-3-disclosures-q3-2023.pdf |
| `aljazira-2023-q4-pillar3.json` | Pillar 3 (KM1) | 2023-12-31 | 14 | https://ir.aljazirabank.com.sa/media/smepsqw0/pillar-3-disclosures-q4-2023.pdf |
| `aljazira-2024-q1-pillar3.json` | Pillar 3 (KM1) | 2024-03-31 | 14 | https://ir.aljazirabank.com.sa/media/ybtfxg3y/pillar-3-disclosures-q1-2024.pdf |
| `aljazira-2024-q2-pillar3.json` | Pillar 3 (KM1) | 2024-06-30 | 14 | https://ir.aljazirabank.com.sa/media/2tjh1n2b/pillar-3-disclosures-q2-2024.pdf |
| `aljazira-2024-q3-pillar3.json` | Pillar 3 (KM1) | 2024-09-30 | 14 | https://ir.aljazirabank.com.sa/media/4jievwix/pillar-3-disclosures-q3-2024.pdf |
| `aljazira-2024-q4-pillar3.json` | Pillar 3 (KM1) | 2024-12-31 | 14 | https://ir.aljazirabank.com.sa/media/li0p0mvj/pillar-3-disclosures-q4-2024.pdf |
| `aljazira-2025-fy.json` | Financial statements | 2025-12-31 | 86 | https://ir.aljazirabank.com.sa/media/p3qlaib4/ajb-fs-fy-2025-english.pdf |
| `aljazira-2025-q1-pillar3.json` | Pillar 3 (KM1) | 2025-03-31 | 14 | https://ir.aljazirabank.com.sa/media/4l1pytgm/pillar-3-disclosures-q1-2025.pdf |
| `aljazira-2025-q1-supplement.json` | Data Supplement | 2025-03-31 | 33 | https://ir.aljazirabank.com.sa/media/kj5k2edu/data-supplement-q1-25.xlsx |
| `aljazira-2025-q2-pillar3.json` | Pillar 3 (KM1) | 2025-06-30 | 14 | https://ir.aljazirabank.com.sa/media/0lqojf4x/pillar-3-disclosures-q2-2025.pdf |
| `aljazira-2025-q2-supplement.json` | Data Supplement | 2025-06-30 | 65 | https://ir.aljazirabank.com.sa/media/pvjjt1y0/data-supplement-q2-25.xlsx |
| `aljazira-2025-q3-pillar3.json` | Pillar 3 (KM1) | 2025-09-30 | 14 | https://ir.aljazirabank.com.sa/media/a4ol5ppf/pillar-3-disclosures-q3-2025.pdf |
| `aljazira-2025-q3-supplement.json` | Data Supplement | 2025-09-30 | 65 | https://ir.aljazirabank.com.sa/media/nbvfj1dt/data-supplement-q3-25.xlsx |
| `aljazira-2025-q4-pillar3.json` | Pillar 3 (KM1) | 2025-12-31 | 14 | https://ir.aljazirabank.com.sa/media/zgeoctpp/pillar-3-disclosures-q4-2025.pdf |
| `aljazira-2025-q4-supplement.json` | Data Supplement | 2025-12-31 | 16 | https://ir.aljazirabank.com.sa/media/dqqdfbxq/data_supplement_q4_25_v2.xlsx |
| `aljazira-2026-q1-pillar3.json` | Pillar 3 (KM1) | 2026-03-31 | 14 | https://ir.aljazirabank.com.sa/media/d1vjod1r/basel-pillar-iii-disclosure-q1-2026.pdf |
| `aljazira-2026-q1-supplement.json` | Data Supplement | 2026-03-31 | 33 | https://ir.aljazirabank.com.sa/media/pblpkmcs/data-supplement-q1-26.xlsx |
| `aljazira-2026-q2-pillar3.json` | Pillar 3 (KM1) | 2026-06-30 | 70 | https://ir.aljazirabank.com.sa/media/o5vhop1j/basel-pillar-iii-disclosure-q2-2026.pdf |
| `aljazira-2026-q2-supplement.json` | Data Supplement | 2026-06-30 | 196 | https://ir.aljazirabank.com.sa/media/dezdxgv5/data_supplement_q2_26.xlsx |

### Bank Albilad (60)

| Manifest | Filing | Period | Facts | Source |
| --- | --- | --- | --- | --- |
| `albilad-2011-fy.json` | Annual report | 2011-12-31 | 19 | https://www.bankalbilad.com.sa/downloads/about/financial-results/Annual%20Report%202011%20EN.pdf |
| `albilad-2012-fy.json` | Annual report | 2012-12-31 | 30 | https://www.bankalbilad.com.sa/downloads/about/financial-results/Annual%20Report%202012%20EN.pdf |
| `albilad-2018-fy-pillar3.json` | Pillar 3 (KM1) | 2018-12-31 | 13 | https://www.bankalbilad.com.sa/Documents/افصاحات%20خاصة%20بالركيزة%20الثالثة.pdf |
| `albilad-2018-fy.json` | Annual report | 2018-12-31 | 24 | https://www.bankalbilad.com.sa/Documents/boardscv2019/Albilad%20Annual%20Report%202018_English%20draft%201.pdf |
| `albilad-2019-fy-pillar3.json` | Pillar 3 (KM1) | 2019-12-31 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%204Q2019.pdf |
| `albilad-2019-fy.json` | Financial statements | 2019-12-31 | 32 | https://www.bankalbilad.com.sa/Documents/BAB%20English%20FS%20of%20Dec%202019%20%20.pdf |
| `albilad-2019-q1-pillar3.json` | Pillar 3 (KM1) | 2019-03-31 | 13 | https://www.bankalbilad.com.sa/Documents/BAB%20Pillar%203%20Disclousres%201Q2019.pdf |
| `albilad-2019-q2-pillar3.json` | Pillar 3 (KM1) | 2019-06-30 | 13 | https://www.bankalbilad.com.sa/Documents/BAB%20Pillar%203%20Disclousres%202Q2019%20Final000.pdf |
| `albilad-2019-q3-pillar3.json` | Pillar 3 (KM1) | 2019-09-30 | 13 | https://www.bankalbilad.com.sa/Documents/BAB%20Pillar%203%20Disclousres%203Q2019%20Final.pdf |
| `albilad-2020-fy-pillar3.json` | Pillar 3 (KM1) | 2020-12-31 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%204Q2020%20.pdf |
| `albilad-2020-fy.json` | Financial statements | 2020-12-31 | 31 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20English%20FS%20of%20Dec%202020%20final.pdf |
| `albilad-2020-q1-pillar3.json` | Pillar 3 (KM1) | 2020-03-31 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%201Q2020.pdf |
| `albilad-2020-q1.json` | Interim statements | 2020-03-31 | 33 | https://www.bankalbilad.com.sa/Documents/FS-2020-Q1-English.pdf |
| `albilad-2020-q2-pillar3.json` | Pillar 3 (KM1) | 2020-06-30 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%202Q%202020-%20FINAL.pdf |
| `albilad-2020-q2.json` | Interim statements | 2020-06-30 | 43 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q2%20-%202020%20English%20FS%20Final.pdf |
| `albilad-2020-q3-pillar3.json` | Pillar 3 (KM1) | 2020-09-30 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%203Q%202020%20.pdf |
| `albilad-2020-q3.json` | Interim statements | 2020-09-30 | 43 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q3%20-%202020%20English%20FS%20%20Final.pdf |
| `albilad-2021-fy-pillar3.json` | Pillar 3 (KM1) | 2021-12-31 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%20Q4%202021.pdf |
| `albilad-2021-fy.json` | Financial statements | 2021-12-31 | 29 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20FS%20YE%202021%20-%20English%20bank%20website.pdf |
| `albilad-2021-q1-pillar3.json` | Pillar 3 (KM1) | 2021-03-31 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%201Q2021.pdf |
| `albilad-2021-q1.json` | Interim statements | 2021-03-31 | 29 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q1-%202021%20English%20%20FS.pdf |
| `albilad-2021-q2-pillar3.json` | Pillar 3 (KM1) | 2021-06-30 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%202Q%202021.pdf |
| `albilad-2021-q2.json` | Interim statements | 2021-06-30 | 43 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q2%20-%202021%20English%20%20FS.pdf |
| `albilad-2021-q3-pillar3.json` | Pillar 3 (KM1) | 2021-09-30 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%20Q3%202021.pdf |
| `albilad-2021-q3.json` | Interim statements | 2021-09-30 | 40 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q3%20-%202021%20English%20FS.pdf |
| `albilad-2022-fy-pillar3.json` | Pillar 3 (KM1) | 2022-12-31 | 33 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%20Q4%202022.pdf |
| `albilad-2022-fy.json` | Financial statements | 2022-12-31 | 34 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20YE%20-%202022%20English%20FS.pdf |
| `albilad-2022-q1-pillar3.json` | Pillar 3 (KM1) | 2022-03-31 | 13 | https://www.bankalbilad.com.sa/downloads/about/basel/quantitative-and-qualitative-disclosure/BAB%20Pillar%203%20Disclousres%20Q1%202022.pdf |
| `albilad-2022-q1.json` | Interim statements | 2022-03-31 | 35 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q1%20-%202022%20English%20FS%20%20final.pdf |
| `albilad-2022-q2-pillar3.json` | Pillar 3 (KM1) | 2022-06-30 | 13 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclousres%202Q%202022.pdf |
| `albilad-2022-q2.json` | Interim statements | 2022-06-30 | 45 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q2%20-%202022%20English%20FS.pdf |
| `albilad-2022-q3-pillar3.json` | Pillar 3 (KM1) | 2022-09-30 | 13 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclosures%20Q3%202022.pdf |
| `albilad-2022-q3.json` | Interim statements | 2022-09-30 | 45 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q3%20-%202022%20English%20FS.pdf |
| `albilad-2023-fy-pillar3.json` | Pillar 3 (KM1) | 2023-12-31 | 9 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclosure%20Q4%202023.pdf |
| `albilad-2023-fy.json` | Financial statements | 2023-12-31 | 35 | https://www.bankalbilad.com.sa/downloads/about/financial-results/FS%20for%20Banks%20englishYE%202023.pdf |
| `albilad-2023-q1-pillar3.json` | Pillar 3 (KM1) | 2023-03-31 | 8 | https://www.bankalbilad.com.sa/downloads/about/BAB%20Pillar%203%20Disclousres%20Q1%202023.pdf |
| `albilad-2023-q1.json` | Interim statements | 2023-03-31 | 37 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q1%20-%202023%20English%20FS_Final_Signed.pdf |
| `albilad-2023-q2-pillar3.json` | Pillar 3 (KM1) | 2023-06-30 | 8 | https://www.bankalbilad.com.sa/downloads/about/BAB%20Pillar%20III%20Disclosures%20Q2%202023.pdf |
| `albilad-2023-q2.json` | Interim statements | 2023-06-30 | 49 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q2%20-%202023%20English%20FS_Final_Signed.pdf |
| `albilad-2023-q3-pillar3.json` | Pillar 3 (KM1) | 2023-09-30 | 8 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%20III%20Disclosures%20Q3%202023.pdf |
| `albilad-2023-q3.json` | Interim statements | 2023-09-30 | 49 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q3%20-%202023%20English%20FS_Signed.pdf |
| `albilad-2024-fy-pillar3.json` | Pillar 3 (KM1) | 2024-12-31 | 8 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclosure%20Q4%202024.pdf |
| `albilad-2024-q1-pillar3.json` | Pillar 3 (KM1) | 2024-03-31 | 7 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%20III%20Disclosures%20Q1%202024.pdf |
| `albilad-2024-q1.json` | Interim statements | 2024-03-31 | 37 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q1%20-%202024%20English%20FS.pdf |
| `albilad-2024-q2-pillar3.json` | Pillar 3 (KM1) | 2024-06-30 | 9 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclosure%20Q2%202024.pdf |
| `albilad-2024-q2.json` | Interim statements | 2024-06-30 | 50 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q2%20-%202024%20English%20FS_Signed.pdf |
| `albilad-2024-q3-pillar3.json` | Pillar 3 (KM1) | 2024-09-30 | 7 | https://www.bankalbilad.com.sa/downloads/about/investor-relations/BAB%20Pillar%20III%20Disclosures%20Q3%202024.pdf |
| `albilad-2024-q3.json` | Interim statements | 2024-09-30 | 50 | https://www.bankalbilad.com.sa/downloads/about/investor-relations/BAB%20Q3%20-%202024%20English%20FS.pdf |
| `albilad-2025-fy-pillar3.json` | Pillar 3 (KM1) | 2025-12-31 | 38 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclosure%20Q4%202025.pdf |
| `albilad-2025-fy.json` | Financial statements | 2025-12-31 | 86 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20YE%20-%202025%20English%20FS.pdf |
| `albilad-2025-q1-pillar3.json` | Pillar 3 (KM1) | 2025-03-31 | 8 | https://www.bankalbilad.com.sa/downloads/about/investor-relations/BAB%20Pillar%20III%20Disclosures%20Q1%202025.pdf |
| `albilad-2025-q1.json` | Interim statements | 2025-03-31 | 34 | https://www.bankalbilad.com.sa/downloads/about/investor-relations/BAB%20Q1%20-%202025%20English%20FS.pdf |
| `albilad-2025-q2-pillar3.json` | Pillar 3 (KM1) | 2025-06-30 | 8 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclosure%20Q2%202025.pdf |
| `albilad-2025-q2.json` | Interim statements | 2025-06-30 | 50 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q2%20-%202025%20English%20FS.pdf |
| `albilad-2025-q3-pillar3.json` | Pillar 3 (KM1) | 2025-09-30 | 8 | https://www.bankalbilad.com.sa/downloads/about/basel/BAB%20Pillar%20III%20Disclosures%20Q3%202025.pdf |
| `albilad-2025-q3.json` | Interim statements | 2025-09-30 | 50 | https://www.bankalbilad.com.sa/downloads/about/basel/Bank%20Albilad%20Q3%20-%202025%20English%20FS.pdf |
| `albilad-2026-q1-pillar3.json` | Pillar 3 (KM1) | 2026-03-31 | 8 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%20III%20Disclosures%20Q1%202026.pdf |
| `albilad-2026-q1.json` | Interim statements | 2026-03-31 | 30 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q1%20-%202026%20English%20FS.pdf |
| `albilad-2026-q2-pillar3.json` | Pillar 3 (KM1) | 2026-06-30 | 40 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Pillar%203%20Disclosure%20Q2%202026.pdf |
| `albilad-2026-q2.json` | Interim statements | 2026-06-30 | 46 | https://www.bankalbilad.com.sa/downloads/about/financial-results/BAB%20Q2%20-%202026%20English%20FS.pdf |

