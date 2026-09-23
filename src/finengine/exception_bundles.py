from __future__ import annotations

"""Group open exceptions into small, reviewable "bundles" by shared root cause.

Why this exists (see docs/ops/exception-bundles-workflow.md for the full
picture): reviewing exceptions one at a time burns a huge amount of AI/human
review time, because each exception gets read with full document context even
when hundreds of them share one root cause (one reader bug, one missing
caption->metric mapping, one unreachable source domain, ...).

This module never writes anything back to the database and never touches
`data/imports/**` or `data/raw/**`. It reads exception rows the caller already
fetched (via the existing `FinancialQueryService.exceptions()` path — this
module does not run its own SQL query against the `exceptions` table) plus a
small amount of joined context (source_documents, data_catalog_fields,
metric_definitions), and emits compact bundles.

Hard privacy rule: a bundle never contains full document text. Each bundle
carries at most `MAX_SAMPLES` representative exceptions, each with a
`context`/`table_context` string capped at `MAX_CONTEXT_CHARS`, plus a
reference (path/hash) to the archived source — never the source content
itself. Every string field that lands in a bundle is passed through
`redact_secrets()` first, as a safety net.
"""

import difflib
import re
from collections import OrderedDict
from urllib.parse import urlparse

from .reading import BANK_LINE_MAP, INSURANCE_LINE_MAP, LINE_MAP

# ---------------------------------------------------------------------------
# Constants documented in the CLI help text (see cli.py "exception-bundles").
# ---------------------------------------------------------------------------

MAX_SAMPLES = 3
MAX_CONTEXT_CHARS = 240
MAX_FIELD_CHARS = 160

CLASSIFICATIONS = (
    "generic_parser_fix",
    "generic_mapping_fix",
    "company_specific_review",
    "source_unavailable",
    "not_applicable",
    "licensed_provider_required",
    "data_conflict_or_restatement",
)

# Exception codes seen in pipeline.py/cli.py/universe.py at the point an
# exception is raised (grep `db.exception(` across the codebase). Codes not
# listed here fall through to the message-based heuristics in `classify()`,
# and ultimately default to "company_specific_review" — the safe default
# when nothing lets us say a fix generalizes.
_MAPPING_CODES = {"unmapped_metric", "mapping_review_required"}
_PARSER_CODES = {
    "invalid_value", "invalid_fact", "required_field", "invalid_period",
    "invalid_fiscal_quarter", "missing_period_start", "pdf_extraction_failed",
    "pdf_ocr_required", "interim_period_semantics_required",
}
_CONFLICT_CODES = {
    "lower_trust_current_conflict", "balance_sheet_unbalanced",
    "period_rollforward_mismatch",
}
_NOT_APPLICABLE_CODES = {"not_applicable"}

_UNAVAILABLE_HINTS = (
    "not found", "404", "unreachable", "timeout", "timed out", "connection",
    "dns", "no such host", "source_access_blocked", "access blocked", "denied",
    "refused", "gone", "410",
)
_LICENSED_HINTS = (
    "licensed", "consensus", "subscription", "paid data", "paid provider",
    "wisesheets", "sahmk", "analyst estimate",
)
_NOT_APPLICABLE_HINTS = ("not applicable", "structurally inapplicable")

# ---------------------------------------------------------------------------
# Secret redaction (safety net; exception payloads should never contain
# secrets in the first place, but bundles are the thing that gets shared
# outside the pipeline, so this is the last line of defense).
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                                    # AWS access key id
    re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-_.]{20,}"),                      # bearer tokens
    re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),  # JWT
    re.compile(r"sk-[a-zA-Z0-9]{16,}"),                                 # OpenAI-style API key
    re.compile(r"(?i)(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"]?[a-zA-Z0-9\-_.]{10,}['\"]?"),
    re.compile(r"(?i)(postgres|postgresql|mysql|mongodb|redis)(\+\w+)?://[^\s:@/]+:[^\s@/]+@\S+"),  # conn strings
]


