"""Insurance-only reader fixes must never change bank/corporate behaviour.

Tawuniya's and Bupa Arabia's interim statements exposed two real reader gaps:

1. A decimal sub-note reference ("5.1", "5.2") sits about 110pt left of the
   value column - further than the 90pt zone the reader uses everywhere
   else, and the old note-reference pattern did not even recognise a decimal
   token as a note reference in the first place. Left unfixed, the token is
   treated as a label word that "looks numeric", and the whole row is
   silently dropped (see `_statement_facts`, the `_NUMBER.match(token) for
   token in text_tokens` guard).

2. A prose sentence ("For the six-month period ended 30 June 2025") above
   the real two-column header prints a lone year close to the header's own
   columns; left unfixed it merges into the header's column block and
   corrupts period-column detection.

Both fixes are gated to `profile == "insurance"` because widening them
globally reopens a regression in ANB's already-merged annual reports, where
a multi-page "commission rate sensitivity" note table gets misread as a
continuation of the balance sheet (see data/imports/anb-2018-annual-report.json
and anb-2019-annual-report.json). Each test below proves the fix fires for
`profile="insurance"` and proves it does NOT fire - i.e. behaviour is
unchanged - for `profile="bank"`, using the exact same page layout.
"""
import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False


def _note_ref_pdf(path: Path) -> None:
    """One income-statement row whose decimal note ref sits 110pt from the
    value column: inside the insurance-only 130pt zone, outside the default
    90pt zone used for every other profile."""
    document = pymupdf.open()
    page = document.new_page(width=640, height=842)
    page.insert_text((40, 50), "STATEMENT OF INCOME", fontsize=11)
    page.insert_text((360, 80), "For the six-month period ended", fontsize=7)
    for x, year in zip((430, 520), ("2025", "2024")):
        page.insert_text((x, 100), f"June 30, {year}", fontsize=8)
    # The year-word column centres land at ~472/562 (offset right of the
    # "June 30, " prefix), so the note ref sits ~112pt left of the column -
    # outside the default 90pt zone but inside the insurance-only 130pt zone.
    page.insert_text((40, 140), "Insurance revenue", fontsize=9)
    page.insert_text((355, 140), "5.1", fontsize=7)
    for x, value in zip((430, 520), ("5,225,943", "4,900,000")):
        page.insert_text((x, 140), value, fontsize=9)
    # A second signature line ("revenue" + "net profit for the") is required
    # for the page to be recognised as an income statement at all.
    page.insert_text((40, 160), "Net profit for the period", fontsize=9)
    for x, value in zip((430, 520), ("467,417", "400,000")):
        page.insert_text((x, 160), value, fontsize=9)
    document.save(path)
    document.close()


def _sentence_year_pdf(path: Path) -> None:
    """A prose sentence prints a lone "2025" close to the real two-column
    header, which - without the insurance-only exclusion - merges into the
    same column block and produces a spurious third column."""
    document = pymupdf.open()
    page = document.new_page(width=640, height=842)
    page.insert_text((40, 50), "STATEMENT OF INCOME", fontsize=11)
    # Lone sentence year, close (within 30pt) to the header's first column.
    page.insert_text((40, 75), "For the six-month period ended 30 June", fontsize=7)
    page.insert_text((410, 75), "2025", fontsize=7)
    # Real two-column comparative header, siblings on the same line.
    for x, year in zip((430, 520), ("2025", "2024")):
        page.insert_text((x, 100), f"June 30, {year}", fontsize=8)
    page.insert_text((40, 140), "Insurance revenue", fontsize=9)
    for x, value in zip((430, 520), ("5,225,943", "4,900,000")):
        page.insert_text((x, 140), value, fontsize=9)
    page.insert_text((40, 160), "Net profit for the period", fontsize=9)
    for x, value in zip((430, 520), ("467,417", "400,000")):
        page.insert_text((x, 160), value, fontsize=9)
    document.save(path)
    document.close()


