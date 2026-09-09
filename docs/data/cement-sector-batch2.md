# Saudi cement sector — FY2025 batch 2

Batch branch: `claude/data-cement-2`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited financial statements (the full
audited PDFs linked on the Saudi Exchange company-profile "Financial Statements"
tab, "Annual / 2025" cell). No third-party data vendors.

One flagged engine change: an IFRS 5 `net income = continuing + discontinued
operations` identity in `verification.py` (Arabian Cement discloses the split).

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 3010 | Arabian Cement Company | `data/imports/arabian-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (EY) |
| 3040 | Qassim Cement Company | `data/imports/qassim-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (BDO) |
| 3060 | Yanbu Cement Company | `data/imports/yanbu-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (BDO) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 3010 | `https://www.saudiexchange.sa/Resources/fsPdf/423_0_2026-02-23_11-20-33_En.pdf` | `95310e37c7e8adf82177a557e2949da2438f240300def0cbed6b61a0be75b261` | `data/raw/SA/3010/documents/95310e37…pdf` |
| 3040 | `https://www.saudiexchange.sa/Resources/fsPdf/426_0_2026-02-25_16-50-21_En.pdf` | `17ca838773025846d9b502f6f78c2bfbabcf18463c9399c37d5eea62b8308aa1` | `data/raw/SA/3040/documents/17ca8387…pdf` |
| 3060 | `https://www.saudiexchange.sa/Resources/fsPdf/428_0_2026-03-11_16-20-46_En.pdf` | `7aa24367df35cb17de610dc6b94d1d0be084c710ad44eb5a1f6cb3cf607343b9` | `data/raw/SA/3060/documents/7aa24367…pdf` |

Registered in `data/raw/archive-index.json` (Arabian Cement 709,323 bytes;
Qassim 1,485,938 bytes; Yanbu 2,090,190 bytes; all `application/pdf`).

## Company notes

* **Arabian Cement (3010):** auditor Ernst & Young Professional Services;
  Board approved 15 February 2026 (Note 39). SAR thousands. **The filed PDF is
  digital text** (`reader: manual.text`), only the auditor signature page is a
  scan. Consolidated with a non-controlling interest (its Jordanian cement
  subsidiary). **IFRS 5 — discontinued operations:** a separate
  "Profit from discontinuing operations" line (SAR 6.8m FY2025 / 7.8m FY2024)
  sits below the continuing-operations result; the reported pre-tax profit and
  zakat/income-tax charge are continuing-only, so `income_before_income_taxes_and_zakat`
  is dropped and `net_income = continuing_operations_income + discontinued_operations_income`
  is checked instead (needs the flagged `verification.py` change). A
  "Non-current asset held for sale" of SAR 43.4m at year-end (nil FY2024) is
  presented *inside* total current assets with no matching liabilities-held-for-sale,
  so `assets_held_for_sale` is carried and the current/total-assets identities
  hold with it included. The statutory and general reserves (SAR 595m) were
  released to retained earnings in FY2025 under the new Companies Law.
  `income_taxes_and_zakat` = Zakat + Income Tax; `other_reserves` bundles the
  two remaining negative reserve balances; `provisions` = rehabilitation
  (quarry) provision. Revenue +23.8% to SAR 1.06bn, net profit SAR 167.6m,
  diluted EPS 1.65. verify 22 pass / 0 warn / 0 fail; 228 data points.

* **Qassim Cement (3040):** auditor BDO Dr. Mohamed Al-Amri & Co.; Board
  approved 16 February 2026 (Note 41). **Full Saudi Riyals** (`scale` 1).
  Primary statements scanned (`manual.vision`), notes scanned with an OCR text
  layer. Consolidated; **no non-controlling interest** (`total_equity` only).
  **FY2024 comparatives RESTATED (Note 37)** — the IFRS 3 purchase price
  allocation for Hail Cement Company (acquired 2024) was finalised in H1 2025,
  restating the comparatives retrospectively (PP&E +SAR 77.3m among others).
  `goodwill` is carried (Hail Cement acquisition); `long_term_investments`
  combines the non-current FVTPL investments and the amortized-cost investments;
  `impairment_charges` is 'Reversal / (allowance) for expected credit loss'
  (a reversal in FY2025); `other_nonoperating_income` bundles unrealised +
  realised FVTPL gains; `current_debt` is 'Short term borrowing' (nil FY2024);
  `other_current_liabilities` = dividends payable + other provision. Softer
  year — cost of revenue outran revenue so gross margin fell from 33.6% to
  23.0% and net profit slipped 9.6% to SAR 259.9m, EPS 2.37. verify 20 pass /
  0 warn / 0 fail; 208 data points.

* **Yanbu Cement (3060):** auditor BDO Dr. Mohamed Al-Amri & Co.; Board
  approved 3 March 2026 (Note 41). **Full Saudi Riyals** (`scale` 1). Primary
  statements scanned (`manual.vision`), notes digital text. Consolidated;
  **no non-controlling interest** (`total_equity` only). **FY2024 comparatives
  reclassified (Note 40)** — certain items (intangible assets and related
  cash-flow lines) reclassified retrospectively, no equity impact.
  `share_of_profit_associates` is a small loss both years; `other_nonoperating_expense`
  is the derivative-instrument fair-value loss; `other_current_assets` is the
  'Financial derivative' asset; `other_reserves` is just the statutory reserve;
  `current_debt` combines the current bank-borrowing portion and short-term
  financing; `debt_repaid` combines bank-borrowing and short-term-financing
  repayments; `interest_paid` is 'Finance cost paid'. **Weaker year** — a jump
  in selling/distribution expenses and cost of revenue took operating profit
  from SAR 179.7m to SAR 128.4m and net profit from SAR 157.1m to SAR 104.5m,
  EPS 0.66 (FY2024 1.00). verify 20 pass / 0 warn / 0 fail; 217 data points.

## Verification

`finengine verify arabian-cement` → 22 / 0 / 0; `finengine verify
qassim-cement` → 20 / 0 / 0; `finengine verify yanbu-cement` → 20 / 0 / 0.
Bootstrap publishes 228 + 208 + 217 data points with no pipeline errors. All
balance-sheet identities, the pre-tax→net (or IFRS 5 continuing+discontinued)
bridge and the cash-flow reconciliation hold exactly, and each issuer's
cash-flow closing balance ties to its balance-sheet cash line.

Tests: `tests/test_cement_sector_batch2.py`.

## Engine change (for integration review)

`src/finengine/verification.py` — added a `net income = continuing_operations_income
+ discontinued_operations_income` entry to `ADDITIVE_IDENTITIES`, dormant unless
an issuer discloses both lines (Arabian Cement here; also covers earlier
retail/materials/real-estate/food branches). Committed separately, titled
"For integration review". Codex dedupes on merge if an earlier branch merged first.

## Unresolved fields

* **Clinker / cement production, dispatch volumes, capacity utilisation,
  export share, average selling price** are in the board reports, not the
  audited FS.
* **Qassim FY2024 / Yanbu FY2024 restatement detail** — only the restated
  comparatives are carried; the pre-restatement figures are in Notes 37 / 40.
* **Arabian Cement discontinued operation identity** — the disposal group is
  described in Note 16; only the net profit/OCI split is carried.
* **EBITDA / net debt** — not presented as statement lines.
