# Saudi health care sector — FY2025 batch 1

Batch branch: `claude/data-healthcare-1`. Source-faithful manifest transcribed by
hand from the issuer's official FY2025 audited consolidated financial statements.
No third-party data vendors. No engine or catalog changes.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 4013 | Dr. Sulaiman Al Habib Medical Services Group Company | `data/imports/hmg-2025-fy.json` | enabled, published | hmg.com IR audited consolidated FS PDF |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 4013 | `https://hmg.com/ir/en/Lists/Reports_Publications/Attachments/110/Consolidated%20Financial%20Statements%20FY%202025%20(E).pdf` | `712f37a5d8c6a2212b409d02e0634fdeec298d45452952d514144b495722c5a1` | `data/raw/SA/4013/documents/712f37a5…pdf` |

Registered in `data/raw/archive-index.json`.

* **HMG (4013):** consolidated statement of financial position printed page 7,
  statement of income page 8, cash flows page 11. Authorised for issuance by the
  Board of Directors on 26 Sha'ban 1447H / **14 February 2026** (used as
  `filed_at`). In the filed PDF the SoFP and income statement are scanned images
  (transcribed from page images); the statement of changes in equity, cash flows
  and notes are digital text. Amounts in **full Saudi Riyals** (`scale` 1).

## Mapping notes

* `income_taxes_and_zakat` is the single reported "Zakat and income tax" line.
* `long_term_debt` is the non-current "Long-term loans"; `current_debt` is the
  "Current portion of long-term loans"; IFRS 16 lease liabilities are mapped
  separately.
* `depreciation_amortization` is the single "Depreciation" add-back on the
  cash-flow statement (note 12 covers property/equipment including right-of-use
  assets; HMG discloses no separate amortisation line). `capex` is "Purchase of
  property and equipment".

## Verification

`finengine verify hmg` → 24 pass / 0 warn / 0 fail. Bootstrap publishes 187 data
points with no pipeline errors. Derived FY2025: gross margin 30.7%, operating
margin 19.1%, net margin 18.2%, return on equity 31.1%, free cash flow
+SAR 419m. FY2025 was a strong growth year — revenue +22.4% to SAR 13.7bn as
Al-Hamra, Al-Kharj and Al-Muhammadiyah hospitals ramped up (capex ≈ SAR 3.0bn).

Tests: `tests/test_healthcare_sector.py`.

## Unresolved fields

* **Mouwasat (4002), Dallah Healthcare (4004), Care / National Medical Care
  (4014), Sulaiman Al Rajhi (4017), Fakeeh Care (4285)** — follow-up batches
  (Mouwasat's IR statements are only reachable through the EurolandIR mirror /
  Tadawul, which need a per-issuer fetch pass).
* **HMG operational KPIs** (bed count, occupancy, patient volumes, hospital-level
  breakdown) are in the board report, not the audited FS.
* **EBITDA / net debt** — not presented as statement lines.
* **No engine or catalog changes in this batch.**
