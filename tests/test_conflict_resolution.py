from __future__ import annotations

"""Generic, company-agnostic tests for cross-manifest conflict resolution.

Each test proves one rule holds for synthetic fixture data - not for any one
company - so the guarantee is: "audited beats presentation" (etc.) for any
issuer, any metric. Real-world regression coverage for the eight Aramco
conflicts lives in test_known_data_regressions.py / bootstrap verification.
"""

from decimal import Decimal

import pytest

from finengine.conflict_resolution import (
    AUDITED,
    EARNINGS_RELEASE,
    OTHER,
    PRESENTATION,
    REVIEWED,
    Candidate,
    assurance_tier,
    resolve,
)


def test_assurance_tier_classifies_generic_filing_labels():
    assert assurance_tier("Annual Report - Audited Financial Statements") == AUDITED
    assert assurance_tier("Q2 2024 Interim Report") == REVIEWED
    assert assurance_tier("FY2024 Earnings Release") == EARNINGS_RELEASE
    assert assurance_tier("Investor Presentation - Q3 2024") == PRESENTATION
    assert assurance_tier("some unrecognized internal memo") == OTHER
    assert assurance_tier(None) == OTHER


@pytest.mark.parametrize("company_a,company_b", [
    ("synthetic-co-a", "synthetic-co-b"),
    ("2222", "1120"),
    ("acme-holdings", "widget-corp"),
])
def test_rule_source_authority_audited_beats_presentation(company_a, company_b):
    """Rule 1 holds for any company: audited > reviewed > earnings release > presentation."""
    audited = Candidate(
        source_id=f"{company_a}-annual-report", value=Decimal("100.0"),
        filing_type="Annual Report - Audited Financial Statements", filed_at="2024-03-01",
        metric="net_income",
    )
    presentation = Candidate(
        source_id=f"{company_b}-investor-deck", value=Decimal("105.0"),
        filing_type="Investor Presentation", filed_at="2024-06-01",  # later, but weaker
        metric="net_income",
    )
    result = resolve([audited, presentation])
    assert result is not None
    assert result.winner is audited
    assert result.rule == "source_authority"


def test_rule_source_authority_full_ranking_order():
    audited = Candidate("s1", Decimal("1"), filing_type="audited annual financial statements", metric="x")
    reviewed = Candidate("s2", Decimal("2"), filing_type="Q1 interim report", metric="x")
    earnings = Candidate("s3", Decimal("3"), filing_type="earnings release", metric="x")
    presentation = Candidate("s4", Decimal("4"), filing_type="investor presentation", metric="x")
    assert resolve([reviewed, earnings, presentation]).winner is reviewed
    assert resolve([earnings, presentation]).winner is earnings
    assert resolve([audited, reviewed, earnings, presentation]).winner is audited


def test_rule_period_recency_same_tier_more_recent_filing_wins():
    """Rule 2: same assurance tier, same period -> the more recently filed
    document (a later annual report's restated comparative) wins."""
    original = Candidate(
        source_id="fy1-original", value=Decimal("2.47"),
        filing_type="Annual Report", filed_at="2023-03-12", metric="eps_diluted",
    )
    restated = Candidate(
        source_id="fy2-comparative-restatement", value=Decimal("2.72"),
        filing_type="Annual Report", filed_at="2024-03-10", metric="eps_diluted",
    )
    result = resolve([original, restated])
    assert result.winner is restated
    assert result.rule == "period_recency"


def test_rule_consolidated_over_segment_for_unified_metric():
    """Rule 3: a company-wide metric's consolidated value outranks a segment
    value reported under the same tier/date, for any issuer or metric key
    that is structurally a unified total."""
    consolidated = Candidate(
        source_id="co-annual-report-consolidated", value=Decimal("50.0"),
        filing_type="annual report", filed_at="2024-03-01", scope="consolidated",
        metric="revenue",
    )
    segment = Candidate(
        source_id="co-annual-report-segment-note", value=Decimal("32.0"),
        filing_type="annual report", filed_at="2024-03-01", scope="segment",
        metric="revenue",
    )
    result = resolve([consolidated, segment])
    assert result.winner is consolidated
    assert result.rule == "consolidated_over_segment"


