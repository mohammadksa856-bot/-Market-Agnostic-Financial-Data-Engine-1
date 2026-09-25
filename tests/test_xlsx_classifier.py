import glob
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None

from finengine.reading_xlsx import _column_period
from finengine.xlsx_classifier import (
    MappingSelectionError, fingerprint_workbook, load_mappings, select_mapping,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "supplements"


def _mapping(sheet="Income Statement", labels=None, company="sa:0001"):
    labels = labels or [f"line item {i}" for i in range(10)]
    return {"company_id": company, "scale": "1000000", "period_kinds": ["fy", "quarter"],
            "sheets": {sheet: {label: [f"metric_{i}", "flow"] for i, label in enumerate(labels)}}}


def _workbook(path, sheets):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(row)
    wb.save(path)


@unittest.skipIf(openpyxl is None, "openpyxl is not installed")
class PeriodHeaderTests(unittest.TestCase):
    def test_header_spellings(self):
        self.assertEqual(_column_period("FY 2023"), ("fy", 2023, "2023-12-31"))
        self.assertEqual(_column_period("1Q25"), ("quarter", 2025, "2025-03-31"))
        self.assertEqual(_column_period("Q3'24"), ("quarter", 2024, "2024-09-30"))
        self.assertEqual(_column_period("2025 Q2"), ("quarter", 2025, "2025-06-30"))
        self.assertEqual(_column_period("1H-24"), ("ytd", 2024, "2024-06-30"))

    def test_non_periods_still_rejected(self):
        for text in ("Q5 2025", "FY 1999", "Total 25", "Note 2", "2025"):
            self.assertIsNone(_column_period(text), text)


@unittest.skipIf(openpyxl is None, "openpyxl is not installed")
class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.maps = self.dir / "maps"
        self.maps.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write_map(self, name, mapping):
        (self.maps / name).write_text(json.dumps(mapping), encoding="utf-8")

    def _book(self, name="book.xlsx", sheet="Income Statement", labels=None, header=None):
        labels = labels or [f"line item {i}" for i in range(10)]
        path = self.dir / name
        _workbook(path, {sheet: [["SAR mn"] + (header or ["FY 2024", "1Q 2025"])]
                         + [[label, 1, 2] for label in labels]})
        return path

    def test_structural_match_selects_mapping_and_keeps_hash(self):
        self._write_map("a.json", _mapping())
        book = self._book()
        before = hashlib.sha256(book.read_bytes()).hexdigest()
        chosen = select_mapping(book, self.maps)
        self.assertEqual(chosen["selection"]["mapping"], "a.json")
        self.assertEqual(chosen["selection"]["workbook_sha256"], before)
        self.assertEqual(hashlib.sha256(book.read_bytes()).hexdigest(), before)

    def test_company_identity_never_selects_a_mapping(self):
        # Mapping owner and document company agree, yet the workbook does not
        # match structurally: identity must not rescue it.
        self._write_map("owner.json", _mapping(company="sa:1060"))
        book = self._book(sheet="Totally Different", labels=["alpha", "beta"])
        with self.assertRaises(MappingSelectionError) as ctx:
            select_mapping(book, self.maps, document_company_id="sa:1060")
        self.assertEqual(ctx.exception.code, "xlsx_mapping_required")

    def test_no_match_carries_sheet_and_header_evidence(self):
        self._write_map("a.json", _mapping())
        book = self._book(sheet="Statement of Profit", labels=["alpha", "beta"], header=["FY 2024"])
        with self.assertRaises(MappingSelectionError) as ctx:
            select_mapping(book, self.maps)
        ev = ctx.exception.evidence
        self.assertEqual(ev["sheet_names"], ["Statement of Profit"])
        self.assertEqual(ev["sheets"][0]["period_columns"], 1)
        self.assertEqual(ev["top_candidates"][0]["missing_sheets"], ["Income Statement"])
        self.assertEqual(len(ev["sha256"]), 64)

    def test_date_typed_headers_are_diagnosed(self):
        import datetime
        self._write_map("a.json", _mapping())
        path = self.dir / "dates.xlsx"
        _workbook(path, {"Income Statement": [
            ["SAR mn", datetime.datetime(2025, 3, 31), datetime.datetime(2025, 6, 30)],
            ["line item 0", 1, 2]]})
        with self.assertRaises(MappingSelectionError) as ctx:
            select_mapping(path, self.maps)
        diag = ctx.exception.evidence["diagnosis"]
        self.assertEqual(diag["date_typed_header_cells"], 2)
        self.assertIn("Income Statement", diag["sheets_without_parseable_period_headers"])

    def test_two_indistinguishable_mappings_are_ambiguous(self):
        self._write_map("a.json", _mapping())
        self._write_map("b.json", _mapping(company="sa:0002"))
        with self.assertRaises(MappingSelectionError) as ctx:
            select_mapping(self._book(), self.maps)
        self.assertEqual(ctx.exception.code, "xlsx_mapping_ambiguous")
        self.assertEqual(sorted(ctx.exception.evidence["ambiguous_between"]), ["a.json", "b.json"])

    def test_cross_issuer_reuse_needs_near_complete_match(self):
        labels = [f"line item {i}" for i in range(10)]
        self._write_map("a.json", _mapping(labels=labels + ["x1", "x2"], company="sa:0001"))
        # 10 of 12 phrases present = 0.83: below the 0.85 floor for anyone.
        with self.assertRaises(MappingSelectionError):
            select_mapping(self._book(labels=labels), self.maps, document_company_id="sa:0001")
        self._write_map("a.json", _mapping(labels=labels + ["x1"], company="sa:0001"))
        # 10 of 11 = 0.91: fine for the owner, too weak for another issuer.
        chosen = select_mapping(self._book(labels=labels), self.maps, document_company_id="sa:0001")
        self.assertFalse(chosen["selection"]["cross_issuer"])
        with self.assertRaises(MappingSelectionError):
            select_mapping(self._book(labels=labels), self.maps, document_company_id="sa:0002")

    def test_unreadable_workbook_is_a_precise_refusal(self):
        bad = self.dir / "bad.xlsx"
        bad.write_bytes(b"PK\x03\x04 not really")
        with self.assertRaises(MappingSelectionError) as ctx:
            select_mapping(bad, self.maps)
        self.assertTrue(ctx.exception.evidence["unreadable"])

    def test_fingerprint_reports_statement_type_units_and_periods(self):
        path = self.dir / "fp.xlsx"
        _workbook(path, {
            "Balance": [["SAR mn", "FY 2023", "FY 2024"], ["Total assets", 5, 6], ["Total liabilities", 3, 4]],
            "P&L": [["SAR '000", "1Q25", "2Q25"], ["Net income", 1, 2]]})
        sheets = {s.name: s for s in fingerprint_workbook(path)["sheets"]}
        self.assertEqual(sheets["Balance"].statement_type, "balance")
        self.assertEqual(sheets["Balance"].period_kinds, ["fy"])
        self.assertEqual(sheets["P&L"].statement_type, "income")
        self.assertEqual(sheets["P&L"].last_period, "2025-06-30")
        self.assertTrue(sheets["P&L"].unit_evidence[0].endswith("=>1000"))
        self.assertEqual(sheets["P&L"].header_row, 1)


@unittest.skipIf(openpyxl is None, "openpyxl is not installed")
class ArchivedWorkbookTests(unittest.TestCase):
    """Every archived Saudi workbook must select exactly its own reviewed map."""

    def test_archived_workbooks_select_their_own_mapping_by_structure(self):
        books = sorted(glob.glob(str(ROOT / "data" / "raw" / "SA" / "*" / "documents" / "*.xlsx")))
        if not books:
            self.skipTest("no archived workbooks")
        for book in books:
            symbol = Path(book).parents[1].name
            before = hashlib.sha256(Path(book).read_bytes()).hexdigest()
            # No document_company_id: selection is by structure alone.
            chosen = select_mapping(book, CONFIG)
            self.assertEqual(chosen["selection"]["mapping"], f"{symbol}.json", book)
            self.assertEqual(chosen["selection"]["workbook_sha256"], before)
            self.assertEqual(hashlib.sha256(Path(book).read_bytes()).hexdigest(), before)

    def test_foreign_layout_is_not_selected_for_another_issuer(self):
        # Al Rajhi's workbook fully matches only Al Rajhi's own layout.
        book = next(iter(glob.glob(str(ROOT / "data/raw/SA/1120/documents/*.xlsx"))), None)
        if not book:
            self.skipTest("no Al Rajhi workbook")
        chosen = select_mapping(book, CONFIG, document_company_id="sa:1120")
        self.assertEqual(chosen["selection"]["mapping"], "1120.json")
        self.assertGreaterEqual(len(load_mappings(CONFIG)), 7)
