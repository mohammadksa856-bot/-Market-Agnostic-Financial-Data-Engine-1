from __future__ import annotations

"""Official Saudi Exchange daily-price acquisition.

The Exchange historical-report page is browser-rendered and protects its JSON
route with the page's portal session.  This connector obtains that route from
the rendered table, reuses the same browser cookie jar, and returns a stable
source payload that can be archived before publication.
"""

import contextlib
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .fetching import _UA

_HALT_PLACEHOLDERS = {"", "-", "--", "n/a", "na", "null", "none"}


def _is_valid_group_shape(tokens: list[str], *, decimal_last: bool) -> bool:
    """Check a token run matches standard thousands grouping.

    The leading token may be 1-3 digits; every following token must be
    exactly 3 digits, except the run's final token when it carries the
    turnover's decimal fraction, whose integer part must be exactly 3 digits
    unless it is also the run's only token.
    """
    if not tokens:
        return False
    if not tokens[0].isdigit() or not (1 <= len(tokens[0]) <= 3):
        return False
    middle = tokens[1:-1] if decimal_last and len(tokens) > 1 else tokens[1:]
    if any(not (token.isdigit() and len(token) == 3) for token in middle):
        return False
    if decimal_last and len(tokens) > 1:
        last = tokens[-1]
        integer_part, _, fraction = last.partition(".")
        if not fraction or not integer_part.isdigit() or len(integer_part) != 3:
            return False
    elif decimal_last:
        integer_part, _, fraction = tokens[0].partition(".")
        if not fraction:
            return False
    return True


