"""Offline tests for the B002 raw-document audit (8230, 1211, 1302, 2223, 2290).
No network, no raw files needed: they pin the committed transcriptions (page evidence, arithmetic) and the general
period-from-cover rule that exposes the collector's publication-year FY labels."""
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "docs" / "audits" / "saudi-independent" / "raw-B002"
SYMS = ["8230", "1211", "1302", "2223", "2290"]
sys.path.insert(0, str(B / "transcripts"))

MONTH = {m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())}
SLOT = {3: "Q1", 6: "H1", 9: "9M", 12: "FY"}
DATE = re.compile(r"(?:ended|ending)\s+(?:(\d{1,2})\w{0,2}\s*)?(january|february|march|april|may|june|july|august|september|october|november|december)\s*,?\s*(?:(\d{1,2})\w{0,2},?\s*)?(20\d\d)", re.I)


def period_from_cover(text):
    m = DATE.search(" ".join(text.split()))
    if not m:
        return None
    return f"{m.group(4)}|{SLOT[MONTH[m.group(2).lower()]]}"


@pytest.mark.parametrize("text,expected", [
    ("FINANCIAL STATEMENTS FOR THE YEAR ENDED 31ST DECEMBER 2025", "2025|FY"),
    ("FOR THE YEAR ENDED DECEMBER 31, 2022", "2022|FY"),
    ("THREE AND NINE MONTHS PERIODS ENDED SEPTEMBER 30, 2022", "2022|9M"),
    ("for the quarter and six months ended 30 June 2026", "2026|H1"),
    ("FOR THE THREE-MONTH PERIOD ENDED 31 MARCH 2026", "2026|Q1"),
])
def test_period_from_cover(text, expected):
    assert period_from_cover(text) == expected


@pytest.mark.parametrize("sym", SYMS)
def test_transcript_arithmetic(sym):
    spec = importlib.util.spec_from_file_location("t" + sym, B / "transcripts" / f"t{sym}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    n = 0
    for d in m.T:
        for s in d["statements"]:
            assert s["pdf_page"] >= 1
            for name, parts, total in s["checks"]:
                assert abs(sum(parts) - total) < 0.5, (sym, d["sha"], s["name"], name)
                n += 1
    assert n > 20


@pytest.mark.parametrize("sym", SYMS)
def test_company_json_invariants(sym):
    d = json.loads((B / f"{sym}.json").read_text(encoding="utf-8"))
    assert d["symbol"] == sym
    for f in d["files"]:
        assert re.fullmatch(r"[0-9a-f]{64}", f["sha256"])
        assert f["sha256_recomputed_ok"] is True
        assert f["value_correctness"]["status"] in ("extractable_and_verified", "partial", "not_read")
    verified = [f for f in d["files"] if f["value_correctness"]["status"] == "extractable_and_verified"]
    assert verified and all(f["value_correctness"]["statements"] for f in verified)
    assert d["unread_items"]


@pytest.mark.parametrize("sym", SYMS)
def test_publication_year_label_defect_documented(sym):
    """The collector labels SE statement PDFs with the publication year: every company has >=3 annual files whose
    page-derived FY differs from the label by +1."""
    d = json.loads((B / f"{sym}.json").read_text(encoding="utf-8"))
    shifted = [f for f in d["files"] if f["page_derived_period"] and f["collector_label"].endswith("|FY")
               and int(f["collector_label"][:4]) - int(f["page_derived_period"][:4]) == 1]
    assert len(shifted) >= 3
