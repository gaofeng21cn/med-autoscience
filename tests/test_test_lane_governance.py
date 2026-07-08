from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from tests.standard_agent_purity_helpers import (
    assert_standard_agent_purity_boundary,
)


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _test_lane_manifest() -> dict[str, object]:
    return json.loads(_read("contracts/test-lane-manifest.json"))


def test_meta_lane_does_not_rerun_family_or_architecture_owner_tests() -> None:
    makefile = _read("Makefile")
    conftest = _read("tests/conftest.py")

    meta_block = makefile.split("test-meta:", maxsplit=1)[1].split("\ntest-display:", maxsplit=1)[0]
    assert "scripts/run-pytest-clean.sh -q -m meta" in meta_block
    assert "ARCH_OWNER_BOUNDARY_TEST" not in meta_block
    meta_files_block = conftest.split("META_FILES = {", maxsplit=1)[1].split("\n}", maxsplit=1)[0]
    assert "tests/test_dev_preflight.py" not in meta_files_block
    assert "tests/test_dev_preflight_contract.py" not in meta_files_block


def test_test_lane_manifest_paths_exist_and_are_used_by_makefile() -> None:
    manifest = _test_lane_manifest()
    makefile = _read("Makefile")

    lane_markers = {
        marker
        for lane in manifest["lanes"].values()
        for marker in lane.get("markers", [])
    }
    marker_registry = set(manifest["marker_registry"])
    assert lane_markers <= marker_registry

    for lane in manifest["lanes"].values():
        for path in lane.get("paths", []):
            assert (REPO_ROOT / path).exists(), path
    for lane_id, lane in manifest["focused_lanes"].items():
        for key in ("paths", "docs"):
            for path in lane.get(key, []):
                assert (REPO_ROOT / path).exists(), f"{lane_id} references missing {key}: {path}"
    assert " ".join(manifest["lanes"]["smoke"]["paths"]) in makefile
    for path in manifest["lanes"]["fast"]["paths"]:
        assert path in makefile


def test_fast_lane_is_path_based_and_not_regression_alias() -> None:
    manifest = _test_lane_manifest()
    makefile = _read("Makefile")
    verify_script = _read("scripts/verify.sh")
    fast_paths = manifest["lanes"]["fast"]["paths"]

    assert fast_paths == [
        "tests/test_smoke_entrypoints.py",
        "tests/test_line_budget.py",
        "tests/test_test_lane_governance.py",
    ]
    assert manifest["lanes"]["fast"]["overlap_policy"] == "entry_and_lane_governance_only"

    fast_make_block = makefile.split("test-fast:", maxsplit=1)[1].split(
        "\ntest-meta:", maxsplit=1
    )[0]
    assert "test-regression" not in fast_make_block
    assert "scripts/run-pytest-clean.sh $(FAST_TESTS) -q" in fast_make_block

    fast_verify_block = verify_script.split('if [[ "${lane}" == "fast" ]]', maxsplit=1)[
        1
    ].split('if [[ "${lane}" == "meta" ]]', maxsplit=1)[0]
    assert '"make test-fast" make test-fast' in fast_verify_block
    assert "make test-regression" not in fast_verify_block


def test_test_lane_manifest_entries_are_unique() -> None:
    manifest = _test_lane_manifest()

    for lane_id, lane in manifest["lanes"].items():
        for key in ("paths", "markers"):
            values = lane.get(key, [])
            assert len(values) == len(set(values)), f"{lane_id} has duplicate {key}: {values}"
    for lane_id, lane in manifest["focused_lanes"].items():
        for key in ("paths", "docs"):
            values = lane.get(key, [])
            assert len(values) == len(set(values)), f"{lane_id} has duplicate {key}: {values}"


def test_functional_privatization_audit_exposes_standard_agent_purity_guard() -> None:
    audit = json.loads(_read("contracts/functional_privatization_audit.json"))
    boundary = audit["functional_consumer_boundary"]

    assert audit["classification_buckets"] == [
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    ]
    assert audit["standard_agent_purity_policy"] == (
        "default_surfaces_must_remain_standard_agent_purity_guarded"
    )
    assert_standard_agent_purity_boundary(boundary)


