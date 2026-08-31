from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

class Market(StrEnum):
    SA = "SA"
    US = "US"

class PeriodKind(StrEnum):
    INSTANT = "instant"
    QUARTER = "quarter"
    YTD = "ytd"
    FY = "fy"
    TTM = "ttm"

@dataclass(frozen=True)
class Company:
    company_id: str
    market: Market
    symbol: str
    name: str
    currency: str
    cik: str | None = None
    isin: str | None = None
    fiscal_year_end: str = "12-31"
    sources: tuple[str, ...] = ()

@dataclass(frozen=True)
class SourceDocument:
    company_id: str
    market: Market
    source_url: str
    source_key: str
    filing_type: str
    filed_at: str
    content: bytes
    content_type: str = "application/json"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Fact:
    company_id: str
    metric: str
    value: Decimal
    currency: str
    unit: str
    period_start: str | None
    period_end: str
    period_kind: PeriodKind
    fiscal_year: int
    fiscal_quarter: int | None
    source_key: str
    source_url: str
    filed_at: str
    accession: str | None = None
    form: str | None = None
    is_calculated: bool = False
    calculation: str | None = None

    @property
    def natural_key(self) -> tuple[Any, ...]:
        return (self.company_id, self.metric, self.period_end, self.period_kind.value, self.fiscal_year, self.fiscal_quarter, self.currency, self.unit)
