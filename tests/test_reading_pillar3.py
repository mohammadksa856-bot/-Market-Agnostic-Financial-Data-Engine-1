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

from finengine.verification import ManifestVerifier

_X = (330, 390, 450, 510, 570)
# Column d carries the issuer typo seen in a live SNB disclosure: "31 Mar 2024"
# printed between "31 Dec 2025" and "30 Jun 2025".
_HEADERS = ("30 Jun 2026", "31 Mar 2026", "31 Dec 2025", "31 Mar 2024", "30 Jun 2025")


def _capital_rows(cet1_ratio_a="17.65%"):
    return [
        ("1", "Common Equity Tier 1 (CET1)",
         ("150,000,000", "148,000,000", "146,000,000", "144,000,000", "142,000,000")),
        ("1a", "Fully loaded ECL accounting model CET1",
         ("150,000,000", "148,000,000", "146,000,000", "144,000,000", "142,000,000")),
        ("2", "Tier 1",
         ("170,000,000", "168,000,000", "166,000,000", "164,000,000", "162,000,000")),
        ("3", "Total capital",
         ("180,000,000", "178,000,000", "176,000,000", "174,000,000", "172,000,000")),
        ("4", "Total risk-weighted assets (RWA)",
         ("850,000,000", "840,000,000", "830,000,000", "820,000,000", "810,000,000")),
        ("5", "CET1 ratio (%)", (cet1_ratio_a, "17.62%", "17.59%", "17.56%", "17.53%")),
        ("6", "Tier 1 ratio (%)", ("20.00%", "20.00%", "20.00%", "20.00%", "20.00%")),
        ("7", "Total capital ratio (%)", ("21.18%", "21.19%", "21.20%", "21.22%", "21.23%")),
    ]


def _liquidity_rows():
    return [
        ("15", "Total high-quality liquid assets (HQLA)",
         ("200,000,000", "200,000,000", "200,000,000", "200,000,000", "200,000,000")),
        ("16", "Total net cash outflow",
         ("80,000,000", "80,000,000", "80,000,000", "80,000,000", "80,000,000")),
        ("17", "LCR ratio (%)", ("250%", "250%", "250%", "250%", "250%")),
    ]


def _km1_pdf(path: Path, rows, *, unit="SAR '000", headers=_HEADERS) -> None:
    doc = pymupdf.open()
    cover = doc.new_page(width=640, height=842)
    cover.insert_text((50, 80), "Table of contents - Key metrics KM1 page 2", fontsize=11)
    page = doc.new_page(width=640, height=842)
    page.insert_text((50, 70), "KM1 - Key metrics (at consolidated group level)", fontsize=11)
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
    doc.save(path)
    doc.close()


class QuarterHeaderTests(unittest.TestCase):
    def test_issuer_header_variants_parse_to_quarter_ends(self):
        from finengine.reading_pillar3 import _quarter_end

        self.assertEqual(_quarter_end("30 Jun 2026"), date(2026, 6, 30))
        self.assertEqual(_quarter_end("a Dec-25"), date(2025, 12, 31))
        self.assertEqual(_quarter_end("Dec'20"), date(2020, 12, 31))
        self.assertEqual(_quarter_end("30 June 2025"), date(2025, 6, 30))

    def test_calendar_quarter_headers_used_by_earlier_filings(self):
        from finengine.reading_pillar3 import _quarter_end

        self.assertEqual(_quarter_end("group level) Q1 2023"), date(2023, 3, 31))
        self.assertEqual(_quarter_end("4Q 2022"), date(2022, 12, 31))
        self.assertIsNone(_quarter_end("Q5 2022"))

    def test_month_first_headers_and_riyal_abbreviation_units(self):
        # SAIB prints "T-1 ... December 31, 2025"; Riyad Bank and SAIB declare "SR 000".
        from finengine.reading_pillar3 import Pillar3KeyMetricsReader, _quarter_end

        self.assertEqual(_quarter_end("T-1 December 31, 2025"), date(2025, 12, 31))
        self.assertEqual(_quarter_end("March 31 2026"), date(2026, 3, 31))
        self.assertIsNone(_quarter_end("March 30, 2026"))
        self.assertEqual(Pillar3KeyMetricsReader._scale("Basel III Pillar III\nSR 000's"), 1000)
        self.assertEqual(Pillar3KeyMetricsReader._scale("SR 000\na b c d e"), 1000)
        self.assertEqual(Pillar3KeyMetricsReader._scale("SR mn"), 1_000_000)

    def test_abbreviated_month_with_short_year_after_a_space(self):
        # Riyad Bank's 2018-2022 KM1 columns print "T Mar 18" / "Dec 19".
        from finengine.reading_pillar3 import Pillar3KeyMetricsReader, _quarter_end

        self.assertEqual(_quarter_end("a T Mar 18"), date(2018, 3, 31))
        self.assertEqual(_quarter_end("b Dec 19"), date(2019, 12, 31))
        self.assertEqual(_quarter_end("b T-1 Dec 17"), date(2017, 12, 31))
        self.assertEqual(_quarter_end("e T-4 Mar 17"), date(2017, 3, 31))
        self.assertEqual(_quarter_end("Mar 31, 2026"), date(2026, 3, 31))
        self.assertIsNone(_quarter_end("December 30"))
        self.assertIsNone(_quarter_end("Apr 25"))
        self.assertEqual(Pillar3KeyMetricsReader._scale("a b c\nSAR (000)\n31-Mar-22"), 1000)

    def test_wrapped_row_caption_keeps_the_figures_on_its_continuation_line(self):
        from finengine.reading_pillar3 import _ROW_ID

        self.assertTrue(_ROW_ID.match("1a"))

    def test_malformed_or_non_quarter_headers_are_not_dated(self):
        from finengine.reading_pillar3 import _quarter_end

        self.assertIsNone(_quarter_end("30 Jun 205"))   # printed year truncated
        self.assertIsNone(_quarter_end("30 Apr 2025"))  # not a quarter end
        self.assertIsNone(_quarter_end("30 Mar 2025"))  # wrong month-end day
        self.assertIsNone(_quarter_end("SAR '000"))