def test_private_surface_retirement_contracts_expose_completion_gates() -> None:
    audit = json.loads(_read("contracts/functional_privatization_audit.json"))
    policy = json.loads(_read("contracts/private_functional_surface_policy.json"))
    inventory = json.loads(_read("contracts/authority_kernel_inventory.json"))

    disposition = audit["retirement_disposition_matrix"]
    assert disposition["surface_kind"] == "mas_private_surface_retirement_disposition_matrix"
    assert disposition["source_of_truth_chain"] == (
        "DomainIntent -> OPL Command/Event/Outbox/StageRun -> MAS OwnerAnswer -> Derived Projection"
    )
    assert disposition["completion_claim_policy"] == {
        "contracts_or_tests_alone_can_claim_100_percent": False,
        "live_proof_required_before_100_percent": True,
        "ready_claim_authorized": False,
    }
    assert disposition["required_retirement_gate_fields"] == [
        "no_active_caller",
        "no_forbidden_write_proof",
        "replacement_parity",
        "retirement_gate",
        "tombstone_or_provenance",
    ]
    dispositions_by_id = {
        module_id: item["disposition"]
        for item in disposition["surface_dispositions"]
        for module_id in item["module_ids"]
    }
    assert dispositions_by_id["generic_daemon_or_scheduler_lifecycle"] == "tombstone_only"
    assert dispositions_by_id["generic_queue_attempt_retry_dead_letter"] == (
        "opl_primitive_replacement"
    )
    assert dispositions_by_id["generic_transition_runner"] == "opl_primitive_replacement"
    assert dispositions_by_id["workbench_portal_generic_shell"] == "temporary_refs_projection"
    assert dispositions_by_id["paper_mission_owner_surface_materialize_dispatch_shell"] == (
        "temporary_refs_projection"
    )
    assert dispositions_by_id["owner_receipt"] == "retained_minimal_authority_function"
    for item in disposition["surface_dispositions"]:
        for required_field in disposition["required_retirement_gate_fields"]:
            assert item[required_field], item["disposition"]

    boundary_followthrough = audit["functional_consumer_boundary"][
        "functional_followthrough_gap_summary"
    ]
    assert audit["functional_followthrough_gap_summary"]["retirement_gate_checklist"] == (
        boundary_followthrough["retirement_gate_checklist"]
    )
    checklist = boundary_followthrough["retirement_gate_checklist"]
    assert checklist["surface_kind"] == "mas_private_surface_retirement_gate_checklist"
    assert checklist["completion_percent_policy"].startswith("do_not_report_100_percent")
    assert {item["gate_id"] for item in checklist["gate_items"]} == {
        "no_active_caller",
        "replacement_parity",
        "no_forbidden_write_proof",
        "tombstone_or_provenance",
        "live_owner_or_stable_blocker",
    }

    private_policy = policy["mas_private_surface_retirement_gate_policy"]
    assert private_policy["surface_kind"] == "mas_private_surface_retirement_gate_policy"
    assert private_policy["active_caller_alone_retains_surface"] is False
    assert private_policy["allowed_dispositions"] == [
        "opl_primitive",
        "temporary_refs_projection",
        "retained_minimal_authority_function",
        "tombstone_only",
    ]
    assert "current_tests_green" in private_policy["forbidden_retention_reasons"]
    assert "100_percent_complete_without_live_proof" in private_policy["must_not_claim"]
    assert policy["classification_required_for_private_surfaces"] is True

    inventory_policy = inventory["retirement_gate_policy"]
    assert inventory_policy["surface_kind"] == "mas_authority_kernel_retirement_gate_policy"
    assert inventory_policy["completion_percent_policy"].startswith(
        "inventory_or_test_green_is_not_100_percent"
    )
    required_item_fields = set(inventory_policy["required_item_fields"])
    for item in inventory["items"]:
        assert required_item_fields <= set(item), item["item_id"]
        assert item["no_forbidden_write_proof"].startswith("required_no_write_to_")
        if item["category"] in {"refs_only_helper", "diagnostic_probe"}:
            assert item["disposition"] == "temporary_refs_projection", item["item_id"]
        elif item["category"] == "retired_diagnostic_provenance":
            assert item["disposition"] == "tombstone_only", item["item_id"]
        else:
            assert item["disposition"] == "retained_minimal_authority_function", item["item_id"]


