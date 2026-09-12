"""One-off runner for the second half of the banking/cement/telecom
profile-population batch (see docs/QUALITATIVE_READER_AND_NEWS_CONNECTOR.md).
Meant to be run once from inside the production container (which already
has ANTHROPIC_API_KEY, pymupdf and anthropic installed), against PDFs
already archived under /app/data/raw/. Not part of the CLI -- this is a
throwaway script for finishing one specific batch, kept in git only so
it can be pulled onto the server via `git show` without retyping it.
"""
import json
import pymupdf
from finengine.populate_profile import write_profile_batch

COMPANIES = [
    ("2010", "/app/data/raw/SA/2010/documents/888b4c0373f7da9588dc393a44c8d5682c0f2206bdfc8185ad4d9a37bf8ba6aa.pdf"),
    ("3002", "/app/data/raw/SA/3002/documents/759a24ad88cd92b8c6c5c0d59299024ff321a3cd296787ba39bd7443819b9167.pdf"),
    ("3003", "/app/data/raw/SA/3003/documents/6958b51f874c338076467a8c7bac0e93f7a3aa13b944206be95bc6f3025127cd.pdf"),
    ("3005", "/app/data/raw/SA/3005/documents/c1c7da561e2bcdec8cc3e8a8a116389c7e0799a58b3ca5edcfd74c9fa0848c67.pdf"),
    ("3010", "/app/data/raw/SA/3010/documents/95310e37c7e8adf82177a557e2949da2438f240300def0cbed6b61a0be75b261.pdf"),
    ("3020", "/app/data/raw/SA/3020/documents/5f522341d6ad40c84c4ba13fec7de717f89c31dd93365088f382b097eea802a0.pdf"),
    ("3030", "/app/data/raw/SA/3030/documents/799306475fca27d3cf24a9300db797e973b753662f1f2fe1bda250a7b57103ab.pdf"),
    ("3040", "/app/data/raw/SA/3040/documents/17ca838773025846d9b502f6f78c2bfbabcf18463c9399c37d5eea62b8308aa1.pdf"),
    ("3050", "/app/data/raw/SA/3050/documents/25c47e79e1906fafa75c4b40f84c260ec662059feb1c5668b62e0b44fcf09acb.pdf"),
    ("3060", "/app/data/raw/SA/3060/documents/7aa24367df35cb17de610dc6b94d1d0be084c710ad44eb5a1f6cb3cf607343b9.pdf"),
    ("7010", "/app/data/raw/SA/7010/documents/aeec895e88a6d48c1ae9e64c99eadeed5773deb87381239e9265403137b95e55.pdf"),
    ("7030", "/app/data/raw/SA/7030/documents/bee6f9b63c9d81f625abb5675852d96679bb2776b746ef6f1bf2b1e7e26d192c.pdf"),
    ("7202", "/app/data/raw/SA/7202/documents/287f14a69420bbc31ddb70ab916b1aef480ffe14ac951fc1622d7a0e9ab2e2ca.pdf"),
    ("7203", "/app/data/raw/SA/7203/documents/363810a1a59f0d824d5c053286e35900c0bd4092b22807a125003cddb0c11600.pdf"),
]

OUT_DIR = "/tmp/profile_batch_out"

jobs = []
for symbol, path in COMPANIES:
    doc = pymupdf.open(path)
    meta_date = doc.metadata.get("creationDate", "")
    doc.close()
    filed_at = "2026-01-01"
    if meta_date.startswith("D:") and len(meta_date) >= 10:
        y, m, d = meta_date[2:6], meta_date[6:8], meta_date[8:10]
        filed_at = f"{y}-{m}-{d}"
    jobs.append({
        "out_name": symbol,
        "pdf_path": path,
        "market": "SA",
        "symbol": symbol,
        "company_id": f"sa:{symbol}",
        "source_url": f"https://www.saudiexchange.sa/wps/portal/saudiexchange/ourmarkets/main-market-watch/company-profile-main/?companySymbol={symbol}",
        "filed_at": filed_at,
        "period_end": "2025-12-31",
        "max_pages": 35,
    })

print(f"running {len(jobs)} companies...")
summaries = write_profile_batch(jobs, out_dir=OUT_DIR, model="claude-opus-5")
for s in summaries:
    print(json.dumps(s, ensure_ascii=False))

total_in = sum(s.get("model_usage", {}).get("input_tokens", 0) for s in summaries if "error" not in s)
total_out = sum(s.get("model_usage", {}).get("output_tokens", 0) for s in summaries if "error" not in s)
errors = [s for s in summaries if "error" in s]
print(f"\nTOTAL input_tokens={total_in} output_tokens={total_out} errors={len(errors)}")
