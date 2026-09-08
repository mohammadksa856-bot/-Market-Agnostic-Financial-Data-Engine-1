# Saudi materials / petrochemicals sector — FY2025 batch 2

Batch branch: `claude/data-materials-2`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited consolidated financial statements
(the full audited PDFs linked on the Saudi Exchange company-profile "Financial
Statements" tab). No third-party data vendors. All PwC-audited.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 2020 | SABIC Agri-Nutrients Company | `data/imports/sabic-agri-nutrients-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |
| 2310 | Sahara International Petrochemical Company (SIPCHEM) | `data/imports/sipchem-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |
| 2350 | Saudi Kayan Petrochemical Company | `data/imports/saudi-kayan-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited FS PDF (PwC, standalone) |
| 2380 | Rabigh Refining and Petrochemical Company (Petro Rabigh) | `data/imports/petro-rabigh-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited FS PDF (PwC, standalone) |
| 2060 | National Industrialization Company (Tasnee) | `data/imports/tasnee-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 2020 | `https://www.saudiexchange.sa/Resources/fsPdf/382_0_2026-03-03_15-09-07_En.pdf` | `2697df89a62c351da1017fc8d1bd5fb876af856614cf810bce590f8380001bd1` | `data/raw/SA/2020/documents/2697df89…pdf` |
| 2310 | `https://www.saudiexchange.sa/Resources/fsPdf/411_0_2026-03-27_01-07-03_En.pdf` | `88430efa5a9b99617452aa32a899a5401f2a41339470cb3902841903998caa50` | `data/raw/SA/2310/documents/88430efa…pdf` |
| 2350 | `https://www.saudiexchange.sa/Resources/fsPdf/415_0_2026-03-03_14-16-34_En.pdf` | `c1e66e9796d90846cccb470749ede4ece0dbe2132ac13d4f63606fe66f34b3f5` | `data/raw/SA/2350/documents/c1e66e97…pdf` |
| 2380 | `https://www.saudiexchange.sa/Resources/fsPdf/418_0_2026-03-12_08-59-50_En.pdf` | `42d71071dd21a3a74edf2c68d1f73ea14e2c4e8b11a2084f0499fe8b65595b37` | `data/raw/SA/2380/documents/42d71071…pdf` |
| 2060 | `https://www.saudiexchange.sa/Resources/fsPdf/386_0_2026-03-16_13-44-52_En.pdf` | `abafcf7c3e3343110135385e834cacc0b07463011a32d9b98370cb6730cc5205` | `data/raw/SA/2060/documents/abafcf7c…pdf` |

Registered in `data/raw/archive-index.json` (SABIC AN 2,353,825 bytes; SIPCHEM
1,198,198 bytes; Saudi Kayan 2,732,911 bytes; Petro Rabigh 2,331,071 bytes;
Tasnee 1,956,761 bytes; all `application/pdf`).

* **Saudi Kayan (2350):** thousands of SAR. Board approved / authorized issue
  **24 February 2026** (7 Ramadan 1447H). **Standalone** statements — Saudi Kayan
  has no subsidiaries, so there is no non-controlling interest. The five primary
  statements (printed pages 7-11) are **scanned images** (transcribed from page
  renders at 2.6×); notes digital text. **FY2025 was a heavy loss year** — a
  gross LOSS of SAR 893.9m (cost of sales exceeded revenue) and a net loss of
  SAR 2,293.9m (2024: −1,803.7m); accumulated losses reached SAR 6,521.0m,
  equity fell to SAR 9,179.8m. `net_income`, `operating_income`, `gross_profit`,
  `comprehensive_income` and FY2025 EPS (−1.53) are all negative.
  `income_taxes_and_zakat` is the single "Zakat (expense) / benefit" line
  (SAR −8.1m against a SAR 2.29bn pre-tax loss → the effective-tax bound warns —
  expected). `other_reserves` combines the statutory reserve, "Other components
  of equity" and the actuarial reserve (the SAR 288.5m statutory reserve was
  released to accumulated losses in 2025). `long_term_debt` / `current_debt` are
  the non-current "Debt" and its current portion — the company refinanced heavily
  in 2025 (repaid SAR 7.24bn, drew SAR 7.99bn of project / Islamic financing).

