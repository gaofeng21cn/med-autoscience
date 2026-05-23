from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta

EXPECTED_CAPABILITY_IDS = [
    "runtime_execution",
    "artifact_inventory",
    "paper_contract_health",
    "manuscript_coverage",
    "prompt_stage_discipline",
    "memory_and_lesson_store",
]
EXPECTED_CLASSIFICATIONS = [
    "mas_owned",
    "rewrite_in_mas",
    "fixture_only",
    "retire",
    "external_source_archive_only",
    "opl_owned_runtime_control_mas_domain_refs",
]
EXPECTED_REMAINING_SURFACE_CLASSIFICATIONS = [
    *EXPECTED_CLASSIFICATIONS,
    "opl_runtime_control_with_mas_refs",
    "retired_mas_runtime_surface",
]
EXPECTED_REMAINING_SURFACE_IDS = [
    "runtime_core_daemon",
    "quest_lifecycle",
    "worker_runner_lifecycle",
    "channels_connectors_transport",
    "mcp_surface",
    "tui_web_visual_status",
    "gitops_workspace_state",
    "skills_overlay_templates",
    "team_multiagent_coordination",
    "upstream_source_archive",
]
EXPECTED_BEHAVIOR_SURFACE_IDS = [
    "daemon_residency",
    "supervision_cadence",
    "turn_completion_continuation",
    "quest_create_resume_pause_stop",
    "live_worker_session_tracking",
    "crash_recovery_auto_resume",
    "queued_user_messages_mailbox",
    "progress_visibility",
    "webui_websocket_terminal_streaming",
    "connector_channel_background_delivery",
    "mcp_surface",
    "gitops_state_management",
    "memory_lesson_store",
    "team_multiagent_coordination",
    "artifact_interaction_handoff",
    "system_update_daemon_lifecycle_controls",
    "workspace_local_host_service",
]
EXPECTED_PAPER_PROGRESS_DEGRADATION_CLASSES = [
    "production_degrading",
    "production_risk",
    "diagnostic_degrading",
    "acceptable_design_difference",
    "retired_non_goal",
]
EXPECTED_PRODUCTION_DEGRADING_OVERLAY_IDS = [
    "owner_handoff_dispatch",
    "repeat_suppression",
    "work_unit_redrive",
]
EXPECTED_RUNTIME_CONTINUITY_USER_SURFACES = [
    "study_progress",
    "workspace_cockpit",
    "product_entry_status",
    "progress_portal",
    "mcp_study_progress",
    "opl_handoff",
]

EXPECTED_SUPERSEDE_PROOF_IDS = [
    "artifact_inventory",
    "package_locator",
    "paper_contract_health",
    "manuscript_coverage",
    "prompt_stage_discipline",
    "memory_and_lesson_store",
]


def _complete_proof_bundle_from_matrix(matrix: dict[str, object]) -> dict[str, object]:
    capabilities = []
    for capability in matrix["capabilities"]:
        capabilities.append(
            {
                "capability_id": capability["capability_id"],
                "mas_owner_surface": capability["mas_owner_surface"],
                "oracle_fixture_ref": capability["oracle_fixture_ref"],
                "parity_status": "passed",
                "rollback_surface": capability["rollback_surface"],
                "provenance_ref": capability["provenance_ref"],
                "classification": capability["classification"],
                "quality_authority_allowed": False,
                "publication_ready_authority_allowed": False,
                "quality_ready_authority_allowed": False,
                "submission_ready_authority_allowed": False,
                "proof_ref": f"proof-bundles/mds-capability-parity/{capability['capability_id']}.json",
                "supersede_proofs": capability["supersede_proofs"],
            }
        )
    return {
        "surface": "mds_capability_parity_proof_bundle",
        "schema_version": 1,
        "capabilities": capabilities,
    }