def parse_saudi_history_csv(text: str) -> tuple[list[dict], list[dict]]:
    """Deterministically parse the Exchange's exported CSV rows.

    Each row is ``date,open,high,low,close,volume,turnover,trades`` where the
    last three fields are thousands-grouped (e.g. ``1,215,120``) and the
    delimiter between fields is also a comma, so naive ``split(",")`` cannot
    tell a field boundary from a digit-group boundary, and a plain
    "3-digits-after-a-comma continues the number" regex is ambiguous whenever
    volume itself spans more than one group (both volume and turnover are
    then indistinguishable runs of 3-digit groups back to back).

    Rows are split on the first four commas to isolate the five ungrouped
    price fields (this market's prices never reach four digits, so they
    never carry a thousands separator themselves). The remaining comma-split
    tokens are partitioned into exactly three numbers - volume, turnover,
    trades - by finding the one token holding the decimal point (turnover is
    the only field with a fraction) and testing every possible volume/
    turnover split point against the standard grouping shape (leading token
    1-3 digits, every other token exactly 3 digits). Real trading data
    resolves to exactly one candidate split; when the shape check alone
    leaves more than one, the true split is the one whose turnover/volume
    ratio (the day's volume-weighted average price) falls inside that row's
    own [low, high] - a value no other split can satisfy by construction.
    Ambiguous or shapeless rows are excluded rather than guessed.

    Trading-halt rows (``-`` placeholders for OHLCV) are excluded, never
    zero-filled. Returns ``(rows, excluded)`` where ``rows`` are dicts shaped
    for :func:`normalize_saudi_market_rows` and ``excluded`` records the raw
    line plus the reason it was dropped.

    Some captures collapse row breaks into plain spaces instead of newlines
    (one giant line of space-joined rows) while others keep one row per
    physical line. Both are normalized the same way: every run of whitespace
    is collapsed to a single space, then the text is split right before each
    ``YYYY-MM-DD,`` date token, which is the one unambiguous row boundary
    common to both capture styles.
    """
    collapsed = re.sub(r"\s+", " ", text).strip()
    row_start = re.compile(r"(?=\d{4}-\d{2}-\d{2},)")
    candidate_lines = [segment.strip() for segment in row_start.split(collapsed) if segment.strip()]
    rows: list[dict] = []
    excluded: list[dict] = []
    for line in candidate_lines:
        if not line:
            continue
        parts = line.split(",")
        if len(parts) < 8:
            excluded.append({"line": line, "reason": f"expected >=8 comma fields, got {len(parts)}"})
            continue
        date_str, open_, high_, low_, close_ = parts[0], parts[1], parts[2], parts[3], parts[4]
        if any(field.strip().lower() in _HALT_PLACEHOLDERS for field in (open_, high_, low_, close_)):
            excluded.append({"line": line, "reason": "trading-halt placeholder in OHLC field"})
            continue
        try:
            open_d, high_d, low_d, close_d = (Decimal(open_), Decimal(high_), Decimal(low_), Decimal(close_))
        except InvalidOperation:
            excluded.append({"line": line, "reason": "non-numeric OHLC field"})
            continue
        if high_d < max(open_d, close_d) or low_d > min(open_d, close_d):
            excluded.append({"line": line, "reason": "failed OHLC sanity check (high/low out of range)"})
            continue
        tokens = parts[5:]
        decimal_positions = [index for index, token in enumerate(tokens) if "." in token]
        if len(decimal_positions) != 1:
            excluded.append({
                "line": line,
                "reason": f"expected exactly one decimal (turnover) token, found {len(decimal_positions)}",
            })
            continue
        decimal_idx = decimal_positions[0]
        candidates = []
        for start2 in range(1, decimal_idx + 1):
            group1, group2, group3 = tokens[:start2], tokens[start2:decimal_idx + 1], tokens[decimal_idx + 1:]
            if not group3:
                continue
            if not (_is_valid_group_shape(group1, decimal_last=False)
                    and _is_valid_group_shape(group2, decimal_last=True)
                    and _is_valid_group_shape(group3, decimal_last=False)):
                continue
            volume = int("".join(group1))
            turnover = Decimal("".join(group2))
            trades = int("".join(group3))
            candidates.append((volume, turnover, trades))
        if len(candidates) > 1:
            # Disambiguate with the day's volume-weighted average price,
            # which must fall within [low, high] for the correct split.
            in_range = [
                candidate for candidate in candidates
                if candidate[0] and low_d <= (candidate[1] / candidate[0]) <= high_d
            ]
            if len(in_range) == 1:
                candidates = in_range
        if len(candidates) != 1:
            excluded.append({
                "line": line,
                "reason": f"volume/turnover/trades split not uniquely determined ({len(candidates)} candidates)",
            })
            continue
        volume, turnover, trades = candidates[0]
        rows.append({
            "transactionDateStr": date_str,
            "todaysOpen": open_, "highPrice": high_, "lowPrice": low_,
            "previousClosePrice": close_,
            "volumeTraded": str(volume), "turnOver": str(turnover), "noOfTrades": str(trades),
        })
    return rows, excluded


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


def _entity_option_for(symbol: str, values: list[str]) -> str | None:
    """Match a listed symbol against the portal's entity option values.

    The historical-reports selector does not spell every issuer the same way:
    some options carry the bare symbol ("1150"), others pad it ("01150") or
    prefix the market ("SA1150"). Matching on the digits alone keeps the lookup
    working for issuers the exact-string comparison used to miss, while still
    refusing anything whose digits differ.
    """
    wanted = "".join(character for character in str(symbol) if character.isdigit())
    if not wanted:
        return None
    for value in values:
        digits = "".join(character for character in str(value) if character.isdigit())
        if digits and digits.lstrip("0") == wanted.lstrip("0"):
            return value
    return None


def _access_blocked(title: str, body_text: str) -> bool:
    """Recognize CDN denial pages before waiting for controls that do not exist."""
    evidence = f"{title}\n{body_text}".lower()
    return any(marker in evidence for marker in (
        "access denied", "permission to access", "errors.edgesuite.net",
    ))


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


