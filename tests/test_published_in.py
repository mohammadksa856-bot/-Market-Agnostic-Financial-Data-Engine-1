import unittest
from types import SimpleNamespace

from finengine.extraction import JsonExtractor

COMPANY = SimpleNamespace(company_id="sa:TST", currency="SAR")
DOCUMENT = SimpleNamespace(source_key="file:summary", source_url="https://example.test/ar-2025.pdf",
                           filed_at="2026-03-03", filing_type="five-year summary")


def row(**extra):
    return {"metric": "revenue", "value": "141.54", "scale": "1000000000", "period_start": "2023-01-01",
            "period_end": "2023-12-31", "period_kind": "fy", "fiscal_year": 2023, **extra}


class PublishedInTests(unittest.TestCase):
    def test_reproduced_figure_keeps_the_filing_it_came_from(self):
        origin = {"source_url": "https://example.test/fs-2023.pdf", "filed_at": "2024-03-21"}
        facts, errors = JsonExtractor()._sa(COMPANY, DOCUMENT, {"facts": [row(published_in=origin)]})
        self.assertEqual(errors, [])
        self.assertEqual((facts[0].source_url, facts[0].filed_at), (origin["source_url"], origin["filed_at"]))
        self.assertEqual(facts[0].source_key, "file:summary")

    def test_figures_without_it_belong_to_the_document(self):
        facts, _ = JsonExtractor()._sa(COMPANY, DOCUMENT, {"facts": [row()]})
        self.assertEqual((facts[0].source_url, facts[0].filed_at), (DOCUMENT.source_url, DOCUMENT.filed_at))

    def test_incomplete_attribution_is_rejected(self):
        facts, errors = JsonExtractor()._sa(COMPANY, DOCUMENT, {"facts": [row(published_in={"source_url": "x"})]})
        self.assertEqual(facts, [])
        self.assertEqual(errors[0]["code"], "invalid_fact")


if __name__ == "__main__":
    unittest.main()
