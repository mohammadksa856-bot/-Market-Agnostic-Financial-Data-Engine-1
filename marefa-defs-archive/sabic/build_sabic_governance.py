"""SABIC governance, industry context and governance disclosures from the Integrated Annual Report 2025.

Every attribute and disclosure carries a quote that must appear, whitespace-normalised, on its PDF page.
Usage: build_sabic_governance.py <sabic-ar2025.pdf> <out.json>"""
import json, sys
import pymupdf
pdf, out = sys.argv[1:3]
doc = pymupdf.open(pdf)
page_text = lambda n: " ".join(doc[n - 1].get_text().split())
URL = "https://www.sabic.com/en/Images/SABIC-Integrated-Annual-Report-2025-EN_tcm1010-49452.pdf"

BOARD = [  # p.100: board as of December 31, 2025
    ("Khalid Al-Dabbagh", "Chairman", "non-executive", "2020-06"),
    ("Dr. Mohammed Al-Qahtani", "Vice Chairman", "non-executive", "2022-04"),
    ("Abdulrahman Al-Fageeh", "Director, Chief Executive Officer", "executive", "2023-03"),
    ("Yousef Al-Zamel", "Director", "independent", "2022-04"),
    ("Dr. Ramesh Ramachandran", "Director", "independent", "2025-04"),
    ("Mohammed Al-Subaie", "Director", "independent", "2025-04"),
    ("Ziad Al-Murshed", "Director", "non-executive", "2020-06"),
    ("Dr. Faisal Al-Faqeer", "Director", "non-executive", "2023-09"),
    ("Lucrèce De Ridder", "Director", "non-executive", "2025-04"),
]
EXECUTIVES = [  # pp.111-114: executive management biographies (name heading followed by title)
    ("Abdulrahman Al-Fageeh", "Chief Executive Officer"),
    ("Salah Al-Hareky", "Executive Vice President, Corporate Finance"),
    ("Ernesto Occhiello", "Executive Vice President, Corporate Technology & Innovation and Sustainability"),
    ("Abdulaziz Al-Oudan", "Executive Vice President, Shared Services"),
    ("Ahmed Al-Shaikh", "Executive Vice President, Engineering and Project Management"),
    ("Abdulrahman Shamsaddin", "Executive Vice President, Manufacturing"),
    ("Faisal Al-Suwailem", "Executive Vice President, Corporate Human Resources"),
    ("Sami Al-Osaimi", "Executive Vice President, Polymers"),
    ("Olivier Thorel", "Executive Vice President, Chemicals"),
    ("Naveena Shastri", "Executive Vice President, Corporate Governance"),
]
def committee(name, chair, members, meetings, attendance):
    return {"name": name, "chair": chair, "members": members, "meetings_held_2025": meetings, "attendance": attendance}
BAC = committee("Board Audit Committee (BAC)", "Mohammed Al-Subaie",
                ["Mohammed Al-Subaie", "Dr. Ramesh Ramachandran", "Bassam M. Asiri", "Wilhelmus Jansen", "Ralph M. Wetzels"],
                5, "96%")
BRNC = committee("Board Remuneration and Nomination Committee (BRNC)", "Dr. Ramesh Ramachandran",
                 ["Dr. Ramesh Ramachandran", "Dr. Mohammed Al-Qahtani", "Ziad Al-Murshed", "Thomas Palmer"], 8, "96.9%")
BSREC = committee("Board Sustainability, Risk, and EHSS Committee (BSREC)", "Dr. Faisal Al-Faqeer",
                  ["Dr. Faisal Al-Faqeer", "Yousef Al-Zamel", "Mohammed Al-Subaie", "Lucrèce De Ridder"], 5, "100%")
BIC = committee("Board Investment Committee (BIC)", "Dr. Mohammed Al-Qahtani",
                ["Dr. Mohammed Al-Qahtani", "Abdulrahman Al-Fageeh", "Ziad Al-Murshed", "Yousef Al-Zamel", "Lucrèce De Ridder"],
                8, "95%")
