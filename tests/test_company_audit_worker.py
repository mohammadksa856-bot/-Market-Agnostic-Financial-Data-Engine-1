import importlib.util
import tempfile
import unittest
from pathlib import Path

script = Path(__file__).resolve().parents[1]/'scripts'/'company_audit_worker.py'
if not script.exists():
    script = Path('/tmp/company_audit_worker.py')
spec = importlib.util.spec_from_file_location('company_audit_worker', script)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class AuditQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'queue.sqlite3'
        self.queue = worker.Queue(self.path)

    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()

    def test_unchanged_completed_job_is_not_duplicated(self):
        self.queue.seed('sa:1','a',100)
        self.queue.claim(101)
        self.queue.finish('sa:1',True,None,102)
        self.queue.seed('sa:1','a',103)
        self.assertIsNone(self.queue.claim(104))

    def test_changed_source_set_is_requeued(self):
        self.queue.seed('sa:1','a',100)
        self.queue.claim(101)
        self.queue.finish('sa:1',True,None,102)
        self.queue.seed('sa:1','b',103)
        self.assertEqual(self.queue.claim(104)['fingerprint'],'b')

    def test_running_company_cannot_be_claimed_twice(self):
        self.queue.seed('sa:1','a',100)
        self.assertIsNotNone(self.queue.claim(101))
        self.queue.seed('sa:1','b',102)
        self.assertIsNone(self.queue.claim(103))

    def test_failed_job_has_bounded_retry_backoff(self):
        self.queue.seed('sa:1','a',100)
        for n in range(3):
            now=100+n*1900
            self.assertIsNotNone(self.queue.claim(now))
            self.queue.finish('sa:1',False,'test',now+1)
            self.assertIsNone(self.queue.claim(now+2))
        self.assertIsNone(self.queue.claim(10000))

    def test_queue_survives_reopen_without_claiming_approval(self):
        self.queue.seed('sa:1','a',100)
        self.queue.claim(101)
        self.queue.finish('sa:1',True,None,102)
        other=worker.Queue(self.path)
        try:
            self.assertEqual(other.status()['queue_counts'],{'checks_completed_review_pending':1})
            self.assertEqual(other.status()['correctness_approved'],0)
            self.assertEqual(other.status()['completeness_approved'],0)
        finally:
            other.db.close()
