import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location(
    "windows_tadawul_relay", SCRIPTS / "windows_tadawul_relay.py"
)
relay = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(relay)


class WindowsRelayShardTests(unittest.TestCase):
    def test_even_and_odd_shards_are_disjoint_and_exhaust_sorted_registry(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry.json"
            rows = [
                {"market": "SA", "symbol": symbol}
                for symbol in ("4000", "1010", "3000", "2000", "5000")
            ]
            registry.write_text(json.dumps(rows), encoding="utf-8")

            def load(shard):
                args = SimpleNamespace(
                    registry=registry, symbols=None, shard=shard,
                    registry_seed=Path(temporary) / "seed.json",
                    registry_overrides=Path(temporary) / "overrides.json",
                )
                with mock.patch.object(relay, "validate_registry"):
                    return [item["symbol"] for item in relay._load_companies(args)]

            all_symbols = load("all")
            even = load("even")
            odd = load("odd")
            self.assertEqual(all_symbols, ["1010", "2000", "3000", "4000", "5000"])
            self.assertEqual(even, ["1010", "3000", "5000"])
            self.assertEqual(odd, ["2000", "4000"])
            self.assertFalse(set(even) & set(odd))
            self.assertEqual(set(even) | set(odd), set(all_symbols))


class FakeFetcher:
    def __init__(self, candidate, content=b"%PDF-1.7\nverified filing"):
        self.candidate = candidate
        self.content = content
        self.discover_calls = 0
        self.download_calls = 0

    def discover(self, source_url, **kwargs):
        self.discover_calls += 1
        return [dict(self.candidate)]

    def download_bytes(self, url, referer=None, content_type="application/pdf"):
        self.download_calls += 1
        return self.content


class WindowsRelayOutboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.args = SimpleNamespace(
            stage="all",
            batch_size=1,
            max_documents=5,
            enqueue_limit=0,
            timeout_seconds=5,
            symbols=None,
            crawl_issuer_site=False,
            registry=root / "registry.json",
            registry_seed=root / "seed.json",
            registry_overrides=root / "overrides.json",
            state=root / "state.json",
            archive=root / "archive",
            outbox=root / "outbox.json",
            lock=root / "relay.lock",
            log=root / "relay.jsonl",
            edge=root / "msedge.exe",
            ssh_key=root / "deploy-key",
            known_hosts=root / "known-hosts",
            server="relay@example.test",
            worker="worker-1",
        )
        self.company = {
            "market": "SA",
            "symbol": "1183",
            "exchange": "Tadawul Main Market",
            "sources": [],
        }
        self.candidate = {
            "url": "https://issuer.example/reports/fy-2025.pdf",
            "referer": "https://issuer.example/investors/reports",
            "title": "Annual report 2025",
            "content_type": "application/pdf",
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_enqueue_failure_is_retried_without_redownload_or_reupload(self):
        fetcher = FakeFetcher(self.candidate)
        remote_archive = mock.Mock(return_value="created")
        remote_enqueue = mock.Mock(side_effect=[
            RuntimeError("database is locked"),
            ("job_created", {
                "status": "queued", "queued": True, "job_id": "job-1",
            }),
        ])

        with (
            mock.patch.object(relay, "_load_companies", return_value=[self.company]),
            mock.patch.object(relay, "_remote_archive", remote_archive),
            mock.patch.object(relay, "_remote_enqueue", remote_enqueue),
        ):
            first_code, first = relay._execute(
                self.args, fetcher_factory=lambda *args, **kwargs: fetcher
            )
            second_code, second = relay._execute(
                self.args, fetcher_factory=lambda *args, **kwargs: fetcher
            )

        self.assertEqual(first_code, 0, "enqueue must not fail raw archive stage")
        self.assertEqual(first["downloads"], 1)
        self.assertEqual(first["local_archived"], 1)
        self.assertEqual(first["aws_archived"], 1)
        self.assertEqual(first["enqueue_failures"], 1)
        self.assertEqual(first["job_created"], 0)
        self.assertEqual(first["outbox"], {"pending_enqueue": 1})
        self.assertEqual(second_code, 0)
        self.assertEqual(second["downloads"], 0)
        self.assertEqual(second["aws_archived"], 0)
        self.assertEqual(second["already_archived"], 1)
        self.assertEqual(second["job_created"], 1)
        self.assertEqual(second["duplicate_job"], 0)
        self.assertEqual(fetcher.download_calls, 1)
        self.assertEqual(remote_archive.call_count, 1)
        self.assertEqual(remote_enqueue.call_count, 2)

        saved = relay._load_outbox(self.args.outbox)
        record = next(iter(saved["documents"].values()))
        self.assertEqual(record["status"], "job_created")
        self.assertEqual(record["enqueue_attempts"], 2)
        self.assertIsNone(record["last_enqueue_error"])
        self.assertEqual(record["source_url"], self.candidate["url"])
        self.assertEqual(record["source_page"], self.candidate["referer"])
        self.assertTrue(Path(record["local_path"]).is_file())
        self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            record["remote_archive_path"],
            f"/app/state/raw/SA/1183/documents/{record['sha256']}.pdf",
        )

    def test_pending_local_archive_retries_aws_without_redownload(self):
        fetcher = FakeFetcher(self.candidate)
        remote_archive = mock.Mock(side_effect=[
            RuntimeError("ssh unavailable"),
            "created",
        ])
        first_outbox = {"version": relay.OUTBOX_VERSION, "documents": {}}
        first_state = {"cursor": 0, "seen": {}, "retry_symbols": []}
        first = relay._new_summary()
        second = relay._new_summary()

        with mock.patch.object(relay, "_remote_archive", remote_archive):
            relay._archive_companies(
                self.args, [self.company], first_state, first_outbox,
                fetcher, first,
            )
            saved_after_failure = json.loads(
                self.args.outbox.read_text(encoding="utf-8")
            )
            failed_record = next(iter(saved_after_failure["documents"].values()))
            self.assertEqual(failed_record["status"], "pending_archive")
            self.assertTrue(Path(failed_record["local_path"]).is_file())

            relay._archive_companies(
                self.args,
                [self.company],
                relay._load_json(self.args.state, {}),
                relay._load_outbox(self.args.outbox),
                fetcher,
                second,
            )

        self.assertEqual(fetcher.download_calls, 1)
        self.assertEqual(remote_archive.call_count, 2)
        self.assertEqual(first["archive_failures"], 1)
        self.assertEqual(second["aws_archived"], 1)
        self.assertEqual(second["already_archived"], 1)
        final_record = next(
            iter(relay._load_outbox(self.args.outbox)["documents"].values())
        )
        self.assertEqual(final_record["status"], "pending_enqueue")
        self.assertEqual(final_record["archive_attempts"], 2)

    def test_duplicate_job_is_terminal_but_not_counted_as_created(self):
        content = b"%PDF-1.7\nduplicate"
        digest = relay.hashlib.sha256(content).hexdigest()
        local = self.args.archive / f"{digest}.pdf"
        local.parent.mkdir(parents=True)
        local.write_bytes(content)
        record = relay._outbox_record(
            self.company, self.candidate, local, digest, content
        )
        record["status"] = "pending_enqueue"
        record["remote_archived_at"] = relay._utc_now()
        outbox = {
            "version": relay.OUTBOX_VERSION,
            "documents": {f"SA:1183:{digest}": record},
        }
        relay._save_outbox(self.args.outbox, outbox)
        summary = relay._new_summary()

        with mock.patch.object(
            relay,
            "_remote_enqueue",
            return_value=("duplicate_job", {
                "status": "duplicate_job", "queued": False,
                "job_id": "existing-job",
            }),
        ):
            relay._enqueue_pending(self.args, outbox, summary)

        self.assertEqual(summary["duplicate_job"], 1)
        self.assertEqual(summary["job_created"], 0)
        self.assertEqual(summary["published_duplicate"], 0)
        self.assertEqual(record["status"], "duplicate_job")

    def test_enqueue_response_requires_consistent_status_and_boolean(self):
        cases = [
            ({"status": "queued", "queued": True}, "job_created"),
            ({"status": "duplicate_job", "queued": False}, "duplicate_job"),
            ({"status": "duplicate", "queued": False}, "published_duplicate"),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                status, parsed = relay._parse_enqueue_result(json.dumps(payload))
                self.assertEqual(status, expected)
                self.assertEqual(parsed, payload)
        for payload in (
            {"status": "duplicate_job", "queued": True},
            {"status": "queued", "queued": False},
            {"status": "duplicate"},
        ):
            with self.subTest(invalid=payload):
                with self.assertRaisesRegex(RuntimeError, "inconsistent"):
                    relay._parse_enqueue_result(json.dumps(payload))

    def test_existing_verified_aws_artifact_is_not_uploaded_again(self):
        content = b"%PDF-1.7\nremote exists"
        digest = relay.hashlib.sha256(content).hexdigest()
        local = self.args.archive / f"{digest}.pdf"
        local.parent.mkdir(parents=True)
        local.write_bytes(content)
        record = relay._outbox_record(
            self.company, self.candidate, local, digest, content
        )
        scp = mock.Mock()
        with (
            mock.patch.object(relay, "_ssh_run"),
            mock.patch.object(relay, "_remote_digest", return_value=digest),
            mock.patch.object(relay, "_run", scp),
        ):
            disposition = relay._remote_archive(self.args, record)
        self.assertEqual(disposition, "existing")
        scp.assert_not_called()

    def test_outbox_corruption_is_not_silently_replaced(self):
        self.args.outbox.write_text("{not-json", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "durable relay outbox"):
            relay._load_outbox(self.args.outbox)

    def test_application_lock_rejects_second_instance_and_is_reusable(self):
        with relay.SingleInstanceLock(self.args.lock):
            with self.assertRaises(relay.RelayAlreadyRunning):
                with relay.SingleInstanceLock(self.args.lock):
                    self.fail("second relay instance unexpectedly acquired lock")
        with relay.SingleInstanceLock(self.args.lock):
            pass
        metadata = json.loads(self.args.lock.read_text(encoding="utf-8"))
        self.assertEqual(metadata["pid"], relay.os.getpid())


if __name__ == "__main__":
    unittest.main()
