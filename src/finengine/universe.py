from __future__ import annotations

import csv
import hashlib
import io
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from .database import Database, _json
from .jobs import DurableScheduler
from .models import Company, Market


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
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
    registry_path: str = "config/companies.json",
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
    if batch["market"] != "US":
        raise ValueError("automatic eligibility promotion currently supports US batches only")
    rows = db.conn.execute(
        """SELECT a.issuer_id,a.company_id,c.symbol,p.fiscal_year_end FROM universe_activations a
        JOIN companies c USING(company_id)
        JOIN universe_issuer_profiles p USING(issuer_id)
        WHERE a.batch_id=? AND a.status='staged' AND p.eligibility_status='eligible'
        ORDER BY a.priority LIMIT ?""", (batch_id, limit),
    ).fetchall()
    scheduler = DurableScheduler(db)
    promoted = []
    for row in rows:
        schedule_id = f"monitor:US:{row['symbol']}"
        scheduler.upsert(
            schedule_id, f"Monitor US:{row['symbol']}", "monitor", schedule_every,
            {"market": "US", "symbol": row["symbol"], "registry": registry_path,
             "raw_dir": "data/raw", "source_limit": 12, "browser": False, "llm": False},
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
    eligible_remaining = db.conn.execute(
        """SELECT count(*) FROM universe_activations a JOIN universe_issuer_profiles p USING(issuer_id)
        WHERE a.batch_id=? AND a.status='staged' AND p.eligibility_status='eligible'""",
        (batch_id,),
    ).fetchone()[0]
    return {"status": "active" if promoted else "empty", "batch_id": batch_id,
            "promoted": len(promoted), "eligible_remaining": eligible_remaining,
            "companies": promoted}


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
