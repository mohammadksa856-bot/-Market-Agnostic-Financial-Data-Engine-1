# Saudi retail sector — FY2025 batch 1

Batch branch: `claude/data-retail-1`. Source-faithful manifest transcribed by hand
from the issuer's official FY2025 audited consolidated financial statements. No
third-party data vendors. No engine or catalog changes.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 4190 | Jarir Marketing Company | `data/imports/jarir-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF |
| 4003 | United Electronics Company (eXtra) | `data/imports/extra-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |
| 4240 | AFG International Company (Cenomi Retail) | `data/imports/cenomi-retail-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (BDO, going-concern paragraph) |
| 4001 | Abdullah Al-Othaim Markets Company | `data/imports/al-othaim-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (EY) |
| 4161 | BinDawood Holding Company | `data/imports/bindawood-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (KPMG) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 4190 | `https://www.saudiexchange.sa/Resources/fsPdf/454_0_2026-03-31_11-52-35_En.pdf` | `7c1e35764a96d4d66cc748468d4608d9e4d2b13ff159e990596948c6e9ce2f36` | `data/raw/SA/4190/documents/7c1e3576…pdf` |
| 4003 | `https://www.saudiexchange.sa/Resources/fsPdf/434_0_2026-02-18_11-09-38_En.pdf` | `99fc44596d81650a9184561b09a3df278afb66803b712723c573971f6bef25ea` | `data/raw/SA/4003/documents/99fc4459…pdf` |
| 4240 | `https://www.saudiexchange.sa/Resources/fsPdf/459_0_2026-03-16_23-59-34_En.pdf` | `6e44c326312ed8400b19c82643fefbe91bbd2124963db285edfa7e0b809df04f` | `data/raw/SA/4240/documents/6e44c326…pdf` |
| 4001 | `https://www.saudiexchange.sa/Resources/fsPdf/432_0_2026-03-30_18-04-51_En.pdf` | `189024cada46cd3ade0fee976c78cde492d629e802624218e17e7144d1774ec8` | `data/raw/SA/4001/documents/189024ca…pdf` |
| 4161 | `https://www.saudiexchange.sa/Resources/fsPdf/1821_0_2026-03-18_15-07-17_En.pdf` | `30816e63a89d93f7e2f547b634ca3eea33eb36d0ea04bb7be232a081258f90ff` | `data/raw/SA/4161/documents/30816e63…pdf` |

Registered in `data/raw/archive-index.json` (Jarir 2.15 MB; eXtra 4.79 MB; Cenomi 2.92 MB; Al-Othaim 4.05 MB; BinDawood 1.99 MB; all `application/pdf`).

### How the audited FS was retrieved

The Saudi Exchange company-profile "Financial Statements" tab
(`NJstatementsTabData?statementType=6`) lists, per fiscal year, an **"Annual"**
row linking the **full audited consolidated FS** (auditor's report + notes) on
`Resources/fsPdf/<issuerCode>_0_<datetime>_En.pdf` — distinct from the "Board
Report" row (board annual report) and the Q1–Q4 rows (interim). The portlet only
renders through the site's own search flow (from a residential IP), so the tab
was opened in the browser and the `fsPdf` link scraped; the PDF itself is then a
plain static resource fetchable by URL. Issuer codes: Jarir 454, eXtra 434.

* **Al-Othaim Markets (4001):** grocery retailer, audited consolidated FS, **EY**
  auditor. Board approved 26 Ramadan 1447H / **15 March 2026** (`filed_at`).
  Auditor's report is digital text; the five primary statements (printed pages
  7–11) are scanned images; notes digital text. **Full SAR** (`scale` 1).
  `income_taxes_and_zakat` is the net zakat/tax effect: FY2025 −11.1m; FY2024 is
  "Zakat and foreign tax" −17.1m net of a +17.7m prior-year reversal, i.e. a net
  +0.6m credit (which trips the effective-tax bound as a warn — expected).
  `operating_income` is the reported "Operating profit"; `rental_income` is
  "Rental income, net" (Al-Othaim sublets space in its malls). `long_term_debt`
  is nil; `current_debt` is "Short term loans". `long_term_investments` bundles
  the three financial-asset lines (amortised cost / FVIS / FVOCI).

