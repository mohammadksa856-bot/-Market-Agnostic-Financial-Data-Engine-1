# Bundled release snapshot

`financial.sqlite3` is the reproducible v1.0 snapshot used by the read-only query service,
API, and Telegram adapter. It is built from 26 reviewed manifests and currently contains
321 current facts across Saudi Aramco, Apple, Microsoft, and NVIDIA. The Aramco seed covers
annual 2021-2025 facts plus reviewed interim 2025 and Q1/H1 2026 facts. US samples demonstrate
the same canonical schema with SEC EDGAR/XBRL provenance.

Every fact keeps its source, staging path, period semantics, version history, consolidation
scope, and optional dimensions. The active `backlog_items` ledger describes known coverage
and domain gaps; backlog rows are planning records and are never counted as verified facts.

`imports/` is the tracked, portable source archive used to rebuild the snapshot through the
normal extraction, mapping, normalization, validation, and publication pipeline. Large raw
documents downloaded during live monitoring remain excluded from Git, while their URLs,
hashes, processing states, and provenance stay in the database.

Rebuild the database atomically, install four persistent six-hour schedules, and regenerate
the HTML/CSV outputs with:

    python -m finengine --db data/financial.sqlite3 bootstrap --replace --schedule-every 21600

Verify the release snapshot with:

    python -m finengine --db data/financial.sqlite3 audit --project-root . --strict-warnings

Regenerate only the human-readable outputs with:

    python -m finengine --db data/financial.sqlite3 report
