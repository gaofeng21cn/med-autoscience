from __future__ import annotations

from typing import Any


def assert_opl_follow_through_and_external_practice_mapping(
    contract: dict[str, Any],
) -> None:
    provider_identity = contract["identity_policy"]["provider_admission_identity_contract"]
    assert provider_identity["required_fields"] == [
        "study_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "dispatch_path_or_ref",
        "currentness_basis",
        "route_identity_key",
        "attempt_idempotency_key",
    ]
    assert provider_identity["currentness_basis_required_fields"] == [
        "work_unit_id",
        "work_unit_fingerprint",
        "truth_epoch",
        "runtime_health_epoch_or_source_eval_id",
    ]
    assert provider_identity["weak_identity_decision"] == "weak_provider_admission_identity"
    assert provider_identity["weak_identity_effect"] == "suppress_provider_admission_pending"
    assert provider_identity["fingerprintless_stop_loss_closeout_match"] == (
        "requires_same_source_eval_truth_or_runtime_health_epoch"
    )
    assert provider_identity["action_id_role"] == (
        "action_family_only_not_route_or_attempt_identity"
    )
    record_only = provider_identity["record_only_closeout_consumption_policy"]
    assert record_only["record_only_owner_refs_are_identity"] is False
    assert record_only["accepted_record_only_closeout_required_any"] == [
        "native_work_unit_fingerprint_or_action_fingerprint",
        "route_identity_key_or_attempt_idempotency_key_match",
        "matching_owner_route_currentness_basis",
        "matching_source_eval_id",
        "matching_truth_and_runtime_health_epoch",
    ]
    assert record_only["record_ref_only_effect"] == (
        "audit_only_retain_provider_admission_pending"
    )
    assert record_only["identity_fill_for_candidate_root_closeout"] == (
        "may_fill_action_type_and_work_unit_id_only; must_not_fill_fingerprint_source_eval_or_epochs_from_candidate"
    )

    arbiter = contract["stage_route_arbiter_surface"]
    accepted_closeout = next(
        item
        for item in arbiter["decision_kinds"]
        if item["decision"] == "accepted_closeout_consumed_pending"
    )
    assert accepted_closeout["record_only_closeout_policy_ref"] == (
        "identity_policy.provider_admission_identity_contract.record_only_closeout_consumption_policy"
    )
    assert {
        "record_only_owner_ref_without_native_fingerprint_or_currentness_basis",
        "action_and_work_unit_only_record_ref_match",
        "candidate_fingerprint_filled_into_closeout_without_native_identity",
    } <= set(accepted_closeout["forbidden_match"])

    follow_through = contract["required_opl_follow_through"]
    assert follow_through["source"] == "one-person-lab read-only substrate audit 2026-06-12"
    assert {
        "current_owner_delta ordinary planning root",
        "StageRun launch and closeout admission boundary",
        "attempt ledger terminal observation",
        "worker_source_stale supervised restart guard",
    } <= set(follow_through["already_supported"])
    assert follow_through["remaining_mas_consumption_gaps"] == []

    capabilities = {
        item["capability"]: item
        for item in follow_through["opl_covered_and_mas_consumes"]
    }
    assert capabilities["terminal_closeout_precedes_live_projection"][
        "identity_mismatch_effect"
    ] == "fail_closed_currentness_blocker"
    assert capabilities["terminal_closeout_precedes_live_projection"][
        "mas_consumption_surface"
    ] == "stage_route_arbiter_surface.terminal_closeout_precedes_live_projection"
    assert {
        "stage_run_id",
        "stage_run_generation",
        "stage_manifest_ref",
        "current_pointer_ref",
        "source_fingerprint",
        "domain_source_fingerprint",
        "idempotency_key",
        "provider_attempt_ref",
        "active_lease_ref",
        "execution_authorization_ref",
        "workflow_id",
        "task_id",
        "provider_admission_identity",
        "provider_admission_identity_key",
        "route_identity_key",
        "attempt_idempotency_key",
        "owner_route_currentness_basis",
    } <= set(capabilities["stage_run_currentness_identity"]["required_fields"])
    assert "embedded verbatim" in capabilities["stage_run_currentness_identity"][
        "required_effect"
    ]
    assert capabilities["stage_run_currentness_identity"]["mas_consumption_surface"] == (
        "identity_policy.provider_admission_identity_contract"
    )
    assert "automatic-redrive stop" in capabilities["no_progress_budget_contract"][
        "required_effect"
    ]
    assert capabilities["no_progress_budget_contract"]["mas_consumption_surface"] == (
        "anti_loop_policy"
    )
    assert capabilities["stage_log_minimum_viability_contract"]["required_effect"] == (
        "terminal closeout missing required user-stage-log domain fields is consumed as "
        "domain_closeout_provided_incomplete_user_stage_log typed blocker, receives no "
        "paper-progress credit, and cannot trigger automatic redrive"
    )
    stage_log = contract["stage_log_minimum_viability"]
    assert stage_log["accounting_status_policy"] == {
        "duration": "observed_or_explicit_missing_with_reason",
        "token_usage": "observed_or_explicit_missing_with_reason",
        "cost": "observed_or_explicit_missing_with_reason",
    }
    assert stage_log["missing_accounting_status_effect"] == (
        "consume_terminal_closeout_as_typed_blocker_without_paper_progress_credit"
    )
    assert stage_log["accounting_missing_reason_required_fields"] == [
        "status",
        "reason",
        "source_refs",
    ]
    assert "no active attempt exists" in capabilities["worker_source_stale_supervisor_projection"][
        "required_effect"
    ]
    assert "without entering ordinary planning" in capabilities["trace_span_correlation_refs"][
        "required_effect"
    ]
    assert capabilities["trace_span_correlation_refs"]["mas_consumption_surface"] == (
        "trace_span_correlation_policy"
    )

    practices = contract["mature_engineering_practice_mapping"]
    assert practices["kubernetes_controller"]["reject"] == (
        "status, queue, or worklist deriving domain truth"
    )
    assert practices["temporal"]["reject"] == (
        "provider completion counting as MAS domain acceptance"
    )
    assert practices["argo_workflows"]["reject"] == (
        "workflow archive, memoized step result, or retry success replacing MAS owner receipt, typed blocker, or evidence body"
    )
    assert practices["airflow"]["reject"] == (
        "small task metadata becoming artifact body, memory body, study truth, or publication verdict"
    )
    assert practices["aws_step_functions"]["reject"] == (
        "transport idempotency replacing owner receipt or typed blocker"
    )
    assert practices["durable_functions"]["reject"] == (
        "open-ended LLM medical judgment or non-idempotent artifact mutation inside deterministic orchestration"
    )
    assert practices["openlineage"]["reject"] == (
        "lineage proving medical validity, quality closure, or publication readiness"
    )
    assert practices["opentelemetry"]["reject"] == (
        "observability traces closing quality gate or publication verdict"
    )


