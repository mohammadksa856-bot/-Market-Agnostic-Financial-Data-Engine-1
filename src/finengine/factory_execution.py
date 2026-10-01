from __future__ import annotations

import json
from pathlib import Path


DEFAULT_EXECUTION_PLAN = Path("config/factory/execution-plan.json")

TERMINAL_SUCCESS_STATES = frozenset({"published", "validated", "skipped"})
TERMINAL_FAILURE_STATES = frozenset({"blocked", "cancelled"})


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_execution_plan(
    contract_path: str | Path,
    execution_plan_path: str | Path = DEFAULT_EXECUTION_PLAN,
) -> tuple[dict, dict[str, dict]]:
    """Load and validate the dependency plan against the canonical contract.

    The execution plan is deliberately separate from completeness scoring: it
    may order work, but it cannot alter weights, thresholds or hard gates.
    """
    contract = _load_json(contract_path)
    plan = _load_json(execution_plan_path)
    contract_keys = {item["category_key"] for item in contract["categories"]}
    metadata: dict[str, dict] = {}
    wave_keys: set[str] = set()
    ordinals: set[int] = set()

    for wave in plan.get("waves", []):
        wave_key = str(wave.get("wave_key", "")).strip()
        ordinal = int(wave.get("ordinal", 0))
        if not wave_key or wave_key in wave_keys:
            raise ValueError(f"duplicate or empty execution wave: {wave_key!r}")
        if ordinal < 1 or ordinal in ordinals:
            raise ValueError(f"duplicate or invalid execution wave ordinal: {ordinal}")
        wave_keys.add(wave_key)
        ordinals.add(ordinal)
        for position, item in enumerate(wave.get("categories", []), start=1):
            key = str(item.get("category_key", "")).strip()
            if key in metadata:
                raise ValueError(f"execution category appears more than once: {key}")
            dependencies = list(item.get("depends_on", []))
            metadata[key] = {
                "wave_key": wave_key,
                "wave_ordinal": ordinal,
                "wave_position": position,
                "execution_mode": wave.get("execution_mode"),
                "depends_on": dependencies,
            }

    planned_keys = set(metadata)
    if planned_keys != contract_keys:
        missing = sorted(contract_keys - planned_keys)
        extra = sorted(planned_keys - contract_keys)
        raise ValueError(f"execution plan does not match contract; missing={missing}, extra={extra}")

    for key, item in metadata.items():
        unknown = set(item["depends_on"]) - contract_keys
        if unknown:
            raise ValueError(f"{key} has unknown dependencies: {sorted(unknown)}")
        if key in item["depends_on"]:
            raise ValueError(f"{key} cannot depend on itself")
        for dependency in item["depends_on"]:
            if metadata[dependency]["wave_ordinal"] >= item["wave_ordinal"]:
                raise ValueError(
                    f"{key} dependency {dependency} must be in an earlier wave"
                )
    contract_by_key = {item["category_key"]: item for item in contract["categories"]}
    for key, item in metadata.items():
        category = contract_by_key[key]
        item["official_sources"] = list(category["official_sources"])
        item["field_groups"] = list(category["field_groups"])
        item["job_strategy"] = category["job_strategy"]
    return plan, metadata


def dependency_status(states: dict[str, str], dependencies: list[str]) -> tuple[str, list[str]]:
    """Classify an item's upstream state without confusing readiness and execution.

    `validated` is terminal for orchestration even when the category did not
    reach its readiness threshold. This lets later waves compute whatever is
    possible while the final contract continues to report the honest gap.
    """
    failed = [key for key in dependencies if states.get(key) in TERMINAL_FAILURE_STATES]
    if failed:
        return "blocked", failed
    waiting = [key for key in dependencies if states.get(key) not in TERMINAL_SUCCESS_STATES]
    if waiting:
        return "waiting", waiting
    return "ready", []
