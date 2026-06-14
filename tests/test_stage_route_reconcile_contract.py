from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.stage_route_reconcile_contract_cases.dm002_dm003_recovery import (
    assert_dm002_dm003_conformance_invariants,
    assert_dm002_dm003_recovery_acceptance,
)
from tests.stage_route_reconcile_contract_cases.follow_through_and_operator_policy import (
    assert_desired_current_status_policy,
    assert_opl_follow_through_and_external_practice_mapping,
    assert_runtime_supervision_operator_policy,
    assert_trace_span_refs_audit_only,
)


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "stage_route_reconcile_contract.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_stage_route_reconcile_contract_declares_single_planning_root() -> None:
    contract = _contract()

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
        "domain_health_diagnostic.provider_admission_current_control",
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
        "domain_health_diagnostic.provider_admission_current_control",
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


def test_stage_route_reconcile_contract_requires_strong_identity_and_closeout_sequence() -> None:
    contract = _contract()

    identity = contract["identity_policy"]
    assert {
        "study_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "idempotency_key",
        "target_surface",
    } <= set(identity["required_owner_identity_fields"])
    assert identity["minimum_match_for_provider_running"] == [
        "same_study_id",
        "same_action_type",
        "same_work_unit_id_or_fingerprint",
        "same_dispatch_ref_or_stage_attempt_id",
        "no_terminal_closeout_for_stage_attempt",
    ]
    assert identity["missing_identity_policy"] == "fail_closed_to_diagnostic_or_typed_blocker_candidate"
    assert identity["weak_label_match_can_authorize_route"] is False
    same_tick = identity["same_tick_materialized_dispatch_identity_policy"]
    assert same_tick["same_action_and_work_unit_label_only_authorizes_provider_admission"] is False
    assert same_tick["required_current_action_identity_any"] == [
        "explicit_work_unit_fingerprint",
        "explicit_action_fingerprint",
        "source_ref_embedded_in_candidate_fingerprint",
        "owner_route_currentness_basis_with_source_eval_or_epochs",
    ]
    assert same_tick["missing_explicit_current_identity_effect"] == (
        "suppress_same_tick_provider_admission_candidate"
    )
    assert same_tick["applies_to"] == [
        "developer_supervisor_same_tick.materialize.default_executor_dispatches",
        "same_tick_materialized_dispatch",
    ]
    progress_ticket = identity["progress_current_owner_ticket_contract"]
    assert progress_ticket["synthetic_fingerprint_prefix_forbidden"] == (
        "study-progress-current-owner-ticket::"
    )
    assert "current_executable_owner_action.work_unit_fingerprint" in (
        progress_ticket["required_strong_identity_any"]
    )
    assert progress_ticket["weak_identity_effect"] == (
        "diagnostic_only_no_default_executor_dispatch"
    )
    assert progress_ticket["weak_identity_reason"] == (
        "fresh_progress_current_owner_ticket_requires_strong_currentness_identity"
    )
    assert progress_ticket["route_generation_policy"] == (
        "do_not_generate_owner_route_from_generated_at_or_source_ref_only"
    )
    gate_followthrough = identity["gate_followthrough_owner_action_contract"]
    assert gate_followthrough["source"] == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    )
    assert gate_followthrough["required_fields"] == [
        "surface_kind=current_executable_owner_action",
        "status=ready",
        "supported_action_type",
        "work_unit_id",
        "work_unit_fingerprint_or_action_fingerprint",
    ]
    assert {
        "stale_current_owner_ticket",
        "stale_typed_blocker_ticket",
        "same_study_stale_progress_ticket",
    } <= set(gate_followthrough["preempts_stale_surfaces"])
    assert gate_followthrough["precedence_effect"] == (
        "project_strong_current_owner_action_before_progress_current_owner_ticket_fallback"
    )
    assert gate_followthrough["missing_identity_effect"] == (
        "fail_closed_to_typed_blocker_currentness_arbiter"
    )
    assert gate_followthrough["typed_blocker_self_authorization_allowed"] is False
    assert gate_followthrough["authority_boundary"] == {
        "can_project_executable_owner_action": True,
        "can_authorize_provider_admission_without_provider_identity": False,
        "can_write_domain_truth": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
    }

    handshake = contract["closeout_handshake"]
    assert handshake["required_sequence"] == [
        "OPL attempt reaches terminal state",
        "terminal closeout packet exists for the same stage attempt or work-unit identity",
        "MAS consumes closeout through domain-health-diagnostic apply or equivalent authority consumer",
        "fresh study progress/read-model is regenerated",
        "if provider_admission_pending remains for a new identity, OPL scoped tick/hydrate may start the next attempt",
        "if the same identity remains pending, classify as closeout consumption/currentness bug",
    ]
    assert handshake["dry_run_semantics"] == {
        "starts_llm_or_provider": False,
        "observe_only_for_runtime_execution": True,
        "may_refresh_diagnostic_evidence": True,
        "must_not_be_called_no_write": False,
    }
    assert "record_only_archive" in handshake["terminal_closeout_status_prefixes"]
    assert "running" in handshake["non_terminal_statuses"]


