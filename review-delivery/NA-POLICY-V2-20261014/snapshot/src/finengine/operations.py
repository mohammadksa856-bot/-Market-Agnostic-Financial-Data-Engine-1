from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import zipfile
import uuid
import signal
import threading
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .database import Database
from .jobs import DurableScheduler
from .registry import CompanyRegistry


def _sha256_file(path: Path) -> str:
    """Hash a potentially multi-gigabyte file without loading it into RAM."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _require_bundle_capacity(database_bytes: int, raw_bytes: int,
                             destination_free: int, snapshot_free: int,
                             same_device: bool, reserve: int = 1024 ** 3) -> None:
    """Do not assume already-compressed PDFs will shrink inside a ZIP."""
    destination_required = database_bytes + raw_bytes + reserve
    snapshot_required = database_bytes + reserve
    if same_device:
        destination_required += database_bytes
        snapshot_required = destination_required
    if destination_free < destination_required or snapshot_free < snapshot_required:
        raise OSError(
            f"Insufficient safe backup capacity: destination needs {destination_required} bytes "
            f"(free {destination_free}); snapshot needs {snapshot_required} "
            f"(free {snapshot_free}). Existing verified backups were preserved.")


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
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex
    destination = destination_dir / f"financial-{stamp}.sqlite3"
    partial = destination.with_suffix(".sqlite3.part")
    metadata = destination.with_suffix(".json")
    partial_metadata = metadata.with_suffix(".json.part")
    wal = Path(str(source) + "-wal")
    required = source.stat().st_size + (wal.stat().st_size if wal.is_file() else 0) + 1024 ** 3
    if shutil.disk_usage(destination_dir).free < required:
        raise OSError(f"Insufficient safe database backup capacity: need {required} bytes; "
                      "existing recovery points were preserved")
    # Exclusive invocation-owned paths: failure cleanup must never touch a
    # preceding snapshot, another invocation, or an already finalized database.
    owned = False
    metadata_owned = False
    previous_sigterm = None
    signal_installed = False
    cancelled = False
    def cancel_backup(signum, frame):
        nonlocal cancelled
        cancelled = True
        raise InterruptedError("database backup cancelled by SIGTERM")
    try:
        # Default container SIGTERM would otherwise bypass exception cleanup.
        # Only the main thread can temporarily own signal delivery; restore the
        # caller's exact handler on every path and propagate cancellation.
        if threading.current_thread() is threading.main_thread():
            previous_sigterm = signal.getsignal(signal.SIGTERM)
            signal.signal(signal.SIGTERM, cancel_backup)
            signal_installed = True
        with partial.open("xb"):
            owned = True
        source_uri = f"file:{source.as_posix()}?mode=ro"
        with closing(sqlite3.connect(source_uri, uri=True)) as source_db:
            with closing(sqlite3.connect(partial)) as backup_db:
                # Re-enter Python regularly so SIGTERM is processed during the
                # SQLite backup and during the potentially long integrity scan.
                source_db.backup(backup_db, pages=128, progress=lambda status, remaining, total: None)
                backup_db.commit()
                backup_db.set_progress_handler(lambda: 0, 5000)
                integrity = backup_db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"backup integrity check failed: {integrity}")
        digest = _sha256_file(partial)
        size = partial.stat().st_size
        with partial_metadata.open("x", encoding="utf-8") as handle:
            metadata_owned = True
            json.dump({"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "source": source.name, "backup": destination.name,
                       "bytes": size, "sha256": digest, "integrity": integrity}, handle, indent=2)
            handle.write("\n")
        partial.rename(destination)
        partial_metadata.rename(metadata)
    except BaseException as exc:
        if owned:
            for path in (partial, Path(str(partial) + "-wal"),
                         Path(str(partial) + "-shm"), Path(str(partial) + "-journal")):
                path.unlink(missing_ok=True)
        if metadata_owned:
            partial_metadata.unlink(missing_ok=True)
        if cancelled and not isinstance(exc, InterruptedError):
            raise InterruptedError("database backup cancelled by SIGTERM") from exc
        raise
    finally:
        if signal_installed:
            signal.signal(signal.SIGTERM, previous_sigterm)

    # No-JSON/failed historical files are held for recovery review, not silently
    # deleted. Only managed snapshots with valid metadata can expire, and the
    # actual bytes must still match their recorded SHA immediately before unlink.
    snapshots = []
    held = []
    for snapshot in sorted(destination_dir.glob("financial-*.sqlite3"), reverse=True):
        try:
            info = json.loads(snapshot.with_suffix(".json").read_text(encoding="utf-8"))
            if (not isinstance(info, dict) or snapshot.is_symlink()
                    or snapshot.resolve() == source or info.get("integrity") != "ok"
                    or info.get("backup") != snapshot.name
                    or info.get("source") != source.name
                    or info.get("bytes") != snapshot.stat().st_size
                    or not isinstance(info.get("sha256"), str)
                    or len(info["sha256"]) != 64
                    or _sha256_file(snapshot) != info["sha256"]):
                raise ValueError("not a verified managed snapshot")
            snapshots.append((snapshot, info))
        except (OSError, ValueError, TypeError):
            held.append(snapshot.name)
    expired_count = 0
    for expired, info in snapshots[keep:]:
        if _sha256_file(expired) != info["sha256"]:
            held.append(expired.name)
            continue
        expired.unlink()
        expired.with_suffix(".json").unlink()
        expired_count += 1
    return {
        "status": "ready", "backup": str(destination), "metadata": str(metadata),
        "sha256": digest, "bytes": destination.stat().st_size,
        "retained": len(snapshots) - expired_count, "held_for_review": held,
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
    # Never remove the preceding verified recovery point to make an attempt
    # fit. Retention is applied only after the replacement is verified below.
    # Content-address the archive entries. The same immutable artifact may be
    # referenced from more than one table/path; ZIP members must be written once.
    files: dict[str, dict] = {}
    tables = (
        ("source_documents", "source_key", "local_path", "content_hash"),
        ("source_artifacts", "artifact_key", "local_path", "content_hash"),
        ("universe_snapshots", "snapshot_id", "local_path", "content_hash"),
        ("universe_issuer_profiles", "issuer_id", "local_path", "content_hash"),
    )
    conn = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        digest_cache: dict[Path, str] = {}

        def file_digest(path: Path) -> str:
            resolved = path.resolve()
            if resolved not in digest_cache:
                digest_cache[resolved] = _sha256_file(resolved)
            return digest_cache[resolved]

        def archived_copy(content_hash: str) -> tuple[Path, Path] | None:
            """Resolve an immutable archive when a reviewed seed moved or changed."""
            archived = conn.execute(
                """SELECT local_path FROM source_artifacts
                WHERE content_hash=? AND status='archived' AND local_path IS NOT NULL
                ORDER BY archived_at DESC""", (content_hash,),
            ).fetchall()
            for candidate in archived:
                candidate_path = Path(candidate["local_path"])
                candidate_absolute = (
                    candidate_path if candidate_path.is_absolute()
                    else root / candidate_path
                ).resolve()
                if candidate_absolute.is_file() and file_digest(candidate_absolute) == content_hash:
                    return candidate_path, candidate_absolute
            return None

        for table, identity, local_path, content_hash in tables:
            if table == "source_artifacts":
                where = " WHERE status='archived'"
            elif table == "source_documents":
                # Superseded snapshots remain in SQLite for version lineage,
                # but a documented lost intermediate archive must not prevent
                # backing up the current, verified production evidence set.
                where = " WHERE status<>'superseded'"
            else:
                where = ""
            predicate = " AND" if where else " WHERE"
            query = (
                f"SELECT {identity} AS identity,{local_path} AS local_path,"
                f"{content_hash} AS content_hash FROM {table}{where}"
                f"{predicate} {local_path} IS NOT NULL"
            )
            for row in conn.execute(query):
                path = Path(row["local_path"])
                absolute = path if path.is_absolute() else root / path
                absolute = absolute.resolve()
                if not absolute.is_file():
                    fallback = archived_copy(row["content_hash"])
                    if fallback is None:
                        raise FileNotFoundError(
                            f"bundle source missing: {row['identity']}: {path}"
                        )
                    path, absolute = fallback
                digest = file_digest(absolute)
                if digest != row["content_hash"]:
                    # A reviewed seed manifest can evolve while the immutable
                    # pipeline artifact remains the evidence for the published
                    # source version.  Resolve that content-addressed artifact
                    # rather than either backing up changed bytes or failing a
                    # valid production backup forever.
                    fallback = archived_copy(row["content_hash"])
                    if fallback is None:
                        raise ValueError(f"bundle source hash mismatch: {row['identity']}")
                    path, absolute = fallback
                    digest = row["content_hash"]
                bundle_path = f"files/{digest}{absolute.suffix.lower()}"
                entry = files.setdefault(bundle_path, {
                    "content_hash": digest, "bytes": absolute.stat().st_size,
                    "bundle_path": bundle_path, "original_path": str(path),
                    "original_paths": [], "references": [], "_absolute": absolute,
                })
                if str(path) not in entry["original_paths"]:
                    entry["original_paths"].append(str(path))
                entry["references"].append({"table": table, "identity": row["identity"]})
    finally:
        conn.close()
    temporary_root = Path(tempfile.gettempdir())
    _require_bundle_capacity(
        source.stat().st_size, sum(item['bytes'] for item in files.values()),
        shutil.disk_usage(destination_dir).free, shutil.disk_usage(temporary_root).free,
        destination_dir.stat().st_dev == temporary_root.stat().st_dev)
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot = Path(temp_dir) / "financial.sqlite3"
        with closing(sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)) as source_db:
            with closing(sqlite3.connect(snapshot)) as backup_db:
                source_db.backup(backup_db); backup_db.commit()
                if backup_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("bundle database integrity check failed")
        database_hash = _sha256_file(snapshot)
        manifest_files = [
            {key: value for key, value in item.items() if key != "_absolute"}
            for item in files.values()
        ]
        manifest = {
            "format": "finengine-portable-bundle-v1",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "database": {"bundle_path": "database/financial.sqlite3",
                         "content_hash": database_hash, "bytes": snapshot.stat().st_size},
            "files": sorted(manifest_files, key=lambda item: item["bundle_path"]),
        }
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        try:
            with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=6) as archive:
                archive.write(snapshot, "database/financial.sqlite3")
                for item in files.values():
                    archive.write(item["_absolute"], item["bundle_path"])
                archive.writestr("manifest.json", manifest_bytes)
        except BaseException:
            # Only this invocation's incomplete archive, never other backups.
            partial.unlink(missing_ok=True)
            raise
        partial.replace(target)
    verification = verify_portable_bundle(target)
    bundle_hash = _sha256_file(target)
    sidecar = target.with_suffix(".json")
    sidecar.write_text(json.dumps({
        "bundle": target.name, "sha256": bundle_hash,
        **verification,
    }, indent=2) + "\n", encoding="utf-8")
    bundles = sorted(destination_dir.glob("financial-bundle-*.zip"), reverse=True)
    for expired in bundles[keep:]:
        expired.unlink(missing_ok=True); expired.with_suffix(".json").unlink(missing_ok=True)
    return {"status": "ready", "bundle": str(target), "metadata": str(sidecar),
            "sha256": bundle_hash, **verification}


def verify_portable_bundle(bundle: str | Path) -> dict:
    """Verify every byte represented by a portable bundle manifest."""
    path = Path(bundle)
    with zipfile.ZipFile(path, "r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        database = manifest["database"]
        with archive.open(database["bundle_path"]) as handle:
            database_hash = hashlib.file_digest(handle, "sha256").hexdigest()
        if database_hash != database["content_hash"]:
            raise ValueError("bundle database hash mismatch")
        for item in manifest["files"]:
            with archive.open(item["bundle_path"]) as handle:
                item_hash = hashlib.file_digest(handle, "sha256").hexdigest()
            if item_hash != item["content_hash"]:
                raise ValueError(f"bundle file hash mismatch: {item['bundle_path']}")
    return {"format": manifest["format"], "files": len(manifest["files"]),
            "database_bytes": database["bytes"],
            "source_bytes": sum(item["bytes"] for item in manifest["files"])}


def configure_production_schedules(
    database: str | Path,
    registry_path: str | Path = "config/companies.json",
    interval_seconds: int = 21600,
    source_limit: int = 50,
    use_llm: bool = False,
    raw_dir: str | Path = "data/raw",
) -> dict:
    """Idempotently configure monitoring for every enabled registry company."""
    db = Database(database)
    configured = []
    try:
        # The production database is the durable authority after a complete
        # universe activation.  Seed JSON remains authoritative for its own
        # companies, while DB-only activated issuers must not be omitted from
        # recurring monitoring and Saudi market-history collection.
        seed_registry = CompanyRegistry.from_json(registry_path)
        for company in seed_registry.all():
            db.register_company(company)
        registry = CompanyRegistry.combined(db.conn, registry_path)
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
            if company.market.value == "SA":
                market_schedule_id = f"market-history:SA:{company.symbol}"
                source_key = f"market-history:{company.company_id}"
                access_blocked = db.conn.execute(
                    """SELECT 1 FROM exceptions
                    WHERE company_id=? AND source_key=?
                    AND code='source_access_blocked' AND status='open'
                    LIMIT 1""",
                    (company.company_id, source_key),
                ).fetchone()
                if access_blocked:
                    # Do not recreate hundreds of jobs known to be impossible
                    # from this host. The archived exception/backlog remains the
                    # durable resume signal; resolving it re-enables scheduling
                    # on the next configuration pass.
                    with db.conn:
                        db.conn.execute(
                            "UPDATE schedules SET enabled=0,updated_at=CURRENT_TIMESTAMP "
                            "WHERE schedule_id=?",
                            (market_schedule_id,),
                        )
                    continue
                scheduler.upsert(
                    market_schedule_id,
                    f"Archive Saudi Exchange prices SA:{company.symbol}",
                    "market_history", interval_seconds,
                    {"symbol": company.symbol, "registry": str(registry_path),
                     "raw_dir": str(raw_dir), "sector": company.sector,
                     "market_segment": company.exchange},
                    company.company_id, priority=60,
                )
                configured.append(market_schedule_id)
        # LLM profile extraction is deliberately opt-in. The production worker
        # must remain useful with no model key and must not silently spend a
        # token budget every six hours. Unsupported deterministic extraction is
        # routed to the durable review backlog instead.
        if use_llm:
            scheduler.upsert(
                "profile-scan", "Scan archived annual reports for grounded company profiles",
                "profile_scan", interval_seconds,
                {"registry": str(registry_path), "raw_dir": str(raw_dir),
                 "limit": 10, "max_pages": 40, "model": "claude-opus-5"},
            )
            configured.append("profile-scan")
        scheduler.upsert(
            "understanding-refresh", "Re-score the 18-category 95% coverage contract",
            "understanding_refresh", interval_seconds,
            {"source_map_version": "18-categories-v1", "target_score": "95"},
            priority=80,
        )
        configured.append("understanding-refresh")
    finally:
        db.close()
    return {"status": "ready", "configured": configured, "count": len(configured)}
