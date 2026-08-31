# Market-Agnostic Financial Data Engine

An auditable, dependency-light financial data factory for Saudi and US company filings. Every automated or AI-assisted result is confined to staging. Only deterministic normalization and validation code can open the publication gate.

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
- FCF, net margin, liabilities/equity, and four-discrete-quarter TTM calculations.
- SQLite publication store and a read-only query service.
- Unit/integration tests and GitHub Actions.

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
- SQLite is a working local store. For multiple writers, retain the model and migrate publication to PostgreSQL.
- Add authentication/rate limiting in the API layer; keep FinancialQueryService read-only.
- Review open exceptions before expanding the registry or enabling scheduled publication.
- Treat the 0.95 confidence threshold as a minimum publication policy, not as evidence that probabilistic output is correct.
