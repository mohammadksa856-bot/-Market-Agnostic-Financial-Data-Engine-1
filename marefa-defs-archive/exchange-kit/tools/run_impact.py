"""engine_impact from this kit's contract_compare, run inside any engine checkout (PYTHONPATH=src).
usage: python3 run_impact.py BEFORE.sqlite3 AFTER.sqlite3 LABEL"""
import importlib.util, json, sys
from pathlib import Path

import finengine  # noqa: F401  (the checkout's package, so the kit module resolves its evaluator)

spec = importlib.util.spec_from_file_location("finengine.contract_compare", Path(__file__).resolve().parent / "contract_compare.py")
module = importlib.util.module_from_spec(spec); sys.modules["finengine.contract_compare"] = module; spec.loader.exec_module(module)
print(json.dumps(module.engine_impact(sys.argv[1], sys.argv[2], label=sys.argv[3]), indent=1))
