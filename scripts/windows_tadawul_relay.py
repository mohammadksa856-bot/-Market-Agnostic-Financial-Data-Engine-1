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
import re
import subprocess
import time
from datetime import date
from pathlib import Path

from finengine.fetching import (
    BrowserFetcher,
    BrowserIssuerMonitor,
    _published_at_from_url,
)


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
DEFAULT_STATE = PROJECT / "output" / "local-relay" / "state.json"
DEFAULT_ARCHIVE = PROJECT / "output" / "local-relay" / "archive"
DEFAULT_LOG = PROJECT / "output" / "local-relay" / "relay.jsonl"


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


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


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


def _remote_publish(args, company: dict, candidate: dict,
                    local_path: Path) -> tuple[str, str]:
    digest = hashlib.sha256(local_path.read_bytes()).hexdigest()
    suffix = local_path.suffix.lower()
    remote_name = f"{company['symbol']}-{digest}{suffix}"
    remote_host_path = f"/tmp/finengine-relay/{remote_name}"
    container_file = f"/tmp/{remote_name}"
    container_manifest = f"/tmp/{remote_name}.json"
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
    _run(ssh + ["mkdir", "-p", "/tmp/finengine-relay"])
    _run(scp + [str(local_path), f"{args.server}:{remote_host_path}"])
    _run(ssh + ["docker", "cp", remote_host_path,
                f"{args.worker}:{container_file}"])
    archive_dir = f"/app/state/raw/SA/{company['symbol']}/documents"
    archive_file = f"{archive_dir}/{digest}{suffix}"
    _run(ssh + ["docker", "exec", args.worker, "mkdir", "-p", archive_dir])
    _run(ssh + ["docker", "cp", remote_host_path,
                f"{args.worker}:{archive_file}"])

    filed_at = _published_at_from_url(candidate["url"]) or date.today().isoformat()
    filing_type = BrowserIssuerMonitor._document_type(
        f"{candidate['title']} {candidate['url']}"
    )
    profile = "bank" if "bank" in str(company.get("industry") or "").lower() else (
        "insurance" if "insurance" in str(company.get("industry") or "").lower()
        else "corporate"
    )
    read = ssh + [
        "docker", "exec", args.worker, "finengine", "read", container_file,
        "SA", str(company["symbol"]), "--source-url", candidate["url"],
        "--filed-at", filed_at, "--filing-type", filing_type,
        "--profile", profile, "--out", container_manifest,
    ]
    period = _period_end(candidate["title"])
    if period:
        read += ["--period-end", period, "--fiscal-year", period[:4]]
    try:
        read_output = _run(read, attempts=1)
    except RuntimeError as error:
        detail = str(error)
        if ("verify ok=False" in detail or "wrote 0 facts" in detail or
                "could not infer the reporting year" in detail):
            return "review_required", detail
        raise
    ingest_output = _run(ssh + [
        "docker", "exec", args.worker, "finengine", "--db",
        "/app/state/financial.sqlite3", "ingest", "SA", str(company["symbol"]),
        "--file", container_manifest, "--raw-dir", "/app/state/raw",
    ], attempts=12)
    return "published", f"{read_output}\n{ingest_output}".strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-documents", type=int, default=5)
    parser.add_argument(
        "--crawl-issuer-site",
        action="store_true",
        help="Follow the official company website linked by Saudi Exchange.",
    )
    parser.add_argument("--registry", type=Path, default=PROJECT / "config" / "companies.json")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--edge", type=Path, default=DEFAULT_EDGE)
    parser.add_argument("--ssh-key", type=Path,
                        default=PROJECT / "output" / "github-actions-finengine-deploy")
    parser.add_argument("--known-hosts", type=Path,
                        default=PROJECT / "output" / "github-actions-known-hosts")
    parser.add_argument("--server", default="ubuntu@13.60.3.12")
    parser.add_argument("--worker", default="repo-worker-1")
    args = parser.parse_args()

    companies = [item for item in _load_json(args.registry, [])
                 if item.get("market") == "SA" and str(item.get("symbol") or "").isdigit()]
    if not companies:
        raise SystemExit("No Saudi companies found in registry")
    state = _load_json(args.state, {"cursor": 0, "seen": {}, "retry_symbols": []})
    cursor = int(state.get("cursor") or 0) % len(companies)
    seen = state.setdefault("seen", {})
    by_symbol = {str(item["symbol"]): item for item in companies}
    retry_set = {str(symbol) for symbol in state.get("retry_symbols", [])
                 if str(symbol) in by_symbol}
    batch = [by_symbol[symbol] for symbol in sorted(retry_set)]
    fresh_count = 0
    target_size = min(max(args.batch_size, 1), len(companies))
    while len(batch) < target_size and fresh_count < len(companies):
        company = companies[(cursor + fresh_count) % len(companies)]
        fresh_count += 1
        if str(company["symbol"]) not in {str(item["symbol"]) for item in batch}:
            batch.append(company)
    fetcher = LocalEdgeFetcher(args.archive, edge=args.edge, timeout_ms=90_000)
    summary = {"companies": 0, "candidates": 0, "published": 0,
               "duplicates": 0, "failures": 0}
    for company in batch:
        summary["companies"] += 1
        try:
            candidates: list[dict] = []
            candidate_urls: set[str] = set()
            discovery_errors: list[Exception] = []
            for source_url in _discovery_urls(company, args.crawl_issuer_site):
                remaining = args.max_documents - len(candidates)
                if remaining <= 0:
                    break
                try:
                    discovered = fetcher.discover(
                        source_url,
                        max_documents=remaining,
                        crawl_issuer_site=False,
                    )
                except Exception as error:
                    discovery_errors.append(error)
                    _log(args.log, {
                        "status": "source_failed",
                        "symbol": company["symbol"],
                        "source_url": source_url,
                        "error": f"{type(error).__name__}: {error}",
                    })
                    continue
                for candidate in discovered:
                    if candidate["url"] in candidate_urls:
                        continue
                    candidate_urls.add(candidate["url"])
                    candidates.append(candidate)
                    if len(candidates) >= args.max_documents:
                        break
            if not candidates and discovery_errors:
                raise discovery_errors[-1]
            summary["candidates"] += len(candidates)
            for candidate in candidates:
                if candidate["url"] in seen:
                    summary["duplicates"] += 1
                    continue
                content = fetcher.download_bytes(
                    candidate["url"], candidate.get("referer"),
                    candidate["content_type"],
                )
                digest = hashlib.sha256(content).hexdigest()
                suffix = ".xlsx" if "spreadsheet" in candidate["content_type"] else ".pdf"
                target = args.archive / "SA" / str(company["symbol"]) / f"{digest}{suffix}"
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_bytes(content)
                status, output = _remote_publish(args, company, candidate, target)
                seen[candidate["url"]] = {
                    "sha256": digest, "published_at": date.today().isoformat(),
                    "status": status,
                }
                if status == "published":
                    summary["published"] += 1
                else:
                    summary.setdefault("review_required", 0)
                    summary["review_required"] += 1
                _log(args.log, {"status": status, "symbol": company["symbol"],
                                "url": candidate["url"], "sha256": digest,
                                "detail": output[-2000:]})
            retry_set.discard(str(company["symbol"]))
        except Exception as error:
            summary["failures"] += 1
            retry_set.add(str(company["symbol"]))
            _log(args.log, {"status": "failed", "symbol": company["symbol"],
                            "error": f"{type(error).__name__}: {error}"})
    state["cursor"] = (cursor + fresh_count) % len(companies)
    state["retry_symbols"] = sorted(retry_set)
    state["last_run"] = date.today().isoformat()
    state["last_summary"] = summary
    _save_state(args.state, state)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not summary["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
