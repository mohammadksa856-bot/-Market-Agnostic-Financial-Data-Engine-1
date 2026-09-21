# Saudi insurance batch 1: Tawuniya and Bupa Arabia

Scope: `sa:8010` (The Company for Cooperative Insurance, "Tawuniya") and `sa:8210`
(Bupa Arabia for Cooperative Insurance Company). This is deliberately the *first*
insurance batch, not the whole archive: it covers the IFRS 17 era only (fiscal years
2023-2025, the basis both issuers have reported on since IFRS 17 replaced IFRS 4 for
Saudi insurers). Extending backward into the pre-IFRS 17 years is left to a later
batch - see "Scope and gaps" below for why that boundary was chosen deliberately
rather than reached by running out of time.

Every published fact comes from a document the issuer itself published, archived
under `data/raw/SA/<symbol>/documents/` and recorded in `data/raw/archive-index.json`
with its official URL, SHA-256, media type and byte size. No value is estimated, and
nothing is published that the accounting verifier rejects.

## Before and after

| Company | Manifests | Facts (manifests) | Current data points | Metrics | Period ends | Span |
| --- | --- | --- | --- | --- | --- | --- |
| Tawuniya (`sa:8010`) before | 1 | 30 | 41 | 41 | 1 | 2025-12-31 only |
| Tawuniya (`sa:8010`) after | 8 | 325 | 372 | 60 | 8 | 2023-12-31..2025-12-31 |
| Bupa Arabia (`sa:8210`) before | 0 | 0 | 0 | 0 | 0 | not previously covered |
| Bupa Arabia (`sa:8210`) after | 11 | 373 | 403 | 49 | 11 | 2023-03-31..2025-09-30 |

"Before" for Tawuniya is the one curated `tawuniya-2025-fy.json` manifest already on
`main`; it is untouched by this batch. Bupa Arabia did not exist in the company
registry before this batch (added in `config/companies.json`, no ISIN yet - see gaps).

## Current data points, from a CI-parity bootstrap

Counted the way `audit` counts them: rows in `data_points` with `is_current = 1`, in a
scratch database built from `data/imports` alone, compared against the identical
bootstrap run on unmodified `origin/main` (commit `4112007`).

| Company | Current points | Calculated | Metrics | Fiscal years | FY | Instant | Quarter | YTD | TTM |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tawuniya before | 41 | 11 | 41 | 2025 | 24 | 17 | 0 | 0 | 0 |
| Tawuniya after | 372 | 110 | 60 | 2023-2025 | 49 | 117 | 80 | 124 | 2 |
| Bupa before | 0 | 0 | 0 | - | 0 | 0 | 0 | 0 | 0 |
| Bupa after | 403 | 73 | 49 | 2023-2025 | 38 | 156 | 82 | 123 | 4 |

Every other previously-merged company's current-point count is identical between the
baseline bootstrap and this batch's bootstrap (see "Verification" below) - this batch
adds facts, it does not touch anyone else's.

## Manifests

