"""Contract ownership keys derived from ownership-position rows.

A key is emitted only when the rows determine it: a list of named holders never stands in
for an investor-class total, and a ranking is emitted only when no unnamed holder can change it.

Row roles, read from ``ownership_type``:
- partition rows split the issued shares (``direct``, ``indirect``, ``free_float``, ``treasury`` and
  any other type); at one date they must sum to 100% within PARTITION_TOLERANCE to be used;
- ``aggregate`` rows are an investor-class total that overlaps the partition (e.g. all foreign
  investors, most of them inside the free float).
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import json

PARTITION_TOLERANCE = Decimal("0.0001")
CLASS_TOTAL_TYPE = "aggregate"
SINGLE_HOLDER_TYPES = {"direct", "indirect"}
NOT_A_HOLDER_TYPES = {"treasury"}
# Partition rows that by definition hold no strategic stake.
NON_STRATEGIC_TYPES = {"free_float", "treasury"}
STRATEGIC_HOLDER_TYPES = {"strategic", "corporate_strategic", "sovereign_and_strategic"}
# Investor-class keys and the holder_type a class total carries.
CLASS_KEYS = {"foreign_ownership": "foreign", "institutional_ownership": "institutional",
              "retail_ownership": "retail", "insider_ownership": "insider"}
TOP_N_KEYS = {"top_5_shareholder_concentration": 5, "top_10_shareholder_concentration": 10}
# A holder is major at or above this share at either date of a change.
MAJOR_HOLDER_THRESHOLD = Decimal("0.05")
# Contract keys whose definition needs a decision; never emitted until it is made.
DEFINITION_PENDING = {
    "ownership_concentration": "measure not defined: largest holder, holders >= 5%, or a Herfindahl index",
}
DERIVED_KEYS = {"government_ownership", "free_float", "strategic_ownership", "major_holder_change",
                *CLASS_KEYS, *TOP_N_KEYS}


def _pct(row):
    return None if row["ownership_pct"] is None else Decimal(str(row["ownership_pct"]))


def _metadata(row) -> dict:
    try:
        value = json.loads(row["metadata_json"] or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _reconciled(partition) -> bool:
    return bool(partition) and all(_pct(row) is not None for row in partition) and \
        abs(sum(_pct(row) for row in partition) - 1) <= PARTITION_TOLERANCE


def ownership_metrics(rows) -> dict[str, list[dict]]:
    """Determined ownership keys as {key: [{as_of_date, value, basis, holder_key?}]}, newest date first."""
    by_date = defaultdict(list)
    for row in rows:
        if row["as_of_date"]:
            by_date[str(row["as_of_date"])[:10]].append(row)
    out: dict[str, list[dict]] = defaultdict(list)

    def emit(key, date, value, basis, holder_key=None):
        item = {"as_of_date": date, "value": value, "basis": basis}
        if holder_key is not None:
            item["holder_key"] = holder_key
        out[key].append(item)

    for date in sorted(by_date, reverse=True):
        day = by_date[date]
        partition = [row for row in day if row["ownership_type"] != CLASS_TOTAL_TYPE]
        reconciled = _reconciled(partition)
        for row in day:
            if row["holder_type"] == "government" and _pct(row) is not None:
                emit("government_ownership", date, _pct(row), "government holder row", row["holder_key"])
            if row["ownership_type"] == "free_float" and _pct(row) is not None:
                emit("free_float", date, _pct(row), "free float row", row["holder_key"])

        for key, investor_class in CLASS_KEYS.items():
            totals = [row for row in day if row["ownership_type"] == CLASS_TOTAL_TYPE
                      and row["holder_type"] == investor_class and _pct(row) is not None]
            members = [row for row in day if row["holder_type"] == investor_class
                       and row["ownership_type"] != CLASS_TOTAL_TYPE]
            if len(totals) == 1:
                emit(key, date, _pct(totals[0]), "investor-class total row")
            elif not totals and members and all(
                    _metadata(row).get("class_complete") is True and _pct(row) is not None for row in members):
                # the source states these rows are every holder of the class (e.g. the full insider-interest table)
                emit(key, date, sum(_pct(row) for row in members),
                     "sum of a complete holder list for the class")

        if reconciled and all(row["holder_type"] in STRATEGIC_HOLDER_TYPES
                              or row["ownership_type"] in NON_STRATEGIC_TYPES
                              or row["ownership_type"] in SINGLE_HOLDER_TYPES for row in partition):
            strategic = [row for row in partition if row["holder_type"] in STRATEGIC_HOLDER_TYPES]
            if strategic:
                emit("strategic_ownership", date, sum(_pct(row) for row in strategic),
                     "sum of strategic holder rows in a reconciled partition")

        if reconciled:
            holders = sorted((_pct(row) for row in partition if row["ownership_type"] in SINGLE_HOLDER_TYPES),
                             reverse=True)
            pooled = [_pct(row) for row in partition
                      if row["ownership_type"] not in SINGLE_HOLDER_TYPES | NOT_A_HOLDER_TYPES]
            largest_pooled = max(pooled, default=Decimal(0))
            for key, n in TOP_N_KEYS.items():
                if len(holders) >= n and largest_pooled <= holders[n - 1]:
                    # no unnamed holder inside a pooled row can exceed the n-th named holder
                    emit(key, date, sum(holders[:n]), f"largest {n} named holders; pooled rows cannot outrank them")
                elif holders and largest_pooled == 0:
                    emit(key, date, sum(holders), "every holder is named")

    dates = sorted(by_date, reverse=True)
    if len(dates) >= 2:
        latest, prior = dates[0], dates[1]
        holdings = {date: {(row["holder_key"], row["ownership_type"]): _pct(row) for row in by_date[date]
                           if row["ownership_type"] != CLASS_TOTAL_TYPE and _pct(row) is not None}
                    for date in (latest, prior)}
        # Within partitions that both add up to 100%, a holder missing at one date held nothing then
        # (an exit or an entry); otherwise only holders reported at both dates are compared.
        both_reconciled = all(_reconciled([row for row in by_date[date] if row["ownership_type"] != CLASS_TOTAL_TYPE])
                              for date in (latest, prior))
        identities = (holdings[latest].keys() | holdings[prior].keys() if both_reconciled
                      else holdings[latest].keys() & holdings[prior].keys())
        for identity in sorted(identities):
            now = holdings[latest].get(identity, Decimal(0))
            before = holdings[prior].get(identity, Decimal(0))
            if max(now, before) >= MAJOR_HOLDER_THRESHOLD:
                basis = (f"ownership_pct change since {prior}" if identity in holdings[latest] and identity in holdings[prior]
                         else f"ownership_pct change since {prior}; absent from one reconciled partition (0%)")
                emit("major_holder_change", latest, now - before, basis, identity[0])
    return dict(out)
