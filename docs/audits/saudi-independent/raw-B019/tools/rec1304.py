"""Builds raw-B019/1304.json (audit record) from the page transcripts."""
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
    doc("ee5be447", "FY ended 2025-09-30 consolidated FS, label 2026|FY", False, {"bs": 9, IS: 10, "cf": "12-13"}, {"bs": 7, IS: 8, "cf": "10-11"}, VIS, "equity statement (pdf p11) and auditor report not read"),
    doc("64c896ec", "FY ended 2024-09-30 consolidated FS as issued, label 2025|FY", False, {"bs": 10, IS: 11, "cf": "13-14", "equity": 12}, {"bs": 8, IS: 9, "cf": "11-12", "equity": 10}, VIS, "pdf p9 auditor-report last page viewed; remaining report pages not read; equity statement p12 viewed for layout, values not transcribed"),
    doc("46c6fed7", "FY ended 2023-09-30 consolidated FS as issued, label 2024|FY", False, {"bs": 10, IS: 11, "cf": "13-14"}, {"bs": 8, IS: 9, "cf": "11-12"}, VIS),
    doc("4b97c75b", "FY ended 2022-09-30 consolidated FS as issued, label 2022|FY (not publication year + 1); whole file image-only; inventory class partial_statements", False, {"bs": 10, IS: 11, "cf": 13}, {"bs": 8, IS: 9, "cf": 11}, VIS, "auditor report last page viewed (dated 2022-12-29)"),
    doc("8e302b19", "9M ended 2026-06-30 interim (Q3 FY2026)", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "4-5"}, VIS),
    doc("88a11f9b", "6M ended 2026-03-31 interim (Q2 FY2026)", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "4-5"}, VIS),
    doc("302c92d2", "3M ended 2025-12-31 interim (Q1 FY2026); pdf p5 text layer holds titles only, figures read from image", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, VIS),
    doc("1520e347", "9M ended 2025-06-30 interim as issued (Q3 FY2025); inventory class partial_statements", True, {"bs": 4, IS: 5, "cf": "7-8"}, {"bs": 2, IS: 3, "cf": "5-6"}, VIS),
]

SC = "whole-file scan; cover image viewed; statements not read"
identified = {
    "08e494d9": ("3M ended 2021-12-31 (Q1 FY2022; cover text)", "classed other_no_statements_found; not transcribed"),
    "9564e270": ("6M ended 2022-03-31 (cover text)", "classed other_no_statements_found; not transcribed"),
    "b6719f64": ("9M ended 2022-06-30 (cover image)", SC),
    "78bac1bb": ("3M ended 2022-12-31 (Q1 FY2023; cover text)", "statement pages pdf p3-8 textless; not transcribed"),
    "2c49af57": ("6M ended 2023-03-31 (cover image)", SC),
    "76ecc611": ("9M ended 2023-06-30 (cover text)", "statement pages pdf p4-8 textless; not transcribed"),
    "1c7379ce": ("3M ended 2023-12-31 (Q1 FY2024; cover text)", "statement pages pdf p3-8 textless; not transcribed"),
    "105c93b9": ("6M ended 2024-03-31 (cover image)", SC),
    "b2a66e5a": ("9M ended 2024-06-30 (cover image)", SC + "; inventory class other_no_statements_found"),
    "1250b105": ("3M, period not confirmed from text (label 2025|Q1, expected 2024-12-31)", "statement pages pdf p3-8 textless; not opened beyond text layer; Q1 FY2025 values known as comparatives in the Q1 FY2026 filing"),
    "92b990d7": ("6M ended 2025-03-31 (cover text)", "statement pages pdf p4-8 textless; not transcribed; 6M and Q2 FY2025 known as comparatives in the H1 FY2026 filing"),
}

method = ("SHA-256 recomputed for every audited file. Statement pages of all eight audited filings are image-only (the text layer is empty or holds titles only) and were rendered and read by eye. "
          "Fiscal year ends 30 September; periods below are page-derived. tools/check_transcripts.py over transcripts/1304.json checks BS identity, cash-flow sum and roll, gross profit, profit before zakat plus zakat to net profit, owners plus NCI, cross-filing agreement of comparatives (restated and re-presented columns carry written reasons), and Q1+Q2=H1 / H1+Q3=9M rolls for revenue, profit before zakat and net profit; "
          "the checker was extended with a per-column _tol (riyals) used only where the printed totals of the issuer differ by 1 riyal (FY2023 balance sheet, 9M FY2025 cash flow); all checks pass.")

