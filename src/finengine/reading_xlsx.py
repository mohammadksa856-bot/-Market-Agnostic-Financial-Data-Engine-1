from __future__ import annotations

"""Reader for issuer 'data supplement' spreadsheets.

Large Saudi issuers (banks, SABIC, STC, Aramco, ...) publish a quarterly Excel
'data supplement' / 'fact sheet': one machine-readable file with the full income
statement and balance sheet across ~10 years of annual columns plus quarterly
history. It is a primary source produced by the company itself.

This reader turns one such file into a source-faithful manifest, the same shape
`finengine.reading` emits. It is driven by a per-issuer map
(`config/supplements/<symbol>.json`) because every supplement lays its rows out
differently. It ingests only the raw reported lines - the supplement's own
pre-computed ratios (ROE, NIM, cost-to-income, ...) are deliberately skipped;
the engine recomputes every ratio from the ingested lines.

Requires the optional `xlsx` extra (`openpyxl`). The core engine stays
dependency-free.
"""

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

_PERIOD = re.compile(r"^\s*(FY|1Q|2Q|3Q|4Q|1H|9M|H1|Q1|Q2|Q3|Q4)[\s\-]*(20\d{2})\s*$", re.I)
_TAGS = r"(FY|1Q|2Q|3Q|4Q|1H|9M|H1|Q1|Q2|Q3|Q4)"
# Same tags, other common header spellings: two-digit year ("1Q25", "Q1'25",
# "FY 25") and year-first ("2025 Q1", "2025-FY").
_PERIOD_SHORT = re.compile(rf"^\s*{_TAGS}[\s\-]*['’]?(\d{{2}})\s*$", re.I)
_PERIOD_YEAR_FIRST = re.compile(rf"^\s*(20\d{{2}})[\s\-]*{_TAGS}\s*$", re.I)
_QUARTER_END = {"1Q": "03-31", "2Q": "06-30", "3Q": "09-30", "4Q": "12-31",
                "Q1": "03-31", "Q2": "06-30", "Q3": "09-30", "Q4": "12-31"}
_CUMULATIVE_END = {"1h": "06-30", "h1": "06-30", "9m": "09-30"}
_SCALE_WORDS = ((re.compile(r"\bmn\b|\bmillion", re.I), 1_000_000),
                (re.compile(r"'?000|\bthousand", re.I), 1000),
                (re.compile(r"\bbn\b|\bbillion", re.I), 1_000_000_000))


def _norm(label) -> str:
    return " ".join(str(label).strip().lower().split()) if label is not None else ""


def _number(cell) -> Decimal | None:
    if cell is None or isinstance(cell, str) and not cell.strip():
        return None
    try:
        value = Decimal(str(cell).replace(",", "").strip())
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def _quantize(value: Decimal, places) -> Decimal:
    """Round a workbook value to the precision the issuer reports.

    Formula cells carry binary float noise (``56575.571299999996`` for a figure
    reported as 56,575.571). A reviewed mapping may declare that reporting
    precision; without one, values are kept exactly as stored.
    """
    from decimal import ROUND_HALF_EVEN

    return value.quantize(Decimal(1).scaleb(-int(places)), rounding=ROUND_HALF_EVEN)


def _column_period(text: str):
    """(period_kind, fiscal_year, period_end) for a header like 'FY 2023', or None."""
    # Issuer data books commonly footnote back-calculated discrete Q4 columns
    # with a trailing asterisk.  The footnote changes assurance, not period
    # identity, so accept it without weakening the anchored period parser.
    cleaned = re.sub(r"[\s*¹²³⁴]+$", "", text or "")
    match = _PERIOD.match(cleaned)
    if match:
        tag, year = match.group(1).upper(), int(match.group(2))
    elif (match := _PERIOD_SHORT.match(cleaned)):
        tag, year = match.group(1).upper(), 2000 + int(match.group(2))
    elif (match := _PERIOD_YEAR_FIRST.match(cleaned)):
        tag, year = match.group(2).upper(), int(match.group(1))
    else:
        return None
    if tag == "FY":
        return "fy", year, f"{year}-12-31"
    if tag in _QUARTER_END:
        return "quarter", year, f"{year}-{_QUARTER_END[tag]}"
    low = tag.lower()
    if low in _CUMULATIVE_END:
        return "ytd", year, f"{year}-{_CUMULATIVE_END[low]}"
    return None


