# Saudi banks — BSF (1050) and ANB (1080), batch 1

Branch `claude/banks-bsf-anb-enrichment`, cut from `origin/main` at `4d9a0e1`.
Scope is limited to Banque Saudi Fransi (`sa:1050`) and Arab National Bank
(`sa:1080`). No database, deployment, service or worker was changed. Every fact
below was produced by an engine reader from an archived official document and
verified before it was written; nothing was transcribed by hand and nothing was
estimated.

## What changed for the two banks

Measured by a CI-parity bootstrap into a scratch database, before and after.

| | BSF before | BSF after | ANB before | ANB after |
|---|---|---|---|---|
| Published documents | 1 | 17 | 1 | 78 |
| Current data points | 133 | 2,573 (518 calculated) | 141 | 3,937 (766 calculated) |
| Unique metrics | 73 | 98 | 77 | 88 |
| Fiscal years | 2024–2025 | 2015–2026 | 2024–2025 | 2003–2025 |
| Annual periods | 2 | 11 | 2 | 21 |
| Quarter-end balance sheets | 2 | 37 | 2 | 75 |
| Discrete quarters | none | 34 | none | 41 |
| YTD periods | none | 14 | none | 57 |
| TTM periods | none | 3 | none | 38 |
| Regulatory capital | none | Tier 1 capital, total capital, RWA, LCR and Basel III leverage ratio across the supplement's quarter ends | none | none — no reachable source |
| Open exceptions in the database | 0 | 0 | 0 | 0 |

ANB's history now runs from Q2-2003; BSF's from FY2015, the first year its Data
Supplement covers. Whole-directory verification after the write: 1,606 checks
passed, 14 warnings, 0 failures. CI-parity bootstrap and
`audit --strict-warnings`: 0 failures, with the single pre-existing
`enabled_company_coverage` warning that unmodified `main` also reports. The six
banks merged before this batch are unchanged: SAB 231, SNB 838, Riyad 2,255,
SAIB 1,418, Al Rajhi 2,286, Alinma 1,470 current data points.

## Source priority applied

