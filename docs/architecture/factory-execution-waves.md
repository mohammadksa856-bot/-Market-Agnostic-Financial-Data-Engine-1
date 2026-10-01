# 18-category factory execution waves

The canonical completeness contract remains
`config/factory/18-category-contract.json`. Its weights, thresholds and hard
gates decide readiness. The execution plan in
`config/factory/execution-plan.json` only decides when and how work runs; it is
not allowed to make a category easier to pass.

## Why waves exist

The former factory planner materialized 18 work items but collapsed almost all
source-driven work into one generic issuer monitor and allowed valuation to run
before financial, per-share and market inputs were terminal. It also launched
one deterministic refresh per company even though each refresh recalculated
the entire enabled universe. That created duplicated CPU work and misleading
`running` factory runs.

The wave plan separates execution completion from category readiness:

- `published`: the category passes its threshold and hard gates;
- `validated`: its acquisition/calculation attempt finished but an honest gap
  remains;
- `blocked`: the job or an upstream dependency cannot proceed;
- `queued`/`running`: actual work remains.

A `validated` upstream category may unlock a calculation that can use partial
inputs, but it never counts as ready. Therefore useful calculations continue
while the final 95% contract still reports the missing fields.

## The six waves

| Wave | Categories | Execution rule |
| --- | --- | --- |
| Financial foundation | financial statements | Archive, extract, normalize and validate reported facts first. |
| Financial derivations | profitability, liquidity/solvency, efficiency, growth, per-share, smart metrics | Rebuild deterministic formulas from current reported facts; no network or AI. |
| Market and events | market data, dividends, corporate actions, announcements | Use official exchange and issuer event streams. |
| Company intelligence | profile, segments, ownership | Use archived issuer/registry filings and retain evidence. |
| Sector depth | operational KPIs, sector-specific fields | Activate only the reviewed sector pack. |
| Valuation and assurance | valuation, source lineage/freshness | Valuation waits for financials, per-share and market data; final assurance audits provenance and freshness. |

Independent source waves may run while historical statements are extracting.
Explicit dependencies still prevent nonsensical work: valuation cannot run
before its three input categories, sector fields cannot run before the company
profile identifies the sector, and financial ratios cannot run before the
statement attempt is terminal.

## Efficiency and auditability

Eligible categories sharing the same company and strategy are coalesced into a
single durable job. Every job records `factory_run_id`, `wave_keys`,
`target_categories` and `expected_source_types`. Idempotency includes the exact
target-category set, so a later-unlocked wave can run without duplicating a
previous successful job.

The deterministic refresh is company-scoped. It rebuilds all historical
financial calculations from current reported inputs, then refreshes market
statistics, point-in-time valuations, catalog coverage and readiness. Old
calculated values cannot seed their own replacements.

Factory status exposes counts per wave. When all jobs are terminal but one or
more categories remain merely `validated` or `blocked`, the run ends as
`blocked` instead of staying `running` forever. The unresolved categories are
then actionable gaps, not hidden background work.
