import json
import unittest

from finengine.announcements import announcement_fields


def row(disclosure_type="earnings_release", language="en", metadata=None, **extra):
    base = {"disclosure_type": disclosure_type, "title": "Q3 results", "body_text": "Revenue rose.",
            "language": language, "published_at": "2026-10-25", "period_end": "2026-09-30",
            "metadata_json": json.dumps(metadata or {}), "source_url": "https://example.test/release.pdf"}
    return {**base, **extra}


class AnnouncementFieldTests(unittest.TestCase):
    def test_record_properties_become_fields(self):
        fields = announcement_fields([row()])
        self.assertTrue({"announcement_category", "announcement_date", "announcement_body", "announcement_title_en",
                         "announcement_source_url", "related_financial_period", "earnings_flag"} <= fields)
        self.assertNotIn("announcement_title_ar", fields)
        self.assertNotIn("announcement_id", fields)

    def test_arabic_title_from_an_arabic_record_or_the_issuer_listing(self):
        self.assertIn("announcement_title_ar", announcement_fields([row(language="ar")]))
        self.assertIn("announcement_title_ar", announcement_fields([row(metadata={"title_ar": "بيان النتائج"})]))

    def test_flags_need_a_record_in_their_class(self):
        fields = announcement_fields([row("risk_factor"), row("material_event", metadata={"event_class": "divestment"})])
        self.assertIn("merger_acquisition_flag", fields)
        self.assertFalse({"earnings_flag", "dividend_flag", "contract_flag", "governance_flag"} & fields)

    def test_missing_properties_are_not_counted(self):
        fields = announcement_fields([row(source_url=None, period_end=None, published_at=None, body_text=" ")])
        self.assertFalse({"announcement_source_url", "related_financial_period", "announcement_date",
                          "announcement_body"} & fields)

    def test_no_records_no_fields(self):
        self.assertEqual(announcement_fields([]), set())


if __name__ == "__main__":
    unittest.main()
