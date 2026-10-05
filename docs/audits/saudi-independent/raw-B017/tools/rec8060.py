"""Builds raw-B017/8060.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SAR 000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("0ea15501", "FY ended 2025-12-31 audited consolidated FS (collector label 2026|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "13-14"}, {"bs": 6, "is": 7, "cf": "11-12"}, "visual (pdf p3-14 textless)",
        "Inventory class annual_report_no_statements is wrong: pdf p8-14 carry the full consolidated BS, IS and CF as images. Consolidated for the first time in 2025 (subsidiary acquired: goodwill 76,729, minority interest 2,900, purchase consideration paid 68,209). The H1 2026 filing re-presents the 31 Dec 2025 balance sheet (goodwill 76,729 to 51,571, intangibles 107,452 to 132,610; totals unchanged), see defect B017-8060-3."),
    doc("041b9f6a", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "13-14"}, {"bs": 8, "is": 9, "cf": "13-14"}, "visual (pdf p3-14 textless)",
        "FY2024 includes a 425,000 capital increase (share capital 850,583 to 1,275,583) and 35,161 share premium. Balance-sheet lines are presented differently from the 31 Dec 2024 comparative in the FY2025 filing (due from/to insurance operations 1,940 netted; accrued expenses 160,313 versus 162,253; prepaid 86,460 versus 88,400) with identical totals."),
    doc("a57b1123", "FY ended 2023-12-31 audited FS as first issued, with 2022 and 2021 restated (label 2024|FY = publication year)", False, {"bs": 12, "is": 13, "cf": "17-18"}, {"bs": 10, "is": 11, "cf": "15-16"}, "visual (pdf p3-18 textless)",
        "Zakat and tax presented as one line 15,000. FY2023 EPS 1.74 as issued versus 1.45 restated in the FY2024 filing. FY2023 cash flow re-presented in the FY2024 filing (CFO 422,928 to 423,386)."),
    doc("a8eaa7a2", "3M and 6M ended 2026-06-30 unaudited consolidated interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": "9-10"}, {"bs": 2, "is": 3, "cf": "7-8"}, "visual (pdf p3-10 textless; inventory partial_statements although all three statements present)",
        "income columns 3M 2026, 3M 2025, 6M 2026, 6M 2025; cash flow six-month only; Dec 2025 balance sheet marked Restated (goodwill and intangibles re-allocated)"),
    doc("531e3feb", "3M ended 2026-03-31 unaudited consolidated interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": "9-10"}, {"bs": 2, "is": 3, "cf": "7-8"}, "visual (pdf p3, p5-10 textless; inventory partial_statements although all three statements present)",
        "Dec 2025 comparative still shows the pre-reallocation goodwill 76,729 and intangibles 107,452; Q1 2026 CFO -2,553 versus H1 2026 CFO -23,367 (Q2 by subtraction -20,814) but the Q1 filing has no zakat line while H1 shows zakat paid, so Q2 by subtraction is NOT validated"),
]
nt = "not transcribed"
cv = "(cover text)"
identified = {
    "c86f43a7": ("3M and 9M ended 2022-09-30 interim " + cv, nt + "; pdf p3-11 textless"),
    "fc983b3a": ("3M and 6M ended 2022-06-30 interim " + cv, nt + "; pdf p3-11 textless"),
    "d559879a": ("3M ended 2022-03-31 interim " + cv, nt + "; pdf p3-11 textless"),
    "3e6cc355": ("3M and 9M ended 2023-09-30 interim " + cv, nt),
    "facb2cde": ("FY ended 2022-12-31 audited FS as issued (IFRS 4), label 2023|FY", nt + "; pdf p3-16 textless; the primary statements were not rendered"),
    "08fc1b74": ("3M and 6M ended 2023-06-30 interim " + cv, nt),
    "81453bc3": ("3M ended 2023-03-31 interim " + cv, nt),
    "9ffde04a": ("3M and 9M ended 2024-09-30 interim " + cv, nt + "; inventory class other_no_statements_found although it is a full interim"),
    "c2445d7a": ("3M and 6M ended 2024-06-30 interim " + cv, nt),
    "9f1231e3": ("3M ended 2024-03-31 interim " + cv, nt + "; inventory class annual_report_with_statements, 98 pages"),
    "3f87941a": ("3M and 9M ended 2025-09-30 interim, consolidated " + cv, nt),
    "f7994d56": ("3M and 6M ended 2025-06-30 interim, consolidated " + cv, nt + "; inventory class results_announcement but 85 pages; H1 2025 comparatives read in the H1 2026 filing"),
    "ce3394a3": ("3M ended 2025-03-31 interim " + cv, nt + "; Q1 2025 comparatives read in the Q1 2026 filing"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_5_filings_declared_restatements_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) read from rendered pages for FY2025, FY2024, FY2023 as first issued (2022 restated), H1 2026 and Q1 2026. All identities pass exactly (balance sheet, cash-flow sum and roll, pre-zakat result less zakat and tax equals net result, owners plus minority equals net result). FY2025: insurance revenue 3,104,295, loss before zakat and tax -155,084, net loss -175,084 (owners -175,816, minority 732; EPS -1.38), total assets 5,456,783, equity 1,672,634, CFO -545,897, closing cash 407,070. FY2024 net profit 64,303 (revenue 3,344,580); FY2023 147,977. H1 2026 net profit 43,495 (owners 43,166; Q1 16,237, Q2 27,258); Q1 + Q2 = H1 for revenue, pre-tax result, zakat and tax, net result and owners result in 2026 and 2025 (pass; 2025 H1 loss -117,127). Declared: (1) FY2023 cash flow re-presented in the FY2024 filing (CFO 422,928 versus 423,386, CFI -440,574 versus -441,032, 458 reclassified), (2) FY2023 EPS 1.74 as issued versus 1.45 restated, (3) 31 Dec 2025 balance sheet re-presented in the H1 2026 filing (goodwill 76,729 to 51,571 and intangibles 107,452 to 132,610; total assets and equity identical), (4) 31 Dec 2024 balance-sheet line presentation differs between FY2024 and FY2025 filings (totals identical). The FY2022 IFRS 4 as-issued filing (facb2cde) was not read, so the IFRS 4 to IFRS 17 transition is evidenced only through the restated 2022 and 2021 columns in the FY2023 filing. Insurance service expense is printed in brackets (negative).",
        "not_read": ["notes (acquisition accounting, restatement notes)", "statements of changes in equity (except H1 2026 comparative pdf p8 image)", "FY2022 as issued (facb2cde primary statements)", "Q2 cash flow by subtraction not validated", "all other 13 files", "segment-note totals versus primary balance sheet"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_five_files_opened_all_statement_pages_are_image_only",
        "summary": "Five files carry balance sheet, income statement and cash flow on image-only pages (pdf p3 to 18 textless; no usable text layer for any statement page), although the inventory classes 0ea15501 (FY2025) annual_report_no_statements and a8eaa7a2, 531e3feb partial_statements. Several other files are mis-classed by the inventory: 9ffde04a other_no_statements_found, 9f1231e3 annual_report_with_statements and f7994d56 results_announcement are full interim statement sets by their covers. FY2025 is the first consolidated set (subsidiary acquired in 2025); earlier annual sets are standalone, so FY2024 and FY2025 are not like-for-like. No FY2021 own FS in the collection. All files are English only.",
        "defect_ids": ["B017-8060-1", "B017-8060-2", "B017-8060-3", "B017-8060-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2022_to_2026_H1_by_page_derived_period_FY2022_values_unread",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY, unread)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2022 and FY2021 IFRS 17 restated (FY2023 filing)", "2025 Q1 and H1 (2026 filings)"],
        "values_not_read": ["FY2022 as issued (IFRS 4)", "2022 to 2025 interim originals"],
        "missing": ["FY2021 and earlier own filings (no file)", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in all four annual files; interim labels match cover periods.",
    },
}
defects = [
    {"id": "B017-8060-1", "class": "image_only_statements_flagged_as_missing_or_partial", "severity": "high",
     "evidence": "0ea15501 (annual_report_no_statements) pdf p8, p9, p13-14; a8eaa7a2 (partial_statements) pdf p4, p5, p9-10; 531e3feb (partial_statements) pdf p4, p5, p9-10 hold the full primary statements as images; 041b9f6a pdf p3-14 and a57b1123 pdf p3-18 textless."},
    {"id": "B017-8060-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "a57b1123 FY2023 labelled 2024|FY, 041b9f6a FY2024 labelled 2025|FY, 0ea15501 FY2025 labelled 2026|FY, facb2cde FY2022 labelled 2023|FY."},
    {"id": "B017-8060-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "FY2023 cash flow: CFO 422,928 (a57b1123 pdf p17) versus 423,386 (041b9f6a pdf p13); CFI -440,574 versus -441,032; EPS 1.74 versus 1.45. 31 Dec 2025 balance sheet: goodwill 76,729, intangibles 107,452 (0ea15501 pdf p8 and 531e3feb pdf p4) versus 51,571 and 132,610 marked Restated (a8eaa7a2 pdf p4). Both recorded, none substituted."},
    {"id": "B017-8060-4", "class": "consolidation_change_and_inventory_misclassification", "severity": "medium",
     "evidence": "FY2025 is the first consolidated period (minority interest 2,900, purchase consideration 68,209; 0ea15501 pdf p8, p14); 9ffde04a, 9f1231e3, f7994d56 are full interim sets classed other_no_statements_found, annual_report_with_statements and results_announcement."},
]
unread = ["notes", "statements of changes in equity (except H1 2026 comparative page)", "FY2022 as issued (facb2cde)", "13 files not value-read (interims 2022 to 2025 identified by cover only)",
          "FY2021 and earlier (no file)", "Arabic originals (none in collection)", "segment-note totals versus the primary balance sheet", "insurance operations vs shareholders operations supplementary statements"]
conclusion = ("NOT claimed complete. Five filings value-verified from rendered image-only pages (FY2023 as first issued, FY2024, FY2025, Q1 2026, H1 2026); cash-flow, EPS and balance-sheet re-presentations declared with both values; "
              "FY2022 as issued and 13 interim files not value-read; FY2021 and earlier absent.")
mkrecord.build(dict(
    symbol="8060", name="WALAA COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. All statement pages of the five audited filings are image-only and were rendered and read by eye. "
            "tools/check_transcripts.py over transcripts/8060.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result less zakat and tax to net result, owners plus minority to net result, cross-filing comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls for revenue, pre-tax result, zakat and tax, net result and owners result (2026 and 2025); all pass.")))
