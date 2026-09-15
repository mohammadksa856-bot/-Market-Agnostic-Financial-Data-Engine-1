from __future__ import annotations

"""Deterministic projections from governed dimensional facts.

The source-faithful metric remains the record of what the issuer reported.  A
projection adds a canonical query key only when the relationship is exact.  In
particular, a component table must reconcile to its reported total before it is
used to create an undimensioned balance or expense line.
"""

import json
import re
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable

from .models import Fact, PeriodKind

if TYPE_CHECKING:  # pragma: no cover - imported only for type checking
    from .database import Database


PPE_CLASS_ALIASES = {
    "land and land improvements": "land",
    "buildings": "buildings",
    "plant machinery and equipment": "machinery_equipment",
    "oil and gas properties": "oil_gas_properties",
    "construction in progress": "construction_in_progress",
}

SEGMENT_SUFFIX_ALIASES = {
    "depreciation_amortization": "segment_depreciation_amortization",
    "investments_associates": "segment_investments_associates",
    "liabilities": "segment_liabilities",
    "impairment": "segment_impairment",
    "revenue": "segment_revenue",
    "assets": "segment_assets",
    "ebitda": "segment_ebitda",
    "capex": "segment_capex",
    "ebit": "segment_ebit",
}

# These fields are intentionally absent.  They cannot be inferred from Aramco's
# by-nature income statement or from aggregate capex.  Keeping the exclusion
# executable prevents a future "coverage" change from silently manufacturing
# values that the issuer did not report.
NON_PROJECTABLE_PRESENTATION_FIELDS = frozenset({
    "cost_of_revenue",
    "gross_profit",
    "general_and_administrative_expense",
    "selling_and_distribution_expense",
    "ppe_purchases",
    "intangible_asset_purchases",
    "joint_venture_investments",
    "investments_joint_ventures",
})

FIXED_SOURCE_METRICS = frozenset({
    "property_plant_equipment",
    "property_plant_equipment_by_class",
    "current_debt",
    "long_term_debt",
    "borrowings_by_instrument",
    "depreciation_amortization",
    "depreciation_by_ppe_class",
    "intangible_amortization_by_class",
    "revenue",
    "other_income_related_to_sales",
    "revenue_and_other_income_related_to_sales",
    "operating_costs",
    "long_term_investments",
    "shares_repurchased",
    "expected_credit_losses",
    "related_party_receivables",
    "related_party_payables",
})

CANONICAL_TARGET_METRICS = frozenset({
    *PPE_CLASS_ALIASES.values(),
    *SEGMENT_SUFFIX_ALIASES.values(),
    "bank_loans",
    "bonds_sukuk",
    "depreciation_expense",
    "amortization_expense",
    "revenue_ex_other_income",
    "other_operating_revenue",
    "operating_expenses",
    "treasury_share_purchases",
    "allowance_doubtful_accounts",
    "due_from_related_parties",
    "due_to_related_parties",
})

