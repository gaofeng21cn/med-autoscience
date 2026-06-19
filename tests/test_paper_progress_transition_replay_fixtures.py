from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _stable_transition_step(payload: Mapping[str, Any]) -> dict[str, Any]:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(payload, source="dm002_dm003.replay_fixture")
    assert result
    request = result["opl_domain_progress_transition_request"]
    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert "projection_metadata" not in request
    assert "opl_domain_progress_transition_event" not in request
    assert "opl_domain_progress_transition_outbox_item" not in request
    assert "stage_run_identity" not in request
    return {
        "paper_progress_policy_result": result,
        "opl_domain_progress_transition_request": request,
        "transition_kind": result["recommended_opl_transition_kind"],
        "postcondition_kind": request["required_postcondition"]["kind"],
        "outcome_kind": result["policy_outcome_kind"],
        "authority_boundary": result["authority_boundary"],
        "projection_metadata": result["projection_metadata"],
    }


def _non_advancing_step(payload: Mapping[str, Any]) -> dict[str, Any]:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_non_advancing_policy_blocker(
        payload,
        reason="dm002_dm003_replay_no_stable_runtime_outcome",
    )
    request = result["opl_domain_progress_transition_request"]
    return {
        "paper_progress_policy_result": result,
        "opl_domain_progress_transition_request": request,
        "transition_kind": result["recommended_opl_transition_kind"],
        "postcondition_kind": request["required_postcondition"]["kind"],
        "outcome_kind": result["policy_outcome_kind"],
        "authority_boundary": result["authority_boundary"],
        "projection_metadata": result["projection_metadata"],
        "non_advancing_apply": True,
    }


def _current_work_unit_from_progress(
    *,
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]] | None = None,
    current_executable_owner_action: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    next_owner: str | None = None,
) -> dict[str, Any]:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")
    return module.build_current_work_unit(
        progress=progress,
        actions=actions,
        current_executable_owner_action=current_executable_owner_action,
        typed_blocker=typed_blocker,
        next_owner=next_owner,
    )


def _assert_mas_adapter_only(step: Mapping[str, Any]) -> None:
    boundary = step["authority_boundary"]
    assert boundary["mas_can_authorize_provider_admission"] is False
    assert boundary["mas_can_run_fixed_point_reconciler"] is False
    assert boundary["mas_can_own_event_log_or_outbox"] is False
    assert boundary["mas_can_create_opl_outbox_record"] is False
    assert boundary["opl_owns_transition_runtime"] is True
    assert step["projection_metadata"]["authority"] is False
    assert step["projection_metadata"]["fixed_point_runtime_owner"] == "one-person-lab"


def _assert_exactly_one_transition(
    step: Mapping[str, Any],
    *,
    transition_kind: str,
    postcondition_kind: str,
    outcome_kind: str,
) -> None:
    assert step["transition_kind"] == transition_kind
    assert step["postcondition_kind"] == postcondition_kind
    assert step["outcome_kind"] == outcome_kind
    request = step["opl_domain_progress_transition_request"]
    assert request["recommended_transition_kind"] == transition_kind
    assert request["required_postcondition"]["kind"] == postcondition_kind
    assert request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["mas_can_create_opl_outbox_record"] is False
    assert "projection_metadata" not in request
    assert "opl_domain_progress_transition_event" not in request
    assert "opl_domain_progress_transition_outbox_item" not in request
    assert "stage_run_identity" not in request
    _assert_mas_adapter_only(step)


def test_dm002_replay_fixture_converges_to_exactly_one_stable_typed_blocker_transition() -> None:
    step = _stable_transition_step(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "ai_reviewer_record_gate_consumption"
                ),
                "typed_blocker": {
                    "blocker_type": "anti_loop_budget_exhausted",
                    "typed_blocker_ref": (
                        "studies/002-dm-china-us-mortality-attribution/artifacts/"
                        "supervision/consumer/default_executor_execution/"
                        "sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
                    ),
                },
                "currentness_basis": {
                    "observed_generation": "runtime-health-event-007034-9e7d25f9f14067b0",
                },
            },
        }
    )

    _assert_exactly_one_transition(
        step,
        transition_kind="RecordTypedBlocker",
        postcondition_kind="typed_blocker_ref",
        outcome_kind="typed_blocker",
    )
    assert step["paper_progress_policy_result"]["paper_policy_verdict"]["typed_blocker_ref"].endswith(
        "sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
    )


