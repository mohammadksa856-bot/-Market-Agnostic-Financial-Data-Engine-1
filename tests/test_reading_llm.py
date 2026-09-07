import json
import tempfile
import types
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False

from finengine.verification import ManifestVerifier


def _two_statement_pdf(path: Path) -> None:
    doc = pymupdf.open()
    bs = doc.new_page(width=595, height=842)
    bs.insert_text((60, 60), "Consolidated Statement of Financial Position", fontsize=13)
    bs.insert_text((360, 90), "2025", fontsize=9)
    bs.insert_text((60, 100), "SAR '000", fontsize=8)
    for i, (label, value) in enumerate([
        ("TOTAL ASSETS", "1,200,000"), ("TOTAL EQUITY", "750,000"),
        ("TOTAL LIABILITIES", "450,000"),
    ]):
        bs.insert_text((60, 150 + i * 20), label, fontsize=9)
        bs.insert_text((360, 150 + i * 20), value, fontsize=9)

    pl = doc.new_page(width=595, height=842)
    pl.insert_text((60, 60), "Consolidated Statement of Profit or Loss", fontsize=13)
    pl.insert_text((360, 90), "2025", fontsize=9)
    for i, (label, value) in enumerate([("Revenue", "900,000"), ("Profit for the year", "180,000")]):
        pl.insert_text((60, 150 + i * 20), label, fontsize=9)
        pl.insert_text((360, 150 + i * 20), value, fontsize=9)
    doc.save(path)
    doc.close()


def _fake_client(facts):
    class Messages:
        def create(self, **kwargs):
            self.request = kwargs
            text = json.dumps({"reporting_scale": "1000", "facts": facts})
            return types.SimpleNamespace(
                content=[types.SimpleNamespace(type="text", text=text)],
                usage=types.SimpleNamespace(input_tokens=4000, output_tokens=300))
    return types.SimpleNamespace(messages=Messages())


def _fake_vision_client(facts):
    return _fake_client(facts)


def _scanned_statement_pdf(path: Path) -> None:
    """A digital heading page followed by an image-only 'scanned' statement page."""
    doc = pymupdf.open()
    head = doc.new_page(width=595, height=842)
    head.insert_text((60, 60), "Consolidated Statement of Financial Position", fontsize=13)
    head.insert_text((60, 80), "As at 31 December 2025", fontsize=9)

    rendered = pymupdf.open()
    body = rendered.new_page(width=595, height=842)
    body.insert_text((60, 60), "TOTAL ASSETS 1,200,000 1,000,000", fontsize=10)
    png = body.get_pixmap(matrix=pymupdf.Matrix(2, 2)).tobytes("png")
    rendered.close()

    scan = doc.new_page(width=595, height=842)
    scan.insert_image(scan.rect, stream=png)
    doc.save(path)
    doc.close()


