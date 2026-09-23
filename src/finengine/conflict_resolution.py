from __future__ import annotations

"""Deterministic, company-agnostic rules for resolving cross-manifest value conflicts.

Two archived documents sometimes report different values for the same
(company, metric, period, scope, dimensions) fact - a later annual report
restates a prior year's comparative, an investor presentation rounds a figure
the audited financial statements state precisely, or a quarterly data
supplement is superseded by the reviewed interim statements it summarizes.
This module picks exactly one winner using rules that hold for any company
and any metric - never an average, never a hand pick.

The rules are applied in this fixed order. Each is a total tiebreak on ties
from the rule above it; only the first rule that distinguishes the
candidates decides the outcome, and that rule's name is recorded so every
resolution is auditable.

1. ``source_authority``  - audited > reviewed > earnings_release > presentation > other.
2. ``period_recency``    - for the same period, the more recently filed document
                            (a later annual report's restated comparative, a later
                            interim report) takes precedence over an earlier one.
3. ``consolidated_over_segment`` - for a metric that is a unified, company-wide
                            figure (not intrinsically segment-dimensioned), a
                            consolidated-scope value outranks a segment-scope one.
4. ``reported_over_calculated``  - an as-filed (reported) value outranks a value
                            derived by this engine's own formulas.
5. ``precision``          - when authority, period and reported/calculated status
                            are all tied (for example two tables in the very same
                            audited annual report), the figure carrying more
                            decimal precision wins, because a rounded headline
                            figure is a lossy presentation of the detailed one,
                            never a conflicting fact.

If every rule ties, resolution refuses to guess: the candidates are returned
unresolved so a human reviews the filing, per "never hand-pick a value
without an auditable rule".
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

# Tier 4 is the strongest. Matching is by keyword, on the free-text
# ``filing_type``/document label every archived source already carries, so
# any newly ingested document type is classified without code changes as
# long as it uses ordinary English filing vocabulary.
AUDITED = 4
REVIEWED = 3
EARNINGS_RELEASE = 2
PRESENTATION = 1
OTHER = 0

# Order matters: more specific/negative phrases are matched before the
# generic ones they contain (e.g. "unaudited interim" before "annual report").
_TIER_KEYWORDS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (PRESENTATION, (
        "presentation", "webcast", "investor day", "roadshow", "slide", "deck",
        "transcript",
    )),
    (EARNINGS_RELEASE, (
        "earnings release", "earnings-release", "results announcement",
        "press release", "news release", "trading update", "results presentation",
    )),
    (REVIEWED, (
        "interim", "quarterly", "q1 ", "q2 ", "q3 ", "q4 ", "10-q", "review report",
        "data-supplement", "data supplement", "regulatory-disclosure",
        "regulatory disclosure", "pillar 3", "pillar3",
    )),
    (AUDITED, (
        "audited", "annual report", "annual-report", "annual financial",
        "financial-statements", "financial statements", "10-k", "parent-annual",
        "official-regulator-report", "official-regulation",
    )),
)


def assurance_tier(filing_type: str | None) -> int:
    """Classify any free-text filing/document label into an assurance tier.

    Falls back to ``OTHER`` for anything unrecognized rather than guessing,
    so an unfamiliar label never silently outranks a known audited source.
    """
    text = (filing_type or "").casefold()
    for tier, keywords in _TIER_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return tier
    return OTHER


# Metrics whose economic meaning is inherently a single company-wide total.
# A segment-scope value for one of these is a component of the whole, not an
# alternate version of it, so it must never outrank the consolidated figure
# for the same metric key. This list is deliberately generic (metric names,
# not company names) and mirrors the catalog's own unified-metric fields.
UNIFIED_COMPANY_WIDE_METRICS = frozenset({
    "revenue", "net_income", "net_income_parent", "operating_income", "total_assets",
    "total_liabilities", "total_equity", "total_liabilities_equity", "basic_eps",
    "eps_diluted", "roace", "return_on_equity", "return_on_assets",
    "return_on_capital_employed", "total_gas_production", "total_hydrocarbon_production",
    "total_liquids_production", "ebitda", "ebit", "operating_cash_flow",
    "free_cash_flow", "market_cap",
})


def _precision(value: Decimal) -> int:
    """Count digits after the decimal point, as a proxy for reporting granularity.

    Deliberately does not call ``.normalize()`` first: normalizing strips the
    trailing zeros that are the whole signal here (``Decimal("10.00")`` must
    outrank ``Decimal("10.0")`` as the more precisely reported figure).
    """
    exponent = value.as_tuple().exponent
    return max(0, -exponent) if isinstance(exponent, int) else 0


@dataclass(frozen=True)
class Candidate:
    """One archived document's claim about a single fact."""

    source_id: str
    value: Decimal
    filing_type: str = ""
    filed_at: str = ""
    scope: str = "consolidated"
    is_calculated: bool = False
    metric: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Resolution:
    winner: Candidate
    rule: str
    ordered: tuple[Candidate, ...]
    rationale: str


RULE_NAMES = (
    "source_authority",
    "period_recency",
    "consolidated_over_segment",
    "reported_over_calculated",
    "precision",
)


def _rule_source_authority(c: Candidate) -> int:
    return assurance_tier(c.filing_type)


def _rule_period_recency(c: Candidate) -> str:
    return c.filed_at or ""


def _rule_consolidated_over_segment(c: Candidate) -> int:
    if c.metric not in UNIFIED_COMPANY_WIDE_METRICS:
        return 0
    return 1 if c.scope == "consolidated" else 0


def _rule_reported_over_calculated(c: Candidate) -> int:
    return 0 if c.is_calculated else 1


def _rule_precision(c: Candidate) -> int:
    try:
        return _precision(Decimal(str(c.value)))
    except Exception:
        return 0


_RULE_FUNCS = {
    "source_authority": _rule_source_authority,
    "period_recency": _rule_period_recency,
    "consolidated_over_segment": _rule_consolidated_over_segment,
    "reported_over_calculated": _rule_reported_over_calculated,
    "precision": _rule_precision,
}


def resolve(candidates: list[Candidate]) -> Resolution | None:
    """Pick exactly one winning candidate, or ``None`` if every rule ties.

    Never averages. Never picks by insertion order or file name. The
    returned :class:`Resolution` records which rule decided the case, and
    ``ordered`` preserves every candidate (the audit trail) ranked from
    strongest to weakest.
    """
    if not candidates:
        return None
    remaining = list(candidates)
    deciding_rule = None
    for rule_name in RULE_NAMES:
        key = _RULE_FUNCS[rule_name]
        best = max(key(c) for c in remaining)
        narrowed = [c for c in remaining if key(c) == best]
        if len(narrowed) < len(remaining):
            deciding_rule = rule_name
        remaining = narrowed
        if len(remaining) == 1:
            break
    ordered = tuple(
        sorted(
            candidates,
            key=lambda c: tuple(_RULE_FUNCS[name](c) for name in RULE_NAMES),
            reverse=True,
        )
    )
    if len(remaining) != 1:
        return None
    winner = remaining[0]
    rule = deciding_rule or "no_conflict"
    rationale = (
        f"decided by '{rule}': {winner.source_id} "
        f"(filing_type={winner.filing_type!r}, filed_at={winner.filed_at!r}, "
        f"scope={winner.scope!r}, is_calculated={winner.is_calculated}, value={winner.value})"
    )
    return Resolution(winner=winner, rule=rule, ordered=ordered, rationale=rationale)