def test_dm003_replay_fixture_records_non_advancing_apply_when_owner_action_request_lacks_opl_readback() -> None:
    stable_request = _stable_transition_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "currentness_basis": {
                    "observed_generation": "runtime-health-event-006974-79380e0c39b23587",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {
                    "obligation": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    }
                },
                "next_safe_action": {
                    "kind": "materialize_mas_transition_request_or_owner_callable",
                    "owner": "write",
                    "provider_admission_allowed": True,
                },
            },
        }
    )
    non_advancing = _non_advancing_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
        }
    )

    _assert_exactly_one_transition(
        stable_request,
        transition_kind="MaterializeOwnerAction",
        postcondition_kind="owner_action_ref",
        outcome_kind="owner_action_requested",
    )
    _assert_exactly_one_transition(
        non_advancing,
        transition_kind="NonAdvancingApply",
        postcondition_kind="non_advancing_apply_typed_blocker_ref",
        outcome_kind="non_advancing_apply_typed_blocker",
    )
    assert non_advancing["paper_progress_policy_result"]["paper_policy_verdict"] == {
        "verdict": "stable_typed_blocker_required",
        "typed_blocker_type": "non_advancing_apply",
        "reason": "dm002_dm003_replay_no_stable_runtime_outcome",
    }


def test_owner_receipt_recorded_replay_requires_non_advancing_apply_when_readback_does_not_move() -> None:
    owner_receipt_recorded = _stable_transition_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "owner_receipt_recorded",
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "publication-blockers::owner-receipt-recorded",
                "currentness_basis": {
                    "truth_epoch": "truth::dm003::owner-receipt-recorded",
                    "observed_generation": "runtime-health-event::owner-receipt-recorded",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_receipt_recorded",
                "owner_receipt_ref": "owner_receipt:dm003:publication_gate_replay",
                "next_safe_action": {
                    "kind": "consume_owner_receipt",
                    "owner_receipt_ref": "owner_receipt:dm003:publication_gate_replay",
                },
            },
        }
    )
    same_identity_readback = _non_advancing_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "owner_receipt_recorded",
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "publication-blockers::owner-receipt-recorded",
                "currentness_basis": {
                    "truth_epoch": "truth::dm003::owner-receipt-recorded",
                    "observed_generation": "runtime-health-event::owner-receipt-recorded",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_receipt_recorded",
                "owner_receipt_ref": "owner_receipt:dm003:publication_gate_replay",
            },
        }
    )

    _assert_exactly_one_transition(
        owner_receipt_recorded,
        transition_kind="ConsumeOwnerReceipt",
        postcondition_kind="owner_receipt_consumed",
        outcome_kind="owner_receipt",
    )
    assert owner_receipt_recorded["paper_progress_policy_result"]["paper_policy_verdict"] == {
        "verdict": "mas_owner_receipt_consumption_required",
        "owner_receipt_ref": "owner_receipt:dm003:publication_gate_replay",
        "paper_progress_credit_allowed": True,
    }
    _assert_exactly_one_transition(
        same_identity_readback,
        transition_kind="NonAdvancingApply",
        postcondition_kind="non_advancing_apply_typed_blocker_ref",
        outcome_kind="non_advancing_apply_typed_blocker",
    )


