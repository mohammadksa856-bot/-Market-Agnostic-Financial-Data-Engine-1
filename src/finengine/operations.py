from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import zipfile
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


def create_portable_bundle(
    database: str | Path, output_dir: str | Path, project_root: str | Path = ".",
    keep: int = 7,
) -> dict:
    """Create a verified portable bundle of SQLite plus every referenced raw file."""
    if keep < 1:
        raise ValueError("keep must be at least 1")
    source = Path(database).resolve()
    root = Path(project_root).resolve()
    destination_dir = Path(output_dir).resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = destination_dir / f"financial-bundle-{stamp}.zip"
    partial = target.with_suffix(".zip.part")
    files: dict[Path, dict] = {}
    tables = (
        ("source_documents", "source_key", "local_path", "content_hash"),
        ("source_artifacts", "artifact_key", "local_path", "content_hash"),
        ("universe_snapshots", "snapshot_id", "local_path", "content_hash"),
        ("universe_issuer_profiles", "issuer_id", "local_path", "content_hash"),
    )
    conn = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        for table, identity, local_path, content_hash in tables:
            for row in conn.execute(
                f"SELECT {identity} AS identity,{local_path} AS local_path,"
                f"{content_hash} AS content_hash FROM {table} WHERE {local_path} IS NOT NULL"
            ):
                path = Path(row["local_path"])
                absolute = path if path.is_absolute() else root / path
                absolute = absolute.resolve()
                if not absolute.is_file():
                    raise FileNotFoundError(f"bundle source missing: {row['identity']}: {path}")
                digest = hashlib.sha256(absolute.read_bytes()).hexdigest()
                if digest != row["content_hash"]:
                    raise ValueError(f"bundle source hash mismatch: {row['identity']}")
                entry = files.setdefault(absolute, {
                    "content_hash": digest, "bytes": absolute.stat().st_size,
                    "bundle_path": f"files/{digest}{absolute.suffix.lower()}",
                    "original_path": str(path), "references": [],
                })
                entry["references"].append({"table": table, "identity": row["identity"]})
    finally:
        conn.close()
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot = Path(temp_dir) / "financial.sqlite3"
        with closing(sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)) as source_db:
            with closing(sqlite3.connect(snapshot)) as backup_db:
                source_db.backup(backup_db); backup_db.commit()
                if backup_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("bundle database integrity check failed")
        database_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        manifest = {
            "format": "finengine-portable-bundle-v1",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "database": {"bundle_path": "database/financial.sqlite3",
                         "content_hash": database_hash, "bytes": snapshot.stat().st_size},
            "files": sorted(files.values(), key=lambda item: item["bundle_path"]),
        }
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as archive:
            archive.write(snapshot, "database/financial.sqlite3")
            for absolute, item in files.items():
                archive.write(absolute, item["bundle_path"])
            archive.writestr("manifest.json", manifest_bytes)
        partial.replace(target)
    verification = verify_portable_bundle(target)
    sidecar = target.with_suffix(".json")
    sidecar.write_text(json.dumps({
        "bundle": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        **verification,
    }, indent=2) + "\n", encoding="utf-8")
    bundles = sorted(destination_dir.glob("financial-bundle-*.zip"), reverse=True)
    for expired in bundles[keep:]:
        expired.unlink(missing_ok=True); expired.with_suffix(".json").unlink(missing_ok=True)
    return {"status": "ready", "bundle": str(target), "metadata": str(sidecar),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), **verification}


def verify_portable_bundle(bundle: str | Path) -> dict:
    """Verify every byte represented by a portable bundle manifest."""
    path = Path(bundle)
    with zipfile.ZipFile(path, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"corrupt bundle member: {bad}")
        manifest = json.loads(archive.read("manifest.json"))
        database = manifest["database"]
        if hashlib.sha256(archive.read(database["bundle_path"])).hexdigest() != database["content_hash"]:
            raise ValueError("bundle database hash mismatch")
        for item in manifest["files"]:
            if hashlib.sha256(archive.read(item["bundle_path"])).hexdigest() != item["content_hash"]:
                raise ValueError(f"bundle file hash mismatch: {item['bundle_path']}")
    return {"format": manifest["format"], "files": len(manifest["files"]),
            "database_bytes": database["bytes"],
            "source_bytes": sum(item["bytes"] for item in manifest["files"])}


def configure_production_schedules(
    database: str | Path,
    registry_path: str | Path = "config/companies.json",
    interval_seconds: int = 21600,
    source_limit: int = 50,
    use_llm: bool = True,
    raw_dir: str | Path = "data/raw",
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
                "raw_dir": str(raw_dir),
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