def test_stage_route_reconcile_contract_orders_currentness_and_blocks_transport_as_domain_closeout() -> None:
    contract = _contract()

    precedence = contract["currentness_precedence"]
    assert [item["signal"] for item in precedence[:7]] == [
        "weak_provider_admission_identity",
        "terminal_closeout_for_same_stage_attempt",
        "strict_live_provider_attempt_for_current_identity",
        "same_work_unit_stop_loss_terminal_stage",
        "accepted_typed_closeout_for_same_identity",
        "weak_fresh_progress_current_owner_ticket_identity",
        "fresh_current_owner_action",
    ]
    assert precedence[0]["effect"] == "suppress_provider_admission_pending"
    assert precedence[1]["effect"] == "suppress_running_projection"
    assert precedence[2]["allowed_output"] == "running_provider_attempt"
    assert precedence[3]["effect"] == "project_typed_blocker_and_suppress_provider_admission"
    assert precedence[3]["allowed_output"] == "typed_blocker"
    assert precedence[3]["default_blocker"] == "anti_loop_budget_exhausted"
    assert precedence[5]["effect"] == "diagnostic_only_no_default_executor_dispatch"
    assert precedence[5]["allowed_output"] == "ignored_diagnostic"
    assert precedence[-1]["allowed_output"] == "ignored_diagnostic"

    lifecycle = contract["lifecycle_state_machine"]
    assert lifecycle["main_chain"] == [
        "DesiredOwnerDelta",
        "ProviderAdmissionRequested",
        "OPLStageRunAdmitted",
        "ProviderRunning",
        "ProviderTerminalCloseoutObserved",
        "MASCloseoutConsumed",
        "DomainAcceptedOrTypedBlocked",
        "NextOwnerDeltaProjected",
    ]
    assert lifecycle["provider_completion_counts_as_domain_accepted"] is False
    assert lifecycle["queue_completion_counts_as_next_owner_delta"] is False
    assert lifecycle["active_run_id_counts_as_paper_progress"] is False


