"""Standalone snapshot validation and comparison (no engine install needed).

usage:
  python3 snapshot_tool.py validate SNAPSHOT.json
  python3 snapshot_tool.py compare A.json B.json [--tolerance 0.000001] [--out RESULT.json]
Exit code 2 means the snapshot is not a valid contract bundle; every problem is listed.
"""
import argparse, json, sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_compare import InvalidBundle, compare_bundles, load_bundle, normalize_bundle, validate_bundle  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("snapshot")
    compare = sub.add_parser("compare"); compare.add_argument("a"); compare.add_argument("b")
    compare.add_argument("--tolerance", default="0.000001"); compare.add_argument("--out")
    args = parser.parse_args()
    if args.cmd == "validate":
        try:
            snapshot = load_bundle(args.snapshot)
        except json.JSONDecodeError as error:
            print(json.dumps({"status": "invalid_json", "errors": [str(error)]}, indent=2)); return 2
        result = validate_bundle(normalize_bundle(snapshot) if isinstance(snapshot, dict) else snapshot)
        print(json.dumps({"status": "invalid_bundle" if result["errors"] else "valid", **result}, indent=2, ensure_ascii=False))
        return 2 if result["errors"] else 0
    try:
        result = compare_bundles(load_bundle(args.a), load_bundle(args.b), tolerance=Decimal(args.tolerance))
    except InvalidBundle as error:
        print(json.dumps({"status": "invalid_bundle", "errors": error.errors}, indent=2, ensure_ascii=False)); return 2
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    summary = {k: (len(v) if isinstance(v, list) else v) for k, v in result.items()
               if k in ("weight_diffs", "definition_diffs", "conflicts", "period_differences", "not_comparable",
                        "conflicted_keys", "conflicts_touched_by_engine_corrections")}
    print(json.dumps({"status": "compared", "keys": {k: len(v) for k, v in result["keys"].items()}, **summary,
                      "closure": result["closure"], "scores": result["scores"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
