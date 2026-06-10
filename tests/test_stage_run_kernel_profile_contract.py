from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _profile() -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts/stage_run_kernel_profile.json").read_text(encoding="utf-8"))


def _adoption() -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts/stage_artifact_kernel_adoption.json").read_text(encoding="utf-8"))


def _controlled_canary_evidence() -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts/stage_run_canary_evidence.json").read_text(encoding="utf-8"))


def test_stage_run_kernel_profile_declares_minimal_stage_native_state_shell() -> None:
    profile = _profile()

    assert profile["surface_kind"] == "mas_opl_stage_run_kernel_profile"
    assert profile["version"] == "stage-run-kernel-profile.v1"
    assert profile["domain_id"] == "med-autoscience"
    assert profile["state"] == "active_contract"
    assert profile["stage_native_unit"] == [
        "stage_folder",
        "stage_manifest",
        "role_artifacts",
        "owner_receipt_or_typed_blocker",
    ]
    assert profile["kernel_role"] == "minimal_state_shell_not_mas_controller_system"
    assert profile["stage_folder_manifest_role"] == "artifact_evidence_and_structure_contract"
    assert profile["transition_authority"] == "mas_owner_receipt_or_typed_blocker_only"

    assert profile["required_object_models"] == [
        "StageRun",
        "ArtifactRef",
        "OwnerReceipt",
        "TypedBlocker",
        "ReadModel",
    ]


def test_stage_folder_manifest_foundation_requires_role_artifacts_and_receipts() -> None:
    manifest = _profile()["stage_folder_manifest"]

    assert manifest["manifest_file_name"] == "stage_manifest.json"
    assert manifest["stage_folder_contract_ref"] == (
        "contracts/opl-framework/stage-artifact-runtime-contract.json"
    )
    assert manifest["required_directories"] == [
        "inputs",
        "outputs",
        "receipts",
        "lineage",
        "projection",
    ]
    assert manifest["required_manifest_sections"] == [
        "stage_run_ref",
        "required_input_artifact_refs",
        "required_role_artifacts",
        "produced_artifact_refs",
        "owner_receipt_refs",
        "typed_blocker_refs",
        "lineage_refs",
        "projection_refs",
    ]
    assert manifest["role_artifact_contract"]["file_name_is_interface"] is False
    assert manifest["role_artifact_contract"]["role_is_interface"] is True
    assert manifest["role_artifact_contract"]["artifact_ref_body_included"] is False
    assert manifest["closeout_contract"]["requires_owner_receipt_or_typed_blocker"] is True
    assert manifest["closeout_contract"]["output_only_stage_folder_is_orphan"] is True
    assert manifest["projection_contract"]["projection_directory_is_authority"] is False


def test_opl_contract_refs_are_external_consumer_refs_not_repo_local_truth() -> None:
    refs = _profile()["opl_contract_refs"]

    assert refs["owner"] == "one-person-lab"
    assert refs["domain_repo_role"] == "consumer_profile_ref_only"
    assert refs["repo_local_file_required"] is False
    assert refs["local_resolution_policy"] == "do_not_copy_opl_framework_contracts_into_domain_repo"
    assert refs["refs"] == [
        "contracts/opl-framework/stage-run-kernel-contract.json",
        "contracts/opl-framework/stage-manifest.schema.json",
        "contracts/opl-framework/role-artifact-ref.schema.json",
        "contracts/opl-framework/stage-owner-receipt.schema.json",
        "contracts/opl-framework/stage-typed-blocker.schema.json",
        "contracts/opl-framework/stage-artifact-runtime-contract.json",
    ]


def test_stage_run_states_keep_provider_and_domain_closeout_separate() -> None:
    states = _profile()["stage_run_state_machine"]

    assert states["main_chain"] == [
        "Declared",
        "InputsReady",
        "Admitted",
        "Running",
        "Terminalizing",
        "DomainAccepted",
        "NextStageReady",
    ]
    assert {
        "NeedsHumanDecision",
        "NeedsExternalResource",
        "RetryScheduled",
        "TypedBlocked",
        "InfrastructureCrashed",
        "Superseded",
    } <= set(states["exception_states"])
    assert states["terminal_transition_authority"]["DomainAccepted"] == (
        "MAS consumes closeout and signs OwnerReceipt or TypedBlocker"
    )
    assert states["terminal_transition_authority"]["NextStageReady"] == (
        "route emitted from accepted OwnerReceipt or stable TypedBlocker"
    )
    assert states["provider_completion_counts_as_domain_accepted"] is False
    assert states["stage_folder_files_count_as_next_stage_ready"] is False


