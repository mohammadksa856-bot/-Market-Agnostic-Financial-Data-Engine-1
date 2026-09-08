# Saudi cement sector — FY2025 batch 1

Batch branch: `claude/data-cement-1`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited financial statements (the full
audited PDFs linked on the Saudi Exchange company-profile "Financial Statements"
tab, "Annual / 2025" cell). No third-party data vendors. No engine or catalog
changes in this batch.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 3030 | Saudi Cement Company | `data/imports/saudi-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (BDO) |
| 3050 | Southern Province Cement Company | `data/imports/southern-province-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited standalone FS PDF (BDO) |
| 3020 | Yamama Cement Company | `data/imports/yamama-cement-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited standalone FS PDF (Professional Consultants Company) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 3030 | `https://www.saudiexchange.sa/Resources/fsPdf/425_0_2026-03-16_10-20-05_En.pdf` | `799306475fca27d3cf24a9300db797e973b753662f1f2fe1bda250a7b57103ab` | `data/raw/SA/3030/documents/79930647…pdf` |
| 3050 | `https://www.saudiexchange.sa/Resources/fsPdf/427_0_2026-04-07_21-05-53_En.pdf` | `25c47e79e1906fafa75c4b40f84c260ec662059feb1c5668b62e0b44fcf09acb` | `data/raw/SA/3050/documents/25c47e79…pdf` |
| 3020 | `https://www.saudiexchange.sa/Resources/fsPdf/424_0_2026-02-25_15-17-48_En.pdf` | `5f522341d6ad40c84c4ba13fec7de717f89c31dd93365088f382b097eea802a0` | `data/raw/SA/3020/documents/5f522341…pdf` |

Registered in `data/raw/archive-index.json` (Saudi Cement 2,045,538 bytes;
Southern Province 4,295,570 bytes; Yamama 1,789,892 bytes; all `application/pdf`).

## Company notes

All three have scanned primary statements (transcribed from page renders) and
digital-text notes. None has non-controlling interest or discontinued operations
— the standard pre-tax − zakat bridge applies. Southern Province and Yamama
publish **standalone** (non-consolidated) statements — neither has subsidiaries.

* **Saudi Cement (3030):** auditor BDO Dr. Mohamed Al-Amri & Co.; board
  authorised to issue 9 March 2026 (Note 36). Thousands of SAR. Consolidated
  (has an equity-method associate). The statutory reserve was transferred to
  retained earnings in FY2024, so equity is just share capital + retained
  earnings. `other_current_liabilities` combines 'Dividend payable' and 'Contract
  liabilities'. FY2025 was softer — cement demand and pricing eased so revenue
  was flat at SAR 1.67bn while cost of revenue rose, taking gross margin from
  39.8% to 36.1% and net income down 13.8% to SAR 363.7m, EPS 2.38.
  verify 20 pass / 0 warn / 0 fail; 198 data points.

* **Southern Province Cement (3050):** auditor BDO Dr. Mohamed Al-Amri & Co.;
  board approved 30 March 2026. **Full Saudi Riyals** (`scale` 1). The FY2024
  comparatives are **restated** (issuer Note 34, reclassification of investment
  properties). **FY2025 was a LOSS year** — cost of revenues jumped from
  SAR 626.0m to SAR 835.2m as energy and clinker costs rose and prices fell,
  cutting gross margin from 33.0% to 3.7%; operating loss SAR 40.8m, net loss
  SAR 48.5m (FY2024 restated net profit SAR 193.0m), EPS −0.35. `net_income`,
  `operating_income` and FY2025 EPS are negative. The single 'Zakat' line
  (SAR 13.5m charge) against a pre-tax loss makes the effective-tax bound warn
  (expected). `provisions` is 'Quarry rehabilitation provision'; the FY2024
  'Investment properties' line (SAR 5.5m) was disposed in FY2025. Heavy
  plant-upgrade year — SAR 657.8m capex funded by SAR 624.3m of new loans.
  verify 19 pass / 1 warn / 0 fail; 200 data points.

* **Yamama Cement (3020):** auditor Professional Consultants Company
  (Abdullah S. Al Msned); board approved 16 February 2026. **Full Saudi Riyals**
  (`scale` 1). `operating_income` is 'Income from main activities';
  `impairment_charges` combines 'Provision for expected credit loss (ECL)' and
  'Provision for impairment of spare parts for Plants and equipment' (both new in
  FY2025); `other_nonoperating_income` is a large SAR 163.6m 'Gain from sale of
  property, plant and equipment' (land / plant disposals). `other_reserves`
  combines the statutory reserve, an 'Additional reserve' and the negative
  cumulative-fair-value-of-OCI. The cash-flow statement discloses no separate
  'finance cost paid' line, so `interest_paid` is not carried. `capex` combines
  'Purchase of property, plant, and equipment' and 'Additions to capital works in
  progress' (SAR 416.0m FY2025 after SAR 983.8m FY2024). FY2025: revenue +21.3%
  to SAR 1.42bn, net income +14.8% to SAR 482.9m (helped by the disposal gain),
  EPS 2.38. verify 20 pass / 0 warn / 0 fail; 212 data points.

## Verification

`finengine verify saudi-cement` → 20 / 0 / 0; `finengine verify
southern-province-cement` → 19 / 1 / 0; `finengine verify yamama-cement` →
20 / 0 / 0. Bootstrap publishes 198 + 200 + 212 data points with no pipeline
errors. All balance-sheet identities, the pre-tax→net bridge and the cash-flow
reconciliation hold exactly, and each issuer's cash-flow closing balance ties to
its balance-sheet cash line.

Tests: `tests/test_cement_sector_batch1.py`.

## Unresolved fields

* **Clinker / cement production and dispatch volumes, capacity utilisation,
  export share, average selling price** are in the board reports, not the
  audited FS.
* **Southern Province FY2024 restatement detail** — only the restated
  comparatives are carried; the pre-restatement figures are in Note 34.
* **EBITDA / net debt** — not presented as statement lines.
* **No engine or catalog changes in this batch.**
