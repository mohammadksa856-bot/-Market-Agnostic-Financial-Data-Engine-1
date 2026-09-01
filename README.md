# Market-Agnostic Financial Data Engine

An auditable financial data factory for Saudi and US companies. The production model is row-based and can hold hundreds or thousands of facts per company without adding a column for every metric. Every automated or AI-assisted result is confined to staging. Only deterministic normalization and validation code can open the publication gate.

## What is implemented

- Company registry seeded with Saudi Aramco and AAPL, MSFT, and NVDA.
- Source monitoring primitives and an interval scheduler.
- Live SEC Company Facts (EDGAR/XBRL JSON) fetcher with SEC-compliant identifying User-Agent.
- Configurable Saudi JSON manifest fetcher. This intentionally keeps unstable issuer/Saudi Exchange URLs in configuration rather than hard-coding private or undocumented endpoints.
- SHA-256 raw archive and source-level idempotency.
- US-GAAP and Arabic/English Saudi label mapping into canonical metrics.
- Persistent `extracted_facts`, `mapped_facts`, and `normalized_facts` staging layers.
- Source-faithful raw labels, values, page/table references, and XBRL taxonomy provenance.
- Exact dictionary mappings carry a confidence of 1.0; anything below 0.95 is blocked for review.
- Explicit instant, discrete-quarter, YTD, FY, and TTM semantics.
- Deterministic normalization (scale, Decimal values, units and currencies).
- Validation including the balance-sheet equation; failures go to an exception queue and do not publish.
- Immutable versions for restatements with one current observation.
- Multi-dimensional facts for segments, products, geographies, reserves, production and other company-specific details.
- Separate versioned stores for numeric facts, disclosures, company attributes and corporate events.
- A versioned metric catalog covering financial statements, ratios, calculated metrics and operational KPIs.
- FCF, net margin, liabilities/equity, and historical four-discrete-quarter TTM calculations.
- Atomic batch publication: a validated filing is fully published or fully rolled back.
- A durable background job queue with idempotency keys, leases, retries, exponential backoff, worker heartbeats and attempt history.
- Persistent schedules that survive restarts and a read-only query service with facts, snapshots, disclosures, attributes and health views.
- Separate company, security and listing identities so one company can have multiple securities or market listings.
- Dedicated versioned stores for daily/intraday market prices, ownership snapshots and structured corporate actions.
- Typed production facts (`decimal`, `text`, `date`, `boolean`, `json`) for financial, operational and general company data.
- A calculation registry that versions each formula and records its metric dependencies.
- Market, sector, industry and company metric packs with required/recommended/optional applicability rules.
- Automatic coverage scoring for every processed period, including missing required metrics and source freshness.
- Configurable freshness policies by market, sector, industry or company; no arbitrary SLA is imposed by default.
- Unit/integration tests and GitHub Actions.

## Data model

`data_points` is the canonical numeric/typed fact store. Its identity includes company, metric, period semantics, currency, unit, consolidation scope and an arbitrary dimension set. Examples of dimensions are `segment=Upstream`, `product=Crude oil`, `geography=Saudi Arabia` or `reserve_type=Proved`.

The other production domains are:

- `metric_definitions`: the versioned master schema and aggregation rules.
- `disclosures`: strategy, risks, guidance, management commentary and announcement text.
- `company_attributes`: general information such as employees, headquarters, activities and governance attributes.
- `corporate_events`: dividends, capital changes, acquisitions and other dated events.
- `securities` and `listings`: company-issued instruments and their market-specific symbols.
- `market_prices`: OHLCV/turnover time series kept outside filing facts.
- `ownership_positions`: holder snapshots with shares, ownership percentages and versions.
- `corporate_actions`: structured dividends, splits, rights issues, capital changes and their relevant dates.
- `calculation_definitions` and `calculation_dependencies`: auditable deterministic formula versions.
- `metric_applicability`: reusable market/sector/industry/company metric packs.
- `coverage_status`: expected versus available metrics for each period and domain.
- `freshness_policies`: reviewed age limits used to mark coverage as fresh or stale.
- `source_documents`: immutable provenance for every published item.

Raw PDFs, HTML, XBRL and JSON are archived as files; the database stores their hashes, paths, content types and processing state.

