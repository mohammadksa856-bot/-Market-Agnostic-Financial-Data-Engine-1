# Saudi telecommunications sector — FY2025 batch

The original stc/Zain batch is extended on `codex/telecom-95pct` with Mobily's
official FY2025 annual report and the first source-grounded operational KPI
layer. No third-party data vendors are used.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 7010 | Saudi Telecom Company (stc) | `data/imports/stc-2025-fy.json` | enabled, published | stc IR annual FS PDF |
| 7020 | Etihad Etisalat (Mobily) | `data/imports/mobily-2025-fy.json` | enabled, published | Mobily FY2025 annual report |
| 7030 | Mobile Telecommunications Company Saudi Arabia (Zain KSA) | `data/imports/zain-ksa-2025-fy.json` | enabled, published | Zain KSA IR signed FS PDF |

## Sources and archives

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 7010 | `https://www.stc.com/content/dam/groupsites/en/pdf/stc_Annual-2025-en.pdf` | `aeec895e88a6d48c1ae9e64c99eadeed5773deb87381239e9265403137b95e55` | `data/raw/SA/7010/documents/aeec895e…pdf` |
| 7020 | `https://ir.mobily.link/2025/pdfs/Mobily%20Annual%20Report%202025%20-%20English.pdf` | `6368c06e2379afdb844861d843bd7b136508b393a1babb210dfdb8640b7e22b6` | `data/raw/SA/7020/documents/6368c06e…pdf` |
| 7030 | `https://sa.zain.com/sites/default/files/media/2026-02/Zain%20English%20Signed%20FS%202025_3.pdf` | `bee6f9b63c9d81f625abb5675852d96679bb2776b746ef6f1bf2b1e7e26d192c` | `data/raw/SA/7030/documents/bee6f9b6…pdf` |

Both are registered in `data/raw/archive-index.json`. In both PDFs the primary
statements (financial position, profit or loss, cash flows) are **scanned
images**; the notes are digital text. Primary-statement figures were transcribed
from the page images (`reader: manual.vision/...`) and cross-checked against the
digital note disclosures (revenue, cost of revenue, depreciation & amortisation,
finance cost, segment totals, board-approval date all reconcile).

### Page references

* **stc (7010):** statement of financial position p8, profit or loss p9,
  cash flows p11. Filed / board-approved 2026-02-17.
* **Mobily (7020):** operating KPIs pp9, 13 and 25; primary statements pp116–117;
  segment revenue and capital expenditure p144. Board approval 2026-02-16;
  annual-report publication/PDF metadata date 2026-03-31.
* **Zain KSA (7030):** statement of financial position p8, profit or loss p9,
  cash flows p11. Board-approved 22 Sha'ban 1447H = 10 February 2026.

## Mapping notes

* **`selling_general_administrative_expense`** combines each issuer's separately
  presented "selling & marketing / distribution and marketing" and "general and
  administrative" lines.
* **stc** presents discontinued operations (TAWAL tower business and Digital
  Infrastructure Company / DIC) below the tax line per IFRS 5:
  `discontinued_operations_income` = SAR (54,133) thousand in 2025 and
  SAR 13,973,360 thousand in 2024 (disposal gains). The additive identity
  `pre-tax income − tax (+ discontinued ops) = net income` now accepts
  `discontinued_operations_income` as an optional third component so the 2024
  bridge (12,134,447 − 1,191,564 + 13,973,360 = 24,916,243) holds. This is the
  only engine contract change in the batch and is in a separate commit flagged
  for integration review.
* **Zain KSA** `income_taxes_and_zakat` is a credit (+41,887 thousand) in 2024
  following a withholding-tax provision reversal, producing an effective-tax
  ratio outside the usual band — this is a legitimate `warn`, not a failure.
* **Zain KSA** refinanced in 2025: current portion of borrowings fell from
  SAR 5.97bn to SAR 0.23bn as long-term borrowings rose. Both the current and
  non-current debt lines are mapped.
* **`capex`** for Zain KSA sums the property/equipment and intangible-asset
  purchase lines in investing activities.

## Verification

`finengine verify stc` → 23 pass / 1 warn / 0 fail.
`finengine verify mobily` → 3 pass / 0 warn / 0 fail.
`finengine verify zain` → 20 pass / 1 warn / 0 fail.
The warns are the zakat-reversal effective-tax ratios described above.

Bootstrap into a throwaway snapshot publishes 192 (stc) and 184 (Zain KSA) data
points with no pipeline errors. Derived checks: stc FY2025 net margin 19.4%
(down from 32.8% in FY2024 because of the prior-year disposal gain), operating
margin 18.6%, free cash flow SAR 6.49bn, ROE 16.9%; Zain KSA FY2025 net margin
5.5%, operating margin 12.0%, free cash flow SAR 1.28bn, ROE 5.6%.

Mobily publishes 45 current points in a clean bootstrap, including four segment
revenue facts and nine operating facts: mobile/prepaid/postpaid/fiber subscribers,
3G/4G/5G coverage, 5G sites and network capex. The four segment revenue facts
reconcile exactly to consolidated revenue of SAR 19.642bn.

Tests: `tests/test_telecom_sector.py` (11 tests).

## Unresolved fields

* **Historical depth.** Mobily currently has FY2025 only; stc and Zain remain
  shallow. Annual and quarterly source histories must be archived and parsed
  before any operator can honestly be called 95% complete.
* **Operational KPIs.** Mobily now has the printed subscriber split, FTTH,
  coverage, 5G sites and network capex. ARPU, churn and traffic are absent from
  the FY2025 report and remain explicit gaps. stc and Zain still need their own
  source-grounded operational supplements.
* **Company understanding domains.** Detailed company model, products,
  competitors, ownership history, governance, announcements, corporate actions,
  market data and valuation history are not completed by this batch. They remain
  required by the 18-category 95% target.
* **EBITDA / net debt / net-debt-to-EBITDA.** Neither issuer presents EBITDA or a
  net-debt reconciliation as a line in the audited statements (both stop at
  operating profit). The engine does not derive them. If a deterministic
  definition is agreed (operating income + depreciation_amortization; total_debt
  − cash), it should be added platform-side in an engine-review commit rather
  than baked into these manifests.
* **stc segment disclosures and Zain KSA lease maturity detail** live in the
  notes and were not extracted in this batch.