* **SABIC Agri-Nutrients (2020):** thousands of SAR. Board authorised issue
  **26 February 2026** (09 Ramadan 1447H). 50.1%-owned by SABIC (2010). The
  primary statements and notes are digital text, but the SoFP, income statement
  and cash-flow statement were cross-read from page images because the
  two-column PwC layout mis-aligns on plain text extraction. `income_taxes_and_zakat`
  sums the reported "Zakat expense", "Income tax expense" and "Deferred tax
  (expense) credit" (also carried split). `additional_paid_in_capital` = "Share
  premium". `other_noncurrent_liabilities` = the non-current "Derivative
  financial instrument" (a put/call option over Al-Bayroni NCI). No bank debt —
  only IFRS 16 leases. FY2025 net income +29.8% to SAR 4.47bn (EPS 9.08).

* **SIPCHEM (2310):** thousands of SAR. Board authorised issue **16 March 2026**
  (27 Ramadan 1447H). Digital text throughout (single-column layout). **FY2025
  was a loss year** — net loss SAR 772.4m (2024: +466.2m profit) as petrochemical
  margins compressed (gross profit SAR 256.7m vs SAR 1,439.5m) plus a SAR 300m
  PP&E impairment; `net_income`, `net_income_parent`, `comprehensive_income` and
  FY2025 EPS (−1.17 diluted) are all negative and retained earnings fell to
  SAR 2.7bn. `income_taxes_and_zakat` sums "Zakat (expense) / credit", "Income
  tax expense" and "Deferred tax credit / (expense)"; in FY2024 the net figure is
  a **+SAR 18.2m credit**. `impairment_charges` = the "Impairment of property,
  plant and equipment" add-back. `current_debt` sums the current portion of
  long-term borrowings and short-term borrowings. `provisions` = "Provision for
  decommissioning costs".

* **Petro Rabigh (2380):** thousands of SAR. Board authorised issue **09 March
  2026** (20 Ramadan 1447H). **Standalone** statements (Saudi Aramco / Sumitomo
  Chemical JV; no subsidiaries → no non-controlling interest). Primary statements
  are scanned images (transcribed from page renders); notes digital text. Carries
  a **going-concern disclosure**; FY2024 comparatives **restated** per issuer
  Note 26. **Heavy loss year** — gross loss SAR 1,755.3m, net loss SAR 3,898.7m
  (2024 restated: net income +SAR 201.5m), accumulated losses SAR 9,190.7m; a
  Class B rights issue raised SAR 5,263.7m. `income_taxes_and_zakat` sums zakat
  and income tax — in FY2024 income tax is a **+SAR 203.3m credit** so the
  effective-tax bound warns against a small positive pre-tax figure (expected).
  `other_reserves` combines the statutory reserve and the ESOP reserve.
  `deferred_tax_assets` carried. Sector Energy / Oil & Gas Refining & Marketing.

* **Tasnee / National Industrialization (2060):** thousands of SAR. Board approved
  the consolidated statements **12 March 2026** (Note 49). **Consolidated with
  non-controlling interests.** Primary statements are scanned images (transcribed
  from page renders); notes digital text. FY2024 comparatives **restated** (issuer
  Notes 45-46, the 2024 SAMCO business combination). **Heavy loss year** — a
  SAR 2,108.1m impairment of non-financial assets plus a SAR 821.7m share of
  associate/JV losses drove an operating loss of SAR 3,359.3m; a SAR 2,029.0m net
  gain on debt restructuring partly offset it; net loss SAR 1,466.2m, of which
  SAR 1,765.3m is attributable to the parent (NCI took a SAR 299.1m profit).
  **IFRS 5:** Tasnee has a discontinued operation and classifies a disposal group
  (titanium-dioxide / Cristal-related, Note 46) as held for sale. As with Cenomi
  Retail in the retail batch, the manifest carries `continuing_operations_income`
  (−SAR 1,491.3m) and `discontinued_operations_income` (+SAR 25.2m) and **drops**
  `income_before_income_taxes_and_zakat` (the reported "loss before zakat" is a
  continuing-operations figure); it carries `assets_held_for_sale` (SAR 1,102.3m)
  and `liabilities_held_for_sale` (SAR 388.7m) and **drops** the non-current
  subtotals, so the balance-sheet check runs on `total_assets = total_liabilities
  + total_equity` (SAR 20,819.2m = 10,663.0m + 10,156.2m). `income_taxes_and_zakat`
  is the continuing-operations "Zakat and income tax". `operating_income` is the
  reported "Operating loss" (Tasnee presents impairments and the share of
  associates above operating loss). `other_nonoperating_income` = the one-off
  "Gain on debt restructuring, net". The cash-flow closing balance (SAR 2,144.5m)
  differs from the SoFP "Cash and bank balances" (SAR 2,018.2m) because
  SAR 126.3m of cash sits inside the held-for-sale disposal group — the
  cash-to-balance-sheet cross-check warns (expected). Sector Materials /
  Diversified Chemicals.