def test_mds_capability_parity_matrix_keeps_mds_backend_oracle_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    matrix = module.build_mds_capability_parity_matrix()

    assert matrix["surface"] == "mds_capability_parity_matrix"
    assert matrix["mds_role"] == "frozen_source_archive_or_historical_fixture_only"
    assert matrix["mds_quality_authority"] == "none"
    assert matrix["mas_owner"] == "MedAutoScience"
    assert matrix["physical_absorb_allowed"] == "landed_no_history_functional_monolith"
    assert matrix["allowed_capability_classifications"] == EXPECTED_CLASSIFICATIONS
    assert [capability["capability_id"] for capability in matrix["capabilities"]] == EXPECTED_CAPABILITY_IDS
    assert matrix["capability_ids"] == EXPECTED_CAPABILITY_IDS
    assert matrix["supersede_proof_ids"] == EXPECTED_SUPERSEDE_PROOF_IDS
    assert [fixture["capability_id"] for fixture in matrix["retained_capability_oracle_fixtures"]] == EXPECTED_CAPABILITY_IDS
    assert [surface["surface_id"] for surface in matrix["remaining_surface_inventory"]] == EXPECTED_REMAINING_SURFACE_IDS
    assert matrix["parity_summary"] == {
        "capability_count": 6,
        "proof_count": 6,
        "oracle_fixture_count": 6,
        "remaining_surface_count": 10,
        "behavior_surface_count": 17,
        "paper_progress_classifier_entry_count": 20,
        "paper_progress_production_degrading_entry_count": 3,
        "quality_owner": "MedAutoScience",
        "mds_role": "frozen_source_archive_or_historical_fixture_only",
        "medical_quality_authority": "blocked_for_mds",
        "fully_equivalent_to_mds_daemon": False,
    }
    fixtures_by_capability = {
        fixture["capability_id"]: fixture for fixture in matrix["retained_capability_oracle_fixtures"]
    }
    for capability in matrix["capabilities"]:
        assert capability["mds_authority_role"] in {"backend", "behavior_oracle", "mechanical_oracle"}
        assert capability["can_authorize_medical_quality"] is False
        assert capability["quality_ready_authority_allowed"] is False
        assert capability["quality_authority_allowed"] is False
        assert capability["publication_ready_authority_allowed"] is False
        assert capability["submission_ready_authority_allowed"] is False
        assert capability["classification"] in EXPECTED_CLASSIFICATIONS
        assert capability["mas_owner_surface"]
        assert capability["oracle_fixture_ref"]
        assert capability["parity_status"] == "oracle_fixture_defined"
        assert capability["rollback_surface"]
        assert capability["provenance_ref"]
        assert fixtures_by_capability[capability["capability_id"]] == {
            "capability_id": capability["capability_id"],
            "mas_owner_surface": capability["mas_owner_surface"],
            "oracle_fixture_ref": capability["oracle_fixture_ref"],
            "parity_status": "oracle_fixture_defined",
            "rollback_surface": capability["rollback_surface"],
            "provenance_ref": capability["provenance_ref"],
            "classification": capability["classification"],
            "quality_authority_allowed": False,
            "publication_ready_authority_allowed": False,
            "quality_ready_authority_allowed": False,
            "submission_ready_authority_allowed": False,
        }
        for proof in capability["supersede_proofs"]:
            assert proof["proof_id"] in EXPECTED_SUPERSEDE_PROOF_IDS
            assert proof["mas_owned"] is True
            assert proof["mds_mechanical_signal_role"] == "evidence_only"
            assert proof["mechanical_signal_can_only"].startswith("request_")
            assert proof["quality_ready_authorized"] is False
            assert proof["publication_ready_authorized"] is False
            assert proof["submission_ready_authorized"] is False
        assert capability["required_parity_proof"]
        assert set(capability["parity_proof"]) == {"proof_kind", "mas_contract", "mds_oracle", "acceptance"}
        assert capability["parity_proof"]["mas_contract"]
        assert capability["parity_proof"]["mds_oracle"]
        assert capability["parity_proof"]["acceptance"]
        cutover_readiness = capability["cutover_readiness"]
        assert cutover_readiness["cutover_status"] == "landed_functional_monolith"
        assert cutover_readiness["owner_switch_allowed"] is True
        assert cutover_readiness["required_gates"] == matrix["cutover_gates"]
        assert cutover_readiness["mas_side_contract"]
        assert cutover_readiness["mds_oracle_fixture"]
        assert cutover_readiness["oracle_fixture_ref"] == capability["oracle_fixture_ref"]
        assert cutover_readiness["provenance_ref"] == capability["provenance_ref"]
        assert cutover_readiness["quality_gate_not_relaxed"] is True
        assert cutover_readiness["rollback_surface"]
        assert cutover_readiness["old_mds_authority_surface_status"] in {"marked_oracle", "retired"}
        assert cutover_readiness["quality_ready_authority_allowed"] is False
        assert cutover_readiness["publication_ready_authority_allowed"] is False
        assert cutover_readiness["submission_ready_authority_allowed"] is False


