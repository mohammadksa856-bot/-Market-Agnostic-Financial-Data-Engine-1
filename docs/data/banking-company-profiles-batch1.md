# Saudi banking sector — company-profile pilot batch 1

Batch branch: `claude/data-banking-profiles-1` (branched from `origin/main` @
`64964c6`). This batch adds the qualitative/operational/segment/risk layer
that the existing financial-statement manifests do not cover — it is
additive to, not a replacement of, `alrajhi-2025-fy.json` and
`alrajhi-supplement.json` (already on `main`, pure financial-statement
data). No engine/catalog change touches any existing field's meaning.

## Why this batch exists

A full site-schema vs. engine-catalog audit (cross-referencing the
`pixel-perfect-showcase-276` site's `Company` TypeScript type against all
1,047 engine catalog fields) found that the engine's `company_model`,
`disclosures`, `segments` and "operational KPI" categories were designed
but essentially unpopulated for every company except Aramco and SABIC.
This batch proves the same discipline used for financial statements
(primary source, page-cited, nothing guessed) also works for that
qualitative/operational layer, using Al Rajhi Bank (1120) as the pilot —
the same company already has deep financial-statement coverage, so this
batch completes rather than starts its profile.

## Company

| Symbol | Company | Manifest | Primary source |
|---|---|---|---|
| 1120 | Al Rajhi Bank | `data/imports/alrajhi-company-profile-2025.json` | alrajhi bank's own Investor Relations page → Integrated Annual Report 2025 PDF |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 1120 | `https://objectstorage.me-jeddah-1.oraclecloud.com/n/ax0k7s74wvl7/b/Marketing_Email_Images/o/ARBIAR25%20integrated%20annual%20report%20full%20proof%20English.pdf` | `e66e4adfe206deef5b561d61f736be0b9b67d772a0203757a45f0a0ea439de42` | `data/raw/SA/1120/documents/e66e4adf…pdf` |

The PDF link was confirmed live on alrajhi bank's own official Investor
Relations page (`https://www.alrajhibank.com.sa/en/About-alrajhi-bank/Investor-Relations`)
on 2026-09-11 before download — a primary source, not a third-party
aggregator. 13,942,086 bytes, 432 pages, digital text (not scanned).
Registered in `data/raw/archive-index.json`.

## What this batch adds, with page citations

* **Identity/governance** (`company_attributes`): legal name, founding year
  (1957), headquarters and commercial registration (p.11), Chairman
  Abdullah bin Sulaiman Al Rajhi (p.25, statement signature block),
  Managing Director/CEO Waleed Abdullah Al-Mogbel (p.30, review signature
  block), purpose/mission and ambition/vision statements (p.10),
  Shariah-compliance status and business description (p.12), 9 named
  subsidiaries (p.13-14), and a 15-person **executive management team**
  with role and years of experience each (p.224-227) — the new
  `executive_management_team` catalog field's first real population.
* **Operating segments** (`segments`, dimensioned by `segment`): total
  assets, total liabilities, total operating income and income before
  Zakat for each of Al Rajhi's four reported segments (Retail, Corporate,
  Treasury, Investment services/brokerage) for FY2025, sourced from Note
  30 "Operating segments" (p.371) of the consolidated financial
  statements bound into the same report.
* **Banking operational KPIs** (new `banking_operations` catalog
  sub-group): branches (511), ATMs (4,327), POS terminals (991,927),
  remittance centres (135), digital active users (14.9m), total customers
  (20.6m), digital-to-manual transaction ratio (96:4), Net Promoter Score
  (82), Saudisation rate (98%), and market share in personal finance
  (38.5%), auto leasing (34.4%), mortgages (37.7%) and credit cards
  (38.4%, with a 2024 comparative of 35.4%) — p.15-18 and p.56.
* **Risk factors** (`disclosures`, `risk_factor` type): the bank's own
  top-10 risk ranking and 5 emerging risks for 2025, p.264-266.

## Backlog — deliberately not included

| Field / item | Why not carried | Resolution |
|---|---|---|
| Major shareholders / ownership percentages | Third-party trackers report figures (GOSI ~9.6%, an Al Rajhi family member individually ~2.18%) but none were sourced from Tadawul directly or an official bank disclosure — this batch's own primary-source-only rule excludes them | Retrieve directly from Tadawul's company-profile ownership tab (requires the browser-driven retrieval flow, not a plain HTTP request — Tadawul returns 403 to non-browser clients) in a follow-up batch |
| Current share price / market cap / valuation multiples | Not sourced in this batch | Archive a same-day Saudi Exchange price snapshot, same pattern as `aramco-market-prices-2026-09-04.json` |
| Index memberships (TASI, MSCI, Nomu) | Not disclosed in the annual report itself | Source from the index provider or Saudi Exchange's own index-constituent pages |
| Short interest | Catalog field added this batch (`short_interest_*`) but Saudi short-selling activity is rare/limited; needs a per-company check of whether it is even offered before treating a missing value as a gap | Confirm with Tadawul's securities-lending disclosure before the next batch |
| Business-line commentary translated to Arabic | Only the English edition of the Integrated Annual Report was read this pass | Source the Arabic edition (alrajhi bank publishes one) for `_ar` attribute variants |

## Engine / catalog changes (separate commit, "For integration review")

`src/finengine/catalog.py`: added `executive_management_team`,
`board_of_directors`, `index_memberships` to `company_model`; added
`short_interest_shares`, `short_interest_percent_float`,
`short_interest_days_to_cover` to `market_data`; added `next_earnings_date`,
`next_agm_date` to `disclosures`; added a new `banking_operations`
sub-group under the Banks industry pack (branches, ATMs, POS, remittance
centres, digital users, customers, digital/manual ratio, NPS, Saudisation
rate, average monthly transactions, and 4 product market-share fields) —
the Banks pack previously had no operational-KPI sub-group, unlike every
other sector pack.

## Verification

`finengine verify alrajhi` → 54 pass / 0 warn / 0 fail (financial-statement
identities from the already-merged manifests; this batch adds no new
numeric identity to check since segment/operational/qualitative facts are
not accounting identities). A clean scratch `bootstrap` across the full
`data/imports` tree publishes the new manifest with 0 rejected facts (20/20
company attributes, 3/3 disclosures, all segment and operational facts
inserted) and `finengine audit --strict-warnings` against that scratch
database returns **0 failures / 0 warnings** across all checks, including
`source_archive_hashes` for the newly archived PDF.

Tests: `tests/test_banking_company_profiles_batch1.py` — 2 tests, both
pass (manifest structural checks + a snapshot-rebuild check that the
segment and operational facts land with the correct dimensions).
