# Bundled release snapshot

`financial.sqlite3` is the reproducible v1.3 snapshot used by the read-only query service,
API, and Telegram adapter. It is built from 29 reviewed manifests and currently contains
825 current facts across Saudi Aramco, Apple, Microsoft, and NVIDIA. Aramco contributes 610
current facts, 23 official daily price rows, and 15 point-in-time valuation metrics. The seed
covers annual 2019-2025 facts plus Q1/H1 2026; US samples demonstrate the same canonical schema
with SEC EDGAR/XBRL provenance.

Every fact keeps its source, staging path, period semantics, version history, consolidation
scope, and optional dimensions. The active `backlog_items` ledger describes known coverage
and domain gaps; backlog rows are planning records and are never counted as verified facts.

Schema v10 includes a reviewed 391-field commercial target catalog. The universal company pack
contains 322 fields across company model, statements, ratios, market data, ownership,
corporate actions, and disclosures. Integrated Oil & Gas companies receive another 69
segment and operating fields. Aramco currently populates 295 fields (75.4%).
`company_completeness` records what is actually populated;
catalog definitions and backlog items are never presented as sourced production facts.

`imports/` is the tracked, portable reviewed-data archive used to rebuild the snapshot through the
normal extraction, mapping, normalization, validation, and publication pipeline. Large raw
documents are stored under `raw/` and indexed by `raw/archive-index.json`. Rebuild and release
audit verify their hashes. PDF binaries remain excluded from ordinary Git because of their size;
the index and compact Saudi Exchange JSON capture are tracked.

Archive or refresh official source files before rebuilding:

    python -m finengine --db data/financial.sqlite3 archive-sources --market SA --symbol 2222 --project-root .

Rebuild the database atomically, install four persistent six-hour schedules, and regenerate
the HTML/CSV outputs with:

    python -m finengine --db data/financial.sqlite3 bootstrap --replace --schedule-every 21600

Verify the release snapshot with:

    python -m finengine --db data/financial.sqlite3 audit --project-root . --strict-warnings

Regenerate only the human-readable outputs with:

    python -m finengine --db data/financial.sqlite3 report