def test_stage_route_reconcile_contract_declares_stage_route_call_graph_and_loop_guards() -> None:
    contract = _contract()

    graph = contract["stage_route_call_graph"]
    assert graph["surface_kind"] == "mas_opl_stage_route_call_graph"
    assert graph["source_code_refs"] == [
        "src/med_autoscience/controllers/study_progress_parts/current_executable_owner_action.py",
        "src/med_autoscience/controllers/current_work_unit.py",
        "src/med_autoscience/controllers/current_execution_envelope.py",
        "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control.py",
        "src/med_autoscience/controllers/domain_action_request_materializer_parts/current_action_selection.py",
        "src/med_autoscience/controllers/domain_owner_action_dispatch_parts/persisted_dispatches.py",
    ]

    nodes = {item["id"]: item for item in graph["nodes"]}
    assert nodes["current_owner_delta"]["state_role"] == "desired"
    assert nodes["current_work_unit"]["state_role"] == "desired_projection"
    assert nodes["provider_admission_current_control"]["state_role"] == "transport_intent"
    assert nodes["opl_stage_run_attempt"]["state_role"] == "current"
    assert nodes["terminal_closeout"]["state_role"] == "terminal_current"
    assert nodes["stage_route_arbiter_decisions"]["state_role"] == "status"
    assert nodes["trace_span_refs"]["state_role"] == "observability"
    assert nodes["mas_owner_receipt_or_typed_blocker"]["state_role"] == "domain_authority"

    edges = {(item["from"], item["to"]): item for item in graph["edges"]}
    assert edges[("current_owner_delta", "current_work_unit")]["authority_effect"] == (
        "derive_canonical_operator_surface"
    )
    assert edges[("current_work_unit", "current_execution_envelope")]["authority_effect"] == (
        "derive_user_and_operator_execution_state"
    )
    assert edges[("current_execution_envelope", "provider_admission_current_control")][
        "loop_guard"
    ] == "only_when_executable_owner_action_and_strong_provider_admission_identity"
    assert edges[("provider_admission_current_control", "opl_stage_run_attempt")][
        "loop_guard"
    ] == "materialized_pending_only_no_live_attempt_no_terminal_closeout_no_current_typed_blocker"
    assert edges[("terminal_closeout", "domain_health_diagnostic_apply")]["authority_effect"] == (
        "consume_closeout_or_materialize_current_control_for_matching_identity"
    )
    assert edges[("domain_health_diagnostic_apply", "mas_owner_receipt_or_typed_blocker")][
        "loop_guard"
    ] == "accepted_owner_answer_or_stable_typed_blocker_required"
    assert edges[("mas_owner_receipt_or_typed_blocker", "next_current_owner_delta")][
        "authority_effect"
    ] == "project_successor_or_stop_loss"

    assert graph["acyclic_same_identity_order"] == [
        "current_owner_delta",
        "current_work_unit",
        "current_execution_envelope",
        "provider_admission_current_control",
        "opl_stage_run_attempt",
        "provider_running",
        "terminal_closeout",
        "domain_health_diagnostic_apply",
        "mas_owner_receipt_or_typed_blocker",
        "next_current_owner_delta",
    ]
    assert graph["same_identity_feedback_policy"] == {
        "feedback_edge": "next_current_owner_delta -> current_owner_delta",
        "requires_any": [
            "new_work_unit_identity",
            "new_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "canonical_changed_surface_ref",
            "stable_typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
            "stop_loss",
        ],
        "forbidden_when": [
            "same_work_unit_without_new_consumed_evidence",
            "same_identity_terminal_closeout_unconsumed",
            "same_identity_anti_loop_budget_exhausted",
            "status_or_observability_only_delta",
        ],
    }

    forbidden_edges = {(item["from"], item["to"]): item for item in graph["forbidden_edges"]}
    assert forbidden_edges[("trace_span_refs", "current_owner_delta")]["reason"] == (
        "observability refs cannot generate desired owner state"
    )
    assert forbidden_edges[("active_run_id_or_transport_status", "current_work_unit")][
        "reason"
    ] == "transport status cannot become canonical current work unit"
    assert forbidden_edges[("typed_blocker_only", "provider_admission_current_control")][
        "reason"
    ] == "typed blocker cannot self-authorize provider admission or readiness execution"
    assert forbidden_edges[("provider_completion", "mas_owner_receipt_or_typed_blocker")][
        "reason"
    ] == "provider completion is not MAS domain acceptance"
    assert forbidden_edges[("old_persisted_dispatch", "provider_admission_current_control")][
        "reason"
    ] == "stale dispatch cannot bypass selected-dispatch currentness"

    risks = {item["risk"]: item for item in graph["dead_loop_risk_guards"]}
    assert risks["typed_blocker_self_authorization"]["blocked_by"] == [
        "owner_action_dispatch_authority_policy.typed_blocker_can_self_authorize_owner_action=false",
        "current_typed_blocker_precedes_provider_admission",
    ]
    assert risks["stale_running_projection"]["blocked_by"] == [
        "currentness_precedence.terminal_closeout_for_same_stage_attempt",
        "identity_policy.minimum_match_for_provider_running",
    ]
    assert risks["same_work_unit_redrive_loop"]["blocked_by"] == [
        "anti_loop_policy.max_same_identity_terminal_without_progress",
        "dm002_dm003_recovery_acceptance_policy.same_work_unit_stop_loss_policy",
    ]

    boundary = graph["authority_boundary"]
    assert boundary["graph_is_explanatory_and_contractual"] is True
    assert boundary["can_generate_owner_delta"] is False
    assert boundary["can_authorize_provider_admission"] is False
    assert boundary["can_mark_paper_progress"] is False


