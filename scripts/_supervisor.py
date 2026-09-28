"""Auto-restart wrapper for a single detached collector worker.

The collector's own in-process watchdog (HARD_COMPANY_TIMEOUT in
sa_raw_statement_collector.py) is meant to kill the worker outright
(os._exit) when a browser context wedges badly enough that even its own
page-level recovery can't unblock it - but in production it was observed
NOT firing at all across four workers that sat completely idle (zero CPU
growth, zero logged progress) for 2.5+ hours, five times its own 30-minute
deadline. The most likely explanation is that Playwright's sync API (which
uses greenlets under the hood to block the calling thread on results from
its own internal asyncio-driver thread) can, in some wedged state, prevent
Python's GIL from ever being handed to this process's OTHER threads,
including the in-process watchdog thread itself - so anything that depends
on cooperation from inside the process cannot be trusted as the only
safety net.

This supervisor is the other half, and now the primary, OS-level one: it
enforces its OWN hard wall-clock timeout on the whole worker process via
subprocess.run(..., timeout=...), which the OS guarantees regardless of
what the child's Python interpreter or threads are doing internally, and
relaunches the worker whenever it exits or is killed for any reason, with
backoff. It never runs the collector's own retry passes itself and never
touches AWS/DB commands - it only re-execs the exact command it was given.

Usage: _supervisor.py <name> <root> <worker-cmd...>
Stop a supervised worker cleanly by creating <root>/state/stop_<name>.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

SUPERVISOR_TIMEOUT = 2400  # seconds: external, OS-enforced hard cap per
                           # worker run. Deliberately longer than the
                           # in-process 30-minute deadline so a healthy
                           # worker's own recovery gets first chance, but
                           # this fires regardless of whether that internal
                           # mechanism is itself working.

name, root, *worker_cmd = sys.argv[1:]
stop_flag = Path(root) / "state" / f"stop_{name}"
finished_flag = Path(root) / "state" / f"finished_{name}"
restarts = 0
fast_fail_streak = 0
while not stop_flag.exists() and not finished_flag.exists():
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(worker_cmd, timeout=SUPERVISOR_TIMEOUT)
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        # subprocess.run already tried to kill() the child on timeout, but
        # that only reaches the immediate child - our worker is itself a
        # detached "python -u collector.py run ..." whose own children
        # (the Playwright driver, Edge) are not guaranteed to die with it.
        # Sweep for anything still alive under this exact worker_cmd's own
        # identifying arguments (phase + worker-index, unique per worker)
        # and force them down too, so a wedged worker cannot leave orphaned
        # Edge/driver processes behind across restarts.
        timed_out = True
        returncode = "TIMEOUT"
        try:
            filters = " -and ".join(
                f"$_.CommandLine -like '*{arg}*'" for arg in worker_cmd
                if arg in {"--phase", "--worker-index", "--scope"} or
                worker_cmd[max(0, worker_cmd.index(arg) - 1)] in
                {"--phase", "--worker-index", "--scope"})
            if filters:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     f"Get-CimInstance Win32_Process | Where-Object {{{filters}}} | "
                     "ForEach-Object { Stop-Process -Id $_.ProcessId -Force "
                     "-ErrorAction SilentlyContinue }"],
                    timeout=30)
        except Exception:
            pass
    elapsed = time.time() - started
    restarts += 1
    print(f"[_supervisor] {name} exited code={returncode} "
          f"after {round(elapsed)}s (restart #{restarts})"
          f"{' [SUPERVISOR TIMEOUT]' if timed_out else ''}", flush=True)
    if stop_flag.exists() or finished_flag.exists():
        break
    if timed_out:
        fast_fail_streak = 0
        wait = 5
    elif elapsed < 30:
        # A near-instant exit (crashed or a clean "nothing to do" loop) is
        # never worth retrying every 5s: on this machine, launching Edge for
        # every worker again immediately after a crash can itself fail
        # (STATUS_DLL_INIT_FAILED) under memory/handle pressure, turning one
        # bad launch into a tight, resource-hungry crash loop across the
        # whole fleet. Back off, and harder the more it keeps happening.
        fast_fail_streak += 1
        wait = min(30 * (2 ** (fast_fail_streak - 1)), 600)
    else:
        fast_fail_streak = 0
        wait = 5
    time.sleep(wait)
print(f"[_supervisor] {name} stopping "
      f"({'stop flag' if stop_flag.exists() else 'slice finished'})", flush=True)