G = "governance"; I = "industry_context"
ATTRIBUTES = [
 ("board_of_directors", G, [{"name": n, "role": r, "classification": c, "joined": j} for n, r, c, j in BOARD], 100,
  "As of December 31, 2025, the SABIC Board comprises the following directors"),
 ("board_size", G, 9, 99, "SABIC has a one-tier Board consisting of nine directors"),
 ("independent_directors", G, {"count": 3, "share": "33.3%", "names": [n for n, _, c, _ in BOARD if c == "independent"]}, 101,
  "As of December 31, 2025, one-third (33.3%) of the Board directors are independent"),
 ("board_term_end", G, "2028-04-09", 101, "The Board was reformed through GA voting on April 9, 2025, for a new three-year term ending on April 9, 2028."),
 ("board_meetings_held", G, {"year": 2025, "count": 7, "attendance": "100%"}, 103,
  "During the year ended December 31, 2025, the Board met seven times."),
 ("board_committees", G, [BAC["name"], BRNC["name"], BSREC["name"], BIC["name"]], 104,
  "the Board has established four committees: the Audit Committee; Remuneration and Nomination Committee; Sustainability, Risk, and EHSS Committee; and Investment Committee."),
 ("audit_committee", G, {**BAC, "composition": "2 independent directors and 3 non-director (outside) members; independent chairman"}, 104,
  "BOARD AUDIT COMMITTEE (BAC) 5 Members 2 Independent 3 Non-Director (Outside) Members Independent Chairman 96% Attendance"),
 ("nomination_committee", G, {**BRNC, "note": "remuneration and nomination are combined in one committee"}, 106,
  "BOARD REMUNERATION AND NOMINATION COMMITTEE (BRNC) 4 Members 1 Independent Director 2 Non-Executive Directors 1 Non-Director (Outside) Member Independent Chairman 96.9% Attendance"),
 ("compensation_committee", G, {**BRNC, "note": "remuneration and nomination are combined in one committee"}, 106,
  "BOARD REMUNERATION AND NOMINATION COMMITTEE (BRNC) 4 Members"),
 ("sustainability_risk_hse_committee", G, BSREC, 108,
  "BOARD SUSTAINABILITY, RISK, AND EHSS COMMITTEE (BSREC) 4 Members 2 Independent Director 2 Non-Executive Directors Non-Executive Chairman 100% Attendance"),
 ("executive_management_team", G, [{"name": n, "role": r} for n, r in EXECUTIVES], 111,
  "ABDULRAHMAN AL-FAGEEH Chief Executive Officer SALAH AL-HAREKY Executive Vice President, Corporate Finance"),
 ("compensation_policy", G, {"shareholder_approved": True,
   "board_member_pay": "fixed fee and an allowance for attendance at Board and committee meetings",
   "executive_pay": "base salary, allowances, benefits in kind and incentive plans",
   "board_annual_cap_sar": 1800000, "outside_committee_member_annual_sar": 300000}, 115,
  "governed by the SABIC Remuneration Policy which was approved at the General Assembly and is subject to regular review"),
 ("governance_framework", G, {"basis": "SABIC bylaws, Board and committee charters", "regulation": "Capital Market Authority (CMA) Corporate Governance Regulations",
   "exception": "no separate corporate governance committee (CGR Article 92, guiding)"}, 90,
  "The framework is established under SABIC's bylaws and the charters of the Board and its committees"),
 ("internal_control_assessment", G, {"assessor": "Board Audit Committee", "year": 2025,
   "assessment": "Executive management has maintained an effective internal control system capable of providing reasonable assurances",
   "board_declaration": "the internal control system was established on a sound basis and implemented effectively"}, 105,
  "the Committee is of the opinion that the Company’s Executive Management has maintained an effective internal control system capable of providing reasonable assurances"),
 ("industry_overview", I, {"chemical_industry_share_of_global_gdp": "6%", "everyday_products_containing_chemicals": "90%+",
   "jobs_supported": "120 million", "chemicals_in_commercial_use": "100,000+", "source_cited": "ICIS, Oxford Economics"}, 37,
  "6% share of global GDP contributed by the chemical industry 90%+ everyday products that contain chemicals"),
 ("industry_size", I, {"share_of_global_gdp": "6%", "projected_global_chemical_sales_2030_usd": "7.8 trillion",
   "source_cited": "ICIS, Oxford Economics"}, 37, "US$ 7.8 Tn. projected global chemical sales in 2030"),
 ("industry_growth", I, {"outlook_2026": "supply growth expected to continue outpacing demand growth; a period of rationalization "
   "with closures of older, inefficient assets in Europe and Asia"}, 38,
  "The outlook for 2026 remains cautious for most products, as supply growth is expected to continue outpacing demand growth."),
 ("industry_drivers", I, ["feedstock prices and availability (lower crude/LPG, tight natural gas and ethane)",
   "trade policy and tariffs", "interest rates and consumer and industrial demand", "capacity additions"], 38,
  "Overall feedstock prices trended lower as the pace of supply growth outpaced demand."),
 ("competitive_environment", I, {"condition": "significant oversupply",
   "capacity_additions": "aggressive expansion in China, alongside new, low-cost plants in the United States and the GCC"}, 38,
  "The industry continues to navigate through a significant oversupply situation. This capacity addition is being driven primarily by aggressive expansion in China, alongside new, low-cost plants in the United States and the GCC."),
 ("regulatory_environment", I, ["Carbon Border Adjustment Mechanism (CBAM)", "Corporate Sustainability Reporting Directive (CSRD)",
   "Corporate Sustainability Due Diligence Directive (CSDDD)", "new tariffs", "CMA Corporate Governance Regulations"], 109,
  "Reviewed reports on rapidly evolving local and global legislation including Carbon Border Adjustment Mechanism (CBAM), Corporate Sustainability Reporting Directive (CSRD), Corporate Sustainability Due Diligence Directive (CSDDD)"),
]
DISCLOSURES = [
 ("related_party_transaction", "Sale of the ALBA stake to Ma'aden approved by the Ordinary General Assembly",
  "SABIC Industrial Investments Co. sold its 20.62% stake in ALBA (292,804,000 shares) to the Saudi Arabian Mining Company "
  "(Ma'aden) for BHD 363,076,960 (about SAR 3.61 billion); the Board Vice Chairman has an indirect interest as a member of "
  "the Ma'aden Board. Approved by the Ordinary General Assembly on April 9, 2025.", 123,
  "sold its stake in ALBA Co., amounting to 292,804,000 common shares representing 20.62% of the total shareholding of ALBA, to the Saudi Arabian Mining Company (Ma’aden)",
  {"counterparty": "Saudi Arabian Mining Company (Ma'aden)", "consideration_bhd": 363076960, "approved_by": "Ordinary General Assembly",
   "approved_on": "2025-04-09", "event_class": "divestment"}),
 ("board_change", "Board reconstituted for a new three-year term from April 10, 2025",
  "The General Assembly of April 9, 2025 elected the Board for a new three-year term (April 10, 2025 to April 9, 2028). "
  "Dr. Ramesh Ramachandran, Mohammed Al-Subaie and Lucrèce De Ridder joined; Mohammed Al-Nahas, Nader Al-Wehibi and "
  "Calum MacLean left on April 9, 2025.", 99,
  "On April 10, 2025, the Board commenced a new three-year term with a refreshed formation with three new directors, including a woman.",
  {"effective": "2025-04-10", "joined": ["Dr. Ramesh Ramachandran", "Mohammed Al-Subaie", "Lucrèce De Ridder"],
   "left": ["Mohammed Al-Nahas", "Nader Al-Wehibi", "Calum MacLean"]}),
 ("management_change", "Executive Vice President, Strategy & Transformation served until April 1, 2025",
  "Anas Kentab served as Executive Vice President, Strategy & Transformation until April 1, 2025.", 114,
  "ANAS KENTAB Executive Vice President, Strategy & Transformation Until April 01, 2025",
  {"effective": "2025-04-01", "person": "Anas Kentab", "role": "Executive Vice President, Strategy & Transformation"}),
]
errors = []
for key, _, _, page, quote in ATTRIBUTES:
    if " ".join(quote.split()) not in page_text(page): errors.append((key, page))
