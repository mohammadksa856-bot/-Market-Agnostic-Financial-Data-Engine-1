"""Archive reviewed official Mobily historical reports and earnings supplements."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DEST = RAW / "SA" / "7020" / "documents"
INDEX = RAW / "archive-index.json"
SOURCE_INDEX = "https://mobily.com.sa/web/en/personal/about-mobily/investor-relations-details/financial-results"

SOURCES = {
    "mobily-2021-fy": "https://ir.mobily.link/2021/assets/img/pdfs/mobily_ar21_eng.pdf",
    "mobily-2022-fy": "https://ir.mobily.link/2022/assets/img/pdfs/Mobily%20AR_2022_English.pdf",
    "mobily-2022-q1": "https://www.mobily.com.sa/wps/wcm/connect/cd8825a0-385f-4a5c-810c-118f57cfef08/Earnings%2BPresentation%2BQ122.pdf?MOD=AJPERES",
    "mobily-2022-q2": "https://www.mobily.com.sa/wps/wcm/connect/1f663d19-95ec-4cdb-8a50-f0c45f9f01bb/Earnings%2BPresentation%2B2Q22.pdf?MOD=AJPERES",
    "mobily-2022-q3": "https://www.mobily.com.sa/wps/wcm/connect/b5f8837a-e249-49c9-8b9c-626cac07b20d/Earnings_Presentation_3Q22%2Bwithout%2Bscript%2B-%2BFinal.pdf?MOD=AJPERES",
    "mobily-2023-fy": "https://ir.mobily.link/2023/assets/img/pdfs/AR2023_English.pdf",
    "mobily-2023-q1": "https://mobily.com.sa/wps/wcm/connect/4eae094a-6747-4422-82af-53831549ef55/Earnings_Presentation_Q1%2B2023.pdf?MOD=AJPERES",
    "mobily-2023-q2": "https://www.mobily.com.sa/wps/wcm/connect/ef8aef77-ea2f-40a7-8594-f75d3bf1c692/Earnings_Presentation_Q2%2B2023%2B.pdf?MOD=AJPERES",
    "mobily-2023-q3": "https://www.mobily.com.sa/wps/wcm/connect/a6687b9d-481b-438b-aab3-d9b94a981fe5/Earnings_Presentation_Q3%2B2023.pdf?MOD=AJPERES",
    "mobily-2024-fy": "https://www.mobily.com.sa/wps/wcm/connect/a3751ebe-adea-4054-8cdb-d1dc5c6f51aa/Earnings%2BPresentation%2BFY%2B2024.pdf?CACHEID=ROOTWORKSPACE-a3751ebe-adea-4054-8cdb-d1dc5c6f51aa-plrZejc&MOD=AJPERES",
    "mobily-2024-q1": "https://www.mobily.com.sa/wps/wcm/connect/af61b54b-2905-436a-80c0-dc2048c03498/Earnings_Presentation_Q1%2B2024.pdf?MOD=AJPERES",
    "mobily-2024-q2": "https://www.mobily.com.sa/wps/wcm/connect/67628fc4-bde7-448f-a90b-e6d1fbd2fc8d/Earnings%2BPresentation%2BQ2%2B2024.pdf?MOD=AJPERES",
    "mobily-2024-q3": "https://www.mobily.com.sa/wps/wcm/connect/eae0b374-6b0c-4e12-bd42-7ae2d2a4594d/Earnings%2BPresentation%2BQ3%2B2024.pdf?MOD=AJPERES",
}


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    artifacts = list(index["artifacts"])
    archived_urls = {item["source_url"] for item in artifacts}
    captured = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for manifest, url in SOURCES.items():
        if url in archived_urls:
            print("existing", manifest, flush=True)
            continue
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=90) as response:
            content = response.read()
            content_type = response.headers.get_content_type()
        if not content.startswith(b"%PDF"):
            raise RuntimeError(f"{manifest}: response is not a PDF")
        digest = hashlib.sha256(content).hexdigest()
        suffix = mimetypes.guess_extension(content_type) or ".pdf"
        path = DEST / f"{digest}{suffix}"
        path.write_bytes(content)
        artifacts.append({
            "artifact_key": f"artifact:sa:7020:{digest}",
            "company_id": "sa:7020",
            "source_url": url,
            "content_hash": digest,
            "local_path": path.relative_to(ROOT).as_posix(),
            "content_type": content_type,
            "byte_size": len(content),
            "archived_at": captured,
            "metadata": {
                "manifests": [f"{manifest}.json"],
                "immutable": True,
                "capture_method": "official Mobily annual report PDF" if manifest.endswith("fy") else "official Mobily earnings presentation PDF",
                "source_index_url": "https://mobily.com.sa/wps/portal/web/corporate/investor-relations/details/company-overview/annual-reports" if manifest.endswith("fy") else SOURCE_INDEX,
            },
        })
        print(manifest, digest, len(content), path, flush=True)
        artifacts.sort(key=lambda item: item["artifact_key"])
        index["artifacts"] = artifacts
        index["generated_at"] = captured
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
