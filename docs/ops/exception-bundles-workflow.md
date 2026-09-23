# Exception bundles workflow — دليل تجميع الاستثناءات

Plain-English guide to `finengine exception-bundles`: what it is for, how to
read its output, and how a fix travels from "one bundle" back to "hundreds of
closed exceptions."

## The problem this solves

Every time a document fails somewhere in the pipeline (a caption the reader
doesn't recognize, a value it can't parse, a number that conflicts with an
already-published one, a source the fetcher couldn't reach), the engine
writes one row into the `exceptions` table (`src/finengine/database.py`,
`CREATE TABLE exceptions`). Reviewing those one at a time — reading the full
document each time — is expensive, and most of that expense is wasted: a
single reader bug or a single missing caption→metric mapping can be the root
cause behind hundreds of individually-filed exceptions.

`finengine exception-bundles` reads every **open** exception, groups the ones
that plausibly share one root cause, and prints one compact bundle per group.
A human or an AI reviewer reads the bundle (not the underlying documents),
writes **one** deterministic fix, and that one fix — after its own regression
test — closes every exception the bundle represents once the affected
documents are reprocessed.

## End-to-end pipeline

```
Server (worker/API)
   │
   ▼
archive → extract → map → validate   (Pipeline in pipeline.py; failures land in `exceptions`)
   │
   ▼
finengine exception-bundles           (this tool: read-only, groups + redacts, never touches data/imports or data/raw)
   │
   ▼
Claude/Codex (or a human) reviews ONE bundle
   │
   ▼
One deterministic fix                 (e.g. a new reading.py LINE_MAP entry, or an extraction.py/validation.py fix)
   │
   ▼
A regression test for that fix        (synthetic fixture, positive + negative case — see "Writing the regression test" below)
   │
   ▼
Server deployment (the normal release path — unaffected by this tool)
   │
   ▼
Reprocess the affected documents      (`finengine retry-source <source_key>` per affected document,
                                        or `resolve-source-exceptions` / `resolve-exception` once verified)
```

This tool only touches the loop between "exceptions exist" and "a fix is
proposed." It does not deploy anything, does not resolve exceptions itself,
and does not read or write `data/imports/**` or `data/raw/**`.

## Running it

```
PYTHONPATH=src python -B -m finengine.cli --db <scratch-or-prod-db-path> exception-bundles
```

Always pass an explicit `--db`. Flags:

- `--limit N` — how many open exceptions to read before bundling. The default
  `0` reads all open exceptions in deterministic pages of 1,000 rows.
- `--classification NAME` — only print bundles of one classification.
- `--output PATH` — write JSON Lines to a file instead of stdout.
- `--sort-by-priority` / `--no-sort-by-priority` — priority order is the
  default; pass `--no-sort-by-priority` for deterministic group-key order
  instead.

Output is **JSON Lines** (one JSON object per line), not one big JSON array,
so a reviewer (or a script) can process bundles one at a time without holding
the whole thing in memory, and so a diff between two runs is line-oriented.

## Reading a bundle

Every bundle has this shape (see `src/finengine/exception_bundles.py`,
`_build_one_bundle`):

```json
{
  "classification": "generic_mapping_fix",
  "group_key": {"reader": "inferred:mapping:application/pdf", "source_domain": "tadawul.com.sa",
                 "document_type": "financial-results", "stage": "mapping",
                 "code": "unmapped_metric", "metric": "Sales revenue",
                 "layout_fingerprint": null},
  "exception_count": 37,
  "exception_ids": [101, 104, 118, "... every real exception id, nothing summarized away"],
  "affected_companies": ["SA:1050", "SA:2280", "..."],
  "affected_companies_count": 12,
  "affected_documents": ["tadawul:1050:fy2024", "..."],
  "affected_documents_count": 20,
  "representative_samples": [
    {"exception_id": 101, "company_ref": "SA:1050", "raw_label": "Sales revenue",
     "raw_value": null, "unit": null, "table_context": "unmapped_metric",
     "source_page": null, "archived_source_path": "/archive/.../fy2024.pdf", "content_hash": "..."}
  ],
  "suggested_canonical_mappings": [{"candidate_metric": "revenue", "similarity": 0.83}],
  "deterministic_fix_possible": true,
  "deterministic_fix_reasoning": "A new LINE_MAP/BANK_LINE_MAP/INSURANCE_LINE_MAP caption entry closes every member of this group.",
  "estimated_exceptions_closed_by_one_fix": 37,
  "criticality": 3,
  "source_authority": 2,
  "status": "open",
  "resolved": false,
  "redactions_applied": false,
  "priority_score": 222
}
```

Key points:

- **At most 3 `representative_samples`**, each capped at a short length
  (`MAX_CONTEXT_CHARS` = 240 characters for the context field). No full
  document text ever appears. `archived_source_path` and `content_hash` are
  *references* to the archived source, never its content.
- **`exception_ids` is the full list**, every time — nothing is summarized
  away. That is the audit trail back to the real rows in `exceptions`.
- **`status`/`resolved`** are always `"open"`/`false` from this tool, on
  purpose: bundling is not resolving. A `not_applicable` or
  `source_unavailable` bundle still says `resolved: false` — grouping a
  field as "structurally can't be fixed right now" must never look like
  "this is done."
- **`redactions_applied`** is `true` if the safety-net secret scanner
  (`redact_secrets()`) had to remove anything AWS-key-shaped, bearer-token-
  shaped, JWT-shaped, or connection-string-shaped from a sample. Exception
  payloads should never contain secrets in the first place; this is a
  last-resort net, not the primary control.

## Classifications

Every bundle gets exactly one of these (`classify()` in
`exception_bundles.py`), checked in this order so a conflict never gets
mistaken for a generic fix:

1. **`data_conflict_or_restatement`** — a genuinely conflicting value across
   periods/sources (codes like `lower_trust_current_conflict`,
   `balance_sheet_unbalanced`, `period_rollforward_mismatch`, or anything
   with "conflict" in its code). These are grouped **per company and
   period**, never merged across companies — two different restatement
   conflicts are two different bundles even if they hit the same metric.
2. **`not_applicable`** — structurally inapplicable (e.g. an insurance-only
   field on a bank). Nothing to fix; the point of the bundle is just to make
   the "not applicable, not missing" status visible in bulk.
3. **`source_unavailable`** — the underlying source is unreachable/gone
   (timeouts, 404/410, access blocked). No fix closes these until the source
   is reachable again.
4. **`licensed_provider_required`** — needs a paid/licensed data source this
   project doesn't have (see the data-source decision in project memory: no
   paid API until the app earns revenue).
