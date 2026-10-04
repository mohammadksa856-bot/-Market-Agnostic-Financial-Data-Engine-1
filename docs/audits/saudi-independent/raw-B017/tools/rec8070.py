"""Builds raw-B017/8070.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SAR 000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("f37574d3", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 10, "is": 11, "cf": 14}, {"bs": 10, "is": 11, "cf": 14},
        "visual and text layer (text layer present; agrees with the rendered pages)",
        "Balance-sheet cash 259,168 = cash-flow closing cash 249,619 + restricted cash 9,549 (note 9, pdf p73). Note 30 (pdf p115) documents the Al Ahli Takaful merger (effective 12 Jan 2022, acquisition method, 23,852,462 shares) and pdf p92 the Alinma Tokio Marine merger (effective 15 Nov 2023). Insurance Authority combined/insurance-operations/shareholders-operations supplementary statements at pdf p120-129 not transcribed."),
    doc("441d0b94", "FY ended 2024-12-31 audited FS with 2023 and 1 Jan 2023 restated (label 2025|FY = publication year)", False, {"bs": 10, "is": 11, "cf": 15}, {"bs": 10, "is": 11, "cf": 15}, "visual (pdf p10-15 textless)",
        "FY2023 comparative restated (note 31): see defect B017-8070-3. The 1 Jan 2023 (= 31 Dec 2022) column shows total assets 2,461,613 and total liabilities 1,276,441 versus 2,520,772 and 1,335,600 in the FY2023 filing (due-from/due-to shareholders and policyholder-surplus lines netted differently; equity 1,185,172 identical); not transcribed to the cross-check."),
    doc("efb18e0c", "FY ended 2023-12-31 audited FS as first issued, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", False, {"bs": 12, "is": 13, "cf": 17}, {"bs": 12, "is": 13, "cf": 17},
        "text layer rows plus image read of the balance sheet (pdf p11 textless)",
        "2023 column is as issued, 2022 and 1 Jan 2022 are restated; the 2023 column was later restated in the FY2024 filing."),
    doc("842ec46a", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", False, {"bs": 11, "is": 12, "cf": "16-17"}, {"bs": 11, "is": 12, "cf": "16-17"}, "visual (pdf p4-17 textless)",
        "IFRS 4 presentation (gross premiums written, total revenues 743,375); restated to IFRS 17 in the FY2023 filing: net result 27,920 to -18,225. Both declared; neither substituted."),
    doc("604d6cc8", "3M and 6M ended 2026-06-30 unaudited interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 5, "is": 6, "cf": 9}, {"bs": 5, "is": 6, "cf": 9}, "visual (entire file is image pages, inventory class scanned_unreadable, yet it carries full statements)",
        "income columns: 3M 2026, 3M 2025, year to date 2026, year to date 2025; cash flow six-month only; balance-sheet cash exceeds cash-flow closing cash by 12,009 (cause in note 9 not read)"),
    doc("86813dab", "3M ended 2026-03-31 unaudited interim (label 2026|Q1 correct)", True, {"bs": 5, "is": 6, "cf": 9}, {"bs": 5, "is": 6, "cf": 9}, "visual (pdf p4-9 textless)",
        "balance-sheet cash exceeds cash-flow closing cash by 10,450 (cause in note 9 not read)"),
]
nt = "not transcribed"
identified = {
    "bd571829": ("3M and 9M ended 2022-09-30 interim (cover text)", nt + "; pdf p4-10 textless"),
    "1feee496": ("not identified from text (entire file image-only, inventory class scanned_unreadable); label 2022|H1", "not opened as images for this audit"),
    "85c435bd": ("3M ended 2022-03-31 interim (cover text)", nt),
    "2459636a": ("not identified from text (entire file image-only, inventory class scanned_unreadable); label 2023|9M", "not opened as images for this audit"),
    "1b3c8244": ("not identified from cover text (pdf p1-10 textless); label 2023|H1", nt),
    "a83211e1": ("3M ended 2023-03-31 interim (cover text)", nt),
    "d0fe4844": ("3M and 9M ended 2024-09-30 interim (cover text); 94 pages incl. supplementary", nt),
    "4a923358": ("3M and 6M ended 2024-06-30 interim (cover text)", nt),
    "c17af772": ("not identified from cover text (pdf p1-9 textless); label 2024|Q1", nt),
    "63002089": ("3M and 9M ended 2025-09-30 interim (cover text)", nt),
    "f4bba8b2": ("3M and 6M ended 2025-06-30 interim (cover text)", nt + "; H1 2025 comparatives read in the H1 2026 filing"),
    "ab577602": ("not identified from cover text (pdf p1-9 textless); label 2025|Q1", nt + "; Q1 2025 comparatives read in the Q1 2026 filing"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_restatements_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) read from rendered pages for FY2025, FY2024 (2023 restated), FY2023 as first issued (2022 restated), FY2022 as issued under IFRS 4, H1 2026 (image-only file) and Q1 2026. All identities pass exactly (balance sheet, cash-flow sum and roll, pre-tax result less zakat and tax equals net result). FY2025: insurance revenue 1,881,892, loss before zakat and tax -31,270, net loss -43,753 (EPS -0.55), total assets 4,894,739, equity 1,632,308, CFO 50,076, closing cash per cash flow 249,619 (balance-sheet cash 259,168 includes restricted cash 9,549, note 9). FY2024 net profit 70,995; FY2023 first issued 44,188 (restated 66,940); FY2022 IFRS 4 27,920 (IFRS 17 restated -18,225). H1 2026: insurance revenue 801,665, net profit 7,725 (Q1 4,898, Q2 2,827); Q1 + Q2 = H1 for revenue, pre-tax result, zakat plus tax and net result in 2026 and 2025 (pass). Declared differences: (1) FY2022 IFRS 4 as issued versus IFRS 17 restated. (2) FY2023 as first issued versus restated in the FY2024 filing (net result, total assets, equity, and a cash-flow reclassification moving FVTPL investment purchases from investing to operating: CFO 48,420 versus 228,409). (3) 1 Jan 2023 balance sheet netting differences. Cash-flow closing cash differs from balance-sheet cash by restricted cash (verified only for FY2025). Insurance service expense is printed in brackets (negative).",
        "not_read": ["notes (except note 9 cash split and note 30 merger text)", "statements of changes in equity", "Insurance Authority combined / insurance operations / shareholders operations supplementary statements (FY2025 pdf p120-129, interim pdf p83-88)", "restricted-cash cause for the H1 2026 and Q1 2026 balance-sheet versus cash-flow cash differences", "Q2 cash flow by subtraction not validated", "12 other interim filings", "segment-note totals versus primary balance sheet"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_six_files_opened_three_files_image_only_or_textless",
        "summary": "Six files carry balance sheet, income statement and cash flow. 604d6cc8 (H1 2026) is entirely image pages and is classed scanned_unreadable by the inventory although it holds full statements; 86813dab (Q1 2026) is classed partial_statements although it holds all three on image pages; 441d0b94 and 842ec46a statements are image pages while the inventory lists them as annual_report_with_statements or partial_statements. Two further files (1feee496 2022 H1, 2459636a 2023 9M) are fully image-only and were not opened. The inventory text-layer reader risk: FY2025 text layer is a Print-to-PDF layer whose rows merge columns, so values were confirmed on rendered images. Entity: all statement files carry Arabian Shield Cooperative Insurance Company; the Al Ahli Takaful merger (effective 12 Jan 2022) is accounted for by acquisition, so there are no separate Al Ahli Takaful statements to expect and FY2022 and later include it; Alinma Tokio Marine merged 15 Nov 2023 (included from that date in FY2023). No FY2021 own FS in the collection.",
        "defect_ids": ["B017-8070-1", "B017-8070-2", "B017-8070-3", "B017-8070-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2022_to_2026_H1_with_gaps_by_page_derived_period",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)",
                                                    "2022 Q1", "2022 H1 (image-only, unidentified)", "2022 9M", "2023 Q1", "2023 H1 (cover textless)", "2023 9M (image-only, unidentified)", "2024 Q1 (cover textless)", "2024 H1", "2024 9M", "2025 Q1 (cover textless)", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023 (as first issued)", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing)", "FY2022 IFRS 17 restated (FY2023 filing)", "FY2023 restated (FY2024 filing)", "2025 Q1 and H1 (2026 filings)"],
        "values_not_read": ["2022 Q1/H1/9M", "2023 Q1/H1/9M", "2024 Q1/H1/9M", "2025 Q1/H1/9M originals"],
        "missing": ["FY2021 and earlier own filings (no file)", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in all four FS files. Interim labels match cover periods where cover text exists; 1feee496, 2459636a, 1b3c8244, c17af772, ab577602 periods rest on the collector label only (no readable cover text).",
    },
}
defects = [
    {"id": "B017-8070-1", "class": "image_only_or_scanned_statements_flagged_as_unreadable_or_partial", "severity": "high",
     "evidence": "604d6cc8 (2026 H1, scanned_unreadable) pdf p5-9 hold full BS, IS and CF as images; 86813dab (2026 Q1, partial_statements) pdf p4-9 textless but full statements; 441d0b94 pdf p10-15 and 842ec46a pdf p4-17 textless."},
    {"id": "B017-8070-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "842ec46a FY2022 labelled 2023|FY, efb18e0c FY2023 labelled 2024|FY, 441d0b94 FY2024 labelled 2025|FY, f37574d3 FY2025 labelled 2026|FY."},
    {"id": "B017-8070-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "FY2022: IFRS 4 net result 27,920 (842ec46a pdf p12) versus IFRS 17 restated -18,225 (efb18e0c pdf p13); total assets 2,678,635 versus 2,520,772. FY2023: as first issued net result 44,188, total assets 3,531,551, CFO 48,420 (efb18e0c pdf p12, p13, p17) versus restated 66,940, 3,355,638, 228,409 (441d0b94 pdf p10, p11, p15, note 31). Both recorded, none substituted."},
    {"id": "B017-8070-4", "class": "balance_sheet_cash_versus_cash_flow_cash_and_merger_comparability", "severity": "medium",
     "evidence": "FY2025 balance-sheet cash 259,168 versus cash-flow closing cash 249,619 (restricted cash 9,549, note 9 pdf p73); H1 2026 801,315 versus 789,306 and Q1 2026 536,920 versus 526,470 unexplained from pages read. Mergers: Al Ahli Takaful (12 Jan 2022) and Alinma Tokio Marine (15 Nov 2023) make FY2022 to FY2024 period-on-period comparison structurally non-comparable (share capital 400,000 to 638,525 to 798,153)."},
]
unread = ["notes (except note 9 and note 30 text)", "statements of changes in equity", "Insurance Authority supplementary statements (insurance operations vs shareholders operations)", "12 interim filings 2022 Q1 to 2025 9M (identified by cover where text exists; 2 are fully image-only)",
          "restricted-cash reconciliation for H1 2026 and Q1 2026", "FY2021 and earlier (no file)", "Arabic originals (none identified in collection)", "segment-note totals versus the primary balance sheet"]
conclusion = ("NOT claimed complete. Six filings value-verified from rendered pages (FY2022 as issued, FY2023 as first issued, FY2024, FY2025, Q1 2026, H1 2026); IFRS 17 FY2022 restatement and FY2023 restatement are declared with both values; "
              "12 interim filings identified by cover (two not identifiable) but not value-read; FY2021 and earlier absent.")
mkrecord.build(dict(
    symbol="8070", name="ARABIAN SHIELD COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Statement pages rendered and read by eye (text layers used only where they agree with images). "
            "tools/check_transcripts.py over transcripts/8070.json checks balance-sheet identity, cash-flow sum and roll, pre-tax result plus zakat and tax to net result, cross-filing comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls for revenue, pre-tax result, zakat plus tax and net result (2026 and 2025); all pass.")))
