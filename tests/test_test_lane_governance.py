from __future__ import annotations

import ast
import importlib
import json
import re
from pathlib import Path

import pytest


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

    for lane in manifest["lanes"].values():
        for path in lane.get("paths", []):
            assert (REPO_ROOT / path).exists(), path
    assert " ".join(manifest["lanes"]["smoke"]["paths"]) in makefile


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
    assert lane["authority_boundary"] == "entry_projection_and_controlled_sidecar_bridge_no_study_truth_authority"
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

    sidecar = lane["sidecar_bridge"]
    assert sidecar["export_command"] == "medautosci sidecar export --profile <profile> --format json"
    assert sidecar["dispatch_command"] == "medautosci sidecar dispatch --task <task.json> --format json"
    assert sidecar["export_surface_kind"] == "mas_family_sidecar_export"
    assert sidecar["dispatch_receipt_surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert sidecar["bridge_policy"] == "controlled_bridge_to_mas_owner_surface"
    assert sidecar["allowed_bridge_writes"] == [
        "artifacts/runtime/opl_family_sidecar/dispatch_receipts/*.json",
    ]
    assert "runtime_supervisor/reconcile-apply" in sidecar["allowed_task_kinds"]
    assert "notification/receipt" in sidecar["allowed_task_kinds"]

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
        "study_runtime_status",
        "runtime_watch",
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
    assert lane["implementation_status"] == "landed_functional_consumer_guard"
    assert lane["machine_truth_surface"] == "contracts/test-lane-manifest.json"
    assert lane["generic_surface_owner"] == "one-person-lab"
    assert lane["default_scheduler_owner"] == "opl_provider_runtime_manager"
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
    assert set(lane["mas_retains"]) == {
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
        "sidecar",
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
    assert generated["current_mas_role"] == "handwritten_migration_bridge"
    assert generated["long_term_mas_owner"] is False
    assert generated["mas_handwritten_shell_expansion_allowed"] is False
    generated_by_id = {item["surface_id"]: item for item in generated["handoff_surfaces"]}
    assert set(generated_by_id) == set(pack_input["compiler_outputs_expected"])
    assert generated_by_id["cli"]["target_role"] == "opl_generated_command_surface"
    assert generated_by_id["mcp"]["target_role"] == "opl_generated_mcp_descriptor_surface"
    assert generated_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert generated_by_id["product_entry"]["target_role"] == "opl_generated_product_entry_surface"
    assert generated_by_id["sidecar"]["target_role"] == "opl_generated_sidecar_handoff_surface"
    assert generated_by_id["status"]["target_role"] == "opl_generated_status_wrapper_over_mas_truth_refs"
    assert generated_by_id["workbench"]["target_role"] == (
        "opl_hosted_workbench_shell_consuming_mas_refs"
    )
    assert generated_by_id["projection_shell"]["target_role"] == "opl_generated_projection_shell"
    assert generated_by_id["test_lane_harness"]["target_role"] == (
        "opl_generated_harness_consumer_over_mas_pack"
    )
    consumer_migration = importlib.import_module(
        "med_autoscience.controllers.supervision_scheduler_parts.consumer_migration"
    )
    runtime_boundary = consumer_migration.build_functional_consumer_boundary()
    minimal_authority = runtime_boundary["minimal_authority_function_manifest"]
    assert minimal_authority["surface_kind"] == "mas_minimal_authority_function_manifest"
    assert minimal_authority["semantic_model"] == (
        "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
    )
    assert minimal_authority["requires_ai_first_record"] is True
    assert minimal_authority["boundary_ids"] == [
        "publication_quality_stage_gate_boundary",
        "ai_reviewer_quality_stage_gate_boundary",
        "artifact_mutation_stage_gate_boundary",
        "publication_route_memory_accept_reject_stage_gate_boundary",
        "source_readiness_stage_gate_boundary",
    ]
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
    assert minimal_authority["all_other_program_surfaces"] == "opl_generated_or_migration_bridge"
    assert minimal_authority["forbidden_long_term_mas_shell_owners"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    classification = lane["functional_surface_classification"]
    assert classification["declarative_pack_generated_surface"] == [
        "workspace_source_intake_shell",
        "workbench_portal_generic_shell",
        "runtime_supervisor_scan_consume_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter",
        "generic_transition_runner",
    ]
    assert classification["refs_only_adapter"] == [
        "runtime_lifecycle_sqlite_reference_adapter",
        "paper_work_unit_outbox_index",
        "runtime_storage_maintenance",
        "publication_route_memory_locator_transport_shell",
        "artifact_lifecycle_storage_audit_shell",
        "terminal_attach_transport",
    ]
    assert set(classification["minimal_authority_function"]) == set(lane["mas_retains"]) | {
        "study_runtime_status",
        "runtime_watch_domain_health",
        "ai_reviewer_workflow",
        "publication_gate",
    }
    assert set(classification["legacy_cleanup_no_active_caller_gate"]) == {
        "local_launchd_scheduler_install_path",
        "workspace_local_watch_service_wrappers",
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_without_active_caller",
    }
    assert lane["functional_module_inventory_ref"] == (
        "product_entry_manifest.functional_consumer_boundary.functional_module_inventory"
    )
    assert lane["functional_module_inventory_expected_count"] == 18
    assert lane["functional_module_inventory_required_fields"] == [
        "module_id",
        "classification",
        "code_paths",
        "active_callers",
        "active_caller_status",
        "migration_action",
    ]
    assert runtime_boundary["declarative_pack_compiler_input"] == pack_input
    assert runtime_boundary["generated_surface_handoff"] == generated
    assert runtime_boundary["minimal_authority_function_manifest"]["function_ids"] == lane[
        "minimal_authority_function_manifest"
    ]["function_ids"]
    assert runtime_boundary["minimal_authority_function_manifest"] == minimal_authority
    inventory = runtime_boundary["functional_module_inventory"]
    assert len(inventory) == 18
    assert sorted(item["module_id"] for item in inventory) == sorted(
        lane["functional_module_inventory_expected_modules"]
    )
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
        "src/med_autoscience/runtime_protocol/study_runtime.py",
        "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
    ]
    assert set(inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert inventory_by_id["paper_work_unit_outbox_index"]["classification"] == "refs_only_adapter"
    assert inventory_by_id["paper_work_unit_outbox_index"]["migration_action"] == (
        "keep_paper_work_unit_refs_only_adapter_and_declare_queue_attempt_requirements"
    )
    assert inventory_by_id["runtime_supervisor_scan_consume_dispatch_shell"]["active_caller_status"] == (
        "opl_runtime_manager_loop_consumed_mas_owner_route_guard_active"
    )
    closed_semantic_equivalence_modules = [
        "runtime_storage_maintenance",
        "artifact_lifecycle_storage_audit_shell",
        "workbench_portal_generic_shell",
        "runtime_supervisor_scan_consume_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_queue_attempt_retry_dead_letter",
    ]
    for module_id in closed_semantic_equivalence_modules:
        entry = inventory_by_id[module_id]
        readout = " ".join(
            str(entry.get(field, ""))
            for field in (
                "active_caller_status",
                "migration_action",
                "authority_boundary",
            )
        )
        assert not re.search(
            r"active_private|pending|should_move|should_derive|handoff_required|until_opl|lifecycle_candidate|mixed_generic",
            readout,
            flags=re.IGNORECASE,
        ), module_id
        assert entry["proof_refs"], module_id
        assert entry["opl_expected_primitives"], module_id
    assert inventory_by_id["publication_quality_verdict"]["cannot_absorb_reason"] == (
        "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts."
    )
    assert inventory_by_id["artifact_authority"]["migration_action"] == "retain_in_mas"
    assert inventory_by_id["local_launchd_scheduler_install_path"]["active_caller_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert inventory_by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["trigger_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["write_install_proof_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["classification"] == (
        "legacy_cleanup_no_active_caller_gate"
    )
    assert inventory_by_id["local_launchd_scheduler_install_path"]["no_active_caller_gate"][
        "default_caller_count"
    ] == 0
    assert inventory_by_id["workspace_local_watch_service_wrappers"]["tombstone_required"] is True
    assert runtime_boundary["functional_module_inventory_summary"]["classification_counts"] == {
        "declarative_pack_generated_surface": 7,
        "refs_only_adapter": 6,
        "minimal_authority_function": 3,
        "legacy_cleanup_no_active_caller_gate": 2,
    }
    assert runtime_boundary["functional_module_inventory_summary"]["classification_gap_count"] == 0
    assert runtime_boundary["functional_module_inventory_summary"]["functional_structure_gap_count"] == 5
    assert runtime_boundary["functional_module_inventory_summary"]["active_private_generic_residue_count"] == 0
    assert (
        runtime_boundary["functional_module_inventory_summary"]["remaining_gap_classification"]
        == "functional_followthrough_and_test_evidence_gates"
    )
    assert runtime_boundary["functional_module_inventory_summary"][
        "long_term_opl_owned_replacement_count"
    ] == 0
    assert runtime_boundary["functional_module_inventory_summary"][
        "retire_tombstone_classification_count"
    ] == 0
    followthrough_summary = runtime_boundary["functional_followthrough_gap_summary"]
    assert followthrough_summary["status"] == "classification_closed_followthrough_gaps_open"
    assert followthrough_summary["classification_gap_count"] == 0
    assert followthrough_summary["functional_structure_gap_count"] == 5
    assert followthrough_summary["active_private_generic_residue_count"] == 0
    assert followthrough_summary["remaining_gap_classification"] == (
        "functional_followthrough_and_test_evidence_gates"
    )
    assert followthrough_summary["remaining_items_are_evidence_gates"] is False
    assert followthrough_summary["legacy_cleanup_items_are_remaining_active_gaps"] is True
    assert followthrough_summary["legacy_cleanup_items_have_default_entry"] is False
    assert followthrough_summary["legacy_cleanup_items_have_standard_template_refs"] is False
    assert followthrough_summary["remaining_functional_followthrough_gate_ids"] == [
        "generated_surface_active_caller_cutover",
        "refs_only_adapter_thinning",
        "legacy_cleanup_physical_retirement",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
    ]
    assert followthrough_summary["does_not_clear"] == (
        followthrough_summary["remaining_functional_followthrough_gate_ids"]
    )
    assert followthrough_summary["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]
    assert {item["functional_structure_gap"] for item in followthrough_summary["remaining_evidence_gates"]} == {
        False
    }
    assert set(followthrough_summary["cleared_by_surfaces"]) == {
        "functional_module_inventory",
        "declarative_pack_compiler_input",
        "generated_surface_handoff",
        "minimal_authority_function_manifest",
        "no_active_caller_proof",
        "opl_functional_harness_consumer_coverage",
    }
    lifecycle_role = lane["runtime_lifecycle_sqlite_role"]
    assert lifecycle_role["classification"] == "refs_only_adapter"
    assert lifecycle_role["current_mas_role"] == "domain_sidecar_index_reference_adapter"
    assert lifecycle_role["authority"] == "refs_only_index_not_generic_persistence_engine"
    assert lifecycle_role["owner"] == "one-person-lab"
    assert lifecycle_role["mas_may_claim_generic_persistence_engine"] is False
    assert lifecycle_role["mas_consumes_opl_lifecycle_index_refs"] is True
    assert lifecycle_role["mas_may_write_domain_truth"] is False
    assert set(lifecycle_role["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert lifecycle_role["replacement_expectation"]["audit_ref"] == (
        "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough"
    )
    assert lane["no_active_caller_proof"]["default_caller_count"] == 0
    assert lane["no_active_caller_proof"]["default_manager"] == "opl"
    assert lane["no_active_caller_proof"]["forbidden_default_callers"] == [
        "cli_default_local_scheduler_install",
        "workspace_bootstrap_local_scheduler_install",
        "product_entry_local_scheduler_install",
        "sidecar_local_scheduler_install",
        "mcp_local_scheduler_install",
    ]
    assert "workspace_bootstrap_manager_is_opl" in lane["no_active_caller_proof"]["proof_items"]
    cleanup_only = lane["legacy_local_scheduler_cleanup_only_proof"]
    assert cleanup_only["install_allowed"] is False
    assert cleanup_only["trigger_allowed"] is False
    assert cleanup_only["write_install_proof_allowed"] is False
    assert cleanup_only["default_cli_exposes_local_install"] is False
    assert cleanup_only["default_bootstrap_exposes_local_install"] is False
    assert cleanup_only["remaining_physical_delete_blockers"] == [
        "legacy_launchagent_or_tick_script_may_exist_on_operator_machines",
        "explicit_status_remove_cleanup_path_still_needed_until_artifacts_absent",
        "provenance_and_regression_fixtures_still_assert_tombstone_behavior",
    ]
    assert lane["required_projection_surfaces"] == [
        "product_entry_manifest.functional_consumer_boundary",
        "product_entry_manifest.functional_consumer_boundary.declarative_pack_compiler_input",
        "product_entry_manifest.functional_consumer_boundary.generated_surface_handoff",
        "product_entry_manifest.functional_consumer_boundary.minimal_authority_function_manifest",
        "sidecar_export.functional_consumer_boundary",
        "sidecar_export.functional_consumer_boundary.declarative_pack_compiler_input",
        "sidecar_export.functional_consumer_boundary.generated_surface_handoff",
        "sidecar_export.functional_consumer_boundary.minimal_authority_function_manifest",
        "supervision_scheduler.consumer_migration.functional_consumer_boundary",
        "family_contract_adoption.runtime_observability_export",
    ]
    coverage = lane["opl_functional_harness_consumer_coverage"]
    assert coverage["status"] == "landed_domain_authority_pack_consumer"
    assert coverage["coverage_items"] == [
        "refs_only_memory_writeback_chain",
        "queue_stage_attempt_typed_closeout",
        "generic_transition_runner",
        "restart_dead_letter_repair_human_gate_state_chain",
    ]
    assert coverage["opl_harness_pass_is_paper_closure"] is False
    assert coverage["opl_harness_pass_is_publication_ready"] is False
    assert coverage["mas_owns_generic_runtime"] is False
    assert set(coverage["mas_retains_domain_authority_pack"]) == set(lane["mas_retains"])
    observability = lane["opl_consumed_observability_surface"]
    assert observability["owner"] == "one-person-lab"
    assert observability["surface"] == "opl runtime observability-export"
    assert observability["authority"] == "read_only_non_authoritative"
    assert set(observability["mas_consumes"]) == {
        "source_refs",
        "freshness",
        "owner_split",
        "domain_owned_projection_refs",
        "owner_receipt_refs",
        "typed_blocker_refs",
    }
    assert set(observability["forbidden_mas_interpretations"]) == {
        "domain_action_authorization",
        "executor_switch_authorization",
        "auto_degrade_authorization",
        "domain_truth_write",
        "memory_body_write",
        "publication_quality_verdict",
        "paper_or_artifact_closure",
    }
    assert lane["no_active_caller_proof_required"] == [
        "cli_default_manager_is_opl",
        "local_scheduler_ensure_cleanup_only",
        "sidecar_exports_no_generic_owner",
        "product_entry_manifest_exports_no_generic_owner",
        "observability_export_consumed_as_refs_only",
        "focused_tests_green",
    ]
    assert set(lane["forbidden_runtime_regressions"]) == {
        "mas_default_generic_scheduler",
        "mas_resident_generic_daemon",
        "mas_owned_generic_queue",
        "mas_owned_attempt_ledger",
        "mas_generic_transition_runner",
        "mas_generic_workbench_shell",
    }
