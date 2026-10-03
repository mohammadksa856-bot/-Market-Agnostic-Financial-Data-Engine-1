"""Batch2-E: assemble docs/audits/saudi-independent/<symbol>.json from manifests + page transcriptions + findings.
Run from repo root: python docs/audits/saudi-independent/tools/e_build_reports.py"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "docs", "audits", "saudi-independent")
BRANCH = ("origin/codex/telecom-95pct @ ec610f3; the five manifests are byte-identical on origin/main and on "
          "claude/data-cement-1/2/3 and claude/aramco-alrajhi-gap-closure")
RAW_BRANCH = ("origin/claude/audit-saudi-batch1-B (read via git show; sha256 verified equal to "
              "data/raw/archive-index.json content_hash)")

STMT_PAGES = {
    "3002": {7: ("balance_sheet", 8), 8: ("income_statement", 9), 9: ("comprehensive_income", 10), 11: ("cash_flow", 12)},
    "3003": {5: ("balance_sheet", 7), 6: ("income_statement+OCI", 8), 8: ("cash_flow", 10)},
    "3005": {6: ("balance_sheet", 8), 7: ("income_statement+OCI", 9), 9: ("cash_flow", 11)},
    "3020": {5: ("balance_sheet", 7), 6: ("income_statement+OCI", 8), 8: ("cash_flow", 10)},
    "3040": {7: ("balance_sheet", 8), 8: ("income_statement+OCI", 9), 10: ("cash_flow", 11)},
}
META = {
    "3002": dict(name="Najran Cement Company", manifest="najran-cement-2025-fy.json",
                 unit="SAR thousands (scale 1000); per-share SAR",
                 auditor="BDO Dr. Mohamed Al-Amri & Co., opinion dated Jeddah 6 April 2026",
                 board="29 March 2026 (Note 33)", consolidated=True,
                 visual="pdf p8 (BS), p9 (P&L), p12 (CF) rendered and read by eye; p10 (OCI) via text layer only (text layer present although pages are scans)",
                 method="text-layer line match (tools/e_textlayer_verify.py: 104 match + 2 sign_convention of 106) + eyeballed page renders; transcription tools/e_transcripts/3002.json"),
    "3003": dict(name="City Cement Company", manifest="city-cement-2025-fy.json",
                 unit="full SAR (scale 1); per-share SAR", auditor="BDO Dr. Mohamed Al-Amri & Co.",
                 board="16 March 2026 / 27 Ramadan 1447H (Note 35)", consolidated=True,
                 visual="pdf p7 (BS), p8 (P&L+OCI), p10 (CF) rendered and read by eye (image-only pages, no text layer); Note 15 (pdf p31) read from digital text",
                 method="independent page transcription (tools/e_transcripts/3003.json) compared with manifest by tools/e_compare.py; every subtotal re-added"),
    "3005": dict(name="Umm Al-Qura Cement Company", manifest="umm-al-qura-cement-2025-fy.json",
                 unit="full SAR (scale 1); per-share SAR", auditor="BDO Dr. Mohamed Al-Amri & Co., Riyadh 15 March 2026",
                 board="12 March 2026 / 23 Ramadan 1447H (Note 27)", consolidated=False,
                 visual="pdf p8 (BS), p9 (P&L+OCI), p11 (CF) rendered and read by eye (image-only pages)",
                 method="independent page transcription (tools/e_transcripts/3005.json) compared with manifest; subtotals and cash-flow add-back sums re-added"),
    "3020": dict(name="Yamama Cement Company", manifest="yamama-cement-2025-fy.json",
                 unit="full SAR (scale 1); per-share SAR", auditor="Professional Consultants Company, Riyadh 23 February 2026",
                 board="16 February 2026", consolidated=False,
                 visual="pdf p7 (BS) and p10 (CF) rendered and read by eye; p8 (P&L+OCI) via digital text layer (current-year column sequence checked by tools/e_seq_verify.py, 66 rows) and subtotal arithmetic; FY2024 P&L column not eyeballed on the image",
                 method="independent page transcription (tools/e_transcripts/3020.json) + text-layer sequence check; subtotals re-added"),
    "3040": dict(name="Qassim Cement Company", manifest="qassim-cement-2025-fy.json",
                 unit="full SAR (scale 1); per-share SAR", auditor="BDO Dr. Mohamed Al-Amri & Co., Dammam 23 February 2026",
                 board="16 February 2026 / 28 Sha'ban 1447H (Note 41)", consolidated=True,
                 visual="pdf p8 (BS), p9 (P&L+OCI), p11 (CF) rendered and read by eye; Note 37 (restatement) read from OCR text pdf p50",
                 method="independent page transcription (tools/e_transcripts/3040.json) compared with manifest; subtotals and component sums re-added"),
}
FIND = {
    "3002": dict(defects=[], observations=[
        "Statement text is scanned but the PDF carries a text layer; text layer equals rendered image on p8/p9/p12.",
        "depreciation_amortization stored NEGATIVE (-98,351 / -96,480) while the cash-flow add-back is printed positive; repo-wide convention (engine uses abs()) - not counted as a defect.",
        "current_debt = Current portion of long-term borrowing 35,393 + Short-term financing 10,000 = 45,393 (2024: 61,357+30,000 = 91,357); debt_repaid = -16,000 + -20,000 = -36,000; composites verified by arithmetic."],
        missing=[("weighted_average_shares_basic/diluted", "Face P&L p8 prints 166,940 (2025) / 170,000 (2024) thousand shares; not carried"),
                 ("proceeds_from_ppe_sales", "CF p12 287 / 1,325; no metric carried"),
                 ("employee_benefits_paid", "CF p12 (2,220) / (4,360); no metric carried")],
        fix="none for numbers; add weighted_average_shares to the cement manifests (manifest/reader level, general)"),
    "3003": dict(defects=[], observations=[
        "Scan columns are visually offset (manifest notes say so); every value re-read from the render matches its note-number row and all subtotals re-add.",
        "cash_end 113,777,135 (CF p8) vs balance-sheet cash 13,777,135 (p5) differ by exactly 100,000,000: PROVEN genuine by Note 15 (pdf p31): 'Short Term Deposit* 100,000,000 ... maturities of 90 days or less ... classified as cash equivalents'. The BS separately lists 'Short term time deposit' 146,000,000 (also inside published short_term_investments 540,563,647 = 394,563,647 + 146,000,000), so a consumer summing cash + short_term_investments double-counts up to 100m on the CF definition. The cross-check warn is expected, not an error.",
        "short_term_investments composite verified: 2025 394,563,647 + 146,000,000; 2024 214,976,744 + 216,000,000 = 430,976,744.",
        "capex 2025 = PPE and CWIP 84,273,279 only; 2024 = PPE 39,116,033 + intangibles 341,084 = 39,457,117 (investment in JV 2,066,921 correctly excluded)."],
        missing=[("weighted_average_shares", "not carried; Note 26 (EPS) not read"),
                 ("interest_paid", "not disclosed separately in the CF (confirmed absent)"),
                 ("other_comprehensive_income components", "p6: equity-instrument OCI (471,016)/(552,494), actuarial (142,701)/1,379,018 not carried; only total comprehensive income is")],
        fix="none for numbers"),
    "3005": dict(defects=[], observations=[
        "Standalone statements (no subsidiaries) per cover/notes; consistent with the manifest.",
        "depreciation_amortization = 51,697,431 + 147,943 + 1,123,089 = 52,968,463 (2024: 51,360,017 + 196,022 + 1,081,061 = 52,637,100): composite verified.",
        "CF p9 finance-costs add-back is 9,379,546 vs P&L 9,379,545 (1 riyal rounding in the source itself); manifest carries the P&L value only.",
        "capex -13,915,042 excludes 'Payment for purchase of financial investments at FVOCI' (4,830), a financial investment; investing_cash_flow -13,919,872 = both lines. FY2025 long_term_debt is absent because the SIDF loan 200,095,467 is wholly current (BS p6 shows '-'): verified."],
        missing=[("weighted_average_shares", "not carried"),
                 ("employee_benefits_paid", "CF p9 (547,000) / (378,098) not carried"),
                 ("dividends_paid", "no dividend line in the FY2025 or FY2024 CF (confirmed absent)")],
        fix="none for numbers"),
    "3020": dict(defects=[
        dict(id="AUDIT-E-3020-1", cls="classification: composite mixes statement positions", severity="low",
             where="P&L printed p6 (pdf p8); manifest fact impairment_charges FY2025",
             published="-51,987,657",
             correct="ECL provision (20,185,882) is deducted ABOVE 'Income from main activities' (533,611,568 - 18,999,529 - 75,731,975 - 20,185,882 = 418,694,182); 'Provision for impairment of spare parts for Plants and equipment' (31,801,775) sits under 'Other (expenses)/income' BELOW operating income (418,694,182 - 67,583,596 - 31,801,775 + 6,262,657 + 163,562,977 + 6,743,079 = 495,877,524). The sum is arithmetically right, but the single fact fits neither bridge.",
             evidence="P&L p6 line items 'Provision for expected credit loss (ECL)' (note 11) and 'Provision for impairment of spare parts for Plants and equipment' (note 6); both bridges re-added exactly",
             fix="general reader/manifest rule: never sum lines on opposite sides of operating income; emit ECL as impairment_charges and the spare-parts impairment as other_nonoperating_expense. No data/** edit by this audit."),
        dict(id="AUDIT-E-3020-2", cls="definition inconsistency", severity="low",
             where="CF printed p8 (pdf p10); manifest capex FY2025 -415,983,274 / FY2024 -983,767,109",
             published="PPE + CWIP only",
             correct="'Purchase of Intangible assets' (294,281 / 1,470,413) is a separate investing line not included, whereas 3003 (2024) and 3040 add intangibles to capex. Impact 0.07% / 0.15%.",
             evidence="CF p8 lines 'Purchase of property, plant, and equipment', 'Additions to capital works in progress', 'Purchase of Intangible assets'",
             fix="align the capex definition across cement manifests (policy decision for Codex)")],
        observations=[
            "Standalone statements. PDF statement pages carry digital text although the manifest/archive note says 'scanned'; text layer equals rendered image on p7 and p10.",
            "other_reserves = 726,883,763 + 579,936,772 + (43,218,618) = 1,263,601,917 (2024: ... + 101,171,726 = 1,407,992,261); verified.",
            "P&L 2024 has no ECL/impairment lines; correctly no FY2024 impairment fact."],
        missing=[("debt_issued", "CF p8: Proceeds from long-term loan 427,000,000 / 833,000,000 - NOT carried"),
                 ("debt_repaid", "CF p8: Repayment of long-term loan (380,845,940) / (360,571,429) - NOT carried"),
                 ("lease_payments", "CF p8: Change in lease obligations (1,653,956) / (3,410,133) - NOT carried"),
                 ("weighted_average_shares", "not carried"),
                 ("share_of_profit_associates", "CF p8 profits from associates (2,199,119)/(4,309,236); no separate P&L line, so not derivable from the face P&L")],
        fix="add debt_issued/debt_repaid/lease_payments to the Yamama manifest (Codex); split the impairment composite (AUDIT-E-3020-1)"),
    "3040": dict(defects=[], observations=[
        "FY2024 comparatives are RESTATED (face statements headed 'Restated note 37'); Note 37 (pdf p50) confirms PP&E +77.3m fair-value adjustment less 7.5m additional depreciation, so manifest FY2024 values are the restated ones, as labelled. No pre-restatement FY2024 filing exists in the repo; a future original FY2024 filing would differ.",
        "Hail Cement was acquired 10 June 2024 (Note 36): FY2024 comparative contains Hail for about 6.5 months only; FY2025 vs FY2024 growth is not like-for-like.",
        "Composites verified: long_term_investments 184,873,756 + 100,000,000 (2024: 76,164,241 + 100,000,000); other_reserves 270,000,000 + (960,381) (2024: + 116,709); other_current_liabilities 55,353,806 + 817,314 (2024: 53,947,760 + 817,314); other_nonoperating_income 2,003,172 + 3,522,047 (2024: 21,295,976 + 1,768,591); depreciation 120,491,520 + 12,182,652 + 126,266; capex 261,655,931 + 4,187,641.",
        "Manifest notes cite 'SAR 184,873,756k' (stray k); the values themselves are full SAR and correct (documentation typo only).",
        "Tool artefact, not a defect: the text-layer matcher first picked the CF add-back '(Reversal)/allowance for expected credit loss' for the P&L fact; P&L pdf p9 text and image both show 1,251,729 / (3,651,540), equal to the manifest."],
        missing=[("weighted_average_shares", "not carried"),
                 ("debt_repaid", "none disclosed (only Proceeds from short term borrowings 100,000,000)"),
                 ("investing detail", "CF p11 proceeds from disposal of PPE 552,579, sale of FVTPL investments 191,934,421, investment income 12,764,325 not carried")],
        fix="none for numbers"),
}
SHARED_META = dict(
    id="AUDIT-E-META-1", cls="metadata / point-in-time", severity="medium-low", where="manifest.filed_at",
    detail="filed_at equals the Board approval date from the notes, which is earlier than the Saudi Exchange publication timestamp in source_url (and for 3002 earlier than the 6 April 2026 audit-opinion date). Canonicalization ranks facts by filed_at and as-of queries use it, so facts become 'known' 6-9 days before the audited document was public.",
    proof="tools/e_filed_at_check.py over data/imports: 11 of 12 fsPdf-sourced manifests have filed_at < URL publication date; Group E: 3002 03-29 vs 04-06, 3003 03-16 vs 03-24, 3005 03-12 vs 03-17, 3020 02-16 vs 02-25, 3040 02-16 vs 02-25.",
    fix="general: derive filed_at from the fsPdf URL timestamp (publication) or audit-report date; keep the board date in notes. Offline test tests/test_audit_batch2_e_cement.py::test_filed_at_not_before_publication (strict xfail until fixed). Not applied to data/**.")


def main():
    arch_idx = json.load(open(os.path.join(ROOT, "data", "raw", "archive-index.json"), encoding="utf8"))
    for sym, meta in META.items():
        man = json.load(open(os.path.join(ROOT, "data", "imports", meta["manifest"]), encoding="utf8"))
        tr = json.load(open(os.path.join(HERE, "e_transcripts", sym + ".json"), encoding="utf8"))
        pages = STMT_PAGES[sym]
        arch = next((x for x in arch_idx["artifacts"] if x["company_id"] == "sa:" + sym), None)
        items = []
        for f in man["facts"]:
            t = tr["facts"][f["metric"]]
            t = t if isinstance(t, dict) else t[0]
            v = t["v2025"] if f["period_end"].startswith("2025") else t["v2024"]
            if isinstance(v, list):
                v = sum(v)
            src = None if v is None else v * t.get("sign", 1)
            ok = src is not None and float(f["value"]) == src
            st = pages.get(f["page"], ("?", None))
            items.append(dict(metric=f["metric"], period_end=f["period_end"], period_kind=f["period_kind"],
                              statement=st[0], printed_page=f["page"], pdf_page=st[1], source_label=f["source_label"],
                              published_value=f["value"], source_value=src,
                              status="verified_correct" if ok else "unverified"))
        nver = sum(1 for i in items if i["status"] == "verified_correct")
        fnd = FIND[sym]
        defects = list(fnd["defects"]) + [dict(SHARED_META, id=SHARED_META["id"] + "-" + sym)]
        rep = dict(
            symbol=sym, company=meta["name"], audited_branch=BRANCH, source_archive_branch=RAW_BRANCH,
            auditor_session="claude/audit-saudi-batch2-E (Group E)",
            dimension_1_numeric_correctness=dict(
                verdict="verified_correct for %d of %d published facts against the printed statements; %d classification/definition defect(s); 1 metadata defect; 0 numeric mismatches" % (nver, len(items), len(fnd["defects"])),
                facts_checked=len(items), facts_verified_correct=nver,
                facts_unverified=len(items) - nver, method=meta["method"],
                sign_convention="outflows/expenses stored negative; depreciation_amortization stored negative although the add-back is printed positive (repo convention, engine uses abs)",
                defects=defects, observations=fnd["observations"]),
            dimension_2_document_completeness=dict(
                verdict="one source document audited; its primary statements are covered, notes and the equity statement are not",
                sources=[dict(
                    status="done", document="Annual 2025 audited financial statements (FY2025 with FY2024 comparatives)",
                    source_url=man["source_url"], archive=arch["local_path"] if arch else None,
                    sha256=arch["content_hash"] if arch else None, bytes=arch["byte_size"] if arch else None,
                    company_identity="cover/headers name %s; manifest company_id %s symbol %s" % (meta["name"], man["company_id"], man["symbol"]),
                    consolidated=meta["consolidated"], unit_scale=meta["unit"],
                    period="FY2025-01-01..2025-12-31 with FY2024 comparatives; period_kind fy/instant and fiscal_year labels 2025/2024 correct on all facts; no duplicate (metric, period) keys",
                    auditor=meta["auditor"], board_approval=meta["board"], filed_at_published=man["filed_at"],
                    checks_performed=["identity", "period/fiscal-year labels", "currency and unit/scale", "sign convention",
                                      "balance sheet", "income statement", "cash flow",
                                      "quarter-vs-cumulative (n/a: annual only)", "restated comparatives",
                                      "subtotal re-addition", "composite lines re-added"],
                    visual_coverage=meta["visual"],
                    statement_pages=[dict(printed_page=k, statement=v[0], pdf_page=v[1]) for k, v in pages.items()],
                    facts=items,
                    missing_fields_present_in_source=[dict(field=a, evidence=b) for a, b in fnd["missing"]],
                    not_checked=["statement of changes in equity values (not carried as facts)",
                                 "notes other than those cited above", "auditor's report text beyond identity/date"])]),
            dimension_3_company_coverage=dict(
                verdict="THIN: one fiscal year (FY2025) plus FY2024 comparatives from a single annual filing; no quarterly, no interim, no pre-2024 history",
                manifests_published=1, fiscal_years_covered=[2024, 2025],
                fiscal_years_missing="all earlier years and all interim periods (Q1-Q3, H1, 9M); FY2024 exists only as comparatives, not as its own original filing",
                not_proven="whether Saudi Exchange offers earlier/interim statements for this symbol was not checked online (no network use)"),
            fix_plan=fnd["fix"], tests="tests/test_audit_batch2_e_cement.py (offline)")
        with open(os.path.join(OUT, sym + ".json"), "w", encoding="utf8") as fh:
            json.dump(rep, fh, indent=1, ensure_ascii=False)
        print(sym, nver, len(items))


main()