5. **`generic_mapping_fix`** — a caption→canonical-metric gap, the same
   shape as the existing `LINE_MAP`/`BANK_LINE_MAP`/`INSURANCE_LINE_MAP`
   entries in `reading.py`. `suggested_canonical_mappings` gives candidate
   metric keys from fuzzy-matching the raw caption against those maps and
   the enabled metric catalog — candidates with a similarity score, never a
   single asserted answer.
6. **`generic_parser_fix`** — a reader/parsing bug hitting many documents the
   same way (same reader, same stage, same failure code).
7. **`company_specific_review`** — the default when nothing above applies;
   doesn't generalize, needs individual attention.

## Grouping key

Exceptions are grouped by: reader/parser identity, source domain, document
type, pipeline stage, failure code, and metric/raw label — see
`resolve_reader()` and `_group_key()` in `exception_bundles.py`. Two
approximations are worth knowing about:

- **Reader/parser identity** is exact only for the PDF/XLSX reader-agent
  path (payload carries an explicit `"reader"` key: `"deterministic"`,
  `"deterministic+ocr"`, `"llm"`, `"xlsx-supplement"`, `"pillar3-km1"`) and
  for the fetch-stage `source_access_blocked` path (payload carries
  `"connector"`). Everywhere else — most extraction/mapping/validation
  exceptions, raised directly from `pipeline.py` — there is no reader field
  in the schema, so the tool falls back to `"inferred:<stage>:<content_type>"`
  as a labelled proxy.
- **`layout_fingerprint` is always `null`.** Neither `exceptions` nor
  `source_documents` stores anything like a column-position hash or a
  heading-pattern fingerprint. This is a real limitation, not an oversight:
  the field is emitted (so the bundle shape stays consistent and future
  code can start populating it) but never invented from unrelated data. If
  layout-sensitive grouping is wanted later, the reader agent in
  `reading.py` would need to compute and persist a fingerprint at
  extraction time — that is new engine work, not something this read-only
  tool can retrofit.

