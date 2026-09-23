import json, tempfile, unittest
from pathlib import Path

from finengine.database import Database
from finengine.models import Company, Market, SourceDocument
from finengine.pipeline import Pipeline


class FakeConnector:
    """Mirrors the manifest-file connectors: JSON bytes plus a source_key."""
    def __init__(self, payload, key="fixture:disclosure-1"):
        self.content = json.dumps(payload).encode()
        self.key = key

    def fetch(self, company):
        return SourceDocument(
            company.company_id, company.market, "fixture://board-report",
            self.key, "annual-report", "2025-03-01", self.content,
        )


def disclosure_payload(**overrides):
    item = {
        "disclosure_type": "governance",
        "title": "Board composition FY2024",
        "body_text": (
            "The board consists of 11 directors as disclosed on page 42, "
            "Annual Report 2024: \"the Board comprises eleven members, "
            "eight of whom are independent.\""
        ),
        "published_at": "2025-03-01",
        "period_end": "2024-12-31",
        "language": "en",
        "metadata": {"page": 42, "document": "Annual Report 2024"},
    }
    item.update(overrides)
    return {
        "period_end": "2024-12-31", "filed_at": "2025-03-01",
        "disclosures": [item],
    }


class DisclosuresOnlyPublishingTests(unittest.TestCase):
    """Generic pipeline test: a facts-less manifest containing only
    disclosures[] must publish through the real domain-store path, exactly
    like ownership_positions/corporate_actions/market_prices already do for
    the reviewed-manifest bootstrap sync. This is not company-specific: the
    fixture company below is neither Aramco nor Al Rajhi to prove the fix is
    structural, not name-keyed.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = str(Path(self.tmp.name) / "db.sqlite3")
        self.db = Database(self.dbpath)
        self.company = Company("sa:9999", Market.SA, "9999", "Generic Test Co", "SAR")

    def tearDown(self):
        self.db.close(); self.tmp.cleanup()

    def _run(self, payload, key="fixture:disclosure-1"):
        return Pipeline(self.db, Path(self.tmp.name) / "raw").run(
            self.company, FakeConnector(payload, key),
        )

    def test_disclosures_only_manifest_publishes(self):
        result = self._run(disclosure_payload())
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["stage"], "domain_publish")
        self.assertEqual(result["inserted"], 1)

        row = self.db.conn.execute(
            "SELECT disclosure_type,title,body_text,source_key,is_current "
            "FROM disclosures WHERE company_id=?", (self.company.company_id,),
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["disclosure_type"], "governance")
        self.assertEqual(row["source_key"], "fixture:disclosure-1")
        self.assertEqual(row["is_current"], 1)
        self.assertIn("page 42", row["body_text"])

        # The source itself is recorded as published, not stuck under review.
        status = self.db.source_status("fixture:disclosure-1")
        self.assertEqual(status, "published")
        self.assertEqual(
            self.db.conn.execute(
                "SELECT count(*) FROM exceptions WHERE source_key=? AND status='open'",
                ("fixture:disclosure-1",),
            ).fetchone()[0],
            0,
        )

    def test_reprocessing_same_disclosure_is_idempotent_not_duplicated(self):
        self._run(disclosure_payload())
        second = self._run(disclosure_payload(), key="fixture:disclosure-1")
        # Same source_key + unchanged status short-circuits to duplicate at
        # the top of Pipeline._run, exactly as it does for numeric sources.
        self.assertEqual(second["status"], "duplicate")
        count = self.db.conn.execute(
            "SELECT count(*) FROM disclosures WHERE company_id=?",
            (self.company.company_id,),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_restated_disclosure_keeps_prior_version_not_current(self):
        self._run(disclosure_payload(), key="fixture:disclosure-1")
        self._run(
            disclosure_payload(body_text="Restated: the Board comprises twelve members."),
            key="fixture:disclosure-2",
        )
        rows = self.db.conn.execute(
            "SELECT version,is_current FROM disclosures WHERE company_id=? ORDER BY version",
            (self.company.company_id,),
        ).fetchall()
        self.assertEqual([(r["version"], r["is_current"]) for r in rows], [(1, 0), (2, 1)])

    def test_disclosure_missing_required_citation_field_cannot_publish(self):
        payload = disclosure_payload()
        del payload["disclosures"][0]["body_text"]
        with self.assertRaises(KeyError):
            self._run(payload)
        # No half-published/fabricated row is left behind.
        count = self.db.conn.execute(
            "SELECT count(*) FROM disclosures WHERE company_id=?",
            (self.company.company_id,),
        ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_manifest_with_neither_facts_nor_domains_still_goes_to_review(self):
        payload = {"period_end": "2024-12-31", "filed_at": "2025-03-01", "facts": []}
        result = self._run(payload, key="fixture:empty")
        self.assertEqual(result["status"], "exception")
        self.assertEqual(self.db.source_status("fixture:empty"), "review_required")

    def test_manifest_with_facts_and_disclosures_still_uses_numeric_path(self):
        # Facts present -> normal numeric staging/validation governs the
        # outcome; the domain-only shortcut must never bypass it.
        payload = disclosure_payload()
        payload["facts"] = [{
            "metric": "revenue", "value": 1000, "period_start": "2024-01-01",
            "period_end": "2024-12-31", "period_kind": "fy", "fiscal_year": 2024,
        }]
        result = self._run(payload, key="fixture:mixed")
        self.assertEqual(result["status"], "published")
        self.assertNotEqual(result.get("stage"), "domain_publish")
        # The domain-only shortcut is bypassed once facts are present; a
        # manifest cannot smuggle a disclosure through it alongside facts.
        count = self.db.conn.execute(
            "SELECT count(*) FROM disclosures WHERE company_id=?",
            (self.company.company_id,),
        ).fetchone()[0]
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
