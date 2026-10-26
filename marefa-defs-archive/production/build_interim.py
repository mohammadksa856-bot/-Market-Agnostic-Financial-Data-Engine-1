"""Build the Aramco 2026 interim-statements manifest and check every value against its page text."""
import json, re, sys
src, out = sys.argv[1], sys.argv[2]
DOCS = {
    "q1": {"txt": f"{src}/q1-2026.txt", "filed_at": "2026-05-11",
           "url": "https://argaamplus.s3.amazonaws.com/45ab0adb-30ad-44ce-ae51-6f0609d2e43d.pdf",
           "sha256": "e3f8215a49ca2568df65c178ef0b681fdd6c43aa20558032424bc9e033c46191",
           "title": "Saudi Aramco First quarter interim report 2026"},
    "q2": {"txt": f"{src}/q2-2026.txt", "filed_at": "2026-08-04",
           "url": "https://argaamplus.s3.amazonaws.com/7643a85d-4d87-4ebc-b4d7-16982f1e2c39.pdf",
           "sha256": "4773cfe444de7e9734a65a59d8e1dd301229d9aa05164729e2b8f983d81cfb41",
           "title": "Saudi Aramco Second quarter and half year interim report 2026"},
}
P = {  # period id -> (start, end, kind, fy, fq)
    "Q4-25": ("2025-10-01", "2025-12-31", "quarter", 2025, 4),
    "Q1-25": ("2025-01-01", "2025-03-31", "quarter", 2025, 1),
    "Q2-25": ("2025-04-01", "2025-06-30", "quarter", 2025, 2),
    "H1-25": ("2025-01-01", "2025-06-30", "ytd", 2025, 2),
    "Q1-26": ("2026-01-01", "2026-03-31", "quarter", 2026, 1),
    "Q2-26": ("2026-04-01", "2026-06-30", "quarter", 2026, 2),
    "H1-26": ("2026-01-01", "2026-06-30", "ytd", 2026, 2),
}
IS, CF, EB, SUM = ("condensed consolidated statement of income", "condensed consolidated statement of cash flows",
                   "non-IFRS reconciliation: EBIT and adjusted EBIT", "summary of financial results")
# (doc, page, table, metric, {period: printed value}); sign follows the engine's existing Aramco rows
ROWS = [
    ("q1", 23, IS, "operating_income", {"Q1-26": 222536, "Q1-25": 191361}),
    ("q1", 23, IS, "eps_diluted", {"Q1-26": "0.50", "Q1-25": "0.40"}),
    ("q1", 23, IS, "depreciation_amortization", {"Q1-26": -24116, "Q1-25": -22823}),
    ("q1", 23, IS, "revenue", {"Q1-25": 405646}),
    ("q1", 23, IS, "net_income", {"Q1-25": 97543}),
    ("q1", 27, CF, "operating_cash_flow", {"Q1-25": 118908}),
    ("q1", 27, CF, "capex", {"Q1-25": 47059}),
    ("q1", 27, CF, "dividends_paid", {"Q1-26": 82080}),
    ("q1", 12, EB, "ebit", {"Q1-26": 223505, "Q4-25": 152543, "Q1-25": 189528}),
    ("q1", 3, SUM, "operating_income", {"Q4-25": 154849}),
    ("q1", 3, SUM, "net_income", {"Q4-25": 66630}),
    ("q2", 27, IS, "operating_income", {"Q2-26": 216151, "Q2-25": 167092, "H1-26": 438687, "H1-25": 358453}),
    ("q2", 27, IS, "eps_diluted", {"Q2-26": "0.50", "Q2-25": "0.35", "H1-26": "1.00", "H1-25": "0.75"}),
    ("q2", 27, IS, "depreciation_amortization", {"Q2-26": -23762, "Q2-25": -23054, "H1-26": -47878, "H1-25": -45877}),
    ("q2", 27, IS, "revenue", {"Q2-25": 378831, "H1-25": 784477}),
    ("q2", 27, IS, "net_income", {"Q2-25": 85022, "H1-25": 182565}),
    ("q2", 31, CF, "operating_cash_flow", {"Q2-25": 103284, "H1-25": 222192}),
    ("q2", 31, CF, "capex", {"Q2-25": 46158, "H1-25": 93217}),
    ("q2", 31, CF, "dividends_paid", {"Q2-26": 82073, "H1-26": 164153}),
    ("q2", 14, EB, "ebit", {"Q2-26": 218043, "Q2-25": 165484, "H1-26": 441548, "H1-25": 355012}),
]
def printed(v):
    if isinstance(v, str): return v
    s = f"{abs(v):,}"
    return f"({s})" if v < 0 else s
manifests = {}
errors = []
for doc, page, table, metric, values in ROWS:
    text = open(DOCS[doc]["txt"]).read().split("\f")[page - 1]
    for period, v in values.items():
        token = printed(v)
        # page text must carry the printed figure as a whole token
        if not re.search(r"(?<![\d,.])" + re.escape(token) + r"(?![\d,])", text):
            errors.append((doc, page, metric, period, token))
        start, end, kind, fy, fq = P[period]
        fact = {"metric": metric, "value": float(v) if isinstance(v, str) else v,
                "currency": "SAR", "unit": "SAR/share" if metric == "eps_diluted" else "SAR",
                "period_start": start, "period_end": end, "period_kind": kind,
                "fiscal_year": fy, "fiscal_quarter": fq, "page": page, "table": table}
        if metric != "eps_diluted":
            fact["scale"] = 1000000
        else:
            fact["value"] = v  # keep the printed decimal string's precision
        manifests.setdefault(doc, []).append(fact)
if errors:
    print("NOT FOUND ON PAGE:", errors); sys.exit(1)
for doc, facts in manifests.items():
    d = DOCS[doc]
    body = {"company_id": "sa:2222",
            "filing_type": f"{d['title']} — condensed interim statements and EBIT reconciliation (production batch, isolated)",
            "filed_at": d["filed_at"], "period_end": "2026-03-31" if doc == "q1" else "2026-06-30",
            "source_url": d["url"],
            "notes": f"Original filing PDF as mirrored by Argaam; sha256 {d['sha256']}. Values checked against the page text. "
                     "Rows already present in aramco-2026-q1/q2.json are not repeated.",
            "facts": facts}
    path = f"{out}/aramco-2026-{doc}-interim-statements.json"
    json.dump(body, open(path, "w"), indent=1, ensure_ascii=False)
    print(path, len(facts))
