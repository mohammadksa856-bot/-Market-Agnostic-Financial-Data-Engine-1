# Saudi telecommunications sector — FY2025 batch

The governed Saudi telecom universe contains four listed operators: stc,
Mobily, Zain KSA, and Etihad Atheeb/GO. All four have source-grounded issuer
data; GO currently has five annual periods, a company profile and one interim
quarter plus 12 historical standalone quarters, with deeper statement-line and
industry-context coverage still open. No
third-party data vendors are used.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 7010 | Saudi Telecom Company (stc) | `data/imports/stc-2025-fy.json` | enabled, published | stc IR annual FS PDF |
| 7020 | Etihad Etisalat (Mobily) | `data/imports/mobily-2025-fy.json` | enabled, published | Mobily FY2025 annual report |
| 7030 | Mobile Telecommunications Company Saudi Arabia (Zain KSA) | `data/imports/zain-ksa-2025-fy.json` | enabled, published | Zain KSA IR signed FS PDF |
| 7040 | Etihad Atheeb/GO Telecom | `data/imports/go-telecom-2021-2025-fy-history.json` | enabled, published | GO Telecom FY2025 annual report |

## Reviewed global peers

Each operator has an explicit reviewed global peer set. It contains the other
three Saudi listed operators plus e&, Ooredoo, Zain Group, Vodafone, Orange and
Deutsche Telekom. Membership records the official issuer/IR source and the
classification rationale; it does not invent financial metrics. Quantitative
comparisons use only peers whose sourced financial data has been onboarded,
while the complete nine-member universe remains visible in coverage scoring.

## Sources and archives

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 7010 | `https://www.stc.com/content/dam/groupsites/en/pdf/stc_Annual-2025-en.pdf` | `aeec895e88a6d48c1ae9e64c99eadeed5773deb87381239e9265403137b95e55` | `data/raw/SA/7010/documents/aeec895e…pdf` |
| 7020 | `https://ir.mobily.link/2025/pdfs/Mobily%20Annual%20Report%202025%20-%20English.pdf` | `6368c06e2379afdb844861d843bd7b136508b393a1babb210dfdb8640b7e22b6` | `data/raw/SA/7020/documents/6368c06e…pdf` |
| 7030 | `https://sa.zain.com/sites/default/files/media/2026-02/Zain%20English%20Signed%20FS%202025_3.pdf` | `bee6f9b63c9d81f625abb5675852d96679bb2776b746ef6f1bf2b1e7e26d192c` | `data/raw/SA/7030/documents/bee6f9b6…pdf` |
| 7040 | `https://www.go.com.sa/en/Resources/2/2025-2024-E.pdf` | `d76f55f907fc95a16d3fc852616c135f9a0e61d7d698e96c9ab2cc52e0ef34fe` | `data/raw/SA/7040/documents/d76f55f9…pdf` |

The completed issuer PDFs are registered in `data/raw/archive-index.json`.
Where primary statements (financial position, profit or loss, cash flows) are
**scanned images**, figures were transcribed from the page images
(`reader: manual.vision/...`) and cross-checked against digital note disclosures
(revenue, cost of revenue, depreciation & amortisation, finance cost, segment
totals and board-approval date reconcile).

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

The second operational pass adds 28 sourced stc facts and 19 sourced Zain KSA
facts. stc now has 5G coverage for 2021-2025, 4G coverage and data traffic for
2021-2023, 5G sites, FTTH homes passed, data-center count and 2024-2025 subscriber
splits. Zain KSA now has a continuous 2021-2025 customer, blended-ARPU and capex
series, plus only those network-coverage observations explicitly identified by
the issuer. The ambiguous 99% coverage cards in the 2023/2024 parent presentations
are deliberately not labelled as 5G coverage.

Mobily's company-understanding layer publishes 23 versioned attributes, two
ownership positions reconciling to 100%, three dividend actions and four
disclosures. Every item points back to the archived FY2025 annual report.

