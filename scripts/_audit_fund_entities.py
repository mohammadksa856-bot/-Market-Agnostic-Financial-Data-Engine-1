"""One-off audit: re-check already-collected documents for REIT/fund
companies against the same wrong_entity_not_fund_specific rule that
handle_candidate() now applies going forward, without re-downloading
anything. A document already on disk is only ever moved from docs[] to
rejected[] here - the archived file itself is deleted only for that one
mis-attributed copy, and only if no other company's docs[] still
references the same content hash (a REIT and its manager can legitimately
share unrelated documents; only cross-symbol *fund financial statements*
without any fund/REIT wording get removed).

Usage: _audit_fund_entities.py --root <dir> [--apply]
Without --apply, prints what it would do and changes nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FUND_ENTITY_WORD = re.compile(r"\breit\b|\bfund\b|صندوق|ريت", re.I)
FUND_NAME = re.compile(r"\breit\b|\bfund\b|صندوق|ريت", re.I)


def jload(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def jsave(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--registry", default=str(
        Path(__file__).resolve().parent.parent / "config" / "sa-market-registry.json"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    reg = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    companies = reg if isinstance(reg, list) else reg.get("companies", reg)
    fund_symbols = {c["symbol"]: c["name"] for c in companies if FUND_NAME.search(c["name"])}
    print(f"{len(fund_symbols)} REIT/fund-named companies in the registry")

    # Which content hashes are still legitimately used elsewhere, so a
    # shared-but-wrong file for one symbol is not deleted out from under a
    # different symbol that also (still, correctly or not) references it.
    hash_owners: dict[str, set[str]] = {}
    for part in ("se", "issuer"):
        for f in (root / "state" / part).glob("*.json"):
            st = jload(f, {})
            for d in st.get("docs", []):
                hash_owners.setdefault(d["content_hash"], set()).add(st.get("symbol", f.stem))

    flagged, removed_bytes = [], 0
    for part in ("se", "issuer"):
        for symbol, name in fund_symbols.items():
            f = root / "state" / part / f"{symbol}.json"
            st = jload(f, None)
            if st is None:
                continue
            keep, drop = [], []
            for d in st.get("docs", []):
                if d.get("bucket") != "statement" or d.get("scanned"):
                    keep.append(d)
                    continue
                evidence = d.get("evidence", "") or ""
                urls = f"{d.get('source_url', '')} {d.get('index_url', '')}"
                if FUND_ENTITY_WORD.search(evidence) or FUND_ENTITY_WORD.search(urls):
                    keep.append(d)
                else:
                    drop.append(d)
            if not drop:
                continue
            for d in drop:
                flagged.append((part, symbol, name, d))
                st.setdefault("rejected", []).append({
                    "url": d["source_url"], "title": d.get("title", "")[:150],
                    "reason": "wrong_entity_not_fund_specific",
                    "index_url": d.get("index_url", ""), "sha256": d["content_hash"],
                    "stage": "audit_backfill"})
                su = st.get("seen_urls", {})
                if d["source_url"] in su:
                    su[d["source_url"]] = {"status": "rejected",
                                           "reason": "wrong_entity_not_fund_specific"}
                other_owners = hash_owners.get(d["content_hash"], set()) - {symbol}
                if not other_owners and args.apply:
                    p = Path(d["local_path"])
                    if p.exists():
                        removed_bytes += p.stat().st_size
                        p.unlink()
            st["docs"] = keep
            if args.apply:
                jsave(f, st)

    print(f"\n{len(flagged)} document(s) flagged as wrong_entity_not_fund_specific:")
    by_symbol: dict[str, list] = {}
    for part, symbol, name, d in flagged:
        by_symbol.setdefault(f"{symbol} {name}", []).append(d)
    for label, docs in by_symbol.items():
        print(f"  {label}: {len(docs)} doc(s)")
        for d in docs[:3]:
            print(f"    - {d.get('title', '')[:70]!r} (fy={d.get('fiscal_year')} "
                  f"slot={d.get('period_slot')})")
    print(f"\n{'APPLIED' if args.apply else 'DRY RUN (pass --apply to actually change state)'}"
          f" - would free ~{removed_bytes / 1e6:.1f} MB of uniquely-wrong archived files"
          if args.apply else
          f"\nDRY RUN only - nothing changed. Re-run with --apply to remove these "
          f"from docs[] (and delete the archived file where no other company still uses it).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
