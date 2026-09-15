# Saudi banks — SAB (1060) and SNB (1180), batch 1

Branch `claude/banks-sab-snb-enrichment`. Scope is limited to Saudi Awwal Bank
(`sa:1060`) and The Saudi National Bank (`sa:1180`); ANB is untouched. No database,
deployment, service or worker was changed. Every fact below was produced by an
engine reader from an archived official document and verified before it was
written; nothing was transcribed by hand and nothing was estimated.

## What changed for the two banks

| | Before | After this batch |
|---|---|---|
| SNB periods | FY2024, FY2025 (one audited filing) | FY2022–FY2025 flows; 10 quarter-end balance sheets (Mar-2024 → Jun-2026); 10 discrete quarters; YTD H1/9M 2024–2026 |
| SNB regulatory capital | none | 18 consecutive quarter ends, Mar-2022 → Jun-2026: regulatory capital, RWA, CET1 ratio, Tier 1 ratio (CAR is calculated by the engine) |
| SAB regulatory capital | none | 20 quarter ends, Dec-2019 → Mar-2026 (gaps listed below) |
| New manifests | — | 25 (19 SNB, 6 SAB), 44 MB of archived sources |

Whole-directory verification (`finengine verify --imports data/imports`):
98 manifests, 721 checks, 708 pass, 13 warnings (all pre-existing, other issuers),
0 failures.

## Source priority applied

1. **Issuer IR (primary).** SNB `financial-information` library (reviewed interim
   statements, quarterly Financial Data Supplements, Pillar 3); SNB and SAB Pillar 3
   filings hosted on the issuer domains.
2. **Saudi Exchange.** Not needed for the periods published here; it remains the
   route for SAB interim statements (see exceptions).
3. **Regulator.** Not needed; Pillar 3 is the SAMA-mandated disclosure itself.

## Reusable engine changes (read before merging)

Adapters and readers — Claude workstream:

* `reading_pillar3.py` — new generic Basel III Pillar 3 **KM1** reader. One reader
  for every Saudi bank: geometry-based columns, explicit unit required on the page,
  column headers must form an unbroken quarterly sequence (issuer typos are excluded
  with evidence, never re-dated), and a column is published only if CET1, Tier 1 and
  total capital amounts reproduce the printed ratios within printed rounding.
  Verified on 14 real SNB/SAB filings across four layout generations.
* `manifest_vintages.py` — new. One source of record per fact when publications
  overlap (each supplement repeats five quarters, each KM1 five quarter ends).
  Rank: assurance (statements > regulatory disclosure > supplement), then latest
  period covered, then `filed_at`. Superseded and restated values stay in
  `excluded_facts` with the winning source. `by_period=True` makes the reviewed
  statement the source of record for its whole period, so identities never mix
  original and restated vintages.
* `reading.py` (StatementReader), each with a regression test:
  * rule lines drawn as text (`────`) no longer capture a subtotal's figures;
  * a blank cell never borrows a neighbouring column's figure;
  * typographic apostrophes normalised; captions match only at a word start
    (`non-operating income` is not `operating income`);
  * note references `10,` / `(a)` stripped from captions;
  * reversible credit-impairment sign follows the statement's convention
    (a parenthesised amount on an unsigned-expense statement is a reversal);
  * salaries, G&A and depreciation added to the unsigned-expense set;
  * diluted EPS extracted with a `SAR/share` unit and exempt from the magnitude filter;
  * bank captions: gross/net fee income, financing and advances, impairment
    charge/(reversal), expenses before ECL, other operating income/(expenses) net.
* `reading_xlsx.py` — opt-in `precision` (mapping or row) removes spreadsheet
  float noise; manifests now carry `period_end`.
* `fetching.py`, `connectors/issuer.py` — Pillar 3 / Basel III discovery keywords
  and a `regulatory-disclosure` document type checked before quarter tokens.

**Platform-owned files — separate commit, needs Codex review:**

* `cli.py` — routes `regulatory-disclosure` PDFs to the KM1 reader; `_source_period`
  accepts quarter-end month names (`march-2026`, `Dec-2025`, `Dec_20`,
  `30 June 2025`) for interim and regulatory filings only (annual reports excluded
  because titles can carry a publication month) and unquotes URLs.

