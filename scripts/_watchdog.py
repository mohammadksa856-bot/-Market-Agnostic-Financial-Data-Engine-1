"""Stateless fleet watchdog for the Saudi raw-statement collector.

Meant to be invoked repeatedly and independently (a Windows Scheduled Task
every few minutes), not run as a long-lived process itself - manual
relaunching from inside an interactive session has repeatedly left the fleet
dead for hours whenever that session was not actively watching it. Each
invocation is a single, stateless pass: for every expected worker, check
whether a genuinely-ours process is alive for it, and launch it if not.

Never touches any process that isn't unambiguously ours: a match requires
both "_supervisor.py" (our supervisor script) and this exact worker's own
--phase/--worker-index/--scope arguments in the command line. Unrelated
automation on this machine (e.g. a separate Codex relay process, which uses
a completely different script path and its own Playwright/Edge instances)
is never enumerated for a kill decision here - this script only ever
*starts* missing processes, it never stops anything.

Usage: _watchdog.py --root <dir> [--workers 6] [--se-workers 3] [--scope full]
Logs one line per pass to <root>/logs/watchdog.log.
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COLLECTOR = SCRIPT_DIR / "sa_raw_statement_collector.py"
SUPERVISOR = SCRIPT_DIR / "_supervisor.py"
PROJECT = SCRIPT_DIR.parent


def log(root: Path, msg: str) -> None:
    line = f"{datetime.datetime.now().isoformat()} {msg}"
    print(line, flush=True)
    with (root / "logs" / "watchdog.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def is_alive(name: str, phase: str, worker_index: int, scope: str) -> bool:
    """True iff a process tree that is unambiguously OUR supervisor for this
    exact worker is currently running, verified via Win32_Process so we
    never mistake another tool's automation (e.g. Codex's own Playwright
    processes elsewhere on this machine) for one of ours."""
    filt = (
        "$_.Name -eq 'python.exe' -and "
        "$_.CommandLine -like '*_supervisor.py*' -and "
        f"$_.CommandLine -like '*--phase*{phase}*' -and "
        f"$_.CommandLine -like '*--worker-index*{worker_index}*' -and "
        f"$_.CommandLine -like '*--scope*{scope}*'"
    )
    ps = (
        "(Get-CimInstance Win32_Process | Where-Object {" + filt + "}).Count"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=30)
        return out.stdout.strip() not in ("", "0")
    except Exception:
        # If we can't tell, don't launch a possible duplicate on top of a
        # worker that might actually be alive.
        return True


def launch(root: Path, name: str, extra: list[str]) -> None:
    out = open(root / "logs" / f"{name}.out", "ab")
    flags = 0x00000008 | 0x00000200 | 0x01000000 if os.name == "nt" else 0
    worker_cmd = [sys.executable, "-B", "-u", str(COLLECTOR), "run",
                  "--root", str(root), *extra]
    cmd = [sys.executable, "-B", "-u", str(SUPERVISOR), name, str(root)] + worker_cmd
    subprocess.Popen(cmd, stdout=out, stderr=out, stdin=subprocess.DEVNULL,
                      creationflags=flags, cwd=str(PROJECT), close_fds=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--se-workers", type=int, default=3)
    ap.add_argument("--scope", default="full")
    args = ap.parse_args(argv)
    root = Path(args.root)
    (root / "logs").mkdir(parents=True, exist_ok=True)

    jobs = [(f"se-worker-{args.scope}-{i}", "se", i,
             ["--phase", "se", "--workers", str(args.se_workers),
              "--worker-index", str(i), "--scope", args.scope])
            for i in range(args.se_workers)] + [
            (f"issuer-{args.scope}-{i}", "issuer", i,
             ["--phase", "issuer", "--workers", str(args.workers),
              "--worker-index", str(i), "--scope", args.scope])
            for i in range(args.workers)]

    started, alive, skipped = [], [], []
    for name, phase, idx, extra in jobs:
        if (root / "state" / f"stop_{name}").exists():
            skipped.append(name)
            continue
        if (root / "state" / f"finished_{name}").exists():
            skipped.append(name)
            continue
        if is_alive(name, phase, idx, args.scope):
            alive.append(name)
            continue
        # Stagger relaunches within a single pass: restarting up to 9 dead
        # workers back-to-back means up to 9 Edge instances launching within
        # the same second, which has been observed to crash-loop workers
        # before they reach their first company (STATUS_DLL_INIT_FAILED
        # under startup memory/handle contention). A few seconds between
        # each launch is cheap insurance, same as the main launch command.
        if started:
            time.sleep(8)
        launch(root, name, extra)
        started.append(name)

    log(root, f"pass: alive={len(alive)} started={started} "
              f"skipped(finished/stopped)={len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
