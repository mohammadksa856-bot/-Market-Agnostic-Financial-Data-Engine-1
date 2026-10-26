"""SABIC fiscal-year statements 2019-2023 (IFRS), one manifest per filing, plus FY EBITDA from the earnings releases.

Each filing is kept with its own comparative column, so a later filing's re-presented comparative supersedes the
earlier figure (manifests are processed in name order). Checks per period: revenue + cost of sales = gross profit;
income before zakat and tax - zakat - income tax = net income (continuing operations where a discontinued
operation is shown); continuing + discontinued = net income; parent + non-controlling interests = net income;
operating cash flow is re-added from its printed sub-total. Text pages are also matched against the page text;
image pages (2021 Q4 report, 2022 financial statements) are transcribed from the page image.
Usage: build_sabic_annual.py <src-dl/sabic> <src-dl/sabic-er> <out-dir>"""
import json, re, subprocess, sys
src, er_src, out = sys.argv[1:4]
idx = {l.split("\t")[0]: l.rstrip("\n").split("\t") for l in open(f"{src}/index.tsv")}

# year -> values in SAR thousands; eps as printed. capex = purchase of PPE + additions of intangibles (SABIC's own
# free-cash-flow definition), or the single "purchase of tangible and intangible assets" line where printed so.
DOCS = {
 "23-Quarterly_Report_2020_Q4.pdf": {"pages": (5, 8), "text": True, "years": {
   2020: dict(revenue=116955466, cost_of_revenue=-94135670, gross_profit=22819796, operating_income=4478477,
              ibt=3267195, zakat=-1682560, tax=-342421, net_income=1242214, parent=41891, nci=1200323, eps="0.01",
              operating_cash_flow=21606256, capex=-13142521),
   2019: dict(revenue=135396003, cost_of_revenue=-105991286, gross_profit=29404717, operating_income=11523151,
              ibt=9198809, zakat=-1941007, tax=-653932, net_income=6603870, parent=5198113, nci=1405757, eps="1.73",
              operating_cash_flow=33776834, capex=-18577669)}},
 "19-Quarterly_Report_2021_Q4.pdf": {"pages": (5, 8), "text": False, "years": {
   2021: dict(revenue=174924275, cost_of_revenue=-123775195, gross_profit=51149080, operating_income=33319755,
              ibt=34075000, zakat=-1960393, tax=-1625813, net_income=30488794, parent=23033722, nci=7455072, eps="7.68",
              operating_cash_flow=40304443, capex=-11562519,
              ocf_parts=(43473886, -1036072, -2133371)),
   2020: dict(revenue=116949287, cost_of_revenue=-94311132, gross_profit=22638155, operating_income=4573937,
              ibt=3277257, zakat=-1682560, tax=-338468, net_income=1256229, parent=66825, nci=1189404, eps="0.02",
              operating_cash_flow=22145917, capex=-13255646,
              ocf_parts=(25919917, -1034687, -2739313))}},
 "15-SABIC_Financials_2022.pdf": {"pages": (9, 12), "text": False, "years": {
   2022: dict(revenue=198466764, cost_of_revenue=-155794483, gross_profit=42672281, operating_income=23879060,
              ibt=25988176, zakat=-1962183, tax=-533170, net_income=23492823, parent=16529722, nci=6963101, eps="5.51",
              operating_cash_flow=35810131, ppe=-10111785, intangibles=-111897,
              ocf_parts=(36957543, 2537993, 653075, -973904, -3364576)),
   2021: dict(revenue=174883126, cost_of_revenue=-127005996, gross_profit=47877130, operating_income=33599995,
              ibt=34087964, zakat=-1960393, tax=-1625800, net_income=30501771, parent=23066002, nci=7435769, eps="7.69",
              operating_cash_flow=39493631, ppe=-10800388, intangibles=-171074,
              ocf_parts=(39050110, 3363026, 290377, -1076511, -2133371))}},
 "11-Sabic_FInancials_2023.pdf": {"pages": (10, 14), "text": True, "years": {
   2023: dict(revenue=141537187, cost_of_revenue=-119463105, gross_profit=22074082, operating_income=3720393,
              ibt=4523614, zakat=-1269160, tax=438208, continuing=3692662, discontinued=-4076939, net_income=-384277,
              parent=-2772282, nci=2388005, eps="-0.92", operating_cash_flow=24452920, ppe=-10456518,
              intangibles=-36757, ocf_parts=(25909564, 1787474, 1738327, -1989138, -2993307)),
   2022: dict(revenue=183076594, cost_of_revenue=-141754850, gross_profit=41321744, operating_income=22907873,
              ibt=25112381, zakat=-1830246, tax=-533170, continuing=22748965, discontinued=743858, net_income=23492823,
              parent=16529722, nci=6963101, eps="5.51", operating_cash_flow=35810131, ppe=-10111785,
              intangibles=-111897, ocf_parts=(36957543, 2537993, 653075, -973904, -3364576))}},
}
# earnings release file -> {year: EBITDA in SAR billion as printed}
RELEASES = {
 "2022-02-03_Earnings-Release-Q4-2021.pdf": ("https://www.sabic.com/en/Images/ER-Q4-21-EN_tcm1010-31855.pdf", 2021,
                                             {2021: "48.27", 2020: "20.22"}),
 "2023-02-28_Earnings-Release-2022.pdf": ("https://www.sabic.com/en/Images/ER-Full-Year-22-EN_tcm1010-38909.pdf", 2022,
                                          {2022: "38.57", 2021: "48.51"}),
 "2024-02-29_Earnings-Release-2023.pdf": ("https://www.sabic.com/en/Images/EARNINGS%20RELEASE%202023_tcm1010-42835.pdf",
                                          2023, {2023: "19.02", 2022: "36.40"}),
}
errors = []
def printed(v):
    s = f"{abs(v):,}" if isinstance(v, int) else v.lstrip("-")
    return f"({s})" if (v < 0 if isinstance(v, int) else v.startswith("-")) else s
