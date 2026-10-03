"""Offline guard for batch B004 page transcriptions: arithmetic identities, declared restatements and inventory sha links. No network."""
import importlib.util
import json
from pathlib import Path

import pytest

B004 = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B004"
spec = importlib.util.spec_from_file_location("check_transcripts_b004", B004 / "tools" / "check_transcripts.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SYMBOLS = sorted(p.stem for p in mod.TR.glob("*.json"))


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_transcript_identities(symbol):
    t, problems = mod.check(symbol)
    assert t["docs"]
    assert problems == []


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_company_record_links_to_inventory(symbol):
    rec = json.loads((B004 / f"{symbol}.json").read_text(encoding="utf8"))
    inv = json.loads((mod.INV / f"{symbol}.json").read_text(encoding="utf8"))
    shas = {f["sha256"] for f in inv["files"]}
    assert rec["documents"]
    for d in rec["documents"]:
        assert d["sha256"] in shas
    assert {"value_correctness", "document_completeness", "company_coverage"} <= rec["dimensions"].keys()
    assert rec["unread_items"]
