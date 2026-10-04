"""Builds raw-B015/8130.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SR'000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("41855727", "FY ended 2020-12-31 audited FS (collector label 2021|FY = publication year)", False, {"bs": 8, "is": "9-10", "cf": "14-15"}, {"bs": 6, "is": "7-8", "cf": "12-13"},
        "visual (statement pages textless scans)",
        "FY2019 comparatives are re-presented (gross IBNR and reinsurers' share of IBNR; investible contributions inside revenue); see defect B015-8130-3"),
    doc("c95c3409", "FY ended 2019-12-31 audited FS (label 2020|FY = publication year; inventory detected 2018-12-31, wrong)", False, {"bs": 8, "is": "9-10", "cf": "14-15"}, {"bs": 7, "is": "8-9", "cf": "13-14"},
        "visual (statement pages textless scans)", "2018 comparatives are marked Restated by the issuer; both original and restated recorded"),
    doc("16466467", "FY ended 2018-12-31 audited FS as issued (label 2019|FY = publication year)", False, {"bs": 7, "is": 8, "cf": "12-13"}, {"bs": 6, "is": 7, "cf": "11-12"},
        "visual (statement pages textless scans)"),
    doc("ae851486", "3M and 9M ended 2021-09-30 reviewed interim (label 2021|9M correct); latest period in the collection", True, {"bs": 4, "is": "5-6", "cf": "10-11"}, {"bs": 2, "is": "3-4", "cf": "8-9"},
        "visual (statement pages textless scans); note 1 (pdf p12) read for the proposed merger into Arabian Shield"),
]
identified = {
    "99ba47a0": ("3M and 9M ended 2018-09-30 interim (cover text)", "not transcribed"),
    "2498d78e": ("3M and 6M ended 2018-06-30 interim (cover image read); whole-file scan, zero text on all 36 pages, inventory class scanned_unreadable", "statements not opened; not transcribed"),
    "5321ab6f": ("3M ended 2018-03-31 interim (cover text)", "not transcribed"),
    "baf48a4c": ("3M and 9M ended 2019-09-30 interim (cover text)", "not transcribed"),
    "dd1acf6f": ("3M and 6M ended 2019-06-30 interim (cover text)", "not transcribed"),
    "1db14ae3": ("3M ended 2019-03-31 interim (cover text)", "not transcribed"),
    "9150504b": ("3M and 9M ended 2020-09-30 interim (cover text)", "not transcribed; 9M 2020 values known only as the comparative column in the 9M 2021 filing"),
    "31ec9ed2": ("3M and 6M ended 2020-06-30 interim (cover text)", "not transcribed"),
    "6b56185b": ("3M ended 2020-03-31 interim (cover text)", "not transcribed"),
    "598e9d12": ("3M and 6M ended 2021-06-30 interim (cover text)", "not transcribed"),
    "fdc45965": ("3M ended 2021-03-31 interim (cover text)", "not transcribed"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_4_filings_declared_restatements_and_representations_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) read from rendered scan pages for FY2020, FY2019, FY2018 (as issued) and 9M 2021 (with 3M columns). All identities hold exactly (balance sheet, cash-flow sum and roll, net income = pre-zakat income - zakat - tax). FY2020: total revenues 191,091, net income attributable to shareholders after zakat 8,019 (EPS 0.48), total assets 1,088,807, equity 249,946, CFO -18,848, CFI 32,942, closing cash 33,713 (FY2019 net income 7,338; FY2018 as issued 10,421). 9M 2021: net loss after zakat -858 (3M -4,700), total assets 1,126,660, CFO 790, closing cash 48,507. The statements are entity-level takaful statements with surplus from insurance operations attributed separately (shareholders' result shown before zakat); unit-linked investments (about 660 million) sit on the balance sheet. Declared differences: (1) FY2018 as issued net income 10,421 with no zakat line (EPS 0.63) versus restated 5,458 in the FY2019 filing (EPS 0.33); FY2018 CFO -36,500 and CFF -10,466 versus restated -35,130 and -11,836 (income-tax recovery reclassified). (2) FY2019 comparatives re-presented in the FY2020 filing: total assets 1,074,517 versus 1,092,355 and total liabilities 832,754 versus 850,592 (gross IBNR, difference 17,838), total revenues 52,538 versus 202,165 (investible contributions presented inside revenue); net underwriting income 32,338, net income 7,338 and equity 241,763 agree. No roll check was possible (no Q1/H1 2021 transcribed), so quarterly values by subtraction are NOT validated.",
        "not_read": ["notes in every file (except note 1 of 9M 2021)", "statements of changes in equity", "FY2017 comparatives (only 2017 balance sheet and cash flow transcribed from the FY2018 filing)", "all other interims", "auditor reports"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_four_files_opened_all_statement_pages_are_textless_scans",
        "summary": "FY2018, FY2019, FY2020 and 9M 2021 each carry balance sheet, income statement, cash-flow statement and equity statement as scanned pages with no text layer, although 14 of 15 files are classed financial_statements with statement_pages derived from note text. 2498d78e (H1 2018) is a whole-file scan classed scanned_unreadable whose statements were not opened. There is no FY2021 FS, no 2021 Q3-onwards and no post-merger filing: the entity merged into Arabian Shield (note 1 of the 9M 2021 filing), so the series is final, not truncated by the collector.",
        "defect_ids": ["B015-8130-1", "B015-8130-2", "B015-8130-3", "B015-8130-4"],
    },
    "company_coverage": {
        "status": "annual_FY2018_to_FY2020_and_interims_2018_to_2021_9M_final_series_entity_merged",
        "present_in_files_by_page_derived_period": ["FY2018 (label 2019|FY)", "FY2019 (label 2020|FY)", "FY2020 (label 2021|FY)",
                                                    "2018 Q1", "2018 H1 (scan)", "2018 9M", "2019 Q1", "2019 H1", "2019 9M", "2020 Q1", "2020 H1", "2020 9M", "2021 Q1", "2021 H1", "2021 9M"],
        "values_verified_from_own_pages": ["FY2018 (as issued)", "FY2019", "FY2020", "2021 9M and Q3 2021"],
        "values_known_only_as_comparatives": ["FY2017 (FY2018 filing, partial)", "FY2018 restated (FY2019 filing)", "9M 2020 and Q3 2020 (9M 2021 filing)"],
        "values_not_read": ["2018 Q1/H1/9M", "2019 Q1/H1/9M", "2020 Q1/H1/9M", "2021 Q1/H1"],
        "missing": ["FY2017 and earlier (no file)", "FY2021 and everything after 2021 9M (entity merged into Arabian Shield, per note 1)"],
        "inventory_corrections": "FY labels equal the publication year in all three FS files (2019|FY holds FY2018, 2020|FY FY2019, 2021|FY FY2020); the inventory detected 2018-12-31 for c95c3409 (the comparative column), but its primary period is 2019-12-31. Registry symbol 8130 'ATC' is Alahli Takaful Company (verified from covers and note 1), a legal entity that no longer exists; its successor series belongs to Arabian Shield and must not be appended.",
    },
}
defects = [
    {"id": "B015-8130-1", "class": "image_only_or_scanned_statements_flagged_as_present", "severity": "high",
     "evidence": "All four opened files have textless statement pages (FY2020 pdf p3-13 textless; FY2019 p3-13; FY2018 p3-13; 9M 2021 p3-11) although classed financial_statements; 2498d78e is a 36-page zero-text scan classed scanned_unreadable."},
    {"id": "B015-8130-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "16466467 (FY2018) is labelled 2019|FY, c95c3409 (FY2019) 2020|FY, 41855727 (FY2020) 2021|FY; the 2021|FY slot therefore does not hold FY2021 and no FY2021 file exists. Inventory flagged detected=2018-12-31 against label 2019|FY."},
    {"id": "B015-8130-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "FY2018 net income 10,421 as issued (16466467 pdf p8) versus 5,458 restated after zakat in the FY2019 filing (c95c3409 pdf p10); FY2018 CFO -36,500 versus -35,130, CFF -10,466 versus -11,836 (pdf p12-13 versus p14-15). FY2019 total assets 1,074,517 (c95c3409 pdf p8) versus 1,092,355 re-presented in FY2020 (41855727 pdf p8); total revenues 52,538 versus 202,165. Both values recorded, none substituted; a revenue series across 2019/2020 mixes two definitions."},
    {"id": "B015-8130-4", "class": "merged_or_delisted_entity", "severity": "medium",
     "evidence": "9M 2021 note 1 (ae851486 pdf p12): binding merger agreement of 12 July 2021 into Arabian Shield Cooperative Insurance Company, exchange ratio 1.43114769137705 Arabian Shield shares per ATC share. No FS after 9M 2021 exist for this symbol; absence of FY2021 and later is genuine, not a collection gap."},
]
unread = ["notes (except note 1 of 9M 2021)", "statements of changes in equity", "H1 2018 scan statements", "11 interim filings 2018 Q1 to 2021 H1 (identified by cover only)", "FY2017 and earlier (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Four filings value-verified from rendered scan pages (FY2018 as issued, FY2019, FY2020, 9M 2021); two restatements/re-presentations declared with both values; "
              "11 interim filings identified by cover but not value-read; the series ends legitimately at 9M 2021 because the entity merged into Arabian Shield.")
mkrecord.build(dict(
    symbol="8130", name="ALAHLI TAKAFUL COMPANY (ATC)", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. All statement pages of the four audited filings are textless scans and were rendered and read by eye (balance sheet, income statement, cash flow). "
            "tools/check_transcripts.py over transcripts/8130.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat income plus zakat/tax to net income, and cross-filing comparatives "
            "(declared differences only: FY2018 restatement keys, FY2019 re-presentation keys); all pass. No roll checks (no consecutive interims transcribed).")))
