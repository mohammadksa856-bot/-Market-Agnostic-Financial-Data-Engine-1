# Production readiness and whole-market rollout

## Honest current status

The engine is production-shaped, but the bundled dataset is still a controlled
pilot. Its enabled registry contains Aramco, SABIC, ACWA Power, stc, Tawuniya,
all ten listed Saudi banks, Apple, Microsoft, and NVIDIA. It must
not be described as covering every Saudi and US listed company yet.

| Layer | Current readiness | What remains for whole-market use |
|---|---|---|
| Versioned financial database | Ready | Move to PostgreSQL before multiple publishing workers or hosts |
| Validation, restatements, quarter/YTD/TTM semantics | Ready and tested | Add sector acceptance cases as new issuers expose unusual presentations |
| US SEC fundamentals monitor | Official inventory synchronized; first 100-issuer batch enriched; a local `FLWS` acceptance run completed monitor/fetch/validate/publish with 1,780 facts | Move live archives to durable object storage, then expand eligible issuers in controlled batches and map custom XBRL tags and segment disclosures |
| Saudi market universe | Live connector acceptance archived 396 securities (272 Main, 124 Nomu), classified as 376 companies and 20 funds/REITs; snapshots are versioned. The read-only rollout inventory distinguishes discovery, staging, activation, exceptions, published facts, backlog, and completeness per security | Add licensed sector classifications where required and run controlled sector acceptance batches |
| Saudi issuer-report monitor | Live SABIC acceptance published 90 current facts from a Q2 2026 filing. Al Rajhi's official Q2 2026 XLSX verified 1,295 sourced facts and published 1,824 sourced/calculated points. STC's official H1 2026 PDF published 15 sourced facts and 23 sourced/calculated points. ACWA Power's image-only official Q2/H1 2026 statements were locally OCR'd into 39 sourced facts and 58 sourced/calculated points; all 11 accounting/quality checks passed. Tawuniya's hybrid two-page IFRS 17 statements produced 30 sourced facts and 41 sourced/calculated points with all five manifest checks passing. Browser discovery now falls back safely to a bounded ordinary document request when an official issuer CDN blocks both in-page CORS and browser request-context downloads. Exact upload dates embedded in Exchange attachment URLs are preserved | Verify discovery and unusual layouts on acceptance issuers from the remaining sectors before batch activation |
| Immutable source archive and lineage | Ready, including a self-verifying portable database/source bundle | Upload bundles to durable object storage and apply off-host retention rules |
| Read-only API and Telegram adapter | Ready for sourced database questions | Add consumer-specific response contracts, caching, rate limits, TLS, and production secrets |
| Daily prices and trading data | Partial pilot history | Connect an authorized Saudi/US OHLCV and corporate-action feed |
| Analyst consensus and forward estimates | Not populated | License an authoritative point-in-time estimates feed |
| News, event calendar, and research | Not populated as a complete product feed | Connect authorized feeds and retain their source/version metadata |
| Website integration | Not connected | Map the frontend to the API contract and remove all demonstration values |

## Aramco page readiness

The database can already supply a strong sourced core for an Aramco company page:
company profile, audited annual and quarterly statements, cash flow, balance sheet,
many calculated ratios, segments, oil-and-gas operating KPIs, ownership, corporate
actions, disclosures, dividends, and source/page/hash lineage.

It is not yet sufficient for every widget in a live investment product. Live
price and intraday market statistics, long market-price history, beta and technical
averages, analyst consensus, forward forecasts, news, peer rankings, community
content, and some issuer-specific qualitative analysis require additional feeds or
reviewed editorial data. An unavailable field must be returned as unavailable with
a reason; the API or frontend must never substitute a demonstration value.

Every consumer response should preserve at least:

- canonical field and value;
- unit, currency, scale, and dimensions;
- period kind, fiscal year/quarter, period start/end, and as-of time;
- reported, restated, calculated, or estimated status;
- official source URL, archived artifact hash, page/table, and retrieval time;
- formula and dependencies for calculated fields;
- freshness state and an explicit unavailable reason when applicable.

Frontend code must request a specific period kind. Selecting the newest date alone
can incorrectly mix a discrete quarter with YTD, FY, TTM, or a point-in-time value.
The `GET /v1/companies/{market}/{symbol}/page` contract enforces this separation,
reports availability for each consumer section, and never fills missing fields with
demonstration data.

## Whole-market rollout gates

1. Build authoritative security masters for every Saudi listing and the complete
   SEC ticker/CIK universe, including listings, aliases, fiscal calendars, new
   listings, mergers, symbol changes, and delistings.
2. Assign and continuously verify official report and announcement sources for
   every issuer. Run acceptance companies from each sector pack before enabling
   automatic publication for that sector.
3. Connect licensed market-data, corporate-action, consensus, and news sources.
   Keep their point-in-time history rather than overwriting old observations.
4. Expose one stable product API contract to the website and Telegram bot. Add
   cache policy, API authentication, TLS, monitoring, and per-field freshness SLAs.
