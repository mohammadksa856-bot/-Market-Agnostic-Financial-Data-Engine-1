# MAREFA contract-snapshot exchange kit

Compare a coverage snapshot from an independent pipeline with ours, and integrate it on an isolated
engine copy. The kit holds no company data: the examples are synthetic (`sa:TST`).

| Path | Content |
|---|---|
| `schema/contract-bundle.schema.json` | The snapshot format (JSON Schema 2020-12) |
| `examples/example-snapshot-full.json` | A full snapshot: field definitions and observations |
| `examples/example-snapshot-minimal.json` | The smallest valid snapshot: keys only, `record_default: "missing"` |
| `tools/snapshot_tool.py` | `validate` and `compare`, standard library only, no engine needed |
| `tools/contract_compare.py` | The comparison module (same code as the engine's `finengine.contract_compare`) |
| `tools/export_from_engine.py` | Export a snapshot from any engine checkout without modifying it |
| `tools/escalate.py` | Split comparison results into `needs_review` and `coverage_differences` |
| `integration/integration_run.sh` | The five-step integration on a third engine copy |
| `integration/codex_intake.sh` | The first real integration: fingerprints, validation, exact reproduction of the stated figures, comparison, special-source evidence, a third engine copy at the Codex commit, before/after rebuilds around the correctness pack, measurement from the unified records, escalations |
| `tools/reproduce.py`, `tools/evidence_check.py`, `tools/run_impact.py`, `tools/integration_summary.py` | The helpers it runs |
| `CODEX-TRANSFER-REQUEST.md` | What to send and how |
| `git/correctness-pack.bundle` | The correctness pack, applied by the integration script |

## Producing a snapshot
Required: `bundle_version: 1`, `company_id`, `contract.categories[]` (`key`, `weight`, `fields` or
`score_only`) and `records[]` (`key`, `status` = `closed` | `missing` | `excluded`, `observations`).
Each observation needs `period_kind` (`instant`, `quarter`, `ytd`, `fy`, `ttm`, `as_of`, `daily`),
an ISO `period_end`, and a `value`; `period_start`, `unit`, `currency`, `source_url`, `dimensions`
and `calculation` are compared when present. Fields may be plain keys; with
`record_default: "missing"` only closed keys need records. Missing field definitions are reported as
`definition_not_provided`, never as differences. A key may appear in several categories.

## Checking and comparing
```
python3 tools/snapshot_tool.py validate SNAPSHOT.json        # exit 2 lists every structural error
python3 tools/snapshot_tool.py compare OURS.json SNAPSHOT.json --out RESULT.json
```
`RESULT.json`: common and extra keys; weight, category-placement and definition differences;
value, unit, currency and period-start conflicts on keys both closed; periods held by one side only
(within the common range when an export was truncated); keys not comparable (closed without values);
union coverage per distinct key and per contract slot, each counted once; scores of each side and
of the union on each contract; conflicts on keys an engine correction touched are flagged.

## Integration
```
integration/integration_run.sh ORIGINAL_ENGINE_CLONE SNAPSHOT.json OUR_BUNDLE.json EMPTY_WORKDIR [EXTRA_IMPORTS]
```
1. validates the snapshot; 2. compares it with our bundle; 3. clones the original engine into the
workdir, applies the correctness pack, rebuilds from the imports (plus optional extra manifests) and
exports an integration snapshot; 4. compares that with the external snapshot for the union
coverage; 5. writes `5-escalations.json` with two sections: `needs_review` (value, unit, currency
or period-start conflicts on keys both closed, definition and weight differences) and
`coverage_differences` (periods one side holds and the other does not). Nothing is resolved
automatically and the original engine is only read. `tools/escalate.py` produces the same split for
any comparison results.
