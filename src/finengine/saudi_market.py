from __future__ import annotations

"""Official Saudi Exchange daily-price acquisition.

The Exchange historical-report page is browser-rendered and protects its JSON
route with the page's portal session.  This connector obtains that route from
the rendered table, reuses the same browser cookie jar, and returns a stable
source payload that can be archived before publication.
"""

import contextlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation

from .fetching import _UA


SAUDI_HISTORICAL_REPORTS_URL = (
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/"
    "reports-publications/historical-reports?locale=en"
)

SECTOR_CODES = {
    "Energy": "TENI:31", "Materials": "TMTI:32", "Capital Goods": "TCGI:33",
    "Commercial & Professional Services": "TCPI:34", "Transportation": "TTNI:35",
    "Consumer Durables & Apparel": "TDAI:37", "Consumer Services": "TCSI:38",
    "Media and Entertainment": "TMDI:39",
    "Consumer Discretionary Distribution & Retail": "TRLI:40",
    "Consumer Staples Distribution & Retail": "TFSI:41", "Food & Beverages": "TFBI:42",
    "Household & Personal Products": "THPI:43", "Health Care Equipment & Services": "THEI:44",
    "Pharma, Biotech & Life Science": "TPBI:45", "Banks": "TBNI:46",
    "Financial Services": "TDFI:47", "Insurance": "TISI:48",
    "Software & Services": "TSSI:49", "Telecommunication Services": "TTSI:52",
    "Utilities": "TUTI:53", "REITs": "TRTI:21", "Real Estate Management & Development": "TRMI:54",
}


def _number(value) -> str | None:
    text = str(value or "").strip().replace(",", "")
    if text in {"", "-", "--", "null", "None"}:
        return None
    try:
        return str(Decimal(text))
    except InvalidOperation as error:
        raise ValueError(f"invalid Saudi Exchange number: {value!r}") from error


def normalize_saudi_market_rows(rows: list[dict]) -> list[dict]:
    """Normalize the Exchange's historical-table JSON without inventing data."""
    normalized, seen = [], set()
    for row in rows:
        observed = str(row.get("transactionDateStr") or row.get("transactionDate") or "")
        observed = observed.strip().replace("/", "-")
        try:
            observed = date.fromisoformat(observed[:10]).isoformat()
        except ValueError as error:
            raise ValueError(f"invalid Saudi Exchange trading date: {observed!r}") from error
        if observed in seen:
            continue
        close = _number(row.get("previousClosePrice"))
        if close is None:
            continue
        item = {
            "observed_at": observed,
            "interval": "1d",
            "open": _number(row.get("todaysOpen")),
            "high": _number(row.get("highPrice")),
            "low": _number(row.get("lowPrice")),
            # Despite its legacy JSON name, this field backs the visible Close
            # column on the official report page.
            "close": close,
            "volume": _number(row.get("volumeTraded")),
            "turnover": _number(row.get("turnOver")),
            "currency": "SAR",
        }
        seen.add(observed)
        normalized.append(item)
    normalized.sort(key=lambda item: item["observed_at"])
    return normalized


