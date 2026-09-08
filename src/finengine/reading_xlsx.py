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
_QUARTER_END = {"1Q": "03-31", "2Q": "06-30", "3Q": "09-30", "4Q": "12-31",
                "q1": "03-31", "q2": "06-30", "q3": "09-30", "q4": "12-31"}
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


def _column_period(text: str):
    """(period_kind, fiscal_year, period_end) for a header like 'FY 2023', or None."""
    match = _PERIOD.match(text or "")
    if not match:
        return None
    tag, year = match.group(1).upper(), int(match.group(2))
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
        only = set(period_kinds) | {"fy"}
        workbook = openpyxl.load_workbook(self.xlsx_path, data_only=True)
        facts: list[dict] = []
        seen: set[tuple] = set()

        for sheet_name, row_map in self.mapping.get("sheets", {}).items():
            if sheet_name not in workbook.sheetnames:
                continue
            sheet = workbook[sheet_name]
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
                    if negate:
                        value = -value
                    key = (metric, period_end, emit_kind)
                    if key in seen:
                        continue  # a supplement often repeats a subtotal label; the first hit wins
                    fact = {
                        "metric": metric, "source_label": str(raw_label).strip(),
                        "value": str(value), "period_end": period_end,
                        "period_kind": emit_kind, "fiscal_year": fiscal_year,
                        "scale": str(scale), "currency": currency, "unit": currency,
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
        workbook.close()

        return {
            "company_id": f"{market.lower()}:{symbol}",
            "market": market, "symbol": symbol,
            "filing_type": filing_type, "filed_at": filed_at,
            "source_url": self.mapping.get("source_url", ""),
            "reader": "finengine.reading_xlsx/1",
            "facts": sorted(facts, key=lambda f: (f["period_end"], f["metric"])),
        }
