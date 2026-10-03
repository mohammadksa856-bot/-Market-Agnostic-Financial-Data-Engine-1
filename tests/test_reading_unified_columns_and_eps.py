"""Offline regression tests for two defects found by the unified before/after re-read:
aljazira-2008-q2 (prior-year six-month figure read for the current six-month column)
and anb-2019-annual-report (EPS printed with a decimal comma read as thousands)."""
import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False


def _read(pdf, period_end, fiscal_year, filing_type):
    from finengine.reading import StatementReader

    return StatementReader(pdf, enable_ocr=False).read(
        "SA", "9999", "SAR", "https://example.invalid/x.pdf", "2024-08-01",
        period_end=period_end, fiscal_year=fiscal_year, filing_type=filing_type, profile="bank")["facts"]


def _put_right(page, right, y, text):
    width = pymupdf.get_text_length(text, fontsize=9)
    page.insert_text((right - width, y), text, fontsize=9)


@unittest.skipUnless(HAVE_PYMUPDF, "requires pymupdf")
class TightFourColumnRowsTests(unittest.TestCase):
    """Right-aligned short figures sit nearer the next header centre than their own."""

    ROWS = [
        ("Special commission income", ["254,450", "227,177", "523,754", "432,350"]),
        ("Exchange income, net", ["5,204", "3,915", "9,037", "7,273"]),
        ("Trading income, net", ["6,489", "7,385", "1,784", "11,841"]),
        ("Dividend income", ["1,994", "5,501", "6,330", "6,602"]),
        ("Other operating income", ["2,676", "473", "2,717", "3,787"]),
        ("Total operating expenses", ["231,255", "156,651", "419,914", "269,501"]),
        ("Net income for the period", ["100,062", "206,677", "253,157", "508,994"]),
        ("Total operating income", ["331,317", "363,328", "673,071", "778,495"]),
        ("Basic and diluted earnings per share (expressed in SR)", ["0.33", "0.69", "0.84", "1.70"]),
    ]

    def _pdf(self, path):
        doc = pymupdf.open()
        page = doc.new_page(width=900, height=792)
        page.insert_text((40, 38), "CONSOLIDATED STATEMENTS OF INCOME", fontsize=12)
        page.insert_text((40, 66), "FOR THE THREE AND SIX MONTHS ENDED JUNE 30, 2008 AND 2007", fontsize=9)
        page.insert_text((545, 120), "Three Months Ended", fontsize=9)
        page.insert_text((690, 120), "Six Months Ended", fontsize=9)
        centres = [535.7, 613.4, 717.8, 785.5]
        for c, year in zip(centres, ["2008", "2007", "2008", "2007"]):
            page.insert_text((c - 50, 144), "June 30,", fontsize=9)
            page.insert_text((c - 9, 144), year, fontsize=9)
        # centres measured on the archived page: 6-digit figures vs 4-digit figures
        # (right-aligned, so the short ones sit ~5pt further left)
        wide = [505.6, 581.4, 687.2, 755.6]
        narrow = [500.2, 577.1, 682.1, 749.5]
        for i, (label, values) in enumerate(self.ROWS):
            y = 180 + i * 12
            page.insert_text((40, y), label, fontsize=9)
            for k, v in enumerate(values):
                c = (wide if len(v) >= 7 else narrow)[k]
                page.insert_text((c - pymupdf.get_text_length(v, fontsize=9) / 2, y), v, fontsize=9)
        doc.save(path)
        doc.close()

    def test_current_six_month_figure_is_read_not_prior_year(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "is.pdf"
            self._pdf(pdf)
            facts = _read(pdf, "2008-06-30", 2008, "interim-report")
        got = {(f["metric"], f["period_kind"]): f["value"] for f in facts}
        self.assertEqual(got[("exchange_income", "ytd")], "9037")
        self.assertEqual(got[("exchange_income", "quarter")], "5204")
        self.assertEqual(got[("trading_income", "ytd")], "1784")
        self.assertEqual(got[("dividend_income", "ytd")], "6330")
        self.assertEqual(got[("other_income", "ytd")], "2717")
        self.assertEqual(got[("eps_diluted", "ytd")], "0.84")
        self.assertEqual(got[("financing_income", "ytd")], "523754")


@unittest.skipUnless(HAVE_PYMUPDF, "requires pymupdf")
class DecimalCommaEpsTests(unittest.TestCase):
    def _pdf(self, path):
        doc = pymupdf.open()
        page = doc.new_page(width=612, height=792)
        page.insert_text((50, 60), "Consolidated Statement of Income", fontsize=12)
        page.insert_text((50, 76), "For the years ended December 31, 2019 and 2018", fontsize=9)
        page.insert_text((410, 100), "2019", fontsize=9)
        page.insert_text((500, 100), "2018", fontsize=9)
        rows = [("Special commission income", "7,632,624", "6,832,413"),
                ("Special commission expense", "2,079,685", "1,680,971"),
                ("Total operating income", "9,000,000", "8,800,000"),
                ("Total operating expenses", "4,000,000", "3,900,000"),
                ("Net income for the year", "3,021,812", "3,970,659"),
                ("Basic and diluted earnings per share (expressed in SAR)", "2,02", "2,65")]
        for i, (label, cur, prior) in enumerate(rows):
            y = 130 + i * 16
            page.insert_text((50, y), label, fontsize=9)
            _put_right(page, 440, y, cur)
            _put_right(page, 530, y, prior)
        doc.save(path)
        doc.close()

    def test_decimal_comma_eps_is_a_decimal_and_thousands_are_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "eps.pdf"
            self._pdf(pdf)
            facts = _read(pdf, "2019-12-31", 2019, "annual-report")
        got = {f["metric"]: f["value"] for f in facts}
        self.assertEqual(got["eps_diluted"], "2.02")
        self.assertEqual(got["net_income"], "3021812")
        self.assertEqual(got["financing_income"], "7632624")


if __name__ == "__main__":
    unittest.main()
