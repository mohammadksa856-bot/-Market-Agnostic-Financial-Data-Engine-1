from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from .database import Database, _json
from .jobs import DurableScheduler
from .models import Company, Market


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
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
                    "market_segment", "website", "source_url") if row.get(key) not in (None, "")}
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
    selection = {"exchanges": normalized_exchanges, "symbols": normalized_symbols,
                 "limit": limit, "enable": enable, "schedule_every": schedule_every}
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
        company_enabled = bool(existing["enabled"]) if existing else enable
        company = Company(
            company_id=company_id, market=Market(market), symbol=row["symbol"],
            name=row["name"], currency=row["currency"],
            cik=row["authority_id"] if market == "US" else None,
            isin=security_metadata.get("isin") or metadata.get("isin"),
            exchange=row["exchange"], country=row["country"],
            sector=metadata.get("sector"), industry=metadata.get("industry"),
            timezone="America/New_York" if market == "US" else "Asia/Riyadh",
            locale="en" if market == "US" else "ar", enabled=company_enabled,
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


def sync_universe(db: Database, market: str, raw_dir: str | Path,
                  user_agent: str | None = None, input_path: str | Path | None = None,
                  source_url: str | None = None) -> dict:
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
    elif input_path is not None:
        path = Path(input_path)
        content = path.read_bytes()
        suffix = path.suffix
        source_url = source_url or path.resolve().as_uri()
    else:
        raise ValueError("Saudi universe sync requires an official JSON or CSV export")
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
