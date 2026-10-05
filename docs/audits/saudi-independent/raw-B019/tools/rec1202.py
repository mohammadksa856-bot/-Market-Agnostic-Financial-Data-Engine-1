"""Builds raw-B019/1202.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"
IS = "is"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


VIS = "visual (statement pages textless, rendered and read)"
TXT = "text layer (clean)"
documents = [
    doc("27f0b1cb", "FY ended 2025-12-31 consolidated FS, label 2026|FY = publication year", False, {"bs": 8, IS: 9, "cf": "11-12", "equity": 10}, {"bs": 6, IS: 7, "cf": "9-10", "equity": 8}, TXT, "pdf p7 textless (auditor report signature page), not viewed"),
    doc("56b0f17a", "FY ended 2024-12-31 consolidated FS as issued, label 2025|FY = publication year; inventory class other_no_statements_found", False, {"bs": 8, IS: 9, "cf": "11-12"}, {"bs": 6, IS: 7, "cf": "9-10"}, VIS),
    doc("e9e1bfd9", "FY ended 2023-12-31 consolidated FS as issued, label 2024|FY = publication year; inventory class partial_statements", False, {"bs": 8, IS: 9, "cf": "11-12"}, {"bs": 6, IS: 7, "cf": "9-10"}, VIS),
    doc("dac8ceda", "FY ended 2022-12-31 consolidated FS as issued, label 2023|FY = publication year", False, {"bs": 8, IS: 9, "cf": 11}, {"bs": 6, IS: 7, "cf": 9}, TXT),
    doc("3ee0937e", "3M and 6M ended 2026-06-30 (English); inventory class partial_statements", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, VIS, "pdf p6 equity statement not read; Arabic twin de3f6b3c balance-sheet totals matched (see de3f6b3c)"),
    doc("1b3c4e61", "3M ended 2026-03-31 (English); inventory class other_no_statements_found", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, VIS),
    doc("eb8f0442", "3M and 9M ended 2025-09-30; pdf p8 text layer scrambled, read from image; inventory class partial_statements", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, VIS),
    doc("a7b11ec3", "3M and 6M ended 2025-06-30; inventory class partial_statements", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, VIS),
    doc("d841b90b", "3M ended 2025-03-31; inventory class partial_statements", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, VIS),
    doc("8969f4f0", "3M ended 2024-03-31 as issued", True, {"bs": 4, IS: 5, "cf": 7}, {"bs": 2, IS: 3, "cf": 5}, TXT),
]

identified = {
    "5a774c4a": ("Annual report 2017 (Arabic cover text)", "122 pages; statement pages not transcribed"),
    "a4c03983": ("9M 2021 earnings press release (cover text: 27 October 2021)", "no statements; not transcribed"),
    "3abdca4d": ("3M and 9M ended 2022-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "615289ff": ("7-page press-release-like file, text layer holds no period phrase; period unverified", "label 2022|9M unverified"),
    "0f872c2f": ("FY2022 earnings press release dated 19 March 2023 (cover text)", "label 2022|FY here is the fiscal year, unlike the FS files where FY labels are publication years"),
    "d848b1f4": ("3M and 6M ended 2022-06-30 interim FS (cover text); inventory class results_announcement", "class is wrong, file is a 20-page interim FS; not transcribed"),
    "e6aa0e4c": ("3M ended 2022-03-31 (cover text)", "classed other_no_statements_found; not transcribed"),
    "2025f11e": ("3M and 9M ended 2023-09-30 (cover text)", "text FS present (statement pages p4-8); not transcribed"),
    "5a1b5efa": ("Annual report 2023 (Arabic cover text)", "106 pages; statements not transcribed"),
    "664851b5": ("3M and 6M ended 2023-06-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "e86914d1": ("3M ended 2023-03-31 (cover text)", "classed other_no_statements_found; not transcribed"),
    "b3075261": ("3M and 9M ended 2024-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "b091508a": ("Annual report 2024 (Arabic cover text)", "90 pages; statements not transcribed"),
    "f58d10b8": ("Annual report 2024 (English cover text)", "90 pages; statements not transcribed"),
    "09778a39": ("3M and 6M ended 2024-06-30 as issued (cover text); text layer", "BS and several lines viewed in text but headline subtotals not transcribed; not value-audited; H1 2024 restated comparatives (note 21) read from the H1 2025 filing"),
    "de3f6b3c": ("3M and 6M ended 2026-06-30, Arabic twin of 3ee0937e", "balance-sheet totals read from image (pdf p4): assets 2,796,333,041, liabilities 1,158,791,734, equity 1,637,541,307 match the English file; IS/CF not read"),
    "ee041266": ("3M ended 2026-03-31, Arabic twin of 1b3c4e61", "balance-sheet totals read from image (pdf p4): assets 2,759,060,525, liabilities 1,139,722,148, equity 1,619,338,377 match the English file; IS/CF not read"),
}

method = ("SHA-256 recomputed for every audited file. Statement pages of 7 of the 10 opened filings are image-only (FY2024, FY2023 and all 2025/2026 interims) and were rendered and read by eye; FY2025, FY2022 and Q1 2024 were read from a clean text layer. "
          "tools/check_transcripts.py over transcripts/1202.json checks BS identity, cash-flow sum and roll, gross profit, profit before zakat less zakat to net income, owners plus NCI, cross-filing agreement of comparatives (restated and re-presented columns carry written reasons) and Q1+Q2=H1 / H1+Q3=9M rolls; all pass.")

dimensions = {
    "value_correctness": {
        "status": "verified_for_10_filings_with_declared_reclassifications_and_restatements",
        "summary": ("Headline BS, income and cash-flow values (full SAR) read from pages for FY2022-FY2025, 3M 2024, 3M/6M/9M 2025, 3M 2026 and 6M 2026; all identities hold with zero difference. "
                    "FY2025: revenue 1,060,527,264, profit 22,203,520 (parent 23,410,074), total assets 2,668,255,373, equity 1,620,738,788, CFO 123,079,082, cash 495,352,589. FY2024: revenue 1,065,255,961, loss -77,468,000, total assets 2,558,600,261, CFO -100,005,234, cash 610,683,119. "
                    "FY2023 (as issued): revenue 866,752,771, loss -87,637,497. FY2022: revenue 1,187,005,798, profit 270,729,810. H1 2026: revenue 542,305,194, profit 13,929,024 (Q1 -1,400,411 + Q2 15,329,435 rolls exactly). "
                    "Declared differences, never substituted: (1) FY2023 income statement restated in the FY2024 filing (note 36.2): 41,319,658 of selling expense moved into cost of revenue (cost 781,756,682 -> 823,076,340, gross profit 84,996,089 -> 43,676,431; operating loss, loss before zakat and net loss unchanged; other operating income 8,761,401 split into 10,917,276 and a 2,155,875 write-off line). "
                    "(2) FY2023 cash flow: CFO 199,126,581 / CFF -17,765,657 in the FY2023 filing vs 198,122,581 / -16,761,657 in the FY2024 filing (1,004,000 of lease payment moved from operating to financing; net change -88,696,688 unchanged). "
                    "(3) FY2022 cash flow: CFO 286,390,856 / CFI -213,019,473 in the FY2022 filing vs 238,674,940 / -165,303,557 in the FY2023 filing (capital project advances 47,715,916 moved from investing into operating working capital); FY2022 statement of financial position other current assets 91,911,302 vs 94,011,302 and prepayments 16,690,045 vs 14,590,045. "
                    "(4) Dec 2024 PPE appears as 1,221,071,925 (FY2024 filing), 1,241,079,841 (2025 interim filings, with right-of-use assets) and 1,268,700,865 (FY2025 filing, with CWIP and right-of-use); trade and other payables 184,404,644 vs 191,982,075 (current lease liabilities folded in); totals unchanged. "
                    "(5) 2024 interim comparatives restated in the 2025 filings (notes 19, 21, 22.b): Q1 2024 cost of revenue -210,944,782 as issued vs -219,775,825 restated; revenue and net loss (-18,713,677) unchanged. "
                    "Interim cash flow: Q1 2026 CFO 35,453,580 vs H1 2026 95,367,830 and 9M 2025 CFO 123,463,769 vs H1 2025 91,471,980; interim Q2/Q3 by subtraction from cash flow was NOT validated. Income-statement Q2 2026 by subtraction does equal the issued three-month column (revenue 542,305,194 = 244,292,290 + 298,012,904)."),
        "not_read": [
            "notes in every file",
            "statements of changes in equity except FY2025 p10 (text)",
            "auditor report pages (FY2025 pdf p7 textless, reports of the other files)",
            "2022 Q1, H1, 9M; 2023 Q1, H1, 9M; 2024 H1 headline totals, 2024 9M interim filings",
            "annual reports 2017, 2023, 2024 (Arabic and English)",
            "Arabic twins: income statement and cash flow",
        ],
    },
    "document_completeness": {
        "status": "annual_FY2022_to_FY2025_and_interims_2024Q1_2025Q1_to_2026H1_read; other files not transcribed",
        "summary": ("The inventory under-reports statement content: the FY2024 FS (class other_no_statements_found, pdf p8-12 textless), FY2023 FS (partial_statements, p7-12 textless), the Q1 2026 file (other_no_statements_found) and the 2025/2026 interims (partial_statements) all carry complete BS, income and cash-flow statements as images; "
                    "the H1 2022 file (class results_announcement) is a 20-page interim FS. FS FY labels are publication years (2026|FY holds FY2025, 2025|FY holds FY2024, 2024|FY holds FY2023, 2023|FY holds FY2022), but the FY2022 earnings press release 0f872c2f labelled 2022|FY is also FY2022, so labels mix publication and fiscal year within this company. "
                    "Arabic twins exist for Q1 2026 and H1 2026 (same figures at balance-sheet level). Unit is full SAR in every file read."),
        "defect_ids": ["B019-1202-1", "B019-1202-2", "B019-1202-3"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_present_with_statements_interims_2022_to_2026H1_present_by_cover_text",
        "present_in_files_by_page_derived_period": ["FY2022", "FY2023", "FY2024", "FY2025", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1", "annual reports 2017, 2023, 2024 (cover only)"],
        "values_verified_from_own_pages": ["FY2022", "FY2023", "FY2024", "FY2025", "2024 Q1", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "2023 Q1 (Q1 2024 filing)", "2024 H1 and Q2 and 9M and Q3 restated (2025 filings)"],
        "values_not_read": ["2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 H1 own filing", "2024 9M own filing"],
        "missing": ["FY2021 and earlier own FS (annual report 2017 in file, not read)", "no FY2025 annual report file", "no 2024 Q2/Q3 separate files (derivable from H1/9M)"],
        "inventory_corrections": "Inventory expected_periods and periods_with_complete_statements understate coverage: 7 of the 10 value-read filings are classed partial or no-statements by the inventory.",
    },
}

defects = [
    {"id": "B019-1202-1", "kind": "inventory_class", "detail": "56b0f17a (FY2024), e9e1bfd9 (FY2023), 1b3c4e61 (Q1 2026) and the 2025/2026 interims a7b11ec3, d841b90b, eb8f0442, 3ee0937e are classed partial/no statements but hold full statements as images; d848b1f4 is classed results_announcement but is a 20-page interim FS."},
    {"id": "B019-1202-2", "kind": "label_semantics", "detail": "FS FY labels are publication years; the FY2022 press release 0f872c2f is labelled 2022|FY (fiscal year). Page-derived periods must be used, not collector labels."},
    {"id": "B019-1202-3", "kind": "reclassifications", "detail": "FY2023 and FY2022 cash flows and the FY2023 and 2024-interim income statements were re-presented in later filings; PPE composition differs across the FY2024, 2025-interim and FY2025 filings. All declared in transcripts; no value substituted."},
]

unread = [
    "notes to the financial statements in every file (going-concern, restatement notes 21/22.b/36.2, zakat, borrowings)",
    "statements of changes in equity (except FY2025)",
    "auditor and review report pages",
    "2022 and 2023 interim filings (Q1, H1, 9M each year), 2024 H1 and 9M own filings",
    "annual reports 2017, 2023, 2024 (Arabic and English)",
    "income statement and cash flow of the Arabic twins de3f6b3c and ee041266",
    "615289ff period unverified (7-page file with no period text)",
    "earnings press releases a4c03983, 0f872c2f",
]

spec = dict(
    symbol="1202",
    name="MEPCO (Middle East Company for Manufacturing and Producing Paper)",
    method=method,
    documents=documents,
    identified=identified,
    dimensions=dimensions,
    defects=defects,
    unread_items=unread,
    conclusion="Company is NOT claimed complete: annual FY2022-FY2025 and six interims were read, but 2022-2023 interims, 2024 H1/9M own filings, annual reports and all notes are unread. Values read are arithmetic-consistent with declared reclassifications.",
)
if __name__ == "__main__":
    mkrecord.build(spec)
