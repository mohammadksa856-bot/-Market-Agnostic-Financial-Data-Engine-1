# Qualitative reader and news connector

Two new reusable modules, built to answer a direct question from the data-
expansion workstream: can the manual, one-company-at-a-time qualitative
research process (used for `data/imports/alrajhi-company-profile-2025.json`
and `alrajhi-news-2026-09.json`) become software that runs without a human
re-reading the source document each time?

Both modules follow the same principle `reading_llm.py` already
established for financial facts: an LLM may propose a value, but nothing
it proposes reaches publication without a deterministic check that does
not trust the model's own claim.

## `src/finengine/reading_qualitative.py` — the multi-agent company-profile reader

Replaces the manual "read the annual report, cite the page" step for
`company_model` fields (business description, leadership, products,
subsidiaries, mission/vision, risk factors) with a pipeline that runs
without a human in the loop for the common case:

1. **Two independent extraction passes** over the same source pages, each
   using a differently-worded system prompt (one framed as populating a
   database, the other as fact-checking someone else's draft) so the two
   passes are not just two samples of the same correlated phrasing.
2. **Deterministic grounding check**: every finding must include an exact
   quote plus a page number. The quote is checked byte-for-byte (after
   whitespace/case normalization, tolerant of ±1 page numbering) against
   the actual page text — never trusted from the model.
3. **Agreement check**: only findings both passes independently
   reproduced, with matching values, and that are grounded in *both*
   passes, are `accepted`. Everything else — a single-pass finding, a
   disagreement, or a quote that isn't actually on the cited page — goes
   to `review_queue`, tagged with why, and must never be published
   directly.

A test (`test_unverifiable_quote_is_not_grounded_even_if_both_passes_agree`)
locks in the specific failure mode this design exists to catch: two
passes hallucinating the *same* wrong quote. Agreement between passes is
necessary but not sufficient — the grounding check is what actually
catches that case.

CLI: `finengine read-profile <pdf> <market> <symbol> --source-url URL
--filed-at DATE [--pages 10,11,224,225] [--out result.json]`. Without
`--pages` it reads the whole document (fine for shorter filings; for a
400+ page integrated annual report, pass the specific page ranges
already known to hold the profile/leadership/risk sections — the same
ranges a human would have jumped to).

Output is never auto-published. A caller (human or a future scheduled
job) must route `accepted` items through the normal
`company_attributes`/`disclosures` publication path, and `review_queue`
items to the exceptions table.

## `src/finengine/news_connector.py` — the widened news connector

Answers the "أبيها أوسع" (I want it wider) request: the pilot batch used
3 outlets (Reuters, Argaam, Maaal); the allowlist now has 17 named
sources across both tiers:

- **Tier 1 (official)**: Saudi Exchange issuer announcements, Saudi Press
  Agency, Capital Market Authority.
- **Tier 2 (press, always attributed)**: Reuters, Bloomberg, WSJ, FT,
  CNBC, Argaam, Maaal, Al-Eqtisadiah, Asharq Business, CNBC Arabia,
  Zawya, Mubasher, Arab News, Asharq Al-Awsat, Okaz.

The safety property is the same as the qualitative reader's: **the
allowlist check is deterministic, not a prompt instruction the model is
trusted to follow.** The search prompt tells the model to restrict itself
to these outlets (which helps relevance and reduces wasted search calls),
but every returned URL is independently parsed and matched against
`ALLOWLIST` by domain (including subdomains, e.g. `markets.ft.com`
matches `ft.com`) before it can reach `official` or `press`. Anything
from an unlisted domain is diverted to `rejected_offlist` — kept
visible, not silently dropped, so a reviewer can deliberately widen the
allowlist later rather than the filter quietly discarding evidence that
the search step is finding good sources outside it.
`test_off_allowlist_domain_is_rejected_even_if_model_returns_it` locks
this in: even a fake client that "misbehaves" and returns an off-list
result cannot get it published.

Uses Claude's server-side web-search tool (`web_search_20250305`) as the
retrieval mechanism. This is new to the codebase — `reading_llm.py`'s
structured-output pattern didn't previously combine with a tool — and the
exact tool-call shape here is based on current Anthropic API documentation
but has not been exercised against a live key in this session (no
`ANTHROPIC_API_KEY` was available); verify the tool name/version string
still matches the current API before the first live run.

CLI: `finengine news-search "<Company Name>" <market> <symbol> [--out
result.json]`.

## What this does NOT do yet

Both modules are library functions plus a manual CLI invocation — real
automation, in the sense that a single command now does what previously
took many manual browser/PDF steps, but **not yet wired into the
always-on production loop** (`finengine run`, the durable job queue,
`configure-production`'s per-company schedules). That loop already runs
for financial-statement monitoring on the production deployment; adding
these two as new scheduled job types (qualitative refresh: roughly
annual, since it only changes with a new annual report; news: daily per
the agreed cadence) is a `src/finengine/jobs.py` /
`operations.py` change — platform work, per `docs/WORKSTREAMS.md`'s
Codex/Claude split — not done in this commit.

Also not done: an `ANTHROPIC_API_KEY` was not available in this
environment, so neither module has been exercised end-to-end against the
live Anthropic API in this session — only against the injected fake
clients in `tests/test_reading_qualitative.py` and
`tests/test_news_connector.py`. The first real run against a live key
should be treated as a fresh acceptance test, not assumed to work
identically to the mocked tests.

## Tests

`tests/test_reading_qualitative.py` (5 tests) and
`tests/test_news_connector.py` (4 tests), both using the same fake-client
injection pattern `tests/test_reading_llm.py` already established. Full
repo suite: 200 passed, 1 skipped, 0 failed.
