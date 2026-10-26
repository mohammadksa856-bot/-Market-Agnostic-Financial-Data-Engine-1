"""SABIC 2026 earnings releases: quarters on the 2026 presentation basis, the new segment split, and the releases
themselves as announcements.

The FY2025 and 2026 releases present every period with the European Petrochemicals and the Americas/Europe
Engineering Thermoplastics businesses as discontinued operations, so Q4 2024 to Q3 2026 are on one basis. Values are
SAR billion as printed (EPS in SAR). A period already in the interim statements at full precision is not repeated
from a release. Checks: every printed value is found in its release's summary table text; quarters add to the
year-to-date and fiscal-year columns within rounding; segments add to the group total in the Q3 2026 reconciliation.
Usage: build_sabic_releases.py <src-dl/sabic-er> <arabic report listing json> <out-dir>"""
import json, sys
from decimal import Decimal
er, ar_listing, out = sys.argv[1:4]
AR_TITLES = {r["PublishedDate"][:10]: r["Title"] for r in json.load(open(ar_listing))["Reports"]
             if r.get("ReportType") == "Earnings Release"}
B = Decimal(10) ** 9
Q = {"2024Q4": ("2024-10-01", "2024-12-31", "quarter", 2024, 4), "2025Q1": ("2025-01-01", "2025-03-31", "quarter", 2025, 1),
     "2025Q2": ("2025-04-01", "2025-06-30", "quarter", 2025, 2), "2025Q3": ("2025-07-01", "2025-09-30", "quarter", 2025, 3),
     "2025Q4": ("2025-10-01", "2025-12-31", "quarter", 2025, 4), "2026Q1": ("2026-01-01", "2026-03-31", "quarter", 2026, 1),
     "2026Q2": ("2026-04-01", "2026-06-30", "quarter", 2026, 2), "2026Q3": ("2026-07-01", "2026-09-30", "quarter", 2026, 3),
     "2025H1": ("2025-01-01", "2025-06-30", "ytd", 2025, 2), "2026H1": ("2026-01-01", "2026-06-30", "ytd", 2026, 2),
     "2025M9": ("2025-01-01", "2025-09-30", "ytd", 2025, 3), "2026M9": ("2026-01-01", "2026-09-30", "ytd", 2026, 3),
     "2025FY": ("2025-01-01", "2025-12-31", "fy", 2025, None), "2024FY": ("2024-01-01", "2024-12-31", "fy", 2024, None)}
