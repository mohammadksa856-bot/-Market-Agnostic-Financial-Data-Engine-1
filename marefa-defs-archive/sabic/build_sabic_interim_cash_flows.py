"""SABIC cumulative interim cash flows (thousands of SAR) that the discrete-quarter derivation needs.

- Quarterly report 2025 Q2, statement of cash flows (text layer): six months 2024 comparative.
- Quarterly report 2025 Q3, statement of cash flows (page image; no text layer): nine months 2025 and 2024. Each
  figure must be an OCR word on the page, and net cash from operating activities must equal the printed subtotal plus
  interest received, less interest paid and zakat and income tax paid. The 2024 capex also appears in the text of
  Quarterly report 2024 Q3.
Usage: build_sabic_interim_cash_flows.py <src-dl/sabic> <out-dir>"""
import json, subprocess, sys
src, out = sys.argv[1:3]
idx = {l.split("\t")[0]: l.rstrip("\n").split("\t") for l in open(f"{src}/index.tsv")}
errors = []

def text(name, page=None):
    args = ["pdftotext", "-layout"] + (["-f", str(page), "-l", str(page)] if page else []) + [f"{src}/{name}", "-"]
    return " ".join(subprocess.run(args, capture_output=True, text=True).stdout.split())

q2 = "05-Quarterly_report_2025_Q2.pdf"
q2_text = text(q2)
for printed in ("3,352,070 2,846,642", "(3,835,417) (4,633,601)"):
    if printed not in q2_text: errors.append((q2, printed))

q3 = "04-Quarterly_report_2025_Q3.pdf"
ocr = json.load(open(f"{src}/{q3}.ocr.json"))
words = {w[4] for w in ocr["pages"]["7"]["words"]}  # 0-based index 7 = PDF page 8
NINE = {2025: dict(subtotal=11973564, received=1721953, paid=-1684131, tax=-1847336, ocf=10164050, capex=-6306850),
        2024: dict(subtotal=11860614, received=1109387, paid=-1440212, tax=-2128972, ocf=9400817, capex=-7265355)}
for year, v in NINE.items():
    for key, value in v.items():
        printed = f"({abs(value):,})" if value < 0 else f"{value:,}"
        if printed not in words: errors.append((q3, year, key, printed))
    if v["subtotal"] + v["received"] + v["paid"] + v["tax"] != v["ocf"]: errors.append((q3, year, "ocf bridge"))
if "7265355" not in text("08-Quarterly_Report_2024_Q3.pdf").replace(" ", "").replace(",", ""):
    errors.append(("Q3 2024 report", "capex 7,265,355"))
if errors:
    print("CHECK FAILED:"); [print(" ", e) for e in errors]; sys.exit(1)

def row(metric, value, year, quarter, page, label):
    return {"metric": metric, "value": value, "currency": "SAR", "unit": "SAR", "scale": 1000,
            "period_start": f"{year}-01-01", "period_end": f"{year}-{3 * quarter:02d}-{30 if quarter in (2, 3) else 31}",
            "period_kind": "ytd", "fiscal_year": year, "fiscal_quarter": quarter, "page": page,
            "table": "condensed consolidated interim statement of cash flows", "source_label": label}
OCF, CAPEX = "Net cash from operating activities", "Purchase of property, plant and equipment and intangible assets"
for name, facts, note in (
        (q2, [row("operating_cash_flow", 2846642, 2024, 2, 8, OCF), row("capex", -4633601, 2024, 2, 8, CAPEX)],
         "Six-month 2024 comparative; the 2025 column matches the comparative already filed from the 2026 report."),
        (q3, [row("operating_cash_flow", NINE[y]["ocf"], y, 3, 8, OCF) for y in NINE]
             + [row("capex", NINE[y]["capex"], y, 3, 8, CAPEX) for y in NINE],
         "Page image (no text layer): every figure is an OCR word on page 8, and net cash from operating activities "
         "equals the printed subtotal + interest received - interest paid - zakat and income tax paid.")):
    _, _, pub, title, url, sha, _ = idx[name]
    stem = "sabic-2025-q2-interim-cash-flows.json" if name == q2 else "sabic-2025-q3-interim-cash-flows.json"
    json.dump({"company_id": "sa:2010", "filing_type": f"{title} (SABIC investor relations) - statement of cash flows",
               "filed_at": pub, "period_end": facts[0]["period_end"] if name == q3 else "2025-06-30", "source_url": url,
               "notes": f"sha256 {sha}. {note} Cumulative figures; totals include discontinued operations.",
               "facts": facts}, open(f"{out}/{stem}", "w"), indent=1)
    print(stem, len(facts))
