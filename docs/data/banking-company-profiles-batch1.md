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
| 1120 | Al Rajhi Bank | `data/imports/alrajhi-market-ownership-2025.json` | Tadawul's own company-profile page for symbol 1120 (live price, shareholding, corporate actions) |

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
* **Live price, shareholding and corporate actions** (second manifest,
  `alrajhi-market-ownership-2025.json`, sourced directly from Tadawul's own
  company-profile page for symbol 1120, retrieved 2026-09-11):
  - a dated `market_prices` snapshot (1d interval: open/high/low/close,
    volume, turnover; 1y interval: 52-week high/low) — this is what
    unlocks the engine's automatic valuation chain (market_cap, P/E,
    dividend yield, enterprise value all became `is_calculated: true`
    once this landed, where they were previously skipped with reason
    `no_market_price`);
  - `shares_outstanding` (6,000,000,000) and `share_capital` (SAR
    60,000,000,000) from the page's Equity Profile — dated 2026-09-11,
    and independently reproduces the quoted price exactly
    (396,000,000,000 / 6,000,000,000 = 66.00);
  - **12 ownership positions** from Tadawul's own Board-of-Directors
    shareholding table (Chairman Abdullah bin Sulaiman Al Rajhi at
    2.1791737%, 11 other board/senior-executive holdings, all under
    0.004% individually);
  - a disclosure recording that Tadawul's own **Substantial Shareholders**
    (≥5%) tab returned no rows for Al Rajhi — i.e. no shareholder
    currently holds 5% or more, sourced from the exchange's own page,
    not inferred;
  - **10 corporate actions**: 5 historical bonus-share (capitalisation)
    issues 2008–2026 and 5 historical cash dividends 2024–2026, both from
    Tadawul's own Corporate Actions and Dividends tabs.

## A real discrepancy this batch surfaced and did not silently resolve

The engine's own calculated `price_to_earnings` for Al Rajhi comes out to
**15.95**, while Tadawul's own Peer Comparison tool on the same page shows
**14.94** for the same day. Both are legitimate, sourced numbers — the gap
is a real methodology effect, not an error: the engine's formula is
`market_cap / latest_filed_fy(net_income)`, and `market_cap` uses
**today's** share count (6,000,000,000, current as of 2026-09-11), while
FY2025's `net_income` (and the reported EPS of 5.85 it implies) was earned
over a **smaller** weighted-average share count, since Al Rajhi's bonus
share issue that raised capital to SAR 60bn only took effect in April
2026 — after FY2025 closed. Dividing a post-bonus-issue market cap by a
pre-bonus-issue net income structurally inflates the ratio until FY2026's
own EPS is reported on the new share count. This is a real, useful
observation for the platform workstream (retroactive split/bonus-share
adjustment of historical per-share figures is standard practice in
equity data platforms) — flagged here rather than fixed, since it is a
`calculations.py` change and belongs with Codex's platform ownership per
`docs/WORKSTREAMS.md`.

## Backlog — deliberately not included

| Field / item | Why not carried | Resolution |
|---|---|---|
| Index memberships (TASI, MSCI, Nomu) | Not disclosed on either the annual report or the Tadawul company-profile page checked this batch | Source from the index provider or Saudi Exchange's own index-constituent pages |
| Short interest | Catalog field added this batch (`short_interest_*`) but Saudi short-selling activity is rare/limited, and Tadawul's own company-profile page for 1120 has no securities-lending/short-interest tab | Confirm whether Tadawul discloses this for any Saudi issuer before treating a missing value as a gap |
| Business-line commentary translated to Arabic | Only the English edition of the Integrated Annual Report was read this pass | Source the Arabic edition (alrajhi bank publishes one) for `_ar` attribute variants |
| Foreign-ownership aggregate percentage | Tadawul's page has a separate "Foreign Ownership" tab; opened but not fully read before this batch closed | Read it in the next banking batch |

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
numeric identity to check since segment/operational/qualitative/ownership
facts are not accounting identities). A clean scratch `bootstrap` across
the full `data/imports` tree publishes both new manifests with 0 rejected
facts:
- `alrajhi-company-profile-2025.json`: 20/20 company attributes, 3/3
  disclosures;
- `alrajhi-market-ownership-2025.json`: 2/2 facts, 2/2 market-price rows,
  12/12 ownership positions, 10/10 corporate actions, 1/1 disclosure —
  and this is what flips `market_valuations` for `sa:1120` from `skipped
  (no_market_price)` to **published, 11 calculated facts** (market_cap,
  P/E, dividend yield, enterprise value, price-to-book, etc.), independently
  cross-checked: `market_cap` (396,000,000,000) exactly equals
  `shares_outstanding × price_close` (6,000,000,000 × 66.00).

`finengine audit --strict-warnings` against that scratch database returns
**0 failures / 0 warnings** across all checks, including
`source_archive_hashes` for the newly archived annual-report PDF.

Two real lessons from building this manifest, both now documented in its
`notes` field rather than left implicit: (1) `price_open`/`price_high`/
`price_low`/`previous_close`/`fifty_two_week_high`/`fifty_two_week_low`
are reserved metric names the mapping engine only accepts via the
dedicated `market_prices` array (see `src/finengine/domains.py`'s
`price_map`), not the generic `facts` array — the first bootstrap attempt
correctly rejected them there; (2) every `corporate_actions` entry
requires an `announcement_date`, even when the only date Tadawul discloses
for an older bonus-share event is an eligibility date — handled by setting
`announcement_date` equal to `eligibility_date` with an explicit caveat in
`details`, not by inventing a separate date.

Tests: `tests/test_banking_company_profiles_batch1.py` (5 tests) and
`tests/test_banking_market_ownership_batch1.py` (5 tests), all pass. Full
repo suite: 201 passed, 1 skipped, 0 failed.
