"""setdone.py <symbol> <status>: update progress.json status for one company."""
import json
import sys
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "progress.json"
d = json.loads(p.read_text(encoding="utf8"))
d["status"][sys.argv[1]] = sys.argv[2]
p.write_text(json.dumps(d, indent=1) + "\n", encoding="utf8")
