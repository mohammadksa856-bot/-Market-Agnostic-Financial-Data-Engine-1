"""Pure, as-of evaluation of authoritative disclosure-monitoring evidence."""
from datetime import date, datetime, time, timedelta, timezone
import re


def _instant(value, *, end=False):
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime.combine(value, time.max if end else time.min)
    elif isinstance(value, str) and len(value) == 10:
        result = datetime.combine(date.fromisoformat(value), time.max if end else time.min)
    else:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def _gaps(spans, start, end):
    cursor = start
    gaps = []
    for left, right in sorted(spans):
        if right < cursor:
            continue
        if left > cursor:
            gaps.append({"start": cursor.isoformat(), "end": (left - timedelta(microseconds=1)).isoformat()})
        cursor = max(cursor, right + timedelta(microseconds=1))
    if cursor <= end:
        gaps.append({"start": cursor.isoformat(), "end": end.isoformat()})
    return gaps


def evaluate_continuity(intervals, window_start, window_end, as_of):
    """Assess a requested monitoring window without inferring absence from silence.

    Date-only window endpoints denote inclusive UTC days. Timestamp endpoints are
    exact instants. Captures must be known by as_of and complete by observed_at.
    A caller may use the listing date as window_start, but cannot shrink its
    contractual reporting window implicitly. Evidence does not confer N/A.
    """
    start, end, cutoff = _instant(window_start), _instant(window_end, end=True), _instant(as_of)
    if end < start or end > cutoff:
        raise ValueError("Monitoring window must be ordered and end no later than as_of")
    spans, absence_spans, rejected, events, accepted = [], [], [], [], []
    for index, record in enumerate(intervals):
        reason = None
        try:
            left, right = _instant(record["start"]), _instant(record["end"], end=True)
            observed = _instant(record["observed_at"])
            if left > right or observed < right:
                reason = "invalid_capture_interval"
            elif observed > cutoff:
                reason = "capture_not_known_as_of"
            elif record.get("status") != "success":
                reason = "capture_not_successful"
            elif record.get("authoritative") is not True:
                reason = "authority_not_verified"
            elif not str(record.get("source_url", "")).strip() or not re.fullmatch(r"[0-9a-fA-F]{64}", str(record.get("source_sha256", ""))):
                reason = "source_evidence_missing"
        except (ValueError, TypeError, KeyError, OverflowError):
            reason = "invalid_capture_record"
        if reason:
            rejected.append({"index": index, "reason": reason})
            continue
        left, right = max(left, start), min(right, end)
        if left > right:
            continue
        spans.append((left, right))
        accepted.append(index)
        if record.get("no_event_verified") is True and not record.get("events"):
            absence_spans.append((left, right))
        for event in record.get("events", []):
            try:
                occurred = _instant(event["occurred_at"])
                known = _instant(event["observed_at"])
                if left <= occurred <= right and occurred <= known <= observed and event.get("verified") is True:
                    events.append(dict(event))
            except (ValueError, TypeError, KeyError):
                continue
    gaps = _gaps(spans, start, end)
    absence_gaps = _gaps(absence_spans, start, end)
    state = "events_observed" if events else ("verified_no_events" if not gaps and not absence_gaps else "unknown")
    return {"coverage_complete": not gaps, "event_state": state, "gaps": gaps,
            "absence_proof_gaps": absence_gaps, "accepted_capture_indices": accepted,
            "rejected_captures": rejected, "events": sorted(events, key=lambda e: (str(e.get("occurred_at")), str(e.get("id", "")))),
            "as_of": cutoff.isoformat(), "window_start": start.isoformat(), "window_end": end.isoformat(),
            "not_applicable": False, "accuracy_certification": False}