def test_ordinary_progress_handoff_accepts_t0_progress_delta_without_ready_claims() -> None:
    handoff = _profile()["ordinary_progress_handoff"]

    assert handoff["surface_kind"] == "mas_ordinary_progress_handoff_policy"
    assert handoff["version"] == "ordinary-progress-handoff.v1"
    assert handoff["default_progress_root"] == "current_owner_delta"
    assert handoff["stage_goal_source"] == "stage_run_current_owner_delta"
    assert handoff["executor_output_requirement"] == "concrete_delta"
    assert handoff["accepted_closeout_shapes"] == [
        "ProgressDeltaReceipt",
        "OwnerReceipt",
        "TypedBlocker",
        "human_gate_ref",
        "route_back_ref",
    ]

    progress_receipt = handoff["progress_delta_receipt"]
    assert progress_receipt["receipt_kind"] == "ProgressDeltaReceipt"
    assert progress_receipt["artifact_tier"] == "T0_progress_delta"
    assert progress_receipt["role"] == "ordinary_step_handoff_not_stage_completion"
    assert {
        "changed_surface_refs",
        "produced_refs",
        "consumed_refs",
        "progress_delta_classification",
        "deliverable_progress_delta",
        "platform_repair_delta",
        "next_owner",
        "next_required_delta",
    } <= set(progress_receipt["required_fields"])
    assert {
        "domain_ready",
        "publication_ready",
        "submission_ready",
        "quality_or_export_ready",
        "artifact_authority",
        "memory_accept_reject",
        "production_ready",
        "physical_delete",
    } <= set(progress_receipt["cannot_authorize"])

    artifact_policy = handoff["artifact_tier_policy"]
    assert artifact_policy["tiers"] == [
        "T0_progress_delta",
        "T1_stage_transition",
        "T2_delivery_artifact",
        "T3_production_evidence",
    ]
    assert artifact_policy["default_tier"] == "T0_progress_delta"
    assert artifact_policy["ordinary_delta_requires_full_stage_artifact_manifest"] is False
    assert artifact_policy["delivery_or_publication_claim_requires_tier"] == [
        "T2_delivery_artifact",
        "T3_production_evidence",
    ]

    readiness = handoff["readiness_jit_policy"]
    assert readiness["default_mode"] == "just_in_time_for_current_delta"
    assert readiness["check_scope_source"] == "stage_run_current_owner_delta.next_required_delta"
    assert readiness["full_readiness_inventory_role"] == "audit_or_terminal_gate_only"
    assert readiness["cannot_require_all_surfaces_before_writing_analysis_or_review_delta"] is True

    sidecar = handoff["audit_sidecar_policy"]
    assert sidecar["can_generate_default_next_action"] is False
    assert sidecar["can_close_stage"] is False
    assert sidecar["can_claim_domain_ready"] is False