def test_mds_remaining_surface_inventory_classifies_functional_monolith_surfaces_without_upstream_history() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    inventory = module.build_mds_remaining_surface_inventory()

    assert inventory["surface"] == "mds_remaining_surface_inventory"
    assert inventory["schema_version"] == 1
    assert inventory["owner"] == "MedAutoScience"
    assert inventory["mds_final_role"] == "frozen_source_archive_or_historical_fixture_only"
    assert inventory["default_operation_requires_external_mds"] is False
    assert inventory["upstream_history_import_allowed"] is False
    assert inventory["allowed_classifications"] == EXPECTED_REMAINING_SURFACE_CLASSIFICATIONS
    assert [surface["surface_id"] for surface in inventory["remaining_surfaces"]] == EXPECTED_REMAINING_SURFACE_IDS
    assert {surface["classification"] for surface in inventory["remaining_surfaces"]} == {
        "mas_owned",
        "rewrite_in_mas",
        "fixture_only",
        "retire",
        "external_source_archive_only",
        "opl_runtime_control_with_mas_refs",
        "retired_mas_runtime_surface",
    }
    assert inventory["classification_summary"] == {
        "surface_count": 10,
        "mas_owned": 2,
        "rewrite_in_mas": 1,
        "fixture_only": 2,
        "retire": 2,
        "external_source_archive_only": 1,
        "opl_owned_runtime_control_mas_domain_refs": 0,
        "opl_runtime_control_with_mas_refs": 1,
        "retired_mas_runtime_surface": 1,
    }
    surfaces_by_id = {surface["surface_id"]: surface for surface in inventory["remaining_surfaces"]}
    assert surfaces_by_id["runtime_core_daemon"]["classification"] == "retired_mas_runtime_surface"
    assert surfaces_by_id["worker_runner_lifecycle"]["classification"] == "mas_owned"
    assert surfaces_by_id["runtime_core_daemon"]["parity_proof"]["proof_kind"] == "retired_runtime_surface_parity"
    assert surfaces_by_id["worker_runner_lifecycle"]["parity_proof"]["proof_kind"] == "worker_runner_receipts"
    for surface in inventory["remaining_surfaces"]:
        assert surface["classification"] in EXPECTED_REMAINING_SURFACE_CLASSIFICATIONS
        assert surface["mas_target_owner"]
        assert surface["mds_final_role"]
        assert surface["cutover_contract"]
        assert surface["owner_boundary"]
        assert surface["provenance_ref"] == "docs/references/med-deepscientist/source_provenance.json"
        assert surface["authority_claims"] == []
        assert surface["imports_upstream_history"] is False
        assert surface["default_runtime_dependency_allowed"] is False
        assert surface["quality_authority_allowed"] is False
        assert surface["publication_ready_authority_allowed"] is False

    assert module.validate_mds_remaining_surface_inventory(inventory)["ok"] is True


