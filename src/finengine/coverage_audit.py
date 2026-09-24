from __future__ import annotations

"""Deterministic raw-archive vs manifest coverage audit (Gap 3).

Answers one question honestly, per company: of everything actually archived
under ``data/raw/<market>/<symbol>/**``, what happened to it? Raw file COUNT
is never treated as coverage proof - two byte-identical files (an Arabic and
an English copy of the same filing, or a re-downloaded duplicate) are one
document, not two, so every classification is computed after deduplicating
by SHA-256 content hash.

Every unique archived document is classified into exactly one of:

  manifested_and_published     - linked to a source_documents row that is
                                  currently published.
  manifested_review_required   - linked to a source_documents row still
                                  awaiting review.
  duplicate_or_language_equivalent - a second (or further) artifact sharing
                                  the content hash of an already-classified
                                  document (a translation, a re-fetch, ...).
  context_only_nonfinancial    - not linked to any manifest, and its content
                                  type/URL/metadata identify it as investor
                                  collateral (presentation, webcast,
                                  transcript, sustainability report, ...)
                                  rather than a financial statement.
  unsupported_format           - not linked to any manifest, not identified
                                  as context-only, and its content type has
                                  no reader in this engine (anything other
                                  than PDF, XLSX or CSV/JSON).
  missing_manifest             - looks like a real financial-statement type
                                  document (PDF/XLSX/CSV) with no manifest
                                  or source_documents link at all - a real
                                  extraction gap.
  missing_binary                - archive-index/DB says the file exists at
                                  ``local_path``, but it is not on disk.
  hash_mismatch                 - the file is on disk, but its actual
                                  SHA-256 does not match the recorded
                                  content_hash (silent corruption/edit).

This module only reads; it never writes to the database or the filesystem.
"""

import hashlib
import json
from pathlib import Path

CLASSIFICATIONS = (
    "manifested_and_published",
    "manifested_review_required",
    "duplicate_or_language_equivalent",
    "context_only_nonfinancial",
    "market_data",
    "unsupported_format",
    "missing_manifest",
    "missing_binary",
    "hash_mismatch",
)

# Content types this engine has a reader for (reading.py / reading_xlsx.py /
# saudi_market.py CSV import / manifest JSON). Anything else archived under
# data/raw cannot currently be turned into a manifest at all.
SUPPORTED_CONTENT_TYPES = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "application/json",
})

# Generic keyword signals (on the source URL or archive-index metadata) that
# a document is investor collateral rather than a financial statement. Never
# company-specific - any issuer's presentation/webcast/ESG report matches.
NONFINANCIAL_KEYWORDS = (
    "presentation", "webcast", "transcript", "roadshow", "investor-day",
    "investor_day", "sustainability", "esg-report", "esg_report",
    "corporate-governance-report", "press-release", "newsletter",
)


def _sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _looks_nonfinancial(source_url: str, metadata: dict) -> bool:
    haystack = " ".join([
        source_url or "",
        json.dumps(metadata or {}, ensure_ascii=False),
    ]).casefold()
    return any(keyword in haystack for keyword in NONFINANCIAL_KEYWORDS)


# A daily price/volume/turnover history is market data, not a financial
# statement: it belongs to the market_data domain (see catalog.py) and is
# published through the separate market-history connector
# (saudi_market.py / finengine market-history), never through the
# financial-statements manifest pipeline. The archive layout already
# encodes this distinction structurally - every issuer's raw archive keeps
# price exports under a dedicated ``.../market/`` directory, sibling to
# ``.../documents/`` where statement PDFs/XLSX land - so this check reuses
# that existing convention instead of inventing a new one. A CSV/JSON here
# is out of the financial-statements package's coverage scope by
# definition; it is never a "missing manifest" gap for that package,
# whether or not it happens to already be linked to a published
# market-history source.
def _looks_like_market_data(local_path: str, content_type: str) -> bool:
    if content_type not in {"text/csv", "application/json"}:
        return False
    parts = {part.lower() for part in Path(local_path).parts}
    return "market" in parts


