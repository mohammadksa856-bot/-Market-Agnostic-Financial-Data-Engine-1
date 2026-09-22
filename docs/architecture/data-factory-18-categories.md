# The 18-category data factory contract

This document explains `config/factory/18-category-contract.json` and the
sector packs in `config/factory/sector-packs/`. It is a specification/contract
deliverable only: nothing here populates company data, changes scoring code,
or touches `src/finengine/database.py`, `jobs.py`, `cli.py`, `operations.py`,
`factory.py` (it does not exist on this branch), or
`tests/test_data_factory_acceptance.py`. Those files remain the engine's own;
this contract is designed to sit on top of them.

## Why a second 18-category document exists

This branch already has `docs/DATA_MODEL_18_CATEGORIES.md`, an earlier
18-category model (Identity, Business model, Management/governance,
Ownership, Historical financial statements, Earnings quality, Financial
ratios, Operational KPIs, Dividends & corporate actions, Industry & sector,
Competitors, Liquidity/trading, Forecasts, Analyst coverage, Valuation,
Risks, ESG, News/disclosures/investor materials) built by checking a
6-category sketch against CFA Institute, sell-side reports and vendor models.

**This is a different 18-category list**, specified directly by the project
owner for this deliverable: company profile, financial statements,
profitability, liquidity/solvency, efficiency, growth, per-share, valuation,
market data, dividends, segments, ownership, corporate actions,
announcements, operational KPIs, sector-specific fields, calculated/smart
metrics, sources/lineage/freshness.

The two lists overlap heavily but are not the same partition — the older
document groups by *investor-narrative topic* (e.g. "Risks" and "ESG" as
their own categories, no separate "sources/lineage/freshness" category); this
contract groups by *how the factory ingests and scores a field* (splitting
generic financial ratios into profitability/liquidity/efficiency/growth/
per-share/valuation the way `src/finengine/catalog.py`'s `GROUPS` already
does, and adding sources/lineage/freshness as its own gated category because
provenance is scored, not assumed). **This document does not attempt to
reconcile the two into one master list** — that would silently resolve an
ambiguity the project owner should decide, per the instruction not to
silently resolve ambiguous conflicts. Both documents can stand: the older one
is a narrative/coverage audit tool, this one is the factory's own ingestion
contract.

## How this contract was grounded

Before writing anything, this branch's actual state was read:

- `src/finengine/catalog.py` — the `GROUPS` tuple is the real, already-shipped
  field-group catalog (company_model, income_statement, balance_sheet,
  profitability, banking, telecommunications, ... 36 groups, 1,069 fields).
  This contract's `field_groups` per category are literal `GROUPS[i][0]`
  names, not invented — see the `field_groups` field on every category.
- `docs/MASTER_SCHEMA.md` — already defines the pack model
  (`company_core_v5`, `banking_v1`, `telecommunications_v1`, ...) and the
  existing missing-reason vocabulary: *pending extraction, not disclosed, not
  applicable, event not observed, missing formula inputs/history,
  qualitative-only, licensed source required*. This contract reuses that
  vocabulary verbatim in `unavailable_conditions`/`not_applicable_conditions`
  rather than inventing a second, conflicting one.
- `docs/SOURCE_MAP.md` — already defines a four-tier source model (Primary /
  Computed / Opinion / Secondary) and the rule "if it can be computed,
  compute the canonical value" (e.g. beta, computed internally rather than
  imported from five disagreeing vendors). This contract's
  `official_sources` / `source_cost` fields follow that same rule: any
  derived category's `official_sources` is `internal_computation`, never a
  vendor.
- `docs/data/telecom-sector.md` — already uses the exact phrases this
  contract formalizes: *"the 18-category 95% target"*, *"the weighted score
  and all hard gates pass"*, and the five-annual/12-quarter/provenance/
  no-synthetic-source readiness gates. This contract's
  `overall_completeness_threshold` (0.95) and `anti_averaging_principle` are
  literally naming and structuring language this branch already committed to
  but had not yet formally specified.

## Category shape

Every category in `config/factory/18-category-contract.json` carries the
same 14 keys (see the JSON for the authoritative values):
`category_key`, `weight`, `field_groups`, `applicability`,
`official_sources`, `extraction_mode`, `job_strategy`,
`unavailable_conditions`, `not_applicable_conditions`,
`completeness_threshold`, `threshold_rationale`, `hard_gates`, `source_cost`
(+ `source_cost_notes`), `provenance_requirements`, `freshness_policy`.

### `field_groups`, not individual field keys