1. **Issuer IR (primary).**
   * BSF — [quarterly results / investor presentations](https://bsf.sa/english/top-menu/investorrelation/quarterly-results):
     the quarterly Data Supplement workbooks (FY2015 onward) and the consolidated
     financial statements PDFs.
   * ANB — [financial reports](https://anb.com.sa/en/web/anb/financial-reports)
     (quarterly statements back to 2003) and
     [annual reports](https://anb.com.sa/en/web/anb/annual-reports)
     (Part 2 — Financial Statements).
2. **Saudi Exchange.** Attempted as the fallback for the Pillar 3 gap below; the
   portal answers `403` to this network, so it could not fill it.
3. **Regulator.** Not applicable — neither bank publishes a KM1 disclosure that
   could be reached.

## Regulatory capital: where it comes from for these two banks

Unlike the six banks merged before this batch, **neither BSF nor ANB publishes a
Basel III Pillar 3 KM1 disclosure on a reachable page**:

* BSF's investor site exposes 152 documents, all under one
  `Investor_Presentations` folder — statements, Data Supplements, earnings
  releases, presentations, transcripts and factsheets. There is no Basel or
  Pillar 3 document in either the English or the Arabic library, and no annual
  report either.
* ANB's Basel III disclosures page renders empty (no document links in the DOM),
  its investor-relations landing page carries only product menus, its sitemap
  lists no Basel or Pillar 3 entry, and the Euroland-hosted IR site used by the
  existing FY2025 manifest (`financial.eurolandir.com`) does not answer from this
  network.

BSF's own Data Supplement carries the regulatory lines, so for BSF they are read
from there: Tier 1 capital, total capital, risk-weighted assets, the liquidity
coverage ratio and the Basel III leverage ratio are now mapped, while the capital
adequacy, Tier 1 and NPL ratios stay unmapped because the engine recomputes them
from the published amounts. ANB has no reachable source for capital or liquidity
at all; that is recorded as an open gap rather than filled from a secondary site.

## Reusable engine changes

All three are generic, each with a regression test, and each was checked against
every manifest in `data/imports` that an engine reader produced (53 of them) by
re-reading its archived PDF before and after the change.

* `reading.py` — period columns headed by **pre-2010 years** were not detected:
  column detection accepted year headings from 2010 onward only, so a bank's
  older filings produced no value columns at all and read as empty. ANB
  publishes quarterly statements from 2003; lowering the floor to 2000 makes 33
  more of its archived documents readable (every quarter from 2003-Q2 to
  2010-Q4, plus the 2005–2008 and 2010 annual reports), 28–52 facts each. The
  floor still excludes 19xx, note-reference columns are still discarded, and the
  page must already be a confirmed statement.
  Test: `test_period_columns_headed_by_pre_2010_years_are_detected`.
* `reading.py` — the **trailing ", net" fee caption** had no entry, so it fell
  back to the gross caption: ANB's 2025 annual report published the net subtotal
  (878,412) as `fee_income` instead of the gross 2,283,365. Now
  `fee and commission income, net` maps to `net_fee_income`, matching the
  existing `fee income from banking services, net` precedent.
  Test: `test_trailing_net_fee_caption_is_not_gross_fee_income`.
* `reading.py` — the cash-flow statement heading list required the plural
  ("statement of cash flows"). ANB titles the page **"Consolidated statement of
  cash flow"**, so the entire page was skipped and every figure on it was lost:
  ANB's 2024 annual statements read 16 facts instead of 21, with no operating,
  investing or financing cash flow. The singular form is now recognised.
  Regression test: `tests/test_reading.py::test_cash_flow_statement_titled_in_the_singular_is_read`,
  which builds a statement page titled in the singular and asserts the three
  cash-flow subtotals are read. The change only adds a heading variant, so it
  cannot remove an existing match; the 2015-2023 ANB layouts and every BSF
  statement read identically before and after.
* `config/supplements/1050.json` — the BSF map now rounds to the issuer's
  reported precision (its formula cells carry binary float noise), carries
  `SAR/share` scale and unit on the per-share rows, integer share counts, and
  maps the capital and liquidity rows described above.

No catalog field was added: the Basel III amounts and ratios these banks report
(`tier1_capital`, `liquidity_coverage_ratio`, `leverage_ratio`,
`regulatory_capital`, `risk_weighted_assets`) already exist in the `banking_v1`
pack from the previous batch.

### Two findings for review (not changed by this batch)

* **Riyad Bank (`sa:1010`) carries the same fee mistake.** Its merged manifests
  print all three fee lines for many periods, and their stored `fee_income` is
  actually the net subtotal — for 2020-Q2, `fee_income` is 322,740 (quarter) and
  894,698 (YTD), which are the net figures; the gross lines are 481,519 and
  1,266,616. Rebuilding `sa:1010` with the corrected mapping would fix
  `fee_income` and add `net_fee_income` for 37 manifests. This batch does not
  rewrite another bank's merged data; it is left for Codex to schedule.
* **`sabic-2025-fy.json` no longer reproduces from its archived PDF.** It holds
  59 facts; both this branch *and* untouched `origin/main` read 41 from the same
  document (the cash-flow pages are no longer picked up). The manifest predates
  reader changes already merged into `main`, so this is pre-existing drift on an
  out-of-scope company, reported here rather than fixed.

## The reviewed FY2025 manifests are kept, not re-read

Both banks already had a reviewed manual manifest for FY2025, and this batch
leaves them in place. For BSF the automatic re-read of the very same PDF was
tested and rejected: it produced 40 facts against the manual manifest's 86,
dropped every FY2024 comparative along with capex, the cash-flow lines,
customer deposits and debt securities issued, and disagreed on two FY2025
figures. The disagreements are explained by the filing itself — BSF prints two
impairment lines ("on loans and advances, net" and "for investments, financial
assets and others, net"), so the automatic read captured one of them
(-973,997) where the reviewed manifest carries the combined charge (-988,630),
and `due_to_banks` differs the same way. A thinner, conflicting automatic read
does not replace a reviewed one, so the builder skips that document and the
curated manifest — including its note about the note-44 balance-sheet
restatement — stands.

## Vintage reconciliation

Each BSF Data Supplement repeats every prior quarter back to FY2015, so
`reconcile_vintages` keeps one source of record per fact — assurance first, then
the latest period covered, then `filed_at` — and the reviewed statements outrank
the workbooks for the periods they both cover. Superseded workbook vintages are
kept in the archive and recorded as superseded rather than deleted.

## Exceptions

| Bank | Documents | Code | Evidence | Proposed action |
|---|---|---|---|---|
| ANB | 1: anb-2003-Q1 | `identity_not_satisfied` | 27 facts read, but assets do not equal liabilities plus equity, so the read is not trustworthy | OCR review; the 2003-Q2 and 2003-Q3 filings are published and unaffected |
| ANB | 11: anb-2013-Q2, anb-2021-Q2, anb-2021-Q4, anb-2022-Q1, anb-2022-Q2, anb-2022-Q3 … (+5 more) | `image_only_statements` | the statement pages are scanned, or carry captions whose figures are images; the reader returns no facts | OCR review or the Saudi Exchange copy - ANB publishes no data supplement, so these periods have no other source |
| ANB | 4: anb-ar-2002, anb-ar-2003, anb-ar-2004, anb-ar-2016 | `partial_text_layer` | 15-19 facts read from an otherwise scanned annual report | OCR review; a partial read is not published |
| BSF | 3: BSF Q1-2022 March 31, BSF Q2-2022 June 30, BSF Q3-2022 September 30 | `image_only_statements` | the primary statement pages carry no text layer; the reader returns no facts | the Data Supplement already publishes these periods; OCR or the Saudi Exchange copy would add the statement detail |
| BSF | 1: BSF FY-2022 December 31 | `partial_text_layer` | only the cash-flow page has text (8 facts); the balance sheet and income statement are scanned images | same as above - a partial read is not published |

A further 29 manifests were superseded in full by a later vintage of
the same series and are therefore not written; their documents stay archived and the
superseding source is recorded in each fact's provenance.

## Documents and manifests

All archived under `data/raw/SA/<symbol>/documents/<sha256>.<ext>` and indexed in
`data/raw/archive-index.json`, each with its official URL, SHA-256, content type,
byte size, archive date and the index page it was listed on. `filed_at` is inferred
from PDF creation or workbook last-modified metadata (`filed_at_basis` per manifest).

### Banque Saudi Fransi (sa:1050) — 17 manifests

| Manifest | Type | Facts | Periods | SHA-256 (first 16) | Official URL |
|---|---|---:|---|---|---|
| `bsf-2020-q2-supplement.json` | data-supplement | 25 | 2019-06-30 | `a0f02ec6858c5d79` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Data_Supplement_2020-Q2.xlsx) |
| `bsf-2021-q2-supplement.json` | data-supplement | 25 | 2020-06-30 | `6f44a0ad2bed7246` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/BSF_Data_Supplement_2Q_2021_FINAL.xlsx) |
| `bsf-2021-q3-supplement.json` | data-supplement | 25 | 2020-09-30 | `7dd2555ac2becf83` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Data_Supplement_3Q_2021.xlsx) |
| `bsf-2022-q2-supplement.json` | data-supplement | 22 | 2021-06-30 | `597e532e50313353` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/BSF-Data-Supplement-2Q-2022.xlsx) |
| `bsf-2022-q3-supplement.json` | data-supplement | 22 | 2021-09-30 | `654ef29cf37ed27b` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Data_Supplement_3Q_2022.xlsx) |
| `bsf-2023-fy.json` | financial-statements | 39 | 2023-12-31 | `ac8cff11cb9da21d` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Consolidated%20Financial%20Statments%20FY-2023,%20December%2031.pdf) |
| `bsf-2023-q1.json` | interim-report | 38 | 2023-03-31 | `d85e62d284aad634` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Consolidated%20Financial%20Statments%20Q1-2023,%20March%2031.pdf) |
| `bsf-2023-q2-supplement.json` | data-supplement | 22 | 2022-06-30 | `72ea9a10be9656c6` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/BSF-Data-Supplement-2Q-2023_v3.3.xlsx) |
| `bsf-2023-q2.json` | interim-report | 56 | 2023-06-30 | `39edfd35735d2167` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Consolidated%20Financial%20Statments%20Q2-2023,%20June%2030.pdf) |
| `bsf-2023-q3-supplement.json` | data-supplement | 22 | 2022-09-30 | `9a12565e67d282b5` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/BSF%20Data%20Supplement%203Q%202023.xlsx) |
| `bsf-2023-q3.json` | interim-report | 55 | 2023-09-30 | `f9b09058b9d2c7eb` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Consolidated%20Financial%20Statments%20Q3-2023,%20September%2030.pdf) |
| `bsf-2024-q1.json` | interim-report | 37 | 2024-03-31 | `416c5420146fda65` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Consolidated%20Financial%20Statments%20Q1-2024.pdf) |
| `bsf-2024-q2.json` | interim-report | 55 | 2024-06-30 | `e2286a56c8051ae8` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Consolidated%20Financial%20Statments%20Q2-2024.pdf) |
| `bsf-2025-fy.json` | financial-statements | 86 | 2024-12-31 → 2025-12-31 (2) | `8fcf18cde5250db0` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Financial_Statments_Q4_2025.pdf) |
| `bsf-2025-q3-supplement.json` | data-supplement | 22 | 2024-09-30 | `04da29be6eee5698` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/BSFDataSupplement3Q2025.xlsx) |
| `bsf-2025-q3.json` | interim-report | 55 | 2025-09-30 | `b1b9212ba22bc92e` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/Financial%20Statments%20Q3%202025.pdf) |
| `bsf-2026-q2-supplement.json` | data-supplement | 1449 | 2015-12-31 → 2026-06-30 (31) | `0b97acebcf1c9d1e` | [link](https://bsf.sa/Library/Assets/Gallery/Documents/Investor_Presentations/BSFDataSupplement2Q2026.xlsx) |

### Arab National Bank (sa:1080) — 78 manifests

| Manifest | Type | Facts | Periods | SHA-256 (first 16) | Official URL |
|---|---|---:|---|---|---|
| `anb-2003-q2.json` | interim-report | 37 | 2003-06-30 | `57836e66d5a036ce` | [link](https://anb.com.sa/documents/55607/85139/2003_Q2.pdf/768aeaa6-eb13-1de9-1ed9-242a49c337d3) |
| `anb-2003-q3.json` | interim-report | 39 | 2003-09-30 | `58932fa391429883` | [link](https://anb.com.sa/documents/55607/85145/2003_Q3.pdf/ac22cfe3-68c3-05f2-b553-9185ec42e160) |
| `anb-2004-q1.json` | interim-report | 29 | 2004-03-31 | `dd647cf992a4bb22` | [link](https://anb.com.sa/documents/55607/85133/2004_Q1.pdf/adbe93b0-bf5a-d9e4-663a-8999b223e3d3) |
| `anb-2004-q2.json` | interim-report | 43 | 2004-06-30 | `eb3df59a5c589266` | [link](https://anb.com.sa/documents/55607/85139/2004_Q2.pdf/03eacdd3-962c-d619-bde0-71479a853981) |
| `anb-2004-q3.json` | interim-report | 40 | 2004-09-30 | `117d2f58c7e0c0bf` | [link](https://anb.com.sa/documents/55607/85145/2004_Q3.pdf/f908bb2f-5bfa-c6bf-7adf-94a2ebcc7888) |
| `anb-2005-annual-report.json` | financial-statements | 32 | 2005-12-31 | `93ed25e002f45f6b` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2005.pdf/c6fe47c6-e092-c003-76f5-ab5460aacf0c) |
| `anb-2005-q1.json` | interim-report | 31 | 2005-03-31 | `30b8b108c7c75540` | [link](https://anb.com.sa/documents/55607/85133/2005_Q1.pdf/0acbef4a-161a-423f-6f97-c2ea205fd86e) |
| `anb-2005-q2.json` | interim-report | 46 | 2005-06-30 | `909c8031a519a50e` | [link](https://anb.com.sa/documents/55607/85139/2005_Q2.pdf/1549f889-bc75-3b2e-2d74-6f192f263f8e) |
| `anb-2005-q3.json` | interim-report | 45 | 2005-09-30 | `e1767eb4b0e8c3ed` | [link](https://anb.com.sa/documents/55607/85145/2005_Q3.pdf/8221090f-f720-136b-de63-acb609286cb8) |
| `anb-2006-annual-report.json` | financial-statements | 33 | 2006-12-31 | `e44f05576c61b419` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2006.pdf/5a018214-45c6-ff5b-e0d4-869ffff85f70) |
| `anb-2006-q1.json` | interim-report | 28 | 2006-03-31 | `37b069da5e2e0ec8` | [link](https://anb.com.sa/documents/55607/85133/2006_Q1.pdf/4bd9f132-1374-38bb-b7c0-9f1dead16923) |
| `anb-2006-q2.json` | interim-report | 29 | 2006-06-30 | `9144cb8b95f29430` | [link](https://anb.com.sa/documents/55607/85139/2006_Q2.pdf/c6d559e8-e3df-48f7-d397-e7b72a082d47) |
| `anb-2006-q3.json` | interim-report | 44 | 2006-09-30 | `e1d29573790b9f7c` | [link](https://anb.com.sa/documents/55607/85145/2006_Q3.pdf/45c56401-5d63-c85c-0ab0-a6a2200d0f37) |
| `anb-2007-annual-report.json` | financial-statements | 31 | 2007-12-31 | `af7ea7f4e20ce8f5` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2007.pdf/11072d5f-d433-4cca-2cba-50702227bfb7) |
| `anb-2007-q1.json` | interim-report | 31 | 2007-03-31 | `11c7ac821092eec7` | [link](https://anb.com.sa/documents/55607/85133/2007_Q1.pdf/842a9fff-340b-533c-f35b-8e293a0252bf) |
| `anb-2007-q2.json` | interim-report | 47 | 2007-06-30 | `c2d877c5dda1e00a` | [link](https://anb.com.sa/documents/55607/85139/2007_Q2.pdf/534988db-b67d-d354-1f0c-44127ba53c1a) |
| `anb-2007-q3.json` | interim-report | 44 | 2007-09-30 | `97918243b07b65e2` | [link](https://anb.com.sa/documents/55607/85145/2007_Q3.pdf/a48a8790-2d37-9a76-11c1-0c7b92cae851) |
| `anb-2008-fy.json` | financial-statements | 35 | 2008-12-31 | `6209aac371536291` | [link](https://anb.com.sa/documents/55607/85151/2008_Q4.pdf/b19c179f-1b81-603e-95e3-91f6ea7a87e7) |
| `anb-2008-q1.json` | interim-report | 32 | 2008-03-31 | `e41b77e927143d0c` | [link](https://anb.com.sa/documents/55607/85133/2008_Q1.pdf/6fd75428-d569-1d83-04c9-69f744b81177) |
| `anb-2008-q2.json` | interim-report | 45 | 2008-06-30 | `861b0e7c1ae33452` | [link](https://anb.com.sa/documents/55607/85139/2008_Q2.pdf/58f8865a-5f31-4378-138f-a512519cc90e) |
| `anb-2008-q3.json` | interim-report | 45 | 2008-09-30 | `f46b0b66c88f198b` | [link](https://anb.com.sa/documents/55607/85145/2008_Q3.pdf/c08dbc45-540a-646d-726c-b23aa8866d31) |
| `anb-2009-fy.json` | financial-statements | 36 | 2009-12-31 | `e4bdf11cdf2f993f` | [link](https://anb.com.sa/documents/55607/85151/2009_Q4.pdf/d77335e4-6cec-5cc7-51a2-de39801b235e) |
| `anb-2009-q1.json` | interim-report | 33 | 2009-03-31 | `33dbccdd4b230355` | [link](https://anb.com.sa/documents/55607/85133/2009_Q1.pdf/de358adc-5e51-8385-5583-19147694c225) |
| `anb-2009-q2.json` | interim-report | 48 | 2009-06-30 | `bdb95cb0d08e6882` | [link](https://anb.com.sa/documents/55607/85139/2009_Q2.pdf/7e007340-a1d1-a50d-a57f-f1c6a8a5f9fb) |
| `anb-2009-q3.json` | interim-report | 48 | 2009-09-30 | `ca18f7d3b50d8c3f` | [link](https://anb.com.sa/documents/55607/85145/2009_Q3.pdf/dbf0c7a7-afdc-30cd-795a-2af84c08c937) |
| `anb-2010-annual-report.json` | financial-statements | 38 | 2010-12-31 | `26bff9f18a76e067` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2010.pdf/a09cffc6-9ac0-a0fe-1445-5d9f18a6845e) |
| `anb-2010-q1.json` | interim-report | 36 | 2010-03-31 | `949eebee47066fe4` | [link](https://anb.com.sa/documents/55607/85133/2010_Q1.pdf/a4316906-42f7-0bb9-ca33-5ed4804779b8) |
| `anb-2010-q2.json` | interim-report | 51 | 2010-06-30 | `4bd15c1b65f716b0` | [link](https://anb.com.sa/documents/55607/85139/2010_Q2.pdf/30c14cc4-fd61-9bcf-967c-42dacc12d094) |
| `anb-2010-q3.json` | interim-report | 52 | 2010-09-30 | `e4950f888ca318da` | [link](https://anb.com.sa/documents/55607/85145/2010_Q3.pdf/e3632b36-f9a4-e22d-1c85-86f8661d1114) |
| `anb-2011-fy.json` | financial-statements | 36 | 2011-12-31 | `d3c9914e13360702` | [link](https://anb.com.sa/documents/55607/85151/2011_Q4.pdf/9b20858c-57ac-f6f2-03eb-e1ad5ede5a8c) |
| `anb-2011-q1.json` | interim-report | 36 | 2011-03-31 | `36befbaa5e23ae0e` | [link](https://anb.com.sa/documents/55607/85133/2011_Q1.pdf/d253f973-bb54-513d-943b-40196a361cef) |
| `anb-2011-q2.json` | interim-report | 50 | 2011-06-30 | `9720f20354b86366` | [link](https://anb.com.sa/documents/55607/85139/2011_Q2.pdf/f559a007-f545-4f56-d02e-3d49cc01415f) |
| `anb-2011-q3.json` | interim-report | 50 | 2011-09-30 | `0d708d64a6084632` | [link](https://anb.com.sa/documents/55607/85145/2011_Q3.pdf/94a75b11-a806-810d-ded7-99b1a7cb9bba) |
| `anb-2012-annual-report.json` | financial-statements | 36 | 2012-12-31 | `eb0186d4a8d82b78` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2012.pdf/1fa073e3-e7ab-a0e8-cfd1-3fe075dfce46) |
| `anb-2012-q1.json` | interim-report | 37 | 2012-03-31 | `4b60dccb2f783a0b` | [link](https://anb.com.sa/documents/55607/85133/2012_Q1.pdf/484e34e4-f27a-ebef-4849-41f57807f8c7) |
| `anb-2012-q2.json` | interim-report | 50 | 2012-06-30 | `e0349769e10c2706` | [link](https://anb.com.sa/documents/55607/85139/2012_Q2.pdf/aa111bc6-9709-8f42-0c66-3fa69de90844) |
| `anb-2012-q3.json` | interim-report | 49 | 2012-09-30 | `a9bc6a6b71fc9a4d` | [link](https://anb.com.sa/documents/55607/85145/2012_Q3.pdf/f962f9f8-959a-4bc7-5a52-4f208e60ddc9) |
| `anb-2013-annual-report.json` | financial-statements | 36 | 2013-12-31 | `d82326c4e3060730` | [link](https://anb.com.sa/documents/55607/84986/ANB_Financial_Accounts_2013_EN_1.pdf/87b203e2-b92a-23fd-233f-d05e38ccc91a) |
| `anb-2013-q3.json` | interim-report | 51 | 2013-09-30 | `f8b90401b7b6231f` | [link](https://anb.com.sa/documents/55607/85145/2013_Q3_EN.pdf/404d2d19-9485-e925-06ba-9fe47686250c) |
| `anb-2014-annual-report.json` | financial-statements | 37 | 2014-12-31 | `53b2a85f892249d6` | [link](https://anb.com.sa/documents/55607/84986/ANB_AnnualReport_Eng2014_Part2.pdf/3b9fe776-d4fb-af68-a921-20245067ec78) |
| `anb-2014-q1.json` | interim-report | 31 | 2014-03-31 | `591e1d444c038d7e` | [link](https://anb.com.sa/documents/55607/85133/FS_2014_Q1_EN.pdf/00d2d010-923c-3996-1f73-1cadbdba2883) |
| `anb-2014-q2.json` | interim-report | 51 | 2014-06-30 | `1c61d5b0a4b38b4a` | [link](https://anb.com.sa/documents/55607/85139/FS_2014_Q2_EN.pdf/195bdd56-6c5a-61d7-1012-3beb472c73dd) |
| `anb-2014-q3.json` | interim-report | 51 | 2014-09-30 | `ca409e34711ee834` | [link](https://anb.com.sa/documents/55607/85145/FS_2014_Q3_EN.pdf/6770932e-91b6-5bb1-56e1-c1689ae9ce33) |
| `anb-2015-annual-report.json` | financial-statements | 20 | 2015-12-31 | `0482608a38c0f746` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2015.pdf/c7a61b7e-e8d8-7f17-60aa-ee7cdc4d6c59) |
| `anb-2015-q1.json` | interim-report | 31 | 2015-03-31 | `07454afef6843648` | [link](https://anb.com.sa/documents/55607/85133/2015_Q1_EN.pdf/82506114-9eaa-2cb5-df4b-acafa9e395cd) |
| `anb-2015-q2.json` | interim-report | 42 | 2015-06-30 | `15db9b137ac02a94` | [link](https://anb.com.sa/documents/55607/85139/2015_Q2_EN.pdf/8d4daef7-8211-c0c6-cc4a-52a0efb4480b) |
| `anb-2015-q3.json` | interim-report | 45 | 2015-09-30 | `6461ea14020bac26` | [link](https://anb.com.sa/documents/55607/85145/2015_Q3_EN.pdf/16420519-39b3-d0fe-d1e8-566dd4b67ae7) |
| `anb-2016-fy.json` | financial-statements | 35 | 2016-12-31 | `c86538d1ac0d7775` | [link](https://anb.com.sa/documents/55607/85151/English+FS+-++December+2016-1.pdf/19f63ce7-8632-8e3b-7bb4-b0555439dc4f) |
| `anb-2016-q1.json` | interim-report | 34 | 2016-03-31 | `5c0118722160e449` | [link](https://anb.com.sa/documents/55607/85133/FS_2016_Q1_EN.pdf/be4bb82a-0d43-7f3e-b194-36b155bc1c41) |
| `anb-2016-q2.json` | interim-report | 48 | 2016-06-30 | `7817401bbff0abd3` | [link](https://anb.com.sa/documents/55607/85139/FS_2016_Q2_EN.pdf/d25c3a1b-26f2-c2f0-74ca-024a33b075b8) |
| `anb-2016-q3.json` | interim-report | 50 | 2016-09-30 | `4a8cc39d6504277a` | [link](https://anb.com.sa/documents/55607/85145/English+FS+Sept.+2016.pdf/9a861adf-5896-7940-1b3d-5c310fa61799) |
| `anb-2017-annual-report.json` | financial-statements | 21 | 2017-12-31 | `91b1d6217433c1e4` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2017.pdf/b5236175-15e3-3ed2-0df2-34362ec4a596) |
| `anb-2017-q1.json` | interim-report | 34 | 2017-03-31 | `226f79a8a1dca369` | [link](https://anb.com.sa/documents/55607/85133/English+FS+March+31++2017.pdf/2c35040c-2bcb-253e-5884-c9c5e174e44e) |
| `anb-2017-q2.json` | interim-report | 53 | 2017-06-30 | `0da1fdc1ab1110a3` | [link](https://anb.com.sa/documents/55607/85139/English+FS+-+Q2%2C+2017_1.pdf/868dd769-6bf4-2b0d-64c5-dbfe90f25ade) |
| `anb-2017-q3.json` | interim-report | 46 | 2017-09-30 | `88ec8352b154a1ee` | [link](https://anb.com.sa/documents/55607/85145/English+FS+Q3+-+2017.pdf/0f735342-b7aa-cb89-a410-d6206bef50ea) |
| `anb-2018-annual-report.json` | financial-statements | 24 | 2018-12-31 | `b5759f230bdce834` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2018.pdf/01eb3ab9-ca90-5c40-361c-6cf7bd4d6ed8) |
| `anb-2018-q1.json` | interim-report | 37 | 2018-03-31 | `edf97f841f31f37a` | [link](https://anb.com.sa/documents/55607/85133/English+Q1+2018+FS.pdf/f425f210-e285-9b44-1257-bf6043089da8) |
| `anb-2018-q2.json` | interim-report | 53 | 2018-06-30 | `4e20a938adcf9b84` | [link](https://anb.com.sa/documents/55607/85139/English+FS+Q2-+2018_1.pdf/33324173-f867-7fb0-8df3-e64926b1f9dd) |
| `anb-2018-q3.json` | interim-report | 49 | 2018-09-30 | `f6362a4175af0719` | [link](https://anb.com.sa/documents/55607/85145/FS+Q3+English+2018_1.pdf/cc7eb0ca-a610-1dac-5832-617582596448) |
| `anb-2019-annual-report.json` | financial-statements | 30 | 2019-12-31 | `f05ee3e34dc7d21f` | [link](https://anb.com.sa/documents/55607/84986/Financial.statements_2019.pdf/beb71e2a-ce07-f34a-2e52-e61589c1f498) |
| `anb-2019-q1.json` | interim-report | 35 | 2019-03-31 | `6247964e37e68f2b` | [link](https://anb.com.sa/documents/55607/85133/English+FS+March+2019.pdf/93336e8f-7cd2-faa6-de9e-4ff7c0e4ba69) |
| `anb-2019-q2.json` | interim-report | 55 | 2019-06-30 | `afe6c9e74d5cf456` | [link](https://anb.com.sa/documents/55607/85139/English+FS+30+June+2019+ANB+with+review+report_1.pdf/e6fca76c-f888-74d7-63f3-9c0d1cb71ed7) |
| `anb-2019-q3.json` | interim-report | 54 | 2019-09-30 | `eb09e1cb645988c4` | [link](https://anb.com.sa/documents/55607/85145/FS+Q3+2019+-+English.pdf/4b996677-2180-5de2-c73a-b89863c8f9b2) |
| `anb-2020-fy.json` | financial-statements | 35 | 2020-12-31 | `1755779113404f48` | [link](https://anb.com.sa/documents/55607/85151/English_FS_Q4_2020_with_Audit_Report_.pdf/b33f8539-2056-1f97-0cf5-3a8e543b98d9) |
| `anb-2020-q1.json` | interim-report | 45 | 2020-03-31 | `bb7acd369c118165` | [link](https://anb.com.sa/documents/55607/85133/FS+English+-+Q1_2020+with+Audit+Review+Report.pdf/f7fb45c6-cfd9-7c32-2180-d49d855f6503) |
| `anb-2020-q2.json` | interim-report | 58 | 2020-06-30 | `57d4db89a1d051fd` | [link](https://anb.com.sa/documents/55607/85139/English+FSQ2.2020+-+with+Audit+Report.pdf/ffa73127-bf54-388d-7e19-01946ecff1ed) |
| `anb-2020-q3.json` | interim-report | 58 | 2020-09-30 | `e067b1460f52d67c` | [link](https://anb.com.sa/documents/55607/85145/2020_Q3.pdf/3db7780c-2bdb-67d7-8acf-0f79a68c1395) |
| `anb-2021-annual-report.json` | financial-statements | 20 | 2021-12-31 | `f68b8a9f6f75d586` | [link](https://anb.com.sa/documents/55607/0/Financial+-+Annual+Report+2021-+EN+part+2.pdf/bea7ee01-56b5-5cf0-da29-cbcaaa23cb01) |
| `anb-2021-q1.json` | interim-report | 44 | 2021-03-31 | `34a845e4794654c4` | [link](https://anb.com.sa/documents/55607/85133/FS_English+_Q1_2021.pdf/f5567850-ca40-4871-83fb-e87fedb363c1) |
| `anb-2021-q3.json` | interim-report | 38 | 2021-09-30 | `043f5ec235f19686` | [link](https://anb.com.sa/documents/55607/85145/FS.English.Q3.2021.pdf/0bc70cf0-ef11-0713-e37e-ed8fd53540ab) |
| `anb-2022-annual-report.json` | financial-statements | 27 | 2022-12-31 | `11067c275da03584` | [link](https://anb.com.sa/documents/55607/84986/Part+2+-+Financial+Statements+2022.pdf/c54cddc1-9f6f-d6a6-2a67-b9e21081fbbf) |
| `anb-2023-fy.json` | financial-statements | 22 | 2023-12-31 | `a74d0df3a826a1c7` | [link](https://anb.com.sa/documents/55607/0/2023+Q4+FS+EN+1.pdf/e3c733d4-f7f5-77be-6118-73dd6dd28017) |
| `anb-2024-q1.json` | interim-report | 40 | 2024-03-31 | `71a524c250b02aa6` | [link](https://anb.com.sa/documents/55607/0/ANB+FS+-+Q1+2024+EN.pdf/d6d84486-1d5a-6972-b8ff-c050a448662a) |
| `anb-2024-q2.json` | interim-report | 56 | 2024-06-30 | `f5f810a988c9d268` | [link](https://anb.com.sa/documents/55607/0/ANB+FS+-+Q2+2024+EN.pdf/a9d70782-4f7f-5fac-8eb1-9b8d1f2b9d38) |
| `anb-2024-q3.json` | interim-report | 57 | 2024-09-30 | `1ada2b04851817a1` | [link](https://anb.com.sa/documents/55607/0/ANB+FS+-+Q3+2024+EN.pdf/c5242e4f-71ac-3087-8a31-ac7103fa296c) |
| `anb-2025-annual-report.json` | financial-statements | 33 | 2025-12-31 | `b32c41d05bb4b280` | [link](https://anb.com.sa/documents/55607/0/anb+AR25_English+Financial+Statements.pdf/d53d7250-ab72-b324-bbd7-c13dac3d95af) |
| `anb-2025-fy.json` | financial-statements | 94 | 2024-12-31 → 2025-12-31 (2) | `d05a366caba368d1` | [link](https://anb-financial.eurolandir.com/media/n5gahf1d/anb-fs-q4-2025-en.pdf) |
| `anb-2025-q3.json` | interim-report | 49 | 2025-09-30 | `69dc53ff9f488101` | [link](https://anb.com.sa/documents/55607/0/%28anb%29+FS+English+-+Q3+2025.pdf/0334b08c-ec53-2888-3cdb-2b7442a2d4fc) |