def test_mds_behavior_equivalence_matrix_separates_default_independence_from_daemon_equivalence() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    matrix = module.build_mds_behavior_equivalence_matrix()

    assert matrix["surface"] == "mds_behavior_equivalence_matrix"
    assert matrix["owner"] == "MedAutoScience"
    assert matrix["default_operation_requires_external_mds"] is False
    assert matrix["default_supervision_owner"] == "opl_provider_runtime_manager"
    assert matrix["default_scheduler_adapter"] == "opl"
    assert matrix["optional_scheduler_adapters"] == []
    assert matrix["retired_scheduler_adapters"] == ["hermes_gateway_cron_retired_tombstone"]
    assert matrix["default_tick_interval_seconds"] == 300
    assert matrix["default_tick_max_ticks"] == 1
    assert matrix["mas_default_runtime_is_resident_daemon"] is False
    assert matrix["mds_daemon_was_resident_http_websocket_server"] is True
    assert matrix["completion_claim"] == "default_independence_not_full_behavior_equivalence"
    assert matrix["allowed_paper_progress_degradation_classes"] == EXPECTED_PAPER_PROGRESS_DEGRADATION_CLASSES
    assert [item["surface_id"] for item in matrix["behavior_surfaces"]] == EXPECTED_BEHAVIOR_SURFACE_IDS
    assert matrix["summary"] == {
        "surface_count": 17,
        "behavior_equivalent": 2,
        "purpose_equivalent_with_different_timing": 6,
        "purpose_equivalent_with_authority_split": 1,
        "partially_equivalent": 3,
        "not_equivalent_retired": 4,
        "historical_fixture_only": 1,
        "fully_equivalent_to_mds_daemon": False,
    }
    assert matrix["paper_progress_degradation_summary"] == {
        "behavior_surface_count": 17,
        "overlay_risk_count": 3,
        "total_classifier_entry_count": 20,
        "automatic_paper_production_behavior_surface_count": 10,
        "automatic_paper_production_entry_count": 13,
        "production_degrading_entry_count": 3,
        "behavior_surface_classification_counts": {
            "production_degrading": 0,
            "production_risk": 8,
            "diagnostic_degrading": 2,
            "acceptable_design_difference": 3,
            "retired_non_goal": 4,
        },
        "overlay_classification_counts": {
            "production_degrading": 3,
            "production_risk": 0,
            "diagnostic_degrading": 0,
            "acceptable_design_difference": 0,
            "retired_non_goal": 0,
        },
        "combined_classification_counts": {
            "production_degrading": 3,
            "production_risk": 8,
            "diagnostic_degrading": 2,
            "acceptable_design_difference": 3,
            "retired_non_goal": 4,
        },
        "production_degrading_risk_ids": EXPECTED_PRODUCTION_DEGRADING_OVERLAY_IDS,
    }
    classifier = matrix["paper_progress_degradation_classifier"]
    assert classifier["surface"] == "mds_paper_progress_degradation_classifier"
    assert classifier["allowed_degradation_classes"] == EXPECTED_PAPER_PROGRESS_DEGRADATION_CLASSES
    assert [item["surface_id"] for item in classifier["behavior_surface_classifications"]] == (
        EXPECTED_BEHAVIOR_SURFACE_IDS
    )
    assert [item["risk_id"] for item in classifier["overlay_risks"]] == EXPECTED_PRODUCTION_DEGRADING_OVERLAY_IDS
    assert classifier["summary"] == matrix["paper_progress_degradation_summary"]
    by_surface = {item["surface_id"]: item for item in matrix["behavior_surfaces"]}
    assert by_surface["daemon_residency"]["equivalence_class"] == "purpose_equivalent_with_different_timing"
    assert by_surface["daemon_residency"]["paper_progress_degradation"] == {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "outer_supervision_recovery_latency",
        "rationale": "Scheduled supervision can delay stale-run detection and recovery, but MAS turn continuation no longer depends on resident MDS.",
        "required_guard_surface": "domain_health_diagnostic/runtime_supervision freshness",
    }
    assert by_surface["daemon_residency"]["behavior_difference"] == "MAS default supervision is scheduled ticks, not a resident HTTP/WebSocket daemon."
    assert by_surface["supervision_cadence"]["mas_behavior"]["interval_seconds"] == 300
    assert by_surface["supervision_cadence"]["mas_behavior"]["max_ticks"] == 1
    assert by_surface["supervision_cadence"]["mas_behavior"]["inner_turn_continuation_owner"] == "OPL stage attempt ledger"
    assert by_surface["turn_completion_continuation"]["equivalence_class"] == "behavior_equivalent"
    assert by_surface["turn_completion_continuation"]["mas_behavior"]["auto_continue_delay_seconds"] is None
    assert "OPL-owned" in by_surface["turn_completion_continuation"]["mas_contract"]
    assert by_surface["live_worker_session_tracking"]["mas_behavior"]["session_store"] == (
        "OPL current_control_state plus MAS domain authority refs"
    )
    assert by_surface["live_worker_session_tracking"]["mas_behavior"]["runner_monitor"] is False
    assert "OPL current_control_state" in by_surface["live_worker_session_tracking"]["mas_contract"]
    assert by_surface["queued_user_messages_mailbox"]["mas_behavior"] == {
        "task_intake": True,
        "controller_handoff": True,
        "domain_intake_refs": True,
        "daemon_mailbox": False,
    }
    assert "OPL owns recovery scheduling" in by_surface["crash_recovery_auto_resume"]["mas_contract"]
    assert by_surface["progress_visibility"]["equivalence_class"] == "partially_equivalent"
    assert by_surface["progress_visibility"]["mas_behavior"]["primary_scope"] == "workspace_shell_with_per_study_pages"
    assert by_surface["progress_visibility"]["mas_behavior"]["paper_scoped_navigation"] == "landed_per_study_pages"
    assert by_surface["progress_visibility"]["mas_behavior"]["route_decision_trail"] == "landed_read_only"
    assert by_surface["progress_visibility"]["mas_behavior"]["executor_conversation_runtime_drilldown"] == (
        "retired_physical_no_alias_mas_surface"
    )
    assert by_surface["progress_visibility"]["mas_behavior"]["combined_portal_runtime_soak_keys"] is False
    assert "mas_progress_portal_route_decision_trail" in by_surface["progress_visibility"]["mas_contract"]
    assert "runtime truth" in by_surface["progress_visibility"]["mas_contract"]
    assert by_surface["progress_visibility"]["paper_progress_degradation"]["classification"] == "diagnostic_degrading"
    assert by_surface["progress_visibility"]["paper_progress_degradation"]["affects_automatic_paper_production"] is False
    assert by_surface["progress_visibility"]["future_parity_candidate"] == (
        "opl_app_current_control_state_user_path_soak"
    )
    assert by_surface["webui_websocket_terminal_streaming"]["equivalence_class"] == "purpose_equivalent_with_different_timing"
    assert by_surface["webui_websocket_terminal_streaming"]["mas_behavior"]["mas_private_runtime_console"] == (
        "retired_physical_no_alias_surface"
    )
    assert by_surface["webui_websocket_terminal_streaming"]["mas_behavior"]["websocket_terminal_attach"] == "not_exposed_by_mas"
    assert by_surface["webui_websocket_terminal_streaming"]["mas_behavior"]["terminal_attach_gate"] == (
        "retired_physical_no_alias_surface"
    )
    assert by_surface["webui_websocket_terminal_streaming"]["mas_behavior"]["terminal_attach_owner"] == (
        "one-person-lab"
    )
    assert by_surface["webui_websocket_terminal_streaming"]["mas_behavior"]["authorized_portal_actions"] == (
        "not_supported_by_mas_portal"
    )
    assert by_surface["webui_websocket_terminal_streaming"]["future_parity_candidate"] == (
        "opl_current_control_state_provider_drilldown_soak"
    )
    assert by_surface["webui_websocket_terminal_streaming"]["paper_progress_degradation"]["classification"] == (
        "diagnostic_degrading"
    )
    assert by_surface["webui_websocket_terminal_streaming"]["paper_progress_degradation"][
        "affects_automatic_paper_production"
    ] is False
    assert "physically retired with no compatibility alias" in by_surface[
        "webui_websocket_terminal_streaming"
    ]["mas_contract"]
    assert "OPL current_control_state" in by_surface["webui_websocket_terminal_streaming"]["mas_contract"]
    assert by_surface["connector_channel_background_delivery"]["equivalence_class"] == "not_equivalent_retired"
    assert by_surface["connector_channel_background_delivery"]["paper_progress_degradation"]["classification"] == (
        "retired_non_goal"
    )
    assert by_surface["memory_lesson_store"]["equivalence_class"] == "purpose_equivalent_with_authority_split"
    assert by_surface["memory_lesson_store"]["mas_behavior"]["stage_knowledge_packet"] is True
    assert by_surface["memory_lesson_store"]["mas_behavior"]["stage_memory_closeout_packet"] is True
    assert by_surface["memory_lesson_store"]["mas_behavior"]["memory_write_router_receipt"] is True
    assert by_surface["memory_lesson_store"]["mas_behavior"]["stage_recall_index"] is True
    assert by_surface["memory_lesson_store"]["mas_behavior"]["quality_authority"] is False
    assert "stage_knowledge_packet" in by_surface["memory_lesson_store"]["mas_contract"]
    assert "memory_write_router_receipt" in by_surface["memory_lesson_store"]["mas_contract"]
    assert by_surface["memory_lesson_store"]["remaining_gap_until_soak"] == (
        "real-paper stage injection soak must keep proving consumed refs, accepted/rejected writes, route impact, and next owner in Progress/Portal surfaces."
    )
    assert by_surface["memory_lesson_store"]["paper_progress_degradation"]["classification"] == "production_risk"
    assert by_surface["turn_completion_continuation"]["paper_progress_degradation"]["classification"] == (
        "acceptable_design_difference"
    )
    assert by_surface["workspace_local_host_service"]["equivalence_class"] == "not_equivalent_retired"
    continuity = matrix["runtime_continuity_completion"]
    assert continuity["status"] == "landed"
    assert continuity["external_mds_repo_required"] is False
    assert continuity["mds_daemon_required"] is False
    assert continuity["active_scheduler"] == "opl_provider_runtime_manager"
    assert continuity["active_scheduler_adapter"] == "opl"
    assert continuity["legacy_diagnostic_scheduler"] == "mas_legacy_domain_slo_diagnostic"
    assert continuity["legacy_diagnostic_scheduler_adapter"] == "local"
    assert continuity["optional_scheduler_adapters"] == []
    assert continuity["retired_scheduler_adapters"] == ["hermes_gateway_cron_retired_tombstone"]
    assert continuity["current_control_state_projection"]["role"] == "read_model"
    assert continuity["current_control_state_projection"]["read_only"] is True
    assert continuity["current_control_state_projection"]["writes_authority_surface"] is False
    assert continuity["retired_mas_recovery_projection"]["role"] == "physical_retired_no_alias"
    assert continuity["retired_mas_recovery_projection"]["allowed_current_actions"] == []
    assert continuity["retired_mas_recovery_projection"]["replacement_surface"] == (
        "opl_current_control_state plus MAS typed_blocker_or_owner_receipt"
    )
    assert continuity["safe_reconcile_trigger"]["executes_reconcile"] is False
    assert continuity["safe_reconcile_trigger"]["writes_runtime"] is False
    assert "parked" in continuity["safe_reconcile_trigger"]["blocked_current_truth"]
    assert continuity["user_surface_projection"]["surfaces"] == EXPECTED_RUNTIME_CONTINUITY_USER_SURFACES
    assert continuity["user_surface_projection"]["reinterprets_study_truth"] is False
    assert continuity["quality_ready_authorized"] is False
    assert continuity["publication_ready_authorized"] is False
    assert continuity["submission_ready_authorized"] is False
    for item in matrix["behavior_surfaces"]:
        assert item["mas_default_requires_external_mds"] is False
        assert item["requires_mds_daemon_for_default_operation"] is False
        assert item["quality_authority_allowed"] is False
        assert item["publication_ready_authority_allowed"] is False
        paper_progress = item["paper_progress_degradation"]
        assert paper_progress["classification"] in EXPECTED_PAPER_PROGRESS_DEGRADATION_CLASSES
        assert isinstance(paper_progress["affects_automatic_paper_production"], bool)
        assert paper_progress["production_path"]
        assert paper_progress["rationale"]
        assert paper_progress["required_guard_surface"]
        assert item["recommended_operator_action"] in {
            "use_mas_default",
            "use_mas_with_latency_awareness",
            "use_progress_portal",
            "use_explicit_archive_import_ref_only",
            "retired_no_active_replacement",
            "retired_no_resurrection",
            "use_historical_fixture_only",
            "use_opl_provider_stage_runtime",
            "use_opl_runtime_workbench",
        }
    assert module.validate_mds_behavior_equivalence_matrix(matrix)["ok"] is True


