"""Acceptance tests for the Al Rajhi Bank (1120) news pilot -- the sixth
and final data category from the original 6-category scope for this
banking company-profile batch.

First real application of the project's two-tier news sourcing policy:
Tier 1 'official_announcement' (Tadawul's own issuer-announcements feed,
same trust level as a financial disclosure) and Tier 2 'press_coverage'
(named third-party outlets only, each carrying its own source name/URL/
date, never displayed as a bare engine-verified fact).

News items are domain-only (no numeric facts), so they go through
finengine's disclosures table directly rather than the fact-extraction
pipeline -- confirmed here via a snapshot rebuild.
"""

import json
import tempfile
import unittest
from pathlib import Path

from finengine.bootstrap import rebuild_snapshot
from finengine.query import FinancialQueryService

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_IMPORTS = REPO_ROOT / "data" / "imports"


class BankingNewsBatch1ManifestTests(unittest.TestCase):
    def test_manifest_has_both_tiers(self):
        path = REPO_IMPORTS / "alrajhi-news-2026-09.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        tiers = [d["metadata"]["tier"] for d in data["disclosures"]]
        self.assertEqual(tiers.count(1), 5)
        self.assertEqual(tiers.count(2), 2)
        # Every Tier 2 item must carry a source_name and source_url so the
        # site can attribute it to its publisher rather than presenting it
        # as an engine-verified fact.
        for item in data["disclosures"]:
            if item["metadata"]["tier"] == 2:
                self.assertIn("source_name", item["metadata"])
                self.assertIn("source_url", item["metadata"])
                self.assertIn("display_rule", item["metadata"])


class BankingNewsBatch1SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "banking_news1.sqlite3")
        cls.summary = rebuild_snapshot(
            cls.dbpath,
            imports_dir=REPO_IMPORTS,
            registry_path=REPO_ROOT / "config" / "companies.json",
            raw_dir=REPO_ROOT / "data" / "raw",
            replace=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_news_manifest_publishes_all_seven_disclosures(self):
        rows = [r for r in self.summary["results"]
                if r["manifest"] == "alrajhi-news-2026-09.json"]
        self.assertTrue(rows)
        row = rows[0]
        self.assertEqual(row["status"], "published", row)
        self.assertEqual(row["domains"]["disclosures"]["inserted"], 7)

    def test_official_announcements_and_press_coverage_both_queryable(self):
        q = FinancialQueryService(self.dbpath)
        try:
            official = q.disclosures("SA", "1120", disclosure_type="official_announcement")
            press = q.disclosures("SA", "1120", disclosure_type="press_coverage")
        finally:
            q.close()
        self.assertEqual(len(official), 5)
        self.assertEqual(len(press), 2)
        for item in press:
            self.assertIn("source_name", item["metadata"])


if __name__ == "__main__":
    unittest.main()
