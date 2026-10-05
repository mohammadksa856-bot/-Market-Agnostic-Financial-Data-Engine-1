"""expand_sha.py <symbol>: replace every "sha256" prefix (8+ hex chars) in raw-B020/<symbol>.json documents[] with the full SHA-256 from the
raw-coverage inventory, and recompute it from the raw file to prove it. Read-only on raw files; rewrites only the audit JSON."""
import json
import sys
from pathlib import Path

import pg

sym = sys.argv[1]
path = Path(__file__).resolve().parent.parent / f"{sym}.json"
data = json.loads(path.read_text(encoding="utf8"))
inv = json.loads((Path(pg.INV) / f"{sym}.json").read_text(encoding="utf8"))
for d in data["documents"]:
    pre = d["sha256"]
    m = [f for f in inv["files"] if f["sha256"].startswith(pre)]
    assert len(m) == 1, (pre, len(m))
    full = m[0]["sha256"]
    raw = Path(pg.RAW) / m[0]["relpath"].replace("/", "\\")
    assert pg.sha(str(raw)) == full, ("sha mismatch", pre)
    d["sha256"] = full
    d["relpath"] = m[0]["relpath"]
    d["collector_label"] = f"{m[0]['fiscal_year']}|{m[0]['period_slot']}"
    d["inventory_file_class"] = m[0]["file_class"]
    d["pdf_total_pages"] = m[0]["pages"]
path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print(sym, "documents", len(data["documents"]), "sha verified")
