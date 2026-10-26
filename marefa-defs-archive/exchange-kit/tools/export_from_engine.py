"""Export a contract bundle from any engine checkout, using this kit's contract_compare module.

usage (run from the engine checkout, PYTHONPATH=src):
  python3 export_from_engine.py DB COMPANY_ID OUT LABEL [ENGINE_SHA]
The kit module is loaded as finengine.contract_compare so it uses that checkout's evaluator; the
checkout itself is not modified.
"""
import importlib.util, json, sys
from pathlib import Path

import finengine
from finengine.database import Database

spec = importlib.util.spec_from_file_location("finengine.contract_compare",
                                              Path(__file__).resolve().parent / "contract_compare.py")
module = importlib.util.module_from_spec(spec)
sys.modules["finengine.contract_compare"] = module
spec.loader.exec_module(module)

db_path, company_id, out, label = sys.argv[1:5]
db = Database(db_path)
try:
    bundle = module.export_bundle(db, company_id, label=label, engine_sha=sys.argv[5] if len(sys.argv) > 5 else "")
finally:
    db.close()
Path(out).write_text(json.dumps(bundle, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"out": out, "engine_total_score": bundle["engine_total_score"], "records": len(bundle["records"])}))
