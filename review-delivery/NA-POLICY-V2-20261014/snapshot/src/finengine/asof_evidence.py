"""Read-only point provenance at an explicit historical cutoff.

Source location and reproduced lineage are not independent accuracy verification.
Reviewed manifests are accepted only when bound to the exact immutable point snapshot.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
from .calculation_lineage import snapshot, verify

MANIFEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS point_source_evidence(
 point_id INTEGER NOT NULL, point_version INTEGER NOT NULL, snapshot_sha256 TEXT NOT NULL,
 source_hash TEXT NOT NULL, page INTEGER, table_ref TEXT, authority TEXT NOT NULL,
 known_at TEXT NOT NULL, independent_state TEXT NOT NULL DEFAULT 'not_verified');
"""

MARKET_MANIFEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_source_evidence(
 market_price_id INTEGER NOT NULL, market_price_version INTEGER NOT NULL,
 snapshot_sha256 TEXT NOT NULL, source_hash TEXT NOT NULL,
 table_ref TEXT NOT NULL, authority TEXT NOT NULL, known_at TEXT NOT NULL,
 independent_state TEXT NOT NULL DEFAULT 'not_verified');
"""

def _time(value):
    if not value:
        return None
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)
    except ValueError:
        return None

def _known(cutoff, *values):
    return all(_time(v) is not None and _time(v) <= cutoff for v in values)

def _cutoff(value):
    """Caller instants require timezone; date-only means the full UTC day."""
    if not value:
        return None
    text=str(value)
    if len(text)==10:
        return _time(text+'T23:59:59.999999+00:00')
    try:
        parsed=datetime.fromisoformat(text.replace('Z','+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (ValueError,TypeError):
        return None

def _source_sha_valid(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-fA-F]{64}',value) is not None

def _table(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

def point_snapshot_hash(row):
    return hashlib.sha256(json.dumps(snapshot(row), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def provenance_for_market_price(conn, price_id, as_of):
    """Require explicit source-native API/CSV locator on the exact price edition."""
    cutoff = _cutoff(as_of)
    if cutoff is None:
        raise ValueError("explicit valid as_of required")
    result = {"domain": "market_prices", "point_id": price_id, "as_of": cutoff.isoformat(),
              "lineage_complete": False, "source_complete": False,
              "independent_state": "not_verified", "reasons": [],
              "retirement_history_state": "not_recorded_not_inferred_from_current_flag"}
    row = conn.execute("SELECT * FROM market_prices WHERE id=?", (price_id,)).fetchone()
    if row is None or not _known(cutoff, row["observed_at"], row["published_at"]):
        result["reasons"].append("market_price_missing_or_future")
        return result
    result.update(version=row["version"], snapshot_sha256=point_snapshot_hash(row))
    issuer = conn.execute("SELECT s.company_id FROM listings l JOIN securities s USING(security_id) WHERE l.listing_id=?", (row["listing_id"],)).fetchone()
    source = conn.execute("SELECT * FROM source_documents WHERE source_key=?", (row["source_key"],)).fetchone()
    if issuer is None or source is None or source["company_id"] != issuer[0] or not source["source_url"] or not _source_sha_valid(source["content_hash"]) or not _known(cutoff, source["filed_at"], source["created_at"]):
        result["reasons"].append("market_source_missing_mismatched_or_future")
        return result
    if _table(conn, "market_source_evidence"):
        rows = conn.execute("SELECT * FROM market_source_evidence WHERE market_price_id=? AND market_price_version=? AND snapshot_sha256=? AND source_hash=?", (price_id,row["version"],point_snapshot_hash(row),source["content_hash"])).fetchall()
        accepted = [m for m in rows if m["table_ref"].strip() and m["authority"].strip() and _known(cutoff,m["known_at"])]
        if accepted:
            result["source_complete"] = result["lineage_complete"] = True
            result["independent_state"] = "verified" if any(m["independent_state"] == "verified" for m in accepted) else "not_verified"
    if not result["source_complete"]:
        result["reasons"].append("exact_market_source_locator_not_proven")
    return result

def provenance_for_point(conn, point_id, as_of, _visiting=None):
    cutoff = _cutoff(as_of)
    if cutoff is None:
        raise ValueError("explicit valid as_of required")
    result = {"point_id": point_id, "as_of": cutoff.isoformat(), "lineage_complete": False,
              "source_complete": False, "independent_state": "not_verified", "inputs": [], "reasons": [],
              "retirement_history_state": "not_recorded_not_inferred_from_current_flag"}
    visiting = set(_visiting or ())
    if point_id in visiting:
        result["reasons"].append("lineage_cycle")
        return result
    visiting.add(point_id)
    row = conn.execute("SELECT * FROM data_points WHERE id=?", (point_id,)).fetchone()
    if row is None or not _known(cutoff, row["filed_at"], row["published_at"]):
        result["reasons"].append("point_missing_or_not_known_as_of")
        return result
    result.update(version=row["version"], snapshot_sha256=point_snapshot_hash(row), is_calculated=bool(row["is_calculated"]))
    if row["is_calculated"]:
        if not _table(conn, "calculation_lineage") or not _table(conn, "calculation_input_edges") or not verify(conn, point_id, historical=True):
            result["reasons"].append("unreproduced_or_missing_lineage")
            return result
        edges = conn.execute("SELECT input_id,input_version FROM calculation_input_edges WHERE output_id=? ORDER BY ordinal", (point_id,)).fetchall()
        result["inputs"] = [provenance_for_point(conn, edge["input_id"], as_of, visiting) for edge in edges]
        if _table(conn,"calculation_market_input_edges"):
            market_edges = conn.execute("SELECT input_id,input_version FROM calculation_market_input_edges WHERE output_id=? ORDER BY ordinal",(point_id,)).fetchall()
            result["inputs"].extend(provenance_for_market_price(conn,edge["input_id"],as_of) for edge in market_edges)
            edges = list(edges) + list(market_edges)
        result["lineage_complete"] = bool(edges) and all(item["lineage_complete"] and item.get("version") == edge["input_version"] for item, edge in zip(result["inputs"], edges))
        result["source_complete"] = result["lineage_complete"] and all(item["source_complete"] for item in result["inputs"])
        # Input checks alone do not independently certify the calculated output.
        result["independent_state"] = "inputs_verified_output_not_verified" if result["inputs"] and all(item["independent_state"] == "verified" for item in result["inputs"]) else "not_verified"
        return result
    source = conn.execute("SELECT * FROM source_documents WHERE source_key=? AND company_id=?", (row["source_key"], row["company_id"])).fetchone()
    if source is None or not _source_sha_valid(source["content_hash"]) or source["source_url"] != row["source_url"] or source["filed_at"] != row["filed_at"] or not _known(cutoff, source["filed_at"], source["created_at"]):
        result["reasons"].append("source_missing_mismatched_or_future")
        return result
    if _table(conn, "point_source_evidence"):
        manifests = conn.execute("SELECT * FROM point_source_evidence WHERE point_id=? AND point_version=? AND snapshot_sha256=? AND source_hash=?", (point_id, row["version"], point_snapshot_hash(row), source["content_hash"])).fetchall()
        accepted = [m for m in manifests if m["authority"].strip() and ((m["page"] or 0) > 0 or (m["table_ref"] or "").strip()) and _known(cutoff, m["known_at"])]
        if accepted:
            result["source_complete"] = result["lineage_complete"] = True
            result["independent_state"] = "verified" if any(m["independent_state"] == "verified" for m in accepted) else "not_verified"
            return result
    if all(_table(conn, t) for t in ("extracted_facts", "mapped_facts", "normalized_facts")):
        staged = conn.execute("""SELECT e.page,e.table_ref,e.created_at AS extracted_at,m.created_at AS mapped_at,n.created_at AS normalized_at
         FROM extracted_facts e JOIN mapped_facts m ON m.extracted_fact_id=e.id
         JOIN normalized_facts n ON n.mapped_fact_id=m.id
         WHERE e.source_key=? AND e.company_id=? AND m.canonical_metric=? AND m.status='accepted'
         AND n.status IN ('validated','published') AND n.normalized_value=? AND n.currency=? AND n.unit=?
         AND coalesce(e.period_start,'')=? AND e.period_end=? AND e.period_kind=? AND e.fiscal_year=? AND coalesce(e.fiscal_quarter,0)=?
         AND e.scope=? AND e.dimensions_json=? AND coalesce(n.period_start,'')=? AND n.period_end=? AND n.period_kind=?
         AND n.fiscal_year=? AND coalesce(n.fiscal_quarter,0)=? AND n.scope=? AND n.dimensions_json=?""",
         (row["source_key"],row["company_id"],row["metric_key"],row["value_decimal"],row["currency"],row["unit"],row["period_start"],row["period_end"],row["period_kind"],row["fiscal_year"],row["fiscal_quarter"],row["scope"],row["dimensions_json"],row["period_start"],row["period_end"],row["period_kind"],row["fiscal_year"],row["fiscal_quarter"],row["scope"],row["dimensions_json"])).fetchall()
        result["source_complete"] = any(((s["page"] or 0) > 0 or (s["table_ref"] or "").strip()) and _known(cutoff,s["extracted_at"],s["mapped_at"],s["normalized_at"]) for s in staged)
    result["lineage_complete"] = result["source_complete"]
    if not result["source_complete"]:
        result["reasons"].append("exact_point_location_not_proven")
    return result

def points_known_as_of(conn, company_id, as_of):
    """Select historical versions without consulting mutable current flags."""
    cutoff = _cutoff(as_of)
    if cutoff is None:
        raise ValueError("explicit valid as_of required")
    selected = {}
    for row in conn.execute("SELECT * FROM data_points WHERE company_id=? ORDER BY id", (company_id,)):
        if not _known(cutoff, row["filed_at"], row["published_at"]):
            continue
        key = tuple(row[k] for k in ("metric_key","currency","unit","period_end","period_kind","fiscal_year","fiscal_quarter","scope","dimensions_json"))
        prior = selected.get(key)
        if prior is None or (row["version"], row["id"]) > (prior["version"], prior["id"]):
            selected[key] = row
    return [selected[k] for k in sorted(selected)]