The historical pass adds audited/issuer-reported annual headlines for Mobily
FY2021-FY2024 and standalone Q1-Q3 for 2021-2024. It also adds 12 consecutive
quarters for stc and Zain KSA (Q1 2023 through Q4 2025). stc manifests are split
by presentation so each fact resolves to the exact official PDF; Zain facts
carry the precise Saudi Exchange announcement sources, including both inputs
for Q4 values derived as FY minus 9M. Mobily's 2021 quarters are explicitly
labelled comparatives from the corresponding 2022 issuer presentations.

Tests: `tests/test_telecom_sector.py` lock the universe to all four operators
and require every enabled telecom to publish without errors. Issuer-specific
financial identities, operational history, segment reconciliation, profile,
ownership, dividends and disclosures are asserted where those layers are
ingested. GO also has a manifest identity test and participates in the common
publication gate.

## Readiness measurement

The annual/quarter, provenance, no-synthetic-source and no-critical-exception
gates are evaluated independently from the weighted 18-category contract. GO
(7040) has five annual periods, 12 historical standalone quarters for
FY2023-FY2025, and FY2026 Q1 with clean provenance; deeper statement-line
coverage remains open.

On 2026-09-22 the official Saudi Exchange Historical Reports UI was captured
through the reviewed browser path after the server-side connector was denied.
The governed manifests contain 20,335 unique daily closes: stc 6,062
(2003-01-25 onward), Mobily 5,495 (2004-12-20 onward), Zain KSA 4,616
(2008-03-22 onward), and GO 4,162 (2009-03-21 onward). All end at 2026-09-22.
Rows whose exchange-displayed open/high/low violate OHLC ordering keep the
official close, volume and turnover but leave those three unsafe optional
values null; no session or close was invented or discarded.

Under contract version 1.0.0 after that import, the current governed scores are
45.82 for stc, 43.63 for Mobily, 49.33 for Zain KSA and 26.62 for GO. The market
history raised them from 44.25, 37.80, 42.53 and 24.47 respectively. None is
labelled 95% or ready: only one of 18 categories currently clears its complete
category gate for each company. The largest weighted gaps are deeper
statement/note coverage, operational KPIs, announcements, dividends, ownership
and valuation. Attributable/licensed analyst coverage remains explicitly
unavailable until a governed provider exists and cannot be counted as complete.

## Unresolved fields

* **Historical statement depth.** The annual/quarter hard gates are now closed
  for all four listed operators. Most historical quarters contain headline revenue/profit measures rather
  than every IFRS statement line. Mobily Q4 standalone values require the
  governed `FY - 9M` derivation; they are not presented directly by the issuer.
* **stc presentation archive.** Exact official URLs and per-file manifests are
  retained, but the issuer CDN returns HTTP 403/TLS authentication failures to
  the local archive worker for six quarterly-presentation PDFs. No fictitious
  archive entries were created; this remains an explicit retrieval backlog.
* **Operational KPI gaps.** Mobily now has the printed subscriber split, FTTH,
  coverage, 5G sites and network capex, but ARPU and churn are not disclosed.
  stc does not publish ARPU in the reviewed 2021-2025 reports and no proxy is
  invented. Zain's 2023-2024 5G-specific coverage is not disclosed separately.
* **Company understanding domains.** Identity, business model, current
  ownership, dividends, governance and selected risks/ESG are now populated,
  but valuation, industry context, deeper financial notes and
  attributable analyst coverage remain incomplete. They remain required by the
  18-category 95% target; the engine must not label the sector ready before the
  weighted score and all hard gates pass.
* **EBITDA / net debt / net-debt-to-EBITDA.** Neither issuer presents EBITDA or a
  net-debt reconciliation as a line in the audited statements (both stop at
  operating profit). The engine does not derive them. If a deterministic
  definition is agreed (operating income + depreciation_amortization; total_debt
  − cash), it should be added platform-side in an engine-review commit rather
  than baked into these manifests.
* **stc segment disclosures and Zain KSA lease maturity detail** live in the
  notes and were not extracted in this batch.
