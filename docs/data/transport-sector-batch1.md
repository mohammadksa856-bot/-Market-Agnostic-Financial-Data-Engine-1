# Saudi transport & logistics sector — FY2025 batch 1

Batch branch: `claude/data-transport-1` (rebased onto `origin/main` @ `b244e95`,
after the cement and tech batches merged). Source-faithful manifests transcribed
by hand from each issuer's official FY2025 audited consolidated financial
statements (the full audited PDFs linked on the Saudi Exchange company-profile
"Financial Statements" tab, "Annual / 2025" cell). No third-party data vendors.
No engine or catalog changes in this batch. `config/companies.json` and
`data/raw/archive-index.json` were merged as a union onto main's current
versions (only the two new records added); `data/financial.sqlite3` and the
generated `financial-report.html` / `financial-data.csv` are untouched.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 4030 | The National Shipping Company of Saudi Arabia (Bahri) | `data/imports/bahri-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (EY) |
| 4263 | SAL Saudi Logistics Services Company | `data/imports/sal-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (EY) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 4030 | `https://www.saudiexchange.sa/Resources/fsPdf/439_0_2026-03-17_13-59-49_En.pdf` | `3236f81fdc8baa9592a7d7a44228ea5972cd19799c4f43b58e8f3179d8b00872` | `data/raw/SA/4030/documents/3236f81f…pdf` |
| 4263 | `https://www.saudiexchange.sa/Resources/fsPdf/5026_0_2026-02-16_20-30-54_En.pdf` | `9d222fb6278ea52462fa23350f2813da17a9cf36ad3494a3d50da6fa07883725` | `data/raw/SA/4263/documents/9d222fb6…pdf` |

Registered in `data/raw/archive-index.json` (Bahri 1,847,202 bytes; SAL
2,217,225 bytes; both `application/pdf`).

## Company notes

Both publish in **thousands of SAR** (`scale` 1000), both audited by **Ernst &
Young**, both with scanned primary statements (transcribed from page renders) and
digital-text notes. Neither has discontinued operations.

* **Bahri (4030):** the Board approved the statements on 21 Ramadan 1447H /
  **10 March 2026** (Note 33). Consolidated with non-controlling interests (the
  chemical-tanker and dry-bulk fleet subsidiaries). `other_operating_revenue` is
  the **'Bunker subsidy'** — a government fuel subsidy presented between 'Gross
  profit before bunker subsidy' and the reported 'Gross profit'; `gross_profit`
  is the reported line (after the subsidy). `share_of_profit_associates` is the
  large 'Share of results of equity accounted investees' (Bahri's tanker/bulk
  JVs — SAR 566.4m in FY2025). `construction_in_progress` is 'Projects under
  construction' (newbuild vessels); `capex` sums additions to PP&E and to
  projects under construction (SAR 4.24bn in FY2025 — a heavy fleet-expansion
  year), funded by a net SAR 2.94bn increase in borrowings after a FY2025 share
  capital increase from SAR 7.38bn to SAR 9.23bn. Revenue +9.1% to SAR 10.35bn,
  net income +7.3% to SAR 2.56bn, EPS 2.63. verify 24 pass / 0 warn / 0 fail;
  221 data points.

* **SAL (4263):** the Board approved the statements on 22 Sha'aban 1447H /
  **10 February 2026** (Note 37). Consolidated group (SAL and one subsidiary);
  **no non-controlling interest**, so only `total_equity` is carried. SAL is the
  cargo-handling / air-freight logistics operator carved out of Saudia; its large
  `right_of_use_assets` and `lease_liabilities` are the airport and warehouse
  concession leases. `impairment_charges` is the 'Allowance for expected credit
  losses' line — a small net reversal in both years. `other_reserves` combines
  the statutory 'Reserve' and the negative 'Actuarial reserve'; `prepayments`
  combines 'Prepayments and other receivables' and the 'Sublease' asset.
  `income_taxes_and_zakat` is the single 'Zakat expense' line. Revenue +4.6% to
  SAR 1.71bn, net income +5.5% to SAR 697.9m (net margin 40.8%), EPS 8.72.
  verify 20 pass / 0 warn / 0 fail; 197 data points.

## Verification

`finengine verify bahri` → 24 pass / 0 warn / 0 fail; `finengine verify sal` →
20 pass / 0 warn / 0 fail. Full-repo `finengine verify` after the rebase: 599
pass / 11 warn / 0 fail (all 11 warnings pre-date this batch and belong to other
issuers). A clean rebuild to a scratch database publishes **221 sourced facts
for Bahri (sa:4030)** and **197 for SAL (sa:4263)** with no pipeline errors, and
`finengine audit --strict-warnings` against that scratch database returns
0 failures / 0 warnings across all 24 checks (including `source_archive_hashes`
and `raw_artifact_hashes` for the two new PDFs). All balance-sheet identities,
the pre-tax→net bridge, the owners/NCI split (Bahri) and the cash-flow
reconciliation hold exactly, and each issuer's cash-flow closing balance ties to
its balance-sheet cash line.

Tests: `tests/test_transport_sector_batch1.py` — 5 tests, all pass.

## Backlog — fields not carried (nothing was guessed)

| Field / item | Why not carried | Resolution |
|---|---|---|
| Operational KPIs — Bahri: fleet count, DWT, TCE / spot rates, fleet utilisation, voyage vs time-charter days. SAL: tonnage handled, import/export/transit cargo mix, station throughput, dwell time | Disclosed only in the board / management report, not in the audited financial statements or their notes | Add a `transport_operations` sector pack (`fleet_size`, `cargo_volume`, `passenger_load_factor`-analogues, `revenue_per_tonne_km`) and ingest from the board report or an issuer data supplement in a later, separately-reviewed pass |
| Bahri "bunker subsidy" receivable / accrual roll-forward | Presented as a single P&L line ('Bunker subsidy') with no balance-sheet receivable movement on the face of the statements; the note gives only the annual amount | Carry the note-level government-grant receivable movement if a future year discloses it; for now `other_operating_revenue` holds the reported annual figure |
| Segment revenue / result splits (Bahri: oil / chemicals / dry bulk / logistics; SAL: ground handling / cargo / other) | In the segment note as a table, not yet mapped to dimensioned facts in this batch | Ingest via the existing `segment_revenue` / `segment_investments_associates` dimensioned metrics in a follow-up |
| EBITDA, net debt | Not presented as statement lines | Engine-computed downstream by `calculations.py` from the carried inputs; no manifest fact needed |

## Engine / catalog changes

None in this batch.
