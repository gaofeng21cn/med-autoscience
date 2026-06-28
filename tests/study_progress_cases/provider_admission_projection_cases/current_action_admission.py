from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.study_progress_cases.shared import _write_json
from tests.study_progress_cases.provider_admission_projection import (
    _non_advancing_opl_transition_result,
    _opl_transition_result,
    _quality_repair_current_work_unit,
    _quality_repair_handoff,
    _supervisor_decision,
    _write_ready_quality_repair_dispatch,
    _write_transition_runtime_log,
)


def test_provider_admission_projection_emits_candidate_for_current_executable_action(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert len(fields["provider_admission_candidates"]) == 1
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == "medical_prose_write_repair"
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["next_executable_owner"] == "write"
    expected_identity = f"provider-admission::{study_id}::{fingerprint}"
    expected_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "owner_callable_adapters/run_quality_repair_batch.json"
    )
    assert candidate["route_identity_key"] == expected_identity
    assert candidate["attempt_idempotency_key"] == expected_identity
    assert candidate["stage_packet_ref"] == expected_stage_packet_ref
    assert candidate["stage_packet_refs"] == [candidate["stage_packet_ref"]]


def test_provider_admission_projection_consumes_matching_terminal_closeout_over_current_action(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_handoff",
            "provider_admission_terminal_closeout_consumed": {
                "surface_kind": "provider_admission_terminal_closeout_consumed",
                "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
                "stage_attempt_id": "sat-terminal",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                    "controller/repair_execution_receipts/latest.json"
                ),
                "authority_boundary": {
                    "projection_only": True,
                    "runtime_owner": "one-person-lab",
                    "domain_truth_owner": "med-autoscience",
                    "can_authorize_provider_admission": False,
                    "can_start_provider_attempt": False,
                    "provider_completion_is_domain_completion": False,
                },
            },
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []
    assert fields["provider_admission_terminal_closeout_consumed"]["stage_attempt_id"] == "sat-terminal"


def test_provider_admission_projection_blocks_queue_residue_under_supervisor_stop_decision(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "supervisor_decision": _supervisor_decision(
                    "stop_with_stable_typed_blocker",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["paper_autonomy_supervisor_decision"]["decision"] == "stop_with_stable_typed_blocker"
    assert fields["provider_admission_blocked_by_supervisor_decision"] == {
        "decision": "stop_with_stable_typed_blocker",
        "reason": "paper_autonomy_supervisor_decision_blocks_provider_admission",
    }


def test_provider_admission_projection_execute_decision_allows_current_candidate(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "supervisor_decision": _supervisor_decision(
                    "execute_current_owner_delta",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["provider_admission_candidates"][0]["work_unit_fingerprint"] == fingerprint


def test_provider_admission_projection_materialize_recovery_action_accepts_log_readback(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_requires_opl_runtime_result": True,
                "successor_owner_action": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "supervisor_decision": _supervisor_decision(
                "materialize_recovery_action",
                study_id=study_id,
                fingerprint=fingerprint,
            ),
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "provider_admission_pending": False,
            },
            "currentness_basis": {
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "truth_epoch": "truth::current",
                "runtime_health_epoch": "runtime::current",
            },
        },
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "action_queue": [],
    }
    current_control = module._current_control_payload_for_provider_admission(
        payload=payload,
        handoff=handoff,
    )
    candidates = provider_admission.current_control_provider_admission_candidates(
        current_control,
        study_root=study_root,
        status_payload=payload,
        current_control_ref=handoff["source_path"],
    )
    assert len(candidates) == 1
    request = candidates[0]["opl_domain_progress_transition_request"]
    _write_transition_runtime_log(
        study_root,
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        idempotency_key=request["idempotency_key"],
    )

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff=handoff,
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []
    assert "provider_admission_blocked_by_supervisor_decision" not in fields
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["status"] == "provider_admission_pending"
    assert candidate["provider_admission_pending"] is True
    assert candidate["provider_admission_requires_opl_runtime_result"] is False
    assert candidate["opl_transition_readback_source"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )


def test_provider_admission_projection_consumes_same_identity_owner_receipt_successor_terminal_closeout(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "conditions": [
                    {
                        "condition": "consumed_owner_receipt_routeback_successor",
                        "source_condition": "current_work_unit_owner_receipt_recorded",
                    }
                ],
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "supervisor_decision": _supervisor_decision(
                    "materialize_recovery_action",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "provider_admission_pending": False,
                },
                "currentness_basis": {
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "provider_admission_terminal_closeout_consumed": {
                "surface_kind": "provider_admission_terminal_closeout_consumed",
                "stage_attempt_id": "sat_f22f2e9d25d336fa2a2a4306",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                    "controller/repair_execution_receipts/latest.json"
                ),
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "owner_receipt_recorded",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "owner_receipt_recorded",
                    "owner_receipt_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                        "controller/repair_execution_receipts/latest.json"
                    ),
                },
            },
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
            },
            "action_queue": [],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []
    consumed = fields["provider_admission_terminal_closeout_consumed"]
    assert consumed["stage_attempt_id"] == "sat_f22f2e9d25d336fa2a2a4306"
    assert consumed["work_unit_id"] == work_unit_id
    assert consumed["work_unit_fingerprint"] == fingerprint


def test_provider_admission_projection_keeps_handoff_live_readback_for_successor_after_owner_receipt(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    readback = _opl_transition_result(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "source": "opl_current_control_state.provider_admission_candidates",
                "study_id": study_id,
                "quest_id": study_id,
                "status": "provider_admission_pending",
                "next_executable_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "provider_attempt_or_lease_required": True,
                "opl_domain_progress_transition_runtime_live_readback": readback,
            }
        ],
        "action_queue": [],
    }
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "owner_receipt_recorded",
                "provider_admission_pending": False,
            },
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_allowed": True,
                "successor_owner_action": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
    }

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff=handoff,
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["transition_request_pending_count"] == 0
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["opl_transition_readback_source"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )


def test_provider_admission_projection_consumes_non_advancing_apply_without_provider_admission(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    handoff = _quality_repair_handoff(study_id=study_id, fingerprint=fingerprint)
    handoff["action_queue"][0]["opl_domain_progress_transition_runtime_live_readback"] = (
        _non_advancing_opl_transition_result(
            study_id=study_id,
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
        )
    )

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
        },
        handoff=handoff,
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []


def test_provider_admission_projection_materializes_gate_followthrough_owner_action_without_pending_flag(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "owner_route_currentness_basis": {
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "source_eval_id": source_eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
                "target_surface": {
                    "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                    "route_target": "write",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "next_work_unit": work_unit_id,
                    "owner_answer_missing": False,
                    "owner_answer_still_required": False,
                    "provider_admission_pending": False,
                },
                "currentness_basis": {
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "source_eval_id": source_eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "action_queue": [],
            "blocked_reason": "no_selected_dispatch_for_requested_action_types",
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 1
    candidate = fields["transition_request_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["currentness_basis"]["source_eval_id"] == source_eval_id
    assert candidate["status"] == "transition_request_pending"
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["mas_owner_action_source"] == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    )
    expected_identity = f"provider-admission::{study_id}::{fingerprint}"
    expected_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "owner_callable_adapters/run_quality_repair_batch.json"
    )
    assert candidate["route_identity_key"] == expected_identity
    assert candidate["attempt_idempotency_key"] == expected_identity
    assert candidate["stage_packet_ref"] == expected_stage_packet_ref
    assert candidate["stage_packet_refs"] == [candidate["stage_packet_ref"]]