def redact_secrets(text: str | None) -> tuple[str | None, bool]:
    """Return (redacted_text, was_redacted). Never raises on non-secret text."""
    if text is None:
        return None, False
    redacted = False
    out = text
    for pattern in _SECRET_PATTERNS:
        new_out, count = pattern.subn("[REDACTED:secret-like-value]", out)
        if count:
            redacted = True
            out = new_out
    return out, redacted


def _clip(text: str | None, limit: int) -> str | None:
    if text is None:
        return None
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _safe(text, limit: int = MAX_FIELD_CHARS) -> tuple[str | None, bool]:
    """Redact then clip a value that may land in bundle output."""
    if text is None:
        return None, False
    clean, was_redacted = redact_secrets(str(text))
    return _clip(clean, limit), was_redacted


# ---------------------------------------------------------------------------
# Reader / domain / classification derivation
# ---------------------------------------------------------------------------

def resolve_reader(payload: dict, stage: str, content_type: str | None) -> str:
    """Best-effort identification of which reader/parser/connector produced
    this exception.

    Priority: an explicit "reader" key in payload_json (set by the PDF/XLSX
    reader-agent path in cli.py, e.g. "deterministic", "deterministic+ocr",
    "llm", "xlsx-supplement", "pillar3-km1") beats an explicit "connector"
    key (set by the fetch-stage source_access_blocked path). When neither is
    present — most extraction/mapping/validation exceptions raised directly
    from pipeline.py do not carry either key — we fall back to
    "<stage>:<content_type>" as a labelled *inferred* reader identity. This
    is documented as an approximation: the exceptions schema has no
    dedicated reader/parser column (see database.py CREATE TABLE
    exceptions), so the pipeline stage plus the document's content type is
    the closest deterministic proxy available today.
    """
    reader = payload.get("reader")
    if reader:
        return str(reader)
    connector = payload.get("connector")
    if connector:
        return f"connector:{connector}"
    return f"inferred:{stage}:{content_type or 'unknown'}"


def domain_from_url(url: str | None) -> str:
    if not url:
        return "unknown"
    try:
        netloc = urlparse(url).netloc or urlparse("//" + url).netloc
    except ValueError:
        return "unknown"
    return netloc.lower().removeprefix("www.") or "unknown"


def classify(code: str, stage: str, message: str | None) -> str:
    """Deterministic classification into exactly one CLASSIFICATIONS bucket.

    Order matters: conflict/not-applicable/unavailable/licensed checks run
    before the generic parser/mapping buckets, so a mapping-shaped code that
    is actually a genuine restatement conflict (e.g. carries "conflict" in
    its code) is never silently folded into generic_mapping_fix.
    """
    text = f"{code} {message or ''}".lower()
    if code in _CONFLICT_CODES or "conflict" in code.lower():
        return "data_conflict_or_restatement"
    if code in _NOT_APPLICABLE_CODES or any(h in text for h in _NOT_APPLICABLE_HINTS):
        return "not_applicable"
    if any(h in text for h in _UNAVAILABLE_HINTS):
        return "source_unavailable"
    if any(h in text for h in _LICENSED_HINTS):
        return "licensed_provider_required"
    if code in _MAPPING_CODES:
        return "generic_mapping_fix"
    if code in _PARSER_CODES:
        return "generic_parser_fix"
    return "company_specific_review"


# ---------------------------------------------------------------------------
# Canonical mapping suggestions (generic_mapping_fix bundles only)
# ---------------------------------------------------------------------------

_ALL_LINE_MAPS: dict[str, tuple[str, str]] = {**LINE_MAP, **BANK_LINE_MAP, **INSURANCE_LINE_MAP}


