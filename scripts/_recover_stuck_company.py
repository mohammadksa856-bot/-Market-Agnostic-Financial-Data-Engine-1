"""Recover a company whose crawl hangs completely, by running it in its
own OS process with a real, OS-enforced timeout instead of relying on the
in-process page-stall watchdog thread.

Root cause (confirmed live, 2026-09-30): IssuerCrawler._watch() runs in a
Python thread and is meant to force-close a page stuck for more than 8
minutes, but Playwright's sync API can starve the GIL badly enough that
this thread never actually gets to run - a direct foreground debug crawl
of Al Omran sat completely silent for 41 minutes with the watchdog never
firing once. No amount of retrying the normal worker fleet fixes this,
because every retry hits the exact same in-process mechanism.

This script sidesteps the problem instead of trying to fix the thread: it
shells out to `... run --symbols <symbol> ...` as a **subprocess**, and
enforces the timeout with `subprocess.run(..., timeout=N)`, which the OS
guarantees regardless of what the child's Python/Playwright internals are
doing - the same trick _supervisor.py already uses at the whole-worker
level, applied here at the single-company level instead. A much shorter
timeout is viable here (default 180s) because nothing else in that
worker's queue is blocked while we wait - unlike the normal fleet, where
the reset + relaunch had to first try a full fresh crawl attempt in a
shared process.

Usage: _recover_stuck_company.py --root <dir> <symbol> [<symbol> ...]
       [--attempts 3] [--timeout 180]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COLLECTOR = SCRIPT_DIR / "sa_raw_statement_collector.py"


def reset_company(root: Path, symbol: str) -> None:
    p = root / "state" / "issuer" / f"{symbol}.json"
    if not p.exists():
        return
    st = json.loads(p.read_text(encoding="utf-8"))
    st["crawl_start_attempts"] = 0
    st["status"] = "incomplete"
    st["issuer"] = {}
    p.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def docs_count(root: Path, symbol: str) -> int:
    p = root / "state" / "issuer" / f"{symbol}.json"
    if not p.exists():
        return 0
    return len(json.loads(p.read_text(encoding="utf-8")).get("docs", []))


def recover(root: Path, symbol: str, attempts: int, timeout: int) -> dict:
    reset_company(root, symbol)
    before = docs_count(root, symbol)
    for attempt in range(1, attempts + 1):
        cmd = [sys.executable, "-B", "-u", str(COLLECTOR), "run",
               "--root", str(root), "--phase", "issuer", "--symbols", symbol,
               "--name", f"recover-{symbol}"]
        try:
            proc = subprocess.run(cmd, timeout=timeout, cwd=str(SCRIPT_DIR.parent),
                                  capture_output=True, text=True)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = "TIMEOUT"
        after = docs_count(root, symbol)
        print(f"  attempt {attempt}/{attempts}: rc={rc} docs={after}", flush=True)
        if after > before or (rc == 0 and after >= before):
            # A normal (non-timeout) return - whether or not it found
            # documents, the company genuinely finished this pass, so
            # don't keep burning attempts pretending it's still wedged.
            if rc != "TIMEOUT":
                return {"symbol": symbol, "result": "finished", "docs": after}
        # Timed out: reset again for a clean retry (the killed subprocess
        # may have left crawl_start_attempts/status half-written).
        reset_company(root, symbol)
    return {"symbol": symbol, "result": "still_stuck", "docs": docs_count(root, symbol)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("symbols", nargs="+")
    args = ap.parse_args()
    root = Path(args.root)

    results = []
    for symbol in args.symbols:
        print(f"=== {symbol} ===", flush=True)
        results.append(recover(root, symbol, args.attempts, args.timeout))

    print("\nSummary:")
    for r in results:
        print(f"  {r['symbol']}: {r['result']} docs={r['docs']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
