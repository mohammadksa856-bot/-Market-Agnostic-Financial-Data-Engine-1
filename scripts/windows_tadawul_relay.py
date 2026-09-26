"""Residential Saudi Exchange relay for Windows.

The Exchange blocks the AWS datacenter address but serves the same official
pages to the operator's normal Windows connection.  This bounded relay only
does source discovery and immutable download locally; extraction, validation
and publication remain on the production server.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

from finengine.fetching import (
    BrowserFetcher,
    BrowserIssuerMonitor,
    _published_at_from_url,
    _validate_document_bytes,
)
from finengine.relay_discovery import (
    DEFAULT_DISCOVERY_LIMIT_PER_SOURCE,
    gather_company_candidates,
    select_upload_candidates,
)
from build_sa_market_registry import (
    DEFAULT_OUTPUT as DEFAULT_MARKET_REGISTRY,
    DEFAULT_OVERRIDES as DEFAULT_COMPANY_OVERRIDES,
    DEFAULT_SEED as DEFAULT_MARKET_SEED,
    RegistryError,
    ensure_registry,
    validate_registry,
)


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
DEFAULT_STATE = PROJECT / "output" / "local-relay" / "state.json"
DEFAULT_ARCHIVE = PROJECT / "output" / "local-relay" / "archive"
DEFAULT_LOG = PROJECT / "output" / "local-relay" / "relay.jsonl"
DEFAULT_OUTBOX = PROJECT / "output" / "local-relay" / "outbox.json"
DEFAULT_LOCK = PROJECT / "output" / "local-relay" / "relay.lock"
OUTBOX_VERSION = 1


class RelayAlreadyRunning(RuntimeError):
    """Raised when another process owns the relay application lock."""


class SingleInstanceLock:
    """Hold an OS-backed, cross-process lock for one relay installation.

    The small metadata file intentionally remains after release.  Its presence
    is not the lock; the kernel lock on byte zero is.  Keeping the inode avoids
    the unlink/recreate race that can otherwise admit two Windows processes.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self._handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":  # pragma: no cover - exercised on relay host
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as error:
            handle.close()
            detail = ""
            with contextlib.suppress(OSError, UnicodeDecodeError):
                detail = self.path.read_text(encoding="utf-8").strip()
            suffix = f" ({detail})" if detail else ""
            raise RelayAlreadyRunning(
                f"another Windows Saudi relay instance is running{suffix}"
            ) from error
        self._handle = handle
        metadata = {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "started_at": _utc_now(),
        }
        handle.seek(0)
        handle.truncate()
        handle.write((json.dumps(metadata, sort_keys=True) + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
        handle.seek(0)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._handle is None:
            return
        handle = self._handle
        self._handle = None
        handle.seek(0)
        if os.name == "nt":  # pragma: no cover - exercised on relay host
            import msvcrt

            with contextlib.suppress(OSError):
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


class LocalEdgeFetcher(BrowserFetcher):
    def __init__(self, *args, edge: Path = DEFAULT_EDGE, **kwargs):
        super().__init__(*args, **kwargs)
        self.edge = edge

    def _context(self, stack):
        from playwright.sync_api import sync_playwright

        if not self.edge.exists():
            raise FileNotFoundError(f"Microsoft Edge not found: {self.edge}")
        pw = stack.enter_context(sync_playwright())
        browser = pw.chromium.launch(
            executable_path=str(self.edge),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        stack.callback(browser.close)
        return browser.new_context(
            accept_downloads=True,
            locale="en-US",
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )


def _run(command: list[str], attempts: int = 3, timeout: int = 120) -> str:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            last_error = RuntimeError(
                f"command timed out after {timeout}s: {' '.join(command[:2])}"
            )
            if attempt < attempts:
                time.sleep(5 * attempt)
            continue
        if result.returncode == 0:
            return result.stdout.strip()
        last_error = RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command[:2])}: "
            f"{(result.stderr + result.stdout).strip()[-2000:]}"
        )
        if attempt < attempts:
            time.sleep(5 * attempt)
    raise last_error


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _save_json(path: Path, value: dict) -> None:
    """Atomically and durably replace one relay checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _save_state(path: Path, state: dict) -> None:
    _save_json(path, state)


def _load_outbox(path: Path) -> dict:
    """Load the durable archive-to-enqueue hand-off without silent data loss."""
    if not path.exists():
        return {"version": OUTBOX_VERSION, "documents": {}}
    try:
        outbox = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"cannot read durable relay outbox {path}: {error}") from error
    if not isinstance(outbox, dict) or outbox.get("version") != OUTBOX_VERSION:
        raise RuntimeError(
            f"unsupported relay outbox schema in {path}; expected version "
            f"{OUTBOX_VERSION}"
        )
    documents = outbox.get("documents")
    if not isinstance(documents, dict):
        raise RuntimeError(f"relay outbox documents must be an object: {path}")
    for entry_id, entry in documents.items():
        if not isinstance(entry_id, str) or not isinstance(entry, dict):
            raise RuntimeError(f"invalid relay outbox entry in {path}: {entry_id!r}")
    return outbox


def _save_outbox(path: Path, outbox: dict) -> None:
    outbox["version"] = OUTBOX_VERSION
    outbox["updated_at"] = _utc_now()
    _save_json(path, outbox)


def _log(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _profile_url(company: dict) -> str:
    profile = "company-profile-nomu-parallel" if (
        "parallel" in str(company.get("exchange") or "").lower()
        or "nomu" in str(company.get("exchange") or "").lower()
    ) else "company-profile-main"
    return (
        "https://www.saudiexchange.sa/wps/portal/saudiexchange/ourmarkets/"
        f"main-market-watch/{profile}?companySymbol={company['symbol']}"
    )


def _discovery_urls(company: dict, include_issuer_sources: bool) -> list[str]:
    urls: list[str] = []
    if include_issuer_sources:
        for source in company.get("sources") or []:
            url = source.get("url") if isinstance(source, dict) else source
            if isinstance(url, str) and url.startswith("https://") and url not in urls:
                urls.append(url)
    profile = _profile_url(company)
    if profile not in urls:
        urls.append(profile)
    return urls


def _period_end(title: str) -> str | None:
    match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", title)
    if match:
        try:
            return date(*(int(value) for value in match.groups())).isoformat()
        except ValueError:
            return None
    year_match = re.search(r"\b(20\d{2})\b", title)
    if not year_match:
        return None
    year = int(year_match.group(1))
    lowered = title.lower()
    if re.search(r"\b(?:q1|first quarter)\b", lowered):
        return f"{year}-03-31"
    if re.search(r"\b(?:q2|second quarter|half year|six months)\b", lowered):
        return f"{year}-06-30"
    if re.search(r"\b(?:q3|third quarter|nine months)\b", lowered):
        return f"{year}-09-30"
    if re.search(r"\b(?:q4|fourth quarter|annual|year ended|year ending)\b", lowered):
        return f"{year}-12-31"
    return None


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_local_archive(record: dict) -> bool:
    path = Path(str(record.get("local_path") or ""))
    digest = str(record.get("sha256") or "")
    byte_size = record.get("byte_size")
    if not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return False
    try:
        if byte_size is not None and path.stat().st_size != int(byte_size):
            return False
        return _sha256_path(path) == digest
    except (OSError, TypeError, ValueError):
        return False


def _write_local_immutable(path: Path, content: bytes, digest: str) -> bool:
    """Write a content-addressed local file once and verify its identity."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if _sha256_path(path) != digest:
            raise RuntimeError(f"immutable local archive collision: {path}")
        return False
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
    if _sha256_path(path) != digest:
        raise RuntimeError(f"local archive verification failed: {path}")
    return True