def test_mds_behavior_equivalence_validation_blocks_overclaim_and_legacy_runtime_dependency() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    matrix = module.build_mds_behavior_equivalence_matrix()
    matrix["default_operation_requires_external_mds"] = True
    matrix["mas_default_runtime_is_resident_daemon"] = True
    matrix["behavior_surfaces"][0]["equivalence_class"] = "behavior_equivalent"
    matrix["behavior_surfaces"][0]["requires_mds_daemon_for_default_operation"] = True
    matrix["behavior_surfaces"][1]["quality_authority_allowed"] = True
    matrix["behavior_surfaces"][2]["publication_ready_authority_allowed"] = True
    matrix["runtime_continuity_completion"]["mds_daemon_required"] = True
    matrix["runtime_continuity_completion"]["current_control_state_projection"]["writes_authority_surface"] = True
    matrix["runtime_continuity_completion"]["safe_reconcile_trigger"]["executes_reconcile"] = True
    matrix["runtime_continuity_completion"]["user_surface_projection"]["reinterprets_study_truth"] = True
    matrix["runtime_continuity_completion"]["quality_ready_authorized"] = True
    matrix["allowed_paper_progress_degradation_classes"] = ["production_risk"]
    matrix["behavior_surfaces"][3]["paper_progress_degradation"]["classification"] = "paper_only"
    matrix["paper_progress_degradation_classifier"]["behavior_surface_classifications"].pop()
    matrix["paper_progress_degradation_classifier"]["behavior_surface_classifications"][0]["rationale"] = "drift"
    matrix["paper_progress_degradation_classifier"]["overlay_risks"][0]["classification"] = "production_risk"
    matrix["paper_progress_degradation_classifier"]["overlay_risks"][1]["affects_automatic_paper_production"] = "yes"
    matrix["paper_progress_degradation_classifier"]["summary"]["total_classifier_entry_count"] = 999

    validation = module.validate_mds_behavior_equivalence_matrix(matrix)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "behavior_matrix_external_mds_default_dependency",
        "behavior_matrix_resident_daemon_overclaim",
        "daemon_residency_overclaimed_as_behavior_equivalent",
        "behavior_surface_requires_mds_daemon_for_default_operation",
        "behavior_surface_quality_authority_allowed",
        "behavior_surface_publication_ready_authority_allowed",
        "runtime_continuity_mds_daemon_dependency",
        "runtime_continuity_session_authority_write",
        "runtime_continuity_safe_trigger_executes_reconcile",
        "runtime_continuity_user_projection_reinterprets_truth",
        "runtime_continuity_quality_ready_authorized",
        "behavior_matrix_allowed_paper_progress_degradation_classes_drift",
        "behavior_surface_invalid_paper_progress_degradation_class",
        "paper_progress_degradation_behavior_surface_coverage_drift",
        "paper_progress_degradation_missing_required_production_overlay",
        "paper_progress_degradation_invalid_impact_flag",
        "paper_progress_degradation_classifier_surface_projection_drift",
        "paper_progress_degradation_summary_drift",
        "paper_progress_degradation_matrix_summary_drift",
    }