**Contract decision for Codex.** KM1 `cet1_ratio` and `tier1_capital_ratio` are
published as reported by the regulatory disclosure (reconciled to the amounts in
the same table) because the catalog has no CET1/Tier 1 amount fields to compute
them from. `capital_adequacy_ratio` is *not* published — the engine calculates it
from the published `regulatory_capital` / `risk_weighted_assets`, and the printed
ratio is kept as a passed cross-check. If computed-only ratios are preferred, add
`cet1_capital` and `tier1_capital` to the catalog (values are already extracted in
`excluded_facts`) and switch the reader's row mapping.

## Documents and manifests

All archived under `data/raw/SA/<symbol>/documents/<sha256>.<ext>` and indexed in
`data/raw/archive-index.json`. `filed_at` is inferred: issuer files expose no
machine-readable publication time, so it is the PDF creation date or workbook
last-modified date (`filed_at_basis` in each manifest; SNB 3Q-2025 has neither and
uses the retrieval date). Ranking never relies on it alone.

| Manifest | Type | Facts | Periods | SHA-256 (first 16) | Official URL |
|---|---|---:|---|---|---|
| snb-2023-q1-pillar3.json | regulatory-disclosure | 20 | Mar-22 → Mar-23 | f1231091a31282df | alahli.com …/english/basel-iii-pillar-q1-2023-final.pdf |
| snb-2024-q2-pillar3.json | regulatory-disclosure | 8 | Jun-23, Sep-23 | 4e03ee3c61597d09 | …/english/basel-iii-pillar-3q2-2024.pdf |
| snb-2024-q4-pillar3.json | regulatory-disclosure | 4 | Dec-23 | 4d3b5bcc7c028795 | …/english/Basel-IV-Pillar-3-December-2024-Final-with-Remuneration.pdf |
| snb-2025-q1-pillar3.json | regulatory-disclosure | 4 | Mar-24 | 3d165a4840557d3b | …/English/SNB-Pillar-3-Disclosures-Q1-2025.pdf |
| snb-2025-q2-pillar3.json | regulatory-disclosure | 4 | Jun-24 | 55e1ef5c6878de12 | …/english/snb-pillar-3-disclosures-q2-2025.pdf |
| snb-2025-q3-pillar3.json | regulatory-disclosure | 4 | Sep-24 | 6713b3c181b66ba7 | …/english/SNB-Pillar-3-Disclosures-Q3-2025.pdf |
| snb-2025-q4-pillar3.json | regulatory-disclosure | 4 | Dec-24 | cdc4f9f2a9cb55a5 | …/english/SNB-Pillar-3-Disclosures-Dec-2025-HR.pdf |
| snb-2026-q1-pillar3.json | regulatory-disclosure | 4 | Mar-25 | 20ae7010d38373b7 | …/English/SNB-Pillar-3-Disclosures-Q1-2026.pdf |
| snb-2026-q2-pillar3.json | regulatory-disclosure | 20 | Jun-25 → Jun-26 | 47232592de58baba | …/english/SNB-Pillar-3-Disclosures-Q2-2026.pdf |
| snb-2025-q1-supplement.json | data-supplement | 34 | Q1-24 | fce918d2699e865a | …/financial-data-supplement/english/snb-1q-2025-data-supplement.xlsx |
| snb-2025-q2-supplement.json | data-supplement | 52 | Q2-24, H1-24 | 62b7419cec5dbf3f | …/snb-2q-2025-data-supplement.xlsx |
| snb-2025-q3-supplement.json | data-supplement | 88 | FY22, FY23, Q3-24, 9M-24 | 2a6db9db47f405e0 | …/snb-3q-2025-data-supplement.xlsx |
| snb-2025-q4-supplement.json | data-supplement | 18 | Q4-24 | 0ded488172fd3902 | …/SNB-4Q-2025-Data-Supplement.xlsx |
| snb-2026-q1-supplement.json | data-supplement | 34 | Q1-25 | 8325cf411a3b8abb | …/snb-1q-2026-data-supplement.xlsx |
| snb-2026-q2-supplement.json | data-supplement | 36 | Q4-25, Q1-26 (discrete quarters) | cd8439096b29a3da | …/snb-2q-2026-data-supplement.xlsx |
| snb-2025-q2.json | interim-report | 69 | Q2-25, H1-25 | d1cb051e03c338ac | …/Financial-Statements/English/2Q-2025-Financial-Statement-English.pdf |
| snb-2025-q3.json | interim-report | 69 | Q3-25, 9M-25 | e272c89f1cf2b25a | …/SNB-3Q-2025-Financial-Statements-English.pdf |
| snb-2026-q1.json | interim-report | 45 | Q1-26 | 85441d26c682dbcc | …/SNB-1Q-2026-Financials-English.pdf |
| snb-2026-q2.json | interim-report | 69 | Q2-26, H1-26 | d55aa563e5894121 | …/SNB-2Q-2026-Financials-English.pdf |
| sab-2020-q4-pillar3.json | regulatory-disclosure | 20 | Dec-19 → Dec-20 | 565a692ef6665f9c | sab.com …/2020/basel-disclosures/Basel_III_Pillar_3_Disclosures_Dec_20_EN.pdf |
| sab-2023-q2-pillar3.json | regulatory-disclosure | 8 | Jun-22, Sep-22 | bb2ab2da67a1116e | …/2023/basel-disclosures/Q2-2023-Basel-III-Pillar-3-Disclosures-Updated.pdf |
| sab-2023-q4-pillar3.json | regulatory-disclosure | 20 | Dec-22 → Dec-23 | 5b2ef7851a2672bd | …/documents/Dec 2023 - Annual Pillar 3 Disclosures EN (Resubmitted).pdf |
| sab-2025-q2-pillar3.json | regulatory-disclosure | 8 | Jun-24, Sep-24 | a037941047cea8ab | …/2025/basel-disclosures/SAB - PILLAR 3 Disclosures - Jun 2025.pdf |
| sab-2025-q4-pillar3.json | regulatory-disclosure | 4 | Dec-24 | 4a7c00f9613821fd | …/2025/basel-disclosures/Basel III Pillar 3 Disclosures - 2025 English.pdf |
| sab-2026-q1-pillar3.json | regulatory-disclosure | 20 | Mar-25 → Mar-26 | 9b2c9d0dc7958ed9 | …/2026/sab-pillar-3-disclosures-march-2026.pdf |