def _connection_commands(args) -> tuple[list[str], list[str]]:
    connection_options = [
        "-o", f"UserKnownHostsFile={args.known_hosts}",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        "-o", "ConnectionAttempts=1",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=2",
    ]
    ssh = ["ssh", "-i", str(args.ssh_key), *connection_options, args.server]
    scp = ["scp", "-i", str(args.ssh_key), *connection_options]
    return ssh, scp


def _ssh_run(ssh: list[str], command: list[str], *, attempts: int = 3,
             timeout: int = 120) -> str:
    # OpenSSH joins arguments after the host into one remote shell command.
    return _run(ssh + [shlex.join(command)], attempts=attempts, timeout=timeout)


def _remote_digest(ssh: list[str], args, path: str) -> str | None:
    try:
        output = _ssh_run(
            ssh,
            ["docker", "exec", args.worker, "sha256sum", "--", path],
            attempts=1,
        )
    except RuntimeError:
        return None
    digest = output.split(maxsplit=1)[0] if output else ""
    return digest if re.fullmatch(r"[0-9a-f]{64}", digest) else None


def _remote_archive(args, record: dict) -> str:
    """Copy one verified local artifact into content-addressed AWS raw storage.

    Returns ``created`` or ``existing``.  The final container path is never
    overwritten: a temporary is moved with ``mv -n`` and the resulting digest
    is verified before the outbox may advance to ``pending_enqueue``.
    """
    if not _verify_local_archive(record):
        raise RuntimeError(
            f"local archive is missing or corrupt: {record.get('local_path')}"
        )
    digest = str(record["sha256"])
    local_path = Path(record["local_path"])
    remote_archive_path = str(record["remote_archive_path"])
    archive_dir = remote_archive_path.rsplit("/", 1)[0]
    suffix = local_path.suffix.lower()
    remote_name = f"{record['symbol']}-{digest}{suffix}"
    remote_host_path = f"/tmp/finengine-relay/{remote_name}"
    remote_temporary = f"{archive_dir}/.{digest}.{os.getpid()}.relay-tmp{suffix}"
    ssh, scp = _connection_commands(args)
    _ssh_run(ssh, ["docker", "exec", args.worker, "mkdir", "-p", archive_dir])
    existing = _remote_digest(ssh, args, remote_archive_path)
    if existing is not None:
        if existing != digest:
            raise RuntimeError(
                f"immutable AWS archive collision at {remote_archive_path}: "
                f"expected {digest}, found {existing}"
            )
        return "existing"
    _ssh_run(ssh, ["mkdir", "-p", "/tmp/finengine-relay"])
    try:
        _run(scp + [str(local_path), f"{args.server}:{remote_host_path}"])
        host_output = _ssh_run(ssh, ["sha256sum", "--", remote_host_path])
        host_digest = host_output.split(maxsplit=1)[0] if host_output else ""
        if host_digest != digest:
            raise RuntimeError(
                f"AWS staging verification failed: expected {digest}, "
                f"found {host_digest or 'no digest'}"
            )
        _ssh_run(
            ssh,
            ["docker", "cp", remote_host_path,
             f"{args.worker}:{remote_temporary}"],
        )
        install_script = 'mv -n -- "$1" "$2"; rm -f -- "$1"'
        _ssh_run(
            ssh,
            ["docker", "exec", args.worker, "sh", "-c", install_script,
             "relay-install", remote_temporary, remote_archive_path],
        )
        archived_digest = _remote_digest(ssh, args, remote_archive_path)
        if archived_digest != digest:
            raise RuntimeError(
                f"AWS archive verification failed at {remote_archive_path}: "
                f"expected {digest}, found {archived_digest or 'no digest'}"
            )
    finally:
        with contextlib.suppress(RuntimeError):
            _ssh_run(
                ssh, ["rm", "-f", "--", remote_host_path],
                attempts=1, timeout=30,
            )
    return "created"


