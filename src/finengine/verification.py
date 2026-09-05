from __future__ import annotations

"""Deterministic cross-checks on reviewed manifests before they are trusted.

Every check here is an accounting identity or a plausibility bound - never a
guess about what a number "should" be. A manifest that fails an identity check
has a transcription or labelling error and is not source-faithful, no matter
which agent or person produced it. This runs before the publication pipeline;
it does not touch production data.
"""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .catalog import iter_catalog_fields
from .database import DEFAULT_METRICS
from .mapping import canonicalize

KNOWN_METRICS = (
    set(DEFAULT_METRICS)
    | {field["field_key"] for field in iter_catalog_fields()}
)

# result_metric == sum(component_metrics), within tolerance. Components may be
# stored with their natural sign (expenses and taxes negative).
ADDITIVE_IDENTITIES = (
    ("income_statement: revenue + other income",
     "revenue_and_other_income_related_to_sales",
     ("revenue", "other_income_related_to_sales")),
    ("income_statement: pre-tax income - tax = net income",
     "net_income",
     ("income_before_income_taxes_and_zakat", "income_taxes_and_zakat")),
    ("income_statement: net income = owners + non-controlling",
     "net_income",
     ("net_income_parent", "net_income_noncontrolling")),
    ("balance_sheet: assets = liabilities + equity",
     "total_assets", ("total_liabilities", "total_equity")),
    ("balance_sheet: assets = current + non-current",
     "total_assets", ("current_assets", "noncurrent_assets")),
    ("balance_sheet: liabilities = current + non-current",
     "total_liabilities", ("current_liabilities", "noncurrent_liabilities")),
    ("balance_sheet: equity = owners + non-controlling",
     "total_equity", ("equity_parent", "noncontrolling_interests")),
    ("balance_sheet: liabilities + equity total",
     "total_liabilities_equity", ("total_liabilities", "total_equity")),
    ("dividends: total = base + performance-linked",
     "dividends_paid", ("base_dividends_paid", "performance_linked_dividends_paid")),
    # Banking. Only fire when the bank lines are present, so a corporate
    # manifest is unaffected. Expense components carry their natural sign.
    ("banking: net special commission income = income - expense",
     "net_interest_income", ("interest_income", "interest_expense")),
    ("banking: net fee and commission income = income - expense",
     "net_fee_and_commission_income", ("fee_and_commission_income", "fee_and_commission_expense")),
)

# Cash reconciliation is presentation-dependent: some issuers fold the FX effect
# into "net change in cash", others add it separately after it. Both are valid,
# so the check tries each convention and passes if either holds.
CASH_FLOWS = ("operating_cash_flow", "investing_cash_flow", "financing_cash_flow")

# result_metric (flow, period_end X) == other_metric (instant, same period_end X)
CROSS_KIND_IDENTITIES = (
    ("cash_flow: period-end cash ties to the balance sheet", "cash_end", "cash"),
)

RATIO_BOUNDS = (
    ("net margin (net_income / revenue)", "net_income", "revenue",
     Decimal("-0.5"), Decimal("0.85")),
    ("effective tax (-tax / pre-tax income)",
     "income_taxes_and_zakat", "income_before_income_taxes_and_zakat",
     Decimal("-0.65"), Decimal("0")),
)


def _tolerance(value: Decimal) -> Decimal:
    return max(abs(value) * Decimal("0.005"), Decimal("1"))


def _resolve(label: str) -> str | None:
    metric = canonicalize(label, "SA")
    if metric:
        return metric
    key = "_".join(label.strip().lower().split())
    return key if key in KNOWN_METRICS else (label if label in KNOWN_METRICS else None)


def _value(fact: dict) -> Decimal | None:
    try:
        raw = Decimal(str(fact["value"]))
        scale = fact.get("scale")
        return raw * Decimal(str(scale)) if scale not in (None, "") else raw
    except (InvalidOperation, KeyError, TypeError):
        return None


def _company_key(path: Path, payload: dict) -> str:
    """Stable issuer identity for cross-manifest comparisons.

    New manifests carry company_id/market/symbol explicitly.  Historical
    reviewed manifests predate that header, so their issuer prefix remains a
    deterministic compatibility key (aramco-..., aapl-..., etc.).
    """
    if payload.get("company_id"):
        return str(payload["company_id"])
    if payload.get("market") and payload.get("symbol"):
        return f"{str(payload['market']).lower()}:{payload['symbol']}"
    return path.name.split("-", 1)[0].lower()


