"""Page transcript for 8180 Al Sagr Cooperative Insurance (SAR full riyals as printed). FY2022-as-issued and H1 2026 statements are image/OCR pages read visually."""
from trlib import bs, write
from tr8120 import isx, cf, D


FY25 = bs(651837105, 309693696, 342143409, cash=171030408, ppe=5587109)
FY24 = bs(743509202, 342599237, 400909965, cash=262559683, ppe=6247601)
IS24 = isx(503656077, 40672194, -8813986, 31858208, 1.26)
CF24 = cf(27603492, -73050520, 152259043, 106812015, 155747668, 262559683)
IS23 = isx(486224565, 49499859, -7200000, 42299859)
CF23 = cf(-3031730, -63248679, -938588, -67218997, 222966665, 155747668)
BS23 = bs(573956195, 375758591, 198197604, cash=155747668, ppe=4172517)

docs = [
    D("e2b38e66", "FY2025 audited FS in annual report (collector label 2026|FY = publication year)", "2025-12-31", "2024-12-31", "FY",
      "text layer: pdf p7 BS (printed 6), p8 IS (7), p11-12 CF (10-11)", dict(bs=7, is_=8, cf="11-12"),
      dict(cur=FY25, prior=FY24),
      dict(cur=isx(604414187, -71317330, 1000000, -70317330, -2.34), prior=IS24),
      dict(cur=cf(-93014777, 2757106, -1271604, -91529275, 262559683, 171030408), prior=CF24)),
    D("ec20ffab", "FY2024 audited FS in annual report (label 2025|FY = publication year); pdf p11 textless (equity statement)", "2024-12-31", "2023-12-31", "FY",
      "text layer: pdf p8 BS (printed 7), p9 IS (8), p12-13 CF (11-12)", dict(bs=8, is_=9, cf="12-13"),
      dict(cur=FY24, prior=BS23), dict(cur=IS24, prior=isx(486224565, 49499859, -7200000, 42299859, 1.99, _declared_diff={"eps_basic": "2023 EPS restated 1.99 in the FY2024 filing versus 3.02 as issued (capital increase 2024)"})),
      dict(cur=CF24, prior=CF23)),
    D("d50bb975", "FY2023 audited FS in annual report (label 2024|FY = publication year); 2022 and 1 Jan 2022 restated (IFRS 17)", "2023-12-31", "2022-12-31", "FY",
      "text layer: pdf p10 BS (printed 9), p11 IS (10), p14-15 CF (13-14)", dict(bs=10, is_=11, cf="14-15"),
      dict(cur=BS23, prior=bs(567895461, 414437387, 153458074, cash=222966665, ppe=5248300, restated=True)),
      dict(cur=isx(486224565, 49499859, -7200000, 42299859, 3.02), prior=isx(473347548, -48859717, -4600000, -53459717, -3.82, restated=True)),
      dict(cur=CF23, prior=cf(-72316933, 8356541, -1291196, -65251588, 288218253, 222966665)),
      restatements=["FY2022 and 1 Jan 2022 are restated for the IFRS 17 transition (notes 3 and 5); restated FY2022 values as printed here. The FY2022 as-issued values were not read in this audit, so the restatement amounts are not stated."]),
    D("78343af2", "Q1 2026 interim (label 2026|Q1 correct)", "2026-03-31", "2025-03-31", "Q1",
      "text layer: pdf p4 BS (printed 3), p5 IS (4), p8-9 CF (7-8)", dict(bs=4, is_=5, cf="8-9"),
      dict(cur=bs(647001018, 303792452, 343208566, cash=170608923), prior=FY25),
      dict(cur=isx(146130776, 2006186, -1000000, 1006186, 0.03), prior=isx(150712841, -16922730, -1000000, -17922730, -0.6)),
      dict(cur=cf(86292, 168459, -676236, -421485, 171030408, 170608923), prior=cf(-17257982, 5035553, -547742, -12770171, 262559683, 249789512)),
      bs_prior_end="2025-12-31"),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    for blk in ("is", "is_q"):
        for col in ("cur", "prior"):
            c = d.get(blk, {}).get(col)
            if c and c.get("revenue") is None:
                c.pop("revenue", None)

rolls = [
]
if __name__ == "__main__":
    write("8180", "AL SAGR COOPERATIVE INSURANCE COMPANY", "SAR", "SAR full riyals as printed", docs, rolls)
