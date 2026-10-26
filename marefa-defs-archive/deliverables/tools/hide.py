"""Copy-only: mark the given Aramco keys not current in a COPY of an isolated DB."""
import sqlite3, sys, shutil
src, dst, *keys = sys.argv[1:]
assert "/scratchpad/" in dst and dst != src
shutil.copyfile(src, dst)
c = sqlite3.connect(dst)
with c:
    n = c.execute(f"UPDATE data_points SET is_current=0 WHERE company_id='sa:2222' AND metric_key IN ({','.join('?'*len(keys))})", keys).rowcount
print(dst, "hidden rows:", n)
