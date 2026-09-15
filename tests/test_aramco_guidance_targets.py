import json
import unittest
from pathlib import Path

import pymupdf

from finengine.reading_qualitative import _normalize


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "imports" / "aramco-2025-guidance-targets.json"
ARCHIVE_INDEX = ROOT / "data" / "raw" / "archive-index.json"
PDF_HASH = "78bb678e8e45f5c58fa1b2402ab5a29c5ad10adfda8ba5e7ee5f4d1ad76cd227"
PDF = ROOT / "data" / "raw" / "SA" / "2222" / "documents" / f"{PDF_HASH}.pdf"


class AramcoGuidanceTargetTests(unittest.TestCase):
    def test_guidance_is_issuer_reported_and_not_analyst_consensus(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        guidance = manifest["disclosures"]
        self.assertEqual(len(guidance), 10)
        self.assertTrue(all(item["disclosure_type"] == "guidance" for item in guidance))
        self.assertTrue(all(item["metadata"]["issuer_reported"] for item in guidance))
        self.assertTrue(all(not item["metadata"]["analyst_forecast"] for item in guidance))
        self.assertTrue(all(item["metadata"]["forward_looking"] for item in guidance))

    def test_every_guidance_quote_is_grounded_on_its_archived_pdf_page(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        document = pymupdf.open(PDF)
        try:
            for item in manifest["disclosures"]:
                metadata = item["metadata"]
                self.assertIn(
                    _normalize(metadata["quote"]),
                    _normalize(document[metadata["pdf_page"] - 1].get_text()),
                    item["title"],
                )
        finally:
            document.close()

    def test_archive_inventory_links_the_guidance_manifest(self):
        index = json.loads(ARCHIVE_INDEX.read_text(encoding="utf-8"))
        artifact = next(
            item for item in index["artifacts"] if item["content_hash"] == PDF_HASH
        )
        self.assertIn(MANIFEST.name, artifact["metadata"]["manifests"])

    def test_legacy_dividend_label_is_not_forward_looking_guidance(self):
        annual = json.loads(
            (ROOT / "data" / "imports" / "aramco-2025-annual-metrics.json").read_text(
                encoding="utf-8"
            )
        )
        dividend = next(
            item for item in annual["disclosures"]
            if item["title"] == "Fourth quarter 2025 base dividend"
        )
        self.assertEqual(dividend["disclosure_type"], "guidance")
        self.assertNotEqual(dividend.get("metadata", {}).get("forward_looking"), True)


if __name__ == "__main__":
    unittest.main()
