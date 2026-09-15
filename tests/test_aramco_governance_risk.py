import json
import unittest
from pathlib import Path

import pymupdf

from finengine.reading_qualitative import _normalize


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "imports" / "aramco-2025-governance-risk.json"
ARCHIVE_INDEX = ROOT / "data" / "raw" / "archive-index.json"
PDF_HASH = "78bb678e8e45f5c58fa1b2402ab5a29c5ad10adfda8ba5e7ee5f4d1ad76cd227"
PDF = ROOT / "data" / "raw" / "SA" / "2222" / "documents" / f"{PDF_HASH}.pdf"


class AramcoGovernanceRiskTests(unittest.TestCase):
    def test_every_declared_quote_is_grounded_on_the_archived_pdf_page(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        document = pymupdf.open(PDF)
        try:
            checked = 0
            for item in manifest["company_attributes"] + manifest["disclosures"]:
                metadata = item.get("metadata", {})
                quote = metadata.get("quote")
                pages = metadata.get("pdf_pages", [])
                page = metadata.get("pdf_page") or (pages[0] if pages else None)
                if not quote:
                    continue
                checked += 1
                self.assertIsNotNone(page, item)
                self.assertIn(
                    _normalize(quote), _normalize(document[page - 1].get_text()),
                    item.get("attribute_key") or item.get("title"),
                )
        finally:
            document.close()
        self.assertGreaterEqual(checked, 25)

    def test_archive_inventory_links_the_reviewed_manifest(self):
        index = json.loads(ARCHIVE_INDEX.read_text(encoding="utf-8"))
        artifact = next(
            item for item in index["artifacts"] if item["content_hash"] == PDF_HASH
        )
        self.assertIn(MANIFEST.name, artifact["metadata"]["manifests"])
        self.assertEqual(artifact["company_id"], "sa:2222")


if __name__ == "__main__":
    unittest.main()