def test_mds_capability_cutover_gate_requires_complete_proof_bundle_for_owner_switch() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")

    gate = module.build_mds_capability_cutover_gate()

    assert gate["surface"] == "mds_capability_cutover_gate"
    assert gate["mds_role"] == "frozen_source_archive_or_historical_fixture_only"
    assert gate["mds_quality_authority"] == "none"
    assert gate["quality_authority_rule"] == "mds_can_never_authorize_medical_quality"
    assert gate["owner_switch_allowed"] is False
    assert gate["cutover_status"] == "blocked_pending_parity_proof_bundle"
    assert gate["proof_bundle_status"] == "missing"
    assert gate["required_gates"] == [
        "mas_side_contract_exists",
        "mds_oracle_fixture_exists",
        "quality_gate_not_relaxed",
        "rollback_surface_exists",
        "old_mds_authority_surface_retired_or_marked_oracle",
    ]
    assert gate["summary"] == {
        "capability_count": 6,
        "owner_switch_allowed_count": 0,
        "blocked_capability_count": 6,
        "medical_quality_authority": "blocked_for_mds",
    }
    for capability in gate["capabilities"]:
        assert capability["cutover_status"] == "blocked_pending_parity_proof_bundle"
        assert capability["owner_switch_allowed"] is False
        assert capability["proof_bundle_status"] == "missing"
        assert capability["required_gates"] == gate["required_gates"]
        assert capability["mas_side_contract"]
        assert capability["mds_oracle_fixture"]
        assert capability["quality_gate_not_relaxed"] is True
        assert capability["rollback_surface"]
        assert capability["old_mds_authority_surface_status"] in {"marked_oracle", "retired"}
        assert capability["can_authorize_medical_quality"] is False
        assert capability["quality_ready_authority_allowed"] is False
        assert capability["quality_authority_allowed"] is False
        assert capability["publication_ready_authority_allowed"] is False
        assert capability["submission_ready_authority_allowed"] is False
        for proof in capability["supersede_proofs"]:
            assert proof["mechanical_signal_can_only"].startswith("request_")
            assert proof["quality_ready_authorized"] is False
            assert proof["publication_ready_authorized"] is False
            assert proof["submission_ready_authorized"] is False


