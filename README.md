# Market-Agnostic Financial Data Engine 2.0

An auditable financial-data factory for Saudi and US companies. It discovers official filings, archives source documents, extracts source-faithful facts into staging, maps them to a canonical schema, normalizes and validates them deterministically, calculates derived metrics, and only then publishes versioned production data.

AI or probabilistic extractors never write to production. PDF/XLSX output enters staging and must pass the same mapping, normalization, validation, and publication gate as deterministic connectors.

## Release status

The bundled portable snapshot is rebuilt from 55 reviewed manifests and currently contains:

- 15 enabled companies in the bundled snapshot: Saudi Aramco, SABIC, all ten listed
  Saudi banks, Apple, Microsoft, and NVIDIA.
- The archived official SEC universe snapshot contains 8,010 issuers and 10,415
  ticker/exchange associations. It is inventory, not automatic publication:
  activation and monitoring are released in controlled batches. The first 100-issuer
  review batch is fully enriched from archived SEC registrant profiles: 70 eligible
  operating companies, 14 excluded vehicles, and 16 conservative review cases.
- The public Saudi Exchange directory now has a first-class browser connector.
  A full connector acceptance run on 7 September 2026 archived 272 Main Market
  securities and 124 Nomu securities: 376 operating-company records and 20
  fund/REIT records. The connector keeps the two markets separate, records ISIN
  and profile provenance, and excludes funds from normal company activation.
- 4,257 current facts and 4,409 total fact versions in the bundled snapshot.
- 1,020 current Aramco data points, plus 37 profile attributes, four ownership positions, disclosures, corporate actions, 23 official daily market-price rows, and point-in-time market and valuation metrics. Coverage includes detailed financial, segment, operational, ESG, commercial, commitment, tax, credit-risk, lease, geographic revenue, PPE movements, and annual history for 2019–2025, plus discrete Q1/H1 2026 semantics. The 2025 production table is stored at reported precision and drives a deterministic 52.54-year reserve-life calculation with full formula lineage.
- 207 Apple facts, plus audited FY 2026 baselines for Microsoft and NVIDIA. A local
  `FLWS` acceptance run also completed the live SEC monitor/fetch/validate/publish
  path with 1,780 facts; that operational snapshot is kept outside the code release.
- 55 published source documents and 13 independently hashed raw artifacts in the
  bundled snapshot, with zero open publication exceptions and zero dead jobs.
- Master Schema catalog version 10 contains 1,046 governed fields and 916 metric contracts: 545 universal fields, 20 dividend fields, 28 announcement fields, and 15 sector packs. In addition to oil and gas, the 64-field chemicals pack now includes resource intensity, emissions, waste, process safety, innovation, workforce, and supplier KPIs. The 43-field banking pack powers sector-aware bank ratios and scores. Insurance, telecommunications, utilities, mining, real estate/REITs, retail, health care, transportation/logistics, industrials/construction, technology, food/agriculture, and asset management are also covered. The schema includes 61 governed dimensions and keeps sector packs applicable only to matching canonical industries. See [the Master Schema specification](docs/MASTER_SCHEMA.md).
- Aramco currently populates 395 of 662 applicable catalog fields (59.7% raw target coverage), with all 28 core required fields present. The lower percentage reflects a large target model, not lost data.
- SABIC is the first Saudi generalization acceptance pilot: its official 2025 integrated report is archived by SHA-256. The snapshot publishes 528 sourced facts plus 240 deterministic calculated facts. It covers audited annual history for 2021–2025, the full 2025 statements and restated 2024 comparative, detailed PPE classes and disposals, cash and receivables, debt instruments and maturities, leases, employee benefits, provisions, related parties, tax components, commitments, production and sales volumes, segment and geographic revenue, dividends and year-end market history, company profile, ownership, corporate actions, disclosures, resource intensity, emissions, process safety, innovation, workforce, and suppliers. SABIC populates 377 of 657 applicable catalog fields and all 28 core required fields. Every sourced fact retains its report page and table reference; deterministic calculations retain their formula lineage.
- All 655 directly sourced Aramco facts resolve to an extraction row and archived official artifact. This includes the seven-component breakdown of other reserves for both 2024 and 2025; it is not mislabeled as accumulated OCI because one component includes share-based compensation. Read-only fact responses expose source URL/key, report page/table, extraction label/value, mapping confidence/method, archive path and SHA-256. Calculated facts expose their deterministic formula and dependencies.
- Every unresolved catalog field is classified in the durable backlog as pending official extraction, not disclosed in archived filings, qualitative-only, event-driven with no event observed, not applicable to the market, dependent on missing calculation inputs/history, or requiring a licensed/authoritative source. Each field now carries a plain-language reason, a concrete resolution, and a machine-readable solution code so background agents can close the gap without inventing data.
- Database schema version 17, catalog version 10, and 106 unit/integration/release tests (reader/browser tests require their optional dependencies).

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
    finengine --db data/financial.sqlite3 dossier SA 2222 --output data/aramco-2222-dossier.json
    finengine --db data/financial.sqlite3 page SA 2222 --output data/aramco-2222-page.json
    finengine --db data/financial.sqlite3 facts SA 2222 --category operational
    finengine --db data/financial.sqlite3 completeness SA 2222 --refresh
    finengine --db data/financial.sqlite3 catalog --limit 500
    finengine --db data/financial.sqlite3 report