def suggest_canonical_mappings(raw_label: str | None, known_metric_keys: set[str],
                                limit: int = 3) -> list[dict]:
    """Never invents a mapping with high confidence it can't justify: this
    returns *candidates* (with a similarity score) derived from phrases the
    codebase already maps successfully (reading.py LINE_MAP family) and from
    the enabled metric catalog, never a single asserted answer.
    """
    if not raw_label:
        return []
    needle = raw_label.strip().lower()
    if not needle:
        return []
    candidates: dict[str, float] = {}
    phrase_matches = difflib.get_close_matches(needle, _ALL_LINE_MAPS.keys(), n=limit, cutoff=0.6)
    for phrase in phrase_matches:
        metric = _ALL_LINE_MAPS[phrase][0]
        score = difflib.SequenceMatcher(None, needle, phrase).ratio()
        candidates[metric] = max(candidates.get(metric, 0.0), score)
    if known_metric_keys:
        key_matches = difflib.get_close_matches(needle, known_metric_keys, n=limit, cutoff=0.55)
        for metric in key_matches:
            score = difflib.SequenceMatcher(None, needle, metric.replace("_", " ")).ratio()
            candidates[metric] = max(candidates.get(metric, 0.0), score)
    ranked = sorted(candidates.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{"candidate_metric": metric, "similarity": round(score, 3)} for metric, score in ranked]


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------

# criticality: how central the affected metric is to the catalog contract.
# Sourced from data_catalog_fields.requirement (required/recommended/optional);
# a metric with no catalog entry is treated as the lowest ("optional") tier
# because we cannot claim it is central to the contract.
CRITICALITY_WEIGHTS = {"required": 3, "recommended": 2, "optional": 1}
DEFAULT_CRITICALITY = 1

# source_authority: this project's own documented source-priority tiers
# (docs/SOURCE_MAP.md: P=issuer/exchange/auditor primary, C=computed by this
# engine, S=named secondary press/vendor, O=third-party opinion). A handful
# of domains this project fetches from directly are pinned to their known
# tier; everything else defaults to "S" (secondary) rather than assuming
# primary authority it hasn't earned.
SOURCE_AUTHORITY_WEIGHTS = {"P": 4, "C": 3, "S": 2, "O": 1}
DOMAIN_AUTHORITY_TIER = {
    "sec.gov": "P",
    "tadawul.com.sa": "P",
    "saudiexchange.sa": "P",
    "argaam.com": "S",
    "mubasher.info": "S",
    "reuters.com": "S",
    "bloomberg.com": "S",
}
DEFAULT_AUTHORITY_TIER = "S"


def _criticality(metric: str | None, catalog_requirement: dict[str, str]) -> int:
    requirement = catalog_requirement.get(metric) if metric else None
    return CRITICALITY_WEIGHTS.get(requirement or "", DEFAULT_CRITICALITY)


def _source_authority(domain: str) -> int:
    tier = DOMAIN_AUTHORITY_TIER.get(domain, DEFAULT_AUTHORITY_TIER)
    return SOURCE_AUTHORITY_WEIGHTS[tier]


def priority_score(bundle: dict) -> float:
    """criticality x affected_companies_count x estimated_exceptions_closed x source_authority.

    All four factors are documented, small integers (see CRITICALITY_WEIGHTS
    and SOURCE_AUTHORITY_WEIGHTS above), so the score is reproducible from
    the bundle's own fields — it is recomputed here rather than trusted from
    input, and is exposed on the bundle as `priority_score` for transparency.
    """
    return (
        bundle["criticality"]
        * max(bundle["affected_companies_count"], 1)
        * max(bundle["estimated_exceptions_closed_by_one_fix"], 1)
        * bundle["source_authority"]
    )


# ---------------------------------------------------------------------------
# Bundle construction
# ---------------------------------------------------------------------------

def _company_ref(row: dict) -> str | None:
    """`FinancialQueryService.exceptions()` joins companies but only selects
    market/symbol, not company_id (see query.py `exceptions()`), so that is
    the identity this module has to work with. Synthesize "MARKET:SYMBOL" as
    the affected-company reference; fall back to company_id if a caller
    supplies rows from elsewhere that do carry it.
    """
    market = row.get("market")
    symbol = row.get("symbol")
    if market and symbol:
        return f"{market}:{symbol}"
    return row.get("company_id")


