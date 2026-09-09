# Saudi retail sector — FY2025 batch 2

Batch branch: `claude/data-retail-2`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited financial statements (the full
audited PDFs linked on the Saudi Exchange company-profile "Financial Statements"
tab, "Annual / 2025" cell). No third-party data vendors. No engine or catalog
changes in this batch.

Retail follow-ups to batch 1 (Jarir, eXtra, Cenomi Retail, Al-Othaim,
BinDawood).

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 4193 | Nice One Beauty Digital Marketing Company | `data/imports/nice-one-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (EY) |
| 4180 | Fitaihi Holding Group Company | `data/imports/fitaihi-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (El Sayed El Ayouty / Moore) |
| 4008 | Saudi Company for Hardware (SACO) | `data/imports/saco-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (KPMG) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 4193 | `https://www.saudiexchange.sa/Resources/fsPdf/6866_0_2026-03-31_13-24-00_En.pdf` | `99e9db85fdadde6070fd81d2a138d921cf91839b2c9aad29c95d35e5b9640929` | `data/raw/SA/4193/documents/99e9db85…pdf` |
| 4180 | `https://www.saudiexchange.sa/Resources/fsPdf/453_0_2026-03-19_10-53-38_En.pdf` | `222938f60e4ff9b6d38972595d5a607f728a18120103ab1fa209be04cad10420` | `data/raw/SA/4180/documents/222938f6…pdf` |
| 4008 | `https://www.saudiexchange.sa/Resources/fsPdf/643_0_2026-03-10_11-26-00_En.pdf` | `c97865ad3d616538b38ca8dee48e2f7a26e5098fd7c9603040943492649d0b09` | `data/raw/SA/4008/documents/c97865ad…pdf` |

Registered in `data/raw/archive-index.json` (Nice One 7,422,052 bytes; Fitaihi
1,119,486 bytes; SACO 1,521,807 bytes; all `application/pdf`).

## Company notes

All three are consolidated, full Saudi Riyals, with **no non-controlling
interest**, no discontinued operations, and scanned primary statements
(`manual.vision`).

* **Nice One (4193):** auditor Ernst & Young; Board approved 16 March 2026
  (Note 32). **FY2025 was Nice One's first full year as a listed company** —
  the December 2024 IPO proceeds (SAR 5.5m to share capital + SAR 185.2m to
  share premium, cash-flow `capital_increase_proceeds` SAR 192.5m) were used to
  repay all borrowings, so the Group is now debt-free. `additional_paid_in_capital`
  is 'Share premium'; `other_reserves` is the small statutory reserve;
  `related_party_receivables` is 'Amounts due from related parties' (nil FY2025).
  **Rough year** — a large step-up in selling/marketing (SAR 146m → 179m) and
  G&A (SAR 43m → 56m) took operating profit from SAR 79.0m to SAR 10.3m and net
  profit from SAR 71.7m to SAR 3.0m, EPS 0.03 (FY2024 0.65). FY2025 zakat is
  66.6% of the collapsed pre-tax profit (zakat is on the zakat base, not income),
  so the effective-tax plausibility bound warns (expected). verify 19 pass /
  1 warn / 0 fail; 185 data points.

* **Fitaihi Holding (4180):** auditor El Sayed El Ayouty & Co. (Moore network);
  Board approved 10 March 2026 (Note 28). Fitaihi is a holding group — its
  jewellery / luxury-retail operations run an operating **loss** (SAR -8.4m
  FY2025 / -7.9m FY2024) and Group earnings come from an equity-accounted
  associate (`investments_associates` SAR 194.1m) and FVOCI-equity dividends.
  `share_of_profit_associates` is 'Company's share of the business result of the
  associate company'; `dividend_income` is the FVOCI-instrument dividend;
  `other_reserves` bundles the statutory reserve, the FVOCI reserve and the
  associate's cash-flow-hedge reserve. **No bank debt** — only lease
  liabilities. FY2025 net profit SAR 4.0m (FY2024 SAR 14.5m, which had a much
  larger associate contribution), EPS 0.015. verify 20 pass / 0 warn / 0 fail;
  171 data points.

* **SACO (4008):** auditor KPMG; Board approved 3 March 2026 (Note 37).
  **FY2024 was a loss year (net SAR -14.1m); FY2025 recovered to a net profit of
  SAR 45.6m**, helped by a SAR 42.2m 'Gain on sale of investment property, net'
  (the whole SAR 94.3m investment-property book value was disposed; SAR 140.4m
  cash proceeds — carried in `proceeds_asset_sales` — repaid all bank
  borrowings, leaving the Group with only IFRS 16 lease liabilities).
  `intangible_assets` is 'Intangible assets and goodwill'; `investment_property_value`
  is carried for FY2024 only; `short_term_investments` is the current
  FVOCI-held-for-sale AIH shareholding; `impairment_charges` is 'Expected credit
  losses' (a reversal in FY2025); `other_nonoperating_income` is the
  investment-property gain. FY2024's zakat charge against a pre-tax loss makes
  the effective-tax bound warn (expected). Revenue +7.4% to SAR 1.07bn, EPS 1.27
  (FY2024 -0.39). verify 19 pass / 1 warn / 0 fail; 196 data points.

## Verification

`finengine verify nice-one` → 19 / 1 / 0; `finengine verify fitaihi` →
20 / 0 / 0; `finengine verify saco` → 19 / 1 / 0. The two warnings are the
effective-tax plausibility bound firing on Nice One FY2025 (high zakat vs
collapsed pre-tax profit) and SACO FY2024 (zakat charge against a pre-tax loss)
— both expected, both because zakat is levied on the zakat base rather than
income. Bootstrap publishes 185 + 171 + 196 data points with no pipeline
errors. All balance-sheet identities, the pre-tax→net bridge and the cash-flow
reconciliation hold exactly, and each issuer's cash-flow closing balance ties
to its balance-sheet cash line.

Tests: `tests/test_retail_sector_batch2.py`.

## Unresolved fields

* **Operating KPIs** — Nice One's order / basket / cohort metrics, Fitaihi's
  store count and same-store sales, SACO's store count and store-format splits
  — are in the board reports, not the audited FS.
* **Fitaihi associate detail** — only the equity-accounted carrying value and
  the Group's share of result / OCI are carried; the associate's own financials
  are in the notes.
* **SACO lease-interest split** — `interest_paid` carries only the borrowing
  finance cost paid; the separate SAR 16.8m 'Interest on lease liabilities paid'
  is disclosed but not folded in.
* **EBITDA / net debt** — not presented as statement lines.
* **No engine or catalog changes in this batch.**
