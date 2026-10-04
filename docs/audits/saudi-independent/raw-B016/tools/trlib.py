"""Small helpers for writing page transcripts (batch B016)."""
import json
from pathlib import Path
TR = Path(__file__).resolve().parent.parent / "transcripts"


def bs(ta, tl, te, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, **k)


def write(symbol, name, currency, unit, docs, roll_checks=None, extra=None):
    t = dict(symbol=symbol, name=name, currency=currency, unit=unit, docs=docs)
    if roll_checks:
        t["roll_checks"] = roll_checks
    if extra:
        t.update(extra)
    (TR / f"{symbol}.json").write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
    print(symbol, "docs", len(docs))