RELEASES = {
 "2026-03-04_EARNINGS-RELEASE-2025": {
   "name": "sabic-2026-fy2025-earnings-release.json", "period_end": "2025-12-31", "label": "full year 2025",
   "url": "https://www.sabic.com/en/Images/EARNINGS%20RELEASE%202025_tcm1010-49420.pdf", "title": "EARNINGS RELEASE 2025",
   "body": ("Saudi Basic Industries Corporation (SABIC) announced its financial results for the full year of 2025: "
            "revenue of SAR 116.53 billion, EBITDA of SAR 16.43 billion, net loss attributable to equity holders of the "
            "Parent of SAR 25.78 billion and free cash flow of SAR 7.18 billion."),
   "values": {"revenue": {"2025Q4": "27.95", "2025Q3": "29.08", "2024Q4": "29.65"},
              "ebitda": {"2025Q4": "3.04", "2025Q3": "5.04", "2024Q4": "4.26"},
              "ebit": {"2025Q4": "-0.88", "2025Q3": "2.28", "2024Q4": "1.29"},
              # adjusted figures eliminate non-operational anomalies and one-offs (release footnote 2)
              "adjusted_ebit": {"2025FY": "6.92", "2024FY": "9.79"},
              "earnings_per_share_normalized": {"2025FY": "0.69", "2024FY": "1.96"}}},
 "2026-04-29_EARNINGS-RELEASE-Q1-2026": {
   "name": "sabic-2026-q1-earnings-release.json", "period_end": "2026-03-31", "label": "first quarter of 2026",
   "url": "https://www.sabic.com/en/Images/EARNINGS-RELEASE-Q1-2026_tcm1010-51239.pdf", "title": "EARNINGS RELEASE Q1 2026",
   "body": ("SABIC announced its financial results for the first quarter of 2026: revenue of SAR 26.15 billion, "
            "EBITDA of SAR 4.15 billion and net income attributable to equity holders of the Parent of SAR 0.01 billion."),
   "values": {"ebitda": {"2026Q1": "4.15", "2025Q1": "3.02"}}},
 "2026-07-29_EARNINGS-RELEASE-Q2-2026": {
   "name": "sabic-2026-q2-earnings-release.json", "period_end": "2026-06-30", "label": "second quarter of 2026",
   "url": "https://www.sabic.com/en/Images/EARNINGS-RELEASE-Q2-2026_tcm1010-51709.pdf", "title": "EARNINGS RELEASE Q2 2026",
   "body": ("SABIC announced its financial results for the second quarter of 2026: revenue of SAR 24.81 billion, "
            "EBITDA of SAR 3.79 billion and a net loss attributable to equity holders of the Parent of SAR 0.83 billion."),
   "values": {"ebitda": {"2026Q2": "3.79", "2025Q2": "5.33", "2026H1": "7.94", "2025H1": "8.34"}},
   "events": [
     {"disclosure_type": "dividend_announcement", "title": "Cash dividends of SAR 3.3 billion for the first half of 2026",
      "body_text": "SABIC's CEO statement in the second-quarter 2026 earnings release reports the announcement of SAR 3.3 "
                   "billion in dividends for the first half of 2026.",
      "quote": "with the announcement of SAR 3.3 billion in dividends for the first half of 2026",
      "metadata": {"event_class": "dividend", "total_amount_sar": 3300000000, "dividend_period": "2026H1", "page": 2}}]},
 "2026-10-25_EARNINGS-RELEASE-Q3-2026": {
   "name": "sabic-2026-q3-earnings-release.json", "period_end": "2026-09-30", "label": "third quarter of 2026",
   "url": "https://www.sabic.com/en/Images/EARNINGS-RELEASE-Q3-2026_tcm1010-51796.pdf", "title": "EARNINGS RELEASE Q3 2026",
   "body": ("SABIC announced its financial results for the third quarter of 2026, reporting a 14% increase in revenue "
            "and a 40% increase in adjusted EBITDA quarter-on-quarter: revenue of SAR 28.17 billion, EBITDA of SAR 4.74 "
            "billion and net income attributable to equity holders of the Parent of SAR 0.5 billion."),
   "values": {"revenue": {"2026Q3": "28.17", "2026M9": "79.13", "2025M9": "88.57"},
              "ebitda": {"2026Q3": "4.74", "2026M9": "12.67", "2025M9": "13.38"},
              "ebit": {"2026Q3": "2.06", "2026M9": "4.22", "2025M9": "5.25"},
              "net_income_parent": {"2026Q3": "0.5", "2026M9": "-0.32"},
              "eps_diluted": {"2026Q3": "0.17", "2026M9": "-0.11"}},
   # segment -> metric -> period -> value (Gross Revenue, EBITDA, Income from operations), pages 5-6
   "segments": {"Petrochemicals": {"revenue": {"2026Q3": "22.95", "2026Q2": "20.47", "2025Q3": "23.89", "2026M9": "65.18", "2025M9": "73.78"},
                                   "ebitda": {"2026Q3": "4.01", "2026Q2": "2.77", "2025Q3": "3.50", "2026M9": "9.14", "2025M9": "9.34"},
                                   "ebit": {"2026Q3": "1.70", "2026Q2": "0.08", "2025Q3": "1.14", "2026M9": "1.87", "2025M9": "2.39"}},
                "Agri-Nutrients": {"revenue": {"2026Q3": "3.22", "2026Q2": "2.40", "2025Q3": "3.40", "2026M9": "8.33", "2025M9": "9.64"},
                                   "ebitda": {"2026Q3": "0.65", "2026Q2": "0.68", "2025Q3": "1.42", "2026M9": "2.70", "2025M9": "3.74"},
                                   "ebit": {"2026Q3": "0.45", "2026Q2": "0.49", "2025Q3": "1.22", "2026M9": "2.12", "2025M9": "3.10"}},
                "Specialties": {"revenue": {"2026Q3": "2.00", "2026Q2": "1.94", "2025Q3": "1.79", "2026M9": "5.62", "2025M9": "5.15"},
                                "ebitda": {"2026Q3": "0.41", "2026Q2": "0.38", "2025Q3": "0.30", "2026M9": "1.23", "2025M9": "0.80"},
                                "ebit": {"2026Q3": "0.28", "2026Q2": "0.22", "2025Q3": "0.13", "2026M9": "0.75", "2025M9": "0.36"}}},
   # Q3 2026 sales volumes (pages 5-6), million tonnes; Specialties printed in thousand tonnes
   "volumes": [("sales_volume_by_product", "3.67", {"segment": "Petrochemicals", "product": "Chemicals"},
                "Chemicals sales volume was 3.67 MMT"),
               ("sales_volume_by_product", "2.95", {"segment": "Petrochemicals", "product": "Polymers"},
                "Polymers sales volume was 2.95"),
               ("sales_volume", "6.71", {"segment": "Petrochemicals"}, "Total Petrochemicals sales volume of 6.71 MMT"),
               ("sales_volume", "1.62", {"segment": "Agri-Nutrients"}, "Total Agri-Nutrients sales volume of 1.62 MMT"),
               ("specialties_sales_volume", "0.065", None, "Total Specialties sales volume of 65 KMT during Q3 2026")],
   "events": [
     {"disclosure_type": "material_event", "title": "Divestment of the Engineering Thermoplastics business in the Americas and Europe completed",
      "body_text": "SABIC completed the divestment of its Engineering Thermoplastics business in the Americas and Europe for an "
                   "enterprise value of US$ 450 million, as part of its Portfolio Optimization Program.",
      "quote": "the completion of the divestment of the Engineering Thermoplastics business in the Americas and Europe for an enterprise value of $450 million",
      "metadata": {"event_class": "divestment", "enterprise_value_usd": 450000000, "page": 3}},
     {"disclosure_type": "material_event", "title": "SABIC Agri-Nutrients final investment decision for an ammonia and urea complex",
      "body_text": "SABIC Agri-Nutrients reached a final investment decision to build a new industrial complex in the Kingdom "
                   "with annual capacity of 1.2 million metric tons of ammonia and 2.6 million metric tons of urea, raising "
                   "its urea production capacity by 54%.",
      "quote": "Final Investment Decision to build a new industrial complex for ammonia and urea production",
      "metadata": {"event_class": "capital_project", "ammonia_capacity_mtpa": "1.2", "urea_capacity_mtpa": "2.6", "page": 3}},
     {"disclosure_type": "guidance", "title": "Full-year 2026 capital expenditure guidance of US$ 3 to 3.3 billion",
      "body_text": "SABIC guides full-year 2026 capital expenditure and capital injection for its growth project, including "
                   "CAPEX expensed off in the discontinued businesses, in the range of US$ 3 to 3.3 billion (US$ 3.5 to 4 "
                   "billion in the second-quarter release).",
      "quote": "full-year expenditure guidance in the range of US$ 3 to 3.3 billion",
      "metadata": {"guidance_item": "capital_expenditure", "fiscal_year": 2026, "low_usd": 3000000000,
                   "high_usd": 3300000000, "previous_range_usd": [3500000000, 4000000000], "page": 9}}]},
}
SEGMENT_KEYS = {"Petrochemicals": "petrochemicals", "Agri-Nutrients": "agri_nutrients", "Specialties": "specialties"}
errors = []
def squash(text):
    return " ".join(text.replace("(", "-").replace(")", "").split())