## Synchronize the company universe

The universe inventory is versioned separately from enabled ingestion companies,
so a full-market refresh cannot accidentally launch thousands of jobs. SEC issuer,
ticker, and exchange associations can be synchronized from the official file after
setting a declared operator identity:

    finengine --db data/financial.sqlite3 universe-sync US
    finengine --db data/financial.sqlite3 universe-status

Create a reviewable batch without launching network jobs:

    finengine --db data/financial.sqlite3 universe-activate US --limit 50 --exchange Nasdaq --exchange NYSE

Enrich a staged batch from official SEC submissions metadata and classify operating
companies separately from funds, blank-check companies, and review cases:

    finengine --db data/financial.sqlite3 universe-enrich --limit 25

Promote only SEC-confirmed operating companies, in a bounded batch, and create
durable monitoring schedules:

    finengine --db data/financial.sqlite3 universe-promote activation:BATCH_ID --limit 10 --schedule-every 21600

Activation is a separate explicit step. To enable and schedule a reviewed symbol
batch, pass the symbols and a monitoring interval (minimum one hour):

    finengine --db data/financial.sqlite3 universe-activate US --symbols AAPL,MSFT,NVDA --enable --schedule-every 21600

Saudi Exchange can be synchronized directly through its public dynamic issuer
directory. Install the browser extra once; production containers already include it:

    pip install -e ".[browser]"
    playwright install chromium
    finengine --db data/financial.sqlite3 universe-sync SA

The command reads Main Market and Nomu separately and archives the normalized
source capture before updating inventory. It does not enable hundreds of schedules.
Company activation excludes funds and REITs unless `--include-funds` is explicit:

    finengine --db data/financial.sqlite3 universe-activate SA --limit 25

Authorized Saudi Exchange/eReference JSON or CSV exports remain supported through
the same archived model when licensed fields such as sector classification are needed:

    finengine --db data/financial.sqlite3 universe-sync SA --input issuers.csv --source-url https://www.saudiexchange.sa/

Every snapshot retains its retrieval time, source URL, local archive path, SHA-256,
issuer versions, and security versions. Multi-ticker US issuers share one CIK-based
issuer identity. Activation batches are durable and idempotent, and workers can
resolve activated companies from SQLite without expanding the hand-maintained seed
registry. See [parallel workstreams](docs/WORKSTREAMS.md).

Open `data/financial-report.html` for the Arabic searchable report. It has company, period, and category filters; every direct fact shows its official source, page/table, archived file and hash, while derived facts show their formula. `data/financial-data.csv` carries the same audit columns and is Excel-compatible.

## Rebuild the database from source manifests

The snapshot is reproducible; the binary database is not the only copy of the data.

    finengine --db data/financial.sqlite3 bootstrap --replace --schedule-every 21600

This command builds a temporary database, ingests every reviewed manifest, refreshes coverage and backlog, creates monitoring schedules, verifies database integrity, keeps a `.bak` safety copy, atomically replaces the snapshot, and regenerates the HTML/CSV outputs.

To build a separate verification copy, omit `--replace` and choose another database path:

    finengine --db data/verification.sqlite3 bootstrap

## Archive official sources for offline use

Download every distinct official source used by the reviewed manifests, verify its content, store it under a content-addressed local path, and update the portable archive index:

    finengine --db data/financial.sqlite3 archive-sources --market SA --symbol 2222 --project-root .

`data/raw/archive-index.json` records the URL, SHA-256 hash, media type, byte size, local path, and linked manifests for every artifact. Rebuilds verify each local artifact against the index and link it to its source rows. Queries and reports therefore read the local SQLite snapshot; they do not fetch the Internet at request time.

The seven Aramco PDF binaries total about 70.5 MB and are intentionally excluded from ordinary Git commits. Keep that local archive in backed-up object storage or Git LFS for production. The small Saudi Exchange JSON capture and the full archive index are tracked directly in Git.

## Run continuously

Production startup configures an idempotent monitor for every enabled company in
`config/companies.json` and every explicitly promoted universe company. Inventory
refresh and activation remain separate so discovery never launches hundreds of
jobs. See [production readiness and rollout](docs/PRODUCTION.md).