@unittest.skipUnless(HAVE_PYMUPDF, "Pillar 3 reader needs the optional pymupdf extra")
class Pillar3KeyMetricsReaderTests(unittest.TestCase):
    def _read(self, directory: Path, rows, **kwargs):
        from finengine.reading_pillar3 import Pillar3KeyMetricsReader

        pdf = directory / "pillar3.pdf"
        _km1_pdf(pdf, rows, **kwargs)
        return Pillar3KeyMetricsReader(pdf).read(
            market="SA", symbol="1180", currency="SAR",
            source_url="https://bank.example/pillar-3-q2-2026.pdf", filed_at="2026-08-20")

    def test_publishes_reconciled_columns_and_excludes_the_typo_column(self):
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), _capital_rows())
        self.assertEqual(manifest["filing_type"], "regulatory-disclosure")
        self.assertEqual(manifest["period_end"], "2026-06-30")
        periods = sorted({fact["period_end"] for fact in manifest["facts"]})
        self.assertEqual(periods, ["2025-06-30", "2025-12-31", "2026-03-31", "2026-06-30"])
        [column] = manifest["excluded_columns"]
        self.assertEqual(column["cell"], "d")
        self.assertEqual(column["reason"], "period_header_inconsistent")
        self.assertEqual(column["parsed_period_end"], "2024-03-31")

        by = {(fact["metric"], fact["period_end"]): fact for fact in manifest["facts"]}
        capital = by[("regulatory_capital", "2026-06-30")]
        self.assertEqual((capital["value"], capital["scale"], capital["unit"]),
                         ("180000000", "1000", "SAR"))
        self.assertEqual((capital["table"], capital["row"], capital["cell"]), ("KM1", "3", "a"))
        self.assertEqual(by[("risk_weighted_assets", "2025-06-30")]["value"], "810000000")
        ratio = by[("cet1_ratio", "2026-06-30")]
        self.assertEqual((ratio["value"], ratio["unit"], ratio["currency"]), ("0.1765", "ratio", ""))
        self.assertEqual(by[("tier1_capital_ratio", "2025-12-31")]["value"], "0.2")
        self.assertNotIn("capital_adequacy_ratio", {fact["metric"] for fact in manifest["facts"]})

    def test_amounts_without_catalog_fields_are_kept_as_excluded_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), _capital_rows() + _liquidity_rows())
        reasons = {(fact["metric"], fact["reason"]) for fact in manifest["excluded_facts"]
                   if fact["period_end"] == "2026-06-30"}
        self.assertIn(("cet1_capital", "catalog_field_missing"), reasons)
        self.assertIn(("tier1_capital", "catalog_field_missing"), reasons)
        self.assertIn(("liquidity_coverage_ratio", "catalog_field_missing"), reasons)
        self.assertIn(("total_capital_ratio", "engine_calculates_metric"), reasons)
        lcr = [check for check in manifest["checks"]
               if check["check"].startswith("liquidity_coverage_ratio")
               and check["period_end"] == "2026-06-30"]
        self.assertEqual(lcr[0]["status"], "pass")

    def test_column_whose_printed_ratio_does_not_reconcile_is_not_published(self):
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), _capital_rows(cet1_ratio_a="18.65%"))
        self.assertNotIn("2026-06-30", {fact["period_end"] for fact in manifest["facts"]})
        rejected = {fact["reason"] for fact in manifest["excluded_facts"]
                    if fact["period_end"] == "2026-06-30"}
        self.assertEqual(rejected, {"reported_ratio_does_not_reconcile"})
        self.assertIn("2026-03-31", {fact["period_end"] for fact in manifest["facts"]})

    def test_undeclared_unit_is_an_error_not_an_assumption(self):
        from finengine.reading_pillar3 import Pillar3ReadError

        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(Pillar3ReadError) as raised:
                self._read(Path(name), _capital_rows(), unit="")
        self.assertEqual(raised.exception.code, "unit_not_declared")

    def test_alternate_thousands_declaration_is_recognized(self):
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), _capital_rows(), unit="(Figures in SAR 000's)")
        self.assertEqual({fact["scale"] for fact in manifest["facts"] if fact["unit"] == "SAR"},
                         {"1000"})

    def test_ifrs9_qualified_row_labels_and_short_year_headers(self):
        # SAIB's KM1 qualifies rows 1-3 "(excluding IFRS 9 Adjustment)" and row 4
        # "(RWA)-Pillar 1"; Riyad Bank's older KM1 dates columns "Jun 26".
        labels = {
            "1": "Common Equity Tier 1 (CET1) (excluding IFRS 9 Adjustment)",
            "2": "Tier 1 (excluding IFRS 9 Adjustment)",
            "3": "Total capital (Tier I+Tier II) (excluding IFRS 9 Adjustment)",
            "4": "Total risk-weighted assets (RWA)-Pillar 1",
        }
        self._assert_qualified_labels_publish(labels)

    def test_ifrs9_transitional_row_labels(self):
        # Alinma prints "(after transitional arrangement for IFRS 9)", "(CET 1)"
        # with a space, and "(RWA)-Pillar - 1".
        labels = {
            "1": "Common Equity Tier 1 (CET 1) (after transitional arrangement for IFRS 9)",
            "2": "Tier 1 (after transitional arrangement for IFRS 9)",
            "3": "Total Capital (after transitional arrangement for IFRS 9)",
            "4": "Total risk-weighted assets (RWA)-Pillar - 1",
        }
        self._assert_qualified_labels_publish(labels)

    def _assert_qualified_labels_publish(self, labels):
        rows = [(row_id, labels.get(row_id, label), values)
                for row_id, label, values in _capital_rows()]
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), rows, unit="SAR (000)",
                                  headers=("Jun 26", "Mar 26", "Dec 25", "Sep 25", "Jun 25"))
        periods = sorted({fact["period_end"] for fact in manifest["facts"]})
        self.assertEqual(periods, ["2025-06-30", "2025-09-30", "2025-12-31",
                                   "2026-03-31", "2026-06-30"])
        by = {(fact["metric"], fact["period_end"]): fact for fact in manifest["facts"]}
        self.assertEqual(by[("regulatory_capital", "2025-09-30")]["value"], "174000000")
        self.assertEqual(by[("risk_weighted_assets", "2026-06-30")]["scale"], "1000")

    def test_row_caption_wrapped_onto_the_line_that_carries_the_figures(self):
        # Alinma prints "1 Common Equity Tier 1 (CET 1)" on one line and
        # "(after transitional arrangement for IFRS 9)  27,069,537 ..." on the
        # next, so the figures belong to the continuation line.
        rows = []
        for row_id, label, values in _capital_rows():
            if row_id in {"1", "2", "3"}:
                rows.append((row_id, label, ("", "", "", "", "")))
                rows.append(("", "(after transitional arrangement for IFRS 9)", values))
            else:
                rows.append((row_id, label, values))
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name), rows)
        by = {(fact["metric"], fact["period_end"]): fact for fact in manifest["facts"]}
        self.assertEqual(by[("regulatory_capital", "2026-06-30")]["value"], "180000000")
        self.assertEqual(by[("risk_weighted_assets", "2026-06-30")]["value"], "850000000")

    def test_manifest_passes_the_accounting_verifier(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            manifest = self._read(directory, _capital_rows())
            imports = directory / "imports"
            imports.mkdir()
            (imports / "snb-pillar3-2026-q2.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
        self.assertTrue(report["ok"], report["detail"])
        self.assertEqual(report["unmapped_labels"], [])


if __name__ == "__main__":
    unittest.main()
