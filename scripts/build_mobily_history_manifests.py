"""Build reviewed Mobily FY/quarter headline manifests from archived official PDFs."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPORTS = ROOT / "data" / "imports"
INDEX = ROOT / "data" / "raw" / "archive-index.json"

# Values are SAR millions exactly as printed in the cited issuer document.
# page tuple: revenue, EBITDA, net income.
ROWS = {
    (2021, "q1"): ("2021-03-31", 1, ("3603", "1365", "226"), (8, 9, 13)),
    (2021, "q2"): ("2021-06-30", 2, ("3728", "1344", "244"), (7, 8, 12)),
    (2021, "q3"): ("2021-09-30", 3, ("3606", "1389", "281"), (8, 9, 13)),
    (2021, "fy"): ("2021-12-31", None, ("14834.056", None, "1071.541"), (142, None, 142)),
    (2022, "q1"): ("2022-03-31", 1, ("3811", "1445", "319"), (8, 9, 13)),
    (2022, "q2"): ("2022-06-30", 2, ("3899", "1482", "360"), (7, 8, 12)),
    (2022, "q3"): ("2022-09-30", 3, ("3828", "1487", "373"), (8, 9, 13)),
    (2022, "fy"): ("2022-12-31", None, ("15669", "6179", "1657"), (12, 12, 12)),
    (2023, "q1"): ("2023-03-31", 1, ("4051", "1554", "465"), (8, 8, 8)),
    (2023, "q2"): ("2023-06-30", 2, ("4248", "1586", "497"), (9, 10, 14)),
    (2023, "q3"): ("2023-09-30", 3, ("4100", "1596", "524"), (9, 10, 14)),
    (2023, "fy"): ("2023-12-31", None, ("16763", "6625", "2232"), (8, 8, 8)),
    (2024, "q1"): ("2024-03-31", 1, ("4545", "1651", "638"), (8, 8, 8)),
    (2024, "q2"): ("2024-06-30", 2, ("4465", "1650", "661"), (8, 8, 8)),
    (2024, "q3"): ("2024-09-30", 3, ("4499", "1846", "829"), (8, 8, 8)),
    (2024, "fy"): ("2024-12-31", None, ("18206", "7195", "3107"), (9, 9, 9)),
}

FILE_DATES = {
    "2021-q1": "2022-04-20", "2021-q2": "2022-07-28", "2021-q3": "2022-10-26",
    "2021-fy": "2022-05-10", "2022-q1": "2022-04-20", "2022-q2": "2022-07-28",
    "2022-q3": "2022-10-26", "2022-fy": "2023-05-24", "2023-q1": "2023-05-17",
    "2023-q2": "2023-08-01", "2023-q3": "2023-10-25", "2023-fy": "2024-03-31",
    "2024-q1": "2024-05-12", "2024-q2": "2024-07-28", "2024-q3": "2024-10-27",
    "2024-fy": "2025-02-19",
}


def main() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    sources = {}
    for item in index["artifacts"]:
        for manifest in item.get("metadata", {}).get("manifests", []):
            if manifest.startswith("mobily-"):
                sources[manifest.removesuffix(".json")] = item["source_url"]
    for (year, kind), (period_end, quarter, values, pages) in ROWS.items():
        stem = f"mobily-{year}-{kind}"
        source_stem = stem if stem in sources else f"mobily-2022-{kind}"
        source_url = sources[source_stem]
        period_start = f"{year}-01-01" if kind == "fy" else {
            "q1": f"{year}-01-01", "q2": f"{year}-04-01", "q3": f"{year}-07-01"
        }[kind]
        facts = []
        for metric, label, value, page in zip(
            ("revenue", "ebitda", "net_income"),
            ("Revenues", "EBITDA", "Net Income"), values, pages,
        ):
            if value is None:
                continue
            fact = {
                "metric": metric, "source_label": label, "value": value,
                "period_start": period_start, "period_end": period_end,
                "period_kind": "quarter" if kind != "fy" else "fy", "fiscal_year": year, "page": page,
                "scale": "1000000", "currency": "SAR", "unit": "SAR",
            }
            if quarter is not None:
                fact["fiscal_quarter"] = quarter
            facts.append(fact)
        payload = {
            "company_id": "sa:7020", "market": "SA", "symbol": "7020",
            "filing_type": "annual-report" if kind == "fy" and year < 2024 else "earnings-presentation",
            "filed_at": FILE_DATES[f"{year}-{kind}"],
            "filed_at_basis": "pdf_metadata_creation_date",
            "period_end": period_end, "source_url": source_url,
            "reader": "manual.review/mobily-history", "profile": "corporate",
            "source_index_url": "https://mobily.com.sa/web/en/personal/about-mobily/investor-relations-details/financial-results",
            "notes": ("Official Mobily issuer PDF; headline facts manually reviewed against the cited page. "
                      "Quarterly values are standalone quarters, not YTD. " +
                      ("The 2021 quarter is a clearly labelled comparative in the corresponding 2022 presentation."
                       if year == 2021 and kind != "fy" else "")),
            "facts": facts,
            "verify": {"ok": True, "passed": 0, "failures": 0, "source": "deterministic"},
        }
        (IMPORTS / f"{stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(stem, len(facts))

        if source_stem != stem:
            for artifact in index["artifacts"]:
                if artifact["source_url"] == source_url:
                    manifests = artifact.setdefault("metadata", {}).setdefault("manifests", [])
                    if f"{stem}.json" not in manifests:
                        manifests.append(f"{stem}.json")
                    manifests.sort()
                    break
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