@unittest.skipUnless(HAVE_PYMUPDF, "needs the optional pymupdf extra")
class LlmReaderTests(unittest.TestCase):
    def test_parses_model_output_into_a_verifiable_manifest(self):
        from finengine.reading_llm import llm_read

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            pdf = directory / "acme.pdf"
            _two_statement_pdf(pdf)
            client = _fake_client([
                {"metric": "total_assets", "source_label": "TOTAL ASSETS",
                 "value": "1,200,000", "period_kind": "instant", "scale": "1000"},
                {"metric": "total_equity", "source_label": "TOTAL EQUITY",
                 "value": "750,000", "period_kind": "instant", "scale": "1000"},
                {"metric": "total_liabilities", "source_label": "TOTAL LIABILITIES",
                 "value": "450,000", "period_kind": "instant", "scale": "1000"},
                {"metric": "revenue", "source_label": "Revenue",
                 "value": "900,000", "period_kind": "fy", "scale": "1000"},
                {"metric": "net_income", "source_label": "Profit for the year",
                 "value": "180,000", "period_kind": "fy", "scale": "1000"},
            ])
            manifest = llm_read(
                pdf, market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/acme.pdf", filed_at="2026-03-01",
                period_end="2025-12-31", fiscal_year=2025, client=client)

            self.assertEqual(manifest["reader"].split("/")[0], "finengine.reading_llm")
            metrics = {f["metric"]: f for f in manifest["facts"]}
            self.assertEqual(metrics["total_assets"]["value"], "1200000")
            self.assertEqual(metrics["total_assets"]["currency"], "SAR")
            self.assertEqual(metrics["revenue"]["period_start"], "2025-01-01")

            imports = directory / "imports"
            imports.mkdir()
            (imports / "acme-2025-fy.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
            self.assertTrue(report["ok"], report["detail"])

    def test_vision_reader_captures_both_period_columns(self):
        from finengine.reading_llm import llm_read_vision

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            pdf = directory / "scanned.pdf"
            _scanned_statement_pdf(pdf)

            def facts(year, assets, equity, liab):
                return [
                    {"metric": "total_assets", "source_label": "TOTAL ASSETS",
                     "value": assets, "period_kind": "instant", "fiscal_year": year,
                     "period_end": f"{year}-12-31", "scale": "1000", "page": 2},
                    {"metric": "total_equity", "source_label": "TOTAL EQUITY",
                     "value": equity, "period_kind": "instant", "fiscal_year": year,
                     "scale": "1000", "page": 2},
                    {"metric": "total_liabilities", "source_label": "TOTAL LIABILITIES",
                     "value": liab, "period_kind": "instant", "fiscal_year": year,
                     "scale": "1000", "page": 2},
                ]

            client = _fake_vision_client(
                facts(2025, "1,200,000", "750,000", "450,000")
                + facts(2024, "1,000,000", "600,000", "400,000"))

            manifest = llm_read_vision(
                pdf, market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/scanned.pdf", filed_at="2026-03-01",
                fiscal_year=2025, client=client)

            self.assertEqual(manifest["reader"].split("/")[0], "finengine.reading_llm_vision")
            self.assertEqual(manifest["pages_read"], [2])
            years = {f["fiscal_year"] for f in manifest["facts"]}
            self.assertEqual(years, {2024, 2025})
            self.assertTrue(any(msg.get("type") == "image"
                                for msg in client.messages.request["messages"][0]["content"]))

            imports = directory / "imports"
            imports.mkdir()
            (imports / "acme-2025-fy.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
            self.assertEqual(report["failures"], 0, report["detail"])

    def test_vision_reader_normalises_bracketed_negatives(self):
        from finengine.reading_llm import llm_read_vision

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "scanned.pdf"
            _scanned_statement_pdf(pdf)
            client = _fake_vision_client([
                {"metric": "cost_of_revenue", "source_label": "Cost of sales",
                 "value": "(3,648,933)", "period_kind": "fy", "fiscal_year": 2025,
                 "scale": "1000", "page": 2},
            ])
            manifest = llm_read_vision(
                pdf, market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/x.pdf", filed_at="2026-03-01",
                fiscal_year=2025, client=client)
            fact = next(f for f in manifest["facts"] if f["metric"] == "cost_of_revenue")
            self.assertEqual(fact["value"], "-3648933")

    def test_drops_hallucinated_metric_names_and_bad_numbers(self):
        from finengine.reading_llm import llm_read

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _two_statement_pdf(pdf)
            client = _fake_client([
                {"metric": "revenue", "source_label": "Revenue", "value": "900,000",
                 "period_kind": "fy", "scale": "1000"},
                {"metric": "totally_made_up_metric", "source_label": "X",
                 "value": "1", "period_kind": "fy"},
                {"metric": "net_income", "source_label": "Profit", "value": "n/a",
                 "period_kind": "fy", "scale": "1000"},
            ])
            manifest = llm_read(
                pdf, market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/x.pdf", filed_at="2026-03-01",
                period_end="2025-12-31", fiscal_year=2025, client=client)
            metrics = {f["metric"] for f in manifest["facts"]}
            self.assertEqual(metrics, {"revenue"})


if __name__ == "__main__":
    unittest.main()
