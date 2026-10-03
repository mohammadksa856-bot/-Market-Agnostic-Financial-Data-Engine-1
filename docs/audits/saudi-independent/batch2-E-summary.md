# Batch 2 / Group E independent audit: 3002, 3003, 3005, 3020, 3040 (cement)

Audited: `origin/codex/telecom-95pct` @ `ec610f3` (the five manifests are byte-identical on `origin/main` and on
`claude/data-cement-1/2/3`, `claude/aramco-alrajhi-gap-closure`). Source PDFs were read with `git show` from
`origin/claude/audit-saudi-batch1-B` (they are not on the audited branch); each sha256 equals the
`data/raw/archive-index.json` content_hash. No data/**, AWS, Supabase or other branch was touched. 1050/1060 not touched.

Method: every printed statement page (balance sheet, P&L/OCI, cash flow) was rendered and read by eye; values were
transcribed independently (`tools/e_transcripts/*.json`, page + line item) and compared with every published fact by
`tools/e_compare.py`; every subtotal and every composite fact (sums of several source lines) was re-added; the
text layer was used as a second reader (`tools/e_textlayer_verify.py`, `tools/e_seq_verify.py`) where present.

## Per company (three dimensions kept separate)

| Symbol | (1) Numeric correctness | (2) Document completeness | (3) Company coverage |
|---|---|---|---|
| 3002 Najran | verified_correct 106/106 facts, 0 mismatches, 0 numeric defects | 1 doc (FY2025 FS, SAR 000). BS/P&L/CF eyeballed; OCI page text-layer only. Missing: weighted shares, PPE-sale proceeds, employee-benefits paid | THIN: FY2025 + FY2024 comparatives only |
| 3003 City | verified_correct 111/111, 0 mismatches. CF cash vs BS cash differs by exactly 100,000,000: proven genuine (Note 15, 90-day deposits) | 1 doc. BS/P&L/CF eyeballed (image-only). Missing: weighted shares, OCI components | THIN |
| 3005 Umm Al-Qura | verified_correct 105/105, 0 mismatches | 1 doc (standalone). BS/P&L/CF eyeballed. Missing: weighted shares, employee-benefits paid | THIN |
| 3020 Yamama | verified_correct 114/114 values, but 2 DEFECTS (classification/definition, see below) | 1 doc (standalone). BS and CF eyeballed; P&L via digital text + arithmetic (FY2024 P&L column not eyeballed). Missing, present in source: debt_issued, debt_repaid, lease_payments, weighted shares | THIN |
| 3040 Qassim | verified_correct 120/120, 0 mismatches. FY2024 comparatives are the RESTATED figures (Note 37), labelled as such | 1 doc. BS/P&L/CF eyeballed; Note 37/36 read. Missing: weighted shares, investing detail | THIN |

Coverage honestly: each company has exactly ONE published manifest (FY2025 annual, with FY2024 only as comparatives).
No quarterly, interim, or pre-2024 data exists for any of them. Whether Saudi Exchange offers more was not checked
(no network use). "Verified" below applies only to what is published; nothing is claimed about completeness of the
company's history.

## Proven defects (page + line evidence)

* **AUDIT-E-3020-1 (low, classification).** Yamama `impairment_charges` FY2025 = -51,987,657 sums two lines on opposite sides of
  operating income. P&L printed p6 (pdf p8): 'Provision for expected credit loss (ECL)' (20,185,882) is above 'Income from
  main activities'; 'Provision for impairment of spare parts for Plants and equipment' (31,801,775) is under 'Other
  (expenses)/income'. Both bridges re-add exactly to 418,694,182 and 495,877,524. Operating income itself is correct.
* **AUDIT-E-3020-2 (low, definition).** Yamama `capex` omits 'Purchase of Intangible assets' (294,281 / 1,470,413; CF p8) while
  City (2024) and Qassim include intangibles.
* **AUDIT-E-META-1 (medium-low, metadata, all five).** `filed_at` = Board approval date, earlier than the Saudi Exchange
  publication timestamp in `source_url` (3002: 2026-03-29 vs 2026-04-06, which is also before the 6 April audit opinion).
  11 of 12 fsPdf manifests in `data/imports` show this (`tools/e_filed_at_check.py`). `filed_at` drives fact ranking and
  as-of logic, so facts look known days before the audited document was public.
* No numeric (value, sign, scale, period) defect was found in any of the 556 published facts.

Not defects (documented): depreciation_amortization stored negative while the add-back is printed positive (repo
convention, engine uses abs); Qassim FY2024 restated; Qassim FY2024 includes Hail Cement only from 10 June 2024
(not like-for-like growth); City `short_term_investments` (146m time deposit) overlaps the 100m that the cash-flow
statement counts as cash equivalents; stray 'k' in Qassim manifest notes; archive/manifest notes call Yamama and Najran
statement pages "scanned" although a matching text layer exists.

## Shared root causes and fixes (nothing applied to data/**; Codex to publish)

1. `filed_at` semantics (AUDIT-E-META-1): derive from the URL publication timestamp / audit-report date. Offline test
   `tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication` (strict xfail, flips to a failure once fixed so
   the xfail marker must then be removed).
2. Composite facts must not straddle operating income (3020) and capex definition should be one policy (intangibles in or out).
3. Manifest completeness: weighted average shares absent in all five; Yamama debt/lease cash-flow lines absent.

## Tests run

`python -m pytest tests/test_audit_batch2_e_cement.py -q` -> 7 passed, 5 xfailed (pins every published fact of the five
manifests to the page transcriptions; parser unit tests; documented filed_at defect). Existing
`tests/test_cement_sector_batch*.py` run unchanged (see report message).

## Unverified / limits

* Equity statement pages and notes (except Notes 15 (3003), 36/37 (3040)) not checked; statement of changes in equity
  has no carried facts.
* Najran OCI page (pdf p10) and Yamama P&L (pdf p8) were verified through the text layer and arithmetic, not by eye.
* Transcriptions are my own reading of renders at ~1.3-1.4x with subtotal re-addition as the guard; a transposed
  digit that preserves all subtotals is not excluded for non-summed lines.
* Earlier/interim filings for these symbols were not looked for online.