def test_stage_run_object_models_capture_stage_folder_manifest_and_receipt_refs() -> None:
    models = _profile()["object_models"]

    assert models["StageRun"]["owner"] == "opl_runtime_with_mas_stage_spec"
    assert models["StageRun"]["required_fields"] == [
        "stage_run_id",
        "program_id",
        "study_id",
        "stage_id",
        "generation",
        "spec_ref",
        "status",
        "observed_generation",
        "stage_folder_ref",
        "stage_manifest_ref",
        "event_log_ref",
    ]
    assert models["StageRun"]["authority_boundary"]["owns_medical_quality"] is False
    assert models["StageRun"]["authority_boundary"]["can_mutate_domain_artifact_body"] is False

    assert models["ArtifactRef"]["owner"] == "mas_authority_or_opl_locator"
    assert {
        "artifact_ref",
        "role",
        "content_hash",
        "lineage_ref",
        "stage_manifest_ref",
        "body_included",
    } <= set(models["ArtifactRef"]["required_fields"])
    assert models["ArtifactRef"]["body_included"] is False
    assert models["ArtifactRef"]["file_presence_counts_as_completion"] is False

    assert models["OwnerReceipt"]["owner"] == "med-autoscience"
    assert models["OwnerReceipt"]["transition_authority"] == "success_or_route_handoff"
    assert "consumed_artifact_refs" in models["OwnerReceipt"]["required_fields"]
    assert "produced_artifact_refs" in models["OwnerReceipt"]["required_fields"]

    assert models["TypedBlocker"]["owner"] == "med-autoscience"
    assert models["TypedBlocker"]["transition_authority"] == "blocked_or_deferred_domain_outcome"
    assert {
        "blocker_type",
        "blocking_owner",
        "blocked_surface",
        "required_input_refs",
        "next_safe_action_ref",
    } <= set(models["TypedBlocker"]["required_fields"])

    assert models["ReadModel"]["owner"] == "opl_or_product_projection"
    assert models["ReadModel"]["authority_boundary"]["rebuildable_projection"] is True
    assert models["ReadModel"]["authority_boundary"]["can_write_transition"] is False
    assert models["ReadModel"]["authority_boundary"]["can_promote_latest_to_authority"] is False


def test_coscientist_strategy_refs_stay_within_stage_and_advisory() -> None:
    boundary = _profile()["coscientist_stage_strategy_boundary"]

    assert boundary["stage_scope"] == "within_stage_execution_strategy_and_evidence_refs"
    assert boundary["strategy_refs"] == [
        "candidate_generation_refs",
        "reflection_refs",
        "review_refs",
        "meta_review_refs",
        "ranking_refs",
        "proximity_refs",
        "evolution_refs",
    ]
    assert boundary["strategy_refs_are_advisory"] is True
    assert boundary["strategy_refs_can_define_hardcoded_workflow"] is False
    assert boundary["strategy_refs_can_close_quality_gate"] is False
    assert boundary["strategy_refs_can_promote_stage"] is False
    assert boundary["quality_gate_requires_independent_reviewer_or_auditor_receipt"] is True
    assert boundary["promotion_requires_owner_receipt_or_stable_typed_blocker"] is True
    assert boundary["progress_jit_affordance_role"] == (
        "current_owner_native_jit_affordance_not_control_surface"
    )
    assert boundary["progress_jit_affordance_mechanisms"] == [
        "next_delta_tournament",
        "bounded_micro_candidate_generation",
        "critique_as_repair_hint",
        "reusable_lesson_extraction",
        "triggered_meta_review",
        "opportunistic_knowledge_prefetch",
    ]
    assert boundary["progress_jit_affordance_can_block_attempt_when_missing"] is False
    assert boundary["next_delta_tournament_authorizes"] == "single_next_attempt_only"
    assert boundary["micro_candidate_unselected_branch_blocks_route"] is False
    assert boundary["critique_hint_can_close_quality_gate"] is False
    assert boundary["reusable_lesson_max_refs_per_invoked_attempt"] == 1
    assert boundary["meta_review_triggered_only_by"] == [
        "stop_loss_candidate",
        "repeated_failure",
        "human_gate_pressure",
        "claim_boundary_drift",
        "no_loop_budget_exhausted",
    ]
    assert boundary["opportunistic_prefetch_mainline_waits"] is False
    assert boundary["platform_repair_or_prefetch_counts_as_paper_progress"] is False


def test_stage_run_kernel_boundary_keeps_mas_authority_and_opl_runtime_substrate_distinct() -> None:
    boundary = _profile()["opl_mas_boundary"]

    assert boundary["opl_owns"] == [
        "stage_run_spec_status",
        "event_log",
        "queue",
        "hold",
        "admission",
        "lease",
        "attempt",
        "retry_dead_letter",
        "projection_rebuild",
    ]
    assert boundary["mas_owns"] == [
        "stage_semantics",
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "memory_accept_reject",
        "owner_receipt",
        "typed_blocker",
        "route_decision",
    ]
    assert boundary["forbidden_opl_authority"] == [
        "write_mas_study_truth",
        "write_publication_eval_as_authority",
        "write_controller_decision_as_authority",
        "mutate_domain_artifact_body",
        "authorize_publication_quality",
        "sign_mas_owner_receipt",
        "replace_mas_typed_blocker",
    ]
    assert boundary["forbidden_mas_claims"] == [
        "mas_owns_generic_queue",
        "mas_owns_generic_attempt_ledger",
        "mas_owns_generic_state_machine_runner",
        "mas_owns_generic_read_model_shell",
        "mas_controller_system_required_for_stage_run_kernel",
    ]


