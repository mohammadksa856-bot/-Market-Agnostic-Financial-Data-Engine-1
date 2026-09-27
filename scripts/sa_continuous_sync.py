#!/usr/bin/env python3
"""Quietly sync new Claude-collected Saudi statements to AWS in batches."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import build_sa_bulk_bundle as bundle
import sa_raw_statement_collector as collector


CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def run(command: list[str], *, cwd: Path, timeout: int | None = None):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, creationflags=CREATE_NO_WINDOW)


def ssh_command(args, remote: str, *, timeout: int = 60):
    return run([
        args.ssh, "-i", args.ssh_key,
        "-o", f"UserKnownHostsFile={args.known_hosts}",
        "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
        args.server, remote,
    ], cwd=Path(args.project), timeout=timeout)


def sync_once(args, state: dict) -> dict:
    root = Path(args.root)
    project = Path(args.project)
    done = set(state.get("done", []))
    documents = collector._collector_documents(root)
    if not state.get("initialized"):
        cutoff = Path(args.baseline_bundle).stat().st_mtime if args.baseline_bundle else time.time()
        for document in documents:
            path = Path(str(document.get("local_path") or ""))
            if path.is_file() and path.stat().st_mtime <= cutoff:
                done.add(str(document.get("content_hash") or ""))
        state.update({"initialized": True, "baseline_at": cutoff, "done": sorted(done)})
        save(Path(args.state), state)

    candidates = [d for d in documents
                  if d.get("bucket") == "statement"
                  and d.get("content_hash") not in done]
    if not candidates:
        state["last_scan_at"] = datetime.now(timezone.utc).isoformat()
        save(Path(args.state), state)
        return {"status": "idle", "new": 0}

    busy = ssh_command(
        args,
        "docker top repo-worker-1 -eo args | grep -q '[s]a-bulk/ingest.py'",
    )
    if busy.returncode == 0:
        return {"status": "ingest_busy", "new": len(candidates)}
    if busy.returncode not in {0, 1}:
        state["last_error"] = (busy.stderr or busy.stdout)[-1000:]
        save(Path(args.state), state)
        return {"status": "server_check_failed", "new": len(candidates)}

    for stale in (root / "state").glob("sa-delta-*.tar"):
        stale.unlink(missing_ok=True)
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = root / "state" / f"sa-delta-{batch_id}.tar"
    result = bundle.build(root, archive, done)
    if not result["documents"]:
        return {"status": "idle", "new": 0}

    remote_file = "/tmp/sa-delta-current.tar"
    prepare = ssh_command(args, f"touch {remote_file}")
    if prepare.returncode:
        state["last_error"] = (prepare.stderr or prepare.stdout)[-1000:]
        save(Path(args.state), state)
        return {"status": "upload_prepare_failed", "new": result["documents"]}
    with tempfile.NamedTemporaryFile("w", suffix=".sftp", encoding="utf-8",
                                     delete=False) as batch:
        batch.write(f'reput "{archive.as_posix()}" {remote_file}\n')
        batch_path = Path(batch.name)
    try:
        upload = run([
            args.sftp, "-b", str(batch_path), "-i", args.ssh_key,
            "-o", f"UserKnownHostsFile={args.known_hosts}",
            "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", args.server,
        ], cwd=project, timeout=args.transfer_timeout)
    finally:
        batch_path.unlink(missing_ok=True)
    if upload.returncode:
        state["last_error"] = (upload.stderr or upload.stdout)[-1000:]
        save(Path(args.state), state)
        return {"status": "upload_failed", "new": result["documents"]}

    remote = (
        "docker top repo-worker-1 -eo args | grep -q '[s]a-bulk/ingest.py' && exit 75; "
        "cat /tmp/sa-delta-current.tar | docker exec -i repo-worker-1 tar -xf - -C /app/state && "
        "rm -f /tmp/sa-delta-current.tar && "
        "docker exec repo-worker-1 python /app/state/sa-bulk/ingest.py "
        "--manifest /app/state/sa-bulk/manifest.jsonl "
        "--checkpoint /app/state/sa-bulk/checkpoint.json "
        "--database /app/state/financial.sqlite3 "
        "--registry /app/state/sa-bulk/registry.json"
    )
    ingest = ssh_command(args, remote, timeout=args.ingest_timeout)
    if ingest.returncode:
        state["last_error"] = (ingest.stderr or ingest.stdout)[-1000:]
        save(Path(args.state), state)
        return {"status": "ingest_deferred" if ingest.returncode == 75 else "ingest_failed",
                "new": result["documents"]}

    new_hashes = {d["content_hash"] for d in candidates}
    done.update(new_hashes)
    state.update({"done": sorted(done), "last_success_at": datetime.now(timezone.utc).isoformat(),
                  "last_batch": batch_id, "last_documents": result["documents"],
                  "last_error": ""})
    save(Path(args.state), state)
    archive.unlink(missing_ok=True)
    return {"status": "synced", "new": result["documents"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--server", default="ubuntu@13.60.3.12")
    parser.add_argument("--ssh-key", required=True)
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--baseline-bundle")
    parser.add_argument("--state", required=True)
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--transfer-timeout", type=int, default=7200)
    parser.add_argument("--ingest-timeout", type=int, default=7200)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--sftp", default=r"C:\Windows\System32\OpenSSH\sftp.exe")
    parser.add_argument("--ssh", default=r"C:\Windows\System32\OpenSSH\ssh.exe")
    args = parser.parse_args()
    state = load(Path(args.state), {})
    while True:
        try:
            result = sync_once(args, state)
            state["last_result"] = result
            save(Path(args.state), state)
        except Exception as exc:
            state["last_error"] = repr(exc)
            save(Path(args.state), state)
        if args.once:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
