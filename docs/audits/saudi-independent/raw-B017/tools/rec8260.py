"""Builds raw-B017/8260.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SAR 000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("05cbd6dd", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 12}, {"bs": 8, "is": 9, "cf": 12},
        "text rows plus image read of the income statement (all values tie by identity)",
        "Going concern: material uncertainty paragraph in the auditors' report (pdf p3) and note 2(b) (pdf p14): accumulated losses 259 million (86% of capital), solvency ratio 52% versus 100% minimum, 50,000 subordinated shareholder loan. Statements are combined; insurance operations and shareholders operations supplementary statements follow at pdf p86-91 (not transcribed)."),
    doc("951540a4", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 12}, {"bs": 8, "is": 9, "cf": 12}, "visual (pdf p8-12 textless)",
        "2024 goodwill impairment 36,260 inside net loss; capital reduced 500,000 to 300,000 in 2024 (comparative EPS 2023 therefore 0.12 here versus 0.07 as first issued)."),
    doc("9062d8a2", "FY ended 2023-12-31 audited FS, first IFRS 17 year, 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 13}, {"bs": 8, "is": 9, "cf": 13}, "visual",
        "EPS 2023 printed 0.07 on 50,000 thousand shares; restated to 0.12 on 30,000 thousand shares in the FY2024 filing (share-capital reduction). Investing cash flow split differs between this filing and the FY2024 comparative (Murabaha placements -12,756 versus -10,000, commission 6,821 versus 4,065) with identical CFI -5,917."),
    doc("618d4f55", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "12-13"}, {"bs": 6, "is": 7, "cf": "10-11"}, "visual (statement pages textless)",
        "IFRS 4 presentation (gross written premiums 373,293, total revenues 258,702); restated to IFRS 17 in the FY2023 filing. Both declared; neither substituted."),
    doc("08af868a", "3M and 6M ended 2026-06-30 unaudited interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 5, "is": 6, "cf": 9}, {"bs": 3, "is": 4, "cf": 7}, "visual (pdf p4-9 textless)",
        "review report states solvency ratio non-compliance (note 17); income columns 3M 2026, 3M 2025, 6M 2026, 6M 2025; cash flow six-month only"),
    doc("4cfca767", "3M ended 2026-03-31 unaudited interim (label 2026|Q1 correct)", True, {"bs": 5, "is": 6, "cf": 9}, {"bs": 5, "is": 6, "cf": 9}, "visual (pdf p3-9 textless)",
        "review report (pdf p4) carries a Material Uncertainty Related to Going Concern paragraph and the 30 April 2026 agreement to issue 17,600,000 new shares (176 million, of which 50 million converts the subordinated loan)"),
]
cv = "(cover text)"
identified = {
    "7f3e8150": ("3M and 6M ended 2016-06-30 interim " + cv, "not opened beyond cover; inventory partial_statements"),
    "d3a82f68": ("Arabic board report for FY2016 (annual_report_no_state)", "no primary statements per inventory; not opened"),
    "8c90d07f": ("Arabic board report FY2017 (annual_report_no_state)", "not opened"),
    "83ffdfa9": ("Arabic board report FY2018 (annual_report_no_state)", "not opened"),
    "a5efcd27": ("Arabic board report FY2025 (annual_report_no_state)", "not opened; narrative only per inventory"),
    "898e7b87": ("3M and 9M ended 2022-09-30 interim " + cv, "not transcribed"),
    "f180b259": ("3M and 6M ended 2022-06-30 interim " + cv, "not transcribed"),
    "e09614b7": ("3M ended 2022-03-31 interim " + cv, "not transcribed"),
    "42fb4dd7": ("3M and 9M ended 2023-09-30 interim " + cv, "not transcribed"),
    "0c2ca53e": ("6M ended 2023-06-30 interim, English (KPMG report)", "not transcribed"),
    "974b401a": ("3M ended 2023-03-31 interim, English (KPMG report)", "not transcribed"),
    "56ab0435": ("6M ended 2023-06-30 interim, Arabic twin (scrambled text layer)", "not transcribed"),
    "20f3f264": ("3M ended 2023-03-31 interim, Arabic twin (scrambled text layer)", "not transcribed"),
    "fe64f442": ("3M and 9M ended 2024-09-30 interim, English " + cv, "not transcribed"),
    "ed06cdb4": ("3M and 6M ended 2024-06-30 interim " + cv, "not transcribed"),
    "dc2e1981": ("3M ended 2024-03-31 interim " + cv, "not transcribed"),
    "4ff1752c": ("3M and 9M ended 2025-09-30 interim, English " + cv, "not transcribed"),
    "27234b99": ("3M and 6M ended 2025-06-30 interim, English " + cv, "not transcribed; H1 2025 comparatives read in the H1 2026 filing"),
    "c61de616": ("3M ended 2025-03-31 interim, English " + cv, "not transcribed; Q1 2025 comparatives read in the Q1 2026 filing"),
    "d3469b27": ("6M ended 2025-06-30 interim, Arabic twin", "not transcribed"),
    "6b2f6584": ("3M ended 2025-03-31 interim, Arabic twin", "not transcribed"),
    "e73ca8ca": ("9M 2025 interim, Arabic twin (period per label)", "not transcribed"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_restatements_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) read for FY2025, FY2024, FY2023 (2022 restated), FY2022 as issued under IFRS 4, H1 2026 and Q1 2026. All identities pass exactly (balance sheet, cash-flow sum and roll, pre-zakat result less zakat equals net result). FY2025: insurance revenue 321,752, loss before zakat -116,988, net loss -120,488 (EPS -4.02), total assets 349,043, equity 165,114 (after a 50,000 subordinated shareholder loan), CFO -124,385, closing cash 8,179. FY2024 net loss -94,207 (including goodwill impairment 36,260); FY2023 net profit 3,532; FY2022 IFRS 4 net loss -104,190 versus IFRS 17 restated -106,017. H1 2026 net loss -29,488 (Q1 -14,019, Q2 -15,469); Q1 + Q2 = H1 for revenue, loss before zakat, zakat and net loss in 2026 and 2025 (pass). Declared: IFRS 4 to IFRS 17 FY2022 restatement; FY2023 EPS 0.07 as issued versus 0.12 after share-capital reduction; investing-line reclassification in the 2023 cash flow (totals equal). Insurance service expense is printed in brackets (negative). Going-concern material uncertainty is present in the FY2025 audit report and Q1 2026 review report.",
        "not_read": ["notes (except note 2(b) going concern text)", "statements of changes in equity (except H1/Q1 2026 pages)", "insurance operations vs shareholders operations supplementary statements (FY2025 pdf p86-91)", "Q2 cash flow by subtraction not validated", "all other 36 files", "segment-note totals versus the primary balance sheet"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_six_files_opened_four_of_them_image_only",
        "summary": "Six files carry balance sheet, income statement and cash flow: FY2025 has a real text layer; FY2024, FY2022, H1 2026 and Q1 2026 statement pages are image-only although the inventory classes them financial_statements. Files 2015 to 2021 are partly scanned_unreadable (bc7e2ef5, ed8826fd, 016f0a3d, 8b2c061d, fb388d57, 0255de1d, 1f175522, b1f26a00, 10c59fb2, 3af519c5) or carry scrambled Arabic text layers (f82964ed, d43b307d, eabf71c4, 4e4a9b9c, 19bebc43, 5881d67e, f8453c58, 1074e985) and were not opened as images, so their period content is unverified. Arabic and English twins exist for several 2023 to 2025 interims; the Arabic twins were not compared. 3af519c5 has no collector fiscal year or period (None|None).",
        "defect_ids": ["B017-8260-1", "B017-8260-2", "B017-8260-3", "B017-8260-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_verified_interims_2022_to_2026_H1_present_older_history_unread",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1",
                                                    "2015 to 2021 interims and FY2016-FY2018/FY2020 files exist by label only, unverified"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing)", "FY2022 IFRS 17 restated (FY2023 filing)", "2025 Q1 and H1 (2026 filings)"],
        "values_not_read": ["2022 to 2025 interim originals", "all 2015 to 2021 files"],
        "missing": ["FY2019 and FY2021 own annual statements (no file labelled so; 1074e985 2019|None is unidentified)", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in the four FS files read. Several 2015 to 2021 files could not be period-identified from text.",
    },
}
defects = [
    {"id": "B017-8260-1", "class": "image_only_or_scanned_statements_flagged_as_present", "severity": "high",
     "evidence": "951540a4 pdf p8-12, 618d4f55 statement pages pdf p8-13 (textless), 08af868a pdf p4-9, 4cfca767 pdf p3-9 are image-only; ten older files are scanned_unreadable."},
    {"id": "B017-8260-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "618d4f55 FY2022 labelled 2023|FY, 9062d8a2 FY2023 labelled 2024|FY, 951540a4 FY2024 labelled 2025|FY, 05cbd6dd FY2025 labelled 2026|FY. 3af519c5 has no label."},
    {"id": "B017-8260-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "IFRS 17 transition: FY2022 net loss -104,190 as issued (618d4f55 pdf p9) versus -106,017 restated (9062d8a2 pdf p9); total assets 602,511 versus 481,552 (pdf p8); CFO -97,589 versus -100,898 (pdf p12-13 versus p13). FY2023 EPS 0.07 versus 0.12 (9062d8a2 pdf p9 versus 951540a4 pdf p9). Both recorded, none substituted."},
    {"id": "B017-8260-4", "class": "going_concern_and_arabic_twins", "severity": "high",
     "evidence": "FY2025 (05cbd6dd pdf p3, p14) and Q1 2026 (4cfca767 pdf p4) carry material uncertainty on going concern; solvency ratio 52% at FY2025. Arabic and English twin interims coexist for 2023 to 2025 and the Arabic ones have scrambled text layers."},
]
unread = ["notes (except note 2(b))", "statements of changes in equity (except H1 and Q1 2026)", "insurance operations vs shareholders operations supplementary statements", "22 or more interim filings 2022 to 2025 and all 2015 to 2021 files (identified by cover where text exists)",
          "Arabic twins vs English comparison", "FY2019 and FY2021 own annual statements (not found by label)", "segment-note totals versus the primary balance sheet"]
conclusion = ("NOT claimed complete. Six filings value-verified from rendered pages (FY2022 as issued, FY2023, FY2024, FY2025, Q1 2026, H1 2026); IFRS 4 to IFRS 17 FY2022 restatement and FY2023 EPS restatement declared with both values; "
              "the many 2015 to 2025 interim and annual files are identified at most by cover and not value-read; going-concern uncertainty flagged for FY2025 and Q1 2026.")
mkrecord.build(dict(
    symbol="8260", name="GULF GENERAL COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Statement pages rendered and read by eye (FY2025 text layer used only after checking against images). "
            "tools/check_transcripts.py over transcripts/8260.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat to net result, cross-filing comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls for revenue, loss before zakat, zakat and net loss (2026 and 2025); all pass.")))
