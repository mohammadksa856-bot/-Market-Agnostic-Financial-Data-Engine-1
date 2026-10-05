"""Builds raw-B016/8120.json from the page transcripts."""
import mkrecord

U = "SAR full riyals as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


T = "text layer, tied by arithmetic"
documents = [
    doc("ecca065f", "FY ended 2025-12-31 audited FS in annual report (collector label 2026|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "12-13"}, {"bs": 7, "is": 8, "cf": "11-12"}, T,
        "net loss -83,626,718 (EPS -1.82), accumulated losses -46,861,637; going-concern note p15 states the going-concern basis; auditor report p6 not read beyond standard wording"),
    doc("72d9553f", "FY ended 2024-12-31 audited FS in annual report (label 2025|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "12-13"}, {"bs": 7, "is": 8, "cf": "11-12"}, T),
    doc("bf341b2f", "FY ended 2022-12-31 audited FS as issued under IFRS 4 in annual report (label 2023|FY = publication year)", False, {"bs": 10, "is": "11-12", "cf": "16-17"}, {"bs": 9, "is": "10-11", "cf": "15-16"}, T,
        "pdf p3-9 textless (auditor report); statement pages have a text layer; contains the 2021 comparatives (loss -141,189,259)"),
    doc("f518cfe1", "9M 2025 interim (label 2025|9M correct); nine and three months", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, T),
    doc("4bc33d9d", "H1 2025 interim (label 2025|H1 correct); six and three months", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, T),
    doc("a9efebce", "Q1 2026 interim (label 2026|Q1 correct); three months", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, T),
    doc("6d995550", "H1 2026 interim (label 2026|H1 correct); six and three months", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 2, "is": 3, "cf": 6}, T),
]
identified = {
    "e9810ff7": ("FY2023 audited FS in annual report (label 2024|FY); statement pages pdf p11-17 image-only. NOT READ in this audit (page images were not viewable). FY2023 values are verified only as the comparative column of the FY2024 filing (72d9553f). The IFRS 17 restated FY2022 column in this file is UNREAD", "statements not read"),
    "c5cbd36d": ("9M 2022 interim, whole-file 61-page scan classed scanned_unreadable (all pages textless); NOT READ, statement content unverified", "statements not read"),
    "977d4749": ("Q1 2022 interim (cover: three months ended 31 March 2022); pdf p3-10 textless", "statements not opened; not transcribed; notes include a business combination note 4 (heading only seen)"),
    "bc8e8e5b": ("H1 2022 interim (balance sheet text read: 30 June 2022 total assets 1,049,459,194, net equity 321,471,221); cover and pdf p11-60 textless", "only the balance-sheet headline read; income and cash-flow not transcribed"),
    "0e299886": ("Q1 2023 interim (cover: three months ended 31 March 2023); pdf p7 textless", "not transcribed"),
    "fff82a49": ("H1 2023 interim (cover: ended 30 June 2023); pdf p4-9 textless", "not transcribed"),
    "3e2edac2": ("9M 2023 interim (cover: ended 30 September 2023); pdf p4-9 textless", "not transcribed"),
    "aab0f402": ("Q1 2024 interim (cover: ended 31 March 2024); pdf p4-9 textless", "not transcribed"),
    "4fe96053": ("H1 2024 interim (cover: ended 30 June 2024); pdf p4-9 textless", "not transcribed; H1 2024 values known only as comparatives in 4bc33d9d"),
    "3b4941aa": ("9M 2024 interim (cover: ended 30 September 2024)", "not transcribed; known only as comparatives in f518cfe1"),
    "c1acb5d7": ("Q1 2025 interim (cover: ended 31 March 2025); pdf p4-9 textless", "not transcribed; Q1 2025 values known only as comparatives in a9efebce"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_7_filings_FY2023_via_comparatives_IFRS17_restated_FY2022_unread",
        "summary": ("Headline balance sheet, income and cash-flow values (SAR full riyals as printed) read from text layers and tied by arithmetic for FY2025, FY2024, FY2022 as issued (IFRS 4), 9M 2025, H1 2025, Q1 2026 and H1 2026; FY2023 is verified only through the comparative column of the FY2024 filing. Balance-sheet identity, cash-flow sum and roll, and pre-zakat result less zakat/tax = net result hold exactly; eight roll checks close exactly. "
                    "FY2025: insurance revenue 1,038,197,346, net loss -83,626,718 (EPS -1.82), total assets 1,157,085,266, equity 568,942,632, CFO -89,145,754. FY2024: 804,752,396 and 43,645,516. FY2023 (comparative): 624,483,382 and 125,037,351. FY2022 as issued under IFRS 4: total revenues 434,827,553, net profit 2,523,564, total assets 1,053,695,384, equity 334,592,277. H1 2026: insurance revenue 464,732,809, net profit 1,682,232. "
                    "FY2022 was restated for IFRS 17 in the FY2023 filing (e9810ff7), but that file's image-only pages were NOT read, so the restated FY2022 values are UNVERIFIED and not recorded; FY2022 as issued must not be used as the IFRS 17 basis. FY2024 and FY2023 comparatives in later filings agree exactly. "
                    "Insurance and shareholder operations are not presented separately."),
        "not_read": ["notes in every file (except note headings)", "statements of changes in equity", "FY2023 filing statements (image-only, not viewed) incl. restated FY2022 column", "9M 2022 whole-file scan statements", "FY2025 auditor report beyond standard wording",
                     "own filings of Q1 2022, H1 2022 (headline only), 2023 interims, Q1/H1/9M 2024, Q1 2025", "FY2021 and earlier (comparatives only)"],
    },
    "document_completeness": {
        "status": "primary_statements_present_for_every_period_2022Q1_to_2026H1_several_statement_sets_image_only",
        "summary": ("Eighteen files give a statement set for every period from Q1 2022 to H1 2026 (annual FY2022 to FY2025 inside annual reports with embedded FS). Image-only statement pages: FY2023 annual report (pdf p11-17), the 9M 2022 file is a whole-file 61-page scan flagged scanned_unreadable (its content was NOT viewed in this audit, so whether it holds statements is unverified), H1 2022 (text only on pdf p4-10), Q1 2022 (p3-10), H1/9M 2023 (p4-9), Q1 2024 and H1 2024 (p4-9), Q1 2025 (p4-9). "
                    "No Arabic twins in the collection (all files English). Every annual item is an annual report with embedded audited FS, not a standalone FS file."),
        "defect_ids": ["B016-8120-1", "B016-8120-2", "B016-8120-3", "B016-8120-4"],
    },
    "company_coverage": {
        "status": "contiguous_quarterly_and_annual_coverage_2022Q1_to_2026H1_nothing_earlier_than_2022",
        "present_in_files_by_page_derived_period": ["2022 Q1", "2022 H1", "2022 9M", "FY2022 (label 2023|FY)", "2023 Q1", "2023 H1", "2023 9M", "FY2023 (label 2024|FY)", "2024 Q1", "2024 H1", "2024 9M", "FY2024 (label 2025|FY)",
                                                    "2025 Q1", "2025 H1", "2025 9M", "FY2025 (label 2026|FY)", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued)", "FY2024", "FY2025", "2025 H1 and Q2", "2025 9M and Q3", "2026 Q1", "2026 H1 and Q2"],
        "values_known_only_as_comparatives": ["FY2023 (FY2024 filing)", "FY2021 (FY2022 filing)", "2024 H1/Q2 and 9M/Q3 (2025 filings)", "2025 Q1 (Q1 2026 filing)", "FY2022 restated, 1 Jan 2022 restated (FY2023 filing)"],
        "values_not_read": ["FY2023 own filing and restated FY2022", "2022 9M", "2022 Q1", "2022 H1 (balance sheet headline only)", "2023 Q1, H1, 9M", "2024 Q1, H1, 9M own filings", "2025 Q1 own filing"],
        "missing": ["FY2021 and earlier (no file; the inventory expected window starting 2009 is a collector artefact, not a gap in this collection), 2022 FY slot by label (FY2022 sits at 2023|FY)"],
        "inventory_corrections": ("Annual labels equal publication year: 2023|FY holds FY2022, 2024|FY holds FY2023, 2025|FY holds FY2024, 2026|FY holds FY2025; the labels 2022|FY and earlier do not exist. The inventory therefore counts 49 'absent' periods dominated by a window opening at 2009 that precedes the collection. "
                                  "Entity: Gulf Union Alahlia Cooperative Insurance Company; share capital doubled from 229,474,640 to 458,949,280 in 2022 with a business-combination note (note 4 of the Q1 2022 filing, heading only seen), so 2021 and earlier figures describe the pre-combination entity."),
    },
}
defects = [
    {"id": "B016-8120-1", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "Annual FS files carry labels one year ahead: bf341b2f (cover and statements FY2022) is 2023|FY, e9810ff7 (FY2023) 2024|FY, 72d9553f (FY2024) 2025|FY, ecca065f (FY2025) 2026|FY; no 2022|FY label exists although FY2022 is present."},
    {"id": "B016-8120-2", "class": "image_only_or_scanned_statements_flagged_as_present_or_unreadable", "severity": "high",
     "evidence": "c5cbd36d (9M 2022) is classed scanned_unreadable with all 61 pages textless (tl.py); content not viewed, so statement presence is unverified. e9810ff7 statements pdf p11-17 are textless although classed annual_report_with_state and were not viewed either. Eight more interims have textless statement or note pages per tl.py (Q1 2022, H1 2022 p11 onward, Q1 2023 p7, H1/9M 2023, Q1/H1 2024, Q1 2025)."},
    {"id": "B016-8120-3", "class": "restated_or_represented_comparatives_ifrs17", "severity": "high",
     "evidence": "FY2022 as issued under IFRS 4 (bf341b2f pdf p10-12) was restated for IFRS 17 in the FY2023 filing (e9810ff7 pdf p11-17, image-only). The restated values were NOT read in this audit; the existence of the restatement is known from the FY2023 filing notes/headings only and its amounts are unverified. FY2022 as issued is recorded as issued."},
    {"id": "B016-8120-4", "class": "net_loss_year_with_going_concern_basis_stated", "severity": "low",
     "evidence": "FY2025 net loss -83,626,718, accumulated losses -46,861,637 against equity 568,942,632 (ecca065f pdf p8-9); pdf p15 states the financial statements are prepared on a going-concern basis after a management assessment; no material uncertainty identified in the pages read (auditor opinion not read in full). Quarterly 2025 results were losses in Q1-Q3."},
]
unread = ["notes in every file", "statements of changes in equity", "cash-flow and equity statements of 9M 2022 scan", "income and cash-flow statements of H1 2022", "Q1 2022 statements (textless)", "2023 Q1/H1/9M interims", "Q1/H1/9M 2024 own filings", "Q1 2025 own filing",
          "FY2025 auditor report", "business combination note 4 (2022) detail", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Seven filings value-verified (FY2022 as issued, FY2024, FY2025, 9M 2025, H1 2025, Q1 2026, H1 2026; FY2023 only as a comparative); the IFRS 17 restatement of FY2022 exists but its values are unread. "
              "Statement files exist for every period Q1 2022 to H1 2026 by page-derived period, but eleven of them are unread or identified by cover only and are unread; no pre-2022 filing exists.")
mkrecord.build(dict(
    symbol="8120", name="GULF UNION ALAHLIA COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Born-digital statement pages read from the text layer with tools/rows.py; FY2023 and 9M 2022 statement pages are image-only and were NOT read (page images were unavailable); FY2023 is taken from comparatives. "
            "tools/check_transcripts.py over transcripts/8120.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result less zakat/tax to net result, cross-filing comparatives (the restated FY2022 columns are flagged) and eight Q1+Q2=H1 / H1+Q3=9M roll checks; all pass.")))