def test_stage_route_reconcile_contract_declares_anti_loop_budget_and_owner_split() -> None:
    contract = _contract()

    anti_loop = contract["anti_loop_policy"]
    assert anti_loop["budget_scope"] == (
        "study_id + action_type + work_unit_id + work_unit_fingerprint + source_eval_id"
    )
    assert anti_loop["max_same_identity_terminal_without_progress"] == 2
    assert anti_loop["max_same_identity_noop_or_owner_output_current"] == 1
    assert {
        "same_work_unit_terminal_closeout_without_domain_consumption",
        "provider_admission_pending_for_consumed_identity",
        "idempotent_noop_without_new_owner_delta",
        "repeated_gate_replay_same_blockers",
        "queue_dead_letter_without_mas_typed_blocker_or_next_owner",
    } <= set(anti_loop["no_progress_signals"])
    assert anti_loop["budget_exhaustion_action"] == (
        "stop_redrive_and_emit_mas_typed_blocker_candidate_or_route_back_evidence"
    )
    assert anti_loop["automatic_redrive_after_budget_exhaustion_allowed"] is False

    arbiter = contract["stage_route_arbiter_surface"]
    assert arbiter["surface_kind"] == "mas_opl_stage_route_arbiter"
    assert arbiter["producer"] == "domain-health-diagnostic.provider_admission_current_control"
    assert arbiter["ordinary_planning_root"] == "current_owner_delta"
    assert arbiter["decision_payload_required_fields"] == [
        "decision",
        "effect",
        "study_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
        "stage_packet_ref_or_refs",
        "evidence_status",
        "authority_boundary",
    ]
    assert arbiter["decision_payload_optional_no_progress_fields"] == [
        "no_progress_signal",
        "anti_loop_classification",
    ]
    assert [item["decision"] for item in arbiter["decision_kinds"]] == [
        "weak_provider_admission_identity",
        "terminal_closeout_precedes_live_projection",
        "running_identity_observed",
        "accepted_closeout_consumed_pending",
        "current_typed_blocker_precedes_provider_admission",
        "pending_provider_admission",
    ]
    effects = {item["decision"]: item["effect"] for item in arbiter["decision_kinds"]}
    assert effects["weak_provider_admission_identity"] == "suppress_provider_admission_pending"
    weak_identity_decision = next(
        item
        for item in arbiter["decision_kinds"]
        if item["decision"] == "weak_provider_admission_identity"
    )
    assert "missing_stage_packet_ref_or_refs" in weak_identity_decision["required_match"]
    assert effects["terminal_closeout_precedes_live_projection"] == (
        "suppress_provider_admission_pending"
    )
    assert effects["running_identity_observed"] == "suppress_provider_admission_pending"
    assert effects["accepted_closeout_consumed_pending"] == (
        "suppress_provider_admission_pending"
    )
    assert effects["current_typed_blocker_precedes_provider_admission"] == (
        "suppress_provider_admission_pending"
    )
    assert effects["pending_provider_admission"] == "retain_provider_admission_pending"
    terminal_decision = next(
        item
        for item in arbiter["decision_kinds"]
        if item["decision"] == "terminal_closeout_precedes_live_projection"
    )
    assert terminal_decision["successor_policy"] == (
        "if_current_executable_owner_action_has_different_work_unit_identity_keep_successor_pending_and_attach_terminal_precedence_evidence"
    )
    assert terminal_decision["stale_running_projection_effect"] == (
        "suppress_stale_running_projection"
    )
    assert {
        "study_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "dispatch_path_or_ref",
        "stage_packet_ref_or_refs",
        "currentness_basis",
        "route_identity_key",
        "attempt_idempotency_key",
    } <= set(arbiter["required_identity_fields"])
    assert arbiter["pending_provider_admission_required_match"] == [
        "strong_provider_admission_identity",
        "no_weak_provider_admission_identity",
        "no_matching_live_attempt",
        "no_matching_accepted_closeout",
        "no_current_typed_blocker_for_same_action_or_work_unit",
        "no_same_currentness_basis_fingerprintless_stop_loss_closeout",
    ]
    unscanned = arbiter["scoped_scan_unscanned_retention_policy"]
    assert unscanned["retention_semantics"] == "audit_only"
    assert unscanned["active_queue_semantics"] == "scanned_studies_only"
    assert unscanned["can_increment_provider_admission_pending_count"] is False
    self_identity = arbiter["carrier_self_identity_policy"]
    assert self_identity["current_control_action_can_self_authorize"] is False
    assert self_identity["missing_canonical_identity_effect"] == (
        "suppress_provider_admission_candidate"
    )
    assert self_identity["action_id_role"] == "action_family_only_not_dedupe_or_route_identity"
    assert self_identity["weak_identity_effect"] == "weak_provider_admission_identity"
    assert "current_owner_delta" in self_identity["canonical_identity_sources"]
    projection_shape = arbiter["provider_admission_projection_shape_policy"]
    assert projection_shape["surface_kind"] == "provider_admission_projection_shape_policy"
    assert projection_shape["top_level_fields"] == [
        "provider_admission_pending_count",
        "provider_admission_candidates",
    ]
    assert projection_shape["suppressed_or_absent_shape"] == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
    }
    assert projection_shape["empty_candidates_semantics"] == (
        "explicit_no_current_provider_admission_candidate_not_missing_projection"
    )
    assert projection_shape["candidate_presence_is_not_running_proof"] is True
    assert projection_shape["empty_projection_can_authorize_hydrate"] is False
    assert projection_shape["empty_projection_can_mark_paper_progress"] is False
    assert projection_shape["refresh_required_on_full_assembly_and_existing_projection_refresh"] is True
    assert arbiter["authority_boundary"] == {
        "arbiter_surface": "currentness_projection_only",
        "can_write_domain_truth": False,
        "can_authorize_publication_ready": False,
        "provider_completion_is_domain_ready": False,
    }
    assert arbiter["must_be_written_with_current_control"] is True

    dispatch_policy = contract["owner_action_dispatch_authority_policy"]
    assert dispatch_policy["surface_kind"] == "mas_owner_action_dispatch_authority_policy"
    assert dispatch_policy["scope"] == [
        "domain_action_request_materializer",
        "domain_owner_action_dispatch",
    ]
    assert dispatch_policy["typed_blocker_can_self_authorize_owner_action"] is False
    assert dispatch_policy["blocker_only_effect"] == (
        "suppress_stale_transition_queue_or_dispatch_and_emit_diagnostic"
    )
    assert dispatch_policy["readiness_dispatch_requires_any"] == [
        "explicit_current_executable_owner_action",
        "stage_native_workspace_next_action_with_authority_binding",
        "terminal_closeout_owner_answer_dispatch",
    ]
    assert {
        "current_work_unit.typed_blocker",
        "current_execution_envelope.typed_blocker",
        "stale_default_executor_dispatch_owner_route",
        "source_ref_or_fingerprint_match_without_executable_owner_action",
    } <= set(dispatch_policy["readiness_blocker_only_forbidden_basis"])
    assert dispatch_policy["forbidden_readiness_dispatch_effect"] == (
        "blocker_only_executes_complete_medical_paper_readiness_surface"
    )
    stage_native = dispatch_policy["stage_native_next_action_policy"]
    assert stage_native["dispatch_requires_any"] == [
        "canonical_current_work_unit_binding",
        "owner_route_match_with_allowed_action",
        "shared_currentness_identity_with_fingerprint",
    ]
    assert stage_native["stale_or_unbound_effect"] == (
        "diagnostic_only_no_default_executor_dispatch"
    )
    assert dispatch_policy["default_dispatch_allowed_false_effect"] == (
        "ignored_diagnostic_no_request_task_no_default_executor_dispatch"
    )
    terminal_owner_answer = dispatch_policy["terminal_closeout_owner_answer_dispatch_policy"]
    assert terminal_owner_answer["requires_any"] == [
        "closeout_ref_or_source_ref_points_to_dispatch",
        "typed_blocker_ref_points_to_dispatch",
        "shared_currentness_identity_with_fingerprint",
    ]
    assert terminal_owner_answer[
        "same_action_and_work_unit_without_ref_or_fingerprint_effect"
    ] == "reject_dispatch_as_stale_identity"
    assert dispatch_policy["authority_boundary"] == {
        "can_write_domain_truth": False,
        "can_authorize_publication_ready": False,
        "can_convert_blocker_to_owner_receipt": False,
        "explicit_owner_action_required": True,
    }

    stage_log = contract["stage_log_minimum_viability"]
    assert stage_log["surface_kind"] == "mas_opl_stage_log_minimum_viability_policy"
    assert stage_log["canonical_domain_log_field"] == "paper_stage_log"
    assert stage_log["accepted_aliases"] == [
        "paper_stage_log",
        "user_stage_log",
        "stage_log_summary",
    ]
    assert {
        "stage_goal",
        "stage_work_done",
        "paper_work_done",
        "duration",
        "token_usage",
        "cost",
        "progress_delta_classification",
        "deliverable_progress_delta",
        "paper_progress_delta",
        "platform_repair_delta",
        "next_forced_delta",
    } <= set(stage_log["required_domain_fields"])
    assert stage_log["missing_domain_fields_effect"] == "consume_terminal_closeout_as_typed_blocker"
    assert stage_log["typed_blocker_reason"] == "domain_closeout_provided_incomplete_user_stage_log"
    assert stage_log["paper_progress_credit_allowed_when_incomplete"] is False
    assert stage_log["automatic_redrive_allowed_when_incomplete"] is False
    workbench_projection = stage_log["workbench_projection"]
    assert workbench_projection["field"] == "stage_log_workbench_summary"
    assert workbench_projection["read_model"] == "stage_log_minimum_viability_workbench_projection"
    assert workbench_projection["projection_scope"] == "agent_operator_workbench_summary"
    assert workbench_projection["source_log_field"] == "paper_stage_log"
    assert workbench_projection["body_policy"] == "refs_only_body_free"
    assert {
        "stage_goal",
        "actual_work",
        "paper_delta",
        "deliverable_delta",
        "platform_delta",
        "observability",
        "evidence_refs",
        "next_forced_delta",
        "missing_domain_fields",
        "source_refs",
        "authority_boundary",
    } <= set(workbench_projection["required_summary_fields"])
    assert workbench_projection["field_presence_shape"] == {
        "status": "present_or_missing",
        "item_count": "integer",
        "refs": "refs_only",
        "body_included": False,
    }
    assert {
        "stage_work_done",
        "paper_work_done",
        "paper_body",
        "artifact_body",
        "memory_body",
        "publication_verdict_body",
        "transcript_body",
    } <= set(workbench_projection["forbidden_body_fields"])
    assert workbench_projection["authority_boundary"] == {
        "refs_only": True,
        "body_free": True,
        "observability_only": True,
        "can_mark_domain_ready": False,
        "can_write_paper_truth": False,
        "can_authorize_quality_verdict": False,
        "can_block_provider_admission": False,
    }
    assert stage_log["authority_boundary"] == {
        "mas_consumes_as_domain_typed_blocker": True,
        "opl_projects_missing_fields_only": True,
        "provider_completion_is_domain_progress": False,
        "can_write_paper_body": False,
        "can_authorize_quality_or_submission": False,
    }

    split = contract["opl_substrate_optimization"]
    assert "StageRun Kernel" in split["opl_owns"]
    assert "durable queue" in split["opl_owns"]
    assert "current_owner_delta" in split["mas_owns"]
    assert "owner receipt" in split["mas_owns"]
    assert "typed blocker" in split["mas_owns"]
    assert {
        "publication_ready_claim",
        "quality_verdict",
        "artifact_authority",
        "owner_receipt_signing",
    } <= set(split["forbidden_opl_authority"])
    assert {
        "private_scheduler",
        "worker_residency_owner",
        "second_route_table",
        "second_active_backlog",
    } <= set(split["forbidden_mas_runtime_residue"])


