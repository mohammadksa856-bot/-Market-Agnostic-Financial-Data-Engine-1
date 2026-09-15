from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import shutil
import tempfile
import uuid
from contextlib import closing
from pathlib import Path
from typing import Iterable

from .connectors import LocalFileConnector
from .archive import load_archive_index
from .database import Database
from .domains import CompanyDomainStore
from .jobs import DurableScheduler
from .pipeline import Pipeline
from .registry import CompanyRegistry
from .report import export_readable_report


MANIFEST_DOMAIN_KEYS = (
    "company_attributes", "disclosures", "ownership_positions",
    "corporate_actions", "market_prices", "consensus_estimates",
)


def _manifest_company(path: Path, payload: dict, registry: CompanyRegistry):
    if payload.get("company_id"):
        return registry.get(payload["company_id"])
    cik = payload.get("cik")
    if cik is not None:
        normalized = str(cik).zfill(10)
        matches = [company for company in registry.all() if company.cik == normalized]
        if len(matches) == 1:
            return matches[0]
    stem_tokens = set(re.findall(r"[a-z0-9]+", path.stem.lower()))
    generic_name_tokens = {
        "arabian", "bank", "company", "corporation", "financial", "group",
        "holding", "holdings", "international", "limited", "national", "saudi",
    }
    # Prefer a distinctive issuer-name token over a numeric ticker. Annual
    # manifest names contain years, and a year such as 2019 can itself be a
    # valid Saudi ticker in the full production registry.
    name_matches = []
    for company in registry.all():
        name_tokens = {
            token for token in re.findall(r"[a-z0-9]+", company.name.lower())
            if len(token) >= 4 and token not in generic_name_tokens
        }
        if name_tokens & stem_tokens:
            name_matches.append(company)
    if len(name_matches) == 1:
        return name_matches[0]
    symbol_matches = [
        company for company in registry.all()
        if company.symbol.lower() in stem_tokens
    ]
    if len(symbol_matches) == 1:
        return symbol_matches[0]
    # The Saudi manifest contract has a flat facts list. This fallback is safe only
    # while the selected registry contains one Saudi issuer.
    if isinstance(payload.get("facts"), list):
        matches = [company for company in registry.all() if company.market.value == "SA"]
        if len(matches) == 1:
            return matches[0]
    raise ValueError(f"cannot identify company for manifest: {path}")


def _publish_manifest_domains(
    db: Database, company, payload: dict, source_key: str,
) -> dict[str, dict[str, int]]:
    """Publish reviewed non-financial domains from the same immutable manifest.

    Domain records deliberately bypass the numeric extractor, but retain the
    manifest's content-addressed source key and their own version history.
    """
    store = CompanyDomainStore(db)
    counts: dict[str, dict[str, int]] = {}

    def record(domain: str, state: str) -> None:
        bucket = counts.setdefault(domain, {"inserted": 0, "restated": 0, "duplicate": 0})
        bucket[state] += 1

    effective_at = payload.get("period_end") or payload.get("filed_at")
    for item in payload.get("company_attributes", []):
        state = db.publish_company_attribute(
            company.company_id, item["attribute_key"], item["value"],
            item.get("effective_at", effective_at), source_key,
            item.get("category", "general"), item.get("language", "en"),
            item.get("metadata"),
        )
        record("company_attributes", state)
    for item in payload.get("disclosures", []):
        state = db.publish_disclosure(
            company.company_id, item["disclosure_type"], item["title"], item["body_text"],
            item.get("published_at", payload.get("filed_at")), source_key,
            item.get("period_end", payload.get("period_end")), item.get("language", "en"),
            item.get("metadata"),
        )
        record("disclosures", state)
    for item in payload.get("ownership_positions", []):
        values = dict(item)
        values.update(company_id=company.company_id, source_key=source_key)
        state = store.publish_ownership_position(**values)
        record("ownership_positions", state)
    for item in payload.get("corporate_actions", []):
        values = dict(item)
        values.update(company_id=company.company_id, source_key=source_key)
        state = store.publish_corporate_action(**values)
        record("corporate_actions", state)
    for item in payload.get("market_prices", []):
        values = dict(item)
        values.update(company_id=company.company_id, source_key=source_key)
        state = store.publish_market_price(**values)
        record("market_prices", state)
    for item in payload.get("consensus_estimates", []):
        values = dict(item)
        values.update(company_id=company.company_id, source_key=source_key)
        state = store.publish_consensus_estimate(**values)
        record("consensus_estimates", state)
    return counts


