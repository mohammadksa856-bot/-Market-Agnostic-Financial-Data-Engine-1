"""Daily 2010.SR prices from the Yahoo Finance chart feed (no archived daily sessions exist for SABIC)."""
import datetime, hashlib, json, sys
raw, out = sys.argv[1:3]
blob = open(raw, "rb").read()
y = json.loads(blob)["chart"]["result"][0]
meta = y["meta"]
assert meta["currency"] == "SAR" and meta["exchangeName"] == "SAU" and meta["symbol"] == "2010.SR"
assert not y.get("events", {}).get("splits"), "split or bonus inside the window"
tz = datetime.timezone(datetime.timedelta(seconds=meta["gmtoffset"]))
q = y["indicators"]["quote"][0]
rows, skipped = [], 0
for i, t in enumerate(y["timestamp"]):
    o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
    if None in (o, h, l, c, v) or not v:
        skipped += 1; continue  # placeholder bar
    day = datetime.datetime.fromtimestamp(t, tz).date().isoformat()
    rows.append({"observed_at": day, "interval": "1d", "open": f"{o:.2f}", "high": f"{h:.2f}", "low": f"{l:.2f}",
                 "close": f"{c:.2f}", "volume": str(int(v)), "currency": "SAR"})
body = {"company_id": "sa:2010", "filing_type": "Yahoo Finance daily chart (Tadawul feed) price history",
        "filed_at": "2026-10-25", "period_end": rows[-1]["observed_at"],
        "source_url": "https://query1.finance.yahoo.com/v8/finance/chart/2010.SR?period1=1577836800&period2=1793000000&interval=1d&events=div%2Csplit",
        "notes": (f"Response sha256 {hashlib.sha256(blob).hexdigest()}. Cross-check against the annual-report five-year "
                  "history in this engine: intraday annual high and low equal 2021-2025 (2025 low 50.65 printed 50.6); "
                  "year-end close equal in 2021, 2023, 2024, 2025; 2022 prints 90.4 while the same report's 2022 market cap "
                  f"(268.2bn / 3bn shares = 89.4) equals this feed. {skipped} zero-volume placeholder bars dropped. "
                  "No split or bonus event in the window."),
        "facts": [], "market_prices": rows}
json.dump(body, open(out, "w"), indent=1)
print(out, len(rows), rows[0]["observed_at"], rows[-1]["observed_at"], "skipped", skipped)