def page_text(path, first, last):
    return subprocess.run(["pdftotext", "-f", str(first), "-l", str(last), "-layout", path, "-"],
                          capture_output=True, text=True).stdout

for f, doc in DOCS.items():
    text = page_text(f"{src}/{f}", *doc["pages"]) if doc["text"] else ""
    for year, v in doc["years"].items():
        if v["revenue"] + v["cost_of_revenue"] != v["gross_profit"]: errors.append((f, year, "gross profit"))
        after_tax = v["ibt"] + v["zakat"] + v["tax"]
        if after_tax != v.get("continuing", v["net_income"]): errors.append((f, year, "tax bridge", after_tax))
        if "continuing" in v and v["continuing"] + v["discontinued"] != v["net_income"]:
            errors.append((f, year, "continuing + discontinued"))
        if v["parent"] + v["nci"] != v["net_income"]: errors.append((f, year, "parent + nci"))
        if "ocf_parts" in v and sum(v["ocf_parts"]) != v["operating_cash_flow"]: errors.append((f, year, "ocf"))
        if doc["text"]:
            for key, value in v.items():
                if key == "ocf_parts": continue
                if not re.search(r"(?<![\d,.])" + re.escape(printed(value)) + r"(?![\d,])", text.replace("  ", " ")):
                    errors.append((f, year, "not on page", key, printed(value)))
for f, (url, _, years) in RELEASES.items():
    text = open(f"{er_src}/{f[:-4]}.txt").read()
    for year, value in years.items():
        if value not in text: errors.append((f, year, "EBITDA not in release text", value))
if errors:
    print("CHECK FAILED:"); [print(" ", e) for e in errors]; sys.exit(1)

