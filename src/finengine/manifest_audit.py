from __future__ import annotations

"""Offline source-fidelity checks for reviewed manifests.

``verification.ManifestVerifier`` proves internal consistency (accounting
identities, ratio bounds, cross-manifest conflicts).  It cannot see the defect
classes an independent audit found in reviewed Saudi manifests, because every one
of them is internally consistent:

* a figure printed as "SAR 11,298 million" stored as raw 11,298,000 with scale 1
  (understated 1000x);
* a fact whose ``page`` points at a page that does not hold the number (printed
  page numbers mixed with PDF page numbers, or a page of another document);
* a quarterly series whose four quarters do not add up to the audited year
  (restated vs original basis, or a transcription slip).

The functions here compare a manifest with the *archived page text* of its
source document and with the other manifests of the same issuer.  They never
change a manifest, never use the network and never guess a value: they only
report where the number is (or is not) printed.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Iterable, Sequence

# Arabic-Indic digits and separators appear in some Saudi issuer PDFs (notes to
# the financial statements of GO Telecom print every number this way).
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٬٫", "0123456789,.")
_TEXT_MIN_CHARS = 40  # a page with less text than this is an image (scanned) page


def normalise_page_text(text: str) -> str:
    text = (text or "").translate(_ARABIC_DIGITS)
    return re.sub(r"[ \t\r\n  ]+", " ", text)


def _scaled(fact: dict) -> Decimal | None:
    try:
        raw = Decimal(str(fact["value"]))
    except (InvalidOperation, KeyError, TypeError):
        return None
    scale = fact.get("scale")
    try:
        return raw * (Decimal(str(scale)) if scale not in (None, "") else Decimal(1))
    except InvalidOperation:
        return None


def _alternative_renderings(fact: dict) -> set[str]:
    """The same quantity printed in thousands (statements of issuers that publish in SAR
    thousands while the manifest stores SAR millions, e.g. 14,834.056 million = 14,834,056)."""
    magnitude = _scaled(fact)
    scale = fact.get("scale")
    try:
        stored_in_millions_or_more = scale not in (None, "") and Decimal(str(scale)) >= Decimal(10) ** 6
    except InvalidOperation:
        stored_in_millions_or_more = False
    # Only for values stored in millions/billions: a small-scale value (scale 1 or 1000) whose
    # thousands rendering matches the page is exactly the 1000x error this module must not hide.
    if not stored_in_millions_or_more or magnitude is None or magnitude == 0:
        return set()
    thousands = abs(magnitude) / Decimal(1000)
    if thousands == thousands.to_integral_value():
        return {f"{thousands:,.0f}"}
    return set()


def _plain(number: Decimal) -> str:
    text = format(number.normalize(), "f")
    return text


def printed_forms(raw: Decimal) -> set[str]:
    """Ways ``raw`` can be printed in a statement table (magnitude only)."""
    value = abs(raw)
    forms = {f"{value:,.0f}"} if value == value.to_integral_value() else set()
    if value != value.to_integral_value():
        for places in (1, 2, 3):
            forms.add(f"{value:,.{places}f}")
        forms.add(f"{value.normalize():,f}")
    forms.add(_plain(value))
    return {form for form in forms if form}


def _number_pattern(number: str) -> re.Pattern:
    return re.compile(r"(?<![\d,.])" + re.escape(number) + r"(?![\d]|,\d)")


def pages_containing(pages: Sequence[str], number: str) -> list[int]:
    pattern = _number_pattern(number)
    return [index + 1 for index, text in enumerate(pages) if pattern.search(text)]


_UNIT_WORDS = {"million": Decimal(10) ** 6, "billion": Decimal(10) ** 9}


def _unit_text_matches(pages: Sequence[str], page_numbers: Iterable[int], magnitude: Decimal) -> list[dict]:
    """Find "N million" / "N billion" statements on the given pages and report the
    ratio between what the text implies and the fact's scaled magnitude."""
    hits = []
    pattern = re.compile(r"(?<![\d,.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(million|billion)\b", re.I)
    for number in page_numbers:
        for match in pattern.finditer(pages[number - 1]):
            try:
                stated = Decimal(match.group(1).replace(",", "")) * _UNIT_WORDS[match.group(2).lower()]
            except InvalidOperation:
                continue
            if stated == 0 or magnitude == 0:
                continue
            hits.append({"page": number, "text": match.group(0), "stated": stated,
                         "ratio_to_fact": stated / abs(magnitude)})
    return hits


