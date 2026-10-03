"""Batch2-E: manifests whose filed_at precedes the publication timestamp embedded in a Saudi Exchange fsPdf URL."""
import json, glob, re, os, sys
root = sys.argv[1] if len(sys.argv) > 1 else "data/imports"
n = 0; bad = []
for p in sorted(glob.glob(os.path.join(root, "*.json"))):
    try: d = json.load(open(p, encoding="utf8"))
    except Exception: continue
    if not isinstance(d, dict) or "filed_at" not in d: continue
    m = re.search(r"/fsPdf/\d+_\d+_(\d{4}-\d{2}-\d{2})_", d.get("source_url", ""))
    if m:
        n += 1
        if str(d["filed_at"])[:10] < m.group(1): bad.append((os.path.basename(p), d["filed_at"], m.group(1)))
print(json.dumps({"checked": n, "filed_before_publication": len(bad), "rows": bad}, indent=1))
