# Batch 2 / Group F independent audit: 3060 (Yanbu Cement), 7202 (solutions by stc)

Audited: `origin/codex/telecom-95pct` @ `ec610f3`. One manifest each (`yanbu-cement-2025-fy.json`, `stc-solutions-2025-fy.json`).
Source PDFs are on the audited branch under `data/raw/SA/<symbol>/documents`; SHA-256 re-computed and equal to
`data/raw/archive-index.json`. No data/**, AWS, Supabase or other branch was changed. 1050/1060 not touched.

Method: every printed statement page rendered and read by eye (3060 statements are born-digital, 7202 P&L/OCI/BS are
scanned); values transcribed independently (`tools/f_transcripts/*.json`, page + line item) and compared with every published fact
(`tools/f_compare.py`); composites re-added; text layer as second reader (`tools/f_textlayer_check.py`); notes read for
restatements, approval date, audit-report date.

## Per company (three dimensions kept separate)

| Symbol | (1) Numeric correctness | (2) Document completeness | (3) Company coverage |
|---|---|---|---|
| 3060 Yanbu | verified_correct 118/118 facts, 0 mismatches (FY2024 = restated comparatives, Note 40, disclosed) | 1 doc, all 5 statements present, BS fully extracted. Missing printed items: OCI component, basic EPS fact, employee benefits paid, FVTPL flows, equity statement, notes | THIN: FY2025 + FY2024 comparatives only; no quarters, no history, no original FY2024 |
| 7202 solutions by stc | verified_correct 128/128, 0 mismatches (scale 1000 correct). FY2024 BS comparatives are PPA-adjusted (Note 43) and this is undisclosed | 1 doc, all statements present, BS fully extracted. Missing: basic EPS 12.62/13.42, OCI components/attribution, cash-flow detail, equity statement | THIN: same |

No numeric (value, sign, scale, period) defect was found in any of the 246 published facts.

## Proven defects

* **F-3060-1 (low, provenance).** Manifest notes, reader tag, archive-index capture_method and `docs/data/cement-sector-batch2.md`
  call the statements scanned. PDF pp6-10 (the five statements) have a full text layer; only the auditor's report (pp3-5) is scanned.
* **F-3060-2 / F-7202-2 (medium-low, filed_at).** `filed_at` is the Board approval date. 3060: 2026-03-03 (Note 41, p46) vs audit report
  11 March 2026 (p5) and file stamp 2026-03-11. 7202: 2026-02-15 (Note 45, p64) vs Deloitte report 19 February 2026 (p8) and file
  stamp 2026-02-23. Same root cause as AUDIT-E-META-1 (cement batch).
* **F-7202-1 (low-medium, undisclosed adjusted comparatives).** FY2024 balance-sheet comparatives were adjusted for the LABS purchase
  price allocation (Note 43, PDF p64): intangibles 557,229 -> 559,813, trade payables/accruals 3,886,613 -> 3,885,729,
  NCI 22,034 -> 25,502 (SAR 000). Published FY2024 values equal the adjusted figures (correct as printed) but the manifest notes never say so,
  unlike 3060 which flags its Note 40 restatement.
* **F-3060-3 / F-7202-3 (low, missing fields).** Basic EPS (7202: 12.62/13.42; 3060 printed as "Basic and diluted" 0.66/1.00),
  OCI components, cash-flow detail lines.
* **F-3060-4 / F-7202-4 (medium, coverage).** Only FY2025 (+ comparatives).
* Info: fact.page is the printed page (PDF page - 2) in both manifests; 7202 `accounts_payable` is the broader
  "Trade payables, accruals and other liabilities" line.

Not defects: D&A stored negative (repo convention); 3060 FY2024 capex includes 6,634,550 carbon credits moved to investing by Note 40;
7202 operating cash flow FY2025 genuinely negative (-100,669, printed).

## Shared root causes and fixes (nothing applied to data/**; Codex to publish)

1. `filed_at` semantics (also seen in batch 2-E): derive from the publication timestamp/audit-report date. Test
   `tests/test_audit_batch2_f_3060_7202.py::test_filed_at_not_before_publication` (strict xfail for both).
2. Manifest notes must disclose adjusted/restated comparatives (7202 Note 43). Test `test_7202_notes_disclose_comparative_adjustment` (strict xfail).
3. Provenance descriptions (scanned vs digital) should be derived from the text layer, not assumed.
4. Completeness: basic EPS and OCI/cash-flow detail.

## Tests run

`python -m pytest tests/test_audit_batch2_f_3060_7202.py -q` -> 4 passed, 3 xfailed (transcription pin of every published fact,
subtotal/cash reconciliation, 2 filed_at defects, 1 disclosure defect).

## Unverified / limits

* Equity statements and notes (except Notes 40/41, 43/44/45, 40 segments) not checked line by line; no facts are carried from them.
* Transcriptions are my own reading at 1.5-1.8x with subtotal re-addition and the text layer (3060 all pages, 7202 cash flow) as guards;
  7202 P&L/OCI/BS rely on eyeballing plus subtotal re-addition only (scanned). A transposed digit preserving every subtotal on a
  non-summed line is not excluded for those three pages.
* Rejected facts: no rejected files in the repo; the production rejected-fact registry was out of bounds -> unverified.
* Earlier/interim filings, price history and the originally filed FY2024 statements were not looked for (no network).
