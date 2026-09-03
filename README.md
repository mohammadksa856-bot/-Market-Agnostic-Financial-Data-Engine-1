# Market-Agnostic Financial Data Engine 1.2

An auditable financial-data factory for Saudi and US companies. It discovers official filings, archives source documents, extracts source-faithful facts into staging, maps them to a canonical schema, normalizes and validates them deterministically, calculates derived metrics, and only then publishes versioned production data.

AI or probabilistic extractors never write to production. PDF/XLSX output enters staging and must pass the same mapping, normalization, validation, and publication gate as deterministic connectors.

## Release status

The bundled portable snapshot is rebuilt from 26 reviewed manifests and currently contains:

- 4 enabled companies: Saudi Aramco, Apple, Microsoft, and NVIDIA.
- 664 current facts and 721 total fact versions.
- 469 current Aramco facts: 35 profile attributes, four ownership positions, eight disclosures, three corporate actions, detailed financial/segment/operational/ESG data, annual history for 2019–2025, and discrete Q1/H1 2026 semantics.
- 167 Apple facts, plus audited FY 2026 baselines for Microsoft and NVIDIA.
- 26 published source documents, four persistent monitoring schedules, zero open publication exceptions, and zero dead jobs.
- A reviewed 391-field commercial data catalog: 322 universal company fields plus a 69-field Integrated Oil & Gas sector pack.
- Schema version 9 and 40 unit/integration/release tests.

The catalog is the target model, not fabricated data. Per-company completeness scores and a durable catalog backlog make every missing field explicit. The release audit checks SQLite integrity, foreign keys, current-fact uniqueness, source-file hashes, open exceptions, dead jobs, mapping review, balance-sheet equations, company coverage, and catalog readiness.

## Architecture

    official issuer index / SEC submissions
        -> source_candidates discovery inbox
        -> durable fetch job and immutable source archive
        -> extracted_facts (source label, value, page/table, scope, dimensions)
        -> mapped_facts (canonical metric, method, confidence)
        -> normalized_facts (deterministic units, scale, sign and periods)
        -> validation gate (required fields, balance sheet, YTD/FY roll-forwards)
        -> calculated metrics (FCF, margins, leverage and TTM)
        -> versioned production stores
        -> read-only HTTP API / Telegram bot / Arabic report

For Saudi PDF/XLSX documents, the worker archives the binary and creates a durable `document_extraction` backlog item. A reviewed extractor can then produce source-faithful staging facts. Unsupported binary formats never disappear silently and never publish placeholder values.

## Fastest way to inspect the bundled data

Python 3.11+ is required. There are no runtime package dependencies.

    python -m venv .venv
    .venv/Scripts/pip install -e .
    finengine --db data/financial.sqlite3 audit --project-root . --strict-warnings
    finengine --db data/financial.sqlite3 query SA 2222 revenue
    finengine --db data/financial.sqlite3 dossier SA 2222
    finengine --db data/financial.sqlite3 facts SA 2222 --category operational
    finengine --db data/financial.sqlite3 completeness SA 2222 --refresh
    finengine --db data/financial.sqlite3 catalog --limit 500
    finengine --db data/financial.sqlite3 report

Open `data/financial-report.html` for the Arabic searchable report. It has company, period, and category filters and links every fact to its official source. `data/financial-data.csv` is Excel-compatible.

## Rebuild the database from source manifests

The snapshot is reproducible; the binary database is not the only copy of the data.

    finengine --db data/financial.sqlite3 bootstrap --replace --schedule-every 21600

This command builds a temporary database, ingests every reviewed manifest, refreshes coverage and backlog, creates monitoring schedules, verifies database integrity, keeps a `.bak` safety copy, atomically replaces the snapshot, and regenerates the HTML/CSV outputs.

To build a separate verification copy, omit `--replace` and choose another database path:

    finengine --db data/verification.sqlite3 bootstrap

## Run continuously

Set a real SEC operator identity before enabling US monitoring:

    set SEC_USER_AGENT=YourProduct your-email@example.com

Optionally protect the API:

    set FINENGINE_API_KEY=replace-with-a-long-random-secret

Start the durable scheduler, worker, and read-only API together:

    finengine --db data/financial.sqlite3 run --host 127.0.0.1 --port 8000

