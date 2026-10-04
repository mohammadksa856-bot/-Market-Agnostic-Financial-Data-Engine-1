"""Arithmetic identity and cross-filing checks over the batch-B014 page transcriptions (offline, read-only).

Per document/column:
  * balance sheet: total_assets == total_liabilities + total_equity (when all three transcribed)
  * cash flow: cfo + cfi + cff == net_change; cash_begin + net_change (+ fx) == cash_end
  * income: gross_profit == revenue + cost_of_revenue (cost stored negative); or gross_profit_before_subsidy == revenue + operating_costs and gross_profit == gross_profit_before_subsidy + bunker_subsidy (shipping); net_income == ni_parent + ni_nci
  * the same identities on is_q (quarter-only columns)
Cross-filing (restatement detector, never silent):
  * a cumulative column ('prior') that repeats a period reported as 'cur' in another transcribed filing must agree on the keys in
    CROSS_KEYS. Every disagreement must be declared in the transcript's `restatements` list with BOTH values and the filings,
    and every declared restatement must match a real disagreement (so a declared value cannot be wrong or stale).
  * quarter-sum checks listed in `quarter_sums` ([{"key","parts":[[doc,col],...],"total":[doc,col]}]) must add up exactly.
Also validates that each transcript's sha256_prefix exists in the raw-coverage inventory.
Usage: python check_transcripts.py [symbol ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT.parent / "raw-coverage" / "companies"
TR = ROOT / "transcripts"
CROSS_KEYS = {
    "bs": ["total_assets", "total_liabilities", "total_equity", "cash", "insurance_contract_liabilities", "ppe", "total_current_assets", "loans", "deposits"],
    "is": ["insurance_revenue", "insurance_service_expenses", "insurance_service_result", "net_reinsurance_result", "pool_surplus", "pbt_before_attribution", "surplus_to_insurance_operations", "other_income_expenses", "total_insurance_service_result", "net_insurance_finance_result", "net_insurance_investment_result", "other_operating_expenses", "gross_written_premiums", "net_underwriting_result", "net_investment_income", "income_tax", "revenue", "cost_of_revenue", "operating_costs", "gross_profit_before_subsidy", "bunker_subsidy", "eps", "gross_profit", "operating_income", "pbt", "net_income", "ni_parent", "total_operating_expenses", "zakat_tax", "net_special_commission_income"],
    "cf": ["cfo", "cfi", "cff", "net_change", "cash_begin", "cash_end", "capex_ppe", "capex_projects", "capex_investment_property"],
}


def identities(doc):
    bad = []
    for col in ("cur", "prior", "prior2"):
        bs = doc.get("bs", {}).get(col)
        if bs and {"total_assets", "total_liabilities", "total_equity"} <= bs.keys():
            if bs["total_assets"] != bs["total_liabilities"] + bs["total_equity"]:
                bad.append((doc["label"], col, "bs", bs["total_assets"], bs["total_liabilities"] + bs["total_equity"]))
        cf = doc.get("cf", {}).get(col)
        if cf:
            if {"cfo", "cfi", "cff", "net_change"} <= cf.keys() and cf["cfo"] + cf["cfi"] + cf["cff"] != cf["net_change"]:
                bad.append((doc["label"], col, "cf-sum", cf["net_change"], cf["cfo"] + cf["cfi"] + cf["cff"]))
            if {"cash_begin", "net_change", "cash_end"} <= cf.keys():
                rolled = cf["cash_begin"] + cf["net_change"] + cf.get("fx", 0)
                if rolled != cf["cash_end"]:
                    bad.append((doc["label"], col, "cf-roll", cf["cash_end"], rolled))
        for key in ("is", "is_q"):
            i = doc.get(key, {}).get(col)
            if not i:
                continue
            if {"net_income", "ni_parent", "ni_nci"} <= i.keys() and i["net_income"] != i["ni_parent"] + i["ni_nci"]:
                bad.append((doc["label"], col, key, i["net_income"], i["ni_parent"] + i["ni_nci"]))
            if {"revenue", "cost_of_revenue", "gross_profit"} <= i.keys() and i["gross_profit"] != i["revenue"] + i["cost_of_revenue"] + i.get("inventory_loss", 0):
                bad.append((doc["label"], col, key + "-gp", i["gross_profit"], i["revenue"] + i["cost_of_revenue"] + i.get("inventory_loss", 0)))
            if {"revenue", "operating_costs", "gross_profit_before_subsidy"} <= i.keys() and i["gross_profit_before_subsidy"] != i["revenue"] + i["operating_costs"]:
                bad.append((doc["label"], col, key + "-gpb", i["gross_profit_before_subsidy"], i["revenue"] + i["operating_costs"]))
            if {"revenue", "total_operating_expenses", "pbt"} <= i.keys() and i["pbt"] != i["revenue"] + i["total_operating_expenses"]:
                bad.append((doc["label"], col, key + "-bank-pbt", i["pbt"], i["revenue"] + i["total_operating_expenses"]))
            if {"insurance_service_result", "pool_surplus", "total_insurance_service_result"} <= i.keys() and i["total_insurance_service_result"] != i["insurance_service_result"] + i["pool_surplus"]:
                bad.append((doc["label"], col, key + "-total-isr", i["total_insurance_service_result"], i["insurance_service_result"] + i["pool_surplus"]))
            if {"total_insurance_service_result", "net_investment_income", "net_insurance_finance_result", "net_insurance_investment_result"} <= i.keys() and i["net_insurance_investment_result"] != i["total_insurance_service_result"] + i["net_investment_income"] + i["net_insurance_finance_result"]:
                bad.append((doc["label"], col, key + "-net-ins-inv", i["net_insurance_investment_result"], i["total_insurance_service_result"] + i["net_investment_income"] + i["net_insurance_finance_result"]))
            if {"net_insurance_investment_result", "other_operating_expenses", "pbt"} <= i.keys() and i["pbt"] != i["net_insurance_investment_result"] + i["other_operating_expenses"]:
                bad.append((doc["label"], col, key + "-pbt-chain", i["pbt"], i["net_insurance_investment_result"] + i["other_operating_expenses"]))
            if {"pbt_before_attribution", "surplus_to_insurance_operations", "pbt"} <= i.keys() and i["pbt"] != i["pbt_before_attribution"] + i["surplus_to_insurance_operations"]:
                bad.append((doc["label"], col, key + "-attribution", i["pbt"], i["pbt_before_attribution"] + i["surplus_to_insurance_operations"]))
            if {"insurance_service_result", "net_investment_income", "net_insurance_finance_result", "other_income_expenses", "pbt_before_attribution"} <= i.keys() and "total_insurance_service_result" not in i and i["pbt_before_attribution"] != i["insurance_service_result"] + i["net_investment_income"] + i["net_insurance_finance_result"] + i["other_income_expenses"]:
                bad.append((doc["label"], col, key + "-pre-attribution-chain", i["pbt_before_attribution"], i["insurance_service_result"] + i["net_investment_income"] + i["net_insurance_finance_result"] + i["other_income_expenses"]))
            if {"pbt", "zakat_tax", "net_income"} <= i.keys() and i["net_income"] != i["pbt"] + i["zakat_tax"] + i.get("income_tax", 0):
                bad.append((doc["label"], col, key + "-ni-after-tax", i["net_income"], i["pbt"] + i["zakat_tax"] + i.get("income_tax", 0)))
            if {"insurance_revenue", "insurance_service_expenses", "insurance_service_result"} <= i.keys() and i["insurance_service_result"] != i["insurance_revenue"] + i["insurance_service_expenses"] + i.get("net_reinsurance_result", 0):
                bad.append((doc["label"], col, key + "-insurance-service-result", i["insurance_service_result"], i["insurance_revenue"] + i["insurance_service_expenses"] + i.get("net_reinsurance_result", 0)))
            if {"gross_profit_before_subsidy", "bunker_subsidy", "gross_profit"} <= i.keys() and i["gross_profit"] != i["gross_profit_before_subsidy"] + i["bunker_subsidy"]:
                bad.append((doc["label"], col, key + "-gp-sub", i["gross_profit"], i["gross_profit_before_subsidy"] + i["bunker_subsidy"]))
    return bad


def column_index(docs):
    """(stmt, period_end, period_type) -> [(label, column, columndict)]"""
    idx = {}
    for d in docs:
        for stmt in ("bs", "is", "cf"):
            for col in ("cur", "prior", "prior2"):
                c = d.get(stmt, {}).get(col)
                if not c:
                    continue
                if col == "cur":
                    pe, pt = d["period_end"], d["period_type"]
                elif col == "prior2":
                    pe, pt = d["bs_prior2_period_end"], "FY"
                elif stmt == "bs":
                    pe, pt = d["bs_prior_period_end"], "FY"
                else:
                    pe, pt = d["prior_period_end"], d["period_type"]
                idx.setdefault((stmt, pe, pt), []).append((d["label"], col, c))
    return idx


def cross(t):
    problems = []
    seen = []
    for (stmt, pe, pt), cols in column_index(t["docs"]).items():
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                (la, ca, a), (lb, cb, b) = cols[i], cols[j]
                for k in CROSS_KEYS[stmt]:
                    if k in a and k in b and a[k] != b[k]:
                        seen.append((stmt, pe, pt, k, la, ca, a[k], lb, cb, b[k]))
    declared = t.get("restatements", [])
    used = set()
    for s in seen:
        stmt, pe, pt, k, la, ca, va, lb, cb, vb = s
        hit = None
        for n, r in enumerate(declared):
            if (r["stmt"], r["period_end"], r["period_type"], r["key"]) == (stmt, pe, pt, k) and {r["original_doc"], r["represented_doc"]} == {la, lb}:
                vals = {r["original_doc"]: r["original"], r["represented_doc"]: r["represented"]}
                if vals[la] == va and vals[lb] == vb:
                    hit = n
        if hit is None:
            problems.append(("undeclared-difference", stmt, pe, pt, k, la, va, lb, vb))
        else:
            used.add(hit)
    for n, r in enumerate(declared):
        if n not in used:
            problems.append(("declared-restatement-not-found-or-values-wrong", r["stmt"], r["period_end"], r["period_type"], r["key"]))
    # quarter sums
    docs = {d["label"]: d for d in t["docs"]}
    for q in t.get("quarter_sums", []):
        def val(ref):
            doc, stmt, col, key = ref
            return docs[doc][stmt][col][key]
        total = sum(val(p) for p in q["parts"])
        if abs(total - val(q["total"])) > q.get("tol", 0) or (q.get("tol", 0) and not q.get("note")):
            problems.append(("quarter-sum", q.get("note", ""), total, val(q["total"])))
    return problems


def check(symbol):
    t = json.loads((TR / f"{symbol}.json").read_text(encoding="utf8"))
    inv = json.loads((INV / f"{symbol}.json").read_text(encoding="utf8"))
    shas = {f["sha256"] for f in inv["files"]}
    problems = []
    labels = [d["label"] for d in t["docs"]]
    if len(labels) != len(set(labels)):
        problems.append(("duplicate labels",))
    for d in t["docs"]:
        if not any(s.startswith(d["sha256_prefix"]) for s in shas):
            problems.append((d["label"], "sha not in inventory"))
        bad = identities(d)
        for decl in d.get("declared_footing", []):
            m = [b for b in bad if b[1] == decl["col"] and b[2] == decl["check"] and b[3] == decl["printed"] and b[4] == decl["computed"]]
            if not m:
                problems.append((d["label"], "declared footing difference not found", decl["check"]))
            bad = [b for b in bad if b not in m]
        problems += bad
    problems += cross(t)
    return t, problems


if __name__ == "__main__":
    syms = sys.argv[1:] or sorted(p.stem for p in TR.glob("*.json"))
    rc = 0
    for s in syms:
        t, p = check(s)
        print(s, "docs", len(t["docs"]), "restatements", len(t.get("restatements", [])), "problems", p)
        rc |= bool(p)
    sys.exit(rc)
