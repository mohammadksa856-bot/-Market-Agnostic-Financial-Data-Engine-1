"""Builds raw-B013/6012.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"
IS = "is"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


VIS = "visual (statement pages textless, rendered and read)"
documents = [
    doc("c08a825b", "FY ended 2025-12-31 FS of Ridan Company Food (Raydan), label 2026|FY = publication year", False, {"bs": 9, IS: 10, "cf": "12-13"}, {"bs": 7, IS: 8, "cf": "10-11"}, VIS),
    doc("80898466", "FY ended 2024-12-31 consolidated FS as issued, label 2025|FY = publication year; inventory class partial_statements", False, {"bs": 9, IS: 10, "cf": 12}, {"bs": 7, IS: 8, "cf": 10}, VIS),
    doc("dc9b7753", "FY ended 2023-12-31 consolidated FS as issued, label 2024|FY = publication year", False, {"bs": 9, IS: 10, "cf": 12}, {"bs": 7, IS: 8, "cf": 10}, VIS),
    doc("94f34098", "FY ended 2022-12-31 consolidated FS as issued, label 2023|FY = publication year; inventory class partial_statements", False, {"bs": 9, IS: 10, "cf": 12}, {"bs": 7, IS: 8, "cf": 10}, VIS),
    doc("6f8cb490", "3M and 6M ended 2025-06-30 as issued (Egypt subsidiary in liquidation shown as discontinued)", True, {"bs": 5, IS: 6, "cf": 8}, {"bs": 3, IS: 4, "cf": 6}, VIS),
    doc("8937ac21", "3M ended 2025-03-31 as issued", True, {"bs": 5, IS: 6, "cf": 8}, {"bs": 3, IS: 4, "cf": 6}, VIS),
    doc("87839b51", "3M ended 2026-03-31 (inventory class partial_statements)", True, {"bs": 5, IS: 6, "cf": 8}, {"bs": 3, IS: 4, "cf": 6}, VIS, "pdf p7 equity statement not read"),
    doc("10e0e51c", "3M and 6M ended 2026-06-30; FY2025 balance sheet and 2025 comparatives re-presented for discontinued operations", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, "text layer"),
]

identified = {
    "26706f30": ("3M and 9M ended 2022-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "43f319d8": ("3M and 6M ended 2022-06-30 (cover read; pdf p1-4, p10-17 textless)", "scan-like file; not transcribed"),
    "3cb063af": ("3M ended 2022-03-31 (cover text)", "text FS present (statement_pages p4, p6, p7, p8); not transcribed"),
    "283a3789": ("3M and 9M ended 2023-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "0901fa5b": ("3M and 6M ended 2023-06-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "b6013c59": ("3M ended 2023-03-31 (cover read, whole-file scan 17 pages)", "classed scanned_unreadable; not transcribed"),
    "4fe48841": ("3M and 9M ended 2024-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "203e4945": ("3M and 6M ended 2024-06-30 (cover text)", "statement pages pdf p3-8 textless; not transcribed; 6M and Q2 2024 known from the H1 2025 comparatives"),
    "412688c3": ("3M ended 2024-03-31 (cover text)", "statement pages pdf p3-7 textless; not transcribed; Q1 2024 known from the Q1 2025 comparatives"),
    "dd119750": ("3M and 9M ended 2025-09-30 (cover text)", "statement pages pdf p4-9 textless; not transcribed"),
}

spec = dict(
    symbol="6012", name="RAYDAN (Raydan Food Company)",
    method=("SHA-256 recomputed for every audited file. Seven of the eight filings have image-only statement pages (pdf p4-13) and were rendered and read by eye; the H1 2026 interim was read from the text layer and tied by arithmetic. "
            "tools/check_transcripts.py over transcripts/6012.json checks BS identity, cash-flow sum and roll (with the foreign-currency effect), gross profit, profit before zakat to net loss including discontinued operations, "
            "owners + NCI, cross-filing agreement of comparatives (restated and re-presented columns flagged, differences written up) and Q1 + Q2 = H1 rolls; all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_8_filings_with_cash_flow_reclassifications_and_discontinued_operations_representation",
            summary=("Headline BS, income and cash-flow values (full SAR) from pages for FY2022, FY2023, FY2024, FY2025, H1 2025, Q1 2025, Q1 2026 and H1 2026; identities hold with zero difference. Net losses: FY2025 -64,729,123 "
                     "(revenue 114,080,252, total assets 136,549,435, equity 17,146,431, CFO 1,153,775, cash 1,353,666), FY2024 -73,105,420 (revenue 155,367,760), FY2023 -30,889,166 (revenue 177,373,734), FY2022 -24,621,539 (revenue 159,177,603); "
                     "H1 2026 net loss -22,330,947 with shareholders' deficit -5,184,516 (liabilities exceed assets). Q1 2026 + Q2 2026 = H1 2026 net loss; Q1 2025 + Q2 2025 = H1 2025 for revenue, cost of revenue, profit before zakat and net loss (as issued). "
                     "Declared differences, never substituted: (1) FY2023 balance-sheet cash 6,585,363 and cash flow (CFO 5,082,168, net change -20,879,791) in the FY2023 filing versus 6,476,639, CFO 4,973,444, net change -20,988,515 in the FY2024 filing "
                     "(a cash difference of 108,724; total assets identical 266,262,198 because prepayments rise by 108,724; the H1 2025 filing's 2024 comparative still opens from 6,585,363); (2) FY2022 cash flow in the FY2022 filing (CFO -18,586,904, "
                     "CFI -19,609,853, CFF -10,437,566, FX -88,907) re-presented in the FY2023 filing (CFO -24,650,997, CFI -11,248,567, CFF -12,823,666, FX folded into net change -48,723,230); (3) FY2024 operating loss -67,170,616 as issued versus -66,046,611 in the "
                     "FY2025 filing (impairment of the associate 2,685,020 and other items moved below operating profit; loss before zakat -72,805,202 unchanged); (4) H1 2026 re-presents discontinued operations: 6M 2025 revenue 68,876,490 as issued versus 53,143,977, "
                     "operating loss -21,336,147 versus -17,355,739, loss from continuing operations -18,385,760 versus -14,312,213 (net loss -18,389,432 unchanged), and Dec 2025 total assets 136,549,435 versus 136,806,587 (assets of discontinued operations 257,152); "
                     "Q1 2026 revenue 19,522,387 as issued plus Q2 3,483,621 does not equal H1 2026 revenue 20,660,235, so a revenue-based Q2 by subtraction from the Q1 file is wrong (net loss rolls exactly); Q1 2025 operating loss -5,983,823 versus -6,516,573 in the Q1 2026 filing "
                     "(other income moved below operating). Interim cash flow: Q1 2026 CFO -4,579,736 versus H1 2026 CFO -5,700,167; Q2 by subtraction is NOT validated. Going-concern material-uncertainty paragraph is present in the H1 2025 review report; FY2025 capital reduction "
                     "158,084,670 -> 73,136,030 offset against accumulated losses (non-cash)."),
            not_read=["notes in every file", "statements of changes in equity (H1 2025 glimpsed only)", "auditor's report pages other than H1 2025 p4 and Q1 2026 p4 cover/report", "Q1 2022, H1 2022, 9M 2022, Q1/H1/9M 2023, Q1/H1/9M 2024, 9M 2025 filings",
                      "Q1 2026 equity statement pdf p7", "FY2021 own FS (known only as FY2022 comparatives)"]),
        document_completeness=dict(
            status="annual_FY2022_to_FY2025_and_interims_2022Q1_to_2026H1_with_statements_image_only_in_most_files",
            summary=("Seven of eight opened filings carry textless statement pages (pdf p4-13) although the files are labelled financial_statements, partial_statements or scanned_unreadable; the inventory finds only note pages "
                     "(e.g. FY2024 BS p30,40,42,47; FY2022 income p25,43). 2022 Q2 and 2023 Q1 are scans. The H1 2026 file is born digital with a text layer. The collector name is Raydan; the FY2025 and Q1 2026 filings are titled Ridan Company Food (Listed Company), "
                     "same company (logo, signatories Khalil Kamil Abufadel and Nair Bayan Al-Sulami, figures roll from FY2024). No restated-from-error note found; reclassifications noted in value_correctness."),
            defect_ids=["B013-6012-1", "B013-6012-2", "B013-6012-3"]),
        company_coverage=dict(
            status="annual_FY2022_to_FY2025_interims_2022Q1_to_2026H1_complete_by_label",
            present_in_files_by_page_derived_period=["FY2022", "FY2023", "FY2024", "FY2025", "2022 Q1", "2022 H1 (scan)", "2022 9M", "2023 Q1 (scan)", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            values_verified_from_own_pages=["FY2022", "FY2023", "FY2024", "FY2025", "2025 Q1", "2025 H1", "2026 Q1", "2026 H1"],
            values_known_only_as_comparatives=["FY2021 (FY2022 filing)", "2024 Q1, 6M and Q2 (Q1 2025 and H1 2025 filings)", "2025 H1 re-presented (H1 2026 filing)"],
            values_not_read=["2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1 original", "2024 H1 original", "2024 9M", "2025 9M"],
            missing=["FY2021 standalone", "everything before FY2021", "annual reports"],
            inventory_corrections="FY labels are publication years (2023|FY holds FY2022, 2024|FY holds FY2023, 2025|FY holds FY2024, 2026|FY holds FY2025). Interim labels match the covers."),
    ),
    defects=[
        dict(id="B013-6012-1", **{"class": "image_only_statement_pages_not_detected"}, severity="high",
             evidence="94f34098, dc9b7753, 80898466, c08a825b (pdf p8-13) and 6f8cb490, 8937ac21, 87839b51 (pdf p4-9) have textless statement pages; inventory classes 94f34098, 80898466, 87839b51 as partial_statements and misses the statements; b6013c59 and 43f319d8 are scans."),
        dict(id="B013-6012-2", **{"class": "restated_or_represented_comparatives"}, severity="high",
             evidence=("FY2023 cash 6,585,363 vs 6,476,639 and CFO 5,082,168 vs 4,973,444; FY2022 CFO -18,586,904 vs -24,650,997; FY2024 operating loss -67,170,616 vs -66,046,611; 6M 2025 revenue 68,876,490 vs 53,143,977 and Dec 2025 total assets 136,549,435 vs 136,806,587 "
                       "(discontinued operations); Q1 2025 operating loss -5,983,823 vs -6,516,573. Both versions recorded in the transcript with restated flags or declared differences.")),
        dict(id="B013-6012-3", **{"class": "fiscal_year_label_is_publication_year"}, severity="medium",
             evidence="2023|FY is FY2022, 2024|FY is FY2023, 2025|FY is FY2024, 2026|FY is FY2025."),
        dict(id="B013-6012-4", **{"class": "company_name_variation"}, severity="low",
             evidence="Files titled Raydan Food Company (2022 to FY2024, H1 2025), Ridan Company Food (FY2025, Q1 2026) and Raydan Food Company again (H1 2026); same entity by figures and signatories."),
        dict(id="B013-6012-5", **{"class": "interim_flow_not_comparable_for_subtraction"}, severity="medium",
             evidence="Q1 2026 revenue 19,522,387 + Q2 3,483,621 = 23,006,008 vs H1 2026 20,660,235; Q1 2025 + Q2 2025 operating loss (-5,983,823 + -14,774,574) does not equal H1 2025 operating loss -21,336,147 (other income placement differs between the Q1 and H1 statements)."),
    ],
    unread_items=["notes in all files", "statements of changes in equity", "auditor's reports", "2022 to 2024 interims and 9M 2025 financial statements", "FY2021 standalone"],
    conclusion=("NOT claimed complete. Eight filings value-verified from pages (seven read from images); comparatives re-presented in three places and recorded without substitution; 10 further files not value-read; "
                "nothing before FY2021."),
)
mkrecord.build(spec)
