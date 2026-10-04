"""Builds raw-B016/8313.json from the page transcripts."""
import mkrecord

U = "SAR full riyals as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


T = "text layer, tied by arithmetic"
documents = [
    doc("bb6fc163", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 11}, {"bs": 6, "is": 7, "cf": 9}, T,
        "31 Dec 2025 balance sheet is later restated in the H1 2026 filing (total assets 988,752,885, not 1,347,885,386); see defect B016-8313-3"),
    doc("2f31a99e", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 9, "is": 10, "cf": 12}, {"bs": 7, "is": 8, "cf": 10}, T),
    doc("9ca661d8", "FY ended 2023-12-31 audited FS (label 2024|FY = publication year; shares the slot with FY2022 EN and FY2024 AR)", False, {"bs": 6, "is": 7, "cf": 9}, {"bs": 4, "is": 5, "cf": 7}, T,
        "pre-IPO closed joint stock company; equity statement shows a non-controlling-style retained earnings split not carried into the FY2024 filing (all 2023 profit attributed to shareholders there)"),
    doc("4a453924", "FY ended 2022-12-31 audited FS, English (label 2024|FY, wrong slot)", False, {"bs": 6, "is": 7, "cf": 9}, {"bs": 4, "is": 5, "cf": 7}, T,
        "EPS 13.494 (pre-split) versus 0.49 in the FY2023 filing; cash flow comparative differs by 2 riyals from the FY2023 filing"),
    doc("0ad38a49", "FY ended 2021-12-31 audited FS, English (label 2021|FY correct); also holds 2020 and 1 Jan 2020 balance sheet", True, {"bs": 6, "is": 7, "cf": 9}, {"bs": 4, "is": 5, "cf": 7}, T,
        "2020 shows partners' deficit -17,502,697 (LLC at that date)"),
    doc("9f58f106", "H1 2026 reviewed interim, English (label 2026|H1 correct); six months and three months; note 20 restatements", True, {"bs": 4, "is": 5, "cf": 7, "note20": "23-29"}, {"bs": 2, "is": 3, "cf": 5}, T),
    doc("9b0ee4a0", "Q1 2026 interim, English (label 2026|Q1 correct); as originally issued", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5}, T,
        "31 March 2026 balance sheet later restated for time deposits 225,686,217 (restatement 4 of the H1 2026 filing)"),
    doc("7a2bc186", "9M 2025 interim, English (label 2025|9M correct); nine and three months; as originally issued", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5}, T),
    doc("0ae692ef", "H1 2025 interim, English (label 2025|H1 correct); six and three months; as originally issued", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5}, T,
        "H1 2025 profit and revenue restated in the H1 2026 filing; both values declared"),
]
identified = {
    "6f9a352d": ("IPO factsheet (English, 1 page, cover text: listing 30% of share capital on the Main Market)", "not a statement; no label (None|None)"),
    "f5c70d86": ("IPO factsheet (Arabic/mixed, 1 page)", "not a statement; no label"),
    "9f387dd1": ("segmental revenue reconciliation, 1 page (cover text), label None|H1", "not a statement; period not stated in the text read"),
    "318e31ac": ("segmental revenue reconciliation, Arabic, 1 page, label 2026|H1", "not a statement"),
    "46297b17": ("FY ended 2021-12-31 audited FS, Arabic twin (label 2021|FY correct; balance sheet totals and 2020/1 Jan 2020 columns checked against the English file)", "Arabic twin, only the balance sheet head read; no value conflict seen"),
    "9e888147": ("FY ended 2022-12-31 audited FS, Arabic twin (label 2022|FY correct for this file; balance sheet total assets 133,674,054 and 86,500,558 seen)", "Arabic twin; only balance sheet read"),
    "50f113f1": ("FY ended 2024-12-31 audited FS, Arabic twin (label 2024|FY; text layer has reversed Arabic-Indic digits, e.g. 75,800,000 share capital and 188,444,330 share premium recognisable reversed)", "text layer scrambled; digit-reversed read of two lines only; not transcribed"),
    "91b31f8e": ("Annual Report 2024, Arabic (label 2024|FY), classed annual_report_with_state; statements pages 28 flagged are summary", "not opened beyond cover; primary FS taken from 2f31a99e"),
    "cab9b368": ("Annual Report 2024, English (label 2024|FY)", "not opened beyond cover"),
    "4578bf39": ("Annual Report 2025, Arabic (label 2025|FY; contains no statements per inventory)", "not opened beyond cover"),
    "fa82549a": ("Annual Report 2025, English (label 2025|FY; no statements per inventory)", "not opened beyond cover"),
    "9ccdf375": ("results announcement infographic, bilingual, 1 page (label 2025|FY)", "not opened for values; period unverified"),
    "599957d2": ("label 2024|9M, 19 pages, text layer scrambled (EY letterhead), classed partial_statements", "Arabic twin of 9M 2024 by inventory and page count; scrambled text, not opened visually"),
    "ca93c5e8": ("9M 2024 interim, English (cover: ended 30 September 2024)", "not transcribed; 9M 2024 values known only as comparatives in 7a2bc186"),
    "205813d8": ("H1 2024 interim, Arabic twin (cover text)", "not transcribed"),
    "714851d1": ("H1 2024 interim, English (cover: ended 30 June 2024)", "not transcribed; H1 2024 values known only as comparatives in 0ae692ef"),
    "e6a6cbb4": ("Q1 2024 interim, English (cover: ended 31 March 2024)", "not transcribed"),
    "7c352b0c": ("9M 2025 interim, Arabic twin (cover text)", "not transcribed"),
    "de690189": ("Q3 2025 results infographic, 1 page image-only (rendered and read: 9M 2025 revenue 439.6m, net profit 157.4m), inventory class scanned_unreadable", "not a statement; headline figures agree with 7a2bc186 (439,553,374; 157,339,174)"),
    "26541f9d": ("Q2 2025 results infographic, 1 page image-only (rendered: H1 2025 revenue 244.7m, net profit 75.0m, the original unrestated values)", "not a statement; agrees with 0ae692ef"),
    "9b4ce811": ("H1 2025 interim, Arabic twin (cover text)", "not transcribed"),
    "03bffd20": ("label 2025|Q1, 16 pages, scrambled text (EY letterhead), classed other_no_statements_found", "Arabic twin of Q1 2025 by page count; scrambled text, not opened visually; classed no statements although the English Q1 2025 file holds statements"),
    "55752332": ("Q1 2025 interim, English (cover: ended 31 March 2025)", "not transcribed; Q1 2025 values known from the Q1 2026 filing prior column (as reported then, unrestated)"),
    "10c4fea7": ("Q2 2026 results infographic, 1 page image-only (rendered: H1 2026 revenue 517m, net 174m; H1 2025 net 65m = restated)", "not a statement; agrees with 9f58f106"),
    "b418f3ed": ("Q2 2026 Earnings Release, 9 pages image-only (cover rendered; inventory class scanned_unreadable)", "presentation, not opened beyond the cover"),
    "32f06d72": ("Q1 2026 results infographic, 1 page image-only (rendered: revenue 261m, net 88m)", "not a statement; agrees with 9b0ee4a0"),
    "5580c272": ("Q1 2026 Earnings Release, 6 pages image-only (cover rendered)", "presentation, not opened beyond the cover"),
    "831b2d85": ("H1 2026 interim, Arabic twin (cover text)", "not transcribed"),
    "aabef47f": ("Q1 2026 interim, Arabic twin (cover text)", "not transcribed"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_9_filings_one_material_restatement_and_one_unexplained_roll_break_declared",
        "summary": ("Headline balance sheet, income and cash-flow values (SAR full riyals as printed) read from text layers and tied by arithmetic for FY2025, FY2024, FY2023, FY2022, FY2021 (with 2020 comparatives), "
                    "Q1 2026, H1 2026 (six and three months), 9M 2025 and H1 2025 (with 2024 comparatives). Balance-sheet identity, cash-flow sum and roll, gross profit, and pre-zakat income less zakat/tax = net income all hold exactly. "
                    "FY2025 (as issued): revenue 653,252,233, net income 246,806,413 (EPS 3.26), total assets 1,347,885,386, equity 705,438,900, CFO 333,422,120. FY2024: revenue 358,329,900, net income 94,727,797; FY2023: 256,234,155 and 45,952,326; FY2022: 162,491,088 and 34,409,436; FY2021: 86,898,916 and 35,279,886. "
                    "H1 2026: revenue 517,475,435, net income 174,128,603, total assets 1,256,772,289. Declared differences: (1) the H1 2026 filing (note 20) restates the 31 Dec 2025 balance sheet: total assets 1,347,885,386 as issued versus 988,752,885, equity 705,438,900 versus 718,700,287, cash 740,964,123 versus 756,175,300; "
                    "(2) it restates H1 2025: net income 75,017,564 as issued versus 64,905,581, revenue 244,735,828 versus 284,935,975, CFO 102,044,410 versus 76,940,584; Q2 2025 net income 45,016,311 versus 39,521,167; "
                    "(3) FY2022 EPS 13.494 versus 0.49 (share split) and a 2-riyal cash-flow rounding difference between the FY2022 and FY2023 filings; "
                    "(4) the 2026 six-month net income 174,128,603 does NOT equal Q1 2026 as issued 88,284,729 plus Q2 2026 85,163,327 (difference 680,547, sitting in operating expenses), unexplained by note 20. "
                    "All other Q1+Q2=H1, H1+Q3=9M and prior-year rolls close exactly. Whether FY2025 income statement figures were also reclassified (restatements 8-10 raised H1 2025 revenue by about 40m with no profit effect) is not shown for FY2025 and is unresolved."),
        "not_read": ["notes in every file except note 20 and parts of note 1/12 in H1 2026", "statements of changes in equity (read only for reconciling context)", "FY2025 revenue/segment restatement effect",
                     "H1 2024, Q1 2024, 9M 2024 and Q1 2025 own filings (comparatives only)", "all Arabic twins except balance-sheet heads", "auditor/review reports"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_text_layer_for_all_annuals_FY2021_to_FY2025_and_interims_2024_to_2026H1",
        "summary": ("English FY2021 to FY2025 audited FS and the interims Q1 2024 to H1 2026 (every quarter slot present, no Q3 2025 gap in English) each hold balance sheet, income statement, cash-flow statement and equity statement as born-digital text. "
                    "Six files classed scanned_unreadable are not statements: four are one-page results infographics (Q2 2025, Q3 2025, Q1 2026, H1 2026) and two are earnings-release decks (Q1 2026 6 pages, Q2 2026 9 pages), all read as images; their headline figures agree with the filings. "
                    "Two files with scrambled EY-letterhead text layers (599957d2, 03bffd20) are Arabic twins misclassed partial/no-statements. The 2024 and 2025 text layers of Arabic originals use reversed digits (50f113f1). "
                    "No Arabic twin exists for FY2023 and none for FY2025 FS in the collection (FY2025 Arabic FS not found by inventory)."),
        "defect_ids": ["B016-8313-1", "B016-8313-2", "B016-8313-3", "B016-8313-4", "B016-8313-5"],
    },
    "company_coverage": {
        "status": "annual_FY2021_to_FY2025_and_interims_2024Q1_to_2026H1_present_listing_2024_pre_IPO_interims_not_expected",
        "present_in_files_by_page_derived_period": ["FY2021", "FY2022 (EN + AR)", "FY2023 (EN)", "FY2024 (EN + AR)", "FY2025 (EN)", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2021", "FY2022", "FY2023", "FY2024", "FY2025 (as issued)", "2025 H1 and Q2 (as issued)", "2025 9M and Q3", "2026 Q1 (as issued)", "2026 H1 and Q2"],
        "values_known_only_as_comparatives": ["FY2020 (FY2021 filing)", "2024 H1 / Q2 / 9M / Q3 (2025 filings)", "2025 Q1 (Q1 2026 filing prior column)"],
        "values_not_read": ["2024 Q1 own filing", "2024 H1 own filing", "2024 9M own filing", "2025 Q1 own filing", "Arabic twins"],
        "missing": ["FY2020 and earlier own filings (company was an LLC; listed after FY2023)", "2022 and 2023 interims (inventory lists H1/9M 2022 and 2023 as absent; consistent with a pre-IPO closed joint stock company, but no file confirms no interims were published)"],
        "inventory_corrections": ("Annual FY labels: 2021|FY holds FY2021 (correct) and 2022|FY holds FY2022 (Arabic), but 2024|FY holds FY2022 EN, FY2023 EN and FY2024 AR plus two annual reports (one-file-per-label collision), 2025|FY holds FY2024 EN and 2026|FY holds FY2025 EN. "
                                  "Registry sector is null: Rasan is a fintech/insurtech platform (insurance aggregator Tameeni, payments), not an insurer; no insurance-operations/shareholders split exists."),
    },
}
defects = [
    {"id": "B016-8313-1", "class": "fiscal_year_label_mismatch_and_slot_collision", "severity": "medium",
     "evidence": "2024|FY holds four distinct annual items: FY2022 EN (4a453924, cover 'FOR THE YEAR ENDED 31 DECEMBER 2022'), FY2023 EN (9ca661d8), FY2024 AR (50f113f1) and two annual reports; 2025|FY holds FY2024 EN (2f31a99e) and 2026|FY holds FY2025 EN (bb6fc163). Labels are partly publication year, partly period."},
    {"id": "B016-8313-2", "class": "image_only_files_classed_unreadable_are_not_statements", "severity": "low",
     "evidence": "de690189, 26541f9d, 10c4fea7, 32f06d72 are 1-page infographics; b418f3ed and 5580c272 are earnings-release decks (covers rendered). None holds statements; no statement is hidden behind the scanned_unreadable class here."},
    {"id": "B016-8313-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "H1 2026 (9f58f106) pdf p4 and p25: 31 Dec 2025 total assets 988,752,885 versus 1,347,885,386 as issued in FY2025 (bb6fc163 pdf p8); equity 718,700,287 versus 705,438,900; p27 H1 2025 net income 64,905,581 versus 75,017,564 (0ae692ef pdf p5) and revenue 284,935,975 versus 244,735,828; p29 cash flow opening cash 473,500,112 versus 451,030,258. Both values recorded, none substituted."},
    {"id": "B016-8313-4", "class": "roll_does_not_close_unexplained", "severity": "medium",
     "evidence": "2026 six-month net income 174,128,603 (9f58f106 pdf p5) versus Q1 88,284,729 (9b0ee4a0 pdf p5) plus Q2 85,163,327 (9f58f106 pdf p5) = 173,448,056; difference 680,547 within operating expenses. Q2 2026 by subtraction (H1 less Q1) would give 85,843,874 and is not equal to the printed three-month figure."},
    {"id": "B016-8313-5", "class": "interim_balance_sheet_misclassification_corrected_later", "severity": "medium",
     "evidence": "Q1 2026 (9b0ee4a0 pdf p4) cash and cash equivalents 756,528,958 includes time deposits of 225,686,217 reclassified in the H1 2026 filing note 20 item 4 (pdf p23); Q1 2026 cash flow therefore overstates cash equivalents and understates investing outflow."},
]
unread = ["notes (except note 20 and extracts of notes 1 and 12 of H1 2026)", "statements of changes in equity (not transcribed)", "own filings of Q1 2024, H1 2024, 9M 2024, Q1 2025 (comparatives only)",
          "Arabic twins of all interims and FY2021, FY2022, FY2024 (only balance-sheet heads)", "annual reports 2024 and 2025 (covers only)", "earnings-release decks b418f3ed and 5580c272 beyond cover",
          "segmental reconciliation files 9f387dd1 and 318e31ac (1 page each, not read)", "FY2025 restated revenue (not shown anywhere in the collection)", "FY2020 and earlier, 2022-2023 interims (no file)"]
conclusion = ("NOT claimed complete. Nine English filings value-verified from text-layer pages (FY2021 to FY2025, Q1 2026, H1 2026, 9M 2025, H1 2025); a material restatement of the 31 Dec 2025 balance sheet and H1 2025 results is declared with both values, "
              "one unexplained 680,547 roll break in 2026 profit is flagged, and the Arabic twins and four earlier interims are unread.")
mkrecord.build(dict(
    symbol="8313", name="RASAN INFORMATION TECHNOLOGY COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Statement pages are born-digital text and were read from the text layer with tools/rows.py; the six scanned_unreadable files were rendered and read as images. "
            "tools/check_transcripts.py over transcripts/8313.json checks balance-sheet identity, cash-flow sum and roll, gross profit, pre-zakat income plus zakat and tax to net income, cross-filing comparatives (declared differences only) "
            "and eight Q1+Q2=H1 / H1+Q3=9M roll checks, one of which is a declared break with exact amount; all pass.")))