def assert_desired_current_status_policy(contract: dict[str, Any]) -> None:
    policy = contract["desired_current_status_reconcile_policy"]
    assert policy["surface_kind"] == "mas_opl_desired_current_status_reconcile_policy"
    assert policy["desired_sources"] == ["current_owner_delta", "current_work_unit"]
    assert policy["current_sources"] == [
        "StageRun lease",
        "attempt ledger",
        "Temporal workflow liveness",
        "terminal closeout",
    ]
    assert policy["status_sources"] == [
        "conditions",
        "no_progress_budget",
        "trace_refs",
        "span_refs",
        "next_safe_transport_action",
    ]
    assert {
        "current_owner_delta",
        "current_work_unit",
        "current_executable_owner_action",
        "provider_admission_identity",
        "owner_receipt",
        "typed_blocker",
        "publication_ready_claim",
        "paper_progress_delta",
    } <= set(policy["status_cannot_generate"])
    assert {
        "worker_heartbeat",
        "quest_running",
        "queue_completed",
        "transport_succeeded",
        "archive_materialized",
        "old_active_run_id",
        "trace_span_only",
    } <= set(policy["transport_signals_forbidden_as_desired"])
    restart = policy["worker_source_stale_restart_policy"]
    assert restart["allowed_only_when"] == [
        "no_active_attempt",
        "Temporal reachable",
        "attempt ledger readable",
    ]
    assert restart["otherwise_effect"] == "supervisor_diagnostic_fail_closed"


