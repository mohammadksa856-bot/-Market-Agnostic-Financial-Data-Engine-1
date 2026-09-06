# Parallel workstreams: Codex and Claude

The goal is speed without duplicate extraction, binary database conflicts, or two
agents changing the same contract differently.

## Codex owns the platform workstream

- company/security universe synchronization for Saudi Exchange and SEC;
- source monitoring, scheduler, durable jobs, retries, idempotency, and backups;
- canonical storage contracts, period semantics, validation gates, and audit;
- read-only product API, Telegram adapter, deployment, and CI;
- final integration, snapshot rebuild, release audit, and merge to `main`.

Primary paths: `src/finengine/database.py`, `universe.py`, `jobs.py`,
`operations.py`, `api.py`, `query.py`, `cli.py`, `deploy/`, and platform tests.

## Claude owns the data expansion workstream

- collect and archive official issuer reports and announcements;
- produce source-faithful manifests with page/table provenance;
- complete company profiles and sector-specific operational KPIs;
- expand Saudi companies by sector, starting with insurance, telecom, utilities,
  materials/petrochemicals, then remaining sectors;
- build representative US issuer acceptance sets beyond the SEC standard tags;
- classify every unavailable field with a reason; never fabricate a value.

Primary paths: `data/imports/`, `data/raw/`, `config/supplements/`, mapping fixtures,
sector reader tests, and company-specific documentation.

## Integration rules

1. Claude works on `claude/data-<sector>-<batch>` branches; Codex works on
   `codex/platform-<feature>` branches. Do not push incomplete work directly to
   `main`.
2. Claude does not commit generated `data/financial.sqlite3`, HTML, or CSV files.
   Codex rebuilds those once after merging a data batch, avoiding binary conflicts.
3. Changes to the canonical catalog, calculations, database schema, API, or CLI are
   proposed in a separate commit and called out explicitly for integration review.
4. Each data batch includes official source URLs, archived hashes, page/table
   references, verification tests, and a list of unresolved fields with reasons.
5. Codex rebases on the latest data branch, runs all tests and strict audit, rebuilds
   the portable snapshot, and only then merges to `main`.

## Current parallel queue

| Priority | Codex | Claude |
|---|---|---|
| P0 | Finish versioned SA/US universe sync and inventory API | Insurance-sector batch from official FY 2025 reports |
| P1 | Activation batches and rate-limited monitor scheduling | Telecom and utilities acceptance companies |
| P2 | Licensed market/consensus/news provider interfaces | Materials, petrochemicals, and industrial company backfill |
| P3 | Website/Supabase page-contract integration and Telegram coverage | Remaining Saudi sectors and US custom-tag exceptions |
