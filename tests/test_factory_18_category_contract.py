"""Validates config/factory/18-category-contract.json and the sector packs.

This is a standalone specification test. It intentionally does NOT import
src/finengine/factory.py, jobs.py, operations.py, cli.py or database.py, and
does not touch tests/test_data_factory_acceptance.py -- it only checks that
the contract JSON is well-formed, internally consistent, and that the sector
packs reference only things the master contract actually defines. It does
cross-check field_group names against src/finengine/catalog.py, since the
contract claims to align with catalog.py's existing field-group naming.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from finengine.catalog import GROUPS

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "config" / "factory" / "18-category-contract.json"
SECTOR_PACK_DIR = REPO_ROOT / "config" / "factory" / "sector-packs"

REQUIRED_CATEGORY_KEYS = {
    "category_key", "weight", "field_groups", "applicability", "official_sources",
    "extraction_mode", "job_strategy", "unavailable_conditions",
    "not_applicable_conditions", "completeness_threshold", "threshold_rationale",
    "hard_gates", "source_cost", "source_cost_notes", "provenance_requirements",
    "freshness_policy", "notes",
}

EXPECTED_18_CATEGORY_KEYS = {
    "company_profile", "financial_statements", "profitability", "liquidity_solvency",
    "efficiency", "growth", "per_share", "valuation", "market_data", "dividends",
    "segments", "ownership", "corporate_actions", "announcements", "operational_kpis",
    "sector_specific_fields", "calculated_smart_metrics", "sources_lineage_freshness",
}

CATALOG_FIELD_GROUP_NAMES = {g[0] for g in GROUPS}
# The sources_lineage_freshness category is explicitly cross-cutting and does not
# correspond to a catalog.py field_group -- documented in the docs page.
CROSS_CUTTING_SENTINEL = "*cross_cutting*"


@pytest.fixture(scope="module")
def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sector_packs():
    packs = {}
    for path in sorted(SECTOR_PACK_DIR.glob("*.json")):
        packs[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return packs


# --- Master contract structural validation ----------------------------------


def test_contract_file_exists_and_parses(contract):
    assert contract["contract_version"]
    assert isinstance(contract["categories"], list)


def test_exactly_18_categories_with_expected_keys(contract):
    keys = [c["category_key"] for c in contract["categories"]]
    assert len(keys) == 18
    assert set(keys) == EXPECTED_18_CATEGORY_KEYS


def test_no_duplicate_category_keys(contract):
    keys = [c["category_key"] for c in contract["categories"]]
    assert len(keys) == len(set(keys)), "duplicate category_key found"


def test_every_category_has_all_required_top_level_keys(contract):
    for c in contract["categories"]:
        missing = REQUIRED_CATEGORY_KEYS - set(c.keys())
        assert not missing, f"{c.get('category_key')} missing keys: {missing}"


def test_weights_sum_to_100(contract):
    total = sum(c["weight"] for c in contract["categories"])
    assert total == 100, f"category weights sum to {total}, expected 100"


def test_every_weight_is_positive(contract):
    for c in contract["categories"]:
        assert c["weight"] > 0, c["category_key"]


def test_overall_threshold_present_and_reasonable(contract):
    assert 0 < contract["overall_completeness_threshold"] <= 1.0
    assert contract["overall_threshold_rationale"]


def test_completeness_thresholds_in_valid_range(contract):
    for c in contract["categories"]:
        assert 0 < c["completeness_threshold"] <= 1.0, c["category_key"]
        assert c["threshold_rationale"], f"{c['category_key']} has no threshold_rationale"


def test_sources_lineage_freshness_is_100_percent_and_a_hard_gate(contract):
    c = next(x for x in contract["categories"] if x["category_key"] == "sources_lineage_freshness")
    assert c["completeness_threshold"] == 1.0
    assert len(c["hard_gates"]) >= 1


def test_financial_statements_is_95_percent(contract):
    c = next(x for x in contract["categories"] if x["category_key"] == "financial_statements")
    assert c["completeness_threshold"] == 0.95


def test_every_category_has_at_least_one_hard_gate(contract):
    for c in contract["categories"]:
        assert c["hard_gates"], f"{c['category_key']} has no hard_gates"
        for g in c["hard_gates"]:
            assert g["condition"]
            assert g["action"]


def test_every_hard_gate_condition_and_action_are_strings(contract):
    for c in contract["categories"]:
        for g in c["hard_gates"]:
            assert isinstance(g["condition"], str) and g["condition"].strip()
            assert isinstance(g["action"], str) and g["action"].strip()


# --- field_groups alignment with catalog.py ----------------------------------


def test_every_category_field_group_exists_in_catalog_or_is_the_documented_sentinel(contract):
    for c in contract["categories"]:
        for fg in c["field_groups"]:
            assert fg in CATALOG_FIELD_GROUP_NAMES or fg == CROSS_CUTTING_SENTINEL, (
                f"{c['category_key']} references field_group {fg!r} which does not exist "
                f"in src/finengine/catalog.py GROUPS and is not the documented cross-cutting sentinel"
            )


def test_only_sources_lineage_freshness_uses_the_cross_cutting_sentinel(contract):
    for c in contract["categories"]:
        if CROSS_CUTTING_SENTINEL in c["field_groups"]:
            assert c["category_key"] == "sources_lineage_freshness"


def test_field_groups_are_not_empty(contract):
    for c in contract["categories"]:
        assert c["field_groups"], c["category_key"]


# --- required/recommended/optional non-overlap (field_group granularity) -----


def test_no_field_group_double_counted_within_a_category(contract):
    for c in contract["categories"]:
        assert len(c["field_groups"]) == len(set(c["field_groups"])), c["category_key"]


def test_extraction_mode_keys_match_field_groups(contract):
    for c in contract["categories"]:
        assert set(c["extraction_mode"].keys()) == set(c["field_groups"]), c["category_key"]
        for mode in c["extraction_mode"].values():
            assert mode in ("deterministic", "requires_review")


# --- vocabulary conformance ---------------------------------------------------


def test_job_strategy_is_from_the_controlled_vocabulary(contract):
    vocab = set(contract["controlled_vocabularies"]["job_strategy"])
    for c in contract["categories"]:
        assert c["job_strategy"] in vocab, c["category_key"]


def test_official_sources_never_include_a_forbidden_llm_source(contract):
    forbidden = set(contract["controlled_vocabularies"]["forbidden_source_types"])
    valid = set(contract["controlled_vocabularies"]["official_source_types"])
    for c in contract["categories"]:
        for s in c["official_sources"]:
            assert s not in forbidden, f"{c['category_key']} lists a forbidden LLM source type: {s}"
            assert s in valid, f"{c['category_key']} lists an undeclared source type: {s}"


def test_source_cost_is_from_the_controlled_vocabulary(contract):
    vocab = {"free", "mixed", "licensed"}
    for c in contract["categories"]:
        assert c["source_cost"] in vocab, c["category_key"]


def test_unavailable_reasons_are_a_subset_of_the_declared_vocabulary(contract):
    vocab = set(contract["controlled_vocabularies"]["unavailable_reasons"])
    for c in contract["categories"]:
        reasons = set(c["unavailable_conditions"]["allowed_reasons"])
        assert reasons <= vocab, c["category_key"]


def test_not_applicable_reasons_are_a_subset_of_the_declared_vocabulary(contract):
    vocab = set(contract["controlled_vocabularies"]["not_applicable_reasons"])
    for c in contract["categories"]:
        reasons = set(c["not_applicable_conditions"]["allowed_reasons"])
        assert reasons <= vocab, c["category_key"]


def test_unavailable_and_not_applicable_require_evidence(contract):
    for c in contract["categories"]:
        assert c["unavailable_conditions"]["evidence_required"] is True, c["category_key"]
        assert c["not_applicable_conditions"]["evidence_required"] is True, c["category_key"]
        assert c["unavailable_conditions"]["evidence_fields"], c["category_key"]
        assert c["not_applicable_conditions"]["evidence_fields"], c["category_key"]


def test_provenance_requirements_use_only_declared_field_names(contract):
    vocab = set(contract["controlled_vocabularies"]["provenance_field_names"])
    for c in contract["categories"]:
        mandatory = set(c["provenance_requirements"]["mandatory_fields"])
        assert mandatory <= vocab, c["category_key"]
        assert mandatory, f"{c['category_key']} declares zero mandatory provenance fields"


def test_sources_lineage_freshness_requires_all_five_provenance_fields(contract):
    c = next(x for x in contract["categories"] if x["category_key"] == "sources_lineage_freshness")
    vocab = set(contract["controlled_vocabularies"]["provenance_field_names"])
    assert set(c["provenance_requirements"]["mandatory_fields"]) == vocab


def test_freshness_policy_has_a_cadence_kind(contract):
    valid_kinds = {"periodic", "event_driven", "continuous", "derived"}
    for c in contract["categories"]:
        assert c["freshness_policy"]["cadence_kind"] in valid_kinds, c["category_key"]


def test_applicability_is_structured_not_bare_prose(contract):
    for c in contract["categories"]:
        app = c["applicability"]
        assert set(["rule", "condition", "flag_source", "description"]) <= set(app.keys()), c["category_key"]
        assert app["rule"]
        assert app["condition"]


# --- anti-averaging principle -------------------------------------------------


def test_anti_averaging_principle_is_documented(contract):
    assert "anti_averaging_principle" in contract
    assert len(contract["anti_averaging_principle"]) > 50


# --- Sector pack validation ----------------------------------------------------


def test_both_expected_sector_packs_exist(sector_packs):
    assert set(sector_packs.keys()) == {"telecom", "banking"}


def test_sector_pack_activated_field_groups_exist_in_master_contract(contract, sector_packs):
    all_field_groups = set()
    for c in contract["categories"]:
        all_field_groups.update(c["field_groups"])
    for name, pack in sector_packs.items():
        activated = (
            pack["activates"]["operational_kpis_field_groups"]
            + pack["activates"]["sector_specific_fields_field_groups"]
        )
        for fg in activated:
            assert fg in all_field_groups, (
                f"sector pack {name!r} activates field_group {fg!r} which is not "
                f"referenced by any category in the master contract"
            )


def test_sector_pack_not_applicable_categories_are_real_category_keys(contract, sector_packs):
    valid_keys = {c["category_key"] for c in contract["categories"]}
    for name, pack in sector_packs.items():
        for key in pack["category_overrides"]["not_applicable_categories"]:
            assert key in valid_keys, f"sector pack {name!r} references unknown category {key!r}"


def test_sector_pack_activated_kpi_groups_are_within_operational_kpis_category(contract, sector_packs):
    kpi_category = next(c for c in contract["categories"] if c["category_key"] == "operational_kpis")
    allowed = set(kpi_category["field_groups"])
    for name, pack in sector_packs.items():
        activated = set(pack["activates"]["operational_kpis_field_groups"])
        assert activated <= allowed, f"sector pack {name!r} activates a KPI field_group outside operational_kpis: {activated - allowed}"


def test_sector_pack_activated_sector_specific_groups_are_within_that_category(contract, sector_packs):
    ssf_category = next(c for c in contract["categories"] if c["category_key"] == "sector_specific_fields")
    allowed = set(ssf_category["field_groups"])
    for name, pack in sector_packs.items():
        activated = set(pack["activates"]["sector_specific_fields_field_groups"])
        assert activated <= allowed, f"sector pack {name!r} activates a sector-specific field_group outside sector_specific_fields: {activated - allowed}"


def test_sector_pack_never_redefines_master_weight_threshold_or_gates(sector_packs):
    forbidden_keys = {"weight", "completeness_threshold", "hard_gates", "extraction_mode"}
    for name, pack in sector_packs.items():
        assert forbidden_keys.isdisjoint(pack.keys()), (
            f"sector pack {name!r} must not redefine {forbidden_keys & set(pack.keys())}"
        )


def test_sector_pack_canonical_industry_values_are_nonempty_strings(sector_packs):
    for name, pack in sector_packs.items():
        assert pack["canonical_industry_values"]
        for v in pack["canonical_industry_values"]:
            assert isinstance(v, str) and v.strip()


def test_telecom_and_banking_packs_do_not_both_activate_the_same_category(contract, sector_packs):
    # Sanity: telecom activates operational_kpis, not sector_specific_fields, and
    # vice versa for banking, matching the documented catalog.py gap.
    telecom = sector_packs["telecom"]
    banking = sector_packs["banking"]
    assert telecom["activates"]["operational_kpis_field_groups"]
    assert not telecom["activates"]["sector_specific_fields_field_groups"]
    assert banking["activates"]["sector_specific_fields_field_groups"]
    assert not banking["activates"]["operational_kpis_field_groups"]


# --- Deliberately-broken fixtures: prove the validation logic actually catches bad contracts ---


def _reload_validators():
    """Re-import validator-style checks as plain functions so they can be run
    against a mutated, in-memory copy of the contract/packs without touching
    the on-disk fixtures. Mirrors the assertions above but parameterized."""

    def field_groups_exist(contract_obj):
        for c in contract_obj["categories"]:
            for fg in c["field_groups"]:
                if fg not in CATALOG_FIELD_GROUP_NAMES and fg != CROSS_CUTTING_SENTINEL:
                    return False
        return True

    def weights_sum_to_100(contract_obj):
        return sum(c["weight"] for c in contract_obj["categories"]) == 100

    def no_duplicate_keys(contract_obj):
        keys = [c["category_key"] for c in contract_obj["categories"]]
        return len(keys) == len(set(keys))

    def pack_field_groups_exist(contract_obj, pack_obj):
        all_field_groups = set()
        for c in contract_obj["categories"]:
            all_field_groups.update(c["field_groups"])
        activated = (
            pack_obj["activates"]["operational_kpis_field_groups"]
            + pack_obj["activates"]["sector_specific_fields_field_groups"]
        )
        return all(fg in all_field_groups for fg in activated)

    def pack_not_applicable_categories_valid(contract_obj, pack_obj):
        valid_keys = {c["category_key"] for c in contract_obj["categories"]}
        return all(k in valid_keys for k in pack_obj["category_overrides"]["not_applicable_categories"])

    return {
        "field_groups_exist": field_groups_exist,
        "weights_sum_to_100": weights_sum_to_100,
        "no_duplicate_keys": no_duplicate_keys,
        "pack_field_groups_exist": pack_field_groups_exist,
        "pack_not_applicable_categories_valid": pack_not_applicable_categories_valid,
    }


def test_good_contract_passes_every_validator(contract, sector_packs):
    v = _reload_validators()
    assert v["field_groups_exist"](contract) is True
    assert v["weights_sum_to_100"](contract) is True
    assert v["no_duplicate_keys"](contract) is True
    for pack in sector_packs.values():
        assert v["pack_field_groups_exist"](contract, pack) is True
        assert v["pack_not_applicable_categories_valid"](contract, pack) is True


def test_broken_fixture_orphan_field_group_is_rejected(contract):
    v = _reload_validators()
    broken = copy.deepcopy(contract)
    broken["categories"][0]["field_groups"].append("this_field_group_does_not_exist_anywhere")
    assert v["field_groups_exist"](broken) is False


def test_broken_fixture_bad_weight_sum_is_rejected(contract):
    v = _reload_validators()
    broken = copy.deepcopy(contract)
    broken["categories"][0]["weight"] += 5  # now sums to 105
    assert v["weights_sum_to_100"](broken) is False


def test_broken_fixture_duplicate_category_key_is_rejected(contract):
    v = _reload_validators()
    broken = copy.deepcopy(contract)
    broken["categories"][1]["category_key"] = broken["categories"][0]["category_key"]
    assert v["no_duplicate_keys"](broken) is False


def test_broken_fixture_sector_pack_referencing_nonexistent_category_is_rejected(contract, sector_packs):
    """The exact scenario the task asked to prove: a sector pack referencing a
    nonexistent category must fail validation, not silently pass."""
    v = _reload_validators()
    broken_pack = copy.deepcopy(sector_packs["telecom"])
    broken_pack["category_overrides"]["not_applicable_categories"].append("this_category_does_not_exist")
    assert v["pack_not_applicable_categories_valid"](contract, broken_pack) is False


def test_broken_fixture_sector_pack_activating_orphan_field_group_is_rejected(contract, sector_packs):
    v = _reload_validators()
    broken_pack = copy.deepcopy(sector_packs["banking"])
    broken_pack["activates"]["sector_specific_fields_field_groups"].append("nonexistent_field_group_xyz")
    assert v["pack_field_groups_exist"](contract, broken_pack) is False