class SupplementReader:
    def __init__(self, xlsx_path: str | Path, mapping_path: str | Path):
        try:
            import openpyxl  # noqa: F401
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError("the supplement reader needs the optional 'openpyxl' package") from error
        self.xlsx_path = Path(xlsx_path)
        self.mapping = json.loads(Path(mapping_path).read_text(encoding="utf-8"))

    def _detect_scale(self, sheet, mapping_scale) -> int:
        if mapping_scale:
            return int(mapping_scale)
        for row in sheet.iter_rows(min_row=1, max_row=6, values_only=True):
            for cell in row:
                for pattern, value in _SCALE_WORDS:
                    if isinstance(cell, str) and pattern.search(cell):
                        return value
        return 1

    def _period_columns(self, sheet, only_kinds: set[str]):
        """Map column index -> (period_kind, fiscal_year, period_end) from the
        header band (first ~8 rows). Later columns win on a repeated period."""
        columns: dict[int, tuple] = {}
        for row in sheet.iter_rows(min_row=1, max_row=8, values_only=True):
            for index, cell in enumerate(row):
                if not isinstance(cell, str):
                    continue
                period = _column_period(cell.replace("\n", " "))
                if period and period[0] in only_kinds:
                    columns[index] = period
        return columns

    def read(self, market: str, symbol: str, currency: str, filed_at: str,
             filing_type: str = "data-supplement", period_kinds=("fy",)) -> dict:
        import openpyxl

        # A balance-sheet line is an instant fact taken from the year-end (FY)
        # column; a flow line matches its own period kind.
        requested = set(period_kinds)
        configured = set(self.mapping.get("period_kinds", requested))
        only = requested & configured
        source_currency = str(self.mapping.get("currency") or currency)
        workbook = openpyxl.load_workbook(self.xlsx_path, data_only=True)
        facts: list[dict] = []
        excluded_facts: list[dict] = []
        seen: set[tuple] = set()

        # An issuer renames a tab by a stray space between vintages: Bank
        # AlJazira ships "Income Statment " in one quarter and "Income
        # Statment" in the next. Whitespace is not part of the tab's identity,
        # so match on it collapsed; everything else must still be exact.
        by_name = {" ".join(name.split()): name for name in reversed(workbook.sheetnames)}
        for sheet_name, row_map in self.mapping.get("sheets", {}).items():
            actual = by_name.get(" ".join(sheet_name.split()))
            if actual is None:
                continue
            sheet = workbook[actual]
            scale = self._detect_scale(sheet, self.mapping.get("scale"))
            columns = self._period_columns(sheet, only)
            if not columns:
                continue
            # Config keys match as a substring of the row label; the longest
            # matching key wins. Supplement labels vary and are often clipped.
            phrases = sorted(((_norm(label), spec) for label, spec in row_map.items()),
                             key=lambda item: -len(item[0]))
            label_col = min(columns)  # the row label sits left of the first period column

            for row in sheet.iter_rows(values_only=True):
                raw_label = next((cell for cell in row[:label_col]
                                  if isinstance(cell, str) and cell.strip()), None)
                if raw_label is None:
                    continue
                label = _norm(raw_label)
                spec = next((spec for phrase, spec in phrases if phrase and phrase in label), None)
                if not spec:
                    continue
                metric, want_kind = spec[0], spec[1]
                negate = len(spec) > 2 and spec[2] == "negate"
                options = next((item for item in spec[2:] if isinstance(item, dict)), {})
                absolute = bool(options.get("absolute"))
                fact_scale = int(options.get("scale", scale))
                fact_currency = str(options.get("currency", source_currency))
                fact_unit = str(options.get("unit", fact_currency))
                excluded_periods = set(options.get("exclude_period_ends", []))
                for index, (kind, fiscal_year, column_end) in columns.items():
                    if index >= len(row):
                        continue
                    if want_kind == "instant":
                        emit_kind, period_end = "instant", column_end
                    elif want_kind == "flow" and kind in {"fy", "quarter", "ytd"}:
                        emit_kind, period_end = kind, column_end
                    elif kind == want_kind:
                        emit_kind, period_end = kind, column_end
                    else:
                        continue
                    if emit_kind not in only and emit_kind != "instant":
                        continue
                    value = _number(row[index])
                    if value is None:
                        continue
                    precision = options.get("precision", self.mapping.get("precision"))
                    if precision is not None:
                        value = _quantize(value, precision)
                    if absolute:
                        value = abs(value)
                    if negate:
                        value = -value
                    if period_end in excluded_periods:
                        excluded_facts.append({
                            "metric": metric, "source_label": str(raw_label).strip(),
                            "value": str(value), "period_end": period_end,
                            "period_kind": emit_kind, "fiscal_year": fiscal_year,
                            "scale": str(fact_scale), "currency": fact_currency,
                            "unit": fact_unit,
                            "reason": options.get(
                                "exclude_reason",
                                "source value conflicts with a higher-authority filing",
                            ),
                        })
                        continue
                    key = (metric, period_end, emit_kind)
                    if key in seen:
                        continue  # a supplement often repeats a subtotal label; the first hit wins
                    fact = {
                        "metric": metric, "source_label": str(raw_label).strip(),
                        "value": str(value), "period_end": period_end,
                        "period_kind": emit_kind, "fiscal_year": fiscal_year,
                        "scale": str(fact_scale), "currency": fact_currency, "unit": fact_unit,
                    }
                    if emit_kind == "fy":
                        fact["period_start"] = f"{fiscal_year}-01-01"
                    elif emit_kind == "ytd":
                        fact["period_start"] = f"{fiscal_year}-01-01"
                        fact["fiscal_quarter"] = (int(period_end[5:7]) - 1) // 3 + 1
                    elif emit_kind == "quarter":
                        quarter = (int(period_end[5:7]) - 1) // 3 + 1
                        fact["fiscal_quarter"] = quarter
                        fact["period_start"] = f"{fiscal_year}-{(quarter - 1) * 3 + 1:02d}-01"
                    seen.add(key)
                    facts.append(fact)

        # Some issuer workbooks put one period per worksheet instead of one
        # period per column (for example Aramco's adjusted-earnings history).
        # This reviewed layout keeps the same deterministic row mapping while
        # deriving period semantics solely from the anchored worksheet name.
        sheet_periods = self.mapping.get("sheet_periods") or {}
        title_pattern = sheet_periods.get("pattern")
        if title_pattern:
            label_column = int(sheet_periods.get("label_column", 1)) - 1
            value_column = int(sheet_periods.get("value_column", 2)) - 1
            row_map = sheet_periods.get("rows", {})
            phrases = sorted(((_norm(label), spec) for label, spec in row_map.items()),
                             key=lambda item: -len(item[0]))
            for sheet in workbook.worksheets:
                if not re.fullmatch(str(title_pattern), sheet.title, re.I):
                    continue
                period = _column_period(sheet.title)
                if not period or period[0] not in only:
                    continue
                kind, fiscal_year, period_end = period
                scale = self._detect_scale(sheet, self.mapping.get("scale"))
                for row in sheet.iter_rows(values_only=True):
                    if max(label_column, value_column) >= len(row):
                        continue
                    raw_label = row[label_column]
                    if not isinstance(raw_label, str) or not raw_label.strip():
                        continue
                    label = _norm(raw_label)
                    spec = next((item for phrase, item in phrases
                                 if phrase and phrase in label), None)
                    if not spec:
                        continue
                    metric, want_kind = spec[0], spec[1]
                    if want_kind not in {kind, "flow"}:
                        continue
                    value = _number(row[value_column])
                    if value is None:
                        continue
                    negate = len(spec) > 2 and spec[2] == "negate"
                    options = next((item for item in spec[2:] if isinstance(item, dict)), {})
                    precision = options.get("precision", self.mapping.get("precision"))
                    if precision is not None:
                        value = _quantize(value, precision)
                    absolute = bool(options.get("absolute"))
                    if absolute:
                        value = abs(value)
                    if negate:
                        value = -value
                    key = (metric, period_end, kind)
                    if key in seen:
                        continue
                    fact = {
                        "metric": metric, "source_label": raw_label.strip(),
                        "value": str(value), "period_end": period_end,
                        "period_kind": kind, "fiscal_year": fiscal_year,
                        "scale": str(int(options.get("scale", scale))),
                        "currency": str(options.get("currency", source_currency)),
                        "unit": str(options.get("unit", options.get("currency", source_currency))),
                    }
                    if kind == "quarter":
                        quarter = (int(period_end[5:7]) - 1) // 3 + 1
                        fact["fiscal_quarter"] = quarter
                        fact["period_start"] = (
                            f"{fiscal_year}-{(quarter - 1) * 3 + 1:02d}-01"
                        )
                    elif kind == "fy":
                        fact["period_start"] = f"{fiscal_year}-01-01"
                    seen.add(key)
                    facts.append(fact)
        workbook.close()

        return {
            "company_id": f"{market.lower()}:{symbol}",
            "market": market, "symbol": symbol,
            "filing_type": filing_type, "filed_at": filed_at,
            # The latest period the workbook reports, like a statement's header.
            "period_end": max((fact["period_end"] for fact in facts), default=None),
            "source_url": self.mapping.get("source_url", ""),
            "reader": "finengine.reading_xlsx/1",
            "facts": sorted(facts, key=lambda f: (f["period_end"], f["metric"])),
            "excluded_facts": sorted(
                excluded_facts, key=lambda f: (f["period_end"], f["metric"])
            ),
        }
