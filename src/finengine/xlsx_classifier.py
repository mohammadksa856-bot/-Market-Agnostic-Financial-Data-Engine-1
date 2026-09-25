from __future__ import annotations

"""Generic workbook classifier and structural mapping selector.

Issuer 'data supplement' workbooks are read by `reading_xlsx.SupplementReader`
through reviewed row maps in ``config/supplements/*.json``.  Historically the
map was chosen from the company symbol (``<symbol>.json``), which silently
fails whenever an issuer reshapes its workbook and silently succeeds on a
workbook that no longer matches.  This module replaces that with evidence:

* ``fingerprint_workbook`` describes the workbook itself - sheet names, the
  header band that carries period columns, the periods found, unit evidence,
  the statement type each sheet looks like, and how many labelled rows it has.
* ``select_mapping`` scores every reviewed mapping against that fingerprint
  using only structure (sheet names present, period headers parse, mapped row
  phrases found in the sheet).  Company identity is never an input.
* When nothing matches, or several match indistinguishably, it raises
  ``MappingSelectionError`` carrying the evidence, so the pipeline can open a
  precise exception instead of guessing.

The workbook is opened read-only and never modified; its SHA-256 is recorded.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .reading_xlsx import _SCALE_WORDS, _column_period, _norm

# A mapping is structurally compatible when at least this share of its row
# phrases (over the sheets it names that exist in the workbook) is found.
# Calibrated on the 29 archived Saudi workbooks: every workbook scores 0.86-1.00
# against a mapping written for its own layout and at most 0.83 against a
# mapping written for another bank's layout, so 0.85 keeps foreign layouts out.
MIN_ROW_COVERAGE = 0.85
# A mapping reviewed for a different issuer needs a near-complete match.
CROSS_ISSUER_MIN_COVERAGE = 0.95
# ...and at least this many distinct metrics would be extracted.
MIN_METRICS = 6
# Two mappings closer than this in score are indistinguishable -> ambiguous.
AMBIGUITY_MARGIN = 0.03
HEADER_BAND_ROWS = 8

_STATEMENT_HINTS = {
    "income": ("net income", "net profit", "total operating income", "income before", "earnings per share",
               "operating expenses", "special commission income", "revenue"),
    "balance": ("total assets", "total liabilities", "total equity", "shareholders' equity",
                "customers' deposits", "cash and balances"),
    "cashflow": ("cash flows from operating", "net cash", "cash and cash equivalents at"),
}


class MappingSelectionError(Exception):
    """No mapping, or no unique mapping, is structurally compatible."""

    def __init__(self, code: str, message: str, evidence: dict):
        super().__init__(message)
        self.code = code
        self.evidence = evidence


@dataclass
class SheetFingerprint:
    name: str
    normalized_name: str
    statement_type: str
    header_row: int | None
    period_columns: int
    period_kinds: list[str]
    first_period: str | None
    last_period: str | None
    unit_evidence: list[str]
    date_typed_headers: int
    labelled_rows: int
    labels: list[str] = field(default_factory=list, repr=False)

    def summary(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "labels"}


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _collapse(name: str) -> str:
    return " ".join(str(name).split())


def _fingerprint_sheet(sheet) -> SheetFingerprint:
    import datetime

    periods: dict[tuple[int, int], tuple] = {}
    row_hits: dict[int, int] = {}
    unit_evidence: list[str] = []
    date_headers = 0
    for r, row in enumerate(sheet.iter_rows(min_row=1, max_row=HEADER_BAND_ROWS, values_only=True), 1):
        for c, cell in enumerate(row):
            if isinstance(cell, (datetime.date, datetime.datetime)):
                date_headers += 1
                continue
            if not isinstance(cell, str):
                continue
            period = _column_period(cell.replace("\n", " "))
            if period:
                periods[(r, c)] = period
                row_hits[r] = row_hits.get(r, 0) + 1
            for pattern, scale in _SCALE_WORDS:
                if pattern.search(cell):
                    unit_evidence.append(f"r{r}c{c + 1}:{cell.strip()[:60]}=>{scale}")
                    break
    labels: list[str] = []
    label_col = min((c for _, c in periods), default=None)
    for row in sheet.iter_rows(values_only=True):
        limit = label_col if label_col else len(row)
        text = next((cell for cell in row[:limit] if isinstance(cell, str) and cell.strip()), None)
        if text:
            labels.append(_norm(text))
    votes = {kind: sum(1 for label in labels if any(h in label for h in hints))
             for kind, hints in _STATEMENT_HINTS.items()}
    best = max(votes, key=votes.get)
    statement = best if votes[best] else "unknown"
    ordered = sorted(set(periods.values()), key=lambda p: p[2])
    return SheetFingerprint(
        name=sheet.title, normalized_name=_collapse(sheet.title), statement_type=statement,
        header_row=max(row_hits, key=row_hits.get) if row_hits else None,
        period_columns=len({c for _, c in periods}),
        period_kinds=sorted({p[0] for p in periods.values()}),
        first_period=ordered[0][2] if ordered else None,
        last_period=ordered[-1][2] if ordered else None,
        unit_evidence=unit_evidence[:4], date_typed_headers=date_headers,
        labelled_rows=len(labels), labels=labels,
    )


def fingerprint_workbook(path: str | Path) -> dict:
    """Describe a workbook's structure. Opens read-only; never alters the file."""
    import openpyxl

    path = Path(path)
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=False)
    try:
        sheets = [_fingerprint_sheet(sheet) for sheet in workbook.worksheets]
    finally:
        workbook.close()
    return {"path": str(path), "sha256": file_sha256(path),
            "sheet_names": [s.name for s in sheets], "sheets": sheets}


