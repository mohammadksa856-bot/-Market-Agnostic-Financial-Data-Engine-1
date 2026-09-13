# Source map: where every field comes from

One rule per field, decided before building. Written after filling all 18
categories of `DATA_MODEL_18_CATEGORIES.md` for Al Rajhi Bank (1120) from
external sources on 2026-09-13 and finding **ten conflicts on a single
company** — beta alone returned five different values from five sources.

The conflicts are the reason this file exists. Collecting data turned out
to be the easy half; deciding which number wins, and saying so publicly,
is the half that makes the numbers defensible.

## The three tiers

| Tier | Meaning | How it is shown to a reader |
| --- | --- | --- |
| **P — Primary** | The issuer, the exchange, or the auditor. The filer's own words. | Published as fact |
| **D — Derived/market** | A number that exists only because a third party produced it (analyst targets, credit ratings, MSCI scores). No primary source exists. | Always attributed: "per MarketScreener", "per S&P" |
| **C — Computed** | We calculate it ourselves from P data, with the method declared. | Published as fact, with the formula and basis shown |

**The governing rule: if it can be computed, compute it — never fetch it.**
Beta returned 0.34 / 0.58 / 1.09 / 1.15 / 1.34 from five vendors because
each uses a different window and benchmark. Fetching any one of them
imports an undeclared methodology. Computing it from the price series we
already store makes it ours, reproducible, and explainable.

Only two of the eighteen categories have no primary source at all —
analyst coverage (14) and the ESG *rating* inside (17). Everything else
can be kept inside the primary-source rule.

## Layer A — Foundation

| Category | Field group | Tier | Source of record | Engine status |
| --- | --- | --- | --- | --- |
| 1 Identity | symbol, ISIN, name, market | **P** | Saudi Exchange `searchableSymbols` | ✅ `universe.py` |
| 1 Identity | legal name, CR, incorporation, HQ, legal form, FY end, reporting standard, auditor | **P** | Audited statements, pp. 1–3 and the general-information note | ✅ `populate_profile.py` |
| 2 Business model | segment revenue/assets/profit | **P** | Operating-segments note in the audited statements | ✅ `reading.py` |
| 2 Business model | business description, products, geography, subsidiaries | **P** | Annual report | ✅ `populate_profile.py` |
| 2 Business model | revenue by product %, unit economics | **P** | Annual report / investor presentation | ❌ fields not in catalog |
| 3 Governance | board, committees, independence, remuneration policy, related-party | **P** | Board report inside the annual report | ❌ not extracted |
| 3 Governance | appointments, resignations, committee changes | **P** | **Tadawul issuer announcements** | ❌ no connector |
| 3 Governance | insider share dealings | **P** | Tadawul disclosure (mandatory filing) | ❌ no connector |
| 4 Ownership | holders ≥5%, foreign ownership %, free float | **P** | Tadawul company page + ownership disclosures | ⚠️ store exists (`domains.py`), fetcher missing |
| 4 Ownership | institutional holders (Vanguard, BlackRock…) | **D** | MarketScreener | ❌ |
| 4 Ownership | index weight | **C** | Computed from free float × price ÷ index total | ❌ |

## Layer B — Performance

| Category | Field group | Tier | Source of record | Engine status |
| --- | --- | --- | --- | --- |
| 5 Financials | income statement, balance sheet, cash flow | **P** | Audited statements PDF; issuer data-supplement XLSX where published; Tadawul HTML table as cross-check | ✅ `reading.py`, `reading_xlsx.py` — strongest area |
| 6 Earnings quality | auditor opinion type, key audit matters | **P** | Audit report, pp. 3–5 | ❌ fields not in catalog |
| 6 Earnings quality | going-concern **warning** | **P** | Audit report — *must distinguish a real material-uncertainty paragraph from the boilerplate that appears in every report* | ❌ |
| 6 Earnings quality | one-time items, securitisation gains, impairments | **P** | Notes to the statements | ❌ |
| 7 Ratios | all ratios, three sets by company type | **C** | Computed from category 5 | ⚠️ `calculations.py` exists; needs the bank/insurer and loss-making sets, plus a declared basis (year-end vs average equity) |
| 8 Operational KPIs | branches, ATMs, customers, digital users, market share | **P** | Annual report, investor presentation, quarterly fact sheet | ⚠️ partial via `populate_profile.py` |
| 9 Dividends & actions | dividend recommendations, bonus shares, capital changes, AGM outcomes | **P** | **Tadawul issuer announcements** | ⚠️ store exists, fetcher missing |
| 9 Dividends & actions | payout ratio, yield, 10y volatility and growth | **C** | Computed from dividend history + price | ❌ |

## Layer C — Context