def test_mds_capability_cutover_gate_allows_owner_switch_with_complete_proof_bundle() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    matrix = module.build_mds_capability_parity_matrix()
    proof_bundle = _complete_proof_bundle_from_matrix(matrix)

    gate = module.build_mds_capability_cutover_gate(proof_bundle)

    assert gate["proof_bundle_status"] == "complete"
    assert gate["owner_switch_allowed"] is True
    assert gate["cutover_status"] == "landed_functional_monolith"
    assert gate["summary"] == {
        "capability_count": 6,
        "owner_switch_allowed_count": 6,
        "blocked_capability_count": 0,
        "medical_quality_authority": "blocked_for_mds",
    }
    for capability in gate["capabilities"]:
        assert capability["cutover_status"] == "landed_functional_monolith"
        assert capability["owner_switch_allowed"] is True
        assert capability["parity_status"] == "passed"
        assert capability["quality_ready_authority_allowed"] is False
        assert capability["quality_authority_allowed"] is False
        assert capability["publication_ready_authority_allowed"] is False
        assert capability["submission_ready_authority_allowed"] is False


def test_mds_capability_parity_validation_blocks_quality_authority_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    matrix = module.build_mds_capability_parity_matrix()
    matrix["capabilities"][0]["can_authorize_medical_quality"] = True
    matrix["capabilities"][1]["required_parity_proof"] = ""
    matrix["capabilities"][2]["parity_proof"] = {}
    matrix["capabilities"][3]["oracle_fixture_ref"] = ""
    matrix["capabilities"][4]["quality_authority_allowed"] = True
    matrix["capabilities"][5]["publication_ready_authority_allowed"] = True
    matrix["capabilities"][0]["quality_ready_authority_allowed"] = True
    matrix["capabilities"][1]["submission_ready_authority_allowed"] = True
    matrix["capabilities"][2]["supersede_proofs"][0]["quality_ready_authorized"] = True
    matrix["capabilities"][3]["supersede_proofs"][0]["publication_ready_authorized"] = True
    matrix["capabilities"][4]["supersede_proofs"][0]["submission_ready_authorized"] = True
    matrix["capabilities"][0]["rollback_surface"] = ""
    matrix["capabilities"][1]["provenance_ref"] = ""

    validation = module.validate_mds_capability_parity_matrix(matrix)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "mds_quality_authority_drift",
        "capability_missing_parity_proof",
        "capability_incomplete_parity_proof_detail",
        "capability_missing_oracle_fixture_ref",
        "capability_quality_ready_authority_allowed",
        "capability_quality_authority_allowed",
        "capability_publication_ready_authority_allowed",
        "capability_submission_ready_authority_allowed",
        "capability_supersede_proof_ready_authority_drift",
        "capability_missing_rollback_surface",
        "capability_missing_provenance_ref",
    }


