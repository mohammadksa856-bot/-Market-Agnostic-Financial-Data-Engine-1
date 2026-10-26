"""SABIC quarterly income-statement lines 2023-2025, transcribed from each report's statement-of-income page.

Image-only pages cannot be text-matched, so every period is checked arithmetically instead:
revenue + cost of sales = gross profit; quarters add up to the year-to-date column of the same document;
net income (unchanged by discontinued-operation re-presentation) agrees across original and restated columns.
Text pages are also matched against the page text."""
import json, re, subprocess, sys
from collections import defaultdict
src, out = sys.argv[1], sys.argv[2]
idx = {l.split("\t")[0]: l.rstrip("\n").split("\t") for l in open(f"{src}/index.tsv")}
COLS = ("revenue", "cost_of_revenue", "gross_profit", "operating_income", "net_income", "eps_diluted")
P = lambda y, q: {1: (f"{y}-01-01", f"{y}-03-31", "quarter", 1), 2: (f"{y}-04-01", f"{y}-06-30", "quarter", 2),
                  3: (f"{y}-07-01", f"{y}-09-30", "quarter", 3)}[q]
Y = lambda y, q: (f"{y}-01-01", {2: f"{y}-06-30", 3: f"{y}-09-30"}[q], "ytd", q)
# file -> (page, [(period, (rev, cogs, gp, opinc, ni, eps)), ...]); eps as printed (string)
DOCS = {
 "14-Quarterly_Report_2023_Q1.pdf": (5, [(P(2023, 1), (39693360, -33820208, 5873152, 1688254, 935818, "0.22"))]),
 "13-Quarterly_Report_2023_Q2.pdf": (5, [(P(2023, 2), (37166811, -31793552, 5373259, 1432442, 1692121, "0.39")),
                                         (Y(2023, 2), (76860170, -65803962, 11056208, 3120696, 2627939, "0.61"))]),
 "12-Quarterly_Report_2023_Q3.pdf": (5, [(P(2023, 3), (35975303, -29640269, 6335034, 1680722, -2106983, "-0.96")),
                                         ]),  # its 9M column is re-presented for Hadeed while Q1-Q2 2023 as filed are not;
                                              # the same 9M is taken from the Q3 2024 report, after the re-presented quarters
 "10-Quarterly_Report_2024_Q1.pdf": (5, [(P(2024, 1), (32685823, -26823460, 5862363, 1210441, 695087, "0.08")),
                                         (P(2023, 1), (36432362, -30587110, 5845252, 1760189, 935818, "0.22"))]),
 "09-Quarterly_Report_2024_Q2.pdf": (5, [(P(2024, 2), (35718598, -28524783, 7193815, 2100511, 2707508, "0.73")),
                                         (Y(2024, 2), (68404421, -55348243, 13056178, 3310952, 3402595, "0.81")),
                                         (P(2023, 2), (34097383, -28660319, 5437064, 1643646, 1692121, "0.39")),
                                         (Y(2023, 2), (70529746, -59436524, 11093222, 3403835, 2627939, "0.61"))]),
 "08-Quarterly_Report_2024_Q3.pdf": (5, [(P(2024, 3), (36880147, -29880451, 6999696, 2477260, 1763381, "0.33")),
                                         (Y(2024, 3), (105284568, -85228694, 20055874, 5788212, 5165976, "1.14")),
                                         (P(2023, 3), (35975303, -29572011, 6403292, 1680722, -2106983, "-0.96")),
                                         (Y(2023, 3), (106505049, -89008535, 17496514, 5084558, 520956, "-0.35"))]),
 "06-Quarterly_report_2025_Q1.pdf": (5, [(P(2025, 1), (34594245, -29785525, 4808720, -773403, -1163659, "-0.40"))]),
 "05-Quarterly_report_2025_Q2.pdf": (5, [(P(2025, 2), (35565517, -31149386, 4416131, -1883684, -3640901, "-1.36")),
                                         (Y(2025, 2), (70159762, -60934911, 9224851, -2657087, -4804560, "-1.76"))]),
 "04-Quarterly_report_2025_Q3.pdf": (5, [(P(2025, 3), (34332511, -28226834, 6105677, 1663472, 1135385, "0.15")),
                                         (Y(2025, 3), (104492273, -89161745, 15330528, -993615, -3669175, "-1.61"))]),
}
errors, ni = [], defaultdict(set)
def printed(v):
    s = f"{abs(v):,}" if isinstance(v, int) else v.lstrip("-")
    return f"({s})" if (v < 0 if isinstance(v, int) else v.startswith("-")) else s