| Category | Field group | Tier | Source of record | Engine status |
| --- | --- | --- | --- | --- |
| 10 Industry | banking aggregates, insurance GWP, sector loan growth | **P** | SAMA statistics, GASTAT, Insurance Authority | ❌ — but this is ~20 sector datasets, not 439 company ones |
| 10 Industry | sector dynamics, regulation, moat | **P** | Regulator publications + the issuer's own MD&A | ❌ |
| 11 Competitors | peer comparison table | **C** | Computed from our own data across the sector — no external source needed | ❌ query not built |
| 11 Competitors | market share | **P** | Issuer disclosure, cross-checked against sector aggregates | ❌ |
| 12 Trading | price, volume, turnover, 52-week range | **P** | Saudi Exchange | ✅ price store |
| 12 Trading | **beta, volatility** | **C** | **Computed from our own price series against TASI.** Five vendors returned five values; none is adoptable | ❌ |
| 12 Trading | negotiated deals | **P** | Saudi Exchange | ❌ |

## Layer D — Forward view and valuation

| Category | Field group | Tier | Source of record | Engine status |
| --- | --- | --- | --- | --- |
| 13 Forecasts | **company guidance** (the issuer's own targets) | **P** | Results presentation and Tadawul announcement — e.g. Al Rajhi published NIM +25–35bps, CIR <23%, RoE >23.5%, Tier 1 >20% for 2026 | ❌ |
| 13 Forecasts | analyst estimates by year | **D** | Research PDFs, MarketScreener | ❌ no free systematic index — Argaam's research listing is gated, though individual PDFs are open once the URL is known |
| 14 Analyst coverage | ratings, target prices, consensus | **D** | MarketScreener, TradingView, Argaam public page | ❌ — **no primary source exists for this category** |
| 14 Analyst coverage | split adjustment of historical targets | **C** | Computed — a SAR 105.4 target set before Al Rajhi's 3:2 split is not comparable to a SAR 74.95 target set after it | ❌ |
| 15 Valuation | P/E, P/B, EV/EBITDA, yield | **C** | Computed from category 5 + live price, basis declared | ⚠️ partial |
| 15 Valuation | intrinsic value (DCF/DDM) | **C** | **Built in-house.** External models returned SAR 41.72 to 85.46 for the same company on the same day — a 2× spread. A valuation we cannot explain is worse than none | ❌ |

## Layer E — Risk and disclosure

| Category | Field group | Tier | Source of record | Engine status |
| --- | --- | --- | --- | --- |
| 16 Risks | risk factors as disclosed | **P** | Annual report risk section | ⚠️ partial |
| 16 Risks | debt maturity ladder, concentration, contingent liabilities | **P** | Notes to the statements — maturity analysis is in the liquidity note | ❌ |
| 16 Risks | sukuk/bond issuance terms | **P** | Tadawul announcement + issuer press release | ❌ |
| 16 Risks | credit rating | **D** | S&P, Fitch, Moody's public releases | ❌ |
| 17 ESG | emissions, Saudization, sustainable finance, social programmes | **P** | Issuer sustainability report | ❌ |
| 17 ESG | MSCI / Sustainalytics rating | **D** | Rating agency | ❌ |
| 18 News | official announcements | **P** | **Tadawul issuer announcements** | ❌ no connector |
| 18 News | press coverage | **D** | Argaam RSS (free), Google Alerts (free), LLM+search (paid fallback) | ✅ all three built |
| 18 News | events calendar | **P** | Tadawul + issuer IR calendar | ❌ |
| 18 News | investor presentations, transcripts, annual reports | **P** | Issuer IR page | ⚠️ ad-hoc |

## What this map makes obvious

**1. One missing connector blocks six categories.**
The Tadawul issuer-announcements feed (verified 2026-09-13: 90,698
announcements, listed with company, symbol, headline, Hijri and Gregorian
timestamps, keyword search and period filters, fully reachable through the
browser fetch path `fetching.py` already uses) is the source of record for
categories 3, 4, 9, 13, 16 and 18. Nothing else in this map unlocks as
much. It should be built first.

**2. Five fields must be computed, not collected.**
Beta, volatility, index weight, split-adjusted target prices, and
intrinsic value. Every one of them returned contradictory values from
vendors today. Computing them is not extra work — it is the only way to
be able to answer "where did this number come from".

**3. The primary-source rule survives, with two labelled exceptions.**
Sixteen of eighteen categories have a genuine primary source. Only
analyst coverage (14) and the ESG rating inside (17) do not exist outside
third parties, and both are opinions about a company rather than facts
about it — so attributing them explicitly is the honest treatment anyway,
exactly as the news policy already does for press coverage.

**4. The declared-methodology requirement is not optional.**
ROE for Al Rajhi is 17.3% on year-end equity and 22.8% on average equity.
Both are correct. Without publishing which basis is used, a correct number
looks like an error — and the reader has no way to tell the difference.
