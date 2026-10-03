"""Step 1 raw-coverage inventory for Saudi registry companies (read-only on raw files).

Usage (from this tools dir):
    python inventory.py run [--chunk 20] [--workers 18] [--max-chunks N]
Resumable: progress.json (one level up) lists finished symbols.
Writes one JSON per company to ../companies/<symbol>.json.
NOT a value check: nothing here asserts that any number in any file is correct.
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import date, timedelta
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
REPO = OUT.parents[3]
RAW = Path(os.environ.get("RAW_ROOT", "C:/Users/Mohammed856/finengine-raw-odd"))
TODAY = date(2026, 10, 3)
EXCLUDED = {
    "1050", "1060",  # explicitly excluded by the task
    # already audited (task list)
    "1080", "1010", "1140", "1020", "1120", "1150", "1030", "1180", "8010", "2222", "7020", "7010", "7030",
    "7040", "7203", "2010", "2082", "3010", "3030", "3050", "3002", "3003", "3005", "3020", "3040", "3060", "7202",
}
SLOT_ORDER = {"Q1": 1, "H1": 2, "9M": 3, "FY": 4}
SLOT_MONTHS = {"Q1": 3, "H1": 6, "9M": 9, "FY": 12}
sys.path.insert(0, str(HERE))
import pdfscan  # noqa: E402

NAME_STOP = set("""company co corp corporation group holding holdings saudi arabia arabian the for and of al el ltd limited
 national international industries industrial industry investment investments development trading services service
 insurance cooperative takaful reinsurance bank fund reit real estate traded unit sa ksa kingdom general joint stock""".split())


def load_registry():
    reg = json.load(open(REPO / "config/sa-market-registry.json", encoding="utf8"))
    return {r["symbol"]: r for r in reg}


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(RAW.resolve())).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


def disk_index():
    idx = defaultdict(list)  # hash -> [(symbol, relpath)]
    base = RAW / "archive/SA"
    for root, _, fs in os.walk(base):
        sym = Path(root).relative_to(base).parts[0] if Path(root) != base else ""
        for f in fs:
            h = f.rsplit(".", 1)[0]
            idx[h].append((sym, rel(Path(root) / f)))
    return idx


def load_manifests():
    """symbol -> hash -> {'assign': [...], 'sources': set}"""
    out = defaultdict(dict)
    for kind in ("se", "issuer"):
        for p in glob.glob(str(RAW / f"state/{kind}/*.json")):
            s = json.load(open(p, encoding="utf8"))
            for d in s.get("docs", []):
                e = out[s["symbol"]].setdefault(d["content_hash"], {"assign": [], "sources": set(), "in_final_state": True})
                e["assign"].append(d)
                e["sources"].add("state_" + kind)
    for line in open(RAW / "logs/documents.jsonl", encoding="utf8"):
        if not line.strip():
            continue
        d = json.loads(line)
        e = out[d["symbol"]].setdefault(d["content_hash"], {"assign": [], "sources": set(), "in_final_state": False})
        e["sources"].add("documents_jsonl")
        if not e["in_final_state"]:
            e["assign"].append(d)
    return out


def state_info(symbol):
    info = {}
    for kind in ("se", "issuer"):
        p = RAW / f"state/{kind}/{symbol}.json"
        if p.exists():
            s = json.load(open(p, encoding="utf8"))
            info[kind] = {k: s.get(k) for k in ("status", "attempts", "finished_at", "fy_end_month", "se", "issuer", "se_ok")}
            info[kind]["failures"] = [f.get("reason") for f in s.get("failures", [])]
            info[kind]["rejected_reasons"] = sorted({r.get("reason") for r in s.get("rejected", [])})
            info[kind]["expected"] = s.get("expected")
            info[kind]["unclassified_n"] = len(s.get("unclassified", []))
    return info


# ----------------------------------------------------------------- expected periods
def period_end(fy, slot, fym):
    """period end date for fiscal year `fy` (ending in month fym) and slot."""
    m = fym - 12 + SLOT_MONTHS[slot]  # months after fiscal start
    # fiscal year fy ends in month fym of calendar year fy (if fym<=12 convention used by collector)
    mm = fym - 12 + SLOT_MONTHS[slot]
    y = fy
    while mm <= 0:
        mm += 12
        y -= 1
    nxt = date(y + (mm == 12), mm % 12 + 1, 1)
    return nxt - timedelta(days=1)


def due(pe, slot):
    return pe + timedelta(days=(100 if slot == "FY" else 50))


def build_expected(symbol, st, doc_slots, fym):
    """Return dict key 'fy|slot' -> {period_end, basis} and metadata."""
    se_exp = {}
    for kind in ("se",):
        e = (st.get(kind) or {}).get("expected") or {}
        se_exp.update(e)
    keys = {}
    for k, pe in se_exp.items():
        keys[k] = {"period_end": pe, "basis": "saudi_exchange_announcement"}
    observed = set(keys)
    for (fy, sl) in doc_slots:
        observed.add(f"{fy}|{sl}")
    if not observed:
        return {}, {"first_period": None, "last_expected": None, "notes": ["no_anchor_periods"]}
    def ord_(k):
        y, s = k.split("|")
        return (int(y), SLOT_ORDER[s])
    first = min(observed, key=ord_)
    fy0, s0 = first.split("|")
    fy0 = int(fy0)
    # cadence per year from SE announcements
    cad = defaultdict(set)
    for k in se_exp:
        y, s = k.split("|")
        cad[int(y)].add(s)
    last_y = TODAY.year + 1
    default = {"Q1", "H1", "9M", "FY"}
    # Nomu / semi-annual cadence: use nearest SE-observed year
    result = {}
    for y in range(fy0, last_y + 1):
        if y in cad:
            sl = cad[y]
        elif cad:
            near = min(cad, key=lambda c: (abs(c - y), c))
            sl = cad[near]
        else:
            sl = default
        for s in sl:
            if (y, SLOT_ORDER[s]) < (fy0, SLOT_ORDER[s0]):
                continue
            try:
                pe = period_end(y, s, fym)
            except Exception:
                continue
            if due(pe, s) > TODAY:
                continue
            k = f"{y}|{s}"
            if k in keys:
                continue
            result[k] = {"period_end": pe.isoformat(), "basis": "inferred_cadence"}
    for k, v in keys.items():
        y, s = k.split("|")
        try:
            pe = date.fromisoformat(v["period_end"])
        except Exception:
            continue
        if due(pe, s) <= TODAY:
            result[k] = v
    last = max(result, key=ord_) if result else None
    return result, {"first_period": first, "last_expected": last, "notes": []}


# ----------------------------------------------------------------- per-file derivation
def tokens_for(name):
    toks = [t for t in re.findall(r"[a-z]{3,}", name.lower()) if t not in NAME_STOP]
    return toks


def primary_assign(assigns):
    """Choose the most informative assignment (has fy+slot) for display; keep all."""
    best = None
    for a in assigns:
        score = (bool(a.get("fiscal_year")) + bool(a.get("period_slot"))) * 2 + (a.get("bucket") == "statement")
        if best is None or score > best[0]:
            best = (score, a)
    return best[1] if best else {}


def language_of(manifest_lang, scan):
    ar, la = scan.get("has_arabic"), scan.get("has_latin")
    if ar and la:
        return "bilingual_or_mixed"
    if ar:
        return "ar"
    if la:
        return "en"
    return manifest_lang or "unknown"


def period_type(slot, doc_type, assign):
    if slot == "FY":
        return "annual"
    if slot in ("Q1", "H1", "9M"):
        return {"Q1": "Q1", "H1": "H1", "9M": "9M"}[slot]
    if assign.get("classification_method") == "discrete_q4":
        return "other_discrete_q4"
    return "other_unclassified"


def derive_file(symbol, name_tokens, fym, h, meta, scan, disk_paths):
    a = primary_assign(meta["assign"])
    bucket = a.get("bucket") or ("statement" if a.get("document_type") in ("financial_statement", "annual_report") else "supporting")
    dt = a.get("document_type")
    fy, slot = a.get("fiscal_year"), a.get("period_slot")
    flags = []
    pres = scan.get("primary_statements", [])
    has_pos, has_inc, has_cf = "financial_position" in pres, "income" in pres, "cash_flows" in pres
    n_pages = scan.get("pages")
    read = scan.get("readability")
    # file class
    if bucket == "excluded":
        fclass = "excluded_after_download"
    elif dt and dt.startswith("supporting_"):
        fclass = dt.replace("supporting_", "")
    elif scan.get("error"):
        fclass = "unreadable_error"
    elif read in ("scanned_zero_text", "no_pages"):
        fclass = "scanned_unreadable"
    else:
        kinds = set(scan.get("content_kinds", []))
        if has_pos and has_inc:
            fclass = "annual_report_with_statements" if (dt == "annual_report" or (n_pages or 0) >= 90) else "financial_statements"
        elif dt == "annual_report" or (n_pages or 0) >= 90:
            fclass = "annual_report_no_statements_found"
        elif "presentation" in kinds:
            fclass = "presentation"
        elif "results_announcement" in kinds:
            fclass = "results_announcement"
        elif "board_report" in kinds:
            fclass = "board_report"
        elif pres:
            fclass = "partial_statements"
        else:
            fclass = "other_no_statements_found"
    if read in ("mostly_scanned", "mixed") and fclass not in ("scanned_unreadable",):
        flags.append("partly_scanned_pages" if read == "mixed" else "mostly_scanned_needs_visual")
    if fclass == "scanned_unreadable":
        flags.append("zero_text_scan_needs_visual_reading")
    if fclass in ("annual_report_no_statements_found", "other_no_statements_found", "presentation", "results_announcement", "board_report") and bucket == "statement":
        flags.append("not_financial_statements")
    if fclass == "partial_statements":
        flags.append("partial_statements_only")
    if scan.get("hash_matches_name") is False:
        flags.append("hash_mismatch_filename")
    if scan.get("error"):
        flags.append("scan_error:" + scan["error"].split(":")[0])
    if not disk_paths:
        flags.append("missing_on_disk")
    if not meta.get("in_final_state"):
        flags.append("not_in_final_state_manifest")
    if not fy or not slot:
        flags.append("unclassified_period")
    if a.get("classification_method") in ("text_year_only", "filename_code"):
        flags.append("weak_period_classification:" + a["classification_method"])
    # distinct assignments
    ass_set = {(x.get("fiscal_year"), x.get("period_slot")) for x in meta["assign"] if x.get("fiscal_year") or x.get("period_slot")}
    if len(ass_set) > 1:
        flags.append("same_hash_multiple_period_labels")
    # period check
    implied = None
    if a.get("period_end"):
        implied = a["period_end"]
    elif fy and slot:
        try:
            implied = period_end(int(fy), slot, fym).isoformat()
        except Exception:
            implied = None
    det = scan.get("period_end_detected")
    pcheck = "not_checkable"
    if det and implied:
        pcheck = "match" if det == implied else "mismatch"
        if pcheck == "mismatch":
            cands = scan.get("period_end_candidates", [])
            if implied in cands:
                pcheck = "match_in_candidates"  # implied date present on front/statement pages
            else:
                flags.append("period_mismatch_candidate:detected=%s,labelled=%s" % (det, implied))
    elif scan.get("period_end_candidates") is not None and implied and read == "text":
        pcheck = "no_date_found"
    dp = set(scan.get("duration_phrases", []))
    if slot in SLOT_MONTHS and dp and fclass not in ("annual_report_with_statements",):
        interim_found = dp & {3, 6, 9}
        want = SLOT_MONTHS[slot]
        if (slot != "FY" and interim_found and want not in interim_found) or (slot == "FY" and interim_found and 12 not in dp):
            flags.append("duration_phrase_mismatch:labelled=%s,found=%s" % (slot, sorted(dp)))
    # entity check (English-readable only)
    ent = "not_checkable"
    front = scan.get("front_text_norm") or ""
    if name_tokens and front and scan.get("has_latin"):
        ent = "name_token_found" if any(t in front for t in name_tokens) else "name_token_absent"
        if ent == "name_token_absent" and bucket == "statement":
            flags.append("entity_name_not_in_front_pages_check")
    elif front and scan.get("has_arabic") and not scan.get("has_latin"):
        ent = "arabic_only_unverified"
    complete = "unknown_scanned"
    if fclass in ("financial_statements", "annual_report_with_statements"):
        complete = "primary_statements_all" if (has_pos and has_inc and has_cf) else "primary_statements_partial"
        if complete == "primary_statements_partial":
            flags.append("missing_primary_statement:" + ",".join(sorted({"financial_position", "income", "cash_flows"} - set(pres))))
            if read in ("mixed", "mostly_scanned"):
                flags.append("primary_statement_pages_may_be_image_only")
    elif fclass in ("partial_statements",):
        complete = "primary_statements_partial"
        if read in ("mixed", "mostly_scanned"):
            flags.append("primary_statement_pages_may_be_image_only")
    elif fclass in ("scanned_unreadable", "unreadable_error"):
        complete = "unknown_scanned"
    else:
        complete = "none_found"
    rec = {
        "sha256": h,
        "relpath": disk_paths[0][1] if disk_paths else None,
        "ext": (disk_paths[0][1].rsplit(".", 1)[-1] if disk_paths else a.get("file_kind")),
        "size_bytes": scan.get("size") or a.get("bytes"),
        "in_final_state_manifest": bool(meta.get("in_final_state")),
        "manifest_sources": sorted(meta["sources"]),
        "fiscal_year": fy,
        "period_slot": slot,
        "period_type": period_type(slot, dt, a),
        "period_end_manifest": a.get("period_end"),
        "period_end_detected_in_text": det,
        "period_check": pcheck,
        "document_type_manifest": dt,
        "bucket": bucket,
        "file_class": fclass,
        "completeness_dimension": complete,
        "language": language_of(a.get("language"), scan),
        "language_manifest": a.get("language"),
        "readability": read or ("text" if scan.get("kind") == "xlsx" else None),
        "pages": n_pages,
        "empty_pages": scan.get("empty_pages"),
        "text_chars": scan.get("text_chars"),
        "primary_statements_found": pres,
        "statement_pages": scan.get("statement_pages"),
        "entity_check": ent,
        "classification_method": a.get("classification_method"),
        "source": a.get("source"),
        "source_url": a.get("source_url"),
        "manifest_scanned_flag": a.get("scanned"),
        "digest_text_sha1": scan.get("digest_text_sha1"),
        "all_period_labels": sorted({"%s|%s" % (x.get("fiscal_year"), x.get("period_slot")) for x in meta["assign"]}),
        "flags": flags,
    }
    if scan.get("sheets"):
        rec["sheets"] = scan["sheets"][:12]
    return rec


def slot_status(files_for_slot):
    """Document-completeness status of a fiscal-year/slot from the files present."""
    best = "absent"
    rank = {"absent": 0, "non_statement_only": 1, "unreadable_scan_only": 2, "partial_statements": 3,
            "statements_via_annual_report": 4, "statements_complete": 5}
    for f in files_for_slot:
        c = f["file_class"]
        if f["bucket"] != "statement":
            continue
        if c == "financial_statements" and f["completeness_dimension"] == "primary_statements_all":
            s = "statements_complete"
        elif c == "financial_statements":
            s = "partial_statements"
        elif c == "annual_report_with_statements":
            s = "statements_via_annual_report" if f["completeness_dimension"] == "primary_statements_all" else "partial_statements"
        elif c in ("partial_statements",):
            s = "partial_statements"
        elif c in ("scanned_unreadable", "unreadable_error"):
            s = "unreadable_scan_only"
        else:
            s = "non_statement_only"
        if rank[s] > rank[best]:
            best = s
    return best


def analyse_company(symbol, reg, meta_all, scans, idx, st):
    name = reg["name"]
    toks = tokens_for(name)
    fym = None
    for kind in ("se", "issuer"):
        v = (st.get(kind) or {}).get("fy_end_month")
        if v:
            fym = v
            break
    fym = reg.get("fiscal_year_end") if (not fym and isinstance(reg.get("fiscal_year_end"), int)) else fym
    fym = fym or 12
    files = []
    for h, meta in meta_all.items():
        dpaths = [p for p in idx.get(h, []) if p[0] == symbol] or []
        other = [p for p in idx.get(h, []) if p[0] != symbol]
        rec = derive_file(symbol, toks, fym, h, meta, scans.get(h, {}), dpaths)
        if not dpaths and other:
            rec["flags"].append("found_only_under_other_symbol:" + ",".join(sorted({o[0] for o in other})))
            rec["flags"] = [f for f in rec["flags"] if f != "missing_on_disk"] + ["missing_on_disk_under_this_symbol"]
        if other and dpaths:
            rec["flags"].append("same_hash_under_other_symbol:" + ",".join(sorted({o[0] for o in other})))
        files.append(rec)
    # duplicates within company
    dig = defaultdict(list)
    for f in files:
        if f.get("digest_text_sha1"):
            dig[f["digest_text_sha1"]].append(f)
    for d, fl in dig.items():
        if len(fl) > 1 and len({x["sha256"] for x in fl}) > 1:
            for x in fl:
                x["flags"].append("duplicate_text_candidate_of:" + ",".join(sorted(y["sha256"][:10] for y in fl if y is not x)))
    byslot = defaultdict(list)
    for f in files:
        for lab in f["all_period_labels"]:
            fy, s = lab.split("|")
            if fy != "None" and s != "None" and f["bucket"] == "statement":
                byslot[f"{fy}|{s}"].append(f)
    for k, fl in byslot.items():
        langs = defaultdict(list)
        for f in fl:
            if f["file_class"] in ("financial_statements", "annual_report_with_statements"):
                langs[(f["language"], f["file_class"])].append(f)
        for _, g in langs.items():
            if len(g) > 1:
                for x in g:
                    x["flags"].append("multiple_same_language_same_period:" + k)
    doc_slots = set()
    for k, fl in byslot.items():
        fy, s = k.split("|")
        if s in SLOT_ORDER:
            doc_slots.add((int(fy), s))
    expected, emeta = build_expected(symbol, st, doc_slots, fym)
    ord_ = lambda k: (int(k.split("|")[0]), SLOT_ORDER[k.split("|")[1]])
    periods = {}
    for k in sorted(set(expected) | set(byslot), key=ord_):
        fl = byslot.get(k, [])
        stt = slot_status(fl) if fl else "absent"
        periods[k] = {
            "expected": k in expected,
            "expected_basis": expected[k]["basis"] if k in expected else "not_expected_extra_file",
            "period_end": expected[k]["period_end"] if k in expected else None,
            "status": stt,
            "files": sorted(f["sha256"] for f in fl),
            "languages": sorted({f["language"] for f in fl}),
        }
    exp_keys = [k for k in periods if periods[k]["expected"]]
    ok_status = {"statements_complete", "statements_via_annual_report"}
    n_ok = sum(1 for k in exp_keys if periods[k]["status"] in ok_status)
    n_part = sum(1 for k in exp_keys if periods[k]["status"] == "partial_statements")
    n_scan = sum(1 for k in exp_keys if periods[k]["status"] == "unreadable_scan_only")
    n_non = sum(1 for k in exp_keys if periods[k]["status"] == "non_statement_only")
    n_abs = sum(1 for k in exp_keys if periods[k]["status"] == "absent")
    first = emeta["first_period"]
    gaps = [k for k in exp_keys if periods[k]["status"] == "absent"]
    extra = [k for k in periods if not periods[k]["expected"]]
    fa = sorted(k for k in extra if periods[k]["status"] != "absent")
    # leading/internal/trailing gaps
    present_idx = [i for i, k in enumerate(exp_keys) if periods[k]["status"] not in ("absent",)]
    lead = trail = internal = []
    if present_idx:
        lead = [exp_keys[i] for i in range(0, present_idx[0]) if periods[exp_keys[i]]["status"] == "absent"]
        trail = [exp_keys[i] for i in range(present_idx[-1] + 1, len(exp_keys)) if periods[exp_keys[i]]["status"] == "absent"]
        internal = [exp_keys[i] for i in range(present_idx[0], present_idx[-1] + 1) if periods[exp_keys[i]]["status"] == "absent"]
    else:
        lead = list(exp_keys)
    exp_n = len(exp_keys)
    pct_ok = round(n_ok / exp_n, 3) if exp_n else None
    pct_any = round((exp_n - n_abs) / exp_n, 3) if exp_n else None
    def cls(p):
        if p is None:
            return "no_expected_periods"
        return "high" if p >= 0.9 else "good" if p >= 0.7 else "partial" if p >= 0.4 else "sparse" if p > 0 else "none"
    stmt_files = [f for f in files if f["bucket"] == "statement"]
    n_text = sum(1 for f in stmt_files if f["readability"] == "text" and f["file_class"] in ("financial_statements", "annual_report_with_statements"))
    n_scanf = sum(1 for f in stmt_files if f["file_class"] == "scanned_unreadable" or "mostly_scanned_needs_visual" in " ".join(f["flags"]))
    n_stmt_files = len(stmt_files)
    ex_share = (n_text / n_stmt_files) if n_stmt_files else 0
    ext_class = "none" if not n_stmt_files else ("A_text_clean" if ex_share >= 0.85 and n_scanf / n_stmt_files < 0.1 else
                                                 "B_mostly_text" if ex_share >= 0.55 else "C_scan_or_nonstatement_heavy")
    return {
        "symbol": symbol,
        "company_id": reg["company_id"],
        "name": name,
        "registry_sector": reg.get("sector"),
        "registry_industry": reg.get("industry"),
        "fiscal_year_end_month": fym,
        "fiscal_year_end_source": "collector_state_inferred_from_saudi_exchange_announcements" if any((st.get(k) or {}).get("fy_end_month") for k in ("se", "issuer")) else "default_12",
        "dimensions": {
            "value_correctness": {"assessed": False, "note": "Not assessed at Step 1. No statement is verified here."},
            "document_completeness": {
                "files_total": len(files),
                "statement_bucket_files": n_stmt_files,
                "files_with_all_three_primary_statements": sum(1 for f in files if f["completeness_dimension"] == "primary_statements_all"),
                "files_partial_statements": sum(1 for f in files if f["completeness_dimension"] == "primary_statements_partial"),
                "files_no_statements_found": sum(1 for f in files if f["completeness_dimension"] == "none_found" and f["bucket"] == "statement"),
                "files_unknown_scanned": sum(1 for f in files if f["completeness_dimension"] == "unknown_scanned" and f["bucket"] == "statement"),
                "extractability_class": ext_class,
                "text_extractable_statement_files": n_text,
            },
            "company_coverage": {
                "expected_periods": exp_n,
                "periods_with_complete_statements": n_ok,
                "periods_with_partial_statements": n_part,
                "periods_scanned_only": n_scan,
                "periods_non_statement_only": n_non,
                "periods_absent": n_abs,
                "pct_expected_with_complete_statements": pct_ok,
                "pct_expected_with_any_file": pct_any,
                "coverage_class": cls(pct_ok),
                "first_observed_period_proxy_for_listing": emeta["first_period"],
                "last_expected_period": emeta["last_expected"],
                "listing_date": "unknown_not_in_registry_or_raw_state",
                "listing_gap_note": "Expected window starts at the earliest period seen in Saudi Exchange results announcements or collected files; periods before it are NOT counted as missing (listing date unavailable locally). Archive horizon appears to be ~2011; companies whose first period is at/near the horizon may have older history that was never targeted.",
                "leading_gaps_within_window": lead,
                "internal_gaps": internal,
                "trailing_gaps": trail,
                "extra_periods_present_outside_expected": fa,
            },
        },
        "state": {k: {kk: vv for kk, vv in v.items() if kk != "expected"} for k, v in st.items()},
        "periods": periods,
        "files": sorted(files, key=lambda f: (str(f["fiscal_year"]), str(f["period_slot"]), f["sha256"])),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--chunk", type=int, default=20)
    ap.add_argument("--workers", type=int, default=18)
    ap.add_argument("--max-chunks", type=int, default=10**6)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    reg = load_registry()
    targets = [s for s in sorted(reg) if s not in EXCLUDED]
    if a.only:
        targets = [s for s in targets if s in a.only.split(",")]
    (OUT / "companies").mkdir(exist_ok=True)
    prog_p = OUT / "progress.json"
    prog = json.load(open(prog_p)) if prog_p.exists() else {"done": [], "target_count": len(targets)}
    prog["target_count"] = len(targets)
    prog["excluded_symbols"] = sorted(EXCLUDED)
    todo = [s for s in targets if s not in set(prog["done"])]
    print("targets", len(targets), "todo", len(todo), flush=True)
    t0 = time.time()
    idx = disk_index()
    meta = load_manifests()
    print("indexes ready", round(time.time() - t0), flush=True)
    chunks = [todo[i:i + a.chunk] for i in range(0, len(todo), a.chunk)][: a.max_chunks]
    with Pool(a.workers) as pool:
        for ci, ch in enumerate(chunks):
            jobs, owner = [], {}
            for sym in ch:
                for h, m in meta.get(sym, {}).items():
                    paths = [p for p in idx.get(h, []) if p[0] == sym]
                    if paths:
                        jobs.append((str(RAW / paths[0][1]), h))
                        owner[(str(RAW / paths[0][1]))] = (sym, h)
                # orphan files on disk not in any manifest
            for h, lst in idx.items():
                pass
            # orphans: on disk under this symbol but absent from manifests
            for sym in ch:
                have = set(meta.get(sym, {}))
                d = RAW / "archive/SA" / sym
                if d.exists():
                    for root, _, fs in os.walk(d):
                        for f in fs:
                            h = f.rsplit(".", 1)[0]
                            if h not in have:
                                have.add(h)
                                p = str(Path(root) / f)
                                meta.setdefault(sym, {})[h] = {"assign": [], "sources": {"disk_orphan"}, "in_final_state": False}
                                jobs.append((p, h))
                                owner[p] = (sym, h)
            scans = defaultdict(dict)
            for r in pool.imap_unordered(pdfscan.scan_file, jobs, chunksize=2):
                sym, h = owner[r["path"]]
                scans[sym][h] = r
            for sym in ch:
                st = state_info(sym)
                rec = analyse_company(sym, reg[sym], meta.get(sym, {}), scans.get(sym, {}), idx, st)
                with open(OUT / "companies" / f"{sym}.json", "w", encoding="utf8") as f:
                    json.dump(rec, f, ensure_ascii=False, indent=1)
                prog["done"].append(sym)
            prog["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            json.dump(prog, open(prog_p, "w"), indent=1)
            print(f"chunk {ci + 1}/{len(chunks)} done: {len(prog['done'])}/{len(targets)} files={len(jobs)} t={round(time.time() - t0)}s", flush=True)


if __name__ == "__main__":
    main()
