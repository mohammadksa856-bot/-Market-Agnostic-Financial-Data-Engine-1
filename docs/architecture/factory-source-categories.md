# The 8 audited source categories: company_profile, dividends, segments, ownership, corporate_actions, announcements, operational_kpis, sector_specific_fields

This document is the companion audit for the 8 categories named in this
task, inside the already-shipped 18-category contract described in
`docs/architecture/data-factory-18-categories.md`. It does not redefine the
contract (`config/factory/18-category-contract.json`), the catalog
(`src/finengine/catalog.py`), or the financial-statement-derived categories
(financial_statements, profitability, liquidity_solvency, efficiency,
growth, per_share, valuation, market_data, calculated_smart_metrics,
sources_lineage_freshness) — those are other agents' scope and are
byte-identical before and after this branch's changes (verified below).

## What already existed before this audit

Reading `src/finengine/factory_contract.py` and the contract JSON showed the
8 categories were **already substantially complete** on this branch
(`claude/factory-source-categories`, branched from
`origin/codex/telecom-95pct`):

- All 8 categories already have a full contract entry: `field_groups`,
  `applicability`, `official_sources`, `extraction_mode` (split
  deterministic vs. `requires_review` per field_group), `job_strategy`,
  `unavailable_conditions`/`not_applicable_conditions` with evidence
  requirements, a per-category `completeness_threshold` distinct from the
  95% overall figure, at least one `hard_gate`, `provenance_requirements`,
  and a `freshness_policy`.