## Pipeline

    source monitor -> fetch -> immutable raw document
                   -> extracted_facts (source-faithful staging)
                   -> mapped_facts (canonical metric + confidence)
                   -> normalized_facts (deterministic code)
                   -> rules/validation gate
                   -> deterministic calculations
                   -> versioned production observations
                   -> read-only API / Telegram bot

Any extraction, mapping, or validation ambiguity goes to `exceptions`; a blocked source publishes zero observations. There is no method that publishes an extracted or mapped fact directly.

AI-assisted PDF table extraction belongs before mapping. It may write only source-faithful extracted facts, including location evidence, and never receives a production database write path.

## Quick start

Requires Python 3.11+ and no runtime packages.

    python -m venv .venv
    .venv/Scripts/pip install -e .       # Windows
    python -m finengine --db data/financial.sqlite3 init

SEC live ingest (replace the contact identity):

    set SEC_USER_AGENT=YourProduct your-email@example.com
    python -m finengine --db data/financial.sqlite3 ingest US AAPL

Saudi ingest uses a public issuer/Exchange adapter that produces the documented manifest contract:

    python -m finengine --db data/financial.sqlite3 ingest SA 2222 --sa-manifest https://your-source/aramco-2024.json

Read-only bot/API query:

    python -m finengine --db data/financial.sqlite3 query SA 2222 revenue

List up to 500 current facts, optionally filtered by category or period semantics:

    python -m finengine --db data/financial.sqlite3 facts SA 2222 --category financial

Show database and worker health:

    python -m finengine --db data/financial.sqlite3 status

Inspect the metric catalog and period coverage:

    python -m finengine --db data/financial.sqlite3 catalog --category financial
    python -m finengine --db data/financial.sqlite3 coverage SA 2222 --refresh

Read structured market/company domains:

    python -m finengine --db data/financial.sqlite3 prices SA 2222
    python -m finengine --db data/financial.sqlite3 ownership SA 2222
    python -m finengine --db data/financial.sqlite3 actions SA 2222 --type cash_dividend

Create a persistent US schedule and run the background worker:

    python -m finengine --db data/financial.sqlite3 schedule US AAPL --every 21600
    python -m finengine --db data/financial.sqlite3 worker

Saudi schedules require the approved public manifest adapter URL:

    python -m finengine --db data/financial.sqlite3 schedule SA 2222 --every 21600 --sa-manifest https://your-source/aramco-latest.json

The scheduler writes durable `jobs`; workers claim them with renewable leases. A crash or restart does not lose queued work. Repeated schedule ticks do not duplicate the same logical job.

Generate an Arabic browser report and Excel-compatible CSV:

    python -m finengine --db data/financial.sqlite3 report

Build staging audit rows for a database created by an older engine version (does not republish):

    python -m finengine --db data/financial.sqlite3 backfill-staging

Run tests:

    python -m unittest discover -s tests -v

## Saudi manifest contract

    {
      "filing_type": "annual-results", "filed_at": "2025-03-01",
      "period_end": "2024-12-31",
      "facts": [{
        "label": "Revenue", "value": 1000, "scale": 1000000,
        "currency": "SAR", "unit": "SAR",
        "period_start": "2024-01-01", "period_end": "2024-12-31",
        "period_kind": "fy", "fiscal_year": 2024, "fiscal_quarter": null
      }]
    }

For YTD values use period_kind=ytd; do not label them as a discrete quarter. TTM is calculated only from four discrete quarter observations. Restated sources receive a new source key and produce a new observation version.

## Production notes

- Use only sources whose terms permit your intended collection and redistribution. Do not bypass login, CAPTCHA, rate limits, or paid Saudi Exchange products.
- SEC requests must identify the operator and respect current SEC fair-access guidance.
- SQLite uses WAL, atomic publication and a durable queue and is suitable for local/single-writer operation. Use PostgreSQL before enabling several concurrent publisher processes or production-scale multi-host workers.
- Keep filing facts, market prices, ownership snapshots, disclosures and corporate actions in their dedicated stores; do not flatten them into one company spreadsheet.
- Metric packs express applicability rather than forcing every metric onto every company. Sector-specific KPIs remain optional until a reviewed pack enables them.
- Add authentication/rate limiting in the API layer; keep FinancialQueryService read-only.
- Review open exceptions before expanding the registry or enabling scheduled publication.
- Treat the 0.95 confidence threshold as a minimum publication policy, not as evidence that probabilistic output is correct.