def _mapping_sheet_specs(mapping: dict) -> list[tuple[str, dict]]:
    return list((mapping.get("sheets") or {}).items())


def score_mapping(fp: dict, mapping: dict, period_kinds=("fy", "quarter", "ytd")) -> dict:
    """Structural compatibility of one mapping with one workbook fingerprint."""
    by_name = {s.normalized_name: s for s in fp["sheets"]}
    wanted = set(mapping.get("period_kinds", period_kinds)) & set(period_kinds)
    matched_sheets: list[str] = []
    missing_sheets: list[str] = []
    no_periods: list[str] = []
    phrases_total = phrases_found = 0
    metrics: set[str] = set()
    for sheet_name, row_map in _mapping_sheet_specs(mapping):
        sheet = by_name.get(_collapse(sheet_name))
        if sheet is None:
            missing_sheets.append(sheet_name)
            continue
        if not wanted.intersection(sheet.period_kinds):
            no_periods.append(sheet.name)
            continue
        matched_sheets.append(sheet.name)
        for phrase, spec in row_map.items():
            key = _norm(phrase)
            if not key:
                continue
            phrases_total += 1
            if any(key in label for label in sheet.labels):
                phrases_found += 1
                metrics.add(spec[0])
    coverage = phrases_found / phrases_total if phrases_total else 0.0
    reasons = []
    if not matched_sheets:
        reasons.append("no mapped sheet present with parseable period headers")
    if coverage < MIN_ROW_COVERAGE:
        reasons.append(f"row coverage {coverage:.2f} < {MIN_ROW_COVERAGE}")
    if len(metrics) < MIN_METRICS:
        reasons.append(f"only {len(metrics)} distinct metrics would be extracted (< {MIN_METRICS})")
    return {
        "compatible": not reasons, "score": round(coverage, 4), "row_coverage": round(coverage, 4),
        "phrases_found": phrases_found, "phrases_total": phrases_total,
        "metrics_extractable": len(metrics), "matched_sheets": matched_sheets,
        "missing_sheets": missing_sheets, "sheets_without_period_headers": no_periods,
        "reasons": reasons,
    }


def load_mappings(directory: str | Path = "config/supplements") -> list[tuple[Path, dict]]:
    found = []
    for path in sorted(Path(directory).glob("*.json")):
        found.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return found