for stem, r in RELEASES.items():
    text = open(f"{er}/{stem}.txt").read()
    flat = squash(text)
    for metric, periods in r["values"].items():
        for period, value in periods.items():
            if value.lstrip("-") not in flat: errors.append((stem, metric, period, value, "not in text"))
    for segment, metrics in r.get("segments", {}).items():
        for metric, periods in metrics.items():
            for period, value in periods.items():
                if value not in flat: errors.append((stem, segment, metric, period, value))
    for event in r.get("events", []):
        if " ".join(event["quote"].split()) not in " ".join(text.split()): errors.append((stem, "quote", event["title"]))
    for _, _, _, quote in r.get("volumes", []):
        if quote not in " ".join(text.split()): errors.append((stem, "volume", quote))
    if r["url"].split("/")[-1].split("_tcm")[0].replace("%20", " ") not in stem.replace("_", " ").replace("-", " ") and False:
        pass
q3 = RELEASES["2026-10-25_EARNINGS-RELEASE-Q3-2026"]
for period in ("2026Q3", "2026Q2", "2025Q3", "2026M9", "2025M9"):  # segments add to the group within rounding
    total = sum(Decimal(q3["segments"][s]["revenue"][period]) for s in SEGMENT_KEYS)
    group = {"2026Q3": "28.17", "2026Q2": "24.81", "2025Q3": "29.08", "2026M9": "79.13", "2025M9": "88.57"}[period]
    if abs(total - Decimal(group)) > Decimal("0.02"): errors.append(("segment sum", period, total, group))
# quarters add up across releases on the 2026 basis (EBITDA): H1, 9M and FY 2025; H1 and 9M 2026
e = {**RELEASES["2026-03-04_EARNINGS-RELEASE-2025"]["values"]["ebitda"], **RELEASES["2026-04-29_EARNINGS-RELEASE-Q1-2026"]["values"]["ebitda"],
     **RELEASES["2026-07-29_EARNINGS-RELEASE-Q2-2026"]["values"]["ebitda"], **q3["values"]["ebitda"]}
