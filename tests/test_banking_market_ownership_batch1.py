"""Acceptance tests for the Al Rajhi Bank (1120) market price, ownership and
corporate-actions manifest -- the second half of banking company-profile
batch 1, sourced directly from Tadawul's own company-profile page for
symbol 1120 (retrieved 2026-09-11).

Key finding this manifest's tests lock in: after the strong Investor
Relations lesson from this batch (see alrajhi-company-profile-2025.json's
notes on discarding an unverified third-party ownership claim), Tadawul's
own 'Substantial Shareholders' (>=5%) tab returned no rows for Al Rajhi --
i.e. no shareholder currently holds 5% or more. That is asserted here as
a real, sourced fact, not silently dropped.
"""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.bootstrap import rebuild_snapshot
from finengine.query import FinancialQueryService

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_IMPORTS = REPO_ROOT / "data" / "imports"


class BankingMarketOwnershipBatch1SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dbpath = str(Path(cls._tmp.name) / "banking_market1.sqlite3")
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

    def test_market_ownership_manifest_publishes_without_errors(self):
        rows = [r for r in self.summary["results"]
                if r["manifest"] == "alrajhi-market-ownership-2025.json"]
        self.assertTrue(rows)
        row = rows[0]
        self.assertEqual(row["status"], "published", row)
        self.assertEqual(row["domains"]["ownership_positions"]["inserted"], 12)
        self.assertEqual(row["domains"]["corporate_actions"]["inserted"], 10)
        self.assertEqual(row["domains"]["market_prices"]["inserted"], 2)

    def test_market_price_unlocks_automatic_valuation(self):
        """Archiving a dated price is what turns on the whole downstream
        valuation calculation chain (market_cap, P/E, dividend yield,
        enterprise value) -- confirms the engine's is_calculated pipeline
        actually fires for this company now, not just that facts landed."""
        valuations = [m for m in self.summary["market_valuations"]
                      if m["company_id"] == "sa:1120"]
        self.assertTrue(valuations)
        self.assertEqual(valuations[0]["status"], "published")
        self.assertGreater(valuations[0]["published"], 0)

    def test_market_cap_reproduces_quoted_price(self):
        """market_cap = shares_outstanding x price is an internal
        consistency check between two independently-sourced facts on the
        same Tadawul page (Equity Profile's Total Issued Shares vs the
        Peer Comparison tool's own market cap figure)."""
        q = FinancialQueryService(self.dbpath)
        try:
            market_cap = _v(q.metric_history("SA", "1120", "market_cap"), "2026-09-11")
        finally:
            q.close()
        shares = Decimal("6000000000")
        price = Decimal("66.00")
        self.assertEqual(market_cap, shares * price)

    def test_no_substantial_shareholder_disclosed(self):
        """Tadawul's own Substantial Shareholders (>=5%) tab returned no
        rows for Al Rajhi -- confirmed here as a real disclosure, and the
        Chairman's individually-disclosed stake (~2.18%) is the largest
        single holding on record, well under the 5% substantial-holder
        threshold."""
        q = FinancialQueryService(self.dbpath)
        try:
            disclosures = q.disclosures("SA", "1120", disclosure_type="material_event")
        finally:
            q.close()
        titles = [d["title"] for d in disclosures]
        self.assertTrue(any("no holder currently at or above 5%" in t for t in titles))

    def test_chairman_ownership_position_recorded(self):
        q = FinancialQueryService(self.dbpath)
        try:
            q_conn = q.conn
            row = q_conn.execute(
                """SELECT holder_name, ownership_pct FROM ownership_positions
                WHERE company_id='sa:1120' AND holder_key='alrajhi_chairman_abdullah_sulaiman'
                AND is_current=1"""
            ).fetchone()
        finally:
            q.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["holder_name"], "Abdullah bin Sulaiman Abdulaziz Al Rajhi")
        self.assertAlmostEqual(float(row["ownership_pct"]), 0.021791737, places=6)


def _v(history, period_end):
    for row in history:
        if row["period_end"] == period_end:
            return Decimal(row["value"])
    return None


if __name__ == "__main__":
    unittest.main()