`required_fields`/`recommended_fields`/`optional_fields` were requested to
"align with catalog.py's existing field-group naming where a field already
exists there." `catalog.py`'s own `GROUPS` tuples are *already* the atomic
completeness unit the engine uses (a `(name, storage_domain, statement,
period_behavior, unit, aggregation, scope_type, scope_value, keys)` tuple
per group) — the 1,069 individual field keys inside those groups do not
carry independent required/recommended/optional status in the catalog
today; `CORE_REQUIRED_FIELDS` is the only individual-field-level
requirement tier that exists, and it is a 27-field cross-category set,
not one per category. Rather than inventing a second, parallel
individual-field requirement tier that could silently drift from
`CORE_REQUIRED_FIELDS`, this contract references `field_groups` (the
literal `GROUPS[i][0]` names) as its required unit, and each sector pack's
`additional_required_fields` lists specific field keys only where the
task explicitly asked for sector examples (e.g. banking's `gross_loans`,
`cet1_capital`; telecom's `subscriber_count`, `arpu`, `churn_rate`).
This is a deliberate design choice, stated here rather than silently
applied.

### `applicability`

Every category's `applicability` is a `{rule, condition, flag_source,
description}` object — never prose alone. `flag_source` names the actual
flag a sector/company pack sets (e.g. `sector_pack.activated_field_groups`,
`company_pack.reports_multiple_segments`), so "is this category applicable"
is answerable by reading one field, not by re-deriving it from company
data. Two categories demonstrate the two patterns the task called out by
name:

- **Segments** (`company_pack.reports_multiple_segments`) — not applicable
  for a genuinely single-business-line company, evidenced by the
  operating-segments note stating there is one reportable segment. This is
  why `segments` has the lowest completeness floor (75%) in the contract:
  the floor is deliberately low so the `not_applicable` path resolves the
  gap for single-segment companies instead of an unreachable threshold
  quietly doing it.
- **Sector-specific fields / operational KPIs** (`sector_pack.
  activated_field_groups`) — a bank activates `banking`
  (sector_specific_fields) and *not* any `operational_kpis` group under the
  current contract (see the banking pack's notes on why — catalog.py has no
  banking operational-KPI group yet); a telecom operator activates
  `telecommunications` (operational_kpis) and *not* `sector_specific_fields`
  (telecom has no distinct statement-shaped sector template in catalog.py).

### Splitting "operational KPIs" (15) from "sector-specific fields" (16)

`catalog.py` does not separate these two concepts within a single
industry-scoped `GROUPS` entry — e.g. its `"telecommunications"` group mixes
nothing but physical KPIs (subscriber counts, ARPU, churn, network
coverage), while its `"banking"` group is entirely financial-statement-shaped
(gross loans, deposits, NIM, CET1). This contract draws the line the way
`catalog.py`'s own groups already fall out:

| Category 15 `operational_kpis` | Category 16 `sector_specific_fields` |
| --- | --- |
| Physical/operating-unit metrics: subscriber counts, occupancy, production volumes, store counts, bed counts, AUM | Sector-specific **financial-statement-shaped** lines and ratios: gross loans, NIM, CET1, loss ratio, combined ratio, FFO/NAV |
| `oil_gas_operations`, `chemical_operations`, `telecommunications`, `utilities`, `mining`, `retail`, `healthcare`, `transportation_logistics`, `industrial_construction`, `technology`, `food_agriculture`, `asset_management` | `banking`, `insurance`, `real_estate`, `segments` (industry-scoped rows) |
| Voluntary disclosure (investor presentations, results calls) → 85% floor, `requires_review` | Regulator-template statutory disclosure → 90% floor, `deterministic` |

This split is a contract design decision, made explicit here rather than
left implicit in the JSON.

### Thresholds — why they are not uniformly 95%

The task's own worked example ("Financial Statements >=95%, Banking-Specific
>=90%, Sources/Lineage=100%, everything else >=85% default, overall >=95%")
is the model this contract follows, with the deltas justified per category
in the JSON's `threshold_rationale` field (not asserted bare). Summary:

| Category | Threshold | Why not the 85% default |
| --- | ---: | --- |
| financial_statements | 95% | The project's own existing "18-category 95% target" language (telecom-sector.md) |
| liquidity_solvency, per_share, calculated_smart_metrics | 90% | Pure derivations of already-95%-required inputs — should track close to full |
| sector_specific_fields | 90% | Task's own "Banking-Specific >=90%" example; regulator templates are newer and still phasing in for some issuers |
| dividends, corporate_actions | 90% | Mandatory exchange disclosures, but archive retrieval gaps exist (documented stc CDN 403s) |
| company_profile, ownership, operational_kpis, profitability, efficiency | 85% | Default — voluntary/narrative disclosure, or a documented licensed-data exception (ownership's named-holder detail) |
| valuation | 80% | Consensus/DCF inputs need licensed or judgment data this project does not purchase (`project_data_source_decision` memory) |
| growth | 80% | 5y/10y CAGR fields are structurally unavailable for recently-listed companies — permanent, not a collection gap |
| announcements | 80% | Measured as polling-stream coverage, not a fixed field count; 95% would conflate a quiet company with a broken connector |
| segments | 75% | Applicability itself is company-specific and evidence-gated (see above) |
| sources_lineage_freshness | 100% | Task's own example; an unsourced "fact" should not have been published at all — there is no principled partial-credit floor |

### Hard gates and the anti-averaging principle

Every category defines at least one `hard_gates` entry: a pass/fail
condition independent of the weighted average. The contract's top-level
`anti_averaging_principle` field states the rule directly — overall
readiness requires the weighted average **and** every category's own
threshold **and** every category's hard gates, mirroring
`docs/data/telecom-sector.md`'s existing sentence: *"the engine must not
label the sector ready before the weighted score and all hard gates pass."*
Category 16 (`sector_specific_fields`) carries the literal example the task
named: a near-zero sector-specific score cannot be masked by strong
financial_statements/profitability scores.

### `unavailable` vs `not_applicable`

Both require an evidence object (`unavailable(...)`/`not_applicable(...)` in
the JSON) — never a bare boolean flag. `unavailable` requires that an
official source was actually checked (`checked_source_type`, `checked_at`,
`reason`, `reviewer`); `not_applicable` requires the structural rule/flag
that produced the determination (`structural_reason`,
`determined_by`, `evidence_field_or_flag`). The reason vocabularies are
lifted directly from `docs/MASTER_SCHEMA.md`'s existing backlog-reason list
so this contract does not create a second taxonomy that could silently
diverge from the one already in use.

### Extraction mode and escalation

`extraction_mode` is `deterministic` or `requires_review` per field_group.
A field_group is `requires_review` (not `deterministic`) wherever this
project has already hit an ambiguity in practice — for example, telecom
operational KPIs are `requires_review` because
`docs/data/telecom-sector.md` documents Mobily's ambiguous "99% coverage"
figures being deliberately excluded rather than extracted. The escalation
rule stated on every `requires_review` field_group and repeated here because
it governs the "no LLM as a source" hard rule operationally: **an
LLM-assisted reader (`reading_llm.py`) may propose an extraction, but the
proposal is always `requires_review` and is never itself listed as an
`official_source_type`.** The contract's `controlled_vocabularies.
forbidden_source_types` (`llm_general_knowledge`, `llm_output`,
`ai_generated`) exists so a validator can assert this never regresses.

### `job_strategy`

A controlled vocabulary of 11 values (see the JSON's
`controlled_vocabularies.job_strategy`), from `one_time_profile_capture`
through `calculated_no_network` (used by every derived-ratio category —
profitability through calculated_smart_metrics — since those categories
issue no ingestion job at all, only a recomputation) to
`provenance_audit_continuous` (sources_lineage_freshness's own background
audit job, not a data-fetch job).

### `provenance_requirements` and `freshness_policy`

`provenance_requirements.mandatory_fields` is a subset of the five fields
the task named (`source_url`, `document_hash`, `page_or_table_reference`,
`filed_at_or_period_date`, `retrieval_timestamp`), matching field names
already in `src/finengine/database.py`/`models.py`
(`source_url`, `content_hash`, `filed_at`). Calculated categories add a
`calculated_field_supplement`: a `formula_id` plus the input field_key/period
pairs consumed, because a derived number's "document" is the formula and its
inputs, not a fetched artifact — stated explicitly rather than force-fitting
a `document_hash` onto a number with no document.

`freshness_policy` states a `cadence_kind` (`periodic` / `event_driven` /
`continuous` / `derived`), a `recheck_interval_days`, a
`max_age_before_stale_days`, and a `refresh_trigger` in plain language.

## Sector packs

`config/factory/sector-packs/telecom.json` and `.../banking.json` are thin
overlays: `canonical_industry_values` (which must equal an existing
canonical `industry` string already governed by `catalog.py`/
`MASTER_SCHEMA.md`, e.g. `"Banks"`, `"Telecommunications"` — no new
classification taxonomy), `activates` (which `operational_kpis`/
`sector_specific_fields` field_groups this sector turns on),
`category_overrides.not_applicable_categories` (categories this sector
marks not_applicable outright), `additional_required_fields` (sector
example fields named in the task), and `additional_official_sources`.
**A sector pack must never redefine a master category's weight, threshold,
extraction_mode or hard_gates** — that would let a sector quietly lower its
own bar, defeating the point of a shared contract. Adding a third sector
pack later means adding a third file in this same shape; the master
contract file does not change.

## Field lifecycle

A field's state machine, mirroring `docs/MASTER_SCHEMA.md`'s existing
coverage lifecycle: `required`/`recommended`/`optional` (by field_group,
category, and now sector pack) → **pending_extraction** → either
**populated** (with full `provenance_requirements` satisfied, or rejected at
validation per the sources_lineage_freshness hard gates) or
**unavailable**/**not_applicable** (each with its own evidence object, see
above) → periodically re-checked per `freshness_policy` → **stale** if it
exceeds `max_age_before_stale_days` without a successful re-check.

## Conflicts found with the existing catalog

- **Category-name overlap, not field-key overlap.** `catalog.py`'s `GROUPS`
  names (`company_model`, `income_statement`, `profitability`, `banking`,
  ...) map cleanly onto this contract's `field_groups`; no field key means
  two different things between this contract and `catalog.py` — this
  contract references catalog field_groups rather than redefining fields, so
  there is nothing to resolve at the field-key level.
- **Two different "18 categories."** As described above,
  `docs/DATA_MODEL_18_CATEGORIES.md` already claims the name "the 18
  categories" for a different partition. This document does not silently
  pick a winner; both stand, distinguished by which document is being read.
- **Operational KPIs vs sector-specific fields is a contract-level split
  that `catalog.py` does not make.** `catalog.py` has one `GROUPS` entry per
  industry mixing both concepts in some sectors (e.g. `"banking"` is all
  statement-shaped; `"real_estate"` mixes occupancy/GLA KPIs with FFO/NAV
  financial lines in the same group). This contract puts `real_estate`
  entirely under `sector_specific_fields` (not split field-by-field within
  the group) since FFO/NAV dominate its purpose; this is a documented
  simplification, not a hidden one — a future REIT-specific KPI split would
  need a `catalog.py` change, which is out of scope here.
- **No banking operational-KPI field_group exists yet.** `docs/SOURCE_MAP.md`
  already documents this gap (Al Rajhi's 511 branches/4,327 ATMs/20.6M
  customers "exist in a reviewed manifest" but there is no
  `operational_kpis` catalog field_group to hold them for banks). The
  banking sector pack marks `operational_kpis` `not_applicable` for banks
  under the *current* catalog rather than inventing a field mapping that
  isn't backed by `catalog.py` — flagged here as a real gap for a future,
  separate `catalog.py` change (this deliverable does not touch
  `catalog.py`).

## Fields that would need a paid/licensed data provider to ever be closed

Being explicit and honest, per the task's hard rule against assuming paid
data is fine and the project's standing `project_data_source_decision` (no
paid feed until revenue):

1. **`consensus` field_group** (`revenue_estimate`, `ebitda_estimate`,
   `ebit_estimate`, `net_income_estimate`,
   `selling_general_administrative_expense_estimate`, `eps_estimate`) —
   `docs/SOURCE_MAP.md` already states plainly: *"14 Analyst coverage ...
   no primary source exists for this category."* There is no free official
   analyst-consensus feed; this can only close via a licensed vendor or
   systematically collected attributed research.
2. **Named institutional-holder detail inside `ownership`** (identifying a
   specific holder such as Vanguard/BlackRock by name below the 5%
   mandatory-disclosure threshold) — `docs/SOURCE_MAP.md` category 4 flags
   this as Secondary/licensed; the ≥5% holder disclosures themselves remain
   free.
3. **Analyst ratings and target prices** (if modeled as their own fields
   beyond the `consensus` group) — same "no primary source" gap as (1);
   any systematic collection is either licensed-vendor or named/attributed
   press, per `docs/SOURCE_MAP.md`'s Opinion tier rule.

No other category in this contract has a field whose only realistic source
is paid — every other gap on record (Saudi Exchange historical-price CDN
access, stc's presentation-archive 403s, ARPU/coverage non-disclosure) is a
free-source retrieval or disclosure gap, not a licensing requirement, and
this document keeps that distinction explicit so `source_cost` is never
miscoded as `licensed` for convenience.
