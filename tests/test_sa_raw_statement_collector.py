import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from finengine import sa_raw_statements as raw  # noqa: E402

REGISTRY = ROOT / "config" / "sa-market-registry.json"


class ShardTests(unittest.TestCase):
    def setUp(self):
        self.reg = raw.load_registry(REGISTRY)

    def test_shard_rule(self):
        odd = raw.odd_shard(self.reg)
        even = raw.even_shard(self.reg)
        syms = [c["symbol"] for c in odd]
        self.assertEqual(len(self.reg), 439)
        self.assertEqual(len(odd), raw.SHARD_SIZE)
        self.assertEqual(syms[:8], raw.SHARD_FIRST)
        self.assertEqual(syms[-5:], raw.SHARD_LAST)
        self.assertEqual(syms, sorted(syms, key=int))
        self.assertFalse(set(syms) & {c["symbol"] for c in even})
        self.assertEqual(len(odd) + len(even), len(self.reg))

    def test_workers_disjoint_and_complete(self):
        odd = raw.odd_shard(self.reg)
        parts = raw.split_workers(odd, 4)
        flat = [c["symbol"] for p in parts for c in p]
        self.assertEqual(sorted(flat), sorted(c["symbol"] for c in odd))
        self.assertEqual(len(flat), len(set(flat)))


class PeriodTests(unittest.TestCase):
    def cp(self, text, m=12):
        return raw.classify_period(text, m)

    def test_english(self):
        r = self.cp("Interim Financial Results for the Period Ended on 30-06-2026 (Six Months)")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("H1", 2026))
        r = self.cp("Interim results for the period ended on 31-03-2025 (Three Months)")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("Q1", 2025))
        r = self.cp("interim financial results for the period ended on 2018-09-30 ( Nine Months )")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("9M", 2018))
        r = self.cp("Annual Financial results for the Year Ended on 31-12-2025")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("FY", 2025))

    def test_arabic(self):
        r = self.cp("القوائم المالية الأولية للثلاثة أشهر المنتهية في 31 مارس 2024")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("Q1", 2024))
        r = self.cp("القوائم المالية الأولية لفترة الستة أشهر المنتهية في 30 يونيو 2023")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("H1", 2023))
        r = self.cp("القوائم المالية لفترة التسعة أشهر المنتهية في 30 سبتمبر 2022")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("9M", 2022))
        r = self.cp("القوائم المالية السنوية للسنة المنتهية في 31 ديسمبر 2021")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("FY", 2021))

    def test_filenames_and_quarter_words(self):
        self.assertEqual(self.cp("Q3 2023 financial statements")["period_slot"], "9M")
        self.assertEqual(self.cp("Q2-2022 Interim Financial Statements")["period_slot"], "H1")
        self.assertEqual(self.cp("First Quarter 2021 financial statements")["period_slot"], "Q1")
        self.assertIsNone(self.cp("Q4 2020 results")["period_slot"])

    def test_primary_period_beats_comparative(self):
        t = ("Condensed interim financial statements for the three months ended "
             "31 March 2024 and year ended 31 December 2023")
        r = self.cp(t)
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("Q1", 2024))

    def test_non_calendar_fiscal_year(self):
        # FY ends June 30: 30 Sep = Q1, 31 Dec = H1, 31 Mar = 9M, 30 Jun = FY
        r = raw.classify_period("Financial statements as at 30 September 2024", 6)
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("Q1", 2025))
        r = raw.classify_period("Financial statements as at 31 March 2025", 6)
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("9M", 2025))
        r = raw.classify_period("Financial statements for the period ended 30-06-2025", 6)
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("FY", 2025))

    def test_unclassifiable(self):
        self.assertIsNone(self.cp("Financial statements")["period_slot"])

    def test_expected_slots(self):
        exp = raw.expected_slots([date(2025, 3, 31), date(2025, 12, 31), date(2025, 5, 5)])
        self.assertEqual(set(exp), {(2025, "Q1"), (2025, "FY")})