def test_mds_capability_proof_bundle_validation_fails_closed_on_missing_fixture_authority_and_provenance() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    matrix = module.build_mds_capability_parity_matrix()
    proof_bundle = _complete_proof_bundle_from_matrix(matrix)
    proof_bundle["capabilities"][0]["oracle_fixture_ref"] = ""
    proof_bundle["capabilities"][1]["quality_authority_allowed"] = True
    proof_bundle["capabilities"][2]["publication_ready_authority_allowed"] = True
    proof_bundle["capabilities"][3]["rollback_surface"] = ""
    proof_bundle["capabilities"][4]["provenance_ref"] = ""
    proof_bundle["capabilities"][5]["submission_ready_authority_allowed"] = True
    proof_bundle["capabilities"][1]["supersede_proofs"][0]["submission_ready_authorized"] = True

    validation = module.validate_mds_capability_proof_bundle(proof_bundle, matrix)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "proof_bundle_missing_oracle_fixture_ref",
        "proof_bundle_quality_authority_allowed",
        "proof_bundle_publication_ready_authority_allowed",
        "proof_bundle_submission_ready_authority_allowed",
        "proof_bundle_supersede_proof_ready_authority_drift",
        "proof_bundle_missing_rollback_surface",
        "proof_bundle_missing_provenance_ref",
    }


def test_mds_remaining_surface_inventory_validation_blocks_old_classifications_and_authority_claims() -> None:
    module = importlib.import_module("med_autoscience.controllers.mds_capability_parity")
    inventory = module.build_mds_remaining_surface_inventory()
    inventory["remaining_surfaces"][0]["classification"] = "oracle"
    inventory["remaining_surfaces"][1]["authority_claims"] = ["quality_authority"]
    inventory["remaining_surfaces"][2]["imports_upstream_history"] = True
    inventory["remaining_surfaces"][3]["default_runtime_dependency_allowed"] = True
    inventory["remaining_surfaces"][4]["cutover_contract"] = ""

    validation = module.validate_mds_remaining_surface_inventory(inventory)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} >= {
        "invalid_remaining_surface_classification",
        "remaining_surface_claims_mas_authority",
        "remaining_surface_imports_upstream_history",
        "remaining_surface_default_runtime_dependency_allowed",
        "remaining_surface_missing_cutover_contract",
    }