5. Roll out in batches. New or low-confidence mappings remain in staging and the
   exception queue; AI output never bypasses deterministic validation.

## Always-on deployment

Requirements are a persistent Linux Docker host, a domain whose DNS points to
that host, a monitored contact address in `SEC_USER_AGENT`, a strong
`FINENGINE_API_KEY`, durable storage for runtime state and backups, and a
Telegram token only if the bot is enabled. A practical initial host is 4 vCPU,
8 GB RAM, and 150 GB or more of SSD storage. Use 200–300 GB NVMe for a
less constrained pilot and put the immutable archive in separate object
storage before whole-market rollout.

    cp .env.example .env
    # Replace example values in .env before continuing.
    # Prefer absolute host paths in production:
    # FINENGINE_STATE_DIR=/srv/finengine/state
    # FINENGINE_BACKUP_DIR=/srv/finengine/backups
    # API_DOMAIN=api.example.com
    mkdir -p /srv/finengine/state /srv/finengine/backups
    ./deploy/preflight.sh
    docker compose -f compose.yaml -f compose.production.yaml up -d --build
    docker compose -f compose.yaml -f compose.production.yaml --profile telegram up -d --build

To use Supabase as the permanent read database, apply
`supabase/migrations/0001_financial_facts.sql` to the Supabase project, set
`SUPABASE_URL` and the current `SUPABASE_SECRET_KEY` in `.env`, then add
`COMPOSE_PROFILES=supabase` (or `supabase,telegram`). The publisher continuously
upserts validated current facts and prunes withdrawn/restated projections; the
service-role key never reaches the website or Telegram client.

The production overlay adds Caddy, obtains and renews HTTPS certificates, and
proxies only the API. Ports 80 and 443 must reach the host. The engine itself
remains bound to localhost and also requires the API key for protected routes.

Code and runtime state are deliberately separate. Reviewed manifests and seed
source archives are baked into the image under `/app/data`; the live database,
new source documents, cursors, jobs, and exception state live under `/app/state`.
On the first boot only, the startup script builds a clean live database from the
reviewed manifests. Later releases never replace an existing database.

The engine startup script idempotently creates or updates one monitor schedule for
every enabled registry company. It does not duplicate schedules after restarts and
does not reset an existing next-run cursor. The worker uses durable jobs, leases,
retries, dead-job visibility, source cursors, and publication exceptions. The
universe refresh service archives the official SEC and Saudi Exchange inventories
daily without activating newly discovered issuers. The
backup service creates a portable ZIP containing an online SQLite snapshot and all
referenced raw sources, verifies every SHA-256 from its manifest, writes a bundle
sidecar, independently verifies the completed archive, writes atomic freshness
state to `backups/backup-status.json`, and retains the configured number of daily
bundles. Failures retry after a bounded delay instead of restart-hammering the
host. Copy that directory
to encrypted off-host or S3-compatible storage for disaster recovery.

### Automatic deployment from GitHub

The `deploy-production` workflow runs only after the `tests` workflow succeeds on
`main` (or by an explicit manual dispatch). Configure a protected GitHub
Environment named `production` and these encrypted secrets:

- `VPS_HOST`, `VPS_USER`, and `VPS_PORT`;
- `VPS_SSH_KEY` (a deploy-only private key);
- `VPS_KNOWN_HOSTS` (the server host-key line, captured through a trusted path);
- `DEPLOY_PATH` (the absolute repository checkout on the server).

After the first manual deployment succeeds, set the repository variable
`PRODUCTION_DEPLOY_ENABLED=true`. Until then, pushes remain safe: the automatic
deployment job is skipped instead of failing because the server is not configured.

The server checkout needs read access to the repository and a completed `.env`.
The deployment script refuses dirty tracked files, performs a fast-forward-only
pull, rebuilds the containers, and fails unless the engine becomes healthy. It
never resets Git state or deletes the persistent runtime directory.

Before the VPS is available, the `publish-supabase` workflow provides a safe
cloud bridge for reviewed data. Store `SUPABASE_URL` and `SUPABASE_SECRET_KEY`
in the protected `production` environment, then set the repository variable
`SUPABASE_PUBLISH_ENABLED=true`. After every successful `main` test run, and as
a six-hour repair schedule, it rebuilds from tracked manifests, enforces the
strict release audit, and only then upserts the current projection. It does not
perform live source monitoring; that remains the persistent engine's job.

SQLite supports one publishing worker. Keep a single engine/publisher instance
for this phase and move to PostgreSQL plus durable object storage before horizontal
scaling. Also replicate backup bundles off-host; a disk attached only to the same
server is not a disaster-recovery copy.

The server makes collection, validation, publishing, API, bot, backups, and
schedules independent of a laptop or an interactive AI session. It does not bypass
Codex or Claude usage limits; routine production ingestion must rely on this
deterministic engine, with agents reserved for new mappings and exceptions.
