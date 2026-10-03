# Independent audit - Saudi batch 1, group C (7020, 7010, 7030, 7040, 7203)

Auditor: Claude Sonnet 5.5 (independent). Date: 2026-10-03. Read-only with respect to data: no edit to `data/raw/**`, `data/imports/**`
or any earlier audit file; no AWS, no Supabase, no network.

**Audited version.** `origin/codex/telecom-95pct` at `ec610f3` (newest lineage of the telecom manifests). `origin/claude/telecom-shared-gap-closers`
(`a8245ac`) forks at `3980d36` and holds older copies of four stc/Zain manifests; its Mobily, Zain FY2025 and GO manifests are byte-identical, and
`origin/claude/data-tech-1` has an identical Elm manifest. Raw market archives that exist only on the shared-gap-closers branch were read with `git show`.
All 26 archived source PDFs were re-hashed: every SHA-256 equals `data/raw/archive-index.json`.

**Method.** Scanned statement pages were rendered and read line by line (both columns). Digital pages were read from the text layer. Every "correct"
and every "defect" below is tied to a page and line item in the per-company JSON. Internal arithmetic was used only as a secondary check.
Per-company, resumable records: `7010.json`, `7020.json`, `7030.json`, `7040.json`, `7203.json` (each source has `status: done|pending`).
Machine scan of every fact against its cited page: `batch1-C-provenance-scan.json`.

## Per-company status (three dimensions, never blended)

| Symbol | Numeric correctness | Document completeness | Company coverage |
|---|---|---|---|
| 7010 stc | **defective** - FY2025/FY2024 statements 123/123 verified_correct, five-year history 36/36 verified, notes 61/64; 4 proven value/scale defects; 51 quarterly/H1-2026 facts unverified (sources not archived) | **defective** - ~30 FY2024 comparative lines, ~12 printed lines and the equity statement not extracted | **partial** - FY2020-FY2025 (subset before 2024), 12 quarters (3 metrics), H1-2026 ytd; no 2019 and earlier, no Q1-2026 |
| 7020 Mobily | **defective** - 48+70+11 FY2025 facts, FY2021/23/24 headlines and 36 quarterly facts verified; 1 proven defect (FY2022 EBITDA mixed vintage) | **defective** - FY2024 column and equity statement of the FY2025 report not extracted; FY2021-24 only 3 headline metrics although full statements are in the archived reports | **partial** - FY2021-24 headlines, FY2025 full, Q1-Q3 2021-2024; no Q4, no 2025/2026 quarters, no pre-2021 |
| 7030 Zain KSA | **defective** - FS 86/86 verified_correct, notes 99/104; defects are labelling/derivation (scope tag, derived revenue split, 0-encoded sentence, per-share amount in total-amount field); 36 quarterly facts unverified | **defective** - ECL, associate loss, tower gain, grant income, comprehensive income, OCI, hedging reserve, equity statement, FY2024 cash-flow detail not in the primary manifest | **partial** - SAR FY2024-FY2025 only; FY2021-23 only as USD group-report headlines; 12 quarters unverified |
| 7040 GO | **defective (minor)** - 65/66 verified_correct against the Board report (an "over 30%" bound stored as exact); 26 quarterly facts unverified | **defective** - archived document is a Board report, not the audited statements; many rows printed in its five-year tables are not extracted | **partial** - FY2021-FY2025 (March year-end), 12 quarters, FY2026-Q1; no FY2026 audited year |
| 7203 Elm | **verified_correct** - 136/136 facts of the one manifest; | **defective** - basic EPS, OCI, cash-flow detail, equity statement not extracted | **defective** - FY2025 + FY2024 comparatives only; nothing else in the repo |

Totals: 961 published facts in 5 symbols across 53 manifests (+4 price-history manifests). 113 facts (stc 51, Zain 36, GO 26) cannot be
verified because their source documents are not archived (listed in the JSON as `pending`). 36 more stc facts have no archived URL but were
verified against the identical tables in the archived AR2024 PDF. **Rejected facts:** no rejected/excluded records exist in the repo for these
symbols; the production registry was out of bounds - unverified.

## Proven defects (page / line evidence in the JSON)

