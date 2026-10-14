"""Admit immutable GitHub delivery references, not foreign ledger copies."""
import hashlib
import json
from pathlib import Path
import subprocess

from .project_tracking import BOARD, _immutable, fingerprint, load

REPOSITORY = "mohammadksa856-bot/pixel-perfect-showcase-276"
LEDGER = "product-tracking/CHANGELOG.jsonl"
STATUS = "product-tracking/TRACK_STATUS.json"

def central_task_id(sender_task):
    if sender_task.startswith("DATA-02") or sender_task in {"BR-008", "BR-009", "BR-010", "BR-011"}:
        return "DATA-02"
    return sender_task if sender_task in {"P01-15", "R02", "P02"} else "P01"


def git_blob(repo, commit, path):
    return subprocess.check_output(["git", "cat-file", "blob", commit + ":" + path], cwd=repo)


def admit(root, repo, commit, *, source_branch='main-fz2efq', report_names=None):
    root = Path(root)
    ledger = git_blob(repo, commit, LEDGER)
    status_raw = git_blob(repo, commit, STATUS)
    events = [json.loads(line) for line in ledger.splitlines() if line.strip()]
    status = json.loads(status_raw)
    namespace = hashlib.sha256((REPOSITORY + ":" + LEDGER).encode()).hexdigest()[:16]
    old = [load(p) for p in (root / "docs/tracking/external_events").glob("*.json")]
    prefix = {item["external_id"]: item for item in old if item["external_id"].startswith(namespace + ":")}
    if any(item["source_event_sequence"] > len(events) for item in prefix.values()):
        raise ValueError("Remote sender ledger was truncated")
    pending = []
    runs = {run["id"]: run for run in status.get("test_runs", [])}
    for index, event in enumerate(events, 1):
        identity = namespace + ":" + str(index)
        digest = fingerprint(event)
        if identity in prefix:
            if prefix[identity]["source_event_sha256"] != digest:
                raise ValueError("Remote sender history changed")
            continue
        if not {"task", "event", "ts"} <= set(event):
            raise ValueError("Invalid remote ledger event")
        pending.append(dict(external_id=identity, source_event_sha256=digest,
                            source_event_sequence=index, sequence_basis="derived_line_order_not_sender_seq",
                            source_actor_claim=None, source_repository="https://github.com/" + REPOSITORY,
                            source_path=LEDGER, source_branch=source_branch, source_commit=event.get("commit"),
                            reviewed_source_head=commit, source_at=event["ts"], claim_type=event["event"],
                            sender_task_id=event["task"], central_task_id=central_task_id(event["task"]),
                            source_ledger_sha256=hashlib.sha256(ledger).hexdigest(),
                            referenced_runs=[dict(runs[event["run"]], verification="sender_reported_not_rerun")] if event.get("run") in runs else [],
                            review_state="ADMITTED_AS_REMOTE_EVIDENCE_ONLY", raw_event_copied=False,
                            code_accepted=False, tests_verified_here=False, integrated=False,
                            product_accepted=False, production_published=False))
    # Validate the full prefix before adding any receipt; never rewrite old evidence.
    for item in pending:
        _immutable(root / "docs/tracking/external_events" / (item["external_id"].replace(":", "-") + ".json"), item)
    reports = []
    for name in (report_names or ("BR-003.md", "BR-004.md", "P01-15_peer_comparison.md")):
        path = "product-tracking/reports/" + name
        raw = git_blob(repo, commit, path)
        digest = hashlib.sha256(raw).hexdigest()
        reference = "docs/tracking/external_reports/" + digest + ".json"
        receipt = dict(source_report_id=name, source_sha256=digest,
                                        source_path=path, source_repository=REPOSITORY,
                                        source_url="https://github.com/" + REPOSITORY + "/blob/" + commit + "/" + path,
                                        reviewed_source_head=commit, source_branch=source_branch,
                                        raw_report_copied=False, central_disposition="Sender evidence only; no independent financial accuracy or product acceptance")
        if not (root / reference).exists():
            _immutable(root / reference, receipt)
        reports.append(reference)
    board = load(root / BOARD)
    by_id = {t["id"]: t for t in board["tasks"]}
    definitions = {
        "DATA-02": dict(description="Review Claude data batches against current engine, bounded isolated merge and consumer verification", owner="Codex review / Claude Code sources", dependencies=["DATA-01", "B06"], parent_task_id="DATA-01"),
        "P02": dict(description="Company preview integration and acceptance, companion evidence required", owner="Codex review / Claude Code product", dependencies=["E01", "P01-15", "B06"], parent_task_id="P01"),
        "P01-15": dict(description="Claude peer comparison: code review and pending company page wiring", owner="Claude Code", dependencies=["P01", "R02"], parent_task_id="P01"),
        "O02": dict(description="Fail-closed staging/production API startup authentication", owner="Codex", dependencies=["B03"], parent_task_id="O01")}
    for task_id, definition in definitions.items():
        if task_id not in by_id:
            task = dict(id=task_id, **definition, priority=0, state="REVIEW", branch="main-fz2efq" if task_id == "P01-15" else "integration/engine-product-20261012",
                        commits=[], changed_files=[], test_runs=[], evidence=[], blockers=[], required_decisions=[],
                        change_stage="LOCAL_REVIEW", production_published=False)
            board["tasks"].append(task)
            by_id[task_id] = task
    for path in (root / "docs/tracking/external_events").glob("*.json"):
        item = load(path)
        if not item["external_id"].startswith(namespace + ":"):
            continue
        resolved_task = central_task_id(item["sender_task_id"])
        refs = by_id[resolved_task].setdefault("external_evidence", [])
        reference = path.relative_to(root).as_posix()
        if resolved_task != item["central_task_id"]:
            # Fix a coordinator link, never rewrite an immutable receipt or
            # blame the sender/source for our earlier namespace inference.
            link_path = root / "docs/tracking/external_links" / (item["external_id"].replace(":", "-") + "-" + resolved_task + ".json")
            _immutable(link_path, dict(external_id=item["external_id"], source_event_sha256=item["source_event_sha256"],
                original_receipt=reference, original_central_task=item["central_task_id"],
                corrected_central_task=resolved_task, kind="coordinator_namespace_correction_not_source_error",
                original_receipt_modified=False, original_sender_modified=False))
            link_ref=link_path.relative_to(root).as_posix()
            if link_ref not in refs:refs.append(link_ref)
            old_refs=by_id[item["central_task_id"]].get("external_evidence", [])
            if reference in old_refs:old_refs.remove(reference)
        if reference not in refs:
            refs.append(reference)
            refs.sort()
    result = dict(source_head=commit, source_repository=REPOSITORY, source_branch=source_branch,
                  ledger_sha256=hashlib.sha256(ledger).hexdigest(), status_sha256=hashlib.sha256(status_raw).hexdigest(),
                  new_events=len(pending), events_seen=len(events), report_refs=reports,
                  original_sender_writes=0, raw_ledger_copied=False, automatic_acceptance=False)
    board["execution_tracking"]["latest_Claude_cloud_admission"] = result
    (root / BOARD).write_text(json.dumps(board, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
