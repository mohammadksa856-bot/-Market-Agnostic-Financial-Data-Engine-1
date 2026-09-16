"""Bank AlJazira's filing layouts, which no other Saudi bank in the corpus prints.

Its KM1 tables label the columns with relative position tags instead of dates,
punctuate quarters with a comma, declare the amount unit on other templates,
print capital to two decimals, and close a bracket the caption never opened.
Its quarterly supplement respells the worksheet tab between vintages.
"""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False

try:
    import openpyxl
    HAVE_OPENPYXL = True
except ImportError:  # pragma: no cover
    HAVE_OPENPYXL = False

_X = (330, 390, 450, 510, 570)
_DATED_HEADERS = ("30 Jun 2026", "31 Mar 2026", "31 Dec 2025", "30 Sep 2025", "30 Jun 2025")
_TAG_HEADERS = ("a T", "b T-1", "c T-2", "d T-3", "e T-4")
_QUARTER_ENDS = ["2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]


def _capital_rows():
    return [
        ("1", "Common Equity Tier 1 (CET1)",
         ("150,000,000", "148,000,000", "146,000,000", "144,000,000", "142,000,000")),
        # The KM1 page is recognised by its own row captions, and this one is
        # part of that signature, so the fixture carries it as issuers do.
        ("1a", "Fully loaded ECL accounting model CET1",
         ("150,000,000", "148,000,000", "146,000,000", "144,000,000", "142,000,000")),
        ("2", "Tier 1",
         ("170,000,000", "168,000,000", "166,000,000", "164,000,000", "162,000,000")),
        ("3", "Total capital",
         ("180,000,000", "178,000,000", "176,000,000", "174,000,000", "172,000,000")),
        ("4", "Total risk-weighted assets (RWA)",
         ("850,000,000", "840,000,000", "830,000,000", "820,000,000", "810,000,000")),
        ("5", "CET1 ratio (%)", ("17.65%", "17.62%", "17.59%", "17.56%", "17.53%")),
        ("6", "Tier 1 ratio (%)", ("20.00%", "20.00%", "20.00%", "20.00%", "20.00%")),
        ("7", "Total capital ratio (%)", ("21.18%", "21.19%", "21.20%", "21.22%", "21.23%")),
    ]


def _km1_pdf(path, rows, *, unit, headers, note=None, later_page_text=None):
    """A KM1 page that may state its period in prose and its unit elsewhere."""
    document = pymupdf.open()
    cover = document.new_page(width=640, height=842)
    cover.insert_text((50, 80), "Table of contents - Key metrics KM1 page 2", fontsize=11)
    page = document.new_page(width=640, height=842)
    page.insert_text((50, 70), "KM1 - Key metrics (at consolidated group level)", fontsize=11)
    if note:
        page.insert_text((50, 88), note, fontsize=8)
    if unit:
        page.insert_text((50, 110), unit, fontsize=8)
    for x, header in zip(_X, headers):
        page.insert_text((x - 20, 110), header, fontsize=8)
    y = 140
    for row_id, label, values in rows:
        page.insert_text((50, y), row_id, fontsize=8)
        page.insert_text((70, y), label, fontsize=8)
        for x, value in zip(_X, values):
            page.insert_text((x - 20, y), value, fontsize=8)
        y += 14
    if later_page_text:
        document.new_page(width=640, height=842).insert_text(
            (50, 80), later_page_text, fontsize=9)
    document.save(path)
    document.close()


@unittest.skipUnless(HAVE_PYMUPDF, "the KM1 reader needs the optional pymupdf extra")
class AlJaziraKeyMetricsLayoutTests(unittest.TestCase):
    def _read(self, directory, rows, **kwargs):
        from finengine.reading_pillar3 import Pillar3KeyMetricsReader

        pdf = Path(directory) / "km1.pdf"
        _km1_pdf(pdf, rows, **kwargs)
        return Pillar3KeyMetricsReader(pdf).read(
            "SA", "1020", "SAR", "https://issuer.example/pillar3.pdf", "2026-09-16")

    def test_comma_punctuated_quarter_headers_are_dated(self):
        # "Q1, 2022" - the comma stands where other issuers print a space.
        from finengine.reading_pillar3 import _quarter_end

        self.assertEqual(_quarter_end("a Q1, 2022"), date(2022, 3, 31))
        self.assertEqual(_quarter_end("Q3, 2021"), date(2021, 9, 30))
        self.assertIsNone(_quarter_end("Q5, 2021"))

    def test_comma_form_of_the_thousands_declaration(self):
        from finengine.reading_pillar3 import Pillar3KeyMetricsReader

        self.assertEqual(Pillar3KeyMetricsReader._scale("KM1 table\nSAR,000"), 1000)

    def test_relative_tag_columns_anchor_on_the_quarter_stated_on_the_page(self):
        # The columns carry only T, T-1 ... T-4 and the page names the quarter.
        # The unit and the table caption land in the same header band.
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(
                name, _capital_rows(), unit="SR 000's", headers=_TAG_HEADERS,
                note="Basel III Pillar 3 Disclosures as of Q2 2026, ajb")
        self.assertEqual(
            sorted({fact["period_end"] for fact in manifest["facts"]}), _QUARTER_ENDS)

    def test_relative_tags_are_not_dated_when_the_page_names_two_quarters(self):
        from finengine.reading_pillar3 import Pillar3ReadError

        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(Pillar3ReadError) as caught:
                self._read(name, _capital_rows(), unit="SR 000's", headers=_TAG_HEADERS,
                           note="Disclosures for Q2 2026 compared with Q1 2026")
        self.assertEqual(caught.exception.code, "period_headers_unverifiable")

    def test_amount_carrying_separators_and_decimals_is_a_figure(self):
        from finengine.reading_pillar3 import _AMOUNT

        self.assertTrue(_AMOUNT.match("12,545,339.89"))
        self.assertTrue(_AMOUNT.match("12,545,339"))
        self.assertFalse(_AMOUNT.match("1.5"))
        rows = [(row_id, label,
                 tuple(value + ".00" if row_id == "1" else value for value in values))
                for row_id, label, values in _capital_rows()]
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(name, rows, unit="SAR,000", headers=_DATED_HEADERS)
        self.assertTrue([fact for fact in manifest["facts"]
                         if fact["metric"] == "cet1_capital"],
                        "a decimal figure must stay a value, not join the caption")

    def test_caption_closing_a_bracket_it_never_opened_is_read(self):
        rows = [(row_id, "Common Equity Tier 1 (CET1) )" if row_id == "1" else label, values)
                for row_id, label, values in _capital_rows()]
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(name, rows, unit="SAR,000", headers=_DATED_HEADERS)
        self.assertTrue([fact for fact in manifest["facts"]
                         if fact["metric"] == "cet1_capital"])

    def test_unit_is_taken_from_the_document_when_the_km1_page_omits_it(self):
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(
                name, _capital_rows(), unit=None, headers=_DATED_HEADERS,
                later_page_text="B.9.1 Geographic breakdown (Figures in SAR 000's)")
        cet1 = next(fact for fact in manifest["facts"] if fact["metric"] == "cet1_capital")
        self.assertEqual(cet1["value"], "150000000")
        # The scale is what the fallback recovered: the figures are thousands.
        self.assertEqual(cet1["scale"], "1000")

    def test_a_document_declaring_no_unit_anywhere_still_fails(self):
        from finengine.reading_pillar3 import Pillar3ReadError

        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(Pillar3ReadError) as caught:
                self._read(name, _capital_rows(), unit=None, headers=_DATED_HEADERS,
                           later_page_text="Geographic breakdown of exposures")
        self.assertEqual(caught.exception.code, "unit_not_declared")


@unittest.skipUnless(HAVE_OPENPYXL, "the supplement reader needs the optional openpyxl extra")
class AlJaziraSupplementTabTests(unittest.TestCase):
    def test_worksheet_named_with_a_stray_space_still_matches(self):
        # AlJazira ships "Income Statment " in one quarter's supplement and
        # "Income Statment" in the next. The spelling is the tab's identity;
        # the surrounding whitespace is not.
        from finengine.reading_xlsx import SupplementReader

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Income Statement "
            sheet.append(["SAR (mn)", "FY 2025"])
            sheet.append(["Net financing income", 29000])
            path = directory / "supplement.xlsx"
            workbook.save(path)
            mapping = directory / "mapping.json"
            mapping.write_text(json.dumps({
                "company_id": "sa:9999",
                "source_url": "https://issuer.example/supplement.xlsx",
                "scale": "1000000",
                "sheets": {"Income Statement": {
                    "Net financing income": ["net_financing_income", "fy"]}},
            }), encoding="utf-8")
            manifest = SupplementReader(path, mapping).read("SA", "9999", "SAR", "2026-01-31")
        self.assertEqual([fact["value"] for fact in manifest["facts"]], ["29000"])
        self.assertEqual([fact["scale"] for fact in manifest["facts"]], ["1000000"])