def _fp_evidence(fp: dict) -> dict:
    return {"sha256": fp["sha256"], "sheet_names": fp["sheet_names"],
            "sheets": [s.summary() for s in fp["sheets"]]}


def select_mapping(xlsx_path: str | Path, mappings_dir: str | Path = "config/supplements",
                   period_kinds=("fy", "quarter", "ytd"), document_company_id: str | None = None) -> dict:
    """Pick the one reviewed mapping structurally compatible with the workbook.

    Returns ``{"mapping_path", "mapping", "fingerprint", "selection"}``.
    Raises ``MappingSelectionError`` (code ``xlsx_mapping_required`` or
    ``xlsx_mapping_ambiguous``) with evidence otherwise.  The company that owns
    the workbook never chooses the mapping.  ``document_company_id`` may only
    RAISE the bar: a mapping reviewed for a different issuer must match almost
    completely (``CROSS_ISSUER_MIN_COVERAGE``) and is flagged in the evidence.
    """
    try:
        fp = fingerprint_workbook(xlsx_path)
    except Exception as error:  # zip/xml corruption, password protection, ...
        raise MappingSelectionError(
            "xlsx_mapping_required", f"workbook cannot be opened for classification: {error!r}",
            {"path": str(xlsx_path), "unreadable": True, "error": repr(error)[:300]}) from error
    scored = []
    for path, mapping in load_mappings(mappings_dir):
        result = score_mapping(fp, mapping, period_kinds)
        result["mapping"] = path.name
        owner = mapping.get("company_id")
        result["cross_issuer"] = bool(document_company_id and owner and owner != document_company_id)
        if result["compatible"] and result["cross_issuer"] and result["row_coverage"] < CROSS_ISSUER_MIN_COVERAGE:
            result["compatible"] = False
            result["reasons"].append(
                f"mapping reviewed for {owner}; cross-issuer reuse needs coverage >= {CROSS_ISSUER_MIN_COVERAGE}")
        scored.append((result, path, mapping))
    scored.sort(key=lambda item: -item[0]["score"])
    ranking = [item[0] for item in scored[:5]]
    evidence = {**_fp_evidence(fp), "mappings_evaluated": len(scored), "top_candidates": ranking}
    compatible = [item for item in scored if item[0]["compatible"]]
    if not compatible:
        date_typed = sum(s.date_typed_headers for s in fp["sheets"])
        no_period = [s.name for s in fp["sheets"] if not s.period_columns]
        evidence["diagnosis"] = {
            "sheets_without_parseable_period_headers": no_period,
            "date_typed_header_cells": date_typed,
            "note": ("date-typed headers do not identify period kind (quarter/YTD/FY)"
                     if date_typed and no_period else None),
        }
        raise MappingSelectionError(
            "xlsx_mapping_required",
            "no reviewed mapping is structurally compatible with this workbook "
            f"(sheets: {fp['sheet_names']}); best row coverage "
            f"{ranking[0]['row_coverage'] if ranking else 0}",
            evidence)
    top = compatible[0]
    rivals = [item for item in compatible[1:] if top[0]["score"] - item[0]["score"] <= AMBIGUITY_MARGIN]
    if rivals:
        evidence["ambiguous_between"] = [top[0]["mapping"]] + [r[0]["mapping"] for r in rivals]
        raise MappingSelectionError(
            "xlsx_mapping_ambiguous",
            f"{len(rivals) + 1} mappings match this workbook indistinguishably: "
            f"{evidence['ambiguous_between']}",
            evidence)
    selection = {"mapping": top[1].name, "row_coverage": top[0]["row_coverage"],
                 "metrics_extractable": top[0]["metrics_extractable"],
                 "matched_sheets": top[0]["matched_sheets"], "cross_issuer": top[0]["cross_issuer"],
                 "selected_by": "workbook structure (sheet names, period headers, row labels)",
                 "workbook_sha256": fp["sha256"]}
    return {"mapping_path": top[1], "mapping": top[2], "fingerprint": fp, "selection": selection}
