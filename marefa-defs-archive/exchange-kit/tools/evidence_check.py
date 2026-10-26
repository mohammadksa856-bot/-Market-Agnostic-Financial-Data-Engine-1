"""Cross-check a special-source evidence file against a snapshot and our prior decisions.

usage: python3 evidence_check.py EVIDENCE.json SNAPSHOT.json [OUR_CLASSIFICATION.json] [--keys k1,k2,...]
The evidence format is read generically: every object naming a key (key / field_key / metric /
metric_key) is an evidence item. For each key: the evidence items with their source, page, period,
value and unit; the snapshot's status and observations; and our prior decision, if any. Items are
flagged when they lack a source URL, a locator (page/table/section) or a period, or when the
snapshot's value differs from the evidence value. Nothing is accepted here.
"""
import argparse, json
from pathlib import Path

KEY_FIELDS = ("key", "field_key", "metric", "metric_key")
SOURCE_FIELDS = ("source_url", "url", "evidence_source_url", "source")
LOCATOR_FIELDS = ("page", "table", "section", "locator", "sheet", "cell")

def items(node, trail=""):
    if isinstance(node, dict):
        key = next((node[f] for f in KEY_FIELDS if isinstance(node.get(f), str)), None)
        if key:
            yield key, node, trail
        for name, child in node.items():
            yield from items(child, f"{trail}/{name}")
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from items(child, f"{trail}[{index}]")

parser = argparse.ArgumentParser()
parser.add_argument("evidence"); parser.add_argument("snapshot"); parser.add_argument("classification", nargs="?")
parser.add_argument("--keys")
args = parser.parse_args()
evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
records = {r["key"]: r for r in snapshot.get("records", []) if isinstance(r, dict) and "key" in r}
decisions = {}
if args.classification:
    text = json.loads(Path(args.classification).read_text(encoding="utf-8"))
    for section, value in text.items():
        for _, node, _ in items(value):
            k = next((node[f] for f in KEY_FIELDS if isinstance(node.get(f), str)), None)
            decisions.setdefault(k, []).append({"section": section, **{x: node[x] for x in node if x != "key"}})
        if isinstance(value, list):
            for group in value:
                for k in group.get("keys", []) if isinstance(group, dict) else []:
                    decisions.setdefault(k, []).append({"section": section, "decision": group.get("decision")})
wanted = set(args.keys.split(",")) if args.keys else None
report = {}
for key, node, trail in items(evidence):
    if wanted and key not in wanted:
        continue
    flags = []
    if not any(node.get(f) for f in SOURCE_FIELDS): flags.append("no_source_url")
    if not any(node.get(f) not in (None, "") for f in LOCATOR_FIELDS): flags.append("no_locator")
    if not node.get("period_end") and not node.get("period"): flags.append("no_period")
    record = records.get(key)
    if record and "value" in node:
        values = {str(o.get("value")) for o in record.get("observations", [])}
        if values and str(node["value"]) not in values: flags.append("snapshot_value_differs_from_evidence")
    entry = report.setdefault(key, {"evidence": [], "snapshot": None, "our_prior_decision": decisions.get(key, [])})
    entry["evidence"].append({"at": trail, "flags": flags, **{f: node[f] for f in node if not isinstance(node[f], (dict, list))}})
    if record:
        entry["snapshot"] = {"status": record.get("status"), "observations": record.get("observations", [])[:4]}
print(json.dumps({"keys": len(report), "flagged_keys": sorted(k for k, v in report.items() if any(e["flags"] for e in v["evidence"])),
                  "items": report}, indent=1, ensure_ascii=False))