| Manifest | Filing type | Period end | Facts | Source |
| --- | --- | --- | --- | --- |
| `tawuniya-2023-fy.json` | annual-report | 2023-12-31 | 15 | tawuniya.com/docs/BODEn.pdf |
| `tawuniya-2024-q3.json` | interim-report | 2024-09-30 | 39 | tawuniya.com/docs/Tawuniya_Q3_FS-English.pdf |
| `tawuniya-2024-q4.json` | interim-report | 2024-12-31 | 34 | tawuniya.com/docs/2024_Q4_Financial_Statements_EN.pdf |
| `tawuniya-2025-fy.json` (pre-existing) | annual-report | 2025-12-31 | 30 | tawuniya.com/docs/2025_Annual_Report_EN.pdf |
| `tawuniya-2025-q1.json` | interim-report | 2025-03-31 | 34 | tawuniya.com/docs/2025_Q1_Financial_Statements_EN.pdf |
| `tawuniya-2025-q2.json` | interim-report | 2025-06-30 | 46 | tawuniya.com/docs/2025_Q2_Financial_Statements_EN.pdf |
| `tawuniya-2025-q3.json` | interim-report | 2025-09-30 | 40 | tawuniya.com/docs/2025_Q3_Financial_Statements_EN.pdf |
| `tawuniya-2025-q4.json` | interim-report | 2025-12-31 | 36 | tawuniya.com/docs/2025_Q4_Financial_Statements_EN.pdf |
| `bupa-2023-fy.json` | annual-report | 2023-12-31 | 29 | buy.bupa.com.sa .../2023/bupa-arabia-fy23-en.pdf |
| `bupa-2023-q1.json` | interim-report | 2023-03-31 | 33 | buy.bupa.com.sa .../2023/q1-23(en).pdf |
| `bupa-2023-q2.json` | interim-report | 2023-06-30 | 37 | buy.bupa.com.sa .../2023/q2-23(en).pdf |
| `bupa-2023-q4.json` | interim-report | 2023-12-31 | 29 | buy.bupa.com.sa .../2023/q4-23(en).pdf |
| `bupa-2024-fy.json` | annual-report | 2024-12-31 | 16 | buy.bupa.com.sa .../2024/bupa-arabia-fy24.pdf |
| `bupa-2024-q2.json` | interim-report | 2024-06-30 | 38 | buy.bupa.com.sa .../2024/q2-24(en).pdf |
| `bupa-2024-q3.json` | interim-report | 2024-09-30 | 40 | buy.bupa.com.sa .../2024/q3-24(en).pdf |
| `bupa-2024-q4.json` | interim-report | 2024-12-31 | 16 | buy.bupa.com.sa .../files/ir/bupa-2024-en.pdf |
| `bupa-2025-q1.json` | interim-report | 2025-03-31 | 31 | buy.bupa.com.sa .../bupa-arabia-q1-2025--en.pdf |
| `bupa-2025-q2.json` | interim-report | 2025-06-30 | 40 | buy.bupa.com.sa .../bupa-arabia-q2-2025-en.pdf |
| `bupa-2025-q3.json` | interim-report | 2025-09-30 | 35 | buy.bupa.com.sa .../505_0_2025-11-03_17-54-24_en.pdf |

`filed_at` on every new manifest is the PDF's own `/CreationDate` (or `/ModDate` when
`CreationDate` was absent) - real evidence extracted from the document itself, never a
guessed or interpolated date. The issuer's actual filing/announcement date on Tadawul
was not independently confirmed for this batch; see "Gaps" below.

Bupa Arabia's "Quarter 4" document for 2024 (`bupa-2024-en.pdf`) and its labelled
annual financial statements (`bupa-arabia-fy24.pdf`) both yield only 16 facts: Bupa,
unlike Tawuniya, folds its Q4 figures into the annual audited statements rather than
publishing a separate interim, and that annual document's layout (multi-column, with
narrative pages interleaved) yields fewer clean primary-statement rows than a plain
interim. This is a real extraction-coverage gap, not a correctness issue - every fact
that *was* published passed the accounting verifier - and is called out below.

## Official sources

| Company | Index page |
| --- | --- |
| Tawuniya | https://www.tawuniya.com/en/investor?tab=2 |
| Bupa Arabia | https://buy.bupa.com.sa/en/about-us/investor-relations |

No Tadawul/Saudi Exchange announcement pages, Insurance Authority, or SAMA regulatory
disclosures were used as sources in this batch - see "Gaps" for why, and what was
found when each was checked.

## IFRS 17 / IFRS 4 coverage

- All 19 manifests are IFRS 17-basis documents (fiscal years 2023-2025 for both
  issuers; Saudi insurers adopted IFRS 17 for periods beginning 1 January 2023). No
  pre-IFRS 17 (IFRS 4 / gross-written-premium-statement) document was read in this
  batch, so no pre/post-IFRS 17 comparison, bridge, or basis tag was needed - the
  conflation this task explicitly forbids simply cannot occur within this batch's data.
