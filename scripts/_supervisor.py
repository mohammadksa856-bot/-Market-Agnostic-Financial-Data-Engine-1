"""Auto-restart wrapper for a single detached collector worker.

The collector's own in-process watchdog (HARD_COMPANY_TIMEOUT in
sa_raw_statement_collector.py) kills the worker process outright (os._exit)
when a whole browser context wedges badly enough that even its own
page-level recovery can't unblock it. This supervisor is the other half:
it relaunches the worker whenever it exits for any reason (including a
plain crash), with a short backoff, so a stuck worker self-heals without
needing anyone to notice and restart it by hand. It never runs the
collector's own retry passes itself and never touches AWS/DB commands -
it only re-execs the exact command it was given.

Usage: _supervisor.py <name> <root> <worker-cmd...>
Stop a supervised worker cleanly by creating <root>/state/stop_<name>.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

name, root, *worker_cmd = sys.argv[1:]
stop_flag = Path(root) / "state" / f"stop_{name}"
restarts = 0
while not stop_flag.exists():
    started = time.time()
    proc = subprocess.run(worker_cmd)
    restarts += 1
    print(f"[_supervisor] {name} exited code={proc.returncode} "
          f"after {round(time.time() - started)}s (restart #{restarts})",
          flush=True)
    if stop_flag.exists():
        break
    time.sleep(5)
print(f"[_supervisor] {name} stopping (stop flag present)", flush=True)
