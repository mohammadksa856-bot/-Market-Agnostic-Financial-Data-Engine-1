# Market-Agnostic Financial Data Engine

An auditable, dependency-light pipeline for Saudi and US company filings. It stores raw documents, extracts reported facts into a shared canonical schema, validates them, preserves restatements, publishes versioned observations, calculates derived metrics, and exposes a read-only query boundary for an API or Telegram bot.

## What is implemented

- Company registry seeded with Saudi Aramco and AAPL, MSFT, and NVDA.
- Source monitoring primitives and an interval scheduler.
- Live SEC Company Facts (EDGAR/XBRL JSON) fetcher with SEC-compliant identifying User-Agent.
- Configurable Saudi JSON manifest fetcher. This intentionally keeps unstable issuer/Saudi Exchange URLs in configuration rather than hard-coding private or undocumented endpoints.
- SHA-256 raw archive and source-level idempotency.
- US-GAAP and Arabic/English Saudi label mapping into canonical metrics.
- Explicit instant, discrete-quarter, YTD, FY, and TTM semantics.
- Deterministic normalization (scale, Decimal values, units and currencies).
- Validation including the balance-sheet equation; failures go to an exception queue and do not publish.
- Immutable versions for restatements with one current observation.
- FCF, net margin, liabilities/equity, and four-discrete-quarter TTM calculations.
- SQLite publication store and a read-only query service.
- Unit/integration tests and GitHub Actions.

## Pipeline

    monitor -> fetch -> raw archive -> extract -> canonical map -> normalize
            -> validate -> publish/version -> calculate -> read-only query
                         \-> exception queue

AI-assisted PDF table extraction can be added before mapping, but it must emit the same structured manifest and never write directly to production.

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
- SQLite is a working local store. For multiple writers, retain the model and migrate publication to PostgreSQL.
- Add authentication/rate limiting in the API layer; keep FinancialQueryService read-only.
- Review open exceptions before expanding the registry or enabling scheduled publication.