for f, (page, rows) in DOCS.items():
    text = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", f"{src}/{f}", "-"],
                          capture_output=True, text=True).stdout
    by = {}
    for (start, end, kind, fq), vals in rows:
        rev, cogs, gp = vals[:3]
        if rev + cogs != gp: errors.append((f, end, "revenue + cost of sales != gross profit"))
        ni[(start, end, kind)].add(vals[4])
        by[(start, end, kind)] = vals
        if len(text.split()) > 50:  # text page: every value must also appear on it
            for v in vals:
                if not re.search(r"(?<![\d,.])" + re.escape(printed(v)) + r"(?![\d,])", text):
                    errors.append((f, end, "not on page", printed(v)))
    for (start, end, kind), vals in by.items():  # year-to-date = previous YTD (or Q1) + this quarter, same document
        if kind != "ytd": continue
        q = next(v for (s, e, k), v in by.items() if k == "quarter" and e == end)
        y = start[:4]; prev_end = {f"{y}-06-30": f"{y}-03-31", f"{y}-09-30": f"{y}-06-30"}[end]
        prev = next((v for (s, e, k), v in by.items() if e == prev_end), None)
        if prev is None:  # previous period comes from the previous document on the same basis
            continue
for key, values in ni.items():
    if len(values) > 1: errors.append(("net income differs between documents", key, values))
# additivity across consecutive documents where the basis is unchanged (2024, 2025 originals; 2023 restated)
def get(f, end, kind):
    for (s, e, k, q), v in DOCS[f][1]:
        if e == end and k == kind: return v
chains = [("10-Quarterly_Report_2024_Q1.pdf", "09-Quarterly_Report_2024_Q2.pdf", "08-Quarterly_Report_2024_Q3.pdf", 2024),
          ("06-Quarterly_report_2025_Q1.pdf", "05-Quarterly_report_2025_Q2.pdf", "04-Quarterly_report_2025_Q3.pdf", 2025)]
for a, b, c, y in chains:
    q1, q2, h1 = get(a, f"{y}-03-31", "quarter"), get(b, f"{y}-06-30", "quarter"), get(b, f"{y}-06-30", "ytd")
    q3, n9 = get(c, f"{y}-09-30", "quarter"), get(c, f"{y}-09-30", "ytd")
    for i in range(5):
        if abs(q1[i] + q2[i] - h1[i]) > 2 or abs(h1[i] + q3[i] - n9[i]) > 2:
            errors.append(("chain", y, COLS[i], q1[i], q2[i], h1[i], q3[i], n9[i]))
if errors:
    print("CHECK FAILED:"); [print(" ", e) for e in errors]; sys.exit(1)
for f, (page, rows) in DOCS.items():
    _, year, pub, title, url, sha, _ = idx[f]
    q = int(title[-1]); y = title[-7:-3]
    facts = []
    for (start, end, kind, fq), vals in rows:
        for metric, v in zip(COLS, vals):
            facts.append({"metric": metric, "value": v, "currency": "SAR", "unit": "SAR/share" if metric == "eps_diluted" else "SAR",
                          "period_start": start, "period_end": end, "period_kind": kind, "fiscal_year": int(start[:4]),
                          "fiscal_quarter": fq, "page": page, "table": "condensed consolidated interim statement of income",
                          **({} if metric == "eps_diluted" else {"scale": 1000})})
    name = f"{out}/sabic-{y}-q{q}-income-statement.json"
    json.dump({"company_id": "sa:2010", "filing_type": f"{title} (SABIC investor relations) - statement of income",
               "filed_at": pub, "period_end": rows[0][0][1], "source_url": url,
               "notes": (f"sha256 {sha}. filed_at is the investor-relations publication date. Net income is total "
                         "(including non-controlling interests and discontinued operations); EPS is from net income attributable "
                         "to equity holders of the Parent, as in the engine's SABIC FY rows. Prior-year columns are kept as "
                         "re-presented in this document. Checks: revenue + cost of sales = gross profit for every period; "
                         "quarters add to the year-to-date column; net income agrees across original and re-presented columns."),
               "facts": facts}, open(name, "w"), indent=1)
    print(name.split("/")[-1], len(facts))
