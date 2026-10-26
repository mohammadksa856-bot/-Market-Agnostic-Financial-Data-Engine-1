"""SABIC identity from registers and the issuer's Arabic edition.

- GLEIF LEI record (api.gleif.org): LEI and the Arabic legal name as registered, checked against SABIC's commercial
  registration number in the record (validatedAs) and the ISSUED/ACTIVE status.
- Arabic Q3 2026 earnings release, page 2: the company's Arabic name as SABIC writes it. The PDF text layer maps the
  Arabic glyphs wrongly, so the page was rendered and read; the rendered page's sha256 is kept with the value.
Usage: build_sabic_identity.py <gleif-record.json> <arabic-release.pdf> <out-dir>"""
import hashlib, json, subprocess, sys, tempfile
gleif_path, ar_pdf, out = sys.argv[1:4]
CR = "1010010813"
record = json.load(open(gleif_path))["data"]
a = record["attributes"]
errors = []
if a["lei"] != "213800ZCTFZZZJSK8645": errors.append("lei")
if a["entity"]["registeredAs"] != CR or a["registration"]["validatedAs"] != CR: errors.append("registration number")
if a["registration"]["status"] != "ISSUED" or a["entity"]["status"] != "ACTIVE": errors.append("status")
if not any("SAUDI BASIC INDUSTRIES CORPORATION" in n["name"] for n in a["entity"]["transliteratedOtherNames"]):
    errors.append("transliterated name")
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["pdftoppm", "-f", "2", "-l", "2", "-r", "110", "-png", ar_pdf, f"{tmp}/p"], check=True)
    page_sha = hashlib.sha256(open(f"{tmp}/p-02.png", "rb").read()).hexdigest()
pdf_sha = hashlib.sha256(open(ar_pdf, "rb").read()).hexdigest()
if errors:
    print("CHECK FAILED:", errors); sys.exit(1)
lei_url = f"https://api.gleif.org/api/v1/lei-records/{a['lei']}"
json.dump({"company_id": "sa:2010", "market": "SA", "symbol": "2010",
           "filing_type": "GLEIF LEI record (Global Legal Entity Identifier Foundation)",
           "filed_at": a["registration"]["lastUpdateDate"][:10], "period_end": a["registration"]["lastUpdateDate"][:10],
           "source_url": lei_url, "review_state": "reviewed",
           "notes": (f"LEI record validated by registration authority {a['registration']['validatedAt']['id']} against "
                     f"commercial registration {CR}; status {a['registration']['status']}, entity {a['entity']['status']}, "
                     f"corroboration {a['registration']['corroborationLevel']}, next renewal "
                     f"{a['registration']['nextRenewalDate'][:10]}. legal_name_ar is the registered legal name, verbatim."),
           "facts": [],
           "company_attributes": [
               {"attribute_key": "lei", "value": a["lei"], "category": "identity",
                "metadata": {"method": "register_record", "registered_as": CR,
                             "registration_status": a["registration"]["status"],
                             "last_update": a["registration"]["lastUpdateDate"]}},
               {"attribute_key": "legal_name_ar", "value": a["entity"]["legalName"]["name"], "category": "identity",
                "metadata": {"method": "register_record", "language": a["entity"]["legalName"]["language"],
                             "transliterated": a["entity"]["transliteratedOtherNames"][0]["name"]}}]},
          open(f"{out}/sabic-gleif-lei.json", "w"), indent=1, ensure_ascii=False)
json.dump({"company_id": "sa:2010", "market": "SA", "symbol": "2010",
           "filing_type": "SABIC earnings release, third quarter of 2026 (Arabic edition)",
           "filed_at": "2026-10-25", "period_end": "2026-09-30",
           "source_url": "https://www.sabic.com/ar/Images/EARNINGS-RELEASE-Q3-2026-AR_tcm12-51796.pdf",
           "review_state": "reviewed",
           "notes": f"sha256 {pdf_sha}. Page 2 opens: «أعلنت الشركة السعودية للصناعات الأساسية (\"سابك\") (2010-SA)».",
           "facts": [],
           "company_attributes": [
               {"attribute_key": "company_name_ar", "value": "الشركة السعودية للصناعات الأساسية (سابك)",
                "category": "identity",
                "metadata": {"pdf_page": 2, "method": "rendered_page_review", "rendered_page_sha256": page_sha,
                             "quote": "أعلنت الشركة السعودية للصناعات الأساسية (\"سابك\") (2010-SA)"}}]},
          open(f"{out}/sabic-2026-arabic-name.json", "w"), indent=1, ensure_ascii=False)
print("sabic-gleif-lei.json 2 attributes; sabic-2026-arabic-name.json 1 attribute")