def test_legacy_runtime_wrappers_are_retired_to_diagnostic_or_provenance_roles() -> None:
    retirement = _profile()["legacy_runtime_wrapper_retirement"]

    assert retirement["retired_mas_local_surfaces"] == [
        "generic_scheduler",
        "generic_runner",
        "generic_session_store",
        "generic_status_shell",
        "generic_workbench_wrapper",
        "generic_lifecycle_wrapper",
        "generic_attempt_ledger",
        "generic_queue",
    ]
    assert retirement["allowed_roles"] == [
        "migration_input",
        "diagnostic_projection",
        "provenance_tombstone",
        "domain_authority_function_target",
    ]
    assert retirement["allowed_domain_retained_surfaces"] == [
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "owner_receipt",
        "typed_blocker",
        "domain_knowledge",
        "domain_skill",
        "domain_tool",
        "domain_quality_gate",
        "safe_action_ref",
    ]
    assert "mas_owns_workbench_wrapper" in retirement["forbidden_resurrection_claims"]
    assert retirement["new_mas_local_wrapper_requires"] == [
        "mas_domain_authority_reason",
        "active_caller_ref",
        "no_opl_generated_parity_ref",
        "receipt_or_blocker_output_boundary",
        "retirement_gate_ref",
    ]


def test_projection_surfaces_are_explicitly_forbidden_as_transition_authority() -> None:
    projection = _profile()["projection_boundary"]

    assert projection["read_models_are_rebuildable"] is True
    assert projection["latest_progress_portal_and_workbench_are_projection_only"] is True
    assert projection["forbidden_transition_authority"] == [
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "study_progress_projection",
        "runtime_watch_projection",
        "portal_or_workbench_status",
        "stage_folder_file_presence",
        "provider_completion",
        "active_run_id_presence",
    ]
    assert projection["allowed_projection_inputs"] == [
        "StageRun_event_log",
        "stage_manifest_ref",
        "artifact_refs",
        "owner_receipt_refs",
        "typed_blocker_refs",
        "current_owner_delta_ref",
    ]
    assert projection["projection_can_write_truth"] is False
    assert projection["projection_can_authorize_next_stage"] is False


def test_stage_artifact_kernel_adoption_links_stage_run_kernel_profile_as_refs_only_contract() -> None:
    binding = _adoption()["stage_run_kernel_profile_binding"]

    assert binding["profile_ref"] == "contracts/stage_run_kernel_profile.json"
    assert binding["profile_role"] == "minimal_stage_native_state_shell"
    assert binding["stage_run_kernel_is_mas_controller_system"] is False
    assert binding["read_model_is_transition_authority"] is False
    assert binding["terminal_transition_authority"] == "owner_receipt_or_typed_blocker"


def test_stage_run_canary_requires_coscientist_refs_without_legacy_wrapper_authority() -> None:
    canary = _profile()["canary_scope"]

    assert canary["first_stage_spec_id"] == "ai_reviewer_publication_eval_rebuild"
    assert canary["controlled_canary_evidence_ref"] == "contracts/stage_run_canary_evidence.json"
    assert canary["controlled_canary_evidence_scope"] == "controlled_fixture_not_live_domain_progress"
    assert canary["target_studies"] == ["DM002", "DM003"]
    assert canary["coscientist_strategy_refs_required"] == [
        "candidate_generation_refs",
        "reflection_refs",
        "review_refs",
        "meta_review_refs",
    ]
    assert canary["coscientist_strategy_refs_authority"] == "advisory_within_stage_only"
    assert canary["canary_success_requires"] == [
        "fresh_owner_receipt_or_stable_typed_blocker",
        "stage_run_status_matches_stage_manifest",
        "study_progress_projects_stage_run_status",
        "latest_json_is_projection_not_route_authority",
        "no_legacy_scheduler_runner_session_store_status_shell_or_workbench_wrapper_authority",
    ]