class RejectionTests(unittest.TestCase):
    def test_non_financial_rejected(self):
        for text, reason in [
            ("Q2 2024 Investor Presentation", "presentation"),
            ("Sustainability Report 2023", "sustainability"),
            ("Board of Directors' Report 2022", "board_report"),
            ("Invitation to the general assembly", "general_assembly"),
            ("Dividend distribution announcement", "dividend_notice"),
            ("عرض تقديمي للمستثمرين", "presentation"),
            ("Prospectus", "prospectus"),
        ]:
            self.assertEqual(raw.classify_document_type(text), (None, reason), text)

    def test_financial_accepted(self):
        for text in ["Interim Condensed Consolidated Financial Statements Q1 2024",
                     "القوائم المالية السنوية 2023", "Q3 2022 financial statements"]:
            self.assertIsNotNone(raw.classify_document_type(text)[0], text)

    def test_annual_report_is_separate_type(self):
        self.assertEqual(raw.classify_document_type("Annual Report 2023")[0], "annual_report")

    def test_file_kind(self):
        self.assertEqual(raw.detect_file_kind(b"%PDF-1.7 x"), "pdf")
        self.assertEqual(raw.detect_file_kind(b"PK\x03\x04zzz"), "xlsx")
        self.assertIsNone(raw.detect_file_kind(b"<html>Access denied</html>"))
        self.assertIsNone(raw.detect_file_kind(b""))

    def test_language(self):
        self.assertEqual(raw.detect_language("Financial statements"), "en")
        self.assertEqual(raw.detect_language("القوائم المالية الأولية"), "ar")
        self.assertEqual(raw.detect_language("القوائم المالية Financial Statements"), "bilingual")

    def test_website_normalisation(self):
        self.assertEqual(raw.normalize_website("http://https://www.x.com/"), "https://www.x.com")
        self.assertIsNone(raw.normalize_website("-"))


class SupportingAndFilenameTests(unittest.TestCase):
    def test_supporting_buckets(self):
        self.assertEqual(raw.classify_bucket("Pillar 3 Disclosures Q2 2024"), ("supporting", "pillar3"))
        self.assertEqual(raw.classify_bucket("BSF-Leverage Q1-2022"), ("supporting", "pillar3"))
        self.assertEqual(raw.classify_bucket("BSFDataSupplement4Q2025"), ("supporting", "data_supplement"))
        self.assertEqual(raw.classify_bucket("Fact Sheet 2023"), ("supporting", "factsheet"))
        self.assertEqual(raw.classify_bucket("Q1 earnings call transcript"), ("rejected", "presentation"))
        self.assertEqual(raw.classify_bucket("Q1 2024 earnings release")[0], "rejected")

    def test_filename_codes(self):
        for text, slot, fy in [("baj fs 2q13 final english", "H1", 2013),
                               ("baj english signed fs q22015", "H1", 2015),
                               ("bajsignedfs1q14english", "Q1", 2014),
                               ("2019 Q3 statements", "9M", 2019),
                               ("fy2020 financials", "FY", 2020)]:
            r = raw.classify_period(text)
            self.assertEqual((r["period_slot"], r["fiscal_year"]), (slot, fy), text)

    def test_cumulative_period_end_wins(self):
        r = raw.classify_period("financial statements for the three month and nine month "
                                "periods ended 30 September 2024")
        self.assertEqual((r["period_slot"], r["fiscal_year"]), ("9M", 2024))

    def test_supporting_never_in_matrix(self):
        led = raw.Ledger("1")
        led.add_doc({"content_hash": "s", "fiscal_year": 2024, "period_slot": "Q1",
                     "document_type": "supporting_pillar3", "bucket": "supporting",
                     "supporting_type": "pillar3"})
        self.assertEqual(led.coverage(), {})
        self.assertEqual(led.counts()["Q1"], 0)
        self.assertEqual(led.supporting_counts()["pillar3"], 1)
        p = raw.archive_path(Path("R"), "1", "h", "pdf", "supporting")
        self.assertEqual(p.parts[-2:], ("supporting", "h.pdf"))