def _has_extractable_facts(payload: dict) -> bool:
    """Whether a manifest contains facts for the numeric staging pipeline.

    A domain-only manifest still receives an immutable source record and
    versioned publication. It must not invent a placeholder financial fact.
    """
    facts = payload.get("facts")
    return bool(facts) if isinstance(facts, (list, dict)) else False


def _manifest_row_count(payload: dict) -> int:
    facts = payload.get("facts")
    if isinstance(facts, list):
        count = len(facts)
    elif isinstance(facts, dict):
        # SEC Company Facts is nested, so a non-empty object is sufficient for
        # this structural gate. The normal extractor performs the exact count.
        count = int(bool(facts))
    else:
        count = 0
    return count + sum(len(payload.get(key) or []) for key in MANIFEST_DOMAIN_KEYS)


def _portable_manifest_path(path: Path, project_root: str | Path) -> str:
    try:
        return os.path.relpath(path.resolve(), Path(project_root).resolve())
    except ValueError:
        return str(path.resolve())


def _validate_manifest_identity(path: Path, payload: dict, company) -> None:
    if not isinstance(payload, dict):
        raise TypeError(f"manifest must contain a JSON object: {path}")
    if not _manifest_row_count(payload):
        raise ValueError(f"manifest contains no publishable facts or domains: {path}")
    if payload.get("company_id") and payload["company_id"] != company.company_id:
        raise ValueError(f"manifest company_id does not match registry: {path}")
    if payload.get("market") and str(payload["market"]).upper() != company.market.value:
        raise ValueError(f"manifest market does not match registry: {path}")
    if payload.get("symbol") and str(payload["symbol"]).upper() != company.symbol.upper():
        raise ValueError(f"manifest symbol does not match registry: {path}")


def _domain_state_totals(domains: dict[str, dict[str, int]]) -> dict[str, int]:
    return {
        state: sum(bucket.get(state, 0) for bucket in domains.values())
        for state in ("inserted", "restated", "duplicate")
    }


