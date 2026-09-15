from __future__ import annotations

"""Reader for Basel III Pillar 3 "KM1 - Key metrics" disclosures.

SAMA requires every Saudi bank to publish the BCBS Pillar 3 templates. KM1 is
standardised across issuers: numbered rows (1 CET1 through 20 NSFR ratio) and
up to five quarter-end columns, newest first. One geometry-based reader
therefore serves every bank without a per-issuer map.

The reader never guesses:

* the amount unit must be declared on the KM1 page itself;
* every column header must parse to a quarter end, and the headers must form
  an unbroken quarterly sequence. A column whose printed header contradicts
  the sequence (an issuer typo such as "31 Mar 2024" between "30 Jun 2025"
  and "31 Dec 2024") is excluded with its evidence - it is never re-dated;
* reported capital ratios are cross-checks. A column is published only when
  its CET1, Tier 1 and total capital amounts reproduce the printed ratios
  within the printed rounding.

Values without a governed catalog field (CET1 and Tier 1 amounts, leverage,
LCR and NSFR components) stay in ``excluded_facts`` with the reason, so they
remain reviewable without entering production. The printed total capital ratio
is not published either: the engine calculates ``capital_adequacy_ratio`` from
the published ``regulatory_capital`` and ``risk_weighted_assets``.

Requires the optional ``pymupdf`` extra.
"""

import calendar
import re
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

READER_ID = "finengine.reading_pillar3/1"


