#!/usr/bin/env python3
"""Build one server-ready tar containing collected Saudi statements.

The bundle uses the production raw archive layout, carries an enqueue
manifest, and excludes hashes already present in the production database.
It is intentionally a one-time transfer artifact; ongoing collection should
run on the server after the initial archive has been seeded.
"""
from __future__ import annotations

import argparse
import io
import json
import tarfile
from pathlib import Path

import sa_raw_statement_collector as collector
from finengine import sa_raw_statements as raw


PROJECT = Path(__file__).resolve().parents[1]


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def _merged_registry() -> list[dict]:
    market = _load_json(PROJECT / "config" / "sa-market-registry.json", [])
    detailed = _load_json(PROJECT / "config" / "companies.json", [])
    merged = {row["company_id"]: dict(row) for row in market}
    for row in detailed:
        base = merged.get(row["company_id"], {})
        base.update(row)
        merged[row["company_id"]] = base
    return list(merged.values())


def build(root: Path, output: Path, exclude: set[str]) -> dict:
    records: list[dict] = []
    skipped = {"remote": 0, "invalid": 0, "metadata": 0, "non_statement": 0}
    for document in collector._collector_documents(root):
        digest = str(document.get("content_hash") or "")
        if document.get("bucket") != "statement":
            skipped["non_statement"] += 1
            continue
        if digest in exclude:
            skipped["remote"] += 1
            continue
        local_path = Path(str(document.get("local_path") or ""))
        if not digest or not local_path.is_file() or raw.sha256_bytes(local_path.read_bytes()) != digest:
            skipped["invalid"] += 1
            continue
        metadata = raw.publication_metadata(document)
        if not metadata.get("source_url") or not metadata.get("filed_at"):
            skipped["metadata"] += 1
            continue
        symbol = str(document["symbol"])
        kind = local_path.suffix.lower().lstrip(".") or "pdf"
        remote_path = raw.remote_target(symbol, digest, kind, "statement")
        records.append({
            "sha256": digest,
            "symbol": symbol,
            "local_path": str(local_path),
            "remote_path": remote_path,
            "metadata": metadata,
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w") as bundle:
        for record in records:
            arcname = record["remote_path"].removeprefix("/app/state/")
            bundle.add(record["local_path"], arcname=arcname, recursive=False)
        manifest = "".join(json.dumps({k: v for k, v in row.items() if k != "local_path"},
                                      ensure_ascii=False) + "\n" for row in records).encode("utf-8")
        info = tarfile.TarInfo("sa-bulk/manifest.jsonl")
        info.size = len(manifest)
        bundle.addfile(info, io.BytesIO(manifest))
        registry = (json.dumps(_merged_registry(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        info = tarfile.TarInfo("sa-bulk/registry.json")
        info.size = len(registry)
        bundle.addfile(info, io.BytesIO(registry))
        bundle.add(PROJECT / "scripts" / "sa_bulk_ingest_server.py",
                   arcname="sa-bulk/ingest.py", recursive=False)
    return {"documents": len(records), "bytes": output.stat().st_size,
            "skipped": skipped, "output": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--exclude-hashes", type=Path)
    args = parser.parse_args()
    exclude = set(_load_json(args.exclude_hashes, [])) if args.exclude_hashes else set()
    print(json.dumps(build(args.root, args.output, exclude), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
