"""Offline regression tests for the Group E (3002/3003/3005/3020/3040) independent audit.

The page transcriptions under docs/audits/saudi-independent/tools/e_transcripts were read by eye from
the archived source PDFs (page + line item); these tests pin the published manifests to them and
exercise the helper parsers. No network, no database, data/** is only read.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "docs" / "audits" / "saudi-independent" / "tools"

CASES = [
    ("3002", "najran-cement-2025-fy.json"),
    ("3003", "city-cement-2025-fy.json"),
    ("3005", "umm-al-qura-cement-2025-fy.json"),
    ("3020", "yamama-cement-2025-fy.json"),
    ("3040", "qassim-cement-2025-fy.json"),
]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _manifest(fname):
    return json.loads((ROOT / "data" / "imports" / fname).read_text(encoding="utf8"))


def _compare(manifest, tr):
    mism, seen = [], 0
    for f in manifest["facts"]:
        t = tr["facts"].get(f["metric"])
        if t is None:
            mism.append((f["metric"], "not transcribed"))
            continue
        t = t if isinstance(t, dict) else t[0]
        v = t["v2025"] if f["period_end"].startswith("2025") else t["v2024"]
        if v is None:
            continue
        if isinstance(v, list):
            v = sum(v)
        v *= t.get("sign", 1)
        seen += 1
        if float(f["value"]) != v:
            mism.append((f["metric"], f["period_end"], f["value"], v))
    return seen, mism


@pytest.mark.parametrize("symbol,fname", CASES)
def test_manifest_matches_page_transcription(symbol, fname):
    tr = json.loads((TOOLS / "e_transcripts" / f"{symbol}.json").read_text(encoding="utf8"))
    seen, mism = _compare(_manifest(fname), tr)
    assert seen > 90
    assert mism == []


def test_textlayer_helpers_parse_negatives_and_split_parens():
    mod = _load("e_textlayer_verify")
    assert mod.parse_tokens(["(", "43,847", ")"]) == [-43847.0]
    assert mod.parse_tokens([")236("]) == [-236.0]
    assert mod.parse_tokens(["-", "6,722"]) == [0.0, 6722.0]
    lines = ["Finance cost", "26", "21,095", "Finance costs paid", "(19,425)"]
    # exact label must win over the shorter 'Finance cost' prefix hit
    assert mod.locate(lines, "Finance costs paid")[0] == 3


def test_yamama_note_refs_are_not_amounts():
    mod = _load("e_seq_verify")
    assert mod.amt("(22)") is None
    assert mod.amt("1, 172,979,234") == 1172979234.0
    assert mod.amt("(18,999,529)") == -18999529.0


@pytest.mark.xfail(strict=True, reason="AUDIT-E-META-1: filed_at carries the board-approval date, earlier than the "
                   "Saudi Exchange publication timestamp in source_url (shared root cause, 11/12 fsPdf manifests)")
@pytest.mark.parametrize("symbol,fname", CASES)
def test_filed_at_not_before_publication(symbol, fname):
    import re
    m = _manifest(fname)
    stamp = re.search(r"/fsPdf/\d+_\d+_(\d{4}-\d{2}-\d{2})_", m["source_url"]).group(1)
    assert m["filed_at"][:10] >= stamp
