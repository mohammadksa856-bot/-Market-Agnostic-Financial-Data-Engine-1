"""Archive already-downloaded local files through the collector's own
classification/hashing/archiving pipeline (CompanyRun.handle_candidate),
unchanged - for cases where the source needed a real browser session
(cookies) to fetch at all, so the files were saved to disk by hand first.

Usage: one line per file as "local_path<TAB>source_url<TAB>title", then:
  _ingest_local_files.py --root <dir> --symbol <symbol> --index-url <url>
      --fiscal-year-hint none --file <list.txt>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sa_raw_statement_collector as col  # noqa: E402
from finengine import sa_raw_statements as raw  # noqa: E402


class LocalFileDownloader:
    def __init__(self, mapping: dict[str, Path]):
        self.mapping = mapping

    def get(self, url: str, referer: str | None) -> bytes:
        return self.mapping[url].read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--index-url", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--fy-end-month", type=int, default=12)
    args = ap.parse_args()
    root = Path(args.root)

    items = []
    mapping = {}
    for line in Path(args.file).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        local_path, url, title = line.split("\t")
        mapping[url] = Path(local_path)
        items.append((url, title))

    reg = raw.load_registry(col.REGISTRY)
    company = next((c for c in reg if c["symbol"] == args.symbol), None)
    if company is None:
        print(f"symbol {args.symbol} not in registry", file=sys.stderr)
        return 2

    logf = root / "logs" / f"manual-{args.symbol}.jsonl"
    log = lambda ev: col.jlog(logf, ev)  # noqa: E731
    run = col.CompanyRun(root, company, None, log, part="se")
    dl = LocalFileDownloader(mapping)
    before = len(run.state["docs"])
    for url, title in items:
        run.handle_candidate(dl, url, title, "", args.index_url,
                             "saudi_exchange_profile", args.fy_end_month)
    run.save()
    after = len(run.state["docs"])
    print(f"docs: {before} -> {after} (+{after - before})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