def test_terminal_owner_receipt_closeout_consumes_transition_request_projection_residue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff"
    )
    apply_terminal_closeout = getattr(module, "_apply_matching_terminal_closeout_to_handoff")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    route_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    stage_attempt_id = "sat_f22f2e9d25d336fa2a2a4306"
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
    )
    owner_receipt_ref = f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json"
    transition_candidate = {
        "status": "transition_request_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "provider_admission_requires_opl_runtime_result": True,
        "provider_completion_is_domain_completion": False,
    }

    consumed = apply_terminal_closeout(
        {
            "surface_kind": "opl_current_control_state_study_handoff",
            "authority": "observability_only",
            "study_id": study_id,
            "running_provider_attempt": False,
            "active_run_id": "opl-stage-attempt://stale-transition-request",
            "active_stage_attempt_id": stage_attempt_id,
            "active_workflow_id": "wf-stale-transition-request",
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [transition_candidate],
            "latest_terminal_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_attempt_id": stage_attempt_id,
                "status": "closed",
                "execution_status": "owner_receipt_recorded",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "route_identity_key": route_key,
                "attempt_idempotency_key": route_key,
                "stage_packet_ref": stage_packet_ref,
                "stage_packet_refs": [stage_packet_ref],
                "owner_receipt_ref": owner_receipt_ref,
                "paper_stage_log": {
                    "outcome": "closed_with_existing_mas_owner_receipt_ref",
                    "progress_delta_classification": "platform_repair",
                    "changed_paper_surfaces": [],
                    "next_forced_delta": {
                        "required_delta_kind": "consume_existing_owner_receipt_or_route_to_next_owner",
                        "work_unit_id": work_unit,
                        "owner_action": {
                            "next_owner": "MedAutoScience",
                            "action_type": "consume_owner_receipt",
                            "work_unit_id": work_unit,
                        },
                    },
                },
            },
        }
    )

    assert consumed["provider_admission_pending_count"] == 0
    assert consumed["provider_admission_candidates"] == []
    assert consumed["transition_request_pending_count"] == 0
    assert consumed["transition_request_candidates"] == []
    assert consumed["running_provider_attempt"] is False
    assert consumed["runtime_owner"] is None
    assert consumed["provider_attempt_owner"] is None
    assert consumed["queue_owner"] is None
    assert consumed["active_run_id"] is None
    marker = consumed["provider_admission_terminal_closeout_consumed"]
    assert marker["stage_attempt_id"] == stage_attempt_id
    assert marker["work_unit_id"] == work_unit
    assert marker["work_unit_fingerprint"] == fingerprint
    assert marker["owner_receipt_ref"] == owner_receipt_ref
    assert marker["authority_boundary"] == {
        "projection_only": True,
        "runtime_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "can_authorize_provider_admission": False,
        "can_start_provider_attempt": False,
        "provider_completion_is_domain_completion": False,
    }


def test_closeout_stagerun_identity_split_replay_converges_to_one_stable_typed_blocker() -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    current_work_unit_id = "analysis_claim_evidence_repair"
    current_fingerprint = "publication-blockers::497d1260db522f01"
    stale_stage_packet_fingerprint = (
        "owner-route::write::manuscript_story_surface_delta_missing::"
        "run_quality_repair_batch"
    )
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/default_executor_execution/sat_cfb833131bfa30d6661c26c2.closeout.json"
    )

    current_work_unit = _current_work_unit_from_progress(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_cfb833131bfa30d6661c26c2",
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "blocked_reason": "stage_packet_not_current_selected_dispatch",
                    "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                    "work_unit_fingerprint": stale_stage_packet_fingerprint,
                    "stage_name": current_work_unit_id,
                    "source_path": closeout_ref,
                    "closeout_refs": [closeout_ref],
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_current_selected_dispatch",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "required_owner_action": (
                            "provide or admit a current stage packet for "
                            f"{current_work_unit_id}/{current_fingerprint}"
                        ),
                    },
                    "domain_execution": {
                        "blocked_reason": "stage_packet_not_current_selected_dispatch",
                        "requested_stage_packet_work_unit_id": (
                            "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                        ),
                        "requested_stage_packet_work_unit_fingerprint": stale_stage_packet_fingerprint,
                        "fresh_current_control_work_unit_id": current_work_unit_id,
                        "fresh_current_control_work_unit_fingerprint": current_fingerprint,
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "write",
            "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            "work_unit_fingerprint": stale_stage_packet_fingerprint,
            "action_fingerprint": stale_stage_packet_fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_type": "stage_packet_not_current_selected_dispatch",
            "blocked_reason": "stage_packet_not_current_selected_dispatch",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": stale_stage_packet_fingerprint,
            "source_ref": closeout_ref,
            "typed_blocker_ref": closeout_ref,
            "currentness_basis": {
                "work_unit_id": current_work_unit_id,
                "work_unit_fingerprint": stale_stage_packet_fingerprint,
            },
        },
        next_owner="write",
    )
    step = _stable_transition_step(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": current_work_unit,
        }
    )

    assert current_work_unit["status"] == "typed_blocker"
    assert current_work_unit["work_unit_id"] == current_work_unit_id
    assert current_work_unit["work_unit_fingerprint"] == current_fingerprint
    assert current_work_unit["state"]["typed_blocker"]["blocker_type"] == (
        "stage_packet_not_current_selected_dispatch"
    )
    assert current_work_unit["state"]["typed_blocker"]["typed_blocker_ref"] == closeout_ref
    _assert_exactly_one_transition(
        step,
        transition_kind="RecordTypedBlocker",
        postcondition_kind="typed_blocker_ref",
        outcome_kind="typed_blocker",
    )
    assert step["paper_progress_policy_result"]["paper_policy_verdict"] == {
        "verdict": "stable_typed_blocker_required",
        "typed_blocker_ref": closeout_ref,
        "paper_progress_credit_allowed": True,
    }