- `_deterministic_gates()` in `factory_contract.py` already implements real,
  machine-evaluable hard gates for all 8 categories (e.g. company_profile's
  "company_model completeness < 60%" gate, dividends' "fact with no linked
  announcement" gate, ownership's "percentage sum > 100%" gate,
  corporate_actions'/announcements' disclosure-linkage and staleness gates,
  operational_kpis' "activated group but zero populated fields" gate).
- `evaluate_factory_contract()` already enforces the anti-averaging
  principle end to end: every category's own threshold and every hard gate
  must pass independently of the weighted average, and a sector pack can
  only narrow (`not_applicable_categories`, `activates.*_field_groups`), never
  loosen, a gate or threshold — enforced structurally because sector packs
  carry no `weight`/`completeness_threshold`/`hard_gates`/`extraction_mode`
  keys the evaluator ever reads.
- `_reviewed_field_exclusions()` already enforces the "no silent blank"
  rule: an `unavailable`/`not_applicable` field is only excluded from a
  category's denominator if it is backed by an archived `source_documents`
  row (URL + content hash) and a reviewer-attributed reason from the
  contract's controlled vocabulary — `Database.upsert_field_availability`
  raises `ValueError` otherwise (see `test_negative_evidence_cannot_be_
  recorded_without_required_proof`).

**This audit's actual gap, once the above was confirmed, was sector packs.**
Only 2 of the 15 requested sector packs existed (`banking`, `telecom`). The
other 13 are what this branch adds.

## The 15 sector packs

Each pack is a thin JSON file in `config/factory/sector-packs/` that:

1. Names the catalog `industry` string it matches (`canonical_industry_values`,
   taken verbatim from `src/finengine/catalog.py`'s `GROUPS` industry
   `scope_value` — e.g. `"Integrated Oil & Gas"`, `"Health Care"`).
2. Activates the real catalog field_groups that already exist for that
   sector (`activates.operational_kpis_field_groups` and/or
   `activates.sector_specific_fields_field_groups`).
3. Marks the *other* of those two categories `not_applicable` when the
   catalog genuinely has no corresponding field_group for that sector
   (documented per-pack in `notes`, not silently).
4. Lists `additional_required_fields` — a reviewed subset of the activated
   group's fields that should move from "recommended" to effectively
   required for that sector (every field checked against
   `iter_catalog_fields()`; see `test_every_sector_pack_additional_required_
   field_exists_in_catalog`).
5. Adds `sector_regulator` as an `additional_official_sources` entry where a
   real regulator exists (SAMA for banking/insurance, ECRA-style regulators
   for utilities, etc.).

| Pack file | Catalog industry | operational_kpis field_group | sector_specific_fields field_group | not_applicable |
|---|---|---|---|---|
| `banking.json` (pre-existing) | Banks | — | banking | operational_kpis |
| `telecom.json` (pre-existing) | Telecommunications | telecommunications | — | sector_specific_fields |
| `insurance.json` | Insurance | — | insurance | operational_kpis |
| `real-estate.json` | Real Estate & REITs | — | real_estate | operational_kpis |
| `oil-gas.json` | Integrated Oil & Gas | oil_gas_operations | segments | *(none — both activated)* |
| `petrochemicals.json` | Diversified Chemicals | chemical_operations | segments | *(none — both activated)* |
| `retail.json` | Retail | retail | — | sector_specific_fields |
| `healthcare.json` | Health Care | healthcare | — | sector_specific_fields |
| `utilities.json` | Utilities | utilities | — | sector_specific_fields |
| `mining.json` | Mining | mining | — | sector_specific_fields |
| `transportation-logistics.json` | Transportation & Logistics | transportation_logistics | — | sector_specific_fields |
| `industrial-construction.json` | Industrials & Construction | industrial_construction | — | sector_specific_fields |
| `technology.json` | Technology | technology | — | sector_specific_fields |
| `food-agriculture.json` | Food & Agriculture | food_agriculture | — | sector_specific_fields |
| `asset-management.json` | Asset Management | asset_management | — | sector_specific_fields |

**oil_gas and petrochemicals are the two exceptions** to the usual
"operational_kpis XOR sector_specific_fields" pattern banking/telecom
established: `catalog.py` defines an industry-scoped addition to the
`segments` field_group for both (`Integrated Oil & Gas`: upstream/downstream
revenue and EBIT; `Diversified Chemicals`: petrochemicals/agri-nutrients/
specialties/metals segment revenue), which is genuinely a different shape of
data (segment P&L) from the physical production-volume metrics in
`oil_gas_operations`/`chemical_operations`. Both packs activate both
categories rather than forcing a choice the catalog itself didn't make.

## Acquisition plans (per category, not one generic "monitor" step)

| Category | Target source types | Expected output |
|---|---|---|
| company_profile | `issuer_investor_relations_site`, `issuer_annual_report`, `company_registry`, `exchange_disclosure_archive` | `company_model` (deterministic: registry/listing facts), `governance_profile`/`industry_context` (requires_review: board/committee narrative) |
| dividends | `exchange_disclosure_archive` (dividend declaration/eligibility/ex-date announcements), `issuer_investor_relations_site`, `internal_computation` (payout ratios) | Per-declaration `corporate_actions` row of type `cash_dividend` linked to its `disclosures` announcement; derived `dividends` data_points |
| segments | `issuer_audited_financial_statements` (segment note), `issuer_investor_presentation` | Per-segment `data_points` (revenue/EBIT/EBITDA/assets/capex) scoped by `dimensions_json.segment` |
| ownership | `exchange_disclosure_archive` (major-holder disclosures ≥5%, free float), `sector_regulator`, `internal_computation` | `ownership_positions` rows reconciling to 100% per `as_of_date` |
| corporate_actions | `exchange_disclosure_archive`, `issuer_investor_relations_site` | `corporate_actions` rows (splits, bonus shares, buybacks, capital changes, M&A) each linked to the `disclosures` row that announced it |
| announcements | `exchange_disclosure_archive`, `issuer_investor_relations_site` | `disclosures` rows via `continuous_announcement_polling`; materiality tagging is `requires_review` |
| operational_kpis | `issuer_investor_presentation`, `issuer_results_call_transcript`, `issuer_annual_report`, `sector_regulator` | Sector-pack-selected `data_points` for exactly the field_group(s) that sector's pack activates (see table above) |
| sector_specific_fields | `issuer_audited_financial_statements`, `sector_regulator`, `exchange_disclosure_archive` | Sector-pack-selected statement-shaped `data_points` (banking/insurance/real_estate balance-sheet/income/ratio lines, or oil_gas/petrochemicals segment P&L) |

Each row names real source types and a real output shape — no category is
left pointing at an undifferentiated "monitor the company" step.

## Honest gap report

**Implemented (fully, for all 8 categories):**
- Contract entries, catalog field alignment, hard gates, evidence-gated
  unavailable/not_applicable, freshness policies, provenance requirements —
  all pre-existing on this branch and verified by the test suite.
- Sector packs: all 15 requested sectors now have a pack (13 new + 2
  pre-existing), each activating real catalog field_groups only.

**Unsupported source types (no deterministic or review route built):**
- Named institutional-holder detail *below* the ≥5% disclosure threshold
  (ownership) has no official free source on this project — flagged in the
  contract itself as `licensed_source_required` and in the ownership pack's
  `source_cost: "mixed"`.
- There is no deterministic route for *classifying* an announcement's
  materiality (dividend/earnings/governance/M&A flags) — this is
  `requires_review` by design; an LLM may propose a classification but it is
  never itself an `official_source_type` (see `forbidden_source_types` in
  the contract and `test_no_official_source_type_can_ever_be_an_llm_output_
  type`).
- Reserve/resource figures (oil_gas, mining) have no deterministic route
  because classification basis (SEC/PRMS/JORC/SAMREC, proved vs. probable)
  varies by issuer and must be confirmed by a reviewer before publish.

**Fields requiring licensed data:**
- Only one field class across these 8 categories: named institutional
  ownership below the 5% disclosure floor (ownership category). Per this
  project's own data-source decision (no paid data API until the product
  earns revenue), this remains `unavailable` with reason
  `licensed_source_required` rather than purchased.

