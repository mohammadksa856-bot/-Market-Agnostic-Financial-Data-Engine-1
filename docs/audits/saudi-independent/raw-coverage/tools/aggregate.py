"""Aggregate per-company inventories into coverage-summary.json/.md, batch-plan.json/.md and queues.

Reads ../companies/*.json only (plus the registry). Read-only on raw files.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
REPO = OUT.parents[3]
REG = {r["symbol"]: r for r in json.load(open(REPO / "config/sa-market-registry.json", encoding="utf8"))}

# Materiality heuristic: NO market-cap data exists locally. Tier 1 is a hand-maintained list of
# large / index-heavy Saudi issuers (analyst judgement, documented as such); everything else is by
# sector group. Change LARGE_CAPS to re-rank; nothing else depends on it.
LARGE_CAPS = set("""2020 2050 2060 2280 2310 2350 2380 2223 2330 2290 1211 1810 1830 1832 1111 4001 4002 4003 4004 4007 4009 4013
4030 4031 4190 4200 4300 4321 4322 4323 4020 4240 4250 4263 4280 4310 4161 4164 5110 6010 6002 6004 2080 2083 7200 7201 7204
8200 8210 8230 8250 8030 8012 8020 2081 2084 1302 1301 1321 2170 2250 2270 2300 2340 4050 4061 4180 4210 4260 4290 4003 4008
4015 4017 4100 4110 4140 4142 4150 4162 4163 4165 4191 4192 4220 4230 4270 4291 4292 4701 4702 4703""".split())
LARGE_CAPS_TIER1 = set("""2020 2050 2060 2280 2310 2350 2380 2223 2330 2290 1211 1810 1830 1111 4001 4002 4003 4004 4007 4009 4013
4030 4031 4190 4200 4300 4321 4323 4020 4240 4250 4263 4280 4310 4164 5110 6010 7200 7201 8200 8210 8230 8250 2080 2083 1302""".split())


def sector_group(sym, name):
    n = int(sym) if sym.isdigit() else 0
    nm = name.lower()
    if re.search(r"\breit\b|real estate investment|traded fund|\bfund\b", nm) or 4330 <= n <= 4350:
        return "reit_funds"
    if 9000 <= n <= 9999:
        return "nomu_parallel_market"
    if 1000 <= n < 1200:
        return "financials"
    if 1200 <= n < 1400:
        return "materials_capital_goods"
    if 1800 <= n < 1900:
        return "consumer_services"
    if 2000 <= n < 3000:
        return "materials_energy_food"
    if 3000 <= n < 4000:
        return "cement"
    if 4000 <= n < 4020:
        return "retail_health"
    if 4020 <= n < 4400:
        return "real_estate_transport_services"
    if 4400 <= n < 5000:
        return "services_media_education"
    if 5000 <= n < 6000:
        return "utilities_capital_goods"
    if 6000 <= n < 7000:
        return "food_agri"
    if 7000 <= n < 8000:
        return "telecom_tech"
    if 8000 <= n < 9000:
        return "insurance"
    return "other"


def tier_of(sym, grp):
    if sym in LARGE_CAPS_TIER1:
        return 1
    if grp in ("financials", "materials_energy_food", "telecom_tech", "utilities_capital_goods", "insurance",
               "materials_capital_goods", "cement", "retail_health", "food_agri"):
        return 2
    if grp in ("reit_funds",):
        return 4
    if grp == "nomu_parallel_market":
        return 5
    return 3


def flag_kind(f):
    return f.split(":")[0]


def main():
    comps = []
    for p in sorted((OUT / "companies").glob("*.json")):
        comps.append(json.load(open(p, encoding="utf8")))
    n = len(comps)
    # ---- distributions
    cov = Counter(c["dimensions"]["company_coverage"]["coverage_class"] for c in comps)
    ext = Counter(c["dimensions"]["document_completeness"]["extractability_class"] for c in comps)
    fclass, flags, flag_cos, read, lang, ptype, per_status = Counter(), Counter(), defaultdict(set), Counter(), Counter(), Counter(), Counter()
    total_files = total_bytes = 0
    hash_owner = defaultdict(set)
    digest_owner = defaultdict(set)
    for c in comps:
        for f in c["files"]:
            total_files += 1
            total_bytes += f.get("size_bytes") or 0
            fclass[f["file_class"]] += 1
            read[f.get("readability")] += 1
            lang[f["language"]] += 1
            ptype[f["period_type"]] += 1
            hash_owner[f["sha256"]].add(c["symbol"])
            if f.get("digest_text_sha1") and f["bucket"] == "statement":
                digest_owner[f["digest_text_sha1"]].add(c["symbol"])
            for fl in f["flags"]:
                flags[flag_kind(fl)] += 1
                flag_cos[flag_kind(fl)].add(c["symbol"])
        for k, v in c["periods"].items():
            if v["expected"]:
                per_status[v["status"]] += 1
    cross_hash = {h: sorted(s) for h, s in hash_owner.items() if len(s) > 1}
    cross_digest = {h: sorted(s) for h, s in digest_owner.items() if len(s) > 1}
    exp_total = sum(c["dimensions"]["company_coverage"]["expected_periods"] for c in comps)
    ok_total = sum(c["dimensions"]["company_coverage"]["periods_with_complete_statements"] for c in comps)
    # ---- queues
    visual, wrong_period, nonstmt, dups = [], [], [], []
    for c in comps:
        for f in c["files"]:
            fl = " ".join(f["flags"])
            if "zero_text_scan_needs_visual_reading" in fl or "mostly_scanned_needs_visual" in fl or "primary_statement_pages_may_be_image_only" in fl:
                visual.append({"symbol": c["symbol"], "sha256": f["sha256"], "relpath": f["relpath"], "label": f"{f['fiscal_year']}|{f['period_slot']}",
                               "file_class": f["file_class"], "pages": f["pages"], "readability": f["readability"],
                               "reason": [x for x in f["flags"] if "scan" in x or "image_only" in x][:2]})
            if "period_mismatch_candidate" in fl:
                wrong_period.append({"symbol": c["symbol"], "sha256": f["sha256"], "relpath": f["relpath"], "label": f"{f['fiscal_year']}|{f['period_slot']}",
                                     "detail": [x for x in f["flags"] if x.startswith("period_mismatch")][0]})
            if "not_financial_statements" in fl and f["bucket"] == "statement":
                nonstmt.append({"symbol": c["symbol"], "sha256": f["sha256"], "label": f"{f['fiscal_year']}|{f['period_slot']}", "file_class": f["file_class"]})
            if "duplicate_text_candidate_of" in fl or "multiple_same_language_same_period" in fl:
                dups.append({"symbol": c["symbol"], "sha256": f["sha256"], "label": f"{f['fiscal_year']}|{f['period_slot']}",
                             "flags": [x for x in f["flags"] if x.startswith(("duplicate", "multiple"))]})
    json.dump(visual, open(OUT / "visual-reading-queue.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
    json.dump({"period_mismatch_candidates": wrong_period, "not_financial_statements_in_statement_bucket": nonstmt,
               "duplicate_candidates": dups, "cross_company_identical_hash": cross_hash, "cross_company_identical_front_text": cross_digest},
              open(OUT / "anomaly-queues.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
    # ---- ranking and batches
    rows = []
    ext_order = {"A_text_clean": 0, "B_mostly_text": 1, "C_scan_or_nonstatement_heavy": 2, "none": 3}
    for c in comps:
        d, cc = c["dimensions"]["document_completeness"], c["dimensions"]["company_coverage"]
        grp = sector_group(c["symbol"], c["name"])
        tier = tier_of(c["symbol"], grp)
        nvis = sum(1 for f in c["files"] if f["bucket"] == "statement" and (f["file_class"] == "scanned_unreadable" or any("image_only" in x or "mostly_scanned" in x for x in f["flags"])))
        stmt_files = max(1, d["statement_bucket_files"])
        visual_heavy = d["statement_bucket_files"] > 0 and nvis / stmt_files >= 0.3
        rows.append({
            "symbol": c["symbol"], "name": c["name"], "sector_group": grp, "materiality_tier": tier,
            "in_tier1_large_cap_list": c["symbol"] in LARGE_CAPS_TIER1,
            "extractability_class": d["extractability_class"], "visual_reading_heavy": visual_heavy,
            "statement_files": d["statement_bucket_files"], "files_needing_visual": nvis,
            "expected_periods": cc["expected_periods"], "pct_complete": cc["pct_expected_with_complete_statements"],
            "coverage_class": cc["coverage_class"],
            "unknown_or_flagged_files": sum(1 for f in c["files"] if f["flags"]),
        })
    rows.sort(key=lambda r: (r["materiality_tier"], r["sector_group"], ext_order[r["extractability_class"]], -(r["pct_complete"] or 0), r["symbol"]))
    batchable = [r for r in rows if r["statement_files"] > 0]
    nofile = [r for r in rows if r["statement_files"] == 0]
    batches = []
    for tier in sorted({r["materiality_tier"] for r in batchable}):
        for visual_flag in (False, True):
            grp_rows = [r for r in batchable if r["materiality_tier"] == tier and r["visual_reading_heavy"] == visual_flag]
            for i in range(0, len(grp_rows), 5):
                chunk = grp_rows[i:i + 5]
                batches.append({"tier": tier, "visual_reading_batch": visual_flag, "members": chunk})
    batch_plan = []
    for bi, b in enumerate(batches, 1):
        m = b["members"]
        batch_plan.append({
            "batch_id": f"B{bi:03d}", "order": bi, "materiality_tier": b["tier"], "visual_reading_batch": b["visual_reading_batch"],
            "sectors": sorted({x["sector_group"] for x in m}),
            "symbols": [x["symbol"] for x in m],
            "companies": [{"symbol": x["symbol"], "name": x["name"], "extractability_class": x["extractability_class"],
                           "statement_files": x["statement_files"], "files_needing_visual": x["files_needing_visual"],
                           "expected_periods": x["expected_periods"], "pct_expected_with_complete_statements": x["pct_complete"],
                           "coverage_class": x["coverage_class"]} for x in m],
            "total_statement_files": sum(x["statement_files"] for x in m),
            "step2_notes": "Statement-level audit: per file, verify the primary statements and the values they contain against the document itself (value correctness is NOT assessed in Step 1). "
                           + ("Zero-text/image pages require visual reading." if b["visual_reading_batch"] else "Text-layer first; visual check where flagged."),
        })
    json.dump({"batch_size": 5, "ordering": "materiality_tier asc (1=large caps), sector_group, extractability (text-clean first), higher document coverage first; visual-reading-heavy companies are in their own batches after the text batches of each tier",
               "materiality_basis": "Heuristic. No market-cap data in repo; tier 1 = hand-maintained large-cap list (tools/aggregate.py LARGE_CAPS_TIER1); other tiers by sector group; REITs tier 4; Nomu tier 5.",
               "excluded_from_plan_no_statement_files": nofile, "batches": batch_plan,
               "ranked_companies": rows},
              open(OUT / "batch-plan.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
    # ---- summary
    summ = {
        "generated_for": "Step 1 raw coverage inventory (document inventory only; value correctness NOT assessed)",
        "scope": {"registry_companies": len(REG), "excluded_symbols": sorted(json.load(open(OUT / "progress.json")).get("excluded_symbols", [])),
                  "inventoried_companies": n,
                  "note_excluded_count": "Task said 32 audited companies, but the supplied list holds 27 audited symbols + 1050 + 1060 = 29 distinct; all 29 were excluded, so 390 (not 387) remain."},
        "files": {"inventoried_files": total_files, "bytes": total_bytes, "file_class": dict(fclass.most_common()),
                  "readability": dict(read.most_common()), "language": dict(lang.most_common()), "period_type": dict(ptype.most_common())},
        "company_coverage_distribution": dict(cov),
        "extractability_distribution": dict(ext),
        "expected_period_slots": {"total_expected": exp_total, "status_counts": dict(per_status.most_common()),
                                  "pct_with_complete_statements": round(ok_total / exp_total, 4) if exp_total else None},
        "anomaly_classes": {k: {"files": v, "companies": len(flag_cos[k])} for k, v in flags.most_common()},
        "cross_company": {"identical_sha256_in_multiple_companies": len(cross_hash), "identical_front_text_digest_in_multiple_companies": len(cross_digest)},
        "queues": {"visual_reading_files": len(visual), "period_mismatch_candidate_files": len(wrong_period),
                   "non_statement_files_in_statement_bucket": len(nonstmt), "duplicate_candidate_files": len(dups)},
        "batch_plan": {"batches": len(batch_plan), "visual_batches": sum(1 for b in batch_plan if b["visual_reading_batch"]),
                       "companies_in_batches": sum(len(b["symbols"]) for b in batch_plan), "companies_without_statement_files": [r["symbol"] for r in nofile],
                       "by_tier": dict(Counter(b["materiality_tier"] for b in batch_plan))},
        "caveats": [
            "Listing dates are not available locally; the expected window starts at the earliest period seen in Saudi Exchange announcements or collected files (proxy). Earlier history is neither expected nor counted missing.",
            "Statement detection, period-end detection and entity checks are text-layer heuristics (English and Arabic headings); image-only pages are invisible to them and are queued for visual reading.",
            "Nothing here verifies any figure. 'statements_complete' means a file shows all three primary-statement headings with numbers, not that values are correct.",
            "Absence of published/collected data is not absence of an extractable document: absent periods may still be obtainable from issuer sites, annual reports or Saudi Exchange.",
        ],
    }
    json.dump(summ, open(OUT / "coverage-summary.json", "w", encoding="utf8"), indent=1, ensure_ascii=False)
    # markdown
    L = ["# Saudi raw coverage inventory (Step 1)", "",
         "Document inventory only. **Value correctness: not assessed.** No company's statements are verified by this step.", "",
         f"- Companies inventoried: {n} (registry {len(REG)}; 29 excluded: {', '.join(summ['scope']['excluded_symbols'])})",
         f"- Files inventoried: {total_files:,} ({total_bytes / 1e9:.1f} GB)", "",
         "## Company coverage (expected periods with complete statements)", ""]
    for k in ("high", "good", "partial", "sparse", "none", "no_expected_periods"):
        L.append(f"- {k}: {cov.get(k, 0)}")
    L += ["", f"Expected period slots: {exp_total:,}; with complete statements {ok_total:,} ({summ['expected_period_slots']['pct_with_complete_statements']:.1%}).", "",
          "Slot status: " + ", ".join(f"{k}={v}" for k, v in per_status.most_common()), "",
          "## Extractability (document completeness dimension)", ""]
    for k, v in ext.most_common():
        L.append(f"- {k}: {v}")
    L += ["", "## File classes", ""] + [f"- {k}: {v}" for k, v in fclass.most_common()]
    L += ["", "## Readability", ""] + [f"- {k}: {v}" for k, v in read.most_common()]
    L += ["", "## Anomaly classes (flag kind: files / companies)", ""] + [f"- {k}: {v['files']} / {v['companies']}" for k, v in summ["anomaly_classes"].items()]
    L += ["", f"Cross-company identical sha256: {len(cross_hash)}; identical front-text digest: {len(cross_digest)}.", "",
          "## Batch plan", "", f"{len(batch_plan)} batches of 5 ({summ['batch_plan']['visual_batches']} visual-reading batches). Companies without statement files: {', '.join(summ['batch_plan']['companies_without_statement_files']) or 'none'}.", ""]
    for b in batch_plan:
        L.append(f"- {b['batch_id']} T{b['materiality_tier']}{' VISUAL' if b['visual_reading_batch'] else ''}: " + ", ".join(b["symbols"]))
    L += ["", "## Caveats", ""] + [f"- {c}" for c in summ["caveats"]]
    open(OUT / "coverage-summary.md", "w", encoding="utf8").write("\n".join(L) + "\n")
    print(json.dumps({k: summ[k] for k in ("company_coverage_distribution", "extractability_distribution", "queues", "batch_plan")}, indent=1))
    print(json.dumps(summ["anomaly_classes"], indent=1))


if __name__ == "__main__":
    main()