def test_same_tick_stale_blocker_and_admission_conflict_converges_to_stable_typed_blocker() -> None:
    step = _stable_transition_step(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "same-tick::stale-blocker-vs-admission",
                "typed_blocker": {
                    "blocker_type": "anti_loop_budget_exhausted",
                    "typed_blocker_ref": "typed_blocker:dm002:same_tick_stale_blocker",
                },
                "currentness_basis": {
                    "truth_epoch": "truth::dm002::same-tick",
                    "observed_generation": "runtime-health-event::dm002::same-tick",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "next_safe_action": {
                    "kind": "admit_provider_attempt",
                    "owner": "one-person-lab",
                    "provider_admission_allowed": True,
                },
            },
            "provider_admission_pending_count": 1,
        }
    )

    _assert_exactly_one_transition(
        step,
        transition_kind="RecordTypedBlocker",
        postcondition_kind="typed_blocker_ref",
        outcome_kind="typed_blocker",
    )
    assert step["paper_progress_policy_result"]["paper_policy_verdict"]["typed_blocker_ref"] == (
        "typed_blocker:dm002:same_tick_stale_blocker"
    )


def test_provider_admission_pending_count_zero_is_forbidden_as_completion_interpretation() -> None:
    step = _stable_transition_step(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "provider_admission_pending_count": 0,
            "managed_study_opl_provider_admission_candidates": [],
            "action_queue": [],
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": "current-readiness-typed-blocker::dm002",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "typed_blocker_ref": "typed_blocker:dm002:medical_paper_readiness_missing",
                },
            },
        }
    )

    _assert_exactly_one_transition(
        step,
        transition_kind="RecordTypedBlocker",
        postcondition_kind="typed_blocker_ref",
        outcome_kind="typed_blocker",
    )
    assert step["paper_progress_policy_result"]["paper_policy_verdict"]["paper_progress_credit_allowed"] is True


def test_current_work_unit_and_paper_recovery_state_disagreement_resolves_to_one_route_back_transition() -> None:
    step = _stable_transition_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::route-back-disagreement",
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "route_back_required",
                "route_back_evidence_ref": "route_back:dm003:quality_repair_to_publication_gate",
                "next_safe_action": {
                    "kind": "route_back_to_owner_or_repair_materialization",
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "publication-blockers::route-back-disagreement",
                    "route_back_evidence_ref": "route_back:dm003:quality_repair_to_publication_gate",
                },
            },
        }
    )

    _assert_exactly_one_transition(
        step,
        transition_kind="AdoptRouteBackEvidence",
        postcondition_kind="route_back_evidence_ref",
        outcome_kind="route_back_evidence",
    )
    assert step["paper_progress_policy_result"]["paper_policy_verdict"] == {
        "verdict": "route_back_evidence_required",
        "route_back_evidence_ref": "route_back:dm003:quality_repair_to_publication_gate",
        "paper_progress_credit_allowed": True,
    }


def test_dhd_provider_transition_request_without_opl_readback_becomes_non_advancing_apply() -> None:
    requested = _stable_transition_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::await-opl-readback",
                "currentness_basis": {
                    "truth_epoch": "truth::dm003::await-opl-readback",
                    "observed_generation": "runtime-health-event::dm003::await-opl-readback",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "transition_request_pending",
                "next_safe_action": {
                    "kind": "await_opl_transition_readback",
                    "provider_admission_requires_opl_runtime_result": True,
                    "provider_admission_allowed": True,
                },
            },
        }
    )
    no_readback = _non_advancing_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::await-opl-readback",
                "currentness_basis": {
                    "truth_epoch": "truth::dm003::await-opl-readback",
                    "observed_generation": "runtime-health-event::dm003::await-opl-readback",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "transition_request_pending",
            },
        }
    )

    _assert_exactly_one_transition(
        requested,
        transition_kind="StartProviderAttempt",
        postcondition_kind="provider_admission_enqueued_or_blocked",
        outcome_kind="provider_admission_requested",
    )
    assert requested["paper_progress_policy_result"]["paper_policy_verdict"][
        "provider_completion_is_domain_completion"
    ] is False
    _assert_exactly_one_transition(
        no_readback,
        transition_kind="NonAdvancingApply",
        postcondition_kind="non_advancing_apply_typed_blocker_ref",
        outcome_kind="non_advancing_apply_typed_blocker",
    )


