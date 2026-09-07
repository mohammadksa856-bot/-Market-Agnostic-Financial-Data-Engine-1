# Saudi utilities sector — FY2025 batch

Batch branch: `claude/data-utilities-1`. Source-faithful manifests transcribed
by hand from each issuer's official FY2025 audited consolidated financial
statements. No third-party data vendors.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 5110 | Saudi Energy Company (formerly Saudi Electricity Company) | `data/imports/seco-2025-fy.json` | enabled, published | se.com.sa IR FY2025 FS PDF |
| 2082 | ACWA Power Company | `data/imports/acwa-power-2025-fy.json` | enabled, published | acwapower.com IR FY2025 consolidated FS PDF |
| 2083 | Power and Water Utility Company for Jubail and Yanbu (Marafiq) | `data/imports/marafiq-2025-fy.json` | enabled, published | marafiq.com.sa IR FY2025 consolidated FS PDF |

## Sources and archives

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 5110 | `https://www.se.com.sa/-/media/sec/Investors/Financial-Results/FY-2025-Financial-Statements-English.ashx` | `488024b195f0f986619de581c4b44bb0f6675b9ca36beba2dc285de013e02e5c` | `data/raw/SA/5110/documents/488024b1…pdf` |
| 2082 | `https://www.acwapower.com/media/5ulnuxhn/api_consolidated_fs_year-end_2025-_3-03_compressed.pdf` | `b5dad4f16ad2478b5146880d1b96f9cb52174f3ae9bc724f12e53c686de70295` | `data/raw/SA/2082/documents/b5dad4f1…pdf` |
| 2083 | `https://www.marafiq.com.sa/media/5vvplqvl/marafiq-fs-2025-consolidated-fs-english.pdf` | `e5ec1db5eb468dabe179b7650fe4ba0936fa87e31b77d4c9493c3b1a4c1b3e69` | `data/raw/SA/2083/documents/e5ec1db5…pdf` |

All three are registered in `data/raw/archive-index.json`.

* **SECO (5110):** SoFP pages 7-8, profit or loss page 9, cash flows pages
  12-13 (printed page numbers). Auditor Deloitte, signed 21 Ramadan 1447H /
  10 March 2026. The primary-statement pages are **scanned images**; the notes
  are digital text and were used to cross-check.
* **ACWA Power (2082):** SoFP pages 6-7, profit or loss page 8, cash flows
  pages 10-11. Auditor KPMG. Approved by the Board 14 Ramadan 1447H / 3 March
  2026. The PDF is digital text but the two-column layout mis-aligns under text
  extraction, so figures were transcribed from rendered page images.
* **Marafiq (2083):** SoFP page 1, statement of income page 2, cash flows pages
  5-6 (printed statement page numbers). The PDF is **fully scanned** (no
  extractable text); every figure transcribed from page images. `filed_at` is
  the 24 February 2026 Board meeting date (dividend resolution, note 34) — the
  statements carry no separate printed approval date.

## Mapping notes

* **SECO — Mudaraba instrument.** The "Mudaraba instrument" (SAR 173.6bn at
  2025 year-end) is a subordinated Saudi government financing instrument that
  SEC **classifies within equity**. `total_equity` (257.7bn) includes it, so
  engine-derived leverage ratios (debt-to-equity ≈ 0.77, ROE 5.1%) reflect the
  issuer's presentation. An analyst treating the Mudaraba instrument as debt
  would see a very different capital structure. `eps_diluted` is the reported
  after-Mudaraba figure attributable to ordinary shareholders (0.96 for 2025,
  −0.46 for 2024); the pre-Mudaraba EPS is 3.11 / 1.65.
* **SECO `income_taxes_and_zakat`** is the reported Zakat expense (SEC pays no
  corporate income tax); effective rate ~2.6%, a legitimate zakat rate.
* **SECO / ACWA / Marafiq `depreciation_amortization`** is the sum of the
  depreciation/amortisation add-backs on the cash-flow statement — none of the
  three presents a separate D&A line in profit or loss.
* **ACWA Power** `operating_income` is "Operating income after impairment loss
  and other expenses"; `investments_associates` / `share_of_profit_associates`
  are the equity-accounted-investee balance and result (net of zakat and tax).
  FY2024 EPS is restated for the 2025 bonus issue.
* **Marafiq** carries large IFRS 16 lease liabilities (power/water purchase and
  Royal Commission land): mapped as `lease_liabilities_noncurrent` /
  `lease_liabilities_current`, kept out of `long_term_debt` (which is bank loans
  and borrowings only). No current-portion bank borrowing at 2025 year-end.
* All three: no non-controlling interest except ACWA Power (mapped
  `equity_parent` + `noncontrolling_interests`).

## Verification

`finengine verify seco` → 20 pass / 0 warn / 0 fail.
`finengine verify acwa` → 24 pass / 0 warn / 0 fail.
`finengine verify marafiq` → 20 pass / 0 warn / 0 fail.

Bootstrap into a throwaway snapshot publishes 182 (SECO), 202 (ACWA Power) and
185 (Marafiq) data points with no pipeline errors. Derived FY2025 checks:

| | SECO | ACWA Power | Marafiq |
|---|---|---|---|
| net margin | 12.7% | 27.8% | 6.5% |
| operating margin | 18.7% | 42.5% | 18.1% |
| gross margin | 20.3% | 50.8% | 11.8% |
| return on equity | 5.1% | 7.4% | 8.3% |
| free cash flow | −SAR 38.7bn | +SAR 0.11bn | +SAR 1.22bn |

SECO's deeply negative FCF is a real capacity-build year (capex ≈ 86% of
revenue). ACWA Power's high margins reflect its developer/operator model
(equity-accounted project income, not consolidated plant revenue).

Tests: `tests/test_utilities_sector.py`.

## Unresolved fields

* **EBITDA / net debt / net-debt-to-EBITDA.** None of the three presents EBITDA
  or a net-debt reconciliation as a line in the audited statements. The engine
  does not derive EBITDA without a reported `ebit`. If a deterministic
  definition is agreed it should be wired platform-side, not baked into these
  manifests.
* **SECO regulatory disclosures** — the balancing account, required-revenue /
  WACC mechanism (6.65% for 2024-2026), and deferred government grants are
  described in the notes but not extracted as structured facts this batch.
* **ACWA Power operational KPIs** — gross power capacity (GW), water desalination
  capacity, portfolio megawatts by technology, are in the investor report, not
  the audited statements; out of scope for source-faithful FS manifests.
* **Marafiq** — the FY2024 `dividends_paid` line is mapped; the FY2025 cash-flow
  statement shows no dividend paid during the year (the SAR 450m FY2025 dividend
  was resolved 24 February 2026, after year-end).
* **Segment disclosures** (SECO generation/transmission/distribution; Marafiq
  power/water/wastewater) live in the notes and were not extracted this batch.
* **No engine or catalog changes in this batch** — all three manifests map to
  existing catalog fields.
