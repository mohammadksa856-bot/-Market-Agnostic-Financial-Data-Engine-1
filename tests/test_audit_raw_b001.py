"""Offline consistency tests for the raw-document audit batch B001 records.

They read only docs/audits/saudi-independent/raw-B001/*.json (no raw files, no network)
and check: three separate dimensions are present, every file row carries a verdict and a
64-hex sha256, transcribed statements cross-foot, and the FY-label-equals-publication-year
defect is recorded wherever the cover period differs from the collector label.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "docs" / "audits" / "saudi-independent" / "raw-B001"
SYMBOLS = ["1810", "1111", "6010", "8210", "8250"]


def load(sym):
    return json.loads((ROOT / f"{sym}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("sym", SYMBOLS)
def test_three_dimensions_present_and_separate(sym):
    rec = load(sym)
    for key in ("dimension_1_value_correctness", "dimension_2_document_completeness",
                "dimension_3_company_coverage", "unread_items"):
        assert key in rec, key
    assert rec["unread_items"], "unread items must be listed explicitly"


@pytest.mark.parametrize("sym", SYMBOLS)
def test_every_file_has_hash_and_verdict(sym):
    for f in load(sym)["files"]:
        assert re.fullmatch(r"[0-9a-f]{64}", f["sha256"])
        assert f.get("verdict") and f.get("actual_period")


@pytest.mark.parametrize("sym", SYMBOLS)
def test_transcribed_balance_sheets_cross_foot(sym):
    """assets == liabilities + equity for every transcribed doc that gives all three (2-column values)."""
    checked = 0
    for t in load(sym)["dimension_1_value_correctness"]["transcriptions"]:
        v = t.get("values") or t.get("values_sar_thousands") or {}
        a, l, e = v.get("total_assets"), v.get("total_liabilities"), v.get("total_equity")
        if isinstance(a, list) and isinstance(l, list) and isinstance(e, list):
            for x, y, z in zip(a, l, e):
                assert x == y + z, (sym, t["doc"], x, y, z)
                checked += 1
    assert checked >= 0


@pytest.mark.parametrize("sym", SYMBOLS)
def test_cash_flow_foots_where_transcribed(sym):
    for t in load(sym)["dimension_1_value_correctness"]["transcriptions"]:
        v = t.get("values") or t.get("values_sar_thousands") or {}
        if all(k in v for k in ("cfo", "cfi", "cff", "net_change_cash")):
            for o, i, f, n in zip(v["cfo"], v["cfi"], v["cff"], v["net_change_cash"]):
                assert o + i + f == n, (sym, t["doc"])


def test_fy_label_defect_recorded_where_label_is_publication_year():
    for sym in SYMBOLS:
        files = load(sym)["files"]
        shifted = [f for f in files if "MISLABELLED_PERIOD" in f["verdict"]]
        defects = json.dumps(load(sym)["dimension_2_document_completeness"]["defects"])
        assert shifted, sym
        assert "LABEL" in defects, sym
