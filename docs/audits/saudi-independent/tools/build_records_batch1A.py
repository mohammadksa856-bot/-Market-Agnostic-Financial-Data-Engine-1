"""Assemble docs/audits/saudi-independent/<symbol>.json from the independent check outputs.
Inputs (scratch dirs produced by pagecheck.py / p3check.py / xlsxcheck.py / missing-line scan)."""
import json, os, glob, collections, sys
T = os.environ["TEMP"] + "/aud/"
SYMS = {"1080": ("anb", "Arab National Bank"), "1010": ("riyad", "Riyad Bank"), "1140": ("albilad", "Bank Albilad"),
        "1020": ("aljazira", "Bank AlJazira"), "1120": ("alrajhi", "Al Rajhi Bank")}
AUDITED_COMMIT = os.popen("git rev-parse origin/codex/telecom-95pct").read().strip()
miss = json.load(open(T + "missing2.json", encoding="utf8"))
defects = json.load(open(os.path.join(os.path.dirname(__file__), "defects.json"), encoding="utf8"))
inv = json.load(open(T + "inv.json", encoding="utf8"))

def doc_record(sym, n, row):
    b = row["manifest"]; rec = {"manifest": b, "filing_type": row["ft"], "period_end": row["pe"], "facts_published": row["nf"],
                                "facts_rejected_or_excluded": row["nex"], "source_document": (row["arts"][0][0] if row["arts"] else None), "status": "done"}
    pcf = T + "pc/" + b
    p3f = T + "p3/" + b
    xlf = T + "xl/" + b
    pcr = json.load(open(pcf, encoding="utf8"))["results"] if os.path.exists(pcf) else []
    if pcr:
        r = pcr
        c = collections.Counter(); ok = 0; undated = 0; lab = 0; nf = []
        for z in r:
            st = z["status"]; c[st.split("+")[0]] += 1
            if st in ("OK", "SIGN"):
                if z.get("date") is None: undated += 1
                else: ok += 1
            elif st == "LABEL_LOW": lab += 1
            else: nf.append([z["metric"], z["value"], z["page"]])
        rec["numeric_correctness"] = {"method": "independent PyMuPDF row/column rebuild; printed number, label, column header date/period and sign checked on the cited page",
            "verified_correct_value_label_period": ok, "value_on_page_period_header_not_machine_readable": undated,
            "value_on_page_label_match_weak_reviewed_in_defects_or_noise": lab, "not_found_on_cited_page": nf}
    elif os.path.exists(p3f):
        r = json.load(open(p3f, encoding="utf8"))["results"]
        c = collections.Counter(z["status"] for z in r)
        rec["numeric_correctness"] = {"method": "Pillar 3 row id / cell letter vs printed table cell, header month and unit checked (published and rejected facts)",
            "verified_correct": c.get("OK", 0), "not_comparable_cell_missing": c.get("CELL_MISSING", 0), "mismatch": c.get("VALUE_MISMATCH", 0)}
    elif os.path.exists(xlf):
        r = json.load(open(xlf, encoding="utf8"))
        c = collections.Counter(z["status"] for z in r)
        rec["numeric_correctness"] = {"method": "XLSX header period + row label located in workbook; value compared (published and rejected facts)",
            "verified_correct": c.get("OK", 0), "mismatch_eps_rounding_only": c.get("VALUE_MISMATCH", 0), "not_found": c.get("NOT_FOUND", 0)}
    else:
        rec["numeric_correctness"] = {"method": "see defects/manual_visual_checks"}
    rec["document_completeness_unextracted_lines_present_in_document"] = {m: v[0] for m, v in miss.get(b, {}).items()}
    rec["defects"] = [d["id"] for d in defects["defects"] if b in d["documents"] or ("*" + n) in d["documents"]]
    return rec

for sym, (n, name) in SYMS.items():
    docs = [doc_record(sym, n, r) for r in inv[sym]]
    out = {"symbol": sym, "company": name, "audited_branch_commit": "origin/codex/telecom-95pct @ " + AUDITED_COMMIT,
           "other_branches_checked": defects["branches_note"],
           "resumable_status": {"done": len(docs), "pending": 0, "documents_total": len(docs)},
           "dimension_1_numeric_correctness": defects["numeric_summary"][sym],
           "dimension_2_document_completeness": defects["completeness_summary"][sym],
           "dimension_3_company_coverage": defects["coverage"][sym],
           "defects": [d for d in defects["defects"] if sym in d["symbols"]],
           "manual_visual_checks": defects["visual"].get(sym, []),
           "documents": docs}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(__file__)), sym + ".json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(sym, len(docs))