def test_controlled_stage_run_canary_evidence_shape_is_locked() -> None:
    evidence = _controlled_canary_evidence()
    canary = _profile()["canary_scope"]

    assert evidence["surface_kind"] == "opl_stage_run_controlled_canary_evidence"
    assert evidence["version"] == "stage-run-controlled-canary.v1"
    assert evidence["domain_id"] == "med-autoscience"
    assert evidence["canary_id"] == "mas_stage_run_controlled_canary_ai_reviewer_publication_eval_rebuild"
    assert evidence["stage_id"] == canary["first_stage_spec_id"]
    assert evidence["evidence_scope"] == "controlled_fixture_not_live_domain_progress"
    assert canary["controlled_canary_evidence_ref"] == "contracts/stage_run_canary_evidence.json"
    assert canary["controlled_canary_evidence_scope"] == evidence["evidence_scope"]

    for ref_field in ("stage_run_ref", "stage_manifest_ref", "current_pointer_ref"):
        ref = evidence[ref_field]
        assert ref["ref"]
        assert ref["body_included"] is False

    strategy_trace = evidence["strategy_trace"]
    assert list(strategy_trace) == [
        "candidate_generation",
        "grounded_reflection",
        "comparative_selection",
        "evolution_and_revision",
        "meta_review_learning",
        "independent_quality_gate",
    ]
    for strategy in strategy_trace.values():
        assert strategy["refs"]
        assert strategy["can_closeout"] is False
        for ref in strategy["refs"]:
            assert ref["ref"]
            assert ref["body_included"] is False


def test_controlled_stage_run_canary_role_artifacts_and_closeout_are_refs_only() -> None:
    evidence = _controlled_canary_evidence()

    expected_role_artifacts = [
        "candidate_pool_ref",
        "reflection_review_ref",
        "ranking_selection_ref",
        "revision_lineage_ref",
        "meta_review_ref",
        "independent_gate_ref",
    ]
    role_artifacts = evidence["role_artifact_refs"]
    assert list(role_artifacts) == expected_role_artifacts
    assert evidence["controlled_stage_folder"]["stage_manifest"]["required_role_artifacts"] == (
        expected_role_artifacts
    )
    for artifact_name, artifact in role_artifacts.items():
        assert artifact["role"] == artifact_name
        assert artifact["ref"]
        assert artifact["body_included"] is False

    closeout = evidence["closeout"]
    assert closeout["terminal_outcome"] in {"owner_receipt", "typed_blocker"}
    assert "owner_receipt_ref" in closeout or "typed_blocker_ref" in closeout
    assert closeout["same_attempt_self_review"] is False
    if "owner_receipt_ref" in closeout:
        assert closeout["owner_receipt_ref"]["ref"]
        assert closeout["owner_receipt_ref"]["body_included"] is False
    if "typed_blocker_ref" in closeout:
        assert closeout["typed_blocker_ref"]["ref"]
        assert closeout["typed_blocker_ref"]["body_included"] is False


def test_controlled_stage_run_canary_authority_boundary_forbids_live_progress_claims() -> None:
    evidence = _controlled_canary_evidence()

    assert evidence["authority_boundary"] == {
        "refs_only": True,
        "controlled_canary_claims_live_domain_progress": False,
        "provider_completion_counts_as_closeout": False,
        "file_presence_counts_as_closeout": False,
        "read_model_counts_as_closeout": False,
        "conformance_pass_counts_as_closeout": False,
        "opl_can_write_domain_truth": False,
        "opl_can_mutate_artifact_body": False,
        "opl_can_sign_owner_receipt": False,
        "opl_can_create_typed_blocker": False,
        "opl_can_authorize_quality_or_export": False,
    }
    assert evidence["claim_boundary"] == {
        "claims_live_domain_progress": False,
        "claims_paper_closure": False,
        "claims_publication_ready": False,
        "claims_artifact_mutation_authorized": False,
        "claims_current_package_updated": False,
    }


