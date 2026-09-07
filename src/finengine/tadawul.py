from __future__ import annotations

"""Locate an issuer's filed financial-statement PDF on the Saudi Exchange.

Many Saudi issuers publish only a board report + a summary on their own website;
the full audited statements are filed with the Exchange as
``saudiexchange.sa/Resources/fsPdf/<id>_<code>_<datetime>_en.pdf``, linked from
the announcement-details page. This module finds that link so the fetch agent can
archive it.

Three stages, split by how each endpoint behaves under automation:

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

# title patterns for an *annual* results announcement, any issuer category
_ANNUAL = re.compile(
    r"annual\s+(consolidated\s+)?financial\s+(results|statements)"
    r"|annual\s+results\s+for\s+the\s+(year|period)", re.I)
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
    hits = [r for r in feed if r["symbol"] == symbol and _ANNUAL.search(r["title"])]
    hits.sort(key=lambda item: item["an_id"], reverse=True)
    return hits


def _details_url(an_id: str, symbol: str) -> str:
    return f"{_DETAILS_URL}?anId={an_id}&anCat=1&cs={symbol}&locale=en"


def statement_pdf_url(an_id: str, symbol: str, *, fetcher=None,
                      html_getter=None) -> str | None:
    """Scrape the ``fsPdf`` link off an announcement-details page.

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


def fetch_annual_fs(market: str, symbol: str, *, raw_dir="data/raw",
                    cache_path: str | Path = _DEFAULT_CACHE, refresh: bool = False,
                    fetcher=None, opener=urlopen) -> dict:
    """Full flow: find the latest annual-results announcement for ``symbol``,
    resolve its filed-FS PDF, and archive it through the browser fetch agent."""
    from .fetching import BrowserFetcher

    fetcher = fetcher or BrowserFetcher(raw_dir=raw_dir)
    candidates = find_annual_results(symbol, cache_path=cache_path, refresh=refresh,
                                     opener=opener)
    if not candidates:
        raise RuntimeError(
            f"no annual-results announcement found for {symbol} "
            "(try refresh=True / --refresh)")
    errors = []
    for candidate in candidates:
        pdf_url = statement_pdf_url(candidate["an_id"], symbol, fetcher=fetcher)
        if not pdf_url:
            errors.append(f"{candidate['an_id']}: no fsPdf link")
            continue
        record = fetcher.fetch(pdf_url, market, symbol)
        record.update(announcement=candidate, source_url=pdf_url)
        return record
    raise RuntimeError(
        f"found {len(candidates)} annual announcement(s) for {symbol} but no PDF: "
        + "; ".join(errors))
