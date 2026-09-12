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

## `src/finengine/rss_news_connector.py` — zero-cost news via public RSS feeds

Added after live-testing `news_connector.py` against the real API surfaced
a real cost problem: one `find_news` run (Opus 5, live, 2026-09-12)
consumed roughly **$1.04** (47,122 input / 3,157 output tokens, 12 web
searches) -- switching the default model to Haiku 4.5 cut that to
roughly **$0.02** (measured the same way, same day), but running either
one daily across hundreds of companies is still a real, non-trivial
recurring cost purely for *discovering* news, before any is even
published.

This module removes that cost for whatever it can cover: it polls named
outlets' own public RSS feeds directly (no LLM, no search tool, a plain
HTTP GET) and matches company names/aliases against each item's title
and description with case-insensitive substring matching (Arabic and
English both handled -- normalization strips the invisible LTR/RTL marks
these feeds' Arabic-adjacent English titles carry). Verified live against
Argaam's own "company disclosures" and "companies" RSS feeds
(`https://www.argaam.com/en/rss/...`) on 2026-09-12: a real, current
Qassim Cement acquisition disclosure was found with the correct title,
URL, and timestamp, at **zero API cost**.

**Coverage is intentionally partial, and grows by adding verified feeds,
not by loosening the matching logic.** Researched during development:
Reuters discontinued public RSS feeds entirely (no URL exists to add);
Arab News's advertised `/rss` endpoint returned an empty/non-XML response
on a plain GET (needs investigation -- a browser-rendered fetch or
different request headers, not assumed unusable). Only Argaam's two feeds
are wired in as of this commit; every other outlet in
`news_connector.py`'s `ALLOWLIST` remains reachable only through the paid
LLM+search path until its own RSS feed (if any) is found and verified the
same way.

**Recommended order for a real monitoring job**: try
`rss_news_connector.find_news_rss` first (free, frequent -- hourly is
fine); fall back to `news_connector.find_news` (paid, Haiku by default)
only for a company/outlet combination the RSS path has not covered over
some longer window. This module does not decide that fallback policy
itself -- it only reports what it found, plus `feed_errors` for any feed
that failed to fetch or parse, surfaced rather than silently treated as
"no news this run".

CLI: `finengine news-search-rss "<Company Name>,<alias>" <market>
<symbol> [--out result.json]`.

## `src/finengine/email_alerts_connector.py` — zero-cost news via Google Alerts

A second free source, added on request after the user recalled using
Google Alerts (keyword-based email notifications) for exactly this kind
of monitoring before. Google itself does the discovery here -- its own
web crawler, covering far more sites than the two feeds
`rss_news_connector.py` currently polls -- this module only reads the
alert emails Google already sends and decodes each result's Google
redirect link (`google.com/url?...&url=<encoded real URL>&...`) back to
its real destination, which is then checked against the exact same
`news_connector.ALLOWLIST` domain gate as every other source in this
pipeline. Broader discovery does not relax the trust bar: an alert
pointing at an unlisted domain (an anonymous blog, a rumor site) is
reported in `rejected_offlist`, never published, proven by a test using
a synthetic alert email that mixes one Argaam result with one
off-allowlist blog result in the same message.

Setup this module needs and cannot do on its own: an active Google Alert
per company, delivered to a Gmail inbox; and a Gmail **App Password**
for that inbox (`myaccount.google.com/apppasswords`, requires 2-Step
Verification) -- never the account's real password. Both go in `.env` as
`GOOGLE_ALERTS_EMAIL` / `GOOGLE_ALERTS_APP_PASSWORD`, the same pattern as
`ANTHROPIC_API_KEY`.

Uses only the Python standard library (`imaplib`, `email`,
`html.parser`) -- no new dependency. The HTML parser deliberately does
not assume a specific div/class structure inside the alert email (Google
has changed that markup before); it looks only for the `url=` redirect
pattern, the one part that has stayed stable.

**Recommended layering for a real monitoring job, cheapest first:**
1. `rss_news_connector.py` (verified outlets' own feeds -- free, narrow)
2. `email_alerts_connector.py` (Google's own crawl via Alerts -- free,
   broad, depends on an alert already existing for the company)
3. `news_connector.py` (LLM + web search -- paid, Haiku by default,
   reserved for whatever the free layers do not surface)

CLI: `finengine news-search-email-alerts <market> <symbol> [--since-days 2]
[--mailbox INBOX] [--out result.json]` (reads credentials from the
environment, refuses to run with a clear message if they are not set).

## Scoping news coverage to the full Saudi market, not just the pilot registry

The 31-company pilot registry above is a small slice of the real Saudi
market. Checked live against Tadawul's own `main-market-watch` page
(`searchableSymbols`, 2026-09-12): **292 Main Market entities** (`market_type
"M"`, which includes 19 REITs as one of its own sectors -- confirmed by
reading the live Main Market Watch table itself) + **147 Nomu (parallel
market) entities** (`market_type "S"`) = **439 real listed equities today**.
This is higher than the commonly-cited "272 Main Market / 396 total" figures
(the market has grown since those were current) -- treat the live count as
the source of truth, not any cached figure in this repo or elsewhere. The
other `searchableSymbols` codes (`C` traded funds, `B`/`O` sukuk, `E` ETFs,
`D` options/derivatives, `F` non-traded funds) are not operating companies
and are out of scope for company news.

**Decision: do not mass-create a per-company Google Alert for all 439
entities.** Reason, found live rather than assumed: Argaam's two RSS feeds
that `rss_news_connector.py` already polls are themselves **market-wide**,
not scoped to whichever companies happen to be passed in -- a real poll on
2026-09-12 surfaced disclosures for Horizon Educational, Al-Jouf
Agricultural, UCA, SARCO, IA, FIPCO, SABIC AN, National Gypsum, Edarat,
Qomel, Smile Care, KEC, and Elm, none of which are in the pilot registry or
have a Google Alert configured anywhere. `find_news_rss` filters that
market-wide feed down to whatever company names you pass it, but the
underlying feed already covers the whole market for zero cost and zero
per-company setup. Manually clicking through Google's UI to create ~400
more individual alerts would mostly duplicate that coverage while adding
real setup time and standing external state (400+ rules) in one personal
Gmail account for marginal benefit.

**What this means in practice**: the 32 Google Alerts already created
(pilot registry + one Arabic alert) stay as-is -- a supplementary layer for
that batch, not a pattern to repeat for the rest of the market. For the
remaining ~408 entities, `rss_news_connector.py` is the primary zero-cost
layer; `news_connector.py` (paid, Haiku) is the fallback for whatever a
company's RSS-covered outlets do not surface. The real gap worth closing
next is **feed breadth**, not per-company alert count: today only Argaam's
two feeds are wired in (see above) -- adding a second market-wide feed
(Maaal, Mubasher, or another allowlisted outlet, if one exists) would widen
coverage for all ~439 companies at once, the same zero-cost way, rather
than scaling a manual per-company process.

## Tests

`tests/test_reading_qualitative.py` (6 tests), `tests/test_news_connector.py`
(4 tests), `tests/test_rss_news_connector.py` (6 tests), and
`tests/test_email_alerts_connector.py` (4 tests) -- all using fake
fetchers/connectors, no real network call anywhere in the test suite.
Full repo suite: 211 passed, 1 skipped, 0 failed.
