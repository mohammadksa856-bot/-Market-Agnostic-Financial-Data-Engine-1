"""rec.py <symbol>: writes raw-B012/<symbol>.json from transcripts/<symbol>.json, the raw-coverage inventory and tools/spec_<symbol>.json.

Every audited document's SHA-256 is recomputed from the raw file (read-only) and must equal the inventory value. Collector-label correctness is
derived from the page-derived period (not asserted). Inventory files that are not value-read are listed with what was identified, or an explicit
'not opened' note, so nothing is silently dropped."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pg

OUT = HERE.parent
TR = OUT / "transcripts"

SLOT = {"FY": "FY", "H1": "H1", "9M": "9M", "Q1": "Q1"}


def label_status(fy, slot, pe, pt):
    py = int(pe[:4])
    if fy is None:
        return False, "no fiscal year in collector label"
    if pt == "FY":
        if slot == "FY" and fy == py + 1:
            return True, f"collector FY{fy} holds FY{py} (publication-year label, FY n+1)"
        if slot == "FY" and fy == py:
            return True, "label matches the fiscal year"
        return False, f"WRONG: collector {fy}|{slot} holds the year ended {pe}"
    if fy == py and slot == SLOT.get(pt):
        return True, "label matches the period"
    return False, f"WRONG: collector {fy}|{slot} holds the {pt} period ended {pe}"


def build(sym):
    spec = json.loads((HERE / f"spec_{sym}.json").read_text(encoding="utf8"))
    t = json.loads((TR / f"{sym}.json").read_text(encoding="utf8"))
    inv = json.loads((Path(pg.INV) / f"{sym}.json").read_text(encoding="utf8"))
    docs, used = [], set()
    for d in t["docs"]:
        m = [f for f in inv["files"] if f["sha256"].startswith(d["sha256_prefix"])]
        assert len(m) == 1, (sym, d["sha256_prefix"])
        m = m[0]
        raw = Path(pg.RAW) / m["relpath"].replace("/", "\\")
        assert pg.sha(str(raw)) == m["sha256"], ("sha mismatch", d["sha256_prefix"])
        used.add(m["sha256"])
        ok, note = label_status(m["fiscal_year"], m["period_slot"], d["period_end"], d["period_type"])
        e = {"sha256": m["sha256"], "actual_period": f"{d['period_type']} ended {d['period_end']}", "label_ok": ok, "label_note": note,
             "pdf_pages": d["pages"], "printed_pages": d["printed_pages"], "units": t.get("unit", ""), "reading": d["reading"],
             "values_read": [b for b in ("bs", "is", "is_q", "cf") if b in d], "relpath": m["relpath"],
             "collector_label": f"{m['fiscal_year']}|{m['period_slot']}", "inventory_file_class": m["file_class"], "pdf_total_pages": m["pages"]}
        if d.get("restatements"):
            e["declared_restatements"] = d["restatements"]
        if d.get("tol"):
            e["identity_tolerance"] = {"tol": d["tol"], "reason": d.get("tol_reason")}
        if d.get("scale", 1) != 1:
            e["scale_to_full_units"] = d["scale"]
        if d.get("doc_note"):
            e["note"] = d["doc_note"]
        docs.append(e)
    docs.sort(key=lambda e: (e["actual_period"].split("ended ")[1], e["actual_period"]))
    ident = spec.get("identified", {})
    others = []
    for f in sorted(inv["files"], key=lambda f: (f["fiscal_year"] or 0, f["period_slot"] or "", f["sha256"])):
        if f["sha256"] in used:
            continue
        row = {"sha256": f["sha256"], "collector_label": f"{f['fiscal_year']}|{f['period_slot']}", "inventory_file_class": f["file_class"],
               "pdf_total_pages": f["pages"], "language": f.get("language")}
        pre = next((p for p in ident if f["sha256"].startswith(p)), None)
        if pre:
            row["actual_period"], row["note"] = ident[pre]
        else:
            row["actual_period"] = "not identified"
            row["note"] = "not opened for this audit; period and content unverified"
        others.append(row)
    verified = sorted({f"{d['period_end']} {d['period_type']}" for d in t["docs"]})
    dims = spec["dimensions"]
    dims["value_correctness"]["periods_verified_from_own_pages"] = verified
    rec = {
        "schema_version": 1, "symbol": sym, "name": t["name"],
        "audit": {"audited_on": "2026-10-04", "auditor": "Claude Sonnet 5.5 (independent, raw-B012)",
                  "scope": "raw collected files in C:/Users/Mohammed856/finengine-raw-odd (read-only); no network, no data/**, no AWS/Supabase",
                  "method": spec["method"],
                  "tools": ["tools/pg.py", "tools/survey.py", "tools/stm.py", "tools/ext.py", "tools/auto.py", "tools/sheet.py", "tools/tr.py", "tools/rec.py",
                            "tools/check_transcripts.py", f"transcripts/{sym}.json", f"tools/spec_{sym}.json"]},
        "dimensions": dims, "documents": docs, "files_not_audited_for_values": others,
        "defects": spec["defects"], "unread_items": spec["unread_items"], "conclusion": spec["conclusion"],
    }
    (OUT / f"{sym}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    print(sym, "documents", len(docs), "not value-read", len(others), "sha verified; label_not_ok", [d["collector_label"] for d in docs if not d["label_ok"]])


if __name__ == "__main__":
    build(sys.argv[1])
