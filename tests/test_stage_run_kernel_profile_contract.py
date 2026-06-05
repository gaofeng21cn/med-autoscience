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