def fetch_saudi_market_history(
    symbol: str, start_date: str, end_date: str, sector: str | None = None,
    market_segment: str = "Main Market", headless: bool = True,
    timeout_ms: int = 90000,
) -> bytes:
    """Fetch one security's official daily history through a portal session."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:  # pragma: no cover - optional runtime
        raise RuntimeError("Saudi market history needs the optional browser extra") from error

    market_value = "NOMUC" if "nomu" in market_segment.lower() else "MAIN"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            context = browser.new_context(user_agent=_UA, locale="en-US")
            page = context.new_page()
            page.goto(SAUDI_HISTORICAL_REPORTS_URL, timeout=timeout_ms,
                      wait_until="domcontentloaded")
            page.wait_for_selector("#marketOrIndices", timeout=timeout_ms)
            page.select_option("#marketOrIndices", market_value, force=True)
            page.wait_for_function(
                "document.querySelector('#sectors').options.length > 1", timeout=timeout_ms)

            options = page.locator("#sectors option").evaluate_all(
                "els => els.map(e => ({value:e.value,text:(e.textContent||'').trim()}))")
            preferred = SECTOR_CODES.get(sector or "")
            candidates = ([preferred] if preferred and any(
                option["value"] == preferred for option in options) else [])
            candidates.extend(option["value"] for option in options
                              if option["value"] not in {"0", preferred})
            found_sector = None
            for sector_value in candidates:
                page.select_option("#sectors", sector_value, force=True)
                page.wait_for_timeout(250)
                values = page.locator("#entity option").evaluate_all(
                    "els => els.map(e => e.value)")
                if symbol in values:
                    found_sector = sector_value
                    break
            if not found_sector:
                raise KeyError(f"symbol not present in Saudi Exchange historical selector: {symbol}")
            page.select_option("#entity", symbol, force=True)
            # These inputs are deliberately readonly because the public page
            # uses a date picker.  Set the value through the DOM and emit the
            # same events the picker would emit; Locator.fill cannot edit a
            # readonly control on the production page.
            page.evaluate("""({startDate,endDate}) => {
                const setDate=(selector,value) => {
                    const input=document.querySelector(selector);
                    if (!input) throw new Error(`missing date input: ${selector}`);
                    const setter=Object.getOwnPropertyDescriptor(
                        HTMLInputElement.prototype,'value').set;
                    setter.call(input,value);
                    input.dispatchEvent(new Event('input',{bubbles:true}));
                    input.dispatchEvent(new Event('change',{bubbles:true}));
                };
                setDate('#startTimePeriod',startDate);
                setDate('#endTimePeriod',endDate);
            }""", {
                "startDate": date.fromisoformat(start_date).strftime("%d-%m-%Y"),
                "endDate": date.fromisoformat(end_date).strftime("%d-%m-%Y"),
            })
            with page.expect_response(lambda response: "populateCompanyDetails" in response.url,
                                      timeout=timeout_ms):
                page.evaluate("populateCompanyDetails(false)")
            page.wait_for_function(
                "() => $.fn.dataTable.isDataTable('#perfSummary') && "
                "$('#perfSummary').DataTable().ajax.json() != null", timeout=timeout_ms)
            settings = page.evaluate("""() => {
                const table=$('#perfSummary').DataTable();
                const json=table.ajax.json() || {};
                return {total:json.recordsTotal || json.recordsFiltered || 0,
                        firstRows:json.data || []};
            }""")
            # Pagination must also run through DataTables inside the rendered
            # page.  A separate Playwright request context can share cookies,
            # but the Exchange still rejects it because it lacks the exact
            # browser/XHR execution context (HTTP 403 on cloud hosts).
            all_rows = list(settings["firstRows"])
            page_size = 500
            total = max(int(settings["total"]), 1)
            for start in range(0, total, page_size):
                page_number = start // page_size
                result = page.evaluate("""({pageNumber,pageSize,timeoutMs}) =>
                    new Promise((resolve,reject) => {
                        const table=$('#perfSummary').DataTable();
                        const timer=setTimeout(
                            () => reject(new Error('Saudi Exchange DataTables request timed out')),
                            timeoutMs);
                        $('#perfSummary').one('xhr.dt', (_event,_settings,json,xhr) => {
                            clearTimeout(timer);
                            resolve({status:xhr ? xhr.status : 200,
                                     rows:(json && json.data) || []});
                        });
                        table.page.len(pageSize);
                        table.page(pageNumber).draw('page');
                    })
                """, {"pageNumber": page_number, "pageSize": page_size,
                       "timeoutMs": timeout_ms})
                if int(result["status"]) >= 400:
                    raise RuntimeError(
                        f"Saudi Exchange history request failed: HTTP {result['status']}")
                batch = result["rows"]
                # The first response was normally ten rows.  Replace it with
                # the requested full first page, then append later pages.
                if page_number == 0:
                    all_rows = []
                all_rows.extend(batch)
                if not batch or len(all_rows) >= total:
                    break
        finally:
            browser.close()

    prices = normalize_saudi_market_rows(all_rows)
    return json.dumps({
        "schema_version": 1, "source_url": SAUDI_HISTORICAL_REPORTS_URL,
        "symbol": symbol, "market_segment": market_segment,
        "sector_selector": found_sector, "requested_start": start_date,
        "requested_end": end_date, "market_prices": prices,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
