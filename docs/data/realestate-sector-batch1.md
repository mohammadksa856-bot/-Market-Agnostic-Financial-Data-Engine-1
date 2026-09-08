# Saudi real estate sector — FY2025 batch 1

Batch branch: `claude/data-realestate-1`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited consolidated financial statements
(the full audited PDFs linked on the Saudi Exchange company-profile "Financial
Statements" tab, "Annual / 2025" cell). No third-party data vendors.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 4300 | Dar Al Arkan Real Estate Development Company | `data/imports/dar-al-arkan-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (Alluhaid & Alyahya / LYCA) |
| 4220 | Emaar The Economic City | `data/imports/emaar-ec-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (KPMG) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 4300 | `https://www.saudiexchange.sa/Resources/fsPdf/465_0_2026-03-11_12-11-51_En.pdf` | `545ed36b5ec79d12297a8e7a80a9e03bde8f23ffed1ef5856e480e2face238d5` | `data/raw/SA/4300/documents/545ed36b…pdf` |
| 4220 | `https://www.saudiexchange.sa/Resources/fsPdf/457_0_2026-04-08_21-34-46_En.pdf` | `9efbbc44cfffa35a7f9a83327cc138c18cb841e3a8fff27aa36a428ca6c88cd6` | `data/raw/SA/4220/documents/9efbbc44…pdf` |

Registered in `data/raw/archive-index.json` (Dar Al Arkan 2,321,143 bytes; Emaar
EC 1,670,779 bytes; both `application/pdf`).

## Company notes

Both publish in **thousands of Saudi Riyals** (`scale` 1000). The primary
statements are scanned images in both filed PDFs (transcribed from page renders);
Emaar EC's notes are digital text, Dar Al Arkan's entire PDF has no text layer.

* **Dar Al Arkan (4300):** auditor Alluhaid & Alyahya Chartered Accountants
  (LYCA); board approved / authorised for issue **3 March 2026** (Note 31).
  Consolidated with a small (SR 5.8m) non-controlling interest. **IFRS 5:** in
  FY2024 the group recorded a SAR 18,902 thousand net profit from discontinued
  operations (a disposed subsidiary, Note 29); FY2025 has none. So for FY2024
  `income_before_income_taxes_and_zakat` is not carried and the manifest relies on
  `net_income = continuing_operations_income + discontinued_operations_income`
  (flagged verification.py change); FY2025 uses the standard pre-tax − tax bridge.
  `investment_property_value` is 'Investment properties, net'; `development_property_value`
  combines the non-current and current 'Development properties' (the group's
  land-bank / project inventory); `related_party_loans` is the non-current 'Loan
  to a related party' (SAR 1.1bn to an affiliate). `long_term_debt` / `current_debt`
  are the non-current and current portions of 'Borrowings'. Dar Al Arkan pays no
  dividend. FY2025 was a heavy build year — SAR 4.10bn of net additions to
  development properties drove a SAR 3.32bn operating cash outflow, funded by a
  SAR 4.40bn increase in borrowings; net profit +40.5% to SAR 1,133.9m, EPS 1.05.
  verify 23 pass / 0 warn / 0 fail; 192 data points.

* **Emaar The Economic City (4220):** auditor KPMG; board approved / authorised
  for issue **31 March 2026** (Note 40). Consolidated group with **no
  non-controlling interest** (equity = share capital + share premium + statutory
  reserve + accumulated profit), so only `total_equity` is carried. Prepared on a
  **going-concern basis** (Note): a near-breakeven net loss of SAR 8.9m (FY2024:
  SAR 1,134.6m loss) after refinancing SAR 7.87bn of current loans into a
  SAR 4.01bn non-current facility, recognising a SAR 269.3m gain on extinguishment
  of financial liabilities (`other_nonoperating_income`) and a SAR 316.5m reversal
  of prior non-financial-asset impairments. `impairment_charges` combines the two
  P&L impairment lines so a positive figure is a net reversal (SAR +245.9m in
  FY2025). `finance_income` combines 'Financial income' and the FY2024 'Fair value
  gain on derivative financial liability'. `investment_property_value` is
  'Investment properties'; `development_property_value` and `contract_assets`
  each combine their non-current and current portions. `additional_paid_in_capital`
  is 'Share premium' (nil at FY2024, before the FY2025 rights issue that lifted
  share capital from SAR 5.23bn to SAR 8.83bn). `other_noncurrent_liabilities` is
  the non-current 'Zakat Liability' (a long-term zakat settlement). Zakat is a
  charge against a near-zero (FY2025) / negative (FY2024) pre-tax figure so the
  effective-tax bound warns in both years (expected); FY2024's net margin also
  warns. verify 17 pass / 3 warn / 0 fail; 199 data points.

## Engine change (for integration review)

`src/finengine/verification.py::ADDITIVE_IDENTITIES` — a new identity
`net income = continuing_operations_income + discontinued_operations_income`
(fires only when an issuer discloses both lines; dormant otherwise). Dar Al Arkan
FY2024 needs it. This is the same change carried on `claude/data-retail-1` and
`claude/data-materials-2`; if any of those merges first this is a no-op.
Committed separately and flagged.

## Verification

`finengine verify dar-al-arkan` → 23 / 0 / 0; `finengine verify emaar-ec` →
17 / 3 / 0 (Emaar EC's warns are the effective-tax bound in both years and the
FY2024 net-margin bound — a zakat charge / a large loss against near-zero or
negative pre-tax profit). Bootstrap publishes 192 + 199 data points with no
pipeline errors. All balance-sheet identities, the pre-tax→net bridge (Dar Al
Arkan FY2025; Emaar EC both years), the `net income = continuing + discontinued`
bridge (Dar Al Arkan FY2024) and the cash-flow reconciliation hold exactly, and
each issuer's cash-flow closing balance ties to its balance-sheet cash line.

Tests: `tests/test_realestate_sector_batch1.py`.

## Unresolved fields

* **Development-property / land-bank breakdown** (by project, by city, gross land
  area, sold vs unsold) is in the board reports, not the audited FS.
* **Occupancy, leasable area, pre-sales, contracted-not-recognised revenue** —
  not statement lines.
* **EBITDA / net debt / NAV** — not presented as statement lines.
