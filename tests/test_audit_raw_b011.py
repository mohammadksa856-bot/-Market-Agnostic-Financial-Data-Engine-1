"""Offline guard for batch B011 audit records and page transcriptions: arithmetic identities, declared restatements, sha links. No network."""
import importlib.util
import json
from pathlib import Path

import pytest

B011 = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B011"
spec = importlib.util.spec_from_file_location("check_transcripts_b011", B011 / "tools" / "check_transcripts.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
TRANSCRIPTS = sorted(p.stem for p in mod.TR.glob("*.json"))
RECORDS = sorted(p.stem for p in B011.glob("[0-9]*.json"))


@pytest.mark.parametrize("symbol", TRANSCRIPTS)
def test_transcript_identities(symbol):
    t, problems = mod.check(symbol)
    assert t["docs"]
    assert problems == []


@pytest.mark.parametrize("symbol", RECORDS)
def test_company_record_links_to_inventory(symbol):
    rec = json.loads((B011 / f"{symbol}.json").read_text(encoding="utf8"))
    inv = json.loads((mod.INV / f"{symbol}.json").read_text(encoding="utf8"))
    shas = {f["sha256"] for f in inv["files"]}
    assert rec["documents"]
    for d in rec["documents"]:
        assert d["sha256"] in shas
        assert d["sha256_recomputed_ok"] is True
    assert {d["sha256"] for d in rec["documents"]} == shas
    assert {"value_correctness", "document_completeness", "company_coverage"} <= rec["dimensions"].keys()
    assert rec["unread_items"]


def test_progress_lists_all_companies():
    prog = json.loads((B011 / "progress.json").read_text(encoding="utf8"))
    assert set(prog["status"]) == {"7201", "3080", "3091", "3092", "1090", "6019"}
