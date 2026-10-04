"""Offline guard for batch B012 (6014, 6015, 6070, 6090, 6002): page-transcript arithmetic, cross-filing agreement,
inventory sha links and audit-record structure. Reads only files in the repository; no network, no raw files."""
import importlib.util
import json
from pathlib import Path

import pytest

B = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B012"
INV = B.parent / "raw-coverage" / "companies"
spec = importlib.util.spec_from_file_location("check_transcripts_b012", B / "tools" / "check_transcripts.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BATCH = ["6014", "6015", "6070", "6090", "6002"]
DONE = sorted(p.stem for p in (B / "transcripts").glob("*.json"))
RECORDS = sorted(s for s in BATCH if (B / f"{s}.json").exists())


def test_something_audited():
    assert RECORDS


@pytest.mark.parametrize("symbol", DONE)
def test_transcript_identities(symbol):
    t, problems = mod.check(symbol)
    assert t["docs"]
    assert problems == []


@pytest.mark.parametrize("symbol", RECORDS)
def test_record_structure(symbol):
    rec = json.loads((B / f"{symbol}.json").read_text(encoding="utf8"))
    assert rec["symbol"] == symbol
    assert set(rec["dimensions"]) == {"value_correctness", "document_completeness", "company_coverage"}
    assert rec["unread_items"], "an audit record must list unread items explicitly"
    assert "NOT" in rec["conclusion"].upper()
    shas = {f["sha256"] for f in json.loads((INV / f"{symbol}.json").read_text(encoding="utf8"))["files"]}
    for d in rec["documents"]:
        assert d["sha256"] in shas and len(d["sha256"]) == 64


def test_progress_lists_every_company():
    p = json.loads((B / "progress.json").read_text(encoding="utf8"))
    assert set(p["status"]) == set(BATCH)
    for s, st in p["status"].items():
        assert st in ("done", "incomplete", "not_started")
        if st == "done":
            assert (B / f"{s}.json").exists()


def test_checker_detects_errors():
    good = {"label": "x", "period_end": "2025-12-31", "prior_end": "2024-12-31",
            "bs": {"cur": {"total_assets": 10, "total_liabilities": 4, "total_equity": 6}},
            "cf": {"cur": {"cfo": 5, "cfi": -2, "cff": -1, "net_change": 2, "cash_begin": 3, "fx": 0, "cash_end": 5}},
            "is": {"cur": {"net_income": 7, "ni_parent": 5, "ni_nci": 2}}}
    assert mod.identities(good) == []
    bad = json.loads(json.dumps(good))
    bad["bs"]["cur"]["total_assets"] = 11
    bad["cf"]["cur"]["cash_end"] = 6
    bad["is"]["cur"]["ni_nci"] = 1
    assert len(mod.identities(bad)) == 3
    a = {"label": "a", "period_end": "2025-12-31", "prior_end": "2024-12-31", "is": {"cur": {"revenue": 100}}}
    c = {"label": "c", "period_end": "2026-12-31", "prior_end": "2025-12-31", "is": {"prior": {"revenue": 95}}}
    assert len(mod.cross([a, c])) == 1
    c["is"]["prior"]["restated"] = True
    assert mod.cross([a, c]) == []
