"""Audit-worker liveness, not the unrelated HTTP service health check."""
import json
import time
from pathlib import Path

path = Path('/app/state/reports/company-audits/worker-status.json')
assert time.time()-path.stat().st_mtime < 180, 'audit worker heartbeat is stale'
status = json.loads(path.read_text())
assert 'queue_counts' in status
print('audit worker heartbeat current')
