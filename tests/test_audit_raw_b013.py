"""Offline guard for batch B013 (6017, 6018, 6016, 6004, 6012): page-transcript arithmetic, cross-filing agreement,
inventory sha links and audit-record structure. Reads only files in the repository; no network, no raw files."""
import importlib.util
import json
from pathlib import Path

import pytest

B013 = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B013"
INV = B013.parent / "raw-coverage" / "companies"
spec = importlib.util.spec_from_file_location("check_transcripts_b013", B013 / "tools" / "check_transcripts.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BATCH = ["6017", "6018", "6016", "6004", "6012"]
DONE = sorted(p.stem for p in (B013 / "transcripts").glob("*.json"))
RECORDS = sorted(s for s in BATCH if (B013 / f"{s}.json").exists())


def test_something_audited():
    assert RECORDS


@pytest.mark.parametrize("symbol", DONE)
def test_transcript_identities(symbol):
    t, problems = mod.check(symbol)
    assert t["docs"]
    assert problems == []


@pytest.mark.parametrize("symbol", RECORDS)
def test_record_structure(symbol):
    rec = json.loads((B013 / f"{symbol}.json").read_text(encoding="utf8"))
    assert rec["symbol"] == symbol
    dims = rec["dimensions"]
    assert set(dims) == {"value_correctness", "document_completeness", "company_coverage"}
    assert rec["unread_items"], "an audit record must list unread items explicitly"
    assert "NOT" in rec["conclusion"].upper() or "not claimed" in rec["conclusion"].lower()
    inv = json.loads((INV / f"{symbol}.json").read_text(encoding="utf8"))
    shas = {f["sha256"] for f in inv["files"]}
    for d in rec["documents"]:
        assert d["sha256"] in shas, "audited document must carry the full sha256 present in the inventory"
        assert len(d["sha256"]) == 64


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
    b = {"label": "b", "period_end": "2024-12-31", "prior_end": "2023-12-31", "is": {"cur": {"revenue": 90}}}
    c = {"label": "c", "period_end": "2025-12-31", "prior_end": "2024-12-31", "is": {"prior": {"revenue": 95}, "cur": {"revenue": 100}}}
    assert mod.cross([a, b]) == []
    assert mod.cross([a, c]) == [] and len(mod.cross([b, c])) == 1
    c["is"]["prior"]["restated"] = True
    assert mod.cross([b, c]) == []


def test_declared_difference_is_allowed_only_when_written():
    a = {"label": "a", "period_end": "2025-12-31", "prior_end": "2024-12-31", "is": {"cur": {"operating_income": 10}}}
    b = {"label": "b", "period_end": "2025-12-31", "prior_end": "2024-12-31", "is": {"cur": {"operating_income": 12}}}
    assert len(mod.cross([a, b])) == 1
    b["is"]["cur"]["_declared_diff"] = {"operating_income": "rounding in the annual-report copy"}
    assert mod.cross([a, b]) == []


def test_roll_check_detects_mismatch():
    t = {"docs": [{"sha256_prefix": "aa", "is": {"cur": {"revenue": 10}}}, {"sha256_prefix": "bb", "is": {"cur": {"revenue": 4}, }},
                  {"sha256_prefix": "cc", "is": {"cur": {"revenue": 5}}}],
         "roll_checks": [{"name": "x", "total": ["aa", "is", "cur", "revenue"], "parts": [["bb", "is", "cur", "revenue"], ["cc", "is", "cur", "revenue"]]}]}
    assert len(mod.rolls(t)) == 1
