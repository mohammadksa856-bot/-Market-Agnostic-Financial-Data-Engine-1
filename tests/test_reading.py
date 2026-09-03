import json
import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False

from finengine.verification import ManifestVerifier


def _statement_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    def row(y, label, current, prior):
        page.insert_text((60, y), label, fontsize=9)
        page.insert_text((360, y), current, fontsize=9)
        page.insert_text((460, y), prior, fontsize=9)

    page.insert_text((60, 60), "Consolidated Statement of Financial Position", fontsize=13)
    page.insert_text((360, 90), "2025", fontsize=9)
    page.insert_text((460, 90), "2024", fontsize=9)
    page.insert_text((360, 102), "SAR '000", fontsize=8)
    rows = [
        ("Property, Plant and Equipment", "800,000", "760,000"),
        ("Total Non-Current Assets", "900,000", "850,000"),
        ("Inventories", "120,000", "110,000"),
        ("Cash and Cash Equivalents", "80,000", "70,000"),
        ("Total Current Assets", "300,000", "280,000"),
        ("TOTAL ASSETS", "1,200,000", "1,130,000"),
        ("Share Capital", "500,000", "500,000"),
        ("Retained Earnings", "250,000", "180,000"),
        ("TOTAL EQUITY", "750,000", "680,000"),
        ("Total Non-Current Liabilities", "300,000", "310,000"),
        ("Total Current Liabilities", "150,000", "140,000"),
        ("TOTAL LIABILITIES", "450,000", "450,000"),
        ("TOTAL EQUITY AND LIABILITIES", "1,200,000", "1,130,000"),
    ]
    for i, (label, current, prior) in enumerate(rows):
        row(140 + i * 20, label, current, prior)
    doc.save(path)
    doc.close()


@unittest.skipUnless(HAVE_PYMUPDF, "reader needs the optional pymupdf extra")
class StatementReaderTests(unittest.TestCase):
    def test_reads_a_balance_sheet_and_verify_accepts_it(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            pdf = directory / "acme-2025.pdf"
            _statement_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/acme-2025.pdf",
                filed_at="2026-03-01", period_end="2025-12-31", fiscal_year=2025)

            metrics = {f["metric"]: f for f in manifest["facts"]}
            self.assertEqual(metrics["total_assets"]["value"], "1200000")
            self.assertEqual(metrics["total_assets"]["scale"], "1000")   # SAR '000
            self.assertIn("total_equity", metrics)
            self.assertIn("total_liabilities", metrics)
            self.assertEqual(metrics["cash"]["value"], "80000")

            imports = directory / "imports"
            imports.mkdir()
            (imports / "acme-2025-fy.json").write_text(
                json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
            self.assertTrue(report["ok"], report["detail"])
            self.assertTrue(any(
                c["check"].startswith("balance_sheet: assets = liabilities + equity")
                and c["status"] == "pass" for c in report["detail"]))

    def test_picks_the_current_year_column_not_the_prior_year(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _statement_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/x.pdf", filed_at="2026-03-01",
                period_end="2025-12-31", fiscal_year=2025)
            metrics = {f["metric"]: f["value"] for f in manifest["facts"]}
            self.assertEqual(metrics["total_equity"], "750000")   # 2025, not 680,000


if __name__ == "__main__":
    unittest.main()