def test_controlled_canary_operator_summary_is_read_model_only_and_fails_closed_on_overclaim() -> None:
    profile = _profile()
    evidence = _controlled_canary_evidence()
    contract = profile["controlled_canary_operator_summary_contract"]
    summary = evidence["controlled_canary_operator_summary"]
    boundary = evidence["overclaim_boundary"]

    assert contract["summary_ref"] == (
        "contracts/stage_run_canary_evidence.json#/controlled_canary_operator_summary"
    )
    assert contract["summary_role"] == "operator_read_model_summary_not_domain_truth"
    assert contract["required_sections"] == [
        "controlled_canary_operator_summary",
        "overclaim_boundary",
        "legacy_runtime_residue_guard",
    ]
    assert contract["required_completion_classification"] == "platform_repair_controlled_fixture"
    assert contract["allowed_operator_claims_are_closed_set"] is True
    assert contract["operator_summary_can_write_domain_truth"] is False
    assert contract["operator_summary_can_close_stage"] is False
    assert contract["operator_summary_can_resume_dm002_dm003"] is False

    assert summary["summary_kind"] == "controlled_canary_operator_summary"
    assert summary["scope"] == contract["summary_role"]
    assert summary["completion_classification"] == contract["required_completion_classification"]
    assert summary["stage_run_ref"] == evidence["stage_run_ref"]["ref"]
    assert summary["current_status"] == evidence["controlled_stage_folder"]["current_pointer"]["status"]
    assert summary["body_included"] is False
    assert summary["overclaim_boundary_ref"] == (
        "contracts/stage_run_canary_evidence.json#/overclaim_boundary"
    )
    assert summary["legacy_runtime_residue_guard_ref"] == (
        "contracts/stage_run_canary_evidence.json#/legacy_runtime_residue_guard"
    )

    assert boundary["boundary_kind"] == "controlled_canary_operator_overclaim_boundary"
    assert boundary["must_classify_as"] == contract["required_completion_classification"]
    assert boundary["overclaim_guard_fails_closed"] is True
    assert summary["operator_claims"] == boundary["allowed_operator_claims"]
    assert summary["forbidden_operator_claims"] == boundary["forbidden_operator_claims"]
    assert {
        "live_dm002_dm003_domain_progress",
        "paper_closure",
        "publication_ready",
        "artifact_mutation_authorized",
        "current_package_updated",
        "legacy_runtime_residue_authorizes_transition",
    } <= set(summary["forbidden_operator_claims"])
    assert set(contract["forbidden_operator_claims_must_include"]) <= set(
        summary["forbidden_operator_claims"]
    )
    assert "legacy_runtime_residue_authorizes_transition" in boundary["forbidden_operator_claims"]
    assert evidence["claim_boundary"]["claims_live_domain_progress"] is False
    assert evidence["claim_boundary"]["claims_paper_closure"] is False
    assert evidence["claim_boundary"]["claims_publication_ready"] is False


def test_controlled_canary_legacy_runtime_residue_guard_cannot_authorize_transition() -> None:
    profile = _profile()
    evidence = _controlled_canary_evidence()
    contract = profile["controlled_canary_operator_summary_contract"]
    guard = evidence["legacy_runtime_residue_guard"]
    retirement = profile["legacy_runtime_wrapper_retirement"]

    assert guard["guard_kind"] == "legacy_runtime_residue_transition_authority_guard"
    assert guard["retired_surfaces"] == retirement["retired_mas_local_surfaces"]
    assert guard["allowed_roles"] == [
        "migration_input",
        "diagnostic_projection",
        "provenance_tombstone",
    ]
    assert set(guard["allowed_roles"]) <= set(retirement["allowed_roles"])
    assert guard["residue_presence_counts_as_stage_progress"] is False
    assert guard["residue_presence_counts_as_closeout"] is False
    assert guard["operator_summary_must_not_promote_residue"] is True
    assert contract["legacy_runtime_residue_can_authorize_transition"] is False
    assert {
        "stage_transition",
        "domain_closeout",
        "publication_quality_verdict",
        "artifact_mutation_authorization",
        "owner_receipt_signature",
        "typed_blocker_replacement",
    } == set(guard["forbidden_authority"])
