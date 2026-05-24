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
    for lane_id, lane in manifest["focused_lanes"].items():
        for key in ("paths", "docs"):
            for path in lane.get(key, []):
                assert (REPO_ROOT / path).exists(), f"{lane_id} references missing {key}: {path}"
    assert " ".join(manifest["lanes"]["smoke"]["paths"]) in makefile


def test_functional_privatization_cleanup_gate_focused_test_refs_exist() -> None:
    audit = json.loads(_read("contracts/functional_privatization_audit.json"))
    cleanup_gates = audit["functional_consumer_boundary"]["active_path_residue_cleanup_gates"]

    missing_refs = [
        f"{gate['residue_id']}: {path}"
        for gate in cleanup_gates
        for path in gate.get("focused_test_refs", [])
        if path.startswith("tests/") and not (REPO_ROOT / path).exists()
    ]

    assert missing_refs == []


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
    assert "domain_route/owner-handoff" in sidecar["allowed_task_kinds"]
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
    assert lane["implementation_status"] == "landed_functional_consumer_guard_no_resurrection"
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
        "domain_action_adapter",
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
    assert generated["current_mas_role"] == "domain_handler_and_refs_projection_source"
    assert generated["long_term_mas_owner"] is False
    assert generated["mas_handwritten_shell_expansion_allowed"] is False
    generated_by_id = {item["surface_id"]: item for item in generated["handoff_surfaces"]}
    assert set(generated_by_id) == {
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "domain_action_adapter_export_dispatch",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    }
    assert generated_by_id["cli"]["target_role"] == "opl_generated_command_surface"
    assert generated_by_id["mcp"]["target_role"] == "opl_generated_mcp_descriptor_surface"
    assert generated_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert generated_by_id["product_entry"]["target_role"] == "opl_generated_product_entry_surface"
    assert generated_by_id["sidecar"]["target_role"] == "opl_generated_sidecar_handoff_surface"
    assert generated_by_id["domain_action_adapter_export_dispatch"]["current_role"] == (
        "domain_action_adapter"
    )
    assert generated_by_id["domain_action_adapter_export_dispatch"]["target_role"] == (
        "opl_generated_domain_action_adapter_handoff_surface"
    )
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
    assert minimal_authority["all_other_program_surfaces"] == "opl_generated_or_domain_refs_projection_source"
    assert minimal_authority["forbidden_long_term_mas_shell_owners"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_action_adapter",
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
        "owner_route_reconcile_materialize_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter",
        "generic_transition_runner",
    ]
    assert classification["domain_authority_refs"] == [
        "domain_authority_refs_index",
        "paper_work_unit_outbox_index",
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
    assert set(classification["legacy_cleanup_tombstone_provenance"]) == {
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_tombstone_provenance",
    }
    assert set(classification["legacy_cleanup_physical_retired"]) == {
        "local_launchd_scheduler_install_path",
        "domain_health_diagnostic_loop_shell",
        "workspace_local_watch_service_wrappers",
    }
    assert lane["functional_module_inventory_ref"] == (
        "product_entry_manifest.functional_consumer_boundary.functional_module_inventory"
    )
    assert lane["functional_module_inventory_expected_count"] == 18
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
    assert inventory_by_id["domain_authority_refs_index"]["code_paths"] == [
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
    assert inventory_by_id["paper_work_unit_outbox_index"]["classification"] == "domain_authority_refs"
    assert inventory_by_id["paper_work_unit_outbox_index"]["migration_action"] == (
        "declare_paper_work_unit_refs_and_queue_attempt_requirements"
    )
    refs_only_retirement_gates = {
        item["module_id"]: item for item in runtime_boundary["domain_authority_refs_retirement_gates"]
    }
    assert set(refs_only_retirement_gates) == set(classification["domain_authority_refs"])
    for module_id in classification["domain_authority_refs"]:
        gate = inventory_by_id[module_id]["retirement_gate"]
        assert gate == refs_only_retirement_gates[module_id]
        assert gate["classification"] == "domain_authority_refs"
        assert gate["domain_ref_consumer_count"] > 0
        assert gate["domain_ref_consumer_refs"]
        assert gate["generic_owner_claim_allowed"] is False
        assert gate["can_emit_paper_closure_verdict"] is False
        assert gate["can_emit_generic_owner_verdict"] is False
        assert "paper_closure_verdict" in gate["must_not_emit"]
        if module_id == "domain_authority_refs_index":
            assert "domain_authority_refs_replaced_by_opl_generated_ref_index" in gate[
                "delete_or_tombstone_after"
            ]
        else:
            assert gate["delete_or_tombstone_after"]
            assert all("active_caller_count" not in item for item in gate["delete_or_tombstone_after"])
    assert inventory_by_id["owner_route_reconcile_materialize_dispatch_shell"]["current_ref_status"] == (
        "opl_runtime_manager_loop_consumed_mas_owner_route_guard_active"
    )
    closed_semantic_equivalence_modules = [
        "runtime_storage_maintenance",
        "artifact_lifecycle_storage_audit_shell",
        "workbench_portal_generic_shell",
        "owner_route_reconcile_materialize_dispatch_shell",
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
    assert inventory_by_id["artifact_authority"]["migration_action"] == "authority_stays_in_mas"
    assert inventory_by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert inventory_by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["trigger_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["write_install_proof_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["resurrection_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["classification"] == (
        "legacy_cleanup_physical_retired"
    )
    assert inventory_by_id["local_launchd_scheduler_install_path"]["no_resurrection_gate"][
        "default_caller_count"
    ] == 0
    assert inventory_by_id["workspace_local_watch_service_wrappers"]["tombstone_required"] is True
    assert inventory_by_id["domain_health_diagnostic_loop_shell"]["physical_retired"] is True
    assert inventory_by_id["domain_health_diagnostic_loop_shell"]["no_resurrection_gate"]["replacement_surface"] == (
        "opl_provider_runtime_manager"
    )
    assert runtime_boundary["functional_module_inventory_summary"]["classification_counts"] == {
        "declarative_pack_generated_surface": 7,
        "domain_authority_refs": 5,
        "minimal_authority_function": 3,
        "legacy_cleanup_physical_retired": 3,
    }
    assert runtime_boundary["functional_module_inventory_summary"]["retired_legacy_residue_count"] == 4
    assert runtime_boundary["functional_module_inventory_summary"]["legacy_cleanup_items_tombstoned"] == [
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_tombstone_provenance",
    ]
    assert runtime_boundary["functional_module_inventory_summary"]["classification_gap_count"] == 0
    assert runtime_boundary["functional_module_inventory_summary"]["functional_structure_gap_count"] == 0
    assert runtime_boundary["functional_module_inventory_summary"]["active_private_generic_residue_count"] == 0
    assert (
        runtime_boundary["functional_module_inventory_summary"]["remaining_gap_classification"]
        == "live_provider_paper_line_evidence_gates"
    )
    assert runtime_boundary["functional_module_inventory_summary"][
        "long_term_opl_owned_replacement_count"
    ] == 0
    assert runtime_boundary["functional_module_inventory_summary"][
        "retire_tombstone_classification_count"
    ] == 0
    followthrough_summary = runtime_boundary["functional_followthrough_gap_summary"]
    assert followthrough_summary["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert followthrough_summary["classification_gap_count"] == 0
    assert followthrough_summary["functional_structure_gap_count"] == 0
    assert followthrough_summary["active_private_generic_residue_count"] == 0
    assert followthrough_summary["remaining_gap_classification"] == (
        "live_provider_paper_line_evidence_gates"
    )
    assert followthrough_summary["remaining_items_are_evidence_gates"] is True
    assert followthrough_summary["legacy_cleanup_items_are_remaining_active_gaps"] is False
    assert followthrough_summary["legacy_cleanup_items_have_default_entry"] is False
    assert followthrough_summary["legacy_cleanup_items_physical_retired"] == [
        "local_launchd_scheduler_install_path",
        "workspace_local_watch_service_wrappers",
        "domain_health_diagnostic_loop_shell",
    ]
    assert followthrough_summary["legacy_cleanup_items_tombstoned"] == [
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_tombstone_provenance",
    ]
    assert followthrough_summary["legacy_cleanup_items_have_standard_template_refs"] is False
    assert followthrough_summary["remaining_functional_followthrough_gate_ids"] == []
    assert followthrough_summary["remaining_functional_followthrough_gates"] == []
    assert followthrough_summary["closed_functional_structure_gate_ids"] == [
        "generated_surface_default_owner_cutover",
        "domain_authority_refs_thinning",
        "legacy_cleanup_physical_retirement",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
    ]
    assert followthrough_summary["does_not_clear"] == (
        followthrough_summary["remaining_evidence_gate_ids"]
    )
    assert followthrough_summary["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]
    route_stage_boundary = runtime_boundary["route_stage_residue_boundary"]
    assert route_stage_boundary["surface_kind"] == "mas_route_stage_residue_boundary"
    assert route_stage_boundary["route_is_stage"] is False
    assert route_stage_boundary["route_semantics_owner"] == "med-autoscience"
    assert route_stage_boundary["stage_graph_owner"] == "one-person-lab"
    assert route_stage_boundary["runtime_transition_owner"] == "one-person-lab"
    assert route_stage_boundary["queue_attempt_owner"] == "one-person-lab"
    assert route_stage_boundary["mas_owns_inter_route_scheduler"] is False
    assert route_stage_boundary["legacy_surface_names_current_active"] is False
    assert route_stage_boundary["all_residual_surfaces_physically_retired"] is True
    assert route_stage_boundary["physical_retirement_scope"] == (
        "legacy_mas_private_runtime_route_surface_names"
    )
    assert route_stage_boundary["physical_retirement_gate"] == [
        "stale_surface_scan_clean",
        "opl_replacement_parity",
        "domain_receipt_parity",
        "focused_tests",
        "no_forbidden_write_proof",
        "history_tombstone_refs",
    ]
    residue_by_id = {
        item["surface_id"]: item for item in route_stage_boundary["residual_surfaces"]
    }
    assert set(residue_by_id) == {
        "owner_route_reconcile",
        "progress_projection",
        "domain_health_diagnostic",
        "domain_decision_authority",
        "domain_authority_refs_index",
        "owner_route_dispatch_receipt",
    }
    assert residue_by_id["owner_route_reconcile"]["retired_legacy_surface_id"] == "domain_route_scan"
    assert residue_by_id["progress_projection"]["retired_legacy_surface_id"] == "study_runtime_status"
    assert residue_by_id["domain_health_diagnostic"]["retired_legacy_surface_id"] == "runtime_watch"
    assert residue_by_id["domain_decision_authority"]["retired_legacy_surface_id"] == "status_and_decision"
    assert residue_by_id["domain_authority_refs_index"]["retired_legacy_surface_id"] == (
        "domain_authority_ref_locator_index"
    )
    assert residue_by_id["owner_route_dispatch_receipt"]["retired_legacy_surface_id"] == (
        "sidecar_dispatch_adapter"
    )
    assert residue_by_id["owner_route_reconcile"]["opl_consumes_as"] == (
        "owner_route_refs_for_opl_queue_stage_attempt_hydration"
    )
    assert residue_by_id["owner_route_reconcile"]["stage_or_queue_owner"] == "one-person-lab"
    assert residue_by_id["progress_projection"]["current_role"] == (
        "domain_truth_status_projection"
    )
    assert residue_by_id["domain_health_diagnostic"]["long_loop_shell_physical_retired"] is True
    assert residue_by_id["domain_health_diagnostic"]["long_loop_resurrection_allowed"] is False
    assert residue_by_id["domain_decision_authority"]["migration_state"] == (
        "legacy_name_retired_authority_and_projection_split_active"
    )
    assert residue_by_id["domain_authority_refs_index"]["domain_authority_refs_gate"] == (
        refs_only_retirement_gates["domain_authority_refs_index"]
    )
    assert residue_by_id["domain_authority_refs_index"]["physical_delete_permitted"] is True
    assert residue_by_id["owner_route_dispatch_receipt"]["domain_ref_consumer_count"] == 1
    for item in residue_by_id.values():
        assert item["generic_runtime_owner_claim_allowed"] is False
        assert item["physical_retired"] is True
        if item["surface_id"] != "domain_authority_refs_index":
            assert item["physical_delete_permitted"] is False
    assert "route_is_stage" in route_stage_boundary["forbidden_claims"]
    assert "legacy_surface_names_current_active" in route_stage_boundary[
        "forbidden_claims"
    ]
    assert {item["functional_structure_gap"] for item in followthrough_summary["remaining_evidence_gates"]} == {
        False
    }
    assert set(followthrough_summary["cleared_by_surfaces"]) == {
        "functional_module_inventory",
        "declarative_pack_compiler_input",
        "generated_surface_handoff",
        "minimal_authority_function_manifest",
        "stale_surface_scan_clean",
        "opl_functional_harness_consumer_coverage",
        "opl_generated_interface_default_owner_target_proof",
        "opl_app_operator_workbench_drilldown",
        "opl_lifecycle_index_cleanup_restore_ledger",
    }
    tombstones = runtime_boundary["retired_legacy_residue_tombstones"]
    assert {item["residue_id"] for item in tombstones} == set(
        classification["legacy_cleanup_tombstone_provenance"]
    )
    for item in tombstones:
        assert item["current_role"] == "history_tombstone_provenance_only"
        assert item["domain_ref_consumer_count"] == 0
        assert item["default_entry_allowed"] is False
        assert item["retirement_gate"] == "no_resurrection_tombstone"
        assert "paper_closure_verdict" in item["must_not_emit"]
    lifecycle_role = lane["domain_authority_refs_index_role"]
    assert lifecycle_role["classification"] == "domain_authority_refs"
    assert lifecycle_role["current_mas_role"] == "domain_authority_receipt_and_locator_ref_index"
    assert lifecycle_role["authority"] == (
        "refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine"
    )
    assert lifecycle_role["owner"] == "one-person-lab"
    assert lifecycle_role["mas_may_claim_generic_persistence_engine"] is False
    assert lifecycle_role["mas_consumes_opl_current_control_state_refs"] is True
    assert lifecycle_role["mas_may_write_domain_truth"] is False
    assert set(lifecycle_role["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_runtime_lifecycle_owner",
        "generic_restore_retention_owner",
    }
    assert lifecycle_role["replacement_expectation"]["audit_ref"] == (
        "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough"
    )
    assert lane["no_resurrection_proof"]["default_caller_count"] == 0
    assert lane["no_resurrection_proof"]["default_manager"] == "opl"
    assert lane["no_resurrection_proof"]["forbidden_default_callers"] == [
        "cli_default_local_scheduler_install",
        "workspace_bootstrap_local_scheduler_install",
        "product_entry_local_scheduler_install",
        "sidecar_local_scheduler_install",
        "mcp_local_scheduler_install",
    ]
    assert "workspace_bootstrap_manager_is_opl" in lane["no_resurrection_proof"]["proof_items"]
    retirement_proof = lane["legacy_local_scheduler_physical_retirement_proof"]
    assert retirement_proof["install_allowed"] is False
    assert retirement_proof["status_allowed"] is False
    assert retirement_proof["remove_allowed"] is False
    assert retirement_proof["trigger_allowed"] is False
    assert retirement_proof["write_install_proof_allowed"] is False
    assert retirement_proof["default_cli_exposes_local_install"] is False
    assert retirement_proof["default_bootstrap_exposes_local_install"] is False
    assert retirement_proof["cleanup_status"] == "tombstone_only"
    assert retirement_proof["remaining_physical_delete_blockers"] == []
    assert lane["required_projection_surfaces"] == [
        "product_entry_manifest.functional_consumer_boundary",
        "product_entry_manifest.functional_consumer_boundary.declarative_pack_compiler_input",
        "product_entry_manifest.functional_consumer_boundary.generated_surface_handoff",
        "product_entry_manifest.functional_consumer_boundary.minimal_authority_function_manifest",
        "sidecar_export.functional_consumer_boundary",
        "sidecar_export.functional_consumer_boundary.declarative_pack_compiler_input",
        "sidecar_export.functional_consumer_boundary.generated_surface_handoff",
        "sidecar_export.functional_consumer_boundary.minimal_authority_function_manifest",
        "opl_unique_control_plane_boundary.consumer_migration.functional_consumer_boundary",
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
    assert set(coverage["mas_domain_authority_pack"]) == set(lane["mas_domain_authority_surfaces"])
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
    assert lane["no_resurrection_proof_required"] == [
        "cli_default_manager_is_opl",
        "local_scheduler_physical_retirement_tombstone_only",
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
