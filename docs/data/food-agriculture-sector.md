# Saudi food & agriculture sector — FY2025 batch 1

Batch branch: `claude/data-food-1`. Source-faithful manifest transcribed by hand
from the issuer's official FY2025 audited consolidated financial statements. No
third-party data vendors. No engine or catalog changes.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 2280 | Almarai Company | `data/imports/almarai-2025-fy.json` | enabled, published | Almarai Integrated Annual Report 2025 (KPMG-audited consolidated FS) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 2280 | `https://annualreport.almarai.com/downloads/pdf/en/full-report.pdf` | `08ec6e6c6182287604d0b8ead05fd557717c9a3adc38a07484c76db87442e297` | `data/raw/SA/2280/documents/08ec6e6c…pdf` |

Registered in `data/raw/archive-index.json`.

* **Almarai (2280):** consolidated statement of financial position, profit or
  loss and cash flows read from the digital-text Integrated Annual Report 2025
  and cross-checked against the report's own per-statement PDFs. Auditor KPMG
  Professional Services. Approved by the Board of Directors on 29 Rajab 1447H /
  **18 January 2026** (note 43; used as `filed_at`).

## Mapping notes

* `income_taxes_and_zakat` combines the separately presented Zakat (SAR
  −86,831k) and Income Tax (SAR −52,190k) lines so the pre-tax → net bridge
  holds. `finance_costs` is the reported "Finance Cost, net".
* `long_term_debt` is the non-current "Loans and Borrowings"; `current_debt`
  sums "Bank Overdrafts" and current "Loans and Borrowings"; IFRS 16 lease
  liabilities are mapped separately.
* **Biological assets** (dairy herd, poultry, crops — SAR 1,810,686k non-current
  + 160,737k current at 2025 year-end) and long-term prepayments have no
  dedicated catalog field and are captured only within the current / non-current
  asset subtotals, which are mapped. `depreciation_amortization` is the sum of
  all cash-flow depreciation/amortisation add-backs (PP&E + right-of-use +
  intangibles + biological assets + long-term prepayments); `capex` sums
  additions to PP&E, intangible assets and biological assets.

## Verification

`finengine verify almarai` → 24 pass / 0 warn / 0 fail. Bootstrap publishes 195
data points with no pipeline errors. Derived FY2025: gross margin 31.2%,
operating margin 13.9%, net margin 11.1%, return on equity 12.5%, free cash flow
+SAR 36m (capex ≈ SAR 5.4bn against operating cash flow of SAR 5.5bn — a heavy
capacity-investment year).

Tests: `tests/test_food_agriculture_sector.py`.

## Unresolved fields

* **Savola Group (2050), Saudia Dairy & Foodstuff / SADAFCO (2270), NADEC
  (6010), Halwani Bros (6001), Tabuk Agricultural (6040)** and the rest of the
  sector — follow-up batches.
* **Almarai segment reporting** (Dairy & Juice / Bakery / Poultry / Other),
  biological-asset roll-forwards, and the note-level debt maturity profile were
  not extracted as structured facts this batch.
* **EBITDA / net debt / net-debt-to-EBITDA** — not presented as statement lines;
  engine does not derive EBITDA without a reported `ebit`.
* **No engine or catalog changes in this batch.**
