# Saudi market relay registry

The Windows relay universe is generated from two tracked inputs:

- `scripts/seed-data/sa-manual-seed-2026-09-13.json`: the complete 439-symbol universe.
- `config/companies.json`: richer metadata and official source pages for known companies.
- `config/source-registry/sa-*.json`: reviewed official issuer source batches.

Run `python scripts/build_sa_market_registry.py` to update
`config/sa-market-registry.json`, or add `--check` in CI to fail when the tracked
output is stale. The builder rejects duplicate symbols, malformed activity flags,
unknown Saudi overrides, missing required fields, and inconsistent identities.

`scripts/windows_tadawul_relay.py` uses the generated registry by default. Before
starting a relay run it regenerates the file atomically when either tracked input
changes, then validates the complete registry. A custom `--registry` is never
rewritten, but it is still validated before network activity begins.

The Windows scheduled task runs a 20-company batch every 15 minutes and accepts
up to 40 historical statements per company. Its
`IgnoreNew` multiple-instance policy makes this effectively continuous without
overlapping Edge sessions when a batch takes longer than the trigger interval.
The Python entry point also holds an OS-backed lock at
`output/local-relay/relay.lock`, so a manual launch cannot overlap the scheduled
task.

## Durable raw archive and enqueue outbox

The relay is split into two independently runnable stages:

1. `--stage archive` discovers each official URL, downloads and validates the
   PDF/XLSX signature, writes a content-addressed local file, then writes the
   same verified hash to the immutable AWS raw path. It does not open the
   production database.
2. `--stage enqueue` reads `output/local-relay/outbox.json` and invokes
   `relay-enqueue` with the already archived AWS path. It performs no discovery,
   download, or upload.

`--stage all` runs those stages in order and is used by the scheduled task. A
database or queue failure leaves the entry as `pending_enqueue` and the overall
raw-archive stage successful; the next run retries only the enqueue call.
Likewise, an AWS interruption leaves a locally verified entry as
`pending_archive`, which is uploaded from disk before any new download.

The outbox is replaced atomically and flushed after every document and every
status transition. Its terminal statuses distinguish `job_created`,
`duplicate_job`, and `published_duplicate`; only `job_created` increments the
new-job counter. A malformed outbox is a hard error rather than being silently
reset, because losing it could cause duplicate network work.