Full URLs and hashes are in each manifest and in the archive index. The SNB
supplement map is `config/supplements/1180.json`; the SNB registry now monitors the
`financial-information` library first.

## Exception queue (not published, with reason and resolution)

| # | Item | Reason | Resolution |
|---|---|---|---|
| 1 | SNB interim statements Q1-2025 | Statement pages 3–8 are images with no text layer (`pdf_ocr_required`). Q1-2025 balances and discrete quarter are published from the later 1Q-2026 supplement. | Run the worker with the OCR extra; the reviewed statement will then outrank the supplement automatically. |
| 2 | SNB Pillar 3 Q1-2024 | KM1 page declares no amount unit (`unit_not_declared`); the unit is not inferred from other tables. No gap: all five quarter ends are published from adjacent filings. | None needed; keep archived. |
| 3 | SNB Pillar 3 Dec-2025, column d | Header printed "31 Mar 2024" between Jun-25 and Dec-24 (issuer typo) — column excluded, not re-dated. Mar-25 published from Q1-2026. | None. |
| 4 | SNB Pillar 3 Q3-2025, column b | Header printed "30 Jun 205" — excluded. Jun-25 published from Q2-2026. | None. |
| 5 | SNB Pillar 3 Q2-2024 leverage ratio | Printed leverage ratio does not reconcile to Tier 1 / exposure for any column. Leverage is not published (no catalog field). | Review the row mapping for that layout before adding leverage fields. |
| 6 | SAB Pillar 3 Dec-2024 | KM1 table is an image (listed on page 4, no text) → `km1_table_not_found`. Leaves SAB Mar-2024 capital as a gap. | OCR, or an issuer text rendition. |
| 7 | SAB Pillar 3 Mar-2021 → Mar-2022 | Filings not located on sab.com. | Request from SAB IR or locate the archived library pages. |
| 8 | SAB Financial Data Pack (XLSX, 1Q-2022 → Q2-2026) | Issuer WAF returns "Request Rejected" to both direct HTTP and the headless browser (`source_access_blocked`). The PDF rendition downloads and carries 16 quarters of IS/BS and KPI history. | Authorized-network fetch of the XLSX, or a reviewed PDF period-table adapter for the PDF rendition. |
| 9 | SAB interim statements Q1/Q2/Q3-2025 (downloaded, hashes in scratch log) | Text layer present but statement titles are images, so the statement-heading gate finds nothing (0 facts). SAB also prints "Total operating expenses" *excluding* impairment, unlike SNB. | Heading-less statement detection (TOC page numbers + statement signatures), or OCR of the title band; map SAB's total to `operating_expense_banking`. |
| 10 | Capital amounts, leverage, LCR, NSFR (both banks) | Extracted and reconciled (LCR and NSFR pass their cross-checks) but no catalog fields: `cet1_capital`, `tier1_capital`, `leverage_ratio_exposure`, `leverage_ratio`, `high_quality_liquid_assets`, `net_cash_outflow`, `liquidity_coverage_ratio`, `available_stable_funding`, `required_stable_funding`, `net_stable_funding_ratio`. Held in `excluded_facts` (`catalog_field_missing`). | Catalog proposal for Codex; then republish from the same manifests. |
| 11 | NPL, NPL coverage, gross loans, stage 1–3 loans, credit-loss allowance, CASA (demand/savings/time deposits) | Not on the primary statements; they live in IFRS 9 credit-quality and deposit notes. Supplement ratios are issuer-defined (e.g. "excluding POCI") and the contract computes these ratios, so they were not mapped. | Note-table reader for the credit-quality and customer-deposits notes. |
| 12 | NIM, cost of risk, loans-to-deposits, cost-to-income | Not a gap: the engine calculates them from the ingested lines. | — |
| 13 | SNB annual history 2015–2021; SAB annual history | Annual reports discovered (SNB/NCB 2000–2025 on the IR page) but not extracted. Mergers (NCB + Samba, 2021; SABB + Alawwal, 2019) need a legal-predecessor and restatement decision. | Annual-report extraction batch with predecessor tagging. |
| 14 | Supplement "Depreciation and amortization" | Includes amortisation of intangibles (FY2024 SAR 2,608.054 mn) while the audited statement's line excludes it (SAR 1,787,774 thousand) — a different definition. Not mapped. | — |
| 15 | Supplement restatements | Later vintages reclassify earlier quarters (e.g. SNB Q3-2024 net fee income 1,164.067 → 1,216.430 → 1,163.809 SAR mn). The latest vintage is published; earlier values are kept as `restated_in_higher_ranked_publication`. | — |
| 16 | SNB interim cash-flow subtotals | Operating/investing/financing subtotals not captured from the interim cash-flow layout (only opening/closing cash and taxes paid). | Caption mapping for the interim cash-flow statement. |
| 17 | Publication timestamps | Issuer files expose none; `filed_at` is inferred from document metadata. | Link each document to its Saudi Exchange announcement time. |

## Verification performed

* Targeted tests: reader, Pillar 3, supplement, vintages, fetching, monitoring.
* Full suite: 316 tests, 2 errors, 1 skipped — the 2 errors are identical to the
  baseline before this branch: `test_aramco_*` quote-grounding tests need Aramco
  PDFs that are not tracked in git and are absent from a fresh worktree.
* `finengine verify --imports data/imports`: 98 manifests, 0 failures.
* CI-parity `bootstrap` into a throwaway database: all 98 manifests published, no
  publication batch blocked, zero open exceptions for either bank.
  `audit --strict-warnings`: 0 failures, 1 warning (`enabled_company_coverage` for
  five US energy issuers, unrelated to this batch).
* Published result in that database: SNB 838 current data points (156 calculated),
  capital metrics for 18 consecutive quarter ends; the engine-calculated
  `capital_adequacy_ratio` for Jun-2026 is 21.978%, matching SNB's printed 21.98%.
  SAB 231 current data points with capital metrics for 20 quarter ends.
