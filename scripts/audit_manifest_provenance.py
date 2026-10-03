"""Offline provenance scan: does every manifest fact appear on the page it cites?

Usage:
    python scripts/audit_manifest_provenance.py --company sa:7010 --company sa:7020 \
        [--imports data/imports] [--archive-index data/raw/archive-index.json] [--out scan.json]

Reads each manifest of the selected companies, finds its archived source PDF
(archive-index 'manifests' metadata, falling back to the manifest's source_url), extracts
the page text with PyMuPDF and runs ``finengine.manifest_audit``.  Read-only: it never
writes to data/, never touches the network and never edits a manifest.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finengine.manifest_audit import (  # noqa: E402
    audit_manifest_provenance, dominant_page_offset, quarters_vs_fiscal_year, summarise,
)


def _page_texts(path: Path) -> list[str]:
    import pymupdf  # optional extra: pip install pymupdf

    with pymupdf.open(path) as document:
        return [page.get_text() for page in document]


def _artifact_for(manifest_name: str, manifest: dict, artifacts: list[dict]) -> dict | None:
    company = manifest.get("company_id")
    for artifact in artifacts:
        if artifact.get("company_id") == company and manifest_name in artifact.get("metadata", {}).get("manifests", []):
            return artifact
    for artifact in artifacts:
        if artifact.get("company_id") == company and artifact.get("source_url") == manifest.get("source_url"):
            return artifact
    return None


def scan(companies: set[str], imports: Path, archive_index: Path) -> dict:
    artifacts = json.loads(archive_index.read_text(encoding="utf-8")).get("artifacts", [])
    cache: dict[str, list[str]] = {}
    manifests_scanned: dict[str, dict] = {}
    loaded = []
    for path in sorted(imports.glob("*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("company_id") not in companies:
            continue
        if not isinstance(manifest.get("facts"), list) or not manifest["facts"]:
            continue
        loaded.append(manifest)
        artifact = _artifact_for(path.name, manifest, artifacts)
        entry: dict = {"company_id": manifest["company_id"], "facts": len(manifest["facts"]),
                       "source_url": manifest.get("source_url")}
        local = ROOT / artifact["local_path"] if artifact else None
        if artifact is None:
            entry["document"] = "not_in_archive_index"
        elif not local.exists():
            entry["document"] = "archived_file_missing_locally"
            entry["archive_path"] = artifact["local_path"]
        else:
            if artifact["local_path"] not in cache:
                cache[artifact["local_path"]] = _page_texts(local)
            pages = cache[artifact["local_path"]]
            results = audit_manifest_provenance(manifest, pages)
            entry.update({
                "document": artifact["local_path"], "pages": len(pages),
                "summary": summarise(results), "dominant_page_offset": dominant_page_offset(results),
                "problems": [r.as_dict() for r in results if r.status not in ("ok",)],
            })
        manifests_scanned[path.name] = entry
    return {"manifests": manifests_scanned,
            "quarter_sum_vs_fiscal_year": quarters_vs_fiscal_year(loaded)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", action="append", required=True, help="company_id such as sa:7010")
    parser.add_argument("--imports", type=Path, default=ROOT / "data" / "imports")
    parser.add_argument("--archive-index", type=Path, default=ROOT / "data" / "raw" / "archive-index.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = scan(set(args.company), args.imports, args.archive_index)
    text = json.dumps(report, indent=2, ensure_ascii=False, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
