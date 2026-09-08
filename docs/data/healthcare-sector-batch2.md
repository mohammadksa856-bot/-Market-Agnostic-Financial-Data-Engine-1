# Saudi health care sector — FY2025 batch 2

Batch branch: `claude/data-healthcare-2`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited consolidated financial statements
(the full audited PDFs linked on the Saudi Exchange company-profile "Financial
Statements" tab, "Annual / 2025" cell). No third-party data vendors. No engine or
catalog changes in this batch.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 4002 | Mouwasat Medical Services Company | `data/imports/mouwasat-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (KPMG) |
| 4004 | Dallah Healthcare Company | `data/imports/dallah-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (KPMG) |
| 4005 | National Medical Care Company (Care) | `data/imports/care-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 4002 | `https://www.saudiexchange.sa/Resources/fsPdf/433_0_2026-03-26_14-16-17_En.pdf` | `9287e05dc10deb97a50ee2946b7a956cfe4bba6a02e48790db5d5208973d086a` | `data/raw/SA/4002/documents/9287e05d…pdf` |
| 4004 | `https://www.saudiexchange.sa/Resources/fsPdf/435_0_2026-03-12_15-01-34_En.pdf` | `61cf552a91922dc3ef68a9f7c92c04abe575984ec0f473242327b291f6b98c1b` | `data/raw/SA/4004/documents/61cf552a…pdf` |
| 4005 | `https://www.saudiexchange.sa/Resources/fsPdf/436_0_2026-02-24_15-19-49_En.pdf` | `a359133b837c67e73325657b47e84b0b37935646a242ca0abb6914c72b8bf4f0` | `data/raw/SA/4005/documents/a3591338…pdf` |

Registered in `data/raw/archive-index.json` (Mouwasat 5,313,371 bytes; Dallah
3,127,719 bytes; Care 3,627,501 bytes; all `application/pdf`).

## Company notes

All three publish in **full Saudi Riyals** (`scale` 1). In every filed PDF the
primary statements are **scanned images** (transcribed from page renders at
2.6×); the notes are digital text.

* **Mouwasat (4002):** auditor KPMG; board approved the statements 22 Ramadan
  1447H / **11 March 2026** (Note 39). Consolidated with non-controlling
  interests; no discontinued operations. `revenue` combines "Medical services
  revenue" and "Pharmaceutical sales"; `cost_of_revenue` combines "Cost of
  operations" and "Cost of sales". `impairment_charges` is the "Reversal /
  (impairment) loss on accounts receivables" line — a **net reversal** of
  SAR 9.83m in FY2025 (a positive figure). `income_taxes_and_zakat` is the single
  "Zakat expense" line. FY2025: revenue +11.9% to SAR 3.22bn, net income +27.2%
  to SAR 852.0m, EPS 4.11. verify 24 pass / 0 warn / 0 fail; 222 data points.

* **Dallah Healthcare (4004):** auditor KPMG; statements authorised for issue
  15 Ramadan 1447H / **4 March 2026** (Note 37). Consolidated with non-controlling
  interests; no discontinued operations. The FY2024 comparative balance sheet
  carried SAR 118.5m of land as IFRS 5 "Assets held for sale" **inside** the
  current-assets subtotal (nil at FY2025), so no subtotal adjustment is needed.
  `intangible_assets` is the combined "Intangible assets and goodwill";
  `investments_associates` is "Equity-accounted investees";
  `share_of_profit_associates` is the "Group share of results from equity
  accounted investees" line below operating profit. `additional_paid_in_capital`
  is "Share premium"; `other_reserves` combines the statutory reserve and the
  negative fair-value reserve. FY2025 was an **acquisition year** — SAR 313.8m
  spent (net of cash) on subsidiaries plus SAR 435.3m to buy additional NCI, so
  total assets jumped ~38% to SAR 9.14bn and long-term murabaha financing more
  than doubled. Net income +11.4% to SAR 540.5m, EPS 5.32. verify 24 pass /
  0 warn / 0 fail; 226 data points.

* **Care / National Medical Care (4005):** auditor PwC; statements approved by the
  board **17 February 2026** (stated on the face of the SoFP). Consolidated
  group, **no non-controlling interest** (equity = share capital + treasury
  shares + share-based-payment reserve + retained earnings), so only
  `total_equity` is carried. The **FY2024 comparatives are restated** — income
  statement, cash-flow statement and balance sheet updated for additional
  depreciation from finalising the purchase-price allocation on the Al-Salam
  acquisition (Note 14). `intangible_assets` is the combined "Goodwill and
  intangible assets"; `short_term_investments` is "Term deposits";
  `impairment_charges` is "Expected credit loss allowance". `income_taxes_and_zakat`
  is "Zakat (expense) reversal" — a SAR 27.9m charge in FY2025 and a net
  SAR 4.5m **credit** in FY2024 (prior-year zakat reversal), so the effective-tax
  plausibility bound warns on FY2024 (expected). FY2024 operating profit also
  included a SAR 42.3m "Reversal of charge against legal claims" one-off (no
  dedicated catalog field; not separately mapped). FY2025: revenue +23.7% to
  SAR 1.60bn, net income +8.1% to SAR 318.5m, EPS 7.13. verify 19 pass /
  1 warn / 0 fail; 202 data points.

## Verification

`finengine verify mouwasat` → 24 / 0 / 0; `finengine verify dallah` → 24 / 0 / 0;
`finengine verify care` → 19 / 1 / 0 (the one warn is the effective-tax bound on
Care's FY2024 zakat credit). Bootstrap publishes 222 + 226 + 202 data points with
no pipeline errors. All balance-sheet identities, the pre-tax→net bridge, the
owners/NCI split (Mouwasat, Dallah) and the cash-flow reconciliation hold
exactly, and each issuer's cash-flow closing balance ties to its balance-sheet
cash line.

Tests: `tests/test_healthcare_sector_batch2.py`.

## Unresolved fields

* **FY2024 legal-claims reversal (Care)** — the SAR 42.3m "Reversal of charge
  against legal claims" sits inside FY2024 operating profit but has no catalog
  field; carried only implicitly via `operating_income`.
* **Operational KPIs** (bed count, occupancy, outpatient / inpatient volumes,
  hospital-level breakdown) are in the board reports, not the audited FS.
* **EBITDA / net debt** — not presented as statement lines.
* **No engine or catalog changes in this batch.**
