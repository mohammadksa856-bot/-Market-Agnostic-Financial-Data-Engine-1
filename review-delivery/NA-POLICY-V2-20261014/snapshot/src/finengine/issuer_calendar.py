"""Versioned issuer calendars for local B05 R2 measurement.

No calendar is inferred from a listing date or a Gregorian year label. The
reviewed ledger is the authoritative source of period boundaries, including
transition years. Disclosure due dates are separate from accounting periods.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone
from copy import deepcopy


POLICY_VERSION = "b05-r2-cma-2026-01-19"
SOURCE_URL = "https://cma.gov.sa/RulesRegulations/Regulations/Documents/RULES_ON_THE_OFFER_OF_SECURITIES_AND_CONTINUING_OBLIGATIONS_ar2026.pdf"
PREVIOUS_SOURCE_URL = "https://cma.gov.sa/en/RulesRegulations/Regulations/Documents/Rules_on_the_offer_of_securities_and_continuing_obligations_11_2025_EN.pdf"
SAUDI_TZ = timezone(timedelta(hours=3))


def _instant(value: str) -> datetime:
    """Date-only knowledge is conservative: available at end of Saudi day."""
    value = str(value)
    if len(value) == 10:
        return datetime.combine(date.fromisoformat(value), time.max, SAUDI_TZ)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp requires an explicit timezone")
    return parsed.astimezone(SAUDI_TZ)


def _date(value: str) -> date:
    return _instant(value).date()


def add_calendar_months(value: date, months: int) -> date:
    """Calendar months, clamped at month end; never approximate as 90 days."""
    number = value.year * 12 + value.month - 1 + months
    year, month0 = divmod(number, 12)
    month = month0 + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def _check_sequence(periods: list[dict], kind: str, blockers: list[str]) -> None:
    """Counts cannot hide gaps, overlaps or mislabeled quarter order."""
    sequence = sorted(periods, key=lambda x: (x["period_start"], x["period_end"]))
    for previous, current in zip(sequence, sequence[1:]):
        expected_start = _date(previous["period_end"]) + timedelta(days=1)
        actual_start = _date(current["period_start"])
        if actual_start > expected_start:
            blockers.append(f"{kind}_period_sequence_gap")
        elif actual_start < expected_start:
            blockers.append(f"{kind}_period_sequence_overlap")
        if kind == "quarter":
            if current["quarter"] != previous["quarter"] % 4 + 1:
                blockers.append("quarter_sequence_label_conflict")
            if previous["quarter"] != 4 and previous["fiscal_year"] != current["fiscal_year"]:
                blockers.append("quarter_fiscal_year_conflict")
            if previous["quarter"] == 4 and previous["fiscal_year"] == current["fiscal_year"]:
                blockers.append("quarter_fiscal_year_conflict")


def build_period_targets(profile: dict, as_of: str, years: int = 5, quarters: int = 12) -> dict:
    """Return required ledger targets, undisclosed-yet targets and explicit holds.

    profile requires market (main/nomu), issuer_type=equity, reviewed=True,
    calendar_version, calendar_known_at, calendar_source, fiscal_periods. A
    calendar_versions list may replace the calendar fields and is selected by
    known_at, never by the most recent version in today's files. Ledger entries
    require period_start/end, period_kind (FY/Q/H1), fiscal_year and quarter for
    Q. Annual and reporting interim targets become required *after* due_at.
    Q4 is an analytical target using the annual deadline, not a made-up filing.
    The original five-FY/twelve-Q gates remain unchanged and conflicts hold.
    Missing entry known_at inherits the reviewed calendar-version known_at;
    this attests that the version includes the entire explicit ledger. Timestamps
    require an offset. Date-only as_of is the end of that day in Saudi Arabia.
    Historic targets remain valid; current law is not proof of historic lateness.
    ledger_complete_through is a reviewed calendar assertion that all expected
    periods through that Saudi day are listed, independent of available data.
    Missing or expired assertions hold readiness without inventing newer periods.
    """
    instant = _instant(as_of)
    moment = instant.date()
    if years != 5 or quarters != 12:
        raise ValueError("Original contract requires five fiscal years and twelve quarters")
    result = {
        "as_of": moment.isoformat() if len(str(as_of)) == 10 else instant.isoformat(), "policy_version": POLICY_VERSION,
        "source_url": SOURCE_URL, "annual": [], "interim": [],
        "analytical_quarters": [], "not_due": [], "blockers": [],
        "history_classification": "unknown", "contract_requirements": {"years": years, "quarters": quarters},
        "calendar_version": None, "contract_gate_changes_applied": False,
    }
    blockers = result["blockers"]
    if moment < date(2025, 11, 24):
        blockers.append("disclosure_policy_not_known_as_of")
        return result
    if moment < date(2026, 1, 19):
        result["policy_version"] = "b05-r2-cma-2025-11-24"
        result["source_url"] = PREVIOUS_SOURCE_URL
    selected = deepcopy(profile)
    if "calendar_versions" in profile:
        versions = [v for v in profile["calendar_versions"] if v.get("known_at") and _instant(v["known_at"]) <= instant]
        if not versions:
            blockers.append("issuer_calendar_not_known_as_of")
            return result
        version = max(versions, key=lambda v: (_instant(v["known_at"]), str(v.get("version", ""))))
        selected.update(version)
        selected["calendar_known_at"] = version["known_at"]
        selected["calendar_version"] = version.get("version")
    if selected.get("reviewed") is not True or not selected.get("calendar_source") or not selected.get("calendar_version"):
        blockers.append("issuer_calendar_unverified")
        return result
    if not selected.get("calendar_known_at") or _instant(selected["calendar_known_at"]) > instant:
        blockers.append("issuer_calendar_not_known_as_of")
        return result
    result["calendar_version"] = selected["calendar_version"]
    complete_through = selected.get("ledger_complete_through")
    result["ledger_complete_through"] = complete_through
    result["target_window_verified"] = False
    if not complete_through:
        blockers.append("issuer_calendar_target_window_unverified")
    else:
        try:
            if _date(complete_through) < moment:
                blockers.append("issuer_calendar_target_window_expired")
            else:
                result["target_window_verified"] = True
        except (ValueError, TypeError):
            blockers.append("issuer_calendar_target_window_unverified")
    market = selected.get("market")
    if market not in {"main", "nomu"} or selected.get("issuer_type") != "equity":
        blockers.append("issuer_disclosure_policy_unsupported")
        return result
    ledger = selected.get("fiscal_periods", [])
    if not ledger:
        blockers.append("fiscal_period_ledger_missing")
        return result
    label_boundaries = {}
    conflicting_labels = set()
    for entry in ledger:
        if entry.get("known_at") and _instant(entry["known_at"]) > instant:
            continue
        label = (entry.get("period_kind"), str(entry.get("fiscal_year")), entry.get("quarter"))
        boundary = (entry.get("period_start"), entry.get("period_end"))
        if label in label_boundaries and label_boundaries[label] != boundary:
            conflicting_labels.add(label)
        label_boundaries[label] = boundary
    if conflicting_labels:
        blockers.append("conflicting_fiscal_period_boundaries")
    seen = set()
    for entry in ledger:
        if entry.get("known_at") and _instant(entry["known_at"]) > instant:
            continue
        if (entry.get("period_kind"), str(entry.get("fiscal_year")), entry.get("quarter")) in conflicting_labels:
            continue
        try:
            start, end = _date(entry["period_start"]), _date(entry["period_end"])
            kind, fy = entry["period_kind"], entry["fiscal_year"]
            quarter = entry.get("quarter")
            if start > end or kind not in {"FY", "Q", "H1"} or (kind == "Q" and quarter not in {1, 2, 3, 4}):
                raise ValueError("invalid period")
            key = (start, end, kind, fy, quarter)
            if key in seen:
                raise ValueError("duplicate period")
            seen.add(key)
        except (ValueError, KeyError, TypeError):
            blockers.append("invalid_fiscal_period_ledger")
            continue
        period = deepcopy(entry)
        annual_due = add_calendar_months(end, 3)
        if kind == "FY":
            due = annual_due
            agm = entry.get("agm_date")
            if agm and entry.get("agm_source") and entry.get("agm_known_at") and _instant(entry["agm_known_at"]) <= instant:
                due = min(due, _date(agm) - timedelta(days=21))
            destination = "annual"
        elif kind == "H1":
            if market != "nomu":
                blockers.append("interim_frequency_conflicts_with_issuer")
                continue
            due, destination = end + timedelta(days=45), "interim"
        else:
            destination = "analytical_quarters"
            if quarter == 4:
                annual = next((x for x in ledger if x.get("period_kind") == "FY" and x.get("fiscal_year") == fy and x.get("period_end") == entry["period_end"] and (not x.get("known_at") or _instant(x["known_at"]) <= instant)), None)
                if annual is None:
                    blockers.append("q4_annual_boundary_unverified")
                    continue
                due = annual_due
                if annual.get("agm_date") and annual.get("agm_source") and annual.get("agm_known_at") and _instant(annual["agm_known_at"]) <= instant:
                    due = min(due, _date(annual["agm_date"]) - timedelta(days=21))
            elif market == "nomu":
                blockers.append("quarter_history_requires_governed_nomu_resolution")
                continue
            else:
                due = end + timedelta(days=30)
        period["due_at"] = due.isoformat()
        period["deadline_basis"] = ("CMA article 94" if moment >= date(2026, 1, 19) else "CMA article 93") if kind == "H1" else "CMA article 66"
        period["known_at"] = entry.get("known_at") or selected["calendar_known_at"]
        period["disclosure_delay_assessed"] = False
        period["historical_deadline_authority_known"] = end >= date(2025, 11, 24)
        if not period["historical_deadline_authority_known"]:
            period["deadline_basis"] = "historical_requirement_only_not_official_lateness_evidence"
            period["deadline_estimate_only"] = True
        period["disclosure_status"] = "required" if moment > due else "not_due"
        if moment <= due:
            result["not_due"].append(period)
        else:
            result[destination].append(period)
            if destination == "analytical_quarters" and quarter != 4 and market == "main":
                result["interim"].append(deepcopy(period))
    for key, limit in (("annual", years), ("analytical_quarters", quarters)):
        result[key] = sorted(result[key], key=lambda x: (x["period_end"], x["period_start"], str(x["fiscal_year"])), reverse=True)[:limit]
    _check_sequence(result["annual"], "annual", blockers)
    _check_sequence(result["analytical_quarters"], "quarter", blockers)
    result["interim"] = sorted(result["interim"], key=lambda x: (x["period_end"], x["period_start"]), reverse=True)[:quarters]
    result["not_due"] = sorted(result["not_due"], key=lambda x: (x["period_end"], x["period_kind"]))
    if market == "nomu":
        blockers.append("semiannual_issuer_original_quarter_gate_conflict")
    if len(result["annual"]) < years or len(result["analytical_quarters"]) < quarters:
        history_start = selected.get("history_start")
        if history_start and (moment - _date(history_start)).days < 5 * 365:
            result["history_classification"] = "short_operating_history_requires_contract_decision"
            blockers.append("short_operating_history_original_gate_conflict")
        else:
            result["history_classification"] = "missing_history" if history_start else "history_origin_unknown"
            blockers.append("historical_period_ledger_incomplete")
    else:
        result["history_classification"] = "full_contract_period_targets" if not any("sequence" in code or "conflict" in code or "invalid" in code for code in blockers) else "historical_period_sequence_conflict"
        if not result["target_window_verified"]:
            result["history_classification"] = "historical_subset_target_window_unverified"
    listing_date = selected.get("listing_date")
    result["newly_listed"] = bool(listing_date and 0 <= (moment - _date(listing_date)).days < 365)
    result["blockers"] = sorted(set(blockers))
    return result
