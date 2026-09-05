from __future__ import annotations

"""Reader agent: turn a filed PDF into a source-faithful manifest.

Deterministic first - it reconstructs the three primary statement tables from
the PDF's own text-with-coordinates and maps only lines it can name with
confidence. It never invents a number and never writes to production; its
output is a staging manifest that must still pass `finengine verify` and the
publication pipeline. A probabilistic/LLM pass belongs behind this, only for
pages this cannot read (scans, Arabic-only bidi tables), and only writing the
same manifest shape.

Requires the optional `pymupdf` extra.
"""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

ANCHORS = {
    "income_statement": (
        "statement of profit or loss", "statement of income", "income statement",
        "statement of comprehensive income", "قائمة الربح أو الخسارة", "قائمة الدخل",
    ),
    "balance_sheet": (
        "statement of financial position", "balance sheet", "قائمة المركز المالي",
    ),
    "cash_flow": (
        "statement of cash flows", "cash flow statement", "قائمة التدفقات النقدية",
    ),
}

# Normalised label substring -> (canonical metric, period_kind). Longest match wins.
# Order within a statement does not matter; specificity (length) breaks ties.
LINE_MAP = {
    # income statement
    "revenue": ("revenue", "fy"),
    "revenues": ("revenue", "fy"),
    "sales revenue": ("revenue", "fy"),
    "revenue and other income related to sales": ("revenue_and_other_income_related_to_sales", "fy"),
    "other income related to sales": ("other_income_related_to_sales", "fy"),
    "cost of sales": ("cost_of_revenue", "fy"),
    "cost of revenue": ("cost_of_revenue", "fy"),
    "gross profit": ("gross_profit", "fy"),
    "operating profit": ("operating_income", "fy"),
    "operating income": ("operating_income", "fy"),
    "profit from operations": ("operating_income", "fy"),
    "results from operating activities": ("operating_income", "fy"),
    "profit before zakat and income tax": ("income_before_income_taxes_and_zakat", "fy"),
    "profit before tax": ("income_before_income_taxes_and_zakat", "fy"),
    "income before income taxes and zakat": ("income_before_income_taxes_and_zakat", "fy"),
    "profit for the year": ("net_income", "fy"),
    "profit for the period": ("net_income", "fy"),
    "net income": ("net_income", "fy"),
    "net profit": ("net_income", "fy"),
    "profit for the year attributable to": ("net_income_parent", "fy"),
    "attributable to shareholders of the company": ("net_income_parent", "fy"),
    "attributable to equity holders": ("net_income_parent", "fy"),
    "attributable to owners": ("net_income_parent", "fy"),
    # balance sheet
    "total assets": ("total_assets", "instant"),
    "non-current assets": ("noncurrent_assets", "instant"),
    "total non-current assets": ("noncurrent_assets", "instant"),
    "current assets": ("current_assets", "instant"),
    "total current assets": ("current_assets", "instant"),
    "total equity": ("total_equity", "instant"),
    "total liabilities": ("total_liabilities", "instant"),
    "non-current liabilities": ("noncurrent_liabilities", "instant"),
    "total non-current liabilities": ("noncurrent_liabilities", "instant"),
    "current liabilities": ("current_liabilities", "instant"),
    "total current liabilities": ("current_liabilities", "instant"),
    "total equity and liabilities": ("total_liabilities_equity", "instant"),
    "total liabilities and equity": ("total_liabilities_equity", "instant"),
    "cash and cash equivalents": ("cash", "instant"),
    "property, plant and equipment": ("property_plant_equipment", "instant"),
    "inventories": ("inventory", "instant"),
    "share capital": ("share_capital", "instant"),
    "retained earnings": ("retained_earnings", "instant"),
    "equity attributable to": ("equity_parent", "instant"),
    "equity attributable to equity holders": ("equity_parent", "instant"),
    "non-controlling interest": ("noncontrolling_interests", "instant"),
    # cash flow
    "net cash from operating activities": ("operating_cash_flow", "fy"),
    "net cash generated from operating activities": ("operating_cash_flow", "fy"),
    "net cash provided by operating activities": ("operating_cash_flow", "fy"),
    "cash flows from operating activities": ("operating_cash_flow", "fy"),
    "net cash used in investing activities": ("investing_cash_flow", "fy"),
    "net cash from investing activities": ("investing_cash_flow", "fy"),
    "net cash from financing activities": ("financing_cash_flow", "fy"),
    "net cash used in financing activities": ("financing_cash_flow", "fy"),
    "net cash from/(used in) financing activities": ("financing_cash_flow", "fy"),
    "net change in cash and cash equivalents": ("cash_change", "fy"),
    "net increase in cash and cash equivalents": ("cash_change", "fy"),
    "net decrease in cash and cash equivalents": ("cash_change", "fy"),
    "cash and cash equivalents at 1 january": ("cash_beginning", "fy"),
    "cash and cash equivalents at the beginning": ("cash_beginning", "fy"),
    "cash and cash equivalents at 31 december": ("cash_end", "fy"),
    "cash and cash equivalents at the end": ("cash_end", "fy"),
    "effect of movements in exchange rates on cash": ("foreign_exchange_effect", "fy"),
    "effect of exchange rate changes on cash": ("foreign_exchange_effect", "fy"),
}