def _apply_reviewed_manifest(
    db: Database,
    registry: CompanyRegistry,
    manifest: Path,
    raw_dir: str | Path,
    project_root: str | Path,
) -> dict:
    """Apply one immutable reviewed manifest without replacing the database.

    Every production table already has version-aware/idempotent publishers. A
    content-addressed source that is already published skips the numeric
    pipeline entirely, avoiding a new pipeline run/publication batch on every
    deployment, while domain rows are replayed to recover safely from a prior
    partial domain publication.
    """
    content = manifest.read_bytes()
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise TypeError(f"manifest must contain a JSON object: {manifest}")
    company = _manifest_company(manifest, payload, registry)
    _validate_manifest_identity(manifest, payload, company)
    db.register_company(company)

    digest = hashlib.sha256(content).hexdigest()
    source_key = f"file:{digest}"
    previous_status = db.source_status(source_key)
    portable_path = _portable_manifest_path(manifest, project_root)
    has_facts = _has_extractable_facts(payload)

    if has_facts and previous_status != "published":
        numeric = Pipeline(db, raw_dir).run(company, LocalFileConnector(manifest))
        if numeric["status"] not in {"published", "duplicate"}:
            raise RuntimeError(f"manifest did not publish: {manifest.name}: {numeric}")
    elif has_facts:
        numeric = {
            "status": "duplicate", "source_key": source_key, "published": 0,
            "inserted": 0, "restated": 0, "duplicates": 0,
        }
    else:
        document = LocalFileConnector(manifest).fetch(company)
        db.save_source(document, digest, portable_path)
        numeric = {
            "status": "duplicate" if previous_status == "published" else "published",
            "source_key": source_key, "published": 0, "inserted": 0,
            "restated": 0, "duplicates": 0,
        }

    # Keep the reviewed repository path as the portable source identity. The
    # pipeline's separate source_artifact row retains its immutable raw copy.
    db.conn.execute(
        "UPDATE source_documents SET local_path=? WHERE source_key=? AND content_hash=?",
        (portable_path, source_key, digest),
    )
    db.conn.commit()

    domains = _publish_manifest_domains(db, company, payload, source_key)
    domain_totals = _domain_state_totals(domains)
    domain_changes = domain_totals["inserted"] + domain_totals["restated"]
    source_registered = previous_status is None
    if not has_facts:
        db.set_source_status(source_key, "published")
    # The numeric pipeline already records its own batch. Record an additional
    # domain-only batch only when this replay actually changed durable state.
    if domain_changes or (not has_facts and source_registered):
        db.publication_batch(
            source_key, company.company_id, "published", 0, domain_changes,
        )

    numeric_changes = int(numeric.get("inserted", 0)) + int(numeric.get("restated", 0))
    changed = source_registered or numeric_changes > 0 or domain_changes > 0
    return {
        "manifest": manifest.name,
        "manifest_path": str(manifest),
        "company_id": company.company_id,
        "source_key": source_key,
        "status": "published" if changed else "duplicate",
        "source_registered": source_registered,
        "numeric": numeric,
        "domains": domains,
        "counts": {
            "inserted": int(numeric.get("inserted", 0)) + domain_totals["inserted"],
            "restated": int(numeric.get("restated", 0)) + domain_totals["restated"],
            "duplicate": int(numeric.get("duplicates", 0)) + domain_totals["duplicate"],
        },
    }


def _selected_manifests(
    imports_dir: str | Path, manifest_paths: Iterable[str | Path] | None,
) -> list[Path]:
    imports = Path(imports_dir)
    if manifest_paths:
        selected = []
        for value in manifest_paths:
            path = Path(value)
            if not path.is_file():
                path = imports / path
            if not path.is_file():
                raise FileNotFoundError(path)
            selected.append(path)
    else:
        selected = sorted(imports.glob("*.json"))
    if not selected:
        raise FileNotFoundError(f"no JSON manifests found in {imports}")
    return selected


def _verify_selected_manifests(manifests: list[Path]) -> dict:
    """Run deterministic manifest checks before opening the live DB writable."""
    from .verification import ManifestVerifier

    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        names = [manifest.name for manifest in manifests]
        if len(names) != len(set(names)):
            raise ValueError("selected manifests must have unique filenames")
        for manifest in manifests:
            # Preserve legacy filename prefixes because they are part of the
            # issuer identity for manifests created before company_id headers.
            shutil.copy2(manifest, staging / manifest.name)
        report = ManifestVerifier(staging).verify()
    if report["failures"] or report["unmapped_labels"]:
        raise ValueError(
            "reviewed manifest verification failed before publication: "
            f"failures={report['failures']} unmapped={len(report['unmapped_labels'])}"
        )
    return report


def _clone_database(source: Path, destination: Path) -> None:
    source_uri = f"file:{source.resolve().as_posix()}?mode=ro"
    with closing(sqlite3.connect(source_uri, uri=True)) as source_db:
        with closing(sqlite3.connect(destination)) as destination_db:
            source_db.backup(destination_db)
            destination_db.commit()


