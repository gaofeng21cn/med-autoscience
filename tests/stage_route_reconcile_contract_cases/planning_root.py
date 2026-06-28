from __future__ import annotations

from typing import Any


def assert_single_planning_root(contract: dict[str, Any]) -> None:
    assert contract["surface_kind"] == "mas_opl_stage_route_reconcile_contract"
    assert contract["version"] == "stage-route-reconcile.v1"
    assert contract["state"] == "active_contract"
    assert contract["machine_boundary"].startswith("This contract defines route/currentness")
    assert contract["related_contract_refs"][0] == (
        "contracts/paper_recovery_kernel_contract.json"
    )

    root = contract["ordinary_planning_root"]
    assert root["root"] == "current_owner_delta"
    assert {
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "provider_admission_current_control",
    } <= set(root["derived_operator_surfaces"])
    assert {
        "raw_worklist",
        "OPL queue history",
        "attempt ledger",
        "sidecar advisory refs",
        "runtime observability traces",
    } <= set(root["audit_only_surfaces"])
    assert {
        "active_run_id",
        "transport_status",
        "zero_open_worklist",
        "old_route_back_packet",
        "advisory_score_or_ranking",
    } <= set(root["forbidden_default_roots"])
    assert root["no_second_truth"] is True

    paper_recovery = contract["paper_recovery_kernel_consumption"]
    assert paper_recovery["surface_kind"] == "stage_route_paper_recovery_kernel_consumption"
    assert paper_recovery["kernel_contract_ref"] == (
        "contracts/paper_recovery_kernel_contract.json"
    )
    assert paper_recovery["paper_recovery_state_root"] == "paper_recovery_state"
    assert paper_recovery["stage_route_role"] == (
        "consume_paper_recovery_obligation_for_provider_admission_and_closeout_reconcile"
    )
    assert {
        "study_progress",
        "domain_diagnostic_report.provider_admission_current_control",
        "operator_status_card",
        "intervention_lane",
        "operator_verdict",
        "auto_runtime_parked",
        "recovery_contract",
        "autonomy_contract",
        "user_visible_projection",
        "OPL admission projection",
        "human workbench card",
    } <= set(paper_recovery["derived_surfaces_must_read_from_paper_recovery"])
    assert paper_recovery["required_invariants"] == [
        "exactly_one_current_recovery_obligation",
        "identity_bound_provider_admission_required",
        "terminal_closeout_must_consume_or_reject",
        "stop_loss_must_have_successor_or_human_gate",
        "projection_inconsistency_fail_closed",
        "manual_foreground_output_requires_adoption_refs",
        "derived_visible_surfaces_must_be_sanitized",
    ]
    assert paper_recovery["false_authority_flags"] == {
        "stage_route_can_select_recovery_obligation": False,
        "opl_can_own_paper_recovery_state": False,
        "operator_card_can_create_recovery_truth": False,
        "provider_completion_is_recovery_acceptance": False,
        "observe_only_can_create_pending_recovery_execution": False,
        "identity_bound_provider_admission_can_remain_pending_under_observe_only": True,
    }
    projection_guard = paper_recovery["single_kernel_projection_guard"]
    assert projection_guard["kernel_output"] == "paper_recovery_state"
    assert projection_guard["decision_owner"] == "MedAutoScience PaperRecovery"
    assert projection_guard["transport_owner"] == "OPL StageRun substrate"
    assert projection_guard["derived_surface_policy"] == "consume_only_no_redecide_currentness"
    assert projection_guard["derived_surfaces"] == [
        "current_work_unit",
        "current_execution_envelope",
        "study_progress",
        "domain_diagnostic_report.provider_admission_current_control",
        "domain_handler_export.pending_family_tasks",
        "operator_status_card",
        "OPL admission projection",
        "human workbench card",
    ]
    assert projection_guard["derived_surface_required_inputs"] == [
        "recovery_obligation_id",
        "phase",
        "conditions",
        "next_safe_action",
        "current_work_unit_identity",
        "provider_admission_identity",
        "terminal_closeout_refs",
        "consumed_or_rejected_refs",
    ]
    assert projection_guard["forbidden_inputs_as_authority"] == [
        "queue_residue",
        "old_persisted_dispatch",
        "active_run_id",
        "transport_status",
        "operator_card_state",
        "read_model_refresh_time",
        "trace_span_ref",
    ]
    assert projection_guard["projection_inconsistent_effect"] == (
        "emit_projection_inconsistent_or_admission_blocked_without_provider_admission"
    )
    assert projection_guard["implementation_goal"] == (
        "single_recovery_obligation_decision_object_consumed_by_all_operator_projections"
    )

    external = contract["external_engineering_principles"]
    assert external["surface_kind"] == "stage_route_external_engineering_principles"
    assert [item["label"] for item in external["source_refs"]] == [
        "Temporal Event History / Workflow replay",
        "Temporal Activity idempotency",
        "AWS idempotent APIs / client token",
        "Azure CQRS / read-model lag",
        "Google SRE overload / retry budget",
    ]
    assert external["design_rules"] == [
        "identity_first_not_status_first",
        "route_identity_key_and_attempt_idempotency_key_required_for_provider_admission",
        "transport_or_workflow_completion_cannot_mark_mas_domain_progress",
        "read_model_lag_must_be_observable_with_evidence_status",
        "same_identity_no_progress_redrive_must_stop_at_budget",
    ]
    assert external["forbidden_interpretations"] == [
        "heartbeat_or_worker_running_as_paper_progress",
        "queue_empty_as_completion",
        "record_only_ref_as_currentness_identity",
        "same_action_label_as_idempotency_key",
        "retry_without_same_intent_identity",
    ]