class Pillar3ReadError(ValueError):
    """The KM1 table cannot be read without guessing."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class _RowSpec(NamedTuple):
    row_id: str
    key: str
    kind: str
    metric: str | None
    pattern: str
    context: bool


# BCBS KM1 row numbering. ``metric`` is the governed catalog field a row is
# published as; ``None`` keeps the value in excluded_facts. Rows 13-20 often
# wrap their long captions onto neighbouring lines, so they match with context.
_ROWS = (
    _RowSpec("1", "cet1_capital", "amount", None,
             r"^common equity tier 1(?: \(cet1\))?$", False),
    _RowSpec("2", "tier1_capital", "amount", None, r"^tier 1$", False),
    _RowSpec("3", "total_capital", "amount", "regulatory_capital", r"^total capital$", False),
    _RowSpec("4", "total_risk_weighted_assets", "amount", "risk_weighted_assets",
             r"^total risk-weighted assets \(rwa\)$", False),
    _RowSpec("5", "cet1_ratio", "percent", "cet1_ratio",
             r"^(?:cet1|common equity tier 1) ratio \(%\)$", False),
    _RowSpec("6", "tier1_ratio", "percent", "tier1_capital_ratio",
             r"^tier 1 ratio \(%\)$", False),
    _RowSpec("7", "total_capital_ratio", "percent", None, r"^total capital ratio \(%\)$", False),
    _RowSpec("13", "leverage_ratio_exposure", "amount", None,
             r"leverage ratio exposure measure", True),
    _RowSpec("14", "leverage_ratio", "percent", None, r"leverage ratio \(%\)", True),
    _RowSpec("15", "high_quality_liquid_assets", "amount", None,
             r"high-quality liquid assets", True),
    _RowSpec("16", "net_cash_outflow", "amount", None, r"net cash outflow", True),
    _RowSpec("17", "liquidity_coverage_ratio", "percent", None,
             r"\blcr\b|liquidity coverage ratio", True),
    _RowSpec("18", "available_stable_funding", "amount", None, r"available stable funding", True),
    _RowSpec("19", "required_stable_funding", "amount", None, r"required stable funding", True),
    _RowSpec("20", "net_stable_funding_ratio", "percent", None,
             r"\bnsfr\b|net stable funding ratio", True),
)
_SPEC_BY_ID = {spec.row_id: spec for spec in _ROWS}

# ratio row, numerator row, denominator row, check name
_CAPITAL_CHECKS = (
    ("5", "1", "4", "cet1_ratio = cet1_capital / total_risk_weighted_assets"),
    ("6", "2", "4", "tier1_ratio = tier1_capital / total_risk_weighted_assets"),
    ("7", "3", "4", "total_capital_ratio = total_capital / total_risk_weighted_assets"),
)
_OTHER_CHECKS = (
    ("14", "2", "13", "leverage_ratio = tier1_capital / leverage_ratio_exposure"),
    ("17", "15", "16", "liquidity_coverage_ratio = high_quality_liquid_assets / net_cash_outflow"),
    ("20", "18", "19", "net_stable_funding_ratio = available_stable_funding / required_stable_funding"),
)

_MONTHS = {name.lower(): index for index, name in enumerate(calendar.month_abbr) if name}
_AMOUNT = re.compile(r"^\(?-?\d{1,3}(?:,\d{3})+\)?$|^\(?-?\d{5,}\)?$")
_PERCENT = re.compile(r"^\(?-?\d+(?:\.\d+)?%\)?$")
_ROW_ID = re.compile(r"^\d{1,2}[a-e]?$")
_DAY_MONTH_YEAR = re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{2,4})\b")
# A two-digit year needs an explicit separator ("Dec-25", "Dec'20"); after a
# plain space only a four-digit year is accepted, so "December 30" is not 2030.
_MONTH_YEAR = re.compile(r"\b([A-Za-z]{3,9})(?:\s*[-’'‘_]\s*(\d{4}|\d{2})|\s+(\d{4}))\b")
_THOUSANDS = re.compile(r"SAR\s*[’'‘`]?\s*0{3}(?:\s*['’]?s)?\b|\bthousands\b", re.I)
_MILLIONS = re.compile(r"SAR\s*(?:mn|mln|millions?)\b", re.I)
_CELLS = "abcdef"


def _normal(text: str) -> str:
    return " ".join(text.replace("’", "'").replace("‘", "'").lower().split())


def _is_number(token: str) -> bool:
    return bool(_AMOUNT.match(token) or _PERCENT.match(token))


_QUARTER_YEAR = re.compile(r"(?<![A-Za-z0-9])(?:Q([1-4])|([1-4])Q)[\s\-_']*(20\d{2})(?!\d)", re.I)


def _quarter_end(text: str) -> date | None:
    """The quarter end printed in one KM1 column header, or ``None``."""
    # Earlier filings label columns by calendar quarter ("Q1 2023", "4Q 2022").
    quarter = _QUARTER_YEAR.search(text)
    if quarter:
        month = int(quarter.group(1) or quarter.group(2)) * 3
        year = int(quarter.group(3))
        return date(year, month, calendar.monthrange(year, month)[1])
    candidates = [
        (match.group(1), match.group(2), match.group(3))
        for match in _DAY_MONTH_YEAR.finditer(text)
    ] + [
        (None, match.group(1), match.group(2) or match.group(3))
        for match in _MONTH_YEAR.finditer(text)
    ]
    for day_text, month_text, year_text in candidates:
        month = _MONTHS.get(month_text[:3].lower())
        if month is None:
            continue
        if len(year_text) not in (2, 4):
            return None  # a malformed printed year such as "205"
        year = int(year_text) + (2000 if len(year_text) == 2 else 0)
        last_day = calendar.monthrange(year, month)[1]
        if month % 3 or (day_text is not None and int(day_text) != last_day):
            return None
        return date(year, month, last_day)
    return None


def _quarter_shift(value: date, quarters: int) -> date:
    index = value.year * 12 + value.month - 1 + 3 * quarters
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, calendar.monthrange(year, month)[1])


def _parse_cell(token: str | None, kind: str) -> tuple[Decimal, int | None] | None:
    if token is None:
        return None
    negative = token.startswith("(") and token.endswith(")")
    digits = token.strip("()")
    if kind == "amount":
        if not _AMOUNT.match(token):
            return None
        value = Decimal(digits.replace(",", ""))
        return (-value if negative else value), None
    if not _PERCENT.match(token):
        return None
    digits = digits.rstrip("%")
    decimals = len(digits.split(".", 1)[1]) if "." in digits else 0
    value = Decimal(digits) / 100
    return (-value if negative else value), decimals


class Pillar3KeyMetricsReader:
    """Read the KM1 key-metrics table of a Basel III Pillar 3 disclosure PDF."""

    def __init__(self, pdf_path: str | Path):
        try:
            import pymupdf  # noqa: F401
        except ImportError as error:  # pragma: no cover - environment dependent
            raise RuntimeError("the Pillar 3 reader needs the optional 'pymupdf' package") from error
        self.pdf_path = Path(pdf_path)

    def read(self, market: str, symbol: str, currency: str, source_url: str,
             filed_at: str) -> dict:
        import pymupdf

        document = pymupdf.open(self.pdf_path)
        try:
            page_index = self._km1_page(document)
            page = document[page_index]
            text = page.get_text()
            words = [tuple(word[:5]) for word in page.get_text("words")]
        finally:
            document.close()

        scale = self._scale(text)
        centers = self._columns(words)
        pitch = min((b - a for a, b in zip(centers, centers[1:])), default=480.0)
        rows = self._rows(self._lines(words), centers, pitch / 2)
        missing = [row_id for row_id in ("1", "2", "3", "4", "5", "6", "7") if row_id not in rows]
        if missing:
            raise Pillar3ReadError(
                "required_rows_missing", f"KM1 capital rows not found: {', '.join(missing)}")
        headers = self._headers(words, centers, pitch, rows["1"]["y"])
        parsed = [_quarter_end(header) for header in headers]
        anchor = self._anchor(parsed, headers)

        facts: list[dict] = []
        excluded: list[dict] = []
        excluded_columns: list[dict] = []
        checks: list[dict] = []
        for index, (header, period) in enumerate(zip(headers, parsed)):
            cell = _CELLS[index]
            expected = _quarter_shift(anchor, -index)
            if period != expected:
                excluded_columns.append({
                    "cell": cell, "header_text": header,
                    "parsed_period_end": period.isoformat() if period else None,
                    "sequence_anchor": anchor.isoformat(), "sequence_position": index,
                    "reason": "period_header_inconsistent",
                    "resolution": (
                        "Do not re-date the column. The same quarter end is repeated in the "
                        "adjacent quarterly Pillar 3 disclosures; take it from a filing whose "
                        "column headers form a consistent sequence."
                    ),
                })
                continue
            values = {
                row_id: _parse_cell(row["cells"][index], row["spec"].kind)
                for row_id, row in rows.items()
            }
            capital_ok = True
            for ratio_id, numerator_id, denominator_id, name in _CAPITAL_CHECKS:
                check = self._check(values, ratio_id, numerator_id, denominator_id, name, expected)
                checks.append(check)
                capital_ok = capital_ok and check["status"] == "pass"
            other_status = {}
            for ratio_id, numerator_id, denominator_id, name in _OTHER_CHECKS:
                if ratio_id in rows:
                    check = self._check(values, ratio_id, numerator_id, denominator_id, name, expected)
                    checks.append(check)
                    for row_id in (ratio_id, numerator_id, denominator_id):
                        other_status.setdefault(row_id, check["status"])
            for row_id, row in rows.items():
                parsed_value = values[row_id]
                if parsed_value is None:
                    continue
                spec = row["spec"]
                fact = self._fact(spec, row, cell, parsed_value, expected,
                                  page_index + 1, scale, currency)
                if not capital_ok:
                    excluded.append({**fact, "reason": "reported_ratio_does_not_reconcile"})
                elif spec.metric:
                    facts.append(fact)
                elif spec.row_id == "7":
                    excluded.append({
                        **fact, "reason": "engine_calculates_metric",
                        "calculated_metric": "capital_adequacy_ratio",
                        "note": "published regulatory_capital / risk_weighted_assets; the "
                                "printed ratio is retained as a reconciled cross-check",
                    })
                else:
                    reason = ("reported_ratio_does_not_reconcile"
                              if other_status.get(row_id) == "fail" else "catalog_field_missing")
                    excluded.append({**fact, "reason": reason, "proposed_field": spec.key})

        if not facts:
            raise Pillar3ReadError(
                "no_reconciled_columns",
                "no KM1 column passed the period-sequence and capital-ratio checks")
        return {
            "company_id": f"{market.lower()}:{symbol}",
            "market": market,
            "symbol": symbol,
            "filing_type": "regulatory-disclosure",
            "filed_at": filed_at,
            "period_end": anchor.isoformat(),
            "source_url": source_url,
            "reader": READER_ID,
            "profile": "bank",
            "notes": (
                "Basel III Pillar 3 KM1 key metrics (consolidated). Each published column "
                "passed the quarterly header sequence and reproduced the printed CET1, "
                "Tier 1 and total capital ratios from the printed amounts."
            ),
            "facts": facts,
            "excluded_facts": excluded,
            "excluded_columns": excluded_columns,
            "checks": checks,
        }

    @staticmethod
    def _km1_page(document) -> int:
        signature = ("common equity tier 1", "total capital", "total risk-weighted assets",
                     "fully loaded ecl accounting model")
        for index in range(document.page_count):
            lowered = _normal(document[index].get_text())
            if all(term in lowered for term in signature):
                return index
        raise Pillar3ReadError("km1_table_not_found", "no page carries the KM1 key-metrics rows")

    @staticmethod
    def _scale(text: str) -> Decimal:
        thousands = bool(_THOUSANDS.search(text))
        millions = bool(_MILLIONS.search(text))
        if thousands and millions:
            raise Pillar3ReadError("ambiguous_unit", "the KM1 page declares both thousands and millions")
        if not (thousands or millions):
            raise Pillar3ReadError("unit_not_declared", "the KM1 page does not declare its amount unit")
        return Decimal(1000) if thousands else Decimal(1_000_000)

    @staticmethod
    def _columns(words) -> list[float]:
        def clustered(tokens) -> list[float]:
            xs = sorted((word[0] + word[2]) / 2 for word in tokens)
            clusters: list[list[float]] = []
            for x in xs:
                if clusters and x - clusters[-1][-1] <= 25:
                    clusters[-1].append(x)
                else:
                    clusters.append([x])
            return [sorted(cluster)[len(cluster) // 2] for cluster in clusters if len(cluster) >= 5]

        # Percentages are set a few points right of the amounts in the same
        # column; centring on the amounts keeps stacked headers that sit
        # between two columns assigned to the right one.
        centers = clustered([word for word in words if _AMOUNT.match(word[4])])
        if not 2 <= len(centers) <= len(_CELLS):
            centers = clustered([word for word in words if _is_number(word[4])])
        if not 2 <= len(centers) <= len(_CELLS):
            raise Pillar3ReadError(
                "columns_not_detected", f"expected 2-{len(_CELLS)} value columns, found {len(centers)}")
        return centers

    @staticmethod
    def _lines(words) -> list[dict]:
        texts = sorted((word for word in words if not _is_number(word[4])),
                       key=lambda word: (word[1], word[0]))
        lines: list[dict] = []
        for word in texts:
            if lines and abs(word[1] - lines[-1]["y"]) <= 2.5:
                lines[-1]["words"].append(word)
            else:
                lines.append({"y": word[1], "words": [word], "values": []})
        for line in lines:
            line["words"].sort(key=lambda word: word[0])
        for word in (word for word in words if _is_number(word[4])):
            nearest = min(lines, key=lambda line: abs(line["y"] - word[1]), default=None)
            # Label and value baselines differ by a few points in several
            # issuers' layouts; rows themselves are more than ten points apart.
            if nearest is not None and abs(nearest["y"] - word[1]) <= 6:
                nearest["values"].append(word)
        return lines

    @staticmethod
    def _rows(lines: list[dict], centers: list[float], half: float) -> dict[str, dict]:
        found: dict[str, dict] = {}
        for line in lines:
            tokens = [word[4] for word in line["words"]]
            if not tokens or not _ROW_ID.match(tokens[0]):
                continue
            spec = _SPEC_BY_ID.get(tokens[0].lower())
            if spec is None or spec.row_id in found or not line["values"]:
                continue
            label = " ".join(tokens[1:])
            searchable = _normal(label)
            if spec.context:
                neighbours = [
                    other for other in lines
                    if other is not line and not other["values"]
                    and abs(other["y"] - line["y"]) <= 10
                    and not _ROW_ID.match(other["words"][0][4])
                ]
                searchable = " ".join(
                    [searchable, *(_normal(" ".join(word[4] for word in other["words"]))
                                   for other in neighbours)])
            if not re.search(spec.pattern, searchable):
                continue
            cells = []
            for center in centers:
                here = [word[4] for word in line["values"]
                        if abs((word[0] + word[2]) / 2 - center) <= half]
                cells.append(here[0] if len(here) == 1 else None)
            found[spec.row_id] = {
                "spec": spec, "label": label or searchable, "cells": cells, "y": line["y"],
            }
        return found

    @staticmethod
    def _headers(words, centers: list[float], pitch: float, first_row_y: float) -> list[str]:
        band = [word for word in words
                if first_row_y - 60 <= word[1] < first_row_y - 1 and not _is_number(word[4])]
        assigned: list[list[tuple]] = [[] for _ in centers]
        for word in band:
            middle = (word[0] + word[2]) / 2
            index = min(range(len(centers)), key=lambda i: abs(centers[i] - middle))
            # Headers are often centred left of right-aligned figures, and
            # stacked headers ("31 December" over "2024") sit between columns.
            # Each word belongs to its nearest column; anything farther than
            # most of a column pitch is a caption, not a header.
            if abs(centers[index] - middle) <= pitch * 0.75:
                assigned[index].append(word)
        return [
            " ".join(word[4] for word in sorted(tokens, key=lambda word: (round(word[1]), word[0])))
            for tokens in assigned
        ]

    @staticmethod
    def _anchor(parsed: list[date | None], headers: list[str]) -> date:
        implied = Counter(
            _quarter_shift(period, index) for index, period in enumerate(parsed) if period)
        ranked = implied.most_common()
        if not ranked or ranked[0][1] < 2 or (len(ranked) > 1 and ranked[1][1] == ranked[0][1]):
            raise Pillar3ReadError(
                "period_headers_unverifiable",
                f"column headers do not agree on one quarterly sequence: {headers}")
        return ranked[0][0]

    @staticmethod
    def _check(values: dict, ratio_id: str, numerator_id: str, denominator_id: str,
               name: str, period_end: date) -> dict:
        ratio = values.get(ratio_id)
        numerator = values.get(numerator_id)
        denominator = values.get(denominator_id)
        result = {"check": name, "period_end": period_end.isoformat()}
        if ratio is None or numerator is None or denominator is None or not denominator[0]:
            return {**result, "status": "missing"}
        computed = numerator[0] / denominator[0]
        # Half a unit of the last printed percentage digit, plus a small allowance
        # for the issuer rounding the amounts themselves to thousands.
        tolerance = Decimal(5) * Decimal(10) ** -(ratio[1] + 3) + Decimal("0.00001")
        status = "pass" if abs(computed - ratio[0]) <= tolerance else "fail"
        return {
            **result, "status": status, "reported": format(ratio[0].normalize(), "f"),
            "computed": format(computed.quantize(Decimal("0.000001")), "f"),
            "tolerance": format(tolerance, "f"),
        }

    @staticmethod
    def _fact(spec: _RowSpec, row: dict, cell: str, parsed: tuple[Decimal, int | None],
              period_end: date, page_number: int, scale: Decimal, currency: str) -> dict:
        value, _ = parsed
        fact = {
            "metric": spec.metric or spec.key,
            "source_label": row["label"],
            "period_end": period_end.isoformat(),
            "period_kind": "instant",
            "fiscal_year": period_end.year,
            "page": page_number,
            "table": "KM1",
            "row": spec.row_id,
            "cell": cell,
        }
        if spec.kind == "amount":
            fact.update(value=format(value, "f"), scale=format(scale, "f"),
                        currency=currency, unit=currency)
        else:
            fact.update(value=format(value.normalize(), "f"), scale="1", currency="", unit="ratio")
        return fact