def _sync_manifests_to_database(
    db: Database,
    manifests: list[Path],
    registry_path: str | Path,
    raw_dir: str | Path,
    archive_index: str | Path | None,
    project_root: str | Path,
) -> dict:
    registry = CompanyRegistry.combined(db.conn, registry_path)
    results = [
        _apply_reviewed_manifest(db, registry, manifest, raw_dir, project_root)
        for manifest in manifests
    ]
    archived_artifacts = (
        load_archive_index(db, archive_index, project_root) if archive_index else 0
    )
    impacted = sorted({row["company_id"] for row in results})
    store = CompanyDomainStore(db)
    company_results = []
    from .understanding import refresh_company_understanding

    for company_id in impacted:
        changed_payloads = [
            json.loads(manifest.read_text(encoding="utf-8"))
            for manifest, row in zip(manifests, results)
            if row["company_id"] == company_id and row["status"] == "published"
        ]
        market_statistics = None
        market_valuation = None
        if any(payload.get("market_prices") for payload in changed_payloads):
            market_statistics = store.refresh_market_statistics(company_id)
            market_valuation = store.refresh_market_valuations(company_id)
        backlog = store.refresh_company_backlog(company_id)
        understanding = refresh_company_understanding(db.conn, company_id)
        company_results.append({
            "company_id": company_id,
            "catalog_score": backlog["catalog_score"],
            "backlog_open": backlog["open"],
            "understanding_score": understanding["total_score"],
            "market_statistics": market_statistics,
            "market_valuation": market_valuation,
        })
    integrity = db.conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"database failed integrity check after manifest sync: {integrity}")
    totals = {
        state: sum(row["counts"][state] for row in results)
        for state in ("inserted", "restated", "duplicate")
    }
    return {
        "status": "ready",
        "manifests": len(results),
        "published_manifests": sum(row["status"] == "published" for row in results),
        "duplicate_manifests": sum(row["status"] == "duplicate" for row in results),
        "counts": totals,
        "archived_artifacts_loaded": archived_artifacts,
        "companies": company_results,
        "integrity": integrity,
        "results": results,
    }


def sync_reviewed_manifests(
    database: str | Path,
    imports_dir: str | Path = "data/imports",
    registry_path: str | Path = "config/companies.json",
    raw_dir: str | Path = "data/raw",
    manifest_paths: Iterable[str | Path] | None = None,
    archive_index: str | Path | None = "data/raw/archive-index.json",
    project_root: str | Path = ".",
    backup_dir: str | Path | None = None,
    backup_keep: int = 3,
) -> dict:
    """Safely sync reviewed manifests into an existing persistent database.

    The complete selected set is first verified and applied to an online SQLite
    clone. Only after that succeeds is the live database opened for writes. A
    retry is safe: content-addressed sources and version-aware domain publishers
    leave production rows and their versions unchanged for duplicate inputs.
    """
    target = Path(database)
    if not target.is_file():
        raise FileNotFoundError(
            f"manifest sync requires an existing database (refusing to create {target})"
        )
    manifests = _selected_manifests(imports_dir, manifest_paths)
    verification = _verify_selected_manifests(manifests)

    with tempfile.TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        clone = temporary_root / "preflight.sqlite3"
        _clone_database(target, clone)
        preview_db = Database(clone)
        try:
            preview = _sync_manifests_to_database(
                preview_db, manifests, registry_path, temporary_root / "raw",
                archive_index, project_root,
            )
        finally:
            preview_db.close()

    backup = None
    if backup_dir and preview["published_manifests"]:
        from .operations import backup_database
        backup = backup_database(target, backup_dir, backup_keep)

    live_db = Database(target)
    try:
        result = _sync_manifests_to_database(
            live_db, manifests, registry_path, raw_dir, archive_index, project_root,
        )
    finally:
        live_db.close()
    result.update({
        "database": str(target),
        "verification": {
            "checks": verification["checks"],
            "passed": verification["passed"],
            "warnings": verification["warnings"],
            "failures": verification["failures"],
            "unmapped_labels": len(verification["unmapped_labels"]),
        },
        "preflight": {
            "status": preview["status"],
            "published_manifests": preview["published_manifests"],
            "integrity": preview["integrity"],
        },
        "backup": backup,
    })
    return result