def _group_key(row: dict, source_ctx: dict, classification: str) -> tuple:
    payload = row["payload"]
    reader = resolve_reader(payload, row["stage"], source_ctx.get("content_type"))
    domain = domain_from_url(source_ctx.get("source_url"))
    doc_type = source_ctx.get("filing_type") or "unknown"
    metric = payload.get("metric") or payload.get("label") or "unknown"
    base = (classification, reader, domain, doc_type, row["stage"], row["code"], metric)
    if classification == "data_conflict_or_restatement":
        # Genuine value conflicts are inherently company+period specific:
        # never fold two different companies' (or two different periods')
        # conflicts into one bundle as if they shared one root cause.
        period = payload.get("period_end") or payload.get("period") or ""
        return base + (_company_ref(row) or "", period)
    return base


def build_bundles(exception_rows: list[dict], source_lookup: dict[str, dict],
                   catalog_requirement: dict[str, str], known_metric_keys: set[str]) -> list[dict]:
    """Build compact bundles from open-exception rows.

    `exception_rows` is the output of `FinancialQueryService.exceptions()`
    (list of dicts with id/source_key/market/symbol/stage/code/message/
    payload/severity/status/...). `source_lookup` maps source_key ->
    {source_url, filing_type, content_type, local_path, content_hash}, a
    thin join over source_documents. `catalog_requirement` maps metric_key
    -> requirement ("required"/"recommended"/"optional") from
    data_catalog_fields. `known_metric_keys` is the set of enabled metric
    keys, used only for mapping-candidate suggestions.

    Grouping and ordering are deterministic: exceptions are sorted by
    (group key, exception id) before grouping, and the returned bundle list
    is sorted by group key. Callers that want priority order should re-sort
    with `priority_score` (the CLI does this by default).
    """
    decorated = []
    for row in exception_rows:
        source_ctx = source_lookup.get(row["source_key"], {})
        classification = classify(row["code"], row["stage"], row.get("message"))
        key = _group_key(row, source_ctx, classification)
        decorated.append((key, classification, row, source_ctx))
    decorated.sort(key=lambda item: (item[0], item[2]["id"]))

    groups: "OrderedDict[tuple, list]" = OrderedDict()
    for key, classification, row, source_ctx in decorated:
        groups.setdefault(key, []).append((classification, row, source_ctx))

    bundles = []
    for key, members in groups.items():
        classification = members[0][0]
        rows = [m[1] for m in members]
        sources = [m[2] for m in members]
        bundles.append(_build_one_bundle(classification, rows, sources, catalog_requirement, known_metric_keys))
    return bundles