for kind, _, _, page, quote, _ in DISCLOSURES:
    if " ".join(quote.split()) not in page_text(page): errors.append((kind, page))
for name, _, _, _ in BOARD:
    plain = name.replace("Dr. ", "")
    if plain not in page_text(100): errors.append(("board name", name))
for name, role in EXECUTIVES[1:]:
    if not any(name.upper().replace("AL-SUWAILEM", "AL-SUWAILEM") in page_text(p) and role in page_text(p) for p in range(111, 115)):
        errors.append(("executive", name, role))
# pp.119-120: SABIC shares held at 31 December 2025 by Board members (with spouses and minor children) and senior
# executives; every other listed person holds none of SABIC's own shares.
INSIDERS = {"Yousef Al-Zamel": 69200, "Mohammed Al-Subaie": 2000, "Dr. Faisal Al-Faqeer": 7500, "Ahmed Al-Shaikh": 2500}
INSIDER_QUOTES = ((119, "Yousef Al-Zamel 69,200 4,030 82,017 137,000 69,200"),
                  (119, "Mohammed Al-Subaie (1) – – – – 2,000 1,000"),
                  (119, "Dr. Faisal Al-Faqeer 6,600 – – – 7,500"),
                  (120, "Ahmed Al-Shaikh – – – – 2,500 500"))