Set a real SEC operator identity before enabling US monitoring:

    set SEC_USER_AGENT=YourProduct your-email@example.com

Optionally protect the API:

    set FINENGINE_API_KEY=replace-with-a-long-random-secret

Start the durable scheduler, worker, and read-only API together:

    finengine --db data/financial.sqlite3 run --host 127.0.0.1 --port 8000

For an always-on host, copy `.env.example` to `.env`, replace the example SEC
identity and API key, then run:

    docker compose up -d --build

Add `--profile telegram` to start the read-only Telegram adapter. The deployment
also refreshes the official US and Saudi market inventories daily and creates a
verified portable database/source bundle, retaining seven bundles by default.

Create a transportable, self-verifying bundle containing an online SQLite snapshot
and every raw file referenced by its provenance tables:

    finengine --db data/financial.sqlite3 backup-bundle --output-dir backups/bundles --keep 7

The ZIP contains a manifest, a consistent database snapshot, and content-addressed
source files. Every hash is verified after creation, making the bundle suitable for
off-host encrypted backup or S3-compatible object storage.

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
    GET /v1/companies/SA/2222/page
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
    GET /v1/companies/SA/2222/estimates?metric=revenue_estimate&period_end=2027-12-31
    GET /v1/companies/SA/2222/actions
    GET /v1/catalog?category=oil_gas_operations&limit=500
    GET /v1/catalog/history/crude_oil_production
    GET /v1/dimensions
    GET /v1/universe?market=SA&limit=100
    GET /v1/universe/status
    GET /v1/exceptions?status=open

`/page` is the stable website/Telegram contract. It separates FY, quarter, YTD,
TTM and instant snapshots, includes provenance, reports section capability and
missing-source reasons, and explicitly forbids demonstration-value fallbacks.

When `FINENGINE_API_KEY` is set, send it as `X-API-Key` or `Authorization: Bearer ...`. Keep the server on localhost unless it is placed behind TLS, authentication, rate limiting, and normal production observability.

## Publishing to the application (Supabase)

`export-supabase` is the one-way bridge from the engine's SQLite production store to a flat `financial_facts` table the website and Telegram bot read. It upserts the engine's *current* facts - the same rows `finengine facts` returns - carrying every provenance column per row: official source URL, archived SHA-256, the raw extracted label and value, mapping confidence, and, for derived rows, the deterministic formula. It is additive and never touches the application's own tables.

    export SUPABASE_URL=https://<project-ref>.supabase.co
    export SUPABASE_SERVICE_KEY=<service-role key>        # write path; never commit it

    finengine export-supabase SA 2222                     # one company
    finengine export-supabase --all --prune               # every enabled company
    finengine export-supabase SA 1120 --dry-run           # print the rows, send nothing
    finengine export-supabase --all --sql-out facts.sql   # emit an idempotent script to review first

`--prune` deletes rows a company's current export no longer produces (a restated or withdrawn fact). Without a service-role key locally, use `--sql-out` and apply the reviewed script through the Supabase SQL editor. No third-party package is required - the engine talks to PostgREST over stdlib HTTP.

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

Saudi issuer pages can be discovered and fetched through Chromium when ordinary HTTP is blocked by a CDN. For activated Saudi Exchange companies, the monitor follows official financial-result announcement cards, records each announcement as the PDF's referer provenance, and uses that browser session to archive referer-protected attachments. Docker runs Chromium inside an isolated virtual display by default, so no desktop window is shown. The downloaded document is content-addressed and archived before extraction:

    finengine fetch SA 2222 https://issuer.example/investors --discover
    finengine fetch SA 2222 https://issuer.example/report.pdf

The deterministic statement reader converts an archived PDF to a source-faithful staging manifest. `verify` checks accounting identities and treats scope and dimensions as part of a fact's identity, so segment, geography, asset-class, and maturity-band values are not mistaken for restatements:

    finengine read report.pdf SA 2222 --source-url https://issuer.example/report.pdf --filed-at 2026-03-01 --out report.json
    finengine verify --imports data/imports

Interim PDFs that combine quarter and YTD columns are archived automatically but held in the exception queue with `interim_period_semantics_required` until the reader can prove which column has which semantics. They never publish under a guessed FY/Q/YTD identity.

Large issuers publish a machine-readable "data supplement" / "fact sheet" spreadsheet: the full income statement and balance sheet across ~10 years of annual columns plus quarterly history, produced by the company itself. `read-xlsx` turns one into a source-faithful manifest, driven by a per-issuer row map in `config/supplements/<symbol>.json`. It ingests only the raw reported lines - the supplement's own pre-computed ratios (ROE, NIM, cost-to-income, ...) are skipped, because the engine recomputes every ratio from the ingested lines:

    finengine read-xlsx "ARB Data Supplement 4Q2025.xlsx" SA 1120 --filed-at 2026-02-04 --out data/imports/alrajhi-supplement.json