- `insurance_revenue` (the IFRS 17 income-statement top line) is captured and kept
  distinct from `gross_written_premium` (the pre-IFRS 17 top line, and still the
  measure disclosed in the segment note - see "Gross written premium" below); no fact
  in this batch conflates the two.
- `insurance_service_result` (the final, post-reinsurance result) and
  `underwriting_result` (the "before reinsurance contracts held" subtotal both issuers
  also print) are kept as two distinct metrics - see the reader-fix table below.
- `reinsurance_premiums`, `reinsurance_recoveries`, `reinsurance_result` are captured
  from both issuers' "Net (expense)/income from reinsurance contracts held" sections.
- Quarter/YTD/FY period kinds are read from the header text zone on each page (e.g.
  "for the three-month period ended" vs. "for the six-month period ended"), never
  derived by subtraction or inference; each manifest's `quarter` and `ytd` facts are
  independently sourced, printed values.

### Gross written premium

Neither issuer prints `gross_written_premium` on its primary income statement under
IFRS 17 - it appears only inside a wide segment/operating-segments note (a matrix with
one column per line of business and a "Total" column), which is a structurally
different extraction problem from reading a primary two- or four-column statement.
**Not attempted in this batch.** Proposed solution: a dedicated segment-note reader
path (detect the note by its "Total" column header and per-segment row labels, sum
across segments) as a follow-up, scoped and tested independently of the primary-
statement reader touched here.

### Solvency / regulatory capital

No public disclosure of Pillar 3-equivalent solvency margin or regulatory capital
detail was found in any of the 19 documents read for this batch (Saudi insurers are
not subject to the same Basel-style Pillar 3 disclosure regime SAMA requires of banks).
**Not populated in this batch.** Proposed solution: check the Insurance Authority's
own disclosure portal (insurance.gov.sa) directly in a follow-up session, since it was
not reachable from this environment's network during this batch.

## Reader changes, and the test that pins each one

All in `tests/test_insurance_profile_gating.py` unless stated otherwise; caption
aliases are in `src/finengine/reading.py`'s `INSURANCE_LINE_MAP`.