dimensions = {
    "value_correctness": {
        "status": "verified_for_8_filings_with_declared_reclassifications_and_rounding",
        "summary": ("Headline BS, income and cash-flow values (full SAR) read from pages for FY2022-FY2025 (fiscal years ended 30 September), 3M to 2025-12-31, 6M to 2026-03-31, 9M to 2025-06-30 and 9M to 2026-06-30. "
                    "FY2025: sales 1,878,583,619, net profit 55,916,567 (shareholders 59,687,481, NCI -3,770,914), total assets 1,765,063,929, equity 719,873,964, CFO 123,279,072, cash 33,523,454. FY2024: sales 1,956,591,394, net profit 70,246,174, CFO 187,556,296. FY2023: sales 1,559,533,721, net loss -165,144,363 (gross loss -28,294,711), CFO 138,857,778. FY2022: revenue 1,464,976,007, net loss -17,013,073; FY2021 revenue 1,619,027,590 and net profit 244,542,992 known from the FY2022 filing. 9M to 2026-06-30: revenue 1,571,539,377, net profit 155,111,224 (Q3 69,974,485). "
                    "Declared differences, never substituted: (1) FY2022 re-presented in the FY2023 filing: operating income 12,509,260 vs 12,143,497 as issued (administrative expenses and other revenue), CFO -286,677,049 vs -283,478,618 and CFI -97,561,307 vs -100,759,738 (3,198,431 realized gains moved); profit before zakat -3,646,320 unchanged. "
                    "(2) FY2023 re-presented in the FY2024 filing: cost of sales -1,587,952,499 vs -1,587,828,432, gross loss -28,418,778 vs -28,294,711, operating loss -95,432,612 vs -95,308,545 (124,067 PPE impairment reversal moved). (3) FY2023 balance sheet prints total equity 620,361,936 and the FY2024 filing 620,361,935 (1 riyal rounding; liabilities + equity = 1,790,893,284 vs assets 1,790,893,283). "
                    "(4) 30 Sep 2025 balance sheet comparatives in the 2026 interim filings show liabilities 1,045,189,958 and equity 719,873,971 vs 1,045,189,965 / 719,873,964 in the FY2025 filing (7 riyals). "
                    "(5) 9M 2025 cash flow re-presented in the 9M 2026 filing: CFO -46,403,752 and CFF 71,143,197 vs -1,820,695 and 26,560,141 as issued (finance costs paid moved to operating; net change -28,759,523 unchanged; the 9M 2025 issued components sum to -28,759,522, 1 riyal). "
                    "(6) H1 FY2026 and 9M FY2026 income-statement quarters do not roll on cost of sales and gross profit although revenue, pre-zakat profit and net profit do (within 10 riyals): Q1 FY26 cost 421,573,934 + Q2 436,108,825 = 857,682,759 vs 6M 858,431,498 (748,739 reclassified with administrative expenses); 6M + Q3 cost differs from 9M by 27,831. A quarter derived by subtracting cost of sales across filings is therefore NOT validated. "
                    "(7) Quarterly cash flow by subtraction not validated: Q1 FY26 CFO -68,453,438 vs 6M -245,905,051 vs 9M -240,449,946. Zakat is a credit in 6M and 9M FY2025 (reversal of provisions). No going-concern paragraph read (notes not read)."),
        "not_read": [
            "notes in every file",
            "statements of changes in equity",
            "auditor and review report pages (only two signature pages viewed)",
            "2022-2024 interim filings and H1/Q1 FY2025 filings; scan files",
            "FY2021 and earlier own FS",
        ],
    },
    "document_completeness": {
        "status": "annual_FY2022_to_FY2025_and_interims_Q1_FY26_to_Q3_FY26_plus_Q3_FY25_read",
        "summary": ("Statement pages of all 19 files are image-only or scans; the inventory classes FY2022 (partial) and many interims (partial or no-statements) understate content: the FY2022 file holds full statements as page images; four files are whole-file scans (9M 2022, H1 2023, H1 2024, 9M 2024) whose covers announce full statements. "
                    "Fiscal year ends 30 September, not 31 December; collector interim labels follow the fiscal year (Q1 = Oct-Dec) but FY labels are inconsistent: 2022|FY holds FY ended 2022-09-30 (signed Dec 2022) whereas 2024|FY holds FY2023, 2025|FY holds FY2024, 2026|FY holds FY2025, and no 2023|FY file exists. "
                    "Nine-month interim statements are headed by a June period end (correct for a September year end). Unit is full SAR. No Arabic twins in this set."),
        "defect_ids": ["B019-1304-1", "B019-1304-2", "B019-1304-3"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_present_with_statements; interims FY2022_to_FY2026_present_by_cover",
        "present_in_files_by_page_derived_period": [
            "FY2022, FY2023, FY2024, FY2025 (year ended 30 September)",
            "Q1 (3M to Dec): 2021, 2022, 2023, 2024 (label unconfirmed), 2025",
            "H1 (6M to Mar): 2022, 2023, 2024, 2025, 2026",
            "9M (to Jun): 2022, 2023, 2024, 2025, 2026",
        ],
        "values_verified_from_own_pages": ["FY2022", "FY2023", "FY2024", "FY2025", "Q1 FY2026 (3M to 2025-12-31)", "H1 FY2026 (6M to 2026-03-31)", "9M FY2026 (to 2026-06-30)", "9M FY2025 (to 2025-06-30)"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "Q1 FY2025, 6M FY2025, Q2 FY2025 (2026 filings)", "9M FY2024 and Q3 FY2024 (9M 2025 filing)"],
        "values_not_read": ["Q1 FY2022 to Q1 FY2025 filings", "H1 FY2022 to H1 FY2025", "9M FY2022 to 9M FY2024", "FY2025 Q1 and H1 own filings"],
        "missing": ["FY2021 and earlier own FS", "no Q4 file as such (derivable from FY less 9M)"],
        "inventory_corrections": "Inventory gives fiscal_year_end_month 9 correctly; period labels are inconsistent for FY files (see document_completeness).",
    },
}

defects = [
    {"id": "B019-1304-1", "kind": "inventory_class", "detail": "All statement pages are image-only: 4b97c75b (FY2022, class partial), 1520e347, 92b990d7, 1250b105, 76ecc611, 78bac1bb, 1c7379ce (partial) and four whole-file scans (b6719f64, 2c49af57, 105c93b9, b2a66e5a; class scanned_unreadable or other) are not text-extractable."},
    {"id": "B019-1304-2", "kind": "label_semantics", "detail": "FY labels mix conventions (2022|FY = FY2022 filed Dec 2022; later FY labels are FY end year + 1); no 2023|FY file; interim labels follow the fiscal year."},
    {"id": "B019-1304-3", "kind": "reclassifications_and_rounding", "detail": "FY2022/FY2023 comparatives re-presented, 9M 2025 cash flow re-presented, 2026 interim quarters do not roll on cost of sales, and printed totals differ by 1 to 7 riyals in places. All declared; no value substituted."},
]

unread = [
    "notes to the financial statements in every file (going-concern, restatement, related parties, loans, zakat reversals)",
    "statements of changes in equity and auditor/review reports",
    "Q1 FY2022 to Q1 FY2025, H1 FY2022 to H1 FY2025, 9M FY2022 to 9M FY2024 filings (including four whole-file scans)",
    "1250b105 period not confirmed",
    "FY2021 and earlier",
]

spec = dict(
    symbol="1304",
    name="ALYAMAMAH STEEL (Al Yamamah Steel Industries Company)",
    method=method,
    documents=documents,
    identified=identified,
    dimensions=dimensions,
    defects=defects,
    unread_items=unread,
    conclusion="Company is NOT claimed complete: annual FY2022-FY2025 and four interims were read; earlier interims, four scans, notes and equity statements are unread; the September fiscal year and inconsistent FY labels must be handled by page-derived periods.",
)
if __name__ == "__main__":
    mkrecord.build(spec)
