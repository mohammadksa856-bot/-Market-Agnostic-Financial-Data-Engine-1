import unittest
from decimal import Decimal

from finengine.manifest_audit import (
    audit_fact_provenance, audit_manifest_provenance, dominant_page_offset,
    normalise_page_text, quarters_vs_fiscal_year, summarise,
)

PAGES = [
    "Cover page of the annual report 2025 with enough words to count as a text page.",
    # page 2: customer concentration printed in millions, plus a digital statement line
    "Information about major customers. Included in revenues are revenues of approximately "
    "SAR 11,298 million (2024: SAR 11,145 million) from Government entities. "
    "Goodwill amounts to SAR 75.6 million. Defined contribution expense is SAR 631 million.",
    # page 3: a statement table printed in SAR thousands
    "Statement of cash flows (SAR thousands) Net cash generated from operating activities 18,283,163 19,885,337 "
    "Dividends paid (20,954,565) (9,687,757) Earnings per share 2.97 4.95",
    "",  # page 4: scanned image, no text layer
    "Arabic digits note: net profit for the year ٢٢٠٬٩٣٢٬٩٤١ total.",
]


def fact(metric, value, page, scale="1000", **extra):
    return {"metric": metric, "value": value, "page": page, "scale": scale, "period_end": "2025-12-31",
            "period_kind": "fy", **extra}


def audit(f):
    return audit_manifest_provenance({"facts": [f]}, PAGES)[0]


class ProvenanceTests(unittest.TestCase):
    def test_value_printed_on_claimed_page_is_ok(self):
        self.assertEqual(audit(fact("operating_cash_flow", "18283163", 3)).status, "ok")
        self.assertEqual(audit(fact("dividends_paid", "-20954565", 3)).status, "ok")
        self.assertEqual(audit(fact("eps", "2.97", 3, scale=None)).status, "ok")

    def test_short_numbers_are_flagged_as_weak_evidence(self):
        result = audit(fact("eps", "2.97", 3, scale=None))
        self.assertIn("weak", result.detail)

    def test_adjacent_page_is_a_page_offset_and_distant_page_is_wrong_page(self):
        self.assertEqual(audit(fact("operating_cash_flow", "18283163", 2)).status, "page_offset")
        self.assertEqual(audit(fact("operating_cash_flow", "18283163", 1)).status, "wrong_page")

    def test_million_text_stored_as_thousands_with_scale_one_is_a_scale_suspect(self):
        # "SAR 11,298 million" stored as raw 11,298,000 with scale 1 is SAR 11.3 million, 1000x too small.
        result = audit(fact("customer_concentration", "11298000", 2, scale="1"))
        self.assertEqual(result.status, "scale_suspect")
        self.assertIn("11,298 million", result.detail)
        result = audit(fact("employee_benefit_expense", "631000", 2, scale="1"))
        self.assertEqual(result.status, "scale_suspect")

    def test_million_text_stored_correctly_is_not_a_scale_suspect(self):
        # raw 11,298,000 x scale 1000 = SAR 11,298 million -> consistent with the text
        self.assertNotEqual(audit(fact("customer_concentration", "11298000", 2, scale="1000")).status, "scale_suspect")
        # SAR 75.6 million stored as 75,600,000 with scale 1 is right
        self.assertNotEqual(audit(fact("goodwill", "75600000", 2, scale="1")).status, "scale_suspect")

    def test_value_stored_in_millions_matches_a_thousands_table(self):
        pages = ["Statement of profit or loss (SAR thousands) Revenue 14,834,056 14,046,168 Net income 1,071,541"]
        f = {"metric": "revenue", "value": "14834.056", "scale": "1000000", "page": 1,
             "period_end": "2021-12-31", "period_kind": "fy"}
        self.assertEqual(audit_manifest_provenance({"facts": [f]}, pages)[0].status, "ok")

    def test_scanned_page_is_reported_not_guessed(self):
        self.assertEqual(audit(fact("revenue", "77818675", 4)).status, "image_page")

    def test_missing_page_and_out_of_range_page(self):
        self.assertEqual(audit(fact("revenue", "77818675", None)).status, "no_page")
        result = audit(fact("operating_cash_flow", "18283163", 142))
        self.assertEqual(result.status, "page_out_of_range")
        self.assertEqual(result.found_pages, [3])

    def test_not_found_on_a_text_page(self):
        self.assertEqual(audit(fact("revenue", "99999999", 3)).status, "not_found")

    def test_arabic_indic_digits_are_normalised(self):
        self.assertIn("220,932,941", normalise_page_text(PAGES[4]))
        self.assertEqual(audit(fact("net_income", "220932941", 5, scale="1")).status, "ok")

    def test_summary_and_dominant_offset(self):
        results = audit_manifest_provenance({"facts": [
            fact("operating_cash_flow", "18283163", 2),
            fact("dividends_paid", "-20954565", 2),
            fact("customer_concentration", "11298000", 2, scale="1"),
        ]}, PAGES)
        self.assertEqual(summarise(results), {"page_offset": 2, "scale_suspect": 1})
        self.assertEqual(dominant_page_offset(results), 1)


def quarter_fact(metric, fiscal_quarter, value, year=2023, **extra):
    return {"metric": metric, "period_kind": "quarter", "fiscal_quarter": fiscal_quarter, "fiscal_year": year,
            "period_end": f"{year}-{fiscal_quarter * 3:02d}-28", "value": value, "scale": "1000000000", **extra}


class QuarterSumTests(unittest.TestCase):
    def manifests(self, quarters, annual, source="q"):
        return [
            {"company_id": "sa:7010", "source_url": f"{source}.pdf", "facts": quarters},
            {"company_id": "sa:7010", "source_url": "fy.pdf", "facts": [
                {"metric": "revenue", "period_kind": "fy", "fiscal_year": 2023, "period_end": "2023-12-31",
                 "value": annual, "scale": "1000"}]},
        ]

    def test_mixed_original_and_restated_basis_is_reported(self):
        quarters = [quarter_fact("revenue", n, v) for n, v in enumerate(("18.18", "18.33", "18.11", "17.72"), 1)]
        findings = quarters_vs_fiscal_year(self.manifests(quarters, "71777161"))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["fiscal_year"], 2023)
        self.assertGreater(Decimal(findings[0]["gap_fraction"]), Decimal("0.007"))

    def test_rounding_noise_is_not_reported(self):
        quarters = [quarter_fact("revenue", n, v) for n, v in enumerate(("18.9", "19.0", "18.6", "19.3"), 1)]
        self.assertEqual(quarters_vs_fiscal_year(self.manifests(quarters, "75893413")), [])

    def test_incomplete_years_are_never_compared(self):
        quarters = [quarter_fact("revenue", n, "18") for n in (1, 2, 3)]
        self.assertEqual(quarters_vs_fiscal_year(self.manifests(quarters, "71777161")), [])


if __name__ == "__main__":
    unittest.main()