def test_rule_consolidated_over_segment_does_not_apply_to_segment_native_metrics():
    """A metric that is NOT in the unified company-wide list (e.g. a segment
    revenue line) is unaffected by rule 3 - the two candidates are simply
    distinct facts about different scopes, so with everything else tied the
    resolver falls through to the precision rule instead of pretending one
    segment value is more authoritative than another."""
    a = Candidate("s1", Decimal("10.0"), filing_type="annual report", filed_at="2024-01-01",
                  scope="segment", metric="upstream_revenue")
    b = Candidate("s2", Decimal("10.00"), filing_type="annual report", filed_at="2024-01-01",
                  scope="segment", metric="upstream_revenue")
    result = resolve([a, b])
    assert result.winner is b  # more decimal precision, not scope-driven
    assert result.rule == "precision"


def test_rule_reported_over_calculated():
    """Rule 4: an as-filed value outranks a value this engine derived itself,
    for any metric/company, once authority/date/scope are tied."""
    reported = Candidate(
        source_id="co-annual-report-reported", value=Decimal("18.5"),
        filing_type="annual report", filed_at="2024-03-01", is_calculated=False,
        metric="roace",
    )
    calculated = Candidate(
        source_id="co-derived-ratio", value=Decimal("18.9"),
        filing_type="annual report", filed_at="2024-03-01", is_calculated=True,
        metric="roace",
    )
    result = resolve([calculated, reported])
    assert result.winner is reported
    assert result.rule == "reported_over_calculated"


def test_rule_precision_breaks_ties_within_the_same_document_tier_and_date():
    """Rule 5: when authority, date, scope and reported/calculated all tie
    (e.g. a rounded highlights table vs. a detailed table in the very same
    audited annual report), the more precise figure wins - generic to any
    metric or company."""
    rounded = Candidate(
        source_id="co-annual-report-highlights", value=Decimal("11.4"),
        filing_type="Annual report operational highlights", filed_at="2026-03-09",
        metric="total_gas_production",
    )
    detailed = Candidate(
        source_id="co-annual-report-detail-table", value=Decimal("11.365"),
        filing_type="Annual report operational production table precision update",
        filed_at="2026-03-09", metric="total_gas_production",
    )
    result = resolve([rounded, detailed])
    assert result.winner is detailed
    assert result.rule == "precision"


def test_never_averages_and_never_hand_picks_on_a_true_tie():
    """If every rule ties, resolution refuses to guess rather than average or
    arbitrarily pick - this must hold regardless of candidate order."""
    a = Candidate("s1", Decimal("5.0"), filing_type="annual report", filed_at="2024-01-01",
                  metric="net_income")
    b = Candidate("s2", Decimal("7.0"), filing_type="annual report", filed_at="2024-01-01",
                  metric="net_income")
    assert resolve([a, b]) is None
    assert resolve([b, a]) is None  # order independence


def test_single_candidate_is_a_trivial_resolution():
    only = Candidate("s1", Decimal("1.0"), filing_type="annual report", filed_at="2024-01-01",
                      metric="net_income")
    result = resolve([only])
    assert result.winner is only
    assert result.rule == "no_conflict"


def test_resolve_empty_list_returns_none():
    assert resolve([]) is None


def test_ordered_audit_trail_lists_every_candidate_strongest_first():
    audited = Candidate("s1", Decimal("1"), filing_type="audited annual report",
                         filed_at="2024-01-01", metric="net_income")
    presentation = Candidate("s2", Decimal("2"), filing_type="investor presentation",
                              filed_at="2024-06-01", metric="net_income")
    result = resolve([presentation, audited])
    assert result.ordered[0] is audited
    assert result.ordered[1] is presentation
    assert len(result.ordered) == 2
