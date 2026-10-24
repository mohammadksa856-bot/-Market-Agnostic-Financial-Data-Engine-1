"""Compare two factory-contract evidence bundles from independent pipelines.

A bundle is the contract a pipeline scored against (categories, weights, field definitions) and its
per-field evidence (closed or missing, with the observations behind a closed field). Comparing two
bundles reports which keys each contract expects, where definitions or weights differ, where the two
pipelines closed the same key with conflicting values, units, periods or sources, and the coverage
of their union counted once per (category, key) slot, so a key closed by both is never counted twice.
"""
from __future__ import annotations

import copy
import json
from contextlib import closing
import shutil
import sqlite3
import tempfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

BUNDLE_VERSION = 1
DEFINITION_ATTRIBUTES = ("definition", "unit", "period_behavior", "value_type")
RECORD_STATUSES = ("closed", "missing", "excluded")
PERIOD_KINDS = ("instant", "quarter", "ytd", "fy", "ttm", "as_of", "daily")


class InvalidBundle(ValueError):
    """A snapshot that does not have the bundle structure; `errors` names every problem found."""

    def __init__(self, label: str, errors: list[str]):
        super().__init__(f"invalid bundle {label!r}: " + "; ".join(errors))
        self.errors = errors


def normalize_bundle(bundle: dict) -> dict:
    """Copy with minimal-snapshot shorthands expanded: a field may be given as its key alone, and
    `record_default: "missing"` declares every contract key without a record as missing."""
    bundle = copy.deepcopy(bundle)
    for category in (bundle.get("contract") or {}).get("categories") or []:
        if isinstance(category, dict) and isinstance(category.get("fields"), list):
            category["fields"] = [{"key": field} if isinstance(field, str) else field
                                  for field in category["fields"]]
    if bundle.get("record_default") == "missing" and isinstance(bundle.get("records"), list):
        recorded = {record.get("key") for record in bundle["records"] if isinstance(record, dict)}
        for category in bundle["contract"]["categories"]:
            for field in category.get("fields") or []:
                if isinstance(field, dict) and field.get("key") not in recorded:
                    bundle["records"].append({"key": field["key"], "status": "missing", "observations": []})
                    recorded.add(field["key"])
    return bundle


def _is_number(value) -> bool:
    try:
        Decimal(str(value))
        return not isinstance(value, bool)
    except (InvalidOperation, ValueError):
        return False