# non-controlling interest inside the income statement means a different metric
_PL_OVERRIDES = {"noncontrolling_interests": "net_income_noncontrolling"}

_SCALE_PATTERNS = (
    (re.compile(r"in\s+thousands|'?000'?|bآ?لاف\s+الريالات|بالآلاف", re.I), Decimal(1000)),
    (re.compile(r"in\s+millions|s?r?\s*million|بالملايين|مليون", re.I), Decimal(1_000_000)),
    (re.compile(r"in\s+billions|بالمليارات", re.I), Decimal(1_000_000_000)),
)
_NUMBER = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?$")
_YEAR = re.compile(r"\b(19|20)\d{2}\b")


def _parse_number(token: str) -> Decimal | None:
    token = token.strip().replace(",", "").replace("–", "-").replace("—", "-")
    if token in {"", "-", "–", "—", "�", "n/a"}:
        return None
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()")
    try:
        value = Decimal(token)
    except InvalidOperation:
        return None
    return -value if negative else value


def _rows(words, y_tol: float = 3.0):
    ordered = sorted(words, key=lambda w: (w[1], w[0]))
    rows, current, anchor = [], [], None
    for w in ordered:
        if anchor is None or abs(w[1] - anchor) <= y_tol:
            current.append(w)
            anchor = w[1] if anchor is None else anchor
        else:
            rows.append(sorted(current, key=lambda x: x[0]))
            current, anchor = [w], w[1]
    if current:
        rows.append(sorted(current, key=lambda x: x[0]))
    return rows


def _resolve_line(label: str, statement: str) -> str | None:
    # A stock line ("property, plant and equipment") also appears inside a
    # cash-flow note ("purchase of property, plant and equipment") or an
    # equity roll-forward; only accept a match on the statement its LINE_MAP
    # kind actually belongs to, or a balance-sheet line reads as a bogus
    # extra fact wherever else that phrase happens to occur.
    wants_instant = statement == "balance_sheet"
    norm = " ".join(label.lower().split())
    best = None
    for phrase, (metric, kind) in LINE_MAP.items():
        compatible = (kind == "instant") == wants_instant
        if not compatible and statement == "income_statement" and metric in _PL_OVERRIDES:
            compatible = True  # e.g. "non-controlling interest" reread as a P&L split
        if not compatible:
            continue
        if phrase in norm and (best is None or len(phrase) > len(best[0])):
            best = (phrase, metric)
    if best is None:
        return None
    metric = best[1]
    if statement == "income_statement" and metric in _PL_OVERRIDES:
        return _PL_OVERRIDES[metric]
    return metric


