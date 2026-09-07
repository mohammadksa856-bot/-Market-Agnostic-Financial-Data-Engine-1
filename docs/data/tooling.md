# Data-expansion tooling — Tadawul FS locator + vision reader

Branch: `claude/tooling-tadawul-fetch-and-vision-reader`. **For integration
review** — this adds a module, a CLI verb and a reader entry point (Codex owns
the platform contract). Both pieces exist to speed up the sector-by-sector data
expansion; neither extracts or publishes on its own — output still passes
`finengine verify` and the deterministic publication gate.

---

## 1. `finengine tadawul-fs` — find an issuer's filed FS PDF

**Why:** many Saudi issuers publish only a board report + a summary on their own
site. The full audited statements are filed with the Exchange as
`saudiexchange.sa/Resources/fsPdf/<id>_<code>_<datetime>_en.pdf`, linked from the
announcement-details page. This locates that link so the fetch agent can archive
it.

**How it works** (`src/finengine/tadawul.py`):

| Stage | Endpoint | Automation notes |
|---|---|---|
| Feed | `…=NJgetAnnouncementListData=/` (POST) | Accepts a plain, well-headed HTTP client. **Ignores every filter param (symbol, date, type) and caps `pageSize` at 10**, and the server throttles concurrency, so it must be paged newest-first at ~1.5 s/page. `refresh_feed()` pages it in concurrent batches back `since_days` and caches the rows in `data/raw/tadawul-announcement-feed.json`. The **first** full refresh over ~240 days is ~10–15 min (~500 pages); after that it is an incremental top-up (stops at the first cached announcement) and takes seconds. |
| Discovery | (local) | `find_annual_results(symbol)` filters the cached feed by `SYMBOL` + an annual-results title regex. Instant. |
| Resolution | announcement-details HTML | Scrapes `/Resources/fsPdf/…pdf`. **These pages sit behind a flaky WAF that rejects datacenter IPs intermittently**, so this runs through `fetching.BrowserFetcher` (the `browser` extra: `pip install -e ".[browser]" && playwright install chromium`). **The attached PDF is usually the earnings release / summary, not the audited FS** (verified: SABIC Agri-Nutrients, Dallah, Mobily all attach a ~0.3-1 MB earnings release). Some large caps attach the full statements; some annual-results announcements have no attachment at all (Jarir). `fetch_annual_fs` archives whatever is linked and you must check it is the real statements (page count, notes section) before reading it. |

**Bottom line:** treat `tadawul-fs` as a **discovery** tool — it reliably tells you the annual-results filing exists, its date and its announcement page, for every listed company. The audited FS itself still often has to come from the issuer's own IR site or annual report.

**Usage:**

```
finengine tadawul-feed --since-days 240          # first run ~10-15 min; later runs incremental (seconds)
finengine tadawul-feed --full                     # force a complete re-page
finengine tadawul-fs SA 4190 --list              # show Jarir's annual-results announcements (from cache)
finengine tadawul-fs SA 4190                      # resolve + archive the filed FS PDF (needs browser extra)
finengine tadawul-fs SA 4190 --refresh            # incremental feed top-up first
```

`fetch_annual_fs()` returns the same archive record shape as `finengine fetch`
(`{status: "archived", sha256, local_path, source_url, announcement}`), so the
next step is the reader as usual.

**Tested:** the feed paging, incremental top-up, discovery filter and
link-scraping logic have unit coverage (`tests/test_tadawul.py`, stubbed HTTP).
The live feed endpoint returns clean JSON from a plain client (verified: 20-day
window → 400 rows in ~72 s with 8 workers). The browser-backed resolution step
needs Playwright and should be verified on a real run.

**Known limits:** the `!ut/p/z1/…` portlet path in `_LIST_URL` is a WebSphere
state token — if it rotates, refresh it from the Network tab of the
issuer-announcements page. Server-side filtering by symbol/date is not available,
and concurrency past ~8 workers gives no speed-up (server-side throttling).

---

## 2. `finengine read --vision` — read scanned statement pages as images

**Why:** the deterministic reader and the existing `--llm` pass both need an
extractable text layer. A large share of Saudi "signed" filings render the
primary statements as page images with no text at all, which is why the
sector batches so far were transcribed by hand.

**How it works** (`llm_read_vision` in `src/finengine/reading_llm.py`):

* Auto-detects the scanned statement pages (`_scanned_statement_pages`): pages
  with ≤ 25 words of text, at least one image, and a statement heading on the
  page or an immediate neighbour. Override with `--pages 8,9,10`.
* Renders each to PNG (pymupdf, `matrix=2.4`) and sends them as image blocks with
  the canonical-metric vocabulary and a strict JSON schema.
* Unlike `--llm`, it captures **every period column** printed on the page (so the
  manifest carries the prior-year comparative), keyed by `fiscal_year` /
  `period_end` per fact.
* Client-side validation is unchanged: unknown metric names and unparseable
  values are dropped, bracketed amounts become negative, `reader` is stamped
  `finengine.reading_llm_vision/<model>`, and the manifest is re-checked with
  `verify`.

**Usage:**

```
finengine read SA 4013 <fs.pdf> --vision \
  --source-url <url> --filed-at 2026-02-14 --fiscal-year 2025
```

Needs the `llm` extra (`anthropic` + `pymupdf`) and `ANTHROPIC_API_KEY`.
`finengine read <pdf> … --vision` also plugs into the monitor/job path via the
existing `--llm` payload flag (Codex to wire the `vision` flag through
`_read_pdf_manifest` if the automated pipeline should use it).

**Tested:** `tests/test_reading_llm.py` — two vision tests with a stub client and
a synthetic image-only PDF (both-column capture, bracketed-negative
normalisation, manifest passes `verify`). The live model call is not exercised in
CI (no API key).

---

## Combined flow for a new company

```
finengine tadawul-feed --since-days 300                    # once per session
finengine tadawul-fs SA <symbol>                           # -> archived PDF + source_url
finengine read SA <symbol> <archived.pdf> --llm --vision \ # deterministic -> text LLM -> vision
  --source-url <source_url> --filed-at <date> --fiscal-year <yyyy>
# -> manifest; review, drop into data/imports/, verify, bootstrap
```
