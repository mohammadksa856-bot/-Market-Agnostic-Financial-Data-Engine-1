"""Offline guard for batch B008 (2380, 2350, 4240, 4323, 4020): page-transcript arithmetic, cross-filing agreement,
inventory sha links and audit-record structure. Reads only files in the repository; no network, no raw files."""
import importlib.util
import json
from pathlib import Path

import pytest

B008 = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B008"
INV = B008.parent / "raw-coverage" / "companies"
spec = importlib.util.spec_from_file_location("check_transcripts_b008", B008 / "tools" / "check_transcripts.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BATCH = ["2380", "2350", "4240", "4323", "4020"]
DONE = sorted(p.stem for p in (B008 / "transcripts").glob("*.json"))
RECORDS = sorted(s for s in BATCH if (B008 / f"{s}.json").exists())


def test_something_audited():
    assert RECORDS


@pytest.mark.parametrize("symbol", DONE)
def test_transcript_identities(symbol):
    t, problems = mod.check(symbol)
    assert t["docs"]
    assert problems == []


@pytest.mark.parametrize("symbol", RECORDS)
def test_record_structure(symbol):
    rec = json.loads((B008 / f"{symbol}.json").read_text(encoding="utf8"))
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
