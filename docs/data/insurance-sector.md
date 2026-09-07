# Saudi insurance sector — batch 1

A representative acceptance set of Saudi insurers, FY2025 audited financial
statements (FY2024 comparatives from the same filing), IFRS 17 basis.

| Symbol | Company | Segment | Manifest | Source | Archived hash |
|---|---|---|---|---|---|
| 8010 | Tawuniya (The Company for Cooperative Insurance) | Composite / general | `tawuniya-2025-fy.json` | tawuniya.com IR — `2025_Q4_Financial_Statements_EN.pdf` | `e44ceb13…` |
| 8210 | Bupa Arabia for Cooperative Insurance | Health | `bupa-arabia-2025-fy.json` | buy.bupa.com.sa IR — 2025 Annual Report and Accounts (audited FS section) | `80c5b0b2…` |
| 8200 | Saudi Reinsurance Company (Saudi Re) | Reinsurance | `saudi-re-2025-fy.json` | saudire.net IR — `Saudi-Re-YE25-Signed-English-FS.pdf` | `b505c414…` |
| 8060 | Walaa Cooperative Insurance Company | P&C / takaful | `walaa-2025-fy.json` | Saudi Exchange filing — `16751_490_2026-04-22_…_en.pdf` | `c41f54cc…` |

`data/raw/archive-index.json` links each hash to its source URL, byte size and
content type.

## Reader

- **Text-extractable primary statements** (`reader: manual.text/…`): Tawuniya,
  Bupa, Saudi Re. Figures transcribed line-for-line.
- **Scanned primary statements** (`reader: manual.vision/…`): Walaa. The Saudi
  Exchange filing renders the three primary statements as page images; the notes
  are digital text. Statement figures read from the page images.

## Metric mapping (IFRS 17)

| Manifest metric | Statement line |
|---|---|
| `insurance_revenue` | Insurance revenue (reinsurers: "Reinsurance revenue") |
| `insurance_service_expense` | Insurance service expenses |
| `insurance_service_result` | Insurance service result **before** reinsurance (engine-derives it as `insurance_revenue + insurance_service_expense` where the issuer does not print the line — Bupa, Saudi Re) |
| `reinsurance_premiums` / `reinsurance_recoveries` | Allocation of reinsurance premiums / Amounts recoverable from reinsurers (only issuers that split them: Tawuniya, Walaa) |
| `reinsurance_result` | Net expense from reinsurance contracts held (reinsurers: "…from retrocession contracts") |
| `underwriting_result` | Net insurance service result / Insurance service results |
| `insurance_investment_income` | Net investment income / Net investment results |
| `insurance_contract_liabilities`, `reinsurance_contract_assets/liabilities` | Balance-sheet contract positions (reinsurers: inward book = "reinsurance contract …", outward = "retrocession contract …") |
| `income_taxes_and_zakat` | Zakat + income tax charge combined |

## Engine ratios (proposed in the same batch's engine commit, for integration review)

`calculations.py`: `insurance_service_result` derivation; `expense_ratio` =
abs(operating_expenses) / insurance_revenue; `combined_ratio` = (insurance_revenue
− underwriting_result + abs(operating_expenses)) / insurance_revenue;
`retention_ratio` = 1 − abs(reinsurance_premiums) / gross_written_premium. All
no-op unless the insurer lines are present. `verification.py`: two IFRS 17
additive identities.

Engine output (FY2025): combined ratio Tawuniya 98.0%, Bupa 97.6%, Saudi Re
92.9%, Walaa 106.8% (Walaa ran an underwriting loss — a claims spike drove
insurance service expenses from SAR 1.99 bn to 2.71 bn; net loss SAR 175 m,
loss per share SAR 1.38).

## Unresolved / not-yet-available fields, with reasons

| Field(s) | Companies | Reason |
|---|---|---|
| `gross_written_premium` | 8060 Walaa | Walaa's FY2025 filing reports the IFRS 17 top line ("Insurance revenue") but not a GWP figure on the face or in a mapped note. |
| `reinsurance_premiums`, `reinsurance_recoveries` (gross split) | 8210 Bupa | Bupa presents reinsurance only on a net basis ("Net expenses from reinsurance contracts held"); no gross premium / recovery split on the face. |
| `retention_ratio` | 8210 Bupa, 8200 Saudi Re | Needs the gross reinsurance/retrocession premium split, which these issuers do not present. |
| `loss_ratio`, `claims_frequency`, `claims_severity` | all 4 | IFRS 17 statements do not break "insurance service expenses" into claims incurred vs. acquisition vs. attributable expenses on the face; needs the service-expense note. |
| `solvency_ratio`, `solvency_capital` | all 4 | The Insurance Authority solvency margin is not in the primary statements; it is a separate regulatory return. |
| `cash` (instant), FY2024 | 8200 Saudi Re | FY2024 balance-sheet "Cash and bank balances" includes restricted cash outside the cash-flow "cash and cash equivalents"; only FY2025 (which reconciles) is ingested. |
| `equity_parent` / `noncontrolling_interests` (balance sheet) | 8060 Walaa | An EOSB-remeasurement line sits between "Total shareholders' equity" and "Total equity", so those two do not sum to total equity; only `total_equity` is ingested (the income-statement owner/NCI split is ingested). |
| Segment premiums, ownership, market data, valuation, analyst consensus | all 4 | Out of scope for this batch — separate feeds. |
