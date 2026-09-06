# Saudi banking sector — data batch

All ten listed Saudi banks, FY2025 audited consolidated financial statements
(FY2024 comparatives from the same filing), plus the machine-readable data
supplements where the issuer publishes one.

Every figure is a source-faithful reported line. Ratios (NIM, cost-to-income,
NPL ratio / coverage, capital adequacy, CASA, LDR, cost of risk, ROE,
`bank_health_score`) are recomputed by `finengine`; an issuer's own published
ratio is used only as a cross-check.

## Sources (official issuer filings, archived by SHA-256)

| Symbol | Bank | Manifest(s) | Source | Archived (`data/raw/SA/<sym>/documents/`) |
|---|---|---|---|---|
| 1010 | Riyad Bank | `riyad-2025-fy.json` | riyadbank.com IR — Annual Consolidated Financial Statements | `89240afe…pdf` |
| 1020 | Bank AlJazira | `aljazira-2025-fy.json` | bankaljazira.com IR — `ajb-fs-fy-2025-english.pdf` | `2b5d332d…pdf` |
| 1030 | Saudi Investment Bank | `saib-2025-fy.json` | saib.com.sa IR — `SAIB_FS-q42025-en.pdf` | `b6b7f03a…pdf` |
| 1050 | Banque Saudi Fransi | `bsf-2025-fy.json` | bsf.sa IR — `Financial_Statments_Q4_2025.pdf` | `8fcf18cd…pdf` |
| 1060 | Saudi Awwal Bank | `sab-2025-fy.json` | sab.com IR — `SAB FS December 31 2025 - English.pdf` | `ecda5fc2…pdf` |
| 1080 | Arab National Bank | `anb-2025-fy.json` | anb.com.sa IR (eurolandir) — `anb-fs-q4-2025-en.pdf` | `d05a366c…pdf` |
| 1120 | Al Rajhi Bank | `alrajhi-2025-fy.json`, `alrajhi-supplement.json` | alrajhibank.com.sa IR — audited FS PDF + ARB External Data Supplement (xlsx, FY2014→) | `67b6f23b…pdf`, `87d53f4a…xlsx` |
| 1140 | Bank Albilad | `albilad-2025-fy.json` | bankalbilad.com.sa IR — `BAB YE - 2025 English FS.pdf` | `45af3a2d…pdf` |
| 1150 | Alinma Bank | `alinma-supplement.json`, `alinma-notes-2025.json` | ir.alinma.com — Alinma Data Supplement (xlsx, FY2018→) + audited FS PDF for note-level items | `451026b7…xlsx`, `8a721eb9…pdf` |
| 1180 | Saudi National Bank | `snb-2025-fy.json` | alahli.com IR — `SNB-YE-2025-Financials-English.pdf` | `510a940d…pdf` |

`data/raw/archive-index.json` links each hash to its manifest, source URL, byte
size and content type.

## Reader

- **Text-extractable primary statements** (`reader: manual.text/…`): 1010, 1050,
  1080, 1140, 1180. Figures transcribed line-for-line from the statement pages.
- **Scanned primary statements** (`reader: manual.vision/…`): 1020, 1030, 1060,
  1120. The filed PDF renders the three primary statements as page images; the
  auditor report and every note are digital text. Statement figures read from the
  page images; note-level figures (loan staging, capital adequacy, deposit split)
  read from the text notes.
- **Data supplement** (`reader: finengine.reading_xlsx/1`): 1120 (12 years),
  1150 (8 years). Raw reported lines only; the supplement's own ratio rows are not
  mapped.

## Per-issuer notes

- **1080 ANB / 1020 AlJazira / 1030 SAIB** — `provision_expense` combines the
  expected-credit-loss charge with the other-real-estate impairment / reversal so
  `total_operating_expenses = operating_expense_banking + provision_expense`
  holds. `income_taxes_and_zakat` = Zakat + income tax.
- **1080 ANB** — `net_income` includes a small discontinued-operations result
  (AHEL held for sale); the pre-tax − tax = net-income identity therefore clears
  only within tolerance, which is expected.
- **1060 SAB** — presents the ECL provision as its own line above operating
  expenses, so there is no all-in "total operating expenses" figure to ingest;
  `operating_expense_banking` is SAB's reported "Total operating expenses" (ex
  provision) and `total_operating_expenses` is deliberately not ingested.
- **Banks with no non-controlling interest** (1010, 1050, 1140, 1020, 1030, 1060)
  map `total_equity` only; `equity_parent` / `noncontrolling_interests` are not
  applicable.
- **1120 Al Rajhi supplement** — `Fee from banking services, net` and
  `Investments, net` are intentionally unmapped: the audited FS owns gross
  `fee_income` / `fee_expense` and the note-36 `bank_investments` figure (the
  supplement's investments line runs ~SAR 1.16 bn above note 36).

## Unresolved / not-yet-available fields, with reasons

| Field(s) | Banks | Reason |
|---|---|---|
| `capital_adequacy_ratio` (and `risk_weighted_assets`) | 1020 AlJazira | The FY2025 FS capital-adequacy note discloses eligible capital and the ratios but **not** the RWA amount. Not ingested rather than back-computed from the ratio. |
| `bank_health_score` at full weight | 1020 AlJazira | Fires with 3 evaluable signals (no CAR); scores 5/7 for the other nine banks. |
| `cet1_ratio`, `tier1_capital_ratio`, `cost_of_funds` | all 10 | The CET1 / Tier-1 **capital amounts** are disclosed but the catalog carries these as engine-computed ratios needing a per-tier capital metric that is not yet modelled. Issuer-published CET1 / Tier-1 ratios recorded here as cross-checks only. |
| `net_interest_margin`, `return_on_equity`, `cost_of_risk` for single-year manifests | 1120 FY manifest (supplement covers history) | Need an opening balance; compute once FY2024 lands or from the supplement. |
| `time_deposits` "others" residual | 1180, 1120, 1050, 1080, 1030, 1010 | Issuers report a small "other customer accounts / margins" bucket outside demand/savings/time; left unmapped (not demand, savings or time). |
| Segment P&L, ownership, market data, valuation, analyst consensus | all 10 | Out of scope for this batch — separate feeds (segments pack, Tadawul ownership, price feed, consensus interface). |

## Cross-checks (engine vs. issuer disclosure, FY2025)

| Bank | Metric | Engine | Disclosed |
|---|---|---|---|
| 1120 Al Rajhi | CAR (Tier 1+2) | 21.85% | 21.85% |
| 1180 SNB | CAR (Tier 1+2) | 21.16% | 21.2% |
| 1010 Riyad | CAR (Tier 1+2) | 18.35% | 18.35% |
| 1080 ANB | CAR (Tier 1+2) | 20.02% | 20.02% |
| 1140 Albilad | CAR (Tier 1+2) | 20.20% | 20.20% |
| 1060 SAB | CAR (Tier 1+2) | 19.65% | 19.65% |
| 1030 SAIB | CAR (Tier 1+2) | 19.32% | 19.32% |
| 1150 Alinma | CAR | 19.89% | 19.89% |
| 1120 Al Rajhi | cost-to-income | 23.3% | 23.3% |
| 1180 SNB | cost-to-income | 25.2% | ~25% |
