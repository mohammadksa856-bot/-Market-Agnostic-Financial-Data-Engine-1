#!/usr/bin/env python3
"""Enqueue a pre-positioned Saudi raw archive from inside the worker."""
from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("/app/state/sa-bulk/manifest.jsonl"))
    parser.add_argument("--checkpoint", type=Path, default=Path("/app/state/sa-bulk/checkpoint.json"))
    parser.add_argument("--database", default="/app/state/financial.sqlite3")
    parser.add_argument("--registry", default="/app/state/sa-bulk/registry.json")
    args = parser.parse_args()

    lock_path = args.checkpoint.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("w")
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

    checkpoint = load_json(args.checkpoint, {})
    summary = {"selected": 0, "queued": 0, "duplicate": 0, "failed": 0}
    for line in args.manifest.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        digest = record["sha256"]
        if checkpoint.get(digest, {}).get("done"):
            continue
        summary["selected"] += 1
        metadata = record["metadata"]
        command = [
            "finengine", "--db", args.database, "relay-enqueue",
            record["remote_path"], "SA", record["symbol"],
            "--registry", args.registry, "--raw-dir", "/app/state/raw",
            "--source-url", metadata["source_url"],
            "--filed-at", metadata["filed_at"],
            "--filing-type", metadata["filing_type"],
            "--title", metadata["title"],
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        payload = None
        try:
            payload = json.loads(result.stdout)
        except ValueError:
            pass
        status = str((payload or {}).get("status") or ("failed" if result.returncode else "queued"))
        done = result.returncode == 0 and status in {"queued", "duplicate", "duplicate_job"}
        key = "duplicate" if status in {"duplicate", "duplicate_job"} else ("queued" if done else "failed")
        summary[key] += 1
        checkpoint[digest] = {
            "done": done, "status": status,
            "at": datetime.now(timezone.utc).isoformat(),
            "error": "" if done else (result.stderr or result.stdout)[-1000:],
        }
        save_json(args.checkpoint, checkpoint)
        print(json.dumps({"sha256": digest, "symbol": record["symbol"],
                          "status": status, "done": done}), flush=True)
    print(json.dumps(summary), flush=True)
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
