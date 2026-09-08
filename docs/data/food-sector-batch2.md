# Saudi food & agriculture sector — FY2025 batch 2

Batch branch: `claude/data-food-2`. Source-faithful manifests transcribed by hand
from each issuer's official FY2025 audited consolidated financial statements (the
full audited PDFs linked on the Saudi Exchange company-profile "Financial
Statements" tab, "Annual / 2025" cell). No third-party data vendors. (Almarai
2280 was covered in food batch 1.)

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 2050 | Savola Group Company | `data/imports/savola-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (Deloitte) |
| 2270 | Saudia Dairy and Foodstuff Company (SADAFCO) | `data/imports/sadafco-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |
| 6010 | The National Agricultural Development Company (NADEC) | `data/imports/nadec-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (KPMG) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 2050 | `https://www.saudiexchange.sa/Resources/fsPdf/385_0_2026-03-09_15-05-26_En.pdf` | `5d6f64aa1d953b5057b0a6236135364ced2b0bc405fc041a77213ab4322b9a72` | `data/raw/SA/2050/documents/5d6f64aa…pdf` |
| 2270 | `https://www.saudiexchange.sa/Resources/fsPdf/407_0_2026-02-17_13-52-37_En.pdf` | `00e6c07e6c050222667faff445c729f5effaba4dfbe26d2093dc7b9f01dcd496` | `data/raw/SA/2270/documents/00e6c07e…pdf` |
| 6010 | `https://www.saudiexchange.sa/Resources/fsPdf/472_0_2026-02-04_18-05-06_En.pdf` | `7b1ccfda0ba31ff345e30a639153b75310993b783e28d8b41b3b7c919df01501` | `data/raw/SA/6010/documents/7b1ccfda…pdf` |

Registered in `data/raw/archive-index.json` (Savola 5,518,267 bytes; SADAFCO
1,420,371 bytes; NADEC 5,835,842 bytes; all `application/pdf`).

## Company notes

* **Savola (2050):** auditor Deloitte & Touche & Co.; auditor's report 8 March
  2026 (used as `filed_at` — the filed PDF carries no separate board-approval
  note). Thousands of SAR (`scale` 1000); primary statements scanned. Consolidated
  with non-controlling interests. **IFRS 5:** discontinued operations in both
  years (FY2025 loss SAR 7.6m; FY2024 loss SAR 1,440.2m — the Panda / retail and
  other disposals), so `income_before_income_taxes_and_zakat` is not carried and
  the manifest relies on `net_income = continuing_operations_income +
  discontinued_operations_income` (flagged verification.py change).
  `income_taxes_and_zakat` sums 'Income tax expense' and 'Zakat reversal /
  (expense), net' — a **net SAR 86.4m credit** in FY2025 (a large prior-year zakat
  reversal). FY2024 continuing profit also carried a one-off SAR 11,554.7m 'Gain
  on distribution of investment in equity-accounted investee' (the in-kind
  distribution of the Almarai stake) plus a SAR 139.0m derecognition loss —
  carried together as `other_nonoperating_income` for FY2024. `other_reserves`
  combines the general reserve, other reserves, the NCI-transaction effect and the
  foreign-currency translation reserve. FY2025: revenue +13.2% to SAR 26.08bn,
  net income SAR 940.5m, EPS 2.92. verify 20 pass / 2 warn / 0 fail (the two warns
  are the cash-to-balance-sheet cross-check — the cash-flow 'cash and cash
  equivalents' is net of bank overdrafts); 234 data points.

* **SADAFCO (2270):** auditor PwC; board approved 11 February 2026 (Note 38).
  Thousands of SAR; **primary statements are digital text** (`reader:
  manual.text`). Consolidated group; **no non-controlling interest at either
  year-end** (the small FY2024 NCI was extinguished on the disposal of a
  subsidiary). **IFRS 5:** a discontinued operation in both years (overseas dairy
  operations — loss SAR 10.6m FY2025 / SAR 9.6m FY2024) plus a small FY2025
  held-for-sale disposal group (assets SAR 30.3m, liabilities SAR 6.6m, both
  inside the reported current subtotals). `income_before_income_taxes_and_zakat`
  is not carried; the manifest relies on the `net = continuing + discontinued`
  bridge. `impairment_charges` is the 'Reversal of impairment on financial assets'
  line (a net reversal in both years). FY2025 `other_income` includes a SAR 107.4m
  gain on disposal of an asset held for sale. SADAFCO has no bank debt (leases
  only). FY2025: revenue +5.0% to SAR 3.00bn, net income SAR 477.4m, EPS 14.92.
  verify 19 pass / 1 warn / 0 fail (the warn is the cash-to-balance-sheet
  cross-check — SAR 4.5m of cash sits inside the held-for-sale disposal group);
  197 data points.

* **NADEC (6010):** auditor KPMG; board approved 1 February 2026 (13 Sha'aban
  1447H). **Full Saudi Riyals** (`scale` 1); primary statements scanned.
  Consolidated group with **no non-controlling interest and no discontinued
  operations** — the standard pre-tax − tax bridge applies. NADEC is an integrated
  dairy/agriculture producer, so it carries **biological assets**: the non-current
  'Biological assets' is folded into `other_noncurrent_assets` (with long-term
  prepayments) and the current 'Biological assets' into `inventory` — there is no
  dedicated biological-assets catalog field. `impairment_charges` is the trade-
  receivables impairment line; `other_income` / `other_expense` are the 'Other
  income' and 'Other gains/(losses), net' lines. `income_taxes_and_zakat` sums
  'Zakat for current year', 'Zakat reversal related to previous years' and 'Income
  Tax'. FY2024 carried a one-off SAR 356.5m 'Gain from the reclassification of a
  joint venture to an investment at FVOCI' (`other_nonoperating_income`). The
  statutory reserve was released to retained earnings in FY2025 under the new
  Companies Law. FY2025: revenue +9.5% to SAR 3.53bn, net income SAR 393.3m (down
  from a FY2024 boosted by the JV-reclassification gain), EPS 1.30. verify 20 pass
  / 0 warn / 0 fail; 223 data points.

## Engine change (for integration review)

`src/finengine/verification.py::ADDITIVE_IDENTITIES` — a new identity
`net income = continuing_operations_income + discontinued_operations_income`
(fires only when an issuer discloses both lines; dormant otherwise). Savola and
SADAFCO both need it. This is the same change carried on `claude/data-retail-1`,
`claude/data-materials-2` and `claude/data-realestate-1`; if any of those merges
first this is a no-op. Committed separately and flagged.

## Verification

`finengine verify savola` → 20 / 2 / 0; `finengine verify sadafco` → 19 / 1 / 0;
`finengine verify nadec` → 20 / 0 / 0. Bootstrap publishes 234 + 197 + 223 data
points with no pipeline errors. All balance-sheet identities, the pre-tax→net
bridge (NADEC both years), the `net income = continuing + discontinued` bridge
(Savola, SADAFCO both years) and the cash-flow reconciliation hold exactly.

Tests: `tests/test_food_sector_batch2.py`.

## Unresolved fields

* **Biological-asset roll-forward** (herd numbers, fair-value gains/losses on
  livestock, crop-by-crop) is in the notes, not a statement line.
* **Segment / brand / geography splits** (Savola Foods vs Panda vs Herfy;
  SADAFCO by country; NADEC dairy vs poultry vs crops) are in the segment note.
* **EBITDA / net debt** — not presented as statement lines.
