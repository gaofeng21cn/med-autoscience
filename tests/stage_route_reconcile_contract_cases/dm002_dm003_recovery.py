from __future__ import annotations

from typing import Any


def assert_dm002_dm003_recovery_acceptance(contract: dict[str, Any]) -> None:
    recovery = contract["dm002_dm003_recovery_acceptance_policy"]
    assert recovery["surface_kind"] == "mas_opl_dm002_dm003_recovery_acceptance_policy"
    assert recovery["state"] == "active_recovery_acceptance_contract"

    truth = recovery["fresh_truth_policy"]
    assert truth["contract_must_not_be_used_as_current_truth"] is True
    assert truth["live_status_must_be_refreshed_before_acceptance"] is True
    assert {
        "current_stage",
        "active_run_id",
        "current_work_unit.status",
        "current_work_unit.blocker_type_or_reason",
        "current_work_unit.owner",
        "current_work_unit.action_type",
        "current_work_unit.work_unit_id",
        "current_work_unit.work_unit_fingerprint",
        "provider_admission_pending_count",
        "provider_admission_candidates",
        "action_queue",
        "strict_provider_running_proof",
        "owner_receipt_or_typed_blocker_refs",
    } <= set(truth["fresh_readback_required_for_fields"])
    assert truth["drift_handling"] == (
        "if_recent_sample_conflicts_with_fresh_readback_use_fresh_readback_and_treat_sample_as_non_authoritative_context"
    )

    samples = recovery["recent_non_authoritative_samples"]
    assert samples["purpose"] == "debug context only; not acceptance truth"
    assert samples["samples_may_be_stale"] is True
    assert samples["latest_recorded_at"] == "2026-06-13"
    examples = {sample["study_id"]: sample for sample in samples["examples"]}
    assert set(examples) == {
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    }
    assert examples["002-dm-china-us-mortality-attribution"] == {
        "study_id": "002-dm-china-us-mortality-attribution",
        "observed_current_stage": "queued",
        "observed_paper_stage": "publishability_gate_blocked",
        "observed_active_run_id": None,
        "observed_current_work_unit_status": "typed_blocker",
        "observed_blocker": "stage_packet_not_current_selected_dispatch",
        "owner": "one-person-lab",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "dhd_action_class": "observe_only",
        "will_start_llm": False,
        "codex_dispatch_count": 0,
    }
    assert examples["003-dpcc-primary-care-phenotype-treatment-gap"] == {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "observed_current_stage": "queued",
        "observed_paper_stage": "analysis-campaign",
        "observed_active_run_id": None,
        "observed_current_work_unit_status": "typed_blocker",
        "observed_blocker": "medical_publication_surface_blocked",
        "owner": "one-person-lab",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "dhd_action_class": "observe_only",
        "will_start_llm": False,
        "codex_dispatch_count": 0,
    }

    stop_loss = recovery["same_work_unit_stop_loss_policy"]
    assert stop_loss["blocker"] == "anti_loop_budget_exhausted"
    assert stop_loss["owner_source"] == "fresh_current_work_unit_owner"
    assert stop_loss["same_work_unit_redrive_allowed"] is False
    assert stop_loss["applies_only_when_fresh_current_blocker_matches"] is True
    assert {
        "new_work_unit_identity",
        "successor_stage_run_identity",
        "human_gate_ref",
        "route_back_evidence_ref",
    } <= set(stop_loss["allowed_reopen_conditions"])
    assert {
        "same_work_unit_provider_admission_redrive",
        "same_work_unit_default_executor_dispatch",
        "foreground_codex_retry_of_repair_batch",
        "replaying_stale_action_queue_or_provider_admission",
    } <= set(stop_loss["forbidden_recovery_actions"])

    typed_blocker = recovery["current_typed_blocker_recovery_policy"]
    assert typed_blocker["blocker_source"] == "fresh_current_work_unit_blocker_type_or_reason"
    assert typed_blocker["owner_source"] == "fresh_current_work_unit_owner"
    assert {
        "medical_paper_readiness_missing",
        "medical_publication_surface_blocked",
        "stage_packet_not_current_selected_dispatch",
    } <= set(typed_blocker["known_recent_blocker_classes"])
    assert typed_blocker["blocker_only_can_execute_complete_readiness_surface"] is False
    assert {
        "specific_mas_owner_callable",
        "derived_repair_action_with_current_work_unit_binding",
        "stable_typed_blocker_with_named_missing_ref_family",
    } <= set(typed_blocker["must_be_consumed_by_any"])
    assert typed_blocker["provider_admission_blocked_when_current_work_unit_is_typed_blocker"] is True
    assert typed_blocker["progress_first_admission_projection_policy"] == (
        "projection_may_exist_but_admission_requested_false_until_current_typed_blocker_is_consumed_or_superseded"
    )
    assert typed_blocker["derived_repair_action_required_fields"] == [
        "stage_typed_blocker_ref",
        "publication_eval_id",
        "gap_ids",
        "work_unit_fingerprint",
        "required_output_contract",
    ]
    assert typed_blocker["derived_repair_action_required_outputs_any"] == [
        "canonical_manuscript_story_surface_delta",
        "claim_evidence_semantic_delta",
        "review_ledger_delta",
        "publication_gate_delta",
        "stage_owner_receipt_ref",
        "stable_typed_blocker_for_the_specific_repair_work_unit",
    ]
    assert {
        "foreground_codex_completion_of_readiness_surface",
        "stale_gate_replay_or_transition_dispatch",
        "provider_admission_without_current_executable_owner_action",
        "paper_local_manuscript_or_package_edit_without_owner_callable",
    } <= set(typed_blocker["forbidden_recovery_actions"])

    assert set(recovery["acceptance_requires_any"]) == {
        "mas_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "canonical_changed_surface_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
        "strict_provider_running_proof_for_same_current_identity",
    }
    assert recovery["recovery_resumption_acceptance"] == [
        "strict_provider_running_proof_for_same_current_identity"
    ]
    assert "strict_provider_running_proof_for_same_current_identity" not in recovery[
        "paper_progress_acceptance"
    ]
    assert recovery["required_readback"] == [
        "fresh_study_progress_for_dm002",
        "fresh_study_progress_for_dm003",
        "domain_health_diagnostic_dry_run_readback",
        "provider_admission_pending_count_readback",
        "owner_receipt_or_typed_blocker_ref_readback",
    ]
    assert {
        "foreground_codex_message",
        "docs_only_claim",
        "queue_empty_without_owner_delta",
        "provider_completion_without_mas_closeout_consumption",
        "stale_runtime_attempt_or_active_run_id",
        "stage_artifact_file_presence_without_owner_receipt",
    } <= set(recovery["forbidden_acceptance_evidence"])