@unittest.skipUnless(HAVE_PYMUPDF, "the reader needs the optional pymupdf extra")
class InsuranceOnlyNoteZoneWidthTests(unittest.TestCase):
    def _read(self, directory: Path, profile: str):
        from finengine.reading import StatementReader

        pdf = directory / "note-ref.pdf"
        _note_ref_pdf(pdf)
        return StatementReader(pdf, enable_ocr=False).read(
            market="SA", symbol="8010" if profile == "insurance" else "1140",
            currency="SAR", source_url="https://issuer.example/note-ref.pdf",
            filed_at="2025-08-01", period_end="2025-06-30", fiscal_year=2025,
            filing_type="interim-report", profile=profile)

    def test_insurance_profile_reads_the_row_past_the_decimal_note_ref(self):
        # The page text ("six-month period ended") makes this a YTD period,
        # not an FY one - the reader classifies period kind from the header
        # text zone regardless of which profile is reading the page.
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), "insurance")
        values = {(f["metric"], f["period_kind"]): f["value"] for f in manifest["facts"]}
        self.assertEqual(values.get(("insurance_revenue", "ytd")), "5225943")

    def test_bank_profile_is_unaffected_same_layout_row_still_dropped(self):
        # Proves the widened zone is scoped to profile == "insurance": with
        # the identical layout, a bank/corporate document keeps the original,
        # narrower 90pt zone and the note ref is still ~112pt away - outside
        # it - so the row is (as before this change) not published.
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), "bank")
        values = {(f["metric"], f["period_kind"]): f["value"] for f in manifest["facts"]}
        self.assertNotIn(("insurance_revenue", "ytd"), values)
        self.assertNotIn(("insurance_revenue", "fy"), values)


@unittest.skipUnless(HAVE_PYMUPDF, "the reader needs the optional pymupdf extra")
class InsuranceOnlySentenceYearExclusionTests(unittest.TestCase):
    def _read(self, directory: Path, profile: str):
        from finengine.reading import StatementReader

        pdf = directory / "sentence-year.pdf"
        _sentence_year_pdf(pdf)
        return StatementReader(pdf, enable_ocr=False).read(
            market="SA", symbol="8010" if profile == "insurance" else "1140",
            currency="SAR", source_url="https://issuer.example/sentence-year.pdf",
            filed_at="2025-08-01", period_end="2025-06-30", fiscal_year=2025,
            filing_type="interim-report", profile=profile)

    def test_insurance_profile_drops_the_lone_sentence_year_from_columns(self):
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), "insurance")
        values = {(f["metric"], f["period_kind"]): f["value"] for f in manifest["facts"]}
        self.assertEqual(values.get(("insurance_revenue", "ytd")), "5225943")

    def test_column_blocks_unit_insurance_excludes_lone_year_bank_does_not(self):
        # Direct unit check on _column_blocks: the lone sentence year (center
        # 420.0) sits only 20pt from the real header's first column (center
        # 440.0) - close enough to merge into the same column and shift its
        # detected centre from the true 440.0 down to the sentence's own
        # 420.0. Excluding the lone year (profile="insurance") restores the
        # true header centre; every other profile keeps the pre-existing,
        # unfixed (shifted) behaviour unchanged, bit-for-bit.
        from finengine.reading import StatementReader

        class _FakeRect:
            height = 842

        class _FakePage:
            rect = _FakeRect()

        words = [
            (410, 75, 430, 82, "2025", 0, 0, 0),
            (430, 100, 450, 107, "2025", 0, 1, 0),
            (520, 100, 540, 107, "2024", 0, 1, 1),
        ]
        insurance_blocks = StatementReader._column_blocks(_FakePage(), words, profile="insurance")
        bank_blocks = StatementReader._column_blocks(_FakePage(), words, profile="bank")
        default_blocks = StatementReader._column_blocks(_FakePage(), words)
        self.assertEqual(insurance_blocks, [[440.0, 530.0]])
        self.assertEqual(bank_blocks, [[420.0, 530.0]])
        self.assertEqual(default_blocks, [[420.0, 530.0]])
