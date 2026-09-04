from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path

from .connectors import LocalFileConnector
from .archive import load_archive_index
from .database import Database
from .domains import CompanyDomainStore
from .jobs import DurableScheduler
from .pipeline import Pipeline
from .registry import CompanyRegistry
from .report import export_readable_report


def _manifest_company(path: Path, payload: dict, registry: CompanyRegistry):
    if payload.get("company_id"):
        return registry.get(payload["company_id"])
    cik = payload.get("cik")
    if cik is not None:
        normalized = str(cik).zfill(10)
        matches = [company for company in registry.all() if company.cik == normalized]
        if len(matches) == 1:
            return matches[0]
    stem = path.stem.lower()

    def _tokens(company) -> set[str]:
        name = company.name.lower()
        tokens = {company.symbol.lower()}
        if "(" in name and ")" in name:
            tokens.add(name[name.index("(") + 1:name.index(")")].strip())
        tokens.update(word.strip(",.") for word in name.split())
        return {token for token in tokens if len(token) > 2}  # skip "sa", "co", ...

    matches = [company for company in registry.all()
               if any(token in stem for token in _tokens(company))]
    if len(matches) == 1:
        return matches[0]
    # The Saudi manifest contract has a flat facts list. This fallback is safe only
    # while the filename/name matching above left exactly one Saudi issuer.
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
    return counts


def _has_extractable_facts(payload: dict) -> bool:
    """Whether a manifest contains facts for the numeric staging pipeline.

    A domain-only manifest still receives an immutable source record and
    versioned publication. It must not invent a placeholder financial fact.
    """
    facts = payload.get("facts")
    return bool(facts) if isinstance(facts, (list, dict)) else False


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
        market_valuations = [domain_store.refresh_market_valuations(company.company_id)
                             for company in registry.all()]
        domain_store.refresh_all_backlog()
        if schedule_every is not None:
            scheduler=DurableScheduler(db)
            for company in registry.all():
                payload={
                    "market":company.market.value,"symbol":company.symbol,
                    "registry":str(registry_path),"raw_dir":str(raw_dir),
                    "source_index":company.sources[0] if company.sources else None,
                    "source_limit":12,"sa_manifest":None,
                }
                scheduler.upsert(
                    f"monitor:{company.market.value}:{company.symbol}",
                    f"Monitor {company.market.value}:{company.symbol}","monitor",
                    schedule_every,payload,company.company_id,
                )
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
        "scheduled": len(registry.all()) if schedule_every is not None else 0,
    }