@dataclass
class ProvenanceResult:
    metric: str
    period_end: str
    value: str
    scale: str | None
    claimed_page: int | None
    status: str
    found_pages: list[int] = field(default_factory=list)
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "metric": self.metric, "period_end": self.period_end, "value": self.value,
            "scale": self.scale, "claimed_page": self.claimed_page, "status": self.status,
            "found_pages": self.found_pages, "detail": self.detail,
        }


# Statuses, from best to worst:
#   ok                    printed on the claimed page
#   page_offset           printed on claimed page +/- 1 only (printed vs PDF numbering)
#   wrong_page            printed, but only on pages far from the claimed one
#   scale_suspect         the page states the figure in "N million/billion" and N differs
#                         from the stored scaled magnitude by a factor of 1000
#   image_page            claimed page has no text layer (scanned) - needs a visual check
#   page_out_of_range     claimed page does not exist in the document
#   not_found             the claimed page has text but the number is not printed on it
#   not_numeric / no_page non-numeric value / no page recorded
STATUS_ORDER = ("ok", "page_offset", "wrong_page", "scale_suspect", "image_page",
                "page_out_of_range", "not_found", "not_numeric", "no_page")


def audit_fact_provenance(fact: dict, pages: Sequence[str]) -> ProvenanceResult:
    metric = str(fact.get("metric"))
    base = dict(metric=metric, period_end=str(fact.get("period_end")), value=str(fact.get("value")),
                scale=None if fact.get("scale") in (None, "") else str(fact.get("scale")))
    claimed = fact.get("page")
    try:
        raw = Decimal(str(fact["value"]))
    except (InvalidOperation, KeyError):
        return ProvenanceResult(**base, claimed_page=claimed, status="not_numeric")
    if not isinstance(claimed, int):
        return ProvenanceResult(**base, claimed_page=None, status="no_page")
    if claimed < 1 or claimed > len(pages):
        forms = printed_forms(raw) | _alternative_renderings(fact)
        found = sorted({p for form in forms for p in pages_containing(pages, form)})
        return ProvenanceResult(**base, claimed_page=claimed, status="page_out_of_range", found_pages=found,
                                detail=f"document has {len(pages)} pages")
    forms = printed_forms(raw) | _alternative_renderings(fact)
    found = sorted({p for form in forms for p in pages_containing(pages, form)})
    if claimed in found:
        digits = len(_plain(abs(raw)).replace(".", ""))
        return ProvenanceResult(
            **base, claimed_page=claimed, status="ok", found_pages=found,
            detail="" if digits >= 4 else "short number: a match on the page is weak evidence")
    near = [p for p in found if abs(p - claimed) == 1]
    if near:
        return ProvenanceResult(**base, claimed_page=claimed, status="page_offset", found_pages=found,
                                detail=f"printed on page(s) {near}")
    if len(pages[claimed - 1].strip()) < _TEXT_MIN_CHARS:
        return ProvenanceResult(**base, claimed_page=claimed, status="image_page", found_pages=found,
                                detail="claimed page has no text layer")
    magnitude = _scaled(fact)
    if magnitude is not None:
        suspicious = [hit for hit in _unit_text_matches(pages, [claimed], magnitude)
                      if hit["ratio_to_fact"] in (Decimal(1000), Decimal(1) / Decimal(1000))]
        if suspicious:
            hit = suspicious[0]
            return ProvenanceResult(
                **base, claimed_page=claimed, status="scale_suspect", found_pages=found,
                detail=(f"page {claimed} prints '{hit['text']}' (= {hit['stated']:,.0f}) but the fact's scaled "
                        f"value is {magnitude:,.0f}: scale differs by a factor of 1000"))
    if found:
        return ProvenanceResult(**base, claimed_page=claimed, status="wrong_page", found_pages=found,
                                detail=f"printed on page(s) {found[:8]}")
    return ProvenanceResult(**base, claimed_page=claimed, status="not_found", found_pages=found)