**Remaining catalog/schema gaps:**
- `catalog.py` has no dedicated banking or insurance *operational*
  field_group (branch/ATM/policy counts) — both were already flagged
  not_applicable for `operational_kpis` before this audit and remain so; a
  future catalog change (out of scope here, since this contract must not
  edit `catalog.py` per the master contract's own ground rules) could add
  one.
- No sector has a `sector_specific_fields` field_group named after it other
  than banking/insurance/real_estate/segments — the 10 remaining sectors in
  this audit correctly fall back to `not_applicable` for that category
  because the catalog genuinely has nothing sector-specific-statement-shaped
  for them (their financial-statement lines are all covered by the
  universal financial_statements/profitability/etc. categories already).

**Coverage numbers — reported separately, not blended:**
This audit changed zero rows of actual company data (no `data/raw`,
`data/imports`, or Supabase writes). Every one of the five coverage numbers
below is therefore about the *contract/schema*, not about any company's
real completeness, which depends on data this branch did not touch:

- **Raw coverage**: N/A — no raw documents were added, read, or removed.
- **Parsed coverage**: N/A — no extraction ran.
- **Published coverage**: N/A — no `data_points`/`ownership_positions`/etc.
  rows were written.
- **Category coverage** (contract completeness, i.e. "does every one of the
  8 categories have a real, non-stub contract entry + sector packs for all
  15 sectors?"): **100%** — verified by
  `tests/test_factory_18_category_contract.py` and
  `tests/test_factory_contract_runtime.py` (57/57 passing).
- **Final readiness** (can any real company be marked "ready" under this
  contract?): depends entirely on that company's actually collected data,
  which this branch does not touch. The bootstrap/audit run below confirms
  the contract *loads and evaluates* cleanly against a fresh, empty, local
  database — not that any company is ready.

No number above is a substitute for the others, and none is claimed as a
single blended "95%".