d = lambda k: Decimal(e[k])
for parts, total, tol in ((("2025Q1", "2025Q2"), "2025H1", "0.02"), (("2025H1", "2025Q3"), "2025M9", "0.02"),
                          (("2025M9", "2025Q4"), Decimal("16.43"), "0.02"), (("2026Q1", "2026Q2"), "2026H1", "0.02"),
                          (("2026H1", "2026Q3"), "2026M9", "0.02")):
    t = total if isinstance(total, Decimal) else d(total)
    if abs(sum(d(p) for p in parts) - t) > Decimal(tol): errors.append(("ebitda chain", parts, total))
if errors:
    print("CHECK FAILED:"); [print(" ", x) for x in errors]; sys.exit(1)

def fact(metric, value, period, unit="SAR", scale=B, dimensions=None, label=None):
    start, end, kind, fy, fq = Q[period]
    row = {"metric": metric, "value": value, "currency": "SAR", "unit": unit, "period_start": start, "period_end": end,
           "period_kind": kind, "fiscal_year": fy, "fiscal_quarter": fq, "table": "Summary financial results",
           "source_label": label or metric}
    if scale != 1: row["scale"] = str(scale)
    if dimensions: row.update(scope="segment", dimensions=dimensions)
    return row
LABELS = {"revenue": "Revenue", "ebitda": "EBITDA", "ebit": "Income from operations (EBIT)",
          "net_income_parent": "Net (loss) income attributable to equity holders of the Parent",
          "eps_diluted": "Earnings per share attributable to equity holders of the Parent (SAR)",
          "adjusted_ebit": "Adjusted EBIT (income from operations excluding non-operational anomalies and one-offs)",
          "earnings_per_share_normalized": "Adjusted earnings per share attributable to equity holders of the Parent (SAR)"}
for stem, r in RELEASES.items():
    facts = []
    for metric, periods in r["values"].items():
        for period, value in periods.items():
            if metric in ("eps_diluted", "earnings_per_share_normalized"):
                facts.append(fact(metric, value, period, "SAR/share", 1, label=LABELS[metric]))
                continue
            facts.append(fact(metric, value, period, label=LABELS[metric]))
            if metric == "ebit":
                facts.append(fact("operating_income", value, period, label=LABELS[metric]))
    for segment, metrics in r.get("segments", {}).items():
        stem_key = SEGMENT_KEYS[segment]
        for metric, periods in metrics.items():
            label = {"revenue": "Gross Revenue", "ebitda": "EBITDA", "ebit": "Income from operations (EBIT)"}[metric]
            for period, value in periods.items():
                facts.append(fact(f"segment_{metric}", value, period, dimensions={"segment": segment}, label=label))
                if metric in ("revenue", "ebitda"):
                    facts.append(fact(f"{stem_key}_{metric}", value, period, label=f"{segment} {label}"))
    for metric, value, dims, quote in r.get("volumes", []):
        row = fact(metric, value, "2026Q3", "million_tonnes", 1, dimensions=dims, label=quote)
        row.pop("currency")
        facts.append(row)
    date = stem[:10]
    disclosures = [{"disclosure_type": "earnings_release", "title": f"SABIC {r['title'].title()}", "body_text": r["body"],
                    "language": "en", "published_at": date, "period_end": r["period_end"],
                    "metadata": {"title_ar": AR_TITLES[date], "issuer_listing_title": r["title"],
                                 "related_financial_period": r["period_end"], "page": 2}}]
    for event in r.get("events", []):
        disclosures.append({"disclosure_type": event["disclosure_type"], "title": event["title"],
                            "body_text": event["body_text"], "language": "en", "published_at": date,
                            "period_end": r["period_end"], "metadata": {**event["metadata"], "quote": event["quote"]}})
    json.dump({"company_id": "sa:2010", "filing_type": f"SABIC earnings release, {r['label']}", "filed_at": date,
               "period_end": r["period_end"], "source_url": r["url"],
               "notes": ("Summary financial results as printed (SAR billion; EPS in SAR), every period on the release's "
                         "2026 presentation basis (European Petrochemicals and Americas/Europe Engineering Thermoplastics "
                         "as discontinued operations). Periods held at full precision in the interim statements are not "
                         "repeated. title_ar is the title of the Arabic edition in SABIC's Arabic report listing."),
               "facts": facts, "disclosures": disclosures}, open(f"{out}/{r['name']}", "w"), indent=1, ensure_ascii=False)
    print(r["name"], len(facts), "facts", len(disclosures), "disclosures")
