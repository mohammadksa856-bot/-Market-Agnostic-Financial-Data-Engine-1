"""Offline guard for batch B006 (4004, 4001, 4002, 7200, 5110): page-transcription identities, inventory sha links,
and structural rules of the per-company audit records. No network, no raw files needed."""
import importlib.util
import json
from pathlib import Path

import pytest

B = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B006"
INV = B.parent / "raw-coverage" / "companies"
spec = importlib.util.spec_from_file_location("check_transcripts", B / "tools" / "check_transcripts.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RECORDS = sorted(p.stem for p in B.glob("[0-9][0-9][0-9][0-9].json"))
TRANSCRIPTS = sorted(p.stem for p in mod.TR.glob("*.json"))


def test_records_exist():
    assert RECORDS, "no company record found"


@pytest.mark.parametrize("symbol", TRANSCRIPTS)
def test_transcript_identities(symbol):
    t, problems = mod.check(symbol)
    assert t["docs"]
    assert problems == []


@pytest.mark.parametrize("symbol", TRANSCRIPTS)
def test_restatements_really_differ(symbol):
    t = json.loads((mod.TR / f"{symbol}.json").read_text(encoding="utf8"))
    for r in t.get("restatements", []):
        assert r["original"] != r["re_presented"]
        assert r["original_sha"] != r["re_presented_sha"]


@pytest.mark.parametrize("symbol", RECORDS)
def test_record_structure(symbol):
    rec = json.loads((B / f"{symbol}.json").read_text(encoding="utf8"))
    assert rec["symbol"] == symbol
    dims = rec["dimensions"]
    assert set(dims) == {"value_correctness", "document_completeness", "company_coverage"}
    assert dims["value_correctness"]["not_read"], "unread items must be listed explicitly"
    inv = json.loads((INV / f"{symbol}.json").read_text(encoding="utf8"))
    inv_shas = {f["sha256"] for f in inv["files"]}
    doc_shas = [d["sha256"] for d in rec["documents"]]
    assert len(doc_shas) == len(set(doc_shas))
    assert set(doc_shas) <= inv_shas
    assert len(doc_shas) == len(inv_shas), "every inventory file must be accounted for"
    for d in rec["documents"]:
        assert len(d["sha256"]) == 64
        assert "label_ok" in d and "actual_period" in d and "read" in d
        if d["label_ok"] is False:
            assert d.get("correct_label")