def _parse_enqueue_result(output: str) -> tuple[str, dict]:
    try:
        result = json.loads(output)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"relay enqueue returned invalid JSON: {output[-2000:]}"
        ) from error
    status = str(result.get("status") or "")
    queued = result.get("queued")
    if status == "queued" and queued is True:
        return "job_created", result
    if status == "duplicate_job" and queued is False:
        return "duplicate_job", result
    if status == "duplicate" and queued is False:
        return "published_duplicate", result
    raise RuntimeError(
        "unexpected relay enqueue result or inconsistent queued flag: "
        f"{output[-2000:]}"
    )


def _remote_enqueue(args, record: dict) -> tuple[str, dict]:
    ssh, _ = _connection_commands(args)
    enqueue_command = [
        "docker", "exec", args.worker, "finengine", "--db",
        "/app/state/financial.sqlite3", "relay-enqueue",
        str(record["remote_archive_path"]), str(record["market"]),
        str(record["symbol"]), "--source-url", str(record["source_url"]),
        "--filed-at", str(record["filed_at"]),
        "--filing-type", str(record["filing_type"]),
        "--title", str(record.get("title") or ""),
        "--raw-dir", "/app/state/raw",
    ]
    return _parse_enqueue_result(_ssh_run(ssh, enqueue_command))


