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
