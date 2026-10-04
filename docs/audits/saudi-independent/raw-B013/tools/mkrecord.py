"""mkrecord.build(spec): writes raw-B013/<symbol>.json from a per-company spec.

spec keys: symbol, name, method, documents (list of dicts with sha prefix + page-derived fields), identified (prefix -> actual_period/note for
files not value-read), dimensions, defects, unread_items, conclusion.
Every document sha256 prefix is expanded to the full SHA-256 from the raw-coverage inventory and recomputed from the raw file (read-only).
Inventory files that are neither in documents nor in identified are listed with an explicit 'not opened' note, so nothing is silently dropped.
"""
import json
from pathlib import Path

import pg

HERE = Path(__file__).resolve().parent
OUT = HERE.parent


def build(spec):
    sym = spec["symbol"]
    inv = json.loads((Path(pg.INV) / f"{sym}.json").read_text(encoding="utf8"))
    by = {}

    def find(pre):
        m = [f for f in inv["files"] if f["sha256"].startswith(pre)]
        assert len(m) == 1, (sym, pre, len(m))
        return m[0]

    docs = []
    used = set()
    for d in spec["documents"]:
        m = find(d["sha256"])
        raw = Path(pg.RAW) / m["relpath"].replace("/", "\\")
        assert pg.sha(str(raw)) == m["sha256"], ("sha mismatch", d["sha256"])
        used.add(m["sha256"])
        e = dict(d)
        e["sha256"] = m["sha256"]
        e["relpath"] = m["relpath"]
        e["collector_label"] = f"{m['fiscal_year']}|{m['period_slot']}"
        e["inventory_file_class"] = m["file_class"]
        e["pdf_total_pages"] = m["pages"]
        docs.append(e)
    others = []
    ident = spec.get("identified", {})
    for f in sorted(inv["files"], key=lambda f: (f["fiscal_year"] or 0, f["period_slot"] or "", f["sha256"])):
        if f["sha256"] in used:
            continue
        pre = next((p for p in ident if f["sha256"].startswith(p)), None)
        row = {"sha256": f["sha256"], "collector_label": f"{f['fiscal_year']}|{f['period_slot']}", "inventory_file_class": f["file_class"],
               "pdf_total_pages": f["pages"], "language": f.get("language")}
        if pre:
            row["actual_period"], row["note"] = ident[pre]
        else:
            row["actual_period"] = "not identified"
            row["note"] = "not opened for this audit; period and content unverified"
        others.append(row)
    rec = {
        "schema_version": 1,
        "symbol": sym,
        "name": spec["name"],
        "audit": {
            "audited_on": "2026-10-04",
            "auditor": "Claude Sonnet 5.5 (independent, raw-B013)",
            "scope": "raw collected files in C:/Users/Mohammed856/finengine-raw-odd (read-only); no network, no data/**, no AWS/Supabase",
            "method": spec["method"],
            "tools": ["tools/pg.py", "tools/rows.py", "tools/head.py", "tools/survey.py", "tools/tl.py", "tools/mkrecord.py",
                      "tools/check_transcripts.py", f"transcripts/{sym}.json"],
        },
        "dimensions": spec["dimensions"],
        "documents": docs,
        "files_not_audited_for_values": others,
        "defects": spec["defects"],
        "unread_items": spec["unread_items"],
        "conclusion": spec["conclusion"],
    }
    (OUT / f"{sym}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    print(sym, "documents", len(docs), "not value-read", len(others), "sha verified")