def assert_dm002_dm003_conformance_invariants(contract: dict[str, Any]) -> None:
    conformance = contract["stage_route_conformance_invariants"]
    assert conformance["surface_kind"] == "mas_opl_stage_route_conformance_invariants"
    assert conformance["state"] == "active_contract"
    assert conformance["scope"] == [
        "DM002",
        "DM003",
        "stage-route currentness",
        "paper-recovery obligation",
        "OPL StageRun authorization",
        "terminal closeout accounting",
    ]

    false_authority = conformance["false_authority_generation_invariant"]
    assert false_authority["domain_authority_requires_any"] == [
        "mas_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "canonical_changed_surface_ref_consumed_by_mas",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
        "mas_closeout_consumption_or_rejection_ref",
    ]
    assert {
        "queue_entry",
        "queue_empty",
        "active_run_id",
        "transport_status",
        "trace_span_ref",
        "lineage_ref",
        "read_model_projection",
        "stale_persisted_dispatch",
        "old_route_back_packet",
        "provider_completion",
    } <= set(false_authority["forbidden_domain_authority_sources"])
    assert false_authority["violation_effect"] == (
        "diagnostic_only_no_owner_delta_no_paper_progress_no_provider_admission"
    )

    owner_path = conformance["unique_current_owner_path_invariant"]
    assert owner_path["only_chain"] == [
        "current_owner_delta",
        "current_work_unit",
        "current_execution_envelope",
        "provider_admission_current_control",
        "OPLStageRun",
        "terminal_closeout",
        "MAS_closeout_consume_or_reject",
        "next_current_owner_delta",
    ]
    assert owner_path["mas_closeout_step"] == "consume_or_reject_required"
    assert owner_path["same_work_unit_feedback_requires_any"] == [
        "new_work_unit_identity",
        "mas_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "canonical_changed_surface_ref_consumed_by_mas",
        "stable_typed_blocker_ref_with_new_blocker_identity",
        "human_gate_ref",
        "route_back_evidence_ref",
        "successor_recovery_obligation_ref",
    ]
    assert owner_path["forbidden_shortcuts"] == [
        "current_work_unit_from_active_run_id",
        "provider_admission_from_typed_blocker_only",
        "OPLStageRun_from_stale_dispatch",
        "next_owner_delta_from_provider_completion",
        "next_owner_delta_from_read_model_or_trace_only",
    ]

    self_auth = conformance["typed_blocker_self_authorization_invariant"]
    assert self_auth["typed_blocker_can_self_authorize_provider_admission"] is False
    assert self_auth["typed_blocker_can_self_authorize_readiness_execution"] is False
    assert self_auth["typed_blocker_can_become_owner_receipt"] is False
    assert self_auth["allowed_exits"] == [
        "specific_mas_owner_callable",
        "derived_repair_action_with_current_work_unit_binding",
        "stable_typed_blocker_with_named_missing_ref_family",
        "human_gate_ref_when_domain_owner_cannot_continue",
        "route_back_evidence_ref",
    ]

    selected_dispatch = conformance[
        "stage_packet_not_current_selected_dispatch_invariant"
    ]
    assert selected_dispatch["blocker"] == "stage_packet_not_current_selected_dispatch"
    assert selected_dispatch["owner"] == "one-person-lab"
    assert selected_dispatch["blocker_classification"] == "OPL_authorization_blocker"
    assert selected_dispatch["must_route_through_any"] == [
        "OPL_authorization_repair_owner_action",
        "derived_repair_action_with_current_work_unit_binding",
        "successor_recovery_obligation_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert selected_dispatch["same_work_unit_redrive_allowed"] is False
    assert selected_dispatch["forbidden_actions"] == [
        "same_work_unit_default_executor_dispatch",
        "same_work_unit_provider_admission_redrive",
        "stale_stage_packet_replay",
        "foreground_gate_replay_retry_without_owner_binding",
    ]

    closeout = conformance["terminal_closeout_accounting_invariant"]
    assert closeout["stage_log_field"] == "paper_stage_log"
    assert {
        "stage_name",
        "stage_goal",
        "stage_work_done",
        "paper_work_done",
        "duration",
        "token_usage",
        "cost",
        "usage_refs",
        "cost_refs",
        "progress_delta_classification",
        "deliverable_progress_delta",
        "paper_progress_delta",
        "platform_repair_delta",
        "next_forced_delta",
        "evidence_refs",
    } <= set(closeout["required_or_missing_with_reason_fields"])
    assert closeout["missing_field_shape"] == {
        "status": "missing_with_reason",
        "reason": "explicit_required_field_unavailable",
        "source_refs": "refs_only",
    }
    assert closeout["missing_without_reason_effect"] == (
        "consume_terminal_closeout_as_typed_blocker"
    )
    assert closeout["missing_without_reason_typed_blocker"] == (
        "domain_closeout_provided_incomplete_user_stage_log"
    )
    assert closeout["automatic_redrive_allowed_when_incomplete"] is False
