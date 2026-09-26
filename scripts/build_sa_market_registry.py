"""Build the deterministic Saudi relay registry from tracked project inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_SEED = PROJECT / "scripts" / "seed-data" / "sa-manual-seed-2026-09-13.json"
DEFAULT_OVERRIDES = PROJECT / "config" / "companies.json"
DEFAULT_OUTPUT = PROJECT / "config" / "sa-market-registry.json"
REQUIRED_FIELDS = (
    "company_id", "market", "symbol", "name", "currency", "exchange",
    "country", "timezone", "active", "sources",
)


class RegistryError(ValueError):
    """The tracked registry inputs are ambiguous or incomplete."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RegistryError(f"cannot read registry input {path}: {error}") from error


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise RegistryError(f"invalid active value: {value!r}")


def _by_symbol(records: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise RegistryError(f"{label}[{position}] must be an object")
        symbol = str(record.get("symbol") or "").strip()
        if not symbol.isdigit():
            raise RegistryError(f"{label}[{position}] has invalid Saudi symbol {symbol!r}")
        if symbol in indexed:
            raise RegistryError(f"duplicate Saudi symbol {symbol} in {label}")
        indexed[symbol] = record
    return indexed


def validate_registry(records: list[dict[str, Any]]) -> None:
    indexed = _by_symbol(records, "registry")
    for symbol, record in indexed.items():
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            raise RegistryError(f"registry symbol {symbol} missing: {', '.join(missing)}")
        if record["company_id"] != f"sa:{symbol}" or record["market"] != "SA":
            raise RegistryError(f"registry symbol {symbol} has inconsistent identity")
        if not str(record["name"]).strip():
            raise RegistryError(f"registry symbol {symbol} has an empty name")
        if not isinstance(record["active"], bool):
            raise RegistryError(f"registry symbol {symbol} active must be boolean")
        if not isinstance(record["sources"], list):
            raise RegistryError(f"registry symbol {symbol} sources must be a list")


def build_registry(seed_path: Path = DEFAULT_SEED,
                   overrides_path: Path = DEFAULT_OVERRIDES) -> list[dict[str, Any]]:
    seed_document = _read_json(seed_path)
    seed_records = seed_document.get("data") if isinstance(seed_document, dict) else None
    if not isinstance(seed_records, list):
        raise RegistryError(f"{seed_path} must contain a data[] array")
    seed = _by_symbol(seed_records, "seed.data")

    override_records = _read_json(overrides_path)
    if not isinstance(override_records, list):
        raise RegistryError(f"{overrides_path} must contain an array")
    overrides = _by_symbol(
        [record for record in override_records if record.get("market") == "SA"],
        "companies",
    )

    unknown_overrides = sorted(set(overrides) - set(seed), key=int)
    if unknown_overrides:
        raise RegistryError(
            "Saudi company overrides absent from seed: " + ", ".join(unknown_overrides)
        )

    registry: list[dict[str, Any]] = []
    for symbol in sorted(seed, key=lambda value: (int(value), value)):
        raw = seed[symbol]
        rich = overrides.get(symbol, {})
        record = {
            "company_id": f"sa:{symbol}",
            "market": "SA",
            "symbol": symbol,
            "name": str(rich.get("name") or raw.get("name") or "").strip(),
            "currency": str(rich.get("currency") or raw.get("currency") or "SAR"),
            "exchange": str(rich.get("exchange") or raw.get("exchange") or "Saudi Exchange"),
            "country": str(rich.get("country") or "SA"),
            "timezone": str(rich.get("timezone") or "Asia/Riyadh"),
            "active": _boolean(raw.get("active", True)),
            "sources": list(rich.get("sources") or []),
        }
        for field in ("isin", "sector", "industry", "cik", "fiscal_year_end"):
            if rich.get(field) not in (None, ""):
                record[field] = rich[field]
        registry.append(record)
    validate_registry(registry)
    return registry


def render_registry(records: list[dict[str, Any]]) -> str:
    return json.dumps(records, ensure_ascii=False, indent=2) + "\n"


def ensure_registry(output_path: Path = DEFAULT_OUTPUT,
                    seed_path: Path = DEFAULT_SEED,
                    overrides_path: Path = DEFAULT_OVERRIDES,
                    *, check: bool = False) -> bool:
    rendered = render_registry(build_registry(seed_path, overrides_path))
    current = output_path.read_text(encoding="utf-8") if output_path.exists() else None
    if current == rendered:
        return False
    if check:
        raise RegistryError(f"generated registry is stale: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output_path)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = ensure_registry(args.output, args.seed, args.overrides, check=args.check)
    print(json.dumps({"registry": str(args.output), "changed": changed,
                      "companies": len(build_registry(args.seed, args.overrides))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