def test_stage_route_reconcile_contract_splits_foreground_manual_work_from_governed_recovery() -> None:
    contract = _contract()

    frontdoor = contract["codex_executor_frontdoor_policy"]
    assert frontdoor["surface_kind"] == "mas_opl_codex_executor_frontdoor_policy"
    assert frontdoor["ordinary_executor_route"] == (
        "MAS/OPL-governed recovery route uses a MAS owner callable, MAS domain-handler dispatch, or OPL StageRun provider attempt that may invoke Codex as an internal executor"
    )
    assert frontdoor["enforcement_model"] == "authority_acceptance_not_filesystem_prevention"
    assert frontdoor["human_or_foreground_manual_edits_possible"] is True
    assert frontdoor["explicit_manual_foreground_route_allowed"] is True
    assert {
        "user explicitly selects foreground/manual editing or fast-lane mode",
        "agent labels the output as manual foreground work, not MAS/OPL-governed recovery",
        "agent states which workspace surfaces were edited and which MAS/OPL truth surfaces were not updated",
    } <= set(frontdoor["manual_foreground_route_requirements"])
    assert {
        "mas_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
        "same_current_identity_strict_provider_running_proof",
        "canonical_changed_surface_ref_consumed_by_mas_or_opl",
    } <= set(frontdoor["manual_foreground_adoption_requires"])
    assert frontdoor["manual_foreground_without_required_refs_effect"] == (
        "manual_work_product_only_no_mas_opl_recovery_claim"
    )
    assert {
        "paper_local_codex_execution_without_mas_owner_callable_or_explicit_manual_mode",
        "direct_manuscript_or_package_edit_claimed_as_mas_opl_recovery",
        "foreground_replay_of_provider_admission_queue",
        "study_workspace_runtime_artifact_mutation",
        "publication_eval_or_controller_decision_manual_write",
    } <= set(frontdoor["not_accepted_as_governed_recovery"])
    assert {
        "read_live_truth",
        "write_repo_docs_contracts_tests",
        "implement_missing_mas_owner_callable_or_derived_repair_action",
        "run_repo_native_verification",
        "supervise_opl_stage_run_or_provider_attempt",
        "perform_explicit_user_requested_manual_foreground_edit_with_non_authority_label",
    } <= set(frontdoor["allowed_foreground_roles"])
    authority = frontdoor["codex_direct_execution_authority"]
    assert authority["can_act_as_internal_owner_callable_executor"] is True
    assert authority["requires_mas_owner_callable_or_stage_run_context"] is True
    assert authority["can_perform_explicit_manual_paper_local_work"] is True
    assert authority["can_claim_manual_work_as_mas_opl_recovery_without_adoption_refs"] is False
    assert authority["can_write_study_truth_without_owner_receipt"] is False
    assert authority["can_write_publication_eval_or_controller_decisions"] is False
    assert authority["can_mutate_runtime_or_study_artifacts_from_docs_contract_lane"] is False
    assert frontdoor["missing_callable_effect"] == (
        "governed_recovery_needs_typed_blocker_or_repo_implementation; explicit_manual_work_may_continue_only_as_non_authority_output"
    )
    assert frontdoor["route_back_owner_when_platform_binding_missing"] == "one-person-lab"
    assert frontdoor["route_back_owner_when_domain_readiness_callable_missing"] == (
        "MedAutoScience"
    )


def test_stage_route_reconcile_contract_declares_dm002_dm003_recovery_acceptance() -> None:
    contract = _contract()

    assert_dm002_dm003_recovery_acceptance(contract)


def test_stage_route_reconcile_contract_declares_dm002_dm003_conformance_invariants() -> None:
    contract = _contract()

    assert_dm002_dm003_conformance_invariants(contract)


def test_stage_route_reconcile_contract_tracks_opl_follow_through_and_external_practice_mapping() -> None:
    contract = _contract()

    assert_opl_follow_through_and_external_practice_mapping(contract)


def test_stage_route_reconcile_contract_declares_desired_current_status_policy() -> None:
    contract = _contract()

    assert_desired_current_status_policy(contract)


def test_stage_route_reconcile_contract_keeps_trace_span_refs_audit_only() -> None:
    contract = _contract()

    assert_trace_span_refs_audit_only(contract)


def test_stage_route_reconcile_contract_declares_runtime_supervision_operator_policy() -> None:
    contract = _contract()

    assert_runtime_supervision_operator_policy(contract)
