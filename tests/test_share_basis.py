import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.database import Database
from finengine.domains import CompanyDomainStore
from finengine.models import Company, Fact, Market, PeriodKind, SourceDocument
from finengine.share_basis import audit_share_basis, withheld_metric_keys


class ShareBasisAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(str(Path(self.temp.name) / "basis.sqlite3"))
        self.db.register_company(Company("sa:TST", Market.SA, "TST", "Test Energy", "SAR",
                                         isin="SA0000000001", exchange="Saudi Exchange", country="SA",
                                         sector="Energy", industry="Integrated Oil & Gas",
                                         timezone="Asia/Riyadh"))
        self.store = CompanyDomainStore(self.db)
        self.sources = {}
        # Annual reports: FY2021 filed 2022-03, FY2022 report filed 2023-03, FY2023 report filed 2024-03.
        for year, filed in ((2021, "2022-03-20"), (2022, "2023-03-12"), (2023, "2024-03-10")):
            source = SourceDocument("sa:TST", Market.SA, f"https://example.test/ar{year}", f"source:ar{year}",
                                    "annual-report", filed, b"{}")
            self.db.save_source(source, f"digest{year}", None)
            self.sources[year] = source

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def fact(self, metric, value, year, report, calculated=False):
        source = self.sources[report]
        return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR/share" if metric == "eps_diluted" else "ratio",
                    f"{year}-01-01", f"{year}-12-31", PeriodKind.FY, year, None, source.source_key,
                    source.source_url, source.filed_at, is_calculated=calculated,
                    calculation="eps_diluted / prior_fy(eps_diluted) - 1" if calculated else None)

    def bonus(self, effective):
        self.store.publish_corporate_action(f"sa:TST:bonus:{effective}", "sa:TST", "bonus_shares", "bonus issue",
                                            effective, self.sources[2023].source_key, effective_date=effective,
                                            ratio_numerator=1, ratio_denominator=10, status="completed")

    def flagged(self):
        return {(row["metric_key"], row["period_end"]) for row in audit_share_basis(self.db.conn, "sa:TST")}

    def publish_growth_2022(self):
        # EPS 2021 as last stated in the FY2022 report; EPS 2022 restated in the FY2023 report.
        for item in (self.fact("eps_diluted", "1.80", 2021, 2022), self.fact("eps_diluted", "2.47", 2022, 2023),
                     self.fact("eps_growth", "0.372", 2022, 2023, calculated=True)):
            self.db.publish(item)

    def test_growth_between_reports_filed_either_side_of_a_bonus_is_withheld(self):
        self.publish_growth_2022()
        self.bonus("2023-05-08")
        self.assertEqual(self.flagged(), {("eps_growth", "2022-12-31")})
        self.assertEqual(withheld_metric_keys(self.db.conn, "sa:TST"), {"eps_growth"})
        missing = {key for row in self.store.refresh_catalog_completeness("sa:TST")["categories"]
                   for key in row["missing"]}
        self.assertIn("eps_growth", missing)

    def test_no_event_or_an_event_outside_the_filing_window_keeps_the_growth(self):
        self.publish_growth_2022()
        self.assertEqual(self.flagged(), set())
        self.bonus("2024-06-01")  # after both reports: both values share the old basis
        self.bonus("2022-05-12")  # before both reports: both values are restated for it
        self.assertEqual(self.flagged(), set())

    def test_a_clean_year_keeps_the_key_counted(self):
        self.publish_growth_2022()
        for item in (self.fact("eps_diluted", "1.87", 2023, 2023),
                     self.fact("eps_growth", "-0.243", 2023, 2023, calculated=True)):
            self.db.publish(item)
        self.bonus("2023-05-08")
        self.assertEqual(self.flagged(), {("eps_growth", "2022-12-31")})
        self.assertEqual(withheld_metric_keys(self.db.conn, "sa:TST"), set())

    def test_unresolved_inputs_are_withheld_when_the_company_has_share_basis_events(self):
        self.db.publish(self.fact("eps_growth", "0.1", 2022, 2023, calculated=True))
        self.bonus("2023-05-08")
        reasons = {row["reason"] for row in audit_share_basis(self.db.conn, "sa:TST")}
        self.assertEqual(reasons, {"inputs_not_resolved"})


if __name__ == "__main__":
    unittest.main()