One Al Rajhi supplement adds twelve years (2014-2025) of the full statements in a single file. Install `.[xlsx]` for the spreadsheet reader.

Install `.[reader]` for PDF reading, `.[browser]` for browser fetching, `.[xlsx]` for supplement spreadsheets, or `.[agents]` for everything plus the optional LLM fallback. The LLM reader runs only when explicitly enabled and its output must pass the same deterministic verification and publication gate.

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

- `data_catalog_fields` and `data_catalog_field_versions`: reviewed commercial target fields plus an immutable history of every definition change.
- `dimension_definitions`: the governed vocabulary for segment, geography, product, instrument, maturity, note, and other fact axes; unknown production dimensions are rejected.
- `metric_contracts`: the enforceable period-kind, dimension, and unit-family contract for every canonical data-point metric.
- `company_completeness`: category-level expected/populated and required-field counts, with exact missing and required-missing lists per company.
- `data_points`: versioned typed facts with period, scope, dimensions, quality, formula and source provenance.
- `metric_definitions`: canonical schema, units, categories, statements and aggregation rules.
- `source_documents`, `source_artifacts`, `source_artifact_links`, and `source_candidates`: reviewed manifests, independently hashed raw files, provenance links, and the discovery inbox.
- `extracted_facts`, `mapped_facts`, `normalized_facts`: auditable staging layers.
- `disclosures`: risks, strategy, guidance and management commentary.
- `company_attributes`: general, governance and company-profile fields.
- `market_prices`, `ownership_positions`, `corporate_actions`, and `consensus_estimates`: dedicated versioned domains. Consensus rows preserve the target period, estimate observation date, low/high/mean/median type, analyst count, source, and restatement history.
- `calculation_definitions` and dependencies: formula versions and lineage.
- `metric_applicability` and `coverage_status`: company/market/industry metric packs and gaps.
- `exceptions`, `backlog_items`, `jobs`, `job_attempts`, `workers`, and `schedules`: durable operations.

The row-based model can hold hundreds of target fields and thousands of period, segment, product, geography, counterparty, debt-instrument, asset-class, fair-value-level, and versioned facts per company without adding a database column for every metric. `company_core_v4` applies to every company; `oil_gas_v2` adds sector-specific segments, production, reserves, capacity, realized prices, costs, reliability, and environmental intensity measures.

## Backlog versus production data

The bundled backlog deliberately records missing historical periods, partial interim coverage, and any still-empty domain (for example market prices). Aramco's profile, ownership, disclosures, and corporate-action domain tasks now close automatically because those stores are populated. A backlog item is a planning/audit record, not a fact, and can never appear in production queries.

Refresh it at any time:

    finengine --db data/financial.sqlite3 backlog --refresh
    finengine --db data/financial.sqlite3 backlog SA 2222 --status active

Coverage gaps close automatically when validated facts arrive. Domain tasks close when their dedicated production store is populated. Catalog backfill is aggregated by category, so a company with hundreds of missing target fields remains operationally manageable while the exact missing keys stay queryable through completeness.

## Quality checks

    finengine --db data/financial.sqlite3 audit --project-root . --strict-warnings
    python -m unittest discover -s tests -v

GitHub Actions runs the same test suite on every push and pull request.

## Production deployment

The repository includes a production container with Chromium, the deterministic PDF reader, optional LLM reader support, a health check, persistent data storage, and automatic restart. Copy the environment template and replace the placeholder SEC identity before starting:

    copy .env.example .env
    docker compose up -d --build engine
    docker compose ps

The API listens only on `127.0.0.1:8000` by default. The `data` directory is mounted from the host, so the SQLite database, raw archive, job leases, monitoring cursors, schedules, and exceptions survive container replacement.

To add the read-only Telegram adapter after setting `TELEGRAM_BOT_TOKEN`:

    docker compose --profile telegram up -d

Saudi schedules created by `bootstrap` enable the browser monitor automatically. US schedules use SEC EDGAR and require a real `SEC_USER_AGENT`. Keep `.env` and `.secrets` local; both are excluded from Git and Docker build contexts.

## Production boundaries

- Confirm that source terms permit the intended collection, storage, and redistribution.
- Keep raw archives in durable object storage and back them up separately from the relational database.
- Use a secret manager for SEC contact details, API keys, and Telegram tokens.
- Add TLS, authentication, authorization, rate limiting, metrics, logs, and backups before exposing the service publicly.
- Treat the current Saudi and US datasets as a reviewed seed and coverage example, not a promise that every company domain is already complete.
- Keep probabilistic extraction below the publication boundary. Confidence thresholds reduce risk but do not replace reviewed mappings and deterministic validation.
