# Saudi market relay registry

The Windows relay universe is generated from two tracked inputs:

- `scripts/seed-data/sa-manual-seed-2026-09-13.json`: the complete 439-symbol universe.
- `config/companies.json`: richer metadata and official source pages for known companies.
- `config/source-registry/sa-*.json`: reviewed official issuer source batches.

Run `python scripts/build_sa_market_registry.py` to update
`config/sa-market-registry.json`, or add `--check` in CI to fail when the tracked
output is stale. The builder rejects duplicate symbols, malformed activity flags,
unknown Saudi overrides, missing required fields, and inconsistent identities.

`scripts/windows_tadawul_relay.py` uses the generated registry by default. Before
starting a relay run it regenerates the file atomically when either tracked input
changes, then validates the complete registry. A custom `--registry` is never
rewritten, but it is still validated before network activity begins.

The Windows scheduled task runs a 20-company batch every 15 minutes and accepts
up to 40 historical statements per company. Its
`IgnoreNew` multiple-instance policy makes this effectively continuous without
overlapping Edge sessions when a batch takes longer than the trigger interval.