def assert_trace_span_refs_audit_only(contract: dict[str, Any]) -> None:
    policy = contract["trace_span_correlation_policy"]
    assert policy["surface_kind"] == "mas_opl_trace_span_correlation_policy"
    assert policy["chain"] == [
        "current_owner_delta",
        "StageRun",
        "attempt ledger",
        "Temporal workflow",
        "ToolResultEnvelope",
        "owner answer",
    ]
    assert {
        "trace_id",
        "span_id",
        "parent_span_id",
        "span_link_refs",
        "lineage_run_ref",
        "workflow_id",
        "stage_attempt_id",
    } <= set(policy["required_ref_fields_any"])
    assert {
        "audit",
        "observability",
        "workbench drilldown",
        "stage_route_arbiter_decisions",
        "runtime diagnostic report",
    } <= set(policy["allowed_surfaces"])
    assert {
        "ordinary_planning_root",
        "current_owner_delta_derivation",
        "owner_receipt_signing",
        "typed_blocker_semantic_materialization",
        "quality_gate_closure",
        "publication_ready_claim",
        "paper_progress_credit",
    } <= set(policy["forbidden_authority"])
    assert policy["payload_policy"] == "refs_only_body_free"


def assert_runtime_supervision_operator_policy(contract: dict[str, Any]) -> None:
    policy = contract["runtime_supervision_operator_policy"]
    assert policy["surface_kind"] == "mas_opl_runtime_supervision_operator_policy"
    assert policy["ordinary_read_sequence"] == [
        "fresh_study_progress",
        "domain_health_diagnostic_dry_run_with_stage_attempts",
        "opl_current_control_queue_attempt_worker_readback",
        "terminal_closeout_consumer_gate",
        "fresh_study_progress_after_consumer",
    ]

    actions = {item["action"]: item for item in policy["operator_actions"]}
    assert actions["domain_health_diagnostic_dry_run"]["effect"] == (
        "observe_runtime_truth_and_may_refresh_diagnostic_evidence"
    )
    assert actions["domain_health_diagnostic_dry_run"]["starts_provider_or_llm"] is False
    assert actions["domain_health_diagnostic_dry_run"]["can_claim_no_write"] is False
    assert actions["domain_health_diagnostic_apply"]["requires_all"] == [
        "terminal_closeout_observed_for_current_or_successor_identity",
        "dry_run_currentness_identity_matches_selected_study",
        "write_boundary_is_current_control_or_closeout_consumption_only",
    ]
    assert actions["provider_slo_tick"]["effect"] == (
        "health_and_slo_supervision_only_no_mas_handoff_consumption_claim"
    )
    assert actions["provider_slo_tick"]["can_create_stage_attempt_from_mas_handoff"] is False
    assert actions["family_runtime_tick_hydrate"]["requires_all"] == [
        "materialized_provider_admission_pending_for_new_identity",
        "worker_ready_and_source_current_or_supervisor_safe_restarted",
        "no_matching_live_attempt",
        "no_matching_terminal_closeout",
    ]
    assert actions["family_runtime_tick_hydrate"]["effect"] == (
        "may_admit_opl_stagerun_attempt_for_materialized_current_control_identity"
    )
    assert actions["worker_source_stale_restart"]["requires_all"] == [
        "worker_source_stale",
        "Temporal reachable",
        "attempt ledger readable",
        "no active attempt",
    ]
    assert actions["worker_source_stale_restart"]["forbidden_when_any"] == [
        "active attempt exists",
        "attempt ledger unreadable",
        "Temporal unreachable",
    ]
    assert actions["terminal_closeout_consumer_gate"]["effect"] == (
        "force_dhd_apply_or_equivalent_consumer_before_next_hydrate"
    )

    classifications = policy["progress_classification_policy"]
    assert classifications["runtime_running_watch_requires"] == [
        "same_current_identity_strict_provider_running_proof",
        "live_temporal_or_provider_liveness",
        "no_matching_terminal_closeout",
    ]
    assert {
        "provider_admission_pending",
        "provider_slo_healthy",
        "worker_heartbeat",
        "transport_completed",
        "queue_empty",
    } <= set(classifications["paper_progress_forbidden_basis"])
    assert classifications["paper_progress_requires_any"] == [
        "mas_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "canonical_changed_surface_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]

    forbidden = policy["forbidden_automation_shortcuts"]
    assert {
        "repeat_dhd_apply_after_observe_only_without_new_terminal_or_identity",
        "hydrate_without_materialized_provider_admission",
        "same_work_unit_redrive_after_anti_loop_budget_exhausted",
        "provider_slo_tick_as_handoff_consumer",
        "source_stale_restart_with_active_attempt",
    } <= set(forbidden)