for page, quote in INSIDER_QUOTES:
    if quote not in page_text(page): errors.append(("insider holding", page, quote))
DIVIDEND_QUOTES = (19, ("interim dividends for the first half of the year will be announced",
                        "interim dividend distribution for the second half of the year"))
for quote in DIVIDEND_QUOTES[1]:
    if quote not in page_text(DIVIDEND_QUOTES[0]): errors.append(("dividend frequency", quote))
if errors:
    print("CHECK FAILED:"); [print(" ", e) for e in errors]; sys.exit(1)
manifest = {
    "company_id": "sa:2010", "market": "SA", "symbol": "2010",
    "filing_type": "Integrated Annual Report 2025 - corporate governance and business environment",
    "filed_at": "2026-03-03", "period_end": "2025-12-31", "source_url": URL, "review_state": "reviewed",
    "notes": "Corporate governance section (pp. 89-123) and business environment (pp. 37-38). Each item quotes its page; "
             "the quotes are matched against the PDF text. The Board does not name a board/corporate secretary.",
    "facts": [],
    "company_attributes": [{"attribute_key": key, "value": value, "category": category,
                            "metadata": {"pdf_page": page, "quote": quote, "method": "manual_page_review"}}
                           for key, category, value, page, quote in ATTRIBUTES],
    "disclosures": [{"disclosure_type": kind, "title": title, "body_text": body, "language": "en",
                     "published_at": "2026-03-03", "period_end": "2025-12-31",
                     "metadata": {**meta, "pdf_page": page, "quote": quote}}
                    for kind, title, body, page, quote, meta in DISCLOSURES],
    "ownership_positions": [{"holder_key": "board_and_senior_executives", "holder_name": "Board members and senior executives",
                             "holder_type": "insider", "ownership_type": "aggregate", "as_of_date": "2025-12-31",
                             "shares": sum(INSIDERS.values()),
                             "ownership_pct": round(sum(INSIDERS.values()) / 3000000000, 10),
                             "metadata": {"holders": INSIDERS, "pages": [119, 120], "issued_shares": 3000000000,
                                          "note": "inside the public free float; includes spouses and minor children"}}],
    "typed_facts": [{"metric": "dividend_payment_frequency", "value": "semi-annual", "value_type": "text", "unit": "text",
                     "period_start": "2025-01-01", "period_end": "2025-12-31", "period_kind": "fy", "fiscal_year": 2025,
                     "page": 19, "table": "Dividend distribution: interim dividends for the first half and for the second "
                     "half of each year (p.19); 2025 cycles 2H 2024, 1H 2025, 2H 2025 (p.20)"}],
}
json.dump(manifest, open(out, "w"), indent=1, ensure_ascii=False)
print(out, len(ATTRIBUTES), "attributes", len(DISCLOSURES), "disclosures")