| ID | Sev | Defect (published -> correct) |
|---|---|---|
| C-7010-01 | high | stc `customer_concentration` 11298000 scale 1 (SAR 11.3 m) -> scale 1000 (SAR 11,298 m): AR2025 PDF p128 "approximately SAR 11,298 million" |
| C-7010-02 | high | stc `employee_benefit_expense` 631000 scale 1 -> scale 1000: AR2025 p141 "SAR 631 million" |
| C-7010-03 | high | stc `ppe_additions_by_class` 8,279,660 (this is Lands & buildings NBV) -> 8,235,137 total additions: AR2025 p129 Note 10 |
| C-7010-04 | med | stc FY2025 wired broadband 1.3 m (Q4-24 column) -> 1.4 m: AR2025 PDF p38 chart |
| C-7010-06 | med | stc 2023 quarters (pre-restatement deck, sum 72.34 bn) vs FY2023 restated 71.777 bn: +0.78%; AR2024 p73 footnote |
| C-7020-01 | med | Mobily FY2022 EBITDA 6,179 -> 6,161 (AR2022 p4, p22); 6,179 is the AR2023 restated comparative mixed with original revenue 15,669 |
| C-7030-01 | med | Zain entity-segment assets 57.6 bn / liabilities 46.97 bn / D&A 2,153,794 tagged scope=consolidated (consolidated: 28,753,303 / 17,877,352 / 2,160,661); PDF p69-70 |
| C-7030-02 | med | Zain `revenue_by_geography` 9,338,850 is not printed anywhere (only "14.97%"); PDF p52 |
| C-7030-03 | low | Zain sentence "no customer >=10%" stored as numeric 0 |
| C-7030-04 | med | Zain 4 dividend actions store DPS 0.5 in `cash_amount` (all other 22 actions in the repo store the total) |
| C-7030-05 | med | Zain FY2021-23 USD history cites AR2023 p46/p48; values are on AR2023 p17, AR2021 p23, AR2022 p20; USD facts of a SAR issuer under plain metric names |
| C-7040-01/02 | med/low | GO multi-year rows not extracted; "over 30%" 5G stored as 0.30 |
| C-7203-01/02 | low | Elm basic EPS (26.86 / 23.51) missing; page references are printed pages (PDF +2) |
| C-7010-05, C-7020-02 | low | wrong or other-document page references (stc 12+1+KPIs; Mobily FY2022/FY2023/Q1-2023 and 80 facts beyond the PDF length) |

Unverified: C-7010-07 (stc 2024 quarters vs FY, -0.07%), C-7010-08 (stc H1-2026: archived file missing), C-7030-07 (Zain quarters), C-7040-04
(GO FY2025 quarterly net profit -0.63% vs FY).

## Shared root causes

* **RC1 - no source-fidelity gate.** `ManifestVerifier` proves identities and ratio bounds only; all five issuers pass it (stc 56 pass/1 warn, Mobily 26/0, Zain 35/1, GO 18/0, Elm 24/0) while carrying 1000x scale errors, a wrong-column value and mixed vintages. Fixed generally by `manifest_audit.py` (below).
* **RC2 - three page-numbering conventions** (PDF page, printed page, printed spread) used inside single manifests; offsets: Elm +2, Mobily deep notes (printed+2)/2, Zain notes +1, stc segments mixed.
* **RC3 - comparatives and non-headline rows not extracted** (every company): the prior-year column and many printed lines exist in the same table.
* **RC4 - original vs restated vintages mixed** (stc 2023 quarters vs FY2023; Mobily FY2022; Zain FY2022 USD; stc FY2024 comparatives differ from the original AR2024 by a 25,514 reclassification). No basis flag on facts.
* **RC5 - amounts printed as "N million/billion" stored with the table scale** (stc). The PDF text layer also renders the SAR sign as `$`, `&` or `%`; a reader must not map `$` to USD for these documents.
* **RC6 - derived or qualitative values stored as numeric facts** (Zain 9,338,850 and 0; GO ">30%"; stc "over 3.58 m").
* **RC7 - field/scope semantics differ by issuer** (Zain `cash_amount`; scope tags on entity segments).
* **RC8 - source not archived** for 12 manifests (stc decks, stc H1-2026 file missing, Zain/GO exchange announcements).

## Fixes prepared on this branch (isolated; no published number edited)

* `src/finengine/manifest_audit.py` - offline provenance check of a manifest against archived page text (`ok`, `page_offset`, `wrong_page`,
  `scale_suspect`, `image_page`, `page_out_of_range`, `not_found`) with a dominant-offset detector, plus `quarters_vs_fiscal_year` (four discrete
  quarters vs the annual figure, 0.4% default tolerance). It reproduces C-7010-01/02 (`scale_suspect`) and C-7010-06 / C-7040-04 from real data.
* `scripts/audit_manifest_provenance.py` - read-only CLI that runs it over all manifests of chosen companies using `archive-index.json`.
* `tests/test_manifest_audit.py` - 14 offline unit tests (synthetic page text; Arabic digits, scale suspects, millions-vs-thousands tables, scanned pages, quarter sums).
* Corrections for Codex to publish are specified in the findings' `fix` fields (scale -> 1000, value 8235137, wired broadband 1,400,000, EBITDA 6,161, scope -> segment, cash_amount total, page numbers); none was applied.

Tests run: `tests/test_manifest_audit.py` (14 passed); with `test_verification.py`, `test_manifest_vintages.py`, `test_telecom_sector.py`,
`test_telecom_shared_infrastructure.py`, `test_tech_sector_batch1.py`: 73 passed, 12 subtests passed.

## Limits of this audit

* Scanned statements (stc, Zain, Elm) were verified by reading rendered images, not OCR; the scale/sign/column conclusions are from the printed pages.
* Qualitative profile attributes (governance, ESG, board) were sampled only; numeric/identity items in them were verified.
* Price histories: only the windows present in the raw archives on the shared-gap-closers branch (2021-2026 / 2024-2026) were compared (all rows equal); earlier rows are unverified.
* Chart/infographic KPIs were read visually; the machine scan cannot match values printed as "28.34 million" and reports them `not_found` (checked manually instead).