The worker survives normal restarts because schedules, jobs, attempts, leases, cursors, source candidates, and backlog are stored in SQLite. Repeated polling and ingestion are idempotent. Failed jobs retry with exponential backoff; expired leases are recovered; terminal failures remain visible as dead jobs.

For separate processes, use:

    finengine --db data/financial.sqlite3 worker
    finengine --db data/financial.sqlite3 serve --host 127.0.0.1 --port 8000

SQLite is intended for one publishing worker. Migrate the same model to PostgreSQL before running multiple concurrent publishers or multi-host workers.

## Read-only API

All API database connections use SQLite `mode=ro`. Only `GET` is supported; write requests return `405 read_only_service`.

Examples:

    GET /health
    GET /v1/companies/SA/2222
    GET /v1/companies/SA/2222/dossier
    GET /v1/companies/SA/2222/facts?category=financial&limit=100
    GET /v1/companies/SA/2222/snapshot?period_end=2025-12-31
    GET /v1/companies/SA/2222/metrics/revenue?limit=10
    GET /v1/companies/SA/2222/coverage
    GET /v1/companies/SA/2222/completeness
    GET /v1/companies/SA/2222/backlog
    GET /v1/companies/SA/2222/disclosures
    GET /v1/companies/SA/2222/attributes
    GET /v1/companies/SA/2222/prices
    GET /v1/companies/SA/2222/ownership
    GET /v1/companies/SA/2222/actions
    GET /v1/catalog?category=oil_gas_operations&limit=500
    GET /v1/exceptions?status=open

When `FINENGINE_API_KEY` is set, send it as `X-API-Key` or `Authorization: Bearer ...`. Keep the server on localhost unless it is placed behind TLS, authentication, rate limiting, and normal production observability.

## Telegram bot

Create a bot with BotFather, keep the token outside the repository, then run:

    set TELEGRAM_BOT_TOKEN=123456:replace-me
    finengine --db data/financial.sqlite3 telegram

Supported commands:

    /company SA 2222
    /profile SA 2222
    /metric SA 2222 revenue
    /snapshot SA 2222 2025-12-31
    /coverage SA 2222
    /health

The Telegram adapter uses `FinancialQueryService`, so it has no production write path.

## Period semantics and validation

`period_kind` is explicit and never inferred at query time:

- `instant`: a balance at one date.
- `quarter`: one discrete fiscal quarter.
- `ytd`: cumulative from fiscal-year start through the stated quarter.
- `fy`: the full fiscal year.
- `ttm`: four published discrete quarters only.
- `as_of`, `daily`, and `event`: non-filing company domains.

The publication gate validates required fields and dates, requires valid fiscal-quarter numbers, checks `Assets = Liabilities + Equity`, and checks YTD/FY totals against discrete quarters whenever all required quarters exist. A mismatch blocks the whole source batch atomically.

Aramco Q1 and Q2 2026 demonstrate the roll-forward rule: the Q2 H1 values reconcile to Q1 plus discrete Q2 for revenue, net income, operating cash flow, and capex.

Restatements never overwrite history. A changed source creates a new version and marks exactly one observation current. Identity includes company, canonical metric, period semantics, currency, unit, consolidation scope, and an arbitrary dimension set such as `segment=Upstream`, `product=Crude oil`, or `geography=Saudi Arabia`.

## Exception review

Inspect unresolved issues:

    finengine --db data/financial.sqlite3 exceptions --status open

Record a reviewed resolution:

    finengine --db data/financial.sqlite3 resolve-exception 123 --resolution "Approved mapping rule v2" --assigned-to reviewer

After every exception for the source is resolved, replay the exact archived document:

    finengine --db data/financial.sqlite3 retry-source source-key-here

A source cannot be reopened while it still has open exceptions. This prevents a reviewer from accidentally bypassing the publication gate.

## Monitoring and ingestion

Poll official sources once:

    finengine --db data/financial.sqlite3 monitor SA 2222 --source-limit 12
    finengine --db data/financial.sqlite3 monitor US AAPL

For a deliberate Saudi historical discovery pass:

    finengine --db data/financial.sqlite3 monitor SA 2222 --source-limit 500

