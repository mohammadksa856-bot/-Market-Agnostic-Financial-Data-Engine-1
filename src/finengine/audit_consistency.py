from __future__ import annotations

"""Offline, report-only consistency audits over reviewed manifests.

These checks complement ``verification.ManifestVerifier``.  The verifier proves
accounting identities (assets = liabilities + equity, ...), which a manifest can
satisfy while still mixing definitions between periods or double counting a
component.  Everything here is deterministic, needs no network or database and
never modifies a manifest: callers get findings to review, not "corrected"
numbers.

Checks
------
``definition_drift``
    The same company/metric carries labels with different composition in
    different periods (for example FY2024 ``capex`` = PP&E + intangibles but
    FY2025 ``capex`` = PP&E only), so a year-over-year comparison is not
    like-for-like.
``dimension_reconciliation``
    Dimensioned components (borrowings by instrument, revenue by geography,
    ...) must add back to the face-statement total in the same period.  A
    component listed twice (or a composite label that already contains a
    sibling) breaks the sum by more than rounding.
``filing_date_before_exchange_upload``
    Saudi Exchange ``fsPdf`` URLs embed the upload date.  A ``filed_at`` earlier
    than that date (typically the board-approval date) cannot be the date the
    market could first see the document, which causes look-ahead in point-in-time
    use.  Manifests that declare a ``filed_at_basis`` are skipped.
"""

import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Metrics whose label composition legitimately changes meaning (what is summed).
COMPOSITION_SENSITIVE = frozenset({
    "capex", "proceeds_asset_sales", "depreciation_amortization", "current_debt",
    "other_current_liabilities", "dividends_paid", "interest_paid",
    "lease_payments", "taxes_paid", "zakat_paid",
})

_LABEL_STOP = frozenset(
    "of and the in on net total for from to plus restated by during year period at with".split()
)

# (component metric, dimension key, total metrics that the components sum to)
DIMENSION_RECONCILIATIONS = (
    ("borrowings_by_instrument", "instrument", ("current_debt", "long_term_debt")),
    ("revenue_by_geography", "geography", ("revenue",)),
    ("revenue_by_product", "product", ("revenue",)),
    ("segment_revenue", "segment", ("revenue",)),
    ("property_plant_equipment_by_class", "asset_class", ("property_plant_equipment",)),
)

_EXCHANGE_UPLOAD = re.compile(r"/fsPdf/\d+_\d+_(\d{4}-\d{2}-\d{2})_")


def load_manifests(imports_dir: str | Path, prefix: str | None = None) -> list[tuple[str, dict]]:
    manifests = []
    for path in sorted(Path(imports_dir).glob("*.json")):
        if prefix and not path.name.startswith(prefix):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("facts"), list):
            manifests.append((path.name, payload))
    return manifests


def _label(fact: dict) -> str:
    return str(fact.get("source_label") or fact.get("label") or "")


def _scaled(fact: dict) -> Decimal | None:
    try:
        raw = Decimal(str(fact["value"]))
        scale = fact.get("scale")
        return raw * Decimal(str(scale)) if scale not in (None, "") else raw
    except (InvalidOperation, KeyError, TypeError):
        return None


def label_signature(label: str) -> frozenset[str]:
    """Content words of a label; punctuation, plurals and '(restated)' ignored."""
    text = re.sub(r"\([^)]*\)", "", label.lower())
    return frozenset(
        word.rstrip("s") for word in re.findall(r"[a-z]+", text) if word not in _LABEL_STOP
    )


def definition_drift(manifests: list[tuple[str, dict]]) -> list[dict]:
    groups: dict[tuple, dict[frozenset, list[tuple[str, str, str]]]] = defaultdict(lambda: defaultdict(list))
    for name, payload in manifests:
        company = str(payload.get("company_id") or name)
        for fact in payload["facts"]:
            if not isinstance(fact, dict) or fact.get("metric") not in COMPOSITION_SENSITIVE:
                continue
            if fact.get("dimensions"):
                continue
            label = _label(fact)
            if not label:
                continue
            key = (company, fact["metric"], fact.get("period_kind"))
            groups[key][label_signature(label)].append((str(fact.get("period_end", ""))[:10], label, name))
    findings = []
    for (company, metric, kind), by_signature in sorted(groups.items(), key=str):
        if len(by_signature) < 2:
            continue
        findings.append({
            "check": "definition_drift",
            "company_id": company,
            "metric": metric,
            "period_kind": kind,
            "variants": [
                {"periods": sorted({p for p, _, _ in rows}), "label": rows[0][1],
                 "manifests": sorted({m for _, _, m in rows})}
                for _, rows in sorted(by_signature.items(), key=lambda kv: sorted(kv[1])[0])
            ],
        })
    return findings


