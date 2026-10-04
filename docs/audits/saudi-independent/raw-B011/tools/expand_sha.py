"""expand_sha.py <symbol> <in.json> <out.json>: for each documents[].sha256_prefix add full sha256, relpath, size, pages and the inventory's own label/class,
verifying the prefix is unique in the inventory and the raw file's SHA-256 recomputes to the full hash (read-only)."""
import json, sys, os, pg
sym, src, dst = sys.argv[1:4]
inv = json.load(open(os.path.join(pg.INV, sym + ".json"), encoding="utf8"))
doc = json.load(open(src, encoding="utf8"))
for d in doc["documents"]:
    m, p = pg.find(sym, d["sha256_prefix"])
    assert pg.sha(p) == m["sha256"], d["sha256_prefix"]
    d["sha256"] = m["sha256"]; d["sha256_recomputed_ok"] = True
    d["relpath"] = m["relpath"]; d["size_bytes"] = m["size_bytes"]; d["pdf_pages_total"] = m["pages"]
    d["inventory_label"] = f'{m["fiscal_year"]}|{m["period_slot"]}'; d["inventory_class"] = m["file_class"]
    del d["sha256_prefix"]
json.dump(doc, open(dst, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("ok", len(doc["documents"]))
