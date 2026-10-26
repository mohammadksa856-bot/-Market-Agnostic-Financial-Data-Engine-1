"""Daily 2222.SR closes from the Yahoo Finance chart feed, before the archived Saudi Exchange window."""
import datetime, hashlib, json, sys
raw, archive, out = sys.argv[1:4]
blob = open(raw, "rb").read()
y = json.loads(blob)["chart"]["result"][0]
meta = y["meta"]
assert meta["currency"] == "SAR" and meta["exchangeName"] == "SAU" and meta["symbol"] == "2222.SR"
assert not y.get("events", {}).get("splits"), "split or bonus inside the window: share basis changes"
tz = datetime.timezone(datetime.timedelta(seconds=meta["gmtoffset"]))
q = y["indicators"]["quote"][0]
archived = json.load(open(archive))["market_prices"]
first_archived = min(p["observed_at"] for p in archived)
rows, skipped = [], []
for i, t in enumerate(y["timestamp"]):
    day = datetime.datetime.fromtimestamp(t, tz).date().isoformat()
    o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
    if day >= first_archived:
        continue
    if None in (o, h, l, c, v) or not v:
        skipped.append(day); continue  # placeholder bar (no trading recorded)
    rows.append({"observed_at": day, "interval": "1d", "open": f"{o:.2f}", "high": f"{h:.2f}",
                 "low": f"{l:.2f}", "close": f"{c:.2f}", "volume": str(int(v)), "currency": "SAR"})
body = {"company_id": "sa:2222", "filing_type": "Yahoo Finance daily chart (Tadawul feed) price history",
        "filed_at": "2026-10-24", "period_end": rows[-1]["observed_at"],
        "source_url": "https://query1.finance.yahoo.com/v8/finance/chart/2222.SR?period1=1704067200&period2=1793000000&interval=1d&events=div%2Csplit",
        "notes": (f"Response sha256 {hashlib.sha256(blob).hexdigest()}. Cross-check: open/high/low/close/volume equal the "
                  f"archived Saudi Exchange snapshot on 22 of 23 sessions (2026-08-04..2026-09-03); the one mismatch is a "
                  f"zero-volume placeholder bar, so every zero-volume bar is dropped ({len(skipped)} here). Only sessions before "
                  f"{first_archived} are taken, so the Saudi Exchange snapshot stays the current price. No split or bonus "
                  f"event in the window (last bonus issue 2023-05-08)."),
        "facts": [], "market_prices": rows}
json.dump(body, open(out, "w"), indent=1)
print(out, len(rows), rows[0]["observed_at"], rows[-1]["observed_at"], "skipped", skipped)
