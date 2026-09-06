from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .database import Database
from .jobs import DurableScheduler
from .registry import CompanyRegistry


def backup_database(database: str | Path, output_dir: str | Path, keep: int = 14) -> dict:
    """Create and verify a consistent online SQLite backup.

    SQLite's backup API is used instead of copying the live file, so the worker
    may continue monitoring while the snapshot is taken.
    """
    source = Path(database).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if keep < 1:
        raise ValueError("keep must be at least 1")
    destination_dir = Path(output_dir).resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = destination_dir / f"financial-{stamp}.sqlite3"

    source_uri = f"file:{source.as_posix()}?mode=ro"
    with closing(sqlite3.connect(source_uri, uri=True)) as source_db:
        with closing(sqlite3.connect(destination)) as backup_db:
            source_db.backup(backup_db)
            backup_db.commit()
            integrity = backup_db.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"backup integrity check failed: {integrity}")

    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    metadata = destination.with_suffix(".json")
    metadata.write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source.name,
        "backup": destination.name,
        "bytes": destination.stat().st_size,
        "sha256": digest,
        "integrity": integrity,
    }, indent=2) + "\n", encoding="utf-8")

    snapshots = sorted(destination_dir.glob("financial-*.sqlite3"), reverse=True)
    for expired in snapshots[keep:]:
        expired.unlink(missing_ok=True)
        expired.with_suffix(".json").unlink(missing_ok=True)
    return {
        "status": "ready", "backup": str(destination), "metadata": str(metadata),
        "sha256": digest, "bytes": destination.stat().st_size, "retained": min(len(snapshots), keep),
    }


def configure_production_schedules(
    database: str | Path,
    registry_path: str | Path = "config/companies.json",
    interval_seconds: int = 21600,
    source_limit: int = 50,
    use_llm: bool = True,
) -> dict:
    """Idempotently configure monitoring for every enabled registry company."""
    registry = CompanyRegistry.from_json(registry_path)
    db = Database(database)
    configured = []
    try:
        scheduler = DurableScheduler(db)
        for company in registry.all():
            if not company.enabled:
                continue
            db.register_company(company)
            payload = {
                "market": company.market.value,
                "symbol": company.symbol,
                "registry": str(registry_path),
                "raw_dir": "data/raw",
                "sa_manifest": None,
                "source_index": company.sources[0] if company.sources else None,
                "source_limit": source_limit,
                "browser": company.market.value == "SA",
                "llm": use_llm and company.market.value == "SA",
            }
            schedule_id = f"monitor:{company.market.value}:{company.symbol}"
            scheduler.upsert(
                schedule_id, f"Monitor {company.market.value}:{company.symbol}", "monitor",
                interval_seconds, payload, company.company_id,
            )
            configured.append(schedule_id)
    finally:
        db.close()
    return {"status": "ready", "configured": configured, "count": len(configured)}