class StatementReader:
    def __init__(self, pdf_path: str | Path):
        try:
            import pymupdf  # noqa: F401
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError("the reader agent needs the optional 'pymupdf' package") from error
        self.pdf_path = Path(pdf_path)

    def infer_fiscal_year(self) -> int | None:
        """The reporting year printed on the statements themselves - the
        left (current-period) column of whichever confirmed statement pages
        exist. Used so an unattended job never has to be told the period."""
        import pymupdf

        doc = pymupdf.open(self.pdf_path)
        try:
            votes: dict[int, int] = {}
            for page_index in range(doc.page_count):
                page = doc[page_index]
                words = page.get_text("words")
                if not self._heading_statement(page, words):
                    continue
                columns = self._year_columns(page, words)
                if not columns:
                    continue
                top = (page.rect.height or 1000) * 0.45
                years = [int(w[4]) for w in words
                         if _YEAR.fullmatch(w[4]) and w[1] < top and 2010 <= int(w[4]) <= 2035
                         and abs((w[0] + w[2]) / 2 - columns[0]) < 20]
                if years:
                    year = max(years)  # the current period is the newest year in its column
                    votes[year] = votes.get(year, 0) + 1
            return max(votes, key=votes.get) if votes else None
        finally:
            doc.close()

    def read(self, market: str, symbol: str, currency: str,
             source_url: str, filed_at: str, period_end: str | None = None,
             fiscal_year: int | None = None, filing_type: str = "financial-statements") -> dict:
        import pymupdf

        if fiscal_year is None:
            fiscal_year = self.infer_fiscal_year()
            if fiscal_year is None:
                raise ValueError(
                    f"could not infer the reporting year from {self.pdf_path.name}; "
                    "pass fiscal_year explicitly")
        if period_end is None:
            period_end = f"{fiscal_year}-12-31"

        doc = pymupdf.open(self.pdf_path)
        facts: list[dict] = []
        seen: set[tuple[str, str]] = set()
        carry: str | None = None
        carry_page = -99
        for page_index in range(doc.page_count):
            page = doc[page_index]
            words = page.get_text("words")
            blocks = self._column_blocks(page, words)
            columns = blocks[0] if blocks else []
            heading = self._heading_statement(page, words)
            continuation = bool(
                carry and page_index - carry_page == 1 and columns
                and self._looks_tabular(words, columns))
            if heading:
                statement = heading
            elif continuation:
                statement = carry  # the page right after a statement heading
            else:
                carry = None
                continue
            if not blocks:
                carry = None
                continue
            carry, carry_page = statement, page_index
            scale = self._scale(page.get_text().lower())
            page_facts: list = []
            for label, kind, value in self._statement_facts(words, statement, blocks):
                metric = _resolve_line(label, statement)
                if metric is None:
                    continue
                monetary = metric != "eps_diluted"
                key = (metric, kind)
                if key in seen:
                    continue
                fact = {
                    "metric": metric, "source_label": label.strip(), "value": str(value),
                    "period_end": period_end, "period_kind": kind,
                    "fiscal_year": fiscal_year, "page": page_index + 1,
                }
                if kind in {"fy", "ytd", "quarter"}:
                    fact["period_start"] = f"{fiscal_year}-01-01"
                if monetary:
                    fact.update(scale=str(scale), currency=currency, unit=currency)
                page_facts.append((key, fact))
            # The page is already a confirmed statement (leading-heading regex or a
            # continuation of one); a single new mapped line is enough to keep it,
            # and keeps `carry` alive for the rest of a multi-page statement.
            for key, fact in page_facts:
                seen.add(key)
                facts.append(fact)
        doc.close()
        return {
            "filing_type": filing_type, "filed_at": filed_at, "period_end": period_end,
            "source_url": source_url, "reader": "finengine.reading/1",
            "facts": sorted(facts, key=lambda f: (f["page"], f["metric"])),
        }

    @staticmethod
    def _scale(page_text: str) -> Decimal:
        for pattern, value in _SCALE_PATTERNS:
            if pattern.search(page_text):
                return value
        return Decimal(1)

    _NEGATIVE = ("highlights", "at a glance", "key figures", "financial review",
                 "five year", "5-year", "five-year", "summary", "summarised",
                 "summarized", "condensed", "snapshot", "performance review",
                 "review", "commentary")

    # A real primary statement carries these signature line labels; a summary
    # table titled the same way usually does not carry all of them.
    _SIGNATURE = {
        "income_statement": (("revenue", "sales", "turnover"),
                             ("profit for the", "net income", "net profit", "loss for the")),
        "balance_sheet": (("total assets",),
                          ("total equity", "total liabilities", "equity and liabilities")),
        "cash_flow": (("operating activities",), ("financing activities",)),
    }

    _HEADING_PREFIX = re.compile(
        r"^(consolidated |interim |unaudited |condensed )*"
        r"(statement of |statements of |income statement|balance sheet|"
        r"قائمة )", re.I)

    def _heading_statement(self, page, words) -> str | None:
        top = (page.rect.height or 1000) * 0.42
        for row in _rows([w for w in words if w[1] < top]):
            text = " ".join(w[4] for w in row).lower().strip()
            # A persistent side-nav ("At a glance", "Financial review", ...)
            # sits in this same zone on every page of a glossy annual report
            # and must not veto pages it happens to share the top-42% band
            # with - only distrust a row that itself looks like a heading.
            if len(text) > 75 or not self._HEADING_PREFIX.match(text):
                continue
            if any(bad in text for bad in self._NEGATIVE):
                return None
            for name, anchors in ANCHORS.items():
                if any(a in text for a in anchors):
                    return name
        return None

    @staticmethod
    def _column_blocks(page, words) -> list[list[float]]:
        """Up to two side-by-side statement panels on one page (e.g. assets on
        the left, equity and liabilities on the right of a landscape balance
        sheet) - each with its own period columns, current period first
        (leftmost) within its panel. A gap over 150pt between consecutive
        year hits marks a new panel."""
        top = (page.rect.height or 1000) * 0.45
        hits = sorted({round((w[0] + w[2]) / 2, 1) for w in words
                       if _YEAR.fullmatch(w[4]) and w[1] < top and 2010 <= int(w[4]) <= 2035})
        if not hits:
            return []
        blocks: list[list[float]] = [[hits[0]]]
        for x in hits[1:]:
            (blocks.append([x]) if x - blocks[-1][-1] > 150 else blocks[-1].append(x))
        result = []
        for block in blocks:
            columns: list[float] = []
            for x in block:
                if not columns or x - columns[-1] > 25:
                    columns.append(x)
            result.append(columns[:2])
        return result[:2]

    @staticmethod
    def _year_columns(page, words) -> list[float]:
        """x-centres of the first panel's period columns, current period first."""
        blocks = StatementReader._column_blocks(page, words)
        return blocks[0] if blocks else []

    @staticmethod
    def _block_boundary(words, blocks: list[list[float]]) -> float | None:
        """The x that separates a two-panel page's left and right blocks.
        The right panel's own labels ("Share capital", "Total equity", ...)
        sit well before its value columns, so the boundary is not the gap
        around the value columns themselves - it is just before whichever
        label text is the first thing found strictly between the two
        panels' own column geometry (left panel's rightmost column and
        right panel's leftmost column)."""
        if len(blocks) < 2:
            return None
        left_edge, right_edge = max(blocks[0]), min(blocks[1])
        if right_edge <= left_edge:
            return None
        labels_between = [w[0] for w in words
                          if left_edge < w[0] < right_edge and not _NUMBER.match(w[4])]
        return (min(labels_between) - 5) if labels_between else (left_edge + right_edge) / 2

    @staticmethod
    def _aligned_rows(words, columns) -> int:
        count = 0
        for row in _rows(words):
            has_label = any(not _NUMBER.match(w[4]) and len(w[4]) > 2 for w in row)
            has_value = any(
                _NUMBER.match(w[4]) and any(abs((w[0] + w[2]) / 2 - c) < 45 for c in columns)
                for w in row)
            count += bool(has_label and has_value)
        return count

    def _looks_tabular(self, words, columns) -> bool:
        return self._aligned_rows(words, columns) >= 6

    def _statement_facts(self, words, statement: str, blocks: list[list[float]]):
        boundary = self._block_boundary(words, blocks) if len(blocks) > 1 else None
        magnitudes = []
        parsed_rows = []
        for row in _rows(words):
            if boundary is None:
                panels = [(row, blocks[0])]
            else:
                left = [w for w in row if w[0] < boundary]
                right = [w for w in row if w[0] >= boundary]
                panels = [seg for seg in ((left, blocks[0]), (right, blocks[1])) if seg[0]]
            for panel_words, columns in panels:
                current = columns[0]
                note_zone = (min(columns) - 90, min(columns) - 25)  # lone note refs sit just left of the values
                text_tokens, number_tokens = [], []
                for w in panel_words:
                    token = w[4]
                    center = (w[0] + w[2]) / 2
                    if _NUMBER.match(token) and any(abs(center - c) < 45 for c in columns):
                        value = _parse_number(token)
                        if value is not None:
                            number_tokens.append((center, value))
                    elif token.isdigit() and len(token) <= 3 and note_zone[0] < center < note_zone[1]:
                        continue  # a note-reference number, not part of the label
                    else:
                        text_tokens.append(token)
                if not text_tokens or not number_tokens:
                    continue
                label = " ".join(text_tokens).strip(" :.-")
                words_in_label = label.split()
                if not 1 <= len(words_in_label) <= 13 or "%" in label or _YEAR.search(label):
                    continue
                value = min(number_tokens, key=lambda t: abs(t[0] - current))[1]
                magnitudes.append(abs(value))
                parsed_rows.append((label, value))
        if not magnitudes:
            return
        floor = sorted(magnitudes)[len(magnitudes) // 2] / Decimal(1000)  # 0.1% of median
        for label, value in parsed_rows:
            if abs(value) < floor:
                continue  # a stray percentage or ratio among monetary rows
            kind = "instant" if statement == "balance_sheet" else "fy"
            yield label, kind, value