def _archived_csv_payload(
    symbol: str, start_date: str, end_date: str, archived_csv_dir: str | Path,
    market_segment: str,
) -> bytes | None:
    """Build a source payload from previously archived official CSV exports.

    The directory is scoped to one listing by the caller.  We deliberately do
    not infer a symbol from CSV contents (the Exchange export has no symbol
    column), and conflicting observations fail closed instead of choosing one.
    Malformed and trading-halt rows are quarantined by
    :func:`parse_saudi_history_csv`.
    """
    archive = Path(archived_csv_dir)
    candidates = [archive] if archive.is_file() else sorted(archive.glob("*.csv"))
    if not candidates:
        return None

    requested_start = date.fromisoformat(start_date)
    requested_end = date.fromisoformat(end_date)
    by_date: dict[str, dict] = {}
    source_files: list[str] = []
    excluded_count = 0
    for candidate in candidates:
        rows, excluded = parse_saudi_history_csv(
            candidate.read_text(encoding="utf-8-sig", errors="strict"))
        excluded_count += len(excluded)
        accepted = False
        for item in normalize_saudi_market_rows(rows):
            observed = date.fromisoformat(item["observed_at"])
            if not requested_start <= observed <= requested_end:
                continue
            previous = by_date.get(item["observed_at"])
            if previous is not None and previous != item:
                raise ValueError(
                    "conflicting archived Saudi Exchange CSV observations for "
                    f"{symbol} on {item['observed_at']}"
                )
            by_date[item["observed_at"]] = item
            accepted = True
        if accepted:
            source_files.append(candidate.name)
    if not by_date:
        return None

    return json.dumps({
        "schema_version": 1,
        "source_url": SAUDI_HISTORICAL_REPORTS_URL,
        "symbol": symbol,
        "market_segment": market_segment,
        "sector_selector": None,
        "requested_start": start_date,
        "requested_end": end_date,
        "acquisition_method": "archived_official_csv",
        "archive_files": source_files,
        "excluded_rows": excluded_count,
        "market_prices": [by_date[key] for key in sorted(by_date)],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fetch_saudi_market_history_browser(
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
            title = page.title()
            body_text = page.locator("body").inner_text(timeout=min(timeout_ms, 10000))
            if _access_blocked(title, body_text):
                raise RuntimeError(
                    "Saudi Exchange historical reports access denied by the source CDN; "
                    "use an authorized network or licensed market-history feed"
                )
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
                try:
                    page.wait_for_function(
                        "document.querySelector('#entity') && "
                        "document.querySelector('#entity').options.length > 1",
                        timeout=min(timeout_ms, 10000),
                    )
                except Exception:
                    # Some sectors legitimately return no issuers. Continue to
                    # the next selector instead of failing the entire scan.
                    continue
                values = page.locator("#entity option").evaluate_all(
                    "els => els.map(e => e.value)")
                entity_value = _entity_option_for(symbol, values)
                if entity_value:
                    found_sector = sector_value
                    break
            if not found_sector:
                raise KeyError(f"symbol not present in Saudi Exchange historical selector: {symbol}")
            page.select_option("#entity", entity_value, force=True)
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
            # The portal's server-side table accepts its normal UI page sizes;
            # oversized values can return HTTP 200 with an empty data array.
            page_size = 100
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
    if total and not prices:
        raise RuntimeError(
            "Saudi Exchange returned an empty price payload for a non-empty result set")
    return json.dumps({
        "schema_version": 1, "source_url": SAUDI_HISTORICAL_REPORTS_URL,
        "symbol": symbol, "market_segment": market_segment,
        "sector_selector": found_sector, "requested_start": start_date,
        "requested_end": end_date, "market_prices": prices,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fetch_saudi_market_history(
    symbol: str, start_date: str, end_date: str, sector: str | None = None,
    market_segment: str = "Main Market", headless: bool = True,
    timeout_ms: int = 90000, archived_csv_dir: str | Path | None = None,
) -> bytes:
    """Fetch official history, falling back to an archived official CSV.

    This specifically keeps scheduled ingestion working when the public page's
    CDN blocks the worker or its dynamic sector selector never initializes.
    The original browser error remains authoritative when no usable archive is
    present.
    """
    try:
        return _fetch_saudi_market_history_browser(
            symbol, start_date, end_date, sector=sector,
            market_segment=market_segment, headless=headless,
            timeout_ms=timeout_ms,
        )
    except Exception:
        if archived_csv_dir is not None:
            archived = _archived_csv_payload(
                symbol, start_date, end_date, archived_csv_dir, market_segment)
            if archived is not None:
                return archived
        raise