def _entry_urls(record: dict) -> set[str]:
    urls = {str(record.get("source_url") or "")}
    urls.update(str(url) for url in record.get("source_urls") or [])
    urls.discard("")
    return urls


def _entry_for_url(outbox: dict, url: str) -> tuple[str, dict] | None:
    for entry_id, record in outbox["documents"].items():
        if url in _entry_urls(record):
            return entry_id, record
    return None


def _candidate_is_durable(outbox: dict, url: str) -> bool:
    found = _entry_for_url(outbox, url)
    if found is None:
        return False
    _, record = found
    if record.get("status") == "pending_archive":
        return _verify_local_archive(record)
    return record.get("status") in {
        "pending_enqueue", "job_created", "duplicate_job",
        "published_duplicate",
    }


def _outbox_record(company: dict, candidate: dict, local_path: Path,
                   digest: str, content: bytes) -> dict:
    content_type = str(candidate.get("content_type") or "application/pdf")
    suffix = local_path.suffix.lower()
    source_url = str(candidate["url"])
    title = str(candidate.get("title") or "")
    symbol = str(company["symbol"])
    now = _utc_now()
    return {
        "market": "SA",
        "symbol": symbol,
        "sha256": digest,
        "byte_size": len(content),
        "content_type": content_type,
        "local_path": str(local_path.resolve()),
        "remote_archive_path": (
            f"/app/state/raw/SA/{symbol}/documents/{digest}{suffix}"
        ),
        "source_url": source_url,
        "source_urls": [source_url],
        "source_page": candidate.get("referer"),
        "title": title,
        "filed_at": (
            _published_at_from_url(source_url) or date.today().isoformat()
        ),
        "filing_type": BrowserIssuerMonitor._document_type(
            f"{title} {source_url}"
        ),
        "discovered_at": now,
        "local_archived_at": now,
        "remote_archived_at": None,
        "status": "pending_archive",
        "archive_attempts": 0,
        "enqueue_attempts": 0,
        "last_archive_error": None,
        "last_enqueue_error": None,
        "enqueue_result": None,
        "updated_at": now,
    }


def _new_summary() -> dict:
    return {
        "companies": 0,
        "candidates": 0,
        "already_archived": 0,
        "content_duplicates": 0,
        "downloads": 0,
        "local_archived": 0,
        "local_reused": 0,
        "aws_archived": 0,
        "aws_reused": 0,
        "job_created": 0,
        "duplicate_job": 0,
        "published_duplicate": 0,
        "source_failures": 0,
        "download_failures": 0,
        "local_archive_failures": 0,
        "archive_failures": 0,
        "enqueue_failures": 0,
        "company_failures": 0,
    }


def _mark_seen(state: dict, record: dict, status: str) -> None:
    seen = state.setdefault("seen", {})
    for url in _entry_urls(record):
        seen[url] = {
            "sha256": record["sha256"],
            "archived_at": record.get("remote_archived_at"),
            "status": status,
        }


def _attempt_remote_archive(args, outbox: dict, entry_id: str,
                            summary: dict, state: dict | None = None) -> bool:
    record = outbox["documents"][entry_id]
    record["archive_attempts"] = int(record.get("archive_attempts") or 0) + 1
    record["updated_at"] = _utc_now()
    _save_outbox(args.outbox, outbox)
    try:
        disposition = _remote_archive(args, record)
    except Exception as error:
        record["last_archive_error"] = f"{type(error).__name__}: {error}"
        record["updated_at"] = _utc_now()
        _save_outbox(args.outbox, outbox)
        summary["archive_failures"] += 1
        _log(args.log, {
            "status": "archive_failed",
            "symbol": record["symbol"],
            "url": record["source_url"],
            "sha256": record["sha256"],
            "error": record["last_archive_error"],
        })
        return False
    record["status"] = "pending_enqueue"
    record["remote_archived_at"] = record.get("remote_archived_at") or _utc_now()
    record["last_archive_error"] = None
    record["updated_at"] = _utc_now()
    _save_outbox(args.outbox, outbox)
    summary["aws_archived" if disposition == "created" else "aws_reused"] += 1
    if state is not None:
        _mark_seen(state, record, "raw_archived")
        _save_state(args.state, state)
    _log(args.log, {
        "status": "raw_archived",
        "archive_disposition": disposition,
        "symbol": record["symbol"],
        "url": record["source_url"],
        "sha256": record["sha256"],
        "remote_archive_path": record["remote_archive_path"],
    })
    return True