def _build_one_bundle(classification: str, rows: list[dict], sources: list[dict],
                       catalog_requirement: dict[str, str], known_metric_keys: set[str]) -> dict:
    first_payload = rows[0]["payload"]
    metric = first_payload.get("metric") or first_payload.get("label")
    raw_label = first_payload.get("label")
    reader = resolve_reader(first_payload, rows[0]["stage"], sources[0].get("content_type"))
    domain = domain_from_url(sources[0].get("source_url"))
    doc_type = sources[0].get("filing_type") or "unknown"

    companies = sorted({_company_ref(r) for r in rows if _company_ref(r)})
    documents = sorted({r["source_key"] for r in rows if r.get("source_key")})
    exception_ids = sorted(r["id"] for r in rows)

    samples = []
    any_redacted = False
    for row, source_ctx in list(zip(rows, sources))[:MAX_SAMPLES]:
        payload = row["payload"]
        raw_value, red1 = _safe(
            payload.get("value") if "value" in payload else payload.get("incoming_value")
            or payload.get("current_value") or payload.get("row"),
        )
        context, red2 = _safe(row.get("message"), MAX_CONTEXT_CHARS)
        rlabel, red3 = _safe(payload.get("label"))
        archived_path, red4 = _safe(source_ctx.get("local_path"))
        any_redacted = any_redacted or red1 or red2 or red3 or red4
        samples.append({
            "exception_id": row["id"],
            "company_ref": _company_ref(row),
            "raw_label": rlabel,
            "raw_value": raw_value,
            "unit": payload.get("unit"),
            "table_context": context,
            "source_page": payload.get("source_page") or payload.get("page"),
            "archived_source_path": archived_path,
            "content_hash": source_ctx.get("content_hash"),
        })

    suggested = suggest_canonical_mappings(raw_label, known_metric_keys) if classification == "generic_mapping_fix" else []

    deterministic_fix, fix_reason = _deterministic_fix_assessment(classification, len(companies), len(exception_ids))

    criticality = _criticality(metric, catalog_requirement)
    authority = _source_authority(domain)
    # Similar-within-group members (same reader/domain/doc_type/stage/code/
    # metric, or same company+period for conflicts) are assumed to close
    # together under one fix, except for the buckets where that is false by
    # definition (a conflict or a company-specific case does not "close" via
    # a shared rule the way a parser/mapping bug does).
    if classification in ("generic_parser_fix", "generic_mapping_fix"):
        estimated_closed = len(exception_ids)
    elif classification in ("not_applicable", "source_unavailable", "licensed_provider_required"):
        estimated_closed = len(exception_ids)
    else:
        estimated_closed = 1

    bundle = {
        "classification": classification,
        "group_key": {
            "reader": reader, "source_domain": domain, "document_type": doc_type,
            "stage": rows[0]["stage"], "code": rows[0]["code"], "metric": metric,
            "layout_fingerprint": None,  # see LIMITATIONS below
        },
        "exception_count": len(exception_ids),
        "exception_ids": exception_ids,
        "affected_companies": companies,
        "affected_companies_count": len(companies),
        "affected_documents": documents,
        "affected_documents_count": len(documents),
        "representative_samples": samples,
        "suggested_canonical_mappings": suggested,
        "deterministic_fix_possible": deterministic_fix,
        "deterministic_fix_reasoning": fix_reason,
        "estimated_exceptions_closed_by_one_fix": estimated_closed,
        "criticality": criticality,
        "source_authority": authority,
        "status": "open",
        "resolved": False,
        "redactions_applied": any_redacted,
    }
    bundle["priority_score"] = priority_score(bundle)
    return bundle


def _deterministic_fix_assessment(classification: str, company_count: int, exception_count: int) -> tuple[bool, str]:
    if classification == "generic_mapping_fix":
        return True, "A new LINE_MAP/BANK_LINE_MAP/INSURANCE_LINE_MAP caption entry closes every member of this group."
    if classification == "generic_parser_fix":
        return True, "Same reader/stage/code across the group; a single reading.py/extraction.py fix should close all members."
    if classification == "source_unavailable":
        return False, "The underlying source is unreachable; no code fix closes this until the source is reachable again."
    if classification == "not_applicable":
        return False, "Structurally inapplicable; there is nothing to fix, only to mark not_applicable explicitly (not silently)."
    if classification == "licensed_provider_required":
        return False, "Requires a paid/licensed data source this project does not have (see docs/data source decision)."
    if classification == "data_conflict_or_restatement":
        return False, "Genuine conflicting values across periods/sources; needs a human restatement decision, not a code fix."
    return False, f"{exception_count} exception(s) across {company_count} company(ies) did not match a generalizable pattern."


LIMITATIONS = """
layout_fingerprint: the exceptions table and source_documents table carry no
column that identifies a document's visual/column layout (no stored
coordinate hash, heading-pattern hash, or similar). This grouping field is
therefore always emitted as null rather than invented from unrelated data.
If layout-sensitive grouping is wanted later, the reader agent in reading.py
would need to compute and persist such a fingerprint at extraction time.

reader/parser identity: only the PDF/XLSX reader-agent path in cli.py's
sync-manifests flow sets an explicit "reader" key in payload_json (values
like "deterministic", "deterministic+ocr", "llm", "xlsx-supplement",
"pillar3-km1"), and only the fetch-stage source_access_blocked path sets a
"connector" key. Exceptions raised directly by pipeline.py (extraction/
mapping/validation stages, the large majority) carry neither. For those,
`resolve_reader()` falls back to "inferred:<stage>:<content_type>", which is
a proxy, not a verified reader identity.
"""