## Engine change (for integration review)

`src/finengine/verification.py::ADDITIVE_IDENTITIES` — a new identity
`net income = continuing_operations_income + discontinued_operations_income`
(fires only when an issuer discloses both lines; dormant otherwise). IFRS 5
presents the discontinued result net, below the continuing-operations line, which
breaks the standard `pre-tax income − tax = net income` bridge for issuers with a
disposal (here Tasnee; Cenomi Retail in the retail batch). This is the same
change carried on `claude/data-retail-1`; if that branch merges first this is a
no-op. Committed separately and flagged.

`src/finengine/bootstrap.py::_manifest_company` — when a legacy manifest with no
`company_id`/`cik` header (e.g. `aramco-2020-fy-historical.json`) matches more
than one registry company by filename, a distinctive **name-token** match (e.g.
"aramco") now wins over a bare **symbol substring** match (an issuer whose ticker
happens to equal a year in the filename — here SABIC Agri-Nutrients, ticker 2020).
Without this, adding ticker 2020 to the registry makes bootstrap fail to resolve
the Aramco 2020 historical manifest. Committed separately and flagged.

## Verification

`finengine verify sabic-agri-nutrients` → 24 pass / 0 warn / 0 fail;
`finengine verify sipchem` → 22 pass / 2 warn / 0 fail; `finengine verify
saudi-kayan` → 19 pass / 1 warn / 0 fail; `finengine verify petro-rabigh` →
19 pass / 1 warn / 0 fail; `finengine verify tasnee` → 15 pass / 3 warn / 0 fail.
The effective-tax warns are the plausibility bound firing on a zakat charge/credit
that is not a function of pre-tax profit (SIPCHEM's FY2024 net zakat credit and
its FY2025 charge against a loss; Saudi Kayan's small FY2025 zakat charge against
a SAR 2.29bn loss; Petro Rabigh's FY2024 income-tax credit against a small
positive pre-tax figure). Tasnee's warns are (a) two cash-to-balance-sheet
cross-checks — the cash-flow "cash and cash equivalents" includes disposal-group
cash / excludes >3-month deposits, so it differs from the SoFP "Cash and bank
balances" line — and (b) the FY2025 net-margin bound (a SAR 1.47bn loss on
SAR 2.49bn revenue). Bootstrap publishes 215 (SABIC AN) + 237 (SIPCHEM) +
194 (Saudi Kayan) + 199 (Petro Rabigh) + 208 (Tasnee) data points with no
pipeline errors. All balance-sheet identities (Tasnee on `total_assets =
total_liabilities + total_equity` per IFRS 5), the `net income = continuing +
discontinued` bridge, the owners/NCI split, the gross-profit identity and the
cash-flow reconciliation hold exactly.

Tests: `tests/test_materials_sector_batch2.py`.

## Unresolved fields

* **Tasnee FY2024 cash reconciliation** — the FY2024 comparative SoFP "Cash and
  bank balances" (SAR 4,089.7m) exceeds the FY2024 cash-flow closing balance
  (SAR 3,787.4m) by SAR 302.2m; the issuer does not break the difference out on
  the face of the statements (>3-month deposits and/or overdrafts). Carried as
  reported; the cross-check warns.
* **Held-for-sale disposal-group line items** (Tasnee, Note 46) — only the
  aggregate `assets_held_for_sale` / `liabilities_held_for_sale` are carried, not
  the underlying asset/liability composition.
* **Product / plant-level volumes, capacity utilisation and realised prices** are
  in the board reports, not the audited FS.
* **EBITDA / net debt** — not presented as statement lines.