def _retry_pending_archives(args, outbox: dict, summary: dict,
                            state: dict | None = None) -> set[str]:
    failed_symbols: set[str] = set()
    for entry_id in sorted(outbox["documents"]):
        record = outbox["documents"][entry_id]
        if record.get("status") == "pending_archive":
            if not _attempt_remote_archive(
                    args, outbox, entry_id, summary, state):
                failed_symbols.add(str(record.get("symbol") or ""))
    failed_symbols.discard("")
    return failed_symbols


def _enqueue_pending(args, outbox: dict, summary: dict) -> None:
    processed = 0
    enqueue_limit = max(int(getattr(args, "enqueue_limit", 0) or 0), 0)
    for entry_id in sorted(outbox["documents"]):
        record = outbox["documents"][entry_id]
        if record.get("status") != "pending_enqueue":
            continue
        if enqueue_limit and processed >= enqueue_limit:
            break
        processed += 1
        record["enqueue_attempts"] = int(record.get("enqueue_attempts") or 0) + 1
        record["last_enqueue_attempt_at"] = _utc_now()
        record["updated_at"] = _utc_now()
        _save_outbox(args.outbox, outbox)
        try:
            status, result = _remote_enqueue(args, record)
        except Exception as error:
            record["last_enqueue_error"] = f"{type(error).__name__}: {error}"
            record["updated_at"] = _utc_now()
            _save_outbox(args.outbox, outbox)
            summary["enqueue_failures"] += 1
            _log(args.log, {
                "status": "enqueue_failed",
                "symbol": record["symbol"],
                "url": record["source_url"],
                "sha256": record["sha256"],
                "remote_archive_path": record["remote_archive_path"],
                "error": record["last_enqueue_error"],
            })
            continue
        record["status"] = status
        record["last_enqueue_error"] = None
        record["enqueue_result"] = result
        record["enqueued_at"] = _utc_now()
        record["updated_at"] = _utc_now()
        _save_outbox(args.outbox, outbox)
        summary[status] += 1
        _log(args.log, {
            "status": status,
            "symbol": record["symbol"],
            "url": record["source_url"],
            "sha256": record["sha256"],
            "detail": result,
        })


def _load_companies(args) -> list[dict]:
    if args.registry.resolve() == DEFAULT_MARKET_REGISTRY.resolve():
        try:
            ensure_registry(args.registry, args.registry_seed, args.registry_overrides)
        except RegistryError as error:
            raise SystemExit(f"Invalid Saudi relay registry: {error}") from error
    loaded_registry = _load_json(args.registry, [])
    try:
        validate_registry(loaded_registry)
    except RegistryError as error:
        raise SystemExit(f"Invalid Saudi relay registry: {error}") from error
    companies = [
        item for item in loaded_registry
        if item.get("market") == "SA" and str(item.get("symbol") or "").isdigit()
    ]
    requested_symbols = {
        value.strip() for value in str(args.symbols or "").split(",")
        if value.strip()
    }
    if requested_symbols:
        companies = [
            item for item in companies
            if str(item.get("symbol")) in requested_symbols
        ]
        missing = requested_symbols - {str(item["symbol"]) for item in companies}
        if missing:
            raise SystemExit(f"Unknown Saudi symbols: {', '.join(sorted(missing))}")
    if not companies:
        raise SystemExit("No Saudi companies found in registry")
    return companies


