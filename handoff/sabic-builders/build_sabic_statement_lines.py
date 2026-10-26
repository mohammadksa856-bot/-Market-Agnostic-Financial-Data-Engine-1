"""SABIC FY2025/FY2024 statement and note lines from the Integrated Annual Report 2025.

Each printed figure must appear on its PDF page (as printed, thousands of SAR unless noted). Sums are of printed lines
and named as such. Usage: build_sabic_statement_lines.py <sabic-ar2025.pdf> <out.json>"""
import json, sys
import pymupdf
pdf, out = sys.argv[1:3]
doc = pymupdf.open(pdf)
page_text = lambda n: " ".join(doc[n - 1].get_text().split())
URL = "https://www.sabic.com/en/Images/SABIC-Integrated-Annual-Report-2025-EN_tcm1010-49452.pdf"

def printed(v):
    return f"({abs(v):,})" if v < 0 else f"{v:,}"

def fy(metric, value, year, page, label, kind="fy", scale=1000, unit="SAR", dimensions=None, parts=None):
    row = {"metric": metric, "value": value, "currency": "SAR", "unit": unit, "period_end": f"{year}-12-31",
           "period_kind": kind, "fiscal_year": year, "page": page, "source_label": label}
    if kind == "fy": row["period_start"] = f"{year}-01-01"
    if scale != 1: row["scale"] = scale
    if dimensions: row["dimensions"] = dimensions
    return row, (parts if parts is not None else [value])

ROWS = [
 # cash flow statement, pp. 136-137 (totals include discontinued operations, like the statement)
 fy("ppe_purchases", -8750028, 2025, 137, "Purchase of property, plant and equipment"),
 fy("intangible_asset_purchases", -24777, 2025, 137, "Additions of intangible assets"),
 fy("capex", -8774805, 2025, 137, "Purchase of property, plant and equipment + additions of intangible assets",
    parts=[-8750028, -24777]),
 fy("depreciation_amortization_cash_flow", 12897679, 2025, 136,
    "Depreciation of PPE + depreciation of right-of-use assets + amortisation of intangible and other assets",
    parts=[11185373, 1184728, 527578]),
 # statement of income, p. 133
 fy("income_taxes_and_zakat", -1603954, 2025, 133, "Zakat expense + income tax (sum of the two printed lines; expense negative)",
    parts=[-907776, -696178]),
 fy("income_taxes_and_zakat", -821073, 2024, 133, "Zakat expense + income tax (sum of the two printed lines; expense negative)",
    parts=[-213827, -607246]),
 fy("ebit", 9426513, 2024, 133, "Income from operations (EBIT)"),
 # equity at 1 January 2024 as restated in this report (note 42, associate restatement), p. 135
 fy("total_equity", 194807590, 2023, 135, "Total equity - balance as at 1 January 2024 (restated)", kind="instant"),
 fy("equity_parent", 166953664, 2023, 135,
    "Equity attributable to equity holders of the Parent - balance as at 1 January 2024 (restated)", kind="instant"),
 fy("minority_interest_income", 1054265, 2025, 133, "Net (loss) income attributable to non-controlling interests"),
 fy("minority_interest_income", 2184593, 2024, 133, "Net (loss) income attributable to non-controlling interests"),
 # equity, p. 135: other reserves receive other comprehensive income (note 20)
 fy("accumulated_other_comprehensive_income", -1472793, 2025, 135, "Other reserves (balance as at 31 December)",
    kind="instant"),
 fy("accumulated_other_comprehensive_income", -4112475, 2024, 135, "Other reserves (balance as at 31 December)",
    kind="instant"),
 # note 32: earnings per share
 fy("weighted_average_shares_basic", 3000000, 2024, None, "Weighted average number of ordinary shares ('000)", unit="shares"),
 fy("weighted_average_shares_diluted", 3000000, 2024, None,
    "Weighted average number of ordinary shares ('000); no dilutive instruments", unit="shares"),
 # note 33: key management personnel compensation
 *[fy("key_management_compensation", v, y, None, f"Key management compensation - {t}",
      dimensions={"compensation_type": t})
   for t, v25, v24 in (("Short-term employee benefits", 47499, 38425), ("Post-employment benefits", 8610, 8182),
                       ("Other long-term benefits", 11604, 30439)) for y, v in ((2025, v25), (2024, v24))],
 fy("key_management_compensation", 67713, 2025, None, "Key management compensation - total"),
 fy("key_management_compensation", 77046, 2024, None, "Key management compensation - total"),
]
# note pages located by their printed text
def find(*needles):
    hits = [n for n in range(1, len(doc) + 1) if all(x in page_text(n) for x in needles)]
    if len(hits) != 1: sys.exit(f"page for {needles}: {hits}")
    return hits[0]
EPS_PAGE = find("Weighted average number of ordinary shares", "There are no instruments that have diluted")
KMP_PAGE = find("Remuneration of key management can be shown as follows", "67,713", "77,046")
CONT_PAGE = find("39.3 CONTINGENT LIABILITIES", "1,070 million", "1,150 million")
rows = []
errors = []
for row, parts in ROWS:
    if row["page"] is None:
        row["page"] = EPS_PAGE if "weighted" in row["metric"] else KMP_PAGE
    text = page_text(row["page"])
    for part in parts:
        if printed(part) not in text: errors.append((row["metric"], row["fiscal_year"], printed(part), row["page"]))
    if len(parts) > 1 and sum(parts) != row["value"] and -sum(parts) != row["value"]:
        errors.append((row["metric"], "sum", parts, row["value"]))
    rows.append(row)
for year, value in ((2025, 1070), (2024, 1150)):  # contingent liabilities: bank guarantees issued for the Group
    r, _ = fy("contingencies", value, year, CONT_PAGE,
              "Bank guarantees issued on the Group's behalf (contingent liabilities, note 39.3)", kind="instant",
              scale=1000000)
    rows.append(r)
if errors:
    print("CHECK FAILED:"); [print(" ", e) for e in errors]; sys.exit(1)
json.dump({"company_id": "sa:2010", "filing_type": "Integrated Annual Report 2025 - statement and note lines",
           "filed_at": "2026-03-03", "period_end": "2025-12-31", "source_url": URL,
           "notes": ("Consolidated statements and notes 20, 32, 33 and 39 of the Integrated Annual Report 2025; each "
                     "printed figure is matched on its page. Capex is purchase of PPE plus additions of intangible "
                     "assets (SABIC's free-cash-flow definition, as for 2019-2024). Cash-flow D&A and capex include "
                     "discontinued operations, as the statement does."),
           "facts": rows}, open(out, "w"), indent=1)
print(out, len(rows), "facts; pages eps", EPS_PAGE, "kmp", KMP_PAGE, "contingencies", CONT_PAGE)