class LedgerTests(unittest.TestCase):
    def doc(self, fy, slot, h, typ="financial_statement"):
        return {"content_hash": h, "fiscal_year": fy, "period_slot": slot,
                "document_type": typ}

    def test_matrix_and_missing_slots(self):
        led = raw.Ledger("1020")
        led.expected = raw.expected_slots([date(2024, 3, 31), date(2024, 6, 30), date(2024, 12, 31)])
        led.add_doc(self.doc(2024, "Q1", "a"))
        led.add_doc(self.doc(2024, "FY", "b", "annual_report"))
        led.add_doc(self.doc(2024, "Q1", "a"))  # duplicate hash ignored
        self.assertEqual(len(led.docs), 1 + 1)
        m = led.coverage()[2024]
        self.assertEqual(m["Q1"]["status"], "collected")
        self.assertEqual(m["H1"]["status"], "missing")
        self.assertEqual(m["9M"]["status"], "not_expected")
        # annual report counts only as FY-via-annual-report, never standalone
        self.assertEqual(m["FY"]["status"], "collected_via_annual_report")
        c = led.counts()
        self.assertEqual(c["FY"], 0)
        self.assertEqual(c["fy_via_annual_report"], 1)
        self.assertEqual(c["Q1"], 1)

    def test_unclassified_not_counted(self):
        led = raw.Ledger("1")
        led.add_doc(self.doc(None, None, "z"))
        self.assertEqual(led.counts()["unclassified"], 1)
        self.assertEqual(sum(led.counts()[s] for s in raw.SLOTS), 0)
        self.assertEqual(led.coverage(), {})


class UploadTests(unittest.TestCase):
    def test_commands_are_raw_only_and_not_executed(self):
        cmds = raw.upload_commands("ubuntu@13.60.3.12", "repo-worker-1", "K", "H",
                                   "1020", "C:/x/abc.pdf", "abc", "pdf")
        self.assertTrue(raw.commands_are_raw_only(cmds))
        self.assertEqual(cmds[0][0], "ssh")
        self.assertEqual(cmds[1][0], "scp")
        flat = [" ".join(c) for c in cmds]
        self.assertIn("/app/state/raw/SA/1020/documents/abc.pdf", flat[-1])
        self.assertFalse(any("relay-enqueue" in f for f in flat))
        self.assertEqual(raw.remote_target("1020", "abc", "pdf"),
                         "/app/state/raw/SA/1020/documents/abc.pdf")

    def test_outbox_row_and_archive_layout(self):
        p = raw.archive_path(Path("R"), "1020", "abc", "pdf")
        self.assertEqual(p.parts[-4:], ("archive", "SA", "1020", "abc.pdf"))
        row = raw.outbox_row("1020", p, "abc", "pdf")
        self.assertEqual(row["sha256"], "abc")


class IdempotencyTests(unittest.TestCase):
    def test_second_pass_downloads_nothing(self):
        import sa_raw_statement_collector as col
        pdf = b"%PDF-1.4\n" + b"Interim financial statements three months ended 31 March 2024" * 3

        class DL:
            calls = 0

            def get(self, url, ref):
                DL.calls += 1
                return pdf

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            company = {"symbol": "1020", "company_id": "sa:1020"}
            urls = [("https://x.example/q1-2024-financial-statements.pdf",
                     "Q1 2024 Interim Financial Statements"),
                    ("https://x.example/copy-of-q1.pdf",
                     "Q1 2024 Interim Financial Statements (copy)"),
                    ("https://x.example/deck.pdf", "Q1 2024 Investor Presentation")]
            for _ in range(2):
                run = col.CompanyRun(root, company, None, lambda e: None)
                for u, t in urls:
                    run.handle_candidate(DL(), u, t, "", "https://x.example/ir",
                                         "issuer_site", 12)
                run.save()
            # first pass: 1 download, 1 duplicate download; presentation rejected
            self.assertEqual(DL.calls, 2)
            st = json.loads((root / "state" / "issuer" / "1020.json").read_text())
            self.assertEqual(len(st["docs"]), 1)
            self.assertEqual(st["docs"][0]["period_slot"], "Q1")
            self.assertEqual(st["docs"][0]["fiscal_year"], 2024)
            self.assertEqual(st["rejected"][0]["reason"], "presentation")
            files = list((root / "archive" / "SA" / "1020").glob("*.pdf"))
            self.assertEqual(len(files), 1)
            rows = (root / "outbox" / "pending_upload.jsonl").read_text().splitlines()
            self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
