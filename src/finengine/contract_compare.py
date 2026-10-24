"""Compare two factory-contract evidence bundles from independent pipelines.

A bundle is the contract a pipeline scored against (categories, weights, field definitions) and its
per-field evidence (closed or missing, with the observations behind a closed field). Comparing two
bundles reports which keys each contract expects, where definitions or weights differ, where the two
pipelines closed the same key with conflicting values, units, periods or sources, and the coverage
of their union counted once per (category, key) slot, so a key closed by both is never counted twice.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

BUNDLE_VERSION = 1
DEFINITION_ATTRIBUTES = ("definition", "unit", "period_behavior", "value_type")


def _decimal(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _slots(bundle: dict) -> dict[tuple[str, str], dict]:
    return {(category["key"], field["key"]): field
            for category in bundle["contract"]["categories"]
            for field in category.get("fields", [])}


def _records(bundle: dict) -> dict[str, dict]:
    return {record["key"]: record for record in bundle.get("records", [])}


def _closed(bundle: dict) -> set[str]:
    return {key for key, record in _records(bundle).items() if record.get("status") == "closed"}


def _excluded(bundle: dict) -> set[str]:
    return {key for key, record in _records(bundle).items() if record.get("status") == "excluded"}


def contract_score(bundle: dict, closed: set[str]) -> Decimal:
    """Weighted score of `closed` keys against this bundle's contract (engine formula)."""
    excluded = _excluded(bundle)
    total = Decimal(0)
    for category in bundle["contract"]["categories"]:
        weight = Decimal(str(category["weight"]))
        if category.get("score_only") is not None:
            total += weight * Decimal(str(category["score_only"]))
            continue
        fields = [field["key"] for field in category.get("fields", []) if field["key"] not in excluded]
        if category.get("not_applicable") or not fields:
            total += weight
            continue
        total += weight * Decimal(len([key for key in fields if key in closed])) / Decimal(len(fields))
    return total


def _observation_conflicts(key: str, left: dict, right: dict, tolerance: Decimal) -> list[dict]:
    def index(record):
        return {(item.get("period_kind"), item.get("period_end"), item.get("dimensions", "")): item
                for item in record.get("observations", [])}
    a, b = index(left), index(right)
    shared = sorted(set(a) & set(b), key=lambda item: tuple(str(part) for part in item))
    if (a or b) and not shared:
        return [{"key": key, "type": "period_mismatch", "a_periods": sorted(f"{k[0]}:{k[1]}" for k in a),
                 "b_periods": sorted(f"{k[0]}:{k[1]}" for k in b)}]
    conflicts = []
    for period in shared:
        x, y = a[period], b[period]
        where = {"key": key, "period_kind": period[0], "period_end": period[1]}
        if (x.get("unit"), x.get("currency")) != (y.get("unit"), y.get("currency")):
            conflicts.append({**where, "type": "unit_or_currency",
                              "a": [x.get("unit"), x.get("currency")], "b": [y.get("unit"), y.get("currency")]})
            continue
        vx, vy = _decimal(x.get("value")), _decimal(y.get("value"))
        if vx is None or vy is None:
            if x.get("value") != y.get("value"):
                conflicts.append({**where, "type": "value", "a": x.get("value"), "b": y.get("value")})
            continue
        scale = max(abs(vx), abs(vy))
        if scale and abs(vx - vy) > tolerance * scale:
            conflicts.append({**where, "type": "value", "a": str(vx), "b": str(vy)})
        elif x.get("source_url") and y.get("source_url") and x["source_url"] != y["source_url"]:
            conflicts.append({**where, "type": "source_differs_same_value",
                              "a": x["source_url"], "b": y["source_url"]})
        if x.get("period_start") != y.get("period_start"):
            conflicts.append({**where, "type": "period_start",
                              "a": x.get("period_start"), "b": y.get("period_start")})
    return conflicts


def compare_bundles(a: dict, b: dict, *, tolerance: Decimal = Decimal("0.000001")) -> dict:
    for bundle in (a, b):
        if bundle.get("bundle_version") != BUNDLE_VERSION:
            raise ValueError(f"unsupported bundle version in {bundle.get('label')!r}")
    if a.get("company_id") != b.get("company_id"):
        raise ValueError("bundles describe different companies")
    slots_a, slots_b = _slots(a), _slots(b)
    keys_a, keys_b = {key for _, key in slots_a}, {key for _, key in slots_b}
    categories_a = {c["key"]: c for c in a["contract"]["categories"]}
    categories_b = {c["key"]: c for c in b["contract"]["categories"]}

    weight_diffs = [{"category": key, "a": str(categories_a[key]["weight"]), "b": str(categories_b[key]["weight"])}
                    for key in sorted(set(categories_a) & set(categories_b))
                    if Decimal(str(categories_a[key]["weight"])) != Decimal(str(categories_b[key]["weight"]))]
    placement = []
    for key in sorted(keys_a & keys_b):
        in_a = sorted(category for category, field in slots_a if field == key)
        in_b = sorted(category for category, field in slots_b if field == key)
        if in_a != in_b:
            placement.append({"key": key, "a_categories": in_a, "b_categories": in_b})
    definition_diffs = []
    for key in sorted(keys_a & keys_b):
        left = next(field for (_, k), field in slots_a.items() if k == key)
        right = next(field for (_, k), field in slots_b.items() if k == key)
        changed = {attr: [left.get(attr), right.get(attr)] for attr in DEFINITION_ATTRIBUTES
                   if left.get(attr) != right.get(attr)}
        if changed:
            definition_diffs.append({"key": key, **changed})

    closed_a, closed_b = _closed(a), _closed(b)
    records_a, records_b = _records(a), _records(b)
    conflicts = []
    for key in sorted(closed_a & closed_b):
        conflicts.extend(_observation_conflicts(key, records_a[key], records_b[key], tolerance))

    def closure(slots):
        expected = {key for _, key in slots}
        return {
            "slots": len(slots), "keys": len(expected),
            "closed_both": len(expected & closed_a & closed_b),
            "closed_only_a": len((expected & closed_a) - closed_b),
            "closed_only_b": len((expected & closed_b) - closed_a),
            "closed_union": len(expected & (closed_a | closed_b)),
            "slots_closed_union": sum(1 for _, key in slots if key in closed_a | closed_b),
        }

    union = closed_a | closed_b
    return {
        "a": a.get("label"), "b": b.get("label"), "company_id": a.get("company_id"),
        "keys": {"common": sorted(keys_a & keys_b), "only_in_a": sorted(keys_a - keys_b),
                 "only_in_b": sorted(keys_b - keys_a)},
        "weight_diffs": weight_diffs, "category_placement_diffs": placement,
        "definition_diffs": definition_diffs, "conflicts": conflicts,
        "closure": {"on_contract_a": closure(slots_a), "on_contract_b": closure(slots_b)},
        "scores": {
            "a_on_a": str(contract_score(a, closed_a)), "b_on_b": str(contract_score(b, closed_b)),
            "union_on_a": str(contract_score(a, union)), "union_on_b": str(contract_score(b, union)),
        },
        "conflicted_keys": sorted({item["key"] for item in conflicts
                                   if item["type"] not in ("source_differs_same_value",)}),
    }