def _archive_companies(args, companies: list[dict], state: dict, outbox: dict,
                       fetcher, summary: dict) -> None:
    """Stage 1: discover, verify, and archive raw files without touching DB."""
    failed_symbols = _retry_pending_archives(args, outbox, summary, state)
    cursor = int(state.get("cursor") or 0) % len(companies)
    seen = state.setdefault("seen", {})
    by_symbol = {str(item["symbol"]): item for item in companies}
    retry_set = {
        str(symbol) for symbol in state.get("retry_symbols", [])
        if str(symbol) in by_symbol
    }
    retry_set.update(symbol for symbol in failed_symbols if symbol in by_symbol)
    batch = [by_symbol[symbol] for symbol in sorted(retry_set)]
    fresh_count = 0
    target_size = min(max(args.batch_size, 1), len(companies))
    while len(batch) < target_size and fresh_count < len(companies):
        company = companies[(cursor + fresh_count) % len(companies)]
        fresh_count += 1
        if str(company["symbol"]) not in {
                str(item["symbol"]) for item in batch}:
            batch.append(company)

    for company in batch:
        symbol = str(company["symbol"])
        summary["companies"] += 1
        company_failed = symbol in failed_symbols
        try:
            discovery = gather_company_candidates(
                fetcher,
                company,
                _profile_url(company),
                args.crawl_issuer_site,
                max_candidates_per_source=args.max_discovered_per_source,
            )
            for failure in discovery.source_failures:
                _log(args.log, {
                    "status": "source_failed",
                    "symbol": symbol,
                    "source_url": failure.source_url,
                    "error": f"{type(failure.error).__name__}: {failure.error}",
                })
            summary["discovered"] = (
                summary.get("discovered", 0) + len(discovery.candidates)
            )
            summary["source_failures"] += len(discovery.source_failures)
            candidates = select_upload_candidates(
                discovery.candidates,
                args.max_documents,
                seen=seen,
                outbox=outbox,
            )
            company_failed = company_failed or discovery.needs_retry
            summary["candidates"] += len(candidates)
            for candidate in candidates:
                url = str(candidate["url"])
                if url in seen or _candidate_is_durable(outbox, url):
                    summary["already_archived"] += 1
                    continue
                try:
                    content_type = str(
                        candidate.get("content_type") or "application/pdf"
                    )
                    content = fetcher.download_bytes(
                        url,
                        candidate.get("referer"),
                        content_type,
                    )
                    _validate_document_bytes(content, url, content_type)
                    summary["downloads"] += 1
                except Exception as error:
                    company_failed = True
                    summary["download_failures"] += 1
                    _log(args.log, {
                        "status": "download_failed",
                        "symbol": symbol,
                        "url": url,
                        "error": f"{type(error).__name__}: {error}",
                    })
                    continue
                digest = hashlib.sha256(content).hexdigest()
                suffix = ".xlsx" if "spreadsheet" in content_type else ".pdf"
                target = args.archive / "SA" / symbol / f"{digest}{suffix}"
                try:
                    created = _write_local_immutable(target, content, digest)
                except Exception as error:
                    company_failed = True
                    summary["local_archive_failures"] += 1
                    _log(args.log, {
                        "status": "local_archive_failed",
                        "symbol": symbol,
                        "url": url,
                        "sha256": digest,
                        "error": f"{type(error).__name__}: {error}",
                    })
                    continue
                summary["local_archived" if created else "local_reused"] += 1
                entry_id = f"SA:{symbol}:{digest}"
                existing = outbox["documents"].get(entry_id)
                if existing is not None:
                    source_urls = _entry_urls(existing)
                    source_urls.add(url)
                    existing["source_urls"] = sorted(source_urls)
                    existing["local_path"] = str(target.resolve())
                    existing["byte_size"] = len(content)
                    existing["updated_at"] = _utc_now()
                    _save_outbox(args.outbox, outbox)
                    summary["content_duplicates"] += 1
                    if existing.get("status") == "pending_archive":
                        if not _attempt_remote_archive(
                                args, outbox, entry_id, summary, state):
                            company_failed = True
                    elif existing.get("status") in {
                            "pending_enqueue", "job_created", "duplicate_job",
                            "published_duplicate"}:
                        _mark_seen(state, existing, str(existing["status"]))
                        _save_state(args.state, state)
                    continue
                record = _outbox_record(
                    company, candidate, target, digest, content
                )
                outbox["documents"][entry_id] = record
                # This checkpoint is the stage boundary: local verified bytes
                # are now durable even if SSH/AWS is unavailable immediately.
                _save_outbox(args.outbox, outbox)
                _save_state(args.state, state)
                if not _attempt_remote_archive(
                        args, outbox, entry_id, summary, state):
                    company_failed = True
            if company_failed:
                retry_set.add(symbol)
            else:
                retry_set.discard(symbol)
        except Exception as error:
            company_failed = True
            retry_set.add(symbol)
            _log(args.log, {
                "status": "company_failed",
                "symbol": symbol,
                "error": f"{type(error).__name__}: {error}",
            })
        if company_failed:
            failed_symbols.add(symbol)

    summary["company_failures"] = len(failed_symbols)
    state["cursor"] = (cursor + fresh_count) % len(companies)
    state["retry_symbols"] = sorted(retry_set)
    state["last_run"] = _utc_now()
    state["last_archive_summary"] = summary.copy()
    _save_state(args.state, state)


