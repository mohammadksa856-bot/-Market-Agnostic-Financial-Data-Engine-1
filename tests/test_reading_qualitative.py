import json
import tempfile
import types
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False


def _profile_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((60, 60), "This is Acme Bank", fontsize=13)
    page.insert_text((60, 100), "Acme Bank is a Sharia-compliant retail bank headquartered in Riyadh.", fontsize=9)
    page.insert_text((60, 120), "Chief Executive Officer: Jane Doe", fontsize=9)
    doc.save(path)
    doc.close()


def _fake_client(findings_a, findings_b):
    """Two independent Messages.create calls, returning the two passes in
    order -- mirrors how the real Anthropic client is called twice."""
    calls = {"n": 0}

    class Messages:
        def create(self, **kwargs):
            calls["n"] += 1
            findings = findings_a if calls["n"] == 1 else findings_b
            text = json.dumps({"findings": findings})
            return types.SimpleNamespace(
                content=[types.SimpleNamespace(type="text", text=text)],
                usage=types.SimpleNamespace(input_tokens=1000, output_tokens=100))
    return types.SimpleNamespace(messages=Messages())


@unittest.skipUnless(HAVE_PYMUPDF, "needs the optional pymupdf extra")
class QualitativeReaderTests(unittest.TestCase):
    def test_agreeing_grounded_findings_are_accepted(self):
        from finengine.reading_qualitative import qualitative_read

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _profile_pdf(pdf)
            quote = "Acme Bank is a Sharia-compliant retail bank headquartered in Riyadh."
            client = _fake_client(
                findings_a=[{"attribute_key": "business_description", "value": "Sharia-compliant retail bank in Riyadh", "quote": quote, "page": 1},
                            {"attribute_key": "ceo_name", "value": "Jane Doe", "quote": "Chief Executive Officer: Jane Doe", "page": 1}],
                findings_b=[{"attribute_key": "business_description", "value": "Sharia-compliant retail bank in Riyadh", "quote": quote, "page": 1},
                            {"attribute_key": "ceo_name", "value": "Jane Doe", "quote": "Chief Executive Officer: Jane Doe", "page": 1}],
            )
            result = qualitative_read(
                pdf, market="SA", symbol="9999", source_url="https://example.test/acme.pdf",
                filed_at="2026-03-01", client=client)

            accepted_keys = {f["attribute_key"] for f in result["accepted"]}
            self.assertEqual(accepted_keys, {"business_description", "ceo_name"})
            self.assertEqual(result["review_queue"], [])
            for f in result["accepted"]:
                self.assertEqual(f["confidence"], "high")

    def test_disagreement_goes_to_review_not_publication(self):
        from finengine.reading_qualitative import qualitative_read

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _profile_pdf(pdf)
            quote = "Chief Executive Officer: Jane Doe"
            client = _fake_client(
                findings_a=[{"attribute_key": "ceo_name", "value": "Jane Doe", "quote": quote, "page": 1}],
                findings_b=[{"attribute_key": "ceo_name", "value": "John Smith", "quote": quote, "page": 1}],
            )
            result = qualitative_read(
                pdf, market="SA", symbol="9999", source_url="https://example.test/acme.pdf",
                filed_at="2026-03-01", client=client)

            self.assertEqual(result["accepted"], [])
            self.assertEqual(len(result["review_queue"]), 1)
            self.assertEqual(result["review_queue"][0]["reason"], "disagreement")

    def test_unverifiable_quote_is_not_grounded_even_if_both_passes_agree(self):
        """Both passes hallucinating the SAME wrong quote must still be
        caught -- agreement between two passes is necessary but not
        sufficient; the quote must actually be on the page."""
        from finengine.reading_qualitative import qualitative_read

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _profile_pdf(pdf)
            fabricated_quote = "Acme Bank was founded in 1850 by a group of merchants."
            client = _fake_client(
                findings_a=[{"attribute_key": "business_description", "value": "Founded 1850", "quote": fabricated_quote, "page": 1}],
                findings_b=[{"attribute_key": "business_description", "value": "Founded 1850", "quote": fabricated_quote, "page": 1}],
            )
            result = qualitative_read(
                pdf, market="SA", symbol="9999", source_url="https://example.test/acme.pdf",
                filed_at="2026-03-01", client=client)

            self.assertEqual(result["accepted"], [])
            self.assertEqual(result["review_queue"][0]["reason"], "ungrounded")

    def test_punctuation_only_phrasing_differences_still_agree(self):
        """Found running this reader against a real Al Rajhi Bank annual
        report page (431, 'Auditors: Ernst and Young / Deloitte and Touche
        & Co'): two independent, correct readings of the same real text
        rendered it with '&' vs 'and' and different punctuation. An exact
        string-equality agreement check flagged that as a disagreement,
        which would have sent a genuinely-agreed, correctly-grounded fact
        to manual review for no real reason. `_values_agree` compares
        word sets instead, specifically to tolerate this."""
        from finengine.reading_qualitative import qualitative_read

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _profile_pdf(pdf)
            quote = "Chief Executive Officer: Jane Doe"
            client = _fake_client(
                findings_a=[{"attribute_key": "ceo_name", "value": "Jane Doe; Chief Executive", "quote": quote, "page": 1}],
                findings_b=[{"attribute_key": "ceo_name", "value": "Jane Doe & Chief Executive", "quote": quote, "page": 1}],
            )
            result = qualitative_read(
                pdf, market="SA", symbol="9999", source_url="https://example.test/acme.pdf",
                filed_at="2026-03-01", client=client)
            self.assertEqual(len(result["accepted"]), 1)
            self.assertEqual(result["review_queue"], [])

    def test_single_pass_finding_goes_to_review(self):
        from finengine.reading_qualitative import qualitative_read

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _profile_pdf(pdf)
            client = _fake_client(
                findings_a=[{"attribute_key": "ceo_name", "value": "Jane Doe", "quote": "Chief Executive Officer: Jane Doe", "page": 1}],
                findings_b=[],
            )
            result = qualitative_read(
                pdf, market="SA", symbol="9999", source_url="https://example.test/acme.pdf",
                filed_at="2026-03-01", client=client)

            self.assertEqual(result["accepted"], [])
            self.assertEqual(result["review_queue"][0]["reason"], "single_pass")

    def test_unknown_attribute_key_is_dropped_not_invented(self):
        from finengine.reading_qualitative import qualitative_read

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _profile_pdf(pdf)
            findings = [{"attribute_key": "totally_made_up_field", "value": "x", "quote": "Jane Doe", "page": 1}]
            client = _fake_client(findings_a=findings, findings_b=findings)
            result = qualitative_read(
                pdf, market="SA", symbol="9999", source_url="https://example.test/acme.pdf",
                filed_at="2026-03-01", client=client)
            self.assertEqual(result["accepted"], [])
            self.assertEqual(result["review_queue"], [])


if __name__ == "__main__":
    unittest.main()
