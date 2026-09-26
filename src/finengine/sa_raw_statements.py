"""Pure logic for the RAW-ONLY Saudi historical financial-statement collector.

No network, no extraction of numbers.  Everything here is deterministic and
unit-tested offline: shard selection, period classification, document
rejection, language detection, the missing-slot ledger, the coverage matrix and
construction of the (optional) AWS raw-copy commands.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from collections import defaultdict
from datetime import date
from pathlib import Path

SLOTS = ("Q1", "H1", "9M", "FY")
SHARD_FIRST = ["1020", "1050", "1080", "1111", "1140", "1180", "1183", "1202"]
SHARD_LAST = ["9642", "9645", "9648", "9650", "9653"]
SHARD_SIZE = 219

# --------------------------------------------------------------------------
# shard


def sorted_companies(registry: list[dict]) -> list[dict]:
    return sorted(registry, key=lambda c: int(c["symbol"]))


def odd_shard(registry: list[dict]) -> list[dict]:
    """Odd 0-based indices of the numerically sorted registry."""
    return sorted_companies(registry)[1::2]


def even_shard(registry: list[dict]) -> list[dict]:
    return sorted_companies(registry)[0::2]


def load_registry(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def split_workers(companies: list[dict], workers: int) -> list[list[dict]]:
    """Deterministic, disjoint split (round-robin over the sorted shard)."""
    return [companies[i::workers] for i in range(workers)]


# --------------------------------------------------------------------------
# hashing / file validation


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def detect_file_kind(content: bytes) -> str | None:
    """Return 'pdf' / 'xlsx' or None when the bytes are not that format."""
    if not content:
        return None
    if content.startswith(b"%PDF"):
        return "pdf"
    if content.startswith(b"PK\x03\x04"):
        return "xlsx"
    return None


# --------------------------------------------------------------------------
# language

_AR = re.compile(r"[؀-ۿ]")
_LAT = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> str:
    ar = len(_AR.findall(text or ""))
    lat = len(_LAT.findall(text or ""))
    if ar < 3 and lat < 3:
        return "unknown"
    if ar and lat and min(ar, lat) / max(ar, lat) > 0.15:
        return "bilingual"
    return "ar" if ar > lat else "en"


# --------------------------------------------------------------------------
# document type / rejection

_REJECT = [
    (r"presentation|investor deck|earnings call|conference call|webcast|"
     r"العرض التقديمي|عرض تقديمي|عروض المستثمرين|مؤتمر", "presentation"),
    (r"sustainab|\besg\b|استدامة|الاستدامة", "sustainability"),
    (r"board of directors'? report|directors'? report|\bboard report|\bbod report|"
     r"تقرير مجلس الإدارة|تقرير مجلس الادارة", "board_report"),
    (r"corporate governance|governance report|الحوكمة", "governance"),
    (r"dividend|توزيعات|أرباح موزعة|ارباح موزعة", "dividend_notice"),
    (r"general assembly|\bagm\b|\begm\b|invitation|الجمعية العامة|دعوة", "general_assembly"),
    (r"prospectus|نشرة إصدار|نشرة الاصدار|offering circular", "prospectus"),
    (r"credit rating|rating report|التصنيف الائتماني", "credit_rating"),
    (r"press release|news|بيان صحفي|خبر", "news"),
    (r"code of conduct|policy|charter|bylaws|articles of association|"
     r"سياسة|لائحة|النظام الأساسي|ميثاق", "policy_or_charter"),
    (r"transcript|earnings? call|نص المكالمة", "transcript"),
    (r"earnings? release|earnings? presentation|results presentation|"
     r"earnings? highlights|results highlights", "presentation"),
    (r"management discussion|md&a|مناقشة وتحليل الإدارة", "mdna"),
    (r"nomination|remuneration|committee|لجنة", "committee"),
]
_ANNUAL_REPORT = re.compile(r"annual report|التقرير السنوي", re.I)
_STATEMENT = re.compile(
    r"financial statements?|financial results|interim|condensed|consolidated|"
    r"quarter|q[1-4]\b|half[- ]year|six months|three months|nine months|"
    r"year[- ]end|annual|audited|reviewed|"
    r"القوائم المالية|قوائم مالية|القوائم المالية|النتائج المالية|"
    r"مرحلية|أولية|اولية|ربع|سنوية|السنوية|ستة أشهر|تسعة أشهر|ثلاثة أشهر", re.I)


def classify_document_type(text: str) -> tuple[str | None, str | None]:
    """Return (document_type, reject_reason).

    document_type is one of interim_statement / annual_statement /
    annual_report / statement (period unknown) or None when rejected.
    """
    t = " ".join((text or "").split())
    if _ANNUAL_REPORT.search(t) and not re.search(
            r"financial statements?|القوائم المالية|قوائم مالية", t, re.I):
        return "annual_report", None
    for pattern, reason in _REJECT:
        if re.search(pattern, t, re.I):
            # A rejected token must not override an explicit statement title
            # such as "Consolidated Financial Statements ... Basel" only when
            # the statement phrase is present and the reject was weak.
            if reason in {"committee", "news"} and re.search(
                    r"financial statements?|القوائم المالية", t, re.I):
                continue
            return None, reason
    if _ANNUAL_REPORT.search(t):
        return "annual_report", None
    if _STATEMENT.search(t):
        return "statement", None
    return None, "not_financial"


_SUPPORTING = [
    ("pillar3", r"pillar ?(?:3|iii)|basel|بازل|الركيزة الثالثة|risk disclosures?|"
                r"leverage|capital adequacy|liquidity coverage|\blcr\b|nsfr"),
    ("data_supplement", r"data ?supplement|financial ?supplement|financial data pack|"
                        r"ملحق البيانات|ملحق مالي"),
    ("factsheet", r"fact ?sheet|ملخص مالي|ورقة حقائق"),
]


def supporting_type(text: str) -> str | None:
    """pillar3 / data_supplement / factsheet, else None (own bucket, never FS)."""
    t = " ".join((text or "").split())
    for name, pattern in _SUPPORTING:
        if re.search(pattern, t, re.I):
            return name
    return None


def classify_bucket(text: str) -> tuple[str, str | None]:
    """('supporting', type) | ('statement', doc_type) | ('rejected', reason)."""
    sup = supporting_type(text)
    if sup:
        return "supporting", sup
    dtype, reason = classify_document_type(text)
    if dtype:
        return "statement", dtype
    return "rejected", reason


def variant_flags(text: str) -> dict:
    t = " ".join((text or "").split())
    scope = "consolidated" if re.search(r"consolidated|موحد", t, re.I) else (
        "standalone" if re.search(r"stand[- ]?alone|separate|منفصل|مستقل", t, re.I) else None)
    return {
        "scope": scope,
        "amended": bool(re.search(
            r"amended|restated|revised|corrected|addendum|updated|\bv[2-9]\b|"
            r"معدل|مصحح|ملحق تصحيحي|معاد", t, re.I)),
    }


# --------------------------------------------------------------------------
# period classification

_Y = r"(20\d{2}|\d{2})(?!\d)"


def _yy(v: str) -> int:
    n = int(v)
    return n if n >= 100 else 2000 + n


def period_from_filename(text: str) -> tuple[str | None, int | None]:
    """Compact codes such as 2q13, q22015, 2015q3, fy2019, 3Q-2020."""
    t = (text or "").lower()
    for pat, qg, yg in [
        (r"(?<!\d)([1-4])q[-_ ]?" + _Y, 1, 2),
        (r"(?<![a-z\d])q([1-4])[-_ ]?" + _Y, 1, 2),
        (r"(?<!\d)(20\d{2})[-_ ]?q([1-4])(?!\d)", 2, 1),
    ]:
        m = re.search(pat, t)
        if m:
            q = int(m.group(qg))
            return {1: "Q1", 2: "H1", 3: "9M", 4: None}[q], _yy(m.group(yg))
    m = re.search(r"(?<![a-z])fy[-_ ]?" + _Y, t) or re.search(r"(20\d{2})[-_ ]?fy", t)
    if m:
        return "FY", _yy(m.group(1))
    return None, None

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
     "nov", "dec"], 1)}
_AR_MONTHS = {"يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "ابريل": 4,
              "مايو": 5, "يونيو": 6, "يوليو": 7, "أغسطس": 8, "اغسطس": 8,
              "سبتمبر": 9, "أكتوبر": 10, "اكتوبر": 10, "نوفمبر": 11,
              "ديسمبر": 12}

_MONTH_COUNT = [
    (r"twelve months|12[- ]months?|year[- ]?ended|year ending|for the year|"
     r"annual|full[- ]year|\bfy\b|السنة المنتهية|سنوية|السنوي|اثني عشر|12 شهر", 12),
    (r"nine[- ]months?|9[- ]months?|9m\b|\bq3\b|third quarter|3rd quarter|"
     r"تسعة أشهر|التسعة أشهر|تسع أشهر|الربع الثالث|الثلاثة أرباع|9 أشهر", 9),
    (r"six[- ]months?|6[- ]months?|half[- ]year|half year|\bh1\b|\bq2\b|"
     r"second quarter|2nd quarter|1st half|first half|"
     r"ستة أشهر|الستة أشهر|ست أشهر|الربع الثاني|النصف الأول|6 أشهر", 6),
    (r"three[- ]months?|3[- ]months?|\bq1\b|first quarter|1st quarter|"
     r"ثلاثة أشهر|الثلاثة أشهر|ثلاث أشهر|الربع الأول|3 أشهر", 3),
]
# Quarter words alone (Q4 = fourth quarter) are a discrete quarter, not
# cumulative; they are reported as period_slot None so they are not covered.
_Q4 = re.compile(r"\bq4\b|fourth quarter|4th quarter|الربع الرابع", re.I)


def _find_dates(text: str) -> list[date]:
    out: list[date] = []
    for m in re.finditer(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out.append((y, mo, d))
    for m in re.finditer(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", text):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out.append((y, mo, d))
    for m in re.finditer(
            r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]{3})[a-z]*[,\s]+(\d{4})",
            text):
        mo = _MONTHS.get(m.group(2).lower())
        if mo:
            out.append((int(m.group(3)), mo, int(m.group(1))))
    for m in re.finditer(r"([A-Za-z]{3})[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?[,\s]+(\d{4})", text):
        mo = _MONTHS.get(m.group(1).lower())
        if mo:
            out.append((int(m.group(3)), mo, int(m.group(2))))
    for m in re.finditer(r"(\d{1,2})\s+(" + "|".join(_AR_MONTHS) + r")\s+(\d{4})", text):
        out.append((int(m.group(3)), _AR_MONTHS[m.group(2)], int(m.group(1))))
    good = []
    for y, mo, d in out:
        try:
            if 2000 <= y <= 2100:
                good.append(date(y, mo, d))
        except ValueError:
            pass
    return good


def period_end_from_text(text: str) -> date | None:
    """Pick the period-end date: an explicit 'ended/ending/ended on' date wins."""
    t = " ".join((text or "").split())
    m = re.search(
        r"(?:ended|ending|as (?:at|of)|period ended|المنتهي[ةه]? في|المنتهية في|"
        r"كما في)\s*(?:on\s*)?(.{0,40})", t, re.I)
    if m:
        ds = _find_dates(m.group(1))
        if ds:
            return ds[0]
    ds = _find_dates(t)
    return max(ds) if ds else None


def _months_from_fiscal_start(period_end: date, fy_end_month: int) -> int:
    return ((period_end.month - fy_end_month - 1) % 12) + 1


def classify_period(text: str, fy_end_month: int = 12,
                    period_end: date | None = None) -> dict:
    """Classify a title/filename/first-page text into Q1/H1/9M/FY.

    Returns {period_slot, fiscal_year, period_end, method}.  period_slot is
    None when it cannot be decided (the caller files it as unclassified).
    Non-calendar fiscal years: when the period-end date is known its month
    (relative to the fiscal-year end month) decides the slot, unless the text
    states an explicit month count.
    """
    t = " ".join((text or "").split())
    pe = period_end or period_end_from_text(t)
    months = None
    best = None
    found: set = set()
    for pattern, n in _MONTH_COUNT:
        m = re.search(pattern, t, re.I)
        # The earliest phrase wins: comparatives ("... and year ended ...")
        # come after the primary period in statement titles.
        if m:
            found.add(n)
        if m and (best is None or m.start() < best):
            best, months = m.start(), n
    if pe and found:
        # The period-end month is authoritative when the text also names
        # that cumulative length ("three months and nine months ... 30 Sep").
        derived = _months_from_fiscal_start(pe, fy_end_month)
        if derived in found:
            months = derived
    method = "text"
    if months is None and _Q4.search(t):
        return {"period_slot": None, "fiscal_year": pe.year if pe else None,
                "period_end": pe.isoformat() if pe else None,
                "method": "discrete_q4"}
    if months is None and pe:
        n = _months_from_fiscal_start(pe, fy_end_month)
        months = n if n in (3, 6, 9, 12) else None
        method = "period_end_month"
    slot = {3: "Q1", 6: "H1", 9: "9M", 12: "FY"}.get(months)
    fn_slot, fn_year = period_from_filename(t)
    if slot is None and fn_slot:
        slot, method = fn_slot, "filename_code"
    if slot is not None and fn_slot not in (None, slot):
        fn_year = None      # conflicting code: do not borrow its year
    fiscal_year = None
    if pe:
        fiscal_year = fiscal_year_of(pe, fy_end_month)
    elif fn_year:
        fiscal_year = fn_year
    else:
        y = re.findall(r"(?<!\d)(20\d{2})(?!\d)", t)
        if y:
            fiscal_year = max(int(v) for v in y)
        method = method + "_year_only" if slot else method
    return {"period_slot": slot, "fiscal_year": fiscal_year,
            "period_end": pe.isoformat() if pe else None, "method": method}


# --------------------------------------------------------------------------
# expected slots / coverage matrix


def slot_for_period_end(period_end: date, fy_end_month: int = 12) -> str | None:
    n = _months_from_fiscal_start(period_end, fy_end_month)
    return {3: "Q1", 6: "H1", 9: "9M", 12: "FY"}.get(n)


def fiscal_year_of(period_end: date, fy_end_month: int = 12) -> int:
    return period_end.year + (1 if period_end.month > fy_end_month else 0)


def expected_slots(period_ends: list[date], fy_end_month: int = 12) -> dict:
    """{(fiscal_year, slot): period_end_iso} anchored on Saudi Exchange dates."""
    out = {}
    for pe in sorted(set(period_ends)):
        slot = slot_for_period_end(pe, fy_end_month)
        if slot:
            out[(fiscal_year_of(pe, fy_end_month), slot)] = pe.isoformat()
    return out


class Ledger:
    """Collected documents + missing-slot reasons for one company."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.docs: list[dict] = []
        self.rejected: list[dict] = []
        self.unclassified: list[dict] = []
        self.failures: list[dict] = []
        self.expected: dict = {}
        self.slot_reasons: dict = {}     # (fy, slot) -> reason
        self.company_reason: str | None = None

    def add_doc(self, doc: dict) -> None:
        if any(d["content_hash"] == doc["content_hash"] for d in self.docs):
            return
        self.docs.append(doc)

    def coverage(self) -> dict:
        """Years x slots -> collected(hash) | missing(reason) | not_expected."""
        collected: dict = defaultdict(list)
        via_ar: dict = defaultdict(list)
        for d in self.docs:
            if d.get("bucket", "statement") != "statement":
                continue
            fy, slot = d.get("fiscal_year"), d.get("period_slot")
            if not fy or not slot:
                continue
            if d["document_type"] == "annual_report":
                if slot == "FY":
                    via_ar[(fy, slot)].append(d["content_hash"])
                continue
            collected[(fy, slot)].append(d["content_hash"])
        years = sorted({k[0] for k in self.expected} |
                       {k[0] for k in collected} | {k[0] for k in via_ar})
        matrix = {}
        for y in years:
            row = {}
            for s in SLOTS:
                key = (y, s)
                if key in collected:
                    hs = sorted(collected[key], key=lambda h: (
                        self._doc(h).get("language") != "en",
                        bool(self._doc(h).get("amended")), h))
                    row[s] = {"status": "collected", "hash": hs[0],
                              "distinct_files": len(hs),
                              "same_language_extras": len(hs) - len(
                                  {self._doc(h).get("language") for h in hs}),
                              "variants": [self._variant(h) for h in hs]}
                elif key in via_ar:
                    row[s] = {"status": "collected_via_annual_report",
                              "hash": via_ar[key][0]}
                elif key in self.expected:
                    row[s] = {"status": "missing",
                              "reason": self.slot_reasons.get(key) or
                              self.company_reason or "not_found_at_sources"}
                else:
                    row[s] = {"status": "not_expected",
                              "reason": "period_not_in_saudi_exchange_list"}
            matrix[y] = row
        return matrix

    def _doc(self, h: str) -> dict:
        return next((d for d in self.docs if d["content_hash"] == h), {})

    def _variant(self, h: str) -> dict:
        d = self._doc(h)
        return {"hash": h, "language": d.get("language"), "scope": d.get("scope"),
                "amended": d.get("amended", False), "source": d.get("source")}

    def supporting_counts(self) -> dict:
        out = {"pillar3": 0, "data_supplement": 0, "factsheet": 0}
        for d in self.docs:
            if d.get("bucket") == "supporting":
                out[d["supporting_type"]] = out.get(d["supporting_type"], 0) + 1
        return out

    def counts(self) -> dict:
        c = {s: 0 for s in SLOTS}
        via = 0
        for d in self.docs:
            if d.get("bucket", "statement") != "statement":
                continue
            if not d.get("period_slot"):
                continue
            if d["document_type"] == "annual_report":
                via += 1 if d["period_slot"] == "FY" else 0
            else:
                c[d["period_slot"]] += 1
        c["fy_via_annual_report"] = via
        c["unclassified"] = sum(
            1 for d in self.docs if d.get("bucket", "statement") == "statement"
            and not (d.get("period_slot") and d.get("fiscal_year")))
        return c