def dimension_reconciliation(manifests: list[tuple[str, dict]]) -> list[dict]:
    # (company, period_end, period_kind) -> metric -> [(dimensions, scaled value, source label, scale)]
    periods: dict[tuple, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for name, payload in manifests:
        company = str(payload.get("company_id") or name)
        for fact in payload["facts"]:
            if not isinstance(fact, dict):
                continue
            value = _scaled(fact)
            if value is None:
                continue
            key = (company, str(fact.get("period_end", ""))[:10], fact.get("period_kind"))
            periods[key][fact.get("metric")].append((
                fact.get("dimensions") or {}, value, _label(fact),
                Decimal(str(fact.get("scale") or 1)), name,
            ))
    findings = []
    for (company, period_end, kind), metrics in sorted(periods.items(), key=str):
        for component_metric, dimension, total_metrics in DIMENSION_RECONCILIATIONS:
            components = [row for row in metrics.get(component_metric, ()) if set(row[0]) == {dimension}]
            if len(components) < 2:
                continue
            totals = []
            for total_metric in total_metrics:
                plain = [row for row in metrics.get(total_metric, ()) if not row[0]]
                if not plain:
                    totals = []
                    break
                totals.append(plain[0][1])
            if not totals:
                continue
            component_sum = sum((row[1] for row in components), Decimal(0))
            total = sum(totals, Decimal(0))
            # Components are individually rounded to the statement unit, so the
            # sum may differ from the printed total by half a unit per line.
            unit = max(row[3] for row in components)
            tolerance = unit * Decimal(len(components)) / Decimal(2)
            difference = component_sum - total
            if abs(difference) > tolerance:
                findings.append({
                    "check": "dimension_reconciliation",
                    "company_id": company,
                    "period_end": period_end,
                    "period_kind": kind,
                    "component_metric": component_metric,
                    "total_metrics": list(total_metrics),
                    "components_sum": str(component_sum),
                    "total": str(total),
                    "difference": str(difference),
                    "tolerance": str(tolerance),
                    "components": [
                        {"dimension": next(iter(row[0].values())), "value": str(row[1]), "label": row[2]}
                        for row in components
                    ],
                })
    return findings


def filing_date_before_exchange_upload(manifests: list[tuple[str, dict]]) -> list[dict]:
    findings = []
    for name, payload in manifests:
        if payload.get("filed_at_basis"):
            continue
        match = _EXCHANGE_UPLOAD.search(str(payload.get("source_url") or ""))
        filed = str(payload.get("filed_at") or "")[:10]
        if not match or not filed:
            continue
        try:
            uploaded = date.fromisoformat(match.group(1))
            filed_on = date.fromisoformat(filed)
        except ValueError:
            continue
        if filed_on < uploaded:
            findings.append({
                "check": "filing_date_before_exchange_upload",
                "manifest": name,
                "company_id": payload.get("company_id"),
                "filed_at": filed,
                "exchange_upload_date": uploaded.isoformat(),
                "days_early": (uploaded - filed_on).days,
            })
    return findings


def run_all(imports_dir: str | Path, prefix: str | None = None) -> dict:
    manifests = load_manifests(imports_dir, prefix)
    return {
        "manifests": len(manifests),
        "definition_drift": definition_drift(manifests),
        "dimension_reconciliation": dimension_reconciliation(manifests),
        "filing_date_before_exchange_upload": filing_date_before_exchange_upload(manifests),
    }


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    imports_dir = args[0] if args else "data/imports"
    prefix = args[1] if len(args) > 1 else None
    print(json.dumps(run_all(imports_dir, prefix), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