class ManifestVerifier:
    """Group a company's manifest facts by period and check accounting identities."""

    def __init__(self, imports_dir: str | Path = "data/imports"):
        self.imports_dir = Path(imports_dir)

    def _load(self, prefix: str | None) -> list[tuple[Path, dict]]:
        manifests = []
        for path in sorted(self.imports_dir.glob("*.json")):
            if prefix and not path.name.startswith(prefix):
                continue
            manifests.append((path, json.loads(path.read_text(encoding="utf-8"))))
        return manifests

    def verify(self, prefix: str | None = None) -> dict:
        manifests = self._load(prefix)
        if not manifests:
            raise FileNotFoundError(f"no manifests match '{prefix or '*'}' in {self.imports_dir}")

        # (company, period_end, period_kind) -> metric -> values. Company is
        # part of the identity: two issuers reporting the same metric and year
        # are not conflicting versions of one fact.
        periods: dict[tuple[str, str, str], dict[str, list]] = {}
        unmapped: list[dict] = []
        skipped: list[str] = []
        for path, payload in manifests:
            company = _company_key(path, payload)
            facts = payload.get("facts", [])
            if not isinstance(facts, list):
                # US SEC Company Facts shape - checked post-publish against data_points,
                # not by this flat-manifest verifier.
                skipped.append(path.name)
                continue
            for fact in facts:
                if not isinstance(fact, dict):
                    unmapped.append({"file": path.name, "label": repr(fact)})
                    continue
                label = fact.get("metric") or fact.get("label") or ""
                metric = _resolve(label)
                value = _value(fact)
                if metric is None:
                    unmapped.append({"file": path.name, "label": label})
                    continue
                if value is None:
                    continue
                key = (company, fact.get("period_end", ""), fact.get("period_kind", ""))
                periods.setdefault(key, {}).setdefault(metric, []).append(
                    {"value": value, "file": path.name, "label": label,
                     "scope": fact.get("scope", "consolidated"),
                     "dimensions": fact.get("dimensions") or {}})

        checks: list[dict] = []
        checks.extend(self._conflicts(periods))
        checks.extend(self._identities(periods))
        checks.extend(self._cross_kind(periods))
        checks.extend(self._cash_reconciliation(periods))
        checks.extend(self._bounds(periods))

        failures = [c for c in checks if c["status"] == "fail"]
        warnings = [c for c in checks if c["status"] == "warn"]
        return {
            "manifests": len(manifests),
            "flat_manifests_checked": len(manifests) - len(skipped),
            "skipped_non_flat": skipped,
            "periods_checked": len(periods),
            "checks": len(checks),
            "passed": sum(1 for c in checks if c["status"] == "pass"),
            "warnings": len(warnings),
            "failures": len(failures),
            "unmapped_labels": unmapped,
            "ok": not failures,
            "detail": failures + warnings + [c for c in checks if c["status"] == "pass"],
        }

    @staticmethod
    def _one(entries: list) -> Decimal | None:
        return entries[0]["value"] if entries else None

    def _conflicts(self, periods) -> list[dict]:
        out = []
        for (company, period_end, period_kind), metrics in sorted(periods.items()):
            for metric, entries in sorted(metrics.items()):
                identities = {}
                for entry in entries:
                    identity = (
                        entry["scope"],
                        json.dumps(entry["dimensions"], sort_keys=True, separators=(",", ":")),
                    )
                    identities.setdefault(identity, []).append(entry)
                for (scope, dimensions_json), comparable in identities.items():
                    distinct = {entry["value"] for entry in comparable}
                    if len(distinct) < 2:
                        continue
                    values = sorted(distinct)
                    spread = values[-1] - values[0]
                    status = "fail" if spread > _tolerance(values[-1]) else "warn"
                    out.append({
                        "status": status, "check": "cross-manifest value conflict",
                        "company": company,
                        "metric": metric, "period": f"{period_end} {period_kind}",
                        "scope": scope, "dimensions": json.loads(dimensions_json),
                        "values": [str(v) for v in values],
                        "sources": sorted({entry["file"] for entry in comparable}),
                        "note": "restatement or transcription error - reconcile against the filing",
                    })
        return out

    def _identities(self, periods) -> list[dict]:
        out = []
        for (company, period_end, period_kind), metrics in sorted(periods.items()):
            for name, result_metric, components in ADDITIVE_IDENTITIES:
                if result_metric not in metrics:
                    continue
                present = [c for c in components if c in metrics]
                if len(present) < 2:
                    continue
                result = self._one(metrics[result_metric])
                total = sum((self._one(metrics[c]) for c in present), Decimal(0))
                delta = abs(result - total)
                out.append({
                    "status": "pass" if delta <= _tolerance(result) else "fail",
                    "company": company,
                    "check": name, "period": f"{period_end} {period_kind}",
                    "reported": str(result), "computed": str(total),
                    "delta": str(delta), "components": present,
                })
        return out

    def _cash_reconciliation(self, periods) -> list[dict]:
        """cash_end == cash_beginning + operating + investing + financing + fx,
        whichever side of 'net change' the issuer places the FX effect on."""
        out = []
        for (company, period_end, period_kind), metrics in sorted(periods.items()):
            if not all(m in metrics for m in ("cash_beginning", "cash_end")):
                continue
            flows = [m for m in CASH_FLOWS if m in metrics]
            if len(flows) < 2:
                continue
            beginning = self._one(metrics["cash_beginning"])
            end = self._one(metrics["cash_end"])
            fx = self._one(metrics["foreign_exchange_effect"]) if "foreign_exchange_effect" in metrics else Decimal(0)
            movement = sum((self._one(metrics[m]) for m in flows), Decimal(0)) + fx
            delta = abs(end - (beginning + movement))
            check = {
                "status": "pass" if delta <= _tolerance(end) else "fail",
                "company": company,
                "check": "cash_flow: end = beginning + operating + investing + financing + fx",
                "period": f"{period_end} {period_kind}",
                "reported": str(end), "computed": str(beginning + movement), "delta": str(delta),
                "components": flows + (["foreign_exchange_effect"] if fx else []),
            }
            out.append(check)
            if "cash_change" in metrics:
                reported_change = self._one(metrics["cash_change"])
                pre_fx = sum((self._one(metrics[m]) for m in flows), Decimal(0))
                matches = min(abs(reported_change - pre_fx), abs(reported_change - pre_fx - fx))
                out.append({
                    "status": "pass" if matches <= _tolerance(reported_change or Decimal(1)) else "warn",
                    "company": company,
                    "check": "cash_flow: reported net change matches the flow subtotals",
                    "period": f"{period_end} {period_kind}",
                    "reported": str(reported_change), "computed": str(pre_fx), "delta": str(matches),
                })
        return out

    def _cross_kind(self, periods) -> list[dict]:
        by_end: dict[tuple[str, str], dict[str, Decimal]] = {}
        for (company, period_end, period_kind), metrics in periods.items():
            for metric, entries in metrics.items():
                by_end.setdefault((company, period_end), {}).setdefault(metric, entries[0]["value"])
        out = []
        for name, flow_metric, instant_metric in CROSS_KIND_IDENTITIES:
            for (company, period_end), metrics in sorted(by_end.items()):
                if flow_metric in metrics and instant_metric in metrics:
                    a, b = metrics[flow_metric], metrics[instant_metric]
                    delta = abs(a - b)
                    out.append({
                        # The cash-flow definition can legitimately include cash
                        # inside disposal groups and exclude bank overdrafts,
                        # while the face of the balance sheet reports only the
                        # cash-and-equivalents line.  Preserve the tie-out as a
                        # review warning, but do not reject a source-faithful
                        # filing whose primary statements otherwise reconcile.
                        "status": "pass" if delta <= _tolerance(a) else "warn",
                        "company": company,
                        "check": name, "period": period_end,
                        "reported": str(b), "computed": str(a), "delta": str(delta),
                        "note": (None if delta <= _tolerance(a) else
                                 "cash-flow cash may include disposal-group cash and bank overdrafts"),
                    })
        return out

    def _bounds(self, periods) -> list[dict]:
        out = []
        for (company, period_end, period_kind), metrics in sorted(periods.items()):
            for name, numerator, denominator, low, high in RATIO_BOUNDS:
                if numerator not in metrics or denominator not in metrics:
                    continue
                denom = self._one(metrics[denominator])
                if not denom:
                    continue
                ratio = self._one(metrics[numerator]) / denom
                out.append({
                    "status": "pass" if low <= ratio <= high else "warn",
                    "company": company,
                    "check": name, "period": f"{period_end} {period_kind}",
                    "ratio": str(ratio.quantize(Decimal("0.0001"))),
                    "expected_range": f"[{low}, {high}]",
                })
        return out
