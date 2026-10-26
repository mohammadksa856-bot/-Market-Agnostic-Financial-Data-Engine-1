"""Independent QA over an isolated engine DB (read-only). Prints counts and keys only, never values."""
import sqlite3, sys, json
from collections import Counter
from datetime import date, timedelta

db = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True); db.row_factory = sqlite3.Row
company = sys.argv[2] if len(sys.argv) > 2 else None
where = "is_current=1" + (" AND company_id=?" if company else "")
args = (company,) if company else ()
rows = db.execute(f"SELECT * FROM data_points WHERE {where}", args).fetchall()
catalog = {r["field_key"]: r for r in db.execute("SELECT * FROM data_catalog_fields")}
out = {}

def months(r):
    s, e = date.fromisoformat(r["period_start"]), date.fromisoformat(r["period_end"])
    return (e.year - s.year) * 12 + e.month - s.month + (1 if (e + timedelta(days=1)).day == 1 and s.day == 1 else 0)

# 1. duplicate current identities
ident = Counter((r["company_id"], r["metric_key"], r["period_end"], r["period_kind"], r["fiscal_quarter"] or 0,
                 r["currency"], r["unit"], r["scope"], r["dimensions_hash"]) for r in rows)
out["duplicate_current_identities"] = sum(1 for v in ident.values() if v > 1)
# 2. period separation
spans = {"fy": 12, "quarter": 3, "ttm": 12}
bad = [(r["company_id"], r["metric_key"], r["period_kind"], months(r)) for r in rows
       if r["period_kind"] in spans and r["period_start"] and months(r) != spans[r["period_kind"]]]
out["period_span_violations"] = {"count": len(bad), "by_kind": dict(Counter(b[2] for b in bad)),
                                 "sample": sorted({(b[0], b[1], b[2], b[3]) for b in bad})[:8]}
out["fy_or_quarter_without_start"] = sum(1 for r in rows if r["period_kind"] in ("fy", "quarter", "ttm") and not r["period_start"])
q4_fy = 0
fy = {(r["company_id"], r["metric_key"], r["period_end"], r["dimensions_hash"]): r["value_decimal"] for r in rows if r["period_kind"] == "fy"}
for r in rows:
    if r["period_kind"] == "quarter" and r["fiscal_quarter"] == 4 and \
       fy.get((r["company_id"], r["metric_key"], r["period_end"], r["dimensions_hash"])) == r["value_decimal"] and r["value_decimal"] not in ("0", None):
        q4_fy += 1
out["q4_equal_to_fy_value"] = q4_fy
# 3. flows vs balances
flow_as_instant = sorted({r["metric_key"] for r in rows if catalog.get(r["metric_key"]) is not None and
                          catalog[r["metric_key"]]["period_behavior"] == "flow" and r["period_kind"] == "instant"})
stock_as_flow = sorted({r["metric_key"] for r in rows if catalog.get(r["metric_key"]) is not None and
                        catalog[r["metric_key"]]["period_behavior"] in ("stock", "instant", "balance") and r["period_kind"] in ("fy", "quarter", "ttm")})
out["flow_metrics_stored_as_instant"] = flow_as_instant
out["balance_metrics_stored_as_period"] = stock_as_flow
out["catalog_period_behaviors"] = dict(Counter(r["period_behavior"] for r in catalog.values()))
# 4. production vs sales
vol_units = {"mmbpd", "mbpd", "mmboed", "mmscfd", "bscfd", "mtpa", "tonnes", "kbd", "mbd", "bcf", "mmbbl", "bbl"}
sales_keys = [r["metric_key"] for r in rows if ("sales" in r["metric_key"] or "revenue" in r["metric_key"]) and (r["unit"] or "").lower() in vol_units]
prod_money = [r["metric_key"] for r in rows if "production" in r["metric_key"] and (r["unit"] or "") == (r["currency"] or "-")]
out["sales_or_revenue_keys_in_volume_units"] = sorted(set(sales_keys))
out["production_keys_in_currency"] = sorted(set(prod_money))
# 5. DEFINITION_PENDING leaks
sys.path.insert(0, sys.argv[3]) if len(sys.argv) > 3 else None
from finengine.calculations import Calculator
pending = set(Calculator.DEFINITION_PENDING)
out["definition_pending_keys"] = sorted(pending)
out["definition_pending_rows_current"] = sorted({(r["company_id"], r["metric_key"]) for r in rows if r["metric_key"] in pending})
out["definition_pending_rows_any_version"] = db.execute(
    f"SELECT count(*) FROM data_points WHERE metric_key IN ({','.join('?' * len(pending))})" + (" AND company_id=?" if company else ""),
    (*sorted(pending), *args)).fetchone()[0]
# 6. currency/unit mix within a metric series (consolidated, no dims)
mix = Counter()
series = {}
for r in rows:
    if r["dimensions_json"] in ("{}", "") and r["period_kind"] in ("fy", "quarter", "instant"):
        series.setdefault((r["company_id"], r["metric_key"]), set()).add((r["currency"], r["unit"]))
out["series_with_mixed_currency_or_unit"] = sorted(k for k, v in series.items() if len(v) > 1)[:15]
print(json.dumps(out, indent=1, default=str))