def test_physical_source_morphology_scan_is_repo_proof_not_completion_claim() -> None:
    audit = json.loads(_read("contracts/functional_privatization_audit.json"))
    scan = audit["physical_source_morphology_scan"]

    assert scan["surface_kind"] == "mas_physical_source_morphology_scan"
    assert scan["status"] == "repo_scan_proof_landed_live_and_owner_tail_open"
    assert scan["closes_evidence_tail"] == (
        "physical_source_morphology_scan_beyond_classification_zero_ref"
    )
    assert scan["evidence_ref"] == (
        "contracts/functional_privatization_audit.json#/physical_source_morphology_scan"
    )
    assert set(scan["scan_scope"]) == {
        "agent/",
        "contracts/",
        "runtime/authority_functions/",
        "src/",
        "tests/standard_agent_purity_helpers.py",
    }
    assert scan["observed_counts"] == {
        "active_private_generic_residue_count": 0,
        "repo_local_wrapper_tail_count": 0,
        "default_caller_count": 0,
        "runtime_package_residue_count": 0,
        "functional_structure_gap_count": 0,
        "classification_gap_count": 0,
        "functional_module_total_count": 15,
    }
    assert scan["proof_assertions"] == {
        "generic_runtime_owner_in_active_src": False,
        "generated_surface_owner_in_domain_repo": False,
        "repo_local_wrapper_tail_in_default_caller": False,
        "history_detail_in_default_read_model": False,
        "physical_delete_authorized": False,
        "domain_projection_policy": "refs_receipts_blockers_only_no_body_verdict_or_blob",
    }
    assert {
        "direct_or_hosted_generated_surface_production_consumption_ref",
        "physical_retirement_owner_decision_ref",
        "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref",
        "long_soak_negative_conformance_ref",
    } <= set(scan["does_not_close"])
    assert scan["completion_boundary"] == {
        "scan_proof_repo_backed": True,
        "production_consumption_proven": False,
        "physical_retirement_owner_decision_present": False,
        "live_owner_or_stable_blocker_scaleout_complete": False,
        "provider_or_operator_long_soak_complete": False,
        "completion_claim_authorized": False,
    }


def test_smoke_lane_files_do_not_perform_subprocess_or_repo_root_writes() -> None:
    manifest = _test_lane_manifest()

    for path in manifest["lanes"]["smoke"]["paths"]:
        tree = ast.parse(_read(path), filename=path)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert "subprocess" not in imported_modules | imported_from_modules
        assert ".sentrux" not in _read(path)


def _assert_ref_paths_exist(refs: list[str]) -> None:
    for ref in refs:
        path = ref.split("#", maxsplit=1)[0]
        assert (REPO_ROOT / path).exists(), ref


def test_mas_entry_boundary_lane_is_thin_ref_surface() -> None:
    lane = _test_lane_manifest()["focused_lanes"]["mas-entry-boundary"]

    assert set(lane) == {
        "kind",
        "paths",
        "docs",
        "overlap_policy",
        "authority_boundary",
        "source_of_truth",
        "policy_refs",
    }
    assert lane["kind"] == "focused_mas_entry_docs_contract_gate"
    assert lane["overlap_policy"] == "allowed_with_regression"
    assert (
        lane["authority_boundary"]
        == "entry_projection_and_controlled_domain_handler_bridge_no_study_truth_authority"
    )

    for path in lane["paths"] + lane["docs"]:
        assert (REPO_ROOT / path).exists(), path
    _assert_ref_paths_exist(lane["source_of_truth"] + lane["policy_refs"])
    assert "family_runtime_framework" not in lane
    assert "domain_handler_bridge" not in lane
    assert "forbidden_authority_writes" not in lane


def test_mas_functional_consumer_lane_is_thin_ref_surface() -> None:
    lane = _test_lane_manifest()["focused_lanes"]["mas-functional-consumer-followthrough"]

    assert set(lane) == {
        "kind",
        "paths",
        "docs",
        "overlap_policy",
        "authority_boundary",
        "source_of_truth",
        "policy_refs",
    }
    assert lane["kind"] == "focused_mas_functional_consumer_boundary_gate"
    assert lane["authority_boundary"] == "opl_consumed_generic_surfaces_mas_domain_authority_pack_only"

    for path in lane["paths"] + lane["docs"]:
        assert (REPO_ROOT / path).exists(), path
    _assert_ref_paths_exist(lane["source_of_truth"] + lane["policy_refs"])
    assert "declarative_pack_compiler_input" not in lane
    assert "generated_surface_handoff" not in lane
    assert "minimal_authority_function_manifest" not in lane
    assert "standard_agent_purity_guard" not in lane
