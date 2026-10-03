"""Offline guard for batch B003 page transcriptions: arithmetic identities and inventory sha links. No network."""
import importlib.util
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B003" / "tools"
spec = importlib.util.spec_from_file_location("check_transcripts", TOOLS / "check_transcripts.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SYMBOLS = sorted(p.stem for p in mod.TR.glob("*.json"))


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_transcript_identities(symbol):
    t, problems = mod.check(symbol)
    assert t["docs"]
    assert problems == []
