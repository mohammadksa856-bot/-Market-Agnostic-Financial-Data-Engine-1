# Saudi retail sector — FY2025 batch 1

Batch branch: `claude/data-retail-1`. Source-faithful manifest transcribed by hand
from the issuer's official FY2025 audited consolidated financial statements. No
third-party data vendors. No engine or catalog changes.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 4190 | Jarir Marketing Company | `data/imports/jarir-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF |
| 4003 | United Electronics Company (eXtra) | `data/imports/extra-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 4190 | `https://www.saudiexchange.sa/Resources/fsPdf/454_0_2026-03-31_11-52-35_En.pdf` | `7c1e35764a96d4d66cc748468d4608d9e4d2b13ff159e990596948c6e9ce2f36` | `data/raw/SA/4190/documents/7c1e3576…pdf` |
| 4003 | `https://www.saudiexchange.sa/Resources/fsPdf/434_0_2026-02-18_11-09-38_En.pdf` | `99fc44596d81650a9184561b09a3df278afb66803b712723c573971f6bef25ea` | `data/raw/SA/4003/documents/99fc4459…pdf` |

Registered in `data/raw/archive-index.json` (Jarir 2,152,108 bytes; eXtra 4,794,977 bytes; both `application/pdf`).

### How the audited FS was retrieved

The Saudi Exchange company-profile "Financial Statements" tab
(`NJstatementsTabData?statementType=6`) lists, per fiscal year, an **"Annual"**
row linking the **full audited consolidated FS** (auditor's report + notes) on
`Resources/fsPdf/<issuerCode>_0_<datetime>_En.pdf` — distinct from the "Board
Report" row (board annual report) and the Q1–Q4 rows (interim). The portlet only
renders through the site's own search flow (from a residential IP), so the tab
was opened in the browser and the `fsPdf` link scraped; the PDF itself is then a
plain static resource fetchable by URL. Issuer codes: Jarir 454, eXtra 434.

* **eXtra / United Electronics (4003):** audited consolidated FS filed 18 Feb
  2026; **PwC** auditor's report (printed pages 2–6, digital text); the combined
  statement of profit or loss and OCI (printed page 7), financial position (8–9),
  changes in equity (10) and cash flows (11–12) are **scanned images**
  (transcribed from renders at 2.5×); notes (page 13+) digital text. Board
  authorised for issue **12 February 2026** (used as `filed_at`). Thousands of
  SAR (`scale` 1000). eXtra runs a consumer Islamic-financing / instalment book
  alongside electronics retail — `revenue` combines "Sales and services",
  "Income from Islamic financing contracts" and "Income from payroll advances";
  the financing receivables are carried as `long_term_investments` /
  `short_term_investments` ("Investment in Islamic financing contracts",
  non-current / current). `impairment_charges` is "Net impairment losses on
  financial assets" (mostly on that book). `operating_income` is a computed
  subtotal. `income_taxes_and_zakat` = Zakat + income tax combined (also split).
  `contract_liabilities` = non-current "Deferred revenue" (extended-warranty /
  service contracts). `long_term_debt` / `current_debt` = non-current / current
  "Borrowings"; IFRS 16 leases mapped separately. `depreciation_amortization`
  sums PP&E depreciation, right-of-use depreciation and intangible amortisation
  from the cash-flow statement. `capex` = "Payments for purchases of property and
  equipment". The cash-flow statement has no separate FX-effect line.

* **Jarir (4190):** the file linked from the "Annual Financial Results"
  announcement (Tadawul form 1_17) is the earnings release, not the audited
  statements. The full audited consolidated FS is the PDF linked in the
  "Annual / 2025" cell of the company-profile **Financial Statements** tab
  (`NJstatementsTabData?statementType=6&reportType=0`). Board of Directors
  authorised the statements for issue on **30 March 2026** (used as `filed_at`).
  In the filed PDF all five primary statements are **scanned images**
  (transcribed from page images rendered at 2.4×); the notes (printed pages
  12–56) are digital text. Amounts are in **thousands of Saudi Riyals**
  (`scale` 1000). Printed page references: financial position 7, income 8,
  comprehensive income 9, changes in equity 10, cash flows 11.

## Mapping notes

* Jarir owns 100% of its subsidiaries — no non-controlling interest; `net_income`
  and `total_equity` are entirely attributable to the parent's shareholders, so
  `net_income_parent` / `noncontrolling_interests` are not carried.
* `income_taxes_and_zakat` is Zakat + Income tax combined (−28,165 thousand in
  2025); also carried split as `zakat_expense` and `income_tax_expense`.
* `operating_income` is "Income from operations". `other_reserves` is the
  "Foreign exchange reserve" (translation of foreign operations).
* At 31 December 2025 the group had **no bank borrowings** (current portion
  SAR 39,696 thousand at 2024 year-end, carried as `current_debt`). IFRS 16 lease
  liabilities are mapped separately as `lease_liabilities_current` /
  `lease_liabilities_noncurrent`.
* `defined_benefit_obligation` is the non-current "End of service benefits".
  `long_term_investments` is "Financial assets at fair value through profit or
  loss". `investment_property_value` is "Investment properties".
* `depreciation_amortization` is the single "Depreciation" add-back on the
  cash-flow statement (no separate amortisation line). `capex` is "Additions to
  property and equipment" (additions to investment properties were nil in 2025).
  `interest_paid` is "Finance cost paid"; `zakat_paid` is "Zakat and income tax
  paid".

## Verification

`finengine verify jarir` → 20 pass / 0 warn / 0 fail; `finengine verify extra` →
24 pass / 0 warn / 0 fail. No unmapped labels. Bootstrap publishes 193 (Jarir) +
219 (eXtra) data points with no pipeline errors. All balance-sheet identities,
the P&L bridge, the profit-to-tax bridge, gross-profit identity and the cash-flow
reconciliation hold exactly.

Derived FY2025 — **Jarir:** gross margin 12.5%, operating margin 9.9%, net margin
9.2%, ROE ≈ 60%, ROA ≈ 24%, current ratio 1.37, free cash flow ≈ SAR 1.37bn,
payout ≈ 98%; revenue +7.0% to SAR 11.4bn, net income +7.7% to SAR 1.05bn;
debt-free at year-end, SAR 1,032m dividends. **eXtra:** revenue +9.8% to
SAR 7.45bn, gross margin 24.0%, net margin 7.7%, net income +7.8% to SAR 576m
(NCI share SAR 79m, up sharply as the financing JV scaled); operating cash flow
fell to SAR 92m as the Islamic-financing receivable book grew ≈ SAR 0.76bn;
SAR 381m dividends, SAR 238m of treasury-share buybacks.

Tests: `tests/test_retail_sector.py`.

## Unresolved fields

* **Cenomi Retail / AFG International (4240), Al Othaim Markets (4001), BinDawood
  Holding (4161), Nice One (4193), Fitaihi (4180)** — follow-up batches from the
  same Saudi Exchange company-profile FS tab (audited FS PDFs already archived
  for 4240 / 4001 / 4161).
* **Store count, selling area, e-commerce revenue share, like-for-like sales
  growth** — disclosed in Jarir's board report / investor presentation, not in
  the audited financial statements.
* **EBITDA / net debt** — not presented as statement lines; the engine leaves
  `ebitda` unpopulated because no `ebit` line is reported and it does not
  synthesise one for this issuer.
* **No engine or catalog changes in this batch.**
