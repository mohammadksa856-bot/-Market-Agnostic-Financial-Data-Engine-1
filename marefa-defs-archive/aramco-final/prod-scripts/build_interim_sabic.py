"""SABIC 2026 interim-statements manifests; every value is checked against its page text."""
import json, re, sys
src, out = sys.argv[1], sys.argv[2]
DOCS = {
    "q1": {"txt": f"{src}/sabic-q1-2026.txt", "filed_at": "2026-05-05", "period_end": "2026-03-31",
           "url": "https://argaamplus.s3.amazonaws.com/91ffd49e-e704-4f03-a1e4-e2862600626e.pdf",
           "sha256": "19eab943e3bba1c4d7917bacdbf0061a97b962cdf2a6f98a5fc6e906b96dd3d4",
           "title": "SABIC condensed consolidated interim financial statements, three months ended 31 March 2026"},
    "q2": {"txt": f"{src}/sabic-q2-2026.txt", "filed_at": "2026-07-29", "period_end": "2026-06-30",
           "url": "https://argaamplus.s3.amazonaws.com/87da1943-a165-485f-a07d-7a7cf4f3c66e.pdf",
           "sha256": "e906e107abf0ba984ba0265e22a6a44a501729d5fbcdf19e71785b460efe38b3",
           "title": "SABIC condensed consolidated interim financial statements, three and six months ended 30 June 2026"},
}
P = {"Q1-25": ("2025-01-01", "2025-03-31", "quarter", 2025, 1), "Q2-25": ("2025-04-01", "2025-06-30", "quarter", 2025, 2),
     "H1-25": ("2025-01-01", "2025-06-30", "ytd", 2025, 2), "Q1-26": ("2026-01-01", "2026-03-31", "quarter", 2026, 1),
     "Q2-26": ("2026-04-01", "2026-06-30", "quarter", 2026, 2), "H1-26": ("2026-01-01", "2026-06-30", "ytd", 2026, 2),
     "I-Q1-26": (None, "2026-03-31", "instant", 2026, 1), "I-Q2-26": (None, "2026-06-30", "instant", 2026, 2)}
IS, CF, BS = ("condensed consolidated interim statement of income", "condensed consolidated interim statement of cash flows",
              "condensed consolidated interim statement of financial position")
# metric definitions follow the engine's SABIC FY rows: net_income = net income (loss) in total,
# eps = from net income (loss) attributable to equity holders of the Parent; outflows negative as in sabic-2025-fy.json
ROWS = [
    ("q1", 5, IS, "revenue", {"Q1-26": 26151935, "Q1-25": 29266658}),
    ("q1", 5, IS, "gross_profit", {"Q1-26": 5128239, "Q1-25": 5043682}),
    ("q1", 5, IS, "operating_income", {"Q1-26": 1446331, "Q1-25": 299418}),
    ("q1", 5, IS, "net_income", {"Q1-26": 284091, "Q1-25": -1163659}),
    ("q1", 5, IS, "eps_diluted", {"Q1-26": "0.004", "Q1-25": "-0.40"}),
    ("q1", 8, CF, "operating_cash_flow", {"Q1-26": 870866, "Q1-25": 150778}),
    ("q1", 8, CF, "capex", {"Q1-26": -1145074, "Q1-25": -1500908}),
    ("q1", 9, CF, "dividends_paid", {"Q1-26": -4465014, "Q1-25": -5101975}),
    ("q1", 4, BS, "total_assets", {"I-Q1-26": 237906104}),
    ("q1", 4, BS, "total_liabilities", {"I-Q1-26": 88826392}),
    ("q1", 4, BS, "total_equity", {"I-Q1-26": 149079712}),
    ("q1", 4, BS, "cash", {"I-Q1-26": 24553896}),
    ("q1", 4, BS, "intangible_assets", {"I-Q1-26": 18250940}),
    ("q2", 5, IS, "revenue", {"Q2-26": 24806620, "Q2-25": 30227890, "H1-26": 50958555, "H1-25": 59494548}),
    ("q2", 5, IS, "gross_profit", {"Q2-26": 4353398, "Q2-25": 6224371, "H1-26": 9481637, "H1-25": 11268053}),
    ("q2", 5, IS, "operating_income", {"Q2-26": 713867, "Q2-25": 2665753, "H1-26": 2160198, "H1-25": 2965171}),
    ("q2", 5, IS, "net_income", {"Q2-26": -872390, "Q2-25": -3640901, "H1-26": -588299, "H1-25": -4804560}),
    ("q2", 5, IS, "eps_diluted", {"Q2-26": "-0.28", "Q2-25": "-1.36", "H1-26": "-0.27", "H1-25": "-1.76"}),
    ("q2", 8, CF, "operating_cash_flow", {"H1-26": 1053018, "H1-25": 3352070}),
    ("q2", 8, CF, "capex", {"H1-26": -2724250, "H1-25": -3835417}),
    ("q2", 9, CF, "dividends_paid", {"H1-26": -4496727, "H1-25": -5111170}),
    ("q2", 4, BS, "total_assets", {"I-Q2-26": 245232141}),
    ("q2", 4, BS, "total_liabilities", {"I-Q2-26": 96525001}),
    ("q2", 4, BS, "total_equity", {"I-Q2-26": 148707140}),
    ("q2", 4, BS, "cash", {"I-Q2-26": 31297824}),
    ("q2", 4, BS, "intangible_assets", {"I-Q2-26": 18205642}),
]
def printed(v):
    if isinstance(v, str):
        return f"({v[1:]})" if v.startswith("-") else v
    s = f"{abs(v):,}"
    return f"({s})" if v < 0 else s
facts, errors = {}, []
for doc, page, table, metric, values in ROWS:
    text = open(DOCS[doc]["txt"]).read().split("\f")[page - 1]
    for period, v in values.items():
        token = printed(v)
        if not re.search(r"(?<![\d,.])" + re.escape(token) + r"(?![\d,])", text):
            errors.append((doc, page, metric, period, token))
        start, end, kind, fy, fq = P[period]
        fact = {"metric": metric, "value": v, "currency": "SAR", "unit": "SAR/share" if metric == "eps_diluted" else "SAR",
                "period_end": end, "period_kind": kind, "fiscal_year": fy, "fiscal_quarter": fq, "page": page, "table": table}
        if start: fact["period_start"] = start
        if metric != "eps_diluted": fact["scale"] = 1000
        facts.setdefault(doc, []).append(fact)
if errors:
    print("NOT FOUND ON PAGE:", errors); sys.exit(1)
for doc, rows in facts.items():
    d = DOCS[doc]
    json.dump({"company_id": "sa:2010", "filing_type": f"{d['title']} (production batch, isolated)",
               "filed_at": d["filed_at"], "period_end": d["period_end"], "source_url": d["url"],
               "notes": f"Original filing PDF as mirrored by Argaam; sha256 {d['sha256']}. Values checked against the page text. "
                        "filed_at is the PDF creation date (publication day not stated in the document).",
               "facts": rows}, open(f"{out}/sabic-2026-{doc}-interim-statements.json", "w"), indent=1)
    print(doc, len(rows))