Live SEC ingestion uses Company Facts/XBRL JSON:

    finengine --db data/financial.sqlite3 ingest US AAPL

An approved Saudi structured adapter can use the manifest contract:

    finengine --db data/financial.sqlite3 ingest SA 2222 --sa-manifest https://your-source/report.json

The source monitor never bypasses access controls, CAPTCHAs, rate limits, or paid exchange products. Aramco discovery is restricted to the configured official issuer domain. SEC requests require an operator-identifying User-Agent.

## Canonical stores

- `data_catalog_fields`: reviewed commercial target fields, storage domain, period behavior, applicability, and pack lineage.
- `company_completeness`: category-level expected/populated counts and exact missing-field lists per company.
- `data_points`: versioned typed facts with period, scope, dimensions, quality, formula and source provenance.
- `metric_definitions`: canonical schema, units, categories, statements and aggregation rules.
- `source_documents` and `source_candidates`: immutable archives and the discovery inbox.
- `extracted_facts`, `mapped_facts`, `normalized_facts`: auditable staging layers.
- `disclosures`: risks, strategy, guidance and management commentary.
- `company_attributes`: general, governance and company-profile fields.
- `market_prices`, `ownership_positions`, and `corporate_actions`: dedicated versioned domains.
- `calculation_definitions` and dependencies: formula versions and lineage.
- `metric_applicability` and `coverage_status`: company/market/industry metric packs and gaps.
- `exceptions`, `backlog_items`, `jobs`, `job_attempts`, `workers`, and `schedules`: durable operations.

The row-based model can hold hundreds of target fields and thousands of period, segment, product, geography, and versioned facts per company without adding a database column for every metric. `company_core_v2` applies to every company; `oil_gas_v1` adds sector-specific segments, production, reserves, capacity, realized prices, costs, reliability, and environmental intensity measures.

## Backlog versus production data

The bundled backlog deliberately records missing historical periods, partial interim coverage, and any still-empty domain (for example market prices). Aramco's profile, ownership, disclosures, and corporate-action domain tasks now close automatically because those stores are populated. A backlog item is a planning/audit record, not a fact, and can never appear in production queries.

Refresh it at any time:

    finengine --db data/financial.sqlite3 backlog --refresh
    finengine --db data/financial.sqlite3 backlog SA 2222 --status active

Coverage gaps close automatically when validated facts arrive. Domain tasks close when their dedicated production store is populated. Catalog backfill is aggregated by category, so a company with hundreds of missing target fields remains operationally manageable while the exact missing keys stay queryable through completeness.

## Quality checks

    finengine --db data/financial.sqlite3 verify                 # all manifests
    finengine --db data/financial.sqlite3 verify aramco-         # one company
    finengine --db data/financial.sqlite3 audit --project-root . --strict-warnings
    python -m unittest discover -s tests -v

`verify` runs deterministic accounting identities on the reviewed manifests
before the pipeline trusts them - balance sheet (`assets = liabilities + equity`,
current + non-current), income statement (`revenue + other income`,
`pre-tax - tax = net income`, `net income = owners + non-controlling`), cash flow
(`change = operating + investing + financing`, `end = beginning + change`,
period-end cash ties to the balance sheet), dividend build-up, and margin/tax-rate
plausibility bounds. It also flags any canonical metric that appears with
conflicting values across two manifests (a restatement or a transcription error)
and any label it cannot map. A failure means the numbers are not source-faithful,
whichever agent or person produced them. It exits non-zero on any failure, any
unmapped label, or - with `--strict-warnings` - any warning.

GitHub Actions runs the same test suite on every push and pull request.

## Production boundaries

- Confirm that source terms permit the intended collection, storage, and redistribution.
- Keep raw archives in durable object storage and back them up separately from the relational database.
- Use a secret manager for SEC contact details, API keys, and Telegram tokens.
- Add TLS, authentication, authorization, rate limiting, metrics, logs, and backups before exposing the service publicly.
- Treat the current Saudi and US datasets as a reviewed seed and coverage example, not a promise that every company domain is already complete.
- Keep probabilistic extraction below the publication boundary. Confidence thresholds reduce risk but do not replace reviewed mappings and deterministic validation.