# --------------------------------------------------------------------------
# archive layout / state


def archive_path(root: Path, symbol: str, digest: str, kind: str,
                 bucket: str = "statement") -> Path:
    base = Path(root) / "archive" / "SA" / str(symbol)
    if bucket == "supporting":
        base = base / "supporting"
    return base / f"{digest}.{kind}"


def remote_target(symbol: str, digest: str, kind: str,
                  bucket: str = "statement") -> str:
    sub = "documents/supporting" if bucket == "supporting" else "documents"
    return f"/app/state/raw/SA/{symbol}/{sub}/{digest}.{kind}"


def outbox_row(symbol: str, local_path: Path, digest: str, kind: str,
               bucket: str = "statement") -> dict:
    return {"symbol": str(symbol), "local_path": str(local_path),
            "sha256": digest, "bucket": bucket,
            "remote_path": remote_target(symbol, digest, kind, bucket)}


def upload_commands(server: str, worker: str, ssh_key, known_hosts,
                    symbol: str, local_path, digest: str, kind: str,
                    bucket: str = "statement") -> list[list[str]]:
    """Raw-copy part of windows_tadawul_relay._remote_publish.

    mkdir + scp + docker cp into the raw archive dir.  Never `relay-enqueue`.
    Returned as argv lists; nothing is executed here.
    """
    remote_name = f"{symbol}-{digest}.{kind}"
    host_path = f"/tmp/finengine-relay/{remote_name}"
    container_file = f"/tmp/{remote_name}"
    opts = ["-o", f"UserKnownHostsFile={known_hosts}", "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=15", "-o", "ConnectionAttempts=1",
            "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=2"]
    ssh = ["ssh", "-i", str(ssh_key), *opts, server]
    scp = ["scp", "-i", str(ssh_key), *opts]
    archive_dir = f"/app/state/raw/SA/{symbol}/documents" + (
        "/supporting" if bucket == "supporting" else "")
    return [
        ssh + ["mkdir", "-p", "/tmp/finengine-relay"],
        scp + [str(local_path), f"{server}:{host_path}"],
        ssh + ["docker", "cp", host_path, f"{worker}:{container_file}"],
        ssh + ["docker", "exec", worker, "mkdir", "-p", archive_dir],
        ssh + ["docker", "cp", host_path,
               f"{worker}:{archive_dir}/{digest}.{kind}"],
    ]


def commands_are_raw_only(commands: list[list[str]]) -> bool:
    return not any("relay-enqueue" in " ".join(c) for c in commands)


def normalize_website(value: str | None) -> str | None:
    """Repair malformed Saudi Exchange 'Website' values (http://https://x)."""
    v = (value or "").strip()
    if not v or v in {"-", "N/A", "n/a"}:
        return None
    v = re.sub(r"^(https?://)+(https?://)", r"\2", v, flags=re.I)
    v = re.sub(r"^https?://", "", v, flags=re.I).strip("/ ")
    if not v or " " in v or "." not in v:
        return None
    return "https://" + v


__all__ = [n for n in dir() if not n.startswith("_")]
