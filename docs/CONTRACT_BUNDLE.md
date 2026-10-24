# Contract bundles: comparing independent pipelines

A bundle (`docs/contract-bundle.schema.json`) is the factory contract a pipeline scored a company
against, plus its evidence for every contract key: `closed`, `missing` or `excluded` (a reviewed
unavailable / not-applicable assessment), with the observations behind each closed key.

| Command | Purpose |
|---|---|
| `contract-export MARKET SYMBOL --out F --label L [--corrections IMPACT.json]` | Bundle this engine's evidence. Refuses to finish unless the bundle reproduces the evaluator's total score. |
| `contract-validate F` | Structural check of any snapshot, including one produced elsewhere. Exit code 2 and the full error list when invalid. |
| `contract-compare A B` | Common and extra keys; weight, category-placement and definition differences; value, unit, period and source conflicts on keys both closed; union coverage counted once per contract slot. |
| `engine-impact BEFORE.sqlite3 AFTER.sqlite3 --label L` | What an engine change did to the same imports: rows removed, added or changed per metric, and every company's contract score before and after. Inputs are read from temporary copies. |

**Minimal snapshots.** A producer that has no field definitions may list fields as plain keys, and
may declare `"record_default": "missing"` so that only closed keys need a record. Missing definitions
are reported as `definition_not_provided`, never as a definition difference.

**Engine corrections.** An impact report's `engine_corrections` can be attached to a bundle. A conflict
on a key one pipeline's engine corrected is flagged with that correction, so a fixed calculation is
not mistaken for a data dispute; the conflict itself is still reported.

**Counting.** A contract key can sit in more than one category (e.g. `segments` and
`sector_specific_fields`); closure is reported per distinct key and per slot, and a key closed by both
pipelines counts once.
