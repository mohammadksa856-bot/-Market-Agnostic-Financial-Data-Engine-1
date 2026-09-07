from __future__ import annotations

"""Locate an issuer's filed audited financial statements on the Saudi Exchange.

**Preferred: ``company_annual_fs_url``** reads the company-profile "Financial
Statements" tab (``statementType=6``), whose "Annual / <year>" cell links the
full **audited** consolidated FS - auditor's report + notes, filed ~March,
~1-4 MB. That is what the reader needs. It runs through the browser context
because the WebSphere portlet binds its data to the last-rendered company, so
the profile page must be navigated per symbol first.

**Fallback / discovery:** ``find_annual_results`` / ``fetch_annual_fs`` use the
announcements feed. The ``Resources/fsPdf`` attached to the "Annual Financial
Results" announcement is usually only the **earnings-release summary** (~0.3-1
MB, no notes); a few large caps attach the full statements. Good for confirming
the filing exists, its date and its announcement page.

Feed/announcement stages, split by how each endpoint behaves under automation:

* **Feed** — the announcements JSON endpoint
  (``...=NJgetAnnouncementListData=/``) accepts a plain, well-headed HTTP client
  but ignores every filter param and caps ``pageSize`` at 10, so it must be
  paged newest-first. ``refresh_feed`` pages it once for the whole market and
  caches the rows; every issuer is then filtered locally.
* **Discovery** — ``find_annual_results`` filters the cached feed by symbol + an
  annual-results title.
* **Resolution** — ``statement_pdf_url`` loads the announcement-details HTML to
  scrape the ``fsPdf`` link. Those pages sit behind a flaky WAF that rejects
  datacenter IPs intermittently, so this stage runs through the browser context
  (`fetching.BrowserFetcher`) — the same engine the rest of the fetch agent uses.

Nothing here extracts or publishes; it only produces an archive record.
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

_LIST_URL = (
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/"
    "issuer-news/issuer-announcements/!ut/p/z1/"
    "lY_NDoIwHMOfhQcwqxD-zOPUODAgTBjiLmYHY0h0ejA-v8Qb-BHsrcmvacsMa5hx9tGe7L29Onvu"
    "_N7QIRQEP-bIEVcLEEpJuuLTpU9s1wd4JglqI1TuRyFkDWb-yqMsQqhVkQUptpCgcXl8kRjRb_"
    "pILmZRt2A9l0kqAk7REPhwcVDy_uEF_BhZHh27XbRu0CYT4XlP_MzK5g!!/p0/"
    "IZ7_5A602H80O0HTC060SG6UT81DI1=CZ6_5A602H80O0HTC060SG6UT81D26="
    "NJgetAnnouncementListData=/"
)
_ANNOUNCEMENTS_PAGE = (
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/"
    "issuer-news/issuer-announcements?locale=en"
)
_DETAILS_URL = (
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/"
    "issuer-news/issuer-announcements/issuer-announcements-details/"
)
_ORIGIN = "https://www.saudiexchange.sa"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
_DEFAULT_CACHE = "data/raw/tadawul-announcement-feed.json"
_PAGE_SIZE = 10  # server hard cap; larger values are ignored

# title patterns for an *annual* results announcement, across issuer categories
# and the several phrasings issuers use ("annual financial results",
# "consolidated financial results for the year", "annual results for the period").
_ANNUAL = re.compile(
    r"annual\s+(consolidated\s+)?financial\s+(results|statements)"
    r"|(consolidated\s+)?financial\s+(results|statements)\s+for\s+the\s+year"
    r"|annual\s+results\s+for\s+the\s+(year|period)", re.I)
# exclude interim/quarterly filings that also mention "for the year to date" etc.
_INTERIM = re.compile(r"\binterim\b|\bquarter\b|nine[- ]month|six[- ]month|"
                      r"three[- ]month|first[- ]half|1st[- ]half", re.I)
_FS_PDF = re.compile(r"/Resources/fsPdf/[^\s\"'<>]+?\.pdf", re.I)


def _post(url: str, form: dict, *, opener=urlopen, tries: int = 4) -> bytes:
    body = "&".join(f"{k}={v}" for k, v in form.items()).encode("ascii")
    request = Request(url, data=body, headers={
        "User-Agent": _UA,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": _ANNOUNCEMENTS_PAGE,
        "Origin": _ORIGIN,
    })
    last = None
    for attempt in range(tries):
        try:
            with opener(request, timeout=30) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 - retry any transient failure
            last = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"announcement list request failed after {tries} tries: {last}")


def _row_date(row: dict):
    for value in (row.get("PR_DATE"), row.get("timestamp")):
        try:
            return datetime.strptime(str(value).strip().split(" 12:00")[0], "%b %d, %Y").date()
        except (TypeError, ValueError):
            continue
    return None


def _clean(row: dict) -> dict:
    return {
        "an_id": str(row.get("announcementNumber") or row.get("PRESS_REL_ID")),
        "symbol": str(row.get("SYMBOL", "")).strip(),
        "date": row.get("PR_DATE"),
        "title": row.get("SHORT_DESC", "") or "",
        "details_url": urljoin(_ORIGIN, (row.get("announcementUrl") or "")
                               .replace("\\u0026", "&").replace("\\u003d", "=")),
    }


def _page(page: int, opener) -> list[dict] | None:
    """One feed page. ``None`` on a hard failure (skip, keep walking); ``[]`` only
    when the server genuinely returns no rows (end of feed)."""
    try:
        payload = json.loads(_post(_LIST_URL, {
            "annoucmentType": "", "symbol": "", "sectorDpId": "", "searchType": "",
            "fromDate": "", "toDate": "", "datePeriod": "", "productType": "",
            "advisorsList": "", "textSearch": "", "pageNumberDb": str(page),
            "pageSize": str(_PAGE_SIZE),
        }, opener=opener).decode("utf-8"))
    except Exception:  # noqa: BLE001 - a single bad page must not abort the walk
        return None
    return payload.get("announcementList", [])


def refresh_feed(cache_path: str | Path = _DEFAULT_CACHE, *, since_days: int = 300,
                 max_pages: int = 1200, workers: int = 8, full: bool = False,
                 opener=urlopen) -> list[dict]:
    """Page the announcement feed and cache the rows.

    The feed only serves 10 rows a page, so pages are fetched in concurrent
    batches; the walk ends when a batch's oldest row predates the cutoff, the
    feed runs out, or -- unless ``full`` -- a row already in the cache is seen
    (an incremental top-up: only the first refresh pays the full ~10-15 min).
    One cache serves every issuer; ``find_annual_results`` reads it.
    """
    cutoff = date.today() - timedelta(days=since_days)
    path = Path(cache_path)
    existing: list[dict] = []
    known: set[str] = set()
    if path.is_file() and not full:
        try:
            existing = json.loads(path.read_text(encoding="utf-8")).get("rows", [])
            known = {r["an_id"] for r in existing}
        except Exception:  # noqa: BLE001 - a corrupt cache just forces a full walk
            existing, known = [], set()

    seen: set[str] = set()
    fresh: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        page = 1
        while page <= max_pages:
            span = list(range(page, min(page + workers, max_pages + 1)))
            batches = list(pool.map(lambda p: _page(p, opener), span))
            stop = False
            for batch in batches:
                if batch is None:
                    continue
                if not batch:
                    stop = True
                    continue
                for row in batch:
                    item = _clean(row)
                    if not item["an_id"] or item["an_id"] in seen:
                        continue
                    if item["an_id"] in known:
                        stop = True
                        continue
                    seen.add(item["an_id"])
                    fresh.append(item)
                oldest = _row_date(batch[-1])
                if oldest is not None and oldest < cutoff:
                    stop = True
            if stop:
                break
            page += workers

    merged = {r["an_id"]: r for r in existing}
    merged.update({r["an_id"]: r for r in fresh})
    rows = sorted(merged.values(), key=lambda item: item["an_id"], reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "refreshed_at": date.today().isoformat(), "since_days": since_days,
        "rows": rows,
    }, indent=1), encoding="utf-8")
    return rows


def _load_feed(cache_path: str | Path, *, refresh: bool, max_age_days: int,
               opener=urlopen) -> list[dict]:
    path = Path(cache_path)
    if not refresh and path.is_file():
        cached = json.loads(path.read_text(encoding="utf-8"))
        age = (date.today() - date.fromisoformat(cached["refreshed_at"])).days
        if age <= max_age_days:
            return cached["rows"]
    return refresh_feed(cache_path, opener=opener)


def find_annual_results(symbol: str, *, cache_path: str | Path = _DEFAULT_CACHE,
                        refresh: bool = False, max_age_days: int = 3,
                        opener=urlopen) -> list[dict]:
    """Annual-results announcements for ``symbol`` from the cached feed, newest first."""
    symbol = str(symbol).strip()
    feed = _load_feed(cache_path, refresh=refresh, max_age_days=max_age_days, opener=opener)
    hits = [
        r for r in feed
        if r["symbol"] == symbol
        and _ANNUAL.search(r["title"]) and not _INTERIM.search(r["title"])
    ]
    hits.sort(key=lambda item: item["an_id"], reverse=True)
    return hits


def _details_url(an_id: str, symbol: str) -> str:
    return f"{_DETAILS_URL}?anId={an_id}&anCat=1&cs={symbol}&locale=en"


def statement_pdf_url(an_id: str, symbol: str, *, fetcher=None,
                      html_getter=None) -> str | None:
    """Scrape the ``fsPdf`` link off an announcement-details page.

    Large caps attach the full audited FS PDF to their annual-results
    announcement (``Resources/fsPdf/…pdf``); many mid/small caps file only the
    summary form, in which case this returns ``None`` and the caller should fall
    back to the issuer's own annual report.

    Prefers ``fetcher`` (a ``fetching.BrowserFetcher``) because the details HTML
    is WAF-guarded; ``html_getter(url) -> str`` is an injection point for tests.
    """
    url = _details_url(an_id, symbol)
    if html_getter is not None:
        html = html_getter(url)
    elif fetcher is not None:
        html = _details_via_browser(url, fetcher)
    else:
        raise ValueError("pass fetcher=BrowserFetcher() (or html_getter for tests)")
    match = _FS_PDF.search(html or "")
    return urljoin(_ORIGIN, match.group(0)) if match else None


def _details_via_browser(url: str, fetcher) -> str:  # pragma: no cover - needs browser
    import contextlib

    with contextlib.ExitStack() as stack:
        context = fetcher._context(stack)
        page = context.new_page()
        page.goto(url, timeout=fetcher.timeout_ms, wait_until="domcontentloaded")
        with contextlib.suppress(Exception):
            page.wait_for_load_state("load", timeout=8000)
        page.wait_for_timeout(2000)
        return page.content()


_PROFILE_URL = (
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/"
    "!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8ziTR3NDIw8LAz93d2MXA0C3SydAl1c3Q0NvE30I4EK"
    "zBEKDMKcTQzMDPxN3H19LAzdTU31w8syU8v1wwkpK8hOMgUA-oskdg!!/?companySymbol="
)
def company_annual_fs_url(symbol: str, *, fetcher=None, year: int | None = None,
                          html_getter=None) -> tuple[str, str] | None:
    """The audited annual FS PDF for ``symbol`` from the profile "Financial
    Statements" tab. Returns ``(pdf_url, filed_date)`` for the newest annual row
    (or ``year``'s row), or ``None``.

    ``fetcher`` is a ``fetching.BrowserFetcher`` (needed - the portlet is
    per-company stateful). ``html_getter(symbol) -> str`` injects the rendered
    statements-tab HTML for tests.
    """
    if html_getter is not None:
        html = html_getter(symbol)
    elif fetcher is not None:
        html = _fs_tab_via_browser(str(symbol), fetcher)
    else:
        raise ValueError("pass fetcher=BrowserFetcher() (or html_getter for tests)")
    return _pick_annual_fs(html, year)


def _pick_annual_fs(html: str, year: int | None) -> tuple[str, str] | None:
    # rows look like: <th>2026</th><th>2025</th>... then an "Annual" row whose
    # cells hold <a href="/Resources/fsPdf/..."> and <p>YYYY-MM-DD</p>.
    header = re.search(r"<tr[^>]*>((?:\s*<th[^>]*>\s*\d{4}\s*</th>\s*)+)</tr>", html or "")
    years = re.findall(r"<th[^>]*>\s*(\d{4})\s*</th>", header.group(1)) if header else []
    block = re.search(r"<td[^>]*>\s*Annual\s*</td>(.*?)</tr>", html or "", re.S | re.I)
    if not years or not block:
        return None
    cells = re.findall(r"<td[^>]*>(.*?)</td>", block.group(1), re.S)
    picks: list[tuple[int, str, str]] = []
    for col_year, cell in zip(years, cells):
        href = re.search(r'href="(/Resources/fsPdf/[^"]+\.pdf)"', cell, re.I)
        filed = re.search(r"<p[^>]*>\s*([\d-]{8,10})", cell)
        if href:
            picks.append((int(col_year), urljoin(_ORIGIN, href.group(1)),
                          filed.group(1) if filed else ""))
    if not picks:
        return None
    if year is not None:
        picks = [p for p in picks if p[0] == year] or picks
    picks.sort(reverse=True)
    return picks[0][1], picks[0][2]


def _fs_tab_via_browser(symbol: str, fetcher) -> str:  # pragma: no cover - needs browser
    import contextlib

    with contextlib.ExitStack() as stack:
        context = fetcher._context(stack)
        page = context.new_page()
        page.goto(_PROFILE_URL + symbol, timeout=fetcher.timeout_ms,
                  wait_until="domcontentloaded")
        with contextlib.suppress(Exception):
            page.wait_for_load_state("load", timeout=10000)
        page.wait_for_timeout(4000)
        # the statements tab loads its data via NJstatementsTabData; ask for
        # statementType=6 directly on the now-current portlet.
        return page.evaluate(
            """async () => {
              const s=[...document.scripts].filter(x=>!x.src).map(x=>x.textContent).join('\\n');
              const m=s.match(/url:\\s*['\"]([^'\"]*NJstatementsTabData=\\/)['\"]/);
              if(!m) return '';
              const u=new URL(m[1], location.href.split('?')[0]+'/').href
                + '?statementType=6&reportType=0&requestLocale=en&symbol=' + %r;
              const r=await fetch(u); return await r.text();
            }""" % symbol)


def fetch_annual_fs(market: str, symbol: str, *, raw_dir="data/raw",
                    cache_path: str | Path = _DEFAULT_CACHE, refresh: bool = False,
                    year: int | None = None, fetcher=None, opener=urlopen) -> dict:
    """Archive the audited annual FS for ``symbol``: try the profile "Financial
    Statements" tab first (the real audited statements), then fall back to an FS
    PDF attached to the annual-results announcement."""
    from .fetching import BrowserFetcher

    fetcher = fetcher or BrowserFetcher(raw_dir=raw_dir)
    errors = []

    picked = None
    try:
        picked = company_annual_fs_url(symbol, fetcher=fetcher, year=year)
    except Exception as error:  # noqa: BLE001
        errors.append(f"profile tab: {error}")
    if picked:
        pdf_url, filed = picked
        record = fetcher.fetch(pdf_url, market, symbol)
        record.update(source_url=pdf_url, source="profile-financial-statements",
                      filed_at=filed or None)
        return record

    candidates = find_annual_results(symbol, cache_path=cache_path, refresh=refresh,
                                     opener=opener)
    for candidate in candidates:
        pdf_url = statement_pdf_url(candidate["an_id"], symbol, fetcher=fetcher)
        if not pdf_url:
            errors.append(f"announcement {candidate['an_id']}: no fsPdf")
            continue
        record = fetcher.fetch(pdf_url, market, symbol)
        record.update(announcement=candidate, source_url=pdf_url,
                      source="annual-results-announcement",
                      note="verify this is the audited FS, not the earnings release")
        return record

    raise RuntimeError(
        f"could not locate an FS PDF for {symbol}"
        + (f" (latest announcement anId {candidates[0]['an_id']}, "
           f"{candidates[0]['date']})" if candidates else " (no announcement either)")
        + f" -- {'; '.join(errors)}")
