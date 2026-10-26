"""SABIC year-end working-capital balances 2020-2022 and the statutory reserve, transcribed from statement-of-financial-
position page images (2022 financial statements p.8; 2021 Q4 report p.4), each checked against the printed subtotals.
Usage: build_sabic_balances.py <src-dl/sabic> <out-dir>"""
import json, sys
src, out = sys.argv[1:3]
idx = {l.split("\t")[0]: l.rstrip("\n").split("\t") for l in open(f"{src}/index.tsv")}
# file -> page, {year-end: {lines}}, current-asset lines + printed total, current-liability lines + printed total
DOCS = {
 "15-SABIC_Financials_2022.pdf": (8, {
   2022: dict(inventory=28224642, accounts_receivable=23923727, accounts_payable=22537990, statutory_reserve=15000000,
              current_assets=(28224642, 23923727, 5930721, 8678959, 40059331, 106817380),
              current_liabilities=(915839, 5979853, 904614, 22537990, 14864314, 830304, 2160763, 48193677)),
   2021: dict(inventory=28621278, accounts_receivable=26330104, accounts_payable=26149125, statutory_reserve=15000000,
              cash=42319393, totals=dict(non_current_assets=211040697, total_assets=319355328,
                                         property_plant_equipment=131018714),
              current_assets=(28621278, 26330104, 5977302, 5066554, 42319393, 108314631),
              current_liabilities=(13347, 5290046, 951669, 26149125, 15211813, 1128413, 2449597, 51194010))}),
 "11-Sabic_FInancials_2023.pdf": (9, {
   2023: dict(inventory=18332223, accounts_receivable=19295374, accounts_payable=20087016, cash=32414996,
              current_debt=(2414233, 2301534), long_term_debt=23255179, statutory_reserve=0,
              current_assets=(18332223, 19295374, 5295155, 9842617, 32414996, 85180365)),
   2022: dict(cash=40059331, current_debt=(915839, 5979853), long_term_debt=21543556)}),
 # condensed: trade payables are not separated from other current liabilities, so only inventory and receivables
 "19-Quarterly_Report_2021_Q4.pdf": (4, {
   2020: dict(inventory=19311198, accounts_receivable=16927713,
              totals=dict(non_current_assets=214075898, total_assets=295468550, property_plant_equipment=136179720),
              current_assets=(19311198, 16927713, 6141597, 5855928, 33156216, 81392652),
              current_liabilities=(7989565, 29503345, 37492910))}),
}
LABELS = {"inventory": "Inventories", "accounts_receivable": "Trade receivables", "accounts_payable": "Trade payables",
          "statutory_reserve": "Statutory reserve (printed as nil where shown as a dash)",
          "cash": "Cash and cash equivalents (statement of financial position)",
          "current_debt": "Short-term borrowings plus current portion of debt", "long_term_debt": "Debt (non-current)",
          "total_assets": "Total assets", "property_plant_equipment": "Property, plant and equipment",
          "current_assets_total": "Total current assets", "current_liabilities_total": "Total current liabilities"}
METRIC = {"current_assets_total": "current_assets", "current_liabilities_total": "current_liabilities"}
TEXT_PAGES = {"11-Sabic_FInancials_2023.pdf"}
for f, (page, years) in DOCS.items():
    for year, v in years.items():
        for block in ("current_assets", "current_liabilities"):
            if block in v and sum(v[block][:-1]) != v[block][-1]:
                sys.exit(f"{f} {year} {block} does not add to its printed total")
    if f in TEXT_PAGES:  # every figure must be printed on the page text
        import subprocess
        text = " ".join(subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", f"{src}/{f}", "-"],
                                       capture_output=True, text=True).stdout.split())
        for year, v in years.items():
            for metric in LABELS:
                for part in (v[metric] if isinstance(v.get(metric), tuple) else (v.get(metric),)):
                    if part and f"{part:,}" not in text: sys.exit(f"{f} {year} {metric} {part:,} not on page {page}")
    for year, v in years.items():  # years without assets held for sale: emit the totals, checked to add up
        if "totals" in v:
            t = v.pop("totals")
            if t["non_current_assets"] + v["current_assets"][-1] != t["total_assets"]:
                sys.exit(f"{f} {year} total assets do not add up")
            v.update(total_assets=t["total_assets"], property_plant_equipment=t["property_plant_equipment"],
                     current_assets_total=v["current_assets"][-1], current_liabilities_total=v["current_liabilities"][-1])
    _, _, pub, title, url, sha, _ = idx[f]
    for v in years.values():
        if isinstance(v.get("current_debt"), tuple): v["current_debt"] = sum(v["current_debt"])
    facts = [{"metric": METRIC.get(metric, metric), "value": v[metric], "currency": "SAR", "unit": "SAR", "scale": 1000,
              "period_end": f"{year}-12-31", "period_kind": "instant", "fiscal_year": year, "page": page,
              "source_label": LABELS[metric], "table": "statement of financial position"}
             for year, v in years.items() for metric in LABELS if metric in v]
    last = max(years)
    name = {2023: f"{out}/sabic-2023-fy-balance-sheet.json", 2022: f"{out}/sabic-2022-fy-working-capital.json",
            2020: f"{out}/sabic-2021-q4-opening-balances.json"}[last]
    json.dump({"company_id": "sa:2010", "filing_type": f"{title} (SABIC investor relations) - statement of financial position",
               "filed_at": pub, "period_end": f"{last}-12-31", "source_url": url,
               "notes": (f"sha256 {sha}. " + ("Page text matched figure by figure; current assets" if f in TEXT_PAGES
                                                else "Page image transcribed; current assets")
                         + (" and current liabilities" if last == 2022 else "")
                         + " add to the printed totals for every year."
                         + ("" if last != 2020 else " Only the 2020 comparative column is taken: the 2021 balances come "
                            "from the 2022 financial statements, which re-present them.")),
               "facts": facts}, open(name, "w"), indent=1)
    print(name.split("/")[-1], len(facts))