def test_human_gate_and_route_back_are_accepted_live_evidence_shapes_not_queue_claims() -> None:
    human_gate = _stable_transition_step(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "human",
                "action_type": "approve_publication_route",
                "work_unit_id": "publication_route_human_gate",
                "work_unit_fingerprint": "human-gate::dm002",
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "human_gate",
                "human_gate_ref": "human_gate:dm002:publication_route",
                "next_safe_action": {
                    "kind": "wait_for_owner_with_resume_token",
                    "human_gate_ref": "human_gate:dm002:publication_route",
                },
            },
        }
    )
    route_back = _stable_transition_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "route_back_required",
                "route_back_evidence_ref": "route_back:dm003:publication_gate_to_write",
                "next_safe_action": {
                    "kind": "route_back_to_owner_or_repair_materialization",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "route-back::dm003",
                    "route_back_evidence_ref": "route_back:dm003:publication_gate_to_write",
                },
            },
        }
    )

    _assert_exactly_one_transition(
        human_gate,
        transition_kind="OpenHumanGate",
        postcondition_kind="human_gate_ref",
        outcome_kind="human_gate",
    )
    assert human_gate["paper_progress_policy_result"]["paper_policy_verdict"]["human_gate_ref"] == (
        "human_gate:dm002:publication_route"
    )
    _assert_exactly_one_transition(
        route_back,
        transition_kind="AdoptRouteBackEvidence",
        postcondition_kind="route_back_evidence_ref",
        outcome_kind="route_back_evidence",
    )
    assert route_back["paper_progress_policy_result"]["paper_policy_verdict"]["route_back_evidence_ref"] == (
        "route_back:dm003:publication_gate_to_write"
    )


def test_paper_progress_replay_live_evidence_status_contract_keeps_live_acceptance_exactly_one() -> None:
    contract_path = Path("contracts/paper_progress_replay_live_evidence_status.json")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    allowed = contract["live_evidence_acceptance"]["allowed_exactly_one_families"]
    assert allowed == [
        "strict_current_identity_running_proof",
        "owner_receipt_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
        "paper_gate_artifact_semantic_delta_ref",
    ]
    assert contract["live_evidence_acceptance"]["exactly_one_required"] is True
    assert contract["live_evidence_acceptance"]["fresh_live_command_required"] is True
    forbidden = set(contract["forbidden_completion_interpretations"])
    assert "queue_empty" in forbidden
    assert "DHD_dry_run" in forbidden
    assert "provider_admission_pending_count=0" in forbidden
    assert "focused_tests_passed" in forbidden
    assert "stale_transition_request_after_terminal_owner_receipt_closeout_as_pending_progress" in forbidden
    assert contract["current_status"]["live_paper_progress_claim_allowed"] is False
    replay_trace_ids = {item["trace_id"] for item in contract["replay_coverage"]}
    assert "closeout_stagerun_identity_split" in replay_trace_ids
    assert "terminal_owner_receipt_closeout_transition_request_residue" in replay_trace_ids
    assert "provider_admission_same_identity_live_readback_consumes_transition_request" in replay_trace_ids
    assert "provider_admission_cross_identity_readback_remains_request_pending" in replay_trace_ids
    assert "provider_admission_bare_transaction_fragments_rejected" in replay_trace_ids
    assert contract["projection_metadata_completion_gate"]["required_fields"] == [
        "authority",
        "derived_from_event_id",
        "observed_generation",
        "lag_status",
    ]
    assert contract["projection_metadata_completion_gate"]["lag_status_status"] == "covered_by_focused_tests"
    assert contract["projection_metadata_completion_gate"]["blocking_write_set"] == []
