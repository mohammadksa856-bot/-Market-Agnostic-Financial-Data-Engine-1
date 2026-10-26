"""Attribute the AR2025 five-year table's 2021-2023 continuing-operations lines to the filings they reproduce.

The table states "All numbers presented above are based on the published financial statements, including any
restatements of prior periods", and its footnote gives a different discontinued-operations basis per year
(2025/2024: European businesses; 2024-2022: Hadeed; 2021: none). Each annotated figure must equal, at the table's
precision (SAR bn, 2 decimals), the exact figure in the named filing; nothing else in the manifest changes.
Usage: annotate_five_year_origin.py <five-year manifest> <dir with sabic-*-fy-statements/earnings-release manifests>"""
import json, sys
from decimal import Decimal
path, built = sys.argv[1:3]
manifest = json.load(open(path))
# (metric, fiscal year) -> manifest holding the figure as published in the filing the table reproduces
ORIGIN = {("revenue", 2021): "sabic-2022-fy-statements.json", ("ebit", 2021): "sabic-2022-fy-statements.json",
          ("income_taxes_and_zakat", 2021): "sabic-2022-fy-statements.json",
          ("ebitda", 2021): "sabic-2022-fy-earnings-release.json",
          ("revenue", 2022): "sabic-2023-fy-statements.json", ("ebit", 2022): "sabic-2023-fy-statements.json",
          ("income_taxes_and_zakat", 2022): "sabic-2023-fy-statements.json",
          ("ebitda", 2022): "sabic-2023-fy-earnings-release.json",
          ("revenue", 2023): "sabic-2023-fy-statements.json", ("ebit", 2023): "sabic-2023-fy-statements.json",
          ("income_taxes_and_zakat", 2023): "sabic-2023-fy-statements.json",
          ("ebitda", 2023): "sabic-2023-fy-earnings-release.json"}
done = 0
lines = open(path).read().split("\n")
for i, line in enumerate(lines):
    stripped = line.strip().rstrip(",")
    if not stripped.startswith('{"metric"'):
        continue
    fact = json.loads(stripped)
    key = (fact["metric"], fact["fiscal_year"])
    if key not in ORIGIN or fact.get("dimensions"):
        continue
    origin = json.load(open(f"{built}/{ORIGIN[key]}"))
    exact = next(f for f in origin["facts"] if (f["metric"], f["fiscal_year"]) == key)
    exact_value = Decimal(str(exact["value"])) * Decimal(str(exact.get("scale", 1)))
    printed = Decimal(fact["value"]) * Decimal(fact["scale"])
    if (exact_value / Decimal(10) ** 9).quantize(Decimal("0.01")) != printed / Decimal(10) ** 9:
        sys.exit(f"{key}: table {printed} does not round from {ORIGIN[key]} {exact_value}")
    tail = "," if line.rstrip().endswith(",") else ""
    body = line.rstrip().rstrip(",")
    published = json.dumps({"source_url": origin["source_url"], "filed_at": origin["filed_at"]}, separators=(",", ":"))
    lines[i] = body[:-1] + ',"published_in":' + published + "}" + tail
    done += 1
assert done == len(ORIGIN), done
json.loads("\n".join(lines))
open(path, "w").write("\n".join(lines))
print("annotated", done)