def fact(metric, value, year, page, label, scale=1000, unit="SAR"):
    row = {"metric": metric, "value": value, "currency": "SAR", "unit": unit, "period_start": f"{year}-01-01",
           "period_end": f"{year}-12-31", "period_kind": "fy", "fiscal_year": year, "page": page, "source_label": label}
    if scale != 1: row["scale"] = scale
    return row

LABELS = {"revenue": "Revenue", "cost_of_revenue": "Cost of sales", "gross_profit": "Gross profit",
          "operating_income": "Income from operations", "ebit": "Income from operations",
          "income_before_income_taxes_and_zakat": "Income before zakat and income tax",
          "continuing_operations_income": "Net income from continuing operations",
          "discontinued_operations_income": "Net (loss) income from discontinued operation",
          "net_income": "Net income for the year", "net_income_parent": "Attributable to equity holders of the Parent",
          "net_income_noncontrolling": "Attributable to non-controlling interests",
          "operating_cash_flow": "Net cash from operating activities",
          "ppe_purchases": "Purchase of property, plant and equipment",
          "intangible_asset_purchases": "Additions of intangible assets"}
for f, doc in DOCS.items():
    _, _, pub, title, url, sha, _ = idx[f]
    income_page, cash_page = doc["pages"]
    facts = []
    for year, v in doc["years"].items():
        lines = {"revenue": v["revenue"], "cost_of_revenue": v["cost_of_revenue"], "gross_profit": v["gross_profit"],
                 "operating_income": v["operating_income"], "ebit": v["operating_income"],
                 "income_before_income_taxes_and_zakat": v["ibt"], "net_income": v["net_income"],
                 "net_income_parent": v["parent"], "net_income_noncontrolling": v["nci"]}
        if "continuing" in v:
            lines.update(continuing_operations_income=v["continuing"], discontinued_operations_income=v["discontinued"])
        for metric, value in lines.items():
            facts.append(fact(metric, value, year, income_page, LABELS[metric]))
        facts.append(fact("income_taxes_and_zakat", v["zakat"] + v["tax"], year, income_page,
                          "Zakat expense + income tax expense (sum of the two printed lines; expense negative)"))
        for metric in ("eps_diluted", "basic_eps"):
            facts.append(fact(metric, v["eps"], year, income_page, "Basic and diluted earnings per share", 1,
                              "SAR/share"))
        facts.append(fact("operating_cash_flow", v["operating_cash_flow"], year, cash_page, LABELS["operating_cash_flow"]))
        if "ppe" in v:
            facts.append(fact("ppe_purchases", v["ppe"], year, cash_page, LABELS["ppe_purchases"]))
            facts.append(fact("intangible_asset_purchases", v["intangibles"], year, cash_page,
                              LABELS["intangible_asset_purchases"]))
            facts.append(fact("capex", v["ppe"] + v["intangibles"], year, cash_page,
                              "Purchase of property, plant and equipment + additions of intangible assets"))
        else:
            facts.append(fact("capex", v["capex"], year, cash_page, "Purchase of tangible and intangible assets"))
    last = max(doc["years"])
    name = f"{out}/sabic-{last}-fy-statements.json"
    json.dump({"company_id": "sa:2010", "filing_type": f"{title} (SABIC investor relations) - annual statements",
               "filed_at": pub, "period_end": f"{last}-12-31", "source_url": url,
               "notes": (f"sha256 {sha}. filed_at is the investor-relations publication date. The prior-year column is "
                         "kept as re-presented in this filing. Net income is total (including non-controlling interests "
                         "and discontinued operations); EPS is from net income attributable to equity holders of the "
                         "Parent. Checks: gross profit, tax bridge, continuing + discontinued, parent + NCI, operating "
                         "cash flow sub-total" + ("; every value matched on the page text." if doc["text"] else
                                                   "; image pages transcribed and checked arithmetically.")),
               "facts": facts}, open(name, "w"), indent=1)
    print(name.split("/")[-1], len(facts))