def classify_company_artifacts(db, company_id: str, project_root: str | Path = ".") -> list[dict]:
    """Classify every archived raw document for one company.

    Reads ``source_artifacts`` (the DB's record of ``data/raw/**``, built by
    ``finengine archive-sources`` from ``archive-index.json``), cross-checked
    against the filesystem and against ``source_documents``/
    ``source_artifact_links`` for manifest/publication status.
    """
    root = Path(project_root)
    rows = db.conn.execute(
        "SELECT * FROM source_artifacts WHERE company_id=? ORDER BY content_hash, artifact_key",
        (company_id,),
    ).fetchall()

    results: list[dict] = []
    seen_hashes: dict[str, dict] = {}
    for row in rows:
        artifact_key = row["artifact_key"]
        content_hash = row["content_hash"]
        local_path = row["local_path"]
        record = {
            "artifact_key": artifact_key,
            "content_hash": content_hash,
            "local_path": local_path,
            "source_url": row["source_url"],
            "content_type": row["content_type"],
        }

        path = (root / local_path) if not Path(local_path).is_absolute() else Path(local_path)
        if not path.is_file():
            record["classification"] = "missing_binary"
            record["evidence"] = f"local_path does not exist on disk: {local_path}"
            results.append(record)
            continue

        actual_hash = _sha256(path)
        if actual_hash != content_hash:
            record["classification"] = "hash_mismatch"
            record["evidence"] = (
                f"recorded content_hash={content_hash} but file on disk hashes to {actual_hash}"
            )
            results.append(record)
            continue

        if content_hash in seen_hashes:
            record["classification"] = "duplicate_or_language_equivalent"
            record["evidence"] = (
                f"same SHA-256 as already-classified artifact {seen_hashes[content_hash]['artifact_key']} "
                f"({seen_hashes[content_hash]['classification']})"
            )
            results.append(record)
            continue

        link = db.conn.execute(
            """SELECT d.status,d.source_key,d.filing_type FROM source_artifact_links l
            JOIN source_documents d ON d.source_key=l.source_key
            WHERE l.artifact_key=?""",
            (artifact_key,),
        ).fetchone()
        metadata = json.loads(row["metadata_json"] or "{}")
        if link is not None:
            if link["status"] == "published":
                record["classification"] = "manifested_and_published"
            else:
                record["classification"] = "manifested_review_required"
            record["evidence"] = f"linked to source_documents {link['source_key']} (status={link['status']})"
            record["source_key"] = link["source_key"]
            record["filing_type"] = link["filing_type"]
        elif _looks_nonfinancial(row["source_url"], metadata):
            record["classification"] = "context_only_nonfinancial"
            record["evidence"] = "no manifest link; URL/metadata identify it as investor collateral"
        elif _looks_like_market_data(row["local_path"], row["content_type"]):
            record["classification"] = "market_data"
            record["evidence"] = (
                "no manifest link; archived under a market/ directory - a daily "
                "price/volume history published through the separate market-history "
                "connector, not the financial-statements manifest pipeline. Out of "
                "this package's coverage scope, not an extraction gap."
            )
        elif row["content_type"] not in SUPPORTED_CONTENT_TYPES:
            record["classification"] = "unsupported_format"
            record["evidence"] = f"no manifest link; content_type {row['content_type']!r} has no reader"
        else:
            record["classification"] = "missing_manifest"
            record["evidence"] = (
                "no manifest link and content_type is a supported financial-document "
                "format - a real extraction gap"
            )
        seen_hashes[content_hash] = record
        results.append(record)

    return results


def summarize(records: list[dict]) -> dict:
    summary = {key: 0 for key in CLASSIFICATIONS}
    for record in records:
        summary[record["classification"]] += 1
    summary["total_raw_artifacts"] = len(records)
    summary["unique_documents"] = sum(
        summary[key] for key in CLASSIFICATIONS if key != "duplicate_or_language_equivalent"
    )
    return summary


def audit_companies(db, company_ids: list[str], project_root: str | Path = ".") -> dict:
    """Run the audit for several companies and return per-company + totals."""
    per_company = {}
    totals = {key: 0 for key in CLASSIFICATIONS}
    totals["total_raw_artifacts"] = 0
    totals["unique_documents"] = 0
    for company_id in company_ids:
        records = classify_company_artifacts(db, company_id, project_root)
        summary = summarize(records)
        per_company[company_id] = {"summary": summary, "records": records}
        for key in totals:
            totals[key] += summary[key]
    return {"companies": per_company, "totals": totals}
