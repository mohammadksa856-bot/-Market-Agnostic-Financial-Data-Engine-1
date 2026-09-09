# Saudi cement sector — FY2025 batch 3

Batch branch: `claude/data-cement-3`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited financial statements (the full
audited PDFs linked on the Saudi Exchange company-profile "Financial Statements"
tab, "Annual / 2025" cell). No third-party data vendors. No engine or catalog
changes in this batch.

This completes the listed Saudi cement producers (batches 1-3 cover Saudi
Cement, Southern Province, Yamama, Arabian Cement, Qassim, Yanbu, Najran, City
Cement, Umm Al-Qura).

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 3002 | Najran Cement Company | `data/imports/najran-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (BDO) |
| 3003 | City Cement Company | `data/imports/city-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (BDO) |
| 3005 | Umm Al-Qura Cement Company | `data/imports/umm-al-qura-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited standalone FS PDF (BDO) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 3002 | `https://www.saudiexchange.sa/Resources/fsPdf/420_0_2026-04-06_18-38-30_En.pdf` | `759a24ad88cd92b8c6c5c0d59299024ff321a3cd296787ba39bd7443819b9167` | `data/raw/SA/3002/documents/759a24ad…pdf` |
| 3003 | `https://www.saudiexchange.sa/Resources/fsPdf/421_0_2026-03-24_15-45-22_En.pdf` | `6958b51f874c338076467a8c7bac0e93f7a3aa13b944206be95bc6f3025127cd` | `data/raw/SA/3003/documents/6958b51f…pdf` |
| 3005 | `https://www.saudiexchange.sa/Resources/fsPdf/602_0_2026-03-17_15-01-01_En.pdf` | `c1c7da561e2bcdec8cc3e8a8a116389c7e0799a58b3ca5edcfd74c9fa0848c67` | `data/raw/SA/3005/documents/c1c7da56…pdf` |

Registered in `data/raw/archive-index.json` (Najran 3,121,938 bytes; City Cement
7,797,182 bytes; Umm Al-Qura 3,568,894 bytes; all `application/pdf`).

## Company notes

All three are audited by BDO Dr. Mohamed Al-Amri & Co., all have scanned primary
statements (`manual.vision`), and none has a non-controlling interest or a
discontinued operation — the standard pre-tax − zakat bridge applies.

* **Najran Cement (3002):** Board authorized 29 March 2026 (Note 33). SAR
  thousands. Consolidated; equity is just share capital + treasury shares +
  retained earnings (the statutory reserve was transferred to retained earnings
  in FY2024 under the new Companies Law). `treasury_shares` is nil at end-2024;
  SAR 43.8m of shares were bought back during FY2025 (also the
  `treasury_share_purchases` financing outflow). `noncurrent_assets` is a single
  PP&E line. `current_debt` combines the current portion of long-term borrowing
  and short-term financing; `debt_repaid` / `debt_issued` carry the reported
  net movements. **Weaker year** — cost of revenue rose while revenue fell, so
  gross margin went 27.2% → 21.3% and net profit SAR 68.4m → SAR 36.7m, EPS 0.22
  (FY2024 0.40). verify 20 pass / 0 warn / 0 fail; 198 data points.

* **City Cement (3003):** Board approved 16 March 2026 (Note 35). Full Saudi
  Riyals. Consolidated (with an equity-accounted joint venture); no NCI. The
  scanned pages have their label and value columns offset — figures were aligned
  by note number and by checking each subtotal. **The Group has no bank debt** —
  the only borrowings are IFRS 16 lease liabilities. `investments_joint_ventures`
  = 'Investments in Joint Venture'; `share_of_profit_associates` = 'Group's
  share in losses from joint venture'; `short_term_investments` combines the
  current FVTPL investments (SAR 394.6m) and the 'Short term time deposit'
  (SAR 146.0m). **The cash-flow closing cash (SAR 113.8m) is SAR 100m higher
  than the balance-sheet cash line (SAR 13.8m)** because the cash-flow definition
  includes short-term deposits maturing within three months; the two agree at
  end-2024. This makes the cash-flow-to-balance-sheet cross-check warn for FY2025
  only (expected). **Softer year** — gross margin 36.2% → 31.5%, net profit
  SAR 144.1m → SAR 128.9m, EPS 0.92 (FY2024 1.03). verify 19 pass / 1 warn /
  0 fail; 192 data points.

* **Umm Al-Qura Cement (3005):** Board approved 12 March 2026 (Note 27); auditor
  report dated 15 March 2026. Full Saudi Riyals. **Standalone** (non-consolidated)
  — the Company has no subsidiaries. Both the auditor's report and the primary
  statements are scanned. `accounts_receivable` is the combined 'Accounts
  receivable, prepaid expenses and other receivables' line; `long_term_investments`
  = FVOCI investments; `other_reserves` = the FVOCI revaluation reserve. The
  only debt is the Saudi Industrial Development Fund loan, and the entire
  remaining balance (SAR 200.1m) is classified as current at 31 December 2025,
  so no non-current debt fact is carried for FY2025. `other_nonoperating_income`
  is the small net '(Loss) / Profits from foreign currency exchange' P&L line.
  **Softer year** — gross margin 31.2% → 27.6%, net profit SAR 47.7m → SAR
  45.8m, EPS 0.83 (FY2024 0.87). verify 20 pass / 0 warn / 0 fail; 191 data
  points.

## Verification

`finengine verify najran-cement` → 20 / 0 / 0; `finengine verify city-cement`
→ 19 / 1 / 0 (the FY2025 cash-flow cash / balance-sheet cash cross-check warns
because the cash-flow definition includes short-term deposits); `finengine
verify umm-al-qura-cement` → 20 / 0 / 0. Bootstrap publishes 198 + 192 + 191
data points with no pipeline errors. All balance-sheet identities, the
pre-tax→net bridge and the cash-flow reconciliation hold exactly.

Tests: `tests/test_cement_sector_batch3.py`.

## Unresolved fields

* **Clinker / cement production, dispatch volumes, capacity utilisation,
  export share, average selling price** are in the board reports, not the
  audited FS.
* **City Cement — clinker (work-in-process) inventory quantity** is estimated
  by stockpile measurement (a key audit matter); only the carrying value is in
  the FS.
* **Najran / Umm Al-Qura short-term-loan and SIDF-loan movement detail** — only
  the net cash-flow figures and year-end balances are carried.
* **EBITDA / net debt** — not presented as statement lines.
* **No engine or catalog changes in this batch.**