# Used by Database to expose stable formula lineage through the read-only API.
# Segment source names vary by issuer, so those definitions deliberately state
# the governed name transformation rather than pretending to have one fixed
# dependency metric.
PROJECTION_DEFINITIONS = {
    "land": (
        "property_plant_equipment_by_class[asset_class=Land and land improvements]",
        "same_period_after_ppe_reconciliation",
        ("property_plant_equipment_by_class", "property_plant_equipment"),
    ),
    "buildings": (
        "property_plant_equipment_by_class[asset_class=Buildings]",
        "same_period_after_ppe_reconciliation",
        ("property_plant_equipment_by_class", "property_plant_equipment"),
    ),
    "machinery_equipment": (
        "property_plant_equipment_by_class[asset_class=Plant machinery and equipment]",
        "same_period_after_ppe_reconciliation",
        ("property_plant_equipment_by_class", "property_plant_equipment"),
    ),
    "oil_gas_properties": (
        "property_plant_equipment_by_class[asset_class=Oil and gas properties]",
        "same_period_after_ppe_reconciliation",
        ("property_plant_equipment_by_class", "property_plant_equipment"),
    ),
    "construction_in_progress": (
        "property_plant_equipment_by_class[asset_class=Construction in progress]",
        "same_period_after_ppe_reconciliation",
        ("property_plant_equipment_by_class", "property_plant_equipment"),
    ),
    "bank_loans": (
        "borrowings_by_instrument[instrument=Bank borrowings]",
        "same_period_after_total_debt_reconciliation",
        ("borrowings_by_instrument", "current_debt", "long_term_debt"),
    ),
    "bonds_sukuk": (
        "sum(borrowings_by_instrument where instrument in {Debentures,Sukuk})",
        "same_period_after_total_debt_reconciliation",
        ("borrowings_by_instrument", "current_debt", "long_term_debt"),
    ),
    "depreciation_expense": (
        "signed_sum(depreciation_by_ppe_class)",
        "same_period_reconciled_to_depreciation_amortization",
        ("depreciation_by_ppe_class", "depreciation_amortization"),
    ),
    "amortization_expense": (
        "signed_sum(intangible_amortization_by_class)",
        "same_period_reconciled_to_depreciation_amortization",
        ("intangible_amortization_by_class", "depreciation_amortization"),
    ),
    "revenue_ex_other_income": (
        "revenue when revenue + other_income_related_to_sales reconciles to reported combined income",
        "same_period_reconciliation",
        ("revenue", "other_income_related_to_sales", "revenue_and_other_income_related_to_sales"),
    ),
    "other_operating_revenue": (
        "other_income_related_to_sales",
        "same_period_exact_presentation_alias",
        ("other_income_related_to_sales",),
    ),
    "operating_expenses": (
        "operating_costs",
        "same_period_exact_presentation_alias",
        ("operating_costs",),
    ),
    "treasury_share_purchases": (
        "shares_repurchased",
        "same_period_exact_cash_flow_alias",
        ("shares_repurchased",),
    ),
    "allowance_doubtful_accounts": (
        "expected_credit_losses[asset_class=Trade receivables,measure=Loss allowance]",
        "same_period_exact_dimension_alias",
        ("expected_credit_losses",),
    ),
    "due_from_related_parties": (
        "related_party_receivables with source dimensions retained",
        "same_period_exact_dimension_alias",
        ("related_party_receivables",),
    ),
    "due_to_related_parties": (
        "related_party_payables with source dimensions retained",
        "same_period_exact_dimension_alias",
        ("related_party_payables",),
    ),
    **{
        target: (
            f"issuer segment-specific {suffix} metric projected to {target}; segment dimension retained",
            "same_period_exact_segment_alias",
            (),
        )
        for suffix, target in SEGMENT_SUFFIX_ALIASES.items()
    },
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _period_key(fact: Fact) -> tuple:
    return (
        fact.company_id,
        fact.period_start or "",
        fact.period_end,
        fact.period_kind,
        fact.fiscal_year,
        fact.fiscal_quarter,
        fact.currency,
        fact.unit,
        fact.scope,
    )


def projection_period_key(fact: Fact) -> tuple:
    """Public period identity used to limit work to a newly ingested period."""
    return (
        fact.company_id,
        fact.period_end,
        fact.period_kind,
        fact.fiscal_year,
        fact.fiscal_quarter,
    )


def _fact_key(fact: Fact, metric: str | None = None, dimensions: dict[str, str] | None = None) -> tuple:
    return (
        fact.company_id,
        metric or fact.metric,
        fact.period_end,
        fact.period_kind,
        fact.fiscal_year,
        fact.fiscal_quarter,
        fact.currency,
        fact.unit,
        fact.scope,
        tuple(sorted((fact.dimensions if dimensions is None else dimensions).items())),
    )


def _close(left: Decimal, right: Decimal) -> bool:
    tolerance = max(Decimal("0.01"), max(abs(left), abs(right)) * Decimal("0.000000001"))
    return abs(left - right) <= tolerance


def _new_fact(
    metric: str,
    value: Decimal,
    reference: Fact,
    calculation: str,
    dimensions: dict[str, str] | None = None,
    quality_score: Decimal | None = None,
) -> Fact:
    return Fact(
        reference.company_id,
        metric,
        value,
        reference.currency,
        reference.unit,
        reference.period_start,
        reference.period_end,
        reference.period_kind,
        reference.fiscal_year,
        reference.fiscal_quarter,
        reference.source_key,
        reference.source_url,
        reference.filed_at,
        accession=reference.accession,
        form=reference.form,
        is_calculated=True,
        calculation=calculation,
        scope=reference.scope,
        dimensions=dict(reference.dimensions if dimensions is None else dimensions),
        quality_score=quality_score if quality_score is not None else reference.quality_score,
        metric_version=reference.metric_version,
    )


def _coalesce(facts: Iterable[Fact]) -> list[Fact]:
    """Prefer the latest input for one production natural key.

    New, not-yet-published facts are appended after database context by the
    pipeline.  The stable input ordinal therefore resolves a same-day amended
    manifest without double-counting both versions in a reconciliation.
    """
    selected: dict[tuple, tuple[tuple, Fact]] = {}
    for ordinal, fact in enumerate(facts):
        rank = (fact.filed_at, int(not fact.is_calculated), ordinal)
        key = _fact_key(fact)
        if key not in selected or rank > selected[key][0]:
            selected[key] = (rank, fact)
    return [item[1] for item in selected.values()]


class CanonicalProjector:
    """Create only exact, source-traceable canonical aliases and roll-ups."""

    def project(
        self,
        facts: Iterable[Fact],
        target_periods: set[tuple] | None = None,
    ) -> list[Fact]:
        facts = _coalesce(facts)
        reported = {_fact_key(fact) for fact in facts if not fact.is_calculated}
        candidates: dict[tuple, Fact] = {}

        def eligible(reference: Fact) -> bool:
            return target_periods is None or projection_period_key(reference) in target_periods

        def add(fact: Fact) -> None:
            key = _fact_key(fact)
            if fact.metric in NON_PROJECTABLE_PRESENTATION_FIELDS or key in reported:
                return
            previous = candidates.get(key)
            if previous is None or (fact.filed_at, fact.source_key) > (previous.filed_at, previous.source_key):
                candidates[key] = fact

        # An exact issuer-specific segment label becomes the universal segment
        # key only when its prefix agrees with the retained segment dimension.
        for fact in facts:
            segment = fact.dimensions.get("segment")
            if not segment or not eligible(fact):
                continue
            segment_prefix = _slug(segment)
            for suffix, target in SEGMENT_SUFFIX_ALIASES.items():
                if fact.metric == f"{segment_prefix}_{suffix}":
                    add(_new_fact(
                        target,
                        fact.value,
                        fact,
                        f"exact canonical alias of {fact.metric}; segment={segment}",
                    ))
                    break

        groups: dict[tuple, list[Fact]] = defaultdict(list)
        for fact in facts:
            groups[_period_key(fact)].append(fact)

        for group in groups.values():
            if not group or not eligible(group[0]):
                continue
            by_metric: dict[str, list[Fact]] = defaultdict(list)
            for fact in group:
                by_metric[fact.metric].append(fact)

            # PPE class aliases are safe only after the class table reconciles
            # to the reported net PPE balance.
            ppe_total = next((f for f in by_metric["property_plant_equipment"] if not f.dimensions), None)
            ppe_classes = [
                f for f in by_metric["property_plant_equipment_by_class"]
                if set(f.dimensions) == {"asset_class"}
            ]
            if ppe_total and ppe_classes and _close(sum((f.value for f in ppe_classes), Decimal(0)), ppe_total.value):
                for component in ppe_classes:
                    target = PPE_CLASS_ALIASES.get(component.dimensions["asset_class"].casefold())
                    if target:
                        add(_new_fact(
                            target,
                            component.value,
                            component,
                            "exact PPE class alias after sum(property_plant_equipment_by_class) "
                            "reconciled to property_plant_equipment",
                            dimensions={},
                        ))

            # Borrowing instruments must reconcile to current plus long-term
            # debt before components are exposed as canonical debt balances.
            current_debt = next((f for f in by_metric["current_debt"] if not f.dimensions), None)
            long_debt = next((f for f in by_metric["long_term_debt"] if not f.dimensions), None)
            instruments = [
                f for f in by_metric["borrowings_by_instrument"]
                if set(f.dimensions) == {"instrument"}
            ]
            if current_debt and long_debt and instruments:
                instrument_total = sum((f.value for f in instruments), Decimal(0))
                if _close(instrument_total, current_debt.value + long_debt.value):
                    bank = [f for f in instruments if f.dimensions["instrument"].casefold() == "bank borrowings"]
                    if len(bank) == 1:
                        add(_new_fact(
                            "bank_loans",
                            bank[0].value,
                            bank[0],
                            "exact Bank borrowings instrument alias after borrowings table "
                            "reconciled to current_debt + long_term_debt",
                            dimensions={},
                        ))
                    bonds = [
                        f for f in instruments
                        if f.dimensions["instrument"].casefold() in {"debentures", "sukuk"}
                    ]
                    if bonds:
                        reference = max(bonds, key=lambda f: (f.filed_at, f.source_key))
                        add(_new_fact(
                            "bonds_sukuk",
                            sum((f.value for f in bonds), Decimal(0)),
                            reference,
                            "sum(Debentures, Sukuk) after borrowings table reconciled to "
                            "current_debt + long_term_debt",
                            dimensions={},
                            quality_score=min(f.quality_score for f in bonds),
                        ))

            # Split D&A only when all class charges together reproduce the
            # issuer's reported combined D&A line.  The combined line supplies
            # the presentation sign used for both outputs.
            da_total = next((f for f in by_metric["depreciation_amortization"] if not f.dimensions), None)
            depreciation = by_metric["depreciation_by_ppe_class"]
            amortization = by_metric["intangible_amortization_by_class"]
            if da_total and depreciation and amortization:
                depreciation_total = sum((abs(f.value) for f in depreciation), Decimal(0))
                amortization_total = sum((abs(f.value) for f in amortization), Decimal(0))
                if _close(depreciation_total + amortization_total, abs(da_total.value)):
                    sign = Decimal(-1) if da_total.value < 0 else Decimal(1)
                    add(_new_fact(
                        "depreciation_expense",
                        sign * depreciation_total,
                        max(depreciation, key=lambda f: (f.filed_at, f.source_key)),
                        "signed sum(depreciation_by_ppe_class), reconciled with "
                        "amortization classes to depreciation_amortization",
                        dimensions={},
                        quality_score=min(f.quality_score for f in depreciation),
                    ))
                    add(_new_fact(
                        "amortization_expense",
                        sign * amortization_total,
                        max(amortization, key=lambda f: (f.filed_at, f.source_key)),
                        "signed sum(intangible_amortization_by_class), reconciled with "
                        "depreciation classes to depreciation_amortization",
                        dimensions={},
                        quality_score=min(f.quality_score for f in amortization),
                    ))

            # Some by-nature statements show revenue, sales-related other
            # income, and their combined subtotal.  That explicit arithmetic
            # establishes the narrower revenue-ex-other-income alias.
            revenue = next((f for f in by_metric["revenue"] if not f.dimensions), None)
            other_sales = next((f for f in by_metric["other_income_related_to_sales"] if not f.dimensions), None)
            combined = next((f for f in by_metric["revenue_and_other_income_related_to_sales"] if not f.dimensions), None)
            if revenue and other_sales and combined and _close(revenue.value + other_sales.value, combined.value):
                add(_new_fact(
                    "revenue_ex_other_income",
                    revenue.value,
                    revenue,
                    "revenue alias after revenue + other_income_related_to_sales "
                    "reconciled to revenue_and_other_income_related_to_sales",
                    dimensions={},
                ))

        # Exact note aliases retain dimensions when a total is not available;
        # this exposes the source components without pretending they are a
        # consolidated sum.
        for fact in facts:
            if not eligible(fact):
                continue
            if fact.metric == "operating_costs" and not fact.dimensions:
                add(_new_fact(
                    "operating_expenses", fact.value, fact,
                    "exact issuer-presented operating-costs alias",
                    dimensions={},
                ))
            elif fact.metric == "other_income_related_to_sales" and not fact.dimensions:
                add(_new_fact(
                    "other_operating_revenue", fact.value, fact,
                    "exact issuer-presented sales-related other operating income alias",
                    dimensions={},
                ))
            elif fact.metric == "shares_repurchased" and not fact.dimensions:
                add(_new_fact(
                    "treasury_share_purchases", fact.value, fact,
                    "exact cash-flow alias of issuer-reported shares repurchased",
                    dimensions={},
                ))
            elif fact.metric == "expected_credit_losses" and {
                key: value.casefold() for key, value in fact.dimensions.items()
            } == {"asset_class": "trade receivables", "measure": "loss allowance"}:
                add(_new_fact(
                    "allowance_doubtful_accounts",
                    fact.value,
                    fact,
                    "exact expected-credit-loss allowance alias for trade receivables",
                    dimensions={},
                ))
            elif fact.metric == "related_party_receivables" and fact.dimensions:
                add(_new_fact(
                    "due_from_related_parties",
                    fact.value,
                    fact,
                    "exact related-party receivable component alias; source dimensions retained",
                ))
            elif fact.metric == "related_party_payables" and fact.dimensions:
                add(_new_fact(
                    "due_to_related_parties",
                    fact.value,
                    fact,
                    "exact related-party payable component alias; source dimensions retained",
                ))

        return sorted(candidates.values(), key=lambda f: tuple(str(part) for part in _fact_key(f)))


def load_projection_facts(db: Database, company_id: str) -> list[Fact]:
    """Load only the current numeric facts relevant to canonical projection."""
    metrics = sorted(FIXED_SOURCE_METRICS | CANONICAL_TARGET_METRICS)
    placeholders = ",".join("?" for _ in metrics)
    rows = db.conn.execute(
        f"""SELECT d.* FROM data_points d JOIN metric_definitions m USING(metric_key)
        WHERE d.company_id=? AND d.is_current=1 AND d.value_type='decimal'
        AND d.value_decimal IS NOT NULL AND
        (d.metric_key IN ({placeholders}) OR
         (d.dimensions_json<>'{{}}' AND m.statement='segments'))
        ORDER BY d.period_end,d.metric_key,d.dimensions_json""",
        (company_id, *metrics),
    ).fetchall()
    return [Fact(
        company_id=row["company_id"],
        metric=row["metric_key"],
        value=Decimal(row["value_decimal"]),
        currency=row["currency"],
        unit=row["unit"],
        period_start=row["period_start"] or None,
        period_end=row["period_end"],
        period_kind=PeriodKind(row["period_kind"]),
        fiscal_year=row["fiscal_year"],
        fiscal_quarter=row["fiscal_quarter"] or None,
        source_key=row["source_key"],
        source_url=row["source_url"],
        filed_at=row["filed_at"],
        accession=row["accession"],
        form=row["form"],
        is_calculated=bool(row["is_calculated"]),
        calculation=row["calculation"],
        scope=row["scope"],
        dimensions=json.loads(row["dimensions_json"]),
        quality_score=Decimal(row["quality_score"]),
        metric_version=row["metric_version"],
    ) for row in rows]


def refresh_canonical_projections(db: Database, company_id: str) -> dict:
    """Idempotently materialize canonical projections for an existing database."""
    projected = CanonicalProjector().project(load_projection_facts(db, company_id))
    states = db.publish_batch(projected) if projected else []
    return {
        "company_id": company_id,
        "projected": len(projected),
        "inserted": states.count("inserted"),
        "restated": states.count("restated"),
        "duplicates": states.count("duplicate"),
        "metrics": sorted({fact.metric for fact in projected}),
        "states": states,
    }