def _is_date(value) -> bool:
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def validate_bundle(bundle) -> dict:
    """Structural check of a snapshot before any comparison. Returns errors and warnings."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(bundle, dict):
        return {"errors": ["snapshot is not a JSON object"], "warnings": []}
    if bundle.get("bundle_version") != BUNDLE_VERSION:
        errors.append(f"bundle_version must be {BUNDLE_VERSION}, got {bundle.get('bundle_version')!r}")
    if not isinstance(bundle.get("company_id"), str) or not bundle.get("company_id"):
        errors.append("company_id must be a non-empty string")
    contract = bundle.get("contract")
    categories = contract.get("categories") if isinstance(contract, dict) else None
    if not isinstance(categories, list) or not categories:
        errors.append("contract.categories must be a non-empty list")
        categories = []
    contract_keys: set[str] = set()
    seen_categories: set[str] = set()
    total_weight = Decimal(0)
    for index, category in enumerate(categories):
        where = f"contract.categories[{index}]"
        if not isinstance(category, dict):
            errors.append(f"{where} is not an object"); continue
        key = category.get("key")
        if not isinstance(key, str) or not key:
            errors.append(f"{where}.key must be a non-empty string")
        elif key in seen_categories:
            errors.append(f"category {key!r} appears twice")
        seen_categories.add(key)
        if not _is_number(category.get("weight")) or Decimal(str(category["weight"])) < 0:
            errors.append(f"{where}.weight must be a non-negative number")
        else:
            total_weight += Decimal(str(category["weight"]))
        if category.get("score_only") is not None:
            if not _is_number(category["score_only"]) or not 0 <= Decimal(str(category["score_only"])) <= 1:
                errors.append(f"{where}.score_only must be a number between 0 and 1")
            continue
        fields = category.get("fields")
        if not isinstance(fields, list) or (not fields and not category.get("not_applicable")):
            errors.append(f"{where}.fields must be a non-empty list"); continue
        seen_fields = set()
        for position, field in enumerate(fields):
            field_key = field.get("key") if isinstance(field, dict) else None
            if not isinstance(field_key, str) or not field_key:
                errors.append(f"{where}.fields[{position}] needs a non-empty key"); continue
            if field_key in seen_fields:
                errors.append(f"key {field_key!r} appears twice in category {key!r}")
            seen_fields.add(field_key)
            contract_keys.add(field_key)
    if categories and total_weight != Decimal(100):
        warnings.append(f"category weights sum to {total_weight}, not 100")
    records = bundle.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list"); records = []
    record_keys: set[str] = set()
    for index, record in enumerate(records):
        where = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{where} is not an object"); continue
        key = record.get("key")
        if not isinstance(key, str) or not key:
            errors.append(f"{where}.key must be a non-empty string"); continue
        if key in record_keys:
            errors.append(f"record {key!r} appears twice")
        record_keys.add(key)
        if record.get("status") not in RECORD_STATUSES:
            errors.append(f"record {key!r} status must be one of {', '.join(RECORD_STATUSES)}")
        observations = record.get("observations", [])
        if not isinstance(observations, list):
            errors.append(f"record {key!r} observations must be a list"); continue
        for position, item in enumerate(observations):
            at = f"record {key!r} observation {position}"
            if not isinstance(item, dict):
                errors.append(f"{at} is not an object"); continue
            if item.get("period_kind") not in PERIOD_KINDS:
                errors.append(f"{at} period_kind must be one of {', '.join(PERIOD_KINDS)}")
            if not _is_date(item.get("period_end")):
                errors.append(f"{at} period_end must be an ISO date")
            if item.get("period_start") not in (None, "") and not _is_date(item["period_start"]):
                errors.append(f"{at} period_start must be an ISO date or empty")
            if "value" not in item:
                errors.append(f"{at} has no value")
        if record.get("status") == "closed" and not observations:
            warnings.append(f"record {key!r} is closed without observations; values cannot be compared")
    unknown = sorted(record_keys - contract_keys)
    if unknown:
        errors.append(f"{len(unknown)} records are not contract keys: {', '.join(unknown[:10])}")
    unrecorded = sorted(contract_keys - record_keys)
    if unrecorded:
        errors.append(f"{len(unrecorded)} contract keys have no record (declare record_default: \"missing\" "
                      f"if absence means missing): {', '.join(unrecorded[:10])}")
    for index, correction in enumerate(bundle.get("engine_corrections") or []):
        if not isinstance(correction, dict) or not isinstance(correction.get("id"), str) \
                or not isinstance(correction.get("keys"), list):
            errors.append(f"engine_corrections[{index}] needs an id and a list of keys")
    return {"errors": errors, "warnings": warnings}


def checked_bundle(bundle: dict) -> dict:
    """Normalized bundle, or InvalidBundle naming every structural problem."""
    normalized = normalize_bundle(bundle) if isinstance(bundle, dict) else bundle
    result = validate_bundle(normalized)
    if result["errors"]:
        label = bundle.get("label") if isinstance(bundle, dict) else None
        raise InvalidBundle(str(label), result["errors"])
    return normalized


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


def _period_difference(key: str, left: dict, right: dict) -> dict | None:
    """Periods one pipeline holds and the other does not, within the range both exported."""
    def periods(record):
        return {(item.get("period_kind"), item.get("period_end"), item.get("dimensions", ""))
                for item in record.get("observations", [])}
    a, b = periods(left), periods(right)
    if left.get("observations_truncated") or right.get("observations_truncated"):
        low = max(min(end for _, end, _ in a), min(end for _, end, _ in b))
        high = min(max(end for _, end, _ in a), max(end for _, end, _ in b))
        a = {item for item in a if low <= item[1] <= high}
        b = {item for item in b if low <= item[1] <= high}
    if a == b:
        return None
    label = lambda items: sorted(f"{kind}:{end}" + (f":{dims}" if dims else "") for kind, end, dims in items)
    return {"key": key, "only_in_a": label(a - b), "only_in_b": label(b - a)}


def compare_bundles(a: dict, b: dict, *, tolerance: Decimal = Decimal("0.000001")) -> dict:
    a, b = checked_bundle(a), checked_bundle(b)
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
    definition_diffs, definition_not_provided = [], []
    for key in sorted(keys_a & keys_b):
        left = next(field for (_, k), field in slots_a.items() if k == key)
        right = next(field for (_, k), field in slots_b.items() if k == key)
        provided = [attr for attr in DEFINITION_ATTRIBUTES if attr in left and attr in right]
        if len(provided) < len(DEFINITION_ATTRIBUTES):
            definition_not_provided.append(key)
        changed = {attr: [left.get(attr), right.get(attr)] for attr in provided
                   if left.get(attr) != right.get(attr)}
        if changed:
            definition_diffs.append({"key": key, **changed})

    closed_a, closed_b = _closed(a), _closed(b)
    records_a, records_b = _records(a), _records(b)
    conflicts = []
    corrections: dict[str, list[str]] = {}
    for side, bundle in (("a", a), ("b", b)):
        for correction in bundle.get("engine_corrections") or []:
            for key in correction["keys"]:
                corrections.setdefault(key, []).append(f"{side}:{correction['id']}")
    period_differences, not_comparable = [], []
    for key in sorted(closed_a & closed_b):
        if not records_a[key].get("observations") or not records_b[key].get("observations"):
            not_comparable.append(key)  # closed on both sides, but one side exported no values
            continue
        found = _observation_conflicts(key, records_a[key], records_b[key], tolerance)
        difference = _period_difference(key, records_a[key], records_b[key])
        if difference:
            found.append(difference)
        for item in found:
            if key in corrections:
                # One pipeline's engine changed this key; the gap may be that correction, not a data dispute.
                item["engine_corrections"] = sorted(corrections[key])
        conflicts.extend(item for item in found if "type" in item)
        if difference:
            period_differences.append(difference)

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
        "definition_diffs": definition_diffs, "definition_not_provided": definition_not_provided,
        "conflicts": conflicts, "period_differences": period_differences, "not_comparable": not_comparable,
        "closure": {"on_contract_a": closure(slots_a), "on_contract_b": closure(slots_b)},
        "scores": {
            "a_on_a": str(contract_score(a, closed_a)), "b_on_b": str(contract_score(b, closed_b)),
            "union_on_a": str(contract_score(a, union)), "union_on_b": str(contract_score(b, union)),
        },
        "conflicted_keys": sorted({item["key"] for item in conflicts
                                   if item["type"] not in ("source_differs_same_value",)}),
        "conflicts_touched_by_engine_corrections": sorted({item["key"] for item in [*conflicts, *period_differences]
                                                          if item.get("engine_corrections")}),
    }


PROFILE_COLUMNS = {"company_name": "name", "symbol": "symbol", "isin": "isin", "cik": "cik", "exchange": "exchange",
                   "market": "market", "country": "country", "currency": "currency",
                   "fiscal_year_end": "fiscal_year_end", "sector": "sector", "industry": "industry",
                   "timezone": "timezone"}
PRICE_COLUMNS = {"price_open": "open", "price_high": "high", "price_low": "low", "price_close": "close",
                 "price_adjusted_close": "adjusted_close", "trading_volume": "volume", "trading_turnover": "turnover"}
from .ownership_metrics import DERIVED_KEYS as DERIVED_OWNERSHIP_KEYS, ownership_metrics

OWNERSHIP_FIELDS = {"holder_name": "holder_name", "holder_type": "holder_type", "shares_held": "shares",
                    "ownership_percentage": "ownership_pct"}


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _source_url(db, source_key):
    row = db.conn.execute("SELECT source_url FROM source_documents WHERE source_key=?", (source_key,)).fetchone()
    return row["source_url"] if row else None


def _domain_observations(db, company, key: str, domain: str, limit: int) -> list[dict]:
    """Observations for a closed key held outside data_points, so non-numeric evidence compares too."""
    company_id = company["company_id"]
    if domain == "company_profile":
        row = db.conn.execute("""SELECT * FROM company_attributes WHERE company_id=? AND attribute_key=?
            AND is_current=1 ORDER BY effective_at DESC LIMIT 1""", (company_id, key)).fetchone()
        if row is not None:
            return [{"period_kind": "as_of", "period_start": None, "period_end": str(row["effective_at"])[:10],
                     "dimensions": "", "value": row["value_json"], "unit": None, "currency": None,
                     "source_url": _source_url(db, row["source_key"]), "calculation": None}]
        if key in PROFILE_COLUMNS and company[PROFILE_COLUMNS[key]]:
            # Registry values carry no date of their own: stated as of the export.
            return [{"period_kind": "as_of", "period_start": None, "period_end": date.today().isoformat(),
                     "dimensions": "registry", "value": str(company[PROFILE_COLUMNS[key]]), "unit": None,
                     "currency": None, "source_url": None, "calculation": None}]
        return []
    if domain == "market_prices" and key in PRICE_COLUMNS | {"fifty_two_week_high": "", "fifty_two_week_low": ""}:
        interval = "1y" if key.startswith("fifty_two_week") else "1d"
        column = {"fifty_two_week_high": "high", "fifty_two_week_low": "low"}.get(key, PRICE_COLUMNS.get(key))
        row = db.conn.execute(f"""SELECT p.* FROM market_prices p JOIN listings l USING(listing_id)
            JOIN securities s USING(security_id) WHERE s.company_id=? AND p.is_current=1 AND p.interval=?
            AND p.{column} IS NOT NULL ORDER BY p.observed_at DESC LIMIT 1""", (company_id, interval)).fetchone()
        if row is None:
            return []
        return [{"period_kind": "as_of", "period_start": None, "period_end": str(row["observed_at"])[:10],
                 "dimensions": interval, "value": str(row[column]), "unit": None, "currency": row["currency"],
                 "source_url": _source_url(db, row["source_key"]), "calculation": None}]
    if domain == "corporate_actions":
        rows = db.conn.execute("""SELECT * FROM corporate_actions WHERE company_id=? AND action_type=? AND is_current=1
            ORDER BY COALESCE(effective_date,ex_date,announcement_date) DESC LIMIT ?""", (company_id, key, limit)).fetchall()
        return [{"period_kind": "as_of", "period_start": None,
                 "period_end": str(row["effective_date"] or row["ex_date"] or row["announcement_date"])[:10],
                 "dimensions": row["action_key"],
                 "value": _canonical({name: row[name] for name in ("announcement_date", "ex_date", "record_date",
                                      "payment_date", "effective_date", "cash_amount", "currency",
                                      "ratio_numerator", "ratio_denominator", "status")}),
                 "unit": None, "currency": row["currency"], "source_url": _source_url(db, row["source_key"]),
                 "calculation": None} for row in rows if row["effective_date"] or row["ex_date"] or row["announcement_date"]]
    if domain == "ownership_positions" and key in DERIVED_OWNERSHIP_KEYS:
        rows = db.conn.execute("SELECT * FROM ownership_positions WHERE company_id=? AND is_current=1",
                               (company_id,)).fetchall()
        source = {row["as_of_date"]: row["source_key"] for row in rows}
        return [{"period_kind": "as_of", "period_start": None, "period_end": item["as_of_date"],
                 "dimensions": item.get("holder_key"), "value": str(item["value"]), "unit": "ratio",
                 "currency": None, "source_url": _source_url(db, source[item["as_of_date"]]),
                 "calculation": item["basis"]}
                for item in ownership_metrics(rows).get(key, [])[:limit]]
    if domain == "ownership_positions" and key in OWNERSHIP_FIELDS:
        rows = db.conn.execute("""SELECT * FROM ownership_positions WHERE company_id=? AND is_current=1
            ORDER BY as_of_date DESC""", (company_id,)).fetchall()
        column = OWNERSHIP_FIELDS[key]
        return [{"period_kind": "as_of", "period_start": None, "period_end": str(row["as_of_date"])[:10],
                 "dimensions": row["holder_key"], "value": None if row[column] is None else str(row[column]),
                 "unit": "percent" if column == "ownership_pct" else None, "currency": None,
                 "source_url": _source_url(db, row["source_key"]), "calculation": None}
                for row in rows[:limit] if row["as_of_date"] and row[column] is not None]
    if domain == "disclosures":
        rows = db.conn.execute("""SELECT * FROM disclosures WHERE company_id=? AND disclosure_type=? AND is_current=1
            ORDER BY published_at DESC LIMIT ?""", (company_id, key, limit)).fetchall()
        return [{"period_kind": "as_of", "period_start": None,
                 "period_end": str(row["period_end"] or row["published_at"])[:10], "dimensions": row["content_hash"],
                 "value": row["title"], "unit": None, "currency": None,
                 "source_url": _source_url(db, row["source_key"]), "calculation": None}
                for row in rows if (row["period_end"] or row["published_at"])]
    return []


def export_bundle(db, company_id: str, *, label: str, engine_sha: str = "",
                  contract_path: str | Path = "config/factory/18-category-contract.json",
                  sector_pack_dir: str | Path = "config/factory/sector-packs",
                  observations_per_key: int = 12, engine_corrections: list[dict] | None = None) -> dict:
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
            if status == "closed" and not record["observations"] and row["storage_domain"] != "data_points":
                record["observations"] = _domain_observations(db, company, key, row["storage_domain"],
                                                              observations_per_key)
            current_point = db.conn.execute(
                "SELECT 1 FROM data_points WHERE company_id=? AND metric_key=? AND is_current=1 LIMIT 1",
                (company_id, key)).fetchone()
            if status == "closed" and not record["observations"] and current_point:
                record["observations"] = [{
                    "period_kind": item["period_kind"], "period_start": item["period_start"],
                    "period_end": item["period_end"], "dimensions": item["dimensions_hash"] or "",
                    "value": item["value_decimal"] if item["value_decimal"] is not None else item["value_text"],
                    "unit": item["unit"], "currency": item["currency"], "source_url": item["source_url"],
                    "calculation": item["calculation"],
                } for item in db.conn.execute(
                    """SELECT * FROM data_points WHERE company_id=? AND metric_key=? AND is_current=1
                    ORDER BY period_end DESC LIMIT ?""", (company_id, key, observations_per_key))]
                total = db.conn.execute("SELECT count(*) FROM data_points WHERE company_id=? AND metric_key=? AND is_current=1",
                                        (company_id, key)).fetchone()[0]
                record["observations_truncated"] = total > len(record["observations"])
    bundle = {"bundle_version": BUNDLE_VERSION, "label": label, "engine_sha": engine_sha, "company_id": company_id,
              "engine_total_score": result["total_score"],
              "contract": {"version": result.get("contract_version"), "categories": categories},
              "records": sorted(records.values(), key=lambda item: item["key"]),
              "engine_corrections": engine_corrections or []}
    checked_bundle(bundle)
    computed = contract_score(bundle, _closed(bundle))
    if abs(computed - Decimal(result["total_score"])) > Decimal("0.0001"):
        raise ValueError(f"bundle score {computed} does not reproduce the evaluator {result['total_score']}")
    return bundle


def load_bundle(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rows(path: Path, companies: set[str] | None) -> dict:
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as conn:
        query = """SELECT company_id,metric_key,period_end,period_kind,fiscal_quarter,dimensions_hash,
                   COALESCE(value_decimal,value_text,value_json) FROM data_points WHERE is_current=1"""
        return {row[:6]: row[6] for row in conn.execute(query)
                if companies is None or row[0] in companies}


def engine_impact(before: str | Path, after: str | Path, *, label: str, companies: list[str] | None = None,
                  contract_path: str | Path = "config/factory/18-category-contract.json",
                  sector_pack_dir: str | Path = "config/factory/sector-packs") -> dict:
    """What an engine change did to the same imports: rows removed, added or changed per metric, and
    each company's contract score before and after. Inputs are read from temporary copies only."""
    from .database import Database
    from .factory_contract import evaluate_factory_contract
    wanted = set(companies) if companies else None
    old, new = _rows(Path(before), wanted), _rows(Path(after), wanted)
    by_metric: dict[str, dict[str, int]] = {}
    for kind, keys in (("removed", set(old) - set(new)), ("added", set(new) - set(old)),
                       ("changed", {key for key in set(old) & set(new) if old[key] != new[key]})):
        for key in keys:
            by_metric.setdefault(key[1], {"removed": 0, "added": 0, "changed": 0})[kind] += 1
    scores = []
    with tempfile.TemporaryDirectory() as scratch:
        copies = []
        for name, path in (("before", before), ("after", after)):
            target = Path(scratch) / f"{name}.sqlite3"
            shutil.copyfile(path, target)
            copies.append(Database(str(target)))
        try:
            # Every company, not only those whose rows changed: an evaluator change moves scores without rows.
            everyone = {row[0] for db in copies for row in db.conn.execute("SELECT company_id FROM companies")}
            for company in sorted(wanted or everyone):
                results = [evaluate_factory_contract(db, company, contract_path=contract_path,
                                                     sector_pack_dir=sector_pack_dir) for db in copies]
                missing = [{(c["category_key"], key) for c in result["categories"]
                            for keys in (c["evidence"].get("missing_fields") or {}).values() for key in keys}
                           for result in results]
                scores.append({"company_id": company, "score_before": results[0]["total_score"],
                               "score_after": results[1]["total_score"],
                               "delta": str(Decimal(results[1]["total_score"]) - Decimal(results[0]["total_score"])),
                               "keys_closed": sorted(f"{c}:{k}" for c, k in missing[0] - missing[1]),
                               "keys_opened": sorted(f"{c}:{k}" for c, k in missing[1] - missing[0])})
        finally:
            for db in copies:
                db.close()
    return {"label": label, "companies": scores,
            "rows": {kind: sum(item[kind] for item in by_metric.values()) for kind in ("removed", "added", "changed")},
            "by_metric": dict(sorted(by_metric.items())),
            "engine_corrections": [{"id": label, "keys": sorted(by_metric)}]}
