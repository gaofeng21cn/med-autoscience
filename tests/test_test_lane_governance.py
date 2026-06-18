from __future__ import annotations

import ast
import importlib
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
    assert dispositions_by_id["owner_route_reconcile_materialize_dispatch_shell"] == (
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


def test_mas_entry_boundary_lane_freezes_sidecar_skill_mcp_and_docs_contract() -> None:
    lane = _test_lane_manifest()["focused_lanes"]["mas-entry-boundary"]

    assert lane["kind"] == "focused_mas_entry_docs_contract_gate"
    assert lane["overlap_policy"] == "allowed_with_regression"
    assert lane["authority_boundary"] == "entry_projection_and_controlled_domain_handler_bridge_no_study_truth_authority"
    assert lane["implementation_status"] == "landed_docs_contract"
    assert lane["machine_truth_surface"] == "contracts/test-lane-manifest.json"

    for path in lane["paths"] + lane["docs"]:
        assert (REPO_ROOT / path).exists(), path

    assert lane["docs"] == [
        "docs/status.md",
        "docs/architecture.md",
        "docs/runtime/control/controllers.md",
    ]
    assert lane["docs_boundary"] == {
        "markdown_prose_as_machine_truth_allowed": False,
        "docs_role": "human_navigation_and_boundary_explanation_only",
        "contract_lane": "focused_lanes.mas-entry-boundary",
    }

    framework = lane["family_runtime_framework"]
    assert framework["owner"] == "one-person-lab"
    assert framework["framework_role"] == "codex_first_stage_led_provider_backed_runtime_framework"
    assert framework["stage_semantics"] == "human_expert_large_task_stage"
    assert framework["minimal_executor"] == "Codex CLI"
    assert framework["provider_abstraction"] == "opl_family_runtime_provider"
    assert framework["target_production_provider"] == "Temporal"
    assert "legacy_optional_providers" not in framework
    assert framework["optional_executor_adapters"] == [
        {
            "adapter_id": "hermes_agent",
            "display_name": "Hermes-Agent",
            "classification": "explicit_optional_executor_adapter",
            "default_provider": False,
        }
    ]
    assert framework["role"] == "stage_attempt_queue_wakeup_retry_dead_letter_human_gate_receipt_projection_transport"
    assert set(framework["not_authority_for"]) == {
        "study_truth",
        "publication_quality",
        "quality_gate",
        "artifact_authority",
        "paper_package",
    }

    domain_handler = lane["domain_handler_bridge"]
    assert domain_handler["export_command"] == "medautosci domain-handler export --profile <profile> --format json"
    assert domain_handler["dispatch_command"] == "medautosci domain-handler dispatch --task <task.json> --format json"
    assert domain_handler["export_surface_kind"] == "mas_family_domain_handler_export"
    assert domain_handler["dispatch_receipt_surface_kind"] == "mas_family_domain_handler_dispatch_receipt"
    assert domain_handler["bridge_policy"] == "controlled_bridge_to_mas_owner_surface"
    assert domain_handler["allowed_bridge_writes"] == [
        "runtime/artifacts/opl_family_domain_handler/dispatch_receipts/*.json",
    ]
    assert "domain_route/reconcile-apply" in domain_handler["allowed_task_kinds"]
    assert "notification/receipt" in domain_handler["allowed_task_kinds"]

    projections = lane["entry_projection_surfaces"]
    assert projections["action_catalog"] == "med_autoscience.action_catalog family_action_catalog"
    assert projections["mcp"] == "med_autoscience.mcp_server build_tool_manifest action_catalog_projection"
    assert projections["skill"] == "plugins/mas/skills/mas/SKILL.md"
    assert projections["plugin_manifest"] == "plugins/mas/.codex-plugin/plugin.json"
    assert (REPO_ROOT / projections["skill"]).exists()
    assert (REPO_ROOT / projections["plugin_manifest"]).exists()
    assert lane["projection_only_surfaces"] == [
        "MCP tool descriptors",
        "action_catalog projections",
        "OPL generated Skill descriptor targeting MAS domain entry",
        "product-entry manifest domain action intent metadata",
    ]
    assert lane["truth_owner"] == "MedAutoScience"
    assert set(lane["forbidden_authority_writes"]) >= {
        "study_truth",
        "progress_projection",
        "domain_health_diagnostic",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "paper/current_package",
        "manuscript/current_package",
        "quality_ready",
        "publication_ready",
        "submission_ready",
        "artifact_gate_override",
    }


def test_mas_functional_consumer_lane_freezes_generic_surface_handoff() -> None:
    lane = _test_lane_manifest()["focused_lanes"]["mas-functional-consumer-followthrough"]

    assert lane["kind"] == "focused_mas_functional_consumer_boundary_gate"
    assert lane["authority_boundary"] == "opl_consumed_generic_surfaces_mas_domain_authority_pack_only"
    assert lane["implementation_status"] == "functional_consumer_standard_agent_source_shape_landed"
    assert lane["machine_truth_surface"] == "contracts/test-lane-manifest.json"
    assert lane["generic_surface_owner"] == "one-person-lab"
    assert lane["default_scheduler_owner"] == "opl_current_control_state"
    assert lane["live_soak_required_for_this_lane"] is False

    for path in lane["paths"] + lane["docs"]:
        assert (REPO_ROOT / path).exists(), path

    assert lane["mas_does_not_own"] == [
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_transition_runner",
        "generic_workbench",
        "generic_memory_locator",
        "generic_artifact_lifecycle",
        "generic_observability",
    ]
    assert set(lane["mas_domain_authority_surfaces"]) == {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "domain_transition_table",
        "owner_receipt",
        "typed_blocker",
        "safe_action_refs",
    }

    pack_input = lane["declarative_pack_compiler_input"]
    assert pack_input["surface_kind"] == "mas_declarative_pack_compiler_input"
    assert pack_input["compiler_owner"] == "one-person-lab"
    assert pack_input["pack_id"] == "mas-medical-research-pack"
    assert [item["input_id"] for item in pack_input["input_refs"]] == [
        "domain_descriptor",
        "stage_graph",
        "action_intents",
        "domain_transition_table",
        "publication_route_memory_policy",
        "artifact_authority_policy",
        "source_readiness_policy",
        "receipt_schema",
        "no_forbidden_write_contract",
    ]
    assert pack_input["compiler_outputs_expected"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_handler",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    assert pack_input["mas_long_term_code_owner"] == "minimal_authority_functions_only"
    assert pack_input["must_not_generate_or_claim_domain_authority"] is True
    generated = lane["generated_surface_handoff"]
    assert generated["surface_kind"] == "mas_generated_surface_handoff"
    assert generated["generated_surface_owner"] == "one-person-lab"
    assert generated["current_mas_role"] == "domain_handler_and_refs_projection_source"
    assert generated["long_term_mas_owner"] is False
    assert generated["mas_handwritten_shell_expansion_allowed"] is False
    generated_by_id = {item["surface_id"]: item for item in generated["handoff_surfaces"]}
    assert set(generated_by_id) == {
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "domain_handler",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    }
    assert generated_by_id["cli"]["target_role"] == "opl_generated_command_surface"
    assert generated_by_id["mcp"]["target_role"] == "opl_generated_mcp_descriptor_surface"
    assert generated_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert generated_by_id["product_entry"]["target_role"] == "opl_generated_product_entry_surface"
    assert generated_by_id["domain_handler"]["target_role"] == "opl_generated_domain_handler_handoff_surface"
    assert generated_by_id["status"]["target_role"] == "opl_generated_status_wrapper_over_mas_truth_refs"
    assert generated_by_id["workbench"]["target_role"] == (
        "opl_hosted_workbench_shell_consuming_mas_refs"
    )
    assert generated_by_id["projection_shell"]["target_role"] == "opl_generated_projection_shell"
    assert generated_by_id["test_lane_harness"]["target_role"] == (
        "opl_generated_harness_consumer_over_mas_pack"
    )

    consumer_migration = importlib.import_module(
        "med_autoscience.controllers.opl_unique_control_plane_boundary_parts.consumer_migration"
    )
    runtime_boundary = consumer_migration.build_functional_consumer_boundary()

    assert runtime_boundary["declarative_pack_compiler_input"] == lane[
        "declarative_pack_compiler_input"
    ]
    assert runtime_boundary["generated_surface_handoff"] == lane["generated_surface_handoff"]

    minimal_authority = lane["minimal_authority_function_manifest"]
    assert minimal_authority["function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    assert minimal_authority["function_count"] == 7
    assert minimal_authority["forbidden_mechanical_decision_surfaces"] == [
        "script_exit_code_as_publication_quality_verdict",
        "function_return_value_as_ai_reviewer_quality_decision",
        "test_pass_as_artifact_mutation_authorization",
        "queue_completion_as_publication_route_memory_accept_reject",
        "file_presence_as_source_readiness_verdict",
    ]
    independent_policy = minimal_authority["independent_executor_reviewer_agent_policy"]
    assert independent_policy["required"] is True
    assert independent_policy["separate_invocation_required"] is True
    assert independent_policy["separate_context_record_required"] is True
    assert independent_policy["separate_task_record_required"] is True
    assert independent_policy["separate_receipt_required"] is True
    assert independent_policy["self_review_closes_quality_gate"] is False
    assert independent_policy["codex_cli_may_serve_both_roles_only_as_separate_invocations"] is True
    boundary_by_id = {
        item["boundary_id"]: item for item in minimal_authority["stage_quality_gate_boundaries"]
    }
    assert set(boundary_by_id) == set(minimal_authority["boundary_ids"])
    assert boundary_by_id["publication_quality_stage_gate_boundary"]["program_role"] == "validator"
    assert boundary_by_id["artifact_mutation_stage_gate_boundary"]["program_role"] == "materializer"
    assert boundary_by_id[
        "publication_route_memory_accept_reject_stage_gate_boundary"
    ]["program_role"] == "guard"
    for item in boundary_by_id.values():
        assert item["requires_ai_first_record"] is True
        assert item["route_back_semantics"].startswith("route_back_to_")
        assert item["typed_blocker_semantics"].endswith("_blocker")
        assert item["required_record_refs"]
        assert any(
            "stage_quality_pack:" in ref
            or ref in {"AI reviewer workflow", "AI reviewer-backed publication eval"}
            for ref in item["trace_refs"]
        )
    assert minimal_authority["all_other_program_surfaces"] == "opl_generated_or_domain_refs_projection_source"
    assert minimal_authority["forbidden_long_term_mas_shell_owners"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_handler",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]

    classification = lane["functional_surface_classification"]
    assert set(classification) == {
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    }
    assert classification["declarative_pack_generated_surface"] == [
        "workspace_source_intake_shell",
        "workbench_portal_generic_shell",
        "owner_route_reconcile_materialize_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter",
        "generic_transition_runner",
    ]
    assert classification["domain_authority_refs"] == [
        "domain_authority_refs_index",
        "paper_progress_transition_refs",
        "runtime_storage_maintenance",
        "publication_route_memory_locator_transport_shell",
        "artifact_lifecycle_storage_audit_shell",
    ]
    assert set(classification["minimal_authority_function"]) == set(lane["mas_domain_authority_surfaces"]) | {
        "progress_projection",
        "domain_health_diagnostic",
        "ai_reviewer_workflow",
        "publication_gate",
    }
    assert "legacy_cleanup_no_active_caller_gate" not in classification
    assert "legacy_cleanup_tombstone_provenance" not in classification
    assert "legacy_cleanup_physical_retired" not in classification
    assert lane["functional_module_inventory_ref"] == (
        "product_entry_manifest.functional_consumer_boundary.functional_module_inventory"
    )
    assert lane["functional_module_inventory_expected_count"] == 15
    assert lane["functional_module_inventory_required_fields"] == [
        "module_id",
        "classification",
        "code_paths",
        "domain_ref_consumers",
        "current_ref_status",
        "migration_action",
    ]
    assert runtime_boundary["declarative_pack_compiler_input"] == pack_input
    assert runtime_boundary["generated_surface_handoff"] == generated
    assert runtime_boundary["minimal_authority_function_manifest"] == minimal_authority
    assert runtime_boundary["functional_surface_classification"] == lane[
        "functional_surface_classification"
    ]
    assert runtime_boundary["functional_module_inventory_summary"] == lane[
        "functional_module_inventory_summary"
    ]
    assert runtime_boundary["functional_followthrough_gap_summary"] == lane[
        "functional_followthrough_gap_summary"
    ]
    assert runtime_boundary["standard_agent_purity_guard"] == lane["standard_agent_purity_guard"]
    assert runtime_boundary["opl_functional_harness_consumer_coverage"] == lane[
        "opl_functional_harness_consumer_coverage"
    ]
    assert runtime_boundary["domain_authority_refs_index_role"] == lane[
        "domain_authority_refs_index_role"
    ]

    classification = lane["functional_surface_classification"]
    assert set(classification) == {
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    }
    assert set(classification) == set(lane["functional_module_inventory_classification_allowed_values"])

    inventory = runtime_boundary["functional_module_inventory"]
    assert lane["functional_module_inventory_expected_count"] == 15
    assert len(inventory) == 15
    assert sorted(item["module_id"] for item in inventory) == sorted(
        lane["functional_module_inventory_expected_modules"]
    )
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert "local_launchd_scheduler_install_path" not in inventory_by_id
    assert "workspace_local_watch_service_wrappers" not in inventory_by_id
    assert "domain_health_diagnostic_loop_shell" not in inventory_by_id
    assert inventory_by_id["domain_authority_refs_index"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/opl_state_index_source_adapter.py",
        "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
        "src/med_autoscience/opl_domain_pack/",
        "src/med_autoscience/controllers/owner_route_handoff_parts/substrate_adapter.py",
    ]
    assert set(inventory_by_id["domain_authority_refs_index"]["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_runtime_lifecycle_owner",
        "generic_restore_retention_owner",
    }
    assert inventory_by_id["paper_progress_transition_refs"]["classification"] == "domain_authority_refs"
    assert inventory_by_id["publication_quality_verdict"]["cannot_absorb_reason"] == (
        "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts."
    )
    assert inventory_by_id["artifact_authority"]["migration_action"] == "authority_stays_in_mas"
    owner_dispatch_thinning = inventory_by_id[
        "owner_route_reconcile_materialize_dispatch_shell"
    ]["latest_thinning_evidence"]
    assert owner_dispatch_thinning["status"] == (
        "default_executor_action_policy_single_source_landed"
    )
    assert owner_dispatch_thinning["policy_module"] == (
        "src/med_autoscience/controllers/default_executor_action_policy.py"
    )
    assert owner_dispatch_thinning["domain_repo_physical_delete_authorized"] is False
    assert "owner_chain_closed" in owner_dispatch_thinning["does_not_claim"]
    workbench_thinning = inventory_by_id["workbench_portal_generic_shell"][
        "latest_thinning_evidence"
    ]
    assert workbench_thinning["status"] == (
        "opl_hosted_workbench_projection_and_read_model_materializer_landed"
    )
    materializer_boundary = workbench_thinning["read_model_materializer_boundary"]
    assert materializer_boundary["status"] == "domain_owned_read_model_materializer_no_active_workspace_helper"
    assert materializer_boundary["hosted_package_role"] == "read_model_projection_package"
    assert materializer_boundary["hosted_package_truth_role"] == "projection_only_no_workspace_runtime_truth"
    assert materializer_boundary["physical_module"] == (
        "src/med_autoscience/controllers/progress_portal_parts/read_model_materializer.py"
    )
    assert materializer_boundary["domain_repo_physical_delete_authorized"] is False
    assert materializer_boundary["active_callers"] == []
    assert "runtime_control_owner" in materializer_boundary["does_not_claim"]
    assert "read-model evidence" in materializer_boundary["retention_reason"]
    assert "workspace_carrier_boundary" not in workbench_thinning

    summary = runtime_boundary["functional_module_inventory_summary"]
    assert summary["classification_counts"] == {
        "declarative_pack_generated_surface": 7,
        "domain_authority_refs": 5,
        "minimal_authority_function": 3,
    }
    assert summary["classification_gap_count"] == 0
    assert summary["functional_structure_gap_count"] == 0
    assert summary["active_private_generic_residue_count"] == 0
    assert summary["repo_local_wrapper_tail_count"] == 0
    assert summary["source_purity_cutover_status"] == "standard_agent_source_shape_landed"

    purity = runtime_boundary["standard_agent_purity"]
    assert purity["status"] == "standard_agent_source_shape_landed"
    assert purity["active_private_generic_residue_count"] == 0
    assert purity["default_caller_count"] == 0
    assert purity["default_caller_readiness_status"] == "opl_generated_default_caller_ready"
    assert purity["source_purity_cutover_status"] == "standard_agent_source_shape_landed"
    assert purity["repo_local_wrapper_tail_count"] == 0
    assert purity["domain_repo_physical_delete_authorized"] is False
    assert purity["runtime_package_residue_count"] == 0
    assert "active_compatibility_aliases" not in purity
    assert purity["retired_alias_residue_refs"] == []
    assert purity["history_detail_in_default_read_model"] is False
    assert purity["domain_projection_policy"] == (
        "refs_receipts_blockers_only_no_body_verdict_or_blob"
    )
    assert "mas_owned_generic_queue" in purity["forbidden_active_claims"]

    followthrough = runtime_boundary["functional_followthrough_gap_summary"]
    assert followthrough["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert followthrough["classification_gap_count"] == 0
    assert followthrough["functional_structure_gap_count"] == 0
    assert followthrough["remaining_functional_followthrough_gate_ids"] == []
    assert "standard_agent_purity_guard" in followthrough["closed_functional_structure_gate_ids"]
    assert followthrough["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]

    assert lane["standard_agent_purity_guard"] == {
        "status": "standard_agent_purity_cutover_guard",
        "default_caller_count": 0,
        "default_manager": "opl",
        "default_caller_readiness_status": "opl_generated_default_caller_ready",
        "source_purity_cutover_status": "standard_agent_source_shape_landed",
        "repo_local_wrapper_tail_count": 0,
        "repo_local_wrapper_tail_module_ids": [],
        "former_repo_local_wrapper_tail_module_ids": [
            "generic_cli_mcp_product_wrappers",
            "owner_route_reconcile_materialize_dispatch_shell",
            "workbench_portal_generic_shell",
        ],
        "domain_repo_physical_delete_authorized": False,
        "runtime_package_residue_count": 0,
        "retired_alias_residue_refs": [],
        "proof_items": [
            "standard_agent_purity.active_private_generic_residue_count=0",
            "standard_agent_purity.default_caller_count=0",
            "standard_agent_purity.retired_alias_residue_refs=[]",
            "standard_agent_purity.default_caller_readiness_status=opl_generated_default_caller_ready",
            "standard_agent_purity.source_purity_cutover_status=standard_agent_source_shape_landed",
            "standard_agent_purity.domain_projection_policy=refs_receipts_blockers_only_no_body_verdict_or_blob",
        ],
    }
    assert "standard_agent_purity" in lane
    assert lane["standard_agent_purity_guard_required"] == [
        "standard_agent_purity.active_private_generic_residue_count=0",
        "standard_agent_purity.default_caller_count=0",
        "standard_agent_purity.retired_alias_residue_refs=[]",
        "standard_agent_purity.default_caller_readiness_status=opl_generated_default_caller_ready",
        "standard_agent_purity.source_purity_cutover_status=standard_agent_source_shape_landed",
        "standard_agent_purity.history_detail_in_default_read_model=false",
        "domain_handler_exports_standard_agent_purity",
        "product_entry_manifest_exports_standard_agent_purity",
        "observability_export_consumed_as_refs_only",
        "focused_tests_green",
    ]

    assert lane["required_projection_surfaces"] == [
        "product_entry_manifest.functional_consumer_boundary",
        "product_entry_manifest.functional_consumer_boundary.standard_agent_purity",
        "product_entry_manifest.functional_consumer_boundary.declarative_pack_compiler_input",
        "product_entry_manifest.functional_consumer_boundary.generated_surface_handoff",
        "product_entry_manifest.functional_consumer_boundary.minimal_authority_function_manifest",
        "domain_handler_export.functional_consumer_boundary",
        "domain_handler_export.functional_consumer_boundary.standard_agent_purity",
        "domain_handler_export.functional_consumer_boundary.declarative_pack_compiler_input",
        "domain_handler_export.functional_consumer_boundary.generated_surface_handoff",
        "domain_handler_export.functional_consumer_boundary.minimal_authority_function_manifest",
        "opl_unique_control_plane_boundary.consumer_migration.functional_consumer_boundary",
        "family_contract_adoption.runtime_observability_export",
    ]
    assert set(lane["forbidden_runtime_regressions"]) == {
        "mas_default_generic_scheduler",
        "mas_resident_generic_daemon",
        "mas_owned_generic_queue",
        "mas_owned_attempt_ledger",
        "mas_generic_transition_runner",
        "mas_generic_workbench_shell",
    }
