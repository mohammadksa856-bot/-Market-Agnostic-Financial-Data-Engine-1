"""Deliverables of an intake run, measured from the unified records (never by adding percentages).
usage: python3 integration_summary.py WORKDIR"""
import json, sqlite3, sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_compare import checked_bundle, contract_score  # noqa: E402

work = Path(sys.argv[1])
load = lambda name: json.loads((work / name).read_text(encoding="utf-8")) if (work / name).exists() else None
after, before = checked_bundle(load("after-bundle.json")), checked_bundle(load("before-bundle.json"))
ours = checked_bundle(load("ours-bundle.json"))
closed = lambda b: {r["key"] for r in b["records"] if r["status"] == "closed"}
keys = {f["key"] for c in after["contract"]["categories"] for f in c.get("fields", [])}
weight = sum(Decimal(str(c["weight"])) for c in after["contract"]["categories"])
KNOWN_DEFECTS = {"short_term_investments_net": "sign defect recorded as ARAMCO95-CORR-STIN-2025, not applied"}
conservative = closed(after) - set(KNOWN_DEFECTS)
impact = load("8-engine-impact.json") or {}
company = next((c for c in impact.get("companies", []) if c["company_id"] == "sa:2222"), {})
escalations = load("9-escalations.json") or {}
tests = (work / "7-tests.log").read_text().splitlines()[-3:] if (work / "7-tests.log").exists() else []
db = sqlite3.connect(f"file:{work / 'after.sqlite3'}?mode=ro", uri=True)
identity = {"normalized_by_status": dict(db.execute("SELECT status,count(*) FROM normalized_facts GROUP BY 1").fetchall()),
            "exceptions_sa2222": [list(r) for r in db.execute("""SELECT stage,code,count(*) FROM exceptions
                                  WHERE company_id='sa:2222' GROUP BY 1,2 ORDER BY 3 DESC""").fetchall()]}
summary = {
    "integration_sha": (work / "INTEGRATION_SHA").read_text().strip() if (work / "INTEGRATION_SHA").exists() else None,
    "unified_coverage_total": {"distinct_keys": f"{len(closed(after) & keys)}/{len(keys)}",
                               "weighted": str(contract_score(after, closed(after)) / weight * 100)},
    "unified_coverage_conservative": {"excluded": KNOWN_DEFECTS, "distinct_keys": f"{len(conservative & keys)}/{len(keys)}",
                                      "weighted": str(contract_score(after, conservative) / weight * 100)},
    "before_pack": {"distinct_keys": f"{len(closed(before) & keys)}/{len(keys)}",
                    "weighted": str(contract_score(before, closed(before)) / weight * 100)},
    "engine_corrections_effect": {
        "measured_as": "before bundle (Codex code and evaluator) against after bundle (with the pack): code and data together",
        "keys_withdrawn": sorted(closed(before) - closed(after)),
        "keys_added": sorted(closed(after) - closed(before))},
    "keys_codex_data_adds_to_our_version": sorted(closed(after) - closed(ours)),
    "keys_ours_has_and_integration_lacks": sorted(closed(ours) - closed(after)),
    "row_level_impact": {
        "measured_as": "both databases scored by the integrated evaluator, so only row changes show here",
        "sa2222": {k: company.get(k) for k in ("score_before", "score_after", "keys_opened", "keys_closed")},
        "rows_all_companies": impact.get("rows")},
    "needs_review": (escalations.get("needs_review") or {}).get("count"),
    "coverage_differences": (escalations.get("coverage_differences") or {}).get("count"),
    "identity_checks": identity, "tests": tests,
    "financial_acceptance": "none: coverage is local measurement only",
}
print(json.dumps(summary, indent=1, ensure_ascii=False))
