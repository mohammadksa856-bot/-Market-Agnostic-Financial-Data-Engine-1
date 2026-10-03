"""mk.py: helper to assemble a per-company audit record. Expands sha prefixes to full SHA-256 (verified against the raw file by recomputing the hash) and fills inventory facts (collector label, file class, pages)."""
import json, os, pg
def expand(sym, prefix):
    meta, path = pg.find(sym, prefix)
    assert pg.sha(path) == meta["sha256"], prefix
    return meta
def doc(sym, prefix, **kw):
    m = expand(sym, prefix)
    d = {"sha256": m["sha256"], "relpath": m["relpath"], "collector_label": f'{m["fiscal_year"]}|{m["period_slot"]}',
         "inventory_class": m["file_class"], "pdf_pages_total": m["pages"]}
    d.update(kw)
    return d
def write(sym, rec):
    out = os.path.join(os.path.dirname(__file__), "..", f"{sym}.json")
    with open(out, "w", encoding="utf8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print("wrote", os.path.normpath(out))