def _outbox_status_counts(outbox: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in outbox["documents"].values():
        status = str(record.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _execute(args, *, fetcher_factory=LocalEdgeFetcher) -> tuple[int, dict]:
    outbox = _load_outbox(args.outbox)
    summary = _new_summary()
    if args.stage in {"archive", "all"}:
        companies = _load_companies(args)
        state = _load_json(
            args.state, {"cursor": 0, "seen": {}, "retry_symbols": []}
        )
        fetcher = fetcher_factory(
            args.archive,
            edge=args.edge,
            timeout_ms=max(args.timeout_seconds, 5) * 1000,
        )
        _archive_companies(args, companies, state, outbox, fetcher, summary)
    if args.stage in {"enqueue", "all"}:
        _enqueue_pending(args, outbox, summary)
    summary["outbox"] = _outbox_status_counts(outbox)
    if args.stage in {"archive", "all"}:
        archive_failed = any(summary[key] for key in (
            "source_failures", "download_failures", "local_archive_failures",
            "archive_failures",
        ))
        # Enqueue is deliberately a separate, retriable stage.  An unavailable
        # SQLite DB must not turn a completed raw-archive stage into a failure.
        return (1 if archive_failed else 0), summary
    return (1 if summary["enqueue_failures"] else 0), summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", choices=("archive", "enqueue", "all"), default="all",
        help=(
            "archive stores verified raw files; enqueue consumes only the "
            "durable outbox; all runs both while keeping their failure domains "
            "separate"
        ),
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-documents", type=int, default=5)
    parser.add_argument(
        "--max-discovered-per-source",
        type=int,
        default=DEFAULT_DISCOVERY_LIMIT_PER_SOURCE,
        help="Bounded scan depth per official source before upload selection.",
    )
    parser.add_argument(
        "--enqueue-limit", type=int, default=200,
        help="Maximum pending outbox entries attempted by one enqueue stage (0=all).",
    )
    parser.add_argument("--timeout-seconds", type=int, default=90)
    parser.add_argument(
        "--symbols",
        help="Comma-separated Saudi symbols for a bounded pilot run.",
    )
    parser.add_argument(
        "--crawl-issuer-site",
        action="store_true",
        help="Follow the official company website linked by Saudi Exchange.",
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_MARKET_REGISTRY)
    parser.add_argument("--registry-seed", type=Path, default=DEFAULT_MARKET_SEED)
    parser.add_argument("--registry-overrides", type=Path,
                        default=DEFAULT_COMPANY_OVERRIDES)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--edge", type=Path, default=DEFAULT_EDGE)
    parser.add_argument("--ssh-key", type=Path,
                        default=PROJECT / "output" / "github-actions-finengine-deploy")
    parser.add_argument("--known-hosts", type=Path,
                        default=PROJECT / "output" / "github-actions-known-hosts")
    parser.add_argument("--server", default="ubuntu@13.60.3.12")
    parser.add_argument("--worker", default="repo-worker-1")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        with SingleInstanceLock(args.lock):
            exit_code, summary = _execute(args)
    except RelayAlreadyRunning as error:
        print(json.dumps({"status": "already_running", "error": str(error)}),
              file=sys.stderr)
        return 3
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