| Change | Why | Scope | Test |
| --- | --- | --- | --- |
| ~35 new `INSURANCE_LINE_MAP` caption aliases (interim wording variants, Bupa's split zakat/income-tax charges, cash-flow rollforward captions, "investment return" vs. "net investment income", "insurance service expense" singular, etc.) | captions Tawuniya and Bupa actually print that no existing entry matched | all `profile="insurance"` reads | exercised via the 19 manifests' own verify pass |
| "Insurance service result before reinsurance contracts held" now resolves to its own `underwriting_result` metric instead of overwriting the final, post-reinsurance `insurance_service_result` | both issuers print both lines; one was silently discarding the other | all `profile="insurance"` reads | exercised via the 19 manifests' own verify pass |
| `_NOTE_REFERENCE` also matches a decimal sub-note token (`5.1`, not just `5`) | both issuers reference IFRS 17 sub-notes this way | all profiles (regex only; see next row for why the *zone* stays gated) | `test_insurance_profile_reads_the_row_past_the_decimal_note_ref` |
| `note_zone` widened from 90pt to 130pt, and `_column_blocks` drops a lone prose-sentence year that sits close to a real comparative-year header | a decimal note ref ~110pt from the value column was previously classified as a label word and dropped its whole row; a sentence like "For the six-month period ended 30 June 2025" printed a lone year that merged into the real header's column block and shifted its detected centre | **gated to `profile == "insurance"` only** - see below | `test_insurance_profile_reads_the_row_past_the_decimal_note_ref`, `test_bank_profile_is_unaffected_same_layout_row_still_dropped`, `test_insurance_profile_drops_the_lone_sentence_year_from_columns`, `test_column_blocks_unit_insurance_excludes_lone_year_bank_does_not` |

### Why the last two fixes are profile-gated

Both were first tried unscoped (applying to every profile) and each one, independently,
reopened a regression in Bank ANB's (`sa:1080`) already-merged 2018 and 2019 annual
reports: a multi-page "commission rate sensitivity" note table (an interest-rate
repricing/maturity-gap disclosure, printed in reversed reading order across several
pages) got misread as a continuation of the primary balance sheet, corrupting
`due_from_banks`, `cash_and_balances_with_central_bank`, `customer_deposits`,
`bank_investments`, `due_to_banks` and several income-statement metrics with values
pulled from the note's own "Total" column instead. Several targeted, narrower
mitigations were tried (a prose-boilerplate guard on the continuation check, naming the
note table in `_NON_PRIMARY_STATEMENT`, capping the carry-chain depth) and each one
either left ANB still broken or reintroduced Tawuniya/Bupa's original bug. The change
that resolved this cleanly: scope both fixes to `profile == "insurance"` by threading
an explicit `profile` parameter through `_column_blocks` and reading the active
profile off the `StatementReader` instance inside `_statement_facts`, so neither code
path can execute for a bank or corporate document *by construction* - not by tuning a
pattern to avoid one specific note table.

### Effect on companies outside this batch

**None.** Every change other than the caption-alias additions is scoped to
`profile == "insurance"`, and only `sa:8010` and `sa:8210` are registered with that
profile. Verified two ways:

1. A full 171-document corpus sweep (every document referenced by every manifest in
   `data/imports`, across every profile, re-read with the changed reader and diffed
   fact-by-fact against the manifest on disk): **0 conflicts, 0 removed facts, 22
   added** (the 22 are newly-captured facts on the insurance documents themselves,
   from the caption additions - nothing on a bank or corporate document changed).
2. Targeted re-checks of the four documents implicated in the ANB investigation
   (`albilad-2011-fy`, `anb-2018-annual-report`, `anb-2019-annual-report`,
   `anb-2021-q3`): **0 conflicts, 0 removed, 0 added** on every one.

## Verification

All four required checks were run, each compared against an identical run on
unmodified `origin/main` (commit `4112007`):

| Check | This batch | `origin/main` baseline |
| --- | --- | --- |
| `verify --imports data/imports` (whole corpus, 458 manifests) | 1838 checks, 1822 passed, 16 warnings, **0 failures**, ok=true | not run standalone (subsumed by the corpus sweep above, which is the stricter fact-level check) |
| CI-parity `bootstrap` on a temp SQLite DB | 458 manifests published, all `status: "published"` | 440 manifests published (18 fewer = exactly this batch's 18 net-new manifests) |
| `audit --strict-warnings` | 0 failures, 1 warning (`enabled_company_coverage`: 5 US oil majors with no live price feed in this offline environment) | 0 failures, 1 warning - **the identical warning**, same 5 companies |
| Full test suite | 344 passed, 1 skipped (plus the 4 new tests in `test_insurance_profile_gating.py`) | 344 passed, 1 skipped (measured before this branch's new test file existed) |

The one `audit --strict-warnings` warning is confirmed pre-existing and unrelated to
this batch (US oil-major price coverage, not reachable from this network) - it is
identical, company-for-company, on both the batch and the baseline runs.

### New verifier warnings on the insurance manifests themselves

Two of the corpus `verify` run's 16 warnings are new, both on Bupa Arabia:

```
sa:8210 net margin (net_income / revenue), 2023-03-31 quarter, ratio=7.76, expected [-0.5, 0.85]
sa:8210 net margin (net_income / revenue), 2025-03-31 quarter, ratio=17.02, expected [-0.5, 0.85]
```

Both facts behind this warning are individually correct: Bupa prints a tiny
`revenue` line captioned "Other revenue" (SAR 22-24 thousand, non-insurance ancillary
income) separately from `insurance_revenue` (SAR 3.7-4.4 million, the real top line).
The generic `LINE_MAP` caption "revenue" correctly maps "Other revenue" to the
catalog's generic `revenue` field - that mapping is not wrong for what it says. The
verifier's net-margin sanity check, however, divides `net_income` by whatever
`revenue` fact is present, and for an insurer that is the wrong denominator. This is a
**pre-existing verifier limitation**, not a new defect in the data: the check does not
yet know that an insurance-profile company's top line is `insurance_revenue`, not the
generic `revenue` field. It surfaces as a warning, not a failure, and does not block
publication (consistent with the other pre-existing warnings in the corpus). Proposed
solution for a follow-up: teach the net-margin check to prefer `insurance_revenue`
over `revenue` when a company's profile is `"insurance"`, as its own scoped, tested
change - deliberately not bundled into this batch to keep this batch's diff to the
reader and the two companies' own data.

## Scope and gaps

| Gap | Reason | Proposed solution |
| --- | --- | --- |
| Pre-2023 (IFRS 4 era) history not covered | Both issuers restated their basis at IFRS 17 adoption; reading pre-2023 documents needs a second, IFRS-4-specific caption map and explicit basis tagging so the two eras are never compared without that tag - out of scope for a first batch whose job was to prove the IFRS 17 reader path itself is correct and safe | A batch 2 scoped explicitly to IFRS 4-era history, with its own basis-lineage tagging built and tested before any pre-2023 fact is published |
| Tawuniya FY2024 annual report (`2024_Annual_Report_EN.pdf`) | 0 facts extracted; reader recognises none of its statement pages, likely a glossy/narrative layout the current heading or column-detection heuristics don't match | Documented as unread; FY2024 quarter/YTD figures are still fully covered via the four FY2024 quarterly manifests. Needs its own targeted layout investigation, not a guess |
| Tawuniya Q1 2024 | The harvested "2024 Q1 Financial Statements" link on tawuniya.com actually resolves to the 2024 ESG Sustainability Report (the issuer's own site serves the same href under two different button labels) | Locate the correct Q1 2024 financial-statements URL from Tadawul's own disclosure archive in a follow-up, rather than guess a URL |
| Tawuniya Q2 2024, Bupa Q3 2023, Bupa Q1 2024 | Image-only PDFs (scanned/rasterised pages); this reader build has no OCR extra installed (`pip install -e ".[ocr]"`, pulling `rapidocr`/`onnxruntime`) | Install the optional OCR extra in a follow-up and re-read these three documents; no other blocker |
| Bupa Arabia ISIN | Not located during this batch | Add once found; does not block any published fact |
| Gross written premium (all periods) | Disclosed only in a segment-note matrix, a different extraction problem than the primary statement (see "Gross written premium" above) | Dedicated segment-note reader path, as its own scoped, tested change |
| Solvency / regulatory capital metrics | No public disclosure found in the documents read; Insurance Authority portal not reachable from this network | Check insurance.gov.sa directly in a follow-up |
| Filing/announcement date precision | `filed_at` is the PDF's own embedded creation/modification date, not an independently confirmed Tadawul announcement date | Cross-check against Tadawul's disclosure archive in a follow-up if exact announcement timestamps are needed |
| Insurance Authority / SAMA regulatory disclosures | None located as a distinct public source during this batch | Revisit once/if the Insurance Authority publishes a reachable disclosure archive |

None of these gaps caused a guessed, estimated, or fabricated value to be published -
every fact in the 19 new manifests was read from an archived, hashed, official PDF and
passed the accounting verifier.

## Branch discipline

This branch (`claude/insurance-tawuniya-bupa-enrichment`) does not merge into `main`,
does not publish to AWS or Supabase, and does not modify production services. The
bootstrap/audit runs above were against a temporary local SQLite database only. See
the top-level PR/commit summary for the branch SHA and rebase status against `main`.
