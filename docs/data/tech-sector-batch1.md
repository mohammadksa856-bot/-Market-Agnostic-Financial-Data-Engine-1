# Saudi technology sector — FY2025 batch 1

Batch branch: `claude/data-tech-1`. Source-faithful manifests transcribed by hand
from each issuer's official FY2025 audited financial statements (the full audited
PDFs linked on the Saudi Exchange company-profile "Financial Statements" tab,
"Annual / 2025" cell). No third-party data vendors. No engine or catalog changes
in this batch.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 7203 | Elm Company | `data/imports/elm-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (BDO Dr. Mohamed Al-Amri & Co.) |
| 7202 | Arabian Internet and Communication Services Company (Solutions by stc) | `data/imports/stc-solutions-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (Deloitte and Touche & Co.) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 7203 | `https://www.saudiexchange.sa/Resources/fsPdf/2784_0_2026-03-05_17-23-45_En.pdf` | `363810a1a59f0d824d5c053286e35900c0bd4092b22807a125003cddb0c11600` | `data/raw/SA/7203/documents/363810a1…pdf` |
| 7202 | `https://www.saudiexchange.sa/Resources/fsPdf/2302_0_2026-02-23_17-47-49_En.pdf` | `287f14a69420bbc31ddb70ab916b1aef480ffe14ac951fc1622d7a0e9ab2e2ca` | `data/raw/SA/7202/documents/287f14a6…pdf` |

Registered in `data/raw/archive-index.json` (Elm 1,982,951 bytes; stc Solutions
3,370,929 bytes; both `application/pdf`).

## Company notes

Both are **consolidated** groups with a small non-controlling interest, both
audited unqualified, and neither has discontinued operations — the standard
pre-tax − zakat bridge applies (`income_before_income_taxes_and_zakat` is the
reported "profit/net profit before zakat"). In both filed PDFs the primary
statements are scanned images (transcribed from page renders at 2.6x); stc
Solutions' cash-flow statement and both issuers' notes are digital text.

* **Elm (7203):** auditor BDO Dr. Mohamed Al-Amri & Co.; Board approved the
  statements on Ramadan 9, 1447H / **26 February 2026** (Note 43). Full Saudi
  Riyals (`scale` 1). `impairment_charges` combines the two P&L lines "Expected
  credit losses" and "Impairment of non-current assets". `depreciation_amortization`
  is the P&L opex line "Depreciation and amortization". `selling_and_distribution_expense`
  is "Selling and marketing". `finance_income` is "Income from murabaha deposits";
  `share_of_profit_associates` (a loss both years) is "Share in results from
  investments in associates and joint ventures"; `other_nonoperating_income` is
  "Change in fair value of financial assets through profit or loss, net";
  `other_income` is "Other income, net". On the balance sheet `construction_in_progress`
  is "Capital work in progress", `short_term_investments` is "Murabaha deposits"
  (> 3 months), `other_noncurrent_assets` and `other_current_assets` fold in the
  non-current / current portions of "Finance lease receivables" (plus long-term
  prepaid expenses), and `treasury_shares` carries the negative treasury line.
  **Note 40 — acquisition of Thiqah Business Services Company:** on 21 April 2025
  Elm bought 100% of Thiqah from the Public Investment Fund for an adjusted
  SAR 3,385.9m; as a business combination under common control the SAR 3,121.8m
  excess of consideration over net assets acquired was charged straight to
  retained earnings (statement of changes in equity), which is why retained
  earnings fell despite a record profit. The deal drove the SAR −3,141.1m
  "Payment for acquisition of subsidiary" investing outflow (`acquisitions`) and
  the SAR 1,900.0m new long-term borrowing (`debt_issued`; `long_term_debt` /
  `current_debt` were both nil at end-2024, so no FY2024 fact is carried).
  FY2025: revenue +27.8% to SAR 9.46bn, net profit +14.4% to SAR 2.09bn,
  diluted EPS 26.80. verify 24 pass / 0 warn / 0 fail; 223 data points.

* **stc Solutions / Arabian Internet and Communication Services Company (7202):**
  auditor Deloitte and Touche & Co.; Board approved the statements at its meeting
  on 27 Shaaban 1447H / **15 February 2026** (Note 45). SAR thousands (`scale`
  1000). The P&L shows only two operating-expense lines below gross profit —
  `general_and_administrative_expense` and `selling_and_distribution_expense`
  (there is no depreciation line on the face), `share_of_profit_associates` is
  "Share in net results from equity accounted investees", and
  `other_nonoperating_expense` is "Other expenses, net". `contract_liabilities`
  combines the two reported current-liability lines "Deferred revenue" and
  "Contract liabilities" (both IFRS 15 contract liabilities). `lease_liabilities_noncurrent`
  is the reported "Lease and other liabilities" line (Note 28, predominantly
  leases). `depreciation_amortization` combines the two cash-flow add-backs
  "Depreciation and amortization" and "Depreciation - right of use assets".
  `short_term_investments` is "Short term murabaha". **Operating cash flow was a
  net outflow of SAR 100.7m in FY2025** (FY2024 inflow SAR 1.51bn) driven by a
  large working-capital build — trade receivables +SAR 824m and contract assets
  +SAR 734m — even though net profit only slipped 5.6% to SAR 1.51bn; the
  SAR 2.21bn unwind of short-term murabaha funded a SAR 1.19bn dividend.
  Diluted EPS 12.52. verify 24 pass / 0 warn / 0 fail; 227 data points.

## Verification

`finengine verify elm` → 24 / 0 / 0; `finengine verify stc-solutions` →
24 / 0 / 0. Bootstrap publishes 223 + 227 data points with no pipeline errors.
All balance-sheet identities, the pre-tax→net bridge, the net-income →
owners + NCI split and the cash-flow reconciliation hold exactly, and each
issuer's cash-flow closing balance ties to its balance-sheet cash line.

Tests: `tests/test_tech_sector_batch1.py`.

## Unresolved fields

* **Operating KPIs** — Elm's digital-business / BPO / professional-services
  transaction and platform metrics, and stc Solutions' contract backlog / order
  intake — are in the board reports, not the audited FS. Only the segment
  revenue/asset/liability splits in the FS notes are available.
* **Thiqah acquisition-date balance sheet** (Elm Note 40) — carried only in
  narrative; the acquired assets/liabilities table is not ingested as facts.
* **EBITDA / net debt** — not presented as statement lines.
* **No engine or catalog changes in this batch.**