def export_bundle(db, company_id: str, *, label: str, engine_sha: str = "",
                  contract_path: str | Path = "config/factory/18-category-contract.json",
                  sector_pack_dir: str | Path = "config/factory/sector-packs",
                  observations_per_key: int = 12) -> dict:
    """Bundle this engine's contract and evidence for one company (read-only apart from the evaluator's refresh)."""
    from .factory_contract import evaluate_factory_contract
    result = evaluate_factory_contract(db, company_id, contract_path=contract_path, sector_pack_dir=sector_pack_dir)
    company = db.conn.execute("SELECT * FROM companies WHERE company_id=?", (company_id,)).fetchone()
    catalog = db.conn.execute(
        """SELECT * FROM data_catalog_fields WHERE enabled=1 AND review_state='reviewed' AND
        (scope_type='all' OR (scope_type='market' AND scope_value=?) OR
         (scope_type='sector' AND scope_value=?) OR (scope_type='industry' AND scope_value=?) OR
         (scope_type='company' AND scope_value=?))""",
        (company["market"], company["sector"] or "", company["industry"] or "", company_id)).fetchall()
    by_group: dict[str, list] = {}
    for row in catalog:
        by_group.setdefault(row["category"], []).append(row)
    categories, records = [], {}
    for category in result["categories"]:
        evidence = category["evidence"]
        entry = {"key": category["category_key"], "weight": str(category["weight"])}
        if category["status"] == "not_applicable":
            entry["not_applicable"] = True
        groups = evidence.get("field_groups") or []
        if category["category_key"] == "sources_lineage_freshness":
            entry["score_only"] = str(category["score"])
        rows = [row for group in groups for row in by_group.get(group, [])]
        excluded = {item["field_key"] for item in evidence.get("reviewed_unavailable_or_not_applicable", [])}
        missing = {key for keys in (evidence.get("missing_fields") or {}).values() for key in keys}
        if "score_only" not in entry and not entry.get("not_applicable"):
            if len(rows) != int(evidence.get("raw_expected_fields", len(rows))):
                raise ValueError(f"{category['category_key']}: exported fields do not match the evaluator")
        entry["fields"] = [{"key": row["field_key"], "definition": row["display_name"], "unit": row["default_unit"],
                            "period_behavior": row["period_behavior"], "value_type": row["value_type"],
                            "storage_domain": row["storage_domain"]} for row in rows]
        categories.append(entry)
        for row in rows:
            key = row["field_key"]
            status = "excluded" if key in excluded else ("missing" if key in missing else "closed")
            record = records.setdefault(key, {"key": key, "status": status, "storage_domain": row["storage_domain"],
                                              "observations": []})
            if status == "closed" and row["storage_domain"] == "data_points" and not record["observations"]:
                record["observations"] = [{
                    "period_kind": item["period_kind"], "period_start": item["period_start"],
                    "period_end": item["period_end"], "dimensions": item["dimensions_hash"] or "",
                    "value": item["value_decimal"] if item["value_decimal"] is not None else item["value_text"],
                    "unit": item["unit"], "currency": item["currency"], "source_url": item["source_url"],
                    "calculation": item["calculation"],
                } for item in db.conn.execute(
                    """SELECT * FROM data_points WHERE company_id=? AND metric_key=? AND is_current=1
                    ORDER BY period_end DESC LIMIT ?""", (company_id, key, observations_per_key))]
    bundle = {"bundle_version": BUNDLE_VERSION, "label": label, "engine_sha": engine_sha, "company_id": company_id,
              "engine_total_score": result["total_score"],
              "contract": {"version": result.get("contract_version"), "categories": categories},
              "records": sorted(records.values(), key=lambda item: item["key"])}
    computed = contract_score(bundle, _closed(bundle))
    if abs(computed - Decimal(result["total_score"])) > Decimal("0.0001"):
        raise ValueError(f"bundle score {computed} does not reproduce the evaluator {result['total_score']}")
    return bundle


def load_bundle(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
