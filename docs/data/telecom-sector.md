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

After the clean four-company build, all four operators pass the
five-annual-period, 12-quarter, provenance, no-synthetic-source and
no-critical-exception gates. GO (7040) has five annual
periods, 12 historical standalone quarters for FY2023-FY2025, and the latest
FY2026 Q1, all with clean provenance; it still lacks four of the 28 required
core fields. The weighted 18-category coverage target remains open. Current
governed scores are 53.54 for stc, 44.41 for Mobily, 54.84 for Zain KSA and
27.46 for GO. None is labelled 95% or ready.
The largest remaining gaps are deeper statement/note coverage, point-in-time
market history and valuation, issuer guidance, and attributable/licensed analyst
coverage. The Saudi Exchange historical-price CDN currently denies the local
connector, so trading and valuation must remain open rather than being filled
from an unattributed source.

## Market data batch (2026-09-23): Saudi Exchange price history

Real Saudi Exchange historical daily OHLCV was added for all four listed
telecom operators, closing part of the "point-in-time market history and
valuation" gap noted above. The automated `saudi_market.py` connector
remains CDN-blocked from this environment (`access denied` /
`errors.edgesuite.net`), so the data was captured through an authorized
interactive browser session against the official historical-reports UI
(`https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/
reports-publications/historical-reports?locale=en`, Main Market →
Telecommunication Services sector) and then archived and published through
the normal manifest pipeline.

### Sources and archives

| Symbol | Trading days | Range | Raw archive | SHA-256 |
|---|---|---|---|---|
| 7010 (stc) | 1,247 | 2021-09-22 → 2026-09-22 | `data/raw/SA/7010/market/saudi-exchange-historical-2026-09-22.json` | `eb3033f792f3773572df13eccbeb8f0233f860b2ab1a5c10721c9ce17ee668f2` |
| 7020 (Mobily) | 1,247 | 2021-09-22 → 2026-09-22 | `data/raw/SA/7020/market/saudi-exchange-historical-2026-09-22.csv` | `0a9b858381ef4055d14d729d779fe793928566dcbb8fdb8892f760efe6b044b3` |
| 7030 (Zain KSA) | 1,247 | 2021-09-22 → 2026-09-22 | `data/raw/SA/7030/market/saudi-exchange-historical-2026-09-22.csv` | `e0901bd77170323ec993fade9c609f2cbbdc9d8ee8bffadf056655f2aeb853c9` |
| 7040 (GO Telecom) | 516 | 2024-09-01 → 2026-09-22 (**partial**) | `data/raw/SA/7040/market/saudi-exchange-historical-2026-09-22-partial-2024-2026.csv` | `ccecc804a50087376a17baa9aa8be4740dcef8f3c98e370e54eb9b3521ba6014` |

All four are registered in `data/raw/archive-index.json` (source_url,
content_hash, byte_size, content_type, archived_at) and published through
`data/imports/{stc,mobily,zain,go-telecom}-market-prices-2026-09-23.json`,
schema-matched to the existing `aramco-market-prices-2026-09-04.json`.

**GO Telecom (7040) gap, stated plainly:** only the 2024-09-01 through
2026-09-22 window (~2 years) was captured to a file before the authorized
capture session ended. The earlier 2021-09-22 through 2024-08-31 history
was viewed live in that same session but never saved to disk, and several
trading-halt rows in that window showed `-` placeholders for OHLCV. Neither
is included here — the missing ~2.5 years is an open gap for a future
capture pass, not something estimated or interpolated.

### Parsing

The CSV export interleaves the field delimiter and the thousands-group
separator with the same character (e.g. `...,64.10,64.60,63.65,63.65,621,
870,39,823,443.95,2,975`), so a naive comma-split, or a greedy
"3-digits-after-a-comma" regex, cannot reliably place the volume/turnover/
trades boundaries once volume itself spans more than one digit group. A new
`parse_saudi_history_csv` (`src/finengine/saudi_market.py`) resolves this by
testing every split point that matches standard thousands-grouping shape
and, when more than one survives, disambiguating with the row's own
turnover/volume ratio (the day's VWAP), which must fall inside that row's
`[low, high]` — a constraint only the true split satisfies. Trading-halt
rows are excluded, never zero-filled. `normalize_saudi_market_rows` is
reused unchanged for STC's raw DataTables JSON, whose row shape already
matches its expected input. Targeted tests in `tests/test_saudi_market.py`
cover the thousands-grouped reconstruction, halt-row exclusion, and an
OHLC-sanity rejection case.

### Real before/after completeness (scratch-DB bootstrap, `company_completeness` table)

| Symbol | market_data before | market_data after | valuation before | valuation after |
|---|---|---|---|---|
| 7010 (stc) | 5/26 (0.19) | 8/26 (0.31) | 11/25 (0.44) | 11/25 (0.44, unchanged) |
| 7020 (Mobily) | 1/26 (0.04) | 7/26 (0.27) | 0/25 (0.00) | 19/25 (0.76) |
| 7030 (Zain KSA) | 0/26 (0.00) | 7/26 (0.27) | 0/25 (0.00) | 21/25 (0.84) |
| 7040 (GO Telecom) | 0/26 (0.00) | 6/26 (0.23) | 0/25 (0.00) | 0/25 (0.00, unchanged) |

Mobily and Zain KSA both got real valuation facts published by
`refresh_market_valuations` (20 and 22 facts respectively: market cap,
P/E, P/B, EV multiples, yields, 52-week high/low, SMAs, calendar returns,
etc., all filtered to `filed_at <= price_date`). **stc and GO Telecom's
valuation refresh returned `no_fundamentals_available_as_of_price_date`
both times** (first pass and the bootstrap's final registry-wide sweep) —
their market_data completeness improved from the new price archive, but no
new valuation facts were published. This is a real, unresolved finding, not
downplayed here: it needs follow-up to determine why stc's existing
fundamentals don't align with the archived price dates for this refresh
(Zain and Mobily, which do have overlapping filed_at/price_date fundamentals,
worked correctly), and GO Telecom has no valuation facts at all pending
either the fundamentals or the rest of its price history.

Ingestion was proven through the real pipeline, not just JSON validity:
`_apply_reviewed_manifest` (the same code `finengine bootstrap` calls) on a
scratch database, `finengine verify --imports data/imports
--strict-warnings` (0 fail, pre-existing warns only — none new, none on
these four symbols' price data), and `finengine audit --strict-warnings`
(0 failures, 0 warnings). Idempotency was confirmed by re-running the
Mobily manifest through `_apply_reviewed_manifest` twice against the same
scratch DB: both reruns reported `duplicate` (0 inserted, 0 restated, 1,247
duplicate) with the row count and `max(version)` unchanged across both
reruns.

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
  but market history, valuation, industry context, deeper financial notes and
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