for f, (url, last, years) in RELEASES.items():
    facts = [fact("ebitda", value, year, None, "EBITDA (income from operations plus depreciation, amortization and "
                  "impairment), SAR billion", 1_000_000_000) for year, value in years.items()]
    for row in facts: row.pop("page")
    name = f"{out}/sabic-{last}-fy-earnings-release.json"
    json.dump({"company_id": "sa:2010", "filing_type": f"SABIC earnings release FY {last} - summary financial results",
               "filed_at": f[:10], "period_end": f"{last}-12-31", "source_url": url,
               "notes": "Table 1 summary financial results, SAR billion as printed; the prior-year column as re-presented "
                        "in this release.", "facts": facts}, open(name, "w"), indent=1)
    print(name.split("/")[-1], len(facts))

# Dividends per share declared for a fiscal year, as approved by the general assembly (stated in the next year's
# Q4 report), or as stated by the earnings release. Same basis as the engine's 2021-2025 rows (declared for the year).
DPS = {  # file -> (fiscal year, SAR per share, page, sentence that must appear in the page text)
 "43-Quarterly_Report_2015_Q4.pdf": (2014, "5.5", 19, "SR 16.5 billion (SR 5.5 per share)"),
 "39-Quarterly_Report_2016_Q4.pdf": (2015, "5.5", 19, "SR 16.5 billion (SR 5.5 per share)"),
 "35-Quarterly_Report_2017_Q4.pdf": (2016, "4", 70, "SR 12 billion (SR 4 per share)"),
 "31-Quarterly_Report_2018_Q4.pdf": (2017, "4.2", 20, "SR 12.6 billion (SR 4.2 per share)"),
 "27-Quarterly_Report_2019_Q4.pdf": (2018, "4.4", 17, "SR 13.2 billion (SR 4.4 per share)"),
 "23-Quarterly_Report_2020_Q4.pdf": (2019, "4.4", 23, "SR 13.2 billion (SR 4.4 per share)"),
}
DPS_RELEASES = {"2022-02-03_Earnings-Release-Q4-2021.pdf": (2020, "3.0", "SAR 3.0 per share declared dividends in 2020")}
for f, (year, value, page, sentence) in DPS.items():
    text = " ".join(page_text(f"{src}/{f}", page, page).split())
    if sentence not in text:
        print("CHECK FAILED: dividend sentence not on page", f, page, sentence); sys.exit(1)
    _, _, pub, title, url, sha, _ = idx[f]
    row = fact("dividends_per_share", value, year, page, f"Cash dividends approved for {year}: {sentence}", 1, "SAR/share")
    name = f"{out}/sabic-{year + 1}-dividends-approved.json"
    json.dump({"company_id": "sa:2010", "filing_type": f"{title} (SABIC investor relations) - dividends note",
               "filed_at": pub, "period_end": f"{year + 1}-12-31", "source_url": url,
               "notes": f"sha256 {sha}. Dividends declared for fiscal year {year} as approved by the general assembly.",
               "facts": [row]}, open(name, "w"), indent=1)
    print(name.split("/")[-1], 1)
for f, (year, value, sentence) in DPS_RELEASES.items():
    text = " ".join(open(f"{er_src}/{f[:-4]}.txt").read().split())
    if sentence not in text:
        print("CHECK FAILED: dividend sentence not in release", f, sentence); sys.exit(1)
    url = RELEASES[f][0]
    row = fact("dividends_per_share", value, year, None, f"Dividends declared for {year}: {sentence}", 1, "SAR/share")
    row.pop("page")
    name = f"{out}/sabic-{year + 1}-dividends-declared-release.json"
    json.dump({"company_id": "sa:2010", "filing_type": f"SABIC earnings release Q4 {year + 1} - dividends",
               "filed_at": f[:10], "period_end": f"{year + 1}-12-31", "source_url": url,
               "notes": "Dividends per share declared for the prior fiscal year, as stated in the release.",
               "facts": [row]}, open(name, "w"), indent=1)
    print(name.split("/")[-1], 1)
