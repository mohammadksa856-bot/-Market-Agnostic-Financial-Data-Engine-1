"""Acceptance tests for the Saudi banking company-profile pilot batch 1.

Covers Al Rajhi Bank (1120): qualitative company profile, executive
management team, operating segments, banking operational KPIs, and risk
factors, transcribed from the bank's own Integrated Annual Report 2025
(sourced from its official Investor Relations page). This batch is
additive to the already-merged financial-statement manifests
(alrajhi-2025-fy.json, alrajhi-supplement.json) and adds no numeric
accounting identity of its own -- instead it is cross-checked against
those already-verified financial statements (segment totals must sum to
the audited consolidated total).

Engine/catalog change in this batch (separate commit): 5 new catalog
fields (executive_management_team, board_of_directors, index_memberships,
3 short_interest fields, 2 forward-calendar fields) and a new
banking_operations sub-group under the Banks industry pack.
"""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.bootstrap import rebuild_snapshot
from finengine.query import FinancialQueryService

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_IMPORTS = REPO_ROOT / "data" / "imports"


class BankingProfilesBatch1ManifestTests(unittest.TestCase):
    def test_manifest_is_well_formed(self):
        path = REPO_IMPORTS / "alrajhi-company-profile-2025.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["company_id"], "sa:1120")
        self.assertGreaterEqual(len(data["company_attributes"]), 15)
        self.assertGreaterEqual(len(data["facts"]), 25)
        self.assertGreaterEqual(len(data["disclosures"]), 2)
        # Every company_attribute and fact must carry a page citation
        # somewhere traceable -- the manifest keeps these in `notes`
        # rather than per-fact (matching this repo's existing pattern for
        # company_attributes-only manifests), so just check the notes
        # field documents pages for the categories this batch adds.
        for marker in ("p.11", "p.25", "p.30", "p.224", "p.370-372", "p.264"):
            self.assertIn(marker, data["notes"])


class BankingProfilesBatch1SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "banking_profiles1.sqlite3")
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

    def test_profile_manifest_publishes_without_errors(self):
        rows = [r for r in self.summary["results"]
                if r["manifest"] == "alrajhi-company-profile-2025.json"]
        self.assertTrue(rows)
        row = rows[0]
        self.assertEqual(row["status"], "published", row)
        self.assertEqual(row["domains"]["company_attributes"]["inserted"], 20)
        self.assertEqual(row["domains"]["company_attributes"]["duplicate"], 0)
        self.assertEqual(row["domains"]["disclosures"]["inserted"], 3)

    def test_segment_assets_sum_to_audited_total_assets(self):
        """Cross-check against the independently-sourced, already-verified
        financial-statement manifest: the four reported segments' total
        assets must sum exactly to the audited consolidated total_assets
        for FY2025 -- this is the real integrity test for this batch,
        since qualitative/segment facts have no accounting identity of
        their own to verify against."""
        q = FinancialQueryService(self.dbpath)
        try:
            segment_sum = sum(
                Decimal(row["value"])
                for row in q.metric_history("SA", "1120", "segment_assets")
                if row["period_end"] == "2025-12-31"
            )
            total = _v(q.metric_history("SA", "1120", "total_assets"), "2025-12-31")
        finally:
            q.close()
        self.assertEqual(segment_sum, total)

    def test_executive_and_governance_attributes_present(self):
        q = FinancialQueryService(self.dbpath)
        try:
            attrs = q.attributes("SA", "1120")
        finally:
            q.close()
        self.assertEqual(attrs["ceo_name"]["value"], "Waleed Abdullah Al-Mogbel")
        self.assertEqual(attrs["chairman_name"]["value"], "Abdullah bin Sulaiman Al Rajhi")
        team = attrs["executive_management_team"]["value"]
        self.assertEqual(len(team), 15)
        self.assertTrue(all({"role", "name"} <= set(member) for member in team))

    def test_risk_factor_disclosures_present(self):
        q = FinancialQueryService(self.dbpath)
        try:
            risks = q.disclosures("SA", "1120", disclosure_type="risk_factor")
        finally:
            q.close()
        self.assertEqual(len(risks), 2)
        self.assertIn("Credit Risk", risks[1]["body_text"] if "Credit" in risks[1]["body_text"] else risks[0]["body_text"])


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
