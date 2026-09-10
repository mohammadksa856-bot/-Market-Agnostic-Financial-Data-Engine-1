from __future__ import annotations

import csv
import contextlib
import hashlib
import io
import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .database import Database, _json
from .jobs import DurableJobQueue, DurableScheduler
from .models import Company, Market


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SAUDI_ISSUER_DIRECTORY_URL = (
    "https://www.saudiexchange.sa/wps/portal/saudiexchange/trading/"
    "participants-directory/issuer-directory?locale=en"
)
_EXCHANGE_PRIORITY = {
    "Nasdaq": 0, "NYSE": 1, "NYSE American": 2, "NYSE Arca": 3,
    "Cboe BZX": 4, "OTC": 20, "": 99,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def parse_sec_ticker_exchange(payload: dict) -> tuple[list[dict], list[dict]]:
    fields = payload.get("fields")
    data = payload.get("data")
    if not isinstance(fields, list) or not isinstance(data, list):
        raise ValueError("SEC ticker payload must contain fields and data arrays")
    required = {"cik", "name", "ticker", "exchange"}
    if not required.issubset(fields):
        raise ValueError(f"SEC ticker payload is missing: {', '.join(sorted(required-set(fields)))}")
    positions = {name: fields.index(name) for name in required}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for raw in data:
        if not isinstance(raw, list) or len(raw) < len(fields):
            continue
        cik = str(raw[positions["cik"]]).zfill(10)
        ticker = str(raw[positions["ticker"]] or "").strip().upper()
        name = str(raw[positions["name"]] or "").strip()
        exchange = str(raw[positions["exchange"]] or "").strip()
        if not cik.isdigit() or not ticker or not name:
            continue
        grouped[cik].append({"cik": cik, "name": name, "symbol": ticker,
                             "exchange": exchange})
    issuers, securities = [], []
    for cik, listings in sorted(grouped.items()):
        listings.sort(key=lambda item: (_EXCHANGE_PRIORITY.get(item["exchange"], 10),
                                        item["symbol"]))
        primary = listings[0]
        issuer_id = f"us:sec:{cik}"
        issuers.append({
            "issuer_id": issuer_id, "market": "US", "authority_id": cik,
            "name": primary["name"], "country": "US", "active": True,
            "primary_symbol": primary["symbol"], "primary_exchange": primary["exchange"],
            "metadata": {"cik": cik, "listing_count": len(listings)},
        })
        for index, listing in enumerate(listings):
            key_seed = f"{issuer_id}|{listing['exchange']}|{listing['symbol']}"
            securities.append({
                "security_key": "security-universe:" + hashlib.sha256(
                    key_seed.encode("utf-8")).hexdigest()[:24],
                "issuer_id": issuer_id, "market": "US", "symbol": listing["symbol"],
                "exchange": listing["exchange"], "currency": "USD", "active": True,
                "is_primary": index == 0, "metadata": {"cik": cik},
            })
    return issuers, securities


def parse_saudi_reference(content: bytes, suffix: str) -> tuple[list[dict], list[dict]]:
    """Parse a normalized Saudi Exchange/eReference export without inventing fields.

    Accepted columns: symbol, name, issuer_id, isin, exchange, currency, sector,
    industry, market_segment, active. JSON may be either a list or {"data": [...]}.
    """
    if suffix.lower() == ".json":
        payload = json.loads(content)
        rows = payload.get("data", []) if isinstance(payload, dict) else payload
    elif suffix.lower() == ".csv":
        rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    else:
        raise ValueError("Saudi universe input must be JSON or CSV")
    if not isinstance(rows, list):
        raise ValueError("Saudi universe input must contain a row list")
    issuers, securities = [], []
    seen_issuers = set()
    for row in rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        name = str(row.get("name") or row.get("name_en") or "").strip()
        authority_id = str(row.get("issuer_id") or row.get("isin") or symbol).strip()
        if not symbol or not name or not authority_id:
            continue
        issuer_id = f"sa:tadawul:{_slug(authority_id)}"
        active = str(row.get("active", "true")).lower() not in {"0", "false", "no", "inactive"}
        metadata = {key: row[key] for key in ("name_ar", "isin", "sector", "industry",
                    "market_segment", "instrument_type", "trading_name", "profile_url",
                    "website", "source_url") if row.get(key) not in (None, "")}
        if issuer_id not in seen_issuers:
            issuers.append({
                "issuer_id": issuer_id, "market": "SA", "authority_id": authority_id,
                "name": name, "country": "SA", "active": active,
                "primary_symbol": symbol,
                "primary_exchange": str(row.get("exchange") or "Saudi Exchange"),
                "metadata": metadata,
            })
            seen_issuers.add(issuer_id)
        exchange = str(row.get("exchange") or "Saudi Exchange")
        key_seed = f"{issuer_id}|{exchange}|{symbol}"
        securities.append({
            "security_key": "security-universe:" + hashlib.sha256(
                key_seed.encode("utf-8")).hexdigest()[:24],
            "issuer_id": issuer_id, "market": "SA", "symbol": symbol,
            "exchange": exchange, "currency": str(row.get("currency") or "SAR"),
            "active": active, "is_primary": True, "metadata": metadata,
        })
    return issuers, securities


def normalize_saudi_directory_rows(
    rows_by_market: dict[str, list[dict]],
    source_url: str = SAUDI_ISSUER_DIRECTORY_URL,
) -> bytes:
    """Convert the public issuer directory into the stable import contract.

    The directory is an identity inventory, not a fundamentals source. Funds
    remain visible in the security universe but are typed explicitly so later
    activation policy can distinguish them from operating companies.
    """
    normalized = []
    seen: set[tuple[str, str]] = set()
    market_names = {"M": "Main Market", "S": "Nomu - Parallel Market"}
    for market_code in ("M", "S"):
        for raw in rows_by_market.get(market_code, []):
            symbol = str(raw.get("symbol") or "").strip().upper()
            name = str(raw.get("lonaName") or raw.get("longName") or
                       raw.get("name") or "").strip()
            trading_name = str(raw.get("shortName") or raw.get("trading_name") or "").strip()
            isin = str(raw.get("isinCode") or raw.get("isin") or "").strip().upper()
            if not symbol or not name or not isin or (market_code, symbol) in seen:
                continue
            seen.add((market_code, symbol))
            label = f"{name} {trading_name}".lower()
            instrument_type = "fund" if re.search(r"\b(reit|fund)\b", label) else "company"
            profile_url = str(raw.get("companyURL") or raw.get("profile_url") or "").strip()
            if profile_url:
                profile_url = urljoin(source_url, profile_url)
            normalized.append({
                "issuer_id": isin,
                "symbol": symbol,
                "name": name,
                "isin": isin,
                "exchange": f"Saudi Exchange {market_names[market_code]}",
                "currency": "SAR",
                "market_segment": market_names[market_code],
                "instrument_type": instrument_type,
                "trading_name": trading_name,
                "profile_url": profile_url,
                "source_url": source_url,
                "active": True,
            })
    normalized.sort(key=lambda row: (row["market_segment"], row["symbol"], row["isin"]))
    return json.dumps({"schema_version": 1, "data": normalized}, ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def fetch_saudi_issuer_directory(source_url: str = SAUDI_ISSUER_DIRECTORY_URL,
                                 headless: bool = True,
                                 timeout_ms: int = 60000) -> bytes:
    """Render and capture both public Saudi Exchange equity-market lists."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:  # pragma: no cover - optional runtime dependency
        raise RuntimeError(
            "live Saudi universe sync needs the browser extra: "
            "pip install -e \".[browser]\" && playwright install chromium"
        ) from error

    rows_by_market: dict[str, list[dict]] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            context = browser.new_context(locale="en-US", user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ))
            page = context.new_page()
            page.goto(source_url, timeout=timeout_ms, wait_until="domcontentloaded")
            with contextlib.suppress(Exception):
                page.wait_for_load_state("load", timeout=10000)
            page.wait_for_function(
                "typeof companyList !== 'undefined' && companyList.length > 0",
                timeout=timeout_ms,
            )
            for market_code in ("M", "S"):
                if page.locator("#Market_ti").input_value() != market_code:
                    with page.expect_response(
                        lambda response: "getCompanyListByMarknetAndSectors" in response.url,
                        timeout=timeout_ms,
                    ):
                        # Bootstrap-select keeps the native element hidden. Force is
                        # safe here: selecting it still emits the normal change event
                        # that requests the official market-specific directory data.
                        page.select_option("#Market_ti", market_code, force=True)
                page.wait_for_function(
                    "code => document.querySelector('#Market_ti').value === code "
                    "&& typeof companyList !== 'undefined' && companyList.length > 0",
                    arg=market_code,
                    timeout=timeout_ms,
                )
                rows_by_market[market_code] = page.evaluate("() => companyList")
        finally:
            browser.close()
    content = normalize_saudi_directory_rows(rows_by_market, source_url)
    if not json.loads(content).get("data"):
        raise RuntimeError("Saudi issuer directory returned no usable securities")
    return content


class UniverseStore:
    def __init__(self, db: Database):
        self.db = db

    def publish(self, market: str, source_url: str, content: bytes, local_path: str | None,
                issuers: list[dict], securities: list[dict], observed_at: str | None = None) -> dict:
        market = market.upper()
        observed_at = observed_at or _now()
        digest = hashlib.sha256(content).hexdigest()
        snapshot_id = f"universe:{market}:{digest}"
        with self.db.conn:
            self.db.conn.execute(
                """INSERT OR IGNORE INTO universe_snapshots(snapshot_id,market,source_url,
                observed_at,content_hash,local_path,record_count,metadata_json)
                VALUES(?,?,?,?,?,?,?,?)""",
                (snapshot_id, market, source_url, observed_at, digest, local_path,
                 len(securities), _json({"issuers": len(issuers), "securities": len(securities)})),
            )
            self.db.conn.execute("UPDATE issuer_universe SET active=0 WHERE market=?", (market,))
            self.db.conn.execute("UPDATE security_universe SET active=0 WHERE market=?", (market,))
            for issuer in issuers:
                payload = _json(issuer)
                self.db.conn.execute(
                    """INSERT INTO issuer_universe(issuer_id,market,authority_id,name,country,
                    active,primary_symbol,primary_exchange,metadata_json,current_snapshot_id,last_seen_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(issuer_id) DO UPDATE SET
                    name=excluded.name,country=excluded.country,active=excluded.active,
                    primary_symbol=excluded.primary_symbol,primary_exchange=excluded.primary_exchange,
                    metadata_json=excluded.metadata_json,current_snapshot_id=excluded.current_snapshot_id,
                    last_seen_at=excluded.last_seen_at""",
                    (issuer["issuer_id"], market, issuer["authority_id"], issuer["name"],
                     issuer.get("country"), int(issuer.get("active", True)),
                     issuer.get("primary_symbol"), issuer.get("primary_exchange"),
                     _json(issuer.get("metadata", {})), snapshot_id, observed_at),
                )
                self.db.conn.execute(
                    "INSERT OR IGNORE INTO issuer_universe_versions VALUES(?,?,?,?)",
                    (issuer["issuer_id"], snapshot_id, payload, observed_at),
                )
            for security in securities:
                payload = _json(security)
                self.db.conn.execute(
                    """INSERT INTO security_universe(security_key,issuer_id,market,symbol,
                    exchange,currency,is_primary,active,metadata_json,current_snapshot_id,last_seen_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(security_key) DO UPDATE SET
                    symbol=excluded.symbol,exchange=excluded.exchange,currency=excluded.currency,
                    is_primary=excluded.is_primary,active=excluded.active,
                    metadata_json=excluded.metadata_json,current_snapshot_id=excluded.current_snapshot_id,
                    last_seen_at=excluded.last_seen_at""",
                    (security["security_key"], security["issuer_id"], market, security["symbol"],
                     security.get("exchange", ""), security["currency"],
                     int(security.get("is_primary", False)), int(security.get("active", True)),
                     _json(security.get("metadata", {})), snapshot_id, observed_at),
                )
                self.db.conn.execute(
                    "INSERT OR IGNORE INTO security_universe_versions VALUES(?,?,?,?)",
                    (security["security_key"], snapshot_id, payload, observed_at),
                )
        return {"status": "ready", "snapshot_id": snapshot_id, "market": market,
                "issuers": len(issuers), "securities": len(securities), "sha256": digest,
                "local_path": local_path}


def activate_universe(
    db: Database, market: str, limit: int = 50, exchanges: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (), enable: bool = False,
    schedule_every: int | None = None, registry_path: str = "config/companies.json",
    include_funds: bool = False,
) -> dict:
    """Stage a deterministic, idempotent ingestion batch from an archived universe.

    Inventory and activation are deliberately separate. Merely discovering an issuer
    must never start network work. Scheduling requires both ``enable`` and an explicit
    interval, and is capped per invocation by ``limit``.
    """
    market = market.upper()
    if market not in {"SA", "US"}:
        raise ValueError("market must be SA or US")
    limit = min(max(int(limit), 1), 500)
    if schedule_every is not None and not enable:
        raise ValueError("scheduling requires --enable")
    if schedule_every is not None and schedule_every < 3600:
        raise ValueError("universe schedules must be at least 3600 seconds apart")
    filters = ["i.market=?", "i.active=1", "s.active=1", "s.is_primary=1",
               "a.issuer_id IS NULL"]
    args: list = [market]
    if market == "SA" and not include_funds:
        filters.append("COALESCE(json_extract(i.metadata_json,'$.instrument_type'),'company') != 'fund'")
    normalized_exchanges = tuple(sorted({value.strip() for value in exchanges if value.strip()}))
    normalized_symbols = tuple(sorted({value.strip().upper() for value in symbols if value.strip()}))
    if normalized_exchanges:
        filters.append("s.exchange IN (" + ",".join("?" for _ in normalized_exchanges) + ")")
        args.extend(normalized_exchanges)
    if normalized_symbols:
        filters.append("s.symbol IN (" + ",".join("?" for _ in normalized_symbols) + ")")
        args.extend(normalized_symbols)
    args.append(limit)
    rows = db.conn.execute(
        """SELECT i.issuer_id,i.authority_id,i.name,i.country,i.current_snapshot_id,
        i.metadata_json,s.symbol,s.exchange,s.currency,s.metadata_json AS security_metadata_json
        FROM issuer_universe i JOIN security_universe s USING(issuer_id)
        LEFT JOIN universe_activations a USING(issuer_id) WHERE """ + " AND ".join(filters) +
        " ORDER BY i.name,i.issuer_id LIMIT ?", args,
    ).fetchall()
    if not rows:
        return {"status": "empty", "market": market, "count": 0, "companies": []}
    source_indexes: dict[str, str] = {}
    if market == "SA":
        for row in rows:
            metadata = json.loads(row["metadata_json"])
            security_metadata = json.loads(row["security_metadata_json"])
            company_id = f"sa:{row['symbol']}"
            stored_source = db.conn.execute(
                """SELECT url FROM company_sources
                WHERE company_id=? AND enabled=1 ORDER BY priority,id LIMIT 1""",
                (company_id,),
            ).fetchone()
            source_index = (security_metadata.get("profile_url") or
                            metadata.get("profile_url") or
                            (stored_source["url"] if stored_source else None))
            if source_index:
                source_indexes[row["issuer_id"]] = str(source_index)
        if schedule_every is not None:
            missing = [row["symbol"] for row in rows
                       if row["issuer_id"] not in source_indexes]
            if missing:
                raise ValueError(
                    "Saudi monitoring requires an official issuer profile URL; missing for: "
                    + ", ".join(missing)
                )
    selection = {"exchanges": normalized_exchanges, "symbols": normalized_symbols,
                 "limit": limit, "enable": enable, "schedule_every": schedule_every,
                 "include_funds": include_funds}
    seed = _json({"snapshot": rows[0]["current_snapshot_id"], "selection": selection,
                  "issuers": [row["issuer_id"] for row in rows]})
    batch_id = "activation:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    batch_status = "active" if enable else "staged"
    companies = []
    scheduler = DurableScheduler(db) if schedule_every is not None else None
    with db.conn:
        db.conn.execute(
            """INSERT OR IGNORE INTO universe_activation_batches
            (batch_id,market,snapshot_id,status,selection_json,issuer_count,activated_at)
            VALUES(?,?,?,?,?,?,CASE WHEN ?='active' THEN CURRENT_TIMESTAMP END)""",
            (batch_id, market, rows[0]["current_snapshot_id"], batch_status,
             _json(selection), len(rows), batch_status),
        )
    for priority, row in enumerate(rows, 1):
        metadata = json.loads(row["metadata_json"])
        security_metadata = json.loads(row["security_metadata_json"])
        company_id = f"{market.lower()}:{row['symbol']}"
        existing = db.conn.execute(
            "SELECT enabled FROM companies WHERE company_id=?", (company_id,)
        ).fetchone()
        # An explicit enabled activation promotes an already-known disabled
        # registry company too; otherwise a seed-stage record could never join
        # a later complete-universe rollout.
        company_enabled = bool(enable or (existing and existing["enabled"]))
        company = Company(
            company_id=company_id, market=Market(market), symbol=row["symbol"],
            name=row["name"], currency=row["currency"],
            cik=row["authority_id"] if market == "US" else None,
            isin=security_metadata.get("isin") or metadata.get("isin"),
            exchange=row["exchange"], country=row["country"],
            sector=metadata.get("sector"), industry=metadata.get("industry"),
            timezone="America/New_York" if market == "US" else "Asia/Riyadh",
            locale="en" if market == "US" else "ar", enabled=company_enabled,
            sources=((source_indexes[row["issuer_id"]],)
                     if row["issuer_id"] in source_indexes else ()),
        )
        db.register_company(company)
        schedule_id = None
        activation_status = "active" if company_enabled else "staged"
        if scheduler and company_enabled:
            schedule_id = f"monitor:{market}:{company.symbol}"
            scheduler.upsert(
                schedule_id, f"Monitor {market}:{company.symbol}", "monitor",
                schedule_every, {"market": market, "symbol": company.symbol,
                    "registry": registry_path, "raw_dir": "data/raw",
                    "source_index": source_indexes.get(row["issuer_id"]),
                    "source_limit": 12, "browser": market == "SA", "llm": False},
                company.company_id,
            )
        with db.conn:
            db.conn.execute(
                """INSERT OR IGNORE INTO universe_activations
                (batch_id,issuer_id,company_id,priority,status,schedule_id)
                VALUES(?,?,?,?,?,?)""",
                (batch_id, row["issuer_id"], company_id, priority,
                 activation_status, schedule_id),
            )
        companies.append({"company_id": company_id, "symbol": company.symbol,
                          "name": company.name, "exchange": company.exchange,
                          "status": activation_status, "schedule_id": schedule_id})
    return {"status": batch_status, "batch_id": batch_id, "market": market,
            "count": len(companies), "companies": companies}


def classify_sec_submission(payload: dict) -> tuple[str, str]:
    """Classify SEC registrants conservatively before automated ingestion."""
    name = str(payload.get("name") or "").lower()
    entity_type = str(payload.get("entityType") or "").lower()
    sic = str(payload.get("sic") or "").zfill(4)
    forms = set(payload.get("filings", {}).get("recent", {}).get("form", []))
    if sic == "6770" or "blank check" in str(payload.get("sicDescription") or "").lower():
        return "excluded", "blank-check company"
    non_company_markers = (" etf", "exchange traded fund", "income fund",
                           "equity fund", "acquisition corp", "acquisition co")
    if entity_type in {"investment", "investment company"}:
        return "excluded", f"SEC entity type is {entity_type}"
    if any(marker in name for marker in non_company_markers):
        return "excluded", "name indicates a fund or acquisition vehicle"
    if entity_type == "operating" and forms.intersection({"10-K", "10-Q", "20-F", "40-F"}):
        return "eligible", "operating registrant with periodic financial filings"
    return "review", "SEC metadata is insufficient for automatic eligibility"


def classify_sec_sic(sic: str | int | None) -> tuple[str | None, str | None]:
    """Map authoritative SEC SIC codes to broad reviewed sector packs."""
    text = str(sic or "").strip()
    if not text.isdigit():
        return None, None
    code = int(text)
    if 100 <= code <= 999:
        return "Consumer Staples", "Food & Agriculture"
    if 1300 <= code <= 1389:
        return "Energy", "Integrated Oil & Gas"
    if 1000 <= code <= 1499:
        return "Materials", "Mining"
    if 2800 <= code <= 2829:
        return "Materials", "Diversified Chemicals"
    if 2830 <= code <= 2839 or 8000 <= code <= 8099:
        return "Health Care", "Health Care"
    if 3570 <= code <= 3579 or 3670 <= code <= 3679 or 7370 <= code <= 7379:
        return "Technology", "Technology"
    if 4810 <= code <= 4899:
        return "Communication Services", "Telecommunications"
    if 4000 <= code <= 4799:
        return "Industrials", "Transportation & Logistics"
    if 4900 <= code <= 4999:
        return "Utilities", "Utilities"
    if 5000 <= code <= 5999:
        return "Consumer", "Retail"
    if 6000 <= code <= 6099:
        return "Financials", "Banks"
    if 6310 <= code <= 6419:
        return "Financials", "Insurance"
    if 6500 <= code <= 6799:
        return "Real Estate", "Real Estate & REITs"
    return None, None


def enrich_activation_batch(
    db: Database, raw_dir: str | Path, user_agent: str, batch_id: str | None = None,
    limit: int = 25, opener=urlopen, request_interval: float = 0.12,
) -> dict:
    """Archive SEC registrant profiles and classify a staged activation batch."""
    if "@" not in user_agent:
        raise ValueError("live SEC enrichment requires a declared user agent with email")
    limit = min(max(int(limit), 1), 100)
    if batch_id is None:
        row = db.conn.execute(
            """SELECT batch_id FROM universe_activation_batches
            WHERE market='US' AND status='staged' ORDER BY created_at DESC LIMIT 1"""
        ).fetchone()
        if not row:
            raise ValueError("no staged US activation batch exists")
        batch_id = row["batch_id"]
    rows = db.conn.execute(
        """SELECT a.issuer_id,i.authority_id FROM universe_activations a
        JOIN issuer_universe i USING(issuer_id)
        LEFT JOIN universe_issuer_profiles p USING(issuer_id)
        WHERE a.batch_id=? AND i.market='US' AND p.issuer_id IS NULL
        ORDER BY a.priority LIMIT ?""", (batch_id, limit),
    ).fetchall()
    archive_dir = Path(raw_dir) / "US" / "profiles"
    archive_dir.mkdir(parents=True, exist_ok=True)
    counts = {"eligible": 0, "excluded": 0, "review": 0}
    processed = []
    for index, row in enumerate(rows):
        if index and request_interval > 0:
            time.sleep(request_interval)
        url = SEC_SUBMISSIONS_URL.format(cik=row["authority_id"])
        request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
        with opener(request, timeout=30) as response:
            content = response.read()
        payload = json.loads(content)
        digest = hashlib.sha256(content).hexdigest()
        archived = archive_dir / f"{digest}.json"
        if not archived.exists():
            archived.write_bytes(content)
        if hashlib.sha256(archived.read_bytes()).hexdigest() != digest:
            raise RuntimeError("archived SEC profile hash mismatch")
        status, reason = classify_sec_submission(payload)
        sector, industry = classify_sec_sic(payload.get("sic"))
        observed_at = _now()
        metadata = {key: payload.get(key) for key in (
            "name", "tickers", "exchanges", "stateOfIncorporation", "addresses"
        ) if payload.get(key) not in (None, "")}
        with db.conn:
            db.conn.execute(
                """INSERT INTO universe_issuer_profiles(issuer_id,source_url,content_hash,
                local_path,entity_type,sic,sic_description,fiscal_year_end,
                eligibility_status,eligibility_reason,metadata_json,observed_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(issuer_id) DO UPDATE SET
                source_url=excluded.source_url,content_hash=excluded.content_hash,
                local_path=excluded.local_path,entity_type=excluded.entity_type,sic=excluded.sic,
                sic_description=excluded.sic_description,fiscal_year_end=excluded.fiscal_year_end,
                eligibility_status=excluded.eligibility_status,
                eligibility_reason=excluded.eligibility_reason,
                metadata_json=excluded.metadata_json,observed_at=excluded.observed_at,
                updated_at=CURRENT_TIMESTAMP""",
                (row["issuer_id"], url, digest, str(archived), payload.get("entityType"),
                 str(payload.get("sic") or ""), payload.get("sicDescription"),
                 payload.get("fiscalYearEnd"), status, reason, _json(metadata), observed_at),
            )
            if sector and industry:
                db.conn.execute(
                    """UPDATE companies SET sector=?,industry=? WHERE company_id IN
                    (SELECT company_id FROM universe_activations WHERE issuer_id=?)""",
                    (sector, industry, row["issuer_id"]),
                )
        counts[status] += 1
        processed.append({"issuer_id": row["issuer_id"], "status": status, "reason": reason})
    remaining = db.conn.execute(
        """SELECT count(*) FROM universe_activations a
        LEFT JOIN universe_issuer_profiles p USING(issuer_id)
        WHERE a.batch_id=? AND p.issuer_id IS NULL""", (batch_id,),
    ).fetchone()[0]
    return {"status": "ready", "batch_id": batch_id, "processed": len(processed),
            "remaining": remaining, "counts": counts, "issuers": processed}


def promote_activation_batch(
    db: Database, batch_id: str, limit: int = 10, schedule_every: int = 21600,
    registry_path: str = "config/companies.json", raw_dir: str | Path = "data/raw",
) -> dict:
    """Enable only SEC-profiled operating issuers and create durable schedules."""
    limit = min(max(int(limit), 1), 100)
    if schedule_every < 3600:
        raise ValueError("universe schedules must be at least 3600 seconds apart")
    batch = db.conn.execute(
        "SELECT market FROM universe_activation_batches WHERE batch_id=?", (batch_id,)
    ).fetchone()
    if not batch:
        raise KeyError(f"unknown activation batch {batch_id}")
    market = batch["market"]
    if market == "US":
        rows = db.conn.execute(
            """SELECT a.issuer_id,a.company_id,c.symbol,p.fiscal_year_end,
            NULL AS source_index FROM universe_activations a
            JOIN companies c USING(company_id)
            JOIN universe_issuer_profiles p USING(issuer_id)
            WHERE a.batch_id=? AND a.status='staged' AND p.eligibility_status='eligible'
            ORDER BY a.priority LIMIT ?""", (batch_id, limit),
        ).fetchall()
    else:
        rows = db.conn.execute(
            """SELECT a.issuer_id,a.company_id,c.symbol,c.fiscal_year_end,
            (SELECT url FROM company_sources cs WHERE cs.company_id=a.company_id
             AND cs.enabled=1 ORDER BY cs.priority,cs.id LIMIT 1) AS source_index
            FROM universe_activations a JOIN companies c USING(company_id)
            WHERE a.batch_id=? AND a.status='staged'
            AND EXISTS(SELECT 1 FROM company_sources cs WHERE cs.company_id=a.company_id
                       AND cs.enabled=1)
            ORDER BY a.priority LIMIT ?""", (batch_id, limit),
        ).fetchall()
    scheduler = DurableScheduler(db)
    promoted = []
    for row in rows:
        schedule_id = f"monitor:{market}:{row['symbol']}"
        scheduler.upsert(
            schedule_id, f"Monitor {market}:{row['symbol']}", "monitor", schedule_every,
            {"market": market, "symbol": row["symbol"], "registry": registry_path,
             "raw_dir": str(raw_dir), "source_index": row["source_index"],
             "source_limit": 12, "browser": market == "SA", "llm": False},
            row["company_id"],
        )
        with db.conn:
            fiscal_year_end = row["fiscal_year_end"] or "1231"
            if len(fiscal_year_end) == 4 and fiscal_year_end.isdigit():
                fiscal_year_end = fiscal_year_end[:2] + "-" + fiscal_year_end[2:]
            db.conn.execute(
                "UPDATE companies SET enabled=1,fiscal_year_end=? WHERE company_id=?",
                (fiscal_year_end, row["company_id"]),
            )
            db.conn.execute(
                """UPDATE universe_activations SET status='active',schedule_id=?,error=NULL,
                updated_at=CURRENT_TIMESTAMP WHERE batch_id=? AND issuer_id=?""",
                (schedule_id, batch_id, row["issuer_id"]),
            )
        promoted.append({"issuer_id": row["issuer_id"], "company_id": row["company_id"],
                         "symbol": row["symbol"], "schedule_id": schedule_id})
    if promoted:
        with db.conn:
            db.conn.execute(
                """UPDATE universe_activation_batches SET status='active',
                activated_at=COALESCE(activated_at,CURRENT_TIMESTAMP) WHERE batch_id=?""",
                (batch_id,),
            )
    if market == "US":
        eligible_remaining = db.conn.execute(
            """SELECT count(*) FROM universe_activations a
            JOIN universe_issuer_profiles p USING(issuer_id)
            WHERE a.batch_id=? AND a.status='staged' AND p.eligibility_status='eligible'""",
            (batch_id,),
        ).fetchone()[0]
    else:
        eligible_remaining = db.conn.execute(
            """SELECT count(*) FROM universe_activations a WHERE a.batch_id=?
            AND a.status='staged' AND EXISTS(SELECT 1 FROM company_sources cs
            WHERE cs.company_id=a.company_id AND cs.enabled=1)""", (batch_id,),
        ).fetchone()[0]
    backlog_refreshed = 0
    if promoted:
        from .domains import CompanyDomainStore
        domains = CompanyDomainStore(db)
        for item in promoted:
            domains.refresh_company_backlog(item["company_id"])
            backlog_refreshed += 1
    return {"status": "active" if promoted else "empty", "batch_id": batch_id,
            "promoted": len(promoted), "eligible_remaining": eligible_remaining,
            "backlog_refreshed": backlog_refreshed, "companies": promoted}


def enqueue_saudi_historical_backfill(
    db: Database, limit: int = 500, source_limit: int = 500,
    registry_path: str = "config/companies.json", raw_dir: str | Path = "data/raw",
    pause_recurring: bool = True,
) -> dict:
    """Activate the complete Saudi inventory and queue one historical crawl each.

    This is intentionally separate from recurring monitoring.  It includes funds
    because the archived issuer universe is the coverage contract even while their
    fund-specific metric pack is developed later.  Re-running against the same
    universe snapshot is idempotent and cannot duplicate the crawl jobs.
    """
    limit = min(max(int(limit), 1), 500)
    source_limit = min(max(int(source_limit), 1), 1000)
    activation = activate_universe(
        db, "SA", limit=limit, enable=True, registry_path=registry_path,
        include_funds=True,
    )
    snapshot = db.conn.execute(
        """SELECT snapshot_id FROM universe_snapshots WHERE market='SA'
        ORDER BY observed_at DESC LIMIT 1"""
    ).fetchone()
    if not snapshot:
        raise ValueError("Saudi universe must be synchronized before historical backfill")
    run_id = f"sa-historical:{snapshot['snapshot_id'].split(':')[-1][:16]}:v2"
    if pause_recurring:
        with db.conn:
            db.conn.execute(
                """UPDATE schedules SET enabled=0,updated_at=CURRENT_TIMESTAMP
                WHERE job_type='monitor' AND company_id IN
                (SELECT company_id FROM companies WHERE market='SA')"""
            )
    rows = db.conn.execute(
        """SELECT c.company_id,c.symbol,
        (SELECT url FROM company_sources cs WHERE cs.company_id=c.company_id
         AND cs.enabled=1 ORDER BY cs.priority,cs.id LIMIT 1) AS source_index
        FROM issuer_universe i JOIN security_universe s USING(issuer_id)
        JOIN universe_activations a USING(issuer_id)
        JOIN companies c ON c.company_id=a.company_id
        WHERE i.market='SA' AND i.active=1 AND s.active=1 AND s.is_primary=1
        ORDER BY c.symbol LIMIT ?""", (limit,),
    ).fetchall()
    queue = DurableJobQueue(db)
    queued = existing = missing_source = 0
    job_ids = []
    for row in rows:
        if not row["source_index"]:
            missing_source += 1
            db.exception(
                row["company_id"], None, "historical_backfill", "missing_official_source",
                "No archived Saudi Exchange issuer profile URL is available",
                {"run_id": run_id, "symbol": row["symbol"]},
            )
            continue
        payload = {
            "market": "SA", "symbol": row["symbol"],
            "registry": registry_path, "raw_dir": str(raw_dir),
            "source_index": row["source_index"], "source_limit": source_limit,
            "browser": True, "llm": False, "backfill_run_id": run_id,
            "discovery_scope": "historical",
        }
        job_id, created = queue.enqueue(
            "monitor", payload, row["company_id"],
            idempotency_key=f"{run_id}:{row['company_id']}", priority=10,
            max_attempts=8,
        )
        job_ids.append(job_id)
        queued += int(created)
        existing += int(not created)
    return {
        "status": "queued" if queued else "ready", "run_id": run_id,
        "universe_entities": len(rows), "queued": queued, "existing": existing,
        "missing_source": missing_source, "recurring_paused": bool(pause_recurring),
        "source_limit": source_limit, "activation": activation,
        "job_ids": job_ids,
    }


def saudi_historical_backfill_status(db: Database, run_id: str | None = None) -> dict:
    """Report auditable progress for a queued Saudi historical backfill."""
    if run_id is None:
        row = db.conn.execute(
            """SELECT json_extract(payload_json,'$.backfill_run_id') AS run_id
            FROM jobs WHERE json_extract(payload_json,'$.discovery_scope')='historical'
            ORDER BY created_at DESC LIMIT 1"""
        ).fetchone()
        run_id = row["run_id"] if row else None
    if not run_id:
        return {"status": "not_started", "run_id": None, "jobs": {}}
    counts = {
        row["status"]: row["n"] for row in db.conn.execute(
            """SELECT status,count(*) AS n FROM jobs
            WHERE json_extract(payload_json,'$.backfill_run_id')=? GROUP BY status""",
            (run_id,),
        )
    }
    total = sum(counts.values())
    pending = sum(counts.get(key, 0) for key in ("queued", "running", "failed"))
    return {
        "status": "complete" if total and pending == 0 and not counts.get("dead", 0)
                  else "attention" if counts.get("dead", 0) else "running",
        "run_id": run_id, "jobs": counts, "total_jobs": total,
        "pending_jobs": pending, "dead_jobs": counts.get("dead", 0),
    }


def reconcile_onboarding_runtime_paths(
    db: Database, raw_dir: str | Path, recover_running: bool = False,
) -> dict:
    """Repair only onboarding-owned runtime paths and the jobs affected by them."""
    runtime_raw = str(Path(raw_dir))
    schedule_updates = job_updates = retried = download_retried = fallback_retried = 0
    lease_retried = recovered = 0
    activation_companies = "SELECT company_id FROM universe_activations"
    with db.conn:
        schedules = db.conn.execute(
            f"SELECT schedule_id,payload_json FROM schedules WHERE job_type='monitor' "
            f"AND company_id IN ({activation_companies})"
        ).fetchall()
        for row in schedules:
            payload = json.loads(row["payload_json"])
            if payload.get("raw_dir") != runtime_raw:
                payload["raw_dir"] = runtime_raw
                db.conn.execute("UPDATE schedules SET payload_json=?,updated_at=CURRENT_TIMESTAMP "
                                "WHERE schedule_id=?", (_json(payload), row["schedule_id"]))
                schedule_updates += 1
        statuses = "('queued','dead'" + (",'running'" if recover_running else "") + ")"
        jobs = db.conn.execute(
            f"""SELECT job_id,job_type,company_id,status,last_error,payload_json,attempts,max_attempts
            FROM jobs
            WHERE job_type IN ('monitor','fetch_document','extract_document')
            AND company_id IN ({activation_companies}) AND status IN {statuses}"""
        ).fetchall()
        for row in jobs:
            payload = json.loads(row["payload_json"])
            if payload.get("raw_dir") != runtime_raw:
                payload["raw_dir"] = runtime_raw
                db.conn.execute("UPDATE jobs SET payload_json=?,updated_at=CURRENT_TIMESTAMP "
                                "WHERE job_id=?", (_json(payload), row["job_id"]))
                job_updates += 1
            retry_path_error = (row["status"] == "dead" and
                                "Read-only file system" in (row["last_error"] or ""))
            retry_download_error = (row["status"] == "dead" and
                                    "evicted from inspector cache" in
                                    (row["last_error"] or "").lower())
            retry_source_fallback = False
            if (row["status"] == "dead" and row["job_type"] == "monitor" and
                    (row["last_error"] or "").startswith("Page.goto:")):
                source_count = db.conn.execute(
                    "SELECT count(*) FROM company_sources WHERE company_id=? AND enabled=1",
                    (row["company_id"],),
                ).fetchone()[0]
                retry_source_fallback = source_count > 1
            retry_expired_lease = (row["status"] == "dead" and
                                   row["last_error"] == "worker lease expired")
            recover = recover_running and row["status"] == "running"
            if (retry_path_error or retry_download_error or retry_source_fallback or
                    retry_expired_lease or recover):
                previous_attempt = db.conn.execute(
                    "SELECT COALESCE(MAX(attempt_number),0) FROM job_attempts WHERE job_id=?",
                    (row["job_id"],),
                ).fetchone()[0]
                # Preserve the append-only attempt audit trail. Retried repairs
                # receive a fresh allowance above the last recorded attempt.
                max_attempts = max(int(row["max_attempts"]), previous_attempt + 5)
                db.conn.execute(
                    """UPDATE jobs SET status='queued',attempts=?,max_attempts=?,last_error=NULL,
                    leased_by=NULL,lease_until=NULL,finished_at=NULL,
                    available_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE job_id=?""",
                    (previous_attempt, max_attempts, row["job_id"]),
                )
                if recover:
                    db.conn.execute(
                        """UPDATE job_attempts SET status='expired',finished_at=CURRENT_TIMESTAMP,
                        error='worker stopped for runtime path reconciliation'
                        WHERE job_id=? AND finished_at IS NULL""", (row["job_id"],),
                    )
                    recovered += 1
                elif retry_download_error:
                    download_retried += 1
                elif retry_source_fallback:
                    fallback_retried += 1
                elif retry_expired_lease:
                    lease_retried += 1
                else:
                    retried += 1
                candidate_id = payload.get("candidate_id")
                if candidate_id is not None:
                    db.conn.execute("UPDATE source_candidates SET status='queued' WHERE id=?",
                                    (int(candidate_id),))
    return {"status": "ready", "raw_dir": runtime_raw,
            "schedule_updates": schedule_updates, "job_updates": job_updates,
            "retried_path_failures": retried,
            "retried_download_failures": download_retried,
            "retried_source_fallbacks": fallback_retried,
            "retried_expired_leases": lease_retried,
            "recovered_running": recovered}


def onboard_universe(
    db: Database, raw_dir: str | Path, user_agent: str,
    us_limit: int = 25, sa_limit: int = 10, schedule_every: int = 86400,
    opener=urlopen, request_interval: float = 0.12,
) -> dict:
    """Run one bounded, idempotent onboarding cycle for both markets.

    US issuers must pass the archived SEC-profile eligibility gate. Saudi issuers
    must have an official issuer profile URL. Enabling monitoring never bypasses
    staging, canonical mapping, normalization, or deterministic publication rules.
    """
    limits = {"US": min(max(int(us_limit), 1), 100),
              "SA": min(max(int(sa_limit), 1), 100)}
    raw_path = Path(raw_dir)
    document_raw_dir = raw_path.parent if raw_path.name == "universe" else raw_path
    reconciliation = reconcile_onboarding_runtime_paths(db, document_raw_dir)
    results: dict[str, dict] = {}
    for market in ("US", "SA"):
        activation = activate_universe(db, market, limit=limits[market])
        result: dict = {"activation": activation}
        if activation.get("batch_id"):
            if market == "US":
                result["enrichment"] = enrich_activation_batch(
                    db, raw_dir, user_agent, activation["batch_id"], limits[market],
                    opener=opener, request_interval=request_interval,
                )
            result["promotion"] = promote_activation_batch(
                db, activation["batch_id"], limits[market], schedule_every,
                raw_dir=document_raw_dir,
            )
        results[market] = result
    return {"status": "ready", "reconciliation": reconciliation, "markets": results,
            "activated": sum(item.get("promotion", {}).get("promoted", 0)
                             for item in results.values())}


def sync_universe(db: Database, market: str, raw_dir: str | Path,
                  user_agent: str | None = None, input_path: str | Path | None = None,
                  source_url: str | None = None, headless: bool = True) -> dict:
    market = market.upper()
    if market == "US" and input_path is None:
        if not user_agent or "@" not in user_agent:
            raise ValueError("live SEC universe access requires a declared user agent with email")
        source_url = source_url or SEC_TICKERS_URL
        request = Request(source_url, headers={"User-Agent": user_agent,
                                               "Accept": "application/json"})
        with urlopen(request, timeout=30) as response:
            content = response.read()
        suffix = ".json"
    elif market == "SA" and input_path is None:
        source_url = source_url or SAUDI_ISSUER_DIRECTORY_URL
        content = fetch_saudi_issuer_directory(source_url, headless=headless)
        suffix = ".json"
    elif input_path is not None:
        path = Path(input_path)
        content = path.read_bytes()
        suffix = path.suffix
        source_url = source_url or path.resolve().as_uri()
    else:
        raise ValueError("market must be US or SA")
    digest = hashlib.sha256(content).hexdigest()
    archive_dir = Path(raw_dir) / market
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived = archive_dir / f"{digest}{suffix.lower()}"
    if not archived.exists():
        archived.write_bytes(content)
    if hashlib.sha256(archived.read_bytes()).hexdigest() != digest:
        raise RuntimeError("archived universe snapshot hash mismatch")
    if market == "US":
        issuers, securities = parse_sec_ticker_exchange(json.loads(content))
    elif market == "SA":
        issuers, securities = parse_saudi_reference(content, suffix)
    else:
        raise ValueError("market must be US or SA")
    return UniverseStore(db).publish(market, source_url or "", content, str(archived),
                                     issuers, securities)
