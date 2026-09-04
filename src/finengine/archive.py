from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .database import Database
from .registry import CompanyRegistry


def _company_for_manifest(path: Path, payload: dict, registry: CompanyRegistry):
    if payload.get("company_id"):
        return registry.get(payload["company_id"])
    cik = payload.get("cik")
    if cik is not None:
        normalized = str(cik).zfill(10)
        matches = [company for company in registry.all() if company.cik == normalized]
        if len(matches) == 1:
            return matches[0]
    stem = path.stem.lower()
    matches = [company for company in registry.all() if company.symbol.lower() in stem]
    if len(matches) == 1:
        return matches[0]
    if isinstance(payload.get("facts"), list):
        matches = [company for company in registry.all() if company.market.value == "SA"]
        if len(matches) == 1:
            return matches[0]
    raise ValueError(f"cannot identify company for manifest: {path}")


def _extension(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".pdf", ".html", ".htm", ".json", ".xlsx"}:
        return ".html" if suffix == ".htm" else suffix
    return mimetypes.guess_extension(content_type.split(";", 1)[0]) or ".bin"


def _read_limited(response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"source artifact exceeded {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def load_archive_index(
    db: Database, index_path: str | Path, project_root: str | Path = ".",
) -> int:
    """Load the portable archive inventory and link artifacts to reviewed manifests."""
    path = Path(index_path)
    if not path.is_file():
        return 0
    root = Path(project_root).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    count = 0
    for item in payload.get("artifacts", []):
        local = Path(item["local_path"])
        absolute = local if local.is_absolute() else root / local
        if not absolute.is_file():
            continue
        digest = hashlib.sha256(absolute.read_bytes()).hexdigest()
        if digest != item["content_hash"]:
            raise ValueError(f"raw archive hash mismatch: {local}")
        db.save_source_artifact(
            item["artifact_key"], item["company_id"], item["source_url"], digest,
            item["local_path"], item["content_type"], absolute.stat().st_size,
            item.get("metadata"),
        )
        count += 1
    return count


def archive_manifest_sources(
    db_path: str | Path,
    imports_dir: str | Path = "data/imports",
    registry_path: str | Path = "config/companies.json",
    raw_dir: str | Path = "data/raw",
    index_path: str | Path | None = None,
    project_root: str | Path = ".",
    market: str | None = None,
    symbol: str | None = None,
    opener=urlopen,
    max_bytes: int = 150 * 1024 * 1024,
    user_agent: str = "MarketAgnosticFinancialDataEngine/1.3 archive@example.com",
) -> dict:
    """Download every distinct official manifest source into a content-addressed archive."""
    imports = Path(imports_dir)
    raw = Path(raw_dir)
    root = Path(project_root).resolve()
    index = Path(index_path) if index_path else raw / "archive-index.json"
    registry = CompanyRegistry.from_json(registry_path)
    selected: dict[tuple[str, str], dict] = {}
    for manifest in sorted(imports.glob("*.json")):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        source_url = payload.get("source_url")
        if not source_url:
            continue
        company = _company_for_manifest(manifest, payload, registry)
        if market and company.market.value.upper() != market.upper():
            continue
        if symbol and company.symbol.upper() != symbol.upper():
            continue
        key = (company.company_id, source_url)
        selected.setdefault(key, {
            "company_id": company.company_id, "market": company.market.value,
            "symbol": company.symbol, "source_url": source_url, "manifests": [],
        })["manifests"].append(manifest.name)

    existing: dict[tuple[str, str], dict] = {}
    if index.is_file():
        current = json.loads(index.read_text(encoding="utf-8"))
        existing = {
            (item["company_id"], item["source_url"]): item
            for item in current.get("artifacts", [])
        }

    db = Database(db_path)
    results = []
    try:
        for company in registry.all():
            db.register_company(company)
        for key, item in sorted(selected.items()):
            previous = existing.get(key)
            if previous:
                local = Path(previous["local_path"])
                absolute = local if local.is_absolute() else root / local
                if absolute.is_file() and hashlib.sha256(absolute.read_bytes()).hexdigest() == previous["content_hash"]:
                    previous["metadata"] = {
                        **previous.get("metadata", {}),
                        "manifests": sorted(set(item["manifests"])), "immutable": True,
                    }
                    db.save_source_artifact(
                        previous["artifact_key"], previous["company_id"], previous["source_url"],
                        previous["content_hash"], previous["local_path"], previous["content_type"],
                        absolute.stat().st_size, previous.get("metadata"),
                    )
                    results.append({"status": "duplicate", **previous})
                    continue
            request = Request(item["source_url"], headers={"User-Agent": user_agent})
            with opener(request, timeout=120) as response:
                content = _read_limited(response, max_bytes)
                content_type = (response.headers.get_content_type()
                                if hasattr(response.headers, "get_content_type")
                                else response.headers.get("Content-Type", "application/octet-stream").split(";", 1)[0])
            if not content:
                raise ValueError(f"downloaded source was empty: {item['source_url']}")
            if item["source_url"].lower().endswith(".pdf") and not content.startswith(b"%PDF-"):
                raise ValueError(f"expected PDF but received different content: {item['source_url']}")
            digest = hashlib.sha256(content).hexdigest()
            extension = _extension(item["source_url"], content_type)
            target = raw / item["market"] / item["symbol"] / "documents" / f"{digest}{extension}"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                partial = target.with_suffix(target.suffix + ".part")
                partial.write_bytes(content)
                partial.replace(target)
            try:
                portable = os.path.relpath(target.resolve(), root)
            except ValueError:
                portable = str(target.resolve())
            artifact = {
                "artifact_key": f"artifact:{item['company_id']}:{digest}",
                "company_id": item["company_id"], "source_url": item["source_url"],
                "content_hash": digest, "local_path": portable,
                "content_type": content_type, "byte_size": len(content),
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {"manifests": item["manifests"], "immutable": True},
            }
            existing[key] = artifact
            db.save_source_artifact(
                artifact["artifact_key"], artifact["company_id"], artifact["source_url"],
                digest, portable, content_type, len(content), artifact["metadata"],
            )
            results.append({"status": "archived", **artifact})
        index.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": sorted(existing.values(), key=lambda row: (row["company_id"], row["source_url"])),
        }
        temporary = index.with_suffix(index.suffix + ".part")
        temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(index)
    finally:
        db.close()
    return {
        "status": "ready", "sources": len(results),
        "archived": sum(row["status"] == "archived" for row in results),
        "duplicates": sum(row["status"] == "duplicate" for row in results),
        "bytes": sum(int(row["byte_size"]) for row in results),
        "index": str(index), "results": results,
    }