def rebuild_snapshot(
    output_path: str | Path,
    imports_dir: str | Path = "data/imports",
    registry_path: str | Path = "config/companies.json",
    raw_dir: str | Path = "data/raw",
    replace: bool = False,
    html_path: str | Path | None = None,
    csv_path: str | Path | None = None,
    schedule_every: int | None = None,
) -> dict:
    """Build a complete snapshot atomically from reviewed, versioned manifests."""
    target = Path(output_path)
    imports = Path(imports_dir)
    manifests = sorted(imports.glob("*.json"))
    if not manifests:
        raise FileNotFoundError(f"no JSON manifests found in {imports}")
    if target.exists() and not replace:
        raise FileExistsError(f"snapshot already exists: {target}; use replace=True")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.building-{uuid.uuid4().hex}")
    registry = CompanyRegistry.from_json(registry_path)
    results = []
    db = Database(temporary)
    try:
        for company in registry.all():
            db.register_company(company)
        pipeline = Pipeline(db, raw_dir)
        for manifest in manifests:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            company = _manifest_company(manifest, payload, registry)
            digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
            source_key = f"file:{digest}"
            try:
                portable_path = os.path.relpath(manifest.resolve(), Path.cwd().resolve())
            except ValueError:
                portable_path = str(manifest.resolve())
            has_facts = _has_extractable_facts(payload)
            if has_facts:
                result = pipeline.run(company, LocalFileConnector(manifest))
                if result["status"] not in {"published", "duplicate"}:
                    raise RuntimeError(f"manifest did not publish: {manifest.name}: {result}")
                db.conn.execute(
                    "UPDATE source_documents SET local_path=? WHERE source_key=?",
                    (portable_path, source_key),
                )
                db.conn.commit()
            else:
                document = LocalFileConnector(manifest).fetch(company)
                db.save_source(document, digest, portable_path)
                result = {"status": "published", "source_key": source_key, "published": 0}
            domains = _publish_manifest_domains(db, company, payload, source_key)
            if not has_facts:
                domain_rows = sum(sum(bucket.values()) for bucket in domains.values())
                db.set_source_status(source_key, "published")
                db.publication_batch(source_key, company.company_id, "published", 0, domain_rows)
            results.append({
                "manifest": manifest.name, "company_id": company.company_id,
                "status": result["status"], "published": result.get("published", 0),
                "domains": domains,
            })
        archived_artifacts = load_archive_index(
            db, Path(raw_dir) / "archive-index.json", Path.cwd(),
        )
        domain_store = CompanyDomainStore(db)
        market_statistics = [domain_store.refresh_market_statistics(company.company_id)
                             for company in registry.all()]
        market_valuations = [domain_store.refresh_market_valuations(company.company_id)
                             for company in registry.all()]
        domain_store.refresh_all_backlog()
        scheduled_count = 0
        if schedule_every is not None:
            scheduler=DurableScheduler(db)
            for company in registry.all():
                if not company.enabled:
                    continue
                payload={
                    "market":company.market.value,"symbol":company.symbol,
                    "registry":str(registry_path),"raw_dir":str(raw_dir),
                    "source_index":company.sources[0] if company.sources else None,
                    "source_limit":12,"sa_manifest":None,
                    "browser":company.market.value == "SA","llm":False,
                }
                scheduler.upsert(
                    f"monitor:{company.market.value}:{company.symbol}",
                    f"Monitor {company.market.value}:{company.symbol}","monitor",
                    schedule_every,payload,company.company_id,
                )
                scheduled_count += 1
        health = db.health()
        integrity = db.conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"built database failed integrity check: {integrity}")
    finally:
        db.close()
    backup = None
    try:
        if target.exists():
            backup = target.with_suffix(target.suffix + ".bak")
            shutil.copy2(target, backup)
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    if html_path and csv_path:
        export_readable_report(str(target), str(html_path), str(csv_path))
    return {
        "status": "ready", "database": str(target), "backup": str(backup) if backup else None,
        "manifests": len(results), "results": results, "health": health,
        "archived_artifacts": archived_artifacts,
        "market_valuations": market_valuations,
        "scheduled": scheduled_count,
    }
