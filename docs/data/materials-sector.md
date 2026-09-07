# Saudi materials / mining / petrochemicals sector — FY2025 batch 1

Batch branch: `claude/data-materials-1`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited financial statements. No
third-party data vendors. No engine or catalog changes — every manifest maps to
existing catalog fields.

SABIC (2010) is already on `main` (Codex workstream) and is not part of this
batch.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 2290 | Yanbu National Petrochemical Company (YANSAB) | `data/imports/yansab-2025-fy.json` | enabled, published | yansab.com.sa IR FY2025 FS PDF |
| 2330 | Advanced Petrochemical Company | `data/imports/advanced-petrochemical-2025-fy.json` | enabled, published | ir.advancedpetrochem.com FY2025 consolidated FS PDF |
| 1211 | Saudi Arabian Mining Company (Ma'aden) | `data/imports/maaden-2025-fy.json` | enabled, published | Ma'aden Integrated Report 2025 (audited consolidated FS) |

## Sources and archives

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 2290 | `https://www.yansab.com.sa/en/Images/EN%20YANSAB%20FS%202025_tcm1047-49412.pdf` | `02f1136204a74489cad9f493cc635f585bffa5d47f95a75bf82fe8d6db3cf07b` | `data/raw/SA/2290/documents/02f11362…pdf` |
| 2330 | `https://ir.advancedpetrochem.com/media/wclmsyu0/fs_q4-2025_advanced_en.pdf` | `e1a18376cf05fde2f05c470468c5030c20d78504ba70c02665783857b6cc94e1` | `data/raw/SA/2330/documents/e1a18376…pdf` |
| 1211 | `https://axvpvthrjz64.compat.objectstorage.me-jeddah-1.oraclecloud.com/maaden-website-assets/reports/annual-reports/maaden-ar-updated-ver---mar-26-eng-ver_compressed.pdf` | `dae44e050e70e412049516a4caea688f9ff0cd918cab44b393ee86ecaf4b02a6` | `data/raw/SA/1211/documents/dae44e05…pdf` |

All three registered in `data/raw/archive-index.json`.

* **Ma'aden (1211):** consolidated statement of financial position printed
  page 127, profit or loss / OCI page 126, cash flows page 129 (within the
  Integrated Report 2025; the Tadawul earnings announcement is a summary only,
  not the audited FS). Auditor Deloitte & Touche & Co. (Mazen A. Al-Omari,
  licence 480), signed 16 Ramadan 1447H / **5 March 2026** (used as `filed_at`).
  Amounts are in **full Saudi Riyals** (`scale` 1); the convenience USD column
  at SAR 3.75 is ignored. The primary-statement pages are scanned images
  (transcribed from page images); the notes are digital text and were used to
  cross-check.

* **YANSAB (2290):** SoFP page 7, statement of income page 8, statement of cash
  flows page 11 (printed page numbers). Standalone (no subsidiaries). Auditor
  PwC (licence 471), signed 10 February 2026; **approved by the Board of
  Directors on 20 Sha'ban 1447H / 8 February 2026** (used as `filed_at`).
  Text-extractable PDF.
* **Advanced Petrochemical (2330):** SoFP page 7, profit or loss / OCI pages
  5-6, cash flows page 9. In the filed PDF the SoFP and P&L pages are **scanned
  images** (transcribed from page images); the cash-flow statement and notes
  are digital text. **Approved for issuance by the Board of Directors as of
  23 February 2026.**

## Mapping notes

* **YANSAB** carries no bank debt — only IFRS 16 lease liabilities, mapped as
  `lease_liabilities_noncurrent` / `lease_liabilities_current`. `other_reserves`
  is the "Actuarial reserve". `selling_and_distribution_expense` and
  `general_and_administrative_expense` are mapped as the two separately
  presented lines. `operating_income` is "INCOME FROM OPERATIONS". No NCI.
* **Advanced Petrochemical** `long_term_debt` sums the non-current SIDF loan,
  Islamic loan facilities and Murabaha loans; `current_debt` sums their current
  portions; IFRS 16 leases mapped separately. `income_taxes_and_zakat` is the
  total "Zakat and income tax (expense) income" line (zakat + income tax +
  deferred tax). **FY2024 was a loss year** — driven by a SAR 133.4m share of
  associate loss and a SAR 212.1m impairment of that associate investment (both
  mapped for FY2024 as `share_of_profit_associates` and `impairment_charges`).
* All three: `depreciation_amortization` is the cash-flow depreciation add-back
  (none presents a separate D&A line in the income statement); `capex` is the
  "Purchase of / Additions to property, plant and equipment" line (for Ma'aden
  it also includes additions to mine properties and capital work-in-progress).
* **Ma'aden** presents "Profit before zakat, income tax and severance fees" and
  then three separate charges below it: income tax (a **credit** of SAR 129.1m
  in 2025), zakat expense (SAR −373.2m) and severance fees (SAR −1,258.0m, a
  Saudi mining-sector royalty-type levy). `income_taxes_and_zakat` is mapped as
  the sum of all three (SAR −1,502.1m for 2025) so the pre-tax → net-income
  identity holds. `selling_and_distribution_expense` = "Selling, marketing and
  logistics expenses"; `exploration_expense` = "Exploration and technical
  services expenses". `long_term_debt` / `current_debt` are the non-current and
  current "Borrowings"; IFRS 16 leases are mapped separately. Ma'aden paid no
  ordinary dividend in 2025 (only a SAR 716.25m distribution to NCI), so
  `dividends_paid` is omitted.

## Verification

`finengine verify yansab` → 20 pass / 0 warn / 0 fail.
`finengine verify advanced-petrochemical` → 23 pass / 1 warn / 0 fail (the warn
is the FY2024 effective-tax ratio, which is out of band only because FY2024 was
a loss year).

`finengine verify maaden` → 24 pass / 0 warn / 0 fail.

Bootstrap into a throwaway snapshot publishes 165 (YANSAB), 187 (Advanced) and
194 (Ma'aden) data points with no pipeline errors. Derived FY2025 checks:

| | YANSAB | Advanced Petrochemical | Ma'aden |
|---|---|---|---|
| gross margin | 11.5% | 19.1% | 38.3% |
| operating margin | 1.1% | 13.6% | 26.8% |
| net margin | 1.4% | 6.6% | 22.1% |
| return on equity | 0.7% | 6.9% | 13.3% |
| free cash flow | +SAR 0.84bn | −SAR 1.06bn | +SAR 4.02bn |

YANSAB's thin FY2025 margins reflect the weak petrochemical price cycle;
Advanced's negative FCF is a heavy capacity-expansion year (capex ≈ SAR 1.6bn
on the new propane dehydrogenation / polypropylene project). Ma'aden's FY2025
was a record year — revenue +19% to SAR 38.6bn, net profit +156% — driven by
record phosphate output, higher gold/aluminium/phosphate prices and the first
full-year equity-accounted contribution from Alba (including a one-off bargain-
purchase gain).

Tests: `tests/test_materials_sector.py`.

## Unresolved fields

* **SABIC Agri-Nutrients (2020), Saudi Kayan (2350), Petro Rabigh (2380),
  Sipchem/Sahara (2310), Tasnee (2060)** — not in this batch. SABIC
  Agri-Nutrients' IR "Financial Statements" page only publishes standalone FS
  through Q3 2025 (the FY2025 audited FS appears only inside the 14MB board
  annual report, above WebFetch's 10MB limit); the others need a follow-up pass.
* **Ma'aden segment reporting** (phosphate / aluminium / base metals & new
  minerals), production and realised-price disclosures, the decommissioning
  provision detail, and the Alba purchase-price allocation live in the notes /
  strategic report and were not extracted as structured facts this batch.
* **EBITDA / net debt / net-debt-to-EBITDA** — neither issuer presents EBITDA or
  a net-debt reconciliation as a statement line; the engine does not derive
  EBITDA without a reported `ebit`. Platform-side wiring if a deterministic
  definition is agreed.
* **Segment / product-line and volume disclosures** (production tonnage, product
  mix) live in the notes / board report and were not extracted this batch.
* **No engine or catalog changes in this batch.**