def audit_manifest_provenance(manifest: dict, pages: Sequence[str]) -> list[ProvenanceResult]:
    prepared = [normalise_page_text(text) for text in pages]
    return [audit_fact_provenance(fact, prepared) for fact in manifest.get("facts", []) if isinstance(fact, dict)]


def summarise(results: Iterable[ProvenanceResult]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        counts[result.status] += 1
    return {status: counts[status] for status in STATUS_ORDER if counts[status]}


def dominant_page_offset(results: Iterable[ProvenanceResult]) -> int | None:
    """Most common (found - claimed) offset among facts printed on a neighbouring page.

    A consistent non-zero offset means the manifest used another page-numbering
    convention (printed numbers instead of PDF page numbers, or the reverse)."""
    offsets: dict[int, int] = defaultdict(int)
    for result in results:
        if result.status == "page_offset" and result.claimed_page is not None:
            for page in result.found_pages:
                if abs(page - result.claimed_page) == 1:
                    offsets[page - result.claimed_page] += 1
    return max(offsets, key=offsets.get) if offsets else None


def _year_of(fact: dict) -> int | None:
    if fact.get("fiscal_year"):
        return int(fact["fiscal_year"])
    end = str(fact.get("period_end") or "")
    return int(end[:4]) if end[:4].isdigit() else None


def _identity(manifest: dict, fact: dict) -> tuple:
    dims = tuple(sorted((fact.get("dimensions") or {}).items()))
    return (str(manifest.get("company_id") or ""), fact.get("metric"), fact.get("scope", "consolidated"),
            dims, fact.get("currency") or "", _year_of(fact))


def quarters_vs_fiscal_year(manifests: Sequence[dict], tolerance: Decimal = Decimal("0.004")) -> list[dict]:
    """Report fiscal years whose four discrete quarters do not add up to the annual figure.

    Only complete years are compared (four ``quarter`` facts with fiscal_quarter 1..4
    and one ``fy`` fact for the same company/metric/scope/currency).  A gap larger than
    ``tolerance`` (fraction of the annual value) is evidence of mixed bases (original
    vs restated), a transcription error, or cumulative (YTD) figures labelled as
    quarters.  Rounding noise from figures printed in millions stays below the default
    0.4% for any year whose quarters are individually printed at >= 3 significant figures.
    """
    quarters: dict[tuple, dict[int, tuple[Decimal, str]]] = defaultdict(dict)
    years: dict[tuple, tuple[Decimal, str]] = {}
    for manifest in manifests:
        if not isinstance(manifest.get("facts"), list):
            continue
        for fact in manifest["facts"]:
            if not isinstance(fact, dict):
                continue
            magnitude = _scaled(fact)
            if magnitude is None:
                continue
            key = _identity(manifest, fact)
            source = str(manifest.get("source_url") or manifest.get("filing_type") or "")
            if fact.get("period_kind") == "quarter" and fact.get("fiscal_quarter") in (1, 2, 3, 4):
                quarters[key][int(fact["fiscal_quarter"])] = (magnitude, source)
            elif fact.get("period_kind") == "fy":
                years[key] = (magnitude, source)
    findings = []
    for key, by_quarter in sorted(quarters.items(), key=lambda item: str(item[0])):
        if set(by_quarter) != {1, 2, 3, 4} or key not in years:
            continue
        total = sum(value for value, _ in by_quarter.values())
        annual, annual_source = years[key]
        if annual == 0:
            continue
        gap = (total - annual) / abs(annual)
        if abs(gap) > tolerance:
            findings.append({
                "company_id": key[0], "metric": key[1], "fiscal_year": key[5],
                "quarters_sum": str(total), "fiscal_year_value": str(annual),
                "gap_fraction": str(gap.quantize(Decimal("0.00001"))),
                "quarter_sources": sorted({source for _, source in by_quarter.values()}),
                "fiscal_year_source": annual_source,
            })
    return findings