## Priority order

Default sort key, computed by `priority_score()`:

```
priority_score = criticality × affected_companies_count × estimated_exceptions_closed × source_authority
```

- **criticality** (3/2/1): from `data_catalog_fields.requirement` for the
  affected metric — `required` = 3, `recommended` = 2, `optional` = 1. A
  metric with no catalog entry defaults to 1 (we cannot claim it's central
  to the contract without a catalog entry saying so).
- **source_authority** (4/3/2/1): this project's own documented source tiers
  (`docs/SOURCE_MAP.md`: **P**rimary issuer/exchange/auditor = 4,
  **C**omputed by this engine = 3, named **S**econdary press/vendor = 2,
  third-party **O**pinion = 1). A handful of domains this project fetches
  directly (`sec.gov`, `tadawul.com.sa`, `saudiexchange.sa` → P;
  `argaam.com`, `mubasher.info`, `reuters.com`, `bloomberg.com` → S) are
  pinned; an unrecognized domain defaults to S (2) rather than assuming
  primary authority it hasn't earned.
- **estimated_exceptions_closed** — for `generic_parser_fix` /
  `generic_mapping_fix` / `not_applicable` / `source_unavailable` /
  `licensed_provider_required`, this is the group's own `exception_count`
  (every member is assumed to close, or to carry the same non-fixable
  status, together). For `data_conflict_or_restatement` and
  `company_specific_review`, it is 1 — these do not close in bulk by
  definition.

## What a reviewer actually does with a bundle

1. Read the bundle (not the source documents). The 1–3 samples plus
   `suggested_canonical_mappings` are meant to be enough context.
2. Write one deterministic fix:
   - `generic_mapping_fix` → add a caption entry to `LINE_MAP` /
     `BANK_LINE_MAP` / `INSURANCE_LINE_MAP` in `src/finengine/reading.py`.
   - `generic_parser_fix` → fix the extraction/mapping/validation logic in
     `reading.py` / `extraction.py` / `mapping.py` / `validation.py`.
   - `data_conflict_or_restatement` / `company_specific_review` → this
     needs a human decision on the specific case(s); the bundle's
     `exception_ids` point at exactly which rows to look at.
   - `source_unavailable` / `licensed_provider_required` → no code fix;
     revisit later (source comes back, or the project adopts a licensed
     feed — see the data-source decision in project memory).
3. **Writing the regression test**: follow this project's existing
   convention for reader fixes — a synthetic PDF/XLSX fixture with a
   **positive case** (the new caption/label, asserted to map to the right
   canonical metric) and a **negative case** (a similar-but-different
   caption that must NOT match, so the fix doesn't over-generalize). See
   `tests/test_reading.py` for the established pattern (e.g.
   `test_reordered_net_commission_label_is_not_gross_income`,
   `test_two_different_statements_on_one_spread_are_isolated`) — most tests
   there follow the same positive/negative shape.
4. Deploy the fix through the normal release path (unrelated to this tool;
   this project's API/worker split is Codex's work and is out of scope
   here).
5. **Reprocess the affected documents.** Use `finengine retry-source
   <source_key>` for each `source_key` in `affected_documents` (it re-runs
   the pipeline against the already-archived bytes — no new fetch). Once the
   reprocessed run publishes cleanly, the exceptions it used to raise close
   themselves; anything still open after a retry either wasn't actually
   fixed by that change or needs `resolve-exception` /
   `resolve-source-exceptions` with a human-written resolution note.

## Known limitations

- **Large queues are paginated**, not silently truncated. Each database read
  is capped at 1,000 rows, while the command continues until every open
  exception is included. Use `--limit N` only when intentionally sampling.
- **`layout_fingerprint` has no data source** in the current schema (see
  above) — always `null`.
- **Reader/parser identity is inferred**, not verified, for most exceptions
  (see above) — it is a proxy (`stage` + `content_type`), documented as such
  everywhere it is used.
- **`suggested_canonical_mappings` are candidates, not assertions.** They
  come from fuzzy string matching (Python's `difflib`) against known
  mapped captions and the enabled metric catalog, with a similarity score.
  A low-confidence or empty suggestion list is expected and correct for a
  caption nothing resembles yet.
