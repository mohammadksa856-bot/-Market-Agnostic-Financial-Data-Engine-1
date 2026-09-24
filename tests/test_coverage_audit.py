from __future__ import annotations

"""Generic proof that the Gap 3 raw-archive coverage audit classifies every
archived document into exactly one of the nine categories, deduplicates by
SHA-256 (not raw file count), never treats a presentation/webcast as a
financial statement, and never treats an unlinked market-price history
(archived under a market/ directory) as a financial-statement extraction gap.
"""

import tempfile
import unittest
from pathlib import Path

from finengine.coverage_audit import (
    CLASSIFICATIONS,
    classify_company_artifacts,
    summarize,
)
from finengine.database import Database
from finengine.models import Company, Market, SourceDocument


class CoverageAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.docs_dir = self.root / "data" / "raw" / "SA" / "TST" / "documents"
        self.docs_dir.mkdir(parents=True)
        self.market_dir = self.root / "data" / "raw" / "SA" / "TST" / "market"
        self.market_dir.mkdir(parents=True)
        self.db = Database(str(self.root / "audit.sqlite3"))
        self.company = Company("sa:TST", Market.SA, "TST", "Test Co", "SAR")
        self.db.register_company(self.company)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def _write(self, name: str, content: bytes, directory: Path | None = None) -> tuple[str, str]:
        path = (directory or self.docs_dir) / name
        path.write_bytes(content)
        import hashlib
        digest = hashlib.sha256(content).hexdigest()
        rel_path = str(path.relative_to(self.root))
        return digest, rel_path

    def _artifact(self, artifact_key, content_hash, local_path, source_url,
                  content_type="application/pdf", metadata=None):
        # Mirrors the production path (archive.py -> Database.save_source_artifact):
        # links to source_documents by matching company_id + source_url.
        self.db.save_source_artifact(
            artifact_key, self.company.company_id, source_url, content_hash,
            local_path, content_type, 100, metadata or {},
        )

    def test_classifies_all_nine_categories(self):
        # 1. manifested_and_published
        published_hash, published_path = self._write("published.pdf", b"published financial statements")
        self.db.save_source(
            SourceDocument(self.company.company_id, Market.SA, "https://issuer.test/published.pdf",
                           "source:published", "financial-statements", "2025-01-01", b""),
            published_hash, published_path,
        )
        self.db.set_source_status("source:published", "published")
        self._artifact("artifact:published", published_hash, published_path,
                       "https://issuer.test/published.pdf")

        # 2. manifested_review_required
        review_hash, review_path = self._write("review.pdf", b"needs review financial statements")
        self.db.save_source(
            SourceDocument(self.company.company_id, Market.SA, "https://issuer.test/review.pdf",
                           "source:review", "financial-statements", "2025-01-01", b""),
            review_hash, review_path,
        )
        self._artifact("artifact:review", review_hash, review_path, "https://issuer.test/review.pdf")

        # 3. duplicate_or_language_equivalent (byte-identical Arabic copy)
        dup_hash, dup_path = self._write("published-ar.pdf", b"published financial statements")
        self._artifact("artifact:published-ar", dup_hash, dup_path,
                       "https://issuer.test/published-ar.pdf")

        # 4. context_only_nonfinancial
        deck_hash, deck_path = self._write("deck.pdf", b"investor presentation slides")
        self._artifact("artifact:deck", deck_hash, deck_path,
                       "https://issuer.test/q3-investor-presentation.pdf")

        # 5. unsupported_format
        img_hash, img_path = self._write("scan.png", b"a scanned image nobody can read")
        self._artifact("artifact:scan", img_hash, img_path,
                       "https://issuer.test/scan.png", content_type="image/png")

        # 6. missing_manifest
        gap_hash, gap_path = self._write("unextracted.pdf", b"a real filing nobody extracted yet")
        self._artifact("artifact:gap", gap_hash, gap_path, "https://issuer.test/unextracted.pdf")

        # 7. missing_binary
        self._artifact("artifact:missing", "deadbeef" * 8,
                       str(Path("data/raw/SA/TST/documents/ghost.pdf")),
                       "https://issuer.test/ghost.pdf")

        # 8. hash_mismatch
        _, mismatch_path = self._write("tampered.pdf", b"the real bytes on disk")
        self._artifact("artifact:tampered", "0" * 64, mismatch_path,
                       "https://issuer.test/tampered.pdf")

        # 9. market_data (an unlinked daily price/volume history, archived
        # under a market/ directory - never a financial-statement gap)
        price_hash, price_path = self._write(
            "prices.csv", b"date,close,volume\n2025-01-01,10.0,1000\n", directory=self.market_dir,
        )
        self._artifact("artifact:prices", price_hash, price_path,
                       "https://exchange.test/historical-reports", content_type="text/csv")

        records = classify_company_artifacts(self.db, self.company.company_id, str(self.root))
        by_key = {r["artifact_key"]: r["classification"] for r in records}

        self.assertEqual(by_key["artifact:published"], "manifested_and_published")
        self.assertEqual(by_key["artifact:review"], "manifested_review_required")
        self.assertEqual(by_key["artifact:published-ar"], "duplicate_or_language_equivalent")
        self.assertEqual(by_key["artifact:deck"], "context_only_nonfinancial")
        self.assertEqual(by_key["artifact:scan"], "unsupported_format")
        self.assertEqual(by_key["artifact:gap"], "missing_manifest")
        self.assertEqual(by_key["artifact:missing"], "missing_binary")
        self.assertEqual(by_key["artifact:tampered"], "hash_mismatch")
        self.assertEqual(by_key["artifact:prices"], "market_data")

        summary = summarize(records)
        self.assertEqual(summary["total_raw_artifacts"], 9)
        # unique_documents excludes the duplicate language copy.
        self.assertEqual(summary["unique_documents"], 8)
        for key in CLASSIFICATIONS:
            self.assertIn(key, summary)

    def test_market_data_still_manifested_when_already_linked(self):
        """A market-history CSV that IS linked to a published source (e.g.
        Aramco's, via a dedicated market-prices import) keeps reporting as
        manifested_and_published - the market/ directory only reclassifies
        an *unlinked* file away from missing_manifest, it never hides a real
        publication."""
        price_hash, price_path = self._write(
            "prices.csv", b"date,close,volume\n2025-01-01,10.0,1000\n", directory=self.market_dir,
        )
        self.db.save_source(
            SourceDocument(self.company.company_id, Market.SA, "https://exchange.test/historical-reports",
                           "source:prices", "market-data", "2025-01-01", b""),
            price_hash, price_path,
        )
        self.db.set_source_status("source:prices", "published")
        self._artifact("artifact:prices", price_hash, price_path,
                       "https://exchange.test/historical-reports", content_type="text/csv")
        records = classify_company_artifacts(self.db, self.company.company_id, str(self.root))
        self.assertEqual(records[0]["classification"], "manifested_and_published")

    def test_raw_file_count_is_not_treated_as_coverage(self):
        """Two byte-identical files (e.g. an EN/AR pair) must count as one
        unique document, proving count != coverage."""
        h1, p1 = self._write("en.pdf", b"identical bytes")
        h2, p2 = self._write("ar.pdf", b"identical bytes")
        self.assertEqual(h1, h2)
        self._artifact("artifact:en", h1, p1, "https://issuer.test/en.pdf")
        self._artifact("artifact:ar", h2, p2, "https://issuer.test/ar.pdf")
        records = classify_company_artifacts(self.db, self.company.company_id, str(self.root))
        summary = summarize(records)
        self.assertEqual(summary["total_raw_artifacts"], 2)
        self.assertEqual(summary["unique_documents"], 1)
        self.assertEqual(summary["duplicate_or_language_equivalent"], 1)

    def test_never_reclassifies_a_presentation_as_missing_manifest(self):
        """Generic guard: any nonfinancial keyword in the URL routes to
        context_only_nonfinancial, never missing_manifest, regardless of
        company - so it is never forced through the financial-statement
        reader downstream."""
        h, p = self._write("webcast.pdf", b"earnings call webcast transcript")
        self._artifact("artifact:webcast", h, p, "https://issuer.test/q4-earnings-webcast-transcript.pdf")
        records = classify_company_artifacts(self.db, self.company.company_id, str(self.root))
        self.assertEqual(records[0]["classification"], "context_only_nonfinancial")


if __name__ == "__main__":
    unittest.main()