* **BinDawood Holding (4161):** grocery retailer (BinDawood + Danube), audited
  consolidated FS, **KPMG** auditor. Board approved 20 Ramadan 1447H /
  **9 March 2026** (`filed_at`). All five primary statements (printed pages 5–12)
  are scanned images; notes digital text. **Full SAR** (`scale` 1). FY2025 was a
  heavy acquisition year — `intangible_assets` (combined "Intangible assets and
  goodwill") stepped up SAR 336m, the group took on `long_term_debt` /
  `current_debt` ("Bank borrowings", both new) to fund it, and NCI jumped as
  subsidiaries were acquired with minority holders; net income was roughly flat
  (SAR 270m, EPS 0.24). `bonds_sukuk` is the "Compulsory convertible debentures";
  `related_party_payables` is "Due to related parties"; `other_operating_revenue`
  and `other_income` are the two separate other-income lines.

* **Cenomi Retail / AFG International (4240):** audited consolidated FS, **BDO**
  auditor. The name changed from Fawaz Abdulaziz Al Hokair & Co. to AFG
  International Company (EGM 6 January 2026); intermediate parent Al-Futtaim
  Retail Company, ultimate parent Al-Futtaim Group LLC (UAE). Board approved
  issuance 23 Ramadan 1447 / **12 March 2026** (`filed_at`). The auditor's report
  (printed pages 2–5) is a scanned image; **the five primary statements and the
  notes are digital text** (`reader: manual.text/...`). **Full SAR** (`scale` 1).
  The report carries a **material-uncertainty-related-to-going-concern**
  paragraph — net loss SAR 497m, accumulated losses SAR 2,113m, negative equity
  (total liabilities exceed total assets by SAR 1,466m). So `total_equity`,
  `equity_parent`, `noncontrolling_interests` and `retained_earnings`
  (accumulated losses) are all negative. `income_taxes_and_zakat` is the reported
  "Zakat and Income tax expense"; `income_before_income_taxes_and_zakat` is
  **not** carried — the reported "Loss before zakat and income tax" is a
  continuing-operations figure and IFRS 5 discontinued operations sit net below
  the tax line, so `continuing_operations_income` and
  `discontinued_operations_income` are carried instead and the verifier checks
  `net_income = continuing + discontinued`. The non-current-assets /
  non-current-liabilities subtotals are **not** carried because IFRS 5 disposal
  groups (`assets_held_for_sale` SAR 30.8m, `liabilities_held_for_sale`
  SAR 36.2m) sit outside them; the balance-sheet check runs on `total_assets =
  total_liabilities + total_equity`. `other_reserves` = FX translation reserve +
  fair value reserve. `intangible_assets` is the combined "Goodwill and
  intangible assets"; the SAR 120m goodwill impairment is `impairment_charges`.
  `related_party_loans` is the current "Shareholder's loan" (SAR 1,378m, nil in
  2024). `finance_costs` = "Net finance costs". No ordinary dividend.

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

`finengine verify` per issuer: jarir 20/0/0, extra 24/0/0, cenomi-retail 18/0/0,
al-othaim 23/1/0 (the one warn is FY2024's positive effective-tax ratio from the
prior-year zakat reversal), bindawood 24/0/0. No unmapped labels. Bootstrap
publishes 193 (Jarir) + 219 (eXtra) + ~150 (Cenomi) + 218 (Al-Othaim) + 211
(BinDawood) data points with no pipeline errors. All balance-sheet identities,
the P&L bridge, the profit-to-tax bridge, the continuing/discontinued split,
gross-profit identity and the cash-flow reconciliation hold exactly.

### Engine change (for integration review)

`src/finengine/verification.py` gains one `ADDITIVE_IDENTITIES` entry —
`net_income = continuing_operations_income + discontinued_operations_income` —
which fires only for issuers that disclose the IFRS 5 split (Cenomi here; also
newly covers SABIC on `main`, which discloses the split but no `income_taxes_and_zakat`
line). Committed separately and flagged for integration review. It adds passing
checks and no new failures across the 58 bundled manifests.

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

* **Nice One (4193), Fitaihi (4180), SACO (4008), Alsaif Gallery (4183),
  Thob Al Aseel (4180…)** — follow-up batches from the same Saudi Exchange
  company-profile FS tab.
* **Al-Othaim / BinDawood** — store count, selling area, like-for-like sales and
  e-commerce share are in the board report, not the audited FS. `long_term_debt`
  omitted for Al-Othaim (nil). BinDawood's acquisition-driven goodwill detail is
  in the notes, not carried as facts.
* **Cenomi (4240)** — segment revenue by concept, store count and gross leasable
  area are in the board report, not the audited FS. `income_before_income_taxes_and_zakat`
  is intentionally omitted (see the mapping note above). EBITDA / net debt are
  not statement lines.
* **Store count, selling area, e-commerce revenue share, like-for-like sales
  growth** — disclosed in Jarir's board report / investor presentation, not in
  the audited financial statements.
* **EBITDA / net debt** — not presented as statement lines; the engine leaves
  `ebitda` unpopulated because no `ebit` line is reported and it does not
  synthesise one for this issuer.
* **No engine or catalog changes in this batch.**
