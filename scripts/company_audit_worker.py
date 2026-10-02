"""Continuous deterministic audit queue, isolated from production writes."""
import datetime
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path('/app/state/reports/company-audits')


class Queue:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS company_jobs(
            company_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
            checked_at REAL NOT NULL DEFAULT 0, updated_at REAL NOT NULL,
            error TEXT, heartbeat REAL)''')
        self.db.commit()

    def seed(self, company_id, fingerprint, now):
        old = self.db.execute('SELECT * FROM company_jobs WHERE company_id=?', (company_id,)).fetchone()
        if old is None:
            self.db.execute('INSERT INTO company_jobs(company_id,fingerprint,updated_at) VALUES(?,?,?)', (company_id, fingerprint, now))
        elif old['status'] != 'running' and (old['fingerprint'] != fingerprint or (old['checked_at'] and now-old['checked_at'] >= 86400)):
            self.db.execute("UPDATE company_jobs SET fingerprint=?,status='queued',attempts=0,error=NULL,updated_at=?,checked_at=0 WHERE company_id=?", (fingerprint,now,company_id))
        self.db.commit()

    def claim(self, now):
        with self.db:
            row = self.db.execute("""SELECT * FROM company_jobs WHERE status='queued'
                OR (status='failed' AND attempts<3 AND updated_at<?)
                ORDER BY CASE WHEN company_id='sa:1060' THEN 0 ELSE 1 END,company_id LIMIT 1""", (now-1800,)).fetchone()
            if row:
                self.db.execute("UPDATE company_jobs SET status='running',attempts=attempts+1,heartbeat=?,updated_at=? WHERE company_id=?", (now,now,row['company_id']))
            return dict(row) if row else None

    def finish(self, company_id, ok, error, now):
        with self.db:
            self.db.execute('UPDATE company_jobs SET status=?,error=?,checked_at=?,updated_at=?,heartbeat=? WHERE company_id=?',
                ('checks_completed_review_pending' if ok else 'failed',error,now,now,now,company_id))

    def status(self, company_id=None):
        counts = dict(self.db.execute('SELECT status,count(*) FROM company_jobs GROUP BY status').fetchall())
        return {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'active_company': company_id,
                'queue_counts': counts, 'correctness_approved': 0, 'completeness_approved': 0,
                'note': 'Completed jobs mean automated checks finished, not full extraction or correctness approval.'}


def seed_from_production(queue):
    db = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
    companies = {}
    for row in db.execute("SELECT company_id,source_key,content_hash,status FROM source_documents WHERE company_id LIKE 'sa:%' ORDER BY company_id,source_key"):
        companies.setdefault(row[0], []).append(tuple(row[1:]))
    db.close()
    for company, sources in companies.items():
        queue.seed(company, hashlib.sha256(json.dumps(sources).encode()).hexdigest(), time.time())


def save_status(queue, company=None):
    target = ROOT/'worker-status.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(queue.status(company), indent=2)+'\n')
    temporary.replace(target)


def main():
    import fcntl
    ROOT.mkdir(parents=True, exist_ok=True)
    lock = (ROOT/'worker.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    queue = Queue(ROOT/'audit-queue.sqlite3')
    with queue.db:
        queue.db.execute("UPDATE company_jobs SET status='queued' WHERE status='running'")
    next_seed = 0
    while True:
        if time.time() >= next_seed:
            seed_from_production(queue)
            next_seed = time.time()+900
        job = queue.claim(time.time())
        if not job:
            save_status(queue)
            time.sleep(30)
            continue
        company = job['company_id']
        out = ROOT/company.replace(':','-')
        out.mkdir(exist_ok=True)
        save_status(queue,company)
        print(json.dumps({'event':'started','company':company}), flush=True)
        with (out/'worker-run.log').open('a') as log:
            process = subprocess.Popen([sys.executable,str(Path(__file__).with_name('audit_company_sources.py')),company], stdout=log,stderr=subprocess.STDOUT)
            started = time.time()
            timed_out = False
            while process.poll() is None:
                if time.time()-started > 2700:
                    process.kill(); process.wait(); timed_out=True; break
                with queue.db:
                    queue.db.execute('UPDATE company_jobs SET heartbeat=? WHERE company_id=?', (time.time(),company))
                save_status(queue,company)
                time.sleep(10)
        ok = process.returncode == 0 and not timed_out
        queue.finish(company,ok, None if ok else ('timeout' if timed_out else 'exit '+str(process.returncode)),time.time())
        save_status(queue)
        print(json.dumps({'event':'checks_finished' if ok else 'failed','company':company,'status':queue.status()}),flush=True)


if __name__ == '__main__':
    main()
