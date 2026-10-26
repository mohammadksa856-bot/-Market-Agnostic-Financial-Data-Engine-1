"""Dry run of the Codex intake: synthesize minimal snapshots from our bundle, then validate and compare via the CLI."""
import copy, json, subprocess, sys
from pathlib import Path

ours, engine, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
bundle = json.loads(ours.read_text())
closed = [r for r in bundle["records"] if r["status"] == "closed" and r["observations"]
          and r.get("storage_domain") == "data_points"]
missing = [r["key"] for r in bundle["records"] if r["status"] == "missing"]
snapshot = {"bundle_version": 1, "label": "codex-dryrun", "company_id": bundle["company_id"], "record_default": "missing",
            "contract": {"categories": [{"key": c["key"], "weight": c["weight"],
                                         **({"score_only": c["score_only"]} if "score_only" in c else {}),
                                         **({"not_applicable": True} if c.get("not_applicable") else {}),
                                         "fields": [f["key"] for f in c.get("fields", [])]}
                                        for c in bundle["contract"]["categories"]]},
            "records": []}
for record in closed[:-3]:                       # three of our closed keys are missing on the other side
    snapshot["records"].append({"key": record["key"], "status": "closed",
                                "observations": copy.deepcopy(record["observations"][:2])})
snapshot["records"][0]["observations"][0]["value"] = "1"   # one value conflict
for key in missing[:4]:                          # four keys closed only on the other side
    snapshot["records"].append({"key": key, "status": "closed", "observations": [
        {"period_kind": "fy", "period_start": "2025-01-01", "period_end": "2025-12-31", "value": "1", "unit": "SAR"}]})
snapshot["contract"]["categories"][0]["weight"] = str(float(snapshot["contract"]["categories"][0]["weight"]) + 1)
snapshot["contract"]["categories"][0]["fields"].append("codex_only_key")   # a key only the other contract has
broken = copy.deepcopy(snapshot); broken["bundle_version"] = 2
broken["records"].append({"key": "ghost", "status": "done"}); broken["records"][1]["observations"][0]["period_end"] = "2025/12/31"
for name, payload in (("codex-dryrun-snapshot.json", snapshot), ("codex-dryrun-broken.json", broken)):
    (out / name).write_text(json.dumps(payload, indent=1))
def cli(*args):
    run = subprocess.run([sys.executable, "-m", "finengine", "--db", "/dev/null", *args], cwd=engine,
                         capture_output=True, text=True, env={"PYTHONPATH": str(engine / "src"), "PYTHONDONTWRITEBYTECODE": "1"})
    return run.returncode, json.loads(run.stdout)
code, valid = cli("contract-validate", str(out / "codex-dryrun-snapshot.json"))
print("validate snapshot:", code, valid["status"], len(valid["errors"]), "errors,", len(valid["warnings"]), "warnings")
code, bad = cli("contract-validate", str(out / "codex-dryrun-broken.json"))
print("validate broken:", code, bad["status"], *bad["errors"], sep="\n  ")
code, refused = cli("contract-compare", str(ours), str(out / "codex-dryrun-broken.json"))
print("compare broken:", code, refused["status"], len(refused["errors"]), "errors")
code, result = cli("contract-compare", str(ours), str(out / "codex-dryrun-snapshot.json"))
(out / "codex-dryrun-compare.json").write_text(json.dumps(result, indent=1))
print("compare:", code, "only_in_b", result["keys"]["only_in_b"], "weight_diffs", result["weight_diffs"])
print("  conflicts", [(c["key"], c["type"]) for c in result["conflicts"]][:5], "not_comparable", len(result["not_comparable"]))
print("  definition_not_provided", len(result["definition_not_provided"]), "closure", result["closure"]["on_contract_a"])
print("  scores", {k: v[:7] for k, v in result["scores"].items()})
