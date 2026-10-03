"""Per-file content scan (read-only). Heuristic, text-layer based. Never modifies raw files."""
import hashlib
import os
import re
import unicodedata
import zipfile
from datetime import date

try:
    import pymupdf
    pymupdf.TOOLS.mupdf_display_errors(False)
except Exception:  # pragma: no cover
    pymupdf = None

MAX_PAGES = 320
_STMT_EN = {
    "financial_position": r"statements?\s+of\s+financial\s+(position|condition)|balance\s+sheets?",
    "income": r"statements?\s+of\s+(profit\s+or\s+loss|income|comprehensive\s+income|operations|profit\s+and\s+loss|earnings|insurance\s+operations)|income\s+statements?",
    "cash_flows": r"statements?\s+of\s+cash\s+flows?|cash\s+flows?\s+statements?",
    "equity": r"statements?\s+of\s+changes\s+in\s+(shareholders|stockholders|owners|equity|net\s+assets|unitholders)",
}
_STMT_AR = {
    "financial_position": r"المركز المالي|الميزانية العمومية",
    "income": r"قائمة الدخل|الربح او الخسارة|الارباح او الخسائر|الدخل الشامل|الربح أو الخسارة|الأرباح أو الخسائر",
    "cash_flows": r"التدفقات النقدية",
    "equity": r"التغيرات? في حقوق|التغير في حقوق",
}
STMT_EN = {k: re.compile(v, re.I) for k, v in _STMT_EN.items()}
STMT_AR = {k: re.compile(v) for k, v in _STMT_AR.items()}
NOTES_RE = re.compile(r"notes\s+to\s+(the\s+)?(condensed\s+)?(interim\s+)?(consolidated\s+)?financial\s+statements|ايضاحات|إيضاحات")
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
AR_MONTHS = {"يناير": 1, "فبراير": 2, "مارس": 3, "ابريل": 4, "أبريل": 4, "مايو": 5, "يونيو": 6, "يوليو": 7,
             "اغسطس": 8, "أغسطس": 8, "سبتمبر": 9, "اكتوبر": 10, "أكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12}
D1 = re.compile(r"(?<!\d)(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+(20\d\d|19\d\d)", re.I)
D2 = re.compile(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d\d|19\d\d)", re.I)
D3 = re.compile(r"(?<!\d)(20\d\d)[-/](\d{1,2})[-/](\d{1,2})(?!\d)")
D4 = re.compile(r"(?<!\d)(\d{1,2})[-/](\d{1,2})[-/](20\d\d)(?!\d)")
DAR = re.compile(r"(?<!\d)(\d{1,2})\s+(" + "|".join(sorted(AR_MONTHS, key=len, reverse=True)) + r")\s+(20\d\d)")
DUR = [
    (3, re.compile(r"three\s+months?|quarter\s+ended|للثلاثة اشهر|للثلاثة أشهر|لفترة الثلاثة|ثلاثة اشهر|ثلاثة أشهر")),
    (6, re.compile(r"six\s+months?|للستة اشهر|للستة أشهر|لفترة الستة|ستة اشهر|ستة أشهر")),
    (9, re.compile(r"nine\s+months?|للتسعة اشهر|للتسعة أشهر|لفترة التسعة|تسعة اشهر|تسعة أشهر")),
    (12, re.compile(r"(year|twelve\s+months?)\s+ended|للسنة المنتهية|للسنه المنتهيه|سنة المنتهية|year\s+ending|annual\s+report|التقرير السنوي")),
]
KINDS = {
    "results_announcement": re.compile(r"announces?\s+(its\s+)?(interim|annual|financial|q[1-4]|\w+\s+quarter)|financial\s+results\s+(for|of)|تعلن شركة"),
    "presentation": re.compile(r"investor\s+presentation|earnings\s+(presentation|call)|results\s+presentation|العرض التقديمي"),
    "pillar3": re.compile(r"pillar\s*(3|iii)|basel\s+iii\s+disclosure"),
    "board_report": re.compile(r"board\s+of\s+directors['’]?\s+report|تقرير مجلس الادارة|تقرير مجلس الإدارة"),
}


def norm_text(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"[ـً-ٟ]", "", t)
    return re.sub(r"\s+", " ", t).lower()


def arabic_variants(t: str):
    """NFKC text plus word-order-reversed copies (many PDFs store Arabic visually)."""
    n = norm_text(t)
    yield n
    if re.search(r"[؀-ۿ]", n):
        yield " ".join(reversed(n.split(" ")))
        yield n[::-1]


def sha256_file(path, bufsize=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _month_end(y, m, d):
    try:
        dt = date(y, m, d)
    except ValueError:
        return None
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return dt if d == (nxt - date(y, m, 1)).days else None


def dates_in(t: str):
    out = set()
    for m in D1.finditer(t):
        r = _month_end(int(m.group(3)), MONTHS[m.group(2)[:3].lower()], int(m.group(1)))
        if r:
            out.add(r)
    for m in D2.finditer(t):
        r = _month_end(int(m.group(3)), MONTHS[m.group(1)[:3].lower()], int(m.group(2)))
        if r:
            out.add(r)
    for m in D3.finditer(t):
        if 1 <= int(m.group(2)) <= 12:
            r = _month_end(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if r:
                out.add(r)
    for m in D4.finditer(t):
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        for d_, m_ in ((a, b), (b, a)):
            if 1 <= m_ <= 12:
                r = _month_end(y, m_, d_)
                if r:
                    out.add(r)
    for m in DAR.finditer(t):
        r = _month_end(int(m.group(3)), AR_MONTHS[m.group(2)], int(m.group(1)))
        if r:
            out.add(r)
    return out


def scan_pdf(path):
    res = {"kind": "pdf"}
    if pymupdf is None:
        res["error"] = "pymupdf_missing"
        return res
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        res["error"] = f"open_failed:{str(e)[:80]}"
        return res
    try:
        if doc.needs_pass:
            res["error"] = "encrypted"
            return res
        n = doc.page_count
        res["pages"] = n
        lim = min(n, MAX_PAGES)
        res["pages_scanned"] = lim
        chars = empty = 0
        stmts = {k: [] for k in STMT_EN}
        notes_pages = []
        front = []
        stmt_text = []
        kinds = set()
        dur = set()
        digest_src = ""
        for i in range(lim):
            try:
                t = doc.load_page(i).get_text("text") or ""
            except Exception:
                t = ""
            c = len(t.strip())
            chars += c
            if c < 40:
                empty += 1
                continue
            if i < 3:
                front.append(t)
            if i < 2:
                digest_src += t
            digits = len(re.findall(r"\d[\d,\.]*", t))
            hit_here = set()
            head = t[:900]
            for v in arabic_variants(head):
                for k in STMT_EN:
                    if k not in hit_here and (STMT_EN[k].search(v) or STMT_AR[k].search(v)):
                        hit_here.add(k)
            if hit_here and digits >= 15 and len(hit_here) <= 3:
                for k in hit_here:
                    if len(stmts[k]) < 12:
                        stmts[k].append(i + 1)
                if len(stmt_text) < 6:
                    stmt_text.append(t[:2500])
            if i < 40 or hit_here:
                for v in arabic_variants(t[:1500]):
                    for kn, rx in KINDS.items():
                        if rx.search(v):
                            kinds.add(kn)
                    if NOTES_RE.search(v) and digits >= 8 and len(notes_pages) < 5:
                        notes_pages.append(i + 1)
            if i < 6 or hit_here:
                for v in arabic_variants(t[:2500]):
                    for m_, rx in DUR:
                        if rx.search(v):
                            dur.add(m_)
        res["text_chars"] = chars
        res["empty_pages"] = empty
        ratio = empty / lim if lim else 1
        res["empty_page_ratio"] = round(ratio, 3)
        if lim == 0:
            res["readability"] = "no_pages"
        elif chars < 100 or ratio >= 0.97:
            res["readability"] = "scanned_zero_text"
        elif ratio >= 0.6:
            res["readability"] = "mostly_scanned"
        elif ratio >= 0.25:
            res["readability"] = "mixed"
        else:
            res["readability"] = "text"
        res["statement_pages"] = {k: v for k, v in stmts.items() if v}
        res["primary_statements"] = sorted(k for k, v in stmts.items() if v)
        res["notes_pages"] = notes_pages
        res["content_kinds"] = sorted(kinds)
        res["duration_phrases"] = sorted(dur)
        ftxt = " ".join(front + stmt_text[:3])
        dts = set()
        for v in arabic_variants(ftxt):
            dts |= dates_in(v)
        res["period_end_candidates"] = sorted(d.isoformat() for d in dts)[-6:]
        res["period_end_detected"] = max(dts).isoformat() if dts else None
        norm_front = norm_text(" ".join(front))
        res["has_arabic"] = bool(re.search(r"[؀-ۿ]", norm_front))
        res["has_latin"] = bool(re.search(r"[a-z]{4,}", norm_front))
        res["front_text_norm"] = norm_front[:1500]
        res["digest_text_sha1"] = hashlib.sha1(norm_text(digest_src)[:4000].encode("utf8")).hexdigest() if digest_src else None
        res["title_line"] = front[0].strip().split("\n")[0][:120] if front else None
    finally:
        doc.close()
    return res


def scan_xlsx(path):
    res = {"kind": "xlsx", "readability": "text"}
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            wb = z.read("xl/workbook.xml").decode("utf8", "ignore") if "xl/workbook.xml" in names else ""
            res["sheets"] = re.findall(r'<sheet [^>]*name="([^"]+)"', wb)[:40]
            ss = z.read("xl/sharedStrings.xml").decode("utf8", "ignore") if "xl/sharedStrings.xml" in names else ""
        txt = norm_text(re.sub(r"<[^>]+>", " ", ss)) + " " + norm_text(" ".join(res["sheets"]))
        res["text_chars"] = len(txt)
        res["primary_statements"] = sorted(k for k in STMT_EN if STMT_EN[k].search(txt) or STMT_AR[k].search(txt))
        dts = dates_in(txt)
        res["period_end_candidates"] = sorted(d.isoformat() for d in dts)[-6:]
        res["period_end_detected"] = max(dts).isoformat() if dts else None
        res["front_text_norm"] = txt[:800]
        res["has_arabic"] = bool(re.search(r"[؀-ۿ]", txt))
        res["has_latin"] = bool(re.search(r"[a-z]{4,}", txt))
        res["duration_phrases"] = sorted(m for m, rx in DUR if rx.search(txt))
        res["content_kinds"] = []
        res["digest_text_sha1"] = hashlib.sha1(txt[:4000].encode("utf8")).hexdigest()
    except Exception as e:
        res["error"] = f"xlsx_failed:{str(e)[:80]}"
    return res


def scan_file(args):
    path, expect_hash = args
    out = {"path": path}
    try:
        out["size"] = os.path.getsize(path)
        out["sha256"] = sha256_file(path)
        out["hash_matches_name"] = (out["sha256"] == expect_hash) if expect_hash else None
        ext = os.path.splitext(path)[1].lower()
        out.update(scan_xlsx(path) if ext in (".xlsx", ".xlsm") else scan_pdf(path))
    except Exception as e:
        out["error"] = f"scan_failed:{str(e)[:100]}"
    return out
