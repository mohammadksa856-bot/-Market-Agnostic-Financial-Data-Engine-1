"""Offline regression tests for the Group F (3060 Yanbu Cement, 7202 solutions by stc) independent audit.
Transcriptions under docs/audits/saudi-independent/tools/f_transcripts were read from the archived source PDFs
(page + line item). data/** is only read. No network, no database."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "docs" / "audits" / "saudi-independent" / "tools"
CASES = [("3060", "yanbu-cement-2025-fy.json"), ("7202", "stc-solutions-2025-fy.json")]


def _manifest(fname):
    return json.loads((ROOT / "data" / "imports" / fname).read_text(encoding="utf8"))


@pytest.mark.parametrize("symbol,fname", CASES)
def test_manifest_matches_page_transcription(symbol, fname):
    tr = json.loads((TOOLS / "f_transcripts" / f"{symbol}.json").read_text(encoding="utf8"))
    seen, mism = 0, []
    for f in _manifest(fname)["facts"]:
        t = tr["facts"].get(f["metric"])
        if t is None:
            mism.append((f["metric"], "not transcribed"))
            continue
        v = t["v2025"] if f["period_end"].startswith("2025") else t["v2024"]
        v = sum(v) if isinstance(v, list) else v
        v *= t.get("sign", 1)
        seen += 1
        if float(f["value"]) != v:
            mism.append((f["metric"], f["period_end"], f["value"], v))
    assert seen > 100
    assert mism == []


@pytest.mark.parametrize("symbol,fname", CASES)
def test_subtotals_reconcile(symbol, fname):
    vals = {(f["metric"], f["period_end"][:4]): float(f["value"]) for f in _manifest(fname)["facts"]}
    for y in ("2025", "2024"):
        assert vals[("total_assets", y)] == vals[("total_liabilities_equity", y)]
        assert vals[("total_liabilities", y)] + vals[("total_equity", y)] == vals[("total_assets", y)]
        assert vals[("cash_beginning", y)] + vals[("cash_change", y)] + vals.get(("foreign_exchange_effect", y), 0) == vals[("cash_end", y)]
        assert vals[("cash_end", y)] == vals[("cash", y)]


def _filed_before_publication(fname):
    d = _manifest(fname)
    m = re.search(r"/fsPdf/\d+_\d+_(\d{4}-\d{2}-\d{2})_", d["source_url"])
    return str(d["filed_at"])[:10] < m.group(1)


@pytest.mark.xfail(strict=True, reason="AUDIT-F-META-1: filed_at is the Board approval date, earlier than publication/audit-report date")
@pytest.mark.parametrize("symbol,fname", CASES)
def test_filed_at_not_before_publication(symbol, fname):
    assert not _filed_before_publication(fname)


@pytest.mark.xfail(strict=True, reason="AUDIT-F-7202-1: Note 43 PPA adjustment of FY2024 comparatives is not disclosed in the manifest notes")
def test_7202_notes_disclose_comparative_adjustment():
    notes = _manifest("stc-solutions-2025-fy.json")["notes"].lower()
    assert "note 43" in notes or "restated" in notes or "purchase price" in notes
