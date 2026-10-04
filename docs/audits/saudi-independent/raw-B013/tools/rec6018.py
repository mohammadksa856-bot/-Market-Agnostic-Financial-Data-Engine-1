"""Builds raw-B013/6018.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("95156e7d", "FY ended 2022-12-31 STANDALONE FS as originally issued (collector label 2025|FY)", False, dict(bs=5, **{"is": 6}, cf=8), dict(bs=4, **{"is": 5}, cf=7), "text layer"),
    doc("a34966d0", "FY ended 2023-12-31 consolidated FS; FY2022 and FY2021 columns RESTATED in Note 33 (collector label 2025|FY)", False, dict(bs=5, **{"is": 6}, cf=8), dict(bs=4, **{"is": 5}, cf=7), "text layer"),
    doc("0f9cafac", "FY ended 2024-12-31 consolidated FS as originally issued (collector label 2025|FY)", False, dict(bs=5, **{"is": 6}, cf=8), dict(bs=4, **{"is": 5}, cf=7), "text layer"),
    doc("5fc6d9e9", "FY ended 2025-12-31 consolidated FS; FY2024 and 1 Jan 2024 columns RESTATED in Note 34 (collector label 2026|FY)", False, dict(bs=6, **{"is": 7}, cf=9), dict(bs=5, **{"is": 6}, cf=8), "text layer"),
    doc("0032c8f3", "3M and 6M ended 2025-06-30 (inventory finds only index pages; statement pages are images)", True, dict(bs=4, **{"is": 5}, cf=7), dict(bs=3, **{"is": 4}, cf=6), "visual (pdf p3-7 textless, rendered and read)"),
    doc("7e6a815f", "3M and 6M ended 2026-06-30", True, dict(bs=4, **{"is": 5}, cf=7), dict(bs=3, **{"is": 4}, cf=6), "text layer"),
    doc("275c9f02", "3M ended 2026-03-31", True, dict(bs=4, **{"is": 5}, cf=7), dict(bs=3, **{"is": 4}, cf=6), "text layer"),
]

identified = {
    "d9604d54": ("3M and 9M ended 2024-09-30 (cover text)", "text FS present; not transcribed"),
    "6660e436": ("3M and 6M ended 2024-06-30 (cover text)", "text FS present; not transcribed; 6M and Q2 2024 known from the H1 2025 comparatives"),
    "89caf6ab": ("3M ended 2025-03-31, Arabic review report and FS (cover text); label has no period slot", "Arabic twin of 071a3129; not transcribed"),
    "a6ed5be5": ("3M and 9M ended 2025-09-30, Arabic (cover text)", "not transcribed"),
    "cf057480": ("3M and 9M ended 2025-09-30, English (cover text)", "not transcribed"),
    "5e59a3a1": ("Annual Report 2025, Arabic (cover read); text layer is font-garbled", "not transcribed; text unusable"),
    "93d0d117": ("FY ended 2025-12-31 consolidated FS, Arabic twin of 5fc6d9e9 (cover text); label 2025|FY", "not transcribed"),
    "41399a71": ("Key financial figures as of 2025-06-30, English (5 pages)", "results summary, not statements"),
    "7b4b6392": ("Results report 2025-06-30, Arabic (5 pages)", "results summary, not statements"),
    "071a3129": ("3M ended 2025-03-31, English (cover text)", "not transcribed; Q1 2025 income and cash flow known from the Q1 2026 comparatives"),
    "179fd8ca": ("Earnings release for the second quarter of 2026 (cover read), 5 image-only pages", "classed scanned_unreadable by the inventory; it is an earnings release, not statements; not transcribed"),
    "d121eced": ("3M and 6M ended 2026-06-30, Arabic twin (cover text)", "not transcribed"),
    "65948a16": ("Q1 2026 earnings statement (5 pages, Arabic/English mix)", "results summary, not statements"),
    "800bf2bf": ("3M ended 2026-03-31, Arabic twin (cover text)", "not transcribed"),
}

spec = dict(
    symbol="6018", name="SPORT CLUBS (Sport Clubs Company, Fitness Time)",
    method=("SHA-256 recomputed for every audited file. The H1 2025 interim (statement pages image-only) was rendered and read by eye; the other six filings were read from the text layer. "
            "tools/check_transcripts.py over transcripts/6018.json checks BS identity, cash-flow sum and roll, gross profit, profit before zakat to net profit, cross-filing agreement of comparatives "
            "(restated columns flagged and written up, EPS declared) and Q1 + Q2 = H1 rolls; all pass. Restatement Notes 33 (FY2023 file) and 34 (FY2025 file) were read for cause and amounts."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_7_filings_two_restatement_chains_and_unexplained_FY2022_scope_difference",
            summary=("Headline BS, income and cash-flow values (full SAR) from pages for FY2022 (as issued, standalone), FY2023, FY2024 (as issued), FY2025, H1 2025, H1 2026 and Q1 2026. Identities hold with zero difference. "
                     "FY2025: revenue 376,239,000, profit 41,166,865, total assets 944,706,742, CFO 159,440,308, cash 46,676,425. H1 2026: revenue 192,494,098, profit 18,196,113; Q1 2026 + Q2 2026 = H1 2026 for "
                     "revenue and profit; Q1 2025 + Q2 2025 = H1 2025 for revenue, operating income and profit. H1 2025 comparatives in the H1 2026 filing agree with the H1 2025 filing (not restated). "
                     "RESTATED comparatives, never substituted: (1) FY2024 as issued vs restated in the FY2025 filing (Note 34, IAS 8: work-permit fees expensed and depreciation of right-of-use assets on buildings on leased land): "
                     "cost of revenue 228,880,727 -> 230,737,456, profit 38,069,741 -> 36,104,369, EPS 0.37 -> 0.35, total assets 798,406,606 -> 794,329,395, equity 168,808,870 -> 164,731,658, CFO 103,143,540 -> 104,170,083 "
                     "and financing -16,763,255 -> -17,789,795 (a 1,026,540 share-issuance-cost reclassification, not described as such by the note, which says cash-flow impact was not material); "
                     "1 Jan 2024 equity 143,410,464 -> 141,298,624. (2) FY2022 and FY2021 as issued in the FY2022 file vs restated in the FY2023 file (Note 33, capitalised depreciation of right-of-use assets on leased land): "
                     "FY2022 profit 24,261,506 -> 22,682,826, total assets 673,178,718 -> 665,941,152, cash 15,895,356 -> 17,297,313, CFO 107,040,193 -> 105,484,804; FY2021 profit 11,175,889 -> 7,966,306. "
                     "The FY2022 file is titled 'standalone' while the FY2023 file's comparative is consolidated; cash and total assets differ by more than the Note 33 adjustment explains and the page-level reason was not read. "
                     "EPS: 2023 EPS 2.41 (10,400,000 shares) in the FY2023 filing versus 0.24 in the FY2024 filing (declared). FY2024 prior-year total liabilities differ by SAR 1 between FY2024 (629,597,736) and FY2025 (629,597,737)."),
            not_read=["notes in every file other than the restatement notes, share-count note and EPS lines", "statements of changes in equity", "9M 2024, H1 2024, Q1 2025 and 9M 2025 filings (text present, not transcribed)",
                      "all Arabic twins", "Arabic annual report 2025 (garbled text layer)", "FY2021 standalone and earlier years: no file"]),
        document_completeness=dict(
            status="annual_FY2022_to_FY2025_and_interims_2024H1_to_2026H1_with_statements_in_every_opened_file",
            summary=("All seven opened filings carry the full set of statements. H1 2025 statement pages are images (inventory sees only index pages 3-7 as textless). The inventory counts the 2026|FY English file as the FY2025 "
                     "statements and the Arabic twin as 2025|FY. Earnings releases (179fd8ca, 41399a71, 65948a16) are not statements; 179fd8ca is image-only and classed scanned_unreadable."),
            defect_ids=["B013-6018-1", "B013-6018-2", "B013-6018-3"]),
        company_coverage=dict(
            status="annual_FY2022_to_FY2025_interims_2024_H1_to_2026_H1_no_Q1_Q3_2024_file",
            present_in_files_by_page_derived_period=["FY2022 (standalone)", "FY2023", "FY2024", "FY2025", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            values_verified_from_own_pages=["FY2022 (as issued)", "FY2023", "FY2024 (as issued)", "FY2025", "2025 H1", "2026 Q1", "2026 H1"],
            values_known_only_as_comparatives=["FY2021 as issued and restated (FY2022 and FY2023 files)", "2024 H1 and Q2 (H1 2025 filing)", "2025 Q1 and Q2 (Q1 2026 and H1 2026 filings)", "FY2024 restated and 1 Jan 2024 restated (FY2025 filing)"],
            values_not_read=["2024 H1 original", "2024 9M", "2025 Q1 original", "2025 9M"],
            missing=["2024 Q1", "everything before FY2021 (FY2021 as a standalone filing absent)", "FY2022 consolidated as originally issued (only standalone)"],
            inventory_corrections=("Labels are publication years for the FS files: the 2025|FY slot holds FY2022 standalone, FY2023, FY2024 (three English FS) plus the Arabic FY2025 FS and the Arabic annual report 2025; "
                                   "the English FY2025 FS is labelled 2026|FY. 89caf6ab has no period slot (Q1 2025 Arabic). 2026|H1 holds an earnings release that is image-only.")),
    ),
    defects=[
        dict(id="B013-6018-1", **{"class": "fiscal_year_label_is_publication_year_and_slot_collision"}, severity="high",
             evidence="Three English FS for FY2022, FY2023, FY2024 plus Arabic FY2025 FS and Arabic annual report 2025 all carry label 2025|FY; English FY2025 FS carries 2026|FY. A collector taking one file per label would drop two fiscal years."),
        dict(id="B013-6018-2", **{"class": "restated_or_represented_comparatives"}, severity="high",
             evidence="FY2024 profit 38,069,741 as issued vs 36,104,369 restated (Note 34); FY2022 profit 24,261,506 vs 22,682,826 and FY2021 11,175,889 vs 7,966,306 restated (Note 33); FY2024 CFO/CFF reclassified by 1,026,540. Both versions recorded in the transcript with the restated flag."),
        dict(id="B013-6018-3", **{"class": "image_only_statement_pages_not_detected"}, severity="medium",
             evidence="0032c8f3 (H1 2025) statement pages pdf p4, p5, p7 are textless images and the inventory only finds index pages; auditor's review reports on pdf p3-4 of the FS files are also textless."),
        dict(id="B013-6018-4", **{"class": "eps_basis_change"}, severity="low",
             evidence="2023 EPS 2.41 (weighted shares 10,400,000) in the FY2023 filing versus 0.24 in the FY2024 filing; FY2024 EPS 0.37 as issued, 0.35 restated."),
        dict(id="B013-6018-5", **{"class": "standalone_vs_consolidated_unexplained"}, severity="medium",
             evidence="FY2022 file is titled STANDALONE; FY2023 file's FY2022 comparative (consolidated, restated) shows cash 17,297,313 vs 15,895,356 and total assets 665,941,152 vs 673,178,718. Revenue is identical (268,043,244). Cause not verified on the pages read."),
    ],
    unread_items=["notes in all files except restatement and EPS notes", "statements of changes in equity", "Arabic twins and Arabic annual report", "9M 2024, H1 2024, Q1 2025, 9M 2025 financial statements",
                  "auditor's reports (textless pages)", "reason for FY2022 standalone vs consolidated difference"],
    conclusion=("NOT claimed complete. Seven filings value-verified from pages, two restatement chains recorded without substitution; 14 further files are not value-read; "
                "no file for 2024 Q1 and none before FY2021."),
)
mkrecord.build(spec)
