"""setdone.py <symbol> ...: marks symbols done in progress.json."""
import json, sys
from pathlib import Path
p = Path(__file__).resolve().parent.parent / "progress.json"
d = json.loads(p.read_text()) if p.exists() else {"batch": "B016", "status": {s: "pending" for s in ["8313", "8120", "8180", "8100", "8170"]}, "note": ""}
for s in sys.argv[1:]:
    d["status"][s] = "done"
d["note"] = "audited symbols are done; none claimed complete (see unread_items)"
p.write_text(json.dumps(d, indent=1) + "\n")
