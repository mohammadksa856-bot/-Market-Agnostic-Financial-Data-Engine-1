# Bundled release snapshot

`financial.sqlite3` is the reproducible v1.5 snapshot used by the read-only query service,
API, and Telegram adapter. It is built from 30 reviewed manifests and currently contains
1,148 current facts across Saudi Aramco, Apple, Microsoft, and NVIDIA. Aramco contributes 922
current facts (1,007 total versions), 23 official daily price rows, and 15 point-in-time valuation metrics. The seed
covers annual 2019-2025 facts plus Q1/H1 2026; US samples demonstrate the same canonical schema
with SEC EDGAR/XBRL provenance.

Every fact keeps its source, page/table extraction location, archived artifact path and SHA-256,
mapping confidence, staging path, period semantics, version history, consolidation scope, and optional dimensions.
Calculated facts carry their deterministic formula and dependencies. The active `backlog_items` ledger describes known coverage
and domain gaps; backlog rows are planning records and are never counted as verified facts.

Schema v12 includes a reviewed 507-field commercial target catalog. The universal company pack
contains 437 fields across company model, statements, dimensional financial notes, commercial sales/order backlog, investor analytics,
consensus estimates, market data, ownership, corporate actions, and disclosures. Integrated Oil & Gas
companies receive another 69 segment and operating fields. Aramco currently populates 370 fields (73.0%);
the lower percentage reflects the expanded target model rather than removed data.
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
