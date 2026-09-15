import unittest

from finengine.manifest_vintages import reconcile_vintages


def _manifest(filing_type, filed_at, period_end, facts, company_id="sa:1180"):
    return {
        "company_id": company_id, "filing_type": filing_type, "filed_at": filed_at,
        "period_end": period_end, "source_url": f"https://bank.example/{filing_type}-{filed_at}",
        "facts": facts,
    }


def _fact(metric, period_end, value, kind="quarter", **extra):
    return {"metric": metric, "period_kind": kind, "period_end": period_end,
            "value": value, "scale": "1000000", **extra}


class ReconcileVintagesTests(unittest.TestCase):
    def test_latest_vintage_wins_and_the_restated_value_is_kept_as_evidence(self):
        older = _manifest("data-supplement", "2025-04-30", "2025-03-31", [
            _fact("net_fee_income", "2024-09-30", "1164.067"),
            _fact("net_fee_income", "2025-03-31", "1100.000"),
        ])
        newer = _manifest("data-supplement", "2025-07-30", "2025-06-30", [
            _fact("net_fee_income", "2024-09-30", "1216.430"),
        ])
        old, new = reconcile_vintages([older, newer])
        self.assertEqual([f["period_end"] for f in old["facts"]], ["2025-03-31"])
        [superseded] = old["excluded_facts"]
        self.assertEqual(superseded["reason"], "restated_in_higher_ranked_publication")
        self.assertEqual(superseded["superseded_by"]["value"], "1216.430")
        self.assertEqual(superseded["superseded_by"]["filed_at"], "2025-07-30")
        self.assertEqual(len(new["facts"]), 1)

    def test_identical_repeats_are_marked_superseded_not_restated(self):
        first = _manifest("regulatory-disclosure", "2026-05-01", "2026-03-31",
                          [_fact("risk_weighted_assets", "2025-12-31", "830157896", kind="instant")])
        second = _manifest("regulatory-disclosure", "2026-08-01", "2026-06-30",
                           [_fact("risk_weighted_assets", "2025-12-31", "830157896", kind="instant")])
        old, new = reconcile_vintages([first, second])
        self.assertEqual(old["facts"], [])
        self.assertEqual(old["excluded_facts"][0]["reason"], "superseded_by_higher_ranked_publication")
        self.assertEqual(len(new["facts"]), 1)

    def test_reviewed_statement_outranks_a_later_supplement(self):
        statement = _manifest("interim-report", "2025-07-28", "2025-06-30",
                              [_fact("net_income", "2025-06-30", "6127.066")])
        supplement = _manifest("data-supplement", "2026-07-30", "2026-06-30",
                               [_fact("net_income", "2025-06-30", "6127.070")])
        kept_statement, kept_supplement = reconcile_vintages([statement, supplement])
        self.assertEqual(len(kept_statement["facts"]), 1)
        self.assertEqual(kept_supplement["facts"], [])

    def test_fixed_manifests_rank_but_are_not_returned_or_modified(self):
        audited = _manifest("financial-statements", "2026-02-04", "2025-12-31",
                            [_fact("total_operating_income", "2025-12-31", "39194.570", kind="fy")])
        supplement = _manifest("data-supplement", "2026-07-30", "2026-06-30", [
            _fact("total_operating_income", "2025-12-31", "39194.570", kind="fy"),
            _fact("total_operating_income", "2026-06-30", "10582.649"),
        ])
        [result] = reconcile_vintages([supplement], fixed=[audited])
        self.assertEqual([f["period_end"] for f in result["facts"]], ["2026-06-30"])
        self.assertEqual(len(audited["facts"]), 1)
        self.assertNotIn("excluded_facts", audited)

    def test_scope_and_dimensions_are_part_of_the_fact_identity(self):
        first = _manifest("data-supplement", "2026-04-30", "2026-03-31", [
            _fact("net_financing_income", "2026-03-31", "4340.878",
                  dimensions={"segment": "retail"}),
        ])
        second = _manifest("data-supplement", "2026-07-30", "2026-06-30", [
            _fact("net_financing_income", "2026-03-31", "7496.322"),
        ])
        segment, consolidated = reconcile_vintages([first, second])
        self.assertEqual(len(segment["facts"]), 1)
        self.assertEqual(len(consolidated["facts"]), 1)

    def test_inputs_are_not_mutated(self):
        older = _manifest("data-supplement", "2025-04-30", "2025-03-31",
                          [_fact("net_income", "2024-12-31", "5520.069")])
        newer = _manifest("data-supplement", "2025-07-30", "2025-06-30",
                          [_fact("net_income", "2024-12-31", "5520.068")])
        reconcile_vintages([older, newer])
        self.assertEqual(len(older["facts"]), 1)
        self.assertNotIn("excluded_facts", older)

    def test_later_reporting_period_outranks_an_inferred_filing_date(self):
        # Workbook metadata can postdate publication; the period a document covers cannot.
        older = _manifest("data-supplement", "2025-11-20", "2025-06-30",
                          [_fact("net_income", "2024-09-30", "5349.903")])
        newer = _manifest("data-supplement", "2025-11-13", "2025-09-30",
                          [_fact("net_income", "2024-09-30", "5349.905")])
        old, new = reconcile_vintages([older, newer])
        self.assertEqual(old["facts"], [])
        self.assertEqual(len(new["facts"]), 1)

    def test_manifest_without_header_period_is_ranked_by_its_latest_fact(self):
        # Supplement vintages: 2Q-2025 workbook last modified after the 3Q-2025 one.
        older = {"company_id": "sa:1180", "filing_type": "data-supplement", "filed_at": "2025-11-20",
                 "source_url": "https://bank.example/2q-2025.xlsx", "facts": [
                     _fact("net_income", "2022-12-31", "18000.000", kind="fy"),
                     _fact("net_income", "2025-06-30", "6127.066")]}
        newer = {"company_id": "sa:1180", "filing_type": "data-supplement", "filed_at": "2025-11-13",
                 "source_url": "https://bank.example/3q-2025.xlsx", "facts": [
                     _fact("net_income", "2022-12-31", "18100.000", kind="fy"),
                     _fact("net_income", "2025-09-30", "6472.959")]}
        old, new = reconcile_vintages([older, newer], by_period=True)
        self.assertEqual([f["period_end"] for f in old["facts"]], ["2025-06-30"])
        self.assertIn("2022-12-31", [f["period_end"] for f in new["facts"]])

    def test_by_period_lets_the_reviewed_statement_supply_the_whole_period(self):
        statement = _manifest("interim-report", "2025-07-28", "2025-06-30",
                              [_fact("net_income", "2025-06-30", "6127.066")])
        supplement = _manifest("data-supplement", "2026-07-30", "2026-06-30", [
            _fact("net_income", "2025-06-30", "6127.066"),
            _fact("net_fee_income", "2025-06-30", "1243.455"),  # absent from the statement
            _fact("net_income", "2026-06-30", "6614.848"),
        ])
        kept_statement, kept_supplement = reconcile_vintages(
            [statement, supplement], by_period=True)
        self.assertEqual(len(kept_statement["facts"]), 1)
        self.assertEqual([(f["metric"], f["period_end"]) for f in kept_supplement["facts"]],
                         [("net_income", "2026-06-30")])
        reasons = {f["metric"]: f["reason"] for f in kept_supplement["excluded_facts"]}
        self.assertEqual(reasons["net_fee_income"], "period_supplied_by_higher_ranked_publication")
        self.assertEqual(reasons["net_income"], "superseded_by_higher_ranked_publication")


if __name__ == "__main__":
    unittest.main()
