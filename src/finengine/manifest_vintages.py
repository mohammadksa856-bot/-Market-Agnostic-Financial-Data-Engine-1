from __future__ import annotations

"""One source of record per fact when issuer publications overlap.

Banks republish the same period in several documents: each quarterly data
supplement repeats the last five quarters, and each Pillar 3 KM1 table repeats
the last five quarter ends. Later vintages can reclassify earlier periods, and
spreadsheet formula cells carry float noise. Publishing every vintage creates
cross-manifest conflicts and version churn for what is one fact.

``reconcile_vintages`` keeps exactly one publishable occurrence per fact
identity. The highest-assurance document type wins, then the document that
covers the latest reporting period, then the latest ``filed_at``. The period
comes before the filing date because issuer IR files rarely expose a machine-
readable publication time (it is often inferred from document metadata),
while a quarterly series is always republished after the quarter it covers.
A resubmission of the same period is still ordered by ``filed_at``. Every other
occurrence moves to its manifest's ``excluded_facts`` together with the
winning source and value, so no reported number is discarded silently and no
number is invented.

With ``by_period=True`` the winner is chosen per period instead of per metric:
the best-ranked document for a period supplies every fact of that period. Use
it for documents that report the same statements (reviewed interim statements
and data supplements) so accounting identities are never evaluated across a
mixture of original and restated vintages. Do not use it across different
disclosure families - a KM1 table and an income statement share periods but
not metrics.
"""

import copy
import json
from decimal import Decimal

# Reviewed or audited statements outrank regulatory disclosures, which outrank
# issuer convenience workbooks for the same fact.
ASSURANCE_RANK = {
    "annual-report": 3,
    "financial-statements": 3,
    "interim-report": 3,
    "regulatory-disclosure": 2,
    "data-supplement": 1,
}


def _identity(manifest: dict, fact: dict) -> tuple:
    return (
        str(manifest.get("company_id") or ""),
        fact["metric"],
        fact["period_kind"],
        fact["period_end"],
        fact.get("scope", "consolidated"),
        json.dumps(fact.get("dimensions") or {}, sort_keys=True, separators=(",", ":")),
    )


def _period_identity(manifest: dict, fact: dict) -> tuple:
    key = _identity(manifest, fact)
    return key[:1] + key[2:]


def _scaled(fact: dict) -> Decimal:
    scale = fact.get("scale")
    return Decimal(str(fact["value"])) * (Decimal(str(scale)) if scale not in (None, "") else 1)


def _rank(manifest: dict) -> tuple:
    # A manifest without a header period is ranked by the latest period its
    # facts cover, never by filing metadata alone.
    covered = manifest.get("period_end") or max(
        (str(fact.get("period_end") or "") for fact in manifest.get("facts", [])), default="")
    return (
        ASSURANCE_RANK.get(str(manifest.get("filing_type") or ""), 2),
        str(covered),
        str(manifest.get("filed_at") or ""),
    )


def reconcile_vintages(manifests: list[dict], fixed: list[dict] | tuple = (),
                       by_period: bool = False) -> list[dict]:
    """Return copies of ``manifests`` with overlapping facts resolved.

    ``fixed`` manifests (already reviewed files that must not be rewritten)
    take part in ranking and win ties, but are never returned or modified.
    """
    identity = _period_identity if by_period else _identity
    working = [copy.deepcopy(manifest) for manifest in manifests]
    winners: dict[tuple, tuple] = {}
    for is_fixed, manifest in [*((True, item) for item in fixed), *((False, item) for item in working)]:
        for fact in manifest.get("facts", []):
            key = identity(manifest, fact)
            candidate = (_rank(manifest), is_fixed, manifest)
            best = winners.get(key)
            if best is None or candidate[:2] > best[:2]:
                winners[key] = candidate
    for manifest in working:
        kept: list[dict] = []
        excluded = list(manifest.get("excluded_facts", []))
        for fact in manifest.get("facts", []):
            winner = winners[identity(manifest, fact)][2]
            if winner is manifest:
                kept.append(fact)
                continue
            fact_key = _identity(manifest, fact)
            match = next((item for item in winner.get("facts", [])
                          if _identity(winner, item) == fact_key), None)
            if match is None:
                reason = "period_supplied_by_higher_ranked_publication"
            elif _scaled(match) == _scaled(fact):
                reason = "superseded_by_higher_ranked_publication"
            else:
                reason = "restated_in_higher_ranked_publication"
            excluded.append({
                **fact,
                "reason": reason,
                "superseded_by": {
                    "source_url": winner.get("source_url"),
                    "filing_type": winner.get("filing_type"),
                    "filed_at": winner.get("filed_at"),
                    "value": match["value"] if match else None,
                    "scale": match.get("scale") if match else None,
                },
            })
        manifest["facts"] = kept
        manifest["excluded_facts"] = excluded
    return working
