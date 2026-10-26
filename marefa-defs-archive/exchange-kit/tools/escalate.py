"""Split comparison results into what needs a reviewer and what is only a coverage difference.

usage: python3 escalate.py LABEL=RESULT.json [LABEL=RESULT.json ...] > escalations.json
needs_review: value, unit/currency or period-start conflicts on keys both sides closed, definition
differences and weight differences. coverage_differences: periods one side holds and the other does
not. Items an engine correction touched are flagged; nothing is resolved here.
"""
import json, sys

needs_review, coverage = [], []
for argument in sys.argv[1:]:
    label, path = argument.split("=", 1)
    result = json.load(open(path))
    for item in result["conflicts"]:
        if item["type"] != "source_differs_same_value":
            needs_review.append({**item, "against": label})
    needs_review += [{"key": item["key"], "type": "definition", "difference": item, "against": label}
                     for item in result["definition_diffs"]]
    needs_review += [{"key": item["category"], "type": "weight", "difference": item, "against": label}
                     for item in result["weight_diffs"]]
    coverage += [{**item, "against": label} for item in result["period_differences"]]
print(json.dumps({"needs_review": {"count": len(needs_review), "items": needs_review},
                  "coverage_differences": {"count": len(coverage), "items": coverage},
                  "touched_by_engine_corrections": sorted({item["key"] for item in needs_review + coverage
                                                          if item.get("engine_corrections")})}, indent=1))
